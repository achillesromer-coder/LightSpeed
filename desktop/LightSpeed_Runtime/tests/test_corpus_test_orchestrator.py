from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from lightspeed_runtime.corpus_test_orchestrator import (
    CorpusTestPlanError,
    assess_frontier_unit,
    PACKET_SCHEMA,
    RECEIPT_SCHEMA,
    compile_test_packet,
    plan_cascade,
    receipt_is_final,
)


def corpus_snapshot() -> dict:
    return {
        "snapshot_id": "CGX-SNAPSHOT-001",
        "authority": "Drive + admitted CGX graph",
        "source_refs": ["drive:romer-canon:v1", "git:lightspeed:current"],
        "values": {
            "rfs.frequency_hz": {
                "value": 10.0,
                "units": "Hz",
                "source_ref": "drive:rfs:frequency",
                "evidence_state": "verified",
            },
            "rfs.amplitude_m": {
                "value": 0.001,
                "units": "m",
                "source_ref": "drive:rfs:amplitude",
                "evidence_state": "canonical",
            },
        },
    }


def base_spec(test_id: str = "SWEEP-01") -> dict:
    return {
        "test_id": test_id,
        "capability_id": "rfs-emff-screening",
        "kind": "simulation",
        "depends_on": [],
        "complexity_rank": 1,
        "input_bindings": {
            "frequency_hz": {
                "source": "corpus",
                "source_key": "rfs.frequency_hz",
                "required": True,
                "units": "Hz",
            },
            "amplitude_m": {
                "source": "corpus",
                "source_key": "rfs.amplitude_m",
                "required": True,
                "units": "m",
            },
        },
        "execution_controls": {"mode": "screening", "max_cases": 32},
        "expected_artifacts": ["results.json", "manifest.json"],
    }


def final_receipt(test_id: str, packet_sha: str, **outputs) -> dict:
    return {
        "schema": RECEIPT_SCHEMA,
        "test_id": test_id,
        "status": "completed",
        "proof_state": "proven",
        "readback_state": "verified",
        "commit_state": "committed",
        "input_packet_sha256": packet_sha,
        "result_sha256": "f" * 64,
        "outputs": outputs,
        "artifact_refs": [f"local:{test_id}:manifest"],
    }


def test_corpus_packet_contains_inputs_but_never_prefills_results() -> None:
    packet = compile_test_packet(base_spec(), corpus_snapshot())
    assert packet["schema"] == PACKET_SCHEMA
    assert packet["execution_state"] == "ready"
    assert packet["resolved_inputs"] == {"frequency_hz": 10.0, "amplitude_m": 0.001}
    assert packet["result_values_known_before_execution"] is False
    assert packet["result_values"] == {}
    assert packet["canonical_mutation"] is False


def test_missing_or_unverified_corpus_input_blocks_instead_of_guessing() -> None:
    snapshot = corpus_snapshot()
    snapshot["values"]["rfs.frequency_hz"]["evidence_state"] = "candidate"
    packet = compile_test_packet(base_spec(), snapshot)
    assert packet["execution_state"] == "blocked"
    assert "frequency_hz" not in packet["resolved_inputs"]
    assert any(item["reason"] == "SOURCE_VERIFICATION_REQUIRED" for item in packet["unresolved_inputs"])


def test_corpus_unit_mismatch_is_blocked_without_silent_conversion() -> None:
    """Source-bound numbers are not interchangeable across different units."""
    baseline = compile_test_packet(base_spec(), corpus_snapshot())
    assert baseline["execution_state"] == "ready"
    for bad_unit in ("kHz", None, "rad/s"):
        snapshot = corpus_snapshot()
        snapshot["values"]["rfs.frequency_hz"]["units"] = bad_unit
        packet = compile_test_packet(base_spec(), snapshot)
        assert packet["execution_state"] == "blocked"
        assert "frequency_hz" not in packet["resolved_inputs"]
        mismatch = next(
            (row for row in packet["unresolved_inputs"] if row["input"] == "frequency_hz"),
            None,
        )
        assert mismatch is not None
        assert mismatch["reason"] == "SOURCE_VERIFICATION_REQUIRED"
        assert mismatch["unit_check"] == "mismatch"
        assert mismatch["expected_units"] == "Hz"
        assert mismatch["source_units"] == bad_unit
        assert packet["canonical_mutation"] is False


