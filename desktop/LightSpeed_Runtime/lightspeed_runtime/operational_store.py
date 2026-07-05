from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


class OperationalConflict(ValueError):
    """Raised when an idempotency key is reused for different event content."""


def default_operational_db_path(root: Path) -> Path:
    return (
        Path(root)
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "db"
        / "lightspeed_unified.db"
    )


class OperationalStore:
    """SQLite authority for queues, handoffs, telemetry, and governance events."""

    _COUNTABLE_TABLES = frozenset({"operational_events"})

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

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
                return {
                    "event_id": event_id,
                    "inserted": False,
                    "duplicate_count": duplicate_count,
                    "payload_sha256": payload_sha256,
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
                    self._optional_text(event, "source"),
                    self._optional_text(event, "target"),
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
            return {
                "event_id": event_id,
                "inserted": True,
                "duplicate_count": 0,
                "payload_sha256": payload_sha256,
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
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO operational_routes (
                    event_id, source, target, created_utc
                ) VALUES (?, ?, ?, ?)
                """,
                (event_id, source, target, stamp),
            )
        return cursor.rowcount > 0

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
