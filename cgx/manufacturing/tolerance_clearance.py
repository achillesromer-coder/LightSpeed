"""Conservative digital tolerance and STATIC keep-out review for CGX PrintSpace.

The source geometry and exact contact classification remain in the canonical
CGX composition/compiler. This small read-only facet uses integer micrometres
for bounded, explicitly declared symmetric placement uncertainty. It does NOT
certify real manufacturing tolerances, collision-free moving tools, machine
kinematics, printhead swept paths, CSG, FEA or contact/adhesion under tolerance.

Axis-aligned box envelopes are CONSERVATIVE for static keep-outs: a separated
envelope proves separation only for the ASSUMED bounded input translations and
the supplied STATIC AABBs. Overlap is a possible conflict, not proof of true
mesh interference. Nominal face contact can open a gap or form interference.
"""
from __future__ import annotations

import json
import re
from typing import Any

from .composition import compile_geometry_composition, digest

SCHEMA = "CGX-PRINTSPACE-TOLERANCE-STATIC-SCREEN/0.1"
RESULT_SCHEMA = "CGX-PRINTSPACE-TOLERANCE-STATIC-REVIEW/0.1"
MAX_PLAN_BYTES = 64 * 1024
MAX_UM = 1_000_000
SHA = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}\Z")


def _int(value: Any, min_val: int = 0, max_val: int = MAX_UM) -> bool:
    return type(value) is int and min_val <= value <= max_val


def _vec(v: Any, lower: int = 0, upper: int = MAX_UM) -> bool:
    return type(v) is list and len(v) == 3 and all(_int(x, lower, upper) for x in v)


def _hold(reason: str, geometry_hash: str | None = None) -> dict:
    return {
        "schema": RESULT_SCHEMA,
        "state": "HOLD",
        "hold_codes": [reason],
        "geometry_composite_sha256": geometry_hash,
        "screen_sha256": None,
        "static_keepout_results": [],
        "interface_uncertainty": [],
        "physical_tolerances_verified": False,
        "moving_toolpaths_evaluated": False,
        "physical_clearance_authorised": False,
        "machine_authorised": False,
        "mint_authorised": False,
        "commercial_release_authorised": False,
    }


def _envelope(bounds: dict, errors: list[int]) -> dict:
    lo, hi = bounds["min_mm"], bounds["max_mm"]
    if not (_vec(lo, -1_000_000, 1_000_000) and
            _vec(hi, -1_000_000, 1_000_000) and
            all(a <= b for a, b in zip(lo, hi))):
        raise ValueError("INVALID_SOURCE_BOUNDS")
    return {"lower_um": [1000 * x - e for x, e in zip(lo, errors)],
            "upper_um": [1000 * x + e for x, e in zip(hi, errors)]}


def _normal_axis(normals: Any) -> tuple[int, int] | None:
    if not isinstance(normals, list) or len(normals) != 1:
        return None
    n = normals[0]
    if not isinstance(n, list) or len(n) != 3 or any(type(x) is not int for x in n):
        return None
    if sorted(abs(x) for x in n) != [0, 0, 1]:
        return None
    axis = next(i for i, x in enumerate(n) if x != 0)
    return axis, n[axis]


def _gap_lower_bound_um(a: dict, b: dict) -> tuple[int, list[int]]:
    # Bounding-envelope separation by axis; no Euclidean or 3D sweep claim.
    axes = [
        max(0, b["lower_um"][i] - a["upper_um"][i],
               a["lower_um"][i] - b["upper_um"][i])
        for i in range(3)
    ]
    return max(axes), axes


