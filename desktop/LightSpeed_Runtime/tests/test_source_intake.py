from __future__ import annotations

import io
import json
import struct
import zipfile

import pytest

from lightspeed_runtime.source_intake import SourceIntakeError, bind_envelope_to_conversion_plan, build_source_envelope


def test_markdown_preserves_native_identity_and_heading_projection():
    data = b"# Title\n\nBody\n## Child\n"
    env = build_source_envelope(source_name="note.md", data=data, source_ref="drive:file-1")
    assert env["adapter_id"] == "text-stdlib-v0.1"
    assert env["native_preservation"]["source_ref"] == "drive:file-1"
    assert env["projections"][0]["headings"][0]["text"] == "Title"
    assert env["lineage"]["canonical_mutation"] is False


def test_json_projection_is_structured_and_hash_stable():
    data = b'{"b":2,"a":[1,3]}'
    a = build_source_envelope(source_name="state.json", data=data)
    b = build_source_envelope(source_name="state.json", data=data)
    assert a["adapter_id"] == "json-stdlib-v0.1"
    assert a["projections"][0]["value"] == {"b": 2, "a": [1, 3]}
    assert a["sha256"] == b["sha256"]
    assert a["envelope_sha256"] == b["envelope_sha256"]


def test_csv_projection_retains_rows_as_table_not_generic_document():
    env = build_source_envelope(source_name="table.csv", data=b"id,value\nA,1\nB,2\n")
    projection = env["projections"][0]
    assert env["adapter_id"] == "csv-stdlib-v0.1"
    assert projection["kind"] == "table"
    assert projection["rows"][0] == ["id", "value"]


def _docx_bytes():
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello CGX</w:t></w:r></w:p></w:body></w:document>',
        )
        z.writestr("_rels/.rels", "<Relationships/>")
    return out.getvalue()


def test_docx_ooxml_extracts_paragraphs_without_replacing_source():
    env = build_source_envelope(source_name="brief.docx", data=_docx_bytes())
    assert env["adapter_id"] == "docx-ooxml-stdlib-v0.1"
    assert env["projections"][0]["paragraphs"] == ["Hello CGX"]
    assert env["native_preservation"]["round_trip_claim"] == "SEMANTIC_PROJECTION_ONLY"


def _xlsx_bytes():
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1"><v>2</v></c><c r="B1"><f>A1*3</f><v>6</v></c></row></sheetData><mergeCells count="1"><mergeCell ref="C1:D1"/></mergeCells></worksheet>',
        )
    return out.getvalue()


def test_xlsx_projection_keeps_formula_and_merge_structure():
    env = build_source_envelope(source_name="calc.xlsx", data=_xlsx_bytes())
    sheet = env["projections"][0]["sheets"][0]
    assert env["adapter_id"] == "xlsx-ooxml-stdlib-v0.1"
    assert sheet["formulas"] == [{"ref": "B1", "formula": "A1*3"}]
    assert sheet["merged_ranges"] == ["C1:D1"]


def test_pdf_stays_reference_only_not_fake_text_parse():
    env = build_source_envelope(source_name="paper.pdf", data=b"%PDF-1.7\nnot real pdf")
    assert env["adapter_id"] == "pdf-pypdf-v0.1"
    assert env["projections"][0]["format_signature"] == "PDF"
    assert "registered_pdf_capability_not_bound_in_generic_source_intake" in env["unresolved"]


def test_obj_projection_counts_geometry_but_does_not_claim_cad_authority():
    env = build_source_envelope(
        source_name="mesh.obj",
        data=b"o Block\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n",
    )
    projection = env["projections"][0]
    assert projection["counts"]["vertices"] == 3
    assert projection["counts"]["faces"] == 1
    assert env["native_preservation"]["round_trip_claim"] == "SEMANTIC_PROJECTION_ONLY"


