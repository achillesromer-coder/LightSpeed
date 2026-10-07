from pathlib import Path

import pytest

from lightspeed_runtime.cgx_view_policy import CGXViewPolicyError
from lightspeed_runtime.runtime import LightSpeedRuntime
from lightspeed_runtime.floor_bridges import TrinityShellBridge

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = "cgx://romer.industries/emassc"
OBJECTS = ["cgx:test:object-a", "cgx:test:object-b"]


def lease(**overrides):
    payload = {
        "admitted": True,
        "security_scope": "internal-operator",
        "evidence_ceiling": "derived-digital-verification",
        "allowed_views": ["network-runtime", "active-object-inspector", "timeline-dbr"],
        "allowed_object_ids": list(OBJECTS),
        "allowed_source_roots": [SOURCE_ROOT],
    }
    payload.update(overrides)
    return payload


def select(runtime, **overrides):
    kwargs = {
        "security_and_admission": lease(),
        "task_intent": "runtime",
        "active_object_domain_and_type": "lightspeed/runtime-node",
        "work_mode": "operate",
        "device_hydration_capability": "workstation",
        "role_or_audience": "operator",
        "source_root_binding": SOURCE_ROOT,
        "selected_subgraph": [OBJECTS[0]],
        "saved_profile_preferences": {},
        "session_override": {},
        "interaction_capabilities": ["inspect"],
    }
    kwargs.update(overrides)
    return runtime.select_cgx_view(**kwargs)


def test_runtime_selector_is_deterministic_and_non_mutating():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    assert select(runtime) == select(runtime)
    result = select(runtime)
    assert result["primary_view"] == "network-runtime"
    assert result["canonical_mutation"] is False
    assert result["evidence_ceiling"] == "derived-digital-verification"


def test_security_and_scope_fail_closed():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    with pytest.raises(CGXViewPolicyError, match="not admitted"):
        select(runtime, security_and_admission=lease(admitted=False))
    with pytest.raises(CGXViewPolicyError, match="exceeds admission lease"):
        select(runtime, selected_subgraph=["cgx:test:not-authorized"])
    with pytest.raises(CGXViewPolicyError, match="outside admission lease"):
        select(runtime, source_root_binding="cgx://unauthorized/root")


def test_preferences_cannot_raise_evidence_or_publish_scope():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    result = select(
        runtime,
        saved_profile_preferences={"primary_view": "publication", "evidence_ceiling": "empirical-pass"},
        session_override={"primary_view": "publication", "host_local_secret": "must-not-leak"},
    )
    assert result["primary_view"] == "network-runtime"
    assert result["evidence_ceiling"] == "derived-digital-verification"
    assert "must-not-leak" not in str(result)
    assert result["canonical_mutation"] is False


def test_hydration_limits_secondary_views_without_semantic_change():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    lite = select(runtime, device_hydration_capability="projection-lite")
    reader = select(runtime, device_hydration_capability="reader")
    assert lite["secondary_views"] == []
    assert reader["secondary_views"] == ["active-object-inspector"]


def test_trinity_consumes_runtime_view_policy():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    bridge = TrinityShellBridge(runtime)
    result = bridge.select_workspace_projection(
        security_and_admission=lease(),
        task_intent="runtime",
        active_object_domain_and_type="lightspeed/runtime-node",
        work_mode="operate",
        device_hydration_capability="reader",
        role_or_audience="operator",
        source_root_binding=SOURCE_ROOT,
        selected_subgraph=[OBJECTS[0]],
        saved_profile_preferences={"primary_view": "active-object-inspector"},
        interaction_capabilities=["inspect"],
    )
    assert result["primary_view"] == "active-object-inspector"
    assert result["canonical_mutation"] is False
