import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "cgx" / "component_atlas" / "type1_ingest_maturation_contract_v0_1.json"


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_ingest_contract_identity_and_owner_chain():
    d = load_contract()
    assert d["artifact_id"] == "UTP-150"
    assert d["owners"]["maturity_graph"] == "UTP-148"
    assert d["owners"]["composition_matrix"] == "UTP-149"
    assert d["owners"]["normal_form"] == "UTP-147"
    assert d["owners"]["radiative_transport"] == "UTP-146"


def test_ingest_contract_is_append_only_and_fail_closed():
    d = load_contract()
    joined = " ".join(d["hard_boundaries"]).lower()
    assert "no silent overwrite" in joined
    assert "unknown/unsupported coupling remains hold" in joined
    assert "no durable .cgx carrier/root mutation" in joined
    assert "APPEND_IMMUTABLY" in d["mutation_pipeline"]
    assert "INVALIDATE_ONLY_DEPENDENT_DERIVED_RESULTS" in d["mutation_pipeline"]


def test_ingest_contract_preserves_maturity_axes_without_score():
    d = load_contract()
    axes = d["maturity_delta_record"]["required_axes"]
    assert len(axes) == 10
    assert "physical_evidence" in axes
    assert "authority_release" in axes
    assert "Never average axes into a readiness percentage" in d["maturity_delta_record"]["rule"]


def test_ingest_contract_requires_readback_and_contradiction_retention():
    d = load_contract()
    req = set(d["readback_receipt_required"])
    assert {"input_hashes", "dependency_closure_ids", "invalidated_result_ids", "maturity_delta", "next_witness_or_hold"}.issubset(req)
    assert d["contradiction_policy"]["states"]
    assert "OWNER_REVIEW_REQUIRED" in d["contradiction_policy"]["states"]


def test_ingest_contract_seed_graphs_and_numeric_routes():
    d = load_contract()
    assert set(d["seed_graph_policy"]) == {"SG-0", "SG-1", "SG-N"}
    assert d["numeric_inference_policy"]["state_routes"] == ["NUMERIC", "SYMBOLIC", "HOLD"]
    assert "Maxwell capacitance matrix" in d["numeric_inference_policy"]["capacitance"]


def test_ingest_contract_has_negative_change_fixtures():
    d = load_contract()
    fixtures = {x["id"]: x for x in d["initial_proof_fixtures"]}
    assert set(fixtures) == {"INGEST-FIXTURE-001", "INGEST-FIXTURE-002", "INGEST-FIXTURE-003"}
    assert fixtures["INGEST-FIXTURE-003"]["expected_preservation"]
