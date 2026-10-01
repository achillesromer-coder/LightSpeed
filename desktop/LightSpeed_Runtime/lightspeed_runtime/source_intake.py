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
_MAX_CAD_TEXT_BYTES = 16 * 1024 * 1024
_MAX_CAD_ENTITIES = 100000


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
        "image-metadata-stdlib-v0.1": {".png", ".jpg", ".jpeg", ".gif"},
        "image-reference-v0.1": {".webp", ".tif", ".tiff"},
        "svg-xml-stdlib-v0.1": {".svg"},
        "obj-mesh-stdlib-v0.1": {".obj"},
        "stl-mesh-stdlib-v0.1": {".stl"},
        "step-part21-stdlib-v0.1": {".step", ".stp"},
        "freecad-fcstd-stdlib-v0.1": {".fcstd"},
        "gltf-stdlib-v0.1": {".gltf", ".glb"},
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
                "image-metadata-stdlib-v0.1": "image",
                "image-reference-v0.1": "image",
                "svg-xml-stdlib-v0.1": "image-vector",
                "obj-mesh-stdlib-v0.1": "spatial",
                "stl-mesh-stdlib-v0.1": "spatial",
                "step-part21-stdlib-v0.1": "spatial-cad",
                "freecad-fcstd-stdlib-v0.1": "spatial-cad",
                "gltf-stdlib-v0.1": "spatial",
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


def _parse_obj_float_tokens(tokens: list[str], *, line_no: int, family: str) -> list[float]:
    try:
        return [float(token) for token in tokens]
    except ValueError as exc:
        raise SourceIntakeError(f"OBJ {family} contains non-numeric value at line {line_no}") from exc


def _parse_obj_ref(token: str, *, line_no: int) -> dict[str, Any]:
    parts = token.split("/")
    if len(parts) > 3:
        raise SourceIntakeError(f"OBJ face/reference token has too many fields at line {line_no}")
    values: list[int | None] = []
    for part in parts:
        if part == "":
            values.append(None)
            continue
        try:
            values.append(int(part))
        except ValueError as exc:
            raise SourceIntakeError(f"OBJ reference contains non-integer index at line {line_no}") from exc
    while len(values) < 3:
        values.append(None)
    return {
        "raw": token,
        "vertex_index": values[0],
        "texcoord_index": values[1],
        "normal_index": values[2],
    }


