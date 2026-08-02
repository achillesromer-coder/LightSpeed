from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from typing import Any


_FLOOR_ROUTE_TARGETS = {
    value.casefold(): value
    for value in (
        "Achilles",
        "Neo",
        "Architect",
        "TheConstruct",
        "Morpheus",
        "Oracle",
        "Smith",
        "Merovingian",
        "Trinity",
        "Z+3",
        "Z+2",
        "Z+1",
        "Z0",
        "Z-1",
        "Z-2",
        "Z-3",
        "Z-4",
    )
}


def _materialized_route_targets(target: str) -> list[str]:
    """Split only an explicit slash-delimited list of known floor identities."""
    value = str(target).strip()
    parts = [part.strip() for part in value.split("/") if part.strip()]
    if len(parts) <= 1 or not all(part.casefold() in _FLOOR_ROUTE_TARGETS for part in parts):
        return [value]
    resolved: list[str] = []
    for part in parts:
        canonical = _FLOOR_ROUTE_TARGETS[part.casefold()]
        if canonical not in resolved:
            resolved.append(canonical)
    return resolved


class OperationalConflict(ValueError):
    """Raised when an idempotency key is reused for different event content."""


CANONICAL_DATABASE_ENV = "LIGHTSPEED_CANONICAL_DB"
CANONICAL_OPERATOR_ROOT = Path(r"D:\LightSpeed")
CANONICAL_OPERATOR_DATABASE = (
    CANONICAL_OPERATOR_ROOT / "Data" / "db" / "lightspeed_unified.db"
)
_LEGACY_DATABASE_RELATIVE = (
    Path("Z Axis")
    / "Z-4_Merovingian"
    / "data"
    / "db"
    / "lightspeed_unified.db"
)


def _require_same_database_file(candidate: Path, canonical: Path, *, label: str) -> None:
    if not candidate.is_file():
        raise FileNotFoundError(f"{label} database does not exist: {candidate}")
    try:
        same_identity = os.path.samefile(candidate, canonical)
    except OSError as exc:
        raise RuntimeError(
            f"Could not prove {label} database identity: {candidate} -> {canonical}"
        ) from exc
    if not same_identity:
        raise ValueError(
            f"{label} database must identify the same file as {canonical}; "
            f"refusing database alias {candidate}"
        )


def default_operational_db_path(root: Path | None = None) -> Path:
    r"""Resolve the existing singleton operator database without creating it.

    ``root`` is retained for callers that also own a legacy Merovingian alias.
    A present alias must identify the canonical database by file identity. A
    missing alias is never recreated; callers use ``D:\LightSpeed\Data``
    directly. Arbitrary databases are available only through
    :meth:`OperationalStore.for_fixture`.
    """

    canonical_root = Path(CANONICAL_OPERATOR_ROOT)
    canonical = Path(CANONICAL_OPERATOR_DATABASE)
    if not canonical_root.is_dir():
        raise FileNotFoundError(
            f"The canonical LightSpeed operator namespace is unavailable: {canonical_root}"
        )
    if not canonical.is_file():
        raise FileNotFoundError(
            "The LightSpeed operator namespace exists but its sole canonical "
            f"database is missing: {canonical}"
        )

    configured = os.environ.get(CANONICAL_DATABASE_ENV, "").strip()
    if configured:
        configured_path = Path(configured).expanduser()
        if not configured_path.is_absolute():
            raise ValueError(
                f"{CANONICAL_DATABASE_ENV} must be an absolute path: {configured_path}"
            )
        _require_same_database_file(
            configured_path,
            canonical,
            label="Configured canonical LightSpeed",
        )

    if root is not None:
        legacy_alias = Path(root) / _LEGACY_DATABASE_RELATIVE
        if os.path.lexists(legacy_alias):
            _require_same_database_file(
                legacy_alias,
                canonical,
                label="Legacy operational",
            )

    return canonical


