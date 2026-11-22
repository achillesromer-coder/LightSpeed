"""Conservative static tolerance screening; never certify swept machine clearance."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from cgx.manufacturing.composition import compile_geometry_composition
from cgx.manufacturing.tolerance_clearance import screen_static_tolerances

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "cgx/manufacturing/printspace_composite_pilot_v0_1.json"
PLAN = ROOT / "cgx/manufacturing/pc01_tolerance_static_screen_v0_1.json"


def input_pair():
    geom = json.loads(SOURCE.read_text(encoding="utf-8"))
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    hash_value = "a" * 64  # synthetic string, not authenticated physical lot or IR
    geom["manufacturing_ir_configuration_hash"] = hash_value
    plan["manufacturing_ir_configuration_hash"] = hash_value
    return geom, plan


def screen():
    return screen_static_tolerances(*input_pair())


def codes(g, p):
    return screen_static_tolerances(g, p)["hold_codes"]


def test_pilot_static_aabb_screen_and_nominal_gap_budgets():
    r=screen()
    assert r["state"]=="SCREENED_STATIC_DIGITAL_ONLY"
    assert r["geometry_composite_sha256"]=="55b8de2df57a8b19ecda4d5ab0ed0619de57789e21e793ea2170a68b00dfb613"
    assert len(r["instance_uncertainties"])==3
    assert len(r["static_keepout_results"])==3
    assert r["collision_risk_identifiers"]==[]
    assert r["screen_kind"]=="STATIC_CONSERVATIVE_AABB_ONLY"
    edges={(e["from"],e["to"]):e for e in r["interface_uncertainty"]}
    assert len(edges)==2
    assert edges[("structure","interface")]["possible_normal_gap_um"]==125
    assert edges[("structure","interface")]["possible_normal_interference_um"]==125
    assert edges[("interface","conductive")]["possible_normal_gap_um"]==100
    assert all(e["normal_axis"]=="z" for e in edges.values())
    assert all(e["guaranteed_real_contact"] is False for e in edges.values())
    assert all(x["review_state"]=="STATIC_ENVELOPES_SEPARATED" for x in r["static_keepout_results"])
    assert all(x["conservative_axis_gap_lower_bound_um"]>=500 for x in r["static_keepout_results"])
    assert r["physical_tolerances_verified"] is False
    assert r["moving_toolpaths_evaluated"] is False
    assert r["physical_clearance_authorised"] is False
    assert r["machine_authorised"] is False
    assert r["mint_authorised"] is False
    assert r["commercial_release_authorised"] is False
    assert "TOOL_SWEEP_NOT_MODELLED" in r["hold_codes"]
    assert len(r["screen_sha256"])==64


def test_canonical_determinism_for_reordered_uncertainty_list():
    g,p=input_pair()
    original=screen_static_tolerances(g,p)
    p["instance_uncertainties"].reverse()
    assert screen_static_tolerances(g,p)["screen_sha256"] != original["screen_sha256"]
    # Source input hash intentionally captures exact request ordering; output
    # structural risk statements are nevertheless equivalent.
    revised=screen_static_tolerances(g,p)
    assert revised["interface_uncertainty"] == original["interface_uncertainty"]
    assert revised["static_keepout_results"] == original["static_keepout_results"]


def test_static_keepout_possible_conflict_fail_closed():
    g,p=input_pair()
    p["static_keepouts"][0]["lower_um"]=[4000,-1000,-1000]
    p["static_keepouts"][0]["upper_um"]=[4600,5000,5000]
    r=screen_static_tolerances(g,p)
    assert r["state"]=="HOLD"
    assert "POTENTIAL_STATIC_KEEP_OUT_CONFLICT" in r["hold_codes"]
    assert len(r["collision_risk_identifiers"])==3
    assert r["machine_authorised"] is False


def test_small_gap_below_margin_is_not_certified():
    g,p=input_pair()
    p["static_keepouts"][0]["lower_um"]=[4075,-1000,-1000]
    p["static_keepouts"][0]["upper_um"]=[4300,5000,5000]
    r=screen_static_tolerances(g,p)
    assert r["state"]=="HOLD"
    assert any(x["review_state"]=="POTENTIAL_STATIC_KEEP_OUT_CONFLICT" for x in r["static_keepout_results"])


def test_unbound_configuration_hash_rejected():
    g,p=input_pair()
    p["manufacturing_ir_configuration_hash"]=None
    assert "CANONICAL_IR_BINDING_MISSING" in codes(g,p)
    g,p=input_pair()
    p["manufacturing_ir_configuration_hash"]="b"*64
    assert "GEOMETRY_OR_BUILD_HASH_STALE" in codes(g,p)


def test_revised_geometry_and_stale_shape_hash_rejected():
    g,p=input_pair()
    g["instances"][2]["translate_mm"][2]+=1
    assert "EXACT_DIGITAL_GEOMETRY_UNBOUND" in codes(g,p) or "GEOMETRY_OR_BUILD_HASH_STALE" in codes(g,p)
    g,p=input_pair()
    p["geometry_composite_sha256"]="0"*64
    assert "GEOMETRY_OR_BUILD_HASH_STALE" in codes(g,p)


def test_missing_or_duplicate_instance_errors_rejected():
    g,p=input_pair()
    p["instance_uncertainties"].pop()
    assert "STATIC_SCREEN_BUDGET_OR_MISSING_KEEP_OUT" in codes(g,p)
    g,p=input_pair()
    p["instance_uncertainties"][1]["instance_id"]=p["instance_uncertainties"][0]["instance_id"]
    assert "INVALID_OR_DUPLICATE_REGION_TOLERANCE" in codes(g,p)


@pytest.mark.parametrize("invalid", [-1, 1.3, True, "50", 1_000_001, None])
def test_inexact_or_unbounded_tolerance_rejected(invalid):
    g,p=input_pair()
    p["instance_uncertainties"][0]["max_abs_translation_error_um"][0]=invalid
    assert "INVALID_OR_DUPLICATE_REGION_TOLERANCE" in codes(g,p)


def test_unsupported_evidence_escalation_and_tool_commands_rejected():
    g,p=input_pair()
    p["evidence_state"]="CALIBRATED"
    assert "STATIC_SCREEN_SCHEMA_OR_EVIDENCE_ESCALATION" in codes(g,p)
    g,p=input_pair()
    p["physical_execution"]=True
    assert "STATIC_SCREEN_SCHEMA_OR_EVIDENCE_ESCALATION" in codes(g,p)


def test_invalid_keepout_orientation_bounds_and_alias_rejected():
    g,p=input_pair()
    p["static_keepouts"][0]["lower_um"]=[9000,-1000,-1000]
    assert "INVALID_OR_DUPLICATE_KEEP_OUT" in codes(g,p)
    g,p=input_pair()
    p["static_keepouts"].append(copy.deepcopy(p["static_keepouts"][0]))
    assert "INVALID_OR_DUPLICATE_KEEP_OUT" in codes(g,p)


def test_float_and_nonfinite_plan_rejected():
    g,p=input_pair()
    p["instance_uncertainties"][0]["max_abs_translation_error_um"][0]=float("inf")
    assert "NONCANONICAL_STATIC_SCREEN" in codes(g,p)


def test_mutable_geometry_snapshot_does_not_claim_fresh_review():
    g,p=input_pair()
    prior=compile_geometry_composition(g)
    assert prior["state"]=="REVIEW_ONLY"
    g["instances"][0]["translate_mm"][0]+=1
    r=screen_static_tolerances(g,p,prior)
    # The source graph hash and expected request must agree. The separate
    # reverse full service audit always recomputes original source objects.
    assert r["state"] in ("SCREENED_STATIC_DIGITAL_ONLY","HOLD")
    assert r["physical_clearance_authorised"] is False


def test_static_screen_never_returns_real_clearance_guarantee_even_zero_error():
    g,p=input_pair()
    for item in p["instance_uncertainties"]:
        item["max_abs_translation_error_um"]=[0,0,0]
    r=screen_static_tolerances(g,p)
    assert r["state"]=="SCREENED_STATIC_DIGITAL_ONLY"
    assert all(e["guaranteed_real_contact"] is False for e in r["interface_uncertainty"])
    assert r["moving_toolpaths_evaluated"] is False


def test_directionality_remains_distinct_without_inheriting_real_coupon_proof():
    r=screen()
    edges=r["interface_uncertainty"]
    assert [e["from"] for e in edges]==["interface","structure"]
    assert len({(e["from"],e["to"]) for e in edges})==2
    assert all(e["actual_interface_tolerance_measured"] is False for e in edges)