def _obj_projection(data: bytes) -> dict[str, Any]:
    if len(data) > _MAX_CAD_TEXT_BYTES:
        raise SourceIntakeError("OBJ source exceeds bounded structural intake byte limit")
    text, encoding = _decode_text(data)

    vertices: list[dict[str, Any]] = []
    texcoords: list[dict[str, Any]] = []
    normals: list[dict[str, Any]] = []
    parameter_vertices: list[dict[str, Any]] = []
    faces: list[dict[str, Any]] = []
    lines_out: list[dict[str, Any]] = []
    points: list[dict[str, Any]] = []
    directives: list[dict[str, Any]] = []
    total_records = 0

    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        keyword = parts[0]
        args = parts[1:]
        total_records += 1
        if total_records > _MAX_CAD_ENTITIES:
            raise SourceIntakeError("OBJ record count exceeds bounded intake limit")

        if keyword == "v":
            if len(args) not in {3, 4}:
                raise SourceIntakeError(f"OBJ vertex must have 3 or 4 coordinates at line {line_no}")
            vertices.append({
                "index": len(vertices) + 1,
                "line": line_no,
                "raw": stripped,
                "tokens": args,
                "values": _parse_obj_float_tokens(args, line_no=line_no, family="vertex"),
            })
        elif keyword == "vt":
            if not 1 <= len(args) <= 3:
                raise SourceIntakeError(f"OBJ texture coordinate must have 1..3 values at line {line_no}")
            texcoords.append({
                "index": len(texcoords) + 1,
                "line": line_no,
                "raw": stripped,
                "tokens": args,
                "values": _parse_obj_float_tokens(args, line_no=line_no, family="texcoord"),
            })
        elif keyword == "vn":
            if len(args) != 3:
                raise SourceIntakeError(f"OBJ normal must have 3 values at line {line_no}")
            normals.append({
                "index": len(normals) + 1,
                "line": line_no,
                "raw": stripped,
                "tokens": args,
                "values": _parse_obj_float_tokens(args, line_no=line_no, family="normal"),
            })
        elif keyword == "vp":
            if not 1 <= len(args) <= 3:
                raise SourceIntakeError(f"OBJ parameter-space vertex must have 1..3 values at line {line_no}")
            parameter_vertices.append({
                "index": len(parameter_vertices) + 1,
                "line": line_no,
                "raw": stripped,
                "tokens": args,
                "values": _parse_obj_float_tokens(args, line_no=line_no, family="parameter vertex"),
            })
        elif keyword == "f":
            if len(args) < 3:
                raise SourceIntakeError(f"OBJ face must contain at least 3 references at line {line_no}")
            faces.append({
                "index": len(faces) + 1,
                "line": line_no,
                "raw": stripped,
                "references": [_parse_obj_ref(token, line_no=line_no) for token in args],
            })
        elif keyword == "l":
            if len(args) < 2:
                raise SourceIntakeError(f"OBJ line must contain at least 2 references at line {line_no}")
            lines_out.append({
                "index": len(lines_out) + 1,
                "line": line_no,
                "raw": stripped,
                "references": [_parse_obj_ref(token, line_no=line_no) for token in args],
            })
        elif keyword == "p":
            if not args:
                raise SourceIntakeError(f"OBJ point record is empty at line {line_no}")
            points.append({
                "index": len(points) + 1,
                "line": line_no,
                "raw": stripped,
                "references": [_parse_obj_ref(token, line_no=line_no) for token in args],
            })
        else:
            directives.append({
                "line": line_no,
                "keyword": keyword,
                "arguments": args,
                "raw": stripped,
            })

    if not vertices and not faces:
        raise SourceIntakeError("OBJ source contains no vertex/face structure")

    directive_counts: dict[str, int] = {}
    for item in directives:
        directive_counts[item["keyword"]] = directive_counts.get(item["keyword"], 0) + 1

    return {
        "kind": "spatial",
        "conversion_class": "R1_SEMANTIC_REVERSIBLE",
        "format": "Wavefront-OBJ",
        "encoding": encoding,
        "counts": {
            "vertices": len(vertices),
            "texcoords": len(texcoords),
            "normals": len(normals),
            "parameter_vertices": len(parameter_vertices),
            "faces": len(faces),
            "lines": len(lines_out),
            "points": len(points),
            "directives": len(directives),
        },
        "vertices": vertices,
        "texcoords": texcoords,
        "normals": normals,
        "parameter_vertices": parameter_vertices,
        "faces": faces,
        "lines": lines_out,
        "points": points,
        "directives": directives,
        "directive_counts": dict(sorted(directive_counts.items())),
        "mesh_validation_performed": False,
        "engineering_interpretation_performed": False,
        "units_inferred": False,
        "materials_resolved": False,
    }


def _stl_binary_projection(data: bytes, triangles: int) -> dict[str, Any]:
    if triangles > _MAX_CAD_ENTITIES:
        raise SourceIntakeError("STL triangle count exceeds bounded intake limit")
    expected = 84 + triangles * 50
    if expected != len(data):
        raise SourceIntakeError("binary STL byte length does not match triangle count")
    records: list[dict[str, Any]] = []
    for index in range(triangles):
        offset = 84 + index * 50
        values = struct.unpack("<12fH", data[offset:offset + 50])
        normal = list(values[0:3])
        vertices = [
            list(values[3:6]),
            list(values[6:9]),
            list(values[9:12]),
        ]
        records.append({
            "index": index,
            "byte_offset": offset,
            "normal": normal,
            "vertices": vertices,
            "attribute_byte_count": values[12],
        })
    return {
        "kind": "spatial",
        "conversion_class": "R1_SEMANTIC_REVERSIBLE",
        "format": "binary-stl",
        "header_hex": data[:80].hex(),
        "triangle_count": triangles,
        "triangles": records,
        "expected_byte_length": expected,
        "mesh_validation_performed": False,
        "engineering_interpretation_performed": False,
        "units_inferred": False,
    }


