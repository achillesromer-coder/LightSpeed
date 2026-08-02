from __future__ import annotations

import hmac
import hashlib
import importlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
import sys
import threading
from typing import Any, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from lightspeed_runtime.project_artifact_store import stage_project_artifacts
from lightspeed_runtime.project_pipeline import ProjectPipeline, ReviewDecisionConflict
from lightspeed_runtime.representation_edge import (
    RepresentationEdgeDisabled,
    RepresentationValidationError,
    build_store as build_representation_edge_store,
    default_review_paths as representation_review_paths,
)
from lightspeed_runtime.storage_paths import neo_actions_root

COMMAND_SCHEMA = "lightspeed-go-command-v1"
ALLOWED_FLOORS = {
    "Achilles",
    "Neo",
    "Architect",
    "TheConstruct",
    "Morpheus",
    "Oracle",
    "Smith",
    "Merovingian",
    "Trinity",
}
ALLOWED_PRIORITIES = {"critical", "high", "normal", "low"}
ALLOWED_MODES = {"review", "queue"}
DEFAULT_ALLOWED_ORIGINS = [
    "https://lightspeed-go.nathaniel-b.chatgpt.site",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:4173",
    "http://localhost:5173",
    "http://localhost:4173",
]
OWNER_CONFIRMATION_ENV = "LIGHTSPEED_OWNER_APPROVAL_TOKEN"
_COMMAND_SUBMISSION_LOCK = threading.Lock()
_TERMINAL_COMMAND_STATES = frozenset(
    {"complete", "completed", "blocked", "failed", "cancelled", "canceled"}
)
_QUEUE_TAIL_MAX_BYTES = 2 * 1024 * 1024
_QUEUE_TAIL_MAX_LINE_BYTES = 256 * 1024
_LEGACY_COMMAND_LOOKUP_LIMIT = 64
_COMMAND_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _pid_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_limited_information, False, int(pid)
        )
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _supervisor_status(shell_root: Path) -> dict[str, Any]:
    lock_path = (
        shell_root
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "runtime_exports"
        / "merovingian_supervisor.lock.json"
    )
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        heartbeat = datetime.fromisoformat(str(payload["heartbeat_utc"]).replace("Z", "+00:00"))
        if heartbeat.tzinfo is None:
            heartbeat = heartbeat.replace(tzinfo=timezone.utc)
        age_seconds = max(0.0, (datetime.now(timezone.utc) - heartbeat).total_seconds())
        interval_seconds = max(30, min(int(payload.get("interval_seconds", 60)), 3600))
        stale_after_seconds = max(90, interval_seconds * 2 + 15)
        pid = int(payload.get("pid"))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return {
            "alive": False,
            "reason": f"invalid_or_missing_supervisor_lock:{type(exc).__name__}",
            "lock_path": str(lock_path),
        }

    process_alive = _pid_alive(pid)
    heartbeat_fresh = age_seconds <= stale_after_seconds
    return {
        "alive": process_alive and heartbeat_fresh,
        "pid": pid,
        "process_alive": process_alive,
        "heartbeat_fresh": heartbeat_fresh,
        "heartbeat_utc": heartbeat.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "heartbeat_age_seconds": round(age_seconds, 3),
        "stale_after_seconds": stale_after_seconds,
        "state": payload.get("state"),
        "lock_path": str(lock_path),
        "reason": (
            "live"
            if process_alive and heartbeat_fresh
            else "process_not_running" if not process_alive else "heartbeat_stale"
        ),
    }


def _bounded(value: Any, *, maximum: int, required: bool = False) -> str:
    text = " ".join(str(value or "").split()).strip()[:maximum]
    if required and not text:
        raise HTTPException(status_code=400, detail="Required command field is missing")
    return text


def _allowed_origins() -> list[str]:
    configured = [item.strip() for item in os.environ.get("LIGHTSPEED_GO_ALLOWED_ORIGINS", "").split(",")]
    return [*DEFAULT_ALLOWED_ORIGINS, *[item for item in configured if item]]


def _verified_owner_actor(confirmation: str | None) -> str:
    expected = os.environ.get(OWNER_CONFIRMATION_ENV, "")
    if not expected:
        raise HTTPException(
            status_code=403,
            detail=f"Owner confirmation is not configured in {OWNER_CONFIRMATION_ENV}",
        )
    if not confirmation or not hmac.compare_digest(confirmation, expected):
        raise HTTPException(status_code=403, detail="Owner confirmation failed")
    return "Nathaniel"


def _try_get_services(shell_root: Path):
    merovingian_root = shell_root / "Z Axis" / "Z-4_Merovingian"
    # A temporary or recovery shell must not fall through to an unrelated
    # ambient ``core`` package on sys.path and initialize that package's floors.
    if not (merovingian_root / "core").is_dir():
        return None, None
    if str(merovingian_root) not in sys.path:
        sys.path.insert(0, str(merovingian_root))
    try:
        services_module = importlib.import_module("core.services")
        module_file = getattr(services_module, "__file__", None)
        if not module_file:
            return None, None
        module_path = Path(module_file).resolve()
        embedded_root = merovingian_root.resolve()
        if not module_path.is_relative_to(embedded_root):
            return None, None
        initialize_services = getattr(services_module, "initialize_services")

        services = initialize_services()
        return services.get("database"), services.get("storage")
    except Exception:
        return None, None


