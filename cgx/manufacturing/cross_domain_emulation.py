"""Bounded analytical cross-domain/sequence emulator for a digital CGX composite.

Reuses the SAME canonical 12-service PrintSpace stack (including its optional
static tolerance screen) and source-owned Type-I equation kernel catalogue.
No native solver, CAD/CFD/FEM, empirical material fit, process controller,
actual physical equipment, chemistry model, dielectric conduction assumption,
4D material activation, hardware commands, private LOAD or DBR mutation.

The surrogate is deliberately *one lumped thermal node* around an assumed
resistive conductor plus ASSUMED external TERMINAL resistance. No current
path is asserted across the dielectric layer. Its steady-state algebra and
closed-form time evolution are exactly the stated illustrative constitutive
assumptions, not independently verified physics of PC01/PrintCeptor.
"""
from __future__ import annotations

import itertools
import json
import math
import statistics
from pathlib import Path
from typing import Any

from .composition import digest
from .digital_service_stack import compile_digital_service_stack, verify_digital_service_stack_backwards
from .solid_metrics import measure_composite_nominal

SCHEMA = "CGX-PRINTSPACE-ANALYTICAL-CROSS-SWEEP/0.1"
RESULT_SCHEMA = "CGX-PRINTSPACE-CROSS-DOMAIN-EMULATION/0.1"
MAX_CASES = 256
MAX_REQUEST_BYTES = 64 * 1024
EQUATION_LIBRARY = Path(__file__).resolve().parents[1] / "component_atlas" / "type1_equation_kernel_v0_1.json"
REQUIRED_EQUATIONS = (
    "T1K-001",  # thermal expansion, geometry
    "T1K-002",  # R=rho*L/A and I²R
    "T1K-004",  # lumped thermal RC/TCR archetype
    "T1K-013",  # thermal boundaries and C*deltaT
    "T1K-018",  # static clearance and service access
    "T1K-019",  # identity/DBR remains externally gated
)
FACTOR_NAMES = (
    "test_current_a",
    "external_terminal_resistance_ohm",
    "effective_thermal_resistance_k_per_w",
    "relative_cte_per_k",
    "energise_duration_s",
    "synthetic_boundary_multiplier",
)


def _hold(code: str) -> dict[str, Any]:
    return {
        "schema": RESULT_SCHEMA, "state": "HOLD",
        "hold_codes": [code], "case_count": 0, "result_sha256": None,
        "cases": [], "screening_summary": None, "cross_factor_interactions": [],
        "numeric_real_material_model_verified": False, "external_solver_executed": False,
        "physical_evidence_verified": False, "machine_authorised": False,
        "native_dbr_written": False, "mint_authorised": False,
        "commercial_release_authorised": False,
    }


def _finite(v: Any, lower: float, upper: float, *, strict_low: bool = False) -> bool:
    return (type(v) in (int, float) and math.isfinite(v)
            and (lower < v if strict_low else lower <= v) and v <= upper)


def equation_kernel_fingerprint() -> str:
    source = json.loads(EQUATION_LIBRARY.read_text(encoding="utf-8"))
    if (source.get("schema") != "CGX-TYPE1-EQUATION-KERNEL/0.1"
            or not isinstance(source.get("kernels"), list)
            or len(source["kernels"]) != 20):
        raise ValueError("EXISTING_TYPE1_KERNEL_LIBRARY_INVALID")
    keyed = {x.get("kernel_id"): x for x in source["kernels"] if isinstance(x, dict)}
    if len(keyed) != 20 or any(key not in keyed for key in REQUIRED_EQUATIONS):
        raise ValueError("MISSING_EXISTING_EQUATION_KERNELS")
    return digest(source)


