"""Build evidence-ceiling-aware Type 1 SVG review packages for all registered twins.

The first three packages preserve their source-derived/partial states. The
remaining thirteen are explicit E-class interaction-proxy review shells. All
drawings preserve evidence class and unknowns and are not engineering,
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
REQUIREMENTS = REPO_ROOT / "tools" / "digital-twin" / "requirements.txt"
CI_LOCK = REPO_ROOT / "tools" / "digital-twin" / "requirements-ci-linux-py311.lock"
PACKAGE_POLICIES = {
    "SOURCE_DERIVED_GEOMETRY": {
        "package_kind": "SOURCE_BOUNDED_REVIEW",
        "package_state": "SOURCE_DERIVED_REVIEW_ONLY",
        "package_evidence_ceiling": "B",
        "source_binding_state": "COMMITTED_DERIVATION_RECEIPT",
        "dimension_authority": "DERIVED_MODEL_ENVELOPE_ONLY",
        "geometry_layer": "L21-DERIVED-GEOMETRY",
    },
    "SOURCE_DERIVED_PARTIAL": {
        "package_kind": "PARTIAL_SOURCE_REVIEW",
        "package_state": "PARTIAL_SOURCE_PROVISIONAL_REVIEW",
        "package_evidence_ceiling": "MIXED_B_C",
        "source_binding_state": "PARTIAL_DERIVATION_RECEIPT",
        "dimension_authority": "PARTIAL_DERIVED_MODEL_ENVELOPE_ONLY",
        "geometry_layer": "L22-PROVISIONAL-GEOMETRY",
    },
    "INTERACTION_PROXY": {
        "package_kind": "INTERACTION_PROXY_REVIEW_SHELL",
        "package_state": "E_CLASS_INCOMPLETE_REVIEW_SHELL",
        "package_evidence_ceiling": "E",
        "source_binding_state": "NONE_PROXY_ONLY",
        "dimension_authority": "NONE",
        "geometry_layer": "L22-PROVISIONAL-GEOMETRY",
    },
}
DISPLAY_NAMES = {
    "watchtower": "WatchTower Living Twin",
    "m1_elevated_bypass": "M1 Elevated Bypass",
    "romer_spaceport": "Römer Spaceport Twin",
    "mark_iii": "Mark III",
    "luke_family": "Luke / Luke II / Apostle",
    "free_flow_solenoid_stack": "Free Flow Solenoid Stack",
    "solar_hull": "Solar Hull",
    "free_flow_batteries": "Free Flow Batteries",
    "free_flow_capacitors": "Free Flow Capacitors",
    "rfs_emff": "RFS & EMFF",
    "mark_1p": "Mark 1P",
    "mark_i": "Mark I Chamber",
    "maglev_luke_iv": "Mag-Lev / Luke IV",
    "embedded_bio_blocks": "Embedded / Bio-Blocks",
    "second_cycle": "Second Cycle",
    "intersol": "InterSol Facility Twin",
}
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


def normalized_text_sha256(path):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
        [item["twin_id"] for item in sorted(migration, key=lambda item: int(item["priority"][1:]))],
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


def svg_geometry(mesh, view_name, box, object_prefix, feature_addressable=True):
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
    if not feature_addressable:
        segments = []
        for start, end in np.asarray(mesh.edges_unique):
            a, b = screen[start], screen[end]
            segments.append(f"M {a[0]:.3f} {a[1]:.3f} L {b[0]:.3f} {b[1]:.3f}")
        lines.append(
            f'<path id="{object_prefix}-proxy-wireframe" data-feature-class="INTERACTION_PROXY_WIREFRAME" '
            f'd="{" ".join(segments)}" class="geometry"/>'
        )
        return lines
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
    policy = PACKAGE_POLICIES[representation]
    geometry_layer = policy["geometry_layer"]
    is_proxy = representation == "INTERACTION_PROXY"
    domain_unbound = is_proxy and sheet_id in {"T1-02", "T1-03", "T1-04", "T1-05", "T1-06"}
    extents = [float(value) for value in mesh.extents]
    metadata = {
        "twin_id": twin_id,
        "drawing_id": drawing_id,
        "sheet_id": sheet_id,
        "purpose": SHEETS[sheet_id],
        "representation_class": representation,
        "package_kind": policy["package_kind"],
        "package_state": policy["package_state"],
        "package_evidence_ceiling": policy["package_evidence_ceiling"],
        "source_binding_state": policy["source_binding_state"],
        "dimension_authority": policy["dimension_authority"],
        "feature_addressability": "WHOLE_PROXY_ONLY" if is_proxy else "EDGE_LEVEL_DERIVED",
        "type1_complete": False,
        "release_eligible": False,
        "projection_input_obj": mesh_receipt["file"],
        "projection_input_obj_sha256": mesh_receipt["sha256"],
        "units": "m",
        "sheet_domain_state": "UNBOUND" if domain_unbound else "REVIEW_ONLY",
        "next_gate": migration["next_gate"],
        "release_state": "REVIEW_ONLY_NOT_PUBLICLY_RELEASED",
    }
    metadata["proxy_model_extents_m" if is_proxy else "derived_model_extents_m"] = extents
    content = {layer: [] for layer in LAYERS}
    domain_suffix = " · DOMAIN UNBOUND" if domain_unbound else ""
    content["L00-SHEET"] += [
        '<rect x="18" y="18" width="1564" height="964" class="sheet"/>',
        f'<text x="48" y="62" class="title">TYPE 1 SVG · {escape(DISPLAY_NAMES[twin_id].upper())} · {sheet_id}</text>',
        f'<text x="48" y="88" class="subtitle">{escape(SHEETS[sheet_id])}{domain_suffix}</text>',
        '<line x1="18" y1="900" x2="1582" y2="900" class="border"/>',
        f'<text x="48" y="930" class="body">Drawing ID: {drawing_id} · Units: m · Scale: FIT · Coordinate frame: LOCAL REVIEW</text>',
        f'<text x="48" y="954" class="body">Representation: {representation} · Revision: 1 · Release: REVIEW ONLY</text>',
    ]
    source_hash = mesh_receipt["sha256"]
    if is_proxy:
        context_title = "PROJECTION INPUT — NOT SOURCE AUTHORITY"
        context_body = f"Interaction-proxy input {mesh_receipt['file']} SHA-256 {source_hash[:32]} {source_hash[32:]}. The hash identifies only this review proxy; source binding is NONE_PROXY_ONLY."
    elif representation == "SOURCE_DERIVED_PARTIAL":
        context_title = "PARTIAL SOURCE CONTEXT"
        context_body = f"Partial derived input {mesh_receipt['file']} SHA-256 {source_hash[:32]} {source_hash[32:]}. Native CAD/BREP/owning Drive data remains authority; unbound regions stay provisional."
    else:
        context_title = "SOURCE CONTEXT"
        context_body = f"Projection input {mesh_receipt['file']} SHA-256 {source_hash[:32]} {source_hash[32:]}. Native CAD/BREP/owning Drive data remains authority."
    content["L10-CONTEXT"] += text_lines(48, 130, context_title, context_body, width=50)
    views = ("PLAN", "FRONT", "RIGHT") if sheet_id in {"T1-00", "T1-01"} else ("ISOMETRIC",)
    boxes = [(48, 250, 480, 420), (560, 250, 480, 420), (1072, 250, 480, 420)] if len(views) == 3 else [(430, 230, 740, 450)]
    for view, view_box in zip(views, boxes, strict=True):
        content[geometry_layer] += svg_geometry(mesh, view, view_box, f"{drawing_id}-{view}", feature_addressable=not is_proxy)
    content["L31-CENTRE-DATUM"] += [
        '<line id="DATUM-X" x1="80" y1="700" x2="300" y2="700" class="datum"/>',
        '<line id="DATUM-Z" x1="80" y1="700" x2="80" y2="520" class="datum"/>',
        '<text x="306" y="706" class="label">+X</text><text x="66" y="510" class="label">+Z</text>',
    ]
    if is_proxy:
        dimension_title = "E-CLASS PROXY MODEL ENVELOPE"
        dimension_body = f"X {extents[0]:.6g} m · Y {extents[1]:.6g} m · Z {extents[2]:.6g} m. Values describe only the interaction proxy model; dimension authority is NONE."
    elif representation == "SOURCE_DERIVED_PARTIAL":
        dimension_title = "PARTIAL DERIVED MODEL ENVELOPE"
        dimension_body = f"X {extents[0]:.6g} m · Y {extents[1]:.6g} m · Z {extents[2]:.6g} m. Values describe the partial review model, not an as-built or site-authoritative envelope."
    else:
        dimension_title = "DERIVED MODEL ENVELOPE"
        dimension_body = f"X {extents[0]:.6g} m · Y {extents[1]:.6g} m · Z {extents[2]:.6g} m. Values derive from the committed review mesh, not as-built tolerance authority."
    content["L50-DIMENSIONS"] += text_lines(48, 710, dimension_title, dimension_body, width=63)
    content["L60-MATERIALS"] += text_lines(560, 710, "MATERIAL STATE", "Material identity, grade, finish, thickness, batch and physical qualification remain UNKNOWN unless separately bound in the owning canon.", width=63)
    content["L70-INTERFACES"] += text_lines(1072, 710, "INTERFACE STATE", "Critical physical, electrical, structural, fluid, control and ecological interfaces remain evidence-gated; no connection capacity is inferred from geometry.", width=63)
    content["L75-SENSORS"] += text_lines(48, 808, "TELEMETRY STATE", "No LIVE state is asserted. Sensor identity, physical location, calibration, raw dataset hash, uncertainty and last-valid observation remain required.", width=86)
    content["L80-SIMULATION"] += text_lines(820, 808, "SIMULATION STATE", "No solver result or measured performance is promoted by this projection. Reproducible inputs, boundary conditions, solver version, residuals and output hashes remain required.", width=86)
    evidence_body = (
        f"{representation}. Projection input hash is bound; source binding remains {policy['source_binding_state']}. "
        f"Evidence ceiling {policy['package_evidence_ceiling']}; migration priority {migration['priority']} and fidelity {migration['fidelity']}."
    )
    content["L90-EVIDENCE"] += text_lines(440, 130, "EVIDENCE CLASS", evidence_body, width=50)
    content["L91-UNKNOWNS"] += text_lines(800, 130, "OPEN GATE", migration["next_gate"], width=50)
    content["L95-ANNOTATIONS"] += text_lines(1160, 130, "SHEET LIMIT", "This is a machine-addressable review projection. Blank or gated domains are deliberate and must not be aesthetically filled with invented values.", width=50)
    if is_proxy:
        content["L99-CLAIM-GATE"].append('<text x="800" y="112" text-anchor="middle" class="proxy-watermark">INTERACTION PROXY / INCOMPLETE REVIEW SHELL</text>')
    content["L99-CLAIM-GATE"] += [
        '<rect x="18" y="962" width="1564" height="20" class="gate"/>',
        '<text x="800" y="977" text-anchor="middle" class="gate-text">NOT ENGINEERING AUTHORITY · NOT PHYSICAL VALIDATION · NOT PUBLICLY RELEASED</text>',
    ]
    groups = "\n".join(f'<g id="{layer}" data-layer="{layer}">\n' + "\n".join(content[layer]) + "\n</g>" for layer in LAYERS)
    title_id = f"{drawing_id}-title"
    desc_id = f"{drawing_id}-desc"
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="auto" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMin meet" role="img" aria-labelledby="{title_id} {desc_id}" data-twin-id="{twin_id}" data-drawing-id="{drawing_id}" data-representation-class="{representation}" data-package-kind="{policy['package_kind']}" data-evidence-ceiling="{policy['package_evidence_ceiling']}" data-source-binding-state="{policy['source_binding_state']}" data-dimension-authority="{policy['dimension_authority']}" data-type1-complete="false" data-release-eligible="false" data-release-state="REVIEW_ONLY_NOT_PUBLICLY_RELEASED">
<title id="{title_id}">{escape(DISPLAY_NAMES[twin_id])} {sheet_id} Type 1 review sheet</title>
<desc id="{desc_id}">{escape(SHEETS[sheet_id])}. {escape(policy['package_state'])}. Review only; not engineering authority, physical validation or public release.</desc>
<metadata>{escape(json.dumps(metadata, sort_keys=True, separators=(",", ":")))}</metadata>
<style>.sheet{{fill:#fff;stroke:#111;stroke-width:2}}.border,.viewbox{{fill:none;stroke:#555;stroke-width:1}}.geometry{{stroke:#111;stroke-width:1;fill:none;vector-effect:non-scaling-stroke}}.datum{{stroke:#555;stroke-width:1;stroke-dasharray:8 5}}.title{{font:700 24px system-ui,sans-serif}}.subtitle{{font:16px system-ui,sans-serif;fill:#333}}.section-title{{font:700 13px system-ui,sans-serif}}.body,.label{{font:12px ui-monospace,monospace;fill:#222}}.proxy-watermark{{font:700 12px system-ui,sans-serif;fill:#111;letter-spacing:1.5px}}.gate{{fill:#111}}.gate-text{{font:700 12px system-ui,sans-serif;fill:#fff;letter-spacing:1px}}</style>
{groups}
</svg>
'''


def render_gallery(package_twins, assets, migration):
    cards = []
    for twin_id in package_twins:
        policy = PACKAGE_POLICIES[assets[twin_id]["representation_class"]]
        links = "".join(
            f'<a href="{twin_id}/{sheet_id}.svg">{sheet_id}</a>'
            for sheet_id in SHEETS
        )
        cards.append(
            f'''<article data-twin-id="{twin_id}">
<p class="priority">{escape(migration[twin_id]["priority"])} · {escape(policy["package_evidence_ceiling"])}</p>
<h2>{escape(DISPLAY_NAMES[twin_id])}</h2>
<p>{escape(policy["package_kind"])} · {escape(policy["source_binding_state"])}</p>
<nav aria-label="{escape(twin_id)} Type 1 sheets">{links}</nav>
<p><a href="../models/{twin_id}.obj">OBJ review input</a> <a href="../previews/{twin_id}_six_view.png">Six-view PNG</a></p>
</article>'''
        )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'"><title>Type 1 SVG package gallery</title><style>:root{{color-scheme:dark}}*{{box-sizing:border-box}}body{{margin:0;background:#071014;color:#eef7f7;font:15px/1.5 system-ui,sans-serif}}header,main,footer{{padding:24px max(18px,4vw)}}header,footer{{border-block:1px solid #29424b}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:12px}}article{{border:1px solid #29424b;border-radius:12px;padding:16px;background:#0e1b21;break-inside:avoid}}h1,h2{{margin:.2em 0}}p{{color:#c5d7da}}.priority{{color:#70d8d0;font-weight:700}}nav{{display:flex;flex-wrap:wrap;gap:7px}}a{{color:#eef7f7;border:1px solid #48616a;border-radius:7px;padding:6px 8px;text-decoration:none}}a:focus-visible{{outline:3px solid #70d8d0;outline-offset:2px}}@media print{{:root{{color-scheme:light}}body,article{{background:#fff;color:#000}}p,.priority,a{{color:#000}}a{{text-decoration:underline}}}}</style></head><body><header><h1>Type 1 SVG package gallery</h1><p>128 deterministic review sheets across 16 twins. Package and evidence ceilings remain explicit; no sheet is engineering authority, physical validation or public release.</p></header><main><div class="grid">{"".join(cards)}</div></main><footer>REVIEW ONLY · TYPE1 COMPLETE FALSE · RELEASE ELIGIBLE FALSE</footer></body></html>
'''


def generate_packages(model_root, output_root, manifest_output):
    assets, migration, meshes, package_twins = load_contracts()
    records = []
    for twin_id in package_twins:
        model_path = model_root / f"{twin_id}.obj"
        mesh = trimesh.load_mesh(model_path, process=False)
        policy = PACKAGE_POLICIES[assets[twin_id]["representation_class"]]
        for sheet_id in SHEETS:
            output = output_root / twin_id / f"{sheet_id}.svg"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(render_sheet(twin_id, sheet_id, mesh, assets[twin_id], migration[twin_id], meshes[twin_id]), encoding="utf-8", newline="\n")
            records.append({
                "twin_id": twin_id,
                "sheet_id": sheet_id,
                "file": display_path(output),
                "representation_class": assets[twin_id]["representation_class"],
                "package_kind": policy["package_kind"],
                "package_state": policy["package_state"],
                "package_evidence_ceiling": policy["package_evidence_ceiling"],
                "source_binding_state": policy["source_binding_state"],
                "dimension_authority": policy["dimension_authority"],
                "type1_complete": False,
                "release_eligible": False,
                "projection_input_obj_sha256": meshes[twin_id]["sha256"],
                "size_bytes": output.stat().st_size,
                "sha256": sha256(output),
                "release_state": "REVIEW_ONLY_NOT_PUBLICLY_RELEASED",
            })
    gallery_path = output_root / "index.html"
    gallery_path.write_text(render_gallery(package_twins, assets, migration), encoding="utf-8", newline="\n")
    receipt = {
        "schema": "type1_svg_generated_package_receipt_v2",
        "generator": {
            "file": display_path(Path(__file__)),
            "normalized_lf_sha256": normalized_text_sha256(Path(__file__)),
        },
        "dependency_versions": {
            "numpy": np.__version__,
            "trimesh": trimesh.__version__,
        },
        "input_receipts": [
            {"file": display_path(path), "normalized_lf_sha256": normalized_text_sha256(path)}
            for path in (ASSET_CONTRACT, TYPE1_CONTRACT, MESH_RECEIPT)
        ],
        "environment_receipts": [
            {"file": display_path(path), "normalized_lf_sha256": normalized_text_sha256(path)}
            for path in (REQUIREMENTS, CI_LOCK)
        ],
        "twins": package_twins,
        "required_layers": list(LAYERS),
        "sheets": list(SHEETS),
        "package_count": len(package_twins),
        "asset_count": len(records),
        "gallery": {
            "file": display_path(gallery_path),
            "size_bytes": gallery_path.stat().st_size,
            "sha256": sha256(gallery_path),
        },
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
    expected = 16 * len(SHEETS)
    if len(records) != expected:
        raise SystemExit(f"expected {expected} SVG sheets, generated {len(records)}")
    print(json.dumps({"generated": len(records), "packages": 16, "manifest": display_path(args.manifest_output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
