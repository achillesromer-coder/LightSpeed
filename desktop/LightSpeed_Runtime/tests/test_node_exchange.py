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
    assert model["no_public_auto_release"] is True
    assert nx["configurable_n_dataspace_facet"]["canonical_promotion_authorized"] is False
    assert nx["rolling_observer_facet"]["public_publish_authorized"] is False
    rules = model["critical_separations"]
    assert any("government" in text.lower() or "national emergency" in text.lower() for text in rules)
    assert any("LLM" in text or "deterministic" in text for text in rules)
    assert any(row["proof"] == "actual_4d_printing_equipment" and row["status"] == "NOT-RUN"
               for row in model["proof_chain"])



from lightspeed_runtime.node_exchange import (
    PRISM_SLICE_FACET,
    PRISM_HANDSHAKE_FACET,
    validate_prism_slice_profile,
    negotiate_prism_device_candidate,
    resolve_prism_interpretation_candidate,
)


def _prism_fixture():
    import hashlib

    def h(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    return {
        "schema_version": PRISM_SLICE_FACET,
        "object_id": "CGX/DOOM/TEST/PRISM",
        "source_root": h("freedoom/source"),
        "geometry_root": h("freedoom/geometry"),
        "semantic_root": h("freedoom/semantics"),
        "model_root": h("freedoom/model"),
        "layers": [
            {"id": "whole", "parent_id": None, "visibility": "public",
             "source_ref": "freedoom-verified-iwad", "geometry_ref": "wad-lump-tree",
             "owner_ref": "freedoom-upstream", "content_root": h("whole")},
            {"id": "slice", "parent_id": "whole", "visibility": "public",
             "source_ref": "freedoom-static-shard", "geometry_ref": "geometry-2d-slice",
             "owner_ref": "freedoom-upstream", "content_root": h("slice")},
            {"id": "private", "parent_id": "whole", "visibility": "private",
             "source_ref": "private-model", "geometry_ref": "private-geometry",
             "owner_ref": "external-owner", "content_root": h("private")},
        ],
        "interpretations": [
            {"id": "text", "layer_id": "slice", "render_kind": "text",
             "registered_view_ref": "filespace-tree", "language_ref": "en-AU",
             "operation": "identity", "input_keys": ["symbol"], "unit": "unitless"},
            {"id": "metric", "layer_id": "slice", "render_kind": "metric",
             "registered_view_ref": "evidence-claim", "language_ref": "en-AU",
             "operation": "span", "input_keys": ["a", "b"], "unit": "m"},
            {"id": "ratio", "layer_id": "slice", "render_kind": "graph",
             "registered_view_ref": "topology-graph", "language_ref": "en-AU",
             "operation": "ratio", "input_keys": ["a", "b"], "unit": "ratio"},
            {"id": "restricted", "layer_id": "private", "render_kind": "text",
             "registered_view_ref": "evidence-claim", "language_ref": "en-AU",
             "operation": "identity", "input_keys": ["symbol"], "unit": "none"},
        ],
    }


def _prism_device(profile: dict, **overrides):
    import hashlib

    cache = [r["content_root"] for r in profile["layers"][:2]]
    offer = {
        "device_type": "android_touch",
        "render_kinds": ["text", "metric"],
        "requested_interpretations": ["text", "metric", "ratio", "restricted", "unknown"],
        "cached_content_roots": cache,
        "max_layers": 15,
        "static_profile_root": validate_prism_slice_profile(profile)["static_profile_root"],
    }
    offer.update(overrides)
    return offer


def test_prism_multi_layer_mobile_and_desktop():
    p = _prism_fixture()
    result = validate_prism_slice_profile(p)
    assert result["layer_count"] == 3 and result["interpretation_count"] == 4
    mobile = negotiate_prism_device_candidate(profile=p, device_offer=_prism_device(p))
    assert mobile["schema_version"] == PRISM_HANDSHAKE_FACET
    assert mobile["input_hint"] == "touch"
    assert [x["status"] for x in mobile["resolution"]] == [
        "RESOLVABLE_CANDIDATE", "RESOLVABLE_CANDIDATE",
        "UNSUPPORTED_RENDERER", "NOT_AVAILABLE", "NOT_AVAILABLE",
    ]
    assert mobile["entitlement_verified"] is False
    desktop = negotiate_prism_device_candidate(
        profile=p, device_offer=_prism_device(
            p, device_type="desktop_browser", render_kinds=["text", "graph"],
            requested_interpretations=["ratio", "text"]))
    assert desktop["input_hint"] == "keyboard_or_machine"
    assert [x["status"] for x in desktop["resolution"]] == [
        "RESOLVABLE_CANDIDATE", "RESOLVABLE_CANDIDATE"
    ]
    assert mobile["static_profile_root"] == desktop["static_profile_root"]


def test_prism_interpretation_deterministic_and_unknown():
    p = _prism_fixture()
    handshake = negotiate_prism_device_candidate(profile=p, device_offer=_prism_device(p))
    a = resolve_prism_interpretation_candidate(
        profile=p, handshake=handshake, interpretation_id="metric",
        inputs={"a": 21, "b": 6})
    assert a["value"] == 15 and a["unit"] == "m"
    assert a["status"] == "DERIVED_LOCAL_CANDIDATE"
    assert a["authenticated"] is False and a["source_verified"] is False
    missing = resolve_prism_interpretation_candidate(
        profile=p, handshake=handshake, interpretation_id="metric", inputs={"a": 3})
    assert missing["status"] == "UNKNOWN_INPUT"
    denied = resolve_prism_interpretation_candidate(
        profile=p, handshake=handshake, interpretation_id="restricted", inputs={"symbol": 2})
    absent = resolve_prism_interpretation_candidate(
        profile=p, handshake=handshake, interpretation_id="unknown", inputs={})
    assert denied == absent == {
        "status": "NOT_AVAILABLE", "canonical_promotion_authorized": False
    }


def test_prism_context_mismatch_and_missing_static_asset():
    p = _prism_fixture()
    bad = _prism_device(p, static_profile_root="0" * 64)
    result = negotiate_prism_device_candidate(profile=p, device_offer=bad)
    assert all(x == {"status": "RECONCILE_REQUIRED"} for x in result["resolution"])
    no_cache = _prism_device(p, cached_content_roots=[])
    result = negotiate_prism_device_candidate(profile=p, device_offer=no_cache)
    assert result["resolution"][0]["status"] == "NOT_CACHED"
    assert result["resolution"][0]["requires_source_hydration"] is True
    with pytest.raises(NodeExchangeError, match="prior handshake"):
        resolve_prism_interpretation_candidate(
            profile=p, handshake={**result, "static_profile_root": "0" * 64},
            interpretation_id="text", inputs={"symbol": 2})


def test_prism_parent_cycle_or_unregistered_operation_rejected():
    p = _prism_fixture()
    p["layers"][0]["parent_id"] = "slice"
    with pytest.raises(NodeExchangeError, match="cyclic"):
        validate_prism_slice_profile(p)
    p = _prism_fixture()
    p["interpretations"][0]["operation"] = "eval"
    with pytest.raises(NodeExchangeError, match="safe list"):
        validate_prism_slice_profile(p)


@pytest.mark.parametrize("n", [1, 3, 15, 52, 128])
def test_prism_n_layers_are_not_forced_to_nine(n):
    p = _prism_fixture()
    # Retain one public root and N-1 children, with one interpretation per layer.
    import hashlib
    public = p["layers"][0]
    layers = [public]
    for i in range(1, n):
        layers.append({
            "id": f"slice-{i}", "parent_id": "whole", "visibility": "public",
            "source_ref": "source", "geometry_ref": "prism-frame",
            "owner_ref": "registered-owner",
            "content_root": hashlib.sha256(f"slice-{i}".encode()).hexdigest(),
        })
    p["layers"] = layers
    p["interpretations"] = [
        {"id": "view", "layer_id": layers[-1]["id"], "render_kind": "text",
         "registered_view_ref": "filespace-tree", "language_ref": "en-AU",
         "operation": "identity", "input_keys": ["v"], "unit": "unitless"},
    ]
    info = validate_prism_slice_profile(p)
    assert info["layer_count"] == n
    handshake = negotiate_prism_device_candidate(
        profile=p, device_offer=_prism_device(
            p, requested_interpretations=["view"],
            cached_content_roots=[r["content_root"] for r in layers],
            max_layers=n))
    assert handshake["resolution"][0]["status"] == "RESOLVABLE_CANDIDATE"


def test_prism_ratio_zero_is_undefined_not_encoded_message():
    p = _prism_fixture()
    hs = negotiate_prism_device_candidate(
        profile=p, device_offer=_prism_device(
            p, render_kinds=["graph"], requested_interpretations=["ratio"]))
    assert resolve_prism_interpretation_candidate(
        profile=p, handshake=hs, interpretation_id="ratio", inputs={"a": 52, "b": 0}
    )["status"] == "UNDEFINED_OPERATION"
    assert resolve_prism_interpretation_candidate(
        profile=p, handshake=hs, interpretation_id="ratio", inputs={"a": 52, "b": 4}
    )["value"] == 13



def test_prism_rejects_public_child_of_private_parent_and_malformed_cache():
    p = _prism_fixture()
    p["layers"][1]["parent_id"] = "private"
    with pytest.raises(NodeExchangeError, match="protected parent"):
        validate_prism_slice_profile(p)
    p = _prism_fixture()
    with pytest.raises(NodeExchangeError, match="cache declaration"):
        negotiate_prism_device_candidate(
            profile=p, device_offer=_prism_device(p, cached_content_roots=[{}])
        )
    with pytest.raises(NodeExchangeError, match="render capabilities"):
        negotiate_prism_device_candidate(
            profile=p, device_offer=_prism_device(p, render_kinds=[{}])
        )


from lightspeed_runtime.node_exchange import (
    ALEXANDRIA_FRAME_SCHEMA,
    CGX_GEOMETRIC_CELL_SCHEMA,
    build_geometric_cell_candidate,
    build_alexandria_dodecahedron_candidate,
)


def test_alexandria_dodecahedron_has_closed_dual_topology():
    first = build_alexandria_dodecahedron_candidate(object_id="CGX/UNISPACE/ALEXANDRIA")
    second = build_alexandria_dodecahedron_candidate(object_id="CGX/UNISPACE/ALEXANDRIA")
    assert first == second
    assert first["schema_version"] == ALEXANDRIA_FRAME_SCHEMA
    assert (first["vertex_count"], first["edge_count"], first["face_count"]) == (20, 30, 12)
    assert first["topology_euler"] == 2
    assert first["triangulated_surface_candidate_count"] == 36
    assert len(first["vertices"]) == 20 and len(first["faces"]) == 12
    assert len({tuple(e) for e in first["edges"]}) == 30
    assert all(len(face) == 5 and len(set(face)) == 5 for face in first["faces"])
    edge_incidence = {}
    for face in first["faces"]:
        for idx in range(5):
            edge = tuple(sorted((face[idx], face[(idx + 1) % 5])))
            edge_incidence[edge] = edge_incidence.get(edge, 0) + 1
    assert len(edge_incidence) == 30
    assert all(count == 2 for count in edge_incidence.values())
    assert set(edge_incidence) == {tuple(e) for e in first["edges"]}
    assert len(first["cells"]) == 12
    assert {item["state"] for item in first["cells"]} == {"NEUTRAL_UNBOUND"}
    assert first["source_items_present"] == 0
    assert first["reference_radius_physical_m"] is None
    assert first["authenticated"] is False


def test_cgx_geometric_press_square_is_planar_until_extruded():
    square = build_geometric_cell_candidate(object_id="CGX/PERSONAL/FOUR", sides=4, edge_length=2)
    assert square["schema_version"] == CGX_GEOMETRIC_CELL_SCHEMA
    assert square["vertices"] == [[0.0, 0.0], [2.0, 0.0], [2.0, 2.0], [0.0, 2.0]]
    assert square["area_m2"] == 4
    assert square["perimeter_m"] == 8
    assert square["volume_m3"] is None
    assert square["observed_capacity"] is None
    assert square["canonical_promotion_authorized"] is False
    assert build_geometric_cell_candidate(
        object_id="CGX/PERSONAL/FOUR", sides=4, edge_length=2
    )["geometry_root"] == square["geometry_root"]
    extruded = build_geometric_cell_candidate(
        object_id="CGX/PERSONAL/FOUR", sides=4, edge_length=2, extrusion_depth=3
    )
    assert extruded["volume_m3"] == 12
    assert extruded["geometry_root"] != square["geometry_root"]


@pytest.mark.parametrize("sides", [3, 4, 5, 8, 12, 128])
def test_cgx_geometric_press_regular_n_polygon(sides):
    import math

    profile = build_geometric_cell_candidate(
        object_id=f"CGX/PRESS/{sides}", sides=sides, edge_length=1
    )
    assert profile["side_count"] == sides
    assert len(profile["vertices"]) == sides
    assert profile["area_m2"] == pytest.approx(sides / (4 * math.tan(math.pi / sides)))
    assert profile["volume_m3"] is None


def test_cgx_geometric_press_edits_state_held_and_reversible():
    base = build_geometric_cell_candidate(object_id="CGX/FOUR")
    amended = build_geometric_cell_candidate(
        object_id="CGX/FOUR", vertices=[[0, 0], [3, 0], [3, 1], [0, 1]],
        cell_states={"child-a": "OCCUPIED", "child-b": "NEUTRAL_UNBOUND",
                     "child-c": "UNKNOWN", "child-d": "WITHHELD"},
    )
    assert amended["area_m2"] == 3
    assert amended["perimeter_m"] == 8
    assert amended["geometry_root"] != base["geometry_root"]
    assert amended["cell_states"]["child-c"] == "UNKNOWN"
    assert amended["cell_states"]["child-d"] == "WITHHELD"
    assert amended["authentication_authorized"] is False
    roundtrip = build_geometric_cell_candidate(
        object_id=amended["object_id"], sides=amended["side_count"],
        vertices=amended["vertices"], cell_states=amended["cell_states"]
    )
    assert roundtrip["geometry_root"] == amended["geometry_root"]


@pytest.mark.parametrize("kwargs,match", [
    ({"sides": 2}, "3..128"),
    ({"sides": True}, "3..128"),
    ({"vertices": [[0, 0], [1, 1], [0, 1], [1, 0]]}, "self-intersection"),
    ({"vertices": [[0, 0], [1, 0], [1, 0], [0, 1]]}, "zero-length"),
    ({"sides": 3, "vertices": [[0, 0], [1, 0], [2, 0]]}, "degenerate"),
    ({"vertices": [[0, 0], [1, 0], [1, 1]]}, "count"),
    ({"extrusion_depth": 0}, "positive"),
    ({"cell_states": {"child": "WITHHELD_AS_EMPTY"}}, "state/identifier"),
    ({"edge_length": float("inf")}, "finite"),
])
def test_cgx_geometric_press_rejects_invalid_and_private_state_confusion(kwargs, match):
    with pytest.raises(NodeExchangeError, match=match):
        build_geometric_cell_candidate(object_id="CGX/PRESS/NEGATIVE", **kwargs)
