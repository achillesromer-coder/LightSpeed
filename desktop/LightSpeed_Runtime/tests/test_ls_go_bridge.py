from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
import tracemalloc
import types
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime import ls_go_bridge
from lightspeed_runtime.floor_bridges import NeoAchillesBridge
from lightspeed_runtime.project_pipeline import ProjectPipeline
from lightspeed_runtime.representation_edge import FEATURE_FLAG, RepresentationEdgeStore


def test_neo_operator_approval_forwards_authority_contract() -> None:
    observed: dict = {}

    class RuntimeStub:
        def approve_workspace_action(self, *args, **kwargs):
            observed["args"] = args
            observed["kwargs"] = kwargs
            return {"approval_state": "approved"}

    bridge = object.__new__(NeoAchillesBridge)
    bridge.runtime = RuntimeStub()
    authority = {
        "canonical_gate_id": "GO-GATE-TEST-001",
        "owner_decision_ref": "OWNER-TEST-001",
        "core_acceptance_ref": "CORE-TEST-001",
        "approval_or_hold_state": "approve",
        "authorised_scope": "private deterministic test only",
        "prohibited_scope": "deployment and publication",
    }

    result = bridge.approve_operator_action(
        "workspace-test",
        "action-test",
        audit_ref="audit-test",
        authority_contract=authority,
    )

    assert result["approval_state"] == "approved"
    assert observed["args"] == ("workspace-test", "Romer", "action-test")
    assert observed["kwargs"]["audit_ref"] == "audit-test"
    assert observed["kwargs"]["authority_contract"] == authority


def test_quarter_speed_host_profile_bounds_background_work() -> None:
    policy_path = (
        RUNTIME_ROOT.parent
        / "Desktop_Hooks"
        / "LightSpeed"
        / "config"
        / "host_runtime_policy.json"
    )
    limits = json.loads(policy_path.read_text(encoding="utf-8"))["runtime_limits"]

    assert limits["cognigrex_speed_percent"] == 25
    assert limits["max_background_queue_workers"] == 1
    assert limits["max_concurrent_ollama_jobs"] == 1
    assert limits["max_floor_boot_parallelism"] == 2
    assert limits["merovingian_interval_seconds"] == 120
    assert limits["watchdog_interval_minutes"] == 10


def test_watchdog_accepts_canonical_junction_alias(monkeypatch) -> None:
    watchdog_path = (
        RUNTIME_ROOT.parents[1]
        / "scripts"
        / "ensure_cognigrex_local_stack.py"
    )
    spec = importlib.util.spec_from_file_location("ensure_cognigrex_local_stack", watchdog_path)
    assert spec is not None and spec.loader is not None
    watchdog = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(watchdog)
    monkeypatch.setattr(watchdog.os.path, "samefile", lambda left, right: True)

    assert watchdog.paths_refer_to_same_location(
        Path(r"D:\LightSpeed\App"),
        Path(r"C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed"),
    )


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
        "canonical_gate_id": "GO-GATE-TEST-001",
        "owner_decision_ref": "OWNER-TEST-001",
        "core_acceptance_ref": "CORE-TEST-001",
        "approval_or_hold_state": "approve",
        "authorised_scope": "Smith local review queue",
        "prohibited_scope": "deployment, publication, destructive filesystem changes",
        "requested_scope": "Smith local review queue",
    }
    payload.update(overrides)
    return payload


