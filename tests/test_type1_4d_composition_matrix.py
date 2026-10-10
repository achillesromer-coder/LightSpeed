import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "cgx" / "component_atlas" / "type1_4d_composition_matrix_v0_1.json"
SCRIPT = ROOT / "scripts" / "project_type1_4d_composition.py"


def load_script():
    spec = importlib.util.spec_from_file_location("type1_4d_projection", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_matrix():
    return json.loads(MATRIX.read_text(encoding="utf-8-sig"))


def test_matrix_has_complete_20_primitive_basis():
    data = load_matrix()
    records = data["records"]
    names = [record["primitive_basis_class"] for record in records]
    assert len(records) == 20
    assert len(set(names)) == 20
    assert set(data["seed_graphs"]) == {"SG-0", "SG-1", "SG-N"}


def test_each_primitive_has_2d_3d_4d_and_all_seed_routes():
    data = load_matrix()
    for record in data["records"]:
        assert record["schematic_2d_intent"]
        assert record["geometry_3d"]
        assert record["state_history_4d"]
        assert set(record["seed_routes"]) == {"SG_0", "SG_1", "SG_N"}
        assert record["engineering_model_route"]
        assert record["verification"]
        assert record["fail_closed"]


def test_capacitance_ladder_escalates_to_general_3d_field_matrix():
    data = load_matrix()
    ladder = {row["id"]: row for row in data["capacitance_inference_ladder"]}
    assert set(ladder) == {f"CAP-{i}" for i in range(1, 8)}
    assert "parallel plate" in ladder["CAP-1"]["topology"]
    assert "Maxwell capacitance matrix" in ladder["CAP-5"]["gate"]
    assert "R'L'G'C'" in ladder["CAP-6"]["equation"]
    assert "C=C(x,state,t)" in ladder["CAP-7"]["equation"]


def test_projection_is_bounded_and_seed_specific():
    module = load_script()
    projection = module.project("CAPACITIVE_ELECTROSTATIC", "SG-N", MATRIX)
    assert projection["primitive_basis_class"] == "CAPACITIVE_ELECTROSTATIC"
    assert projection["seed_graph"] == "SG-N"
    assert "multi-electrode" in projection["seed_route"]
    assert projection["evidence_ceiling"] == "DIGITAL_COMPOSITION_ONLY / PHYSICAL_NOT_RUN"
    assert "APPLY_UTP148_MATURITY_INVALIDATION" in projection["next_pipeline"]


def test_unknown_primitive_fails_closed():
    module = load_script()
    with pytest.raises(ValueError, match="Unknown primitive basis class"):
        module.project("NOT_A_PRIMITIVE", "SG-0", MATRIX)


def test_unknown_seed_graph_fails_closed():
    module = load_script()
    with pytest.raises(ValueError, match="Unknown seed graph"):
        module.project("STRUCTURE_DATUM", "SG-X", MATRIX)


def test_matrix_preserves_authority_and_energy_boundaries():
    data = load_matrix()
    invariants = " ".join(data["global_invariants"])
    assert "not an energy source" in invariants
    assert "never transfers" in invariants or "never transfer" in invariants
    assert data["proof_binding"]["no_promotion"] == "Digital composition cannot advance physical evidence beyond BUILD_READY."
