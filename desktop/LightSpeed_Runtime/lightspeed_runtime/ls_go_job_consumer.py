from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from typing import Any
from uuid import uuid4

from lightspeed_runtime.corpus_test_orchestrator import (
    CorpusTestPlanError,
    assess_frontier_unit,
)
from lightspeed_runtime.local_agent_cycle import run_cycle
from lightspeed_runtime.local_floor_runner import run_floor
from lightspeed_runtime.cognigrex_supervisor import run_supervised_workflow
from lightspeed_runtime.storage_paths import neo_actions_root
from lightspeed_runtime.source_intake_executor import execute_source_intake


CONSUMER_SCHEMA = "lightspeed-ls-go-job-consumer-v1"
RESULT_SCHEMA = "lightspeed-go-local-result-v1"
POLL_SECONDS = 1.0
JSON_REPLACE_RETRIES = 4
JSON_REPLACE_RETRY_SECONDS = 0.05
CLAIM_LEASE_SECONDS = 900
CLAIM_LEASE_SCHEMA = "LSGO-CLAIM-LEASE/0.1"
FLOOR_NATIVE_BUDGET = {
    "schema": "LSGO-FLOOR-NATIVE-BUDGET/0.1",
    "client_wall_deadline_seconds": 185,
    "ollama_timeout_seconds": 180,
    "requested_completion_token_cap": 1024,
    "total_token_postflight_ceiling": 2048,
    "source_excerpt_char_cap": 600,
    "prompt_utf8_byte_ceiling": 7000,
    "model_function_tool_calls": 0,
    "cost_usd": None,
}


class FloorExecutionUncertain(RuntimeError):
    """The client was stopped, but server completion/cancellation is unknown."""


