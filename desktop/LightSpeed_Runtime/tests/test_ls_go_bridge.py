from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime import ls_go_bridge
from lightspeed_runtime.project_pipeline import ProjectPipeline
from lightspeed_runtime.representation_edge import FEATURE_FLAG


def command_payload(**overrides):
    payload = {
        "schema_version": "lightspeed-go-command-v1",
        "command_id": "LSGO-TEST-001",
        "created_utc": "2026-07-19T00:00:00Z",
        "source": "LS GO",
        "title": "Test command",
        "instruction": "Create a reviewed implementation receipt.",
        "target_floor": "Smith",
        "oversight_floor": "Achilles",
        "priority": "normal",
        "execution_mode": "review",
        "proof_required": True,
        "public_safe": True,
    }
    payload.update(overrides)
    return payload


def configure_shell(root: Path) -> Path:
    (root / "config").mkdir(parents=True)
    (root / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports").mkdir(parents=True)
    project = root / "Z Axis" / "Z+1_Architect" / "projects" / "Project Alpha"
    project.mkdir(parents=True)
    (project / "README.md").write_text("# Project Alpha\n", encoding="utf-8")
    (project / "receipt.json").write_text('{"status":"pass"}\n', encoding="utf-8")
    (project / ".env").write_text("SECRET=not-copied\n", encoding="utf-8")
    config = {
        "project_roots": [
            {
                "root_id": "architect-canonical",
                "path": "Z Axis/Z+1_Architect/projects",
                "authority": "canonical",
                "writable": True,
            }
        ],
        "go_review": {
            "queue_path": "Z Axis/Z-4_Merovingian/data/runtime_exports/go_review_queue.jsonl",
            "decision_path": "Z Axis/Z-4_Merovingian/data/runtime_exports/go_review_decisions.jsonl",
            "allowed_decisions": ["approve", "hold", "reject"],
        },
        "drive_writeback": {
            "local_fallback_path": "Z Axis/Z-4_Merovingian/data/runtime_exports/drive_outbox",
            "max_artifact_files": 10,
            "max_artifact_total_bytes": 1048576,
            "max_single_artifact_bytes": 524288,
            "blocked_artifact_patterns": [".env", "*.pem", "*.key"],
        },
    }
    (root / "config" / "project_routing.json").write_text(json.dumps(config), encoding="utf-8")
    return project


def healthy_pipeline(monkeypatch) -> None:
    monkeypatch.setattr(
        ProjectPipeline,
        "essential_health",
        lambda self, registry: {
            "status": "pass",
            "services": {"database": True, "event_bus": True, "storage": True},
            "details": {"drive_writeback": {"path": str(self.runtime_exports), "mode": "test"}},
            "errors": [],
        },
    )


def write_supervisor_lock(root: Path, *, heartbeat: datetime | None = None, pid: int | None = None) -> None:
    runtime_exports = root / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports"
    runtime_exports.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "lightspeed-merovingian-supervisor-lock-v1",
        "pid": pid or os.getpid(),
        "heartbeat_utc": (heartbeat or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
        "interval_seconds": 60,
        "state": "pass",
    }
    (runtime_exports / "merovingian_supervisor.lock.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def test_status_requires_live_merovingian_supervisor(tmp_path, monkeypatch):
    configure_shell(tmp_path)
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (object(), object()))
    healthy_pipeline(monkeypatch)
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    missing = client.get("/api/v1/status").json()
    assert missing["ok"] is False
    assert missing["services"]["merovingian"] is False
    assert missing["merovingian"]["supervisor"]["alive"] is False

    write_supervisor_lock(tmp_path)
    live = client.get("/api/v1/status").json()
    assert live["ok"] is True
    assert live["services"] == {"db": True, "storage": True, "merovingian": True}
    assert live["merovingian"]["supervisor"]["reason"] == "live"
    assert "resources" in live
    assert "agent_floors" in live
    assert "root_resolution" in live["merovingian"]


def test_status_rejects_stale_supervisor_heartbeat(tmp_path, monkeypatch):
    configure_shell(tmp_path)
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (object(), object()))
    healthy_pipeline(monkeypatch)
    write_supervisor_lock(tmp_path, heartbeat=datetime.now(timezone.utc) - timedelta(minutes=10))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    body = client.get("/api/v1/status").json()
    assert body["ok"] is False
    assert body["merovingian"]["status"] == "unavailable"
    assert body["merovingian"]["supervisor"]["reason"] == "heartbeat_stale"