def _stl_ascii_projection(data: bytes) -> dict[str, Any]:
    if len(data) > _MAX_CAD_TEXT_BYTES:
        raise SourceIntakeError("ASCII STL source exceeds bounded structural intake byte limit")
    text, encoding = _decode_text(data)
    lines = text.splitlines()
    solid_name = None
    triangles: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    def floats(tokens: list[str], line_no: int, family: str) -> list[float]:
        if len(tokens) != 3:
            raise SourceIntakeError(f"ASCII STL {family} must contain 3 values at line {line_no}")
        try:
            return [float(token) for token in tokens]
        except ValueError as exc:
            raise SourceIntakeError(f"ASCII STL {family} contains non-numeric value at line {line_no}") from exc

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        lower = [part.lower() for part in parts]
        if lower[0] == "solid" and solid_name is None:
            solid_name = stripped[5:].strip()
        elif len(lower) >= 2 and lower[0] == "facet" and lower[1] == "normal":
            if current is not None:
                raise SourceIntakeError(f"nested STL facet at line {line_no}")
            current = {
                "index": len(triangles),
                "line_start": line_no,
                "normal": floats(parts[2:], line_no, "facet normal"),
                "vertices": [],
            }
        elif lower[0] == "vertex":
            if current is None:
                raise SourceIntakeError(f"STL vertex outside facet at line {line_no}")
            current["vertices"].append(floats(parts[1:], line_no, "vertex"))
        elif lower[0] == "endfacet":
            if current is None:
                raise SourceIntakeError(f"STL endfacet without facet at line {line_no}")
            if len(current["vertices"]) != 3:
                raise SourceIntakeError(f"STL facet must contain exactly 3 vertices before line {line_no}")
            current["line_end"] = line_no
            triangles.append(current)
            current = None
            if len(triangles) > _MAX_CAD_ENTITIES:
                raise SourceIntakeError("STL triangle count exceeds bounded intake limit")

    if current is not None:
        raise SourceIntakeError("ASCII STL ends before endfacet")
    if not triangles:
        raise SourceIntakeError("ASCII STL contains no facets")

    return {
        "kind": "spatial",
        "conversion_class": "R1_SEMANTIC_REVERSIBLE",
        "format": "ascii-stl",
        "encoding": encoding,
        "solid_name": solid_name,
        "triangle_count": len(triangles),
        "triangles": triangles,
        "mesh_validation_performed": False,
        "engineering_interpretation_performed": False,
        "units_inferred": False,
    }


def _stl_projection(data: bytes) -> dict[str, Any]:
    if len(data) >= 84:
        triangles = int.from_bytes(data[80:84], "little")
        expected = 84 + triangles * 50
        if expected == len(data):
            return _stl_binary_projection(data, triangles)
    if data[:5].lower() == b"solid" and b"facet" in data[:4096].lower():
        return _stl_ascii_projection(data)
    raise SourceIntakeError("STL source is neither exact binary layout nor recognised ASCII facet structure")


def _local_xml_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _svg_projection(data: bytes) -> dict[str, Any]:
    text, encoding = _decode_text(data)
    root = ET.fromstring(text)
    if _local_xml_name(root.tag).lower() != "svg":
        raise SourceIntakeError("SVG root element is not <svg>")

    elements: list[dict[str, Any]] = []

    def walk(node: ET.Element, path: str) -> None:
        if len(elements) >= 20000:
            return
        tag = _local_xml_name(node.tag)
        attrs = {str(k): str(v) for k, v in sorted(node.attrib.items())}
        item: dict[str, Any] = {
            "path": path,
            "tag": tag,
            "attributes": attrs,
        }
        if node.text and node.text.strip():
            item["text"] = node.text.strip()
        elements.append(item)
        child_counts: dict[str, int] = {}
        for child in list(node):
            child_tag = _local_xml_name(child.tag)
            child_counts[child_tag] = child_counts.get(child_tag, 0) + 1
            walk(child, f"{path}/{child_tag}[{child_counts[child_tag]}]")

    walk(root, "/svg[1]")
    tag_counts: dict[str, int] = {}
    for item in elements:
        tag = item["tag"]
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return {
        "kind": "structure",
        "conversion_class": "R1_SEMANTIC_REVERSIBLE",
        "encoding": encoding,
        "root": {
            "width": root.attrib.get("width"),
            "height": root.attrib.get("height"),
            "viewBox": root.attrib.get("viewBox"),
            "preserveAspectRatio": root.attrib.get("preserveAspectRatio"),
        },
        "tag_counts": dict(sorted(tag_counts.items())),
        "elements": elements,
        "truncated": len(elements) >= 20000,
        "scripts_executed": False,
    }


