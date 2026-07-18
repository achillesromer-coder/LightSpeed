from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime import ls_go_bridge


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


def test_bridge_persists_review_gated_command(tmp_path, monkeypatch):
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    response = client.post("/api/v1/ls-go/commands", json=command_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["state"] == "review"
    assert Path(body["artifact_ref"]).exists()


def test_bridge_rejects_command_without_achilles_oversight(tmp_path, monkeypatch):
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    response = client.post(
        "/api/v1/ls-go/commands",
        json=command_payload(oversight_floor="Neo"),
    )

    assert response.status_code == 400
    assert "Achilles oversight" in response.json()["detail"]
