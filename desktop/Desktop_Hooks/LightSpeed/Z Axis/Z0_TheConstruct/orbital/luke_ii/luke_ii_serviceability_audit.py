#!/usr/bin/env python3
"""Audit Luke II v1.3 attachment, access, cable, walkway and print reservations."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from luke_ii_parametric import build_print_references, build_reference

ROOTS = {"PRIMARY_STRUCTURE", "ILLUSTRATIVE_REFERENCE_ROOT"}
STRUCTURAL_MAINTAINABLE_FAMILIES = {
    "solar_hull_panel", "window_frame", "cable_tray", "primary_structure",
    "habitat_walkway", "habitat_bulkhead", "removable_lining",
    "power_harness", "data_harness", "habitat_harness", "arm_harness", "mark_iii_arm_harness",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _trace_to_root(name: str, record_map: dict[str, dict[str, Any]]) -> tuple[bool, list[str]]:
    chain = [name]
    seen = {name}
    parent = record_map[name]["attachment_parent"]
    while parent not in ROOTS:
        if parent not in record_map:
            chain.append(parent)
            return False, chain
        if parent in seen:
            chain.append(parent)
            return False, chain
        chain.append(parent)
        seen.add(parent)
        parent = record_map[parent]["attachment_parent"]
    chain.append(parent)
    return True, chain


def build_audit(parameters: dict[str, Any]) -> dict[str, Any]:
    scene, records = build_reference(parameters)
    record_map = {record["node_name"]: record for record in records}
    physical = [record for record in records if record["physical"]]
    maintainable = [record for record in physical if record["maintainable"]]
    cable_required = [record for record in physical if record["cable_required"]]

    missing_parent = [record["node_name"] for record in physical if not record["attachment_parent"]]
    unresolved_parent: list[str] = []
    cycles_or_unrooted: list[dict[str, Any]] = []
    for record in physical:
        parent = record["attachment_parent"]
        if parent not in ROOTS and parent not in record_map:
            unresolved_parent.append(record["node_name"])
        rooted, chain = _trace_to_root(record["node_name"], record_map)
        if not rooted:
            cycles_or_unrooted.append({"node": record["node_name"], "chain": chain})

    missing_cable_route = [record["node_name"] for record in cable_required if not record["cable_route"]]
    unresolved_cable_route = [
        record["node_name"] for record in cable_required
        if record["cable_route"] and record["cable_route"] not in record_map
    ]
    missing_clearance = [
        record["node_name"] for record in maintainable
        if not record["service_clearance"] and record["family"] not in STRUCTURAL_MAINTAINABLE_FAMILIES
    ]
    unresolved_clearance = [
        record["node_name"] for record in maintainable
        if record["service_clearance"] and record["service_clearance"] not in record_map
    ]
    unresolved_removal = [
        record["node_name"] for record in maintainable
        if record["removal_path"] and record["removal_path"] not in record_map
    ]

    walkway = sorted(
        [record for record in records if record["family"] == "habitat_walkway"],
        key=lambda record: int(record["node_name"].rsplit("_", 1)[1]),
    )
    walkway_centres = [scene.geometry[record["node_name"]].centroid for record in walkway]
    walkway_gaps = [float(np.linalg.norm(b - a)) for a, b in zip(walkway_centres, walkway_centres[1:])] if walkway_centres else []
    max_walkway_gap = max(walkway_gaps, default=0.0)

    print_refs = build_print_references(parameters, scene, records)
    print_rows = []
    for name, mesh in sorted(print_refs.items()):
        print_rows.append({
            "file": name,
            "watertight": bool(mesh.is_watertight),
            "winding_consistent": bool(mesh.is_winding_consistent),
            "extent_x_mm": round(float(mesh.extents[0]), 6),
            "extent_y_mm": round(float(mesh.extents[1]), 6),
            "extent_z_mm": round(float(mesh.extents[2]), 6),
            "largest_extent_mm": round(float(max(mesh.extents)), 6),
            "display_printer_envelope_280mm": bool(max(mesh.extents) <= 280.0 + 1e-6),
        })

    family_counts = Counter(record["family"] for record in records)
    window_count = family_counts["pressure_window"]
    window_frame_count = family_counts["window_frame"]
    walkway_count = family_counts["habitat_walkway"]
    egress_count = family_counts["egress_path"]
    tray_count = family_counts["cable_tray"]
    arm_count = sum(value for family, value in family_counts.items() if family.startswith("mark_iii"))
    bulkhead_count = family_counts["habitat_bulkhead"]
    service_clearance_count = family_counts["service_clearance"]
    removal_path_count = family_counts["removal_path"]

    volumes = parameters["habitation"]
    volume_order = (
        volumes["gross_clear_volume_m3"]
        > volumes["pressure_liner_clear_volume_m3"]
        > volumes["service_allocated_reference_volume_m3"]
        > 0
    )

    checks = {
        "all_geometry_watertight": all(mesh.is_watertight for mesh in scene.geometry.values()),
        "all_geometry_winding_consistent": all(mesh.is_winding_consistent for mesh in scene.geometry.values()),
        "all_physical_nodes_have_parent": not missing_parent,
        "all_physical_nodes_resolve_to_root": not unresolved_parent and not cycles_or_unrooted,
        "all_cable_required_nodes_have_route": not missing_cable_route and not unresolved_cable_route,
        "all_nonstructural_maintainable_nodes_have_clearance": not missing_clearance and not unresolved_clearance,
        "all_declared_removal_paths_resolve": not unresolved_removal,
        "window_layers_present": window_count == 120,
        "window_frames_present": window_frame_count == 120,
        "connected_walkway_segment_count": walkway_count == parameters["closure_revision"]["habitat_access"]["walkway_segment_count"],
        "walkway_centre_gap_within_reference": max_walkway_gap <= 1.05,
        "egress_path_matches_walkway": egress_count == walkway_count,
        "panelled_bulkheads_with_open_doorways_present": bulkhead_count == 24,
        "cable_tray_ring_present": tray_count == 32,
        "service_clearances_present": service_clearance_count >= 250,
        "removal_paths_present": removal_path_count >= 200,
        "mark_iii_arm_decomposition_present": arm_count >= 20,
        "habitation_volume_allocation_ordered": volume_order,
        "all_print_references_watertight": all(row["watertight"] for row in print_rows),
        "all_print_references_winding_consistent": all(row["winding_consistent"] for row in print_rows),
        "all_print_references_fit_280mm_display_envelope": all(row["display_printer_envelope_280mm"] for row in print_rows),
    }

    failures = [name for name, passed in checks.items() if not passed]
    return {
        "schema_version": "luke-ii-serviceability-audit-v1.3",
        "status": "PASS_SERVICEABILITY_REFERENCE_AUDIT" if not failures else "FAIL_SERVICEABILITY_REFERENCE_AUDIT",
        "checks": checks,
        "failures": failures,
        "counts": {
            "geometry_nodes": len(records),
            "physical_nodes": len(physical),
            "maintainable_nodes": len(maintainable),
            "cable_required_nodes": len(cable_required),
            "window_layers": window_count,
            "window_frame_parts": window_frame_count,
            "walkway_segments": walkway_count,
            "egress_segments": egress_count,
            "bulkhead_parts": bulkhead_count,
            "cable_tray_segments": tray_count,
            "service_clearances": service_clearance_count,
            "removal_paths": removal_path_count,
            "mark_iii_interface_arm_nodes": arm_count,
        },
        "walkway": {
            "maximum_centre_gap_m": max_walkway_gap,
            "reference_limit_m": 1.05,
        },
        "habitation_volumes_m3": {
            "gross_planning": volumes["gross_clear_volume_m3"],
            "pressure_liner_clear": volumes["pressure_liner_clear_volume_m3"],
            "service_allocated_reference": volumes["service_allocated_reference_volume_m3"],
            "state": volumes["volume_revision_state"],
        },
        "unresolved": {
            "missing_parent": missing_parent,
            "unresolved_parent": unresolved_parent,
            "cycles_or_unrooted": cycles_or_unrooted,
            "missing_cable_route": missing_cable_route,
            "unresolved_cable_route": unresolved_cable_route,
            "missing_clearance": missing_clearance,
            "unresolved_clearance": unresolved_clearance,
            "unresolved_removal": unresolved_removal,
        },
        "print_references": print_rows,
        "open_engineering_gaps": parameters["open_engineering_gaps"],
        "claim_gate_state": "HELD_NO_ENGINEERING_CAPABILITY_PROMOTION",
    }


def write_audit(audit: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "luke_ii_serviceability_audit.json"
    csv_path = output_dir / "luke_ii_print_segmentation_audit.csv"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = audit["print_references"]
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return json_path, csv_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=Path, default=Path(__file__).with_name("luke_ii_parameters.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("generated"))
    args = parser.parse_args()
    parameters = json.loads(args.parameters.read_text(encoding="utf-8"))
    audit = build_audit(parameters)
    json_path, csv_path = write_audit(audit, args.out_dir)
    print(json.dumps({
        "status": audit["status"],
        "counts": audit["counts"],
        "maximum_walkway_gap_m": audit["walkway"]["maximum_centre_gap_m"],
        "json_sha256": sha256_file(json_path),
        "csv_sha256": sha256_file(csv_path),
    }, indent=2))
    return 0 if audit["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