def test_binary_stl_reads_triangle_header():
    header = b"x" * 80 + struct.pack("<I", 1)
    triangle = b"\x00" * 50
    env = build_source_envelope(source_name="mesh.stl", data=header + triangle)
    projection = env["projections"][0]
    assert projection["format"] == "binary-stl"
    assert projection["triangle_count"] == 1
    assert projection["length_matches"] is True


def test_unknown_binary_is_content_addressed_reference_not_guessed():
    env = build_source_envelope(source_name="mystery.bin", data=b"\x00\x01\x02")
    assert env["adapter_id"] == "binary-reference-v1"
    assert env["projections"][0]["kind"] == "metadata"
    assert env["lineage"]["projection_only"] is True


def test_html_projection_never_executes_script():
    env = build_source_envelope(
        source_name="page.html",
        data=b"<html><body><h1>CGX</h1><script>danger()</script><a href='x'>Link</a></body></html>",
    )
    projection = env["projections"][0]
    assert env["adapter_id"] == "html-stdlib-v0.1"
    assert projection["scripts_executed"] is False
    assert "danger()" not in projection["visible_text"]
    assert projection["links"] == [{"href": "x"}]


def test_obj_diagnostic_remains_frontier_only():
    env = build_source_envelope(
        source_name="mesh.obj",
        data=b"o Block\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n",
    )
    projection = env["projections"][0]
    assert env["adapter_id"] == "obj-diagnostic-v0.1"
    assert projection["admission_state"] == "FRONTIER_ONLY"
    assert projection["conversion_class"] == "R2_RECONSTRUCTED"


def test_conversion_plan_binding_controls_r1_admission():
    data = b'id,value\nA,1\n'
    env = build_source_envelope(source_name="table.csv", data=data, source_ref="drive:table")
    plan = {
        "schema": "CGX-CONVERSION-PLAN/0.1",
        "plan_sha256": "a" * 64,
        "source": {
            "file_name": "table.csv",
            "source_ref": "drive:table",
            "sha256": env["sha256"],
            "media_type": "text/csv",
            "native_authority_preserved": True,
        },
        "type_profile": {"adapter": "csv-stdlib-v0.1"},
        "registered_mapping": None,
        "stages": [
            {"class": "R0_EXACT", "state": "READY"},
            {"class": "R1_SEMANTIC_REVERSIBLE", "state": "READY", "adapter": "csv-stdlib-v0.1"},
        ],
    }
    bound = bind_envelope_to_conversion_plan(env, plan)
    assert bound["admission_state"] == "R1_ADMITTED"
    assert bound["conversion_classes_admitted"] == ["R0_EXACT", "R1_SEMANTIC_REVERSIBLE"]
    assert bound["projections"][0]["admitted_semantic_class"] == "R1_SEMANTIC_REVERSIBLE"


