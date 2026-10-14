from __future__ import annotations

from datetime import UTC, datetime
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import sys
import hashlib
import pytest

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
    persisted_claim = json.loads(db.execute_query("SELECT metadata_json FROM jobs WHERE id=502")[0]["metadata_json"])["ls_go_execution_claim"]
    assert result["execution_claim"] == persisted_claim
    assert persisted_claim["purpose"] == "execute"
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


def test_restart_rejects_receipt_from_different_claim(tmp_path: Path) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    command_id = "GO-TASK-CLAIM-MISMATCH"
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'queued','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)",
            (json.dumps({"command_id": command_id}),),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    assert consumer._claim_job(601, expected_job=consumer.pending_jobs()[0])
    consumer._persist_result({
        "command_id": command_id, "job_id": 601, "task_id": 501,
        "result_id": ls_go_job_consumer.result_id_for(command_id),
        "status": "completed", "completed_utc": ls_go_job_consumer.utc_now_iso(),
        "execution_claim": {"claim_id": "other-attempt"},
    })
    assert consumer._reconcile_running_job_receipt(601) is False
    assert db.execute_query("SELECT status FROM jobs WHERE id=601")[0]["status"] == "running"
    assert db.execute_query("SELECT status FROM tasks WHERE id=501")[0]["status"] == "queued"
    consumer._persist_result({
        "command_id": command_id, "job_id": 601, "task_id": 501,
        "result_id": ls_go_job_consumer.result_id_for(command_id),
        "status": "completed", "completed_utc": ls_go_job_consumer.utc_now_iso(),
        "execution_claim": consumer._execution_claims[601],
    })
    assert consumer._reconcile_running_job_receipt(601) is True
    assert db.execute_query("SELECT status FROM jobs WHERE id=601")[0]["status"] == "completed"
    assert db.execute_query("SELECT status FROM tasks WHERE id=501")[0]["status"] == "completed"


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


def test_claim_binds_exact_work_and_rejects_replay_after_status_reset(tmp_path: Path) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    params_json = json.dumps({"command_id": "GO-TASK-CLAIM", "action_type": "review_only"})
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status) VALUES (501,'queued')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)",
            (params_json,),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    selected = consumer.pending_jobs()[0]
    assert consumer._claim_job(601, expected_job=selected)
    stored = db.execute_query("SELECT status,metadata_json FROM jobs WHERE id=601")[0]
    claim = json.loads(stored["metadata_json"])["ls_go_execution_claim"]
    assert stored["status"] == "running"
    assert claim["claim_id"] == consumer._execution_claims[601]["claim_id"]
    assert claim["job_id"] == 601 and claim["task_id"] == 501
    assert claim["command_id"] == "GO-TASK-CLAIM"
    assert claim["lease_schema"] == "LSGO-CLAIM-LEASE/0.1"
    assert claim["job_params_sha256"] == hashlib.sha256(params_json.encode()).hexdigest()
    assert datetime.fromisoformat(claim["started_utc"]) < datetime.fromisoformat(claim["lease_expires_utc"])
    assert (datetime.fromisoformat(claim["lease_expires_utc"])
            - datetime.fromisoformat(claim["started_utc"])).total_seconds() == 900
    assert not consumer._claim_job(601, expected_job=selected)
    db.execute_update("UPDATE jobs SET status='pending' WHERE id=601")
    with pytest.raises(RuntimeError, match="prior execution claim"):
        consumer._claim_job(601, expected_job=selected)
    assert db.execute_query("SELECT status FROM jobs WHERE id=601")[0]["status"] == "pending"


def test_source_intake_live_claim_check_rejects_cancelled_job(tmp_path: Path) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    params_json = json.dumps({"command_id": "GO-TASK-INTAKE-LEASE", "action_type": "source_preserving_intake"})
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status) VALUES (501,'queued')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)", (params_json,),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    assert consumer._claim_job(601, expected_job=consumer.pending_jobs()[0])
    consumer._require_live_claim(601)
    db.execute_update("UPDATE jobs SET status='held' WHERE id=601")
    with pytest.raises(RuntimeError, match="revoked or changed"):
        consumer._require_live_claim(601)


