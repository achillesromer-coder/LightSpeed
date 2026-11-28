"""Bottom-up source-scoped CGX digital composite and reverse dependency audits."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from cgx.manufacturing import compile_component, find_archetype, load_default_atlas
from cgx.manufacturing.compiler import _canonical_hash
from cgx.manufacturing.digital_service_stack import (
    DEPS, STAGE_ORDER, compile_digital_service_stack, verify_digital_service_stack_backwards,
)

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "cgx/manufacturing"


def inputs():
    ir = compile_component(find_archetype(load_default_atlas(), "PN rectifier diode"),
                           build_id="pc01-three-layer-coupon")
    geometry = json.loads((DIR / "printspace_composite_pilot_v0_1.json").read_text())
    selection = json.loads((DIR / "pc01_interface_witness_plan_v0_1.json").read_text())
    geometry["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
    selection["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
    assert ir["cgx_uri"] == geometry["manufacturing_ir_ref"] == selection["manufacturing_ir_ref"]
    return ir, geometry, selection


def compile_pilot():
    return compile_digital_service_stack(*inputs())


def back(bundle, inputs_tuple=None, process_packet=None):
    return verify_digital_service_stack_backwards(bundle, *(inputs_tuple or inputs()), process_packet)


def test_twelve_service_nodes_one_canonical_ir_and_no_execution():
    ir, geometry, selection = inputs()
    s = compile_digital_service_stack(ir, geometry, selection)
    assert s["state"] == "DIGITAL_STACK_REVIEW_ONLY_PHYSICAL_HOLD"
    assert s["digital_reference_checks"] is True
    assert s["region_count"] == 3
    assert s["distinct_source_shapes"] == 2
    assert s["interface_count"] == 2
    assert s["independent_witness_candidates"] == 4
    assert s["nominal_sum_volume_mm3_exact"] == "64"
    assert s["physical_union_volume_mm3"] is None
    assert s["mass_and_density"] is None
    assert s["canonical_ir"]["configuration_sha256"] == ir["configuration_hash"]
    assert s["canonical_ir"]["uri"] == ir["cgx_uri"]
    assert [x["id"] for x in s["layers"]] == list(STAGE_ORDER)
    assert len(s["layers"]) == 12
    assert s["reverse_replay_order"] == list(reversed(STAGE_ORDER))
    assert "NATIVE_SOURCE_AND_RIGHTS_NOT_ADMITTED" in s["hold_codes"]
    assert "PROCESS_PACKET_NOT_BOUND" in s["hold_codes"]
    assert s["load_mode"] == "H0_NONHYDRATING"
    for flag in ("physically_qualified", "real_source_body_authenticated", "native_dbr_written",
                 "machine_authorised", "mint_authorised", "commercial_release_authorised"):
        assert s[flag] is False


def test_back_down_full_round_trip_by_original_inputs():
    bundle = compile_pilot()
    audit = back(bundle)
    assert audit["state"] == "PASS_DIGITAL_ONLY"
    assert audit["mismatch_layers"] == []
    assert audit["declared_manifest_sha256"] == bundle["manifest_sha256"]
    assert audit["source_replay_manifest_sha256"] == bundle["manifest_sha256"]
    assert audit["manifest_matched"] is True
    assert audit["reverse_order"][0] == "A0_AUTHORITY_HOLD"
    assert audit["reverse_order"][-1] == "R0_SOURCE"
    for flag in ("physical_measurements_verified", "external_source_bodies_or_rights_authenticated",
                 "machine_authorised", "native_dbr_written", "mint_authorised",
                 "commercial_release_authorised"):
        assert audit[flag] is False


def test_every_service_node_depends_on_prior_source_nodes_and_is_unique():
    s = compile_pilot()
    names = {x["id"]: i for i, x in enumerate(s["layers"])}
    assert len(set(names)) == len(STAGE_ORDER)
    for row in s["layers"]:
        deps = row["depends_on"]
        assert [d["id"] for d in deps] == list(DEPS[row["id"]])
        assert all(names[d["id"]] < names[row["id"]] for d in deps)
        assert len(row["node_sha256"]) == len(row["payload_sha256"]) == 64


def test_deterministic_across_dict_key_reordering():
    ir, geometry, selections = inputs()
    one = compile_digital_service_stack(ir, geometry, selections)
    two = compile_digital_service_stack(
        dict(reversed(list(ir.items()))),
        dict(reversed(list(geometry.items()))),
        dict(reversed(list(selections.items()))),
    )
    assert one == two


@pytest.mark.parametrize("key", ["node_sha256", "payload_sha256", "state", "source_owner"])
def test_back_down_detects_any_claimed_service_node_change(key):
    b=compile_pilot()
    item = next(x for x in b["layers"] if x["id"] == "G1_EXACT_CONTACT")
    item[key] = "FORGED"
    audit=back(b)
    assert audit["state"] == "HOLD"
    assert "G1_EXACT_CONTACT" in audit["mismatch_layers"]
    assert not audit["manifest_matched"]


def test_back_down_detects_broken_dependency_link():
    b=compile_pilot()
    node=next(x for x in b["layers"] if x["id"] == "Q0_WITNESS_COUPONS")
    node["depends_on"][0]["sha256"] = "0"*64
    audit = back(b)
    assert audit["state"] == "HOLD"
    assert "Q0_WITNESS_COUPONS" in audit["mismatch_layers"]


def test_back_down_detects_missing_or_duplicate_services():
    b=compile_pilot()
    b["layers"].pop()
    assert back(b)["state"] == "HOLD"
    duplicate=compile_pilot()
    duplicate["layers"][0] = copy.deepcopy(duplicate["layers"][1])
    assert back(duplicate)["state"] == "HOLD"


def test_back_down_detects_renamed_source_and_changed_geometry():
    base=compile_pilot()
    ir,geo,sel=inputs()
    geo["source_shapes"][0]["source_ref"] = "DIFFERENT-SYNTHETIC-GEOMETRY"
    assert back(base, (ir,geo,sel))["state"] == "HOLD"


def test_back_down_rejects_source_row_or_graph_revision_mismatch():
    b=compile_pilot()
    ir,g,s=inputs()
    s["region_selections"][0]["directional_sha256"]="0"*64
    audit=back(b, (ir,g,s))
    assert audit["state"]=="HOLD"


def test_back_down_rejects_unadmitted_raphael_shape_and_174_sentinel():
    ir,g,s=inputs()
    g["source_shapes"][0]["t173_position"]=173
    assert compile_digital_service_stack(ir,g,s)["state"]=="HOLD_DIGITAL_INPUT"
    g["source_shapes"][0]["t173_position"]=174
    assert compile_digital_service_stack(ir,g,s)["state"]=="HOLD_DIGITAL_INPUT"


def test_graph_mutation_with_recomputed_ir_hash_cannot_inherit_old_geometry_or_coupon():
    ir,g,s=inputs()
    ir["blockers"] = ["SYNTHETIC-CHANGE"]
    ir["configuration_hash"]=_canonical_hash({k:v for k,v in ir.items() if k!="configuration_hash"})
    assert compile_digital_service_stack(ir,g,s)["hold_codes"]==["GEOMETRY_BUILD_REF_STALE"]
    g["manufacturing_ir_configuration_hash"]=ir["configuration_hash"]
    assert compile_digital_service_stack(ir,g,s)["hold_codes"]==["WITNESS_BUILD_REF_STALE"]


def test_independent_reverse_must_use_original_canonical_inputs():
    b=compile_pilot()
    ir,g,s=inputs()
    ir["blockers"]= ["SYNTHETIC-PROOF-NOT-CLOSED"]
    audit=back(b,(ir,g,s))
    assert audit["state"]=="HOLD"


def test_forged_machine_or_mint_authority_fails_reverse():
    b=compile_pilot()
    b["machine_authorised"]=True
    assert back(b)["state"]=="HOLD"
    b=compile_pilot()
    b["physically_qualified"]=True
    assert back(b)["state"]=="HOLD"
    b=compile_pilot()
    b["native_dbr_written"]=True
    assert back(b)["state"]=="HOLD"


def test_optional_process_still_held_on_external_measurements():
    ir,g,s=inputs()
    packet={
        "schema":"CGX-PRINTSPACE-REVIEW-INPUT/0.1",
        "article_id":"DIGITAL-COUPON-ONLY",
        "manufacturing_ir_ref":ir["cgx_uri"],
        "manufacturing_ir_configuration_hash":ir["configuration_hash"],
        "source_revision":"SYNTHETIC",
        "geometry":{"catalogue_position":1,"source_id":"SYNTHETIC-GEO","units":"mm",
                    "coordinate_frame":"XYZ","admission_receipt":"SYNTHETIC","rights_ref":"SYNTHETIC",
                    "sha256":"a"*64,"minimum_feature_mm":1},
        "rights":{"status":"RESTRICTED","licence_ref":"TEST-ONLY"},
        "machine":{"physical_state":"NOT_BUILT","safety_control":"INDEPENDENT_C0",
                   "initial_atmosphere":"AMBIENT","tool_ids":["TEST1"],"minimum_feature_mm":1},
        "material_lots":{},
        "interfaces":[],
        "operations":[{"id":"prep","kind":"PREPARE","depends_on":[]}],
    }
    result=compile_digital_service_stack(ir,g,s,packet)
    assert result["state"]=="DIGITAL_STACK_REVIEW_ONLY_PHYSICAL_HOLD"
    assert "PROCESS_DECLARATIONS_NOT_INDEPENDENTLY_ATTESTED" in result["hold_codes"]
    assert result["physically_qualified"] is False
    assert back(result, (ir,g,s), packet)["state"]=="PASS_DIGITAL_ONLY"
    packet["source_revision"]="MUTATED"
    assert back(result,(ir,g,s),packet)["state"]=="HOLD"


def test_malformed_oversize_and_nonfinite_inputs_fail_closed():
    ir,g,s=inputs()
    assert compile_digital_service_stack(ir,[],s)["state"]=="HOLD_DIGITAL_INPUT"
    s["unknown"]=float("inf")
    assert "SERVICE_INPUT_NONCANONICAL_OR_OVERSIZE" in compile_digital_service_stack(ir,g,s)["hold_codes"]
    ir,g,s=inputs()
    g["unknown"]="x"*(1024*1024)
    assert "SERVICE_INPUT_NONCANONICAL_OR_OVERSIZE" in compile_digital_service_stack(ir,g,s)["hold_codes"]


def test_invalid_ir_attempting_hardware_or_physical_activation_denied():
    ir,g,s=inputs()
    ir["physical_execution"]=True
    ir["configuration_hash"]=_canonical_hash({k:v for k,v in ir.items() if k!="configuration_hash"})
    g["manufacturing_ir_configuration_hash"]=ir["configuration_hash"]
    s["manufacturing_ir_configuration_hash"]=ir["configuration_hash"]
    assert "PHYSICAL_EXECUTION_IN_DIGITAL_IR" in compile_digital_service_stack(ir,g,s)["hold_codes"]


def test_invalid_or_missing_bundle_cannot_self_validate():
    ir,g,s=inputs()
    assert verify_digital_service_stack_backwards({},ir,g,s)["state"]=="HOLD"
    assert verify_digital_service_stack_backwards([],ir,g,s)["state"]=="HOLD"
    b=compile_pilot()
    b["manifest_sha256"]="0"*64
    assert back(b)["state"]=="HOLD"


def test_canonical_scope_service_selection_stays_input_bound():
    ir,g,s=inputs()
    out=compile_digital_service_stack(ir,g,s)
    assert out["selected_service_scopes"] == sorted(ir["scope_decision"]["included"])
    assert out["service_scope_not_empirically_modelled"] is True
    assert out["mass_and_density"] is None
    assert out["physically_qualified"] is False


def static_plan_inputs():
    ir, geometry, selection = inputs()
    plan = json.loads((DIR / "pc01_tolerance_static_screen_v0_1.json").read_text())
    plan["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
    return ir, geometry, selection, plan


def test_optional_static_screen_preserves_legacy_twelve_stage_root():
    old = compile_pilot()
    assert old["manifest_sha256"] == "ca600888ab97bbe4a9b7d641d6b66733463f482c97a16bf84d132da457c333e9"
    assert "static_screen_sha256" not in old
    assert "clearance_plan" not in old["input_sha256s"]
    assert back(old)["state"] == "PASS_DIGITAL_ONLY"


def test_static_screen_binds_same_canonical_ir_and_reverse_provenance():
    ir, geo, sel, plan = static_plan_inputs()
    result = compile_digital_service_stack(ir, geo, sel, clearance_plan=plan)
    assert result["state"] == "DIGITAL_STACK_REVIEW_ONLY_PHYSICAL_HOLD"
    assert result["static_screen_state"] == "SCREENED_STATIC_DIGITAL_ONLY"
    assert result["static_screen_risks"] == []
    assert len(result["layers"]) == 12
    assert result["independent_witness_candidates"] == 4
    assert result["nominal_sum_volume_mm3_exact"] == "64"
    assert result["static_screen_sha256"] != result["geometry_sha256"]
    assert result["input_sha256s"]["clearance_plan"]
    assert "STATIC_SCREEN_NOT_PHYSICAL_TOOLPATH_CERTIFICATION" in result["hold_codes"]
    assert result["machine_authorised"] is False
    audit = verify_digital_service_stack_backwards(
        result, ir, geo, sel, clearance_plan=plan)
    assert audit["state"] == "PASS_DIGITAL_ONLY"
    assert audit["external_source_bodies_or_rights_authenticated"] is False


def test_static_screen_drives_g1_e0_and_s0_only_when_requested():
    ir, geo, sel, plan = static_plan_inputs()
    legacy = compile_digital_service_stack(ir, geo, sel)
    bounded = compile_digital_service_stack(ir, geo, sel, clearance_plan=plan)
    changed = {x["id"] for x, y in zip(legacy["layers"], bounded["layers"])
               if x["node_sha256"] != y["node_sha256"]}
    assert "R0_SOURCE" not in changed
    assert "G0_NOMINAL_SOLIDS" not in changed
    assert "G1_EXACT_CONTACT" in changed
    assert "E0_ENVIRONMENT_CONTROL" in changed
    assert "S0_FUNCTIONAL_SERVICE_SCOPES" in changed
    assert "A0_AUTHORITY_HOLD" in changed
    assert bounded["load_mode"] == "H0_NONHYDRATING"
    assert not bounded["native_dbr_written"]


def test_static_keepout_collision_propagates_a_hard_hold():
    ir, geo, sel, plan = static_plan_inputs()
    plan["static_keepouts"][0]["lower_um"][0] = 4000
    plan["static_keepouts"][0]["upper_um"][0] = 4500
    out = compile_digital_service_stack(ir, geo, sel, clearance_plan=plan)
    assert out["state"] == "HOLD_DIGITAL_INPUT"
    assert "STATIC_TOLERANCE_OR_KEEP_OUT_UNRESOLVED" in out["hold_codes"]
    assert out["machine_authorised"] is False


def test_static_plan_revision_detected_by_reverse_audit_even_if_self_hashed():
    ir, geo, sel, plan = static_plan_inputs()
    result = compile_digital_service_stack(ir, geo, sel, clearance_plan=plan)
    assert result["state"] == "DIGITAL_STACK_REVIEW_ONLY_PHYSICAL_HOLD"
    plan["instance_uncertainties"][0]["max_abs_translation_error_um"][2] += 20
    audit = verify_digital_service_stack_backwards(
        result, ir, geo, sel, clearance_plan=plan)
    assert audit["state"] == "HOLD"
    assert audit["manifest_matched"] is False


def test_absent_static_plan_cannot_validate_stronger_manifest():
    ir, geo, sel, plan = static_plan_inputs()
    result = compile_digital_service_stack(ir, geo, sel, clearance_plan=plan)
    assert verify_digital_service_stack_backwards(
        result, ir, geo, sel)["state"] == "HOLD"


def test_stale_static_ir_hash_and_untrusted_real_machine_evidence_rejected():
    ir, geo, sel, plan = static_plan_inputs()
    plan["manufacturing_ir_configuration_hash"] = "0"*64
    assert compile_digital_service_stack(ir, geo, sel, clearance_plan=plan)["state"] == "HOLD_DIGITAL_INPUT"
    ir, geo, sel, plan = static_plan_inputs()
    plan["physical_clearance_authorised"] = True
    assert compile_digital_service_stack(ir, geo, sel, clearance_plan=plan)["state"] == "HOLD_DIGITAL_INPUT"