def test_parser_does_not_self_authorise_specialist_r1():
    env = build_source_envelope(source_name="mesh.obj", data=b"v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
    plan = {
        "schema": "CGX-CONVERSION-PLAN/0.1",
        "plan_sha256": "b" * 64,
        "source": {
            "file_name": "mesh.obj",
            "source_ref": "drive:mesh",
            "sha256": env["sha256"],
            "media_type": "model/obj",
            "native_authority_preserved": True,
        },
        "type_profile": {"adapter": None, "status": "specialist-adapter-required"},
        "registered_mapping": None,
        "stages": [{"class": "R0_EXACT", "state": "READY"}],
    }
    bound = bind_envelope_to_conversion_plan(env, plan)
    assert bound["admission_state"] == "R0_REFERENCE_ONLY"
    assert bound["conversion_classes_admitted"] == ["R0_EXACT"]
    assert bound["projections"][0]["admitted_semantic_class"] is None


def test_plan_source_mismatch_fails_closed():
    env = build_source_envelope(source_name="state.json", data=b'{"a":1}')
    plan = {
        "schema": "CGX-CONVERSION-PLAN/0.1",
        "source": {"file_name": "state.json", "sha256": "0" * 64},
        "stages": [{"class": "R0_EXACT", "state": "READY"}],
    }
    with pytest.raises(SourceIntakeError, match="source hash"):
        bind_envelope_to_conversion_plan(env, plan)


def test_svg_projection_is_structural_and_non_executing():
    data = b'''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50" viewBox="0 0 100 50">
      <g id="layer"><rect id="r1" x="1" y="2" width="10" height="20"/></g>
      <script>danger()</script>
    </svg>'''
    env = build_source_envelope(source_name="diagram.svg", data=data)
    projection = env["projections"][0]
    assert env["adapter_id"] == "svg-xml-stdlib-v0.1"
    assert projection["conversion_class"] == "R1_SEMANTIC_REVERSIBLE"
    assert projection["root"]["viewBox"] == "0 0 100 50"
    assert projection["tag_counts"]["rect"] == 1
    rect = next(item for item in projection["elements"] if item["tag"] == "rect")
    assert rect["path"].endswith("/g[1]/rect[1]")
    assert rect["attributes"]["id"] == "r1"
    assert projection["scripts_executed"] is False


def test_png_metadata_projection_reads_exact_dimensions_without_visual_inference():
    png = (
        b"\x89PNG\r\n\x1a\n"
        + (13).to_bytes(4, "big")
        + b"IHDR"
        + (640).to_bytes(4, "big")
        + (480).to_bytes(4, "big")
        + b"\x08\x06\x00\x00\x00"
    )
    env = build_source_envelope(source_name="image.png", data=png)
    projection = env["projections"][0]
    assert env["adapter_id"] == "image-metadata-stdlib-v0.1"
    assert projection["width_px"] == 640
    assert projection["height_px"] == 480
    assert "text" not in projection


def test_gif_metadata_projection_reads_logical_screen_dimensions():
    gif = b"GIF89a" + (320).to_bytes(2, "little") + (200).to_bytes(2, "little")
    env = build_source_envelope(source_name="image.gif", data=gif)
    projection = env["projections"][0]
    assert projection["format_signature"] == "GIF89a"
    assert projection["width_px"] == 320
    assert projection["height_px"] == 200


def test_gltf_json_projection_keeps_graph_and_external_references():
    payload = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "Root", "mesh": 0}],
        "meshes": [{"name": "Body", "primitives": [{"attributes": {"POSITION": 0}}]}],
        "buffers": [{"uri": "body.bin", "byteLength": 36}],
        "images": [{"uri": "skin.png"}],
    }
    env = build_source_envelope(
        source_name="model.gltf",
        data=json.dumps(payload).encode("utf-8"),
    )
    projection = env["projections"][0]
    assert env["adapter_id"] == "gltf-stdlib-v0.1"
    assert projection["container"] == "gltf-json"
    assert projection["counts"]["nodes"] == 1
    assert projection["counts"]["meshes"] == 1
    assert {item["uri"] for item in projection["external_uris"]} == {"body.bin", "skin.png"}


def test_glb_projection_reads_json_and_chunk_offsets_without_decoding_binary_payload():
    value = json.dumps({"asset": {"version": "2.0"}, "nodes": [{"name": "A"}]}).encode("utf-8")
    padded = value + b" " * ((4 - len(value) % 4) % 4)
    binary = b"\x01\x02\x03\x04"
    json_chunk = len(padded).to_bytes(4, "little") + b"JSON" + padded
    bin_chunk = len(binary).to_bytes(4, "little") + b"BIN\x00" + binary
    length = 12 + len(json_chunk) + len(bin_chunk)
    glb = b"glTF" + (2).to_bytes(4, "little") + length.to_bytes(4, "little") + json_chunk + bin_chunk
    env = build_source_envelope(source_name="model.glb", data=glb)
    projection = env["projections"][0]
    assert projection["container"] == "glb"
    assert projection["version"] == 2
    assert projection["counts"]["nodes"] == 1
    assert [chunk["type"] for chunk in projection["chunks"]] == ["JSON", "BIN"]
    assert projection["chunks"][1]["byte_length"] == 4


