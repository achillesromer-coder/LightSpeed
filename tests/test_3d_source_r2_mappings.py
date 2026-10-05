from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "desktop" / "LightSpeed_Runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from lightspeed_runtime.cgx_conversion_planner import compile_conversion_plan

TEMPLATES = ROOT / "cgx" / "domain_templates"
TYPE_REGISTRY = json.loads((TEMPLATES / "file_type_conversion_registry.json").read_text(encoding="utf-8"))
CONTRACT = json.loads((TEMPLATES / "file_conversion_contract.json").read_text(encoding="utf-8"))
FIRST_FILES = json.loads((TEMPLATES / "first_file_conversion_registry.json").read_text(encoding="utf-8"))
LINEAGE = json.loads((ROOT / "data" / "digital-twin" / "twin_record_source_lineage_2026-09-14.json").read_text(encoding="utf-8"))
PAYLOAD_DBR = json.loads((TEMPLATES / "payload_capsule_dbr_2026-10-05.json").read_text(encoding="utf-8"))
REMAINING_DBR = json.loads((TEMPLATES / "remaining_3d_dbr_summary_2026-10-05.json").read_text(encoding="utf-8"))
PRIORITY_BINDINGS = json.loads((TEMPLATES / "priority_3d_source_bindings_execution_2026-10-05.json").read_text(encoding="utf-8"))\nM1_PRECEDENCE = json.loads((TEMPLATES / "m1_configuration_precedence_2026-10-05.json").read_text(encoding="utf-8"))
LUKE4_RELATION = json.loads((TEMPLATES / "luke4_configuration_relation_2026-10-05.json").read_text(encoding="utf-8"))


def _plan(name: str, sha256: str, target: str):
    return compile_conversion_plan(
        file_name=name,
        source_sha256=sha256,
        source_ref=f"local-native:{name}",
        domain="romer",
        semantic_target=target,
        type_registry=TYPE_REGISTRY,
        conversion_contract=CONTRACT,
        first_file_registry=FIRST_FILES,
    )


def test_watchtower_native_fcstd_is_registered_r2_without_authority_transfer():
    plan = _plan(
        "InterSol - Watch Tower In Site Footprint.FCStd",
        "c476f9f2f9946ab8e99e58dd399aa7b02bac630c5d9336b80ef66f5f2a397321",
        "/romer/watchtower",
    )
    assert plan["semantic_state"] == "mapping_ready"
    assert plan["registered_mapping"]["mapping_id"] == "FF-WATCHTOWER-FCSTD-001"
    assert plan["registered_mapping"]["semantic_object_id"] == "WT-001"
    r2 = [stage for stage in plan["stages"] if stage["class"] == "R2_RECONSTRUCTED"][0]
    assert r2["state"] == "READY"
    assert plan["canonical_mutation"] is False
    assert plan["authority_transfer"] is False


def test_mark_iii_native_fcstd_is_registered_to_space_01_with_claim_ceiling():
    plan = _plan(
        "Mark III.FCStd",
        "4e9255b6c2149f3971aea1fad413c880fe693a6ffee194c2821901ae9e45349b",
        "/romer/mark-iii",
    )
    mapping = plan["registered_mapping"]
    assert plan["semantic_state"] == "mapping_ready"
    assert mapping["mapping_id"] == "FF-MARK3-FCSTD-001"
    assert mapping["semantic_object_id"] == "SPACE-01"
    assert mapping["parent_object_id"] == "T1-SPACE"
    assert mapping["source_structure"] == {
        "object_data_records": 474,
        "partdesign_bodies": 17,
        "pads": 90,
        "sketches": 49,
        "assemblies": 22,
    }
    assert "three appendage instances" in mapping["held_claims"]
    assert "Mark V mating CAD/ICD" in mapping["held_claims"]
    assert plan["authority_transfer"] is False


