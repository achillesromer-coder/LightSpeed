"""CGX analytical cross-sweep: numerical identities, regressions and evidence holds."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from cgx.manufacturing import compile_component, find_archetype, load_default_atlas
from cgx.manufacturing.cross_domain_emulation import (
    equation_kernel_fingerprint, run_cross_domain_emulation, _integrate_phase,
    REQUIRED_EQUATIONS, FACTOR_NAMES,
)
from cgx.manufacturing.digital_service_stack import compile_digital_service_stack
from cgx.manufacturing.composition import digest

ROOT = Path(__file__).resolve().parents[1] / "cgx/manufacturing"


def inputs():
    ir = compile_component(find_archetype(load_default_atlas(), "PN rectifier diode"),
                           build_id="pc01-three-layer-coupon")
    geometry = json.loads((ROOT / "printspace_composite_pilot_v0_1.json").read_text())
    choices = json.loads((ROOT / "pc01_interface_witness_plan_v0_1.json").read_text())
    clearance = json.loads((ROOT / "pc01_tolerance_static_screen_v0_1.json").read_text())
    scenario = json.loads((ROOT / "pc01_synthetic_cross_sweep_v0_1.json").read_text())
    for obj in (geometry, choices, clearance):
        obj["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
    scenario["source_equation_library_sha256"] = equation_kernel_fingerprint()
    assert scenario["source_service_manifest_sha256"] == (
        compile_digital_service_stack(ir, geometry, choices, clearance_plan=clearance)["manifest_sha256"]
    )
    return ir, geometry, choices, clearance, scenario


def run(*args):
    return run_cross_domain_emulation(*(args or inputs()))


def test_216_case_six_factor_cross_sweep_source_bound_and_nonexecuting():
    report = run()
    assert report["state"] == "SYNTHETIC_FACTORIAL_SCREEN_COMPLETE_PHYSICAL_HOLD"
    assert report["case_count"] == 216 == len(report["cases"])
    assert tuple(report["factor_grid"]) == FACTOR_NAMES
    assert report["source_digests"]["equation_kernel_v0_1"] == equation_kernel_fingerprint()
    assert report["source_digests"]["service_manifest"] == (
        "b9d9a67b1d747b29e6eae89a993ec986835b389b95ac5519650f345ba8a67318"
    )
    assert report["source_digests"]["geometry_composite"] == (
        "55b8de2df57a8b19ecda4d5ab0ed0619de57789e21e793ea2170a68b00dfb613"
    )
    assert report["equation_kernel_ids"] == list(REQUIRED_EQUATIONS)
    assert len(report["cross_factor_interactions"]) == 15
    assert report["screening_summary"]["cases"] == 216
    assert sum(report["screening_summary"]["states"].values()) == 216
    assert report["screening_summary"]["cross_interactions_evaluated"] == 15
    assert len({r["scenario_id"] for r in report["cases"]}) == 216
    assert report["conductor_path_length_m"] == pytest.approx(0.004)
    assert report["conductor_rectangular_cross_section_m2"] == pytest.approx(4e-6)
    assert len(report["result_sha256"]) == 64
    assert report["result_sha256"] == digest({k:v for k,v in report.items() if k != "result_sha256"})
    assert report["numeric_real_material_model_verified"] is False
    assert report["external_solver_executed"] is False
    assert report["physical_evidence_verified"] is False
    for flag in ("machine_authorised", "native_dbr_written", "mint_authorised",
                 "commercial_release_authorised"):
        assert report[flag] is False


def test_all_valid_phases_are_explicitly_non_actuating():
    report=run()
    candidates=[x for x in report["cases"] if x["peak_temperature_k"] is not None]
    assert candidates
    for x in candidates:
        assert [p["phase"] for p in x["sequence"]] == [
            "PREPARE", "ANALYTICAL_ENERGISE", "ANALYTICAL_RECOVER",
            "UNMEASURED_READBACK_HOLD",
        ]
        assert all(p["device_operation_executed"] is False for p in x["sequence"])
        assert x["sequence"][-1]["real_sensor_trace"] is None
        assert x["sequence"][-1]["native_dbr_receipt"] is None
        assert x["dielectric_current_path_assumed"] is False


def test_first_law_energy_residual_small_for_every_stable_case():
    report=run()
    results=[r for r in report["cases"] if r["energy_balance_max_residual_j"] is not None]
    assert results
    assert max(r["energy_balance_max_residual_j"] for r in results) < 1e-8
    assert report["screening_summary"]["max_abs_energy_balance_residual_j"] < 1e-8


def test_independent_alpha_zero_analytic_energy_solution():
    c=0.5
    r0=0.2
    theta=20
    i=0.5
    t=30
    out=_integrate_phase(0,t,i,r0,0.0,theta,c)
    equilibrium=i*i*r0*theta
    expected=equilibrium*(1-math.exp(-t/(theta*c)))
    assert out["theta_end_k"] == pytest.approx(expected,abs=1e-13)
    assert out["electrical_energy_j"] == pytest.approx(i*i*r0*t)
    assert out["first_law_residual_j"] == pytest.approx(0,abs=1e-12)


def test_independent_decay_solution():
    start=13.0
    theta=15
    c=0.5
    seconds=35
    out=_integrate_phase(start,seconds,0,0.5,0.003,theta,c)
    assert out["theta_end_k"] == pytest.approx(start*math.exp(-seconds/(theta*c)))
    assert out["electrical_energy_j"] == 0
    assert out["first_law_residual_j"] == pytest.approx(0,abs=1e-11)


def test_screen_monotone_current_and_resistance_with_other_factors_frozen():
    cases=run()["cases"]
    def group(**fixed):
        return sorted((x for x in cases if all(x["factors"][k]==v for k,v in fixed.items())),
                      key=lambda x:x["factors"]["test_current_a"])
    sample=group(external_terminal_resistance_ohm=0.2,
                 effective_thermal_resistance_k_per_w=20,
                 relative_cte_per_k=0.0,
                 energise_duration_s=30,
                 synthetic_boundary_multiplier=1)
    assert len(sample) == 3
    assert sample[0]["peak_temperature_k"] < sample[1]["peak_temperature_k"] < sample[2]["peak_temperature_k"]
    by_r=sorted((x for x in cases
                 if x["factors"]["test_current_a"]==0.5
                 and x["factors"]["effective_thermal_resistance_k_per_w"]==20
                 and x["factors"]["relative_cte_per_k"]==0.0
                 and x["factors"]["energise_duration_s"]==30
                 and x["factors"]["synthetic_boundary_multiplier"]==1),
                key=lambda x:x["factors"]["external_terminal_resistance_ohm"])
    assert len(by_r)==3
    assert by_r[0]["peak_temperature_k"] < by_r[1]["peak_temperature_k"] < by_r[2]["peak_temperature_k"]


def test_longer_energising_and_boundary_multiplier_raise_peak():
    cases=run()["cases"]
    base={"test_current_a":1.0,"external_terminal_resistance_ohm":0.8,
          "effective_thermal_resistance_k_per_w":20,
          "relative_cte_per_k":0.00005}
    short=next(x for x in cases if all(x["factors"][k]==v for k,v in base.items())
               and x["factors"]["energise_duration_s"]==30
               and x["factors"]["synthetic_boundary_multiplier"]==1)
    long=next(x for x in cases if all(x["factors"][k]==v for k,v in base.items())
              and x["factors"]["energise_duration_s"]==120
              and x["factors"]["synthetic_boundary_multiplier"]==1)
    changed=next(x for x in cases if all(x["factors"][k]==v for k,v in base.items())
                 and x["factors"]["energise_duration_s"]==120
                 and x["factors"]["synthetic_boundary_multiplier"]==2)
    assert short["peak_temperature_k"] < long["peak_temperature_k"] < changed["peak_temperature_k"]


def test_relative_cte_changes_displacement_not_electrothermal_equation():
    cases=run()["cases"]
    base={"test_current_a":1.0,"external_terminal_resistance_ohm":0.8,
          "effective_thermal_resistance_k_per_w":80,
          "energise_duration_s":120,"synthetic_boundary_multiplier":2}
    zero=next(x for x in cases if all(x["factors"][k]==v for k,v in base.items())
              and x["factors"]["relative_cte_per_k"]==0)
    nonzero=next(x for x in cases if all(x["factors"][k]==v for k,v in base.items())
                 and x["factors"]["relative_cte_per_k"]==0.00005)
    assert zero["peak_temperature_k"] == nonzero["peak_temperature_k"]
    assert zero["max_relative_expansion_um"] == 0
    assert nonzero["max_relative_expansion_um"] > 0
    assert nonzero["independently_measured_tolerance_compatibility"] is False


def test_sweep_contains_synthetic_limit_exceedance_not_deployment_pass():
    report=run()
    assert report["screening_summary"]["states"].get("EXCEEDS_SYNTHETIC_LIMIT",0) > 0
    assert report["screening_summary"]["states"].get("WITHIN_SYNTHETIC_LIMIT_NOT_QUALIFIED",0)>0
    assert "actual_process_atmosphere" not in report
    assert "4d_actuation" in report["unmodelled_domains"]


def test_cross_factor_rankings_are_screening_not_statistics():
    output=run()
    assert len(output["screening_summary"]["factor_mean_spans"])==6
    assert all(v["interpretation"]=="DESCRIPTIVE_SURROGATE_SPAN_NOT_CAUSAL"
               for v in output["screening_summary"]["factor_mean_spans"])
    assert all(v["interpretation"]=="FINITE_GRID_CROSS_TERM_NOT_EMPIRICAL_INTERACTION"
               for v in output["cross_factor_interactions"])
    assert output["screening_summary"]["statistical_confidence_or_uncertainty"].startswith("NOT_ESTIMATED")


def test_deterministic_reproducibility_and_factor_order():
    i=inputs()
    a,b=run(*i),run(*copy.deepcopy(i))
    assert a==b
    assert [q["scenario_id"] for q in a["cases"]] == [q["scenario_id"] for q in b["cases"]]


@pytest.mark.parametrize("part,new",[
    ("source_service_manifest_sha256","0"*64),
    ("source_geometry_sha256","0"*64),
    ("source_equation_library_sha256","0"*64),
])
def test_stale_kernel_geometry_or_service_manifest_holds(part,new):
    args=list(inputs())
    args[4][part]=new
    assert run(*args)["state"]=="HOLD"


def test_changed_owner_row_or_tolerance_invalidates_full_replay():
    args=list(inputs())
    args[2]["region_selections"][0]["directional_sha256"]="0"*64
    assert run(*args)["state"]=="HOLD"
    args=list(inputs())
    args[3]["instance_uncertainties"][0]["max_abs_translation_error_um"][0]+=1
    assert run(*args)["state"]=="HOLD"


def test_synthetic_qualification_claim_cannot_enter_emulator():
    args=list(inputs())
    args[4]["evidence_status"]="MEASURED_VALIDATED"
    assert "MODEL_OR_AUTHORITY_ESCALATION" in run(*args)["hold_codes"]
    args=list(inputs())
    args[4]["device_command"]="move"
    assert "MODEL_OR_AUTHORITY_ESCALATION" in run(*args)["hold_codes"]


def test_malformed_parameter_and_nonfinite_rejected():
    args=list(inputs())
    args[4]["fixed"]["assumed_conductor_resistivity_ohm_m"]=float("nan")
    assert "NONCANONICAL_EXPERIMENT" in run(*args)["hold_codes"]
    args=list(inputs())
    args[4]["fixed"]["assumed_conductor_resistivity_ohm_m"]=0
    assert "INVALID_OR_NONFINITE_CONSTITUTIVE_INPUT" in run(*args)["hold_codes"]


def test_factor_grid_dimension_and_duplicate_levels_rejected():
    args=list(inputs())
    args[4]["factor_grid"]["test_current_a"]=[0.1,0.1,1.0]
    assert "INVALID_MONOTONE_BOUNDED_FACTOR_LEVELS" in run(*args)["hold_codes"]
    args=list(inputs())
    args[4]["factor_grid"]["test_current_a"]=[0.1,0.5,1.0,1.5]
    assert "INVALID_MONOTONE_BOUNDED_FACTOR_LEVELS" in run(*args)["hold_codes"]
    args=list(inputs())
    args[4]["factor_grid"]["relative_cte_per_k"]=[0,0.00002,0.00005]
    args[4]["factor_grid"]["synthetic_boundary_multiplier"]=[0.5,1.0,2.0]
    assert "FACTORIAL_CASE_LIMIT" in run(*args)["hold_codes"]


def test_bounded_assumed_thermal_feedback_does_not_claim_physical_runaway():
    args=list(inputs())
    # 2 A, 10 ohm contact, 500 K/W can force the *linear surrogate*
    # to have no stable finite steady state. This is NOT physical evidence.
    axes=args[4]["factor_grid"]
    axes["test_current_a"]=[1.0,2.0]
    axes["external_terminal_resistance_ohm"]=[0.1,10.0]
    axes["effective_thermal_resistance_k_per_w"]=[20.0,500.0]
    axes["relative_cte_per_k"]=[0,0.00005]
    axes["energise_duration_s"]=[10,30]
    axes["synthetic_boundary_multiplier"]=[1.0,2.0]
    report=run(*args)
    assert report["state"]=="SYNTHETIC_FACTORIAL_SCREEN_COMPLETE_PHYSICAL_HOLD"
    assert report["case_count"]==64
    assert report["screening_summary"]["states"].get("HOLD_NO_STABLE_LINEAR_STEADY_STATE",0) > 0
    assert report["physical_evidence_verified"] is False


def test_conductor_geom_changed_invalidates_provenance_before_simulation():
    args=list(inputs())
    args[1]["instances"][2]["translate_mm"][2]+=1
    assert run(*args)["state"]=="HOLD"


def test_correct_canonical_conductor_path_not_a_dielectric_short():
    report=run()
    assert all(c["dielectric_current_path_assumed"] is False for c in report["cases"])
    assert all(c["electrical_path"]=="CONDUCTOR_AND_EXTERNAL_TERMINAL_ONLY"
               for c in report["cases"])
    assert "dielectric_field_and_breakdown" in report["unmodelled_domains"]
    assert report["numeric_real_material_model_verified"] is False
