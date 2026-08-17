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


def write_command(root: Path, command_id: str) -> None:
    path = ls_go_job_consumer._queue_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(
            json.dumps(
                {
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
            )
            + "\n"
        )


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