def _exact_slab_path(geometry: dict, *, region_id: str, axis: str) -> tuple[float, float]:
    """Use existing verified convex solids; admit a box only when volume=AABB."""
    metrics = measure_composite_nominal(geometry)
    if metrics["state"] != "EXACT_DIGITAL_NOMINAL_ONLY":
        raise ValueError("EXACT_NOMINAL_SOLIDS_UNVERIFIED")
    from .composition import compile_geometry_composition
    reviewed = compile_geometry_composition(geometry)
    inst = next((r for r in reviewed["graph"]["instances"]
                 if r["instance_id"] == region_id), None)
    part = next((r for r in metrics["parts"] if r["instance_id"] == region_id), None)
    if inst is None or part is None or part["material_slot"] != "conductive":
        raise ValueError("CONDUCTOR_REGION_UNBOUND")
    bounds = inst["bounds_mm"]
    sizes = [b-a for a,b in zip(bounds["min_mm"], bounds["max_mm"])]
    if any(not isinstance(q, int) or q <= 0 for q in sizes):
        raise ValueError("INVALID_CONDUCTIVE_GEOMETRY")
    volume = sizes[0] * sizes[1] * sizes[2]
    if part["volume_mm3_exact"] != str(volume):
        raise ValueError("CONDUCTOR_NOT_VERIFIED_RECTANGULAR_BOX")
    direction = "xyz".index(axis)
    length_m = sizes[direction] * 1e-3
    area_m2 = (volume/sizes[direction]) * 1e-6
    return length_m, area_m2


def _integrate_phase(theta0: float, seconds: float, current: float, r0: float,
                     tcr: float, theta_k_w: float, heat_cap: float) -> dict:
    """Analytic C*dtheta/dt=I²R0*(1+tcr*theta)-theta/Rtheta.

    Integrate energy inputs and losses exactly within this linear surrogate.
    Avoid small-argument cancellation via bounded Taylor terms.
    """
    inp0 = current*current*r0
    a = inp0/heat_cap
    k = (inp0*tcr - 1/theta_k_w)/heat_cap
    z = k*seconds
    if abs(z) < 1e-5:
        e = seconds*(1 + z/2 + z*z/6 + z*z*z/24 + z*z*z*z/120)
        j = seconds*seconds*(0.5 + z/6 + z*z/24 + z*z*z/120)
    else:
        e = math.expm1(z)/k
        j = (e-seconds)/k
    new_theta = theta0*math.exp(z) + a*e
    integral_theta = theta0*e + a*j
    electrical_j = inp0*(seconds+tcr*integral_theta)
    rejected_j = integral_theta/theta_k_w
    stored_j = heat_cap*(new_theta-theta0)
    residual = stored_j-electrical_j+rejected_j
    return {
        "theta_end_k": new_theta, "electrical_energy_j": electrical_j,
        "thermal_boundary_energy_j": rejected_j,
        "stored_thermal_energy_change_j": stored_j,
        "first_law_residual_j": residual,
        "duration_s": seconds, "current_a": current,
    }


