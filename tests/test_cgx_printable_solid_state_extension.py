from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "cgx" / "domain_templates"

EXTENSION = json.loads(
    (TEMPLATES / "cgx_printable_solid_state_extension_2026-10-07.json").read_text(
        encoding="utf-8"
    )
)
DELTA = json.loads(
    (TEMPLATES / "founder_semantic_delta_2026-10-07_printable_solid_state.json").read_text(
        encoding="utf-8"
    )
)
NODE_EXCHANGE = json.loads(
    (TEMPLATES / "node_exchange_contract.json").read_text(encoding="utf-8")
)


def _ids(section: str) -> list[str]:
    return [row["id"] for row in EXTENSION["drive_rows"][section]]


def test_extension_ids_are_unique_and_scoped() -> None:
    all_ids = _ids("solid_state") + _ids("postmix") + _ids("raphael_printer")
    assert len(all_ids) == len(set(all_ids))
    assert all(v.startswith("PT-") for v in _ids("solid_state"))
    assert all(v.startswith("PMX-") for v in _ids("postmix"))
    assert all(v.startswith("RIP-") for v in _ids("raphael_printer"))


def test_thin_endpoint_reuses_existing_node_exchange_authority_boundary() -> None:
    assert "existing CGX identity" in NODE_EXCHANGE["purpose"]
    assert "without creating a second runtime" in NODE_EXCHANGE["purpose"]
    assert "node identity is distinct from agent identity and semantic authority" in NODE_EXCHANGE["identity_rules"]
    assert "delegated compute does not require smartphone-class onboard compute" in EXTENSION["identity_contract"]["invariants"]
    assert "runtime receipt alone cannot promote canonical or physical claims" in EXTENSION["identity_contract"]["invariants"]


def test_energy_and_material_claim_guardrails_are_explicit() -> None:
    guards = EXTENSION["scientific_guardrails"]
    assert "not an energy source" in guards["energy"]
    assert "not by default" in guards["graphene"]
    assert "contamination" in guards["recovered_materials"]
    assert "not presumed" in guards["coatings"]


def test_bootstrap_scenario_is_not_promoted_to_mission_fact() -> None:
    scenario = EXTENSION["bootstrap_scenario"]
    assert scenario["state"] == "FOUNDER_SCENARIO_PENDING_OWNING_CANON_RECONCILIATION"
    assert any("Mark V" in item and "unresolved" in item for item in scenario["proposed_seed"])
    assert "not a flight manifest" in scenario["non_claims"]
    assert "no-mark-v-tagging-role-promotion-before-owning-canon-reconciliation" in DELTA["hard_guardrails"]


def test_triplet_preserves_authority_separation() -> None:
    triplet = EXTENSION["triplet"]
    assert "identity, semantics, provenance" in triplet["filespace"]
    assert "telemetry" in triplet["dataspace"]
    assert "material layers" in triplet["solid_state"]
    assert "DBR" in triplet["binding"]


def test_recursive_manufacturing_is_bounded() -> None:
    assert "not autonomous unlimited self-replication" in EXTENSION["scientific_guardrails"]["recursion"]
    solid = {row["id"]: row["name"] for row in EXTENSION["drive_rows"]["solid_state"]}
    assert solid["PT-081"] == "Recursive modular printer/tooling expansion"