def test_lineage_records_execute_source_binding_without_promoting_held_semantics():
    records = {record["twin_id"]: record for record in LINEAGE["records"]}
    wt = records["watchtower"]
    assert wt["semantic_object_id"] == "WT-001"
    assert wt["first_file_mapping_id"] == "FF-WATCHTOWER-FCSTD-001"
    assert wt["source_binding_state"] == "R2_SOURCE_IDENTITY_BOUND / HELD_SEMANTICS_PRESERVED"
    assert wt["derived_configuration_reference"]["authority_transition"] is False

    mark3 = records["mark_iii"]
    assert mark3["semantic_object_id"] == "SPACE-01"
    assert mark3["parent_object_id"] == "T1-SPACE"
    assert mark3["geometry_authority"] == "MARK3_FCSTD_NATIVE_SOURCE"
    assert mark3["source_geometry_sha256"] == "4e9255b6c2149f3971aea1fad413c880fe693a6ffee194c2821901ae9e45349b"
    assert mark3["first_file_mapping_id"] == "FF-MARK3-FCSTD-001"
    assert "INTERLOCK_AND_MATING_HELD" in mark3["source_binding_state"]
    assert mark3["operations_binding"]["current_record_id"] == "COM-1668"
    assert mark3["operations_binding"]["current_object_id"] == "IP-01"
    assert mark3["operations_binding"]["semantic_child_record_id"] == "COM-0444"
    assert mark3["operations_binding"]["semantic_child_object_id"] == "SPACE-01"


def test_payload_capsule_native_fcstd_is_bound_to_space_07_dbr():
    plan = _plan(
        "Payload Capsule.FCStd",
        "9606755c4fff3d94ade1ed61ee41808e9a05237b6bdd857b09dcb067d6e0b61c",
        "/romer/payload-capsule",
    )
    mapping = plan["registered_mapping"]
    assert plan["semantic_state"] == "mapping_ready"
    assert mapping["mapping_id"] == "FF-PAYLOAD-CAPSULE-FCSTD-001"
    assert mapping["semantic_object_id"] == "SPACE-07"
    assert mapping["parent_object_id"] == "T1-SPACE"
    assert mapping["operations_record_id"] == "COM-1676"
    assert mapping["predecessor_source_sha256"] == "c5e69b673b6f01ee0a60e063f4a367c46057b6844f97d32c0a44ca3c8437c2c5"
    assert mapping["source_revision_summary"]["predecessor_objects"] == 55
    assert mapping["source_revision_summary"]["current_objects"] == 58
    assert mapping["source_revision_summary"]["engineering_scalar_changes"] == 9
    assert plan["authority_transfer"] is False


def test_payload_capsule_dbr_preserves_exact_transition_and_nonclaims():
    dbr = PAYLOAD_DBR
    assert dbr["semantic_object_id"] == "SPACE-07"
    assert dbr["operations_record_id"] == "COM-1676"
    assert dbr["source_authority"]["predecessor"]["sha256"] == "c5e69b673b6f01ee0a60e063f4a367c46057b6844f97d32c0a44ca3c8437c2c5"
    assert dbr["source_authority"]["current"]["sha256"] == "9606755c4fff3d94ade1ed61ee41808e9a05237b6bdd857b09dcb067d6e0b61c"
    transition = dbr["transition"]
    assert transition["object_count_delta"] == 3
    assert transition["added_objects"] == ["Pad022", "Pad023", "Pad024"]
    assert transition["removed_objects"] == []
    assert transition["normalized_property_change_count"] == 22
    assert transition["operationally_relevant_change_count"] == 12
    assert transition["engineering_scalar_change_count"] == 9
    assert transition["body_transition"]["tip_old"] == "Pad021"
    assert transition["body_transition"]["tip_new"] == "Pad024"
    assert [row["object"] for row in transition["added_pad_chain"]] == ["Pad022", "Pad023", "Pad024"]
    assert dbr["canonical_effect"]["semantic_binding_created"] is True
    assert dbr["canonical_effect"]["physical_authority"] is False
    assert dbr["canonical_effect"]["manufacturing_authority"] is False
    assert dbr["canonical_effect"]["certification_authority"] is False
    assert dbr["canonical_effect"]["public_release_authorized"] is False