def _single_case(factors: dict[str, float], fixed: dict, path: tuple[float, float],
                 lateral_bounds: list[dict]) -> dict:
    current = factors["test_current_a"]
    r_contact = factors["external_terminal_resistance_ohm"]
    thermal = factors["effective_thermal_resistance_k_per_w"] * factors["synthetic_boundary_multiplier"]
    mismatch = factors["relative_cte_per_k"]
    seconds = factors["energise_duration_s"]
    resistivity = fixed["assumed_conductor_resistivity_ohm_m"]
    r_bulk = resistivity * path[0] / path[1]
    r0 = r_bulk + r_contact
    alpha = fixed["assumed_effective_network_tcr_per_k"]
    c = fixed["assumed_lumped_heat_capacity_j_per_k"]
    dimensionless_feedback = current*current*r0*alpha*thermal
    key = digest(factors)[:20]
    common = {
        "scenario_id": key, "factors": factors,
        "nominal_bulk_resistance_ohm": r_bulk,
        "hypothetical_terminal_resistance_ohm": r_contact,
        "effective_thermal_resistance_k_per_w": thermal,
        "dimensionless_positive_feedback_ratio": dimensionless_feedback,
        "electrical_path": "CONDUCTOR_AND_EXTERNAL_TERMINAL_ONLY",
        "dielectric_current_path_assumed": False,
        "material_and_boundary_properties": "USER_ASSUMED_NOT_OBSERVED",
        "numeric_physical_qualification": False,
    }
    if dimensionless_feedback >= 1:
        return {**common, "screen_state": "HOLD_NO_STABLE_LINEAR_STEADY_STATE",
                "peak_temperature_k": None, "max_relative_expansion_um": None,
                "energy_balance_max_residual_j": None, "sequence": [],
                "empirical_material_authority": False}
    on = _integrate_phase(0.0, seconds, current, r0, alpha, thermal, c)
    off = _integrate_phase(on["theta_end_k"], fixed["recover_duration_s"], 0.0,
                           r0, alpha, thermal, c)
    rise = on["theta_end_k"]
    peak_t = fixed["ambient_temperature_k"]+rise
    drift_um = abs(fixed["mechanical_reference_length_mm"]*1000*mismatch*rise)
    balance = max(abs(on["first_law_residual_j"]), abs(off["first_law_residual_j"]))
    if not math.isfinite(peak_t) or not math.isfinite(drift_um) or not math.isfinite(balance):
        return {**common, "screen_state": "HOLD_NONFINITE_MODEL_RESULT",
                "peak_temperature_k": None, "max_relative_expansion_um": None,
                "energy_balance_max_residual_j": None, "sequence": [],
                "empirical_material_authority": False}
    if balance > 1e-7 * max(1.0, on["electrical_energy_j"], off["thermal_boundary_energy_j"]):
        return {**common, "screen_state": "HOLD_ANALYTICAL_ENERGY_BALANCE",
                "peak_temperature_k": None, "max_relative_expansion_um": None,
                "energy_balance_max_residual_j": balance, "sequence": [],
                "empirical_material_authority": False}
    at_ambient = fixed["ambient_temperature_k"]
    exceeds = peak_t > fixed["synthetic_temperature_screen_limit_k"]
    return {
        **common,
        "screen_state": ("EXCEEDS_SYNTHETIC_LIMIT" if exceeds
                         else "WITHIN_SYNTHETIC_LIMIT_NOT_QUALIFIED"),
        "steady_state_temperature_rise_k_ideal": (
            (current*current*r0*thermal)/(1-dimensionless_feedback)),
        "peak_temperature_k": peak_t,
        "peak_temperature_rise_k": rise,
        "final_temperature_k": at_ambient+off["theta_end_k"],
        "max_relative_expansion_um": drift_um,
        "interface_lateral_relative_shift_budget_um": lateral_bounds,
        "independently_measured_tolerance_compatibility": False,
        "peak_electrical_power_w": current*current*r0*(1+alpha*rise),
        "integrated_input_energy_j": on["electrical_energy_j"],
        "integrated_boundary_energy_j": on["thermal_boundary_energy_j"]+off["thermal_boundary_energy_j"],
        "energy_balance_max_residual_j": balance,
        "sequence": [
            {"phase": "PREPARE", "time_s": 0, "temperature_k": at_ambient,
             "device_operation_executed": False},
            {"phase": "ANALYTICAL_ENERGISE", "time_s": seconds,
             "temperature_k": peak_t, "energy_in_j": on["electrical_energy_j"],
             "device_operation_executed": False},
            {"phase": "ANALYTICAL_RECOVER", "time_s": seconds+fixed["recover_duration_s"],
             "temperature_k": at_ambient+off["theta_end_k"],
             "energy_out_j": off["thermal_boundary_energy_j"],
             "device_operation_executed": False},
            {"phase": "UNMEASURED_READBACK_HOLD",
             "real_sensor_trace": None, "real_machine_calibration": None,
             "native_dbr_receipt": None, "device_operation_executed": False},
        ],
        "empirical_material_authority": False,
    }


