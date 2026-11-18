from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lightspeed_runtime.cgx_capability_registry import CapabilityRegistryError
from lightspeed_runtime.cgx_surface_projection import (
    build_unispace_surface_manifest, plan_temporary_subagent_batch,
)


def sample():
    surface = build_unispace_surface_manifest("LightSpeed")
    role = next(r["id"] for r in surface["roles"] if r["id"] == "neo")
    route = next(r["id"] for r in surface["routes"] if r["id"] == "cgx.plan_query")
    return surface, dict(
        selector="LightSpeed", task_id="TASK-123", run_id="RUN-1",
        expected_view_sha256=surface["source_view_sha256"],
        role_ids=[role], route_ids=[route],
    )


def test_surface_is_backend_generated_and_not_authority():
    surface, _ = sample()
    assert surface["route_count"] == len(surface["routes"])
    assert surface["route_count"] >= 30
    assert surface["roles"]
    assert not surface["execution_authorized"]
    assert not surface["native_mint_authorized"]
    assert surface["t174_zero"] == "reserved_nonmintable_sentinel"
    assert all(r["execution_enabled"] is False for r in surface["routes"])


def test_candidate_is_pinned_deterministic_and_non_executing():
    _, args = sample()
    a = plan_temporary_subagent_batch(**args)
    assert a == plan_temporary_subagent_batch(**args)
    assert len(a["candidate_sha256"]) == 64
    assert len(a["composition_ternary_root"]) == 64
    assert a["resource_envelope"]["cpu_threads_ceiling"] == 1
    assert a["resource_envelope"]["enforcement_state"] == "NOT_ACTIVATED"
    assert not any(a[k] for k in (
        "training_performed", "execution_performed", "native_mint_authorized",
        "db_mutated", "lease_verified", "source_acl_verified",
    ))


@pytest.mark.parametrize("change", [
    {"expected_view_sha256": "0" * 64},
    {"role_ids": ["neo", "neo"]},
    {"role_ids": ["unregistered"]},
    {"route_ids": ["physics.femm"]},
    {"route_ids": ["made.up"]},
    {"cpu_threads": 10000},
    {"memory_mib": 4096},
    {"max_jobs": 0},
    {"ttl_seconds": 86400},
    {"task_id": "../escape"},
    {"run_id": "bad id"},
])
def test_invalid_or_stale_candidates_hold(change):
    _, args = sample()
    args.update(change)
    with pytest.raises(CapabilityRegistryError):
        plan_temporary_subagent_batch(**args)


def test_gated_route_is_visible_but_never_enabled():
    surface, args = sample()
    args["route_ids"] = ["node.compute"]
    a = plan_temporary_subagent_batch(**args)
    assert a["route_states"]["node.compute"] == "gated"
    assert not a["execution_performed"]
    assert not surface["execution_authorized"]


def test_private_surface_and_batch_require_owner_session(tmp_path):
    from fastapi.testclient import TestClient
    from lightspeed_runtime.ls_go_bridge import create_app
    with TestClient(create_app(tmp_path)) as client:
        assert client.get("/api/v1/cgx/surface").status_code == 403
        assert client.get(
            "/api/v1/cgx/surface", headers={"X-LightSpeed-Session": "forged"}
        ).status_code == 403
        assert client.post(
            "/api/v1/cgx/temporary-batch/plan", json={}
        ).status_code == 403
