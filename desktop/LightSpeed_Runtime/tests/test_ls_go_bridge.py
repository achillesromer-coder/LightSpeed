from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime import ls_go_bridge
from lightspeed_runtime.project_pipeline import ProjectPipeline


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