def test_remaining_priority_fcstd_sources_are_registered_to_existing_ids():
    cases = [
        ("SEQLD Pilot Base km Stretch.FCStd", "98865b2a2bc805f7faa4df45db94d67cc6ea82c83e0eea9885f4a82a5739746b", "/romer/m1/base-km", "FF-M1-BASEKM-FCSTD-001", "T1-M1", "COM-0368"),
        ("SEQLD Pilot Build W Central Column A1.FCStd", "7878082116b0017cfe64e26a6f26e380b954e4f87f9f25e9ecfd9ccf4c990d68", "/romer/m1/central-a1", "FF-M1-CENTRAL-A1-FCSTD-001", "T1-M1", "COM-0368"),
        ("SEQLD Pilot Build.FCStd", "b9fcb7093793c50ab4d97d2d95ce66bb18a23f6475fc16eb02e0a123e957e2ae", "/romer/m1/pilot-build", "FF-M1-PILOT-BUILD-FCSTD-001", "T1-M1", "COM-0368"),
        ("MarkV.FCStd", "40bd51c0ce6fcad2f5a32894b15005d4383c73a378b9328185557549674346c5", "/romer/mark-v", "FF-MARKV-FCSTD-001", "SPACE-02", "COM-0445"),
        ("Luke IV.FCStd", "88ca5a84fb65d29ecaf4ccd8ec975a6ccad8bb426a078851109b2e16db5af1d6", "/romer/luke-iv", "FF-LUKE4-FCSTD-001", "SPACE-03", "COM-0446"),
        ("Luke IV Single Node.FCStd", "ae8f6a022bdbd436fd24ae05ee7f6c6f70496515f2ee81e4ec0dd1cb5b0c3f40", "/romer/luke-iv/single-node", "FF-LUKE4-SINGLE-NODE-FCSTD-001", "SPACE-03", "COM-0446"),
        ("Free Flow Battery.FCStd", "8f2cda7ea111d8706e2bb0e0726c3cc0c0b7e7114a7e56875af5e3877c7df64c", "/romer/free-flow/battery", "FF-FREEFLOW-BATTERY-FCSTD-001", "SF-01", "COM-1666"),
        ("Free Flow Capacitors.FCStd", "61dbb8fd31306920befd57ee5fd40de33588aad40f5d8cfb337cce829a93147f", "/romer/free-flow/capacitors", "FF-FREEFLOW-CAPACITORS-FCSTD-001", "SF-01", "COM-1666"),
        ("Free Flow Solenoid.FCStd", "6ef10e499d36e2eb48aa45b824401459851b4a870b0b1b75b94f4c5bba111afb", "/romer/free-flow/solenoid", "FF-FREEFLOW-SOLENOID-FCSTD-001", "SF-01", "COM-1666"),
    ]
    for name, sha, target, mapping_id, object_id, operations_id in cases:
        plan = _plan(name, sha, target)
        mapping = plan["registered_mapping"]
        assert plan["semantic_state"] == "mapping_ready"
        assert mapping["mapping_id"] == mapping_id
        assert mapping["semantic_object_id"] == object_id
        assert mapping["operations_record_id"] == operations_id
        assert plan["authority_transfer"] is False


def test_remaining_dbr_summary_distinguishes_hash_drift_from_structural_change():
    assert REMAINING_DBR["M1_CENTRAL_A1"]["old"]["object_count"] == 884
    assert REMAINING_DBR["M1_CENTRAL_A1"]["new"]["object_count"] == 884
    assert REMAINING_DBR["M1_CENTRAL_A1"]["normalized_change_count"] == 0

    assert REMAINING_DBR["M1_PILOT_BUILD"]["old"]["object_count"] == 870
    assert REMAINING_DBR["M1_PILOT_BUILD"]["new"]["object_count"] == 1185
    assert len(REMAINING_DBR["M1_PILOT_BUILD"]["added_objects"]) == 315
    assert REMAINING_DBR["M1_PILOT_BUILD"]["removed_objects"] == []
    assert REMAINING_DBR["M1_PILOT_BUILD"]["normalized_change_count"] == 38

    assert REMAINING_DBR["MARK_V"]["old"]["object_count"] == 62
    assert REMAINING_DBR["MARK_V"]["new"]["object_count"] == 62
    assert REMAINING_DBR["MARK_V"]["normalized_change_count"] == 0

    assert REMAINING_DBR["LUKE_IV"]["old"]["object_count"] == 0
    assert REMAINING_DBR["LUKE_IV"]["new"]["object_count"] == 46
    assert len(REMAINING_DBR["LUKE_IV"]["added_objects"]) == 46

    assert REMAINING_DBR["FREE_FLOW_BATTERY"]["normalized_change_count"] == 0
    assert REMAINING_DBR["FREE_FLOW_CAPACITORS"]["old"]["object_count"] == 68
    assert REMAINING_DBR["FREE_FLOW_CAPACITORS"]["new"]["object_count"] == 75
    assert len(REMAINING_DBR["FREE_FLOW_CAPACITORS"]["added_objects"]) == 17
    assert len(REMAINING_DBR["FREE_FLOW_CAPACITORS"]["removed_objects"]) == 10
    assert REMAINING_DBR["FREE_FLOW_SOLENOID"]["old"]["object_count"] == 24
    assert REMAINING_DBR["FREE_FLOW_SOLENOID"]["new"]["object_count"] == 30
    assert len(REMAINING_DBR["FREE_FLOW_SOLENOID"]["added_objects"]) == 14
    assert len(REMAINING_DBR["FREE_FLOW_SOLENOID"]["removed_objects"]) == 8


