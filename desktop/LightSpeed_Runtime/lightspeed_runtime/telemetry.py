from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lightspeed_runtime.operational_store import (
    OperationalStore,
    default_operational_db_path,
)


def default_telemetry_path(root: Path) -> Path:
    return default_operational_db_path(root)


def _hex_digest(value: str, length: int) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:length]


def _time_unix_nano(stamp: datetime) -> int:
    return int(stamp.timestamp() * 1_000_000_000)


def append_otel_event(
    root: Path,
    *,
    category: str,
    message: str,
    level: str = "info",
    source: str = "lightspeed_runtime",
    payload: dict[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> dict:
    stamp = timestamp or datetime.now(timezone.utc)
    payload = payload or {}
    seed = f"{stamp.isoformat()}|{source}|{category}|{message}|{json.dumps(payload, sort_keys=True, default=str)}"
    trace_id = str(payload.get("trace_id") or _hex_digest(seed, 32))
    span_id = _hex_digest(seed + "|span", 16)
    record = {
        "resource": {
            "service.name": "lightspeed-desktop",
            "service.namespace": "LightSpeed",
            "service.instance.id": "local-desktop",
        },
        "scope": {
            "name": "lightspeed_runtime",
            "version": "1",
        },
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": str(payload.get("parent_span_id") or ""),
        "name": f"lightspeed.{category}",
        "kind": "INTERNAL",
        "start_time_unix_nano": _time_unix_nano(stamp),
        "end_time_unix_nano": _time_unix_nano(stamp),
        "status": {
            "code": "ERROR" if str(level).lower() in {"error", "critical"} else "OK",
            "message": message,
        },
        "attributes": {
            "lightspeed.category": category,
            "lightspeed.source": source,
            "lightspeed.level": level,
            "lightspeed.message": message,
        },
        "payload": payload,
    }
    path = default_telemetry_path(root)
    OperationalStore(path).record_event(
        {
            "event_id": f"telemetry:{trace_id}:{span_id}",
            "kind": "telemetry",
            "source": source,
            "risk": str(level).lower(),
            "status": record["status"]["code"],
            "recorded_at": stamp.isoformat(),
            "payload": record,
        }
    )
    return {"telemetry_path": str(path), "record": record}


def telemetry_summary(root: Path, *, tail: int = 8) -> dict:
    path = default_telemetry_path(root)
    if not path.exists():
        return {
            "telemetry_path": str(path),
            "span_count": 0,
            "recent": [],
            "otel_profile": "sqlite_operational_events",
        }
    store = OperationalStore(path)
    rows = store.recent(limit=max(0, tail), kind="telemetry")
    recent: list[dict] = []
    for row in reversed(rows):
        try:
            stored = json.loads(row["payload_json"])
            record = stored.get("payload")
            recent.append(record if isinstance(record, dict) else stored)
        except (TypeError, ValueError, json.JSONDecodeError):
            recent.append({"raw": row.get("payload_json", ""), "name": "unparsed"})
    return {
        "telemetry_path": str(path),
        "span_count": store.count(kind="telemetry"),
        "recent": recent,
        "otel_profile": "sqlite_operational_events",
    }