def test_expired_claim_blocks_work_terminal_write_and_restart_reconciliation(tmp_path: Path) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    command_id = "GO-TASK-EXPIRED-LEASE"
    params_json = json.dumps({"command_id": command_id, "action_type": "review_only"})
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'queued','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)", (params_json,),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    assert consumer._claim_job(601, expected_job=consumer.pending_jobs()[0])
    claim = consumer._execution_claims[601]
    changed = dict(claim, lease_expires_utc="2099-01-01T00:00:00+00:00")
    db.execute_update(
        "UPDATE jobs SET metadata_json=? WHERE id=601",
        (json.dumps({"ls_go_execution_claim": changed}),),
    )
    with pytest.raises(RuntimeError, match="revoked or changed"):
        consumer._require_live_claim(601)
    claim["lease_expires_utc"] = "2000-01-01T00:00:00+00:00"
    db.execute_update(
        "UPDATE jobs SET metadata_json=? WHERE id=601",
        (json.dumps({"ls_go_execution_claim": claim}),),
    )
    with pytest.raises(RuntimeError, match="lease expired"):
        consumer._require_live_claim(601)
    receipt = {
        "command_id": command_id, "job_id": 601, "task_id": 501,
        "result_id": ls_go_job_consumer.result_id_for(command_id),
        "status": "completed", "completed_utc": ls_go_job_consumer.utc_now_iso(),
        "execution_claim": claim,
    }
    with pytest.raises(RuntimeError, match="lease expired"):
        consumer._finish_claimed_job(601, receipt=receipt)
    consumer._persist_result(receipt)
    assert consumer._reconcile_running_job_receipt(601) is False
    assert db.execute_query("SELECT status FROM jobs WHERE id=601")[0]["status"] == "running"


def test_claim_holds_when_selected_job_identity_changes(tmp_path: Path) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    with sqlite3.connect(db.path) as conn:
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending','{}','{}',501)"
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    selected = consumer.pending_jobs()[0]
    db.execute_update("UPDATE jobs SET task_id=502 WHERE id=601")
    with pytest.raises(RuntimeError, match="identity changed"):
        consumer._claim_job(601, expected_job=selected)
    stored = db.execute_query("SELECT status,metadata_json FROM jobs WHERE id=601")[0]
    assert stored == {"status": "pending", "metadata_json": "{}"}


def test_cancelled_job_fences_terminal_receipt_and_preserves_task(tmp_path: Path, monkeypatch) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    command_id = "GO-TASK-CANCEL-FENCE"
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'queued','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)",
            (json.dumps({"command_id": command_id, "action_type": "review_only"}),),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)

    def cancel_while_action_runs(**_kwargs):
        db.execute_update("UPDATE jobs SET status='cancelled' WHERE id=601")
        return {"status": "completed", "action_type": "review_only"}

    monkeypatch.setattr(consumer, "_execute_action", cancel_while_action_runs)
    with pytest.raises(RuntimeError, match="terminal write fenced"):
        consumer.process_once()
    assert db.execute_query("SELECT status,result_json FROM jobs WHERE id=601")[0] == {
        "status": "cancelled", "result_json": None,
    }
    assert db.execute_query("SELECT status FROM tasks WHERE id=501")[0]["status"] == "queued"