def test_dependency_output_propagates_only_after_proof_readback_and_commit() -> None:
    first = base_spec("SWEEP-01")
    first_packet = compile_test_packet(first, corpus_snapshot())
    second = {
        "test_id": "SWEEP-02",
        "capability_id": "dependent-screening",
        "kind": "simulation",
        "depends_on": ["SWEEP-01"],
        "complexity_rank": 2,
        "input_bindings": {
            "frequency_hz": {"source": "corpus", "source_key": "rfs.frequency_hz"},
            "prior_peak": {
                "source": "dependency",
                "test_id": "SWEEP-01",
                "output_key": "peak_force_n",
            },
        },
    }
    blocked = compile_test_packet(second, corpus_snapshot(), {})
    assert blocked["execution_state"] == "blocked"

    uncommitted = final_receipt("SWEEP-01", first_packet["input_packet_sha256"], peak_force_n=0.42)
    uncommitted["commit_state"] = "uncommitted"
    assert compile_test_packet(second, corpus_snapshot(), {"SWEEP-01": uncommitted})["execution_state"] == "blocked"

    complete = final_receipt("SWEEP-01", first_packet["input_packet_sha256"], peak_force_n=0.42)
    assert receipt_is_final(complete)
    ready = compile_test_packet(second, corpus_snapshot(), {"SWEEP-01": complete})
    assert ready["execution_state"] == "ready"
    assert ready["resolved_inputs"]["prior_peak"] == 0.42


def test_sixteen_sweeps_are_topologically_ordered_simplest_to_most_interdependent() -> None:
    specs = []
    for index in range(1, 17):
        test_id = f"SWEEP-{index:02d}"
        spec = {
            "test_id": test_id,
            "capability_id": "cascade-screening",
            "kind": "simulation",
            "depends_on": [] if index == 1 else [f"SWEEP-{index - 1:02d}"],
            "complexity_rank": index,
            "input_bindings": {
                "frequency_hz": {"source": "corpus", "source_key": "rfs.frequency_hz"}
            },
        }
        if index > 1:
            spec["input_bindings"]["prior_value"] = {
                "source": "dependency",
                "test_id": f"SWEEP-{index - 1:02d}",
                "output_key": "derived_value",
            }
        specs.append(spec)

    plan = plan_cascade(specs, corpus_snapshot())
    assert [item["test_id"] for item in plan["tests"]] == [f"SWEEP-{index:02d}" for index in range(1, 17)]
    assert plan["tests"][0]["semantic_state"] == "ready"
    assert all(item["semantic_state"] == "blocked" for item in plan["tests"][1:])
    assert plan["tests"][-1]["dependency_layer"] == 15
    assert plan["result_policy"].startswith("results are absent until execution")


def test_semantic_rollup_exposes_complete_and_underway() -> None:
    first = base_spec("SWEEP-01")
    first_packet = compile_test_packet(first, corpus_snapshot())
    first_receipt = final_receipt("SWEEP-01", first_packet["input_packet_sha256"], peak_force_n=0.42)
    second = {
        "test_id": "SWEEP-02",
        "capability_id": "dependent-screening",
        "kind": "simulation",
        "depends_on": ["SWEEP-01"],
        "complexity_rank": 2,
        "input_bindings": {
            "prior_peak": {
                "source": "dependency",
                "test_id": "SWEEP-01",
                "output_key": "peak_force_n",
            }
        },
    }
    second_packet = compile_test_packet(second, corpus_snapshot(), {"SWEEP-01": first_receipt})
    second_receipt = {
        "schema": RECEIPT_SCHEMA,
        "test_id": "SWEEP-02",
        "status": "underway",
        "proof_state": "unproven",
        "readback_state": "unverified",
        "commit_state": "uncommitted",
        "input_packet_sha256": second_packet["input_packet_sha256"],
        "result_sha256": "",
        "outputs": {},
    }
    plan = plan_cascade([first, second], corpus_snapshot(), {"SWEEP-01": first_receipt, "SWEEP-02": second_receipt})
    states = {item["test_id"]: item["semantic_state"] for item in plan["tests"]}
    assert states == {"SWEEP-01": "complete", "SWEEP-02": "underway"}
    assert plan["overall_state"] == "underway"
    assert plan["automatic_activation"] is False


def test_cycle_is_rejected() -> None:
    a = base_spec("A")
    a["depends_on"] = ["B"]
    a["input_bindings"]["b"] = {"source": "dependency", "test_id": "B", "output_key": "x"}
    b = base_spec("B")
    b["depends_on"] = ["A"]
    b["input_bindings"]["a"] = {"source": "dependency", "test_id": "A", "output_key": "x"}
    with pytest.raises(CorpusTestPlanError, match="cycle"):
        plan_cascade([a, b], corpus_snapshot())


