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


def test_owner_volumetric_kernel_has_40_unique_records_and_tokens() -> None:
    data = load_volumetric_kernel()
    assert data["artifact_id"] == "UTP-137"
    assert data["record_count"] == 40
    assert len(data["records"]) == 40
    assert len({row["kernel_id"] for row in data["records"]}) == 40
    assert len({row["compiler_token"] for row in data["records"]}) == 40
    assert data["records"][0]["kernel_id"] == "VGK-001"
    assert data["records"][-1]["kernel_id"] == "VGK-040"


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

def test_capacitance_policy_and_coupled_4d_summary_are_preserved() -> None:
    data = load_volumetric_kernel()
    policy = data["capacitance_policy"]
    assert policy["kapton_HN_25um_ideal_pF_per_mm2"] == 2 * policy["kapton_HN_50um_ideal_pF_per_mm2"]
    assert "Maxwell capacitance matrix" in policy["general_3d"]
    assert "no voltage rating" in policy["exclusions"]
    assembly = data["coupled_4d_assembly"]
    assert "E(z,p,t)" in assembly["interface"]
    assert "unsupported cross-domain terms remain HOLD" in assembly["meaning"]
    assert "411x60" in data["logical_universal_matrix"]

def test_build072_new_field_kernels_preserve_regime_and_evidence_boundaries() -> None:
    full_wave = find_volumetric_kernel("VGK-037")
    acoustic = find_volumetric_kernel("VGK-038")
    fluid = find_volumetric_kernel("VGK-039")
    dielectric = find_volumetric_kernel("VGK-040")
    assert full_wave["compiler_token"] == "VOL_RF_FULL_WAVE"
    assert "full-wave" in full_wave["numeric_inference_gate"].lower()
    assert acoustic["compiler_token"] == "VOL_ACOUSTIC_PIEZO"
    assert "piezoelectric" in acoustic["governing_law_matrix_form"].lower()
    assert fluid["compiler_token"] == "VOL_FLUID_GENERAL_3D"
    assert "navier" in fluid["governing_law_matrix_form"].lower()
    assert dielectric["compiler_token"] == "VOL_DIELECTRIC_ISOLATION"
    assert "breakdown" in dielectric["numeric_inference_gate"].lower()
    assert all(
        "physical" not in row["compiler_token"].lower()
        for row in (full_wave, acoustic, fluid, dielectric)
    )


def test_clear_family_topologies_no_longer_fall_back_to_generic_coupled_assembly() -> None:
    expected = {
        "Dipole antenna": ["VGK-037"],
        "Quartz crystal resonator": ["VGK-038"],
        "Tesla valve": ["VGK-039"],
        "Printed dielectric / insulation layer": ["VGK-040"],
        "Stripline": ["VGK-011"],
        "Capacitive pressure sensor": ["VGK-026", "VGK-017"],
        "Faraday/shield enclosure": ["VGK-037", "VGK-018"],
    }
    for query, kernels in expected.items():
        resolved = resolve_volumetric_topology(find_archetype(ATLAS, query))
        assert resolved["candidate_kernel_ids"] == kernels, query
        assert resolved["candidate_kernel_ids"] != ["VGK-036"], query


def test_generic_coupled_fallback_is_reduced_but_preserved_for_true_compound_archetypes() -> None:
    fallback = []
    for record in ATLAS["records"]:
        resolved = resolve_volumetric_topology(record)
        if resolved["candidate_kernel_ids"] == ["VGK-036"]:
            fallback.append(record["ID"])
    assert len(ATLAS["records"]) == 411
    assert len(fallback) == 9
    assert set(fallback) == {
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
    assert resolve_volumetric_topology(find_archetype(ATLAS, "LC resonator"))["candidate_kernel_ids"] == ["VGK-036"]
    assert resolve_volumetric_topology(find_archetype(ATLAS, "Rigid PCB stack"))["candidate_kernel_ids"] == ["VGK-036"]


def test_topology_coverage_audit_matches_live_resolver() -> None:
    audit = json.loads(
        (ROOT / "cgx" / "component_atlas" / "type1_topology_coverage_audit_v0_1.json").read_text(encoding="utf-8")
    )
    assert audit["artifact_id"] == "UTP-140"
    assert audit["final"]["volumetric_kernel_count"] == 40
    assert audit["final"]["vgk036_only_count"] == 9
    assert audit["final"]["specific_or_multi_kernel_count"] == 402
    assert len(audit["final"]["residual_generic_only"]) == 9
