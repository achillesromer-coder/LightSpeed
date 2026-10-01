from __future__ import annotations

import copy

import pytest

from lightspeed_runtime.corpus_test_orchestrator import (
    CorpusTestPlanError,
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