SAFE_ACTIONS = {
    "source_preserving_intake",
    "cognigrex_workflow",
    "transport_diagnostic",
    "local_agent_cycle",
    "local_floor_wakeup",
    "rfs_emff_sweep",
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


def _claim_lease_live(claim: dict[str, Any], *, at: datetime | None = None) -> bool:
    """Treat missing, malformed, or expired new execution leases as revoked."""
    expires = claim.get("lease_expires_utc")
    started = claim.get("started_utc")
    if not isinstance(expires, str) or not isinstance(started, str):
        return False
    try:
        deadline = datetime.fromisoformat(expires)
        began = datetime.fromisoformat(started)
    except ValueError:
        return False
    instant = datetime.now(UTC) if at is None else at
    return (
        began.tzinfo is not None and deadline.tzinfo is not None and instant.tzinfo is not None
        and began <= instant < deadline
        and deadline - began <= timedelta(seconds=CLAIM_LEASE_SECONDS)
    )


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
    for attempt in range(JSON_REPLACE_RETRIES):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt + 1 >= JSON_REPLACE_RETRIES:
                raise
            time.sleep(JSON_REPLACE_RETRY_SECONDS)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def result_id_for(command_id: str) -> str:
    if command_id.startswith("GO-TASK-"):
        return "GO-RESULT-" + command_id[len("GO-TASK-") :]
    return "LSGO-RESULT-" + _safe_id(command_id)


def _legacy_result_file_path(shell_root: Path, command_id: str) -> Path:
    """Historical lossy filename; read-only compatibility for exact identity."""
    return neo_actions_root(shell_root) / "results" / f"{_safe_id(result_id_for(command_id))}.json"


def result_file_path(shell_root: Path, command_id: str) -> Path:
    """Bind the receipt filename to the *entire original* command identity.

    The readable prefix is not injective; the digest prevents distinct command
    IDs such as 'a/b' and 'a_b' from sharing the same receipt path.
    """
    identity = str(command_id)
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    label = _safe_id(result_id_for(identity))[:72]
    return neo_actions_root(shell_root) / "results" / f"{label}-{digest}.json"


def identity_hold_file_path(shell_root: Path, command_id: str, job_id: int, task_id: Any) -> Path:
    """Keep a conflicting job's hold separate from the original command receipt."""
    identity = json.dumps([command_id, job_id, task_id], ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return neo_actions_root(shell_root) / "results" / f"LSGO-IDENTITY-HOLD-{digest}.json"


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


def execute_rfs_emff_sweep(
    action_payload: dict[str, Any],
    *,
    command_id: str,
    task_id: Any,
    job_id: int,
    shell_root: Path,
    allow_heavy: bool = False,
) -> dict[str, Any]:
    """Dispatch through the executor-owned schema and existing task/job identity."""
    if allow_heavy:
        raise ValueError("rfs_emff_sweep transport does not permit heavy execution")
    module = importlib.import_module("lightspeed_runtime.rfs_emff_sweep")
    validator = getattr(module, "validate_sweep_request", None)
    executor = getattr(module, "execute_sweep", None)
    if not callable(validator) or not callable(executor):
        raise RuntimeError("RFS/EMFF sweep validator or executor is unavailable")
    normalized = validator(action_payload)
    if not isinstance(normalized, dict):
        raise RuntimeError("RFS/EMFF sweep validator returned an invalid contract")
    result = executor(
        normalized,
        task_id=task_id,
        job_id=job_id,
        shell_root=shell_root,
        allow_heavy=False,
        command_id=command_id,
    )
    if not isinstance(result, dict):
        raise RuntimeError("RFS/EMFF sweep executor returned an invalid result")
    if result.get("drive_write_executed") is True:
        raise RuntimeError("RFS/EMFF sweep executor attempted a Drive write")
    if result.get("public_publish_authorized") is True or result.get("public_publish_executed") is True:
        raise RuntimeError("RFS/EMFF sweep executor attempted public publication")
    return result


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


def host_cpu_admission(shell_root: Path | str, *,
                       observed_percent: float | None = None,
                       previous_hold: bool = False) -> dict[str, Any]:
    """Advisory aggregate CPU gate for *new jobs*, not a hard Windows CPU cap.

    Keep worker/heartbeat responsive. Windows Job Object CPU-rate limits for
    all LS children, machine thermal controls and actual 80% physical cap
    require a separate LOCAL signed witness. Synthetic injected samples are
    allowed only for unit tests; ordinary production samples use psutil.
    """
    import math

    policy = _read_json(Path(shell_root) / "config" / "host_runtime_policy.json")
    raw = policy.get("runtime_limits")
    limits = raw if isinstance(raw, dict) else {}
    ceiling = limits.get("max_total_host_cpu_percent", 80)
    resume = limits.get("cpu_dispatch_resume_percent", 70)
    interval = limits.get("cpu_sampling_interval_seconds", 0.25)
    if (type(ceiling) not in (int, float) or type(resume) not in (int, float)
            or isinstance(ceiling, bool) or isinstance(resume, bool)
            or not (0 < float(resume) < float(ceiling) <= 80)
            or type(interval) not in (int, float) or isinstance(interval, bool)
            or not (0.05 <= float(interval) <= 1.0)):
        return {
            "state": "cpu_policy_invalid", "allow_new_jobs": False,
            "aggregate_cpu_hard_cap_verified": False,
            "measured_total_cpu_percent": None,
        }
    if observed_percent is None:
        try:
            import psutil
            measured = psutil.cpu_percent(interval=float(interval))
        except (ImportError, OSError, RuntimeError, ValueError):
            measured = None
    else:
        measured = observed_percent
    if (type(measured) not in (int, float) or isinstance(measured, bool)
            or not math.isfinite(float(measured))
            or not (0 <= float(measured) <= 100)):
        return {
            "state": "cpu_monitor_unavailable", "allow_new_jobs": False,
            "aggregate_cpu_hard_cap_verified": False,
            "measured_total_cpu_percent": None,
            "max_total_host_cpu_percent": float(ceiling),
        }
    reading = float(measured)
    cpu_hold = reading >= float(ceiling) or (
        previous_hold and reading > float(resume)
    )
    return {
        "state": "paused_cpu_pressure" if cpu_hold else "ready",
        "allow_new_jobs": not cpu_hold,
        "aggregate_cpu_hard_cap_verified": False,
        "measured_total_cpu_percent": reading,
        "max_total_host_cpu_percent": float(ceiling),
        "resume_cpu_percent": float(resume),
        "mobile_device_required": False,
        "cpu_control_scope": "DISPATCH_ADMISSION_ONLY",
    }


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
        self._cpu_pressure_hold = False
        self._execution_claims: dict[int, dict[str, Any]] = {}

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

    def unresolved_running_job_ids(self) -> list[int]:
        """Detect prior in-flight work before this singleton claims new jobs.

        A prior process may have executed an action before losing its durable
        result. Such work cannot safely be replayed or assumed complete here.
        """
        if self.db is None or not callable(getattr(self.db, "execute_query", None)):
            return []
        if not {"id", "job_type", "status", "metadata_json"}.issubset(self._columns("jobs")):
            return []
        rows = self.db.execute_query(
            "SELECT id,status,metadata_json FROM jobs WHERE job_type = ? "
            "AND (status = ? OR metadata_json LIKE ?) ORDER BY id ASC LIMIT 101",
            ("ls_go_command", "running", '%ls_go_execution_uncertain%'),
        )
        return [int(row["id"]) for row in rows if row["status"] == "running"
                or bool(_json_dict(row["metadata_json"]).get("ls_go_execution_uncertain"))]

    def _reconcile_running_job_receipt(self, job_id: int) -> bool:
        """Atomically finish only a prior run with an exact durable result.

        Unknown execution remains running for the startup hold. This route
        never calls an action or creates a replacement result receipt.
        """
        connection = getattr(self.db, "get_connection", None)
        if not callable(connection):
            return False
        with connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            raw_job = conn.execute(
                "SELECT id, status, params_json, metadata_json, task_id FROM jobs "
                "WHERE id = ? AND job_type = ?", (job_id, "ls_go_command"),
            ).fetchone()
            if raw_job is None:
                return False
            job = dict(raw_job)
            if _json_dict(job["metadata_json"]).get("ls_go_execution_uncertain"):
                return False
            if job["status"] != "running" or type(job.get("task_id")) is not int:
                return False
            command_id = str(_json_dict(job.get("params_json")).get("command_id") or "").strip()
            if not command_id:
                return False
            result = self._existing_result(command_id)
            task_id = job["task_id"]
            if not (
                type(result.get("job_id")) is int and result.get("job_id") == job_id
                and type(result.get("task_id")) is int and result.get("task_id") == task_id
                and result.get("status") in {"completed", "blocked", "held"}
                and result.get("result_id") == result_id_for(command_id)
            ):
                return False
            prior_claim = _json_dict(job.get("metadata_json")).get("ls_go_execution_claim")
            if prior_claim is not None:
                receipt_claim = result.get("execution_claim")
                if (isinstance(prior_claim, dict) and prior_claim.get("purpose") == "execute"
                        and (prior_claim.get("lease_schema") == CLAIM_LEASE_SCHEMA
                             or isinstance(receipt_claim, dict)
                             and receipt_claim.get("lease_schema") == CLAIM_LEASE_SCHEMA)):
                    completed = result.get("completed_utc")
                    try:
                        completed_at = datetime.fromisoformat(completed) if isinstance(completed, str) else None
                    except ValueError:
                        completed_at = None
                    if (completed_at is None or prior_claim.get("lease_schema") != CLAIM_LEASE_SCHEMA
                            or not isinstance(receipt_claim, dict)
                            or receipt_claim.get("lease_schema") != CLAIM_LEASE_SCHEMA
                            or receipt_claim.get("started_utc") != prior_claim.get("started_utc")
                            or receipt_claim.get("lease_expires_utc") != prior_claim.get("lease_expires_utc")
                            or not _claim_lease_live(prior_claim, at=completed_at)):
                        return False
                if not (
                    isinstance(prior_claim, dict)
                    and prior_claim.get("job_id") == job_id
                    and prior_claim.get("task_id") == task_id
                    and prior_claim.get("command_id") == command_id
                    and prior_claim.get("job_params_sha256") == hashlib.sha256(
                        job["params_json"].encode("utf-8")
                    ).hexdigest()
                    and (
                        (isinstance(receipt_claim, dict)
                         and receipt_claim.get("claim_id") == prior_claim.get("claim_id"))
                        or (prior_claim.get("purpose") == "reconcile" and receipt_claim is None)
                    )
                ):
                    return False
            raw_task = conn.execute(
                "SELECT status, metadata_json FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if raw_task is None:
                return False
            task = dict(raw_task)
            final_status = str(result["status"])
            if task["status"] in {"completed", "blocked", "held"} and task["status"] != final_status:
                return False
            metadata = _json_dict(task.get("metadata_json"))
            metadata["ls_go_local_result"] = {
                "result_id": result["result_id"],
                "receipt_path": result["receipt_path"],
                "job_id": job_id,
                "status": final_status,
            }
            now = utc_now_iso()
            task_update = conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ?, metadata_json = ? "
                "WHERE id = ? AND status = ?",
                (final_status, now, json.dumps(metadata, ensure_ascii=False), task_id, task["status"]),
            )
            if task_update.rowcount != 1:
                raise RuntimeError("running result task changed during reconciliation")
            job_update = conn.execute(
                "UPDATE jobs SET status = ?, result_json = ?, error = ?, completed_at = ?, updated_at = ? "
                "WHERE id = ? AND job_type = ? AND status = ? AND params_json = ? AND task_id = ?",
                (final_status, json.dumps(result, ensure_ascii=False), result.get("error"), now, now,
                 job_id, "ls_go_command", "running", job["params_json"], task_id),
            )
            if job_update.rowcount != 1:
                raise RuntimeError("running result job changed during reconciliation")
        return True

    def _claim_job(self, job_id: int, *, expected_job: dict[str, Any],
                   purpose: str = "execute", durable_receipt: dict[str, Any] | None = None) -> bool:
        """Bind one selected DB work item to a durable, single-use claim."""
        if purpose not in {"execute", "reconcile", "hold"}:
            raise ValueError("unsupported claim purpose")
        connection = getattr(self.db, "get_connection", None)
        if not callable(connection) or not {"metadata_json", "updated_at", "task_id"}.issubset(self._columns("jobs")):
            raise RuntimeError("durable job claim requires transactional DB and identity columns")
        with connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT job_type,status,params_json,metadata_json,task_id FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
            if row is None or row["job_type"] != "ls_go_command" or row["status"] not in {
                "pending", "queued", "review",
            }:
                return False
            if (row["params_json"] != expected_job.get("params_json")
                    or row["task_id"] != expected_job.get("task_id")):
                raise RuntimeError("queued job identity changed before claim")
            metadata = _json_dict(row["metadata_json"])
            params = _json_dict(row["params_json"])
            action_payload = params.get("action_payload")
            frontier_admission = None
            top_level_frontier = "frontier_request" in params
            nested_frontier = isinstance(action_payload, dict) and "frontier_request" in action_payload
            if top_level_frontier or nested_frontier:
                try:
                    if top_level_frontier and nested_frontier:
                        raise CorpusTestPlanError("ambiguous frontier request locations")
                    request = (params["frontier_request"] if top_level_frontier
                               else action_payload["frontier_request"])
                    decision = assess_frontier_unit(request)
                    frontier_admission = {
                        "schema": decision["schema"],
                        "domain": decision["domain"],
                        "object_id": decision["object_id"],
                        "owner": decision["owner"],
                        "work_key": decision["work_key"],
                        "source_sha256": decision["source_sha256"],
                        "evidence_class": decision["evidence_class"],
                        "verdict": decision["verdict"],
                        "reason": decision["reason"],
                        "reported_usage_is_unverified": True,
                        "resource_ceiling_enforced_by_this_function": False,
                        "native_execution_authorized": False,
                    }
                except CorpusTestPlanError as exc:
                    frontier_admission = {
                        "schema": "CGX-FRONTIER-ADMISSION/0.1",
                        "work_key": None,
                        "verdict": "HOLD",
                        "reason": f"INVALID_FRONTIER_REQUEST:{exc}",
                        "native_execution_authorized": False,
                    }
            now = utc_now_iso()
            params_hash = hashlib.sha256(row["params_json"].encode("utf-8")).hexdigest()
            command_id = str(params.get("command_id") or "").strip() or None
            action_type, _action_source = resolve_action(command_id or "", params)
            frontier_budget = None
            if (frontier_admission is not None
                    and frontier_admission["verdict"] == "READY_FOR_BOUNDED_WORK"
                    and "frontier_request" in params
                    and action_type == "source_preserving_intake"
                    and isinstance(action_payload, dict)):
                request = params["frontier_request"]
                source_matches = (
                    request["operation"] == "source_preserving_intake"
                    and action_payload.get("source_sha256") == frontier_admission["source_sha256"]
                    and params.get("execution_mode") == "queue"
                    and params.get("execute") is True
                    and params.get("allow_heavy") is False
                    and expected_job.get("z_context") == "Neo"
                    and isinstance(params.get("frontier_authenticated_actor"), str)
                    and bool(params["frontier_authenticated_actor"].strip())
                )
                usage = request["usage"]
                zero_initial_usage = (all(usage[field] == 0 for field in (
                    "elapsed_s", "tokens", "tool_calls", "retries",
                )) and usage.get("cost_usd", 0) == 0)
                if source_matches and zero_initial_usage:
                    limits = request["limits"]
                    frontier_budget = {field: limits[field] for field in (
                        "max_elapsed_s", "max_tokens", "max_tool_calls", "max_retries",
                    )}
                    if "max_cost_usd" in limits:
                        frontier_budget["max_cost_usd"] = limits["max_cost_usd"]
                    frontier_admission["native_preflight_ready"] = True
                else:
                    frontier_admission["verdict"] = "HOLD"
                    frontier_admission["reason"] = "FRONTIER_INTAKE_SOURCE_OR_NATIVE_PRECONDITION_MISMATCH"
            claim = metadata.get("ls_go_execution_claim")
            if claim is not None:
                receipt_claim = (durable_receipt or {}).get("execution_claim")
                exact_prior_claim = (
                    purpose != "execute" and durable_receipt is not None
                    and isinstance(claim, dict)
                    and claim.get("job_id") == job_id
                    and claim.get("task_id") == row["task_id"]
                    and claim.get("command_id") == command_id
                    and claim.get("job_params_sha256") == params_hash
                    and (
                        (isinstance(receipt_claim, dict)
                         and receipt_claim.get("claim_id") == claim.get("claim_id"))
                        or (claim.get("purpose") == "reconcile" and receipt_claim is None)
                    )
                )
                if not exact_prior_claim:
                    raise RuntimeError("queued job retains prior execution claim; reconcile before retry")
            else:
                claim = {
                    "claim_id": uuid4().hex,
                    "lease_schema": CLAIM_LEASE_SCHEMA,
                    "purpose": purpose,
                    "job_id": job_id,
                    "task_id": row["task_id"],
                    "command_id": command_id,
                    "job_params_sha256": params_hash,
                    **({"native_budget": dict(FLOOR_NATIVE_BUDGET)}
                       if purpose == "execute" and action_type == "local_floor_wakeup"
                       and bool(params.get("execute", True)) else {}),
                    **({"frontier_admission": frontier_admission} if frontier_admission is not None else {}),
                    **({"frontier_budget": frontier_budget} if frontier_budget is not None else {}),
                    "started_utc": now,
                    "lease_expires_utc": (
                        datetime.fromisoformat(now) + timedelta(seconds=CLAIM_LEASE_SECONDS)
                    ).isoformat(timespec="seconds"),
                    "pid": os.getpid(),
                }
            metadata["ls_go_execution_claim"] = claim
            updated = conn.execute(
                "UPDATE jobs SET status = ?, metadata_json = ?, updated_at = ? "
                "WHERE id = ? AND job_type = ? AND status = ? AND params_json = ? AND task_id IS ?",
                ("running", json.dumps(metadata, ensure_ascii=False), now, job_id,
                 "ls_go_command", row["status"], row["params_json"], row["task_id"]),
            )
            if updated.rowcount != 1:
                raise RuntimeError("queued job changed during transactional claim")
        self._execution_claims[job_id] = claim
        return True

    def _finish_claimed_job(self, job_id: int, *, receipt: dict[str, Any],
                            update_task: bool = True) -> None:
        """Fence and atomically commit the exact claimed job/task result."""
        claim = self._execution_claims.get(job_id)
        if claim is None:
            raise RuntimeError("terminal result has no local execution claim")
        status = receipt.get("status")
        if status not in {"completed", "blocked", "held"}:
            raise RuntimeError("terminal result has invalid status")
        receipt_claim = receipt.get("execution_claim")
        if receipt_claim is not None:
            if not isinstance(receipt_claim, dict) or receipt_claim.get("claim_id") != claim["claim_id"]:
                raise RuntimeError("terminal receipt claim differs from active claim")
        elif claim["purpose"] == "execute":
            raise RuntimeError("executed result lacks its durable claim")
        if (type(receipt.get("job_id")) is not int or receipt["job_id"] != job_id
                or type(receipt.get("task_id")) is not type(claim["task_id"])
                or receipt.get("task_id") != claim["task_id"]
                or receipt.get("command_id") != claim["command_id"]):
            raise RuntimeError("terminal receipt differs from claimed work identity")
        with self.db.get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            raw_job = conn.execute(
                "SELECT status,params_json,metadata_json,task_id FROM jobs "
                "WHERE id = ? AND job_type = ?", (job_id, "ls_go_command"),
            ).fetchone()
            if raw_job is None or raw_job["status"] != "running":
                raise RuntimeError("claimed job no longer running; terminal write fenced")
            persisted_claim = _json_dict(raw_job["metadata_json"]).get("ls_go_execution_claim")
            if (not isinstance(persisted_claim, dict)
                    or persisted_claim.get("claim_id") != claim["claim_id"]
                    or persisted_claim.get("lease_expires_utc") != claim.get("lease_expires_utc")
                    or persisted_claim.get("native_budget") != claim.get("native_budget")
                    or persisted_claim.get("frontier_admission") != claim.get("frontier_admission")
                    or persisted_claim.get("frontier_budget") != claim.get("frontier_budget")
                    or raw_job["task_id"] != claim["task_id"]
                    or hashlib.sha256(raw_job["params_json"].encode("utf-8")).hexdigest()
                    != claim["job_params_sha256"]):
                raise RuntimeError("persisted work claim changed; terminal write fenced")
            if claim["purpose"] == "execute" and not _claim_lease_live(persisted_claim):
                raise RuntimeError("execution claim lease expired; terminal write fenced")
            task_id = claim["task_id"]
            task = None
            if update_task and task_id is not None:
                raw_task = conn.execute(
                    "SELECT status,metadata_json FROM tasks WHERE id = ?", (task_id,),
                ).fetchone()
                if raw_task is None:
                    raise RuntimeError("claimed task missing; terminal write fenced")
                task = dict(raw_task)
                if task["status"] in {"completed", "blocked", "held"} and task["status"] != status:
                    raise RuntimeError("claimed task has conflicting terminal state")
            now = utc_now_iso()
            updated = conn.execute(
                "UPDATE jobs SET status = ?, result_json = ?, error = ?, completed_at = ?, updated_at = ? "
                "WHERE id = ? AND job_type = ? AND status = ? AND params_json = ? AND task_id IS ?",
                (status, json.dumps(receipt, ensure_ascii=False), receipt.get("error"), now, now,
                 job_id, "ls_go_command", "running", raw_job["params_json"], task_id),
            )
            if updated.rowcount != 1:
                raise RuntimeError("claimed job changed during terminal commit")
            if task is not None:
                metadata = _json_dict(task.get("metadata_json"))
                metadata["ls_go_local_result"] = {
                    "result_id": receipt.get("result_id"),
                    "receipt_path": receipt.get("receipt_path"),
                    "job_id": job_id,
                    "status": status,
                }
                updated = conn.execute(
                    "UPDATE tasks SET status = ?, updated_at = ?, metadata_json = ? "
                    "WHERE id = ? AND status = ?",
                    (status, now, json.dumps(metadata, ensure_ascii=False), task_id, task["status"]),
                )
                if updated.rowcount != 1:
                    raise RuntimeError("claimed task changed during terminal commit")

    def _persist_result(self, receipt: dict[str, Any]) -> dict[str, Any]:
        command_id = str(receipt.get("command_id") or f"MISSING-JOB-{receipt.get('job_id') or 'UNKNOWN'}")
        path = result_file_path(self.shell_root, command_id)
        receipt["receipt_path"] = str(path)
        _write_json(path, receipt)
        _append_jsonl(result_queue_path(self.shell_root), receipt)
        return receipt

    def _existing_result(self, command_id: str) -> dict[str, Any]:
        for path in (
            result_file_path(self.shell_root, command_id),
            _legacy_result_file_path(self.shell_root, command_id),
        ):
            payload = _read_json(path)
            if payload and payload.get("command_id") == command_id:
                # The durable file actually read is the result source; an
                # embedded path must not redirect recovery evidence elsewhere.
                payload["receipt_path"] = str(path)
                return payload
        return {}

    def _identity_hold(self, command_id: str, job_id: int, task_id: Any,
                       existing: dict[str, Any], job: dict[str, Any]) -> dict[str, Any] | None:
        path = identity_hold_file_path(self.shell_root, command_id, job_id, task_id)
        receipt = _read_json(path)
        if path.exists() and (
            not receipt
            or receipt.get("command_id") != command_id
            or type(receipt.get("job_id")) is not type(job_id)
            or receipt.get("job_id") != job_id
            or type(receipt.get("task_id")) is not type(task_id)
            or receipt.get("task_id") != task_id
            or receipt.get("status") != "held"
        ):
            raise ValueError("existing identity-hold receipt failed exact readback")
        if not self._claim_job(job_id, expected_job=job, purpose="hold",
                               durable_receipt=receipt or None):
            return None
        if not receipt:
            receipt = {
                "schema_version": RESULT_SCHEMA,
                "result_id": f"LSGO-IDENTITY-HOLD-{job_id}",
                "created_utc": utc_now_iso(),
                "command_id": command_id,
                "job_id": job_id,
                "task_id": task_id,
                "execution_claim": self._execution_claims[job_id],
                "status": "held",
                "error": "command receipt does not match exact job/task identity or terminal status",
                "conflicting_receipt_path": existing.get("receipt_path"),
                "conflicting_job_id": existing.get("job_id"),
                "conflicting_task_id": existing.get("task_id"),
                "drive_write_executed": False,
                "public_publish_authorized": False,
                "receipt_path": str(path),
            }
            _write_json(path, receipt)
            _append_jsonl(result_queue_path(self.shell_root), receipt)
        # A duplicate job may point at the original task. Do not regress it.
        self._finish_claimed_job(job_id, receipt=receipt,
                                 update_task=task_id != existing.get("task_id"))
        return receipt

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

    def _require_live_claim(self, job_id: int) -> None:
        """Stop cooperative native work when its exact DB lease is revoked."""
        if self._stop.is_set():
            raise RuntimeError("source intake cancelled by consumer shutdown")
        claim = self._execution_claims[job_id]
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT status,params_json,metadata_json,task_id FROM jobs "
                "WHERE id = ? AND job_type = ?", (job_id, "ls_go_command"),
            ).fetchone()
        if (row is None or row["status"] != "running"
                or row["task_id"] != claim["task_id"]
                or hashlib.sha256(row["params_json"].encode("utf-8")).hexdigest()
                != claim["job_params_sha256"]
                or _json_dict(row["metadata_json"]).get("ls_go_execution_claim", {}).get("claim_id")
                != claim["claim_id"]
                or _json_dict(row["metadata_json"]).get("ls_go_execution_claim", {}).get("lease_expires_utc")
                != claim.get("lease_expires_utc")
                or _json_dict(row["metadata_json"]).get("ls_go_execution_claim", {}).get("native_budget")
                != claim.get("native_budget")
                or _json_dict(row["metadata_json"]).get("ls_go_execution_claim", {}).get("frontier_admission")
                != claim.get("frontier_admission")
                or _json_dict(row["metadata_json"]).get("ls_go_execution_claim", {}).get("frontier_budget")
                != claim.get("frontier_budget")):
            raise RuntimeError("source intake execution claim was revoked or changed")
        if not _claim_lease_live(_json_dict(row["metadata_json"]).get("ls_go_execution_claim", {})):
            raise RuntimeError("source intake execution claim lease expired")

    def _mark_floor_uncertain(self, job_id: int, reason: str) -> None:
        """Retain a DB recovery hold even if an external cancel changed status."""
        claim = self._execution_claims[job_id]
        with self.db.get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT metadata_json FROM jobs WHERE id = ? AND job_type = ?",
                (job_id, "ls_go_command"),
            ).fetchone()
            metadata = _json_dict(row["metadata_json"]) if row is not None else {}
            persisted = metadata.get("ls_go_execution_claim")
            if not isinstance(persisted, dict) or persisted.get("claim_id") != claim["claim_id"]:
                raise RuntimeError("cannot durably mark uncertain floor: claim identity changed")
            metadata["ls_go_execution_uncertain"] = {
                "claim_id": claim["claim_id"], "observed_utc": utc_now_iso(),
                "reason": reason, "server_cancellation_verified": False,
            }
            conn.execute(
                "UPDATE jobs SET metadata_json = ?, updated_at = ? WHERE id = ?",
                (json.dumps(metadata, ensure_ascii=False), utc_now_iso(), job_id),
            )

    def _hold_floor_uncertain(self, job_id: int, reason: str) -> None:
        """Fence further queue work after a child may have reached Ollama."""
        self._stop.set()
        try:
            self._mark_floor_uncertain(job_id, reason)
        except Exception as exc:
            raise FloorExecutionUncertain(
                "floor outcome unverified and recovery marker could not be persisted"
            ) from exc
        raise FloorExecutionUncertain(
            "floor outcome unverified; retain running claim until independent reconciliation"
        )

    def _run_floor_supervised(self, *, job_id: int, floor: str,
                              allow_heavy: bool, receipt_target: str) -> dict[str, Any]:
        """Bound one existing floor runner call; stop this worker on uncertain cancellation."""
        if receipt_target not in {"neo", "floor"}:
            raise ValueError("unsupported floor receipt target")
        self._require_live_claim(job_id)
        claim = self._execution_claims[job_id]
        claim_id = claim["claim_id"]
        budget = claim.get("native_budget")
        if budget != FLOOR_NATIVE_BUDGET:
            raise RuntimeError("floor execution requires exact durable native budget")
        command = [
            sys.executable, "-m", "lightspeed_runtime.local_floor_runner",
            "--floor", floor, "--execute", "--receipt-target", receipt_target,
            "--timeout-seconds", str(budget["ollama_timeout_seconds"]),
            "--num-predict", str(budget["requested_completion_token_cap"]),
            "--max-total-tokens", str(budget["total_token_postflight_ceiling"]),
            "--max-source-excerpt-chars", str(budget["source_excerpt_char_cap"]),
            "--max-prompt-utf8-bytes", str(budget["prompt_utf8_byte_ceiling"]),
            "--execution-claim-id", claim_id,
        ]
        if allow_heavy:
            command.append("--allow-heavy")
        child = subprocess.Popen(
            command, cwd=Path(__file__).resolve().parents[1],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        deadline = time.monotonic() + budget["client_wall_deadline_seconds"]
        while True:
            try:
                if self._stop.is_set():
                    raise RuntimeError("floor cancelled by consumer shutdown")
                self._require_live_claim(job_id)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("floor exceeded claimed supervised deadline")
                output, _ = child.communicate(timeout=min(0.25, remaining))
                break
            except subprocess.TimeoutExpired:
                continue
            except Exception as exc:
                # The Ollama server may still be finishing a disconnected request.
                # Do not start another queue item or replay this claim on restart.
                self._stop.set()
                try:
                    child.terminate()
                    try:
                        child.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.communicate(timeout=5)
                except Exception:
                    pass
                try:
                    self._mark_floor_uncertain(job_id, type(exc).__name__)
                except Exception as mark_exc:
                    raise FloorExecutionUncertain(
                        "floor client stopped, but uncertain recovery marker could not be persisted"
                    ) from mark_exc
                raise FloorExecutionUncertain(
                    "floor client stopped; Ollama server outcome unverified; retain running claim for recovery"
                ) from exc
        if child.returncode != 0:
            self._hold_floor_uncertain(job_id, "floor_child_nonzero_exit")
        try:
            summary = json.loads(output)
            path = Path(summary["receipt_path"])
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except (KeyError, OSError, ValueError, TypeError):
            self._hold_floor_uncertain(job_id, "floor_receipt_unreadable")
        if (not isinstance(summary, dict) or not isinstance(receipt, dict)
                or not path.is_absolute() or receipt.get("receipt_path") != str(path)
                or str(receipt.get("floor") or "").casefold() != floor.casefold()
                or receipt.get("execution_claim_id") != claim_id
                or receipt.get("status") != summary.get("status")):
            self._hold_floor_uncertain(job_id, "floor_receipt_identity_mismatch")
        if (receipt.get("server_outcome_uncertain") is True
                or (receipt.get("status") == "failed"
                    and receipt.get("server_outcome_uncertain") is not False)):
            self._hold_floor_uncertain(job_id, "ollama_server_outcome_unverified")
        if receipt.get("status") == "completed":
            prompt_preflight = receipt.get("prompt_preflight")
            if (not isinstance(prompt_preflight, dict)
                    or type(prompt_preflight.get("utf8_bytes")) is not int
                    or not 0 < prompt_preflight["utf8_bytes"] <= budget["prompt_utf8_byte_ceiling"]
                    or prompt_preflight.get("ceiling") != budget["prompt_utf8_byte_ceiling"]
                    or prompt_preflight.get("state") != "within_ceiling"
                    or prompt_preflight.get("hard_token_limit") is not False
                    or receipt.get("source_excerpt_char_cap") != budget["source_excerpt_char_cap"]):
                raise RuntimeError("floor runner receipt lacks claimed prompt preflight proof")
            usage = receipt.get("usage_accounting")
            if not isinstance(usage, dict):
                raise RuntimeError("floor runner receipt lacks measured token counters")
            prompt = usage.get("prompt_tokens")
            completion = usage.get("completion_tokens")
            total = usage.get("total_tokens")
            if (usage.get("state") != "MEASURED_OLLAMA_RESPONSE"
                    or type(prompt) is not int or prompt < 0
                    or type(completion) is not int or completion < 0
                    or type(total) is not int or total != prompt + completion
                    or total > budget["total_token_postflight_ceiling"]
                    or usage.get("ollama_generate_attempts") != 1
                    or type(usage.get("tool_calls")) is not int
                    or usage["tool_calls"] != budget["model_function_tool_calls"]
                    or usage.get("tool_call_scope")
                    != "model_function_tools_not_exposed_by_local_generate"):
                raise RuntimeError("floor runner receipt lacks consistent measured usage or no-tools proof")
            if receipt.get("total_token_postflight") != {
                "ceiling": budget["total_token_postflight_ceiling"],
                "state": "within_ceiling", "hard_generation_limit": False,
            }:
                raise RuntimeError("floor runner receipt lacks measured total token ceiling proof")
        return receipt

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
        if action_type == "source_preserving_intake":
            if (str(job.get("z_context") or "") != "Neo" or params.get("execution_mode") != "queue"
                    or params.get("execute") is not True or params.get("allow_heavy") is not False):
                return {"status": "blocked", "action_type": action_type,
                        "error": "intake requires Neo, explicit queue execution and allow_heavy=false"}
            home = _read_json(Path(__file__).resolve().parents[1] / "config" / "agent_home.json")
            configured = (home.get("environment") or {}).get("assimilation_source_root")
            intake = execute_source_intake(params.get("action_payload"), command_id=command_id,
                                          shell_root=self.shell_root,
                                          allowed_roots=[Path(configured)] if configured else [],
                                          check_active=lambda: self._require_live_claim(job["id"]),
                                          frontier_budget=self._execution_claims[job["id"]].get("frontier_budget"))
            return {"status": intake["status"], "action_type": action_type, "intake": intake,
                    "summary": "Exact source snapshot and derived extraction persisted for review.",
                    "next_action": "Review source ownership, extraction coverage and domain mapping before semantic ingestion."}
        if action_type == "rfs_emff_sweep":
            if str(job.get("z_context") or "") != "TheConstruct":
                return {
                    "status": "blocked",
                    "action_type": action_type,
                    "error": "typed rfs_emff_sweep must target TheConstruct",
                    "next_action": "Submit a new validated v2 command targeting TheConstruct; do not rewrite this identity.",
                }
            if params.get("execution_mode") != "queue" or params.get("execute") is not True:
                return {
                    "status": "blocked",
                    "action_type": action_type,
                    "error": "typed rfs_emff_sweep requires queue execution mode",
                    "next_action": "Submit a new validated queued command; do not infer execution authority.",
                }
            if params.get("allow_heavy") is not False:
                return {
                    "status": "blocked",
                    "action_type": action_type,
                    "error": "typed rfs_emff_sweep requires allow_heavy=false",
                    "next_action": "Use the bounded local sweep contract; any heavy run requires a separate manual gate.",
                }
            action_payload = params.get("action_payload")
            if not isinstance(action_payload, dict):
                return {
                    "status": "blocked",
                    "action_type": action_type,
                    "error": "typed rfs_emff_sweep requires a validated action_payload",
                    "next_action": "Submit a new command identity with an executor-validated sweep request.",
                }
            sweep = execute_rfs_emff_sweep(
                action_payload,
                command_id=command_id,
                task_id=job.get("task_id"),
                job_id=int(job.get("id") or 0),
                shell_root=self.shell_root,
                allow_heavy=False,
            )
            successful = str(sweep.get("status") or "").casefold() in {"complete", "completed"}
            return {
                "status": "completed" if successful else "blocked",
                "action_type": action_type,
                "summary": "Bounded local RFS/EMFF parameter sweep returned through TheConstruct.",
                "sweep": sweep,
                "next_action": (
                    "Review the local artifacts and evidence classes before any canonical or Drive promotion."
                    if successful
                    else "Resolve the executor validation or runtime gap against this same task/job identity."
                ),
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
            if bool(params.get("execute", True)):
                floor_receipt = self._run_floor_supervised(
                    job_id=job["id"], floor=floor,
                    allow_heavy=bool(params.get("allow_heavy", False)),
                    receipt_target=str(params.get("receipt_target") or "neo"),
                )
            else:
                floor_receipt = run_floor(
                    floor=floor, dry_run=True,
                    allow_heavy=bool(params.get("allow_heavy", False)),
                    receipt_target=str(params.get("receipt_target") or "neo"),
                )
            return {
                "status": "completed" if floor_receipt.get("status") == "completed" else "blocked",
                "action_type": action_type,
                "summary": f"Bounded local floor wake-up returned for {floor}.",
                "floor_receipt": floor_receipt,
                "floor_supervision": {
                    "client_wall_deadline_seconds": (
                        self._execution_claims[job["id"]]["native_budget"]["client_wall_deadline_seconds"]
                        if bool(params.get("execute", True)) else None),
                    "requested_completion_token_cap": (
                        self._execution_claims[job["id"]]["native_budget"]["requested_completion_token_cap"]
                        if bool(params.get("execute", True)) else None),
                    "total_token_postflight_ceiling": (
                        self._execution_claims[job["id"]]["native_budget"]["total_token_postflight_ceiling"]
                        if bool(params.get("execute", True)) else None),
                    "source_excerpt_char_cap": (
                        self._execution_claims[job["id"]]["native_budget"]["source_excerpt_char_cap"]
                        if bool(params.get("execute", True)) else None),
                    "prompt_utf8_byte_ceiling": (
                        self._execution_claims[job["id"]]["native_budget"]["prompt_utf8_byte_ceiling"]
                        if bool(params.get("execute", True)) else None),
                    "server_cancellation_verified": False,
                },
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
            if self._claim_job(job_id, expected_job=job, purpose="hold"):
                receipt = self._persist_result(
                    {
                        "schema_version": RESULT_SCHEMA,
                        "result_id": f"LSGO-RESULT-JOB-{job_id}",
                        "created_utc": utc_now_iso(),
                        "job_id": job_id,
                        "task_id": job.get("task_id"),
                        "command_id": None,
                        "execution_claim": self._execution_claims[job_id],
                        "status": "held",
                        "error": "ls_go_command job has no command_id",
                        "public_publish_authorized": False,
                        "drive_write_executed": False,
                    }
                )
                self._finish_claimed_job(job_id, receipt=receipt)
                return receipt
            return None

        existing = self._existing_result(command_id)
        if existing:
            # Crash-safe reconciliation: if a receipt was durably written before
            # the DB status update, reconcile only the *same* claimed work item.
            task_id = job.get("task_id")
            exact_identity = (
                task_id is not None
                and type(existing.get("job_id")) is type(job_id)
                and existing.get("job_id") == job_id
                and type(existing.get("task_id")) is type(task_id)
                and existing.get("task_id") == task_id
                and existing.get("status") in {"completed", "blocked", "held"}
            )
            if not exact_identity:
                return self._identity_hold(command_id, job_id, task_id, existing, job)
            if not self._claim_job(job_id, expected_job=job, purpose="reconcile",
                                   durable_receipt=existing):
                return None
            self._finish_claimed_job(job_id, receipt=existing)
            return existing

        if not self._claim_job(job_id, expected_job=job):
            return None

        envelope, envelope_count = find_command_envelope(self.shell_root, command_id)
        action_type, action_source = resolve_action(command_id, params)
        started = utc_now_iso()
        action_started_ns = time.monotonic_ns()
        frontier_admission = self._execution_claims[job_id].get("frontier_admission")
        if frontier_admission is not None:
            action_result = {
                "status": "held",
                "action_type": action_type,
                "frontier_admission": frontier_admission,
                "error": "frontier work requires installed native budget and cancellation enforcement",
                "summary": "Source-addressed frontier decision is bound to this job claim; no action was run.",
                "next_action": "Review the exact claim and enable native limits through the existing owner gate before a new accepted work identity.",
            }
        elif action_type is None:
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
            except FloorExecutionUncertain:
                # No terminal receipt: restart must hold the unresolved running claim.
                raise
            except Exception as exc:
                action_result = {
                    "status": "blocked",
                    "action_type": action_type,
                    "error": f"{type(exc).__name__}: {exc}",
                    "summary": "Typed local action raised a bounded execution error.",
                    "next_action": "Repair the typed action/runtime prerequisite; do not substitute a new command identity unless required by the contract.",
                }

        action_elapsed_ns = time.monotonic_ns() - action_started_ns
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
            "action_wall_elapsed_ms": action_elapsed_ns // 1_000_000,
            "action_wall_clock_source": "time.monotonic_ns; excludes durable receipt persistence",
            "action_wall_clock_budget_enforced": False,
            "shell_root": str(self.shell_root),
            "queue_identity_count": envelope_count,
            "proof_required": bool((envelope or {}).get("proof_required", True)),
            "public_safe": bool((envelope or {}).get("public_safe", True)),
            "drive_write_executed": False,
            "public_publish_authorized": False,
            **action_result,
            "execution_claim": self._execution_claims[job_id],
        }
        receipt = self._persist_result(receipt)
        self._finish_claimed_job(job_id, receipt=receipt)
        return receipt

    def process_once(self, limit: int = 8) -> dict[str, Any]:
        jobs = self.pending_jobs(limit=limit)
        results: list[dict[str, Any]] = []
        for job in jobs:
            if self._stop.is_set():
                break
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
            unresolved = self.unresolved_running_job_ids()
            if unresolved:
                if len(unresolved) <= 100:
                    unresolved = [
                        job_id for job_id in unresolved
                        if not self._reconcile_running_job_receipt(job_id)
                    ]
            if unresolved:
                _write_json(status_receipt_path(self.shell_root), {
                    "schema_version": CONSUMER_SCHEMA,
                    "checked_utc": utc_now_iso(),
                    "state": "recovery_hold_unresolved_running",
                    "shell_root": str(self.shell_root),
                    "unresolved_job_ids_sample": unresolved[:100],
                    "unresolved_job_ids_truncated": len(unresolved) > 100,
                    "pending_jobs_untouched": True,
                    "results_written": 0,
                    "public_publish_authorized": False,
                    "next_action": "Reconcile each job against its exact durable receipt before restarting; never replay unknown work.",
                })
                self._stop.set()
                return
            while not self._stop.is_set():
                state = "polling"
                try:
                    cpu_gate = host_cpu_admission(
                        self.shell_root,
                        previous_hold=self._cpu_pressure_hold,
                    )
                    if cpu_gate["allow_new_jobs"]:
                        self._cpu_pressure_hold = False
                        summary = self.process_once()
                        state = str(summary.get("state") or "ready")
                    else:
                        self._cpu_pressure_hold = True
                        state = str(cpu_gate["state"])
                        _write_json(status_receipt_path(self.shell_root), {
                            "schema_version": CONSUMER_SCHEMA,
                            "checked_utc": utc_now_iso(),
                            "state": state,
                            "shell_root": str(self.shell_root),
                            "cpu_gate": cpu_gate,
                            "pending_jobs_untouched": True,
                            "results_written": 0,
                            "public_publish_authorized": False,
                        })
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
                try:
                    self._heartbeat(state)
                except Exception as exc:
                    failure_state = f"fatal_heartbeat_error:{type(exc).__name__}"
                    try:
                        _write_json(
                            status_receipt_path(self.shell_root),
                            {
                                "schema_version": CONSUMER_SCHEMA,
                                "checked_utc": utc_now_iso(),
                                "state": failure_state,
                                "error": str(exc),
                                "shell_root": str(self.shell_root),
                                "public_publish_authorized": False,
                            },
                        )
                    except Exception:
                        pass
                    self._stop.set()
                    break
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