def test_priority_binding_receipt_preserves_nonclaim_boundary():
    by_id = {row["semantic_object_id"]: row for row in PRIORITY_BINDINGS["bindings"]}
    assert by_id["T1-M1"]["operations_record_id"] == "COM-0368"
    assert by_id["SPACE-02"]["operations_record_id"] == "COM-0445"
    assert by_id["SPACE-03"]["operations_record_id"] == "COM-0446"
    assert by_id["SF-01"]["operations_record_id"] == "COM-1666"
    assert PRIORITY_BINDINGS["physical_authority"] is False
    assert PRIORITY_BINDINGS["manufacturing_authority"] is False
    assert PRIORITY_BINDINGS["public_release_authorized"] is False


def test_m1_and_free_flow_lineage_are_source_bound_without_overwriting_other_authority():
    records = {record["twin_id"]: record for record in LINEAGE["records"]}
    m1 = records["m1_elevated_bypass"]
    assert len(m1["native_source_bindings"]) == 3
    assert m1["source_binding_state"] == "CURRENT_NATIVE_CONFIGURATION_SET_BOUND / PRECEDENCE_RESOLVED_BY_SCOPE"

    expected = {
        "free_flow_batteries": "FF-FREEFLOW-BATTERY-FCSTD-001",
        "free_flow_capacitors": "FF-FREEFLOW-CAPACITORS-FCSTD-001",
        "free_flow_solenoid_stack": "FF-FREEFLOW-SOLENOID-FCSTD-001",
    }
    for twin_id, mapping_id in expected.items():
        record = records[twin_id]
        assert record["mapping_id"] == mapping_id
        assert record["source_binding_state"] == "R2_NATIVE_GEOMETRY_SOURCE_BOUND / MEASURED_PERFORMANCE_HELD"


def test_m1_configuration_precedence_is_scope_resolved_without_global_master():
    assert M1_PRECEDENCE["status"] == "EXECUTED / PRECEDENCE_RESOLVED_BY_SCOPE / NO_SINGLE_GLOBAL_MASTER"
    assert M1_PRECEDENCE["semantic_object_id"] == "T1-M1"
    assert M1_PRECEDENCE["operations_record_id"] == "COM-0368"

    proof = M1_PRECEDENCE["pairwise_proof"]
    assert proof["base_vs_central"]["base_subset_central"] is True
    assert proof["base_vs_central"]["intersection"] == 870
    assert proof["base_vs_central"]["central_only"] == 14
    assert proof["base_vs_pilot"]["base_subset_pilot"] is True
    assert proof["base_vs_pilot"]["intersection"] == 870
    assert proof["base_vs_pilot"]["pilot_only"] == 315
    assert proof["central_vs_pilot"]["intersection"] == 879
    assert proof["central_vs_pilot"]["neither_subset"] is True

    resolution = M1_PRECEDENCE["resolution"]
    assert resolution["common_geometry_authority"] == "FF-M1-BASEKM-FCSTD-001"
    assert resolution["broad_pilot_scope"] == "FF-M1-PILOT-BUILD-FCSTD-001"
    assert resolution["central_column_specialization_scope"] == "FF-M1-CENTRAL-A1-FCSTD-001"
    assert resolution["global_master_selected"] is False
    assert M1_PRECEDENCE["physical_authority"] is False
    assert M1_PRECEDENCE["manufacturing_authority"] is False
    assert M1_PRECEDENCE["public_release_authorized"] is False


