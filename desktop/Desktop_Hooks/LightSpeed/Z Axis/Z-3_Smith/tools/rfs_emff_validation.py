"""Evidence-gated RFS/EMFF screening calculations.

This module intentionally does not estimate extraction rate, purity, optimal
frequency, energy efficiency, or equipment safety. It records qualitative
observations and calculates only established first-order relations when the
required inputs and applicability statements are explicit.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Mapping

MU0 = 4.0 * math.pi * 1e-7


class ValidationError(ValueError):
    """Raised when an input is missing, non-numeric, or outside its domain."""


def _number(source: Mapping[str, Any], key: str, *, allow_zero: bool = True) -> float:
    if key not in source:
        raise ValidationError(f"Missing required input: {key}")
    value = source[key]
    if isinstance(value, bool):
        raise ValidationError(f"{key} must be numeric, not boolean")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{key} must be numeric") from exc
    if not math.isfinite(numeric):
        raise ValidationError(f"{key} must be finite")
    if numeric < 0 or (not allow_zero and numeric == 0):
        rule = "> 0" if not allow_zero else ">= 0"
        raise ValidationError(f"{key} must be {rule}")
    return numeric


def _bool_map_all_true(source: Mapping[str, Any], required: tuple[str, ...]) -> bool:
    return all(source.get(key) is True for key in required)


def evaluate(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Evaluate one evidence packet.

    Expected top-level blocks are optional and additive:
    - observation: qualitative source record
    - rfs: sinusoidal drive and particle inputs
    - emff: solenoid/gradient and particle susceptibility inputs
    - medium: optional Newtonian-fluid drag inputs
    - reasoning_evidence: independent applicability/control checks
    - empirical_evidence: repeat/control state

    The result never emits a performance claim. A mathematical/reasoning gate
    can promote a model result to controlled canon, while physical capability
    language remains blocked until empirical evidence is replicated.
    """

    result: Dict[str, Any] = {
        "schema_version": "1.0",
        "status": "SCREENING_ONLY",
        "epistemic_status": [],
        "calculations": {},
        "applicability": {},
        "gates": {},
        "claim_controls": {
            "extraction_rate_allowed": False,
            "purity_allowed": False,
            "optimal_frequency_allowed": False,
            "energy_efficiency_allowed": False,
            "equipment_safety_allowed": False,
        },
        "notes": [],
    }

    observation = payload.get("observation")
    if observation:
        if not isinstance(observation, Mapping):
            raise ValidationError("observation must be an object")
        result["observation"] = {
            "description": str(observation.get("description", "")).strip(),
            "source": str(observation.get("source", "UNSPECIFIED")).strip(),
            "instrumented": observation.get("instrumented") is True,
            "parameters_recorded": observation.get("parameters_recorded") is True,
        }
        if not result["observation"]["description"]:
            raise ValidationError("observation.description is required")
        if not result["observation"]["instrumented"]:
            result["epistemic_status"].append("OBSERVED_QUALITATIVE")
            result["notes"].append(
                "Observation retained without conversion to force, efficiency, purity, throughput, or optimal-frequency claims."
            )

    math_checks = []

    rfs = payload.get("rfs")
    particle_volume = None
    particle_mass = None
    if rfs is not None:
        if not isinstance(rfs, Mapping):
            raise ValidationError("rfs must be an object")
        frequency_hz = _number(rfs, "frequency_hz")
        amplitude_m = _number(rfs, "displacement_amplitude_m")
        particle_diameter_m = _number(rfs, "particle_diameter_m", allow_zero=False)
        particle_density_kg_m3 = _number(rfs, "particle_density_kg_m3", allow_zero=False)

        omega = 2.0 * math.pi * frequency_hz
        acceleration_peak = omega * omega * amplitude_m
        radius = particle_diameter_m / 2.0
        particle_volume = 4.0 * math.pi * radius**3 / 3.0
        particle_mass = particle_density_kg_m3 * particle_volume
        inertial_force_peak = particle_mass * acceleration_peak

        result["calculations"]["rfs"] = {
            "angular_frequency_rad_s": omega,
            "acceleration_peak_m_s2": acceleration_peak,
            "particle_volume_m3": particle_volume,
            "particle_mass_kg": particle_mass,
            "inertial_force_peak_n": inertial_force_peak,
        }
        result["epistemic_status"].append("CALCULATED_SCREENING")
        math_checks.extend(
            [
                math.isfinite(omega),
                math.isfinite(acceleration_peak),
                math.isfinite(particle_mass),
                math.isfinite(inertial_force_peak),
            ]
        )

    emff = payload.get("emff")
    magnetic_force_n = None
    if emff is not None:
        if not isinstance(emff, Mapping):
            raise ValidationError("emff must be an object")
        turns = _number(emff, "coil_turns")
        coil_length_m = _number(emff, "coil_length_m", allow_zero=False)
        current_a = _number(emff, "current_a")
        relative_permeability = _number(emff, "relative_permeability", allow_zero=False)
        susceptibility = float(emff.get("particle_susceptibility", 0.0))
        if not math.isfinite(susceptibility):
            raise ValidationError("particle_susceptibility must be finite")

        if particle_volume is None:
            particle_diameter_m = _number(emff, "particle_diameter_m", allow_zero=False)
            particle_density_kg_m3 = _number(emff, "particle_density_kg_m3", allow_zero=False)
            radius = particle_diameter_m / 2.0
            particle_volume = 4.0 * math.pi * radius**3 / 3.0
            particle_mass = particle_density_kg_m3 * particle_volume
        else:
            particle_diameter_m = (6.0 * particle_volume / math.pi) ** (1.0 / 3.0)

        b_t = MU0 * relative_permeability * (turns / coil_length_m) * current_a
        if "grad_b2_t2_per_m" in emff:
            grad_b2 = float(emff["grad_b2_t2_per_m"])
            if not math.isfinite(grad_b2):
                raise ValidationError("grad_b2_t2_per_m must be finite")
        else:
            grad_b = float(emff.get("field_gradient_t_per_m", 0.0))
            if not math.isfinite(grad_b):
                raise ValidationError("field_gradient_t_per_m must be finite")
            grad_b2 = 2.0 * b_t * grad_b

        magnetic_force_n = susceptibility * particle_volume * grad_b2 / (2.0 * MU0)
        result["calculations"]["emff"] = {
            "long_solenoid_field_t": b_t,
            "grad_b2_t2_per_m": grad_b2,
            "magnetic_force_linear_susceptibility_n": magnetic_force_n,
            "particle_volume_m3": particle_volume,
            "particle_mass_kg": particle_mass,
        }
        result["epistemic_status"].append("CALCULATED_SCREENING")
        math_checks.extend([math.isfinite(b_t), math.isfinite(grad_b2), math.isfinite(magnetic_force_n)])

        coil_diameter_m = emff.get("coil_diameter_m")
        if coil_diameter_m is not None:
            coil_diameter = _number(emff, "coil_diameter_m", allow_zero=False)
            aspect_ratio = coil_length_m / coil_diameter
            result["applicability"]["long_solenoid_aspect_ratio"] = aspect_ratio
            result["applicability"]["long_solenoid_screening_pass"] = aspect_ratio >= 2.0
        else:
            result["applicability"]["long_solenoid_screening_pass"] = False
            result["notes"].append("coil_diameter_m absent; long-solenoid applicability is not established.")

    medium = payload.get("medium")
    if medium is not None:
        if not isinstance(medium, Mapping):
            raise ValidationError("medium must be an object")
        if magnetic_force_n is None:
            raise ValidationError("medium drag calculation requires an EMFF magnetic-force calculation")
        viscosity = _number(medium, "dynamic_viscosity_pa_s", allow_zero=False)
        medium_density = _number(medium, "density_kg_m3", allow_zero=False)
        diameter = (6.0 * particle_volume / math.pi) ** (1.0 / 3.0)
        radius = diameter / 2.0
        drag_coefficient_n_s_m = 6.0 * math.pi * viscosity * radius
        terminal_velocity_m_s = magnetic_force_n / drag_coefficient_n_s_m
        reynolds = medium_density * abs(terminal_velocity_m_s) * diameter / viscosity
        result["calculations"]["medium"] = {
            "stokes_drag_coefficient_n_s_m": drag_coefficient_n_s_m,
            "terminal_velocity_screening_m_s": terminal_velocity_m_s,
            "reynolds_number": reynolds,
        }
        result["applicability"]["stokes_low_re_pass"] = reynolds < 0.1
        math_checks.extend(
            [
                math.isfinite(drag_coefficient_n_s_m),
                math.isfinite(terminal_velocity_m_s),
                math.isfinite(reynolds),
            ]
        )

    math_pass = bool(math_checks) and all(math_checks)
    reasoning = payload.get("reasoning_evidence", {})
    if reasoning and not isinstance(reasoning, Mapping):
        raise ValidationError("reasoning_evidence must be an object")
    required_reasoning = (
        "boundary_conditions_defined",
        "alternative_causes_controlled",
        "model_applicability_reviewed",
        "independent_reviewer",
    )
    reasoning_pass = _bool_map_all_true(reasoning, required_reasoning)

    if result["applicability"].get("long_solenoid_screening_pass") is False and emff is not None:
        reasoning_pass = False
    if result["applicability"].get("stokes_low_re_pass") is False and medium is not None:
        reasoning_pass = False

    empirical = payload.get("empirical_evidence", {})
    if empirical and not isinstance(empirical, Mapping):
        raise ValidationError("empirical_evidence must be an object")
    repeat_count = int(empirical.get("repeat_count", 0) or 0)
    controls_passed = empirical.get("controls_passed") is True
    instrumented = empirical.get("instrumented") is True
    raw_logs_attached = empirical.get("raw_logs_attached") is True
    empirical_verified = repeat_count >= 2 and controls_passed and instrumented and raw_logs_attached

    promotion_gate = empirical_verified or (math_pass and reasoning_pass)
    physical_capability_claim_allowed = empirical_verified

    result["gates"] = {
        "math_pass": math_pass,
        "independent_reasoning_pass": reasoning_pass,
        "empirical_verified": empirical_verified,
        "promotion_gate_to_controlled_canon": promotion_gate,
        "physical_capability_claim_allowed": physical_capability_claim_allowed,
    }
    if promotion_gate:
        result["status"] = "CONTROLLED_CANON_ELIGIBLE"
    if empirical_verified:
        result["status"] = "EMPIRICALLY_VERIFIED_CONTROLLED"
        result["epistemic_status"].append("EMPIRICALLY_VERIFIED")
    elif math_pass and reasoning_pass:
        result["epistemic_status"].append("DUAL_PROOF_MATH_REASONING")

    if not result["calculations"] and observation:
        result["gates"]["math_pass"] = False
        result["gates"]["promotion_gate_to_controlled_canon"] = False

    return result
