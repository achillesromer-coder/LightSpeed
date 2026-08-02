from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import fnmatch
import hashlib
import importlib
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import sqlite3
import sys
import threading
import time
from typing import Any, Iterable

from lightspeed_runtime.startup_options import CANONICAL_DATABASE_PATH

SCHEMA_VERSION = "lightspeed-project-routing-v1"
REVIEW_SCHEMA = "lightspeed-go-project-review-v1"
_REVIEW_DECISION_LOCK = threading.Lock()
_JSONL_INDEX_SCAN_BYTES = 8 * 1024 * 1024
_JSONL_MAX_LINE_BYTES = 1024 * 1024
_JSONL_MAX_IDENTITY_MATCHES = 64
_JSONL_MEMORY_IDENTITY_LIMIT = 4096
_JSONL_TAIL_READ_BYTES = 4 * 1024 * 1024


class ReviewDecisionConflict(ValueError):
    """Raised when one review identity is reused for a different owner decision."""


class ReviewIndexPending(ValueError):
    """Raised when a bounded identity-index pass has not reached ledger EOF."""

FLOOR_ROOTS = {
    "Architect": "Z+1_Architect",
    "Neo": "Z+2_Neo",
    "Trinity": "Z+3_Trinity",
    "Morpheus": "Z-1_Morpheus",
    "Oracle": "Z-2_Oracle",
    "Smith": "Z-3_Smith",
    "Merovingian": "Z-4_Merovingian",
    "TheConstruct": "Z0_TheConstruct",
}


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _memory_snapshot() -> tuple[int, int]:
    """Return total and available physical memory using only the standard library."""
    if os.name == "nt":
        import ctypes

        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys), int(status.ullAvailPhys)
        raise OSError("GlobalMemoryStatusEx failed")

    page_size = int(os.sysconf("SC_PAGE_SIZE"))
    total = page_size * int(os.sysconf("SC_PHYS_PAGES"))
    available = page_size * int(os.sysconf("SC_AVPHYS_PAGES"))
    return total, available


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        for attempt in range(8):
            try:
                temporary.replace(path)
                return
            except PermissionError:
                # Antivirus, indexers, Explorer and bridge readers can briefly
                # retain a Windows handle that denies the atomic replacement.
                # Keep the prior complete JSON visible and retry the commit.
                if attempt == 7:
                    raise
                time.sleep(0.05 * (attempt + 1))
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def _bounded_jsonl_tail(path: Path, *, byte_limit: int) -> bytes:
    """Read only the bounded tail, dropping a leading partial record."""
    if not path.is_file():
        return b""
    try:
        size_bytes = int(path.stat().st_size)
        read_size = min(size_bytes, max(1, int(byte_limit)))
        start = max(0, size_bytes - read_size)
        with path.open("rb") as stream:
            stream.seek(start)
            payload = stream.read(read_size)
    except OSError:
        return b""
    if start:
        newline = payload.find(b"\n")
        if newline < 0:
            return b""
        payload = payload[newline + 1 :]
    return payload


def _read_jsonl(
    path: Path,
    limit: int = 200,
    *,
    byte_limit: int = _JSONL_TAIL_READ_BYTES,
    line_limit: int = _JSONL_MAX_LINE_BYTES,
) -> list[dict[str, Any]]:
    max_rows = max(1, min(int(limit), 2000))
    bounded_bytes = max(4096, min(int(byte_limit), _JSONL_TAIL_READ_BYTES))
    bounded_line = max(1, min(int(line_limit), _JSONL_MAX_LINE_BYTES))
    payload = _bounded_jsonl_tail(path, byte_limit=bounded_bytes)
    if not payload:
        return []
    rows: list[dict[str, Any]] = []
    lines = payload.split(b"\n")
    if lines and not lines[-1]:
        lines.pop()
    for raw in lines[-max_rows:]:
        raw = raw.rstrip(b"\r")
        if not raw.strip() or len(raw) > bounded_line:
            continue
        try:
            value = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


