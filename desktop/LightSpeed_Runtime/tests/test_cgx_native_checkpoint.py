from __future__ import annotations

import json
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lightspeed_runtime.cgx_surface_projection import (
    build_unispace_surface_manifest, plan_temporary_subagent_batch,
)
from lightspeed_runtime.cgx_native_checkpoint import (
    NativeCheckpointError, host_checkpoint_store, persist_checkpoint,
    read_checkpoint, revoke_checkpoint,
)
from lightspeed_runtime.operational_store import (
    OperationalStore, default_operational_db_path,
)


def owner():
    return "verified-local-owner"


def candidate(task="task-123", run="run-123"):
    manifest = build_unispace_surface_manifest()
    return plan_temporary_subagent_batch(
        selector="LightSpeed", task_id=task, run_id=run,
        expected_view_sha256=manifest["source_view_sha256"],
        role_ids=["neo"], route_ids=["cgx.plan_query"],
        cpu_threads=1, memory_mib=128, max_jobs=2, ttl_seconds=600,
    )


def store(tmp_path):
    return OperationalStore(tmp_path / "lightspeed_unified.db")


def test_checkpoint_exact_readback_survives_reopen_without_second_database(tmp_path):
    db = store(tmp_path)
    payload = candidate()
    receipt = persist_checkpoint(db, payload, verify_owner=owner)
    assert receipt["native_metadata_persisted"] is True
    assert receipt["execution_enabled"] is False
    assert receipt["inserted"] is True
    recovered = read_checkpoint(OperationalStore(db.path), "task-123", "run-123",
                                verify_owner=owner)
    assert recovered["state"] == "REVIEW_ONLY"
    assert recovered["candidate_sha256"] == payload["candidate_sha256"]
    assert recovered["event_sha256"] == receipt["event_sha256"]
    with sqlite3.connect(db.path) as c:
        names = [x[0] for x in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )]
        assert "operational_events" in names
        assert "family" not in " ".join(names).lower()
        row = c.execute("SELECT payload_json FROM operational_events").fetchone()[0]
        assert "source_bytes" not in row
        assert "password" not in row


