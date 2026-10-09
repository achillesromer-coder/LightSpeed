import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "cgx" / "component_atlas" / "universal_type1_stack_compiler_v0_1.json"

def load():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))

def test_owner_and_matrix_cardinality():
    d = load()
    assert d["artifact_id"] == "UTP-124"
    assert d["owner"]["owner_row"] == "26_CGX_Portfolio_Delivery_v0_1!A75:P75"
    assert d["matrix_contract"] == {
        "archetype_count": 411,
        "field_count": 60,
        "directional_fields": 16,
        "quantitative_factorization_fields": 8,
        "primitive_basis_classes": 20,
    }
    assert len(d["primitive_basis"]) == 20
    assert "MAP_PRIMITIVE_BASIS_AND_EQUIVALENT_NETWORK" in d["compile_chain"]\n    assert "RESOLVE_PRIMITIVE_EQUATION_KERNEL" in d["compile_chain"]
    assert "RESOLVE_VOLUMETRIC_TOPOLOGY" in d["compile_chain"]
    assert "RESOLVE_BOUNDARY_INTERFACE_GRAPH" in d["compile_chain"]\n    assert d["inputs"]["equation_kernel"].endswith("type1_equation_kernel_v0_1.json")
    assert d["inputs"]["volumetric_kernel"].endswith("type1_volumetric_kernel_v0_1.json")
    assert "CHECK_VOXEL_PACKING_AND_PROCESS_RESOLUTION" in d["compile_chain"]
    assert "ORDER_DIRECTIONAL_X_TO_Y_STACK" in d["compile_chain"]
    assert "INFER_NUMERIC_OR_RETAIN_SYMBOLIC_OR_HOLD" in d["compile_chain"]

def test_capacitance_fixture_is_derived_not_measured():
    d = load()
    fixture = d["inference_fixtures"][0]
    eps0 = 8.8541878128e-12
    eps_r = fixture["source_inputs"]["epsilon_r_nominal"]
    thickness_m = fixture["source_inputs"]["dielectric_thickness_um_nominal"] * 1e-6
    f_per_m2 = eps0 * eps_r / thickness_m
    pF_per_mm2 = f_per_m2 * 1e6
    assert math.isclose(
        pF_per_mm2,
        fixture["derived"]["capacitance_density_pF_per_mm2"],
        rel_tol=1e-12,
    )
    assert fixture["source_inputs"]["dielectric_thickness_um_nominal"] == 50
    assert math.isclose(
        fixture["derived"]["capacitance_density_pF_per_cm2"],
        pF_per_mm2 * 100,
        rel_tol=1e-12,
    )
    assert "ENGINEERING_INFERENCE" in fixture["class"]
    assert "PHYSICAL_NOT_RUN" in fixture["class"]
    assert "no voltage rating" in fixture["exclusions"]

def test_compiler_fails_closed_on_unknowns_and_authority():
    d = load()
    assert "Required when the equation is known but one or more required inputs are unresolved." in d["inference_policy"]["symbolic"]
    assert "HOLD" in d["inference_policy"]["hold"].upper()
    joined = " ".join(d["non_claims"]).lower()
    assert "not physical readiness" in joined
    assert "not certification" in joined
    assert "not permission to infer absent properties" in joined