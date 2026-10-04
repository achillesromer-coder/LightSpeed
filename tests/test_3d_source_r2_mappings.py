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