def _queue_path(root: Path) -> Path:
    path = neo_actions_root(root) / "ls_go_command_queue.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_queue(root: Path, limit: int = 30) -> list[dict[str, Any]]:
    path = _queue_path(root)
    if not path.is_file():
        return []
    bounded_limit = max(1, min(int(limit), 200))
    try:
        size = path.stat().st_size
        read_size = min(int(size), _QUEUE_TAIL_MAX_BYTES)
        with path.open("rb") as stream:
            stream.seek(max(0, int(size) - read_size))
            tail = stream.read(read_size)
    except OSError:
        return []
    if len(tail) != read_size:
        return []
    if int(size) > read_size:
        newline = tail.find(b"\n")
        tail = tail[newline + 1 :] if newline >= 0 else b""
    if tail and not tail.endswith(b"\n"):
        tail = tail[: tail.rfind(b"\n") + 1] if b"\n" in tail else b""
    rows: list[dict[str, Any]] = []
    for raw_line in reversed(tail.splitlines()):
        if not raw_line or len(raw_line) > _QUEUE_TAIL_MAX_LINE_BYTES:
            continue
        try:
            value = json.loads(raw_line.decode("utf-8", errors="strict"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            rows.append(value)
            if len(rows) >= bounded_limit:
                break
    return rows


def _append_queue(root: Path, payload: dict[str, Any]) -> str:
    path = _queue_path(root)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return str(path)


def _canonical_queue_index_gate_authorized(shell_root: Path) -> bool:
    try:
        launch_control = json.loads(
            (shell_root / "config" / "launch_control.json").read_text(encoding="utf-8")
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False
    gates = launch_control.get("manual_gates")
    return any(
        isinstance(item, dict)
        and item.get("gate_id") == "canonical_queue_indexes"
        and str(item.get("state") or "").casefold() == "operator_authorized"
        for item in (gates if isinstance(gates, list) else [])
    )


def _canonical_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _command_contract(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the immutable LS GO command content, excluding transport timestamps."""
    return {
        "schema_version": str(payload.get("schema_version") or COMMAND_SCHEMA),
        "command_id": str(payload.get("command_id") or ""),
        "source": str(payload.get("source") or "LS GO"),
        "title": str(payload.get("title") or ""),
        "instruction": str(payload.get("instruction") or ""),
        "target_floor": str(payload.get("target_floor") or ""),
        "oversight_floor": str(payload.get("oversight_floor") or ""),
        "priority": str(payload.get("priority") or "normal"),
        "execution_mode": str(payload.get("execution_mode") or "review"),
        "proof_required": payload.get("proof_required") is True,
        "public_safe": payload.get("public_safe") is True,
    }


def _command_payload_sha256(payload: dict[str, Any]) -> str:
    return _canonical_sha256(_command_contract(payload))


class CommandDatabaseUnavailable(RuntimeError):
    """Raised when canonical command state cannot be read transactionally."""


class CommandIdentitySchemaUnavailable(CommandDatabaseUnavailable):
    """Raised until the explicit canonical-DB command migration is installed."""


class CommandIdentityConflict(ValueError):
    """Raised when a command ID already identifies different immutable content."""


class CommandQueueIndexStale(RuntimeError):
    """Raised when immutable queue replacement, truncation, or corruption is detected."""


class CommandQueueIndexPreparing(RuntimeError):
    """Raised after one bounded index chunk commits but before queue EOF is indexed."""


_COMMAND_IDENTITY_COLUMNS = {
    "command_id",
    "canonical_payload_sha256",
    "queue_state",
    "queue_occurrence_count",
    "first_queue_offset",
    "last_queue_offset",
    "task_id",
    "job_id",
    "created_at",
    "updated_at",
}
_COMMAND_QUEUE_STATE_COLUMNS = {
    "queue_key",
    "queue_path",
    "device",
    "inode",
    "indexed_offset",
    "observed_size",
    "observed_mtime_ns",
    "complete",
    "updated_at",
}


class _PersistentCommandEnvelopeIndex:
    """Bounded JSONL-to-canonical-DB command identity index.

    Construction performs no queue or database I/O. Each synchronization reads
    at most ``SCAN_BYTES`` and persists only command identity/hash/offset data;
    no command payload corpus is retained in RAM or duplicated into SQLite.
    """

    QUEUE_KEY = "canonical"
    SCAN_BYTES = 1024 * 1024

    def __init__(self, db: Any, path: Path):
        self.db = db
        self.path = Path(path)

    @staticmethod
    def _file_identity(stat_result: os.stat_result) -> tuple[int, int]:
        return int(stat_result.st_dev), int(stat_result.st_ino)

    @staticmethod
    def _table_columns(cursor: Any, table: str) -> set[str]:
        cursor.execute(f"PRAGMA table_info({table})")
        return {
            str(row.get("name") if isinstance(row, dict) else row[1])
            for row in cursor.fetchall()
        }

    def _require_schema(self, cursor: Any) -> None:
        identity_columns = self._table_columns(cursor, "ls_go_command_identities")
        state_columns = self._table_columns(cursor, "ls_go_command_queue_state")
        if not _COMMAND_IDENTITY_COLUMNS.issubset(identity_columns) or not (
            _COMMAND_QUEUE_STATE_COLUMNS.issubset(state_columns)
        ):
            raise CommandIdentitySchemaUnavailable(
                "LS GO command identity schema is unavailable; run the audited "
                "ensure_ls_go_command_identity_schema migration"
            )

    def _state(self, cursor: Any) -> dict[str, Any]:
        cursor.execute(
            "SELECT * FROM ls_go_command_queue_state WHERE queue_key = ?",
            (self.QUEUE_KEY,),
        )
        return _row_mapping(cursor, cursor.fetchone())

    def _record_line(self, cursor: Any, raw_line: bytes, start: int, end: int) -> None:
        try:
            envelope = json.loads(raw_line.decode("utf-8", errors="strict"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CommandQueueIndexStale(
                f"command queue contains invalid JSON at byte {start}"
            ) from exc
        if not isinstance(envelope, dict) or not str(envelope.get("command_id") or ""):
            raise CommandQueueIndexStale(
                f"command queue contains an unidentified envelope at byte {start}"
            )
        command_id = str(envelope["command_id"])
        computed_hash = _command_payload_sha256(envelope)
        declared_hash = str(envelope.get("canonical_payload_sha256") or computed_hash)
        if declared_hash != computed_hash:
            raise CommandQueueIndexStale(
                f"command queue payload hash mismatch for {command_id!r}"
            )
        cursor.execute(
            "SELECT canonical_payload_sha256 FROM ls_go_command_identities WHERE command_id = ?",
            (command_id,),
        )
        existing = cursor.fetchone()
        if existing:
            existing_hash = str(_row_mapping(cursor, existing)["canonical_payload_sha256"])
            if existing_hash != computed_hash:
                raise CommandQueueIndexStale(
                    f"command queue contains conflicting content for {command_id!r}"
                )
            cursor.execute(
                "UPDATE ls_go_command_identities "
                "SET queue_occurrence_count = queue_occurrence_count + 1, "
                "queue_state = ?, first_queue_offset = COALESCE(first_queue_offset, ?), "
                "last_queue_offset = ?, updated_at = ? WHERE command_id = ?",
                (
                    str(envelope.get("state") or "indexed"),
                    start,
                    end,
                    utc_now_iso(),
                    command_id,
                ),
            )
            return
        cursor.execute(
            "INSERT INTO ls_go_command_identities "
            "(command_id, canonical_payload_sha256, queue_state, queue_occurrence_count, "
            "first_queue_offset, last_queue_offset, created_at, updated_at) "
            "VALUES (?, ?, ?, 1, ?, ?, ?, ?)",
            (
                command_id,
                computed_hash,
                str(envelope.get("state") or "indexed"),
                start,
                end,
                utc_now_iso(),
                utc_now_iso(),
            ),
        )

    def advance_connection(self, connection: Any) -> dict[str, Any]:
        cursor = connection.cursor()
        self._require_schema(cursor)
        state = self._state(cursor)
        queue_path = str(self.path.absolute())
        try:
            before = self.path.stat()
        except FileNotFoundError:
            if state and int(state.get("observed_size") or 0) > 0:
                raise CommandQueueIndexStale("command queue disappeared after indexing began")
            return {"complete": True, "offset": 0, "size": 0, "scanned_bytes": 0}

        identity = self._file_identity(before)
        offset = int(state.get("indexed_offset") or 0) if state else 0
        if state:
            if str(state.get("queue_path") or "") != queue_path:
                raise CommandQueueIndexStale("canonical command queue path changed")
            stored_identity = (int(state.get("device") or 0), int(state.get("inode") or 0))
            if stored_identity != identity:
                raise CommandQueueIndexStale("command queue file identity changed")
            if int(before.st_size) < offset or int(before.st_size) < int(
                state.get("observed_size") or 0
            ):
                raise CommandQueueIndexStale("command queue was truncated")
            if (
                int(before.st_size) == int(state.get("observed_size") or 0)
                and int(before.st_mtime_ns) != int(state.get("observed_mtime_ns") or 0)
            ):
                raise CommandQueueIndexStale("command queue changed without an append")

        remaining = int(before.st_size) - offset
        read_size = min(max(0, remaining), self.SCAN_BYTES)
        chunk = b""
        opened_identity = identity
        if read_size:
            with self.path.open("rb") as stream:
                opened_identity = self._file_identity(os.fstat(stream.fileno()))
                stream.seek(offset)
                chunk = stream.read(read_size)
        if opened_identity != identity or len(chunk) != read_size:
            raise CommandQueueIndexStale("command queue changed during bounded indexing")

        complete = offset + len(chunk) >= int(before.st_size)
        consumed = len(chunk)
        if chunk and not complete:
            newline = chunk.rfind(b"\n")
            if newline < 0:
                raise CommandQueueIndexStale("command queue record exceeds bounded line size")
            consumed = newline + 1
            chunk = chunk[:consumed]
        if complete and chunk and not chunk.endswith(b"\n"):
            raise CommandQueueIndexStale("command queue ends with an incomplete JSONL record")

        position = offset
        for raw_line in chunk.split(b"\n"):
            if not raw_line:
                position += 1
                continue
            end = position + len(raw_line) + 1
            self._record_line(cursor, raw_line.rstrip(b"\r"), position, end)
            position = end
        indexed_offset = offset + consumed
        after = self.path.stat()
        if self._file_identity(after) != identity or int(after.st_size) < int(before.st_size):
            raise CommandQueueIndexStale("command queue changed during bounded indexing")
        complete = indexed_offset >= int(after.st_size)
        cursor.execute(
            "INSERT INTO ls_go_command_queue_state "
            "(queue_key, queue_path, device, inode, indexed_offset, observed_size, "
            "observed_mtime_ns, complete, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(queue_key) DO UPDATE SET queue_path=excluded.queue_path, "
            "device=excluded.device, inode=excluded.inode, indexed_offset=excluded.indexed_offset, "
            "observed_size=excluded.observed_size, observed_mtime_ns=excluded.observed_mtime_ns, "
            "complete=excluded.complete, updated_at=excluded.updated_at",
            (
                self.QUEUE_KEY,
                queue_path,
                identity[0],
                identity[1],
                indexed_offset,
                int(after.st_size),
                int(after.st_mtime_ns),
                1 if complete else 0,
                utc_now_iso(),
            ),
        )
        return {
            "complete": complete,
            "offset": indexed_offset,
            "size": int(after.st_size),
            "scanned_bytes": consumed,
        }

    def synchronize(self) -> dict[str, Any]:
        if not self.db:
            raise CommandDatabaseUnavailable("canonical command database is unavailable")
        try:
            with self.db.get_connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                progress = self.advance_connection(connection)
        except (CommandDatabaseUnavailable, CommandQueueIndexStale):
            raise
        except Exception as exc:
            raise CommandDatabaseUnavailable(
                f"canonical command database read failed: {type(exc).__name__}"
            ) from exc
        if not progress["complete"]:
            raise CommandQueueIndexPreparing(
                f"bounded command identity index preparing: "
                f"{progress['offset']}/{progress['size']} bytes"
            )
        return progress


def _row_mapping(cursor: Any, row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, dict):
        return dict(row)
    try:
        return dict(row)
    except (TypeError, ValueError):
        columns = [item[0] for item in (cursor.description or [])]
        return dict(zip(columns, row))


def _validated_command_id(command_id: str) -> str:
    value = str(command_id or "")
    if not _COMMAND_ID_PATTERN.fullmatch(value):
        raise ValueError(
            "command_id must use 1-96 ASCII letters, digits, dot, underscore, colon, or hyphen"
        )
    return value


def _escaped_like_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _find_command_database_state_connection(
    connection: Any,
    command_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return exact state; SQL errors propagate and can never mean not-found."""
    command_id = _validated_command_id(command_id)
    cursor = connection.cursor()
    cursor.execute(
        "SELECT task_id, job_id FROM ls_go_command_identities WHERE command_id = ?",
        (command_id,),
    )
    identity = _row_mapping(cursor, cursor.fetchone())
    task: dict[str, Any] = {}
    if identity.get("task_id") is not None:
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (identity["task_id"],))
        task = _row_mapping(cursor, cursor.fetchone())
    else:
        escaped_command_id = _escaped_like_literal(command_id)
        cursor.execute(
            "SELECT * FROM tasks WHERE metadata_json LIKE ? ESCAPE '\\' "
            "ORDER BY id ASC LIMIT ?",
            (f'%"command_id"%{escaped_command_id}%', _LEGACY_COMMAND_LOOKUP_LIMIT),
        )
        exact: list[dict[str, Any]] = []
        for row in cursor.fetchmany(_LEGACY_COMMAND_LOOKUP_LIMIT):
            candidate = _row_mapping(cursor, row)
            try:
                metadata = json.loads(candidate.get("metadata_json") or "{}")
            except (TypeError, json.JSONDecodeError):
                continue
            if str(metadata.get("command_id") or "") == command_id:
                exact.append(candidate)
        task = next(
            (
                item
                for item in exact
                if str(item.get("status") or "").lower() in _TERMINAL_COMMAND_STATES
            ),
            exact[0] if exact else {},
        )
    if not task:
        return {}, {}

    job: dict[str, Any] = {}
    if identity.get("job_id") is not None:
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (identity["job_id"],))
        job = _row_mapping(cursor, cursor.fetchone())
    else:
        cursor.execute(
            "SELECT * FROM jobs WHERE task_id = ? AND job_type = ? "
            "ORDER BY id ASC LIMIT ?",
            (task.get("id"), "ls_go_command", _LEGACY_COMMAND_LOOKUP_LIMIT),
        )
        jobs = [
            _row_mapping(cursor, row)
            for row in cursor.fetchmany(_LEGACY_COMMAND_LOOKUP_LIMIT)
        ]
        job = next(
            (
                item
                for item in jobs
                if str(item.get("status") or "").lower() in _TERMINAL_COMMAND_STATES
            ),
            jobs[0] if jobs else {},
        )
    if job and "job_id" not in job:
        job["job_id"] = job.get("id")
    return task, job


def _find_command_database_state(
    db: Any,
    command_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not db:
        raise CommandDatabaseUnavailable("canonical command database is unavailable")
    try:
        with db.get_connection() as connection:
            return _find_command_database_state_connection(connection, command_id)
    except CommandDatabaseUnavailable:
        raise
    except Exception as exc:
        raise CommandDatabaseUnavailable(
            f"canonical command database lookup failed: {type(exc).__name__}"
        ) from exc


def _terminal_command_state(task: dict[str, Any], job: dict[str, Any]) -> str | None:
    for state in (task.get("status"), job.get("status")):
        normalized = str(state or "").lower()
        if normalized in _TERMINAL_COMMAND_STATES:
            return str(state)
    return None


def _create_command_task(
    connection: Any,
    accepted: dict[str, Any],
    artifact_ref: str,
    canonical_payload_sha256: str,
) -> int:
    metadata_json = json.dumps(
        {
            "schema_version": COMMAND_SCHEMA,
            "command_id": accepted["command_id"],
            "canonical_payload_sha256": canonical_payload_sha256,
            "source": "LS GO",
            "target_floor": accepted["target_floor"],
            "oversight_floor": "Achilles",
            "execution_mode": accepted["execution_mode"],
            "proof_required": True,
            "public_safe": True,
            "artifact_ref": artifact_ref,
        },
        ensure_ascii=False,
    )
    now = accepted["accepted_utc"]
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description, project_id, status, priority, created_at, updated_at, metadata_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            accepted["title"],
            accepted["instruction"],
            "LS-GO",
            accepted["state"],
            accepted["priority"],
            now,
            now,
            metadata_json,
        ),
    )
    return int(cursor.lastrowid)


def _create_command_job(
    connection: Any,
    accepted: dict[str, Any],
    artifact_ref: str,
    canonical_payload_sha256: str,
    task_id: int,
) -> dict[str, Any]:
    cursor = connection.cursor()
    cursor.execute("PRAGMA table_info(jobs)")
    columns = {
        str(row.get("name") if isinstance(row, dict) else row[1])
        for row in cursor.fetchall()
    }
    params_json = json.dumps(
        {
            "command_id": accepted["command_id"],
            "canonical_payload_sha256": canonical_payload_sha256,
            "instruction": accepted["instruction"],
            "execution_mode": accepted["execution_mode"],
            "oversight_floor": "Achilles",
        },
        ensure_ascii=False,
    )
    metadata_json = json.dumps(
        {
            "tags": ["ls-go", "achilles", str(accepted["target_floor"]).lower()],
            "inputs": [{"kind": "command_envelope", "path": artifact_ref}],
        },
        ensure_ascii=False,
    )
    values_by_column: dict[str, Any] = {
        "job_type": "ls_go_command",
        "params_json": params_json,
        "status": accepted["state"],
        "created_at": accepted["accepted_utc"],
        "tool_key": "ls_go_command",
        "z_context": accepted["target_floor"],
        "task_id": task_id,
        "project_id": "LS-GO",
        "metadata_json": metadata_json,
    }
    insert_columns = [name for name in values_by_column if name in columns]
    cursor.execute(
        f"INSERT INTO jobs ({', '.join(insert_columns)}) "
        f"VALUES ({', '.join(['?'] * len(insert_columns))})",
        tuple(values_by_column[name] for name in insert_columns),
    )
    job_id = int(cursor.lastrowid)
    return {
        "job_id": job_id,
        "job_type": "ls_go_command",
        "tool_key": "ls_go_command",
        "z_context": accepted["target_floor"],
        "status": accepted["state"],
    }


def _submit_command_transaction(
    db: Any,
    command_index: _PersistentCommandEnvelopeIndex,
    shell_root: Path,
    accepted: dict[str, Any],
    canonical_payload_sha256: str,
) -> dict[str, Any]:
    """Serialize identity, queue append, task, and job through one DB writer lock."""
    if not db:
        raise CommandDatabaseUnavailable("canonical command database is unavailable")
    artifact_ref = str(_queue_path(shell_root))
    try:
        with db.get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            progress = command_index.advance_connection(connection)
            if not progress["complete"]:
                return {"index_pending": progress}

            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM ls_go_command_identities WHERE command_id = ?",
                (accepted["command_id"],),
            )
            identity = _row_mapping(cursor, cursor.fetchone())
            if identity:
                if str(identity["canonical_payload_sha256"]) != canonical_payload_sha256:
                    raise CommandIdentityConflict(
                        f"command_id {accepted['command_id']!r} already identifies different content"
                    )
                task, job = _find_command_database_state_connection(
                    connection,
                    accepted["command_id"],
                )
                terminal_state = _terminal_command_state(task, job)
                repair_performed = False
                if terminal_state is None:
                    if not task:
                        task_id = _create_command_task(
                            connection,
                            accepted,
                            artifact_ref,
                            canonical_payload_sha256,
                        )
                        task = {"id": task_id, "status": accepted["state"]}
                        repair_performed = True
                    if not job:
                        job = _create_command_job(
                            connection,
                            accepted,
                            artifact_ref,
                            canonical_payload_sha256,
                            int(task["id"]),
                        )
                        repair_performed = True
                    cursor.execute(
                        "UPDATE ls_go_command_identities SET task_id = ?, job_id = ?, "
                        "updated_at = ? WHERE command_id = ?",
                        (
                            task.get("id"),
                            job.get("job_id") or job.get("id"),
                            utc_now_iso(),
                            accepted["command_id"],
                        ),
                    )
                state = str(
                    terminal_state
                    or task.get("status")
                    or job.get("status")
                    or identity.get("queue_state")
                    or accepted["state"]
                )
                return {
                    "accepted": True,
                    "idempotent_replay": True,
                    "repair_performed": repair_performed,
                    "command_id": accepted["command_id"],
                    "canonical_payload_sha256": canonical_payload_sha256,
                    "task_id": task.get("id"),
                    "job": job or None,
                    "state": state,
                    "artifact_ref": artifact_ref,
                    "detail": (
                        "Existing immutable envelope reconciled to exactly one database lifecycle."
                        if repair_performed
                        else "Existing immutable command state returned; no queue, task, or job was created."
                    ),
                }

            now = utc_now_iso()
            cursor.execute(
                "INSERT INTO ls_go_command_identities "
                "(command_id, canonical_payload_sha256, queue_state, queue_occurrence_count, "
                "created_at, updated_at) VALUES (?, ?, 'reserved', 0, ?, ?)",
                (accepted["command_id"], canonical_payload_sha256, now, now),
            )
            _append_queue(shell_root, accepted)
            progress = command_index.advance_connection(connection)
            if not progress["complete"]:
                raise CommandQueueIndexStale(
                    "new command append exceeded the bounded identity-index window"
                )
            task_id = _create_command_task(
                connection,
                accepted,
                artifact_ref,
                canonical_payload_sha256,
            )
            job = _create_command_job(
                connection,
                accepted,
                artifact_ref,
                canonical_payload_sha256,
                task_id,
            )
            cursor.execute(
                "UPDATE ls_go_command_identities SET queue_state = ?, task_id = ?, "
                "job_id = ?, updated_at = ? WHERE command_id = ?",
                (
                    accepted["state"],
                    task_id,
                    job["job_id"],
                    utc_now_iso(),
                    accepted["command_id"],
                ),
            )
            return {
                "accepted": True,
                "idempotent_replay": False,
                "repair_performed": False,
                "command_id": accepted["command_id"],
                "canonical_payload_sha256": canonical_payload_sha256,
                "task_id": task_id,
                "job": job,
                "state": accepted["state"],
                "artifact_ref": artifact_ref,
                "detail": "Command persisted and routed to one transactional Desktop lifecycle.",
            }
    except (CommandIdentityConflict, CommandQueueIndexStale, CommandIdentitySchemaUnavailable):
        raise
    except Exception as exc:
        raise CommandDatabaseUnavailable(
            f"canonical command transaction failed: {type(exc).__name__}"
        ) from exc


