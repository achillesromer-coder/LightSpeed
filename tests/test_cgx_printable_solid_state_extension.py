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
    assert scenario["state"] == "FOUNDER_SCENARIO_MARK_V_ROLE_CORROBORATED_PENDING_MISSION_ENGINEERING"
    assert any("Mark V" in item and "UC-005" in item and "no ownership/yield claim" in item for item in scenario["proposed_seed"])
    assert "not a flight manifest" in scenario["non_claims"]
    assert "no-mark-v-ownership-yield-or-mission-readiness-promotion-from-design-stage-uc-005" in DELTA["hard_guardrails"]


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


def test_frontier_projections_are_present_but_not_capability_uplift() -> None:
    projections = {row["id"]: row for row in EXTENSION["frontier_projections"]}
    assert projections["PUBLIC_BENEFIT_NETWORK"]["state"] == "DEPLOYMENT_MODEL"
    assert projections["PLANETARY_RESTORATION_TERRAFORMING_RESEARCH"]["state"] == "LONG_HORIZON_RESEARCH"
    assert "No planetary-scale intervention" in projections["PLANETARY_RESTORATION_TERRAFORMING_RESEARCH"]["boundary"]
    assert projections["TYPE_I_TO_II_SCENARIO"]["boundary"] == "Planning horizon only; no readiness uplift."
    assert "does not solve propulsion" in projections["INTERSTELLAR_LOCAL_HORIZON"]["boundary"]
    assert "never grants specialist authority" in EXTENSION["deployment_actor_model"]["rule"]


def test_node_horizon_operational_registry_is_mirrored_without_pt_renumbering() -> None:
    rows = EXTENSION["drive_rows"]["node_horizon"]
    ids = [row["id"] for row in rows]
    assert len(ids) == 16
    assert len(ids) == len(set(ids))
    assert "CGX-PHYSOBJ-001" in ids
    assert "CGX-COMPILER-001" in ids
    assert "METRIC-CGX-CLOSURE-001" in ids
    assert len(EXTENSION["drive_rows"]["solid_state"]) == 11


def test_physical_object_identity_uses_c0_c1_c2_without_authority_uplift() -> None:
    ident = EXTENSION["physical_object_identity"]
    assert "smartphone-class compute stack" in ident["principle"]
    assert set(ident["compute_split"]) == {"C0", "C1", "C2"}
    assert "never upgrades semantic" in ident["authority_boundary"]
    assert "geometry_hash" in ident["required_fields"]
    assert "material_passport_refs" in ident["required_fields"]


def test_operational_printer_family_taxonomy_is_complete() -> None:
    families = {row["id"]: row for row in EXTENSION["printer_families"]}
    expected = {
        "UTP-PF-STRUCT-001", "UTP-PF-FUNC-001", "UTP-PF-FIBER-001",
        "UTP-PF-HYBRID-001", "UTP-PF-FEED-001", "UTP-PF-METRO-001",
        "UTP-PF-MOBILE-001",
    }
    assert set(families) == expected
    assert "chips" in families["UTP-PF-HYBRID-001"]["core"]
    assert "material passport" in families["UTP-PF-FEED-001"]["core"]


def test_function_stack_and_structural_energy_boundaries_are_explicit() -> None:
    compiler = EXTENSION["function_to_stack_compiler"]
    assert "never automatic build approval" in compiler["rule"]
    energy = EXTENSION["structural_energy_region"]
    assert "never an energy source" in energy["energy_boundary"]
    assert "not a universal default" in energy["rule"]


def test_closure_vector_keeps_hard_gates_and_ruvr_alias_unresolved() -> None:
    metric = EXTENSION["closure_metrics"]
    assert set(metric["dimensions"]) == {"F_local","M_local","I_crit","R_local","V","S","E","A","U"}
    assert "never allow a composite score" in metric["rule"]
    assert "No exact canonical RUVR definition" in metric["ruvr_alias_hold"]
    assert "must not be relabelled RUVR" in metric["ruvr_alias_hold"]


def test_bootstrap_safeguard_and_role_models_remain_bounded() -> None:
    bootstrap = EXTENSION["bootstrap_closure"]
    assert "no autonomous unlimited replication" in bootstrap["non_claims"]
    assert "resource return is downstream optionality" in bootstrap["founder_case"]
    safeguard = EXTENSION["local_safeguard_layer"]
    assert "never itself authorises deorbit" in safeguard["boundary"]
    public = EXTENSION["public_benefit_operating_model"]
    assert "never inherits specialist" in public["rule"]
    federation = EXTENSION["federation_model"]
    assert "never creates supra-national ownership" in federation["rule"]
