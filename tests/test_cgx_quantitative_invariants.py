from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from cgx.manufacturing import (
    InvariantInputError,
    axis_force_budget,
    capacitance_density,
    evaluate_invariant,
    retention_ratio,
    resistor_squares,
    rl_winding_baseline,
    rss_uncertainty,
    sheet_path_resistance,
)

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = json.loads((ROOT / "cgx" / "component_atlas" / "type1_quantitative_invariant_library_v0_1.json").read_text(encoding="utf-8"))
SMART = json.loads((ROOT / "cgx" / "manufacturing" / "dense_smart_stack_reference_v0_1.json").read_text(encoding="utf-8"))


def test_utp139_library_is_factorized_and_evidence_bounded() -> None:
    assert LIBRARY["artifact_id"] == "UTP-139"
    assert len(LIBRARY["invariants"]) == 7
    assert "411 archetype matrix" in LIBRARY["rule"]
    boundary = " ".join(LIBRARY["boundaries"]).lower()
    assert "source sku is not observed lot" in boundary
    assert "numeric inference is not coupon measurement" in boundary
    assert "physical execution" in boundary


def test_capacitance_density_matches_owner_kapton_fixtures() -> None:
    d25 = capacitance_density(epsilon_r=3.4, thickness_um=25)
    d50 = capacitance_density(epsilon_r=3.4, thickness_um=50)
    assert d25["capacitance_density_pF_per_mm2"] == pytest.approx(1.2041695425408)
    assert d50["capacitance_density_pF_per_mm2"] == pytest.approx(0.6020847712704)
    assert d25["capacitance_density_pF_per_cm2"] == pytest.approx(120.41695425408)


def test_sheet_resistance_and_resistor_squares_factor_geometry_without_rating_claim() -> None:
    assert sheet_path_resistance(sheet_resistance_ohm_per_sq=0.007, length_to_width_ratio=1) == pytest.approx(0.007)
    assert resistor_squares(target_resistance_ohm=1000, sheet_resistance_ohm_per_sq=50) == pytest.approx(20)
    assert resistor_squares(target_resistance_ohm=1000, sheet_resistance_ohm_per_sq=5000) == pytest.approx(0.2)


def test_motor_winding_baseline_matches_source_example_without_axis_uplift() -> None:
    result = rl_winding_baseline(inductance_h=0.01, resistance_ohm=5.4, current_a=0.85)
    assert result["electrical_time_constant_s"] == pytest.approx(0.0018518518518518517)
    assert result["copper_loss_w"] == pytest.approx(3.9015)


def test_axis_force_budget_is_parameterized_and_requires_real_machine_inputs() -> None:
    assert axis_force_budget(
        moving_mass_kg=2.0,
        acceleration_m_s2=3.0,
        process_force_n=4.0,
        loss_force_n=1.0,
        gravity_component_m_s2=0.0,
    ) == pytest.approx(11.0)
    with pytest.raises(InvariantInputError):
        axis_force_budget(moving_mass_kg=-1.0, acceleration_m_s2=1.0)


def test_uncertainty_and_recovered_control_comparison_are_bounded_helpers() -> None:
    assert rss_uncertainty([3, 4]) == pytest.approx(5)
    retention = retention_ratio(recovered_value=80, control_value=100)
    assert retention == {"retention_ratio": pytest.approx(0.8), "retention_percent": pytest.approx(80.0)}
    with pytest.raises(InvariantInputError):
        retention_ratio(recovered_value=1, control_value=0)


def test_dispatcher_marks_numeric_results_as_conditional_not_measurement() -> None:
    result = evaluate_invariant("INV-CAP-DENSITY-001", {"epsilon_r": 3.4, "thickness_um": 25})
    assert result["state"] == "NUMERIC_IF_INPUTS_ATTRIBUTABLE"
    assert result["capacitance_density_pF_per_mm2"] == pytest.approx(1.2041695425408)
    with pytest.raises(KeyError):
        evaluate_invariant("INV-NOT-REAL", {})


def test_dense_smart_stack_reuses_existing_kernels_and_keeps_safety_held() -> None:
    assert SMART["artifact_id"] == "UTP-139"
    assert SMART["assembly"]["coupled_kernel"] == "VGK-036"
    assert SMART["assembly"]["physical_execution"] is False
    assert len(SMART["regions"]) == 12
    assert len({row["id"] for row in SMART["regions"]}) == 12
    safe = next(row for row in SMART["regions"] if row["id"] == "REG-SAFE")
    seed = next(row for row in SMART["regions"] if row["id"] == "REG-SEED")
    assert safe["state"] == "HOLD"
    assert seed["state"] == "INSERT_SEED"
    assert "not a device design" in SMART["authority_boundary"]


def test_cli_evaluates_invariant_and_returns_smart_stack_reference(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs.json"
    inputs.write_text(json.dumps({"epsilon_r": 3.4, "thickness_um": 50}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "compile_cgx_manufacturing.py"), "invariant", "--id", "INV-CAP-DENSITY-001", "--inputs", str(inputs)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    result = json.loads(proc.stdout)
    assert result["capacitance_density_pF_per_mm2"] == pytest.approx(0.6020847712704)

    proc2 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "compile_cgx_manufacturing.py"), "smart-stack-reference"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    stack = json.loads(proc2.stdout)
    assert stack["cgx_uri"] == "cgx://manufacturing/smart-stack/type1-dense-reference-v0.1"
    assert stack["assembly"]["physical_execution"] is False
