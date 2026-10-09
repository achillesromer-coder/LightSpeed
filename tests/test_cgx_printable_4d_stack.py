from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from cgx.manufacturing import (
    compile_printable_catalogue,
    compile_printable_component,
    compile_printable_stack,
    find_archetype,
    find_instance,
    load_default_atlas,
    load_default_instance_population,
)

ROOT = Path(__file__).resolve().parents[1]
ATLAS = load_default_atlas()
POP = load_default_instance_population()


def test_all_411_archetypes_compile_to_one_derived_printable_catalogue_without_execution() -> None:
    catalogue = compile_printable_catalogue(ATLAS)
    assert catalogue["artifact_id"] == "UTP-138"
    assert catalogue["archetype_count"] == 411
    assert len(catalogue["records"]) == 411
    assert len({row["archetype_id"] for row in catalogue["records"]}) == 411
    assert {row["packet_state"] for row in catalogue["records"]} == {"CATALOGUE_TEMPLATE"}
    assert {row["physical_execution"] for row in catalogue["records"]} == {False}


def test_rectifier_diode_print_packet_omits_irrelevant_pressure_gravity_and_spatial_scope() -> None:
    diode = compile_printable_component(find_archetype(ATLAS, "PN rectifier diode"))
    scopes = set(diode["four_d_state"]["consequential_optional_scopes"])
    assert {"electrical", "thermal", "esd", "cleanliness"} <= scopes
    assert "pressure" not in scopes
    assert "gravity" not in scopes
    assert "fluid" not in scopes
    assert "spatial_coupling" not in scopes
    assert diode["print_path"] == "PRINT_PLUS_SEED_INSERT_PATH"
    assert diode["physical_execution"] is False


def test_exact_p2_capacitor_packet_reuses_parallel_plate_kernel_and_stays_hold() -> None:
    instance = find_instance(POP, "CGXI-P2-C-001")
    record = find_archetype(ATLAS, instance["archetype_id"])
    packet = compile_printable_component(record, instance=instance, build_id="p2-cap-printable")
    assert packet["topology"]["kernel_ids"] == ["VGK-003"]
    assert packet["topology"]["compiler_tokens"] == ["VOL_CAP_PARALLEL_PLATE"]
    assert packet["packet_state"] == "PRINTABLE_PACKET_DRAFT_HOLD"
    assert packet["machine_program"]["state"].startswith("EMITTABLE_ONLY_AFTER_BUILD_READY")
    assert any(slot["slot"] == "material_lots" for slot in packet["binding_slots"])
    assert packet["evidence"]["physical_state"] == "NOT_RUN"


def test_geometry_parameters_become_slots_not_invented_values() -> None:
    resistor = compile_printable_component(find_archetype(ATLAS, "Thin/thick-film resistor"))
    names = [slot["name"] for slot in resistor["geometry"]["parameter_slots"]]
    assert {"L", "w", "t"} <= set(names)
    assert all(slot["state"] == "OPEN_EXACT_VALUE" for slot in resistor["geometry"]["parameter_slots"])


def test_whole_stack_reuses_child_recipes_and_coupled_4d_kernel() -> None:
    specs = [
        {"record": find_archetype(ATLAS, "Thin/thick-film resistor"), "build_id": "stack-r"},
        {"record": find_archetype(ATLAS, "Parallel-plate capacitor"), "build_id": "stack-c"},
        {"record": find_archetype(ATLAS, "Visible LED die"), "build_id": "stack-led"},
    ]
    stack = compile_printable_stack(specs, stack_id="demo-rc-led")
    assert stack["recipe_bodies_duplicated"] is False
    assert stack["coupled_4d_kernel"] == "VGK-036"
    assert len(stack["component_packet_refs"]) == 3
    assert len(set(stack["child_recipe_refs"])) >= 2
    assert stack["stack_state"] == "HOLD"
    assert stack["physical_execution"] is False
    assert stack["optimization"]["scheduled_transition_count"] <= stack["optimization"]["naive_transition_count"]


def test_cli_can_emit_printable_component_and_full_catalogue() -> None:
    comp = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "compile_cgx_manufacturing.py"),
            "printable-component",
            "--instance-id",
            "CGXI-P2-R-001",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    component = json.loads(comp.stdout)
    assert component["schema"] == "CGX-PRINTABLE-4D-COMPONENT/0.1"
    assert component["instance_id"] == "CGXI-P2-R-001"
    assert component["physical_execution"] is False

    cat = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "compile_cgx_manufacturing.py"),
            "printable-catalogue",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    catalogue = json.loads(cat.stdout)
    assert catalogue["archetype_count"] == 411
    assert len(catalogue["records"]) == 411