def test_step_part21_projection_preserves_entity_identity_and_lines():
    step = b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('CGX test'),'2;1');
FILE_NAME('sample.step','2026-10-01T00:00:00',('A'),('B'),'','','');
ENDSEC;
DATA;
#1=CARTESIAN_POINT('',(0.0,0.0,0.0));
#2=DIRECTION('',(0.0,0.0,1.0));
#3=AXIS2_PLACEMENT_3D('',#1,#2,$);
ENDSEC;
END-ISO-10303-21;
"""
    env = build_source_envelope(source_name="sample.step", data=step)
    projection = env["projections"][0]
    assert env["adapter_id"] == "step-part21-stdlib-v0.1"
    assert projection["format"] == "STEP-Part21"
    assert projection["entity_count"] == 3
    assert projection["entities"][0]["entity_id"] == 1
    assert projection["entities"][0]["entity_type"] == "CARTESIAN_POINT"
    assert projection["entities"][2]["raw"].startswith("#3=AXIS2_PLACEMENT_3D")
    assert projection["engineering_interpretation_performed"] is False
    assert projection["brep_validation_performed"] is False
    assert projection["units_inferred"] is False


def test_step_semicolon_inside_string_does_not_split_statement():
    step = b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('a;b'),'2;1');
ENDSEC;
DATA;
#1=CARTESIAN_POINT('p;1',(1.,2.,3.));
ENDSEC;
END-ISO-10303-21;
"""
    env = build_source_envelope(source_name="quoted.stp", data=step)
    projection = env["projections"][0]
    assert projection["entity_count"] == 1
    assert "'p;1'" in projection["entities"][0]["raw"]


def test_fcstd_projection_reads_container_and_document_structure_without_shape_interpretation():
    out = io.BytesIO()
    document = b'''<Document>
      <ObjectData>
        <Object name="Body" type="PartDesign::Body">
          <Properties>
            <Property name="Label" type="App::PropertyString"/>
            <Property name="Shape" type="Part::PropertyPartShape"/>
          </Properties>
        </Object>
      </ObjectData>
      <ObjectDeps>
        <ObjectDep name="Body" count="0"/>
      </ObjectDeps>
    </Document>'''
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("Document.xml", document)
        z.writestr("GuiDocument.xml", b"<GuiDocument/>")
        z.writestr("PartShape.brp", b"opaque-brep-payload")

    env = build_source_envelope(source_name="model.FCStd", data=out.getvalue())
    projection = env["projections"][0]
    assert env["adapter_id"] == "freecad-fcstd-stdlib-v0.1"
    assert projection["format"] == "FreeCAD-FCStd"
    assert projection["archive_member_count"] == 3
    assert any(item["name"] == "Body" and item["type"] == "PartDesign::Body" for item in projection["objects"])
    assert any(item["name"] == "Shape" and item["type"] == "Part::PropertyPartShape" for item in projection["properties"])
    assert any(item["name"] == "PartShape.brp" for item in projection["members"])
    assert projection["shape_payload_interpreted"] is False
    assert projection["brep_validation_performed"] is False
    assert projection["engineering_geometry_inferred"] is False


def test_invalid_fcstd_falls_back_without_inventing_document_structure():
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("GuiDocument.xml", b"<GuiDocument/>")
    env = build_source_envelope(source_name="broken.fcstd", data=out.getvalue())
    assert env["adapter_id"] == "freecad-fcstd-stdlib-v0.1"
    assert env["projections"][0]["kind"] == "metadata"
    assert any("deep_projection_failed:SourceIntakeError" in warning for warning in env["warnings"])
    assert "deep_projection_requires_recovery_or_specialist_adapter" in env["unresolved"]