def _analysis(cases: list[dict], axes: dict) -> tuple[dict, list[dict]]:
    stable = [c for c in cases if c["peak_temperature_k"] is not None]
    statuses: dict[str, int] = {}
    for c in cases:
        statuses[c["screen_state"]] = statuses.get(c["screen_state"], 0)+1
    factor_spans: list[dict] = []
    for key in FACTOR_NAMES:
        groups = {}
        for level in axes[key]:
            subset = [c["peak_temperature_k"] for c in stable if c["factors"][key] == level]
            groups[str(level)] = {"case_count": len(subset),
                                  "mean_peak_temperature_k": sum(subset)/len(subset) if subset else None}
        usable = [v["mean_peak_temperature_k"] for v in groups.values()
                  if v["mean_peak_temperature_k"] is not None]
        factor_spans.append({"factor": key, "levels": groups,
                             "screening_mean_span_k": max(usable)-min(usable) if usable else None,
                             "interpretation": "DESCRIPTIVE_SURROGATE_SPAN_NOT_CAUSAL"})
    factor_spans.sort(key=lambda x: (-x["screening_mean_span_k"]
                                    if x["screening_mean_span_k"] is not None else 0,
                                    x["factor"]))
    lookup = {tuple(c["factors"][key] for key in FACTOR_NAMES): c for c in cases}
    baseline = {name: axes[name][len(axes[name])//2] for name in FACTOR_NAMES}
    pairs: list[dict] = []
    for x, y in itertools.combinations(FACTOR_NAMES, 2):
        def at(vx, vy):
            f = dict(baseline)
            f[x] = vx
            f[y] = vy
            return lookup[tuple(f[k] for k in FACTOR_NAMES)]["peak_temperature_k"]
        lowlow = at(axes[x][0], axes[y][0])
        lowhigh = at(axes[x][0], axes[y][-1])
        highlow = at(axes[x][-1], axes[y][0])
        highhigh = at(axes[x][-1], axes[y][-1])
        interaction = (highhigh-highlow-lowhigh+lowlow
                       if all(v is not None for v in (lowlow, lowhigh, highlow, highhigh))
                       else None)
        pairs.append({"factor_a": x, "factor_b": y,
                      "end_level_difference_of_differences_k": interaction,
                      "interpretation": "FINITE_GRID_CROSS_TERM_NOT_EMPIRICAL_INTERACTION"})
    pairs.sort(key=lambda q: (-abs(q["end_level_difference_of_differences_k"])
                              if q["end_level_difference_of_differences_k"] is not None else 0,
                              q["factor_a"], q["factor_b"]))
    summary = {
        "cases": len(cases), "states": dict(sorted(statuses.items())),
        "peak_temperature_k_min": min(c["peak_temperature_k"] for c in stable) if stable else None,
        "peak_temperature_k_max": max(c["peak_temperature_k"] for c in stable) if stable else None,
        "max_ideal_relative_expansion_um": max(c["max_relative_expansion_um"] for c in stable) if stable else None,
        "max_abs_energy_balance_residual_j": max(c["energy_balance_max_residual_j"] for c in stable) if stable else None,
        "factor_mean_spans": factor_spans, "cross_interactions_evaluated": len(pairs),
        "statistical_confidence_or_uncertainty": "NOT_ESTIMATED_SYNTHETIC_FACTORIAL_ENUMERATION",
        "real_material_equipment_or_process_results": None,
    }
    return summary, pairs


def run_cross_domain_emulation(manufacturing_ir: Any, geometry_request: Any,
                               interface_selections: Any, clearance_plan: Any,
                               experiment: Any) -> dict:
    """Run bounded reproducible factorial *hypothetical* operating scenarios."""
    if not isinstance(experiment, dict):
        return _hold("INVALID_EXPERIMENT")
    try:
        enc = json.dumps(experiment, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("ascii")
    except (TypeError, ValueError, RecursionError, OverflowError):
        return _hold("NONCANONICAL_EXPERIMENT")
    if len(enc) > MAX_REQUEST_BYTES:
        return _hold("EXPERIMENT_SIZE_BUDGET")
    required = {"schema", "model", "evidence_status", "source_equation_library_sha256",
                "source_service_manifest_sha256", "source_geometry_sha256",
                "conductor_instance_id", "conductor_path_axis", "factor_grid", "fixed"}
    if (set(experiment) != required or experiment.get("schema") != SCHEMA
            or experiment.get("model") != "ONE_NODE_ANALYTICAL_ELECTROTHERMAL_ELASTIC_SCREEN"
            or experiment.get("evidence_status") != "SYNTHETIC_UNCALIBRATED_NO_ACTUATION"):
        return _hold("MODEL_OR_AUTHORITY_ESCALATION")
    try:
        equations_sha = equation_kernel_fingerprint()
    except (ValueError, OSError, TypeError):
        return _hold("CANONICAL_EQUATION_KERNEL_UNAVAILABLE")
    if experiment["source_equation_library_sha256"] != equations_sha:
        return _hold("STALE_OWNER_EQUATION_KERNEL")
    original_stack = compile_digital_service_stack(
        manufacturing_ir, geometry_request, interface_selections,
        clearance_plan=clearance_plan)
    if (original_stack.get("state") != "DIGITAL_STACK_REVIEW_ONLY_PHYSICAL_HOLD"
            or original_stack.get("manifest_sha256") != experiment.get("source_service_manifest_sha256")
            or original_stack.get("geometry_sha256") != experiment.get("source_geometry_sha256")):
        return _hold("EXACT_SOURCE_SERVICE_OR_GEOMETRY_MISMATCH")
    reversed_result = verify_digital_service_stack_backwards(
        original_stack, manufacturing_ir, geometry_request,
        interface_selections, clearance_plan=clearance_plan)
    if reversed_result.get("state") != "PASS_DIGITAL_ONLY":
        return _hold("BOTTOM_UP_SOURCE_REPLAY_UNVERIFIED")
    axes = experiment.get("factor_grid")
    if not isinstance(axes, dict) or set(axes) != set(FACTOR_NAMES):
        return _hold("MISSING_OR_UNKNOWN_FACTOR")
    allowed = {
        "test_current_a": (0.0, 2.0, False),
        "external_terminal_resistance_ohm": (0.0, 10.0, False),
        "effective_thermal_resistance_k_per_w": (0.01, 500.0, True),
        "relative_cte_per_k": (0.0, 0.0005, False),
        "energise_duration_s": (0.1, 600.0, True),
        "synthetic_boundary_multiplier": (0.1, 10.0, True),
    }
    count = 1
    for key in FACTOR_NAMES:
        v = axes[key]
        if (type(v) is not list or not 2 <= len(v) <= 3
                or any(not _finite(x, *allowed[key][:2], strict_low=allowed[key][2]) for x in v)
                or any(v[i] >= v[i+1] for i in range(len(v)-1))):
            return _hold("INVALID_MONOTONE_BOUNDED_FACTOR_LEVELS")
        count *= len(v)
    if count > MAX_CASES:
        return _hold("FACTORIAL_CASE_LIMIT")
    fixed = experiment.get("fixed")
    required_fixed = {
        "assumed_conductor_resistivity_ohm_m",
        "assumed_effective_network_tcr_per_k",
        "assumed_lumped_heat_capacity_j_per_k",
        "ambient_temperature_k",
        "synthetic_temperature_screen_limit_k",
        "recover_duration_s",
        "mechanical_reference_length_mm",
    }
    if not isinstance(fixed, dict) or set(fixed) != required_fixed:
        return _hold("INCOMPLETE_MODEL_CONSTANTS")
    bounds = {
        "assumed_conductor_resistivity_ohm_m": (1e-10, 1.0, True),
        "assumed_effective_network_tcr_per_k": (0, 0.05, False),
        "assumed_lumped_heat_capacity_j_per_k": (1e-5, 1000, True),
        "ambient_temperature_k": (200, 400, True),
        "synthetic_temperature_screen_limit_k": (200, 500, True),
        "recover_duration_s": (0.1, 1000, True),
        "mechanical_reference_length_mm": (0.001, 1000, True),
    }
    if any(not _finite(fixed[key], *bounds[key][:2], strict_low=bounds[key][2])
           for key in required_fixed):
        return _hold("INVALID_OR_NONFINITE_CONSTITUTIVE_INPUT")
    if fixed["synthetic_temperature_screen_limit_k"] <= fixed["ambient_temperature_k"]:
        return _hold("SCREEN_TEMPERATURE_BELOW_AMBIENT")
    if experiment.get("conductor_instance_id") != "conductive":
        return _hold("SOURCE_CONDUCTOR_REGION_UNBOUND")
    if experiment.get("conductor_path_axis") not in ("x", "y", "z"):
        return _hold("CONDUCTOR_PATH_AXIS_INVALID")
    try:
        path = _exact_slab_path(geometry_request, region_id=experiment["conductor_instance_id"],
                                axis=experiment["conductor_path_axis"])
    except (ValueError, TypeError, KeyError, IndexError):
        return _hold("SOURCE_CONDUCTOR_GEOMETRY_INVALID")
    from .tolerance_clearance import screen_static_tolerances
    clearance = screen_static_tolerances(geometry_request, clearance_plan)
    if clearance.get("state") != "SCREENED_STATIC_DIGITAL_ONLY":
        return _hold("STATIC_CLEARANCE_SOURCE_UNRESOLVED")
    shifts = [
        {"from": e["from"], "to": e["to"],
         "synthetic_lateral_shift_um": e["max_lateral_relative_shift_um"]}
        for e in clearance["interface_uncertainty"]
    ]
    cases = []
    for vals in itertools.product(*(axes[key] for key in FACTOR_NAMES)):
        f = dict(zip(FACTOR_NAMES, vals))
        case = _single_case(f, fixed, path, shifts)
        cases.append(case)
    summary, pairs = _analysis(cases, axes)
    out = {
        "schema": RESULT_SCHEMA, "state": "SYNTHETIC_FACTORIAL_SCREEN_COMPLETE_PHYSICAL_HOLD",
        "hold_codes": [
            "MATERIAL_LOTS_AND_CONSTITUTIVE_PARAMS_NOT_MEASURED",
            "SIMPLIFIED_ONE_NODE_MODEL_NOT_VALIDATED_FOR_PC01",
            "DIELECTRIC_AND_MULTILAYER_TRANSPORT_NOT_SIMULATED",
            "ACTUAL_PROCESS_ATMOSPHERE_CHEMISTRY_AND_4D_RESPONSE_UNMODELED",
            "SWEPT_TOOLPATH_AND_DEVICE_SAFETY_NOT_SIMULATED",
            "INDEPENDENT_C0_AND_NATIVE_OWNER_DBR_NOT_ADMITTED",
        ],
        "source_digests": {
            "equation_kernel_v0_1": equations_sha,
            "service_manifest": original_stack["manifest_sha256"],
            "geometry_composite": original_stack["geometry_sha256"],
            "static_tolerance_screen": original_stack["static_screen_sha256"],
            "owner_material_reference": digest(interface_selections),
            "experiment": digest(experiment),
        },
        "equation_kernel_ids": list(REQUIRED_EQUATIONS),
        "model_laws": [
            "R_bulk = resistivity * source_conductor_length / rectangular_cross_area",
            "R_network = R_bulk + ASSUMED external_terminal_R",
            "Ctheta*dtheta_dt = I²*R0*(1+alpha*theta) - theta/Rtheta",
            "delta_L_um = reference_length_mm*1000*relative_cte*peak_delta_temperature",
            "integrated_energy_in - boundary_energy_out = Ctheta*delta_temperature",
        ],
        "equation_use_gate": "ANALYTICALLY_VALID_ONLY_UNDER_DECLARED_SYNTHETIC_LUMPED_ASSUMPTIONS",
        "factor_grid": axes,
        "fixed_assumptions": fixed,
        "conductor_path_length_m": path[0],
        "conductor_rectangular_cross_section_m2": path[1],
        "operating_sequence": ["PREPARE", "ANALYTICAL_ENERGISE",
                               "ANALYTICAL_RECOVER", "UNMEASURED_READBACK_HOLD"],
        "case_count": len(cases),
        "cases": cases,
        "screening_summary": summary,
        "cross_factor_interactions": pairs,
        "cross_sweep_interpretation": "Finite-grid screening and difference-of-differences; no empirical calibration, causal identification or statistical confidence.",
        "unmodelled_domains": ["dielectric_field_and_breakdown", "real_material_chemistry",
                               "oxygen_moisture_and_reactive_transport", "strain_adhesion_and_delamination",
                               "nonconvex_geometry_and_actual_toolpath", "4d_actuation",
                               "distributed_electromagnetics", "fluid_pressure_and_safety"],
        "numeric_real_material_model_verified": False,
        "external_solver_executed": False,
        "physical_evidence_verified": False,
        "machine_authorised": False, "native_dbr_written": False,
        "mint_authorised": False, "commercial_release_authorised": False,
    }
    out["result_sha256"] = digest({k: v for k, v in out.items() if k != "result_sha256"})
    return out
