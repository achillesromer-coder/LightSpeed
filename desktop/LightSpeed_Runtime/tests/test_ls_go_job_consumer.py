from __future__ import annotations

from datetime import UTC, datetime
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime import ls_go_job_consumer


def test_source_intake_consumer_persists_evidence_once(tmp_path, monkeypatch):
    import hashlib
    shell = tmp_path / "App"
    configure_shell(shell)
    source = tmp_path / "source.md"
    raw = b"# Source\nEvidence for review only.\n"
    source.write_bytes(raw)
    payload = {"source_path": str(source), "source_sha256": hashlib.sha256(raw).hexdigest()}
    params = {"command_id": "LSGO-INTAKE-TEST", "action_type": "source_preserving_intake",
              "action_payload": payload, "execution_mode": "queue", "execute": True, "allow_heavy": False}
    write_command(shell, params["command_id"], schema_version="lightspeed-go-command-v2",
                  action_type=params["action_type"], action_payload=payload)
    original_read = ls_go_job_consumer._read_json
    monkeypatch.setattr(ls_go_job_consumer, "_read_json", lambda p:
                        {"environment": {"assimilation_source_root": str(tmp_path)}}
                        if Path(p).name == "agent_home.json" else original_read(p))
    db = configure_db(tmp_path / "intake.db")
    now = datetime.now(UTC).isoformat(timespec="seconds")
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,updated_at,metadata_json) VALUES (501,'queued',?,'{}')", (now,))
        conn.execute("""INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id,project_id,
                     tool_key,z_context,created_at,updated_at)
                     VALUES (502,'ls_go_command','pending',?,'{}',501,'LS-GO','ls_go_command','Neo',?,?)""",
                     (json.dumps(params), now, now))
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    assert consumer.process_once()["results_written"] == 1
    result = json.loads(ls_go_job_consumer.result_file_path(shell, params["command_id"]).read_text())
    assert result["status"] == "completed"
    assert result["intake"]["source_sha256"] == payload["source_sha256"]
    assert result["intake"]["canonical_mutation"] is False
    assert Path(result["intake"]["artifacts"][0]["path"]).read_bytes() == raw
    assert source.read_bytes() == raw
    assert consumer.process_once()["results_written"] == 0


def test_write_json_retries_transient_windows_replace_error(tmp_path: Path, monkeypatch):
    path = tmp_path / "heartbeat.json"
    original_replace = Path.replace
    attempts = {"count": 0}

    def flaky_replace(self, target):
        if Path(target) == path:
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise PermissionError("simulated transient Windows replace contention")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", flaky_replace)
    monkeypatch.setattr(ls_go_job_consumer.time, "sleep", lambda _seconds: None)

    ls_go_job_consumer._write_json(path, {"state": "ready"})

    assert json.loads(path.read_text(encoding="utf-8"))["state"] == "ready"
    assert attempts["count"] == 3


def test_run_forever_fails_closed_and_records_heartbeat_error(tmp_path: Path, monkeypatch):
    shell = tmp_path / "App"
    configure_shell(shell)
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=object())
    monkeypatch.setattr(consumer, "process_once", lambda: {"state": "ready"})

    def fail_heartbeat(_state):
        raise PermissionError("simulated persistent heartbeat write failure")

    monkeypatch.setattr(consumer, "_heartbeat", fail_heartbeat)

    consumer.run_forever(poll_seconds=0.01)

    receipt = json.loads(
        ls_go_job_consumer.status_receipt_path(shell).read_text(encoding="utf-8")
    )
    assert receipt["state"] == "fatal_heartbeat_error:PermissionError"
    assert "persistent heartbeat write failure" in receipt["error"]
    assert consumer._stop.is_set()
    assert not ls_go_job_consumer.heartbeat_path(shell).exists()


