from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any, Mapping, Sequence


POLICY_SCHEMA = "CGX-CORPUS-TEST-CASCADE/0.1"
PACKET_SCHEMA = "CGX-CORPUS-TEST-PACKET/0.1"
RECEIPT_SCHEMA = "CGX-CORPUS-TEST-RECEIPT/0.1"

FINAL_PROOF_STATE = "proven"
FINAL_READBACK_STATE = "verified"
FINAL_COMMIT_STATE = "committed"
FINAL_EXECUTION_STATES = frozenset({"complete", "completed"})


class CorpusTestPlanError(ValueError):
    """Raised when corpus-bound test/simulation planning is invalid or unsafe."""


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CorpusTestPlanError(f"{field} must be non-empty text")
    return " ".join(value.split()).strip()


def _string_list(value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    if value is None and allow_empty:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise CorpusTestPlanError(f"{field} must be a list")
    result: list[str] = []
    for index, item in enumerate(value):
        text = _text(item, f"{field}[{index}]")
        if text not in result:
            result.append(text)
    if not result and not allow_empty:
        raise CorpusTestPlanError(f"{field} must not be empty")
    return result


def validate_corpus_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(snapshot, Mapping):
        raise CorpusTestPlanError("corpus_snapshot must be an object")
    snapshot_id = _text(snapshot.get("snapshot_id"), "corpus_snapshot.snapshot_id")
    source_refs = _string_list(snapshot.get("source_refs", []), "corpus_snapshot.source_refs")
    values = snapshot.get("values")
    if not isinstance(values, Mapping):
        raise CorpusTestPlanError("corpus_snapshot.values must be an object")

    normalized_values: dict[str, dict[str, Any]] = {}
    for key, raw in values.items():
        source_key = _text(key, "corpus_snapshot.values key")
        if not isinstance(raw, Mapping):
            raise CorpusTestPlanError(f"corpus_snapshot.values.{source_key} must be an object")
        if "value" not in raw:
            raise CorpusTestPlanError(f"corpus_snapshot.values.{source_key} requires value")
        evidence_state = str(raw.get("evidence_state") or "unverified").strip().lower()
        source_ref = str(raw.get("source_ref") or "").strip()
        if evidence_state in {"verified", "canonical", "proofed"} and not source_ref:
            raise CorpusTestPlanError(
                f"corpus_snapshot.values.{source_key} requires source_ref when evidence is trusted"
            )
        normalized_values[source_key] = {
            "value": raw.get("value"),
            "units": raw.get("units"),
            "source_ref": source_ref or None,
            "evidence_state": evidence_state,
            "bounds": raw.get("bounds"),
            "metadata": dict(raw.get("metadata") or {}),
        }

    normalized = {
        "snapshot_id": snapshot_id,
        "source_refs": source_refs,
        "values": normalized_values,
        "authority": str(snapshot.get("authority") or "corpus").strip() or "corpus",
    }
    normalized["snapshot_sha256"] = _sha256(normalized)
    return normalized


def validate_test_spec(spec: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, Mapping):
        raise CorpusTestPlanError("test spec must be an object")
    test_id = _text(spec.get("test_id"), "test_id")
    capability_id = _text(spec.get("capability_id"), f"{test_id}.capability_id")
    kind = _text(spec.get("kind"), f"{test_id}.kind")
    depends_on = _string_list(spec.get("depends_on", []), f"{test_id}.depends_on")
    if test_id in depends_on:
        raise CorpusTestPlanError(f"{test_id} cannot depend on itself")

    bindings = spec.get("input_bindings")
    if not isinstance(bindings, Mapping) or not bindings:
        raise CorpusTestPlanError(f"{test_id}.input_bindings must be a non-empty object")

    normalized_bindings: dict[str, dict[str, Any]] = {}
    for input_name, raw in bindings.items():
        name = _text(input_name, f"{test_id}.input_bindings key")
        if not isinstance(raw, Mapping):
            raise CorpusTestPlanError(f"{test_id}.input_bindings.{name} must be an object")
        source = str(raw.get("source") or "").strip().lower()
        if source not in {"corpus", "dependency"}:
            raise CorpusTestPlanError(
                f"{test_id}.input_bindings.{name}.source must be corpus or dependency"
            )
        normalized = {
            "source": source,
            "required": bool(raw.get("required", True)),
            "units": raw.get("units"),
        }
        if source == "corpus":
            normalized["source_key"] = _text(
                raw.get("source_key"), f"{test_id}.input_bindings.{name}.source_key"
            )
        else:
            dep_test_id = _text(
                raw.get("test_id"), f"{test_id}.input_bindings.{name}.test_id"
            )
            if dep_test_id not in depends_on:
                raise CorpusTestPlanError(
                    f"{test_id}.input_bindings.{name} references undeclared dependency {dep_test_id}"
                )
            normalized["test_id"] = dep_test_id
            normalized["output_key"] = _text(
                raw.get("output_key"), f"{test_id}.input_bindings.{name}.output_key"
            )
        normalized_bindings[name] = normalized

    complexity_rank = spec.get("complexity_rank", 0)
    if isinstance(complexity_rank, bool):
        raise CorpusTestPlanError(f"{test_id}.complexity_rank must be numeric")
    try:
        complexity_rank = float(complexity_rank)
    except (TypeError, ValueError) as exc:
        raise CorpusTestPlanError(f"{test_id}.complexity_rank must be numeric") from exc

    return {
        "test_id": test_id,
        "capability_id": capability_id,
        "kind": kind,
        "depends_on": depends_on,
        "input_bindings": normalized_bindings,
        "execution_controls": dict(spec.get("execution_controls") or {}),
        "expected_artifacts": _string_list(
            spec.get("expected_artifacts", []), f"{test_id}.expected_artifacts"
        ),
        "complexity_rank": complexity_rank,
        "description": str(spec.get("description") or "").strip(),
    }


def validate_receipt(receipt: Mapping[str, Any], *, expected_test_id: str | None = None) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise CorpusTestPlanError("receipt must be an object")
    test_id = _text(receipt.get("test_id"), "receipt.test_id")
    if expected_test_id and test_id != expected_test_id:
        raise CorpusTestPlanError(
            f"receipt test_id {test_id} does not match expected {expected_test_id}"
        )
    outputs = receipt.get("outputs")
    if outputs is None:
        outputs = {}
    if not isinstance(outputs, Mapping):
        raise CorpusTestPlanError(f"{test_id} receipt outputs must be an object")
    return {
        "schema": str(receipt.get("schema") or RECEIPT_SCHEMA),
        "test_id": test_id,
        "status": str(receipt.get("status") or "").strip().lower(),
        "proof_state": str(receipt.get("proof_state") or "unproven").strip().lower(),
        "readback_state": str(receipt.get("readback_state") or "unverified").strip().lower(),
        "commit_state": str(receipt.get("commit_state") or "uncommitted").strip().lower(),
        "input_packet_sha256": str(receipt.get("input_packet_sha256") or "").strip(),
        "result_sha256": str(receipt.get("result_sha256") or "").strip(),
        "outputs": dict(outputs),
        "artifact_refs": _string_list(
            receipt.get("artifact_refs", []), f"{test_id}.receipt.artifact_refs"
        ),
    }


def receipt_is_final(receipt: Mapping[str, Any] | None) -> bool:
    if not receipt:
        return False
    normalized = validate_receipt(receipt)
    return (
        normalized["status"] in FINAL_EXECUTION_STATES
        and normalized["proof_state"] == FINAL_PROOF_STATE
        and normalized["readback_state"] == FINAL_READBACK_STATE
        and normalized["commit_state"] == FINAL_COMMIT_STATE
        and bool(normalized["input_packet_sha256"])
        and bool(normalized["result_sha256"])
    )


def _dependency_output(
    dependency_test_id: str,
    output_key: str,
    receipts: Mapping[str, Mapping[str, Any]],
) -> tuple[bool, Any, str | None]:
    receipt = receipts.get(dependency_test_id)
    if not receipt:
        return False, None, "DEPENDENCY_REQUIRED"
    normalized = validate_receipt(receipt, expected_test_id=dependency_test_id)
    if not receipt_is_final(normalized):
        return False, None, "DEPENDENCY_PROOF_REQUIRED"
    if output_key not in normalized["outputs"]:
        return False, None, "DEPENDENCY_OUTPUT_MISSING"
    return True, normalized["outputs"][output_key], None


def compile_test_packet(
    spec: Mapping[str, Any],
    corpus_snapshot: Mapping[str, Any],
    dependency_receipts: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    test = validate_test_spec(spec)
    corpus = validate_corpus_snapshot(corpus_snapshot)
    receipts = dict(dependency_receipts or {})

    resolved: dict[str, Any] = {}
    input_lineage: dict[str, dict[str, Any]] = {}
    unresolved: list[dict[str, Any]] = []

    for dependency_test_id in test["depends_on"]:
        receipt = receipts.get(dependency_test_id)
        if not receipt_is_final(receipt):
            unresolved.append(
                {
                    "input": None,
                    "reason": "DEPENDENCY_PROOF_REQUIRED",
                    "dependency_test_id": dependency_test_id,
                }
            )

    for input_name, binding in test["input_bindings"].items():
        if binding["source"] == "corpus":
            entry = corpus["values"].get(binding["source_key"])
            if not entry:
                if binding["required"]:
                    unresolved.append(
                        {
                            "input": input_name,
                            "reason": "SOURCE_REQUIRED",
                            "source_key": binding["source_key"],
                        }
                    )
                continue
            if entry["evidence_state"] not in {"verified", "canonical", "proofed"}:
                if binding["required"]:
                    unresolved.append(
                        {
                            "input": input_name,
                            "reason": "SOURCE_VERIFICATION_REQUIRED",
                            "source_key": binding["source_key"],
                            "evidence_state": entry["evidence_state"],
                        }
                    )
                continue
            resolved[input_name] = entry["value"]
            input_lineage[input_name] = {
                "source": "corpus",
                "source_key": binding["source_key"],
                "source_ref": entry["source_ref"],
                "evidence_state": entry["evidence_state"],
                "units": entry["units"],
                "bounds": entry["bounds"],
            }
        else:
            ok, value, reason = _dependency_output(
                binding["test_id"], binding["output_key"], receipts
            )
            if not ok:
                if binding["required"]:
                    unresolved.append(
                        {
                            "input": input_name,
                            "reason": reason,
                            "dependency_test_id": binding["test_id"],
                            "output_key": binding["output_key"],
                        }
                    )
                continue
            resolved[input_name] = value
            dep_receipt = validate_receipt(
                receipts[binding["test_id"]], expected_test_id=binding["test_id"]
            )
            input_lineage[input_name] = {
                "source": "dependency",
                "dependency_test_id": binding["test_id"],
                "output_key": binding["output_key"],
                "result_sha256": dep_receipt["result_sha256"],
                "receipt_proof_state": dep_receipt["proof_state"],
            }

    ready = not unresolved
    packet = {
        "schema": PACKET_SCHEMA,
        "policy_schema": POLICY_SCHEMA,
        "test_id": test["test_id"],
        "capability_id": test["capability_id"],
        "kind": test["kind"],
        "corpus_snapshot_id": corpus["snapshot_id"],
        "corpus_snapshot_sha256": corpus["snapshot_sha256"],
        "corpus_source_refs": corpus["source_refs"],
        "resolved_inputs": resolved,
        "input_lineage": input_lineage,
        "unresolved_inputs": unresolved,
        "execution_controls": test["execution_controls"],
        "expected_artifacts": test["expected_artifacts"],
        "dependency_ids": test["depends_on"],
        "result_values_known_before_execution": False,
        "result_values": {},
        "execution_state": "ready" if ready else "blocked",
        "canonical_mutation": False,
    }
    packet["input_packet_sha256"] = _sha256(packet)
    return packet


def _topological_order(specs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized = [validate_test_spec(spec) for spec in specs]
    by_id = {item["test_id"]: item for item in normalized}
    if len(by_id) != len(normalized):
        raise CorpusTestPlanError("test IDs must be unique")
    for item in normalized:
        unknown = [dep for dep in item["depends_on"] if dep not in by_id]
        if unknown:
            raise CorpusTestPlanError(
                f"{item['test_id']} depends on unknown tests: {', '.join(unknown)}"
            )

    indegree = {test_id: 0 for test_id in by_id}
    children: dict[str, list[str]] = defaultdict(list)
    for item in normalized:
        for dep in item["depends_on"]:
            indegree[item["test_id"]] += 1
            children[dep].append(item["test_id"])

    ready = [test_id for test_id, degree in indegree.items() if degree == 0]
    order: list[dict[str, Any]] = []
    while ready:
        ready.sort(
            key=lambda test_id: (
                by_id[test_id]["complexity_rank"],
                len(by_id[test_id]["input_bindings"]),
                test_id,
            )
        )
        current = ready.pop(0)
        order.append(by_id[current])
        for child in children[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)

    if len(order) != len(normalized):
        unresolved = sorted(test_id for test_id, degree in indegree.items() if degree > 0)
        raise CorpusTestPlanError(
            "dependency graph contains a cycle involving: " + ", ".join(unresolved)
        )
    return order


def semantic_state(
    packet: Mapping[str, Any],
    receipt: Mapping[str, Any] | None,
    *,
    dependency_receipts: Mapping[str, Mapping[str, Any]] | None = None,
) -> str:
    if receipt:
        normalized = validate_receipt(receipt)
        if receipt_is_final(normalized):
            return "complete"
        if normalized["status"] in {"running", "underway", "in_progress", "in-progress"}:
            return "underway"
        if normalized["status"] in {"partial", "incomplete"}:
            return "partial"
        if normalized["status"] in {"failed", "blocked", "held"}:
            return "blocked"

    if packet.get("execution_state") == "ready":
        return "ready"

    # A test with any unresolved required input is not executable. Preserve
    # partial progress in its lineage/rollup, but do not present the test itself
    # as partial because that could be mistaken for an active or usable result.
    if packet.get("execution_state") == "blocked":
        return "blocked"

    return "blocked"


def plan_cascade(
    specs: Sequence[Mapping[str, Any]],
    corpus_snapshot: Mapping[str, Any],
    receipts: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    corpus = validate_corpus_snapshot(corpus_snapshot)
    receipts = dict(receipts or {})
    order = _topological_order(specs)

    items: list[dict[str, Any]] = []
    layer_by_id: dict[str, int] = {}
    for sequence_index, spec in enumerate(order, start=1):
        layer = 0
        if spec["depends_on"]:
            layer = max(layer_by_id[dep] for dep in spec["depends_on"]) + 1
        layer_by_id[spec["test_id"]] = layer
        packet = compile_test_packet(spec, corpus, receipts)
        state = semantic_state(
            packet,
            receipts.get(spec["test_id"]),
            dependency_receipts=receipts,
        )
        items.append(
            {
                "sequence": sequence_index,
                "dependency_layer": layer,
                "test_id": spec["test_id"],
                "capability_id": spec["capability_id"],
                "kind": spec["kind"],
                "depends_on": spec["depends_on"],
                "complexity_rank": spec["complexity_rank"],
                "semantic_state": state,
                "packet": packet,
            }
        )

    counts: dict[str, int] = defaultdict(int)
    for item in items:
        counts[item["semantic_state"]] += 1

    if items and counts.get("complete", 0) == len(items):
        overall = "complete"
    elif counts.get("underway", 0):
        overall = "underway"
    elif counts.get("partial", 0) or counts.get("complete", 0):
        overall = "partial"
    elif counts.get("ready", 0):
        overall = "ready"
    else:
        overall = "blocked"

    return {
        "schema": POLICY_SCHEMA,
        "corpus_snapshot_id": corpus["snapshot_id"],
        "corpus_snapshot_sha256": corpus["snapshot_sha256"],
        "ordering_rule": "dependency-safe topological order; simplest/lowest complexity first inside each admissible frontier",
        "result_policy": "results are absent until execution receipt; no result value is inferred from corpus",
        "proof_gate": {
            "downstream_requires": {
                "execution_status": sorted(FINAL_EXECUTION_STATES),
                "proof_state": FINAL_PROOF_STATE,
                "readback_state": FINAL_READBACK_STATE,
                "commit_state": FINAL_COMMIT_STATE,
            }
        },
        "overall_state": overall,
        "state_counts": dict(sorted(counts.items())),
        "tests": items,
        "activation_ready": overall in {"ready", "partial", "underway", "complete"},
        "automatic_activation": False,
        "canonical_mutation": False,
    }
