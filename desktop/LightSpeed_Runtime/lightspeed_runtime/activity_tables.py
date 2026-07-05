from __future__ import annotations

import json
import sqlite3
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lightspeed_runtime.governance_ledgers import default_action_ledger_path, default_approval_ledger_path
from lightspeed_runtime.operational_store import (
    OperationalStore,
    default_operational_db_path,
)
from lightspeed_runtime.storage_paths import merovingian_root
from lightspeed_runtime.telemetry import default_telemetry_path
from lightspeed_runtime.weekly_log import weekly_log_path

MAX_TABLE_ROWS = 120
MAX_RECENT_PER_STREAM = 5000

CATEGORY_FLOOR_HINTS = {
    "achilles": "Neo",
    "ai": "Neo",
    "archive": "Smith",
    "assimilation": "Smith",
    "bellcurve": "Oracle",
    "cleanup": "Merovingian",
    "closure": "Merovingian",
    "columnar": "Oracle",
    "curated": "Oracle",
    "dataset": "Oracle",
    "definition": "Oracle",
    "empirical": "Oracle",
    "entity": "Oracle",
    "execution": "Architect",
    "finalization": "Merovingian",
    "heliocentric": "TheConstruct",
    "ingestion": "Oracle",
    "knowns": "Oracle",
    "publish": "Architect",
    "query": "Oracle",
    "romer": "Architect",
    "scientific": "Oracle",
    "smith": "Smith",
    "telemetry": "Merovingian",
    "ui": "Trinity",
    "unit": "Oracle",
    "validation": "Oracle",
    "workflow": "Smith",
    "zoning": "TheConstruct",
}

