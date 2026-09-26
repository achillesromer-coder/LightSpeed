from __future__ import annotations

from pathlib import Path

import pytest

from lightspeed_runtime.cgx_view_policy import CGXViewPolicyError
from lightspeed_runtime.runtime import LightSpeedRuntime


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


def select(runtime: LightSpeedRuntime, **overrides):
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
        "z_depth": 2,
        "filters": {"state": "active"},
        "units": "SI",
        "layout": "operator",
        "interaction_capabilities": ["inspect"],
    }
    kwargs.update(overrides)
    return runtime.select_cgx_view(**kwargs)


def test_runtime_selector_is_deterministic_and_non_mutating():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    first = select(runtime)
    second = select(runtime)
    assert first == second
    assert first["primary_view"] == "network-runtime"
    assert first["canonical_mutation"] is False
    assert first["selected_subgraph"] == [OBJECTS[0]]
    assert first["security_scope"] == "internal-operator"
    assert first["evidence_ceiling"] == "derived-digital-verification"
    assert first["source_root_binding"] == SOURCE_ROOT


def test_security_admission_is_fail_closed():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    with pytest.raises(CGXViewPolicyError, match="not admitted"):
        select(runtime, security_and_admission=lease(admitted=False))


def test_unauthorized_object_scope_is_rejected():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    with pytest.raises(CGXViewPolicyError, match="exceeds admission lease"):
        select(runtime, selected_subgraph=["cgx:test:not-authorized"])


def test_unauthorized_source_root_is_rejected():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    with pytest.raises(CGXViewPolicyError, match="outside admission lease"):
        select(runtime, source_root_binding="cgx://unauthorized/root")


def test_saved_preference_outranks_session_but_only_inside_admitted_views():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    result = select(
        runtime,
        saved_profile_preferences={"primary_view": "timeline-dbr"},
        session_override={"primary_view": "active-object-inspector"},
    )
    assert result["primary_view"] == "timeline-dbr"
    assert "session_override.primary_view_lower_priority_than_saved_profile" in result["preference_rejections"]


def test_disallowed_preference_cannot_expand_view_scope_or_evidence_ceiling():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    result = select(
        runtime,
        saved_profile_preferences={
            "primary_view": "publication",
            "evidence_ceiling": "empirical-pass",
        },
        session_override={"primary_view": "publication", "selected_subgraph": ["cgx:test:not-authorized"]},
    )
    assert result["primary_view"] == "network-runtime"
    assert result["evidence_ceiling"] == "derived-digital-verification"
    assert result["selected_subgraph"] == [OBJECTS[0]]
    assert "saved_profile_preferences.primary_view" in result["preference_rejections"]
    assert "empirical-pass" not in str(result)


def test_projection_lite_reduces_fidelity_without_changing_semantics():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    result = select(runtime, device_hydration_capability="projection-lite")
    assert result["primary_view"] == "network-runtime"
    assert result["secondary_views"] == []
    assert result["selected_subgraph"] == [OBJECTS[0]]
    assert result["evidence_ceiling"] == "derived-digital-verification"


def test_reader_limits_secondary_projection_to_one():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    result = select(runtime, device_hydration_capability="reader")
    assert result["secondary_views"] == ["active-object-inspector"]


def test_host_local_session_payload_does_not_enter_projection():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    result = select(
        runtime,
        session_override={
            "primary_view": "active-object-inspector",
            "host_local_secret": "must-not-leak",
            "canonical_mutation": True,
        },
    )
    assert result["primary_view"] == "active-object-inspector"
    assert result["canonical_mutation"] is False
    assert "host_local_secret" not in result
    assert "must-not-leak" not in str(result)


def test_no_admitted_view_for_task_fails_closed():
    runtime = LightSpeedRuntime(RUNTIME_ROOT)
    with pytest.raises(CGXViewPolicyError, match="no admitted view"):
        select(
            runtime,
            security_and_admission=lease(allowed_views=["publication"]),
        )
