"""Source-bound directional coupon planning; digital-only/negative authority tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from cgx.manufacturing.composition import compile_geometry_composition
from cgx.manufacturing.interface_qualification import plan_interface_witnesses

ROOT = Path(__file__).resolve().parents[1]
GEOMETRY = ROOT / "cgx/manufacturing/printspace_composite_pilot_v0_1.json"
SELECTION = ROOT / "cgx/manufacturing/pc01_interface_witness_plan_v0_1.json"


def fixture():
    g = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    s = json.loads(SELECTION.read_text(encoding="utf-8"))
    s["manufacturing_ir_configuration_hash"] = "a" * 64  # syntactic plan hash, NOT independent source proof
    result = compile_geometry_composition(g)
    assert result["state"] == "REVIEW_ONLY"
    assert result["geometry_composite_hash"] == s["geometry_composite_hash"]
    return result, s


def hold_codes(geo, selection):
    return plan_interface_witnesses(geo, selection)["hold_codes"]


def test_pilot_generates_four_distinct_bidirectional_witness_plans():
    geo, sel = fixture()
    result = plan_interface_witnesses(geo, sel)
    assert result["state"] == "PLAN_READY_UNQUALIFIED"
    assert result["plan_sha256"] and len(result["plan_sha256"]) == 64
    plan = result["plan"]
    assert len(plan["source_regions"]) == 3
    assert len(plan["interfaces"]) == 2
    assert sorted(r["planning_basis_class"] for r in plan["source_regions"]) == [
        "CONDUCTOR_INTERCONNECT", "DIELECTRIC_ISOLATION", "STRUCTURE_DATUM"
    ]
    assert {r["matrix_id"] for r in plan["source_regions"]} == {"T1M-0257", "T1M-0409", "T1M-0039"}
    assert {r["lot_passport"] for r in plan["source_regions"]} == {"UNBOUND_NO_OBSERVED_LOT"}
    routes = [direction for iface in plan["interfaces"] for direction in iface["directions"]]
    assert len(routes) == 4
    assert len({route["coupon_candidate_id"] for route in routes}) == 4
    assert {route["direction"] for route in routes} == {"SOURCE_TO_TARGET", "TARGET_TO_SOURCE"}
    assert all(iface["geometric_area_mm2_exact"] == "16" for iface in plan["interfaces"])
    assert all(route["target_geometric_face_area_mm2_exact"] == "16" for route in routes)
    assert all(route["raw_measurement_receipt"] is None for route in routes)
    assert all(route["observed_lots"] is None and route["tool_calibration"] is None for route in routes)
    assert all(route["verification"] == "UNMEASURED_NOT_QUALIFIED" for route in routes)
    assert "REVERSE_DIRECTION_COUPONS_NOT_MEASURED" in result["hold_codes"]
    for forbidden in ("material_interface_qualified","evidence_independently_verified","machine_authorised",
                      "native_dbr_written","mint_authorised","commercial_release_authorised"):
        assert result[forbidden] is False


def test_source_to_target_reverse_is_not_reused():
    geo, sel = fixture()
    p = plan_interface_witnesses(geo, sel)["plan"]["interfaces"][0]
    f, r = p["directions"]
    assert f["source_instance"] == p["interface_from"] and f["target_instance"] == p["interface_to"]
    assert r["source_instance"] == p["interface_to"] and r["target_instance"] == p["interface_from"]
    assert f["source_matrix_id"] != r["source_matrix_id"]
    assert f["coupon_candidate_id"] != r["coupon_candidate_id"]


def test_order_of_source_region_declarations_does_not_change_plan_digest():
    geo, sel = fixture()
    a = plan_interface_witnesses(geo, sel)
    sel["region_selections"].reverse()
    b = plan_interface_witnesses(geo, sel)
    assert a["plan_sha256"] == b["plan_sha256"]


@pytest.mark.parametrize("key,value,code", [
    ("evidence_state","QUALIFIED","UNTRUSTED_MEASURED_EVIDENCE"),
    ("evidence_state","MEASURED_DECLARED","UNTRUSTED_MEASURED_EVIDENCE"),
    ("source_scope","LOT_QUALIFIED","MATERIAL_SOURCE_CLAIM_ESCALATION"),
    ("source_revision","2026-11-21","SOURCE_REVISION_NOT_SNAPSHOT"),
    ("owner_projection_sha256","0"*64,"OWNER_MATRIX_PROJECTION_MISMATCH"),
    ("geometry_composite_hash","0"*64,"GEOMETRY_HASH_MISMATCH"),
    ("manufacturing_ir_configuration_hash",None,"CANONICAL_BUILD_HASH_UNBOUND"),
    ("manufacturing_ir_ref","cgx://manufacturing/build/another","CANONICAL_BUILD_MISMATCH"),
])
def test_untrusted_or_cross_build_selection_holds(key,value,code):
    g, p = fixture()
    p[key] = value
    assert code in hold_codes(g, p)


def test_row_hash_tamper_holds():
    g,p=fixture()
    p["region_selections"][0]["directional_sha256"] = "0"*64
    assert "OWNER_ROW_FINGERPRINT_MISMATCH" in hold_codes(g,p)


def test_cross_archetype_rebinding_holds():
    g,p=fixture()
    p["region_selections"][1]["archetype_id"] = "CGA-I-001"
    assert "OWNER_ROW_FINGERPRINT_MISMATCH" in hold_codes(g,p)


def test_duplicate_region_selection_holds():
    g,p=fixture()
    p["region_selections"][1]["instance_id"] = p["region_selections"][0]["instance_id"]
    assert "DUPLICATE_OR_UNKNOWN_REGION" in hold_codes(g,p)


def test_omitted_region_selection_holds():
    g,p=fixture()
    p["region_selections"].pop()
    assert "UNBOUND_REGION_SELECTION" in hold_codes(g,p)


def test_wrong_geometry_slot_cannot_be_relabelled():
    g,p=fixture()
    p["region_selections"][0]["material_slot"] = "fake"
    assert "MATERIAL_SLOT_MISMATCH" in hold_codes(g,p)


def test_untrusted_material_lot_receipt_in_selection_rejected():
    g,p=fixture()
    p["region_selections"][0]["material_lot_id"] = "CLAIMED-LOT"
    assert "UNEXPECTED_MATERIAL_DECLARATION" in hold_codes(g,p)


def test_invented_dbr_or_machine_approval_rejected():
    g,p=fixture()
    p["signed_dbr"] = "synthetic-owner-signature"
    assert "UNAUTHORISED_EVIDENCE_OR_EXECUTION_INPUT" in hold_codes(g,p)
    del p["signed_dbr"]
    p["machine_command"] = "MOVE_AXIS"
    assert "UNAUTHORISED_EVIDENCE_OR_EXECUTION_INPUT" in hold_codes(g,p)


def test_malformed_or_noncanonical_source_input_holds():
    g,p=fixture()
    assert "INVALID_PLAN_REQUEST" in hold_codes(g,["bad"])
    p["unserializable"] = object()
    assert "NONCANONICAL_PLAN_REQUEST" in hold_codes(g,p)


def test_source_index_must_be_integrity_preserving():
    g,p=fixture()
    p["owner_projection_sha256"] = "f"*64
    assert "OWNER_MATRIX_PROJECTION_MISMATCH" in hold_codes(g,p)


def test_geometry_must_match_exact_graph_hash():
    g,p=fixture()
    g["graph"]["interfaces"][0]["exact_convex_contact"]["face_area_mm2_exact"] = "99"
    assert "ALTERED_GEOMETRY_GRAPH" in hold_codes(g,p)


def test_load_h0_cannot_become_unverified_native_carrier():
    g,p=fixture()
    g["load_h0"]["native_admitted"] = True
    assert "LOAD_H0_NOT_SOURCE_ONLY" in hold_codes(g,p)


def test_unadmitted_t173_shape_cannot_qualify_a_witness():
    g,p=fixture()
    g["state"] = "HOLD"
    assert "GEOMETRY_NOT_REVIEWED" in hold_codes(g,p)


def test_geometry_region_without_face_contact_is_not_witnessable():
    g,p=fixture()
    g["graph"]["interfaces"][0]["exact_convex_contact"]["relation"] = "POINT_CONTACT"
    from cgx.manufacturing.composition import digest
    g["geometry_composite_hash"] = digest(g["graph"])
    g["load_h0"]["composite_sha256"] = g["geometry_composite_hash"]
    p["geometry_composite_hash"] = g["geometry_composite_hash"]
    assert "NO_FINITE_INTERFACE_FACE" in hold_codes(g,p)


def test_explicit_syntactic_configuration_hash_is_not_physical_authority():
    g,p=fixture()
    out=plan_interface_witnesses(g,p)
    assert out["state"] == "PLAN_READY_UNQUALIFIED"
    assert out["evidence_independently_verified"] is False
    assert out["native_dbr_written"] is False
    assert out["material_interface_qualified"] is False
