#!/usr/bin/env python3
"""Generate a deterministic dimensional-review register for the Luke II reference.

The register reports geometry facts and evidence states only. It does not promote
reference geometry to engineering, manufacturing, flight, pressure-vessel or
human-rating approval.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from luke_ii_parametric import build_scene


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_node(name: str) -> tuple[str, str, str]:
    """Return family, evidence state and mandatory review gate for a node."""
    if name.startswith("SHELL_"):
        return "shell", "PROVISIONAL_REFERENCE_GEOMETRY", "STRUCTURAL_PRESSURE_SHELL_REVIEW"
    if name == "HABITAT_PRESSURISED_CLEAR_VOLUME":
        return "habitation", "DERIVED_TARGET_NOT_HUMAN_RATED", "HUMAN_FACTORS_ECLSS_REVIEW"
    if name.startswith("HAB_"):
        return "habitation", "DERIVED_FUNCTIONAL_LAYOUT", "HUMAN_FACTORS_ECLSS_REVIEW"
    if name.startswith("SYSTEM_FIELD_MODULE_"):
        return "field_system", "SOURCE_ALIGNED_TOPOLOGY", "COIL_FIELD_THERMAL_REVIEW"
    if name.startswith("SYSTEM_SENSOR_NODE_"):
        return "sensor_system", "SOURCE_ALIGNED_TOPOLOGY", "INSTRUMENTATION_CONTROL_REVIEW"
    if name.startswith("STRUCTURE_"):
        return "structure", "PROVISIONAL_REFERENCE_GEOMETRY", "STRUCTURAL_LOAD_REVIEW"
    if name.startswith("SYSTEM_RESONATOR_BAY_"):
        return "resonator_system", "SOURCE_ALIGNED_TOPOLOGY", "RFS_EMI_REVIEW"
    if name.startswith("SYSTEM_POWER_CAPACITOR_BAY_"):
        return "power_system", "SOURCE_ALIGNED_TOPOLOGY", "POWER_THERMAL_SAFETY_REVIEW"
    if name.startswith("SYSTEM_DAMPING_PLACEHOLDER_"):
        return "damping_system", "CONCEPTUAL_SPECIALIST_REVIEW", "GAS_PRESSURE_HAZARD_REVIEW"
    if name.startswith("INTERFACE_PROVISIONAL_DOCKING_COLLAR_"):
        return "interface", "PROVISIONAL_INTERFACE", "DOCKING_STRUCTURAL_STANDARD_REVIEW"
    if name.startswith("INTERFACE_"):
        return "interface", "FUTURE_BRIDGE_PLACEHOLDER", "INTERFACE_CONTROL_DOCUMENT_REVIEW"
    if name.startswith("PAYLOAD_"):
        return "payload_path", "ILLUSTRATIVE_SEQUENCE_ONLY", "GUIDANCE_CONTROL_ENVELOPE_REVIEW"
    if name.startswith("FIELD_GUIDE_"):
        return "field_guide", "ILLUSTRATIVE_ONLY_NOT_PHYSICAL_FIELD", "MEASURED_FIELD_MAP_REVIEW"
    return "unclassified", "REVIEW_REQUIRED", "CONFIGURATION_CONTROL_REVIEW"


def rounded(values: Any, digits: int = 6) -> list[float]:
    return [round(float(value), digits) for value in values]


def build_audit(parameters: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scene = build_scene(parameters)
    rows: list[dict[str, Any]] = []

    for node_name in sorted(scene.geometry):
        mesh = scene.geometry[node_name]
        family, evidence_state, review_gate = classify_node(node_name)
        bounds = mesh.bounds
        extents = mesh.extents
        centroid = mesh.centroid
        rows.append(
            {
                "node_name": node_name,
                "family": family,
                "evidence_state": evidence_state,
                "review_gate": review_gate,
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
        "schema_version": "luke-ii-dimensional-audit-v1",
        "status": "PASS_DIMENSIONAL_REFERENCE_AUDIT",
        "source_state": parameters["artifact_status"],
        "units": "metres",
        "node_count": len(rows),
        "all_nodes_watertight": all(row["watertight"] for row in rows),
        "all_nodes_winding_consistent": all(row["winding_consistent"] for row in rows),
        "scene_bounds_m": [rounded(scene.bounds[0]), rounded(scene.bounds[1])],
        "scene_extents_m": rounded(scene.extents),
        "family_counts": dict(sorted(family_counts.items())),
        "evidence_state_counts": dict(sorted(evidence_counts.items())),
        "review_gate_counts": dict(sorted(gate_counts.items())),
        "guardrails": [
            "Reference geometry only; no flight, pressure-vessel, human-rating or manufacturing approval.",
            "Bounds and volumes are geometric observations, not validated structural or operational envelopes.",
            "Illustrative payload and field-guide nodes are not physical field-performance evidence.",
            "Provisional values may change only through source-backed engineering review and configuration control.",
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

    summary = dict(summary)
    summary["csv_sha256"] = sha256_file(csv_path)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return csv_path, json_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=Path, default=Path(__file__).with_name("luke_ii_parameters.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("generated"))
    args = parser.parse_args()

    parameters = json.loads(args.parameters.read_text(encoding="utf-8"))
    rows, summary = build_audit(parameters)
    csv_path, json_path = write_audit(rows, summary, args.out_dir)
    result = {
        "status": summary["status"],
        "node_count": summary["node_count"],
        "csv": {"path": csv_path.name, "sha256": sha256_file(csv_path)},
        "summary": {"path": json_path.name, "sha256": sha256_file(json_path)},
        "claim_gate_state": "UNCHANGED",
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
