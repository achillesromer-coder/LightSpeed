import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "cgx" / "component_atlas"


def load(name):
    return json.loads((ATLAS / name).read_text(encoding="utf-8-sig"))


def test_maturity_graph_reuses_existing_binding_state_machine():
    maturity = load("type1_maturity_graph_v0_1.json")
    instance = load("component_instance_build_packet_contract_v0_1.json")

    mapped = [item["binding_state"] for item in maturity["maturity_states"]]
    assert mapped == instance["binding_states"]
    assert [item["level"] for item in maturity["maturity_states"]] == [
        f"M{i}" for i in range(10)
    ]


def test_maturity_graph_is_vector_not_readiness_percentage():
    maturity = load("type1_maturity_graph_v0_1.json")
    axes = {item["axis"] for item in maturity["maturity_vector_axes"]}

    assert len(axes) == 10
    assert {
        "source_authority",
        "geometry",
        "material",
        "process",
        "test_metrology",
        "physical_evidence",
        "integration_coupling",
        "authority_release",
    }.issubset(axes)
    assert "Do not average" in maturity["projection_policy"]["no_single_score"]
    assert "cannot advance physical_evidence beyond M6" in maturity["projection_policy"]["digital_physical"]


def test_maturity_graph_binds_current_411_archetype_and_proof_ladder():
    maturity = load("type1_maturity_graph_v0_1.json")
    atlas = load("component_geometry_atlas_v0_1.json")
    proof = load("component_physical_proof_ladder_v0_1.json")

    assert atlas["record_count"] == 411
    assert len(atlas["records"]) == 411
    assert maturity["proof_ladder_binding"]["stages"] == [
        item["id"] for item in proof["stages"]
    ]
    assert proof["status"].endswith("PHYSICAL_EXECUTION_NOT_RUN")


def test_seed_graphs_cover_zero_one_many_without_authority_uplift():
    maturity = load("type1_maturity_graph_v0_1.json")
    seeds = {item["id"]: item for item in maturity["seed_graphs"]}

    assert set(seeds) == {"SG-0", "SG-1", "SG-N"}
    assert "cannot be used to infer capability" in seeds["SG-0"]["maturity_rule"]
    assert "separately" in seeds["SG-1"]["maturity_rule"]
    assert "weakest required node/edge" in seeds["SG-N"]["maturity_rule"]


def test_ingest_pipeline_invalidation_precedes_recompile_and_promotion():
    maturity = load("type1_maturity_graph_v0_1.json")
    pipe = maturity["ingest_pipeline"]

    assert pipe.index("INVALIDATE_STALE_DERIVED_RESULTS") < pipe.index(
        "RECOMPILE_DIRECTIONAL_STACK_AND_4D_MODEL"
    )
    assert pipe.index("RECOMPILE_DIRECTIONAL_STACK_AND_4D_MODEL") < pipe.index(
        "UPDATE_MATURITY_VECTOR_ONLY_FOR_PROVEN_AXES"
    )
    assert pipe[-1] == "REVIEW_OR_HOLD"


def test_mutation_rules_cover_consequential_source_geometry_material_process_and_calibration_changes():
    maturity = load("type1_maturity_graph_v0_1.json")
    triggers = {rule["trigger"] for rule in maturity["evidence_mutation_rules"]}

    assert {
        "source_revision_or_hash_changed",
        "geometry_revision_changed",
        "material_lot_or_passport_changed",
        "process_recipe_tool_or_environment_changed",
        "instrument_calibration_expired_or_changed",
        "seed_part_or_firmware_revision_changed",
        "environment_or_horizon_changed",
        "contradictory_new_evidence",
    }.issubset(triggers)


def test_4d_and_radiative_policy_fail_closed():
    maturity = load("type1_maturity_graph_v0_1.json")
    f4d = maturity["functional_voxel_4d"]
    field = maturity["radiative_and_field_policy"]

    assert "unsupported coupling terms remain HOLD" in f4d["sparse_coupling"]
    assert "Maxwell capacitance matrix" in field["capacitance_rule"]
    assert "does not create an absent source" in field["energy_rule"]
    assert "no unmeasured ambient-energy claim" in field["radiation_rule"]


def test_hard_boundaries_keep_physical_and_authority_separate():
    maturity = load("type1_maturity_graph_v0_1.json")
    hard = " ".join(maturity["hard_boundaries"]).lower()

    assert "no physical execution" in hard
    assert "no carrier/root promotion" in hard
    assert "no public/certification/legal/financial/high-consequence authority" in hard
    assert "unknowns remain explicit" in hard
