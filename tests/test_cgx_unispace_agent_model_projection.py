"""Agent/model source alignment over existing CGX identity; no new agent runtime."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from tools import cgx_unispace_agent_model_projection as model

ROOT = Path(__file__).resolve().parents[1]


def test_real_nine_selectors_and_three_existing_agent_owners():
    result = model.build(ROOT)
    assert result["canonical_root_id"] == "cgx:root:cognigrex"
    assert result["selector_count"] == 9
    assert result["principal_agent_count"] == 3
    assert len(result["source_refs"]) == 14
    roles = {
        row["selector"]: row["role"]["domain"]
        for row in result["selectors"] if row["role"] is not None
    }
    assert roles == {"neo": "romer", "athene": "eco", "achilles": "emassc"}
    assert all(row["facets_granted_by_projection"] == []
               and row["native_executed"] is False
               and row["provider_bound"] is False
               for row in result["selectors"])
    assert result["model_weights_changed"] is False
    assert result["model_training_executed"] is False
    assert result["agent_spawned"] is False
    assert result["execution_or_publication_authorized"] is False


def test_model_class_discovery_is_not_a_provider_inventory():
    result = model.build(ROOT)
    assert set(result["model_classes"]) == model.MODEL_CLASSES
    assert result["model_classes_are_declared_not_live_models"] is True
    assert result["model_provider_selection_requires_live_scope"] is True
    assert result["native_profile_handshake_verified"] is False
    assert result["native_dbr_authorized"] is False


def test_deterministic_projection_and_existing_facet_identity():
    first, second = model.build(ROOT), model.build(ROOT)
    assert first["source_projection_sha256"] == second["source_projection_sha256"]
    assert all(set(row["presentable_facets"]) == set(model.FACETS)
               for row in first["selectors"])


def test_missing_parent_or_untracked_source_fail_closed(monkeypatch):
    original = model._source

    def substituted(repo, rel, tracked):
        if rel == model.MAIN_CONTRACTS["domains"]:
            obj, proof = original(repo, rel, tracked)
            obj["parent_filespace"]["file"] = "CompetingRoot.cgx"
            return obj, proof
        return original(repo, rel, tracked)

    monkeypatch.setattr(model, "_source", substituted)
    with pytest.raises(model.AgentModelHold, match="canonical source"):
        model.build(ROOT)
    monkeypatch.setattr(model, "_source", original)
    with pytest.raises(model.AgentModelHold, match="unqualified reference"):
        model._source(ROOT, "../../private/model-weights", set())


def test_agent_identity_cannot_be_duplicate_or_self_claimed(monkeypatch):
    original = model._source

    def substituted(repo, rel, tracked):
        obj, proof = original(repo, rel, tracked)
        if rel == model.MAIN_CONTRACTS["domains"]:
            obj["domains"]["eco"]["principal_agent"] = "Neo"
        return obj, proof

    monkeypatch.setattr(model, "_source", substituted)
    with pytest.raises(model.AgentModelHold, match="ambiguous"):
        model.build(ROOT)


def test_runtime_contract_denies_missing_lease_and_identity_separation(monkeypatch):
    original = model._source

    def substituted(repo, rel, tracked):
        obj, proof = original(repo, rel, tracked)
        if rel == model.MAIN_CONTRACTS["agent_runtime"]:
            obj["execution_lease"]["default_on_missing"] = "EXECUTE"
        return obj, proof

    monkeypatch.setattr(model, "_source", substituted)
    with pytest.raises(model.AgentModelHold):
        model.build(ROOT)


def test_model_classes_cannot_be_fabricated(monkeypatch):
    original = model._source

    def substituted(repo, rel, tracked):
        obj, proof = original(repo, rel, tracked)
        if rel == model.MAIN_CONTRACTS["agent_runtime"]:
            obj["model_binding"]["allowed"].append("self-authorizing-supermodel")
        return obj, proof

    monkeypatch.setattr(model, "_source", substituted)
    with pytest.raises(model.AgentModelHold, match="model classes"):
        model.build(ROOT)


def test_plugin_package_cannot_switch_agent_or_routes(monkeypatch):
    original = model._source

    def substituted(repo, rel, tracked):
        obj, proof = original(repo, rel, tracked)
        if rel == "plugins/packages/neo/references/capabilities.json":
            obj["selector"] = "achilles"
        return obj, proof

    monkeypatch.setattr(model, "_source", substituted)
    with pytest.raises(model.AgentModelHold, match="selector source identity"):
        model.build(ROOT)


def test_wrong_plugin_shortcall_cannot_claim_unregistered_route(monkeypatch):
    original = model._source

    def substituted(repo, rel, tracked):
        obj, proof = original(repo, rel, tracked)
        if rel == "plugins/packages/neo/references/capabilities.json":
            obj["profile"]["shortcalls"]["run"] = "unregistered.superuser"
        return obj, proof

    monkeypatch.setattr(model, "_source", substituted)
    with pytest.raises(model.AgentModelHold, match="stale selector"):
        model.build(ROOT)


def test_route_state_drift_is_visible_as_frontier_not_native_qualification(monkeypatch):
    original = model._source

    def substituted(repo, rel, tracked):
        obj, proof = original(repo, rel, tracked)
        if rel == "plugins/packages/neo/references/capabilities.json":
            obj["routes"]["cgx.resolve_context"]["state"] = "gated"
        return obj, proof

    monkeypatch.setattr(model, "_source", substituted)
    result = model.build(ROOT)
    assert any(f["selector"] == "neo"
               and f["route_id"] == "cgx.resolve_context"
               for f in result["routing_frontier"])
    assert result["native_dbr_authorized"] is False


def test_untrusted_read_only_source_is_rejected(monkeypatch):
    original = model._source

    def substituted(repo, rel, tracked):
        obj, proof = original(repo, rel, tracked)
        if rel == model.MAIN_CONTRACTS["technology_stack"]:
            obj["layers"] = [x for x in obj["layers"] if x["id"] != "L13"]
        return obj, proof

    monkeypatch.setattr(model, "_source", substituted)
    with pytest.raises(model.AgentModelHold, match="model/agent/safety"):
        model.build(ROOT)
