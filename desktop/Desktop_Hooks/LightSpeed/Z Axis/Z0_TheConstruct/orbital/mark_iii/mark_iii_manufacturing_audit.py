#!/usr/bin/env python3
"""Audit Mark III v0.3.3 print, sanding, metallisation and assembly-development controls."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from mark_iii_parametric import build_print_references, build_reference, print_kit_manifest

REQUIRED_REFERENCE_DOCUMENTS = {
    "NASA-STD-6030",
    "NASA-STD-6033",
    "NASA-HDBK-5026",
    "ISO/ASTM 52910:2018",
    "ASTM F3529-21",
    "ECSS-Q-ST-70-02C",
    "NASA-STD-6001",
    "NASA-STD-6012A",
    "NASA-STD-6016",
}


def build_audit(parameters: dict[str, Any]) -> dict[str, Any]:
    scene, records = build_reference(parameters)
    refs = build_print_references(parameters, scene, records)
    print_kit_manifest(parameters, refs)
    families = Counter(record["family"] for record in records)
    panels = [record for record in records if record["family"] == "shell_panel"]
    names = {record["node_name"] for record in records}

    feature_failures: list[dict[str, Any]] = []
    panel_rows: list[dict[str, Any]] = []
    for panel in panels:
        suffix = panel["node_name"].removeprefix("M3_SHELL_PANEL_")
        required = {
            "plating_allowance": f"M3_PLATING_ALLOWANCE_{suffix}",
            "insert_boss_1": f"M3_PANEL_INSERT_BOSS_{suffix}_F01",
            "insert_boss_2": f"M3_PANEL_INSERT_BOSS_{suffix}_F02",
            "mask_land_1": f"M3_PLATING_MASK_LAND_{suffix}_E01",
            "mask_land_2": f"M3_PLATING_MASK_LAND_{suffix}_E02",
            "drain_sleeve": f"M3_PLATING_DRAIN_SLEEVE_{suffix}",
            "datum_pad": f"M3_ASSEMBLY_DATUM_PAD_{suffix}",
        }
        missing = [label for label, node_name in required.items() if node_name not in names]
        if missing:
            feature_failures.append({"panel": panel["node_name"], "missing": missing})
        panel_rows.append(
            {
                "panel": panel["node_name"],
                "print_part": panel.get("print_part", ""),
                "manufacturing_state": panel.get("manufacturing_state", ""),
                "required_features_present": not missing,
                "missing_features": ";".join(missing),
                "pre_plate_extent_x_m": panel["extents_m"][0],
                "pre_plate_extent_y_m": panel["extents_m"][1],
                "pre_plate_extent_z_m": panel["extents_m"][2],
            }
        )

    bed = sorted(float(value) for value in parameters["derived_configuration"]["print_bed_mm"])
    print_failures: list[dict[str, Any]] = []
    for name, mesh in refs.items():
        fits = all(
            extent <= limit + 1e-6
            for extent, limit in zip(sorted(float(value) for value in mesh.extents), bed)
        )
        if not (mesh.is_watertight and mesh.is_winding_consistent and fits):
            print_failures.append(
                {
                    "file": name,
                    "watertight": bool(mesh.is_watertight),
                    "winding_consistent": bool(mesh.is_winding_consistent),
                    "fits_reference_bed_by_orientation": fits,
                }
            )

    registered_documents = {
        reference["document"] for reference in parameters.get("qualification_references", [])
    }
    checks = {
        "all_18_panels_have_manufacturing_features": len(panels) == 18 and not feature_failures,
        "all_20_print_references_fit_and_are_manifold": len(refs) == 20 and not print_failures,
        "plating_allowance_exists_for_each_panel": families["plating_allowance"] == 18,
        "two_insert_bosses_exist_for_each_panel": families["fastener"] == 36,
        "mask_drain_datum_features_exist": families["plating_feature"] >= 72,
        "witness_coupon_part_exists": "mark_iii_plating_witness_coupon_tree_1to1.stl" in refs,
        "alignment_and_plating_jig_exists": "mark_iii_alignment_and_plating_jig_1to1.stl" in refs,
        "mandatory_witness_register_complete": len(
            parameters["manufacturing_reference"]["mandatory_witnesses"]
        )
        >= 5,
        "mandatory_inspection_register_complete": len(
            parameters["manufacturing_reference"]["mandatory_inspections"]
        )
        >= 10,
        "qualification_reference_register_complete": REQUIRED_REFERENCE_DOCUMENTS.issubset(
            registered_documents
        ),
        "substrate_selection_remains_open": "UNSELECTED"
        in parameters["manufacturing_reference"]["substrate_state"],
        "plating_process_remains_external_and_unqualified": "QUALIFIED_EXTERNAL_PLATER"
        in parameters["manufacturing_reference"]["metallization_state"],
        "deployment_release_is_not_granted": any(
            "deployment" in gate.lower()
            and ("no " in gate.lower() or "blocked" in gate.lower())
            for gate in parameters["claim_gates"]
        ),
    }
    failures = [name for name, passed in checks.items() if not passed]

    stages = [
        {
            "stage": "A",
            "name": "CAD and datum freeze",
            "state": "REFERENCE_COMPLETE",
            "evidence": "v0.3.3 geometry, component manifest and dimensional audit",
            "release": "No physical release",
        },
        {
            "stage": "B",
            "name": "Printer and process coupon qualification",
            "state": "OPEN",
            "evidence": "Machine, material lot, raster, wall, moisture, dimensional and mechanical coupon results",
            "release": "Required before article print",
        },
        {
            "stage": "C",
            "name": "Article printing and dimensional acceptance",
            "state": "OPEN",
            "evidence": "Build logs, serialised parts, pre/post sanding inspection and insert tests",
            "release": "Required before metallisation",
        },
        {
            "stage": "D",
            "name": "Sealing, activation and plating qualification",
            "state": "OPEN",
            "evidence": "Representative coupons, thickness map, adhesion, continuity, isolation, thermal cycling and corrosion screening",
            "release": "Qualified external plater and engineering approval",
        },
        {
            "stage": "E",
            "name": "Subassembly integration",
            "state": "OPEN",
            "evidence": "Torque/locking records, harness inspection, electrical isolation, propulsion-interface inert-fit checks, and pressure-system exclusion or certification",
            "release": "Low-energy bench article only",
        },
        {
            "stage": "F",
            "name": "Environmental and functional qualification",
            "state": "OPEN",
            "evidence": "Vibration, shock, TVAC/outgassing, flammability, EMI/EMC, thermal, mechanism life, propulsion-interface structural/contamination controls and low-energy RFS/EMFF evidence",
            "release": "Required before any flight or deployment consideration",
        },
    ]

    return {
        "schema_version": "mark-iii-manufacturing-qualification-audit-v0.3.3",
        "status": "PASS_MANUFACTURING_REFERENCE_CONTROLS_DEPLOYMENT_BLOCKED"
        if not failures
        else "FAIL_MANUFACTURING_REFERENCE_CONTROLS",
        "checks": checks,
        "failures": failures,
        "panel_feature_failures": feature_failures,
        "print_reference_failures": print_failures,
        "counts": {
            "panels": len(panels),
            "print_references": len(refs),
            "plating_allowances": families["plating_allowance"],
            "plating_features": families["plating_feature"],
            "insert_bosses": families["fastener"],
        },
        "plating_allowance_per_surface_mm": parameters["derived_configuration"][
            "plating_allowance_per_surface_m"
        ]
        * 1000,
        "print_bed_mm": parameters["derived_configuration"]["print_bed_mm"],
        "process_state": parameters["manufacturing_reference"],
        "qualification_references": parameters.get("qualification_references", []),
        "stages": stages,
        "panel_register": panel_rows,
        "manufacturing_release": "BLOCKED",
        "flight_or_deployment_release": "BLOCKED",
        "allowed_interpretation": "A complete print, finishing, plating and assembly-development reference with auditable qualification gates.",
        "blocked_interpretation": "Production-ready, structurally qualified, electrically qualified, pressure-qualified, flight-ready or deployable hardware.",
    }


def write(audit: dict[str, Any], out_dir: Path) -> tuple[Path, Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "mark_iii_manufacturing_audit.json"
    panel_path = out_dir / "mark_iii_manufacturing_panel_register.csv"
    stage_path = out_dir / "mark_iii_manufacturing_stage_gate.csv"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with panel_path.open("w", newline="", encoding="utf-8") as stream:
        rows = audit["panel_register"]
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with stage_path.open("w", newline="", encoding="utf-8") as stream:
        rows = audit["stages"]
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return json_path, panel_path, stage_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parameters", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    audit = build_audit(json.loads(args.parameters.read_text()))
    paths = write(audit, args.out_dir)
    print(
        json.dumps(
            {
                "status": audit["status"],
                "counts": audit["counts"],
                "outputs": [path.name for path in paths],
            },
            indent=2,
        )
    )
    return 0 if audit["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
