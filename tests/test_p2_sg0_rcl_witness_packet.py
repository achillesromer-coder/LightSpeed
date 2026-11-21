import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "cgx" / "manufacturing" / "p2_sg0_rcl_witness_packet_v0_1.json"

def load():
    return json.loads(PATH.read_text(encoding="utf-8"))

def test_packet_is_passive_and_not_run():
    d=load()
    assert d["artifact_id"]=="UTP-145"
    assert d["build_id"]=="BUILD-078"
    assert d["physical_authority"]["physical_execution"] is False
    assert d["status"].endswith("PHYSICAL_NOT_RUN")
    assert set(d["owner_refs"]["component_instances"])=={"CGXI-P2-R-001","CGXI-P2-C-001","CGXI-P2-L-001"}

def test_gate_order_requires_lot_machine_geometry_process_before_measurement():
    d=load()
    ids=[g["gate"] for g in d["execution_gate_cascade"]]
    assert ids[:5]==["G0-WIT007-LOT-PASSPORT","G1-WIT008-MACHINE-TOOL-CAL","G2-WIT006-GEOMETRY-FREEZE","G3-WIT009-PROCESS-HISTORY","G4-WIT001-002-003-MEASURE"]
    assert all(g["required"] for g in d["execution_gate_cascade"])

def test_capacitance_is_inference_not_measurement():
    d=load()
    c=d["witness_geometry"]["capacitor"]
    assert c["ideal_inference"]["ideal_C_pF"]==120.41695425408
    assert "NOT_MEASURED" in c["ideal_inference"]["evidence"]
    assert d["measurement_packet"]["capacitor"]["required_comparator_point_Hz"]==1000

def test_resistor_and_inductor_remain_parameterized_until_measurement():
    d=load()
    r=d["witness_geometry"]["resistor"]["parameterization"]
    l=d["witness_geometry"]["inductor"]["parameterization"]
    assert "R_target/Rs_meas" in r["square_count"]
    assert "Do not freeze numeric" in r["geometry_rule"]
    assert "Do not invent" in l["freeze_rule"]

def test_p3_requires_measured_p2():
    d=load()
    assert d["p3_dependency"]["blocked_instance"]=="CGXI-P3-LC-001"
    assert "Measured and accepted" in d["p3_dependency"]["release_condition"]


def test_pre_run_authority_is_separate_from_post_run_process_and_measurement_evidence():
    d=load()
    pa=d["physical_authority"]
    pre=" ".join(pa["pre_run_authorization_requires"])
    post=" ".join(pa["post_run_evidence_requires"])
    assert "G0-WIT007" in pre and "G1-WIT008" in pre and "G2-WIT006" in pre
    assert "G3-WIT009" not in pre
    assert "G3-WIT009" in post and "G4-WIT001-002-003" in post and "G5-READBACK-DBR" in post
    assert "G3 is post-run actual process evidence" in pa["execution_requires"]
