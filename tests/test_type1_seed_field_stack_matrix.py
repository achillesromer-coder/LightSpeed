import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "cgx" / "component_atlas" / "type1_seed_field_stack_matrix_v0_1.json"
VOX = ROOT / "cgx" / "component_atlas" / "type1_functional_voxel_field_basis_v0_1.json"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def test_seed_classes_and_boundaries():
    d = load(PATH)
    assert d["artifact_id"] == "UTP-144"
    assert d["build_id"] == "BUILD-077"
    assert d["physical_execution"] is False
    classes = {x["id"]: x for x in d["seed_graph_contract"]["classes"]}
    assert set(classes) == {"SG-0", "SG-1", "SG-N"}
    assert "remain HOLD" in classes["SG-0"]["rule"]
    assert "mutual" in classes["SG-N"]["rule"]

def test_field_basis_covers_distinct_radiative_and_transport_domains():
    d = load(PATH)
    ids = {x["id"] for x in d["field_coupling_basis"]}
    assert {"FC-EQS","FC-MQS","FC-RF","FC-OPT","FC-THERM","FC-MECH","FC-FLUID","FC-CHEM","FC-ION","FC-INERTIAL"} <= ids
    rf = next(x for x in d["field_coupling_basis"] if x["id"] == "FC-RF")
    thermal = next(x for x in d["field_coupling_basis"] if x["id"] == "FC-THERM")
    assert "full-wave Maxwell" in rf["models"]
    assert "q_rad=" in " ".join(thermal["models"])

def test_3d_parasitics_not_flat_schematic_only():
    d = load(PATH)
    p = d["parasitic_and_coupling_extraction"]
    assert "3D as-built geometry" in p["principle"]
    assert "Maxwell C matrix" in p["electrical"]["capacitance"]
    assert "mutual L" in p["electrical"]["inductance"]
    assert "off-diagonal mutual terms" in p["multi_seed"]

def test_functional_voxel_factorization_includes_seed_and_field_layers():
    v = load(VOX)
    assert "SeedGraph" in v["factorization"]
    assert "FieldCoupling" in v["factorization"]
    assert v["seed_field_companion"]["artifact_id"] == "UTP-144"


def test_stack_compiler_consumes_seed_field_matrix_and_25um_cap_fixture():
    c = load(ROOT / "cgx" / "component_atlas" / "universal_type1_stack_compiler_v0_1.json")
    assert c["inputs"]["seed_field_stack_matrix"].endswith("type1_seed_field_stack_matrix_v0_1.json")
    assert c["matrix_contract"]["seed_graph_classes"] == 3
    assert c["matrix_contract"]["field_coupling_classes"] == 10
    assert "EXTRACT_PARASITIC_AND_MUTUAL_COUPLINGS" in c["compile_chain"]
    f = next(x for x in c["inference_fixtures"] if x["id"] == "INF-CAP-KAPTON-HN-25UM-001")
    assert abs(f["derived"]["ideal_capacitance_pF"] - 120.41695425408) < 1e-9
    sg0 = next(x for x in c["candidate_witness_stacks"] if x["id"] == "P2-SG0-RCL-CELL-001")
    assert sg0["observed_lots"] == "UNRESOLVED"
    assert sg0["physical_execution"] is False
