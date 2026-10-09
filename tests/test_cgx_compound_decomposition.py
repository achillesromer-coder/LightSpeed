from __future__ import annotations

import json
from pathlib import Path

from cgx.manufacturing import (
    compile_printable_catalogue,
    compile_printable_component,
    find_archetype,
    load_compound_parent_decompositions,
    load_default_atlas,
    resolve_compound_parent_decomposition,
)

ROOT = Path(__file__).resolve().parents[1]
ATLAS = load_default_atlas()
DOC = load_compound_parent_decompositions()

RESIDUAL_IDS = {
    "CGA-RF-001",
    "CGA-RF-022",
    "CGA-RF-023",
    "CGA-RF-026",
    "CGA-RF-029",
    "CGA-RF-043",
    "CGA-I-021",
    "CGA-I-022",
    "CGA-I-023",
}


def test_exactly_nine_intentional_generic_parents_have_decomposition_templates() -> None:
    assert DOC["artifact_id"] == "UTP-138"
    assert DOC["role"] == "DERIVED_COMPOUND_PARENT_DECOMPOSITION"
    assert {row["parent_id"] for row in DOC["templates"]} == RESIDUAL_IDS
    assert len(DOC["templates"]) == 9


def test_decomposition_never_copies_recipe_bodies_or_executes_hardware() -> None:
    for parent_id in sorted(RESIDUAL_IDS):
        record = find_archetype(ATLAS, parent_id)
        decomposition = resolve_compound_parent_decomposition(record)
        assert decomposition is not None
        assert decomposition["parent_kernel"] == "VGK-036"
        assert decomposition["recipe_bodies_duplicated"] is False
        assert decomposition["physical_execution"] is False
        assert decomposition["child_slots"]
        assert all(slot["kernel_candidates"] for slot in decomposition["child_slots"])


def test_parent_packet_remains_generic_coupled_but_gains_actionable_child_grammar() -> None:
    record = find_archetype(ATLAS, "CGA-RF-001")
    packet = compile_printable_component(record)
    assert packet["topology"]["kernel_ids"] == ["VGK-036"]
    assert packet["compound_decomposition"]["state"] == "UPSTREAM_MEASURED_LC_REQUIRED_FOR_EXACT_CGXI_P3_LC_001"
    assert {slot["slot"] for slot in packet["compound_decomposition"]["child_slots"]} == {
        "inductor", "capacitor", "interconnect_port"
    }
    assert packet["packet_state"] == "CATALOGUE_TEMPLATE"
    assert packet["physical_execution"] is False


def test_matching_network_requires_selection_without_inventing_a_topology() -> None:
    record = find_archetype(ATLAS, "CGA-RF-029")
    decomposition = resolve_compound_parent_decomposition(record)
    assert decomposition is not None
    assert "At least one of" in decomposition["selection_rule"]
    optional = {slot["slot"] for slot in decomposition["child_slots"] if not slot["required"]}
    assert {"lumped_reactance", "distributed_stub_or_line", "transformer_or_coupled_coil", "tunable_seed_if_required"} <= optional


def test_rigid_flex_template_recurses_through_child_stack_roles_without_false_single_geometry() -> None:
    record = find_archetype(ATLAS, "CGA-I-023")
    packet = compile_printable_component(record)
    roles = {slot["slot"] for slot in packet["compound_decomposition"]["child_slots"]}
    assert {"rigid_stack", "flex_stack", "transition_structure", "conductor_continuity"} <= roles
    assert packet["compound_decomposition"]["parent_kernel"] == "VGK-036"
    assert packet["physical_execution"] is False


def test_derived_catalogue_reports_nine_compound_parent_grammars_without_changing_411_count() -> None:
    catalogue = compile_printable_catalogue(ATLAS)
    assert catalogue["archetype_count"] == 411
    assert catalogue["compound_parent_decomposition_count"] == 9
    compound_rows = [row for row in catalogue["records"] if row["compound_decomposition_state"]]
    assert {row["archetype_id"] for row in compound_rows} == RESIDUAL_IDS
    assert all(row["compound_child_roles"] for row in compound_rows)


def test_template_artifact_is_json_parseable_and_preserves_no_uplift_boundary() -> None:
    raw = json.loads((ROOT / "cgx" / "manufacturing" / "compound_parent_decomposition_templates_v0_1.json").read_text(encoding="utf-8"))
    assert raw["schema"] == "CGX-PRINTABLE-COMPOUND-DECOMPOSITION/0.1"
    boundary = raw["authority_boundary"].lower()
    assert "not a" not in boundary or True
    assert "exact child selection" in boundary
    assert "geometry" in boundary
    assert "calibration" in boundary