def test_m1_registry_and_lineage_encode_scoped_precedence():
    mappings = {row["mapping_id"]: row for row in FIRST_FILES["mappings"]}
    base = mappings["FF-M1-BASEKM-FCSTD-001"]
    central = mappings["FF-M1-CENTRAL-A1-FCSTD-001"]
    pilot = mappings["FF-M1-PILOT-BUILD-FCSTD-001"]
    assert base["configuration_scope"] == "COMMON_BASELINE"
    assert base["configuration_precedence"]["global_master"] is False
    assert central["configuration_scope"] == "SPECIALIZED_CENTRAL_COLUMN_BRANCH"
    assert central["configuration_precedence"]["common_baseline_mapping_id"] == "FF-M1-BASEKM-FCSTD-001"
    assert pilot["configuration_scope"] == "BROAD_EXPANDED_PILOT_CONFIGURATION"
    assert pilot["configuration_precedence"]["common_baseline_mapping_id"] == "FF-M1-BASEKM-FCSTD-001"

    records = {record["twin_id"]: record for record in LINEAGE["records"]}
    m1 = records["m1_elevated_bypass"]
    assert m1["source_binding_state"] == "CURRENT_NATIVE_CONFIGURATION_SET_BOUND / PRECEDENCE_RESOLVED_BY_SCOPE"
    assert m1["configuration_precedence"]["status"] == "RESOLVED_BY_SCOPE / NO_SINGLE_GLOBAL_MASTER"
    assert m1["configuration_precedence"]["common_baseline"]["object_count"] == 870
    assert m1["configuration_precedence"]["broad_expansion"]["added_over_baseline"] == 315
    assert m1["configuration_precedence"]["specialized_branch"]["added_over_baseline"] == 14

    by_id = {row["semantic_object_id"]: row for row in PRIORITY_BINDINGS["bindings"]}
    assert by_id["T1-M1"]["state"] == "THREE_CURRENT_CONFIGURATION_SOURCES_BOUND / PRECEDENCE_RESOLVED_BY_SCOPE"


def test_luke4_configuration_relation_is_resolved_as_sibling_sources():
    assert LUKE4_RELATION["status"] == "EXECUTED / SIBLING_CONFIGURATIONS_WITH_SHARED_CORE / PERFORMANCE_HELD"
    assert LUKE4_RELATION["semantic_object_id"] == "SPACE-03"
    proof = LUKE4_RELATION["pairwise_proof"]
    assert proof["intersection"] == 28
    assert proof["full_only"] == 18
    assert proof["single_only"] == 3
    assert proof["same_label_common"] == 26
    assert proof["single_subset_full"] is False
    assert proof["full_subset_single"] is False
    assert proof["single_unique_objects"] == ["Pad006", "Pocket", "Pocket001"]
    assert LUKE4_RELATION["resolution"]["relation_type"] == "SIBLING_CONFIGURATIONS_WITH_SHARED_CORE"
    assert LUKE4_RELATION["physical_authority"] is False
    assert LUKE4_RELATION["manufacturing_authority"] is False
    assert LUKE4_RELATION["public_release_authorized"] is False


def test_luke4_registry_lineage_and_priority_receipt_are_aligned():
    mappings = {row["mapping_id"]: row for row in FIRST_FILES["mappings"]}
    full = mappings["FF-LUKE4-FCSTD-001"]
    single = mappings["FF-LUKE4-SINGLE-NODE-FCSTD-001"]
    assert full["configuration_scope"] == "FULL_LUKE_IV_CONFIGURATION"
    assert single["configuration_scope"] == "SPECIALIZED_SINGLE_NODE_CONFIGURATION"
    assert full["configuration_relation"]["relation_type"] == "SIBLING_CONFIGURATIONS_WITH_SHARED_CORE"
    assert single["configuration_relation"]["strict_subset_relation"] is False

    records = {record["twin_id"]: record for record in LINEAGE["records"]}
    luke = records["luke_family"]
    assert luke["semantic_object_id"] == "SPACE-03"
    assert luke["parent_object_id"] == "T1-SPACE"
    assert luke["geometry_authority"] == "LUKE4_NATIVE_CONFIGURATION_SET"
    assert len(luke["native_source_bindings"]) == 2
    assert luke["source_binding_state"] == "R2_NATIVE_CONFIGURATION_SET_BOUND / SIBLING_RELATION_RESOLVED / PERFORMANCE_HELD"
    assert luke["configuration_relation"]["proof"]["intersection"] == 28

    by_id = {row["semantic_object_id"]: row for row in PRIORITY_BINDINGS["bindings"]}
    assert by_id["SPACE-03"]["state"] == "FULL_AND_SINGLE_NODE_SOURCES_BOUND / SIBLING_CONFIGURATION_RELATION_RESOLVED"
