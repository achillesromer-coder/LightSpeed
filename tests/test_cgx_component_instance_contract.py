from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "cgx" / "component_atlas"

def load(name: str) -> dict:
    return json.loads((BASE / name).read_text(encoding="utf-8"))

INSTANCE = load("component_instance_build_packet_contract_v0_1.json")
LADDER = load("component_physical_proof_ladder_v0_1.json")
ATLAS = load("component_geometry_atlas_v0_1.json")

def test_instance_contract_binds_current_atlas_without_uplift() -> None:
    assert INSTANCE["parents"]["atlas_archetype_count"] == 407
    assert INSTANCE["parents"]["atlas_drive_range"].endswith("A1:V408")
    assert INSTANCE["authority"]["portfolio_id"] == "UTP-106"
    assert INSTANCE["authority"]["queue_id"] == "BUILD-064"
    assert "exact_source_authority" in INSTANCE["required_instance_fields"]
    assert "dimensions_and_tolerances" in INSTANCE["required_instance_fields"]
    assert "material_stack_and_lots" in INSTANCE["required_instance_fields"]
    assert "acceptance_tests" in INSTANCE["required_instance_fields"]
    assert "falsifiers" in INSTANCE["required_instance_fields"]
    assert "REVIEWED_PROMOTION" == INSTANCE["binding_states"][-1]
    assert any("cannot inherit the rating" in x for x in INSTANCE["hard_boundaries"])

def test_raphael_contract_keeps_standard_physics_and_empirical_test() -> None:
    r = INSTANCE["raphael_comparison_contract"]
    assert "not a substitute" in r["rule"]
    assert "Conventional physics solver first" in r["solver_order"]
    assert "empirical" in r["promotion"]
    assert "hard safety" in r["reporting"]

def test_proof_ladder_is_complete_and_all_physical_states_are_not_run() -> None:
    ids = [x["id"] for x in LADDER["stages"]]
    assert ids == [f"P{i}" for i in range(11)]
    assert all(x["physical_state"] == "NOT_RUN" for x in LADDER["stages"])
    assert LADDER["authority"]["portfolio_id"] == "UTP-107"
    assert LADDER["authority"]["queue_id"] == "BUILD-064"

def test_proof_ladder_uses_existing_component_archetypes() -> None:
    atlas_ids = {x["ID"] for x in ATLAS["records"]}
    required = {
        "CGA-I-002", "CGA-I-004", "CGA-I-005",
        "CGA-R-001", "CGA-C-001", "CGA-L-001", "CGA-L-004",
        "CGA-RF-001", "CGA-RF-012", "CGA-RF-020",
        "CGA-S-001", "CGA-S-023", "CGA-L-015",
        "CGA-D-009", "CGA-PWR-014", "CGA-E-016", "CGA-E-018",
    }
    assert required <= atlas_ids

def test_energy_and_frequency_claim_boundaries_are_explicit() -> None:
    by_id = {x["id"]: x for x in LADDER["stages"]}
    assert "Energy conservation" in by_id["P7"]["hard_gate"]
    assert "no free-energy" in by_id["P7"]["hard_gate"]
    assert "No biological" in by_id["P3"]["hard_gate"]
    assert "unmeasured biofeedback" in by_id["P9"]["hard_gate"]

def test_dense_integration_cannot_promote_child_evidence() -> None:
    by_id = {x["id"]: x for x in LADDER["stages"]}
    assert "cannot raise the evidence ceiling" in by_id["P10"]["hard_gate"]
    assert "pairwise interactions" in by_id["P10"]["hard_gate"]
