from __future__ import annotations

from cgx.manufacturing import (
    compile_interface_binding,
    compile_interface_graph,
    compile_printable_stack,
    find_archetype,
    find_interface_operator,
    load_default_atlas,
    load_interface_operator_library,
)

ATLAS = load_default_atlas()


def test_owner_interface_library_has_16_unique_factorized_operators() -> None:
    lib = load_interface_operator_library()
    assert lib["artifact_id"] == "UTP-141"
    assert lib["owner"]["record_count"] == 16
    assert len(lib["records"]) == 16
    ids = [row["Operator ID"] for row in lib["records"]]
    assert ids == [f"IFK-{i:03d}" for i in range(1, 17)]
    assert len(set(ids)) == 16
    assert all(row["Compiler Token"] for row in lib["records"])
    assert all("PHYSICAL_NOT_RUN" in row["Evidence State"] or "PHYSICAL_NOT_RUN" in row["Notes"] for row in lib["records"])


def test_dielectric_interface_preserves_capacitance_geometry_and_maxwell_fallback() -> None:
    op = find_interface_operator("IFK-002")
    law = op["Boundary / Jump Law"]
    fallback = op["Fallback / Higher-Fidelity Route"]
    notes = op["Notes"]
    assert "Maxwell" in law
    assert "Q_i=ΣC_ijV_j" in op["Numeric Inference Gate"] or "Maxwell" in law
    assert "electrostatic" in fallback.lower()
    assert "1.2041695 pF/mm²" in notes
    assert "0.6020848 pF/mm²" in notes
    assert "breakdown" in notes.lower()


def test_interface_compiler_is_symbolic_without_exact_evidence_and_direction_is_explicit() -> None:
    edge = compile_interface_binding(
        "IFK-001",
        region_a="REG-REF-A",
        region_b="REG-SEED-B",
        direction="A_TO_B",
    )
    assert edge["state"] == "SYMBOLIC/HOLD"
    assert edge["direction"] == "A_TO_B"
    assert edge["physical_execution"] is False
    assert "source-or-measurement-refs-open" in edge["blockers"]

    reverse = compile_interface_binding(
        "IFK-001",
        region_a="REG-SEED-B",
        region_b="REG-REF-A",
        direction="B_TO_A",
    )
    assert reverse["direction"] == "B_TO_A"
    assert reverse["interface_hash"] != edge["interface_hash"]


def test_interface_can_reach_numeric_if_only_with_attributable_bindings_and_valid_regime() -> None:
    edge = compile_interface_binding(
        "IFK-003",
        region_a="REG-THERM-A",
        region_b="REG-SEED-B",
        bindings={
            "source_or_measurement_refs": ["sha256:synthetic-source"],
            "geometry_ref": "cgx://geometry/synthetic-interface-v1",
            "process_state_ref": "cgx://process/synthetic-bond-state-v1",
            "regime_validated": True,
        },
    )
    assert edge["state"] == "NUMERIC_IF_BOUND"
    assert edge["blockers"] == []
    assert edge["physical_execution"] is False


def test_safe_state_and_isolation_interfaces_remain_authority_holds() -> None:
    bindings = {
        "source_or_measurement_refs": ["sha256:synthetic-source"],
        "geometry_ref": "cgx://geometry/synthetic",
        "process_state_ref": "cgx://process/synthetic",
        "regime_validated": True,
    }
    assert compile_interface_binding(
        "IFK-016", region_a="REG-SAFE", region_b="REG-SEED", bindings=bindings
    )["state"] == "AUTHORITY_HOLD"
    assert compile_interface_binding(
        "IFK-012", region_a="POWER-A", region_b="LOGIC-B", bindings=bindings
    )["state"] == "AUTHORITY_HOLD"


def test_printable_stack_consumes_explicit_interface_graph_without_recipe_duplication() -> None:
    specs = [
        {"record": find_archetype(ATLAS, "Thin/thick-film resistor"), "build_id": "ifk-r"},
        {"record": find_archetype(ATLAS, "Parallel-plate capacitor"), "build_id": "ifk-c"},
    ]
    stack = compile_printable_stack(
        specs,
        stack_id="ifk-stack",
        interfaces=[
            {
                "operator_id": "IFK-002",
                "region_a": "ifk-c:REG-C",
                "region_b": "ifk-r:REG-REF",
                "direction": "A_TO_B",
            }
        ],
    )
    assert stack["interface_operator_artifact"] == "UTP-141"
    assert stack["interface_graph"]["edge_count"] == 1
    assert stack["interface_graph"]["state"] == "HOLD"
    assert stack["interface_graph"]["edges"][0]["operator_id"] == "IFK-002"
    assert stack["recipe_bodies_duplicated"] is False
    assert stack["stack_state"] == "HOLD"
    assert stack["physical_execution"] is False


def test_empty_explicit_interface_set_preserves_existing_stack_semantics() -> None:
    graph = compile_interface_graph([])
    assert graph["state"] == "NO_EXPLICIT_INTERFACES"
    assert graph["edge_count"] == 0
    assert graph["physical_execution"] is False
