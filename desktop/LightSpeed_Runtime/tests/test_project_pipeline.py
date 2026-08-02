from __future__ import annotations

import json
import os
import sqlite3
import sys
import types
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


def test_runtime_root_redirects_to_sibling_desktop_shell(tmp_path, monkeypatch):
    monkeypatch.delenv("LIGHTSPEED_SHELL_ROOT", raising=False)
    runtime_root = tmp_path / "LightSpeed_Runtime"
    runtime_root.mkdir()
    shell_root = tmp_path / "Desktop_Hooks" / "LightSpeed"
    (shell_root / "config").mkdir(parents=True)
    (shell_root / "config" / "project_routing.json").write_text("{}\n", encoding="utf-8")

    pipeline = ProjectPipeline(runtime_root)

    assert pipeline.requested_shell_root == runtime_root.resolve()
    assert pipeline.shell_root == shell_root.resolve()
    assert pipeline.root_resolution_mode == "runtime_sibling_contract_root"
    assert pipeline.runtime_exports.is_relative_to(shell_root.resolve())
    assert not (runtime_root / "Z Axis").exists()


def test_temporary_shell_health_does_not_initialize_ambient_core_services(
    tmp_path,
    monkeypatch,
):
    shell = make_shell(tmp_path)
    pipeline = ProjectPipeline(shell)
    calls: list[str] = []
    ambient_core = types.ModuleType("core")
    ambient_core.__path__ = []
    ambient_services = types.ModuleType("core.services")

    def initialize_services():
        calls.append("initialized")
        return {"database": object(), "event_bus": object(), "storage": object()}

    ambient_services.initialize_services = initialize_services
    monkeypatch.setitem(sys.modules, "core", ambient_core)
    monkeypatch.setitem(sys.modules, "core.services", ambient_services)

    health = pipeline.essential_health({"projects": [], "summary": {}})

    assert calls == []
    assert health["services"] == {
        "database": False,
        "event_bus": False,
        "storage": False,
    }
    assert any(
        "embedded_core_unavailable_for_shell_root" in error
        for error in health["errors"]
    )
    assert pipeline.runtime_exports.is_relative_to(tmp_path)


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


def test_project_identity_is_stable_across_canonical_path_changes(tmp_path):
    first_shell = make_shell(tmp_path / "first")
    second_shell = make_shell(tmp_path / "second")
    for shell in (first_shell, second_shell):
        project = shell / "Z Axis" / "Z+1_Architect" / "projects" / "Apollo"
        project.mkdir()
        (project / "README.md").write_text(
            "same logical project",
            encoding="utf-8",
        )

    first_id = ProjectPipeline(first_shell).scan_projects()["projects"][0]["project_id"]
    second_id = ProjectPipeline(second_shell).scan_projects()["projects"][0]["project_id"]

    assert first_id == second_id


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


def test_agent_floor_health_preserves_existing_immutable_ledgers(tmp_path):
    shell = make_shell(tmp_path)
    pipeline = ProjectPipeline(shell)
    queue_paths = [
        shell / "Z Axis" / "Z+2_Neo" / "data" / "actions" / "ls_go_command_queue.jsonl",
        pipeline.review_queue_path,
        pipeline.review_decisions_path,
    ]
    expected = {}
    for index, queue_path in enumerate(queue_paths):
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        payload = f'{{"id": {index}}}\n'
        queue_path.write_text(payload, encoding="utf-8")
        timestamp_ns = 1_700_000_000_000_000_000 + index
        os.utime(queue_path, ns=(timestamp_ns, timestamp_ns))
        expected[queue_path] = (payload, queue_path.stat().st_mtime_ns)

    pipeline.agent_floor_health(
        services={"database": True, "event_bus": True, "storage": True},
        event_bus_enabled=True,
    )

    for queue_path, (payload, timestamp_ns) in expected.items():
        assert queue_path.read_text(encoding="utf-8") == payload
        assert queue_path.stat().st_mtime_ns == timestamp_ns


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

    source.write_text("third payload", encoding="utf-8")
    third = pipeline.refresh(force=True, queue_changes=True)
    pending_registry_reviews = [
        item
        for item in pipeline.list_reviews(limit=100)
        if item.get("event_type") == "project_registry_change"
        and item.get("state") == "pending_review"
    ]

    assert third["superseded_review_count"] == 1
    assert len(pending_registry_reviews) == 1
    assert pipeline._supersede_registry_reviews(retain_latest=False) == 1
    assert not [
        item
        for item in pipeline.list_reviews(limit=100)
        if item.get("event_type") == "project_registry_change"
        and item.get("state") == "pending_review"
    ]


