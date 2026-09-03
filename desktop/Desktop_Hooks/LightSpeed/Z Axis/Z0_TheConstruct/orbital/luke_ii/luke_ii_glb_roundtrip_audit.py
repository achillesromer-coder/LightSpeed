#!/usr/bin/env python3
"""Verify an exported Luke II GLB against its canonical source scene.

This audit tolerates normal float32 container precision but requires exact node
identity, topology counts and mesh quality, plus bounded geometric deviations.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import trimesh

from luke_ii_parametric import build_scene


DEFAULT_LINEAR_TOLERANCE_M = 2e-5
DEFAULT_RELATIVE_MEASURE_TOLERANCE = 5e-6
DEFAULT_ABSOLUTE_VOLUME_TOLERANCE_M3 = 1e-6
DEFAULT_ABSOLUTE_AREA_TOLERANCE_M2 = 2e-6


def _max_abs(a: Any, b: Any) -> float:
    return float(np.max(np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float))))


def audit_glb_roundtrip(
    parameters: dict[str, Any],
    glb_path: Path,
    linear_tolerance_m: float = DEFAULT_LINEAR_TOLERANCE_M,
    relative_measure_tolerance: float = DEFAULT_RELATIVE_MEASURE_TOLERANCE,
    absolute_volume_tolerance_m3: float = DEFAULT_ABSOLUTE_VOLUME_TOLERANCE_M3,
    absolute_area_tolerance_m2: float = DEFAULT_ABSOLUTE_AREA_TOLERANCE_M2,
) -> dict[str, Any]:
    source = build_scene(parameters)
    exported = trimesh.load(glb_path, force="scene")

    source_names = set(source.geometry)
    exported_names = set(exported.geometry)
    missing = sorted(source_names - exported_names)
    unexpected = sorted(exported_names - source_names)
    node_results: dict[str, dict[str, Any]] = {}
    failures: list[str] = []

    if missing:
        failures.append(f"missing nodes: {missing}")
    if unexpected:
        failures.append(f"unexpected nodes: {unexpected}")

    max_bounds_error = 0.0
    max_extents_error = 0.0
    max_centroid_error = 0.0
    max_relative_volume_error = 0.0
    max_relative_area_error = 0.0

    for name in sorted(source_names & exported_names):
        expected = source.geometry[name]
        observed = exported.geometry[name]
        bounds_error = _max_abs(expected.bounds, observed.bounds)
        extents_error = _max_abs(expected.extents, observed.extents)
        centroid_error = _max_abs(expected.centroid, observed.centroid)
        volume_denominator = max(abs(float(expected.volume)), 1e-12)
        area_denominator = max(abs(float(expected.area)), 1e-12)
        absolute_volume_error = abs(float(expected.volume) - float(observed.volume))
        absolute_area_error = abs(float(expected.area) - float(observed.area))
        relative_volume_error = absolute_volume_error / volume_denominator
        relative_area_error = absolute_area_error / area_denominator

        checks = {
            "vertex_count_exact": len(expected.vertices) == len(observed.vertices),
            "face_count_exact": len(expected.faces) == len(observed.faces),
            "watertight_exact": bool(expected.is_watertight) == bool(observed.is_watertight),
            "winding_consistent_exact": bool(expected.is_winding_consistent) == bool(observed.is_winding_consistent),
            "bounds_within_tolerance": bounds_error <= linear_tolerance_m,
            "extents_within_tolerance": extents_error <= linear_tolerance_m,
            "centroid_within_tolerance": centroid_error <= linear_tolerance_m,
            "volume_within_tolerance": (relative_volume_error <= relative_measure_tolerance or absolute_volume_error <= absolute_volume_tolerance_m3),
            "area_within_tolerance": (relative_area_error <= relative_measure_tolerance or absolute_area_error <= absolute_area_tolerance_m2),
        }
        if not all(checks.values()):
            failures.append(f"{name}: {[key for key, value in checks.items() if not value]}")

        node_results[name] = {
            "vertices": len(observed.vertices),
            "faces": len(observed.faces),
            "watertight": bool(observed.is_watertight),
            "winding_consistent": bool(observed.is_winding_consistent),
            "bounds_max_abs_error_m": bounds_error,
            "extents_max_abs_error_m": extents_error,
            "centroid_max_abs_error_m": centroid_error,
            "absolute_volume_error_m3": absolute_volume_error,
            "absolute_area_error_m2": absolute_area_error,
            "relative_volume_error": relative_volume_error,
            "relative_area_error": relative_area_error,
            "checks": checks,
        }
        max_bounds_error = max(max_bounds_error, bounds_error)
        max_extents_error = max(max_extents_error, extents_error)
        max_centroid_error = max(max_centroid_error, centroid_error)
        max_relative_volume_error = max(max_relative_volume_error, relative_volume_error)
        max_relative_area_error = max(max_relative_area_error, relative_area_error)

    return {
        "schema_version": "luke-ii-glb-roundtrip-audit-v1",
        "status": "PASS_GLB_ROUNDTRIP_REFERENCE" if not failures else "FAIL_GLB_ROUNDTRIP_REFERENCE",
        "glb_file": glb_path.name,
        "source_nodes": len(source_names),
        "exported_nodes": len(exported_names),
        "matched_nodes": len(source_names & exported_names),
        "missing_nodes": missing,
        "unexpected_nodes": unexpected,
        "linear_tolerance_m": linear_tolerance_m,
        "relative_measure_tolerance": relative_measure_tolerance,
        "absolute_volume_tolerance_m3": absolute_volume_tolerance_m3,
        "absolute_area_tolerance_m2": absolute_area_tolerance_m2,
        "maximum_observed_errors": {
            "bounds_m": max_bounds_error,
            "extents_m": max_extents_error,
            "centroid_m": max_centroid_error,
            "relative_volume": max_relative_volume_error,
            "relative_area": max_relative_area_error,
        },
        "failures": failures,
        "nodes": node_results,
        "claim_gate_state": "UNCHANGED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=Path, required=True)
    parser.add_argument("--glb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    parameters = json.loads(args.parameters.read_text(encoding="utf-8"))
    result = audit_glb_roundtrip(parameters, args.glb)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "source_nodes",
                    "exported_nodes",
                    "matched_nodes",
                    "maximum_observed_errors",
                )
            },
            indent=2,
        )
    )
    return 0 if result["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