def test_task_write_failure_rolls_back_claimed_job_commit(tmp_path: Path) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    params = json.dumps({"command_id": "GO-TASK-ATOMIC"})
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'queued','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)", (params,),
        )
        conn.execute(
            "CREATE TRIGGER reject_task_terminal BEFORE UPDATE OF status ON tasks "
            "BEGIN SELECT RAISE(ABORT, 'task write failed'); END"
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    assert consumer._claim_job(601, expected_job=consumer.pending_jobs()[0])
    receipt = {
        "job_id": 601, "task_id": 501, "command_id": "GO-TASK-ATOMIC",
        "status": "completed", "result_id": "GO-RESULT-ATOMIC",
        "execution_claim": consumer._execution_claims[601],
    }
    with pytest.raises(sqlite3.IntegrityError, match="task write failed"):
        consumer._finish_claimed_job(601, receipt=receipt)
    assert db.execute_query("SELECT status,result_json FROM jobs WHERE id=601")[0] == {
        "status": "running", "result_json": None,
    }
    assert db.execute_query("SELECT status FROM tasks WHERE id=501")[0]["status"] == "queued"


def test_frontier_admission_binds_claim_but_holds_unenforced_action(tmp_path: Path, monkeypatch) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    request = {
        "domain": "COGNIGREX", "object_id": "cgx://RFS-001", "owner": "COGNIGREX",
        "source_sha256": "a" * 64, "operation": "admit_and_test",
        "acceptance_version": "v1", "evidence_class": "COMPUTED",
        "source_changed": True, "dependencies_changed": False,
        "limits": {"max_elapsed_s": 600, "max_tokens": 8000,
                   "max_tool_calls": 12, "max_retries": 1, "max_cost_usd": 0.25},
        "usage": {"elapsed_s": 0, "tokens": 0, "tool_calls": 0,
                  "retries": 0, "cost_usd": 0.0},
    }
    params = {
        "command_id": "GO-TASK-FRONTIER-CLAIM", "action_type": "review_only",
        "action_payload": {"frontier_request": request},
    }
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'queued','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)",
            (json.dumps(params),),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    monkeypatch.setattr(consumer, "_execute_action", lambda **_kw: (_ for _ in ()).throw(
        AssertionError("unmetered frontier action must not execute")))
    assert consumer.process_once()["results_written"] == 1
    job = db.execute_query("SELECT status,metadata_json,result_json FROM jobs WHERE id=601")[0]
    claim = json.loads(job["metadata_json"])["ls_go_execution_claim"]
    result = json.loads(job["result_json"])
    assert job["status"] == "held"
    assert result["execution_claim"] == claim
    assert claim["frontier_admission"]["verdict"] == "READY_FOR_BOUNDED_WORK"
    assert claim["frontier_admission"]["work_key"]
    assert result["frontier_admission"]["native_execution_authorized"] is False
    assert db.execute_query("SELECT status FROM tasks WHERE id=501")[0]["status"] == "held"


def test_invalid_frontier_request_is_durably_held_without_action(tmp_path: Path, monkeypatch) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    params = {
        "command_id": "GO-TASK-FRONTIER-INVALID", "action_type": "review_only",
        "action_payload": {"frontier_request": {"source_sha256": "invalid"}},
    }
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'queued','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)",
            (json.dumps(params),),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    monkeypatch.setattr(consumer, "_execute_action", lambda **_kw: (_ for _ in ()).throw(
        AssertionError("invalid frontier action must not execute")))
    assert consumer.process_once()["results_written"] == 1
    job = db.execute_query("SELECT status,metadata_json FROM jobs WHERE id=601")[0]
    decision = json.loads(job["metadata_json"])["ls_go_execution_claim"]["frontier_admission"]
    assert job["status"] == "held"
    assert decision["verdict"] == "HOLD"
    assert decision["work_key"] is None
    assert decision["reason"].startswith("INVALID_FRONTIER_REQUEST:")


def test_floor_usage_is_retained_in_existing_job_result(tmp_path: Path, monkeypatch) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    command_id = "GO-TASK-FLOOR-USAGE"
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'queued','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)",
            (json.dumps({"command_id": command_id, "action_type": "local_floor_wakeup",
                         "floor": "Neo"}),),
        )
    usage = {
        "state": "MEASURED_OLLAMA_RESPONSE", "prompt_tokens": 17,
        "completion_tokens": 5, "total_tokens": 22,
        "ollama_generate_attempts": 1, "tool_calls": 0,
        "tool_call_scope": "model_function_tools_not_exposed_by_local_generate",
        "cost_usd": None, "budget_enforced": False,
    }
    monkeypatch.setattr(ls_go_job_consumer.LSGoJobConsumer, "_run_floor_supervised", lambda self, **_kw: {
        "status": "completed", "receipt_id": "floor-proof-1", "usage_accounting": usage,
    })
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    assert consumer.process_once()["results_written"] == 1
    result = json.loads(db.execute_query("SELECT result_json FROM jobs WHERE id=601")[0]["result_json"])
    assert result["floor_receipt"]["usage_accounting"] == usage
    persisted_claim = json.loads(db.execute_query(
        "SELECT metadata_json FROM jobs WHERE id=601")[0]["metadata_json"])["ls_go_execution_claim"]
    assert persisted_claim["native_budget"] == ls_go_job_consumer.FLOOR_NATIVE_BUDGET
    assert result["execution_claim"]["native_budget"] == persisted_claim["native_budget"]
    assert result["floor_supervision"] == {
        "client_wall_deadline_seconds": 185,
        "requested_completion_token_cap": 1024,
        "total_token_postflight_ceiling": 2048,
        "source_excerpt_char_cap": 600,
        "prompt_utf8_byte_ceiling": 7000,
        "server_cancellation_verified": False,
    }
    assert result["action_wall_elapsed_ms"] >= 0
    assert result["action_wall_clock_budget_enforced"] is False