def test_restart_holds_before_claiming_when_prior_job_is_running(tmp_path: Path, monkeypatch):
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    with sqlite3.connect(db.path) as conn:
        conn.executemany(
            "INSERT INTO jobs (id,job_type,status,params_json) VALUES (?,'ls_go_command',?,'{}')",
            [(701, "running"), (702, "pending")],
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    monkeypatch.setattr(consumer, "process_once", lambda: (_ for _ in ()).throw(
        AssertionError("unknown prior execution must hold fresh queued work")))

    consumer.run_forever(poll_seconds=0.01)

    receipt = json.loads(
        ls_go_job_consumer.status_receipt_path(shell).read_text(encoding="utf-8")
    )
    assert receipt["state"] == "recovery_hold_unresolved_running"
    assert receipt["unresolved_job_ids_sample"] == [701]
    assert receipt["unresolved_job_ids_truncated"] is False
    assert receipt["pending_jobs_untouched"] is True
    assert db.execute_query("SELECT status FROM jobs WHERE id=701")[0]["status"] == "running"
    assert db.execute_query("SELECT status FROM jobs WHERE id=702")[0]["status"] == "pending"
    assert not ls_go_job_consumer.heartbeat_path(shell).exists()


def test_restart_reconciles_only_exact_durable_result_without_replay(tmp_path: Path, monkeypatch):
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    command_id = "GO-TASK-RESTART-EXACT"
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'running','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,task_id) "
            "VALUES (601,'ls_go_command','running',?,501)",
            (json.dumps({"command_id": command_id}),),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    original = consumer._persist_result({
        "command_id": command_id, "job_id": 601, "task_id": 501,
        "result_id": ls_go_job_consumer.result_id_for(command_id),
        "status": "completed",
    })
    stored = json.loads(Path(original["receipt_path"]).read_text())
    stored["receipt_path"] = str(tmp_path / "unrelated.json")
    Path(original["receipt_path"]).write_text(json.dumps(stored), encoding="utf-8")
    calls = []

    def no_replay():
        calls.append("poll")
        consumer.stop()
        return {"state": "ready"}

    monkeypatch.setattr(consumer, "process_once", no_replay)
    monkeypatch.setattr(consumer, "_execute_action", lambda **_kw: (_ for _ in ()).throw(
        AssertionError("restart reconciliation must not execute")))
    consumer.run_forever(poll_seconds=0.01)

    assert calls == ["poll"]
    job = db.execute_query("SELECT status,result_json FROM jobs WHERE id=601")[0]
    task = db.execute_query("SELECT status,metadata_json FROM tasks WHERE id=501")[0]
    assert job["status"] == task["status"] == "completed"
    assert json.loads(job["result_json"])["receipt_path"] == original["receipt_path"]
    assert json.loads(task["metadata_json"])["ls_go_local_result"]["job_id"] == 601
    assert len(ls_go_job_consumer.result_queue_path(shell).read_text().splitlines()) == 1
    assert not ls_go_job_consumer.heartbeat_path(shell).exists()


def test_restart_keeps_conflicting_receipt_running_and_holds_queue(tmp_path: Path, monkeypatch):
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    command_id = "GO-TASK-RESTART-CONFLICT"
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'running','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,task_id) "
            "VALUES (601,'ls_go_command','running',?,501)",
            (json.dumps({"command_id": command_id}),),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    consumer._persist_result({
        "command_id": command_id, "job_id": 601, "task_id": 999,
        "result_id": ls_go_job_consumer.result_id_for(command_id),
        "status": "completed",
    })
    monkeypatch.setattr(consumer, "process_once", lambda: (_ for _ in ()).throw(
        AssertionError("conflicting receipt must hold fresh work")))
    consumer.run_forever(poll_seconds=0.01)

    assert db.execute_query("SELECT status FROM jobs WHERE id=601")[0]["status"] == "running"
    assert db.execute_query("SELECT status FROM tasks WHERE id=501")[0]["status"] == "running"
    status = json.loads(ls_go_job_consumer.status_receipt_path(shell).read_text())
    assert status["state"] == "recovery_hold_unresolved_running"
    assert status["unresolved_job_ids_sample"] == [601]


def test_consumer_does_not_resolve_operator_root(tmp_path: Path, monkeypatch):
    shell = tmp_path / "App"
    shell.mkdir()

    def unexpected_resolve(*_args, **_kwargs):
        raise AssertionError("operator root must remain lexical")

    monkeypatch.setattr(Path, "resolve", unexpected_resolve)
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=object())

    assert consumer.shell_root == shell.absolute()


