import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "cgx" / "component_atlas" / "type1_functional_voxel_field_basis_v0_1.json"

def load():
    return json.loads(PATH.read_text(encoding="utf-8"))

def test_functional_voxel_basis_covers_all_primitive_kernels():
    d = load()
    assert d["artifact_id"] == "UTP-143"
    assert d["build_id"] == "BUILD-076"
    assert d["physical_execution"] is False
    refs = {k for r in d["region_classes"] for k in r["kernels"]}
    assert refs == {f"T1K-{i:03d}" for i in range(1, 21)}
    assert len(d["region_classes"]) == 17
    assert "directed 3D region/interface graph" in d["non_planar_rule"]

def test_capacitance_selector_has_closed_forms_and_field_fallback():
    d = load()
    modes = {m["id"]: m for m in d["capacitance_selector"]["modes"]}
    for required in {
        "CAP-PP","CAP-MULTILAYER-NORMAL","CAP-PARALLEL-CELLS",
        "CAP-COAX","CAP-SPHERE","CAP-MAXWELL-3D",
        "CAP-RLGC-DISTRIBUTED","CAP-FIELD-SOLVE-OR-MEASURE"
    }:
        assert required in modes
    assert "no universal closed form" in modes["CAP-FIELD-SOLVE-OR-MEASURE"]["law"]

def test_kapton_fixture_capacitance_density():
    d = load()
    eps0 = d["capacitance_selector"]["epsilon0_F_per_m"]
    for f in d["capacitance_selector"]["source_verified_fixtures"]:
        calc = eps0 * f["epsilon_r"] / (f["thickness_um"] * 1e-6) * 1e6
        assert math.isclose(calc, f["inferred_pF_per_mm2"], rel_tol=1e-12, abs_tol=0.0)
        assert "NOT_MEASURED" in f["evidence"]

def test_voxel_contract_preserves_evidence_and_damage_gates():
    d = load()
    required = set(d["voxel_contract"]["required_fields"])
    for key in {"process_history_ref","damage_envelope","preservation_state","witness_refs","dbr_ref"}:
        assert key in required
    assert d["voxel_contract"]["numeric_states"] == ["NUMERIC_IF","SYMBOLIC","HOLD"]
    assert any("does not grant" in x for x in d["safety_invariants"])
