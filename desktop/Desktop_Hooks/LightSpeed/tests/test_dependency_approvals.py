from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.dependency_approvals import (
    build_compact_tool_status_descriptors,
    build_dependency_approval_queue,
    read_dependency_approval_queue,
    write_dependency_approval_queue,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_dependency_queue_captures_missing_tools_and_libraries(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "config" / "settings.json",
        {
            "apis_enabled": {
                "qr": True,
                "tol": True,
                "weather": False,
                "ollama": True,
                "openai": False,
                "google_drive_bridge": True,
            }
        },
    )
    _write_json(
        tmp_path / "config" / "ai_config.json",
        {
            "achilles": {"enabled": True},
            "active_backend": "ollama_local",
            "backends": {"ollama_local": {"enabled": True}},
        },
    )
    _write_json(
        tmp_path / "config" / "function_registry.json",
        {
            "libraries": {
                "numpy": {"available": True, "description": "Numerical computing"},
                "pandera": {"available": False, "description": "DataFrame schema validation"},
                "great_expectations": {"available": False, "description": "Data quality checks"},
            }
        },
    )

    queue = build_dependency_approval_queue(tmp_path)

    assert queue["missing_library_count"] == 2
    assert queue["missing_tool_count"] == 2
    assert any(item["kind"] == "library" for item in queue["approval_queue"])
    assert any(item["kind"] == "api" for item in queue["approval_queue"])
    assert all(item["status"] == "approval_required" for item in queue["approval_queue"])
    assert queue["ai_backend_status"]["kind"] == "ai_backend"
    assert queue["ai_backend_status"]["status"] == "available"


def test_compact_tool_status_descriptors_reflect_api_and_library_state(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "config" / "settings.json",
        {"apis_enabled": {"weather": False, "ollama": True, "openai": False}},
    )
    _write_json(
        tmp_path / "config" / "ai_config.json",
        {
            "backends": {
                "ollama_local": {"label": "Local Ollama", "enabled": True, "type": "ollama"},
                "remote_api": {"label": "Remote API", "enabled": False, "type": "api"},
            }
        },
    )
    _write_json(
        tmp_path / "config" / "function_registry.json",
        {"libraries": {"sklearn": {"available": False, "description": "ML toolkit"}}},
    )

    descriptors = build_compact_tool_status_descriptors(tmp_path)

    assert any(
        item["kind"] == "api" and item["name"] == "weather" and item["action"] == "queue_approval"
        for item in descriptors
    )
    assert any(item["kind"] == "ai_backend" and item["name"] == "ollama_local" for item in descriptors)
    assert any(item["kind"] == "library" and item["status"] == "missing" for item in descriptors)


def test_dependency_queue_round_trips_to_json(tmp_path: Path) -> None:
    _write_json(tmp_path / "config" / "settings.json", {"apis_enabled": {}})
    _write_json(tmp_path / "config" / "ai_config.json", {})
    _write_json(tmp_path / "config" / "function_registry.json", {"libraries": {}})
    out = tmp_path / "dependency_approvals.json"

    payload = write_dependency_approval_queue(tmp_path, out)
    stored = read_dependency_approval_queue(tmp_path, out)

    assert out.exists()
    assert stored["owner_floor"] == "Trinity"
    assert payload["path"] == str(out)