def test_persisted_floor_budget_change_revokes_execution_claim(tmp_path: Path) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    params = {"command_id": "GO-TASK-FLOOR-BUDGET", "action_type": "local_floor_wakeup",
              "floor": "Neo"}
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'queued','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)", (json.dumps(params),),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    assert consumer._claim_job(601, expected_job=consumer.pending_jobs()[0])
    consumer._require_live_claim(601)
    metadata = json.loads(db.execute_query(
        "SELECT metadata_json FROM jobs WHERE id=601")[0]["metadata_json"])
    metadata["ls_go_execution_claim"]["native_budget"]["total_token_postflight_ceiling"] = 4096
    db.execute_update("UPDATE jobs SET metadata_json=? WHERE id=601", (json.dumps(metadata),))
    with pytest.raises(RuntimeError, match="revoked or changed"):
        consumer._require_live_claim(601)


@pytest.mark.parametrize("reason", ["revoked", "deadline", "shutdown"])
def test_supervised_floor_stops_worker_before_another_job(tmp_path: Path, monkeypatch, reason: str) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=object())
    consumer._execution_claims[601] = {
        "claim_id": "a" * 32, "native_budget": dict(ls_go_job_consumer.FLOOR_NATIVE_BUDGET),
    }

    class Child:
        terminated = False
        returncode = None

        def communicate(self, timeout=None):
            if not self.terminated:
                raise ls_go_job_consumer.subprocess.TimeoutExpired("floor", timeout)
            self.returncode = -15
            return ("", None)

        def terminate(self):
            self.terminated = True

    child = Child()
    def start(*_args, **_kwargs):
        if reason == "shutdown":
            consumer._stop.set()
        return child

    monkeypatch.setattr(ls_go_job_consumer.subprocess, "Popen", start)
    if reason == "revoked":
        checks = 0

        def check(_job_id):
            nonlocal checks
            checks += 1
            if checks == 2:
                raise RuntimeError("claim revoked")

        monkeypatch.setattr(consumer, "_require_live_claim", check)
        expected = ls_go_job_consumer.FloorExecutionUncertain
    elif reason == "deadline":
        monkeypatch.setattr(consumer, "_require_live_claim", lambda _job_id: None)
        ticks = iter([0.0, 186.0])
        monkeypatch.setattr(ls_go_job_consumer.time, "monotonic", lambda: next(ticks))
        expected = ls_go_job_consumer.FloorExecutionUncertain
    else:
        monkeypatch.setattr(consumer, "_require_live_claim", lambda _job_id: None)
        expected = ls_go_job_consumer.FloorExecutionUncertain
    with pytest.raises(expected):
        consumer._run_floor_supervised(job_id=601, floor="Neo", allow_heavy=False, receipt_target="neo")
    assert child.terminated
    assert consumer._stop.is_set()


def test_uncertain_floor_cancellation_retains_running_claim_for_restart(tmp_path: Path, monkeypatch) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    command_id = "GO-TASK-UNCERTAIN-FLOOR"
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'queued','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)",
            (json.dumps({"command_id": command_id, "action_type": "local_floor_wakeup", "floor": "Neo"}),),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)

    def uncertain(**_kwargs):
        consumer._stop.set()
        raise ls_go_job_consumer.FloorExecutionUncertain("server outcome unknown")

    monkeypatch.setattr(consumer, "_run_floor_supervised", uncertain)
    with pytest.raises(ls_go_job_consumer.FloorExecutionUncertain):
        consumer.process_once()
    job = db.execute_query("SELECT status,result_json FROM jobs WHERE id=601")[0]
    assert job["status"] == "running" and job["result_json"] is None
    assert not ls_go_job_consumer.result_file_path(shell, command_id).exists()
    assert consumer.unresolved_running_job_ids() == [601]