def test_literal_scientific_input_is_not_an_allowed_binding_source() -> None:
    spec = copy.deepcopy(base_spec())
    spec["input_bindings"]["frequency_hz"] = {"source": "literal", "value": 123.0}
    with pytest.raises(CorpusTestPlanError, match="corpus or dependency"):
        compile_test_packet(spec, corpus_snapshot())


def _frontier_request(**kw):
    obj={"domain":"COGNIGREX","object_id":"cgx://RFS-001","source_sha256":"a"*64,
         "owner":"COGNIGREX","operation":"admit_and_test","acceptance_version":"v1",
         "evidence_class":"COMPUTED","source_changed":True,"dependencies_changed":False,
         "limits":{"max_elapsed_s":600,"max_tokens":8000,"max_tool_calls":12,"max_retries":1,"max_cost_usd":0.25},
         "usage":{"elapsed_s":0,"tokens":0,"tool_calls":0,"retries":0,"cost_usd":0.0}}
    obj.update(kw)
    return obj


def test_frontier_admission_idempotent_and_source_changed():
    first=assess_frontier_unit(_frontier_request())
    assert first["verdict"]=="READY_FOR_BOUNDED_WORK"
    receipt={"work_key":first["work_key"],"terminal_state":"COMPLETE",
             "source_sha256":"a"*64,"readback_verified":True,
             "independent_proof_verified":True}
    same=assess_frontier_unit(_frontier_request(source_changed=False),accepted_receipt=receipt)
    assert same["verdict"]=="NO_CHANGE"
    assert not same["writes_authorized"] and same["historical_ACR3_is_read_only"]
    changed=assess_frontier_unit(_frontier_request(source_sha256="b"*64),accepted_receipt=receipt)
    assert changed["verdict"]=="READY_FOR_BOUNDED_WORK"
    assert changed["work_key"]!=first["work_key"]
    dependency_changed=assess_frontier_unit(_frontier_request(source_changed=False,dependencies_changed=True),accepted_receipt=receipt)
    assert dependency_changed["verdict"]=="READY_FOR_BOUNDED_WORK"
    owner_changed=assess_frontier_unit(_frontier_request(owner="ECO_GREX",source_changed=False),accepted_receipt=receipt)
    assert owner_changed["work_key"]!=first["work_key"]
    assert owner_changed["verdict"]=="HOLD"



def test_frontier_resource_ceiling_blocks_and_does_not_claim_enforcement():
    for field,number,why in [("elapsed_s",600,"WALL_CLOCK_CEILING"),
                             ("tokens",8000,"TOKEN_CEILING"),
                             ("tool_calls",12,"TOOL_CEILING"),
                             ("retries",2,"RETRY_CEILING"),
                             ("cost_usd",0.25,"COST_CEILING")]:
        usage={**_frontier_request()["usage"],field:number}
        result=assess_frontier_unit(_frontier_request(usage=usage))
        assert (result["verdict"],result["reason"])==("HOLD",why)
        assert result["resource_ceiling_enforced_by_this_function"] is False


def test_frontier_missing_or_invalid_inputs_fail_closed():
    for bad in ["ACR3","DUPLICATE_MASTER",""]:
        with pytest.raises(CorpusTestPlanError):
            assess_frontier_unit(_frontier_request(domain=bad))
    for field,invalid in [("tokens",True),("elapsed_s",-1),("tool_calls",1.2)]:
        with pytest.raises(CorpusTestPlanError):
            assess_frontier_unit(_frontier_request(usage={**_frontier_request()["usage"],field:invalid}))
    with pytest.raises(CorpusTestPlanError):
        assess_frontier_unit(_frontier_request(evidence_class="PHYSICALLY_PROVEN_BY_AI"))
    with pytest.raises(CorpusTestPlanError):
        assess_frontier_unit(_frontier_request(source_sha256="NOT_SHA"))


