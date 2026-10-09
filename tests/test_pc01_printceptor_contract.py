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
DIRECTIONAL = load("universal_type1_directional_resolver_v0_1.json")
ROUTES = load("pc01_family_route_compiler_v0_1.json")
FIRST_ARTICLE = load("pc01_first_article_review_v0_1.json")
HOST = load("pc01_secure_host_profile_v0_1.json")

def test_pc01_owner_and_physical_state_are_bounded() -> None:
    assert PC01["authority"]["queue_id"] == "BUILD-066"
    assert PC01["authority"]["operational_matrix_range"].endswith("A1:AD52")
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

def test_directional_type1_resolver_is_411_row_factorized_and_directional() -> None:
    assert DIRECTIONAL["authority"]["archetype_rows"] == 411
    assert DIRECTIONAL["authority"]["total_fields"] == 60
    assert len(DIRECTIONAL["directional_fields"]) == 16
    assert len(DIRECTIONAL["compiler_fields"]) == 8
    assert DIRECTIONAL["authority"]["compiler_range"] == "BA:BH"
    assert PC01["directional_resolver"]["compiler_field_count"] == 8
    assert PC01["directional_resolver"]["total_fields"] == 60
    assert any("X→Y compatibility never implies Y→X" in x for x in DIRECTIONAL["invariants"])
    assert "168k" in DIRECTIONAL["dense_pair_policy"]

def test_pc01_route_compiler_covers_operational_examples_without_uplift() -> None:
    ids = [r["id"] for r in ROUTES["routes"]]
    assert ids == [f"PC01-MX-{i:03d}" for i in range(36, 52)]
    robotic = next(r for r in ROUTES["routes"] if r["id"] == "PC01-MX-038")
    assert robotic["families"] == ["STRUCT", "FUNC", "FIBER", "HYBRID", "METRO"]
    daily = next(r for r in ROUTES["routes"] if r["id"] == "PC01-MX-039")
    assert daily["families"] == []
    assert "never changes UNBOUND/NOT_RUN states" in ROUTES["evidence_rule"]

def test_first_article_is_held_until_source_rights_machine_and_safety_close() -> None:
    assert FIRST_ARTICLE["candidate"]["physical_build"] is False
    assert FIRST_ARTICLE["candidate"]["exact_cad_readback"] is False
    assert FIRST_ARTICLE["candidate"]["redistribution_or_commercial_license"] == "UNVERIFIED"
    assert "Benign P0/P1/P2" in FIRST_ARTICLE["first_physical_preference"]

def test_secure_host_profile_is_measured_but_does_not_force_upgrade() -> None:
    snap = HOST["measured_snapshot"]
    assert snap["cpu"] == "AMD Ryzen 7 2700X Eight-Core Processor"
    assert snap["cpu_cores"] == 8
    assert snap["cpu_logical_processors"] == 16
    assert snap["physical_memory_bytes"] > 32_000_000_000
    assert snap["gpu"] == "NVIDIA GeForce GTX 1660"
    assert HOST["security_state"]["tpm"] == "UNVERIFIED"
    assert HOST["security_state"]["secure_boot"] == "UNVERIFIED"
    assert HOST["security_state"]["bitlocker_or_equivalent_disk_encryption"] == "UNVERIFIED"
    assert "Do not replace hardware" in HOST["suitability"]["upgrade_rule"]

def test_operational_contract_links_new_owner_records() -> None:
    assert PC01["authority"]["portfolio_range"].endswith("A61:P74")
    assert PC01["authority"]["parent_queue_id"] == "BUILD-065"
    assert PC01["directional_resolver"]["portfolio_id"] == "UTP-117"
    assert PC01["route_compiler"]["portfolio_ids"] == ["UTP-120", "UTP-121"]
    assert PC01["first_article"]["portfolio_id"] == "UTP-122"
    assert PC01["secure_host"]["portfolio_id"] == "UTP-123"