def test_bridge_persists_review_gated_command(tmp_path, monkeypatch):
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    response = client.post("/api/v1/ls-go/commands", json=command_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["state"] == "review"
    assert Path(body["artifact_ref"]).exists()


def test_bridge_rejects_command_without_achilles_oversight(tmp_path, monkeypatch):
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    response = client.post(
        "/api/v1/ls-go/commands",
        json=command_payload(oversight_floor="Neo"),
    )

    assert response.status_code == 400
    assert "Achilles oversight" in response.json()["detail"]


def test_bridge_stages_project_artifact_and_accepts_owner_review(tmp_path, monkeypatch):
    project_root = configure_shell(tmp_path)
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    healthy_pipeline(monkeypatch)
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    projects = client.get("/api/v1/projects")
    assert projects.status_code == 200
    project = projects.json()["projects"][0]
    assert project["name"] == "Project Alpha"
    assert project["authority"] == "canonical"

    queued = client.post(
        f"/api/v1/projects/{project['project_id']}/receipts",
        json={
            "summary": "Validated bounded project work.",
            "artifact_paths": ["receipt.json", ".env"],
        },
    )
    assert queued.status_code == 200
    body = queued.json()
    review_id = body["review"]["review_id"]
    manifest = body["artifact_manifest"]
    assert manifest["copied_count"] == 1
    assert manifest["skipped_count"] == 1
    assert manifest["copied"][0]["project_relative_path"] == "receipt.json"
    copied_path = Path(manifest["copied"][0]["destination_path"])
    assert copied_path.is_file()
    assert copied_path.read_text(encoding="utf-8") == (project_root / "receipt.json").read_text(encoding="utf-8")
    assert manifest["skipped"][0]["reason"] == "blocked_secret_or_credential_pattern"
    assert (project_root / ".env").is_file()

    reviews = client.get("/api/v1/reviews")
    assert reviews.status_code == 200
    assert reviews.json()["reviews"][0]["review_id"] == review_id

    decision = client.post(
        f"/api/v1/reviews/{review_id}/decision",
        json={"decision": "approve", "note": "Owner reviewed."},
    )
    assert decision.status_code == 200
    assert decision.json()["receipt"]["decision"] == "approve"


def test_bridge_rejects_unknown_project_and_skips_outside_path(tmp_path, monkeypatch):
    configure_shell(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    healthy_pipeline(monkeypatch)
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    unknown = client.post(
        "/api/v1/projects/not-known/receipts",
        json={"summary": "No project.", "artifact_paths": []},
    )
    assert unknown.status_code == 404

    project = client.get("/api/v1/projects").json()["projects"][0]
    response = client.post(
        f"/api/v1/projects/{project['project_id']}/receipts",
        json={"summary": "Outside path test.", "artifact_paths": [str(outside)]},
    )
    assert response.status_code == 200
    manifest = response.json()["artifact_manifest"]
    assert manifest["copied_count"] == 0
    assert manifest["skipped"][0]["reason"] == "outside_registered_project_root"
    assert outside.read_text(encoding="utf-8") == "outside"


def test_representation_edge_routes_are_disabled_by_default(tmp_path, monkeypatch):
    configure_shell(tmp_path)
    monkeypatch.delenv(FEATURE_FLAG, raising=False)
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    status = client.get("/api/v1/representation-edge/status")
    graphs = client.get("/api/v1/representation-graphs")

    assert status.status_code == 200
    assert status.json()["enabled"] is False
    assert graphs.status_code == 404
    assert not (tmp_path / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db").exists()


def test_representation_edge_api_renders_graphs_and_enforces_identity_first(tmp_path, monkeypatch):
    configure_shell(tmp_path)
    database = (
        tmp_path
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "db"
        / "lightspeed_unified.db"
    )
    database.parent.mkdir(parents=True)
    sqlite3.connect(database).close()
    monkeypatch.setenv(FEATURE_FLAG, "1")
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    graphs = client.get("/api/v1/representation-graphs")
    assert graphs.status_code == 200
    rows = graphs.json()["graphs"]
    assert {row["object"]["object_id"] for row in rows} == {
        "ASPHA.0001",
        "engineering-twin:rfs-emff-sandbox",
        "de-sporte-05d89c2a",
    }
    assert all("missing" in row and "conflicts" in row and "horizons" in row for row in rows)

    apophis = next(row for row in rows if row["object"]["object_id"] == "ASPHA.0001")
    review_id = apophis["review"]["review_id"]
    edge_id = apophis["edges"][0]["edge_id"]
    premature = client.post(
        f"/api/v1/representation-reviews/{review_id}/decision",
        json={
            "decision": "hold",
            "actor": "Nathaniel",
            "scope": "edges",
            "edge_ids": [edge_id],
        },
    )
    assert premature.status_code == 400

    identity = client.post(
        f"/api/v1/representation-reviews/{review_id}/decision",
        json={
            "decision": "provisional_approve",
            "actor": "Achilles",
            "scope": "identity",
            "note": "Candidate identity only.",
        },
    )
    assert identity.status_code == 200
    assert identity.json()["receipt"]["drive_write_executed"] is False

    edge = client.post(
        f"/api/v1/representation-reviews/{review_id}/decision",
        json={
            "decision": "request_evidence",
            "actor": "Nathaniel",
            "scope": "edges",
            "edge_ids": [edge_id],
            "note": "Stable workbook key required.",
        },
    )
    assert edge.status_code == 200

    promotions = client.get("/api/v1/representation-promotions").json()
    assert promotions["drive_write_executed"] is False
    assert promotions["readback_required"] is True
