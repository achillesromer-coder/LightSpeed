#!/usr/bin/env python3
"""Verify Luke II v1.3 portable, semantic, serviceability and review invariants."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

MANIFEST_CANONICAL_SHA256 = "0ebff95d8047d04a27c00ea8f56f961672ce9f6388bb68efc0464e89e9ca792e"


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"Missing required artifact: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: normalize_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_json(item) for item in value]
    if isinstance(value, float):
        rounded = round(value, 8)
        return 0.0 if rounded == 0.0 else rounded
    return value


def canonical_json_sha256(path: Path) -> str:
    value = json.loads(path.read_text(encoding="utf-8"))
    payload = json.dumps(
        normalize_json(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--receipt-output", required=True)
    args = parser.parse_args()

    source = Path(args.source_dir)
    output = Path(args.output_dir)
    receipt = json.loads((source / "luke_ii_execution_receipt.json").read_text(encoding="utf-8"))
    verification = json.loads((output / "luke_ii_verification.json").read_text(encoding="utf-8"))
    dimensional = json.loads((output / "luke_ii_dimensional_audit_summary.json").read_text(encoding="utf-8"))
    serviceability = json.loads((output / "luke_ii_serviceability_audit.json").read_text(encoding="utf-8"))
    roundtrip = json.loads((output / "luke_ii_glb_roundtrip_audit.json").read_text(encoding="utf-8"))
    manifest_path = output / "luke_ii_component_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    observed = {
        "parameters": sha256_file(source / "luke_ii_parameters.json"),
        "requirements": sha256_file(source / "requirements.txt"),
        "parametric_full_source": sha256_file(source / "luke_ii_parametric.py"),
        "assembly_glb_build_receipt": sha256_file(output / "luke_ii_assembly.glb"),
        "component_manifest_build_receipt": sha256_file(manifest_path),
        "component_manifest_canonical": canonical_json_sha256(manifest_path),
        "full_print_reference": sha256_file(output / "luke_ii_reference_1to100.stl"),
        "panel_print_reference": sha256_file(output / "luke_ii_representative_hull_panel_1to20.stl"),
        "window_print_reference": sha256_file(output / "luke_ii_representative_window_1to20.stl"),
        "mark_iii_arm_print_reference": sha256_file(output / "luke_ii_mark_iii_interface_arm_1to20.stl"),
        "interactive_html_build_receipt": sha256_file(output / "luke_ii_interactive.html"),
        "dimensional_audit_build_receipt": sha256_file(output / "luke_ii_dimensional_audit.csv"),
        "dimensional_audit_summary_build_receipt": sha256_file(output / "luke_ii_dimensional_audit_summary.json"),
        "serviceability_audit_build_receipt": sha256_file(output / "luke_ii_serviceability_audit.json"),
        "print_segmentation_audit": sha256_file(output / "luke_ii_print_segmentation_audit.csv"),
        "glb_roundtrip_audit_build_receipt": sha256_file(output / "luke_ii_glb_roundtrip_audit.json"),
    }

    canonical = receipt["canonical_source"]
    if observed["parameters"] != canonical["parameters_sha256"]:
        raise SystemExit("Canonical parameter bytes changed without receipt update")
    if observed["requirements"] != canonical["dependency_sha256"]:
        raise SystemExit("Pinned dependency bytes changed without receipt update")
    if observed["parametric_full_source"] != canonical["parametric_full_source_sha256"]:
        raise SystemExit("Full parametric source does not match the registered source hash")

    expected = receipt["generated_artifacts"]
    exact_portable = {
        "full_print_reference": "full_print_reference",
        "panel_print_reference": "panel_print_reference",
        "window_print_reference": "window_print_reference",
        "mark_iii_arm_print_reference": "mark_iii_arm_print_reference",
        "print_segmentation_audit": "print_segmentation_audit",
    }
    for observed_key, receipt_key in exact_portable.items():
        if observed[observed_key] != expected[receipt_key]["sha256"]:
            raise SystemExit(f"Portable artifact mismatch: {receipt_key}")

    invariants = receipt["acceptance_invariants"]
    expected_manifest = invariants.get("component_manifest_canonical_sha256", MANIFEST_CANONICAL_SHA256)
    if observed["component_manifest_canonical"] != expected_manifest:
        raise SystemExit("Canonical component-manifest meaning changed")

    checks = verification["geometry_checks"]
    node_count = verification["scene"]["geometry_nodes"]
    watertight = sum(1 for value in checks.values() if value["watertight"])
    winding = sum(1 for value in checks.values() if value["winding_consistent"])

    if verification["status"] != "PASS_SERVICEABLE_REFERENCE_GEOMETRY":
        raise SystemExit(f"Unexpected geometry status: {verification['status']}")
    if node_count != invariants["named_nodes"]:
        raise SystemExit("Named-node count changed")
    if verification["configuration"]["physical_nodes"] != invariants["physical_nodes"]:
        raise SystemExit("Physical-node count changed")
    if watertight != invariants["individual_nodes_watertight"]:
        raise SystemExit("Watertight-node count changed")
    if winding != invariants["individual_nodes_winding_consistent"]:
        raise SystemExit("Winding-consistent-node count changed")
    if dimensional["semantic_geometry_sha256"] != invariants["semantic_geometry_sha256"]:
        raise SystemExit("Semantic geometry fingerprint changed")
    if dimensional["node_count"] != node_count:
        raise SystemExit("Dimensional audit node count does not match the source scene")
    if not dimensional["all_nodes_watertight"] or not dimensional["all_nodes_winding_consistent"]:
        raise SystemExit("Dimensional audit mesh-quality gate failed")

    if serviceability["status"] != invariants["serviceability_status"]:
        raise SystemExit("Serviceability audit failed")
    if serviceability["failures"]:
        raise SystemExit(f"Serviceability failures: {serviceability['failures']}")
    required_service_checks = [
        "all_physical_nodes_have_parent",
        "all_physical_nodes_resolve_to_root",
        "all_cable_required_nodes_have_route",
        "all_nonstructural_maintainable_nodes_have_clearance",
        "all_declared_removal_paths_resolve",
        "walkway_centre_gap_within_reference",
        "all_print_references_fit_280mm_display_envelope",
    ]
    missing_checks = [key for key in required_service_checks if serviceability["checks"].get(key) is not True]
    if missing_checks:
        raise SystemExit(f"Maintainability gates failed: {missing_checks}")

    if roundtrip["status"] != invariants["glb_roundtrip_status"]:
        raise SystemExit("GLB roundtrip audit failed")
    if roundtrip["matched_nodes"] != invariants["glb_roundtrip_matched_nodes"]:
        raise SystemExit("GLB roundtrip node count changed")
    if roundtrip["missing_nodes"] or roundtrip["unexpected_nodes"] or roundtrip["failures"]:
        raise SystemExit("GLB roundtrip contains identity or tolerance failures")

    if manifest["node_count"] != node_count or len(manifest["components"]) != node_count:
        raise SystemExit("Component manifest does not cover every named node")
    interactive = output / "luke_ii_interactive.html"
    if interactive.stat().st_size < 1_000_000:
        raise SystemExit("Interactive review surface is unexpectedly small")

    result = {
        "schema_version": "luke-ii-ci-receipt-v1.3.2",
        "status": "PASS_SERVICEABLE_PORTABLE_SEMANTIC_GLB_AND_INTERACTIVE_REGENERATION",
        "source_branch": os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME"),
        "commit": os.environ.get("GITHUB_SHA"),
        "observed_sha256": observed,
        "geometry_nodes": node_count,
        "physical_nodes": verification["configuration"]["physical_nodes"],
        "semantic_geometry_sha256": dimensional["semantic_geometry_sha256"],
        "component_manifest_canonical_sha256": observed["component_manifest_canonical"],
        "serviceability_status": serviceability["status"],
        "serviceability_counts": serviceability["counts"],
        "maximum_walkway_gap_m": serviceability["walkway"]["maximum_centre_gap_m"],
        "glb_roundtrip": {
            "status": roundtrip["status"],
            "matched_nodes": roundtrip["matched_nodes"],
            "maximum_observed_errors": roundtrip["maximum_observed_errors"],
        },
        "raw_glb_hash_policy": "BUILD_RECEIPT_ONLY_NOT_CROSS_PLATFORM_ACCEPTANCE_GATE",
        "raw_derived_json_csv_policy": "BUILD_RECEIPT_ONLY_SEMANTIC_AND_STRUCTURAL_GATES_APPLY",
        "raw_interactive_hash_policy": "BUILD_RECEIPT_ONLY_EMBEDS_PLATFORM_GLTF_CONTAINER",
        "claim_gate_state": "UNCHANGED",
    }
    target = Path(args.receipt_output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
