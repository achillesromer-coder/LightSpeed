"""Build source-bounded Type 1 SVG review packages for the first migration trio.

The drawings are deterministic technical projections of the committed review
meshes. They preserve evidence class and unknowns and are not engineering,
manufacturing, certification, site, or physical-validation authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape

import numpy as np
import trimesh


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_ROOT = REPO_ROOT / "assets" / "models"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "assets" / "type1-svg"
DEFAULT_MANIFEST = REPO_ROOT / "data" / "digital-twin" / "generated_type1_svg_manifest_v1.json"
ASSET_CONTRACT = REPO_ROOT / "data" / "digital-twin" / "complete_digital_asset_manifest_2026-09-12.json"
TYPE1_CONTRACT = REPO_ROOT / "data" / "digital-twin" / "type1_svg_contract_v1.json"
MESH_RECEIPT = REPO_ROOT / "data" / "digital-twin" / "generated_mesh_manifest_v1.json"
MIGRATION_TRIO = ("watchtower", "m1_elevated_bypass", "romer_spaceport")
LAYERS = (
    "L00-SHEET", "L10-CONTEXT", "L20-AUTH-GEOMETRY", "L21-DERIVED-GEOMETRY",
    "L22-PROVISIONAL-GEOMETRY", "L30-HIDDEN", "L31-CENTRE-DATUM", "L40-SECTIONS",
    "L50-DIMENSIONS", "L60-MATERIALS", "L70-INTERFACES", "L75-SENSORS",
    "L80-SIMULATION", "L90-EVIDENCE", "L91-UNKNOWNS", "L95-ANNOTATIONS", "L99-CLAIM-GATE",
)
SHEETS = {
    "T1-00": "Cover / general arrangement",
    "T1-01": "Geometry / orthographic / sections",
    "T1-02": "Assembly / exploded / parts",
    "T1-03": "Interfaces / services / functional networks",
    "T1-04": "Materials / layer stacks",
    "T1-05": "Simulation / operating envelope",
    "T1-06": "Telemetry / instrumentation / living-state bindings",
    "T1-07": "Evidence / verification / unknowns / claim boundary",
}
VIEWS = {
    "PLAN": ([0, 0, 1], [0, 1, 0]),
    "FRONT": ([0, -1, 0], [0, 0, 1]),
    "RIGHT": ([1, 0, 0], [0, 0, 1]),
    "ISOMETRIC": ([1, -1, 1], [0, 0, 1]),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_path(path):
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def load_contracts():
    assets = json.loads(ASSET_CONTRACT.read_text(encoding="utf-8"))["assets"]
    migration = json.loads(TYPE1_CONTRACT.read_text(encoding="utf-8"))["migration"]
    meshes = json.loads(MESH_RECEIPT.read_text(encoding="utf-8"))["assets"]
    return (
        {item["twin_id"]: item for item in assets},
        {item["twin_id"]: item for item in migration},
        {item["twin_id"]: item for item in meshes},
    )


def projection_basis(direction, up_hint):
    direction = np.asarray(direction, dtype=float)
    direction /= np.linalg.norm(direction)
    up_hint = np.asarray(up_hint, dtype=float)
    right = np.cross(up_hint, direction)
    right /= np.linalg.norm(right)
    up = np.cross(direction, right)
    up /= np.linalg.norm(up)
    return right, up


def svg_geometry(mesh, view_name, box, object_prefix):
    direction, up_hint = VIEWS[view_name]
    right, up = projection_basis(direction, up_hint)
    vertices = np.asarray(mesh.vertices)
    centred = vertices - vertices.mean(axis=0)
    points = np.column_stack((centred @ right, centred @ up))
    mins, maxs = points.min(axis=0), points.max(axis=0)
    span = np.maximum(maxs - mins, 1e-9)
    x0, y0, width, height = box
    scale = min((width - 30) / span[0], (height - 50) / span[1])
    screen = (points - (mins + maxs) / 2) * np.array([scale, -scale]) + np.array([x0 + width / 2, y0 + height / 2 + 10])
    lines = [f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" class="viewbox"/>', f'<text x="{x0 + 12}" y="{y0 + 22}" class="label">{view_name}</text>']
    for index, (start, end) in enumerate(np.asarray(mesh.edges_unique)):
        a, b = screen[start], screen[end]
        lines.append(
            f'<line id="{object_prefix}-edge-{index:04d}" data-feature-id="EDGE-{index:04d}" '
            f'x1="{a[0]:.3f}" y1="{a[1]:.3f}" x2="{b[0]:.3f}" y2="{b[1]:.3f}" class="geometry"/>'
        )
    return lines


def text_lines(x, y, title, body, width=86):
    words = body.split()
    lines, current = [], []
    for word in words:
        if len(" ".join(current + [word])) > width and current:
            lines.append(" ".join(current)); current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    output = [f'<text x="{x}" y="{y}" class="section-title">{escape(title)}</text>']
    for index, line in enumerate(lines):
        output.append(f'<text x="{x}" y="{y + 22 + index * 18}" class="body">{escape(line)}</text>')
    return output


def render_sheet(twin_id, sheet_id, mesh, asset, migration, mesh_receipt):
    drawing_id = f"{twin_id.upper()}-{sheet_id}"
    representation = asset["representation_class"]
    geometry_layer = "L21-DERIVED-GEOMETRY" if representation == "SOURCE_DERIVED_GEOMETRY" else "L22-PROVISIONAL-GEOMETRY"
    extents = [float(value) for value in mesh.extents]
    metadata = {
        "twin_id": twin_id,
        "drawing_id": drawing_id,
        "sheet_id": sheet_id,
        "purpose": SHEETS[sheet_id],
        "representation_class": representation,
        "source_obj": mesh_receipt["file"],
        "source_obj_sha256": mesh_receipt["sha256"],
        "units": "m",
        "extents_m": extents,
        "next_gate": migration["next_gate"],
        "release_state": "REVIEW_ONLY_NOT_PUBLICLY_RELEASED",
    }
    content = {layer: [] for layer in LAYERS}
    content["L00-SHEET"] += [
        '<rect x="18" y="18" width="1564" height="964" class="sheet"/>',
        f'<text x="48" y="62" class="title">TYPE 1 SVG · {escape(twin_id.replace("_", " ").upper())} · {sheet_id}</text>',
        f'<text x="48" y="88" class="subtitle">{escape(SHEETS[sheet_id])}</text>',
        '<line x1="18" y1="900" x2="1582" y2="900" class="border"/>',
        f'<text x="48" y="930" class="body">Drawing ID: {drawing_id} · Units: m · Scale: FIT · Coordinate frame: LOCAL REVIEW</text>',
        f'<text x="48" y="954" class="body">Representation: {representation} · Revision: 1 · Release: REVIEW ONLY</text>',
    ]
    source_hash = mesh_receipt["sha256"]
    content["L10-CONTEXT"] += text_lines(48, 130, "SOURCE CONTEXT", f"Projection source {mesh_receipt['file']} SHA-256 {source_hash[:32]} {source_hash[32:]}. Native CAD/BREP/owning Drive data remains authority.", width=50)
    views = ("PLAN", "FRONT", "RIGHT") if sheet_id in {"T1-00", "T1-01"} else ("ISOMETRIC",)
    boxes = [(48, 250, 480, 420), (560, 250, 480, 420), (1072, 250, 480, 420)] if len(views) == 3 else [(430, 230, 740, 500)]
    for view, view_box in zip(views, boxes, strict=True):
        content[geometry_layer] += svg_geometry(mesh, view, view_box, f"{drawing_id}-{view}")
    content["L31-CENTRE-DATUM"] += [
        '<line id="DATUM-X" x1="80" y1="700" x2="300" y2="700" class="datum"/>',
        '<line id="DATUM-Z" x1="80" y1="700" x2="80" y2="520" class="datum"/>',
        '<text x="306" y="706" class="label">+X</text><text x="66" y="510" class="label">+Z</text>',
    ]
    content["L50-DIMENSIONS"] += text_lines(48, 710, "BOUNDING EXTENTS", f"X {extents[0]:.6g} m · Y {extents[1]:.6g} m · Z {extents[2]:.6g} m. Bounding dimensions are derived from the committed review mesh, not as-built tolerance authority.", width=63)
    content["L60-MATERIALS"] += text_lines(560, 710, "MATERIAL STATE", "Material identity, grade, finish, thickness, batch and physical qualification remain UNKNOWN unless separately bound in the owning canon.", width=63)
    content["L70-INTERFACES"] += text_lines(1072, 710, "INTERFACE STATE", "Critical physical, electrical, structural, fluid, control and ecological interfaces remain evidence-gated; no connection capacity is inferred from geometry.", width=63)
    content["L75-SENSORS"] += text_lines(48, 808, "TELEMETRY STATE", "No LIVE state is asserted. Sensor identity, physical location, calibration, raw dataset hash, uncertainty and last-valid observation remain required.", width=86)
    content["L80-SIMULATION"] += text_lines(820, 808, "SIMULATION STATE", "No solver result or measured performance is promoted by this projection. Reproducible inputs, boundary conditions, solver version, residuals and output hashes remain required.", width=86)
    content["L90-EVIDENCE"] += text_lines(440, 130, "EVIDENCE CLASS", f"{representation}. Source mesh hash is bound. Current migration priority {migration['priority']} and fidelity {migration['fidelity']}.", width=50)
    content["L91-UNKNOWNS"] += text_lines(800, 130, "OPEN GATE", migration["next_gate"], width=50)
    content["L95-ANNOTATIONS"] += text_lines(1160, 130, "SHEET LIMIT", "This is a machine-addressable review projection. Blank or gated domains are deliberate and must not be aesthetically filled with invented values.", width=50)
    content["L99-CLAIM-GATE"] += [
        '<rect x="18" y="962" width="1564" height="20" class="gate"/>',
        '<text x="800" y="977" text-anchor="middle" class="gate-text">NOT ENGINEERING AUTHORITY · NOT PHYSICAL VALIDATION · NOT PUBLICLY RELEASED</text>',
    ]
    groups = "\n".join(f'<g id="{layer}" data-layer="{layer}">\n' + "\n".join(content[layer]) + "\n</g>" for layer in LAYERS)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="auto" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMin meet" data-twin-id="{twin_id}" data-drawing-id="{drawing_id}" data-representation-class="{representation}" data-release-state="REVIEW_ONLY_NOT_PUBLICLY_RELEASED">
<metadata>{escape(json.dumps(metadata, sort_keys=True, separators=(",", ":")))}</metadata>
<style>.sheet{{fill:#fff;stroke:#111;stroke-width:2}}.border,.viewbox{{fill:none;stroke:#555;stroke-width:1}}.geometry{{stroke:#111;stroke-width:1;fill:none;vector-effect:non-scaling-stroke}}.datum{{stroke:#555;stroke-width:1;stroke-dasharray:8 5}}.title{{font:700 24px system-ui,sans-serif}}.subtitle{{font:16px system-ui,sans-serif;fill:#333}}.section-title{{font:700 13px system-ui,sans-serif}}.body,.label{{font:12px ui-monospace,monospace;fill:#222}}.gate{{fill:#111}}.gate-text{{font:700 12px system-ui,sans-serif;fill:#fff;letter-spacing:1px}}</style>
{groups}
</svg>
'''


def generate_packages(model_root, output_root, manifest_output):
    assets, migration, meshes = load_contracts()
    records = []
    for twin_id in MIGRATION_TRIO:
        model_path = model_root / f"{twin_id}.obj"
        mesh = trimesh.load_mesh(model_path, process=False)
        for sheet_id in SHEETS:
            output = output_root / twin_id / f"{sheet_id}.svg"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(render_sheet(twin_id, sheet_id, mesh, assets[twin_id], migration[twin_id], meshes[twin_id]), encoding="utf-8", newline="\n")
            records.append({
                "twin_id": twin_id,
                "sheet_id": sheet_id,
                "file": display_path(output),
                "representation_class": assets[twin_id]["representation_class"],
                "source_obj_sha256": meshes[twin_id]["sha256"],
                "size_bytes": output.stat().st_size,
                "sha256": sha256(output),
                "release_state": "REVIEW_ONLY_NOT_PUBLICLY_RELEASED",
            })
    receipt = {
        "schema": "type1_svg_generated_package_receipt_v1",
        "generator": "tools/digital-twin/build_type1_svg_packages.py",
        "twins": list(MIGRATION_TRIO),
        "required_layers": list(LAYERS),
        "sheets": list(SHEETS),
        "assets": records,
    }
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    return records


def parse_args(arguments: Iterable[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-root", type=Path, default=DEFAULT_MODEL_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--manifest-output", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args(arguments)


def main(arguments: Iterable[str] | None = None):
    args = parse_args(arguments)
    records = generate_packages(args.model_root, args.output_root, args.manifest_output)
    if len(records) != 24:
        raise SystemExit(f"expected 24 SVG sheets, generated {len(records)}")
    print(json.dumps({"generated": len(records), "twins": list(MIGRATION_TRIO), "manifest": display_path(args.manifest_output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
