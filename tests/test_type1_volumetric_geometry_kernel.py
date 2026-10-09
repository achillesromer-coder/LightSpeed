import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "cgx" / "component_atlas" / "type1_volumetric_geometry_kernel_v0_1.json"

def load():
    return json.loads(KERNEL.read_text(encoding="utf-8"))

def by_id(d, kid):
    return next(k for k in d["kernels"] if k["Kernel ID"] == kid)

def test_kernel_cardinality_and_unique_ids():
    d = load()
    assert d["artifact_id"] == "UTP-137"
    assert d["state"] == "DIGITAL ENGINEERING KERNEL / PHYSICAL_NOT_RUN"
    assert d["record_count"] == 36
    assert len(d["kernels"]) == 36
    assert len({k["Kernel ID"] for k in d["kernels"]}) == 36

def test_capacitance_topologies_do_not_collapse_to_parallel_plate():
    d = load()
    pp = by_id(d, "VGK-003")
    coax = by_id(d, "VGK-005")
    sphere = by_id(d, "VGK-006")
    maxwell = by_id(d, "VGK-007")
    assert "ε0εrA/d" in pp["Governing Law / Matrix Form"]
    assert "ln(b/a)" in coax["Governing Law / Matrix Form"]
    assert "4π" in sphere["Governing Law / Matrix Form"]
    assert "C_ij" in maxwell["Governing Law / Matrix Form"]
    assert "Maxwell capacitance matrix" in d["capacitance_policy"]["general_3d"]

def test_kapton_inference_is_relation_not_qualification():
    d = load()
    eps0 = 8.8541878128e-12
    er = 3.4
    c50 = eps0 * er / (50e-6) * 1e6
    c25 = eps0 * er / (25e-6) * 1e6
    assert math.isclose(c50, d["capacitance_policy"]["kapton_HN_50um_ideal_pF_per_mm2"], rel_tol=1e-12)
    assert math.isclose(c25, d["capacitance_policy"]["kapton_HN_25um_ideal_pF_per_mm2"], rel_tol=1e-12)
    assert math.isclose(c25, 2 * c50, rel_tol=1e-12)
    assert "no voltage rating" in d["capacitance_policy"]["exclusions"]

def test_coupled_4d_is_assembly_interface_not_universal_solver():
    d = load()
    assembly = by_id(d, "VGK-036")
    assert "E(z,p,t)" in assembly["Governing Law / Matrix Form"]
    assert "not a claim of one universal equation or solver" in assembly["Evidence / Current Example"]
    joined = " ".join(d["boundaries"]).lower()
    assert "no single universal equation or solver claim" in joined
    assert "unsupported cross-domain terms remain hold" in d["coupled_4d_assembly"]["meaning"].lower()