def _jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return None
    pos = 2
    sof_markers = {
        0xC0, 0xC1, 0xC2, 0xC3,
        0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB,
        0xCD, 0xCE, 0xCF,
    }
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        while pos < len(data) and data[pos] == 0xFF:
            pos += 1
        if pos >= len(data):
            break
        marker = data[pos]
        pos += 1
        if marker in {0xD8, 0xD9, 0x01} or 0xD0 <= marker <= 0xD7:
            continue
        if pos + 2 > len(data):
            break
        segment_length = int.from_bytes(data[pos:pos + 2], "big")
        if segment_length < 2 or pos + segment_length > len(data):
            break
        if marker in sof_markers and segment_length >= 7:
            height = int.from_bytes(data[pos + 3:pos + 5], "big")
            width = int.from_bytes(data[pos + 5:pos + 7], "big")
            return width, height
        pos += segment_length
    return None


def _image_metadata_projection(data: bytes) -> dict[str, Any]:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24 and data[12:16] == b"IHDR":
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
        return {
            "kind": "metadata",
            "conversion_class": "R1_SEMANTIC_REVERSIBLE",
            "format_signature": "PNG",
            "width_px": width,
            "height_px": height,
        }
    if data[:3] == b"\xff\xd8\xff":
        dimensions = _jpeg_dimensions(data)
        if not dimensions:
            raise SourceIntakeError("JPEG dimensions could not be read from bounded marker structure")
        width, height = dimensions
        return {
            "kind": "metadata",
            "conversion_class": "R1_SEMANTIC_REVERSIBLE",
            "format_signature": "JPEG",
            "width_px": width,
            "height_px": height,
        }
    if data[:6] in {b"GIF87a", b"GIF89a"} and len(data) >= 10:
        width = int.from_bytes(data[6:8], "little")
        height = int.from_bytes(data[8:10], "little")
        return {
            "kind": "metadata",
            "conversion_class": "R1_SEMANTIC_REVERSIBLE",
            "format_signature": data[:6].decode("ascii"),
            "width_px": width,
            "height_px": height,
        }
    raise SourceIntakeError("image container is not an admitted PNG/JPEG/GIF structure")