class _JsonlIdentityIndex:
    """Index immutable JSONL identities as offsets, never retained row payloads.

    The production backend is a pair of tables in the sole canonical LightSpeed
    database.  Fixtures and pre-migration shells use a small fail-closed memory
    index; that fallback cannot grow beyond ``memory_identity_limit``.
    """

    SOURCE_TABLE = "immutable_jsonl_index_sources"
    OFFSET_TABLE = "immutable_jsonl_identity_offsets"

    def __init__(
        self,
        path: Path,
        field: str,
        *,
        scan_bytes: int | None = None,
        database_path: Path | None = None,
        allow_schema_create: bool = False,
        memory_identity_limit: int = _JSONL_MEMORY_IDENTITY_LIMIT,
    ):
        self.path = Path(path)
        self.field = str(field)
        self.scan_bytes = max(4096, int(scan_bytes or _JSONL_INDEX_SCAN_BYTES))
        self.database_path = Path(database_path) if database_path is not None else None
        self.allow_schema_create = bool(allow_schema_create)
        self.memory_identity_limit = max(1, int(memory_identity_limit))
        source_identity = f"{os.path.normcase(os.path.abspath(str(self.path)))}\0{self.field}"
        self.source_key = hashlib.sha256(source_identity.encode("utf-8")).hexdigest()
        self._lock = threading.Lock()
        self._file_identity: tuple[int, int] | None = None
        self._offset = 0
        self._observed_size = 0
        self._observed_mtime_ns = 0
        self._partial = b""
        self._memory_offsets: dict[str, list[tuple[int, int]]] = {}
        self._complete = False

    @property
    def resident_identity_count(self) -> int:
        return len(self._memory_offsets)

    def _reset_memory(self) -> None:
        self._file_identity = None
        self._offset = 0
        self._observed_size = 0
        self._observed_mtime_ns = 0
        self._partial = b""
        self._memory_offsets.clear()
        self._complete = False

    def _connect(self) -> sqlite3.Connection:
        if self.database_path is None:
            raise ReviewIndexPending("canonical SQLite identity index is not configured")
        if not self.database_path.is_file():
            raise ReviewIndexPending(
                f"existing canonical SQLite database is required: {self.database_path}"
            )
        uri = self.database_path.absolute().as_uri() + "?mode=rw"
        connection = sqlite3.connect(uri, uri=True, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _prepare_schema(self, connection: sqlite3.Connection) -> None:
        names = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?, ?)",
                (self.SOURCE_TABLE, self.OFFSET_TABLE),
            )
        }
        required = {self.SOURCE_TABLE, self.OFFSET_TABLE}
        if names == required:
            return
        if not self.allow_schema_create:
            raise ReviewIndexPending(
                "canonical JSONL identity-index schema activation remains review-gated"
            )
        connection.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS {self.SOURCE_TABLE} (
                source_key TEXT PRIMARY KEY,
                source_path TEXT NOT NULL,
                identity_field TEXT NOT NULL,
                file_device INTEGER,
                file_inode INTEGER,
                indexed_offset INTEGER NOT NULL DEFAULT 0,
                observed_size INTEGER NOT NULL DEFAULT 0,
                observed_mtime_ns INTEGER NOT NULL DEFAULT 0,
                partial_record BLOB NOT NULL DEFAULT X'',
                complete INTEGER NOT NULL DEFAULT 0,
                updated_utc TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS {self.OFFSET_TABLE} (
                source_key TEXT NOT NULL,
                identity TEXT NOT NULL,
                byte_offset INTEGER NOT NULL,
                byte_length INTEGER NOT NULL,
                PRIMARY KEY (source_key, byte_offset)
            );
            CREATE INDEX IF NOT EXISTS idx_immutable_jsonl_identity_lookup
            ON {self.OFFSET_TABLE} (source_key, identity, byte_offset);
            """
        )

    def _parse_locator(self, raw: bytes, byte_offset: int) -> tuple[str, int, int] | None:
        if not raw.strip():
            return None
        if len(raw) > _JSONL_MAX_LINE_BYTES:
            raise ValueError(f"JSONL record exceeds bounded line limit: {self.path}")
        try:
            value = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return None
        if not isinstance(value, dict):
            return None
        identity = str(value.get(self.field) or "")
        if not identity:
            return None
        return identity, int(byte_offset), len(raw)

    def _scan_chunk(
        self,
        *,
        offset: int,
        partial: bytes,
        size_bytes: int,
    ) -> tuple[list[tuple[str, int, int]], int, bytes, bool, int]:
        remaining = max(0, int(size_bytes) - int(offset))
        read_size = min(remaining, self.scan_bytes)
        chunk = b""
        if read_size:
            with self.path.open("rb") as stream:
                stream.seek(offset)
                chunk = stream.read(read_size)
        next_offset = int(offset) + len(chunk)
        content = bytes(partial) + chunk
        content_start = int(offset) - len(partial)
        parts = content.split(b"\n")
        at_snapshot_end = next_offset >= int(size_bytes)
        next_partial = b"" if at_snapshot_end else (parts.pop() if parts else content)
        if len(next_partial) > _JSONL_MAX_LINE_BYTES:
            raise ValueError(f"JSONL record exceeds bounded line limit: {self.path}")

        locators: list[tuple[str, int, int]] = []
        relative_offset = 0
        for raw in parts:
            clean = raw.rstrip(b"\r")
            locator = self._parse_locator(clean, content_start + relative_offset)
            if locator is not None:
                locators.append(locator)
            relative_offset += len(raw) + 1
        return locators, next_offset, next_partial, at_snapshot_end, len(chunk)

    def _advance_memory(self, stat: os.stat_result) -> dict[str, Any]:
        identity = (int(stat.st_dev), int(stat.st_ino))
        replaced = self._file_identity is not None and identity != self._file_identity
        truncated = stat.st_size < self._offset
        rewritten_at_same_size = (
            self._file_identity == identity
            and stat.st_size == self._observed_size
            and self._observed_size > 0
            and stat.st_mtime_ns != self._observed_mtime_ns
        )
        if replaced or truncated or rewritten_at_same_size:
            self._reset_memory()
        self._file_identity = identity
        locators, next_offset, partial, complete, scanned = self._scan_chunk(
            offset=self._offset,
            partial=self._partial,
            size_bytes=int(stat.st_size),
        )
        new_identities = {item[0] for item in locators} - set(self._memory_offsets)
        if len(self._memory_offsets) + len(new_identities) > self.memory_identity_limit:
            raise ReviewIndexPending(
                "bounded memory identity index reached capacity; activate the reviewed "
                "canonical SQLite index tables before processing this ledger"
            )
        for record_identity, byte_offset, byte_length in locators:
            matches = self._memory_offsets.setdefault(record_identity, [])
            if len(matches) >= _JSONL_MAX_IDENTITY_MATCHES:
                raise ValueError(f"too many JSONL records share identity {record_identity!r}")
            matches.append((byte_offset, byte_length))
        self._offset = next_offset
        self._partial = partial
        self._observed_size = int(stat.st_size)
        self._observed_mtime_ns = int(stat.st_mtime_ns)
        self._complete = complete
        return {
            "complete": complete,
            "scanned_bytes": scanned,
            "indexed_locator_delta": len(locators),
            "resident_identity_count": self.resident_identity_count,
            "storage_backend": "bounded_memory",
            "offset": next_offset,
            "size_bytes": int(stat.st_size),
        }

    def _advance_sqlite(self, stat: os.stat_result) -> dict[str, Any]:
        with self._connect() as connection:
            self._prepare_schema(connection)
            row = connection.execute(
                f"SELECT * FROM {self.SOURCE_TABLE} WHERE source_key=?",
                (self.source_key,),
            ).fetchone()
            state = dict(row) if row is not None else {
                "file_device": None,
                "file_inode": None,
                "indexed_offset": 0,
                "observed_size": 0,
                "observed_mtime_ns": 0,
                "partial_record": b"",
                "complete": 0,
            }
            identity = (int(stat.st_dev), int(stat.st_ino))
            prior_identity = (
                int(state["file_device"]),
                int(state["file_inode"]),
            ) if state.get("file_device") is not None and state.get("file_inode") is not None else None
            offset = int(state.get("indexed_offset") or 0)
            observed_size = int(state.get("observed_size") or 0)
            replaced = prior_identity is not None and identity != prior_identity
            truncated = int(stat.st_size) < offset
            rewritten_at_same_size = (
                prior_identity == identity
                and int(stat.st_size) == observed_size
                and observed_size > 0
                and int(stat.st_mtime_ns) != int(state.get("observed_mtime_ns") or 0)
            )
            if replaced or truncated or rewritten_at_same_size:
                connection.execute(
                    f"DELETE FROM {self.OFFSET_TABLE} WHERE source_key=?",
                    (self.source_key,),
                )
                offset = 0
                state["partial_record"] = b""

            locators, next_offset, partial, complete, scanned = self._scan_chunk(
                offset=offset,
                partial=bytes(state.get("partial_record") or b""),
                size_bytes=int(stat.st_size),
            )
            connection.executemany(
                f"""
                INSERT OR REPLACE INTO {self.OFFSET_TABLE}
                    (source_key, identity, byte_offset, byte_length)
                VALUES (?, ?, ?, ?)
                """,
                (
                    (self.source_key, record_identity, byte_offset, byte_length)
                    for record_identity, byte_offset, byte_length in locators
                ),
            )
            connection.execute(
                f"""
                INSERT INTO {self.SOURCE_TABLE} (
                    source_key, source_path, identity_field, file_device, file_inode,
                    indexed_offset, observed_size, observed_mtime_ns, partial_record,
                    complete, updated_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_key) DO UPDATE SET
                    source_path=excluded.source_path,
                    identity_field=excluded.identity_field,
                    file_device=excluded.file_device,
                    file_inode=excluded.file_inode,
                    indexed_offset=excluded.indexed_offset,
                    observed_size=excluded.observed_size,
                    observed_mtime_ns=excluded.observed_mtime_ns,
                    partial_record=excluded.partial_record,
                    complete=excluded.complete,
                    updated_utc=excluded.updated_utc
                """,
                (
                    self.source_key,
                    str(self.path.absolute()),
                    self.field,
                    identity[0],
                    identity[1],
                    next_offset,
                    int(stat.st_size),
                    int(stat.st_mtime_ns),
                    sqlite3.Binary(partial),
                    int(complete),
                    utc_now_iso(),
                ),
            )
        return {
            "complete": complete,
            "scanned_bytes": scanned,
            "indexed_locator_delta": len(locators),
            "resident_identity_count": 0,
            "storage_backend": "canonical_sqlite",
            "offset": next_offset,
            "size_bytes": int(stat.st_size),
        }

    def _reset_missing(self) -> None:
        if self.database_path is None:
            self._reset_memory()
            self._complete = True
            return
        with self._connect() as connection:
            self._prepare_schema(connection)
            connection.execute(
                f"DELETE FROM {self.OFFSET_TABLE} WHERE source_key=?",
                (self.source_key,),
            )
            connection.execute(
                f"DELETE FROM {self.SOURCE_TABLE} WHERE source_key=?",
                (self.source_key,),
            )

    def advance(self) -> dict[str, Any]:
        """Read at most one bounded chunk and preserve ledger bytes and mtime."""
        with self._lock:
            try:
                stat = self.path.stat()
            except OSError:
                self._reset_missing()
                return {
                    "complete": True,
                    "scanned_bytes": 0,
                    "resident_identity_count": self.resident_identity_count,
                    "storage_backend": (
                        "canonical_sqlite" if self.database_path is not None else "bounded_memory"
                    ),
                    "size_bytes": 0,
                }
            if self.database_path is not None:
                return self._advance_sqlite(stat)
            return self._advance_memory(stat)

    def _read_offsets(self, expected: str) -> list[tuple[int, int]]:
        if self.database_path is None:
            return list(self._memory_offsets.get(str(expected), []))
        with self._connect() as connection:
            self._prepare_schema(connection)
            rows = connection.execute(
                f"""
                SELECT byte_offset, byte_length
                FROM {self.OFFSET_TABLE}
                WHERE source_key=? AND identity=?
                ORDER BY byte_offset
                LIMIT ?
                """,
                (self.source_key, str(expected), _JSONL_MAX_IDENTITY_MATCHES + 1),
            ).fetchall()
        if len(rows) > _JSONL_MAX_IDENTITY_MATCHES:
            raise ValueError(f"too many JSONL records share identity {expected!r}")
        return [(int(row[0]), int(row[1])) for row in rows]

    def _read_rows(self, expected: str, offsets: list[tuple[int, int]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if not offsets:
            return rows
        with self.path.open("rb") as stream:
            for byte_offset, byte_length in offsets:
                stream.seek(byte_offset)
                raw = stream.read(byte_length)
                try:
                    value = json.loads(raw.decode("utf-8", errors="replace"))
                except json.JSONDecodeError as exc:
                    raise ReviewIndexPending(
                        f"indexed JSONL locator no longer resolves cleanly: {self.path}"
                    ) from exc
                if not isinstance(value, dict) or str(value.get(self.field) or "") != str(expected):
                    raise ReviewIndexPending(
                        f"indexed JSONL identity no longer matches immutable source: {self.path}"
                    )
                rows.append(value)
        return rows

    def find(self, expected: str) -> list[dict[str, Any]]:
        progress = self.advance()
        if not progress["complete"]:
            raise ReviewIndexPending(
                f"bounded identity index is still preparing {self.path.name}: "
                f"{progress['offset']}/{progress['size_bytes']} bytes; retry after the next cycle"
            )
        return self._read_rows(str(expected), self._read_offsets(str(expected)))


def _review_decision_contract(review_id: str, decision: str, note: str) -> dict[str, Any]:
    return {
        "schema_version": "lightspeed-go-review-decision-v1",
        "review_id": review_id,
        "decision": decision,
        "note": note,
        "decided_by": "Nathaniel Bouwer / Achilles GO gate",
        "applies_external_write": False,
    }


def _review_decision_sha256(review_id: str, decision: str, note: str) -> str:
    payload = json.dumps(
        _review_decision_contract(review_id, decision, note),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _ensure_fixed_json_receipt(path: Path, payload: dict[str, Any]) -> str:
    """Verify or repair one fixed receipt without creating history variants."""
    existed = path.is_file()
    if existed and _read_json(path) == payload:
        return "verified_existing"
    _write_json(path, payload)
    if _read_json(path) != payload:
        raise OSError(f"fixed receipt readback failed: {path}")
    return "repaired_mismatch" if existed else "repaired_missing"


def _slug(value: str) -> str:
    result = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
    while "--" in result:
        result = result.replace("--", "-")
    return result[:72] or "project"


def _windows_absolute(value: str) -> bool:
    return bool(PureWindowsPath(value).drive)


def _has_project_routing_contract(path: Path) -> bool:
    return (path / "config" / "project_routing.json").is_file()


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _embedded_core_services(merovingian_root: Path) -> Any:
    """Import Merovingian services only when module origin proves identity."""
    embedded_core = Path(merovingian_root) / "core"
    if not embedded_core.is_dir():
        raise ImportError("embedded_core_unavailable_for_shell_root")
    root_text = str(merovingian_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    services = importlib.import_module("core.services")
    origin_text = str(getattr(services, "__file__", "") or "")
    if not origin_text or not _path_is_within(Path(origin_text), embedded_core):
        raise ImportError(
            "ambient core.services origin rejected: "
            f"{origin_text or 'unknown'}; expected under {embedded_core}"
        )
    return services


def _canonical_shell_root(requested: Path) -> tuple[Path, str]:
    """Resolve runtime callers onto the one Desktop shell receipt authority."""
    requested = requested.absolute()
    if _has_project_routing_contract(requested):
        return requested, "requested_contract_root"

    candidates: list[tuple[Path, str]] = []
    configured = os.environ.get("LIGHTSPEED_SHELL_ROOT", "").strip()
    if configured:
        candidates.append((Path(configured), "environment_contract_root"))
    if requested.name.casefold() == "lightspeed_runtime":
        candidates.append(
            (requested.parent / "Desktop_Hooks" / "LightSpeed", "runtime_sibling_contract_root")
        )
    candidates.append(
        (requested / "Desktop_Hooks" / "LightSpeed", "workspace_child_contract_root")
    )

    seen: set[str] = set()
    for candidate, mode in candidates:
        resolved = candidate.absolute()
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        if _has_project_routing_contract(resolved):
            return resolved, mode
    return requested, "unresolved_requested_root"


@dataclass(frozen=True)
class ProjectRoot:
    root_id: str
    path: Path
    authority: str
    writable: bool


class ProjectPipeline:
    """Merovingian-owned project inventory, evidence and GO review pipeline.

    Project source content is read-only here. The pipeline writes compact runtime
    receipts, a project registry, cleanup candidates and GO review decisions only.
    It never deletes, archives, publishes or mutates workbooks.
    """

    def __init__(self, shell_root: Path | str):
        self.requested_shell_root = Path(shell_root).absolute()
        self.shell_root, self.root_resolution_mode = _canonical_shell_root(self.requested_shell_root)
        self.config_path = self.shell_root / "config" / "project_routing.json"
        self.config = _read_json(self.config_path)
        self.merovingian_root = self.shell_root / "Z Axis" / "Z-4_Merovingian"
        self.runtime_exports = self.merovingian_root / "data" / "runtime_exports"
        self.registry_path = self.runtime_exports / "project_registry.json"
        self.registry_state_path = self.runtime_exports / "project_registry_state.json"
        self.health_path = self.runtime_exports / "merovingian_health.json"
        self.floor_health_path = self.runtime_exports / "agent_floor_health.json"
        self.cleanup_path = self.runtime_exports / "cleanup_candidates.json"
        go_config = self.config.get("go_review") if isinstance(self.config.get("go_review"), dict) else {}
        self.review_queue_path = self._resolve_shell_path(
            str(go_config.get("queue_path") or "Z Axis/Z-4_Merovingian/data/runtime_exports/go_review_queue.jsonl")
        )
        self.review_decisions_path = self._resolve_shell_path(
            str(go_config.get("decision_path") or "Z Axis/Z-4_Merovingian/data/runtime_exports/go_review_decisions.jsonl")
        )
        index_options = self._review_index_options(go_config)
        self._review_queue_index = _JsonlIdentityIndex(
            self.review_queue_path,
            "review_id",
            **index_options,
        )
        self._review_decisions_index = _JsonlIdentityIndex(
            self.review_decisions_path,
            "review_id",
            **index_options,
        )
        self._last_refresh_monotonic = 0.0
        self._cached_registry: dict[str, Any] = {}

    def _review_index_options(self, go_config: dict[str, Any]) -> dict[str, Any]:
        """Resolve an index backend without inventing a second database.

        Schema activation is deliberately explicit.  Until the reviewed state
        is enabled on the canonical operator shell, the capped memory fallback
        supports small fixtures and fails closed before RAM can grow unchecked.
        """
        config = go_config.get("identity_index")
        config = config if isinstance(config, dict) else {}
        options: dict[str, Any] = {
            "scan_bytes": int(config.get("scan_bytes_per_cycle") or _JSONL_INDEX_SCAN_BYTES),
            "memory_identity_limit": int(
                config.get("fallback_memory_identity_limit") or _JSONL_MEMORY_IDENTITY_LIMIT
            ),
        }
        if str(config.get("backend") or "").casefold() != "canonical_database_tables":
            return options
        if str(config.get("schema_activation") or "").casefold() != "owner_approved":
            return options

        operator_shell_text = str(config.get("required_operator_shell") or r"D:\LightSpeed\App")
        operator_shell = Path(operator_shell_text)
        try:
            if not operator_shell.is_dir() or not os.path.samefile(self.shell_root, operator_shell):
                return options
        except OSError:
            return options

        launch_control = _read_json(self.shell_root / "config" / "launch_control.json")
        manual_gates = launch_control.get("manual_gates")
        index_gate = next(
            (
                item
                for item in (manual_gates if isinstance(manual_gates, list) else [])
                if isinstance(item, dict)
                and item.get("gate_id") == "canonical_queue_indexes"
            ),
            {},
        )
        if str(index_gate.get("state") or "").casefold() != "operator_authorized":
            return options
        authorities = launch_control.get("canonical_authorities")
        authorities = authorities if isinstance(authorities, dict) else {}
        database_text = str(authorities.get("database") or "").strip()
        database_path = Path(database_text).expanduser() if database_text else None
        if (
            database_path is None
            or not (database_path.is_absolute() or _windows_absolute(database_text))
            or database_path.name.casefold() != "lightspeed_unified.db"
            or not database_path.is_file()
        ):
            return options
        canonical_database = Path(CANONICAL_DATABASE_PATH)
        try:
            if not canonical_database.is_file() or not os.path.samefile(
                database_path,
                canonical_database,
            ):
                return options
        except (OSError, ValueError):
            return options
        return {
            **options,
            "database_path": database_path,
            "allow_schema_create": True,
        }

    def _resolve_shell_path(self, value: str) -> Path:
        if not value:
            return self.shell_root
        candidate = Path(value)
        if candidate.is_absolute() or _windows_absolute(value):
            return candidate
        return self.shell_root / candidate

    def _scan_policy(self) -> dict[str, Any]:
        value = self.config.get("scan_policy")
        return value if isinstance(value, dict) else {}

    def _resource_guard(self) -> dict[str, Any]:
        value = self.config.get("resource_guard")
        return value if isinstance(value, dict) else {}

    def _disk_health(self) -> dict[str, Any]:
        guard = self._resource_guard()
        configured = [str(item) for item in guard.get("volume_paths") or [] if str(item).strip()]
        paths = configured or [str(self.shell_root)]
        warning_percent = float(guard.get("warning_disk_percent") or 85)
        critical_percent = float(guard.get("critical_disk_percent") or 95)
        minimum_free_bytes = int(guard.get("minimum_free_bytes") or 0)
        previous = _read_json(self.health_path)
        previous_rows = {
            str(item.get("path")): item
            for item in ((previous.get("details") or {}).get("disks") or [])
            if isinstance(item, dict) and item.get("path")
        }
        previous_time = None
        try:
            previous_time = datetime.fromisoformat(str(previous.get("generated_utc")).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            pass
        sample_seconds = (
            max(1.0, (datetime.now(UTC) - previous_time).total_seconds())
            if previous_time is not None else None
        )

        rows: list[dict[str, Any]] = []
        for value in paths:
            path = Path(value)
            try:
                usage = shutil.disk_usage(path)
            except OSError as exc:
                rows.append({
                    "path": value,
                    "state": "critical",
                    "available": False,
                    "error": f"{type(exc).__name__}:{exc}",
                })
                continue
            used_percent = (usage.used / usage.total * 100.0) if usage.total else 0.0
            state = "pass"
            if used_percent >= critical_percent or (minimum_free_bytes and usage.free < minimum_free_bytes):
                state = "critical"
            elif used_percent >= warning_percent or (
                minimum_free_bytes and usage.free < minimum_free_bytes * 2
            ):
                state = "warning"
            prior = previous_rows.get(value) or {}
            growth = usage.used - int(prior.get("used_bytes") or usage.used)
            hours_to_warning = None
            if sample_seconds and growth > 0 and usage.total:
                warning_used = int(usage.total * warning_percent / 100.0)
                remaining = max(0, warning_used - usage.used)
                bytes_per_second = growth / sample_seconds
                hours_to_warning = round(remaining / bytes_per_second / 3600.0, 2) if bytes_per_second else None
            rows.append({
                "path": value,
                "volume": path.anchor or value,
                "available": True,
                "state": state,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "used_percent": round(used_percent, 2),
                "growth_bytes_since_previous": growth if sample_seconds else None,
                "sample_seconds": round(sample_seconds, 1) if sample_seconds else None,
                "estimated_hours_to_warning": hours_to_warning,
            })
        overall = "critical" if any(row.get("state") == "critical" for row in rows) else (
            "warning" if any(row.get("state") == "warning" for row in rows) else "pass"
        )
        return {
            "schema_version": "lightspeed-volume-health-v1",
            "state": overall,
            "warning_disk_percent": warning_percent,
            "critical_disk_percent": critical_percent,
            "minimum_free_bytes": minimum_free_bytes,
            "volumes": rows,
        }

    def _memory_health(self) -> dict[str, Any]:
        guard = self._resource_guard()
        warning_free_percent = float(guard.get("warning_free_memory_percent") or 15)
        critical_free_percent = float(guard.get("critical_free_memory_percent") or 8)
        minimum_free_bytes = int(guard.get("minimum_free_memory_bytes") or 2 * 1024**3)
        try:
            total_bytes, free_bytes = _memory_snapshot()
        except (OSError, ValueError) as exc:
            return {
                "available": False,
                "state": "warning",
                "error": f"{type(exc).__name__}:{exc}",
                "warning_free_percent": warning_free_percent,
                "critical_free_percent": critical_free_percent,
                "minimum_free_bytes": minimum_free_bytes,
            }

        free_percent = (free_bytes / total_bytes * 100.0) if total_bytes else 0.0
        state = "pass"
        if free_percent <= critical_free_percent or free_bytes < minimum_free_bytes:
            state = "critical"
        elif free_percent <= warning_free_percent or free_bytes < minimum_free_bytes * 2:
            state = "warning"
        return {
            "available": True,
            "state": state,
            "total_bytes": total_bytes,
            "free_bytes": free_bytes,
            "used_bytes": max(0, total_bytes - free_bytes),
            "free_percent": round(free_percent, 2),
            "used_percent": round(100.0 - free_percent, 2),
            "warning_free_percent": warning_free_percent,
            "critical_free_percent": critical_free_percent,
            "minimum_free_bytes": minimum_free_bytes,
        }

    def _resource_health(self) -> dict[str, Any]:
        disks = self._disk_health()
        memory = self._memory_health()
        states = {str(disks.get("state")), str(memory.get("state"))}
        state = "critical" if "critical" in states else ("warning" if "warning" in states else "pass")
        return {
            "schema_version": "lightspeed-resource-health-v2",
            "state": state,
            "work_intake": "hold_heavy" if state == "critical" else (
                "bounded_only" if state == "warning" else "normal"
            ),
            "bounded_work_allowed": state != "critical",
            "heavy_work_allowed": state == "pass",
            "warning_disk_percent": disks["warning_disk_percent"],
            "critical_disk_percent": disks["critical_disk_percent"],
            "minimum_free_bytes": disks["minimum_free_bytes"],
            "volumes": disks["volumes"],
            "memory": memory,
        }

    def agent_floor_health(
        self,
        *,
        services: dict[str, bool],
        event_bus_enabled: bool,
    ) -> dict[str, Any]:
        neo_queue = self.shell_root / "Z Axis" / "Z+2_Neo" / "data" / "actions" / "ls_go_command_queue.jsonl"
        for queue_path in (neo_queue, self.review_queue_path, self.review_decisions_path):
            queue_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                queue_path.touch(exist_ok=False)
            except FileExistsError:
                # Existing ledgers are immutable history. A health read must not
                # advance their timestamps and trigger false sync activity.
                pass
        shared_services = all(bool(services.get(name)) for name in ("database", "event_bus", "storage"))
        floors: list[dict[str, Any]] = []
        for floor, directory in FLOOR_ROOTS.items():
            root = self.shell_root / "Z Axis" / directory
            markers = [root / "_FLOOR_MANIFEST.json", root / "__init__.py", root / "Z Direct"]
            missing = [str(path) for path in markers if not path.exists()]
            if not shared_services:
                missing.append("shared_services")
            floors.append({
                "floor": floor,
                "root": str(root),
                "state": "operational" if not missing else "degraded",
                "execution_model": "asynchronous_shared_queue",
                "markers_present": len(markers) - len([item for item in markers if not item.exists()]),
                "markers_required": len(markers),
                "missing": missing,
            })
        transport = {
            "event_bus_enabled": event_bus_enabled,
            "neo_queue_path": str(neo_queue),
            "neo_queue_writable": neo_queue.is_file() and os.access(neo_queue, os.W_OK),
            "go_review_queue_path": str(self.review_queue_path),
            "go_review_queue_available": self.review_queue_path.is_file(),
            "go_decision_path": str(self.review_decisions_path),
            "go_decision_available": self.review_decisions_path.is_file(),
            "coordination_mode": "independent_observers_shared_state",
        }
        operational_count = sum(item["state"] == "operational" for item in floors)
        aligned = (
            operational_count == len(FLOOR_ROOTS)
            and event_bus_enabled
            and transport["neo_queue_writable"]
            and transport["go_review_queue_available"]
            and transport["go_decision_available"]
        )
        return {
            "schema_version": "lightspeed-agent-floor-health-v1",
            "generated_utc": utc_now_iso(),
            "state": "operational" if aligned else "degraded",
            "operational_count": operational_count,
            "floor_count": len(FLOOR_ROOTS),
            "floors": floors,
            "transport": transport,
        }

    def _ignored_dirs(self) -> set[str]:
        return {str(item) for item in (self._scan_policy().get("ignored_directories") or [])}

    def _ignored_files(self) -> set[str]:
        return {str(item) for item in (self._scan_policy().get("ignored_files") or [])}

    def project_roots(self) -> list[ProjectRoot]:
        rows: list[ProjectRoot] = []
        for item in self.config.get("project_roots") or []:
            if not isinstance(item, dict):
                continue
            value = item.get("path")
            if not isinstance(value, str) or not value.strip():
                continue
            rows.append(
                ProjectRoot(
                    root_id=str(item.get("root_id") or _slug(value)),
                    path=self._resolve_shell_path(value),
                    authority=str(item.get("authority") or "reference"),
                    writable=bool(item.get("writable", False)),
                )
            )

        external = self.config.get("external_project_roots") or {}
        if isinstance(external, dict):
            variable = str(external.get("environment_variable") or "LIGHTSPEED_PROJECT_ROOTS")
            separator = str(external.get("separator") or ";")
            for index, value in enumerate(os.environ.get(variable, "").split(separator), start=1):
                value = value.strip()
                if value:
                    external_path = Path(value)
                    canonical_projects = self.shell_root.parent / "Projects"
                    folded = str(external_path).replace("/", "\\").casefold()
                    if (
                        not external_path.exists()
                        and folded.endswith(r"\lightspeed_consolidated\projects")
                        and canonical_projects.exists()
                    ):
                        external_path = canonical_projects
                    rows.append(
                        ProjectRoot(
                            root_id=f"external-{index}",
                            path=external_path,
                            authority=str(external.get("authority") or "external_reference"),
                            writable=bool(external.get("writable", False)),
                        )
                    )

        unique: list[ProjectRoot] = []
        seen: set[str] = set()
        for row in rows:
            key = os.path.normcase(os.path.abspath(str(row.path)))
            if key not in seen:
                seen.add(key)
                unique.append(row)
        return unique

    def _scan_project(self, root: ProjectRoot, path: Path, budget: list[int]) -> dict[str, Any]:
        ignored_dirs = self._ignored_dirs()
        ignored_files = self._ignored_files()
        per_project_limit = max(1, int(self._scan_policy().get("max_files_per_project") or 50_000))
        file_count = 0
        significant_count = 0
        total_bytes = 0
        latest_mtime = 0.0
        truncated = False
        fingerprint = hashlib.sha256()
        placeholder_names = {
            ".gitkeep", "notes.md", "checklist.md",
            "requirements.txt", "config.json", "config.yaml",
        }

        for current, directories, filenames in os.walk(path):
            directories[:] = [name for name in directories if name not in ignored_dirs]
            current_path = Path(current)
            for filename in sorted(filenames):
                if budget[0] <= 0 or file_count >= per_project_limit:
                    truncated = True
                    directories[:] = []
                    break
                if filename in ignored_files:
                    continue
                target = current_path / filename
                try:
                    stat = target.stat()
                except OSError:
                    continue
                budget[0] -= 1
                file_count += 1
                total_bytes += int(stat.st_size)
                latest_mtime = max(latest_mtime, float(stat.st_mtime))
                relative = target.relative_to(path).as_posix()
                fingerprint.update(relative.encode("utf-8", errors="replace"))
                fingerprint.update(str(int(stat.st_size)).encode("ascii"))
                fingerprint.update(str(int(stat.st_mtime_ns)).encode("ascii"))
                if filename.lower() not in placeholder_names or int(stat.st_size) > 256:
                    significant_count += 1
            if truncated:
                break

        metadata = _read_json(path / "project.json")
        # Identity follows the declared logical root and project name, not the
        # physical C:/D: path used to reach a junction-backed project.
        logical_identity = f"{root.root_id}|{path.name.casefold()}"
        project_id = (
            f"{_slug(path.name)}-"
            f"{hashlib.sha1(logical_identity.encode('utf-8')).hexdigest()[:8]}"
        )
        if file_count == 0:
            condition = "empty"
        elif significant_count == 0:
            condition = "scaffold_only"
        else:
            condition = "active"
        return {
            "project_id": project_id,
            "name": path.name,
            "path": str(path),
            "root_id": root.root_id,
            "authority": root.authority,
            "writable": root.writable,
            "condition": condition,
            "scan_truncated": truncated,
            "file_count": file_count,
            "significant_file_count": significant_count,
            "size_bytes": total_bytes,
            "latest_modified_utc": (
                datetime.fromtimestamp(latest_mtime, UTC).isoformat(timespec="seconds")
                if latest_mtime else None
            ),
            "fingerprint": fingerprint.hexdigest(),
            "metadata": {
                "type": metadata.get("type"),
                "status": metadata.get("status"),
                "description": metadata.get("description"),
                "version": metadata.get("version"),
            },
        }

    def scan_projects(self) -> dict[str, Any]:
        total_limit = max(1000, int(self._resource_guard().get("max_project_scan_files") or 200_000))
        budget = [total_limit]
        projects: list[dict[str, Any]] = []
        roots: list[dict[str, Any]] = []
        global_truncated = False
        for root in self.project_roots():
            root_exists = root.path.is_dir()
            roots.append({
                "root_id": root.root_id,
                "path": str(root.path),
                "authority": root.authority,
                "writable": root.writable,
                "exists": root_exists,
            })
            if not root_exists:
                continue
            try:
                children = [item for item in root.path.iterdir() if item.is_dir() and not item.name.startswith(".")]
            except OSError:
                continue
            for child in sorted(children, key=lambda item: item.name.lower()):
                if budget[0] <= 0:
                    global_truncated = True
                    break
                projects.append(self._scan_project(root, child, budget))
            if budget[0] <= 0:
                global_truncated = True
                break

        name_groups: dict[str, list[dict[str, Any]]] = {}
        for project in projects:
            name_groups.setdefault(str(project["name"]).lower(), []).append(project)
        duplicate_names = [
            {
                "name": group[0]["name"],
                "project_ids": [item["project_id"] for item in group],
                "paths": [item["path"] for item in group],
                "authorities": [item["authority"] for item in group],
            }
            for group in name_groups.values() if len(group) > 1
        ]

        return {
            "schema_version": SCHEMA_VERSION,
            "generated_utc": utc_now_iso(),
            "shell_root": str(self.shell_root),
            "roots": roots,
            "projects": projects,
            "summary": {
                "root_count": len(roots),
                "available_root_count": sum(1 for item in roots if item["exists"]),
                "project_count": len(projects),
                "active_count": sum(1 for item in projects if item["condition"] == "active"),
                "empty_count": sum(1 for item in projects if item["condition"] == "empty"),
                "scaffold_only_count": sum(1 for item in projects if item["condition"] == "scaffold_only"),
                "duplicate_name_group_count": len(duplicate_names),
                "truncated_project_count": sum(1 for item in projects if item["scan_truncated"]),
                "scan_truncated": global_truncated,
                "scanned_file_count": total_limit - budget[0],
                "scan_file_limit": total_limit,
                "total_size_bytes": sum(int(item["size_bytes"]) for item in projects),
            },
            "duplicate_names": duplicate_names,
        }

    def _archive_candidates(self, registry: dict[str, Any]) -> list[dict[str, Any]]:
        cleanup_config = self.config.get("cleanup_policy") or {}
        never_patterns = [str(item) for item in cleanup_config.get("never_delete_patterns") or []]
        max_hash_bytes = int(self._scan_policy().get("max_hash_bytes") or 1_073_741_824)
        max_archives = max(10, int(self._resource_guard().get("max_archive_inventory") or 2000))
        max_hashes = max(1, int(self._resource_guard().get("max_archive_hashes") or 100))
        ignored_dirs = self._ignored_dirs()
        archive_suffixes = {".zip", ".7z", ".tar", ".gz", ".bz2", ".rar"}
        archives: list[dict[str, Any]] = []
        hash_budget = max_hashes
        truncated = False

        for project in registry.get("projects") or []:
            project_path = Path(str(project.get("path") or ""))
            if not project_path.is_dir():
                continue
            for current, directories, filenames in os.walk(project_path):
                directories[:] = [name for name in directories if name not in ignored_dirs]
                for filename in sorted(filenames):
                    if len(archives) >= max_archives:
                        truncated = True
                        break
                    target = Path(current) / filename
                    if target.suffix.lower() not in archive_suffixes:
                        continue
                    try:
                        stat = target.stat()
                    except OSError:
                        continue
                    checksum = None
                    hash_state = "not_hashed_budget_or_size"
                    if hash_budget > 0 and int(stat.st_size) <= max_hash_bytes:
                        digest = hashlib.sha256()
                        try:
                            with target.open("rb") as stream:
                                for block in iter(lambda: stream.read(1024 * 1024), b""):
                                    digest.update(block)
                            checksum = digest.hexdigest()
                            hash_state = "hashed"
                            hash_budget -= 1
                        except OSError:
                            hash_state = "unreadable"
                    archives.append({
                        "candidate_class": "archive_inventory",
                        "path": str(target),
                        "project_id": project.get("project_id"),
                        "size_bytes": int(stat.st_size),
                        "sha256": checksum,
                        "hash_state": hash_state,
                        "protected_by_pattern": any(fnmatch.fnmatch(target.name, pattern) for pattern in never_patterns),
                        "action": "retain_pending_classification",
                    })
                if truncated:
                    break
            if truncated:
                break

        by_checksum: dict[str, list[dict[str, Any]]] = {}
        for archive in archives:
            checksum = archive.get("sha256")
            if checksum:
                by_checksum.setdefault(str(checksum), []).append(archive)
        duplicates = [
            {
                "candidate_class": "duplicate_archive_checksum",
                "sha256": checksum,
                "paths": [row["path"] for row in rows],
                "sizes": [row["size_bytes"] for row in rows],
                "action": "review_canonical_retention_before_quarantine",
            }
            for checksum, rows in by_checksum.items() if len(rows) > 1
        ]
        if truncated:
            archives.append({
                "candidate_class": "archive_inventory_limit",
                "limit": max_archives,
                "action": "continue_in_next_bounded_pass",
            })
        return [*archives, *duplicates]

    def scan_cleanup_candidates(self, registry: dict[str, Any]) -> dict[str, Any]:
        candidates: list[dict[str, Any]] = []
        generated_roots = [
            self.runtime_exports,
            self.merovingian_root / "data" / "logs",
            self.merovingian_root / "data" / "cache",
            self.merovingian_root / "data" / "temp",
        ]
        for root in generated_roots:
            if not root.is_dir():
                continue
            for target in root.rglob("*"):
                if target in {self.registry_path, self.health_path, self.cleanup_path, self.registry_state_path}:
                    continue
                try:
                    if target.is_file() and target.stat().st_size == 0:
                        candidates.append({
                            "candidate_class": "empty_generated_file",
                            "path": str(target),
                            "size_bytes": 0,
                            "action": "quarantine_only_after_reference_scan_and_approval",
                        })
                    elif target.is_dir() and not any(target.iterdir()):
                        candidates.append({
                            "candidate_class": "empty_generated_directory",
                            "path": str(target),
                            "action": "quarantine_only_after_reference_scan_and_approval",
                        })
                except OSError:
                    continue

        for project in registry.get("projects") or []:
            if project.get("condition") in {"empty", "scaffold_only"}:
                candidates.append({
                    "candidate_class": f"project_{project.get('condition')}",
                    "project_id": project.get("project_id"),
                    "path": project.get("path"),
                    "file_count": project.get("file_count"),
                    "size_bytes": project.get("size_bytes"),
                    "action": "review_merge_or_retire; no automatic deletion",
                })
        candidates.extend(self._archive_candidates(registry))
        return {
            "schema_version": "lightspeed-cleanup-evidence-v1",
            "generated_utc": utc_now_iso(),
            "automatic_deletion": False,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "required_proof": (self.config.get("cleanup_policy") or {}).get("required_proof") or [],
        }

    def resolve_drive_receipt_root(self) -> tuple[Path, str]:
        """Return an exact owner-approved Drive target or the local outbox."""
        config = self.config.get("drive_writeback") or {}
        launch_control = _read_json(self.shell_root / "config" / "launch_control.json")
        gates = launch_control.get("manual_gates")
        drive_gate = next(
            (
                item
                for item in (gates if isinstance(gates, list) else [])
                if isinstance(item, dict) and item.get("gate_id") == "drive_writeback"
            ),
            {},
        )
        gate_state = str(drive_gate.get("state") or "").casefold()
        approved_by = str(drive_gate.get("approved_by") or "").strip().casefold()
        decision_id = str(drive_gate.get("decision_id") or "").strip()
        approved_target_text = str(drive_gate.get("approved_target") or "").strip()
        if (
            gate_state == "owner_approved_exact_target"
            and approved_by in {"nathaniel", "nathaniel bouwer"}
            and decision_id
            and approved_target_text
        ):
            approved_target = Path(approved_target_text).expanduser()
            if (approved_target.is_absolute() or _windows_absolute(approved_target_text)) and approved_target.is_dir():
                return approved_target, "owner_approved_exact_drive_target"

        fallback = self._resolve_shell_path(str(
            config.get("local_fallback_path")
            or "Z Axis/Z-4_Merovingian/data/runtime_exports/drive_outbox"
        ))
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback, "local_outbox_pending_drive_sync"

    def _reconcile_decision_receipt(self, receipt: dict[str, Any]) -> dict[str, str]:
        drive_root, drive_mode = self.resolve_drive_receipt_root()
        receipt_path = drive_root / f"{receipt['review_id']}_{receipt['decision']}.json"
        receipt_payload = {**receipt, "drive_writeback_mode": drive_mode}
        receipt_state = _ensure_fixed_json_receipt(receipt_path, receipt_payload)
        return {
            "drive_writeback_mode": drive_mode,
            "decision_receipt_path": str(receipt_path),
            "decision_receipt_state": receipt_state,
        }

    def _queue_review_packet(
        self,
        *,
        title: str,
        summary: str,
        project_ids: list[str],
        artifact_paths: list[str],
        event_type: str,
    ) -> dict[str, Any]:
        created = utc_now_iso()
        seed = (
            f"{created}|{time.time_ns()}|{event_type}|"
            f"{'|'.join(project_ids)}|{'|'.join(artifact_paths)}"
        )
        review_id = f"LSGO-REVIEW-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16].upper()}"
        packet = {
            "schema_version": REVIEW_SCHEMA,
            "review_id": review_id,
            "created_utc": created,
            "source": "LightSpeed Desktop / Merovingian",
            "target": "LS GO",
            "oversight_floor": "Achilles",
            "routing_floor": "Neo",
            "owner": "Nathaniel Bouwer",
            "event_type": event_type,
            "title": title,
            "summary": summary,
            "project_ids": project_ids,
            "artifact_paths": artifact_paths,
            "state": "pending_review",
            "allowed_decisions": ["approve", "hold", "reject"],
            "proof_required": True,
            "public_safe": False,
        }
        _append_jsonl(self.review_queue_path, packet)
        drive_root, drive_mode = self.resolve_drive_receipt_root()
        drive_path = drive_root / f"{review_id}.json"
        _write_json(drive_path, {**packet, "drive_writeback_mode": drive_mode})
        return {**packet, "drive_receipt_path": str(drive_path), "drive_writeback_mode": drive_mode}

    def _supersede_registry_reviews(
        self,
        keep_review_id: str | None = None,
        *,
        retain_latest: bool = True,
    ) -> int:
        """Collapse path-migration review churn while retaining audit history."""
        queue_rows = _read_jsonl(self.review_queue_path, limit=5000)
        decisions = {
            str(item.get("review_id")): item
            for item in _read_jsonl(self.review_decisions_path, limit=5000)
            if item.get("review_id")
        }
        pending = [
            item
            for item in queue_rows
            if item.get("event_type") == "project_registry_change"
            and item.get("review_id")
            and str(item.get("review_id")) not in decisions
        ]
        if not pending or (retain_latest and len(pending) <= 1):
            return 0
        retained = keep_review_id or (
            str(pending[-1].get("review_id")) if retain_latest else None
        )
        superseded = 0
        for item in pending:
            review_id = str(item.get("review_id"))
            if review_id == retained:
                continue
            _append_jsonl(
                self.review_decisions_path,
                {
                    "schema_version": "lightspeed-go-review-decision-v1",
                    "review_id": review_id,
                    "decision": "superseded",
                    "note": (
                        f"Superseded by {retained} while canonical project paths stabilised; "
                        "the original event remains in the immutable queue history."
                    ),
                    "decided_utc": utc_now_iso(),
                    "decided_by": "Merovingian canonical queue maintenance",
                    "applies_external_write": False,
                },
            )
            superseded += 1
        return superseded

    def _project_changes(self, previous: dict[str, Any], current: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        previous_map = {
            str(item.get("project_id")): item for item in previous.get("projects") or []
            if isinstance(item, dict) and item.get("project_id")
        }
        current_map = {
            str(item.get("project_id")): item for item in current.get("projects") or []
            if isinstance(item, dict) and item.get("project_id")
        }
        return {
            "added": [item for key, item in current_map.items() if key not in previous_map],
            "removed": [item for key, item in previous_map.items() if key not in current_map],
            "changed": [
                item for key, item in current_map.items()
                if key in previous_map and item.get("fingerprint") != previous_map[key].get("fingerprint")
            ],
        }

    def essential_health(self, registry: dict[str, Any]) -> dict[str, Any]:
        service_states = {"database": False, "event_bus": False, "storage": False}
        details: dict[str, Any] = {}
        errors: list[str] = []
        event_bus_enabled = False
        try:
            services_module = _embedded_core_services(self.merovingian_root)
            services = services_module.initialize_services()
            if not isinstance(services, dict):
                raise TypeError("initialize_services did not return a service mapping")
            db = services.get("database")
            event_bus = services.get("event_bus")
            storage = services.get("storage")
            service_states = {
                "database": db is not None,
                "event_bus": event_bus is not None,
                "storage": storage is not None,
            }
            if db is not None:
                try:
                    details["database_path"] = str(getattr(db, "db_path", ""))
                    details["database_table_count"] = len(db.get_all_tables())
                except Exception as exc:
                    errors.append(f"database_probe:{type(exc).__name__}")
            if event_bus is not None:
                try:
                    details["event_bus"] = event_bus.get_stats()
                    event_bus_enabled = bool(details["event_bus"].get("enabled"))
                except Exception as exc:
                    errors.append(f"event_bus_probe:{type(exc).__name__}")
            if storage is not None:
                try:
                    details["storage_root"] = str(storage.storage_root)
                    details["storage_stats"] = storage.get_storage_stats()
                except Exception as exc:
                    errors.append(f"storage_probe:{type(exc).__name__}")
        except Exception as exc:
            errors.append(f"essential_services:{type(exc).__name__}:{exc}")

        resources = self._resource_health()
        details["resource_guard"] = resources
        details["root_resolution"] = {
            "requested_root": str(self.requested_shell_root),
            "canonical_shell_root": str(self.shell_root),
            "mode": self.root_resolution_mode,
            "redirected": self.requested_shell_root != self.shell_root,
            "receipt_authority": "desktop_shell_only",
        }
        details["disks"] = resources["volumes"]
        if resources["volumes"]:
            details["disk"] = resources["volumes"][0]

        floor_health = self.agent_floor_health(
            services=service_states,
            event_bus_enabled=event_bus_enabled,
        )
        details["agent_floors"] = floor_health

        drive_root, drive_mode = self.resolve_drive_receipt_root()
        details["drive_writeback"] = {"path": str(drive_root), "mode": drive_mode}
        return {
            "schema_version": "lightspeed-merovingian-health-v1",
            "generated_utc": utc_now_iso(),
            "status": "pass" if (
                all(service_states.values())
                and resources["state"] != "critical"
                and floor_health["state"] == "operational"
            ) else "degraded",
            "services": service_states,
            "details": details,
            "project_summary": registry.get("summary") or {},
            "errors": errors,
            "web_frontend_in_scope": False,
        }

    def refresh(self, *, force: bool = False, queue_changes: bool = True) -> dict[str, Any]:
        self.prepare_identity_indexes()
        refresh_seconds = int(self._scan_policy().get("registry_refresh_seconds") or 60)
        if not force and self._cached_registry and time.monotonic() - self._last_refresh_monotonic < refresh_seconds:
            registry = dict(self._cached_registry)
            health = self.essential_health(registry)
            _write_json(self.health_path, health)
            _write_json(self.floor_health_path, (health.get("details") or {}).get("agent_floors") or {})
            registry["health"] = health
            self._cached_registry = registry
            return registry

        previous = _read_json(self.registry_state_path)
        registry = self.scan_projects()
        cleanup = self.scan_cleanup_candidates(registry)
        health = self.essential_health(registry)
        _write_json(self.registry_path, registry)
        _write_json(self.cleanup_path, cleanup)
        _write_json(self.health_path, health)
        _write_json(self.floor_health_path, (health.get("details") or {}).get("agent_floors") or {})

        changes = self._project_changes(previous, registry) if previous else {"added": [], "removed": [], "changed": []}
        review_packet = None
        if queue_changes and previous and any(changes.values()):
            affected = [*changes["added"], *changes["removed"], *changes["changed"]]
            review_packet = self._queue_review_packet(
                title="Review LightSpeed project registry change",
                summary=(
                    f"Project registry changed: {len(changes['added'])} added, "
                    f"{len(changes['changed'])} modified, {len(changes['removed'])} removed."
                ),
                project_ids=[str(item.get("project_id")) for item in affected if item.get("project_id")],
                artifact_paths=[
                    str(self.registry_path),
                    str(self.cleanup_path),
                    str(self.health_path),
                    str(self.floor_health_path),
                ],
                event_type="project_registry_change",
            )

        _write_json(self.registry_state_path, {
            "schema_version": SCHEMA_VERSION,
            "generated_utc": registry["generated_utc"],
            "projects": registry.get("projects") or [],
            "last_review_id": review_packet.get("review_id") if review_packet else previous.get("last_review_id"),
        })
        superseded_review_count = self._supersede_registry_reviews(
            review_packet.get("review_id") if review_packet else None
        )
        registry.update({
            "health": health,
            "cleanup_summary": {
                "candidate_count": cleanup.get("candidate_count", 0),
                "automatic_deletion": False,
            },
            "changes": {key: [item.get("project_id") for item in value] for key, value in changes.items()},
            "review_packet": review_packet,
            "superseded_review_count": superseded_review_count,
        })
        self._cached_registry = registry
        self._last_refresh_monotonic = time.monotonic()
        return registry

    def prepare_identity_indexes(self) -> dict[str, dict[str, Any]]:
        """Advance fixed in-memory ledger indexes by one bounded chunk each."""
        result: dict[str, dict[str, Any]] = {}
        for name, index in (
            ("review_queue", self._review_queue_index),
            ("review_decisions", self._review_decisions_index),
        ):
            try:
                result[name] = index.advance()
            except (OSError, ValueError) as exc:
                result[name] = {
                    "complete": False,
                    "error": f"{type(exc).__name__}:{exc}",
                }
        return result

    def latest_snapshot(self) -> dict[str, Any]:
        """Read the last supervisor materialization without scanning projects."""
        self.prepare_identity_indexes()
        registry = _read_json(self.registry_path)
        health = _read_json(self.health_path)
        cleanup = _read_json(self.cleanup_path)
        registry.update(
            {
                "health": health,
                "cleanup_summary": {
                    "candidate_count": cleanup.get("candidate_count", 0),
                    "automatic_deletion": False,
                },
            }
        )
        return registry

    def queue_project_work_receipt(
        self,
        *,
        project_id: str,
        summary: str,
        artifact_paths: Iterable[str] = (),
    ) -> dict[str, Any]:
        return self._queue_review_packet(
            title=f"Review project work: {project_id}",
            summary=summary,
            project_ids=[project_id],
            artifact_paths=[str(item) for item in artifact_paths],
            event_type="project_work_receipt",
        )

    def list_reviews(self, limit: int = 100) -> list[dict[str, Any]]:
        decisions = {
            str(item.get("review_id")): item for item in _read_jsonl(self.review_decisions_path, limit=2000)
            if item.get("review_id")
        }
        rows = list(reversed(_read_jsonl(self.review_queue_path, limit=limit)))
        result: list[dict[str, Any]] = []
        for row in rows:
            output = row.copy()
            decision = decisions.get(str(row.get("review_id")))
            if decision:
                output["state"] = str(decision.get("decision") or "reviewed")
                output["decision"] = decision
            if output.get("state") == "superseded":
                continue
            result.append(output)
        return result

    def decide_review(self, review_id: str, decision: str, note: str = "") -> dict[str, Any]:
        allowed = set((self.config.get("go_review") or {}).get("allowed_decisions") or [])
        if decision not in allowed:
            raise ValueError(f"Unsupported review decision: {decision}")
        normalized_note = " ".join(note.split())[:1000]
        canonical_payload_sha256 = _review_decision_sha256(
            review_id,
            decision,
            normalized_note,
        )
        with _REVIEW_DECISION_LOCK:
            review_rows = self._review_queue_index.find(review_id)
            if not review_rows:
                raise KeyError(review_id)

            existing_decisions = self._review_decisions_index.find(review_id)
            if existing_decisions:
                existing_hashes = {
                    str(
                        item.get("canonical_payload_sha256")
                        or _review_decision_sha256(
                            review_id,
                            str(item.get("decision") or ""),
                            " ".join(str(item.get("note") or "").split())[:1000],
                        )
                    )
                    for item in existing_decisions
                }
                if existing_hashes != {canonical_payload_sha256}:
                    raise ReviewDecisionConflict(
                        f"review_id {review_id!r} already identifies a different owner decision"
                    )
                existing = dict(existing_decisions[-1])
                existing.setdefault("canonical_payload_sha256", canonical_payload_sha256)
                receipt_status = self._reconcile_decision_receipt(existing)
                existing["idempotent_replay"] = True
                existing.update(receipt_status)
                return existing

            receipt = {
                **_review_decision_contract(review_id, decision, normalized_note),
                "canonical_payload_sha256": canonical_payload_sha256,
                "decided_utc": utc_now_iso(),
            }
            _append_jsonl(self.review_decisions_path, receipt)
            receipt_status = self._reconcile_decision_receipt(receipt)
            return {**receipt, **receipt_status}
