from __future__ import annotations

import csv
import hashlib
from html.parser import HTMLParser
import io
import json
import mimetypes
import struct
import zipfile
from pathlib import Path
from typing import Any, BinaryIO
import xml.etree.ElementTree as ET


SCHEMA = "CGX-SOURCE-ENVELOPE/0.1"
ADAPTER_VERSION = "0.1"
_MAX_TEXT_BYTES = 2 * 1024 * 1024
_MAX_ROWS = 5000
_MAX_XML_MEMBERS = 256


class SourceIntakeError(ValueError):
    pass


def _hash_stream(stream: BinaryIO) -> tuple[str, int, bytes]:
    sha = hashlib.sha256()
    total = 0
    chunks: list[bytes] = []
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        sha.update(chunk)
        total += len(chunk)
        if sum(len(x) for x in chunks) < _MAX_TEXT_BYTES:
            remaining = _MAX_TEXT_BYTES - sum(len(x) for x in chunks)
            chunks.append(chunk[:remaining])
    return sha.hexdigest(), total, b"".join(chunks)


def _adapter_for(extension: str) -> tuple[str, str]:
    ext = extension.lower()
    groups = {
        "text-stdlib-v0.1": {".txt", ".md", ".markdown", ".py", ".yaml", ".yml", ".ini", ".cfg", ".toml"},
        "json-stdlib-v0.1": {".json", ".jsonl"},
        "csv-stdlib-v0.1": {".csv", ".tsv"},
        "html-stdlib-v0.1": {".html", ".htm"},
        "docx-ooxml-stdlib-v0.1": {".docx"},
        "xlsx-ooxml-stdlib-v0.1": {".xlsx", ".xlsm"},
        "pdf-pypdf-v0.1": {".pdf"},
        "image-reference-v0.1": {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff"},
        "obj-diagnostic-v0.1": {".obj"},
        "stl-diagnostic-v0.1": {".stl"},
        "step-reference-v0.1": {".step", ".stp"},
        "gltf-reference-v0.1": {".gltf", ".glb"},
    }
    for adapter, extensions in groups.items():
        if ext in extensions:
            family = {
                "text-stdlib-v0.1": "text",
                "json-stdlib-v0.1": "structured-text",
                "csv-stdlib-v0.1": "table",
                "html-stdlib-v0.1": "document",
                "docx-ooxml-stdlib-v0.1": "document",
                "xlsx-ooxml-stdlib-v0.1": "workbook",
                "pdf-pypdf-v0.1": "document",
                "image-reference-v0.1": "image",
                "obj-diagnostic-v0.1": "spatial",
                "stl-diagnostic-v0.1": "spatial",
                "step-reference-v0.1": "spatial-cad",
                "gltf-reference-v0.1": "spatial",
            }[adapter]
            return adapter, family
    return "binary-reference-v1", "binary"


def _decode_text(data: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8-replacement"


def _text_projection(data: bytes) -> dict[str, Any]:
    text, encoding = _decode_text(data)
    lines = text.splitlines()
    headings = [
        {"line": i + 1, "text": line.lstrip("#").strip(), "level": len(line) - len(line.lstrip("#"))}
        for i, line in enumerate(lines)
        if line.startswith("#") and line.lstrip("#").strip()
    ][:256]
    return {
        "kind": "text",
        "encoding": encoding,
        "line_count": len(lines),
        "character_count": len(text),
        "headings": headings,
        "text": text,
        "truncated": len(data) >= _MAX_TEXT_BYTES,
    }


class _HTMLProjectionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: dict[str, int] = {}
        self.links: list[dict[str, str]] = []
        self.text_parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self.tags[tag] = self.tags.get(tag, 0) + 1
        if tag in {"script", "style"}:
            self._skip_depth += 1
        if tag == "a" and len(self.links) < 2048:
            attr_map = {str(k).lower(): str(v) for k, v in attrs if v is not None}
            if "href" in attr_map:
                self.links.append({"href": attr_map["href"]})

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = " ".join(data.split())
        if text:
            self.text_parts.append(text)


def _html_projection(data: bytes) -> dict[str, Any]:
    text, encoding = _decode_text(data)
    parser = _HTMLProjectionParser()
    parser.feed(text)
    visible_text = "\n".join(parser.text_parts)
    return {
        "kind": "structure",
        "conversion_class": "R1_SEMANTIC_REVERSIBLE",
        "encoding": encoding,
        "tag_counts": dict(sorted(parser.tags.items())),
        "links": parser.links,
        "visible_text": visible_text,
        "execution_performed": False,
        "scripts_executed": False,
    }


def _json_projection(data: bytes, extension: str) -> dict[str, Any]:
    text, encoding = _decode_text(data)
    if extension == ".jsonl":
        rows = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            if len(rows) >= _MAX_ROWS:
                break
            rows.append({"line": line_no, "value": json.loads(line)})
        return {"kind": "structure", "encoding": encoding, "jsonl": True, "records": rows, "truncated": len(rows) >= _MAX_ROWS}
    value = json.loads(text)
    return {"kind": "structure", "encoding": encoding, "jsonl": False, "value": value}


def _delimited_projection(data: bytes, delimiter: str) -> dict[str, Any]:
    text, encoding = _decode_text(data)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = []
    for index, row in enumerate(reader):
        if index >= _MAX_ROWS:
            break
        rows.append(row)
    width = max((len(row) for row in rows), default=0)
    return {
        "kind": "table",
        "encoding": encoding,
        "delimiter": delimiter,
        "row_count_sampled": len(rows),
        "column_count_max": width,
        "rows": rows,
        "truncated": len(rows) >= _MAX_ROWS,
    }


def _safe_zip_names(data: bytes) -> tuple[zipfile.ZipFile, list[str]]:
    zf = zipfile.ZipFile(io.BytesIO(data))
    names = zf.namelist()
    if len(names) > 50000:
        raise SourceIntakeError("archive member count exceeds bounded intake limit")
    for name in names:
        norm = name.replace("\\", "/")
        if norm.startswith("/") or ".." in norm.split("/"):
            raise SourceIntakeError(f"unsafe archive member path: {name}")
    return zf, names


def _docx_projection(data: bytes) -> dict[str, Any]:
    zf, names = _safe_zip_names(data)
    paragraphs: list[str] = []
    relationships: list[str] = []
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    if "word/document.xml" in names:
        root = ET.fromstring(zf.read("word/document.xml"))
        for paragraph in root.findall(".//w:p", ns):
            text = "".join((node.text or "") for node in paragraph.findall(".//w:t", ns))
            if text:
                paragraphs.append(text)
    for name in names:
        if name.endswith(".rels") and len(relationships) < _MAX_XML_MEMBERS:
            relationships.append(name)
    return {
        "kind": "structure",
        "paragraph_count": len(paragraphs),
        "paragraphs": paragraphs[:5000],
        "relationship_parts": relationships,
        "member_count": len(names),
    }


def _xlsx_projection(data: bytes) -> dict[str, Any]:
    zf, names = _safe_zip_names(data)
    ns = {
        "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    shared_strings: list[str] = []
    if "xl/sharedStrings.xml" in names:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        for si in root.findall(".//m:si", ns):
            shared_strings.append("".join((t.text or "") for t in si.findall(".//m:t", ns)))
    sheets: list[dict[str, Any]] = []
    for name in sorted(n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"))[:256]:
        root = ET.fromstring(zf.read(name))
        cells = []
        formulas = []
        merges = [x.attrib.get("ref") for x in root.findall(".//m:mergeCell", ns) if x.attrib.get("ref")]
        for cell in root.findall(".//m:c", ns):
            ref = cell.attrib.get("r")
            cell_type = cell.attrib.get("t")
            formula = cell.find("m:f", ns)
            value = cell.find("m:v", ns)
            raw_value = value.text if value is not None else None
            display = raw_value
            if cell_type == "s" and raw_value is not None:
                try:
                    display = shared_strings[int(raw_value)]
                except (ValueError, IndexError):
                    display = raw_value
            cells.append({"ref": ref, "type": cell_type, "value": display})
            if formula is not None:
                formulas.append({"ref": ref, "formula": formula.text or ""})
            if len(cells) >= 20000:
                break
        sheets.append({
            "part": name,
            "cell_count_sampled": len(cells),
            "cells": cells,
            "formulas": formulas,
            "merged_ranges": merges,
        })
    return {
        "kind": "structure",
        "sheet_count": len(sheets),
        "sheets": sheets,
        "member_count": len(names),
        "shared_string_count": len(shared_strings),
    }


def _obj_projection(data: bytes) -> dict[str, Any]:
    text, encoding = _decode_text(data)
    counts = {"vertices": 0, "normals": 0, "texcoords": 0, "faces": 0, "objects": 0, "groups": 0, "materials": 0}
    names: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("v "): counts["vertices"] += 1
        elif s.startswith("vn "): counts["normals"] += 1
        elif s.startswith("vt "): counts["texcoords"] += 1
        elif s.startswith("f "): counts["faces"] += 1
        elif s.startswith("o "):
            counts["objects"] += 1
            if len(names) < 256: names.append(s[2:].strip())
        elif s.startswith("g "): counts["groups"] += 1
        elif s.startswith("usemtl "): counts["materials"] += 1
    return {"kind": "spatial", "conversion_class": "R2_RECONSTRUCTED", "admission_state": "FRONTIER_ONLY", "encoding": encoding, "counts": counts, "object_names": names}


def _stl_projection(data: bytes) -> dict[str, Any]:
    is_ascii = data[:5].lower() == b"solid" and b"facet" in data[:4096].lower()
    if is_ascii:
        text, encoding = _decode_text(data)
        triangles = sum(1 for line in text.splitlines() if line.strip().startswith("facet normal"))
        return {"kind": "spatial", "conversion_class": "R2_RECONSTRUCTED", "admission_state": "FRONTIER_ONLY", "format": "ascii-stl", "encoding": encoding, "triangle_count": triangles}
    if len(data) < 84:
        raise SourceIntakeError("binary STL is shorter than 84-byte header")
    triangles = struct.unpack("<I", data[80:84])[0]
    expected = 84 + triangles * 50
    return {"kind": "spatial", "conversion_class": "R2_RECONSTRUCTED", "admission_state": "FRONTIER_ONLY", "format": "binary-stl", "triangle_count": triangles, "expected_byte_length": expected, "length_matches": expected == len(data)}


def _reference_projection(family: str, data: bytes) -> dict[str, Any]:
    projection: dict[str, Any] = {"kind": "metadata", "family": family}
    if family == "document" and data.startswith(b"%PDF-"):
        projection["format_signature"] = "PDF"
    elif family == "image":
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            projection["format_signature"] = "PNG"
        elif data[:3] == b"\xff\xd8\xff":
            projection["format_signature"] = "JPEG"
        elif data[:4] in {b"RIFF"} and data[8:12] == b"WEBP":
            projection["format_signature"] = "WEBP"
    elif family == "spatial-cad":
        text, _ = _decode_text(data[:65536])
        projection["step_header_present"] = "ISO-10303-21" in text
    elif family == "spatial":
        if data[:4] == b"glTF":
            projection["format_signature"] = "GLB"
    return projection


def build_source_envelope(
    *,
    source_name: str,
    data: bytes,
    source_ref: str | None = None,
    authority: str = "source",
    evidence_state: str = "OBSERVED",
    release_class: str = "Internal",
) -> dict[str, Any]:
    if not isinstance(data, (bytes, bytearray)):
        raise SourceIntakeError("data must be bytes")
    raw = bytes(data)
    extension = Path(source_name).suffix.lower()
    adapter_id, family = _adapter_for(extension)
    sha = hashlib.sha256(raw).hexdigest()
    source_id = f"src:{sha}"
    media_type = mimetypes.guess_type(source_name)[0] or "application/octet-stream"
    warnings: list[str] = []
    unresolved: list[str] = []

    try:
        if adapter_id == "text-stdlib-v0.1":
            projections = [_text_projection(raw[:_MAX_TEXT_BYTES])]
        elif adapter_id == "html-stdlib-v0.1":
            projections = [_html_projection(raw[:_MAX_TEXT_BYTES])]
        elif adapter_id == "json-stdlib-v0.1":
            projections = [_json_projection(raw[:_MAX_TEXT_BYTES], extension)]
        elif adapter_id == "csv-stdlib-v0.1":
            projections = [_delimited_projection(raw[:_MAX_TEXT_BYTES], "\t" if extension == ".tsv" else ",")]
        elif adapter_id == "docx-ooxml-stdlib-v0.1":
            projections = [_docx_projection(raw)]
        elif adapter_id == "xlsx-ooxml-stdlib-v0.1":
            projections = [_xlsx_projection(raw)]
        elif adapter_id == "pdf-pypdf-v0.1":
            projections = [_reference_projection(family, raw)]
            unresolved.append("registered_pdf_capability_not_bound_in_generic_source_intake")
        elif adapter_id == "obj-diagnostic-v0.1":
            projections = [_obj_projection(raw[:_MAX_TEXT_BYTES])]
        elif adapter_id == "stl-diagnostic-v0.1":
            projections = [_stl_projection(raw)]
        else:
            projections = [_reference_projection(family, raw)]
            unresolved.append("deep_semantic_projection_not_admitted_for_adapter")
    except (json.JSONDecodeError, csv.Error, zipfile.BadZipFile, ET.ParseError, UnicodeError, SourceIntakeError, ValueError) as exc:
        projections = [_reference_projection(family, raw)]
        warnings.append(f"deep_projection_failed:{type(exc).__name__}:{exc}")
        unresolved.append("deep_projection_requires_recovery_or_specialist_adapter")

    round_trip = {
        "text-stdlib-v0.1": "SEMANTIC_PROJECTION_ONLY",
        "json-stdlib-v0.1": "LOSSLESS_FOR_DECLARED_FIELDS",
        "csv-stdlib-v0.1": "LOSSLESS_FOR_DECLARED_FIELDS",
        "docx-ooxml-stdlib-v0.1": "SEMANTIC_PROJECTION_ONLY",
        "xlsx-ooxml-stdlib-v0.1": "STRUCTURE_PRESERVED",
        "obj-diagnostic-v0.1": "SEMANTIC_PROJECTION_ONLY",
        "stl-diagnostic-v0.1": "SEMANTIC_PROJECTION_ONLY",
    }.get(adapter_id, "IDENTITY_REFERENCE_ONLY")

    envelope = {
        "schema": SCHEMA,
        "source_id": source_id,
        "sha256": sha,
        "byte_length": len(raw),
        "source_name": source_name,
        "media_type": media_type,
        "extension": extension,
        "adapter_id": adapter_id,
        "native_preservation": {
            "source_ref": source_ref,
            "source_sha256": sha,
            "source_byte_length": len(raw),
            "adapter_version": ADAPTER_VERSION,
            "round_trip_claim": round_trip,
        },
        "authority": authority,
        "evidence_state": evidence_state,
        "release_class": release_class,
        "projections": projections,
        "warnings": warnings,
        "unresolved": unresolved,
        "lineage": {
            "parent_source_id": None,
            "canonical_mutation": False,
            "projection_only": True,
        },
    }
    envelope["envelope_sha256"] = hashlib.sha256(
        json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return envelope


def build_source_envelope_from_path(path: str | Path, **kwargs: Any) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise SourceIntakeError(f"source file does not exist: {p}")
    data = p.read_bytes()
    return build_source_envelope(source_name=p.name, data=data, source_ref=str(p.resolve()), **kwargs)


def bind_envelope_to_conversion_plan(
    envelope: dict[str, Any],
    conversion_plan: dict[str, Any],
) -> dict[str, Any]:
    """Bind an extraction envelope to an already-compiled CGX conversion plan.

    Extraction capability and semantic admission are deliberately separate:
    this function will not treat a parser's output as admitted R1 unless the
    conversion plan contains a READY R1 stage for the same exact source.
    """
    if not isinstance(envelope, dict) or envelope.get("schema") != SCHEMA:
        raise SourceIntakeError("unsupported source envelope")
    if not isinstance(conversion_plan, dict) or conversion_plan.get("schema") != "CGX-CONVERSION-PLAN/0.1":
        raise SourceIntakeError("unsupported conversion plan")

    source = conversion_plan.get("source") or {}
    if source.get("sha256") != envelope.get("sha256"):
        raise SourceIntakeError("conversion plan source hash does not match envelope")
    if source.get("file_name") != envelope.get("source_name"):
        raise SourceIntakeError("conversion plan source name does not match envelope")

    stages = conversion_plan.get("stages") or []
    r1 = next(
        (
            stage
            for stage in stages
            if isinstance(stage, dict)
            and stage.get("class") == "R1_SEMANTIC_REVERSIBLE"
            and stage.get("state") == "READY"
        ),
        None,
    )
    expected_adapter = None
    type_profile = conversion_plan.get("type_profile") or {}
    if isinstance(type_profile, dict):
        expected_adapter = type_profile.get("adapter") or type_profile.get("handler")

    bound = json.loads(json.dumps(envelope))
    bound["conversion_plan_sha256"] = conversion_plan.get("plan_sha256")
    bound["conversion_classes_admitted"] = ["R0_EXACT"]
    bound["semantic_target"] = (
        (conversion_plan.get("registered_mapping") or {}).get("semantic_target")
        if isinstance(conversion_plan.get("registered_mapping"), dict)
        else None
    )

    if r1 is None:
        bound["admission_state"] = "R0_REFERENCE_ONLY"
        bound["unresolved"] = list(bound.get("unresolved") or []) + [
            "R1_not_admitted_by_conversion_plan"
        ]
        for projection in bound.get("projections") or []:
            if isinstance(projection, dict):
                projection["admitted_semantic_class"] = None
        return bound

    if expected_adapter and expected_adapter != envelope.get("adapter_id"):
        bound["admission_state"] = "BLOCKED_ADAPTER_MISMATCH"
        bound["unresolved"] = list(bound.get("unresolved") or []) + [
            f"adapter_mismatch:expected={expected_adapter}:actual={envelope.get('adapter_id')}"
        ]
        return bound

    bound["admission_state"] = "R1_ADMITTED"
    bound["conversion_classes_admitted"].append("R1_SEMANTIC_REVERSIBLE")
    for projection in bound.get("projections") or []:
        if isinstance(projection, dict) and projection.get("admission_state") != "FRONTIER_ONLY":
            projection["admitted_semantic_class"] = "R1_SEMANTIC_REVERSIBLE"
    if conversion_plan.get("registered_mapping"):
        bound["conversion_classes_admitted"].append("R2_RECONSTRUCTED")
        bound["semantic_target"] = (conversion_plan.get("registered_mapping") or {}).get("semantic_target")
    return bound
