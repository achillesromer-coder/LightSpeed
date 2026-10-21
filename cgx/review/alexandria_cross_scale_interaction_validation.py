"""Read-only Alexandria cross-scale operator projection and conservative checks.

References existing CGX VGK operators. Does not model orbit, energy devices,
radio receivers, physical deployment, network activation or owner DBR admission.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[2]
REVIEW = "cgx/review/alexandria_cross_scale_interaction_projection_20261021.json"
ATLAS = "cgx/component_atlas/type1_volumetric_kernel_v0_1.json"
EXPECTED_KERNELS = {"VGK-019", "VGK-020", "VGK-021", "VGK-037", "VGK-039"}
HOLD = "SOURCE_ONLY_NOT_PHYSICAL_ACCEPTANCE"


class FrontierHold(ValueError):
    """Candidate input or claim is insufficient to establish a qualified result."""


def _read(root: Path, relative: str) -> tuple[dict, str]:
    raw = (root / relative).read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise FrontierHold("SOURCE_OBJECT_REQUIRED")
    return data, hashlib.sha256(raw).hexdigest()


def qualified_projection(root: Path = ROOT) -> dict:
    projection, source_sha = _read(root, REVIEW)
    atlas, atlas_sha = _read(root, ATLAS)
    if projection.get("parent") != "Cognigrex.cgx" or projection.get("classification") != "SOURCE_ONLY_REVIEW_NOT_CANONICAL":
        raise FrontierHold("UNEXPECTED_PARENT_OR_AUTHORITY")
    record_ids = {r["kernel_id"] for r in atlas.get("records", [])}
    if not EXPECTED_KERNELS.issubset(record_ids):
        raise FrontierHold("PARENT_KERNEL_MISSING")
    if set(projection["reused_kernel_ids"]) != EXPECTED_KERNELS:
        raise FrontierHold("DUPLICATE_OR_MISSING_KERNEL_REFERENCE")
    if len({r["family"] for r in projection["families"]}) != len(projection["families"]):
        raise FrontierHold("DUPLICATE_FAMILY")
    if len({r["id"] for r in projection["frontier_records"]}) != len(projection["frontier_records"]):
        raise FrontierHold("DUPLICATE_FRONTIER")
    for family in projection["families"]:
        if not set(family["existing_kernels"]).issubset(EXPECTED_KERNELS):
            raise FrontierHold("UNVERIFIED_NEW_SOLVER")
        if family["physical_status"] not in {"SYMBOLIC_ONLY", "SOURCE_LINKED_NOT_TESTED", "HYPOTHESIS_MODEL_ONLY", "SOURCE_AND_POLICY_REVIEW_ONLY"}:
            raise FrontierHold("INVALID_PHYSICAL_ACCEPTANCE")
        if not family.get("domain_specific") or not family.get("reuse"):
            raise FrontierHold("LOSS_OF_DOMAIN_CONSTRAINTS")
    for item in projection["frontier_records"]:
        if item.get("grade") not in {"SPECULATIVE_UNPROVEN", "SPECULATIVE_UNPROVEN_AS_STATED",
                                    "DOMAIN_MISMATCH_UNPROVEN", "GEOMETRIC_ANALOGY_ONLY",
                                    "PROGRAMME_VISION_UNPROVEN",
                                    "KNOWN_PRINCIPLE_HYPOTHESIS_FOR_LOCAL_IMPLEMENTATION"}:
            raise FrontierHold("UNSUPPORTED_PHYSICAL_PROMOTION")
        if not item.get("requires") or not item.get("hold"):
            raise FrontierHold("MISSING_FALSIFICATION_OR_GATE")
    gates = projection["authority_gates"]
    if (gates.get("public_issue"), gates.get("native_peer_issue")) != (158, 161):
        raise FrontierHold("PROTECTED_GATE_MISSING")
    if gates.get("public_release_authorised") is not False or gates.get("canonical_promotion") is not False:
        raise FrontierHold("PUBLIC_OR_CANONICAL_PROMOTION_DENIED")
    if gates.get("australian_network_enabled") is not False or gates.get("other_countries_enabled") is not False:
        raise FrontierHold("UNVERIFIED_NETWORK_ENABLED")
    return {
        "schema": "CGX-ALEXANDRIA-CROSS-SCALE-READ-MODEL/0.1",
        "parent": projection["parent"],
        "operator_families": len(projection["families"]),
        "unqualified_frontiers": len(projection["frontier_records"]),
        "existing_kernel_refs": sorted(EXPECTED_KERNELS),
        "source_sha256": {REVIEW: source_sha, ATLAS: atlas_sha},
        "rights": "LINKED_SOURCE_ONLY_NOT_RIGHTS_CLEARED",
        "state": HOLD, "public_release_authorised": False,
        "native_signed_peer_verified": False, "host_receipt_verified": False,
        "model_execution_performed": False,
    }


def _finite_nonnegative(value: object, label: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise FrontierHold("NONFINITE_OR_NEGATIVE_" + label)
    return float(value)


def check_conservation_ledger(
    *, source: Mapping[str, float], disposition: Mapping[str, float],
    unit: str, relative_tolerance: float = 1e-9
) -> dict:
    """Check a *reported* conserved quantity, not an independent measurement.

    Caller must provide sources and all sinks, including loss, residual and
    leakage. Passing an algebraic ledger cannot establish instrument accuracy.
    """
    if unit not in {"kg", "J"} or not source or not disposition:
        raise FrontierHold("MISSING_SOURCE_SINK_OR_UNIT")
    if not 0 < relative_tolerance <= 1e-6:
        raise FrontierHold("UNSAFE_RESIDUAL_TOLERANCE")
    in_total = sum(_finite_nonnegative(v, "SOURCE") for v in source.values())
    out_total = sum(_finite_nonnegative(v, "DISPOSITION") for v in disposition.values())
    if not math.isclose(in_total, out_total, rel_tol=relative_tolerance, abs_tol=0):
        raise FrontierHold("CONSERVATION_RESIDUAL_NOT_CLOSED")
    return {"unit": unit, "reported_input": in_total, "reported_disposition": out_total,
            "status": "ALGEBRAIC_BALANCE_ONLY_NO_MEASURED_CAPABILITY",
            "independent_measurement": False, "useful_energy_proven": False}


def passive_sensing_input_state(
    *, reference_measured: bool, surveillance_measured: bool,
    bandwidth_hz: float, baseline_m: float, snr_db: float
) -> str:
    if reference_measured is not True or surveillance_measured is not True:
        raise FrontierHold("MISSING_DIRECT_AND_REFLECTED_REFERENCE")
    if _finite_nonnegative(bandwidth_hz, "BANDWIDTH") <= 0 or _finite_nonnegative(baseline_m, "BASELINE") <= 0:
        raise FrontierHold("BISTATIC_GEOMETRY_OR_BANDWIDTH_MISSING")
    if type(snr_db) not in (int, float) or not math.isfinite(snr_db):
        raise FrontierHold("SNR_UNMEASURED")
    return "INPUT_DECLARED_TRACKING_AND_FALSE_ALARM_TEST_NOT_RUN"


def orbital_deposition_state(*, epoch_and_frame: str, relative_velocity_m_s: float,
                            capture_model_verified: bool, measured_dissipation: bool) -> str:
    if not epoch_and_frame or "/" not in epoch_and_frame:
        raise FrontierHold("ORBIT_TIME_FRAME_MISSING")
    _finite_nonnegative(relative_velocity_m_s, "RELATIVE_VELOCITY")
    if not capture_model_verified or not measured_dissipation:
        raise FrontierHold("NEARBY_MATERIAL_IS_NOT_CAPTURE_PROOF")
    return "MODEL_INPUT_COMPLETE_ONLY_TRAJECTORY_AND_RISK_STILL_UNQUALIFIED"
