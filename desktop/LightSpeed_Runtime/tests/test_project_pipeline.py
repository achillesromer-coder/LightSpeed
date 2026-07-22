from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

import lightspeed_runtime.project_pipeline as project_pipeline
from lightspeed_runtime.project_pipeline import FLOOR_ROOTS, ProjectPipeline


@pytest.fixture(autouse=True)
def isolate_external_project_roots(monkeypatch):
    """Keep host project routing from leaking into temporary test shells."""
    monkeypatch.delenv("LIGHTSPEED_PROJECT_ROOTS", raising=False)


def test_json_write_retries_transient_windows_lock(tmp_path, monkeypatch):
    target = tmp_path / "health.json"
    original_replace = Path.replace
    attempts = {"count": 0}

    def transient_lock(path, destination):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise PermissionError("simulated reader lock")
        return original_replace(path, destination)

    monkeypatch.setattr(Path, "replace", transient_lock)
    monkeypatch.setattr(project_pipeline.time, "sleep", lambda _seconds: None)

    project_pipeline._write_json(target, {"status": "pass"})

    assert attempts["count"] == 3
    assert json.loads(target.read_text(encoding="utf-8")) == {"status": "pass"}
    assert not list(tmp_path.glob("health.json.tmp.*"))


def make_shell(tmp_path: Path, *, max_scan_files: int = 1000) -> Path:
    shell = tmp_path / "shell"
    (shell / "config").mkdir(parents=True)
    (shell / "Z Axis" / "Z+1_Architect" / "projects").mkdir(parents=True)
    (shell / "Z Axis" / "Z0_TheConstruct" / "projects").mkdir(parents=True)
    (shell / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports").mkdir(parents=True)
    config = {
        "project_roots": [
            {
                "root_id": "architect-canonical",
                "path": "Z Axis/Z+1_Architect/projects",
                "authority": "canonical",
                "writable": True,
            },
            {
                "root_id": "construct-legacy",
                "path": "Z Axis/Z0_TheConstruct/projects",
                "authority": "legacy_reference",
                "writable": False,
            },
        ],
        "scan_policy": {
            "ignored_directories": [".git", ".venv", "node_modules", "__pycache__"],
            "ignored_files": ["Thumbs.db"],
            "max_files_per_project": 50,
            "max_hash_bytes": 1048576,
            "registry_refresh_seconds": 1,
        },
        "resource_guard": {
            "max_project_scan_files": max_scan_files,
            "max_archive_inventory": 100,
            "max_archive_hashes": 20,
        },
        "go_review": {
            "queue_path": "Z Axis/Z-4_Merovingian/data/runtime_exports/go_review_queue.jsonl",
            "decision_path": "Z Axis/Z-4_Merovingian/data/runtime_exports/go_review_decisions.jsonl",
            "allowed_decisions": ["approve", "hold", "reject"],
        },
        "drive_writeback": {
            "local_fallback_path": "Z Axis/Z-4_Merovingian/data/runtime_exports/drive_outbox"
        },
        "cleanup_policy": {
            "never_delete_patterns": ["*.zip", "project.json"],
            "required_proof": ["exact_path", "sha256", "recovery_path"],
        },
    }
    (shell / "config" / "project_routing.json").write_text(json.dumps(config), encoding="utf-8")
    return shell


def test_project_registry_prefers_architect_and_detects_duplicate_names(tmp_path):
    shell = make_shell(tmp_path)
    canonical = shell / "Z Axis" / "Z+1_Architect" / "projects" / "Apollo"
    legacy = shell / "Z Axis" / "Z0_TheConstruct" / "projects" / "Apollo"
    canonical.mkdir()
    legacy.mkdir()
    (canonical / "README.md").write_text("canonical project", encoding="utf-8")
    (legacy / "old.txt").write_text("legacy project", encoding="utf-8")

    pipeline = ProjectPipeline(shell)
    registry = pipeline.scan_projects()

    assert registry["summary"]["project_count"] == 2
    assert registry["summary"]["duplicate_name_group_count"] == 1
    canonical_row = next(item for item in registry["projects"] if item["authority"] == "canonical")
    assert canonical_row["writable"] is True
    assert canonical_row["condition"] == "active"


def test_archive_duplicates_are_evidence_only(tmp_path):
    shell = make_shell(tmp_path)
    project = shell / "Z Axis" / "Z+1_Architect" / "projects" / "Archive Project"
    project.mkdir()
    payload = b"same archive payload"
    (project / "one.zip").write_bytes(payload)
    (project / "two.zip").write_bytes(payload)

    pipeline = ProjectPipeline(shell)
    registry = pipeline.scan_projects()
    cleanup = pipeline.scan_cleanup_candidates(registry)

    duplicate = next(item for item in cleanup["candidates"] if item["candidate_class"] == "duplicate_archive_checksum")
    assert len(duplicate["paths"]) == 2
    assert cleanup["automatic_deletion"] is False
    assert all(item.get("action") != "delete" for item in cleanup["candidates"])


def test_scan_stops_at_resource_limit(tmp_path):
    shell = make_shell(tmp_path, max_scan_files=1000)
    project = shell / "Z Axis" / "Z+1_Architect" / "projects" / "Large Project"
    project.mkdir()
    for index in range(75):
        (project / f"file-{index}.txt").write_text(str(index), encoding="utf-8")

    pipeline = ProjectPipeline(shell)
    registry = pipeline.scan_projects()
    row = registry["projects"][0]

    assert row["file_count"] == 50
    assert row["scan_truncated"] is True
    assert registry["summary"]["truncated_project_count"] == 1


def test_agent_floor_health_materializes_shared_async_queue(tmp_path):
    shell = make_shell(tmp_path)
    for directory in FLOOR_ROOTS.values():
        root = shell / "Z Axis" / directory
        (root / "Z Direct").mkdir(parents=True, exist_ok=True)
        (root / "_FLOOR_MANIFEST.json").write_text("{}\n", encoding="utf-8")
        (root / "__init__.py").write_text("", encoding="utf-8")
    runtime_exports = shell / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports"
    (runtime_exports / "go_review_queue.jsonl").write_text("", encoding="utf-8")
    (runtime_exports / "go_review_decisions.jsonl").write_text("", encoding="utf-8")

    snapshot = ProjectPipeline(shell).agent_floor_health(
        services={"database": True, "event_bus": True, "storage": True},
        event_bus_enabled=True,
    )

    assert snapshot["state"] == "operational"
    assert snapshot["operational_count"] == 8
    assert Path(snapshot["transport"]["neo_queue_path"]).is_file()


def test_memory_guard_throttles_heavy_work_when_memory_is_low(tmp_path, monkeypatch):
    shell = make_shell(tmp_path)
    total = 32 * 1024**3
    free = 3 * 1024**3
    monkeypatch.setattr(project_pipeline, "_memory_snapshot", lambda: (total, free))

    snapshot = ProjectPipeline(shell)._resource_health()

    assert snapshot["state"] == "warning"
    assert snapshot["work_intake"] == "bounded_only"
    assert snapshot["bounded_work_allowed"] is True
    assert snapshot["heavy_work_allowed"] is False
    assert snapshot["memory"]["free_percent"] == 9.38


def test_refresh_queues_change_receipt_without_mutating_project(tmp_path, monkeypatch):
    shell = make_shell(tmp_path)
    project = shell / "Z Axis" / "Z+1_Architect" / "projects" / "Receipt Project"
    project.mkdir()
    source = project / "work.txt"
    source.write_text("first", encoding="utf-8")

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
    pipeline = ProjectPipeline(shell)
    pipeline.refresh(force=True, queue_changes=True)
    source.write_text("second", encoding="utf-8")
    second = pipeline.refresh(force=True, queue_changes=True)

    assert second["review_packet"] is not None
    assert second["review_packet"]["state"] == "pending_review"
    assert source.read_text(encoding="utf-8") == "second"
    assert pipeline.review_queue_path.is_file()