def test_lost_floor_http_response_keeps_running_claim_and_stops_queue(
    tmp_path: Path, monkeypatch,
) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    command_id = "GO-TASK-LOST-FLOOR-HTTP"
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'queued','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)",
            (json.dumps({"command_id": command_id, "action_type": "local_floor_wakeup",
                         "floor": "Neo"}),),
        )
    floor_path = tmp_path / "floor-failed.json"

    class Child:
        returncode = 0

        def communicate(self, timeout=None):
            return (json.dumps({"status": "failed", "receipt_path": str(floor_path)}), None)

    monkeypatch.setattr(ls_go_job_consumer.subprocess, "Popen", lambda *_args, **_kw: Child())
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    original_claim = consumer._claim_job

    def claim_and_write(job_id, **kwargs):
        claimed = original_claim(job_id, **kwargs)
        if claimed:
            floor_path.write_text(json.dumps({
                "status": "failed", "floor": "Neo", "receipt_path": str(floor_path),
                "execution_claim_id": consumer._execution_claims[job_id]["claim_id"],
                "server_outcome_uncertain": True,
            }), encoding="utf-8")
        return claimed

    monkeypatch.setattr(consumer, "_claim_job", claim_and_write)
    with pytest.raises(ls_go_job_consumer.FloorExecutionUncertain):
        consumer.process_once()
    row = db.execute_query("SELECT status,result_json,metadata_json FROM jobs WHERE id=601")[0]
    assert row["status"] == "running" and row["result_json"] is None
    assert json.loads(row["metadata_json"])["ls_go_execution_uncertain"]["reason"] == (
        "ollama_server_outcome_unverified")
    assert consumer._stop.is_set()
    assert consumer.unresolved_running_job_ids() == [601]
    assert not ls_go_job_consumer.result_file_path(shell, command_id).exists()


@pytest.mark.parametrize(
    ("returncode", "output", "reason"),
    [(2, "floor runner failed before receipt", "floor_child_nonzero_exit"),
     (0, "not a receipt summary", "floor_receipt_unreadable")],
)
def test_floor_child_without_receipt_keeps_running_claim(
    tmp_path: Path, monkeypatch, returncode: int, output: str, reason: str,
) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    command_id = f"GO-TASK-CHILD-{returncode}"
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'queued','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)",
            (json.dumps({"command_id": command_id, "action_type": "local_floor_wakeup",
                         "floor": "Neo"}),),
        )

    class Child:
        def communicate(self, timeout=None):
            return (output, None)

    child = Child()
    child.returncode = returncode
    monkeypatch.setattr(ls_go_job_consumer.subprocess, "Popen", lambda *_args, **_kw: child)
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    with pytest.raises(ls_go_job_consumer.FloorExecutionUncertain):
        consumer.process_once()
    row = db.execute_query("SELECT status,result_json,metadata_json FROM jobs WHERE id=601")[0]
    assert row["status"] == "running" and row["result_json"] is None
    assert json.loads(row["metadata_json"])["ls_go_execution_uncertain"]["reason"] == reason
    assert consumer._stop.is_set()
    assert not ls_go_job_consumer.result_file_path(shell, command_id).exists()


def test_cancelled_floor_metadata_keeps_recovery_hold_after_status_change(tmp_path: Path) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    db = configure_db(tmp_path / "work.db")
    params_json = json.dumps({"command_id": "GO-TASK-REVOKED-FLOOR", "action_type": "local_floor_wakeup"})
    with sqlite3.connect(db.path) as conn:
        conn.execute("INSERT INTO tasks (id,status,metadata_json) VALUES (501,'queued','{}')")
        conn.execute(
            "INSERT INTO jobs (id,job_type,status,params_json,metadata_json,task_id) "
            "VALUES (601,'ls_go_command','pending',?,'{}',501)", (params_json,),
        )
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=db)
    assert consumer._claim_job(601, expected_job=consumer.pending_jobs()[0])
    db.execute_update("UPDATE jobs SET status='held' WHERE id=601")
    consumer._mark_floor_uncertain(601, "cancelled")
    metadata = json.loads(db.execute_query("SELECT metadata_json FROM jobs WHERE id=601")[0]["metadata_json"])
    assert metadata["ls_go_execution_uncertain"]["server_cancellation_verified"] is False
    assert consumer.unresolved_running_job_ids() == [601]
    assert consumer._reconcile_running_job_receipt(601) is False


