from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import threading
import time
from typing import Any

from lightspeed_runtime.local_agent_cycle import run_cycle
from lightspeed_runtime.local_floor_runner import run_floor
from lightspeed_runtime.cognigrex_supervisor import run_supervised_workflow
from lightspeed_runtime.storage_paths import neo_actions_root


CONSUMER_SCHEMA = "lightspeed-ls-go-job-consumer-v1"
RESULT_SCHEMA = "lightspeed-go-local-result-v1"
POLL_SECONDS = 1.0
SAFE_ACTIONS = {
    "cognigrex_workflow",
    "transport_diagnostic",
    "local_agent_cycle",
    "local_floor_wakeup",
    "review_only",
}
COMPATIBILITY_ACTIONS = {
    # GO-TASK-0016 predates typed local actions. Its canonical instruction is
    # explicitly bounded to a no-op/diagnostic transport proof, so it may be
    # mapped once without making arbitrary free-form instructions executable.
    "GO-TASK-0016": "transport_diagnostic",
}


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _safe_id(value: Any) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "unknown")).strip("_")
    return text or "unknown"


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _pid_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def result_id_for(command_id: str) -> str:
    if command_id.startswith("GO-TASK-"):
        return "GO-RESULT-" + command_id[len("GO-TASK-") :]
    return "LSGO-RESULT-" + _safe_id(command_id)


def result_file_path(shell_root: Path, command_id: str) -> Path:
    return neo_actions_root(shell_root) / "results" / f"{_safe_id(result_id_for(command_id))}.json"


def result_queue_path(shell_root: Path) -> Path:
    return neo_actions_root(shell_root) / "ls_go_result_queue.jsonl"


def runtime_exports_root(shell_root: Path) -> Path:
    return (
        shell_root
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "runtime_exports"
    )


def heartbeat_path(shell_root: Path) -> Path:
    return runtime_exports_root(shell_root) / "ls_go_job_consumer.lock.json"


def status_receipt_path(shell_root: Path) -> Path:
    return runtime_exports_root(shell_root) / "ls_go_job_consumer_receipt.json"


def _queue_path(shell_root: Path) -> Path:
    return neo_actions_root(shell_root) / "ls_go_command_queue.jsonl"


def find_command_envelope(shell_root: Path, command_id: str) -> tuple[dict[str, Any] | None, int]:
    path = _queue_path(shell_root)
    if not path.is_file():
        return None, 0
    found: dict[str, Any] | None = None
    count = 0
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None, 0
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("command_id") == command_id:
            count += 1
            if found is None:
                found = row
    return found, count


def merovingian_heartbeat(shell_root: Path, *, max_age_seconds: float = 180.0) -> dict[str, Any]:
    path = runtime_exports_root(shell_root) / "merovingian_supervisor.lock.json"
    payload = _read_json(path)
    raw = payload.get("heartbeat_utc")
    if not raw:
        return {"ok": False, "path": str(path), "reason": "heartbeat_missing"}
    try:
        stamp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=UTC)
        age = max(0.0, (datetime.now(UTC) - stamp.astimezone(UTC)).total_seconds())
    except (TypeError, ValueError):
        return {"ok": False, "path": str(path), "reason": "heartbeat_invalid"}
    pid = None
    try:
        pid = int(payload.get("pid"))
    except (TypeError, ValueError):
        pid = None
    process_alive = _pid_alive(pid)
    return {
        "ok": age <= max_age_seconds and process_alive,
        "path": str(path),
        "pid": pid,
        "process_alive": process_alive,
        "heartbeat_utc": stamp.astimezone(UTC).isoformat(timespec="seconds"),
        "age_seconds": round(age, 3),
        "max_age_seconds": max_age_seconds,
    }


def resolve_action(command_id: str, params: dict[str, Any]) -> tuple[str | None, str]:
    compatibility = COMPATIBILITY_ACTIONS.get(command_id)
    if compatibility:
        return compatibility, "compatibility_contract"
    action = str(params.get("action_type") or "").strip()
    if action in SAFE_ACTIONS:
        return action, "typed_action"
    return None, "untyped_command_held"


def _try_get_db(shell_root: Path):
    merovingian_root = shell_root / "Z Axis" / "Z-4_Merovingian"
    import sys

    if str(merovingian_root) not in sys.path:
        sys.path.insert(0, str(merovingian_root))
    try:
        from core.services import initialize_services  # type: ignore

        return (initialize_services() or {}).get("database")
    except Exception:
        return None


