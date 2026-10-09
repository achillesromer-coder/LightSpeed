from __future__ import annotations

import pytest

from cgx.manufacturing import (
    compile_stack_normal_form,
    find_archetype,
    load_default_atlas,
    load_stack_normal_form_contract,
)

ATLAS = load_default_atlas()


def specs():
    return [
        {"record": find_archetype(ATLAS, "Thin/thick-film resistor"), "build_id": "nf-r"},
        {"record": find_archetype(ATLAS, "Parallel-plate capacitor"), "build_id": "nf-c"},
        {"record": find_archetype(ATLAS, "Planar spiral inductor"), "build_id": "nf-l"},
    ]


def test_contract_and_sg0_normal_form_are_deterministic_and_nonexecuting():
    contract = load_stack_normal_form_contract()
    assert contract["artifact_id"] == "UTP-147"
    assert contract["build_id"] == "BUILD-080"

    kwargs = dict(
        component_specs=specs(),
        stack_id="p2-passive-rcl",
        seed_graph_class="SG-0",
        field_transport_regimes=["FTR-EQS", "FTR-MQS"],
        source_nodes=[{"id": "EXT-BENIGN", "kind": "external_test_source"}],
        reference_nodes=[{"id": "REF-0", "kind": "electrical_environment_reference"}],
        coupling_bindings=[
            {"regime_id": "FTR-EQS", "state": "SYMBOLIC"},
            {"regime_id": "FTR-MQS", "state": "SYMBOLIC"},
        ],
        witness_refs=["WIT-001", "WIT-002", "WIT-003"],
    )
    first = compile_stack_normal_form(**kwargs)
    second = compile_stack_normal_form(**kwargs)
    assert first["artifact_id"] == "UTP-147"
    assert first["normal_form_hash"] == second["normal_form_hash"]
    assert first["seed_graph"]["class"] == "SG-0"
    assert first["seed_graph"]["seed_count"] == 0
    assert first["physical_execution"] is False
    assert first["normal_form_state"] == "NORMALIZED_DIGITAL_HOLD"
    assert first["children_and_regions"]["coupled_4d_kernel"] == "VGK-036"
    assert {row["regime_id"] for row in first["field_transport"]["regimes"]} == {"FTR-EQS", "FTR-MQS"}
    assert any(item.startswith("coupling:FTR-EQS:SYMBOLIC") for item in first["blockers"])


def test_seed_graph_cardinality_is_fail_closed():
    with pytest.raises(ValueError, match="seed-count-mismatch:SG-1"):
        compile_stack_normal_form(specs(), stack_id="bad-sg1", seed_graph_class="SG-1")
    with pytest.raises(ValueError, match="seed-count-mismatch:SG-0"):
        compile_stack_normal_form(specs(), stack_id="bad-sg0", seed_graph_class="SG-0", seed_refs=["SEED-X"])
    with pytest.raises(ValueError, match="seed-count-mismatch:SG-N"):
        compile_stack_normal_form(specs(), stack_id="bad-sgn", seed_graph_class="SG-N", seed_refs=["SEED-X"])


def test_one_and_many_seed_graphs_preserve_explicit_seed_refs():
    one = compile_stack_normal_form(
        specs(),
        stack_id="sg1",
        seed_graph_class="SG-1",
        seed_refs=["SEED-EXACT-001"],
        field_transport_regimes=["FTR-EQS"],
        source_nodes=[{"id": "SEED-EXACT-001", "kind": "seed_source"}],
        reference_nodes=[{"id": "REF-0", "kind": "ground"}],
        witness_refs=["WIT-SEED-1"],
    )
    assert one["seed_graph"]["seed_refs"] == ["SEED-EXACT-001"]

    many = compile_stack_normal_form(
        specs(),
        stack_id="sgn",
        seed_graph_class="SG-N",
        seed_refs=["SEED-A", "SEED-B"],
        field_transport_regimes=["FTR-EM-NF", "FTR-THERM-RAD"],
        source_nodes=[
            {"id": "SEED-A", "kind": "seed_source"},
            {"id": "SEED-B", "kind": "seed_source"},
        ],
        reference_nodes=[{"id": "ENV", "kind": "environment"}],
        witness_refs=["WIT-SYSTEM"],
    )
    assert many["seed_graph"]["seed_count"] == 2
    assert set(many["seed_graph"]["seed_refs"]) == {"SEED-A", "SEED-B"}