def _gltf_structure(value: dict[str, Any], *, container: str, chunks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    nodes = value.get("nodes") if isinstance(value.get("nodes"), list) else []
    meshes = value.get("meshes") if isinstance(value.get("meshes"), list) else []
    scenes = value.get("scenes") if isinstance(value.get("scenes"), list) else []
    materials = value.get("materials") if isinstance(value.get("materials"), list) else []
    buffers = value.get("buffers") if isinstance(value.get("buffers"), list) else []
    images = value.get("images") if isinstance(value.get("images"), list) else []

    external_uris: list[dict[str, Any]] = []
    for family, items in (("buffer", buffers), ("image", images)):
        for index, item in enumerate(items):
            if isinstance(item, dict) and isinstance(item.get("uri"), str):
                external_uris.append({"family": family, "index": index, "uri": item["uri"]})

    return {
        "kind": "structure",
        "conversion_class": "R1_SEMANTIC_REVERSIBLE",
        "container": container,
        "asset": value.get("asset"),
        "scene": value.get("scene"),
        "counts": {
            "scenes": len(scenes),
            "nodes": len(nodes),
            "meshes": len(meshes),
            "materials": len(materials),
            "buffers": len(buffers),
            "images": len(images),
            "accessors": len(value.get("accessors", [])) if isinstance(value.get("accessors"), list) else 0,
            "bufferViews": len(value.get("bufferViews", [])) if isinstance(value.get("bufferViews"), list) else 0,
            "animations": len(value.get("animations", [])) if isinstance(value.get("animations"), list) else 0,
        },
        "nodes": [
            {
                "index": index,
                "name": item.get("name"),
                "mesh": item.get("mesh"),
                "children": item.get("children"),
                "camera": item.get("camera"),
                "skin": item.get("skin"),
            }
            for index, item in enumerate(nodes)
            if isinstance(item, dict)
        ],
        "meshes": [
            {
                "index": index,
                "name": item.get("name"),
                "primitive_count": len(item.get("primitives", [])) if isinstance(item.get("primitives"), list) else 0,
            }
            for index, item in enumerate(meshes)
            if isinstance(item, dict)
        ],
        "external_uris": external_uris,
        "chunks": chunks or [],
    }


def _gltf_projection(data: bytes, extension: str) -> dict[str, Any]:
    if extension == ".gltf":
        text, encoding = _decode_text(data)
        value = json.loads(text)
        if not isinstance(value, dict):
            raise SourceIntakeError("glTF JSON root must be an object")
        projection = _gltf_structure(value, container="gltf-json")
        projection["encoding"] = encoding
        return projection

    if extension != ".glb":
        raise SourceIntakeError("unsupported glTF extension")
    if len(data) < 12 or data[:4] != b"glTF":
        raise SourceIntakeError("invalid GLB header")
    version = int.from_bytes(data[4:8], "little")
    declared_length = int.from_bytes(data[8:12], "little")
    if version != 2:
        raise SourceIntakeError(f"unsupported GLB version: {version}")
    if declared_length != len(data):
        raise SourceIntakeError("GLB declared length does not match source byte length")

    pos = 12
    chunks: list[dict[str, Any]] = []
    json_value: dict[str, Any] | None = None
    while pos + 8 <= len(data):
        chunk_length = int.from_bytes(data[pos:pos + 4], "little")
        chunk_type = data[pos + 4:pos + 8]
        start = pos + 8
        end = start + chunk_length
        if end > len(data):
            raise SourceIntakeError("GLB chunk exceeds declared source length")
        type_name = (
            "JSON" if chunk_type == b"JSON"
            else "BIN" if chunk_type == b"BIN\x00"
            else chunk_type.hex()
        )
        chunks.append({
            "index": len(chunks),
            "type": type_name,
            "offset": start,
            "byte_length": chunk_length,
        })
        if chunk_type == b"JSON" and json_value is None:
            decoded = data[start:end].rstrip(b" \t\r\n\x00").decode("utf-8")
            parsed = json.loads(decoded)
            if not isinstance(parsed, dict):
                raise SourceIntakeError("GLB JSON chunk root must be an object")
            json_value = parsed
        pos = end
    if pos != len(data):
        raise SourceIntakeError("GLB contains trailing partial chunk bytes")
    if json_value is None:
        raise SourceIntakeError("GLB contains no JSON chunk")
    projection = _gltf_structure(json_value, container="glb", chunks=chunks)
    projection["version"] = version
    projection["declared_byte_length"] = declared_length
    return projection


def _step_statements(text: str) -> list[dict[str, Any]]:
    statements: list[dict[str, Any]] = []
    buf: list[str] = []
    in_string = False
    in_comment = False
    line = 1
    start_line = 1
    i = 0
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_comment:
            if ch == "*" and nxt == "/":
                in_comment = False
                i += 2
                continue
            if ch == "\n":
                line += 1
            i += 1
            continue

        if not in_string and ch == "/" and nxt == "*":
            in_comment = True
            i += 2
            continue

        if ch == "'":
            if in_string and nxt == "'":
                buf.extend([ch, nxt])
                i += 2
                continue
            in_string = not in_string
            buf.append(ch)
            i += 1
            continue

        if not buf and not ch.isspace():
            start_line = line

        buf.append(ch)
        if ch == ";" and not in_string:
            raw = "".join(buf).strip()
            if raw:
                statements.append({
                    "index": len(statements),
                    "line_start": start_line,
                    "line_end": line,
                    "raw": raw,
                })
            buf = []
            if len(statements) > _MAX_CAD_ENTITIES + 10000:
                raise SourceIntakeError("STEP statement count exceeds bounded intake limit")

        if ch == "\n":
            line += 1
        i += 1

    if in_string:
        raise SourceIntakeError("STEP source ends inside a quoted string")
    if in_comment:
        raise SourceIntakeError("STEP source ends inside a block comment")
    if "".join(buf).strip():
        raise SourceIntakeError("STEP source contains unterminated statement")
    return statements


def _step_part21_projection(data: bytes) -> dict[str, Any]:
    if len(data) > _MAX_CAD_TEXT_BYTES:
        raise SourceIntakeError("STEP source exceeds bounded structural intake byte limit")
    text, encoding = _decode_text(data)
    upper_prefix = text[:4096].upper()
    if "ISO-10303-21" not in upper_prefix:
        raise SourceIntakeError("STEP Part 21 signature ISO-10303-21 not found")

    statements = _step_statements(text)
    section = None
    header: list[dict[str, Any]] = []
    entities: list[dict[str, Any]] = []
    type_counts: dict[str, int] = {}

    import re
    entity_re = re.compile(r"^#(?P<id>\d+)\s*=\s*(?P<type>[A-Z0-9_]+)\s*\(", re.I)
    header_re = re.compile(r"^(?P<type>[A-Z0-9_]+)\s*\(", re.I)

    for statement in statements:
        raw = statement["raw"]
        token = raw.strip().upper()
        if token == "HEADER;":
            section = "HEADER"
            continue
        if token == "DATA;":
            section = "DATA"
            continue
        if token == "ENDSEC;":
            section = None
            continue
        if token == "END-ISO-10303-21;":
            continue

        if section == "HEADER":
            match = header_re.match(raw)
            header.append({
                **statement,
                "type": match.group("type").upper() if match else None,
            })
            continue

        if section == "DATA":
            match = entity_re.match(raw)
            if not match:
                raise SourceIntakeError(
                    f"unrecognised STEP DATA statement at lines {statement['line_start']}-{statement['line_end']}"
                )
            entity_type = match.group("type").upper()
            entity = {
                **statement,
                "entity_id": int(match.group("id")),
                "entity_type": entity_type,
            }
            entities.append(entity)
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
            if len(entities) > _MAX_CAD_ENTITIES:
                raise SourceIntakeError("STEP entity count exceeds bounded intake limit")

    if not entities:
        raise SourceIntakeError("STEP DATA section contains no entities")

    return {
        "kind": "structure",
        "conversion_class": "R1_SEMANTIC_REVERSIBLE",
        "format": "STEP-Part21",
        "encoding": encoding,
        "header": header,
        "entity_count": len(entities),
        "entity_type_counts": dict(sorted(type_counts.items())),
        "entities": entities,
        "engineering_interpretation_performed": False,
        "brep_validation_performed": False,
        "units_inferred": False,
    }


def _freecad_fcstd_projection(data: bytes) -> dict[str, Any]:
    zf, names = _safe_zip_names(data)
    if "Document.xml" not in names:
        raise SourceIntakeError("FCStd archive has no Document.xml")
    info_by_name = {info.filename: info for info in zf.infolist()}
    members = [
        {
            "name": name,
            "file_size": info_by_name[name].file_size,
            "compressed_size": info_by_name[name].compress_size,
            "crc32": f"{info_by_name[name].CRC:08x}",
            "compress_type": info_by_name[name].compress_type,
        }
        for name in names[:50000]
    ]

    document_bytes = zf.read("Document.xml")
    if len(document_bytes) > _MAX_CAD_TEXT_BYTES:
        raise SourceIntakeError("FCStd Document.xml exceeds bounded structural intake limit")
    root = ET.fromstring(document_bytes)

    objects: list[dict[str, Any]] = []
    object_names: set[str] = set()
    for element in root.iter():
        tag = _local_xml_name(element.tag)
        if tag != "Object":
            continue
        name = element.attrib.get("name") or element.attrib.get("Name")
        obj_type = element.attrib.get("type") or element.attrib.get("Type")
        if not name and not obj_type:
            continue
        record = {
            "index": len(objects),
            "name": name,
            "type": obj_type,
            "attributes": {str(k): str(v) for k, v in sorted(element.attrib.items())},
        }
        objects.append(record)
        if name:
            object_names.add(name)
        if len(objects) > _MAX_CAD_ENTITIES:
            raise SourceIntakeError("FCStd object count exceeds bounded intake limit")

    properties: list[dict[str, Any]] = []
    dependencies: list[dict[str, Any]] = []
    for element in root.iter():
        tag = _local_xml_name(element.tag)
        if tag == "Property":
            properties.append({
                "index": len(properties),
                "name": element.attrib.get("name") or element.attrib.get("Name"),
                "type": element.attrib.get("type") or element.attrib.get("Type"),
                "attributes": {str(k): str(v) for k, v in sorted(element.attrib.items())},
            })
        elif tag in {"ObjectDep", "Dependency", "Link"}:
            dependencies.append({
                "index": len(dependencies),
                "tag": tag,
                "attributes": {str(k): str(v) for k, v in sorted(element.attrib.items())},
            })
        if len(properties) > _MAX_CAD_ENTITIES or len(dependencies) > _MAX_CAD_ENTITIES:
            raise SourceIntakeError("FCStd property/dependency count exceeds bounded intake limit")

    tag_counts: dict[str, int] = {}
    for element in root.iter():
        tag = _local_xml_name(element.tag)
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return {
        "kind": "structure",
        "conversion_class": "R1_SEMANTIC_REVERSIBLE",
        "format": "FreeCAD-FCStd",
        "archive_member_count": len(names),
        "members": members,
        "document_root_tag": _local_xml_name(root.tag),
        "document_tag_counts": dict(sorted(tag_counts.items())),
        "object_count": len(objects),
        "objects": objects,
        "property_count": len(properties),
        "properties": properties,
        "dependency_records": dependencies,
        "referenced_object_names": sorted(object_names),
        "shape_payload_interpreted": False,
        "brep_validation_performed": False,
        "engineering_geometry_inferred": False,
    }


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
        elif adapter_id == "svg-xml-stdlib-v0.1":
            projections = [_svg_projection(raw[:_MAX_TEXT_BYTES])]
        elif adapter_id == "image-metadata-stdlib-v0.1":
            projections = [_image_metadata_projection(raw)]
        elif adapter_id == "gltf-stdlib-v0.1":
            projections = [_gltf_projection(raw, extension)]
        elif adapter_id == "step-part21-stdlib-v0.1":
            projections = [_step_part21_projection(raw)]
        elif adapter_id == "freecad-fcstd-stdlib-v0.1":
            projections = [_freecad_fcstd_projection(raw)]
        elif adapter_id == "pdf-pypdf-v0.1":
            projections = [_reference_projection(family, raw)]
            unresolved.append("registered_pdf_capability_not_bound_in_generic_source_intake")
        elif adapter_id == "obj-mesh-stdlib-v0.1":
            projections = [_obj_projection(raw)]
        elif adapter_id == "stl-mesh-stdlib-v0.1":
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
        "svg-xml-stdlib-v0.1": "STRUCTURE_PRESERVED",
        "image-metadata-stdlib-v0.1": "LOSSLESS_FOR_DECLARED_FIELDS",
        "gltf-stdlib-v0.1": "STRUCTURE_PRESERVED",
        "step-part21-stdlib-v0.1": "STRUCTURE_PRESERVED",
        "freecad-fcstd-stdlib-v0.1": "STRUCTURE_PRESERVED",
        "obj-mesh-stdlib-v0.1": "STRUCTURE_PRESERVED",
        "stl-mesh-stdlib-v0.1": "STRUCTURE_PRESERVED",
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