def test_supervised_floor_reads_exact_child_receipt(tmp_path: Path, monkeypatch) -> None:
    shell = tmp_path / "App"
    configure_shell(shell)
    consumer = ls_go_job_consumer.LSGoJobConsumer(shell, db=object())
    consumer._execution_claims[601] = {
        "claim_id": "a" * 32, "native_budget": dict(ls_go_job_consumer.FLOOR_NATIVE_BUDGET),
    }
    monkeypatch.setattr(consumer, "_require_live_claim", lambda _job_id: None)
    receipt_path = tmp_path / "floor.json"
    receipt = {"status": "completed", "floor": "Neo", "receipt_path": str(receipt_path),
               "execution_claim_id": "a" * 32,
               "source_excerpt_char_cap": 600,
               "prompt_preflight": {
                   "utf8_bytes": 5500, "ceiling": 7000,
                   "state": "within_ceiling", "hard_token_limit": False,
               },
               "usage_accounting": {
                   "state": "MEASURED_OLLAMA_RESPONSE", "prompt_tokens": 17,
                   "completion_tokens": 5, "total_tokens": 22,
                   "ollama_generate_attempts": 1, "budget_enforced": False,
                   "tool_calls": 0,
                   "tool_call_scope": "model_function_tools_not_exposed_by_local_generate",
               },
               "total_token_postflight": {
                   "ceiling": 2048, "state": "within_ceiling", "hard_generation_limit": False,
               }}
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    commands = []

    class Child:
        returncode = 0

        def communicate(self, timeout=None):
            return (json.dumps({"status": "completed", "receipt_path": str(receipt_path)}), None)

    def start(command, **_kwargs):
        commands.append(command)
        return Child()

    monkeypatch.setattr(ls_go_job_consumer.subprocess, "Popen", start)
    result = consumer._run_floor_supervised(job_id=601, floor="Neo", allow_heavy=False, receipt_target="neo")
    assert result == receipt
    consumer._execution_claims[601]["native_budget"]["total_token_postflight_ceiling"] = 4096
    with pytest.raises(RuntimeError, match="exact durable native budget"):
        consumer._run_floor_supervised(job_id=601, floor="Neo", allow_heavy=False, receipt_target="neo")
    consumer._execution_claims[601]["native_budget"] = dict(ls_go_job_consumer.FLOOR_NATIVE_BUDGET)
    assert "--execute" in commands[0]
    assert "--num-predict" in commands[0]
    assert commands[0][commands[0].index("--max-total-tokens") + 1] == "2048"
    assert commands[0][commands[0].index("--max-source-excerpt-chars") + 1] == "600"
    assert commands[0][commands[0].index("--max-prompt-utf8-bytes") + 1] == "7000"
    assert commands[0][-2:] == ["--execution-claim-id", "a" * 32]
    assert "--allow-heavy" not in commands[0]
    receipt["prompt_preflight"]["utf8_bytes"] = 7001
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(RuntimeError, match="claimed prompt preflight proof"):
        consumer._run_floor_supervised(job_id=601, floor="Neo", allow_heavy=False, receipt_target="neo")
    receipt["prompt_preflight"]["utf8_bytes"] = 5500
    receipt["usage_accounting"]["tool_calls"] = 1
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(RuntimeError, match="consistent measured usage"):
        consumer._run_floor_supervised(job_id=601, floor="Neo", allow_heavy=False, receipt_target="neo")
    receipt["usage_accounting"]["tool_calls"] = 0
    receipt["usage_accounting"]["total_tokens"] = 21
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(RuntimeError, match="consistent measured usage"):
        consumer._run_floor_supervised(job_id=601, floor="Neo", allow_heavy=False, receipt_target="neo")
    receipt["usage_accounting"]["total_tokens"] = 22
    receipt["usage_accounting"].update(
        prompt_tokens=2048, completion_tokens=1, total_tokens=2049,
    )
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(RuntimeError, match="consistent measured usage"):
        consumer._run_floor_supervised(job_id=601, floor="Neo", allow_heavy=False, receipt_target="neo")
    receipt["usage_accounting"].update(
        prompt_tokens=17, completion_tokens=5, total_tokens=22,
    )
    receipt["total_token_postflight"]["state"] = "unmeasured"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(RuntimeError, match="measured total token ceiling proof"):
        consumer._run_floor_supervised(job_id=601, floor="Neo", allow_heavy=False, receipt_target="neo")
    receipt["total_token_postflight"]["state"] = "within_ceiling"
    receipt["execution_claim_id"] = "b" * 32
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    marks = []
    monkeypatch.setattr(consumer, "_mark_floor_uncertain", lambda _job_id, reason: marks.append(reason))
    with pytest.raises(ls_go_job_consumer.FloorExecutionUncertain, match="outcome unverified"):
        consumer._run_floor_supervised(job_id=601, floor="Neo", allow_heavy=False, receipt_target="neo")
    assert marks == ["floor_receipt_identity_mismatch"]
    assert consumer._stop.is_set()


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