SOURCE_FLOOR_HINTS = {
    "architect": "Architect",
    "construct": "TheConstruct",
    "merovingian": "Merovingian",
    "morpheus": "Morpheus",
    "neo": "Neo",
    "oracle": "Oracle",
    "smith": "Smith",
    "trinity": "Trinity",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_activity_tables_path(root: Path) -> Path:
    """Return the Merovingian-owned compact activity table path."""
    return merovingian_root(root) / "audit" / "activity_tables.json"


def default_activity_db_path(root: Path) -> Path:
    """Return the unified Merovingian SQLite authority."""
    return default_operational_db_path(root)


def read_activity_tables(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_activity_tables_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_jsonl_table(path: Path, *, max_recent: int = MAX_RECENT_PER_STREAM) -> tuple[int, list[dict]]:
    recent: deque[dict] = deque(maxlen=max(1, max_recent))
    line_count = 0
    if not path.exists():
        return 0, []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            line_count += 1
            try:
                recent.append(json.loads(raw))
            except Exception:
                recent.append({"raw": raw})
    return line_count, list(recent)


def _read_operational_table(
    path: Path,
    *,
    kind: str,
    max_recent: int = MAX_RECENT_PER_STREAM,
) -> tuple[int, list[dict]]:
    if not path.exists():
        return 0, []
    store = OperationalStore(path)
    rows = store.recent(limit=max_recent, kind=kind)
    records: list[dict] = []
    for row in reversed(rows):
        try:
            stored = json.loads(row["payload_json"])
            payload = stored.get("payload")
            if isinstance(payload, dict):
                record = dict(payload)
                record.setdefault("recorded_at", row.get("created_utc"))
                records.append(record)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
    return store.count(kind=kind), records


def _first_string(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _floor_from_text(*values: object) -> str:
    for value in values:
        text = str(value or "").lower()
        for hint, floor in SOURCE_FLOOR_HINTS.items():
            if hint in text:
                return floor
        for hint, floor in CATEGORY_FLOOR_HINTS.items():
            if hint in text:
                return floor
    return "Merovingian"


def _artifact_from_payload(payload: dict) -> str:
    for key in (
        "path",
        "report_path",
        "queue_path",
        "router_path",
        "workflow_state_path",
        "trace_id",
        "source_path",
        "target_path",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _normalize_weekly(record: dict) -> dict:
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    category = _first_string(record.get("category"), "weekly_log")
    source = _first_string(record.get("source"), "lightspeed_runtime")
    return {
        "stream": "weekly_log",
        "timestamp": _first_string(record.get("timestamp"), record.get("recorded_at")),
        "floor": _floor_from_text(payload.get("owner_floor"), payload.get("floor"), source, category),
        "category": category,
        "event": _first_string(record.get("message"), category),
        "level": _first_string(record.get("level"), "info"),
        "source": source,
        "artifact_ref": _artifact_from_payload(payload),
        "trace_id": _first_string(payload.get("trace_id"), payload.get("otel_trace_id")),
    }


def _normalize_telemetry(record: dict) -> dict:
    attributes = record.get("attributes") if isinstance(record.get("attributes"), dict) else {}
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    category = _first_string(attributes.get("lightspeed.category"), record.get("name"), "telemetry")
    source = _first_string(attributes.get("lightspeed.source"), "lightspeed_runtime")
    return {
        "stream": "telemetry",
        "timestamp": _first_string(record.get("start_time_unix_nano"), ""),
        "floor": _floor_from_text(payload.get("owner_floor"), payload.get("floor"), source, category),
        "category": category,
        "event": _first_string(attributes.get("lightspeed.message"), (record.get("status") or {}).get("message"), category),
        "level": _first_string(attributes.get("lightspeed.level"), "info"),
        "source": source,
        "artifact_ref": _artifact_from_payload(payload),
        "trace_id": _first_string(record.get("trace_id"), payload.get("trace_id")),
    }


def _normalize_governance(record: dict, *, stream: str) -> dict:
    category = _first_string(record.get("risk"), record.get("action_type"), record.get("type"), stream)
    source = _first_string(record.get("source_floor"), record.get("agent_id"), record.get("source"), stream)
    return {
        "stream": stream,
        "timestamp": _first_string(record.get("recorded_at"), record.get("timestamp")),
        "floor": _floor_from_text(record.get("target_floor"), record.get("source_floor"), source, category),
        "category": category,
        "event": _first_string(record.get("title"), record.get("summary"), record.get("action_id"), category),
        "level": _first_string(record.get("level"), "info"),
        "source": source,
        "artifact_ref": _first_string(record.get("result_ref"), record.get("artifact_ref"), record.get("path")),
        "trace_id": _first_string(record.get("trace_id")),
    }


def _sort_key(row: dict) -> str:
    return str(row.get("timestamp") or "")


def _row_identity(row: dict) -> tuple:
    return (
        row.get("stream"),
        row.get("timestamp"),
        row.get("floor"),
        row.get("category"),
        row.get("event"),
        row.get("artifact_ref"),
        row.get("trace_id"),
    )


def _select_activity_rows(rows: list[dict[str, Any]], *, max_rows: int) -> list[dict[str, Any]]:
    limit = max(1, max_rows)
    sorted_rows = sorted(rows, key=_sort_key)
    latest_by_signal: dict[tuple, dict[str, Any]] = {}
    for row in sorted_rows:
        signal_key = (
            row.get("floor", "Merovingian"),
            row.get("category", "unknown"),
            row.get("stream", "unknown"),
        )
        latest_by_signal[signal_key] = row

    selected: list[dict[str, Any]] = sorted(latest_by_signal.values(), key=_sort_key)[-limit:]
    seen = {_row_identity(row) for row in selected}
    if len(selected) < limit:
        for row in reversed(sorted_rows):
            identity = _row_identity(row)
            if identity in seen:
                continue
            selected.append(row)
            seen.add(identity)
            if len(selected) >= limit:
                break
    return sorted(selected, key=_sort_key)


def build_activity_tables(root: Path, *, output_path: Path | None = None, max_rows: int = MAX_TABLE_ROWS) -> dict:
    """Build the compact Z-axis activity table from append-only audit streams."""
    root = Path(root)
    sources = {
        "weekly_log": weekly_log_path(root),
        "telemetry": default_telemetry_path(root),
        "action_ledger": default_action_ledger_path(root),
        "approval_ledger": default_approval_ledger_path(root),
    }
    counts: dict[str, int] = {}
    rows: list[dict[str, Any]] = []

    weekly_count, weekly_records = _read_jsonl_table(sources["weekly_log"])
    counts["weekly_log"] = weekly_count
    rows.extend(_normalize_weekly(record) for record in weekly_records)

    telemetry_count, telemetry_records = _read_operational_table(
        sources["telemetry"],
        kind="telemetry",
    )
    counts["telemetry"] = telemetry_count
    rows.extend(_normalize_telemetry(record) for record in telemetry_records)

    action_count, action_records = _read_operational_table(
        sources["action_ledger"],
        kind="governance_action",
    )
    counts["action_ledger"] = action_count
    rows.extend(_normalize_governance(record, stream="action_ledger") for record in action_records)

    approval_count, approval_records = _read_operational_table(
        sources["approval_ledger"],
        kind="governance_approval",
    )
    counts["approval_ledger"] = approval_count
    rows.extend(_normalize_governance(record, stream="approval_ledger") for record in approval_records)

    rows = _select_activity_rows(rows, max_rows=max_rows)
    floor_counts = Counter(row.get("floor", "Merovingian") for row in rows)
    category_counts = Counter(row.get("category", "unknown") for row in rows)
    stream_counts = Counter(row.get("stream", "unknown") for row in rows)

    return {
        "generated_at": utc_now_iso(),
        "owner_floor": "Merovingian",
        "control_floor": "Architect",
        "table_path": str(output_path or default_activity_tables_path(root)),
        "database_path": str(default_activity_db_path(root)),
        "purpose": "Compact operator-facing signal table derived from weekly logs and unified operational events.",
        "source_paths": {key: str(path) for key, path in sources.items()},
        "source_line_counts": counts,
        "summary": {
            "owner_floor": "Merovingian",
            "control_floor": "Architect",
            "compaction_policy": "latest_signal_per_floor_category_stream",
            "source_evidence": "weekly_jsonl_plus_sqlite_operational_events",
            "total_source_events": sum(counts.values()),
            "table_rows": len(rows),
            "floor_counts": dict(sorted(floor_counts.items())),
            "category_counts": dict(category_counts.most_common(24)),
            "stream_counts": dict(sorted(stream_counts.items())),
            "latest_event": rows[-1] if rows else {},
        },
        "activity_rows": rows,
        "policy": [
            "SQLite is authoritative for telemetry, governance, queues, handoffs, and Z Direct events.",
            "One bounded weekly JSONL remains a human-readable operational export.",
            "This table is the compact Z-axis operating surface for routine review and signal compaction.",
            "New runtime work should write artifact-rich events, not one-off success files.",
            "Floor-specific reports remain with the owning floor; Merovingian owns cross-floor activity tables.",
        ],
}


def write_activity_table_database(root: Path, payload: dict, db_path: Path | None = None) -> dict:
    """Persist the compact activity table into Merovingian SQLite storage."""
    destination = db_path or default_activity_db_path(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = payload.get("activity_rows") or []
    summary = payload.get("summary") or {}
    with sqlite3.connect(destination) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_events (
                row_index INTEGER PRIMARY KEY,
                stream TEXT NOT NULL,
                timestamp TEXT,
                floor TEXT,
                category TEXT,
                event TEXT,
                level TEXT,
                source TEXT,
                artifact_ref TEXT,
                trace_id TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_summary (
                metric TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.execute("DELETE FROM activity_events")
        connection.execute("DELETE FROM activity_summary")
        connection.executemany(
            """
            INSERT INTO activity_events (
                row_index, stream, timestamp, floor, category, event,
                level, source, artifact_ref, trace_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    index,
                    row.get("stream", ""),
                    str(row.get("timestamp", "")),
                    row.get("floor", ""),
                    row.get("category", ""),
                    row.get("event", ""),
                    row.get("level", ""),
                    row.get("source", ""),
                    row.get("artifact_ref", ""),
                    row.get("trace_id", ""),
                )
                for index, row in enumerate(rows, start=1)
            ],
        )
        connection.executemany(
            "INSERT INTO activity_summary (metric, value) VALUES (?, ?)",
            [
                ("generated_at", payload.get("generated_at", "")),
                ("owner_floor", str(payload.get("owner_floor", ""))),
                ("control_floor", str(payload.get("control_floor", ""))),
                ("compaction_policy", str(summary.get("compaction_policy", ""))),
                ("source_evidence", str(summary.get("source_evidence", ""))),
                ("total_source_events", str(summary.get("total_source_events", 0))),
                ("table_rows", str(summary.get("table_rows", 0))),
                ("floor_counts", json.dumps(summary.get("floor_counts", {}), sort_keys=True)),
                ("category_counts", json.dumps(summary.get("category_counts", {}), sort_keys=True)),
                ("stream_counts", json.dumps(summary.get("stream_counts", {}), sort_keys=True)),
            ],
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_activity_events_floor ON activity_events(floor)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_activity_events_category ON activity_events(category)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_activity_events_stream ON activity_events(stream)")
    return {
        "database_path": str(destination),
        "activity_rows": len(rows),
        "summary_rows": 10,
    }


def write_activity_tables(root: Path, output_path: Path | None = None, max_rows: int = MAX_TABLE_ROWS) -> dict:
    destination = output_path or default_activity_tables_path(root)
    payload = build_activity_tables(root, output_path=destination, max_rows=max_rows)
    db_result = write_activity_table_database(root, payload)
    payload["database_path"] = db_result["database_path"]
    payload["database_rows"] = db_result
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
