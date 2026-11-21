import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "cgx" / "component_atlas" / "type1_radiative_transport_seed_matrix_v0_1.json"
SEED = ROOT / "cgx" / "component_atlas" / "type1_seed_field_stack_matrix_v0_1.json"
COMPILER = ROOT / "cgx" / "component_atlas" / "universal_type1_stack_compiler_v0_1.json"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def test_utp146_identity_and_seed_classes():
    d = load(PATH)
    assert d["artifact_id"] == "UTP-146"
    assert d["build_id"] == "BUILD-079"
    assert d["physical_execution"] is False
    assert set(d["seed_source_contract"]) == {"SG-0", "SG-1", "SG-N"}
    assert "cannot create net active gain" in d["seed_source_contract"]["SG-0"]["source_rule"]

def test_distinct_radiative_and_transport_regimes():
    d = load(PATH)
    ids = {x["id"] for x in d["field_transport_regimes"]}
    required = {
        "FTR-EQS","FTR-MQS","FTR-EM-NF","FTR-EM-FF","FTR-OPT","FTR-THERM-RAD",
        "FTR-ACOUSTIC","FTR-FLUID","FTR-SPECIES","FTR-IONIC","FTR-IONIZING","FTR-INERTIAL"
    }
    assert required == ids
    nf = next(x for x in d["field_transport_regimes"] if x["id"] == "FTR-EM-NF")
    ff = next(x for x in d["field_transport_regimes"] if x["id"] == "FTR-EM-FF")
    assert nf["family"] != ff["family"]
    assert "no universal distance threshold" in nf["regime_gate"]
    assert "full-wave Maxwell" in ff["governing"]

def test_energy_and_mutual_coupling_guards():
    d = load(PATH)
    rules = d["linearity_and_energy_rules"]
    assert "superposition is invalid" in rules["nonlinear_rule"]
    assert "cannot exceed external input plus released stored energy" in rules["passivity"]
    assert "nonreciprocal" in rules["reciprocity"]
    assert "ASSEMBLE_SELF_AND_MUTUAL_TERMS" in d["mapping_chain"]

def test_capacitance_closure_uses_actual_thickness_and_matrix():
    d = load(PATH)
    c = d["capacitance_closure"]
    assert "Q=C·V" in c["multi_conductor"]
    assert "sum_i(d_i/epsilon_ri)" in c["layered_1d"]
    vals = {x["d_um"]: x["C_A_pF_mm2"] for x in c["nominal_thickness_unit_check"]}
    assert abs(vals[25] - 1.2041695425408) < 1e-12
    assert abs(vals[50] - 0.6020847712704) < 1e-12
    assert abs(vals[75] - 0.4013898475136) < 1e-12
    assert abs(vals[125] - 0.24083390850816) < 1e-12
    assert "actual/source thickness" in c["discrepancy_gate"]

def test_stack_compiler_and_seed_matrix_consume_utp146():
    c = load(COMPILER)
    assert c["inputs"]["radiative_transport_seed_matrix"].endswith("type1_radiative_transport_seed_matrix_v0_1.json")
    assert c["matrix_contract"]["field_transport_regimes"] == 12
    assert "RESOLVE_RADIATIVE_TRANSPORT_REGIME" in c["compile_chain"]
    assert "CHECK_ENERGY_RECIPROCITY_PASSIVITY_CAUSALITY" in c["compile_chain"]
    s = load(SEED)
    assert s["radiative_transport_companion"]["artifact_id"] == "UTP-146"

def test_interlayer_edge_contract_and_transfer_basis():
    d = load(PATH)
    edge = d["interlayer_edge_contract"]
    assert "state_or_flux_transferred" in edge["required"]
    assert "parasitic_mutual_terms" in edge["required"]
    assert "predecessor_damage_gate" in edge["required"]
    assert "preservation_action" in edge["required"]
    assert "authority" in edge["required"]
    assert "process_direction is explicit" in " ".join(edge["typed_edge_rules"])
    assert "SOLVED/MEASURED" in " ".join(edge["typed_edge_rules"])
    ilt = {x["id"]: x for x in d["interlayer_transfer_basis"]}
    assert len(ilt) == 12
    assert "Maxwell capacitance matrix" in ilt["ILT-002"]["mutual"]
    assert "S-matrix" in ilt["ILT-004"]["mutual"]
    assert "view-factor" in ilt["ILT-007"]["mutual"]
    assert "common-mode dose" in ilt["ILT-012"]["mutual"]

def test_sequence_preserves_embedded_and_service_regions():
    d = load(PATH)
    rules = " ".join(d["sequence_and_interlayer_rules"])
    assert "qualified preservation/encapsulation barrier" in rules
    assert "Do not close cavities/channels/voids" in rules
    assert "discharge/isolation" in rules
    assert "Process history is part of 4D state" in rules
