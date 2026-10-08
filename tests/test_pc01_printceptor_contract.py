from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "cgx" / "component_atlas"

def load(name: str) -> dict:
    return json.loads((BASE / name).read_text(encoding="utf-8"))

PC01 = load("pc01_printceptor_operational_contract_v0_1.json")
EVENTS = load("pc01_production_event_schema_v0_1.json")
REVIEW = load("pc01_digital_review_sequence_v0_1.json")
READY = load("pc01_build_readiness_vector_v0_1.json")

def test_pc01_owner_and_physical_state_are_bounded() -> None:
    assert PC01["authority"]["queue_id"] == "BUILD-065"
    assert PC01["authority"]["operational_matrix_range"].endswith("A1:AD36")
    assert PC01["physical_state"] == "NOT_BUILT"
    assert "BUILD_READY is not BUILT" in PC01["evidence_boundaries"][0]

def test_compute_delegation_preserves_local_safety_and_no_authority_transfer() -> None:
    assert PC01["compute_profiles"]["C0"]["network_required"] is False
    assert "authority" in PC01["compute_profiles"]["C2"]
    assert "none transferred" in PC01["compute_profiles"]["C2"]["authority"]
    assert "unrestricted agent/LLM runtime" in PC01["device_suitability"]["child_toy"]["forbidden"]
    assert "unqualified retrofit actuation" in PC01["device_suitability"]["consumer_appliance"]["forbidden"]
    assert PC01["learning_policy"]["sentience_claim"] is False

def test_production_event_schema_supports_low_friction_daily_count_without_uplift() -> None:
    diode = next(x for x in EVENTS["examples"] if x["event_id"] == "EXAMPLE-PC01-DIODE-001")
    assert diode["quantity"] == 1
    assert diode["unit"] == "each"
    assert diode["evidence_state"] == "PRODUCTION_COUNT_ONLY"
    assert any("never proves" in rule for rule in EVENTS["rules"])

def test_family_and_interaction_intents_are_explicit() -> None:
    assert set(PC01["intent_classes"]) == {"LOG","BUILD","ENROL","REPAIR","REVIEW","MAINTAIN","QUERY"}
    assert PC01["identity"]["family_contract"] == "CGX-FAMILY-LINEAGE-001"
    assert "authority" in " ".join(PC01["evidence_boundaries"]).lower()

def test_digital_review_is_source_bound_and_non_physical() -> None:
    assert REVIEW["physical_execution"] is False
    assert REVIEW["status"].endswith("PC01_GEOMETRY_NOT_YET_BOUND")
    assert [x["id"] for x in REVIEW["phases"]] == [f"DR-0{i}" for i in range(9)]
    assert any("Do not invent missing dimensions" in x["hard_gate"] for x in REVIEW["phases"])

def test_build_ready_requires_all_hard_dimensions() -> None:
    assert READY["current_pc01"]["state"] == "PLANNED"
    assert READY["current_pc01"]["physical_state"] == "NOT_BUILT"
    assert READY["current_pc01"]["geometry_closure"] == "UNRESOLVED"
    assert "every applicable hard dimension PASS" in READY["promotion_rule"]