def test_cached_refresh_updates_health_without_rescanning_projects(tmp_path, monkeypatch):
    shell = make_shell(tmp_path)
    pipeline = ProjectPipeline(shell)
    monkeypatch.setattr(
        ProjectPipeline,
        "essential_health",
        lambda self, registry: {
            "status": "pass",
            "services": {"database": True},
            "details": {"agent_floors": {"state": "operational"}},
        },
    )
    pipeline.refresh(force=True, queue_changes=False)
    monkeypatch.setattr(
        pipeline,
        "scan_projects",
        lambda: (_ for _ in ()).throw(AssertionError("cached refresh rescanned projects")),
    )

    cached = pipeline.refresh(force=False, queue_changes=False)

    assert cached["health"]["status"] == "pass"
    assert json.loads(pipeline.health_path.read_text(encoding="utf-8"))["status"] == "pass"
    assert json.loads(pipeline.floor_health_path.read_text(encoding="utf-8"))["state"] == "operational"


def test_latest_snapshot_reads_receipts_without_rescanning(tmp_path, monkeypatch):
    shell = make_shell(tmp_path)
    pipeline = ProjectPipeline(shell)
    pipeline.registry_path.write_text(
        json.dumps({"projects": [{"project_id": "project-alpha"}], "summary": {"project_count": 1}}),
        encoding="utf-8",
    )
    pipeline.health_path.write_text(
        json.dumps({"status": "pass", "services": {"database": True}}),
        encoding="utf-8",
    )
    pipeline.cleanup_path.write_text(
        json.dumps({"candidate_count": 3}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        pipeline,
        "scan_projects",
        lambda: (_ for _ in ()).throw(AssertionError("snapshot must not scan")),
    )

    snapshot = pipeline.latest_snapshot()

    assert snapshot["summary"]["project_count"] == 1
    assert snapshot["health"]["status"] == "pass"
    assert snapshot["cleanup_summary"] == {
        "candidate_count": 3,
        "automatic_deletion": False,
    }


def test_drive_writeback_defaults_to_local_outbox_even_when_drive_env_exists(
    tmp_path,
    monkeypatch,
):
    shell = make_shell(tmp_path)
    unapproved_drive = tmp_path / "unapproved-drive"
    unapproved_drive.mkdir()
    monkeypatch.setenv("LIGHTSPEED_DRIVE_SYNC_ROOT", str(unapproved_drive))
    monkeypatch.setenv("GOOGLE_DRIVE_ROOT", str(unapproved_drive))

    root, mode = ProjectPipeline(shell).resolve_drive_receipt_root()

    expected = (
        shell
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "runtime_exports"
        / "drive_outbox"
    )
    assert root == expected
    assert root.is_dir()
    assert mode == "local_outbox_pending_drive_sync"
    assert list(unapproved_drive.iterdir()) == []


def test_drive_writeback_requires_owner_approved_exact_existing_target(tmp_path):
    shell = make_shell(tmp_path)
    exact_target = tmp_path / "approved-drive-target"
    exact_target.mkdir()
    (shell / "config" / "launch_control.json").write_text(
        json.dumps(
            {
                "manual_gates": [
                    {
                        "gate_id": "drive_writeback",
                        "state": "owner_approved_exact_target",
                        "approved_by": "Nathaniel Bouwer",
                        "decision_id": "OWNER-DRIVE-TEST-001",
                        "approved_target": str(exact_target),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    root, mode = ProjectPipeline(shell).resolve_drive_receipt_root()

    assert root == exact_target
    assert mode == "owner_approved_exact_drive_target"


def test_review_decision_replay_repairs_missing_fixed_receipt_without_ledger_rewrite(
    tmp_path,
    monkeypatch,
):
    shell = make_shell(tmp_path)
    pipeline = ProjectPipeline(shell)
    review_id = "LSGO-REVIEW-REPAIR-001"
    pipeline.review_queue_path.write_text(
        json.dumps({"review_id": review_id, "state": "pending_review"}) + "\n",
        encoding="utf-8",
    )
    original_write_json = project_pipeline._write_json
    failures = {"remaining": 1}

    def fail_first_receipt(path, payload):
        if failures["remaining"]:
            failures["remaining"] -= 1
            raise OSError("simulated receipt write failure")
        return original_write_json(path, payload)

    monkeypatch.setattr(project_pipeline, "_write_json", fail_first_receipt)
    with pytest.raises(OSError, match="simulated receipt write failure"):
        pipeline.decide_review(review_id, "approve", "Owner reviewed.")

    decision_bytes = pipeline.review_decisions_path.read_bytes()
    assert len(decision_bytes.splitlines()) == 1
    fixed_timestamp_ns = 1_700_000_000_000_000_000
    os.utime(
        pipeline.review_decisions_path,
        ns=(fixed_timestamp_ns, fixed_timestamp_ns),
    )
    monkeypatch.setattr(project_pipeline, "_write_json", original_write_json)

    repaired = pipeline.decide_review(review_id, "approve", " Owner   reviewed. ")

    receipt_path = Path(repaired["decision_receipt_path"])
    assert repaired["idempotent_replay"] is True
    assert repaired["decision_receipt_state"] == "repaired_missing"
    assert receipt_path.is_file()
    assert pipeline.review_decisions_path.read_bytes() == decision_bytes
    assert pipeline.review_decisions_path.stat().st_mtime_ns == fixed_timestamp_ns

    receipt_bytes = receipt_path.read_bytes()
    receipt_timestamp_ns = 1_700_000_000_100_000_000
    os.utime(receipt_path, ns=(receipt_timestamp_ns, receipt_timestamp_ns))
    verified = pipeline.decide_review(review_id, "approve", "Owner reviewed.")

    assert verified["decision_receipt_state"] == "verified_existing"
    assert receipt_path.read_bytes() == receipt_bytes
    assert receipt_path.stat().st_mtime_ns == receipt_timestamp_ns
    assert pipeline.review_decisions_path.read_bytes() == decision_bytes
    assert pipeline.review_decisions_path.stat().st_mtime_ns == fixed_timestamp_ns


def test_jsonl_identity_index_is_bounded_and_preserves_immutable_ledger(tmp_path):
    ledger = tmp_path / "reviews.jsonl"
    rows = [
        {
            "review_id": f"review-{index:04d}",
            "payload": "x" * 300,
        }
        for index in range(180)
    ]
    ledger.write_bytes(
        b"".join(
            json.dumps(row, sort_keys=True).encode("utf-8") + b"\n"
            for row in rows
        )
    )
    ledger_bytes = ledger.read_bytes()
    ledger_mtime_ns = ledger.stat().st_mtime_ns
    index = project_pipeline._JsonlIdentityIndex(
        ledger,
        "review_id",
        scan_bytes=4096,
    )

    with pytest.raises(project_pipeline.ReviewIndexPending):
        index.find("review-0179")
    while True:
        progress = index.advance()
        assert progress["scanned_bytes"] <= 4096
        if progress["complete"]:
            break

    assert index.find("review-0179") == [rows[-1]]
    assert ledger.read_bytes() == ledger_bytes
    assert ledger.stat().st_mtime_ns == ledger_mtime_ns

    appended = {"review_id": "review-appended", "payload": "bounded-tail"}
    with ledger.open("ab") as stream:
        stream.write(json.dumps(appended).encode("utf-8") + b"\n")
    appended_bytes = ledger.read_bytes()
    appended_mtime_ns = ledger.stat().st_mtime_ns

    assert index.find("review-appended") == [appended]
    assert ledger.read_bytes() == appended_bytes
    assert ledger.stat().st_mtime_ns == appended_mtime_ns


def test_jsonl_list_reader_uses_bounded_tail_without_mutating_large_ledger(
    tmp_path,
    monkeypatch,
):
    ledger = tmp_path / "large-list-ledger.jsonl"
    row_count = 40_000
    with ledger.open("wb") as stream:
        for index in range(row_count):
            stream.write(
                json.dumps(
                    {
                        "review_id": f"tail-review-{index:06d}",
                        "payload": "x" * 160,
                    },
                    sort_keys=True,
                ).encode("utf-8")
                + b"\n"
            )
    ledger_size = ledger.stat().st_size
    fixed_timestamp_ns = 1_700_000_000_200_000_000
    os.utime(ledger, ns=(fixed_timestamp_ns, fixed_timestamp_ns))
    byte_limit = 65_536

    bounded_tail = project_pipeline._bounded_jsonl_tail(
        ledger,
        byte_limit=byte_limit,
    )
    original_read_text = Path.read_text

    def reject_whole_file_read(path, *args, **kwargs):
        if path == ledger:
            raise AssertionError("large JSONL list endpoint used a whole-file text read")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", reject_whole_file_read)
    rows = project_pipeline._read_jsonl(
        ledger,
        limit=25,
        byte_limit=byte_limit,
    )

    assert ledger_size > byte_limit * 10
    assert len(bounded_tail) <= byte_limit
    assert len(rows) == 25
    assert rows[-1]["review_id"] == f"tail-review-{row_count - 1:06d}"
    assert rows[0]["review_id"] != "tail-review-000000"
    assert ledger.stat().st_size == ledger_size
    assert ledger.stat().st_mtime_ns == fixed_timestamp_ns


def test_sqlite_identity_index_resumes_large_ledger_without_resident_rows(tmp_path):
    ledger = tmp_path / "large-review-ledger.jsonl"
    database = tmp_path / "lightspeed_unified.db"
    with sqlite3.connect(database):
        pass
    row_count = 25_000
    with ledger.open("wb") as stream:
        for index in range(row_count):
            stream.write(
                json.dumps(
                    {
                        "review_id": f"large-review-{index:06d}",
                        "payload": "x" * 160,
                    },
                    sort_keys=True,
                ).encode("utf-8")
                + b"\n"
            )
    ledger_bytes = ledger.read_bytes()
    ledger_mtime_ns = ledger.stat().st_mtime_ns

    first_index = project_pipeline._JsonlIdentityIndex(
        ledger,
        "review_id",
        scan_bytes=65_536,
        database_path=database,
        allow_schema_create=True,
        memory_identity_limit=4,
    )
    first = first_index.advance()

    assert first["complete"] is False
    assert first["scanned_bytes"] <= 65_536
    assert first["resident_identity_count"] == 0
    assert first_index.resident_identity_count == 0

    restarted_index = project_pipeline._JsonlIdentityIndex(
        ledger,
        "review_id",
        scan_bytes=65_536,
        database_path=database,
        allow_schema_create=False,
        memory_identity_limit=4,
    )
    resumed = restarted_index.advance()

    assert resumed["offset"] > first["offset"]
    assert resumed["scanned_bytes"] <= 65_536
    assert resumed["resident_identity_count"] == 0
    while not resumed["complete"]:
        resumed = restarted_index.advance()
        assert resumed["scanned_bytes"] <= 65_536
        assert resumed["resident_identity_count"] == 0

    assert restarted_index.find(f"large-review-{row_count - 1:06d}") == [
        {
            "review_id": f"large-review-{row_count - 1:06d}",
            "payload": "x" * 160,
        }
    ]
    with sqlite3.connect(database) as connection:
        indexed_count = connection.execute(
            "SELECT COUNT(*) FROM immutable_jsonl_identity_offsets"
        ).fetchone()[0]
        offset_columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(immutable_jsonl_identity_offsets)"
            )
        }
    assert indexed_count == row_count
    assert offset_columns == {"source_key", "identity", "byte_offset", "byte_length"}
    assert ledger.read_bytes() == ledger_bytes
    assert ledger.stat().st_mtime_ns == ledger_mtime_ns


def test_memory_identity_fallback_fails_closed_before_unbounded_growth(tmp_path):
    ledger = tmp_path / "too-many-identities.jsonl"
    ledger.write_text(
        "".join(
            json.dumps({"review_id": f"review-{index}"}) + "\n"
            for index in range(20)
        ),
        encoding="utf-8",
    )
    index = project_pipeline._JsonlIdentityIndex(
        ledger,
        "review_id",
        scan_bytes=65_536,
        memory_identity_limit=4,
    )

    with pytest.raises(project_pipeline.ReviewIndexPending, match="reached capacity"):
        index.advance()

    assert index.resident_identity_count == 0


def test_repository_drive_and_identity_index_contracts_match_runtime_behavior():
    routing_path = (
        RUNTIME_ROOT.parent
        / "Desktop_Hooks"
        / "LightSpeed"
        / "config"
        / "project_routing.json"
    )
    routing = json.loads(routing_path.read_text(encoding="utf-8"))
    drive = routing["drive_writeback"]
    identity_index = routing["go_review"]["identity_index"]

    assert drive["mode"] == "owner_approved_exact_target_or_local_outbox"
    assert "root_environment_variables" not in drive
    assert "relative_receipt_path" not in drive
    assert drive["required_gate_state"] == "owner_approved_exact_target"
    assert drive["required_owner"] == "Nathaniel Bouwer"
    assert identity_index["backend"] == "canonical_database_tables"
    assert identity_index["schema_activation"] == "owner_approved"
    assert identity_index["approval_source"].endswith(
        "manual_gates[gate_id=canonical_queue_indexes]"
    )
    assert identity_index["stores_full_payloads"] is False


def test_review_index_rejects_noncanonical_same_named_database(
    tmp_path,
    monkeypatch,
):
    shell = make_shell(tmp_path)
    candidate = tmp_path / "candidate" / "lightspeed_unified.db"
    canonical = tmp_path / "canonical" / "lightspeed_unified.db"
    candidate.parent.mkdir()
    canonical.parent.mkdir()
    sqlite3.connect(candidate).close()
    sqlite3.connect(canonical).close()
    routing_path = shell / "config" / "project_routing.json"
    routing = json.loads(routing_path.read_text(encoding="utf-8"))
    routing["go_review"]["identity_index"] = {
        "backend": "canonical_database_tables",
        "schema_activation": "owner_approved",
        "required_operator_shell": str(shell),
        "scan_bytes_per_cycle": 65_536,
        "fallback_memory_identity_limit": 16,
    }
    routing_path.write_text(json.dumps(routing), encoding="utf-8")
    (shell / "config" / "launch_control.json").write_text(
        json.dumps(
            {
                "canonical_authorities": {"database": str(candidate)},
                "manual_gates": [
                    {
                        "gate_id": "canonical_queue_indexes",
                        "state": "operator_authorized",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(project_pipeline, "CANONICAL_DATABASE_PATH", canonical)

    rejected = ProjectPipeline(shell)

    assert rejected._review_queue_index.database_path is None
    assert rejected._review_queue_index.allow_schema_create is False

    (shell / "config" / "launch_control.json").write_text(
        json.dumps(
            {
                "canonical_authorities": {"database": str(canonical)},
                "manual_gates": [
                    {
                        "gate_id": "canonical_queue_indexes",
                        "state": "operator_authorized",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    accepted = ProjectPipeline(shell)

    assert accepted._review_queue_index.database_path == canonical
    assert accepted._review_queue_index.allow_schema_create is True


def test_health_rejects_ambient_core_services_when_embedded_root_exists(
    tmp_path,
    monkeypatch,
):
    shell = make_shell(tmp_path)
    embedded_core = shell / "Z Axis" / "Z-4_Merovingian" / "core"
    embedded_core.mkdir(parents=True)
    ambient_file = tmp_path / "ambient" / "core" / "services" / "__init__.py"
    ambient_file.parent.mkdir(parents=True)
    ambient_file.write_text("# ambient collision\n", encoding="utf-8")
    calls: list[str] = []
    ambient_services = types.ModuleType("core.services")
    ambient_services.__file__ = str(ambient_file)

    def initialize_services():
        calls.append("initialized")
        return {"database": object(), "event_bus": object(), "storage": object()}

    ambient_services.initialize_services = initialize_services
    monkeypatch.setattr(
        project_pipeline.importlib,
        "import_module",
        lambda module_name: ambient_services,
    )

    health = ProjectPipeline(shell).essential_health({"projects": [], "summary": {}})

    assert calls == []
    assert health["services"] == {
        "database": False,
        "event_bus": False,
        "storage": False,
    }
    assert any("ambient core.services origin rejected" in error for error in health["errors"])
