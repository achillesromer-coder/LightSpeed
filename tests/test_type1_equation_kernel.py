import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "cgx" / "component_atlas" / "type1_equation_kernel_v0_1.json"

def load():
    return json.loads(KERNEL.read_text(encoding="utf-8"))

def test_kernel_cardinality_and_unique_primitive_coverage():
    d = load()
    assert d["artifact_id"] == "UTP-131"
    assert d["state"] == "DIGITAL ENGINEERING KERNEL / PHYSICAL_NOT_RUN"
    kernels = d["kernels"]
    assert len(kernels) == 20
    assert len({k["kernel_id"] for k in kernels}) == 20
    assert len({k["primitive"] for k in kernels}) == 20
    assert all(k["law"] and k["inputs"] and k["outputs"] and k["gate"] and k["falsifier"] for k in kernels)

def test_capacitance_fixtures_follow_parallel_plate_relation():
    d = load()
    eps0 = 8.8541878128e-12
    for fixture in d["fixtures"].values():
        expected = eps0 * fixture["epsilon_r"] / (fixture["thickness_um"] * 1e-6) * 1e6
        assert math.isclose(expected, fixture["ideal_capacitance_density_pF_mm2"], rel_tol=1e-12)
    assert math.isclose(d["fixtures"]["kapton_HN_25um"]["ideal_capacitance_density_pF_mm2"], 2 * d["fixtures"]["kapton_HN_50um"]["ideal_capacitance_density_pF_mm2"], rel_tol=1e-12)

def test_kernel_fails_closed_on_missing_or_invalid_inputs():
    d = load()
    assert set(d["inference_classes"]) == {"NUMERIC_IF", "SYMBOLIC", "HOLD"}
    joined = " ".join(d["boundaries"]).lower()
    assert "no inferred voltage" in joined
    assert "no geometry-only semiconductor" in joined
    assert "no compiler output grants physical execution" in joined