def test_exact_retry_idempotent_and_changed_content_rejected(tmp_path):
    db = store(tmp_path)
    payload = candidate()
    persist_checkpoint(db, payload, verify_owner=owner)
    assert persist_checkpoint(db, payload, verify_owner=owner)["inserted"] is False
    changed = candidate()
    changed["resource_envelope"]["ttl_seconds"] = 601
    import hashlib
    raw = {k:v for k,v in changed.items() if k != "candidate_sha256"}
    changed["candidate_sha256"] = hashlib.sha256(
        json.dumps(raw,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
    ).hexdigest()
    with pytest.raises(NativeCheckpointError, match="already binds"):
        persist_checkpoint(db, changed, verify_owner=owner)


def test_revoke_is_durable_and_prevents_reactivation(tmp_path):
    db = store(tmp_path)
    payload = candidate()
    persist_checkpoint(db, payload, verify_owner=owner)
    revoked = revoke_checkpoint(
        db, "task-123", "run-123", expected_candidate_sha256=payload["candidate_sha256"],
        verify_owner=owner,
    )
    assert revoked["state"] == "REVOKED"
    assert read_checkpoint(OperationalStore(db.path), "task-123", "run-123",
                           verify_owner=owner)["state"] == "REVOKED"
    with pytest.raises(NativeCheckpointError, match="revoked"):
        persist_checkpoint(db, payload, verify_owner=owner)


def test_ttl_does_not_extend_on_retry(tmp_path):
    db = store(tmp_path)
    payload = candidate()
    first = persist_checkpoint(db, payload, verify_owner=owner)
    expired = datetime.fromisoformat(first["created_utc"]) + timedelta(seconds=601)
    persist_checkpoint(db, payload, verify_owner=owner)
    readback = read_checkpoint(db, "task-123", "run-123",
                               verify_owner=owner, now=expired)
    assert readback["state"] == "EXPIRED"
    assert readback["created_utc"] == first["created_utc"]


def test_unauthenticated_or_changed_owner_fails(tmp_path):
    db = store(tmp_path)
    for verify in (None, lambda: "", lambda: None):
        with pytest.raises(PermissionError):
            persist_checkpoint(db, candidate(), verify_owner=verify)
    assert db.count(kind="cgx_temporary_checkpoint_review_v1") == 0
    calls = iter(["verified-owner", "different-owner"])
    with pytest.raises(PermissionError, match="changed"):
        persist_checkpoint(db, candidate(), verify_owner=lambda: next(calls))
    # Even if the session drops after the transaction, no execution authority
    # or source contents can be recovered from the metadata-only checkpoint.
    assert db.count(kind="cgx_temporary_checkpoint_review_v1") == 1


def test_tamper_and_elevated_candidate_held(tmp_path):
    db = store(tmp_path)
    payload = candidate()
    payload["native_mint_authorized"] = True
    with pytest.raises(NativeCheckpointError):
        persist_checkpoint(db, payload, verify_owner=owner)
    assert db.count(kind="cgx_temporary_checkpoint_review_v1") == 0
    original = candidate()
    persist_checkpoint(db, original, verify_owner=owner)
    with db._connect() as connection:
        connection.execute(
            "UPDATE operational_events SET payload_sha256=? WHERE kind=?",
            ("0"*64,"cgx_temporary_checkpoint_review_v1"),
        )
    with pytest.raises(NativeCheckpointError, match="integrity"):
        read_checkpoint(db, "task-123", "run-123", verify_owner=owner)


def test_gated_route_not_persistable(tmp_path):
    db = store(tmp_path)
    surface = build_unispace_surface_manifest()
    candidate_gated = plan_temporary_subagent_batch(
        selector="LightSpeed", task_id="t123", run_id="r123",
        expected_view_sha256=surface["source_view_sha256"],
        role_ids=["neo"], route_ids=["node.compute"],
    )
    with pytest.raises(NativeCheckpointError, match="gated or missing"):
        persist_checkpoint(db, candidate_gated, verify_owner=owner)


def test_wrong_revision_revoke_denied(tmp_path):
    db = store(tmp_path)
    persist_checkpoint(db, candidate(), verify_owner=owner)
    with pytest.raises(NativeCheckpointError, match="revision changed"):
        revoke_checkpoint(db, "task-123", "run-123",
                          expected_candidate_sha256="0"*64, verify_owner=owner)
    assert db.count(kind="cgx_temporary_checkpoint_revoke_v1") == 0


def test_host_store_uses_existing_canonical_db_only(tmp_path):
    with pytest.raises(NativeCheckpointError, match="unavailable"):
        host_checkpoint_store(tmp_path)
    path = default_operational_db_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not-a-database")
    with pytest.raises(NativeCheckpointError, match="probe unavailable"):
        host_checkpoint_store(tmp_path)
    path.unlink()
    OperationalStore(path)
    loaded = host_checkpoint_store(tmp_path)
    assert loaded.path == path


def test_scope_identity_prevents_cross_run_lookup(tmp_path):
    db = store(tmp_path)
    persist_checkpoint(db, candidate(), verify_owner=owner)
    with pytest.raises(NativeCheckpointError, match="not found"):
        read_checkpoint(db, "task-123", "run-124", verify_owner=owner)
    with pytest.raises(NativeCheckpointError, match="identities"):
        read_checkpoint(db, "../escape", "run-123", verify_owner=owner)


def test_http_checkpoint_bound_to_owner_session_existing_database(tmp_path, monkeypatch):
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    from lightspeed_runtime import ls_go_bridge

    class DummyDB:
        def execute_query(self, *args, **kwargs):
            return []
        def execute_update(self, *args, **kwargs):
            return 0

    monkeypatch.setattr(ls_go_bridge, "_try_get_services",
                        lambda root: (DummyDB(), object()))
    monkeypatch.setattr(ls_go_bridge, "CredentialStore", lambda db: object())

    def verify_owner(_confirmation, *, session_token=None, **kwargs):
        if session_token != "valid-test-session":
            raise HTTPException(status_code=403, detail="Session invalid")
        return "owner"

    monkeypatch.setattr(ls_go_bridge, "_verified_owner_actor", verify_owner)
    monkeypatch.setattr(ls_go_bridge, "_current_go_authority_contract",
        lambda root: {"approval_or_hold_state": "approved",
                      "authorised_scope": "private local review queue"})
    canonical_path = default_operational_db_path(tmp_path)
    OperationalStore(canonical_path)
    surface = build_unispace_surface_manifest()
    data = {
        "selector": "LightSpeed", "task_id": "test-123", "run_id": "run-123",
        "expected_view_sha256": surface["source_view_sha256"],
        "role_ids": ["neo"], "route_ids": ["cgx.plan_query"],
        "ttl_seconds": 600,
    }
    with TestClient(ls_go_bridge.create_app(tmp_path)) as client:
        url = "/api/v1/cgx/persistence/checkpoint"
        assert client.post(url, json=data).status_code == 403
        assert client.post(url, json=data,
                           headers={"X-LightSpeed-Session": "forged"}).status_code == 403
        headers = {"X-LightSpeed-Session": "valid-test-session"}
        monkeypatch.setattr(ls_go_bridge, "_current_go_authority_contract",
            lambda root: {"approval_or_hold_state": "held",
                          "authorised_scope": "none"})
        assert client.post(url, json=data, headers=headers).status_code == 403
        monkeypatch.setattr(ls_go_bridge, "_current_go_authority_contract",
            lambda root: {"approval_or_hold_state": "approved",
                          "authorised_scope": "private local review queue"})
        response = client.post(url, json=data, headers=headers)
        assert response.status_code == 200, response.text
        first = response.json()
        assert first["state"] == "REVIEW_ONLY"
        assert not first["execution_enabled"]
        assert first["native_metadata_persisted"]
        assert first["inserted"]
        readback = client.get(url + "/test-123/run-123", headers=headers)
        assert readback.status_code == 200
        assert readback.json()["candidate_sha256"] == first["candidate_sha256"]
        assert client.post(url, json=data, headers=headers).json()["inserted"] is False
        revoke = client.post("/api/v1/cgx/persistence/revoke/test-123/run-123",
                             json={"expected_candidate_sha256": first["candidate_sha256"]},
                             headers=headers)
        assert revoke.status_code == 200
        assert revoke.json()["state"] == "REVOKED"
        assert client.post(url, json=data, headers=headers).status_code == 409