class LSGoJobConsumer:
    """Smith-owned durable consumer for DB-backed LS GO jobs.

    The bridge persists jobs in SQLite so commands survive process restarts.
    Smith's historical generic executor uses an in-memory heap, which cannot
    consume those persisted rows. This consumer closes that persistence gap
    without executing free-form instruction text.
    """

    def __init__(self, shell_root: Path | str, *, db: Any | None = None) -> None:
        # Keep the canonical D:\LightSpeed operator namespace in durable
        # receipts instead of resolving the App junction to its C: backing.
        self.shell_root = Path(shell_root).absolute()
        self.db = db if db is not None else _try_get_db(self.shell_root)
        self._stop = threading.Event()
        self._job_columns_cache: set[str] | None = None
        self._task_columns_cache: set[str] | None = None

    def _columns(self, table: str) -> set[str]:
        cache_name = "_job_columns_cache" if table == "jobs" else "_task_columns_cache"
        cached = getattr(self, cache_name)
        if cached is not None:
            return cached
        if self.db is None:
            return set()
        rows = self.db.execute_query(f"PRAGMA table_info({table})")
        cols = {
            str(row.get("name"))
            for row in rows
            if isinstance(row, dict) and row.get("name")
        }
        setattr(self, cache_name, cols)
        return cols

    def pending_jobs(self, limit: int = 8) -> list[dict[str, Any]]:
        if self.db is None:
            return []
        cols = self._columns("jobs")
        required = {"id", "job_type", "status", "params_json"}
        if not required.issubset(cols):
            return []
        wanted = [
            name
            for name in (
                "id",
                "job_type",
                "status",
                "params_json",
                "metadata_json",
                "task_id",
                "project_id",
                "tool_key",
                "z_context",
                "run_dir",
                "created_at",
                "updated_at",
            )
            if name in cols
        ]
        query = (
            f"SELECT {', '.join(wanted)} FROM jobs "
            "WHERE job_type = ? AND status IN ('pending','queued','review') "
            "ORDER BY id ASC LIMIT ?"
        )
        return self.db.execute_query(query, ("ls_go_command", max(1, min(int(limit), 100))))

    def _claim_job(self, job_id: int) -> bool:
        cols = self._columns("jobs")
        now = utc_now_iso()
        if "updated_at" in cols:
            count = self.db.execute_update(
                "UPDATE jobs SET status = ?, updated_at = ? "
                "WHERE id = ? AND status IN ('pending','queued','review')",
                ("running", now, job_id),
            )
        else:
            count = self.db.execute_update(
                "UPDATE jobs SET status = ? WHERE id = ? AND status IN ('pending','queued','review')",
                ("running", job_id),
            )
        return int(count or 0) == 1

    def _update_job(self, job_id: int, *, status: str, result: dict[str, Any]) -> None:
        cols = self._columns("jobs")
        assignments: list[str] = []
        values: list[Any] = []
        for column, value in (
            ("status", status),
            ("result_json", json.dumps(result, ensure_ascii=False)),
            ("error", result.get("error")),
            ("completed_at", utc_now_iso() if status in {"completed", "blocked", "held"} else None),
            ("updated_at", utc_now_iso()),
        ):
            if column in cols and (value is not None or column == "error"):
                assignments.append(f"{column} = ?")
                values.append(value)
        if not assignments:
            return
        values.append(job_id)
        self.db.execute_update(
            f"UPDATE jobs SET {', '.join(assignments)} WHERE id = ?",
            tuple(values),
        )

    def _update_task(self, task_id: Any, *, status: str, receipt: dict[str, Any]) -> None:
        if self.db is None or not task_id:
            return
        cols = self._columns("tasks")
        assignments: list[str] = []
        values: list[Any] = []
        if "status" in cols:
            assignments.append("status = ?")
            values.append(status)
        if "updated_at" in cols:
            assignments.append("updated_at = ?")
            values.append(utc_now_iso())
        if "metadata_json" in cols:
            rows = self.db.execute_query("SELECT metadata_json FROM tasks WHERE id = ?", (int(task_id),))
            metadata = _json_dict(rows[0].get("metadata_json") if rows else None)
            metadata["ls_go_local_result"] = {
                "result_id": receipt.get("result_id"),
                "receipt_path": receipt.get("receipt_path"),
                "job_id": receipt.get("job_id"),
                "status": receipt.get("status"),
            }
            assignments.append("metadata_json = ?")
            values.append(json.dumps(metadata, ensure_ascii=False))
        if assignments:
            values.append(int(task_id))
            self.db.execute_update(
                f"UPDATE tasks SET {', '.join(assignments)} WHERE id = ?",
                tuple(values),
            )

    def _persist_result(self, receipt: dict[str, Any]) -> dict[str, Any]:
        command_id = str(receipt.get("command_id") or "unknown")
        path = result_file_path(self.shell_root, command_id)
        receipt["receipt_path"] = str(path)
        _write_json(path, receipt)
        _append_jsonl(result_queue_path(self.shell_root), receipt)
        return receipt

    def _existing_result(self, command_id: str) -> dict[str, Any]:
        path = result_file_path(self.shell_root, command_id)
        payload = _read_json(path)
        if payload and payload.get("command_id") == command_id:
            payload.setdefault("receipt_path", str(path))
            return payload
        return {}

    def _transport_diagnostic(
        self,
        *,
        command_id: str,
        job: dict[str, Any],
        envelope: dict[str, Any] | None,
        envelope_count: int,
    ) -> dict[str, Any]:
        runtime_root = Path(__file__).resolve().parents[1]
        heartbeat = merovingian_heartbeat(self.shell_root)
        checks = {
            "shell_root_exists": self.shell_root.is_dir(),
            "shell_entrypoint_present": (self.shell_root / "N.py").is_file(),
            "command_queue_present": _queue_path(self.shell_root).is_file(),
            "command_identity_count": envelope_count,
            "command_identity_exactly_once": envelope_count == 1,
            "command_envelope_present": envelope is not None,
            "merovingian_heartbeat": bool(heartbeat.get("ok")),
            "local_agent_cycle_module_present": (
                runtime_root / "lightspeed_runtime" / "local_agent_cycle.py"
            ).is_file(),
            "consumer_attached_to_local_bridge_process": True,
        }
        passed = all(
            value is True
            for key, value in checks.items()
            if key != "command_identity_count"
        ) and envelope_count == 1
        return {
            "status": "completed" if passed else "blocked",
            "action_type": "transport_diagnostic",
            "checks": checks,
            "merovingian": heartbeat,
            "artifact_ref": str(_queue_path(self.shell_root)),
            "summary": (
                "Bounded local LS GO transport diagnostic completed with one command identity."
                if passed
                else "Bounded local LS GO transport diagnostic found an unresolved local bridge prerequisite."
            ),
            "next_action": (
                "Persist this real local receipt to the canonical GO/Drive Results surface and reconcile without redispatch."
                if passed
                else "Repair only the failed local prerequisite, then reconcile this same job identity without redispatch."
            ),
        }

    def _execute_action(
        self,
        *,
        action_type: str,
        params: dict[str, Any],
        command_id: str,
        job: dict[str, Any],
        envelope: dict[str, Any] | None,
        envelope_count: int,
    ) -> dict[str, Any]:
        if action_type == "transport_diagnostic":
            return self._transport_diagnostic(
                command_id=command_id,
                job=job,
                envelope=envelope,
                envelope_count=envelope_count,
            )
        if action_type == "cognigrex_workflow":
            instruction = str(params.get("instruction") or "").strip()
            if not instruction:
                return {
                    "status": "blocked",
                    "action_type": action_type,
                    "error": "typed cognigrex_workflow requires a bounded instruction",
                    "next_action": "Supply the instruction through a new v2 command identity; do not infer it from free-form metadata.",
                }
            workflow = run_supervised_workflow(
                instruction,
                task_id=str(job.get("task_id") or command_id),
                project_id=str(job.get("project_id") or "LS-GO"),
                dry_run=not bool(params.get("execute", False)),
                allow_heavy=bool(params.get("allow_heavy", False)),
                receipt_target=str(params.get("receipt_target") or "neo"),
                stop_on_failure=bool(params.get("stop_on_failure", True)),
            )
            successful = bool(workflow.get("complete_workflow")) and workflow.get("status") == "complete"
            return {
                "status": "completed" if successful else "blocked",
                "action_type": action_type,
                "summary": "Neo-supervised Cognigrex workflow returned durable per-floor and aggregate receipts.",
                "workflow": workflow,
                "next_action": "Achilles/ACR3 must review the aggregate and per-floor receipts before any canonical promotion or release.",
            }
        if action_type == "review_only":
            return {
                "status": "completed",
                "action_type": action_type,
                "summary": "Review-only local command acknowledged without source mutation.",
                "next_action": "Reconcile the review receipt through the owning gate.",
            }
        if action_type == "local_agent_cycle":
            cycle = run_cycle(
                dry_run=not bool(params.get("execute", True)),
                allow_heavy=bool(params.get("allow_heavy", False)),
                receipt_target=str(params.get("receipt_target") or "neo"),
                stop_on_failure=bool(params.get("stop_on_failure", True)),
            )
            successful = bool(cycle.get("complete_cycle")) and not (
                set((cycle.get("counts") or {}).keys()) & {"failed", "blocked"}
            )
            return {
                "status": "completed" if successful else "blocked",
                "action_type": action_type,
                "summary": "Eight-floor sequential equal-share cycle returned a durable aggregate receipt.",
                "cycle": cycle,
                "next_action": "Reconcile all eight floor receipts before accepting the cycle as operational evidence.",
            }
        if action_type == "local_floor_wakeup":
            floor = str(params.get("floor") or job.get("z_context") or "").strip()
            if not floor:
                return {
                    "status": "blocked",
                    "action_type": action_type,
                    "error": "typed local_floor_wakeup requires floor",
                    "next_action": "Supply an explicit canonical floor identity.",
                }
            floor_receipt = run_floor(
                floor=floor,
                dry_run=not bool(params.get("execute", True)),
                allow_heavy=bool(params.get("allow_heavy", False)),
                receipt_target=str(params.get("receipt_target") or "neo"),
            )
            return {
                "status": "completed" if floor_receipt.get("status") == "completed" else "blocked",
                "action_type": action_type,
                "summary": f"Bounded local floor wake-up returned for {floor}.",
                "floor_receipt": floor_receipt,
                "next_action": "Reconcile the floor receipt through Neo/Achilles before any promotion.",
            }
        return {
            "status": "held",
            "action_type": action_type,
            "error": "unsupported safe action",
            "next_action": "Use a registered typed local action; never execute free-form instruction text.",
        }

    def process_job(self, job: dict[str, Any]) -> dict[str, Any] | None:
        if self.db is None:
            return None
        job_id = int(job.get("id") or 0)
        if job_id <= 0:
            return None
        params = _json_dict(job.get("params_json"))
        command_id = str(params.get("command_id") or "").strip()
        if not command_id:
            if self._claim_job(job_id):
                receipt = self._persist_result(
                    {
                        "schema_version": RESULT_SCHEMA,
                        "result_id": f"LSGO-RESULT-JOB-{job_id}",
                        "created_utc": utc_now_iso(),
                        "job_id": job_id,
                        "task_id": job.get("task_id"),
                        "command_id": None,
                        "status": "held",
                        "error": "ls_go_command job has no command_id",
                        "public_publish_authorized": False,
                        "drive_write_executed": False,
                    }
                )
                self._update_job(job_id, status="held", result=receipt)
                self._update_task(job.get("task_id"), status="held", receipt=receipt)
                return receipt
            return None

        existing = self._existing_result(command_id)
        if existing:
            # Crash-safe reconciliation: if a receipt was durably written before
            # the DB status update, consume the receipt rather than re-executing.
            final_status = str(existing.get("status") or "held")
            self._update_job(job_id, status=final_status, result=existing)
            self._update_task(job.get("task_id"), status=final_status, receipt=existing)
            return existing

        if not self._claim_job(job_id):
            return None

        envelope, envelope_count = find_command_envelope(self.shell_root, command_id)
        action_type, action_source = resolve_action(command_id, params)
        started = utc_now_iso()
        if action_type is None:
            action_result = {
                "status": "held",
                "action_type": None,
                "summary": "Persisted LS GO job is intentionally held because it has no registered typed local action.",
                "error": "untyped free-form LS GO commands are not executable",
                "next_action": "Reissue only as a new command identity with a registered typed local action; do not replay this held identity.",
            }
        else:
            try:
                action_result = self._execute_action(
                    action_type=action_type,
                    params=params,
                    command_id=command_id,
                    job=job,
                    envelope=envelope,
                    envelope_count=envelope_count,
                )
            except Exception as exc:
                action_result = {
                    "status": "blocked",
                    "action_type": action_type,
                    "error": f"{type(exc).__name__}: {exc}",
                    "summary": "Typed local action raised a bounded execution error.",
                    "next_action": "Repair the typed action/runtime prerequisite; do not substitute a new command identity unless required by the contract.",
                }

        receipt = {
            "schema_version": RESULT_SCHEMA,
            "result_id": result_id_for(command_id),
            "created_utc": utc_now_iso(),
            "started_utc": started,
            "completed_utc": utc_now_iso(),
            "source": "LightSpeed local Smith durable consumer",
            "command_id": command_id,
            "job_id": job_id,
            "task_id": job.get("task_id"),
            "target_floor": job.get("z_context") or (envelope or {}).get("target_floor"),
            "action_source": action_source,
            "shell_root": str(self.shell_root),
            "queue_identity_count": envelope_count,
            "proof_required": bool((envelope or {}).get("proof_required", True)),
            "public_safe": bool((envelope or {}).get("public_safe", True)),
            "drive_write_executed": False,
            "public_publish_authorized": False,
            **action_result,
        }
        receipt = self._persist_result(receipt)
        final_status = str(receipt.get("status") or "held")
        self._update_job(job_id, status=final_status, result=receipt)
        self._update_task(job.get("task_id"), status=final_status, receipt=receipt)
        return receipt

    def process_once(self, limit: int = 8) -> dict[str, Any]:
        jobs = self.pending_jobs(limit=limit)
        results: list[dict[str, Any]] = []
        for job in jobs:
            receipt = self.process_job(job)
            if receipt:
                results.append(receipt)
        summary = {
            "schema_version": CONSUMER_SCHEMA,
            "checked_utc": utc_now_iso(),
            "state": "ready" if self.db is not None else "db_unavailable",
            "shell_root": str(self.shell_root),
            "pending_seen": len(jobs),
            "results_written": len(results),
            "result_ids": [item.get("result_id") for item in results],
            "free_form_execution": False,
            "safe_actions": sorted(SAFE_ACTIONS),
            "public_publish_authorized": False,
        }
        _write_json(status_receipt_path(self.shell_root), summary)
        return summary

    def _acquire_heartbeat_lock(self) -> None:
        path = heartbeat_path(self.shell_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        for _attempt in range(2):
            try:
                descriptor = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                payload = _read_json(path)
                try:
                    pid = int(payload.get("pid"))
                except (TypeError, ValueError):
                    pid = None
                if _pid_alive(pid):
                    raise RuntimeError(f"LS GO job consumer already active as PID {pid}")
                try:
                    path.unlink()
                except OSError as exc:
                    raise RuntimeError(f"stale LS GO consumer lock cannot be removed: {exc}") from exc
                continue
            payload = {
                "schema_version": CONSUMER_SCHEMA,
                "pid": os.getpid(),
                "started_utc": utc_now_iso(),
                "heartbeat_utc": utc_now_iso(),
                "state": "starting",
            }
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, indent=2, sort_keys=True)
                stream.write("\n")
            return
        raise RuntimeError("unable to acquire LS GO consumer lock")

    def _heartbeat(self, state: str) -> None:
        _write_json(
            heartbeat_path(self.shell_root),
            {
                "schema_version": CONSUMER_SCHEMA,
                "pid": os.getpid(),
                "heartbeat_utc": utc_now_iso(),
                "state": state,
                "shell_root": str(self.shell_root),
            },
        )

    def run_forever(self, *, poll_seconds: float = POLL_SECONDS) -> None:
        self._acquire_heartbeat_lock()
        try:
            while not self._stop.is_set():
                state = "polling"
                try:
                    summary = self.process_once()
                    state = str(summary.get("state") or "ready")
                except Exception as exc:
                    state = f"error:{type(exc).__name__}"
                    _write_json(
                        status_receipt_path(self.shell_root),
                        {
                            "schema_version": CONSUMER_SCHEMA,
                            "checked_utc": utc_now_iso(),
                            "state": state,
                            "error": str(exc),
                            "shell_root": str(self.shell_root),
                            "public_publish_authorized": False,
                        },
                    )
                self._heartbeat(state)
                self._stop.wait(max(0.25, float(poll_seconds)))
        finally:
            try:
                path = heartbeat_path(self.shell_root)
                payload = _read_json(path)
                if int(payload.get("pid") or 0) == os.getpid():
                    path.unlink()
            except (OSError, TypeError, ValueError):
                pass

    def stop(self) -> None:
        self._stop.set()
