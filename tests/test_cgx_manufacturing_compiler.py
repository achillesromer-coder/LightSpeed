from __future__ import annotations

import json
from pathlib import Path

import pytest

from cgx.manufacturing import (
    AdapterError,
    compile_assembly,
    compile_component,
    emit_reference_gcode,
    find_archetype,
    load_default_atlas,
    validate_simulation_result,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads(
    (ROOT / "cgx" / "manufacturing" / "minimal_scope_validation_v0_1.json").read_text(
        encoding="utf-8"
    )
)
ATLAS = load_default_atlas()


def _record_for_case(case: dict) -> dict:
    if "query" in case:
        return find_archetype(ATLAS, case["query"])
    domain = case["query_contains_domain"].lower()
    name = case["query_contains_name"].lower()
    matches = [
        r
        for r in ATLAS["records"]
        if domain in r.get("Domain", "").lower()
        and name in r.get("Component Archetype", "").lower()
    ]
    assert matches, case
    return matches[0]


def test_validation_matrix_covers_minimal_and_consequential_scopes() -> None:
    for case in FIXTURES["cases"]:
        record = _record_for_case(case)
        compiled = compile_component(record, build_id=f"fixture-{case['id']}")
        included = set(compiled["scope_decision"]["included"])
        omitted = set(compiled["scope_decision"]["omitted"])
        assert set(case.get("must_include", [])) <= included, case["id"]
        assert set(case.get("must_omit", [])) <= omitted, case["id"]
        assert compiled["process_strategy"] == case["strategy"], case["id"]
        assert compiled["execution_state"] == "HOLD"
        assert compiled["physical_execution"] is False


def test_diode_seed_does_not_acquire_generic_pressure_spatial_or_gravity_work() -> None:
    diode = compile_component(find_archetype(ATLAS, "PN rectifier diode"))
    included = set(diode["scope_decision"]["included"])
    assert {"electrical", "thermal", "esd", "cleanliness"} <= included
    assert {"pressure", "fluid", "gravity", "radiation", "optical"} <= set(
        diode["scope_decision"]["omitted"]
    )
    assert diode["process_strategy"] == "HYBRID_SEED"
    assert any(op["opcode"] == "PLACE_SEED" for op in diode["operations"])
    assert all(op["physical_execution"] is False for op in diode["operations"])


def test_exact_process_condition_can_add_pressure_without_changing_archetype() -> None:
    diode = compile_component(
        find_archetype(ATLAS, "PN rectifier diode"),
        process_conditions=["vacuum"],
    )
    assert "pressure" in diode["scope_decision"]["included"]
    assert "cleanliness" in diode["scope_decision"]["included"]


def test_led_adds_optics_while_rectifier_diode_does_not() -> None:
    rectifier = compile_component(find_archetype(ATLAS, "PN rectifier diode"))
    led = compile_component(find_archetype(ATLAS, "Visible LED die"))
    assert "optical" not in rectifier["scope_decision"]["included"]
    assert "optical" in led["scope_decision"]["included"]


def test_simulation_refinement_requires_matched_comparator_and_never_uplifts_physical_evidence() -> None:
    good = {
        "baseline_id": "base-1",
        "candidate_id": "cand-1",
        "solver": "standard-physics",
        "solver_version": "1.0",
        "same_material": True,
        "same_environment": True,
        "hard_gates_pass": True,
        "uncertainty_bounded": True,
        "candidate_overrides": {"trace_width_mm": 1.2},
        "physical_evidence_uplift": False,
    }
    result = validate_simulation_result(good)
    assert result["accepted"] is True
    compiled = compile_component(
        find_archetype(ATLAS, "Parallel-plate capacitor"),
        simulation=good,
    )
    assert compiled["parameter_overrides"]["trace_width_mm"] == 1.2
    assert compiled["execution_state"] == "HOLD"
    assert compiled["physical_execution"] is False

    bad = dict(good, same_environment=False, physical_evidence_uplift=True)
    rejected = validate_simulation_result(bad)
    assert rejected["accepted"] is False
    assert rejected["candidate_overrides"] == {}
    assert "required-true:same_environment" in rejected["reasons"]
    assert "simulation-cannot-uplift-physical-evidence" in rejected["reasons"]


def test_all_411_archetypes_compile_to_digital_hold_without_exact_instance() -> None:
    assert len(ATLAS["records"]) == 411
    hashes = set()
    for record in ATLAS["records"]:
        compiled = compile_component(record)
        assert compiled["schema"] == "CGX-MANUFACTURING-IR/0.1"
        assert compiled["execution_state"] == "HOLD"
        assert "exact-instance-not-bound" in compiled["blockers"]
        assert compiled["cgx_uri"].startswith("cgx://manufacturing/build/")
        assert compiled["recipe_uri"].startswith("cgx://manufacturing/recipe/")
        hashes.add(compiled["configuration_hash"])
    assert len(hashes) == 411


def test_component_hash_is_deterministic_and_changes_on_consequential_override() -> None:
    record = find_archetype(ATLAS, "Parallel-plate capacitor")
    a = compile_component(record, build_id="cap-a", parameter_overrides={"plate_area_mm2": 10})
    b = compile_component(record, build_id="cap-a", parameter_overrides={"plate_area_mm2": 10})
    c = compile_component(record, build_id="cap-a", parameter_overrides={"plate_area_mm2": 11})
    assert a["configuration_hash"] == b["configuration_hash"]
    assert a["configuration_hash"] != c["configuration_hash"]


def test_full_print_scheduler_references_child_recipes_without_copying_them() -> None:
    cap = compile_component(find_archetype(ATLAS, "Parallel-plate capacitor"), build_id="cap")
    led = compile_component(find_archetype(ATLAS, "Visible LED die"), build_id="led")
    conduit = compile_component(find_archetype(ATLAS, "Electrical conduit / raceway"), build_id="conduit")
    assembly = compile_assembly([cap, led, conduit], build_id="demo-assembly")
    assert assembly["recipe_bodies_duplicated"] is False
    assert len(assembly["child_build_refs"]) == 3
    assert len(assembly["child_recipe_refs"]) == 3
    assert set(assembly["schedule"]) == set(assembly["operation_refs"])
    assert assembly["optimization"]["scheduled_transition_count"] <= assembly["optimization"]["naive_transition_count"]
    assert assembly["execution_state"] == "HOLD"
    assert assembly["physical_execution"] is False


def test_full_print_scheduler_detects_cross_child_dependency_cycles() -> None:
    cap = compile_component(find_archetype(ATLAS, "Parallel-plate capacitor"), build_id="cap-cycle")
    led = compile_component(find_archetype(ATLAS, "Visible LED die"), build_id="led-cycle")
    cap_first = f"{cap['cgx_uri']}#{cap['operations'][0]['id']}"
    led_first = f"{led['cgx_uri']}#{led['operations'][0]['id']}"
    with pytest.raises(ValueError, match="dependency-cycle"):
        compile_assembly(
            [cap, led],
            build_id="cycle",
            relations=[
                {"before": cap_first, "after": led_first},
                {"before": led_first, "after": cap_first},
            ],
        )


def test_reference_machine_adapter_fails_closed_for_unready_or_mismatched_state() -> None:
    machine = {
        "machine_id": "pc01-synthetic",
        "calibration_hash": "cal-001",
        "supported_ops": ["TOOL_SELECT", "MOVE", "DEPOSIT_LINE", "DWELL"],
        "workspace_mm": {"x": [0, 200], "y": [0, 200], "z": [0, 200]},
        "max_feed_mm_min": 3000,
        "tool_temperature_c": [0, 300],
    }
    packet = {
        "schema": "CGX-TOOLPATH/0.1",
        "execution_state": "HOLD",
        "dry_run_validated": True,
        "machine_id": "pc01-synthetic",
        "calibration_hash": "cal-001",
        "operations": [],
    }
    with pytest.raises(AdapterError, match="build-not-ready"):
        emit_reference_gcode(packet, machine)


def test_reference_machine_adapter_emits_bounded_gcode_only_after_all_adapter_gates() -> None:
    machine = {
        "machine_id": "pc01-synthetic",
        "calibration_hash": "cal-001",
        "supported_ops": ["TOOL_SELECT", "MOVE", "DEPOSIT_LINE", "DWELL"],
        "workspace_mm": {"x": [0, 200], "y": [0, 200], "z": [0, 200]},
        "max_feed_mm_min": 3000,
        "tool_temperature_c": [0, 300],
    }
    packet = {
        "schema": "CGX-TOOLPATH/0.1",
        "execution_state": "BUILD_READY",
        "dry_run_validated": True,
        "machine_id": "pc01-synthetic",
        "calibration_hash": "cal-001",
        "operations": [
            {"opcode": "TOOL_SELECT", "params": {"tool": 0}},
            {"opcode": "MOVE", "params": {"x": 10, "y": 10, "z": 1, "feed_mm_min": 1000}},
            {"opcode": "DEPOSIT_LINE", "params": {"x": 20, "y": 10, "z": 1, "e": 0.5, "feed_mm_min": 600}},
            {"opcode": "DWELL", "params": {"milliseconds": 100}},
        ],
    }
    gcode = emit_reference_gcode(packet, machine)
    assert "G21" in gcode
    assert "T0" in gcode
    assert "G1 X20.0000 Y10.0000 Z1.0000 E0.50000 F600.000" in gcode
    assert "END CGX reference adapter output" in gcode

    out_of_bounds = json.loads(json.dumps(packet))
    out_of_bounds["operations"][1]["params"]["x"] = 201
    with pytest.raises(AdapterError, match="workspace-exceeded"):
        emit_reference_gcode(out_of_bounds, machine)
