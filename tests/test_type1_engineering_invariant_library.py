import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "cgx" / "component_atlas" / "type1_engineering_invariant_library_v0_1.json"


def load():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_invariant_library_is_one_evidence_bounded_extension():
    d = load()
    assert d["schema"] == "CGX-TYPE1-ENGINEERING-INVARIANT-LIBRARY/0.1"
    assert d["artifact_id"] == "UTP-139"
    assert d["policy"]["physical_execution"] is False
    assert d["policy"]["no_rating_uplift"] is True
    assert len(d["invariants"]) >= 12


def test_capacitance_fixtures_preserve_25_and_50_um_as_distinct_states():
    d = load()
    fixtures = {x["id"]: x for x in d["source_bound_fixtures"]}
    c25 = fixtures["FIX-KAPTON-HN-25"]["derived"]["ideal_capacitance_density_pF_mm2"]
    c50 = fixtures["FIX-KAPTON-HN-50"]["derived"]["ideal_capacitance_density_pF_mm2"]
    assert abs(c25 - 1.2041695425408) < 1e-12
    assert abs(c50 - 0.6020847712704) < 1e-12
    assert abs(c25 / c50 - 2.0) < 1e-12
    assert "NOT_MEASURED" in fixtures["FIX-KAPTON-HN-25"]["evidence"]


def test_sheet_resistance_and_motor_fixtures_are_derived_not_qualified():
    d = load()
    fixtures = {x["id"]: x for x in d["source_bound_fixtures"]}
    assert fixtures["FIX-ECI1010-10SQ"]["derived"]["ideal_path_resistance_ohm"] == 0.07
    assert fixtures["FIX-ECI7004LR-1K"]["derived"]["required_square_range"] == [0.2, 20.0]
    motor = fixtures["FIX-PKP243D08B2"]["derived"]
    assert abs(motor["electrical_time_constant_ms"] - (10 / 5.4)) < 1e-12
    assert abs(motor["copper_loss_w_per_phase_at_0_85A"] - (0.85**2 * 5.4)) < 1e-12
    assert motor["full_steps_per_rev"] == 200
    assert "NOT_AXIS_CAPABILITY" in fixtures["FIX-PKP243D08B2"]["evidence"]


def test_dense_stack_is_volumetric_and_not_flat_or_universal_solver_claim():
    d = load()
    stack = d["smart_stack_reference"]
    joined = " ".join(stack["regions"])
    for token in (
        "STRUCTURE_DATUM",
        "CONDUCTOR_INTERCONNECT",
        "DIELECTRIC_ISOLATION",
        "CAPACITIVE_ELECTROSTATIC",
        "INDUCTIVE_MAGNETIC",
        "SENSOR_METROLOGY",
        "SAFE_STATE_PROTECTION",
        "IDENTITY_STATE_DBR",
    ):
        assert token in joined
    assert "not one universal solver" in stack["non_claims"]
    assert "not all regions required in every object" in stack["non_claims"]


def test_circular_reference_uses_comparison_without_invented_pass_threshold():
    d = load()
    circ = d["circular_reference"]
    assert circ["id"] == "UTP-ECO-RPET-REF-001"
    assert len(circ["comparator_metrics"]) >= 5
    assert "no universal pass percentage" in circ["acceptance"]