def screen_static_tolerances(geometry_request: Any, plan: Any, geometry_review: Any = None) -> dict:
    """Return a stable, conservative bounded review with explicit physics holds."""
    if not isinstance(geometry_request, dict) or not isinstance(plan, dict):
        return _hold("INVALID_STATIC_SCREEN_INPUT")
    try:
        raw = json.dumps(plan, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("ascii")
    except (ValueError, TypeError, RecursionError, OverflowError):
        return _hold("NONCANONICAL_STATIC_SCREEN")
    if len(raw) > MAX_PLAN_BYTES:
        return _hold("STATIC_SCREEN_SIZE_BUDGET")
    if (plan.get("schema") != SCHEMA or plan.get("units") != "um"
            or plan.get("uncertainty_kind") != "SYNTHETIC_SYMMETRIC_TRANSLATION_BOUNDS"
            or plan.get("screen_kind") != "STATIC_CONSERVATIVE_AABB_ONLY"
            or plan.get("evidence_state") != "UNMEASURED"
            or set(plan) != {"schema", "units", "uncertainty_kind", "screen_kind", "evidence_state",
                             "geometry_composite_sha256", "manufacturing_ir_ref",
                             "manufacturing_ir_configuration_hash", "instance_uncertainties",
                             "static_keepouts", "minimum_nominal_static_clearance_um"}):
        return _hold("STATIC_SCREEN_SCHEMA_OR_EVIDENCE_ESCALATION")
    ref = plan.get("manufacturing_ir_ref")
    cfg = plan.get("manufacturing_ir_configuration_hash")
    if (not isinstance(ref, str) or not ref.startswith("cgx://manufacturing/build/")
            or not isinstance(cfg, str) or SHA.fullmatch(cfg) is None):
        return _hold("CANONICAL_IR_BINDING_MISSING")
    geometry = compile_geometry_composition(geometry_request) if geometry_review is None else geometry_review
    if (not isinstance(geometry, dict) or geometry.get("state") != "REVIEW_ONLY"
            or geometry.get("machine_authorised") is not False
            or geometry.get("mint_authorised") is not False
            or not isinstance(geometry.get("graph"), dict)
            or not isinstance(geometry.get("load_h0"), dict)
            or geometry["load_h0"].get("source_bytes_hydrated") != 0
            or geometry.get("geometry_composite_hash") != digest(geometry["graph"])):
        return _hold("EXACT_DIGITAL_GEOMETRY_UNBOUND")
    ghash = geometry["geometry_composite_hash"]
    if (plan.get("geometry_composite_sha256") != ghash
            or geometry["graph"].get("manufacturing_ir_ref") != ref
            or geometry_request.get("manufacturing_ir_ref") != ref
            or geometry_request.get("manufacturing_ir_configuration_hash") != cfg):
        return _hold("GEOMETRY_OR_BUILD_HASH_STALE", ghash)
    instances = geometry["graph"].get("instances")
    edges = geometry["graph"].get("interfaces")
    uncertainty = plan.get("instance_uncertainties")
    keepouts = plan.get("static_keepouts")
    if (not isinstance(instances, list) or not 1 <= len(instances) <= 24
            or not isinstance(edges, list) or len(edges) > 64
            or not isinstance(uncertainty, list) or len(uncertainty) != len(instances)
            or not isinstance(keepouts, list) or not 1 <= len(keepouts) <= 12
            or not _int(plan.get("minimum_nominal_static_clearance_um"), 0, MAX_UM)):
        return _hold("STATIC_SCREEN_BUDGET_OR_MISSING_KEEP_OUT", ghash)
    indexed = {}
    for inst in instances:
        if (not isinstance(inst, dict) or not isinstance(inst.get("instance_id"), str)
                or inst["instance_id"] in indexed or not isinstance(inst.get("bounds_mm"), dict)):
            return _hold("UNRESOLVED_COMPOSITION_REGION", ghash)
        indexed[inst["instance_id"]] = inst
    errors = {}
    for row in uncertainty:
        if (not isinstance(row, dict)
                or set(row) != {"instance_id", "max_abs_translation_error_um"}
                or row.get("instance_id") not in indexed
                or row.get("instance_id") in errors
                or not _vec(row.get("max_abs_translation_error_um"))):
            return _hold("INVALID_OR_DUPLICATE_REGION_TOLERANCE", ghash)
        errors[row["instance_id"]] = row["max_abs_translation_error_um"]
    if set(errors) != set(indexed):
        return _hold("INCOMPLETE_REGION_TOLERANCES", ghash)
    try:
        envelopes = {iid: _envelope(inst["bounds_mm"], errors[iid])
                     for iid, inst in indexed.items()}
    except (ValueError, KeyError, TypeError):
        return _hold("INVALID_STATIC_SOURCE_ENVELOPE", ghash)
    analyses = []
    for edge in edges:
        if not isinstance(edge, dict):
            return _hold("INVALID_INTERFACE", ghash)
        src, dst = edge.get("from"), edge.get("to")
        contact = edge.get("exact_convex_contact")
        if src not in indexed or dst not in indexed or not isinstance(contact, dict):
            return _hold("UNBOUND_INTERFACE_REGION", ghash)
        if contact.get("relation") != "FACE_CONTACT":
            return _hold("NO_NOMINAL_FACE_FOR_TOLERANCE_SCREEN", ghash)
        normal = _normal_axis(contact.get("directed_face_normals_from_a_to_b"))
        if normal is None:
            return _hold("OBLIQUE_OR_AMBIGUOUS_FACE_REQUIRES_NEW_METHOD", ghash)
        axis, sign = normal
        budget = errors[src][axis] + errors[dst][axis]
        lateral = [errors[src][i] + errors[dst][i] for i in range(3) if i != axis]
        analyses.append({
            "from": src, "to": dst,
            "nominal_relation": "FACE_CONTACT",
            "nominal_face_area_mm2_exact": contact.get("face_area_mm2_exact"),
            "normal_axis": "xyz"[axis],
            "normal_sign_source_to_target": sign,
            "possible_normal_gap_um": budget,
            "possible_normal_interference_um": budget,
            "max_lateral_relative_shift_um": lateral,
            "guaranteed_real_contact": False,
            "actual_interface_tolerance_measured": False,
        })
    ids = set()
    zones = []
    for zone in keepouts:
        if (not isinstance(zone, dict)
                or set(zone) != {"id", "lower_um", "upper_um", "zone_kind"}
                or not isinstance(zone.get("id"), str) or ID.fullmatch(zone["id"]) is None
                or zone["id"] in ids or zone.get("zone_kind") != "SYNTHETIC_FIXED_KEEP_OUT"
                or not _vec(zone.get("lower_um"), -1_000_000_000, 1_000_000_000)
                or not _vec(zone.get("upper_um"), -1_000_000_000, 1_000_000_000)
                or not all(a < b for a, b in zip(zone["lower_um"], zone["upper_um"]))):
            return _hold("INVALID_OR_DUPLICATE_KEEP_OUT", ghash)
        ids.add(zone["id"])
        zones.append(zone)
    checks = []
    risks = []
    for zone in sorted(zones, key=lambda x: x["id"]):
        for iid in sorted(envelopes):
            gap, gaps = _gap_lower_bound_um(envelopes[iid], zone)
            state = ("STATIC_ENVELOPES_SEPARATED" if gap >= plan["minimum_nominal_static_clearance_um"]
                     and gap > 0 else "POTENTIAL_STATIC_KEEP_OUT_CONFLICT")
            checks.append({
                "instance_id": iid, "keepout_id": zone["id"],
                "conservative_axis_gap_lower_bound_um": gap,
                "individual_axis_gap_lower_bounds_um": gaps,
                "review_state": state,
                "moving_head_or_toolpath_clearance_verified": False,
            })
            if state != "STATIC_ENVELOPES_SEPARATED":
                risks.append(f"{iid}:{zone['id']}")
    response = {
        "schema": RESULT_SCHEMA,
        "state": "SCREENED_STATIC_DIGITAL_ONLY" if not risks else "HOLD",
        "hold_codes": (
            ["REAL_MACHINE_GEOMETRY_UNVERIFIED", "TOOL_SWEEP_NOT_MODELLED",
             "ACTUAL_PLACEMENT_ERROR_AND_CURE_DISTORTION_UNMEASURED"]
            + (["POTENTIAL_STATIC_KEEP_OUT_CONFLICT"] if risks else [])
        ),
        "geometry_composite_sha256": ghash,
        "manufacturing_ir_ref": ref,
        "manufacturing_ir_configuration_hash": cfg,
        "screen_kind": "STATIC_CONSERVATIVE_AABB_ONLY",
        "source_input_sha256": digest(plan),
        "instance_uncertainties": [
            {"instance_id": iid, "max_abs_translation_error_um": errors[iid],
             "expanded_nominal_bounds_um": envelopes[iid]}
            for iid in sorted(errors)
        ],
        "interface_uncertainty": sorted(analyses, key=lambda x: (x["from"], x["to"])),
        "static_keepout_results": checks,
        "collision_risk_identifiers": risks,
        "static_keepout_sources_authenticated": False,
        "physical_tolerances_verified": False,
        "moving_toolpaths_evaluated": False,
        "physical_clearance_authorised": False,
        "machine_authorised": False,
        "mint_authorised": False,
        "commercial_release_authorised": False,
    }
    response["screen_sha256"] = digest({k: v for k, v in response.items() if k != "screen_sha256"})
    return response
