from __future__ import annotations

import math
from typing import Iterable

EPSILON_0_F_PER_M = 8.8541878128e-12


class InvariantInputError(ValueError):
    pass


def capacitance_density(*, epsilon_r: float, thickness_um: float) -> dict[str, float]:
    if epsilon_r <= 0 or thickness_um <= 0:
        raise InvariantInputError("epsilon_r and thickness_um must be positive")
    density_f_per_m2 = EPSILON_0_F_PER_M * epsilon_r / (thickness_um * 1e-6)
    density_pf_per_mm2 = density_f_per_m2 * 1e6
    return {
        "capacitance_density_pF_per_mm2": density_pf_per_mm2,
        "capacitance_density_pF_per_cm2": density_pf_per_mm2 * 100.0,
    }


def sheet_path_resistance(*, sheet_resistance_ohm_per_sq: float, length_to_width_ratio: float) -> float:
    if sheet_resistance_ohm_per_sq < 0 or length_to_width_ratio < 0:
        raise InvariantInputError("sheet resistance and L/W must be non-negative")
    return sheet_resistance_ohm_per_sq * length_to_width_ratio


def resistor_squares(*, target_resistance_ohm: float, sheet_resistance_ohm_per_sq: float) -> float:
    if target_resistance_ohm < 0 or sheet_resistance_ohm_per_sq <= 0:
        raise InvariantInputError("target resistance must be non-negative and sheet resistance positive")
    return target_resistance_ohm / sheet_resistance_ohm_per_sq


def rl_winding_baseline(*, inductance_h: float, resistance_ohm: float, current_a: float) -> dict[str, float]:
    if inductance_h < 0 or resistance_ohm <= 0:
        raise InvariantInputError("inductance must be non-negative and resistance positive")
    return {
        "electrical_time_constant_s": inductance_h / resistance_ohm,
        "copper_loss_w": current_a * current_a * resistance_ohm,
    }


def axis_force_budget(
    *,
    moving_mass_kg: float,
    acceleration_m_s2: float,
    process_force_n: float = 0.0,
    loss_force_n: float = 0.0,
    gravity_component_m_s2: float = 0.0,
) -> float:
    if moving_mass_kg < 0 or process_force_n < 0 or loss_force_n < 0:
        raise InvariantInputError("mass and positive allowance terms must be non-negative")
    return (
        moving_mass_kg * acceleration_m_s2
        + process_force_n
        + loss_force_n
        + moving_mass_kg * gravity_component_m_s2
    )


def rss_uncertainty(independent_uncertainties: Iterable[float]) -> float:
    values = [float(v) for v in independent_uncertainties]
    if any(v < 0 for v in values):
        raise InvariantInputError("uncertainty magnitudes must be non-negative")
    return math.sqrt(sum(v * v for v in values))


def retention_ratio(*, recovered_value: float, control_value: float) -> dict[str, float]:
    if control_value == 0:
        raise InvariantInputError("control_value must be non-zero")
    ratio = recovered_value / control_value
    return {"retention_ratio": ratio, "retention_percent": ratio * 100.0}


def evaluate_invariant(invariant_id: str, inputs: dict) -> dict:
    if invariant_id == "INV-CAP-DENSITY-001":
        return {"state": "NUMERIC_IF_INPUTS_ATTRIBUTABLE", **capacitance_density(**inputs)}
    if invariant_id == "INV-SHEET-R-001":
        return {"state": "NUMERIC_IF_INPUTS_ATTRIBUTABLE", "resistance_ohm": sheet_path_resistance(**inputs)}
    if invariant_id == "INV-R-SQUARES-001":
        return {"state": "NUMERIC_IF_INPUTS_ATTRIBUTABLE", "required_squares": resistor_squares(**inputs)}
    if invariant_id == "INV-RL-001":
        return {"state": "NUMERIC_IF_INPUTS_ATTRIBUTABLE", **rl_winding_baseline(**inputs)}
    if invariant_id == "INV-AXIS-FORCE-001":
        return {"state": "NUMERIC_IF_INPUTS_ATTRIBUTABLE", "required_axis_force_n": axis_force_budget(**inputs)}
    if invariant_id == "INV-UNC-RSS-001":
        return {"state": "NUMERIC_IF_INDEPENDENT_LINEAR_TERMS", "rss_uncertainty": rss_uncertainty(inputs["independent_uncertainties"])}
    if invariant_id == "INV-RETENTION-001":
        return {"state": "NUMERIC_IF_LIKE_FOR_LIKE_TESTS", **retention_ratio(**inputs)}
    raise KeyError(f"unknown-invariant:{invariant_id}")