def test_known_unknown_frontier_is_source_addressed_and_stops_at_g3():
    specs = []
    for index in range(5):
        spec = base_spec(f"FRONTIER-{index}")
        spec["depends_on"] = [] if index == 0 else [f"FRONTIER-{index - 1}"]
        specs.append(spec)
    plan = plan_cascade(specs, corpus_snapshot())
    view = plan["known_unknown_frontier"]
    assert view["schema"] == "CGX-KNOWN-UNKNOWN-FRONTIER/0.1"
    assert [node["generation"] for node in view["nodes"]] == ["G0", "G1", "G2", "G3"]
    assert view["omitted_beyond_G3"] == 1
    assert view["omitted_within_G3_at_node_limit"] == 0
    assert view["execution_authorized"] is False
    assert view["canonical_mutation"] is False
    first = view["nodes"][0]
    assert first["input_packet_sha256"] == plan["tests"][0]["packet"]["input_packet_sha256"]
    assert first["original_source_refs"]
    assert first["result_evidence_class"] == "UNVERIFIED"
    assert view["nodes"][1]["semantic_state"] == "blocked"
    assert any(
        row["reason"] == "DEPENDENCY_PROOF_REQUIRED"
        for row in view["nodes"][1]["unresolved_inputs"]
    )


def test_changed_source_rejects_old_receipt_before_dependency_propagation():
    first = base_spec("SOURCE-01")
    second = base_spec("DEPENDENT-02")
    second["depends_on"] = ["SOURCE-01"]
    second["input_bindings"]["prior_result"] = {
        "source": "dependency",
        "test_id": "SOURCE-01",
        "output_key": "peak_force_n",
    }
    old_packet = compile_test_packet(first, corpus_snapshot())
    old_receipt = final_receipt("SOURCE-01", old_packet["input_packet_sha256"], peak_force_n=0.42)
    changed = corpus_snapshot()
    changed["values"]["rfs.frequency_hz"]["value"] = 11.0
    plan = plan_cascade([first, second], changed, {"SOURCE-01": old_receipt})
    assert plan["tests"][0]["receipt_rejection"] == "INPUT_PACKET_SHA256_MISMATCH"
    assert plan["tests"][0]["semantic_state"] == "ready"
    assert plan["tests"][1]["semantic_state"] == "blocked"
    assert plan["tests"][1]["packet"]["unresolved_inputs"]
    assert plan["known_unknown_frontier"]["nodes"][0]["receipt_rejection"] == "INPUT_PACKET_SHA256_MISMATCH"



def _historical_intent_coverage_registry() -> dict:
    repo_root = Path(__file__).resolve().parents[3]
    path = repo_root / "cgx" / "domain_templates" / "corpus_test_capability_registry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_frontier_historical_intent_coverage_is_explicit_non_authoritative() -> None:
    registry = _historical_intent_coverage_registry()
    coverage = registry["historical_intent_coverage"]
    assert registry["schema"] == "CGX-CORPUS-TEST-CAPABILITY-REGISTRY/0.1"
    assert registry["default_activation_state"] == "prepared_not_activated"
    assert len(registry["capabilities"]) == 4  # no new tool was silently activated
    assert coverage["state"] == "NON_AUTHORITATIVE_RECONCILIATION_CANDIDATE"
    assert coverage["coverage_completeness"].startswith("PARTIAL_BY_DESIGN")
    assert len(coverage["entries"]) == 27
    ids = [entry["intent_id"] for entry in coverage["entries"]]
    assert len(set(ids)) == len(ids)
    assert len({entry["scoped_owner"] for entry in coverage["entries"]}) == 5
    assert "LightSpeed#158" in coverage["existing_operational_gate_issues"]
    assert "LightSpeed#161" in coverage["existing_operational_gate_issues"]


def test_frontier_coverage_prevents_unreviewed_or_inferred_results_becoming_execution() -> None:
    coverage = _historical_intent_coverage_registry()["historical_intent_coverage"]
    repo_root = Path(__file__).resolve().parents[3]
    supported_origins = {
        "existing_contract", "historical_owner_intent_to_reconcile",
        "inferred_follow_on_owner_review",
    }
    for intent in coverage["entries"]:
        assert intent["intent_origin"] in supported_origins
        assert intent["source_binding"] == "RECONCILE_ORIGINAL_OWNER_OBJECT_AND_HASH"
        assert intent["execution_status"] == "NOT_ATTESTED_FOR_THIS_INTENT"
        assert intent["physical_status"] == "NOT_CLAIMED"
        assert intent["method_candidates"]
        assert intent["next_required_evidence"]
        assert intent["owner_source_candidates"]
        for ref in intent["owner_source_candidates"]:
            path = repo_root / ref
            assert ref.startswith("cgx/domain_templates/")
            assert path.is_file(), f"{intent['intent_id']}: missing source candidate {ref}"
        if intent["intent_origin"] == "inferred_follow_on_owner_review":
            assert intent["plan_state"] == "REQUIRES_OWNER_REVIEW"
        else:
            assert intent["plan_state"] == "REVIEW_CANDIDATE_NOT_SCHEDULED"