def install_command_identity_schema(connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS ls_go_command_identities (
            command_id TEXT PRIMARY KEY,
            canonical_payload_sha256 TEXT NOT NULL,
            queue_state TEXT NOT NULL DEFAULT 'indexed',
            queue_occurrence_count INTEGER NOT NULL DEFAULT 0,
            first_queue_offset INTEGER,
            last_queue_offset INTEGER,
            task_id INTEGER,
            job_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ls_go_command_queue_state (
            queue_key TEXT PRIMARY KEY,
            queue_path TEXT NOT NULL,
            device INTEGER,
            inode INTEGER,
            indexed_offset INTEGER NOT NULL DEFAULT 0,
            observed_size INTEGER NOT NULL DEFAULT 0,
            observed_mtime_ns INTEGER NOT NULL DEFAULT 0,
            complete INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        """
    )


class CommandFixtureDatabase:
    def __init__(self, path: Path, *, install_identity: bool = True):
        self.path = path
        with self.get_connection() as connection:
            connection.executescript(
                """
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    project_id TEXT,
                    status TEXT,
                    priority TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    metadata_json TEXT
                );
                CREATE TABLE jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_type TEXT,
                    task_id INTEGER,
                    status TEXT,
                    params_json TEXT
                );
                """
            )
            if install_identity:
                install_command_identity_schema(connection)

    @contextmanager
    def get_connection(self):
        connection = sqlite3.connect(self.path, timeout=10, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


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
        "latest_snapshot",
        lambda self: {
            "health": {
                "status": "pass",
                "services": {"database": True, "event_bus": True, "storage": True},
                "details": {"drive_writeback": {"path": str(self.runtime_exports), "mode": "test"}},
                "errors": [],
            },
            "summary": {},
            "cleanup_summary": {"candidate_count": 0, "automatic_deletion": False},
        },
    )


def test_temp_bridge_does_not_initialize_ambient_merovingian_services(tmp_path, monkeypatch):
    calls: list[str] = []
    ambient_core = types.ModuleType("core")
    ambient_core.__path__ = []
    ambient_services = types.ModuleType("core.services")

    def initialize_services():
        calls.append("initialized")
        return {"database": object(), "storage": object()}

    ambient_services.initialize_services = initialize_services
    monkeypatch.setitem(sys.modules, "core", ambient_core)
    monkeypatch.setitem(sys.modules, "core.services", ambient_services)

    assert ls_go_bridge._try_get_services(tmp_path) == (None, None)
    assert calls == []


def test_bridge_rejects_core_services_outside_embedded_merovingian_root(
    tmp_path, monkeypatch
):
    embedded_services = (
        tmp_path / "Z Axis" / "Z-4_Merovingian" / "core" / "services"
    )
    embedded_services.mkdir(parents=True)
    ambient_services_file = tmp_path / "ambient" / "core" / "services" / "__init__.py"
    ambient_services_file.parent.mkdir(parents=True)
    ambient_services_file.write_text("# wrong runtime\n", encoding="utf-8")

    calls: list[str] = []
    ambient_services = types.ModuleType("core.services")
    ambient_services.__file__ = str(ambient_services_file)

    def initialize_services():
        calls.append("initialized")
        return {"database": object(), "storage": object()}

    ambient_services.initialize_services = initialize_services
    monkeypatch.setattr(
        ls_go_bridge.importlib,
        "import_module",
        lambda module_name: ambient_services,
    )

    assert ls_go_bridge._try_get_services(tmp_path) == (None, None)
    assert calls == []


def test_bridge_initializes_core_services_from_embedded_merovingian_root(
    tmp_path, monkeypatch
):
    embedded_services_file = (
        tmp_path
        / "Z Axis"
        / "Z-4_Merovingian"
        / "core"
        / "services"
        / "__init__.py"
    )
    embedded_services_file.parent.mkdir(parents=True)
    embedded_services_file.write_text("# canonical runtime\n", encoding="utf-8")

    expected_db = object()
    expected_storage = object()
    embedded_services = types.ModuleType("core.services")
    embedded_services.__file__ = str(embedded_services_file)
    embedded_services.initialize_services = lambda: {
        "database": expected_db,
        "storage": expected_storage,
    }
    monkeypatch.setattr(
        ls_go_bridge.importlib,
        "import_module",
        lambda module_name: embedded_services,
    )

    assert ls_go_bridge._try_get_services(tmp_path) == (
        expected_db,
        expected_storage,
    )


def test_bridge_applies_command_identity_schema_only_through_authorized_gate(
    tmp_path, monkeypatch
):
    configure_shell(tmp_path)

    class MigrationDatabase:
        def __init__(self):
            self.calls = 0

        def ensure_ls_go_command_identity_schema(self):
            self.calls += 1

    database = MigrationDatabase()
    monkeypatch.setattr(
        ls_go_bridge,
        "_try_get_services",
        lambda _root: (database, object()),
    )

    ls_go_bridge.create_app(tmp_path)
    assert database.calls == 0

    (tmp_path / "config" / "launch_control.json").write_text(
        json.dumps(
            {
                "manual_gates": [
                    {
                        "gate_id": "canonical_queue_indexes",
                        "state": "operator_authorized",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    ls_go_bridge.create_app(tmp_path)
    assert database.calls == 1


def test_persistent_command_index_startup_does_not_scan_million_entry_queue(tmp_path):
    queue_path = tmp_path / "ls_go_command_queue.jsonl"
    queue_path.write_bytes(b"{}\n" * 1_000_000)

    class NoStartupDatabaseAccess:
        def get_connection(self):
            raise AssertionError("index construction accessed the database")

    tracemalloc.start()
    index = ls_go_bridge._PersistentCommandEnvelopeIndex(
        NoStartupDatabaseAccess(),
        queue_path,
    )
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert index.path == queue_path
    assert peak < 256 * 1024


def test_persistent_command_index_is_bounded_restartable_and_preserves_mtime(tmp_path):
    queue_path = tmp_path / "ls_go_command_queue.jsonl"
    historical = [
        command_payload(command_id=f"LSGO-HISTORY-{index:04d}")
        for index in range(300)
    ]
    queue_path.write_bytes(
        b"".join(
            json.dumps(record, sort_keys=True).encode("utf-8") + b"\n"
            for record in historical
        )
    )
    initial_mtime_ns = queue_path.stat().st_mtime_ns
    database = CommandFixtureDatabase(tmp_path / "identity.db")
    index = ls_go_bridge._PersistentCommandEnvelopeIndex(database, queue_path)
    index.SCAN_BYTES = 4096

    pending_count = 0
    while True:
        try:
            index.synchronize()
            break
        except ls_go_bridge.CommandQueueIndexPreparing:
            pending_count += 1
            assert pending_count < 100
    assert pending_count > 1
    assert queue_path.stat().st_mtime_ns == initial_mtime_ns
    with database.get_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM ls_go_command_identities"
        ).fetchone()[0]
        state = connection.execute(
            "SELECT indexed_offset, complete FROM ls_go_command_queue_state"
        ).fetchone()
    assert count == 300
    assert state[0] == queue_path.stat().st_size
    assert state[1] == 1

    restarted = ls_go_bridge._PersistentCommandEnvelopeIndex(database, queue_path)
    assert restarted.synchronize()["scanned_bytes"] == 0
    appended = command_payload(command_id="LSGO-APPENDED-0001")
    with queue_path.open("ab") as stream:
        stream.write(json.dumps(appended, sort_keys=True).encode("utf-8") + b"\n")
    appended_mtime_ns = queue_path.stat().st_mtime_ns
    restarted.synchronize()
    with database.get_connection() as connection:
        found = connection.execute(
            "SELECT canonical_payload_sha256, queue_occurrence_count "
            "FROM ls_go_command_identities WHERE command_id = ?",
            ("LSGO-APPENDED-0001",),
        ).fetchone()
    assert found[0] == ls_go_bridge._command_payload_sha256(appended)
    assert found[1] == 1
    assert queue_path.stat().st_mtime_ns == appended_mtime_ns


def test_persistent_command_index_fails_closed_on_truncation(tmp_path):
    queue_path = tmp_path / "ls_go_command_queue.jsonl"
    original = command_payload(command_id="LSGO-INDEX-BASE")
    queue_path.write_text(json.dumps(original) + "\n", encoding="utf-8")
    database = CommandFixtureDatabase(tmp_path / "identity.db")
    index = ls_go_bridge._PersistentCommandEnvelopeIndex(database, queue_path)
    index.synchronize()
    queue_path.write_bytes(b"")

    with pytest.raises(
        ls_go_bridge.CommandQueueIndexStale,
        match="truncated",
    ):
        index.synchronize()


def test_read_queue_tails_large_ledger_with_byte_and_line_caps(tmp_path, monkeypatch):
    queue_path = ls_go_bridge._queue_path(tmp_path)
    historical = b'{"command_id":"OLD"}\n' * 20_000
    oversized = json.dumps(
        {"command_id": "OVERSIZED", "payload": "x" * 1000}
    ).encode("utf-8") + b"\n"
    recent = b"".join(
        json.dumps({"command_id": f"RECENT-{index}"}).encode("utf-8") + b"\n"
        for index in range(5)
    )
    queue_path.write_bytes(historical + oversized + recent)
    original_mtime_ns = queue_path.stat().st_mtime_ns
    monkeypatch.setattr(ls_go_bridge, "_QUEUE_TAIL_MAX_BYTES", 4096)
    monkeypatch.setattr(ls_go_bridge, "_QUEUE_TAIL_MAX_LINE_BYTES", 512)

    real_open = Path.open
    reads: list[int] = []

    class GuardedReader:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def seek(self, *args):
            return self.stream.seek(*args)

        def read(self, size=-1):
            assert 0 <= size <= 4096
            reads.append(size)
            return self.stream.read(size)

    def guarded_open(path, *args, **kwargs):
        stream = real_open(path, *args, **kwargs)
        if path == queue_path and args and args[0] == "rb":
            return GuardedReader(stream)
        return stream

    monkeypatch.setattr(Path, "open", guarded_open)
    rows = ls_go_bridge._read_queue(tmp_path, limit=6)

    identifiers = [row.get("command_id") for row in rows]
    assert identifiers[:5] == [f"RECENT-{index}" for index in reversed(range(5))]
    assert "OVERSIZED" not in identifiers
    assert reads == [4096]
    assert queue_path.stat().st_mtime_ns == original_mtime_ns


def test_legacy_command_lookup_escapes_wildcards_and_remains_bounded(tmp_path):
    database = CommandFixtureDatabase(tmp_path / "lookup.db")
    statements: list[str] = []
    with database.get_connection() as connection:
        for index in range(100):
            connection.execute(
                "INSERT INTO tasks (title, metadata_json, status) VALUES (?, ?, 'pending')",
                (f"decoy-{index}", json.dumps({"command_id": "LSGOXTEST"})),
            )
        target = connection.execute(
            "INSERT INTO tasks (title, metadata_json, status) VALUES (?, ?, 'pending')",
            ("target", json.dumps({"command_id": "LSGO_TEST"})),
        ).lastrowid
        job_id = connection.execute(
            "INSERT INTO jobs (job_type, task_id, status, params_json) "
            "VALUES ('ls_go_command', ?, 'pending', '{}')",
            (target,),
        ).lastrowid
        connection.set_trace_callback(statements.append)
        task, job = ls_go_bridge._find_command_database_state_connection(
            connection,
            "LSGO_TEST",
        )

    assert task["id"] == target
    assert job["job_id"] == job_id
    legacy_queries = [statement for statement in statements if "FROM tasks" in statement]
    assert len(legacy_queries) == 1
    assert "ESCAPE" in legacy_queries[0]
    assert "LIMIT 64" in legacy_queries[0]


@pytest.mark.parametrize(
    "command_id",
    ["LSGO%TEST", "LSGO TEST", "LSGO/TEST", "' OR 1=1 --", "_leading"],
)
def test_legacy_command_lookup_rejects_adversarial_identity(tmp_path, command_id):
    database = CommandFixtureDatabase(tmp_path / "adversarial.db")
    with database.get_connection() as connection:
        with pytest.raises(ValueError, match="command_id must use"):
            ls_go_bridge._find_command_database_state_connection(connection, command_id)


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


def test_bridge_fails_closed_when_canonical_command_database_is_unavailable(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    response = client.post("/api/v1/ls-go/commands", json=command_payload())

    assert response.status_code == 503
    assert "canonical command database is unavailable" in response.json()["detail"]
    assert not (tmp_path / "Z Axis" / "Z+2_Neo" / "data" / "actions" / "ls_go_command_queue.jsonl").exists()


def test_bridge_command_replay_is_idempotent_and_conflict_safe(tmp_path, monkeypatch):
    database = CommandFixtureDatabase(tmp_path / "command.db")
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (database, object()))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    first = client.post("/api/v1/ls-go/commands", json=command_payload())
    queue_path = Path(first.json()["artifact_ref"])
    first_bytes = queue_path.read_bytes()
    first_mtime_ns = queue_path.stat().st_mtime_ns

    replay = client.post(
        "/api/v1/ls-go/commands",
        json=command_payload(created_utc="2099-01-01T00:00:00Z"),
    )
    conflict = client.post(
        "/api/v1/ls-go/commands",
        json=command_payload(instruction="Different command content."),
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    assert replay.json()["canonical_payload_sha256"] == first.json()["canonical_payload_sha256"]
    assert queue_path.read_bytes() == first_bytes
    assert queue_path.stat().st_mtime_ns == first_mtime_ns
    assert conflict.status_code == 409
    assert queue_path.read_bytes() == first_bytes


def test_bridge_database_lookup_failure_is_503_and_never_appends_queue(
    tmp_path, monkeypatch
):
    class UnavailableDatabase:
        def get_connection(self):
            raise sqlite3.OperationalError("injected canonical database outage")

    monkeypatch.setattr(
        ls_go_bridge,
        "_try_get_services",
        lambda _root: (UnavailableDatabase(), object()),
    )
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    response = client.post("/api/v1/ls-go/commands", json=command_payload())

    queue_path = (
        tmp_path
        / "Z Axis"
        / "Z+2_Neo"
        / "data"
        / "actions"
        / "ls_go_command_queue.jsonl"
    )
    assert response.status_code == 503
    assert "canonical command database" in response.json()["detail"]
    assert not queue_path.exists()


def test_concurrent_identical_command_creates_one_queue_task_and_job(
    tmp_path, monkeypatch
):
    database = CommandFixtureDatabase(tmp_path / "concurrent.db")
    monkeypatch.setattr(
        ls_go_bridge,
        "_try_get_services",
        lambda _root: (database, object()),
    )
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(
                lambda _: client.post(
                    "/api/v1/ls-go/commands",
                    json=command_payload(),
                ),
                range(2),
            )
        )

    assert [response.status_code for response in responses] == [200, 200]
    assert sorted(response.json()["idempotent_replay"] for response in responses) == [
        False,
        True,
    ]
    queue_path = Path(responses[0].json()["artifact_ref"])
    assert len(queue_path.read_text(encoding="utf-8").splitlines()) == 1
    with database.get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 1
        identity = connection.execute(
            "SELECT first_queue_offset, last_queue_offset, queue_occurrence_count "
            "FROM ls_go_command_identities WHERE command_id = ?",
            ("LSGO-TEST-001",),
        ).fetchone()
    assert identity[0] == 0
    assert identity[1] > identity[0]
    assert identity[2] == 1


def test_bridge_command_replay_does_not_duplicate_task_or_job(tmp_path, monkeypatch):
    database = CommandFixtureDatabase(tmp_path / "command.db")
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (database, object()))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    first = client.post("/api/v1/ls-go/commands", json=command_payload())
    with database.get_connection() as connection:
        connection.execute("UPDATE tasks SET status = 'completed'")
    replay = client.post("/api/v1/ls-go/commands", json=command_payload())

    with database.get_connection() as connection:
        task_count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        job_count = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    assert replay.json()["state"] == "completed"
    assert replay.json()["task_id"] == first.json()["task_id"]
    assert task_count == 1
    assert job_count == 1


def test_bridge_replay_repairs_one_incomplete_database_lifecycle(tmp_path, monkeypatch):
    database = CommandFixtureDatabase(tmp_path / "repair.db")
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (database, object()))
    original_create_job = ls_go_bridge._create_command_job
    attempts = 0

    def fail_once(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("injected job handoff failure")
        return original_create_job(*args, **kwargs)

    monkeypatch.setattr(ls_go_bridge, "_create_command_job", fail_once)
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    first = client.post("/api/v1/ls-go/commands", json=command_payload())
    queue_path = tmp_path / "Z Axis" / "Z+2_Neo" / "data" / "actions" / "ls_go_command_queue.jsonl"
    queue_bytes = queue_path.read_bytes()
    queue_mtime_ns = queue_path.stat().st_mtime_ns
    repaired = client.post("/api/v1/ls-go/commands", json=command_payload())
    replay = client.post("/api/v1/ls-go/commands", json=command_payload())

    with database.get_connection() as connection:
        task_count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        job_count = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        connection.execute("DELETE FROM jobs")
        connection.execute("UPDATE tasks SET status = 'blocked'")
    terminal = client.post("/api/v1/ls-go/commands", json=command_payload())
    with database.get_connection() as connection:
        terminal_job_count = connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

    assert first.status_code == 503
    assert repaired.status_code == 200
    assert repaired.json()["idempotent_replay"] is True
    assert repaired.json()["repair_performed"] is True
    assert replay.json()["repair_performed"] is False
    assert task_count == 1
    assert job_count == 1
    assert terminal.json()["state"] == "blocked"
    assert terminal.json()["repair_performed"] is False
    assert terminal_job_count == 0
    assert queue_path.read_bytes() == queue_bytes
    assert queue_path.stat().st_mtime_ns == queue_mtime_ns


def test_bridge_rejects_command_without_achilles_oversight(tmp_path, monkeypatch):
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    response = client.post(
        "/api/v1/ls-go/commands",
        json=command_payload(oversight_floor="Neo"),
    )

    assert response.status_code == 400
    assert "Achilles oversight" in response.json()["detail"]


def test_bridge_rejects_command_without_canonical_authority_contract(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))
    payload = command_payload()
    for field in ls_go_bridge.AUTHORITY_REQUIRED_FIELDS:
        payload.pop(field, None)

    response = client.post("/api/v1/ls-go/commands", json=payload)

    queue_path = (
        tmp_path
        / "Z Axis"
        / "Z+2_Neo"
        / "data"
        / "actions"
        / "ls_go_command_queue.jsonl"
    )
    assert response.status_code == 400
    assert "Required command field" in response.json()["detail"]
    assert not queue_path.exists()


def test_bridge_rejects_command_on_hold_authority_contract(tmp_path, monkeypatch):
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    response = client.post(
        "/api/v1/ls-go/commands",
        json=command_payload(approval_or_hold_state="hold"),
    )

    assert response.status_code == 403
    assert "not approved" in response.json()["detail"]


def test_bridge_rejects_command_outside_authorised_scope(tmp_path, monkeypatch):
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    response = client.post(
        "/api/v1/ls-go/commands",
        json=command_payload(
            authorised_scope="Oracle local review queue",
            requested_scope="Smith local review queue",
        ),
    )

    assert response.status_code == 403
    assert "outside authorised scope" in response.json()["detail"]


def test_bridge_rejects_command_inside_prohibited_scope(tmp_path, monkeypatch):
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))

    response = client.post(
        "/api/v1/ls-go/commands",
        json=command_payload(instruction="Publish the reviewed receipt."),
    )

    assert response.status_code == 403
    assert "prohibited scope" in response.json()["detail"]


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


def test_bridge_review_decision_replay_is_idempotent_and_conflict_safe(tmp_path, monkeypatch):
    configure_shell(tmp_path)
    pipeline = ProjectPipeline(tmp_path)
    pipeline.review_queue_path.write_text(
        json.dumps({"review_id": "review-idempotency-1", "state": "pending_review"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    client = TestClient(ls_go_bridge.create_app(tmp_path))
    endpoint = "/api/v1/reviews/review-idempotency-1/decision"

    first = client.post(endpoint, json={"decision": "approve", "note": "Owner reviewed."})
    decision_bytes = pipeline.review_decisions_path.read_bytes()
    decision_mtime_ns = pipeline.review_decisions_path.stat().st_mtime_ns
    replay = client.post(
        endpoint,
        json={"decision": "approve", "note": "  Owner   reviewed. "},
    )
    conflict = client.post(endpoint, json={"decision": "hold", "note": "Needs evidence."})

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json()["receipt"]["idempotent_replay"] is True
    assert (
        replay.json()["receipt"]["canonical_payload_sha256"]
        == first.json()["receipt"]["canonical_payload_sha256"]
    )
    assert pipeline.review_decisions_path.read_bytes() == decision_bytes
    assert pipeline.review_decisions_path.stat().st_mtime_ns == decision_mtime_ns
    assert conflict.status_code == 409
    assert pipeline.review_decisions_path.read_bytes() == decision_bytes


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
    monkeypatch.setenv("LIGHTSPEED_OWNER_APPROVAL_TOKEN", "owner-test-token")
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    monkeypatch.setattr(
        ls_go_bridge,
        "build_representation_edge_store",
        lambda _root: RepresentationEdgeStore(database, enabled=True),
    )
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
        headers={"X-LightSpeed-Owner-Confirmation": "owner-test-token"},
        json={
            "decision": "hold",
            "scope": "edges",
            "edge_ids": [edge_id],
        },
    )
    assert premature.status_code == 400

    identity = client.post(
        f"/api/v1/representation-reviews/{review_id}/decision",
        headers={"X-LightSpeed-Owner-Confirmation": "owner-test-token"},
        json={
            "decision": "provisional_approve",
            "scope": "identity",
            "note": "Candidate identity only.",
        },
    )
    assert identity.status_code == 200
    assert identity.json()["receipt"]["drive_write_executed"] is False

    edge = client.post(
        f"/api/v1/representation-reviews/{review_id}/decision",
        headers={"X-LightSpeed-Owner-Confirmation": "owner-test-token"},
        json={
            "decision": "request_evidence",
            "scope": "edges",
            "edge_ids": [edge_id],
            "note": "Stable workbook key required.",
        },
    )
    assert edge.status_code == 200

    promotions = client.get("/api/v1/representation-promotions").json()
    assert promotions["drive_write_executed"] is False
    assert promotions["readback_required"] is True


def test_representation_decision_rejects_actor_spoof_without_owner_confirmation(
    tmp_path, monkeypatch
):
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
    monkeypatch.setenv("LIGHTSPEED_OWNER_APPROVAL_TOKEN", "owner-test-token")
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (None, None))
    monkeypatch.setattr(
        ls_go_bridge,
        "build_representation_edge_store",
        lambda _root: RepresentationEdgeStore(database, enabled=True),
    )
    client = TestClient(ls_go_bridge.create_app(tmp_path))
    review_id = client.get("/api/v1/representation-graphs").json()["graphs"][0]["review"][
        "review_id"
    ]

    missing = client.post(
        f"/api/v1/representation-reviews/{review_id}/decision",
        json={
            "decision": "approve",
            "actor": "Nathaniel",
            "scope": "identity",
        },
    )
    wrong = client.post(
        f"/api/v1/representation-reviews/{review_id}/decision",
        headers={"X-LightSpeed-Owner-Confirmation": "wrong-token"},
        json={
            "decision": "approve",
            "actor": "Nathaniel",
            "scope": "identity",
        },
    )
    authenticated = client.post(
        f"/api/v1/representation-reviews/{review_id}/decision",
        headers={"X-LightSpeed-Owner-Confirmation": "owner-test-token"},
        json={
            "decision": "approve",
            "actor": "Achilles",
            "scope": "identity",
        },
    )
    monkeypatch.delenv("LIGHTSPEED_OWNER_APPROVAL_TOKEN")
    unconfigured = client.post(
        f"/api/v1/representation-reviews/{review_id}/decision",
        headers={"X-LightSpeed-Owner-Confirmation": "owner-test-token"},
        json={
            "decision": "request_evidence",
            "scope": "identity",
        },
    )

    assert missing.status_code == 403
    assert wrong.status_code == 403
    assert authenticated.status_code == 200
    assert authenticated.json()["receipt"]["actor"] == "Nathaniel"
    assert authenticated.json()["receipt"]["owner_authentication_verified"] is True
    assert unconfigured.status_code == 403
