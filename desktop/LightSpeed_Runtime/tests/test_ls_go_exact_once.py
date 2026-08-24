from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from fastapi.testclient import TestClient

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime import ls_go_bridge


def command_payload(**overrides):
    payload = {
        "schema_version": "lightspeed-go-command-v1",
        "command_id": "LSGO-EXACT-ONCE-001",
        "created_utc": "2026-08-17T00:00:00Z",
        "source": "LS GO",
        "title": "Exact-once bridge proof",
        "instruction": "Persist this bounded reviewed command exactly once.",
        "target_floor": "Smith",
        "oversight_floor": "Achilles",
        "priority": "normal",
        "execution_mode": "review",
        "proof_required": True,
        "public_safe": True,
    }
    payload.update(overrides)
    return payload


def queue_rows(root: Path) -> list[dict]:
    path = ls_go_bridge._queue_path(root)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class FakeDb:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE tasks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "title TEXT, description TEXT, project_id TEXT, status TEXT, priority TEXT, "
            "created_at TEXT, updated_at TEXT, metadata_json TEXT)"
        )
        self.jobs: list[dict] = []

    def get_connection(self):
        return self.conn

    def create_job_v1(self, **kwargs):
        self.jobs.append(kwargs)
        return {"job_id": len(self.jobs)}


def test_same_command_envelope_is_idempotent_without_second_queue_append(tmp_path, monkeypatch):
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    first = client.post("/api/v1/ls-go/commands", json=command_payload())
    second = client.post("/api/v1/ls-go/commands", json=command_payload())

    assert first.status_code == 200
    assert first.json()["duplicate"] is False
    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert second.json()["accepted_utc"] == first.json()["accepted_utc"]
    rows = queue_rows(tmp_path)
    assert len(rows) == 1
    assert rows[0]["command_id"] == "LSGO-EXACT-ONCE-001"


def test_same_command_id_with_changed_envelope_is_conflict_without_mutation(tmp_path, monkeypatch):
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    first = client.post("/api/v1/ls-go/commands", json=command_payload())
    conflict = client.post(
        "/api/v1/ls-go/commands",
        json=command_payload(instruction="A materially different instruction."),
    )

    assert first.status_code == 200
    assert conflict.status_code == 409
    assert "different normalized envelope" in conflict.json()["detail"]
    rows = queue_rows(tmp_path)
    assert len(rows) == 1
    assert rows[0]["instruction"] == "Persist this bounded reviewed command exactly once."


def test_duplicate_request_does_not_create_second_database_task_or_job(tmp_path, monkeypatch):
    fake_db = FakeDb()
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (fake_db, object()))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    first = client.post("/api/v1/ls-go/commands", json=command_payload())
    second = client.post("/api/v1/ls-go/commands", json=command_payload())

    assert first.status_code == 200
    assert first.json()["task_id"] is not None
    assert first.json()["job"]["job_id"] == 1
    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert second.json()["task_id"] is None
    assert second.json()["job"] is None
    task_count = fake_db.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    assert task_count == 1
    assert len(fake_db.jobs) == 1
    assert len(queue_rows(tmp_path)) == 1


def test_typed_v2_action_reaches_durable_job_params(tmp_path, monkeypatch):
    fake_db = FakeDb()
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (fake_db, object()))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    response = client.post(
        "/api/v1/ls-go/commands",
        json=command_payload(
            schema_version="lightspeed-go-command-v2",
            command_id="LSGO-V2-EXACT-001",
            action_type="cognigrex_workflow",
            execution_mode="queue",
            target_floor="Neo",
        ),
    )

    assert response.status_code == 200
    assert fake_db.jobs[0]["params"]["action_type"] == "cognigrex_workflow"
    assert fake_db.jobs[0]["params"]["execute"] is True