def test_unknown_field_regime_and_coupling_state_are_rejected():
    with pytest.raises(ValueError, match="unknown-field-transport-regime"):
        compile_stack_normal_form(
            specs(),
            stack_id="bad-ftr",
            seed_graph_class="SG-0",
            field_transport_regimes=["FTR-MAGIC"],
        )
    with pytest.raises(ValueError, match="invalid-coupling-state"):
        compile_stack_normal_form(
            specs(),
            stack_id="bad-state",
            seed_graph_class="SG-0",
            field_transport_regimes=["FTR-EQS"],
            coupling_bindings=[{"regime_id": "FTR-EQS", "state": "ASSUMED_ZERO"}],
        )


def test_absent_sources_references_witnesses_and_regime_stay_explicit_blockers():
    output = compile_stack_normal_form(specs(), stack_id="open", seed_graph_class="SG-0")
    assert "field-transport-regime-unselected" in output["blockers"]
    assert "source-node-unbound" in output["blockers"]
    assert "reference-node-unbound" in output["blockers"]
    assert "witness-unbound" in output["blockers"]
    assert output["authority"]["physical_execution"] is False


def _valid_edge():
    return {
        "edge_id": "EDGE-R-C",
        "region_from": "REG-R",
        "region_to": "REG-C",
        "seed_relation": "SG-0",
        "interface_operator": "IOP-DIELECTRIC",
        "field_transport_regime": "FTR-EQS",
        "state_or_flux_transferred": "potential/displacement/current leakage",
        "transfer_or_jump_law": "source-bound electrostatic/contact relation",
        "reflection_blocking_or_return": "dielectric barrier and return/reference explicit",
        "parasitic_mutual_terms": "Maxwell capacitance matrix terms retained",
        "process_direction": "REG-R->REG-C",
        "predecessor_damage_gate": "PREDECESSOR-DAMAGE-CHECK-EXPLICIT",
        "preservation_action": "PRESERVE-OR-HOLD",
        "state_history": "REVISION-BOUND",
        "witness": "WIT-EDGE-R-C",
        "evidence_state": "SOURCE_BOUND",
        "authority": "DIGITAL_ONLY",
    }


def test_solved_or_measured_coupling_requires_provenance_and_validity():
    for state in ("SOLVED", "MEASURED"):
        with pytest.raises(ValueError, match="coupling-provenance-missing:FTR-EQS"):
            compile_stack_normal_form(
                specs(),
                stack_id=f"bad-{state.lower()}",
                seed_graph_class="SG-0",
                field_transport_regimes=["FTR-EQS"],
                source_nodes=[{"id": "SRC", "kind": "external_test_source"}],
                reference_nodes=[{"id": "REF", "kind": "ground"}],
                witness_refs=["WIT"],
                coupling_bindings=[{"regime_id": "FTR-EQS", "state": state}],
                interlayer_edges=[_valid_edge()],
            )


def test_typed_interlayer_edge_is_directional_and_fail_closed():
    edge = _valid_edge()
    out = compile_stack_normal_form(
        specs(),
        stack_id="edge-source-bound",
        seed_graph_class="SG-0",
        field_transport_regimes=["FTR-EQS"],
        source_nodes=[{"id": "SRC", "kind": "external_test_source"}],
        reference_nodes=[{"id": "REF", "kind": "ground"}],
        witness_refs=["WIT"],
        interlayer_edges=[edge],
    )
    assert out["interlayer_edges"]["edge_count"] == 1
    assert out["interlayer_edges"]["edges"][0]["process_direction"] == "REG-R->REG-C"
    assert "interlayer:EDGE-R-C:SOURCE_BOUND" in out["blockers"]

    reversed_bad = dict(edge)
    reversed_bad["process_direction"] = "REG-C->REG-R"
    with pytest.raises(ValueError, match="interlayer-direction-mismatch"):
        compile_stack_normal_form(
            specs(),
            stack_id="edge-bad-direction",
            seed_graph_class="SG-0",
            interlayer_edges=[reversed_bad],
        )

    missing = dict(edge)
    del missing["preservation_action"]
    with pytest.raises(ValueError, match="interlayer-edge-missing"):
        compile_stack_normal_form(
            specs(),
            stack_id="edge-missing-preservation",
            seed_graph_class="SG-0",
            interlayer_edges=[missing],
        )
