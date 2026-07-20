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


def configure_shell(root: Path) -> None:
    (root / "config").mkdir(parents=True)
    (root / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports").mkdir(parents=True)
    (root / "Z Axis" / "Z+1_Architect" / "projects" / "Project Alpha").mkdir(parents=True)
    (root / "Z Axis" / "Z+1_Architect" / "projects" / "Project Alpha" / "README.md").write_text(
        "# Project Alpha\n", encoding="utf-8"
    )
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
            "local_fallback_path": "Z Axis/Z-4_Merovingian/data/runtime_exports/drive_outbox"
        },
    }
    (root / "config" / "project_routing.json").write_text(json.dumps(config), encoding="utf-8")


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


def test_bridge_lists_projects_and_accepts_owner_review(tmp_path, monkeypatch):
    configure_shell(tmp_path)
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
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
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    projects = client.get("/api/v1/projects")
    assert projects.status_code == 200
    project = projects.json()["projects"][0]
    assert project["name"] == "Project Alpha"
    assert project["authority"] == "canonical"

    queued = client.post(
        f"/api/v1/projects/{project['project_id']}/receipts",
        json={"summary": "Validated bounded project work.", "artifact_paths": ["receipt.json"]},
    )
    assert queued.status_code == 200
    review_id = queued.json()["review"]["review_id"]

    reviews = client.get("/api/v1/reviews")
    assert reviews.status_code == 200
    assert reviews.json()["reviews"][0]["review_id"] == review_id

    decision = client.post(
        f"/api/v1/reviews/{review_id}/decision",
        json={"decision": "approve", "note": "Owner reviewed."},
    )
    assert decision.status_code == 200
    assert decision.json()["receipt"]["decision"] == "approve"