class SQLiteDB:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def get_connection(self):
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()):
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def execute_update(self, query: str, params: tuple = ()):
        with self._connect() as conn:
            cur = conn.execute(query, params)
            conn.commit()
            return cur.rowcount


def configure_db(path: Path) -> SQLiteDB:
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                job_type TEXT,
                status TEXT,
                params_json TEXT,
                metadata_json TEXT,
                task_id INTEGER,
                project_id TEXT,
                tool_key TEXT,
                z_context TEXT,
                run_dir TEXT,
                created_at TEXT,
                updated_at TEXT,
                completed_at TEXT,
                result_json TEXT,
                error TEXT
            );
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY,
                status TEXT,
                updated_at TEXT,
                metadata_json TEXT
            );
            """
        )
    return SQLiteDB(path)


def configure_shell(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "N.py").write_text("# test shell\n", encoding="utf-8")
    runtime_exports = (
        root
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "runtime_exports"
    )
    runtime_exports.mkdir(parents=True, exist_ok=True)
    (runtime_exports / "merovingian_supervisor.lock.json").write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "heartbeat_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "interval_seconds": 60,
                "state": "pass",
            }
        ),
        encoding="utf-8",
    )


def write_command(root: Path, command_id: str, **overrides) -> None:
    path = ls_go_job_consumer._queue_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "lightspeed-go-command-v1",
        "command_id": command_id,
        "source": "LS GO",
        "title": "Test transport",
        "instruction": "Bounded diagnostic only.",
        "target_floor": "Neo",
        "oversight_floor": "Achilles",
        "priority": "high",
        "execution_mode": "queue",
        "state": "queued",
        "proof_required": True,
        "public_safe": True,
    }
    payload.update(overrides)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload) + "\n")


def test_consumer_closes_existing_go_task_0016_once(tmp_path: Path):
    shell = tmp_path / "App"
    configure_shell(shell)
    write_command(shell, "GO-TASK-0016")
    db = configure_db(tmp_path / "lightspeed.db")
    now = datetime.now(UTC).isoformat(timespec="seconds")
    with sqlite3.connect(db.path) as conn:
        conn.execute(
            "INSERT INTO tasks (id, status, updated_at, metadata_json) VALUES (486, 'queued', ?, '{}')",
            (now,),
        )
        conn.execute(
            """
            INSERT INTO jobs
              (id, job_type, status, params_json, metadata_json, task_id, project_id, tool_key, z_context, created_at, updated_at)
            VALUES
              (490022, 'ls_go_command', 'pending', ?, '{}', 486, 'LS-GO', 'ls_go_command', 'Neo', ?, ?)
            """,
            (json.dumps({"command_id": "GO-TASK-0016", "instruction": "diagnostic"}), now, now),
        )
        conn.commit()

    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    first = consumer.process_once()

    assert first["results_written"] == 1
    assert first["result_ids"] == ["GO-RESULT-0016"]
    receipt = json.loads(
        ls_go_job_consumer.result_file_path(shell, "GO-TASK-0016").read_text(encoding="utf-8")
    )
    assert receipt["status"] == "completed"
    assert receipt["job_id"] == 490022
    assert receipt["task_id"] == 486
    assert receipt["checks"]["command_identity_exactly_once"] is True
    assert receipt["action_source"] == "compatibility_contract"
    assert receipt["drive_write_executed"] is False

    assert db.execute_query("SELECT status FROM jobs WHERE id = 490022")[0]["status"] == "completed"
    assert db.execute_query("SELECT status FROM tasks WHERE id = 486")[0]["status"] == "completed"

    result_queue = ls_go_job_consumer.result_queue_path(shell)
    assert len(result_queue.read_text(encoding="utf-8").splitlines()) == 1

    second = consumer.process_once()
    assert second["results_written"] == 0
    assert len(result_queue.read_text(encoding="utf-8").splitlines()) == 1


def test_untyped_free_form_job_is_held_not_executed(tmp_path: Path):
    shell = tmp_path / "App"
    configure_shell(shell)
    write_command(shell, "GO-TASK-9999")
    db = configure_db(tmp_path / "lightspeed.db")
    now = datetime.now(UTC).isoformat(timespec="seconds")
    with sqlite3.connect(db.path) as conn:
        conn.execute(
            "INSERT INTO tasks (id, status, updated_at, metadata_json) VALUES (999, 'queued', ?, '{}')",
            (now,),
        )
        conn.execute(
            """
            INSERT INTO jobs
              (id, job_type, status, params_json, metadata_json, task_id, project_id, tool_key, z_context, created_at, updated_at)
            VALUES
              (1000, 'ls_go_command', 'pending', ?, '{}', 999, 'LS-GO', 'ls_go_command', 'Smith', ?, ?)
            """,
            (
                json.dumps(
                    {
                        "command_id": "GO-TASK-9999",
                        "instruction": "rm -rf / should never be interpreted as a command",
                    }
                ),
                now,
                now,
            ),
        )
        conn.commit()

    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    summary = consumer.process_once()

    assert summary["results_written"] == 1
    receipt = json.loads(
        ls_go_job_consumer.result_file_path(shell, "GO-TASK-9999").read_text(encoding="utf-8")
    )
    assert receipt["status"] == "held"
    assert receipt["action_type"] is None
    assert "not executable" in receipt["error"]
    assert db.execute_query("SELECT status FROM jobs WHERE id = 1000")[0]["status"] == "held"
    assert db.execute_query("SELECT status FROM tasks WHERE id = 999")[0]["status"] == "held"


def test_typed_review_only_job_executes_without_source_mutation(tmp_path: Path, monkeypatch):
    shell = tmp_path / "App"
    configure_shell(shell)
    write_command(shell, "GO-TASK-0100")
    db = configure_db(tmp_path / "lightspeed.db")
    now = datetime.now(UTC).isoformat(timespec="seconds")
    with sqlite3.connect(db.path) as conn:
        conn.execute(
            "INSERT INTO tasks (id, status, updated_at, metadata_json) VALUES (100, 'queued', ?, '{}')",
            (now,),
        )
        conn.execute(
            """
            INSERT INTO jobs
              (id, job_type, status, params_json, metadata_json, task_id, project_id, tool_key, z_context, created_at, updated_at)
            VALUES
              (101, 'ls_go_command', 'pending', ?, '{}', 100, 'LS-GO', 'ls_go_command', 'Morpheus', ?, ?)
            """,
            (
                json.dumps({"command_id": "GO-TASK-0100", "action_type": "review_only"}),
                now,
                now,
            ),
        )
        conn.commit()

    ticks = iter((1_000_000_000, 2_234_567_890))
    monkeypatch.setattr(ls_go_job_consumer.time, "monotonic_ns", lambda: next(ticks))
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    summary = consumer.process_once()

    assert summary["results_written"] == 1
    receipt = json.loads(
        ls_go_job_consumer.result_file_path(shell, "GO-TASK-0100").read_text(encoding="utf-8")
    )
    assert receipt["status"] == "completed"
    assert receipt["action_type"] == "review_only"
    assert receipt["action_source"] == "typed_action"
    assert receipt["action_wall_elapsed_ms"] == 1234
    assert receipt["action_wall_clock_budget_enforced"] is False
    assert receipt["public_publish_authorized"] is False
    assert consumer.process_once()["results_written"] == 0
    assert json.loads(ls_go_job_consumer.result_file_path(shell, "GO-TASK-0100").read_text())[
        "action_wall_elapsed_ms"
    ] == 1234


def test_typed_cognigrex_workflow_routes_to_supervisor(tmp_path: Path, monkeypatch):
    shell = tmp_path / "App"
    configure_shell(shell)
    write_command(shell, "GO-TASK-0200")
    db = configure_db(tmp_path / "lightspeed.db")
    now = datetime.now(UTC).isoformat(timespec="seconds")
    with sqlite3.connect(db.path) as conn:
        conn.execute(
            "INSERT INTO tasks (id, status, updated_at, metadata_json) VALUES (200, 'queued', ?, '{}')",
            (now,),
        )
        conn.execute(
            """
            INSERT INTO jobs
              (id, job_type, status, params_json, metadata_json, task_id, project_id, tool_key, z_context, created_at, updated_at)
            VALUES
              (201, 'ls_go_command', 'pending', ?, '{}', 200, 'LS-GO', 'ls_go_command', 'Neo', ?, ?)
            """,
            (
                json.dumps(
                    {
                        "command_id": "GO-TASK-0200",
                        "action_type": "cognigrex_workflow",
                        "instruction": "Reconcile one bounded source and verify its receipt.",
                        "execute": False,
                    }
                ),
                now,
                now,
            ),
        )
        conn.commit()

    seen = {}

    def fake_supervisor(instruction, **kwargs):
        seen["instruction"] = instruction
        seen.update(kwargs)
        return {
            "status": "complete",
            "complete_workflow": True,
            "workflow_id": "cognigrex-test",
            "floors": [],
        }

    monkeypatch.setattr(ls_go_job_consumer, "run_supervised_workflow", fake_supervisor)
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    summary = consumer.process_once()

    assert summary["results_written"] == 1
    receipt = json.loads(
        ls_go_job_consumer.result_file_path(shell, "GO-TASK-0200").read_text(encoding="utf-8")
    )
    assert receipt["status"] == "completed"
    assert receipt["action_type"] == "cognigrex_workflow"
    assert receipt["workflow"]["workflow_id"] == "cognigrex-test"
    assert seen["instruction"] == "Reconcile one bounded source and verify its receipt."
    assert seen["dry_run"] is True


def test_typed_rfs_emff_sweep_reuses_job_identity_and_stays_local(
    tmp_path: Path, monkeypatch
):
    shell = tmp_path / "App"
    configure_shell(shell)
    action_payload = {
        "schema_version": "lightspeed-rfs-emff-sweep-request-v1",
        "base_case": {
            "rfs": {
                "frequency_hz": 10.0,
                "displacement_amplitude_m": 0.001,
                "particle_diameter_m": 0.001,
                "particle_density_kg_m3": 7800.0,
            }
        },
        "axes": [{"path": "rfs.frequency_hz", "values": [10.0, 20.0]}],
    }
    write_command(
        shell,
        "LSGO-RFS-EMFF-0300",
        schema_version="lightspeed-go-command-v2",
        action_type="rfs_emff_sweep",
        action_payload=action_payload,
        target_floor="TheConstruct",
    )
    db = configure_db(tmp_path / "lightspeed.db")
    now = datetime.now(UTC).isoformat(timespec="seconds")
    with sqlite3.connect(db.path) as conn:
        conn.execute(
            "INSERT INTO tasks (id, status, updated_at, metadata_json) VALUES (300, 'queued', ?, '{}')",
            (now,),
        )
        conn.execute(
            """
            INSERT INTO jobs
              (id, job_type, status, params_json, metadata_json, task_id, project_id, tool_key, z_context, created_at, updated_at)
            VALUES
              (301, 'ls_go_command', 'pending', ?, '{}', 300, 'LS-GO', 'ls_go_command', 'TheConstruct', ?, ?)
            """,
            (
                json.dumps(
                    {
                        "command_id": "LSGO-RFS-EMFF-0300",
                        "action_type": "rfs_emff_sweep",
                        "action_payload": action_payload,
                        "execution_mode": "queue",
                        "execute": True,
                        "allow_heavy": False,
                    }
                ),
                now,
                now,
            ),
        )
        conn.commit()

    seen = {}

    def fake_sweep(payload, **kwargs):
        seen["payload"] = payload
        seen.update(kwargs)
        return {
            "status": "completed",
            "idempotent_replay": False,
            "manifest_path": str(tmp_path / "manifest.json"),
            "drive_write_executed": False,
            "public_publish_authorized": False,
        }

    monkeypatch.setattr(ls_go_job_consumer, "execute_rfs_emff_sweep", fake_sweep)
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    summary = consumer.process_once()

    assert summary["results_written"] == 1
    receipt = json.loads(
        ls_go_job_consumer.result_file_path(shell, "LSGO-RFS-EMFF-0300").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["status"] == "completed"
    assert receipt["action_type"] == "rfs_emff_sweep"
    assert receipt["target_floor"] == "TheConstruct"
    assert receipt["drive_write_executed"] is False
    assert receipt["public_publish_authorized"] is False
    assert seen == {
        "payload": action_payload,
        "command_id": "LSGO-RFS-EMFF-0300",
        "task_id": 300,
        "job_id": 301,
        "shell_root": shell.absolute(),
        "allow_heavy": False,
    }
    with sqlite3.connect(db.path) as conn:
        job_status = conn.execute("SELECT status FROM jobs WHERE id = 301").fetchone()[0]
        task_status = conn.execute("SELECT status FROM tasks WHERE id = 300").fetchone()[0]
    assert job_status == "completed"
    assert task_status == "completed"


def test_rfs_emff_dispatch_uses_executor_validator_and_command_identity(
    tmp_path: Path, monkeypatch
):
    payload = {
        "schema_version": "lightspeed-rfs-emff-sweep-request-v1",
        "base_case": {"rfs": {"frequency_hz": 10.0}},
        "axes": [{"path": "rfs.frequency_hz", "values": [10.0]}],
    }
    seen = {}

    def validate(value):
        seen["validated"] = value
        return {**value, "normalized": True}

    def execute(value, **kwargs):
        seen["executed"] = value
        seen.update(kwargs)
        return {"status": "completed", "drive_write_executed": False}

    class ExecutorModule:
        validate_sweep_request = staticmethod(validate)
        execute_sweep = staticmethod(execute)

    monkeypatch.setattr(
        ls_go_job_consumer.importlib,
        "import_module",
        lambda name: ExecutorModule if name == "lightspeed_runtime.rfs_emff_sweep" else None,
    )

    result = ls_go_job_consumer.execute_rfs_emff_sweep(
        payload,
        command_id="LSGO-RFS-EMFF-DISPATCH",
        task_id=400,
        job_id=401,
        shell_root=tmp_path,
        allow_heavy=False,
    )

    assert result["status"] == "completed"
    assert seen["validated"] == payload
    assert seen["executed"]["normalized"] is True
    assert seen["command_id"] == "LSGO-RFS-EMFF-DISPATCH"
    assert seen["task_id"] == 400
    assert seen["job_id"] == 401
    assert seen["shell_root"] == tmp_path
    assert seen["allow_heavy"] is False


def test_smith_receipt_paths_are_injective_for_colliding_labels(tmp_path: Path) -> None:
    from hashlib import sha256

    shell = tmp_path / "App"
    values = ["CMD/a", "CMD_a", "CMD?a", "CMD a", "CMD/a_", "GO-TASK/a",
              "GO-TASK_a", "GO-TASK?a", "Ω", "unknown", "a" * 200]
    paths = [ls_go_job_consumer.result_file_path(shell, command_id) for command_id in values]
    assert len(paths) == len(set(paths))
    assert all(path.name.endswith(".json") and len(path.name) < 160 for path in paths)
    for command_id, path in zip(values, paths):
        assert sha256(command_id.encode("utf-8")).hexdigest() in path.name
        assert path.parent.name == "results"


def test_smith_existing_receipt_legacy_read_is_exact_identity_only(tmp_path: Path) -> None:
    shell = tmp_path / "App"
    smith = ls_go_job_consumer.LSGoJobConsumer(shell)
    older = ls_go_job_consumer._legacy_result_file_path(shell, "CMD/a")
    older.parent.mkdir(parents=True, exist_ok=True)
    older.write_text(json.dumps({"command_id": "CMD/a", "status": "completed"}),
                     encoding="utf-8")
    assert smith._existing_result("CMD/a")["status"] == "completed"
    # Two different source IDs sharing an old safe name must never reuse a receipt.
    assert smith._existing_result("CMD_a") == {}

    newer = ls_go_job_consumer.result_file_path(shell, "CMD/a")
    newer.write_text(json.dumps({"command_id": "CMD/a", "status": "held"}),
                     encoding="utf-8")
    assert smith._existing_result("CMD/a")["status"] == "held"


def test_smith_missing_command_id_receipts_are_job_specific(tmp_path: Path) -> None:
    smith = ls_go_job_consumer.LSGoJobConsumer(tmp_path / "App")
    first = smith._persist_result({"command_id": None, "job_id": 101, "status": "held"})
    second = smith._persist_result({"command_id": None, "job_id": 102, "status": "held"})
    assert first["receipt_path"] != second["receipt_path"]
    assert json.loads(Path(first["receipt_path"]).read_text(encoding="utf-8"))["job_id"] == 101
    assert json.loads(Path(second["receipt_path"]).read_text(encoding="utf-8"))["job_id"] == 102


def test_smith_reconciles_only_the_exact_job_and_task_after_receipt_first_crash(
    tmp_path: Path, monkeypatch
) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    command_id = "GO-TASK-CRASH-RECOVERY"
    params = json.dumps({"command_id": command_id})
    with sqlite3.connect(db.path) as conn:
        conn.executemany(
            "INSERT INTO tasks (id,status,metadata_json) VALUES (?,?, '{}')",
            [(501, "queued"), (502, "queued")],
        )
        conn.executemany(
            "INSERT INTO jobs (id,job_type,status,params_json,task_id) "
            "VALUES (?,'ls_go_command','pending',?,?)",
            [(601, params, 501), (602, params, 502)],
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    original = consumer._persist_result({
        "command_id": command_id, "job_id": 601, "task_id": 501,
        "result_id": "GO-RESULT-CRASH-RECOVERY", "status": "completed",
    })
    monkeypatch.setattr(consumer, "_execute_action", lambda **_kw: (_ for _ in ()).throw(
        AssertionError("receipt reconciliation must not execute an action")))

    assert consumer.process_once()["results_written"] == 2
    assert db.execute_query("SELECT status FROM jobs WHERE id=601")[0]["status"] == "completed"
    assert db.execute_query("SELECT status FROM tasks WHERE id=501")[0]["status"] == "completed"
    assert db.execute_query("SELECT status FROM jobs WHERE id=602")[0]["status"] == "held"
    assert db.execute_query("SELECT status FROM tasks WHERE id=502")[0]["status"] == "held"
    assert json.loads(Path(original["receipt_path"]).read_text())["job_id"] == 601
    hold_path = ls_go_job_consumer.identity_hold_file_path(shell, command_id, 602, 502)
    assert json.loads(hold_path.read_text())["status"] == "held"
    assert len(ls_go_job_consumer.result_queue_path(shell).read_text().splitlines()) == 2
    assert consumer.process_once()["results_written"] == 0
    assert len(ls_go_job_consumer.result_queue_path(shell).read_text().splitlines()) == 2
    # Simulate a crash after the hold receipt but before the DB status landed.
    db.execute_update("UPDATE jobs SET status='pending' WHERE id=602")
    assert consumer.process_once()["results_written"] == 1
    assert db.execute_query("SELECT status FROM jobs WHERE id=602")[0]["status"] == "held"
    assert len(ls_go_job_consumer.result_queue_path(shell).read_text().splitlines()) == 2


def test_smith_duplicate_job_cannot_regress_original_task(tmp_path: Path) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    command_id = "GO-TASK-SHARED-TASK"
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'completed','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,task_id) "
            "VALUES (602,'ls_go_command','pending',?,501)",
            (json.dumps({"command_id": command_id}),),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    original = consumer._persist_result({
        "command_id": command_id, "job_id": 601, "task_id": 501,
        "status": "completed", "result_id": "GO-RESULT-SHARED-TASK",
    })

    assert consumer.process_once()["results_written"] == 1
    assert db.execute_query("SELECT status FROM jobs WHERE id=602")[0]["status"] == "held"
    assert db.execute_query("SELECT status FROM tasks WHERE id=501")[0]["status"] == "completed"
    assert json.loads(Path(original["receipt_path"]).read_text())["job_id"] == 601



def test_host_cpu_dispatch_gate_hysteresis(tmp_path):
    root = tmp_path / "App"
    (root / "config").mkdir(parents=True)
    (root / "config" / "host_runtime_policy.json").write_text(
        json.dumps({"runtime_limits": {
            "max_total_host_cpu_percent": 80,
            "cpu_dispatch_resume_percent": 70,
            "cpu_sampling_interval_seconds": 0.25,
            "max_background_queue_workers": 1,
        }}), encoding="utf-8")
    gate = ls_go_job_consumer.host_cpu_admission
    assert gate(root, observed_percent=60)["allow_new_jobs"] is True
    high=gate(root, observed_percent=80)
    assert high["state"] == "paused_cpu_pressure"
    assert high["allow_new_jobs"] is False
    assert high["aggregate_cpu_hard_cap_verified"] is False
    assert gate(root, observed_percent=75, previous_hold=True)["allow_new_jobs"] is False
    assert gate(root, observed_percent=70, previous_hold=True)["allow_new_jobs"] is True
    assert gate(root, observed_percent=79.9, previous_hold=False)["allow_new_jobs"] is True


def test_host_cpu_dispatch_missing_monitor_invalid_policy_and_no_mobile(tmp_path):
    root=tmp_path / "App"
    (root / "config").mkdir(parents=True)
    (root / "config" / "host_runtime_policy.json").write_text(
        json.dumps({"runtime_limits": {"max_total_host_cpu_percent": 80,
                                      "cpu_dispatch_resume_percent": 70}}),
        encoding="utf-8")
    gate=ls_go_job_consumer.host_cpu_admission
    import math
    for val in [float("nan"),-1,120,True]:
        assert gate(root,observed_percent=val)["state"] == "cpu_monitor_unavailable"
    sample=gate(root,observed_percent=55)
    assert sample["mobile_device_required"] is False
    assert sample["cpu_control_scope"]=="DISPATCH_ADMISSION_ONLY"
    assert not sample["aggregate_cpu_hard_cap_verified"]
    (root / "config" / "host_runtime_policy.json").write_text(
        json.dumps({"runtime_limits": {"max_total_host_cpu_percent": 100,
                                      "cpu_dispatch_resume_percent": 75}}),
        encoding="utf-8")
    assert gate(root,observed_percent=12)["state"]=="cpu_policy_invalid"


def test_live_consumer_keeps_heartbeat_without_claiming_at_high_cpu(tmp_path, monkeypatch):
    root=tmp_path / "App"
    consumer=ls_go_job_consumer.LSGoJobConsumer(root, db=None)
    samples = iter([80, 74, 70])
    calls={"job":0,"heartbeat":[],"wait":0}
    monkeypatch.setattr(ls_go_job_consumer,"host_cpu_admission",
        lambda _root, previous_hold=False: ls_go_job_consumer.host_cpu_admission.__wrapped__(_root)
        if False else {
            "allow_new_jobs": (v:=next(samples)) <= 70,
            "state": "paused_cpu_pressure" if v>70 else "ready",
            "measured_total_cpu_percent": v, "aggregate_cpu_hard_cap_verified": False,
        })
    monkeypatch.setattr(consumer,"_acquire_heartbeat_lock",lambda: None)
    monkeypatch.setattr(consumer,"process_once",lambda: calls.__setitem__("job",calls["job"]+1) or {"state":"ready"})
    monkeypatch.setattr(consumer,"_heartbeat",lambda state: calls["heartbeat"].append(state))
    monkeypatch.setattr(consumer._stop,"wait",lambda _s: calls.__setitem__("wait",calls["wait"]+1) or (consumer.stop() if calls["wait"]>=3 else None))
    consumer.run_forever(poll_seconds=0.25)
    assert calls["job"]==1
    assert calls["heartbeat"]==["paused_cpu_pressure","paused_cpu_pressure","ready"]
    assert (ls_go_job_consumer.status_receipt_path(root)).exists()