def create_app(root: Path | str) -> FastAPI:
    # Preserve the stable D:\LightSpeed operator namespace. Path.resolve()
    # follows the App junction to its C-drive backing target and makes one
    # physical shell appear to be a second authority in status receipts.
    shell_root = Path(root).absolute()
    db, storage = _try_get_services(shell_root)
    command_identity_migration: dict[str, Any] = {
        "state": "held",
        "detail": "canonical_queue_indexes gate is not operator-authorized",
    }
    if _canonical_queue_index_gate_authorized(shell_root):
        ensure_schema = getattr(db, "ensure_ls_go_command_identity_schema", None)
        if callable(ensure_schema):
            try:
                ensure_schema()
                command_identity_migration = {
                    "state": "available",
                    "detail": "additive command identity schema verified in canonical database",
                }
            except Exception as exc:
                command_identity_migration = {
                    "state": "unavailable",
                    "detail": f"{type(exc).__name__}: {exc}",
                }
        else:
            command_identity_migration = {
                "state": "unavailable",
                "detail": "canonical database service does not expose the reviewed migration",
            }
    command_index = _PersistentCommandEnvelopeIndex(db, _queue_path(shell_root))
    project_pipeline = ProjectPipeline(shell_root)
    representation_edge = build_representation_edge_store(shell_root)
    representation_edge_error: str | None = None
    if representation_edge.enabled:
        review_queue, decisions, outbox = representation_review_paths(shell_root)
        try:
            representation_edge.seed_proof_graphs(
                review_queue_path=review_queue,
                decision_path=decisions,
                local_outbox=outbox,
            )
        except Exception as exc:
            representation_edge_error = f"{type(exc).__name__}: {exc}"
    app = FastAPI(
        title="LightSpeed GO Desktop Bridge",
        description="Local-only, Achilles-governed command, project and review bridge for LS GO.",
        version="1.2.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-LightSpeed-Owner-Confirmation"],
        max_age=600,
    )

    @app.get("/api/v1/status")
    async def status():
        # Merovingian materializes these receipts on its own interval. A health
        # request must stay read-only and must not rescan the complete project
        # tree or create review packets.
        registry = project_pipeline.latest_snapshot()
        health = registry.get("health") or {}
        health_details = health.get("details") or {}
        supervisor = _supervisor_status(shell_root)
        merovingian_healthy = health.get("status") == "pass" and bool(supervisor.get("alive"))
        core_services_healthy = bool(db) and bool(storage) and merovingian_healthy
        return JSONResponse(
            {
                "ok": core_services_healthy,
                "time_utc": utc_now_iso(),
                "bridge": "ls-go",
                "root": str(shell_root),
                "services": {
                    "db": bool(db),
                    "storage": bool(storage),
                    "merovingian": merovingian_healthy,
                },
                "merovingian": {
                    "status": "pass" if merovingian_healthy else "unavailable",
                    "receipt": str(project_pipeline.health_path),
                    "supervisor": supervisor,
                    "project_summary": registry.get("summary") or {},
                    "cleanup_summary": registry.get("cleanup_summary") or {},
                    "drive_writeback": health_details.get("drive_writeback"),
                    "root_resolution": health_details.get("root_resolution"),
                },
                "resources": health_details.get("resource_guard") or {},
                "agent_floors": health_details.get("agent_floors") or {},
                "canonical_queue_indexes": {
                    "command_identity": command_identity_migration,
                    "review_identity": "canonical_database_tables_or_bounded_fail_closed_fallback",
                },
                "queue_path": str(_queue_path(shell_root)),
                "review_queue_path": str(project_pipeline.review_queue_path),
                "representation_edge": {
                    **representation_edge.status(),
                    "error": representation_edge_error,
                },
                "execution_boundary": "local queue, immutable named artifacts, receipts and review only; no public direct execution",
            }
        )

    @app.get("/api/v1/tasks")
    async def list_tasks(limit: int = 30):
        if db:
            try:
                rows = db.execute_query(
                    "SELECT id, title, description, project_id, status, priority, created_at, updated_at, metadata_json "
                    "FROM tasks ORDER BY id DESC LIMIT ?",
                    (max(1, min(int(limit), 200)),),
                )
                return JSONResponse({"tasks": rows})
            except Exception:
                pass
        queue_rows = _read_queue(shell_root, limit=limit)
        tasks = [
            {
                "id": row.get("command_id"),
                "title": row.get("title"),
                "description": row.get("instruction"),
                "status": row.get("state", "queued"),
                "priority": row.get("priority", "normal"),
                "created_at": row.get("accepted_utc"),
            }
            for row in queue_rows
        ]
        return JSONResponse({"tasks": tasks})

    @app.get("/api/v1/projects")
    async def list_projects():
        registry = project_pipeline.latest_snapshot()
        if not registry.get("projects"):
            # Fresh, test and recovery shells may not yet have a supervisor
            # receipt. Populate once without queueing a synthetic change.
            registry = project_pipeline.refresh(force=True, queue_changes=False)
        return JSONResponse(
            {
                "projects": registry.get("projects") or [],
                "summary": registry.get("summary") or {},
                "duplicate_names": registry.get("duplicate_names") or [],
                "cleanup_summary": registry.get("cleanup_summary") or {},
            }
        )

    @app.get("/api/v1/reviews")
    async def list_reviews(limit: int = 50):
        return JSONResponse(
            {"reviews": project_pipeline.list_reviews(limit=max(1, min(int(limit), 200)))}
        )

    @app.post("/api/v1/reviews/{review_id}/decision")
    async def decide_review(review_id: str, body: dict[str, Any]):
        decision = _bounded(body.get("decision"), maximum=16, required=True).lower()
        note = _bounded(body.get("note"), maximum=1000)
        try:
            receipt = project_pipeline.decide_review(review_id, decision, note)
        except KeyError:
            raise HTTPException(status_code=404, detail="Review item not found")
        except ReviewDecisionConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return JSONResponse({"accepted": True, "receipt": receipt})

    def require_representation_edge():
        if not representation_edge.enabled:
            raise HTTPException(
                status_code=404,
                detail="Canonical representation edge is disabled by feature flag.",
            )
        if representation_edge_error:
            raise HTTPException(status_code=503, detail=representation_edge_error)
        try:
            state = representation_edge.status()
        except RepresentationEdgeDisabled as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        if not state.get("migration_applied"):
            raise HTTPException(status_code=503, detail="Representation-edge migration is unavailable.")
        return representation_edge

    @app.get("/api/v1/representation-edge/status")
    async def representation_edge_status():
        return JSONResponse(
            {
                **representation_edge.status(),
                "error": representation_edge_error,
                "drive_write_executed": False,
            }
        )

    @app.get("/api/v1/representation-graphs")
    async def list_representation_graphs():
        edge = require_representation_edge()
        return JSONResponse({"graphs": edge.list_graphs()})

    @app.get("/api/v1/representation-graphs/{object_id:path}")
    async def get_representation_graph(object_id: str):
        edge = require_representation_edge()
        try:
            graph = edge.graph(_bounded(object_id, maximum=160, required=True))
        except KeyError:
            raise HTTPException(status_code=404, detail="Canonical object candidate not found")
        return JSONResponse({"graph": graph})

    @app.get("/api/v1/representation-reviews")
    async def list_representation_reviews():
        edge = require_representation_edge()
        return JSONResponse({"reviews": edge.list_reviews()})

    @app.post("/api/v1/representation-reviews/{review_id}/decision")
    async def decide_representation_review(
        review_id: str,
        body: dict[str, Any],
        owner_confirmation: str | None = Header(
            default=None,
            alias="X-LightSpeed-Owner-Confirmation",
        ),
    ):
        edge = require_representation_edge()
        decision = _bounded(body.get("decision"), maximum=32, required=True)
        actor = _verified_owner_actor(owner_confirmation)
        scope = _bounded(body.get("scope") or "identity", maximum=16, required=True)
        note = _bounded(body.get("note"), maximum=1000)
        raw_edge_ids = body.get("edge_ids") or []
        if not isinstance(raw_edge_ids, list):
            raise HTTPException(status_code=400, detail="edge_ids must be a bounded list")
        edge_ids = [_bounded(value, maximum=160, required=True) for value in raw_edge_ids[:100]]
        _, decision_path, outbox = representation_review_paths(shell_root)
        try:
            receipt = edge.record_decision(
                review_id=_bounded(review_id, maximum=96, required=True),
                decision=decision,
                actor=actor,
                owner_authenticated=True,
                scope=scope,
                note=note,
                edge_ids=edge_ids,
                decision_path=decision_path,
                local_outbox=outbox,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Representation review not found")
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except RepresentationValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return JSONResponse({"accepted": True, "receipt": receipt})

    @app.get("/api/v1/representation-promotions")
    async def list_representation_promotions():
        edge = require_representation_edge()
        return JSONResponse(
            {
                "promotions": edge.list_promotions(),
                "drive_write_executed": False,
                "readback_required": True,
            }
        )

    @app.post("/api/v1/projects/{project_id}/receipts")
    async def accept_project_receipt(project_id: str, body: dict[str, Any]):
        bounded_project_id = _bounded(project_id, maximum=96, required=True)
        summary = _bounded(body.get("summary"), maximum=4000, required=True)
        raw_paths = body.get("artifact_paths") or []
        if not isinstance(raw_paths, list):
            raise HTTPException(status_code=400, detail="artifact_paths must be a list")
        artifact_paths = [_bounded(value, maximum=1000) for value in raw_paths]
        try:
            artifact_manifest = stage_project_artifacts(
                project_pipeline,
                project_id=bounded_project_id,
                artifact_paths=artifact_paths,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Registered project not found")
        except (ValueError, FileNotFoundError, FileExistsError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        copied_paths = [
            str(item.get("destination_path"))
            for item in artifact_manifest.get("copied") or []
            if item.get("destination_path")
        ]
        review_artifacts = [str(artifact_manifest["manifest_path"]), *copied_paths]
        staging_summary = (
            f"{summary} Immutable artifact staging: "
            f"{artifact_manifest.get('copied_count', 0)} copied, "
            f"{artifact_manifest.get('skipped_count', 0)} skipped; "
            f"mode={artifact_manifest.get('drive_writeback_mode')}."
        )
        packet = project_pipeline.queue_project_work_receipt(
            project_id=bounded_project_id,
            summary=staging_summary,
            artifact_paths=review_artifacts,
        )
        return JSONResponse(
            {
                "accepted": True,
                "review": packet,
                "artifact_manifest": artifact_manifest,
            }
        )

    @app.post("/api/v1/ls-go/commands")
    async def accept_command(body: dict[str, Any]):
        if body.get("schema_version") != COMMAND_SCHEMA:
            raise HTTPException(status_code=400, detail="Unsupported command schema")

        try:
            command_id = _validated_command_id(
                _bounded(body.get("command_id"), maximum=96, required=True)
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        instruction = _bounded(body.get("instruction"), maximum=4000, required=True)
        title = _bounded(body.get("title") or instruction, maximum=160, required=True)
        target_floor = _bounded(body.get("target_floor"), maximum=40, required=True)
        priority = _bounded(body.get("priority") or "normal", maximum=16)
        execution_mode = _bounded(body.get("execution_mode") or "review", maximum=16)

        if target_floor not in ALLOWED_FLOORS:
            raise HTTPException(status_code=400, detail="Unsupported target floor")
        if priority not in ALLOWED_PRIORITIES:
            raise HTTPException(status_code=400, detail="Unsupported priority")
        if execution_mode not in ALLOWED_MODES:
            raise HTTPException(status_code=400, detail="Unsupported execution mode")
        if body.get("oversight_floor") != "Achilles":
            raise HTTPException(status_code=400, detail="Achilles oversight is required")
        if body.get("proof_required") is not True or body.get("public_safe") is not True:
            raise HTTPException(status_code=400, detail="Proof and public-safe gates are required")

        accepted = {
            "schema_version": COMMAND_SCHEMA,
            "command_id": command_id,
            "accepted_utc": utc_now_iso(),
            "source": "LS GO",
            "title": title,
            "instruction": instruction,
            "target_floor": target_floor,
            "oversight_floor": "Achilles",
            "priority": priority,
            "execution_mode": execution_mode,
            "state": "review" if execution_mode == "review" else "queued",
            "proof_required": True,
            "public_safe": True,
        }
        canonical_payload_sha256 = _command_payload_sha256(accepted)
        accepted["canonical_payload_sha256"] = canonical_payload_sha256

        try:
            command_index.synchronize()
            with _COMMAND_SUBMISSION_LOCK:
                result = _submit_command_transaction(
                    db,
                    command_index,
                    shell_root,
                    accepted,
                    canonical_payload_sha256,
                )
        except CommandIdentityConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except (
            CommandDatabaseUnavailable,
            CommandIdentitySchemaUnavailable,
            CommandQueueIndexStale,
            CommandQueueIndexPreparing,
        ) as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        if result.get("index_pending"):
            progress = result["index_pending"]
            raise HTTPException(
                status_code=503,
                detail=(
                    "bounded command identity index preparing: "
                    f"{progress['offset']}/{progress['size']} bytes"
                ),
            )
        return JSONResponse(result)

    return app


def start_server(root: Path | str, host: str = "127.0.0.1", port: int = 8765) -> None:
    uvicorn.run(create_app(root), host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server(Path(os.environ.get("LIGHTSPEED_ROOT", Path.cwd())))
