from __future__ import annotations

import io
import json
import struct
import zipfile

from lightspeed_runtime.source_intake import build_source_envelope


def test_markdown_preserves_native_identity_and_heading_projection():
    data = b"# Title\n\nBody\n## Child\n"
    env = build_source_envelope(source_name="note.md", data=data, source_ref="drive:file-1")
    assert env["adapter_id"] == "text-v1"
    assert env["native_preservation"]["source_ref"] == "drive:file-1"
    assert env["projections"][0]["headings"][0]["text"] == "Title"
    assert env["lineage"]["canonical_mutation"] is False


def test_json_projection_is_structured_and_hash_stable():
    data = b'{"b":2,"a":[1,3]}'
    a = build_source_envelope(source_name="state.json", data=data)
    b = build_source_envelope(source_name="state.json", data=data)
    assert a["adapter_id"] == "json-v1"
    assert a["projections"][0]["value"] == {"b": 2, "a": [1, 3]}
    assert a["sha256"] == b["sha256"]
    assert a["envelope_sha256"] == b["envelope_sha256"]


def test_csv_projection_retains_rows_as_table_not_generic_document():
    env = build_source_envelope(source_name="table.csv", data=b"id,value\nA,1\nB,2\n")
    projection = env["projections"][0]
    assert env["adapter_id"] == "tabular-delimited-v1"
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
    assert env["adapter_id"] == "docx-ooxml-v1"
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
    assert env["adapter_id"] == "xlsx-ooxml-v1"
    assert sheet["formulas"] == [{"ref": "B1", "formula": "A1*3"}]
    assert sheet["merged_ranges"] == ["C1:D1"]


def test_pdf_stays_reference_only_not_fake_text_parse():
    env = build_source_envelope(source_name="paper.pdf", data=b"%PDF-1.7\nnot real pdf")
    assert env["adapter_id"] == "pdf-reference-v1"
    assert env["projections"][0]["format_signature"] == "PDF"
    assert "deep_semantic_projection_not_admitted_for_adapter" in env["unresolved"]


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
