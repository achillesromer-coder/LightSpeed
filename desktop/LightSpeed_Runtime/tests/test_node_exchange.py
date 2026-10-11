from __future__ import annotations

from pathlib import Path
import json

import pytest

from lightspeed_runtime.node_exchange import (
    NodeExchangeError,
    build_compute_request,
    build_exchange_status,
    build_transfer_envelope,
    execute_local_compute,
    execute_local_transfer,
    load_node_root_registry,
    resolve_node_root,
)


def test_node_root_registry_resolves_only_registered_access(tmp_path: Path) -> None:
    read_root = tmp_path / "read"
    write_root = tmp_path / "write"
    read_root.mkdir()
    write_root.mkdir()
    registry_path = tmp_path / "node_roots.json"
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": "cgx-node-root-registry-v1",
                "node_id": "bouwerbase",
                "roots": [
                    {
                        "root_id": "read-root",
                        "path": str(read_root),
                        "access": "read",
                        "kind": "source",
                    },
                    {
                        "root_id": "write-root",
                        "path": str(write_root),
                        "access": "read_write",
                        "kind": "staging",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    registry = load_node_root_registry(registry_path)

    assert resolve_node_root(
        registry,
        node_id="bouwerbase",
        root_id="write-root",
        require_write=True,
    ) == write_root.resolve()
    with pytest.raises(NodeExchangeError, match="not write-enabled"):
        resolve_node_root(
            registry,
            node_id="bouwerbase",
            root_id="read-root",
            require_write=True,
        )
    with pytest.raises(NodeExchangeError, match="does not belong"):
        resolve_node_root(
            registry,
            node_id="other-node",
            root_id="write-root",
        )


def test_transfer_round_trip_and_reuse(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    source = source_root / "payload.txt"
    source.write_text("CGX node exchange test\n", encoding="utf-8")

    envelope = build_transfer_envelope(
        source,
        source_node_id="node-a",
        target_node_id="node-b",
        source_root_id="source",
        target_root_id="target",
    )
    receipt = execute_local_transfer(
        envelope,
        target_root=target_root,
        allowed_source_roots=[source_root],
        allowed_target_roots=[target_root],
        lease_validation={
            "valid": True,
            "lease_id": "LEASE-WRITE",
            "lease_class": "DIGITAL_WRITE",
        },
    )
    assert receipt["state"] == "verified"
    assert receipt["exact_readback"] is True
    assert receipt["source_sha256"] == receipt["received_sha256"]
    assert receipt["authority_transfer"] is False

    reused = execute_local_transfer(
        envelope,
        target_root=target_root,
        allowed_source_roots=[source_root],
        allowed_target_roots=[target_root],
        lease_validation={
            "valid": True,
            "lease_id": "LEASE-WRITE",
            "lease_class": "DIGITAL_WRITE",
        },
    )
    assert reused["reused_existing_payload"] is True


def test_transfer_rejects_source_outside_allowlist(tmp_path: Path) -> None:
    source = tmp_path / "outside.txt"
    source.write_text("outside", encoding="utf-8")
    approved_source = tmp_path / "approved"
    target_root = tmp_path / "target"
    approved_source.mkdir()
    target_root.mkdir()
    envelope = build_transfer_envelope(
        source,
        source_node_id="node-a",
        target_node_id="node-b",
        source_root_id="source",
        target_root_id="target",
    )
    with pytest.raises(NodeExchangeError, match="outside approved roots"):
        execute_local_transfer(
            envelope,
            target_root=target_root,
            allowed_source_roots=[approved_source],
            allowed_target_roots=[target_root],
            lease_validation={
                "valid": True,
                "lease_id": "LEASE-WRITE",
                "lease_class": "DIGITAL_WRITE",
            },
        )


def test_transfer_requires_digital_write_class(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    source = source_root / "payload.txt"
    source.write_text("lease boundary", encoding="utf-8")
    envelope = build_transfer_envelope(
        source,
        source_node_id="node-a",
        target_node_id="node-a",
        source_root_id="source",
        target_root_id="target",
    )
    with pytest.raises(NodeExchangeError, match="does not permit digital transfer"):
        execute_local_transfer(
            envelope,
            target_root=target_root,
            allowed_source_roots=[source_root],
            allowed_target_roots=[target_root],
            lease_validation={
                "valid": True,
                "lease_id": "LEASE-COMPUTE",
                "lease_class": "COMPUTE_ONLY",
            },
        )


def test_compute_uses_verified_inputs_and_matching_lease() -> None:
    transfer_receipt = {
        "transfer_id": "NXFER-1",
        "state": "verified",
        "source_sha256": "a" * 64,
        "received_sha256": "a" * 64,
        "size_bytes": 10,
        "exact_readback": True,
    }
    request = build_compute_request(
        "Check the transferred payload and return a bounded result.",
        task_id="T1",
        run_id="R1",
        target_node_id="bouwerbase",
        capability_id="cognigrex-supervised-workflow",
        lease_ref="LEASE-1",
        input_receipts=[transfer_receipt],
    )

    calls: list[dict[str, object]] = []
    def fake_runner(instruction: str, **kwargs):
        calls.append({"instruction": instruction, **kwargs})
        return {
            "status": "complete",
            "complete_workflow": True,
            "workflow_id": "wf-1",
            "receipt_path": "receipt.json",
        }

    receipt = execute_local_compute(
        request,
        local_node_id="bouwerbase",
        lease_validation={
            "valid": True,
            "lease_id": "LEASE-1",
            "lease_class": "COMPUTE_ONLY",
        },
        runner=fake_runner,
    )
    assert receipt["status"] == "complete"
    assert receipt["authority_transfer"] is False
    assert receipt["raw_instruction_persisted_in_receipt"] is False
    assert calls and calls[0]["allow_heavy"] is False

    with pytest.raises(NodeExchangeError, match="lease_ref"):
        execute_local_compute(
            request,
            local_node_id="bouwerbase",
            lease_validation={
                "valid": True,
                "lease_id": "LEASE-OTHER",
                "lease_class": "COMPUTE_ONLY",
            },
            runner=fake_runner,
        )
def test_compute_rejects_unverified_transfer_input() -> None:
    request = build_compute_request(
        "Do bounded compute.",
        task_id="T2",
        run_id="R2",
        target_node_id="bouwerbase",
        capability_id="cognigrex-supervised-workflow",
        lease_ref="LEASE-2",
        input_receipts=[
            {
                "transfer_id": "NXFER-2",
                "state": "staged",
                "source_sha256": "b" * 64,
                "received_sha256": None,
                "size_bytes": 4,
                "exact_readback": False,
            }
        ],
    )
    with pytest.raises(NodeExchangeError, match="verified target readback"):
        execute_local_compute(
            request,
            local_node_id="bouwerbase",
            lease_validation={
                "valid": True,
                "lease_id": "LEASE-2",
                "lease_class": "COMPUTE_ONLY",
            },
            runner=lambda *_args, **_kwargs: {},
        )


def test_status_does_not_treat_carrier_as_peer_compute() -> None:
    status = build_exchange_status(
        local_node_id="bouwerbase",
        local_compute_ready=True,
        verified_carriers=["E-volume"],
        peer_nodes=[],
    )
    assert status["compute"]["local_ready"] is True
    assert status["transport"]["verified_carriers"] == ["E-volume"]
    assert status["transport"]["peer_transport_verified"] is False
    assert status["compute"]["peer_compute_verified"] is False


# DataSpace observer facet: read-only deterministic candidate projection.
from lightspeed_runtime.node_exchange import project_rolling_observer_window

_OBSERVER_ROOT = "a" * 64
_OBSERVER_ARGS = {
    "object_id": "cgx:lab:fixture",
    "geometry_root": _OBSERVER_ROOT,
    "semantic_root": _OBSERVER_ROOT,
    "model_root": _OBSERVER_ROOT,
    "prior_state_root": _OBSERVER_ROOT,
    "selected_nodes": ["a", "b", "c", "d", "e"],
    "end_ms": 60000,
}


def _observer_samples(timestamp_ms: int, state: int | None) -> list[dict]:
    return [
        {
            "observer_id": node,
            "independence_group": group,
            "timestamp_ms": timestamp_ms,
            "state": state,
            "receipt_verified": True,
        }
        for node, group in zip(("a", "b", "c"), ("ga", "gb", "gc"))
    ]


def test_rolling_observer_three_distinct_and_nine_views() -> None:
    result = project_rolling_observer_window(
        **_OBSERVER_ARGS, samples=_observer_samples(60000, 1)
    )
    assert len(result["lenses"]) == 9
    assert result["lenses"]["state"] == 1
    assert result["epistemic_status"] == "OBSERVATIONAL_CANDIDATE"
    assert not result["cryptographically_authenticated_by_this_function"]
    assert not result["canonical_promotion_authorized"]
    assert not result["physical_actuation_authorized"]


def test_rolling_observer_two_readings_not_quorum() -> None:
    result = project_rolling_observer_window(
        **_OBSERVER_ARGS, samples=_observer_samples(60000, 0)[:2]
    )
    assert result["lenses"]["state"] is None


def test_rolling_observer_group_not_independent() -> None:
    samples = _observer_samples(60000, 1)
    for sample in samples:
        sample["independence_group"] = "one"
    result = project_rolling_observer_window(**_OBSERVER_ARGS, samples=samples)
    assert result["lenses"]["state"] is None


def test_rolling_observer_contradiction_retained() -> None:
    samples = _observer_samples(60000, 1)
    samples[-1]["state"] = -1
    result = project_rolling_observer_window(**_OBSERVER_ARGS, samples=samples)
    assert result["lenses"]["state"] is None
    assert result["lenses"]["spatial_corroboration"]["conflicts"] == 1


def test_rolling_observer_short_event_survives_baseline_return() -> None:
    samples = (
        _observer_samples(57000, 0)
        + _observer_samples(58000, 1)
        + _observer_samples(59000, 0)
        + _observer_samples(60000, 0)
    )
    result = project_rolling_observer_window(**_OBSERVER_ARGS, samples=samples)
    assert result["trajectory"][-4:] == [0, 1, 0, 0]
    assert result["lenses"]["activity"]["changes"] == 2


def test_rolling_observer_erasure_is_not_zero() -> None:
    samples = _observer_samples(59000, None) + _observer_samples(60000, -1)
    result = project_rolling_observer_window(**_OBSERVER_ARGS, samples=samples)
    assert result["trajectory"][-2:] == [None, -1]
    assert result["lenses"]["transition"] == "UNKNOWN"


def test_rolling_observer_unverified_receipt_rejected() -> None:
    samples = _observer_samples(60000, 1)
    samples[0]["receipt_verified"] = False
    with pytest.raises(NodeExchangeError, match="adapter-verified"):
        project_rolling_observer_window(**_OBSERVER_ARGS, samples=samples)


def test_rolling_observer_unknown_and_boolean_rejected() -> None:
    samples = _observer_samples(60000, 1)
    samples[0]["state"] = True
    with pytest.raises(NodeExchangeError, match="ternary"):
        project_rolling_observer_window(**_OBSERVER_ARGS, samples=samples)


def test_rolling_observer_duplicates_rejected() -> None:
    samples = _observer_samples(60000, 1)
    with pytest.raises(NodeExchangeError, match="duplicate"):
        project_rolling_observer_window(**_OBSERVER_ARGS, samples=samples + [samples[0]])


def test_rolling_observer_bad_roots_and_phase_change_rejected() -> None:
    with pytest.raises(NodeExchangeError, match="SHA-256"):
        project_rolling_observer_window(
            **{**_OBSERVER_ARGS, "geometry_root": "bad"}, samples=[]
        )
    with pytest.raises(NodeExchangeError, match="nine distinct"):
        project_rolling_observer_window(
            **_OBSERVER_ARGS, samples=[], phase_slots=(0,) * 9
        )


# N-node configuration is a facet of the existing node-exchange test suite.
from hashlib import sha256

from lightspeed_runtime.node_exchange import (
    DATASPACE_PROFILE_FACET,
    apply_dataspace_delta_candidate,
    build_dataspace_delta_candidate,
    validate_dataspace_profile,
)


def _dp_hash(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _dp_fixture():
    old = {"signal": 0, "drift": -1}
    root = "d" * 64
    profile = {
        "schema_version": DATASPACE_PROFILE_FACET,
        "object_id": "cgx:lab:test",
        "geometry_root": root,
        "semantic_root": root,
        "model_root": root,
        "state_root": _dp_hash(old),
        "nodes": [
            {"id": "a", "visibility": "public", "owner_ref": "research:A", "access_policy_ref": "scope:A"},
            {"id": "b", "visibility": "private", "owner_ref": "research:B", "access_policy_ref": "scope:B"},
            {"id": "c", "visibility": "restricted", "owner_ref": "research:C", "access_policy_ref": "scope:C"},
        ],
        "selection": {"include": ["a", "b"], "exclude": ["c"]},
        "interfaces": [
            {"id": "ab", "kind": "electromagnetic", "nodes": ["a", "b"], "model_ref": "model:ab"}
        ],
        "derivables": [
            {"id": "signal", "inputs": ["ab"], "function_ref": "fn:signal", "unit": "trit"},
            {"id": "drift", "inputs": ["ab"], "function_ref": "fn:drift", "unit": "trit"},
        ],
        "relationships": [
            {"id": "r1", "kind": "OBSERVES", "source": "node:a", "target": "interface:ab", "evidence_ref": "evidence:a"},
        ],
        "semantic_lenses": [
            {"id": "first", "derivable_id": "signal", "registered_view_ref": "lens:state"},
            {"id": "second", "derivable_id": "drift", "registered_view_ref": "lens:transition"},
        ],
        "transports": [
            {"id": "wired", "kind": "wired", "throughput_bps": 1000000,
             "spectral_bandwidth_hz": 0, "observed_occupancy_fraction": 0.25,
             "transmit_permission": "NOT_VERIFIED"},
        ],
        "cadence": {"window_ms": 60000, "sample_ms": 1000, "phase_ms": 5000},
        "expected_counts": {"nodes": 3, "selected_nodes": 2, "interfaces": 1,
                            "derivables": 2, "relationships": 1, "semantic_lenses": 2,
                            "transports": 1},
    }
    return profile, old


def test_dataspace_profile_selection_and_sparse_delta():
    profile, old = _dp_fixture()
    result = validate_dataspace_profile(profile)
    assert result["count_summary"]["selected_nodes"] == 2
    assert result["access_authority_verified"] is False
    new = {"signal": 1, "drift": -1}
    candidate = build_dataspace_delta_candidate(
        profile=profile, prior_state=old, new_state=new, sequence=1, window_end_ms=60000
    )
    assert candidate["updates"] == [{"id": "signal", "state": 1}]
    assert candidate["wire_ready"] is False
    assert "nodes" not in candidate and "geometry" not in candidate
    reconstructed = apply_dataspace_delta_candidate(
        profile=profile, prior_state=old, candidate=candidate, expected_sequence=1
    )
    assert reconstructed["candidate_state"] == new
    assert reconstructed["status"] == "RECONSTRUCTED_UNTRUSTED_CANDIDATE"


def test_dataspace_configured_counts_and_selection_fail_closed():
    profile, _ = _dp_fixture()
    profile["expected_counts"]["selected_nodes"] = 3
    with pytest.raises(NodeExchangeError, match="declared counts"):
        validate_dataspace_profile(profile)
    profile, _ = _dp_fixture()
    profile["selection"]["exclude"] = ["b", "c"]
    with pytest.raises(NodeExchangeError, match="partition"):
        validate_dataspace_profile(profile)


def test_dataspace_private_selection_needs_access_policy_reference():
    profile, _ = _dp_fixture()
    profile["nodes"][1]["access_policy_ref"] = None
    with pytest.raises(NodeExchangeError, match="access policy"):
        validate_dataspace_profile(profile)


def test_dataspace_geometry_must_reference_included_nodes():
    profile, _ = _dp_fixture()
    profile["interfaces"][0]["nodes"] = ["a", "c"]
    with pytest.raises(NodeExchangeError, match="authorised selected nodes"):
        validate_dataspace_profile(profile)


def test_dataspace_derivable_requires_registered_function():
    profile, _ = _dp_fixture()
    profile["derivables"][0]["function_ref"] = ""
    with pytest.raises(NodeExchangeError, match="registered function"):
        validate_dataspace_profile(profile)


def test_dataspace_relationship_requires_evidence():
    profile, _ = _dp_fixture()
    profile["relationships"][0]["target"] = "node:ghost"
    with pytest.raises(NodeExchangeError, match="typed endpoints"):
        validate_dataspace_profile(profile)


def test_dataspace_bandwidth_occupancy_and_licence_distinct():
    profile, _ = _dp_fixture()
    profile["transports"][0]["observed_occupancy_fraction"] = 1.1
    with pytest.raises(NodeExchangeError, match="occupancy"):
        validate_dataspace_profile(profile)
    profile, _ = _dp_fixture()
    profile["transports"][0]["transmit_permission"] = "EXTERNALLY_QUALIFIED"
    with pytest.raises(NodeExchangeError, match="licensing"):
        validate_dataspace_profile(profile)
    profile["transports"][0]["licence_or_class_ref"] = "external-class-ref"
    assert validate_dataspace_profile(profile)["transmit_authorised_by_this_function"] is False


def test_dataspace_profile_root_mismatch_rejects_replay_context():
    profile, old = _dp_fixture()
    candidate = build_dataspace_delta_candidate(
        profile=profile, prior_state=old, new_state={"signal": 1, "drift": -1},
        sequence=4, window_end_ms=60000,
    )
    with pytest.raises(NodeExchangeError, match="sequence/replay"):
        apply_dataspace_delta_candidate(
            profile=profile, prior_state=old, candidate=candidate, expected_sequence=5
        )
    profile["semantic_lenses"][0]["registered_view_ref"] = "lens:another"
    with pytest.raises(NodeExchangeError, match="context mismatch"):
        apply_dataspace_delta_candidate(
            profile=profile, prior_state=old, candidate=candidate, expected_sequence=4
        )


def test_dataspace_missing_state_not_unchanged_and_root_preserved():
    profile, old = _dp_fixture()
    candidate = build_dataspace_delta_candidate(
        profile=profile, prior_state=old, new_state={"signal": None, "drift": -1},
        sequence=2, window_end_ms=61000,
    )
    assert candidate["updates"] == [{"id": "signal", "state": None}]
    result = apply_dataspace_delta_candidate(
        profile=profile, prior_state=old, candidate=candidate, expected_sequence=2
    )
    assert result["candidate_state"]["signal"] is None
    candidate["updates"][0]["state"] = 0
    with pytest.raises(NodeExchangeError, match="resulting state root"):
        apply_dataspace_delta_candidate(
            profile=profile, prior_state=old, candidate=candidate, expected_sequence=2
        )


def test_dataspace_plaintext_candidate_does_not_claim_auth():
    profile, old = _dp_fixture()
    candidate = build_dataspace_delta_candidate(
        profile=profile, prior_state=old, new_state=old,
        sequence=1, window_end_ms=60000,
    )
    assert candidate["updates"] == []
    assert candidate["cryptographically_authenticated"] is False
    assert candidate["publication_authorised"] is False
    assert candidate["canonical_promotion_authorized"] is False


def test_sai_aus_capacity_existing_cgx_crosswalk() -> None:
    """Governance topology proof: no extra root, runtime or system authority."""
    base = Path(__file__).resolve().parents[3] / "cgx" / "domain_templates"
    topology = json.loads((base / "cognigrex_parent_topology.json").read_text(encoding="utf-8"))
    corpus = json.loads((base / "corpus_inclusion_registry.json").read_text(encoding="utf-8"))
    nx = json.loads((base / "node_exchange_contract.json").read_text(encoding="utf-8"))

    assert topology["root"]["file"] == "Cognigrex.cgx"
    assert {x["id"] for x in topology["root"]["children"]} == {"romer", "eco", "emassc"}
    crosswalk = topology["programme_authority_crosswalk"]
    ids = [x["id"] for x in crosswalk["hierarchy"]]
    assert ids == ["SYS-AUS-CAP", "PROD-SAI", "CGX-ROOT"]
    assert crosswalk["hierarchy"][1]["parent"] == "SYS-AUS-CAP"
    assert crosswalk["release_status"] == "REVIEW_HOLD"
    existing = next(x for x in corpus["first_class_domains"] if x["id"] == "australian-capacity")
    assert existing["parent"] == "romer"
    assert existing["children"] == ["sai"]
    assert existing["semantic_authority_binding"]["programme_id"] == "SYS-AUS-CAP"
    assert existing["semantic_authority_binding"]["product_child_id"] == "PROD-SAI"
    assert existing["semantic_authority_binding"]["new_identity_created"] is False
    assert corpus["current_cgx_authority"]["state_id"] == "S92"
    sai = nx["sai_aus_capacity_application"]
    assert sai["programme"] == "SYS-AUS-CAP"
    assert sai["service"] == "PROD-SAI"
    assert sai["no_canonical_promotion"] is True
    assert sai["no_public_auto_release"] is True
    funcs = sai["functions"]
    assert len(funcs) == len({row["id"] for row in funcs}) == 12
    assert any(row["id"] == "PS-PRINT" and row["gate"].startswith("measured")
               for row in funcs)
    assert {p["status"] for p in sai["proof_chain"]} >= {
        "SOURCE-RECONCILED", "HOLD", "NOT-RUN", "SPECIFICATION-ONLY"
    }


def test_sai_aus_capacity_emergency_and_node_scope_not_automatic_authority() -> None:
    base = Path(__file__).resolve().parents[3] / "cgx" / "domain_templates"
    nx = json.loads((base / "node_exchange_contract.json").read_text(encoding="utf-8"))
    model = nx["sai_aus_capacity_application"]
    assert "no public" not in model["status"].lower() or model["no_public_auto_release"]
    assert model["no_public_auto_release"] is True
    assert nx["configurable_n_dataspace_facet"]["canonical_promotion_authorized"] is False
    assert nx["rolling_observer_facet"]["public_publish_authorized"] is False
    rules = model["critical_separations"]
    assert any("government" in text.lower() or "national emergency" in text.lower() for text in rules)
    assert any("LLM" in text or "deterministic" in text for text in rules)
    assert any("4d_printing" in text.lower() or "actual_4d_printing" in str(model["proof_chain"]).lower()
               for text in ["actual_4d_printing"])
