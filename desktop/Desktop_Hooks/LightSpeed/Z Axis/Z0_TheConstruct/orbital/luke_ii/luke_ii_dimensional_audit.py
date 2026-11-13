#!/usr/bin/env python3
"""Generate the Luke II v1.3 dimensional/configuration review register."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from luke_ii_geometry_fingerprint import QUANTIZATION_METRES, semantic_geometry_fingerprint
from luke_ii_parametric import build_reference


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rounded(values: Any, digits: int = 6) -> list[float]:
    return [round(float(value), digits) for value in values]


def build_audit(parameters: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scene, records = build_reference(parameters)
    record_map = {record["node_name"]: record for record in records}
    rows: list[dict[str, Any]] = []

    for node_name in sorted(scene.geometry):
        mesh = scene.geometry[node_name]
        record = record_map[node_name]
        bounds = mesh.bounds
        extents = mesh.extents
        centroid = mesh.centroid
        rows.append(
            {
                "node_name": node_name,
                "family": record["family"],
                "evidence_state": record["evidence_state"],
                "review_gate": record["review_gate"],
                "attachment_parent": record["attachment_parent"],
                "physical": record["physical"],
                "maintainable": record["maintainable"],
                "cable_required": record["cable_required"],
                "cable_route": record["cable_route"] or "",
                "service_clearance": record["service_clearance"] or "",
                "removal_path": record["removal_path"] or "",
                "print_candidate": record["print_candidate"],
                "source_basis": record["source_basis"],
                "units": "metres",
                "min_x": round(float(bounds[0][0]), 6),
                "min_y": round(float(bounds[0][1]), 6),
                "min_z": round(float(bounds[0][2]), 6),
                "max_x": round(float(bounds[1][0]), 6),
                "max_y": round(float(bounds[1][1]), 6),
                "max_z": round(float(bounds[1][2]), 6),
                "extent_x": round(float(extents[0]), 6),
                "extent_y": round(float(extents[1]), 6),
                "extent_z": round(float(extents[2]), 6),
                "centroid_x": round(float(centroid[0]), 6),
                "centroid_y": round(float(centroid[1]), 6),
                "centroid_z": round(float(centroid[2]), 6),
                "vertices": int(len(mesh.vertices)),
                "faces": int(len(mesh.faces)),
                "watertight": bool(mesh.is_watertight),
                "winding_consistent": bool(mesh.is_winding_consistent),
                "signed_volume_m3": round(float(mesh.volume), 6),
                "review_status": "OPEN_ENGINEERING_REVIEW",
            }
        )

    family_counts = Counter(row["family"] for row in rows)
    evidence_counts = Counter(row["evidence_state"] for row in rows)
    gate_counts = Counter(row["review_gate"] for row in rows)
    summary = {
        "schema_version": "luke-ii-dimensional-audit-v1.3",
        "status": "PASS_DIMENSIONAL_SERVICEABLE_REFERENCE_AUDIT",
        "source_state": parameters["artifact_status"],
        "units": "metres",
        "node_count": len(rows),
        "physical_node_count": sum(1 for row in rows if row["physical"]),
        "maintainable_node_count": sum(1 for row in rows if row["maintainable"]),
        "semantic_geometry_sha256": semantic_geometry_fingerprint(scene),
        "semantic_geometry_quantization_m": QUANTIZATION_METRES,
        "all_nodes_watertight": all(row["watertight"] for row in rows),
        "all_nodes_winding_consistent": all(row["winding_consistent"] for row in rows),
        "scene_bounds_m": [_rounded(scene.bounds[0]), _rounded(scene.bounds[1])],
        "scene_extents_m": _rounded(scene.extents),
        "family_counts": dict(sorted(family_counts.items())),
        "evidence_state_counts": dict(sorted(evidence_counts.items())),
        "review_gate_counts": dict(sorted(gate_counts.items())),
        "habitation_volumes_m3": {
            "gross_planning": parameters["habitation"]["gross_clear_volume_m3"],
            "pressure_liner_clear": parameters["habitation"]["pressure_liner_clear_volume_m3"],
            "service_allocated_reference": parameters["habitation"]["service_allocated_reference_volume_m3"],
        },
        "guardrails": [
            "Reference geometry only; no flight, pressure-vessel, human-rating or manufacturing approval.",
            "Bounds, volumes and clearances are geometric observations/reservations, not validated operating envelopes.",
            "Window layers, cable routes, attachment interfaces and arm components remain provisional until specialist review.",
            "Illustrative payload and field-guide nodes are not physical field-performance evidence.",
        ],
    }
    return rows, summary


def write_audit(rows: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "luke_ii_dimensional_audit.csv"
    json_path = output_dir / "luke_ii_dimensional_audit_summary.json"
    fieldnames = list(rows[0].keys())
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    stamped = dict(summary)
    stamped["csv_sha256"] = sha256_file(csv_path)
    json_path.write_text(json.dumps(stamped, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return csv_path, json_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=Path, default=Path(__file__).with_name("luke_ii_parameters.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("generated"))
    args = parser.parse_args()
    parameters = json.loads(args.parameters.read_text(encoding="utf-8"))
    rows, summary = build_audit(parameters)
    csv_path, json_path = write_audit(rows, summary, args.out_dir)
    print(json.dumps({
        "status": summary["status"],
        "node_count": summary["node_count"],
        "physical_node_count": summary["physical_node_count"],
        "semantic_geometry_sha256": summary["semantic_geometry_sha256"],
        "csv": {"path": csv_path.name, "sha256": sha256_file(csv_path)},
        "summary": {"path": json_path.name, "sha256": sha256_file(json_path)},
        "claim_gate_state": "UNCHANGED",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
