from __future__ import annotations

import json
from pathlib import Path

from cgx.manufacturing import (
    compile_component,
    find_archetype,
    find_instance,
    find_volumetric_kernel,
    load_default_atlas,
    load_default_instance_population,
    load_volumetric_kernel,
    resolve_volumetric_topology,
)

ROOT = Path(__file__).resolve().parents[1]
ATLAS = load_default_atlas()
POP = load_default_instance_population()


def test_owner_volumetric_kernel_has_36_unique_records_and_tokens() -> None:
    data = load_volumetric_kernel()
    assert data["artifact_id"] == "UTP-137"
    assert data["record_count"] == 36
    assert len(data["records"]) == 36
    assert len({row["kernel_id"] for row in data["records"]}) == 36
    assert len({row["compiler_token"] for row in data["records"]}) == 36
    assert data["records"][0]["kernel_id"] == "VGK-001"
    assert data["records"][-1]["kernel_id"] == "VGK-036"


def test_general_3d_forms_use_matrices_or_coupled_state_instead_of_forcing_flat_closed_forms() -> None:
    cap = find_volumetric_kernel("VGK-007")
    ind = find_volumetric_kernel("VGK-010")
    coupled = find_volumetric_kernel("VGK-036")
    assert "Maxwell capacitance matrix" in cap["governing_law_matrix_form"]
    assert "L_ij" in ind["governing_law_matrix_form"]
    assert "E(z,p,t)" in coupled["governing_law_matrix_form"]
    assert "not a claim of one universal equation or solver" in coupled["evidence_current_example"].lower()


def test_current_p2_p3_instances_resolve_without_evidence_uplift() -> None:
    expected = {
        "CGXI-P2-R-001": (["VGK-035"], "RESOLVED_SYMBOLIC"),
        "CGXI-P2-C-001": (["VGK-003"], "RESOLVED_SYMBOLIC"),
        "CGXI-P2-L-001": (["VGK-008", "VGK-010"], "HOLD_TOPOLOGY_CHOICE"),
        "CGXI-P3-LC-001": (["VGK-012", "VGK-036"], "HOLD_UPSTREAM_EVIDENCE"),
        "CGXI-P3-LOOP-001": (["VGK-012"], "RESOLVED_SYMBOLIC"),
    }
    for iid, (kernels, state) in expected.items():
        instance = find_instance(POP, iid)
        record = find_archetype(ATLAS, instance["archetype_id"])
        resolved = resolve_volumetric_topology(record, instance=instance)
        assert resolved["candidate_kernel_ids"] == kernels
        assert resolved["resolution_state"] == state
        assert resolved["physical_execution"] is False
        assert instance["binding_state"] == "UNBOUND"
        assert instance["physical_state"] == "NOT_RUN"


def test_p2_capacitor_compile_exposes_parallel_plate_topology_but_stays_hold() -> None:
    instance = find_instance(POP, "CGXI-P2-C-001")
    record = find_archetype(ATLAS, instance["archetype_id"])
    compiled = compile_component(record, instance=instance, build_id="p2-cap-volumetric")
    topo = compiled["volumetric_topology"]
    assert topo["candidate_kernel_ids"] == ["VGK-003"]
    assert topo["compiler_tokens"] == ["VOL_CAP_PARALLEL_PLATE"]
    assert topo["numeric_state"] == "SYMBOLIC"
    assert compiled["execution_state"] == "HOLD"
    assert compiled["physical_execution"] is False


def test_p3_loop_uses_reviewed_13_56mhz_loop_topology_but_remains_unbound() -> None:
    instance = find_instance(POP, "CGXI-P3-LOOP-001")
    record = find_archetype(ATLAS, instance["archetype_id"])
    compiled = compile_component(record, instance=instance, build_id="p3-loop-volumetric")
    topo = compiled["volumetric_topology"]
    assert topo["candidate_kernel_ids"] == ["VGK-012"]
    assert topo["compiler_tokens"] == ["VOL_RF_LOOP"]
    assert "13.56 MHz" in instance["electrical_mechanical_thermal_or_process_ratings"]
    assert topo["numeric_state"] == "SYMBOLIC"
    assert "lots" in topo["blockers"]
    assert compiled["execution_state"] == "HOLD"


def test_generic_archetype_projection_does_not_claim_exact_instance_binding() -> None:
    cap = resolve_volumetric_topology(find_archetype(ATLAS, "Parallel-plate capacitor"))
    assert cap["candidate_kernel_ids"] == ["VGK-003"]
    assert cap["resolution_state"] == "ARCHETYPE_TOPOLOGY_CANDIDATE"
    assert cap["blockers"] == ["exact-instance-not-bound"]
    assert cap["physical_execution"] is False
