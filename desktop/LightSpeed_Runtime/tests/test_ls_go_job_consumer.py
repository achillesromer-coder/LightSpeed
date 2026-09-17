from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sqlite3
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime import ls_go_job_consumer


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


def test_typed_review_only_job_executes_without_source_mutation(tmp_path: Path):
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

    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    summary = consumer.process_once()

    assert summary["results_written"] == 1
    receipt = json.loads(
        ls_go_job_consumer.result_file_path(shell, "GO-TASK-0100").read_text(encoding="utf-8")
    )
    assert receipt["status"] == "completed"
    assert receipt["action_type"] == "review_only"
    assert receipt["action_source"] == "typed_action"
    assert receipt["public_publish_authorized"] is False


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