class OperationalStore:
    """SQLite authority for queues, handoffs, telemetry, and governance events."""

    _COUNTABLE_TABLES = frozenset({"operational_events"})

    def __init__(self, path: Path | None = None, *, _fixture: bool = False):
        if _fixture:
            if path is None:
                raise ValueError("fixture database path is required")
            self.path = Path(path)
            self.path.parent.mkdir(parents=True, exist_ok=True)
        else:
            canonical = default_operational_db_path()
            if path is not None:
                _require_same_database_file(
                    Path(path),
                    canonical,
                    label="OperationalStore",
                )
            self.path = canonical
        self._initialize()

    @classmethod
    def for_fixture(cls, path: Path) -> "OperationalStore":
        """Create an isolated database explicitly for a test or fixture."""
        return cls(path, _fixture=True)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS operational_events (
                    event_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    source TEXT,
                    target TEXT,
                    project_id TEXT,
                    priority TEXT,
                    risk TEXT,
                    status TEXT,
                    payload_json TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    duplicate_count INTEGER NOT NULL DEFAULT 0,
                    created_utc TEXT NOT NULL,
                    updated_utc TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_operational_events_status
                    ON operational_events(status, priority, updated_utc);
                CREATE INDEX IF NOT EXISTS idx_operational_events_kind
                    ON operational_events(kind, updated_utc);
                CREATE TABLE IF NOT EXISTS operational_routes (
                    event_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    created_utc TEXT NOT NULL,
                    PRIMARY KEY (event_id, source, target),
                    FOREIGN KEY (event_id)
                        REFERENCES operational_events(event_id)
                        ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_operational_routes_direction
                    ON operational_routes(source, target, created_utc);
                """
            )

    @staticmethod
    def _required_text(event: dict[str, Any], field: str) -> str:
        value = event.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required")
        return value.strip()

    @staticmethod
    def _optional_text(event: dict[str, Any], field: str) -> str | None:
        value = event.get(field)
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def record_event(self, event: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(event, dict):
            raise TypeError("event must be a dictionary")

        event_id = self._required_text(event, "event_id")
        kind = self._required_text(event, "kind")
        persisted_event = dict(event)
        persisted_event.pop("recorded_at", None)
        payload_json = json.dumps(
            persisted_event,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        payload_sha256 = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        stamp = self._optional_text(event, "recorded_at") or datetime.now(UTC).isoformat()
        source = self._optional_text(event, "source")
        target = self._optional_text(event, "target")
        route_targets = _materialized_route_targets(target) if source and target else []

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT payload_sha256, duplicate_count
                FROM operational_events
                WHERE event_id = ?
                """,
                (event_id,),
            ).fetchone()
            if existing is not None:
                if existing["payload_sha256"] != payload_sha256:
                    raise OperationalConflict(
                        f"event_id {event_id!r} already identifies different content"
                    )
                duplicate_count = int(existing["duplicate_count"]) + 1
                connection.execute(
                    """
                    UPDATE operational_events
                    SET duplicate_count = ?, updated_utc = ?
                    WHERE event_id = ?
                    """,
                    (duplicate_count, stamp, event_id),
                )
                route_inserted_count = 0
                for route_target in route_targets:
                    route_inserted_count += connection.execute(
                        """
                        INSERT OR IGNORE INTO operational_routes (
                            event_id, source, target, created_utc
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (event_id, source, route_target, stamp),
                    ).rowcount
                return {
                    "event_id": event_id,
                    "inserted": False,
                    "duplicate_count": duplicate_count,
                    "payload_sha256": payload_sha256,
                    "route_inserted": route_inserted_count > 0,
                    "route_count": len(route_targets),
                    "route_targets": route_targets,
                }

            connection.execute(
                """
                INSERT INTO operational_events (
                    event_id,
                    kind,
                    source,
                    target,
                    project_id,
                    priority,
                    risk,
                    status,
                    payload_json,
                    payload_sha256,
                    duplicate_count,
                    created_utc,
                    updated_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    event_id,
                    kind,
                    source,
                    target,
                    self._optional_text(event, "project_id"),
                    self._optional_text(event, "priority"),
                    self._optional_text(event, "risk"),
                    self._optional_text(event, "status"),
                    payload_json,
                    payload_sha256,
                    stamp,
                    stamp,
                ),
            )
            route_inserted_count = 0
            for route_target in route_targets:
                route_inserted_count += connection.execute(
                    """
                    INSERT OR IGNORE INTO operational_routes (
                        event_id, source, target, created_utc
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (event_id, source, route_target, stamp),
                ).rowcount
            return {
                "event_id": event_id,
                "inserted": True,
                "duplicate_count": 0,
                "payload_sha256": payload_sha256,
                "route_inserted": route_inserted_count > 0,
                "route_count": len(route_targets),
                "route_targets": route_targets,
            }

    def count(
        self,
        table: str = "operational_events",
        *,
        kind: str | None = None,
    ) -> int:
        if table not in self._COUNTABLE_TABLES:
            raise ValueError(f"unsupported table: {table}")
        with self._connect() as connection:
            if kind is None:
                row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            else:
                row = connection.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE kind = ?",
                    (str(kind),),
                ).fetchone()
        return int(row[0])

    def recent(
        self,
        *,
        limit: int = 100,
        kind: str | None = None,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        bounded_limit = max(0, min(int(limit), 10_000))
        if bounded_limit == 0:
            return []
        conditions: list[str] = []
        parameters: list[Any] = []
        if kind is not None:
            conditions.append("kind = ?")
            parameters.append(str(kind))
        if source is not None:
            conditions.append("source = ?")
            parameters.append(str(source))
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        parameters.append(bounded_limit)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM operational_events
                {where_clause}
                ORDER BY updated_utc DESC, event_id DESC
                LIMIT ?
                """,
                parameters,
            ).fetchall()
        return [dict(row) for row in rows]

    def record_route(
        self,
        *,
        event_id: str,
        source: str,
        target: str,
        recorded_at: str | None = None,
    ) -> bool:
        event_id = str(event_id).strip()
        source = str(source).strip()
        target = str(target).strip()
        if not event_id or not source or not target:
            raise ValueError("event_id, source, and target are required")
        stamp = recorded_at or datetime.now(UTC).isoformat()
        route_targets = _materialized_route_targets(target)
        with self._connect() as connection:
            inserted = 0
            for route_target in route_targets:
                inserted += connection.execute(
                    """
                    INSERT OR IGNORE INTO operational_routes (
                        event_id, source, target, created_utc
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (event_id, source, route_target, stamp),
                ).rowcount
        return inserted > 0

    def routed(
        self,
        *,
        source: str,
        target: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        bounded_limit = max(0, min(int(limit), 10_000))
        if bounded_limit == 0:
            return []
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT events.*, routes.created_utc AS routed_utc
                FROM operational_routes AS routes
                JOIN operational_events AS events
                    ON events.event_id = routes.event_id
                WHERE routes.source = ? AND routes.target = ?
                ORDER BY routes.created_utc DESC, events.event_id DESC
                LIMIT ?
                """,
                (str(source), str(target), bounded_limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def peers(self, channel: str) -> list[str]:
        channel = str(channel)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT target AS peer
                FROM operational_routes
                WHERE source = ?
                UNION
                SELECT source AS peer
                FROM operational_routes
                WHERE target = ?
                ORDER BY peer
                """,
                (channel, channel),
            ).fetchall()
        return [str(row["peer"]) for row in rows]
