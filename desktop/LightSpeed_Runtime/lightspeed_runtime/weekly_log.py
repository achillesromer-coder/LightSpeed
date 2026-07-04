from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lightspeed_runtime.storage_paths import logs_root

WEEKLY_CATEGORY_MARKERS = (
    "approval",
    "approved",
    "blocked",
    "cleanup",
    "deploy",
    "error",
    "fail",
    "launch",
    "maintenance",
    "publish",
    "quarantine",
    "recovery",
    "rejected",
)
WEEKLY_LEVELS = frozenset({"warning", "error", "critical"})


def should_persist_weekly(*, category: str, level: str) -> bool:
    normalized_category = str(category).strip().lower()
    normalized_level = str(level).strip().lower()
    return normalized_level in WEEKLY_LEVELS or any(
        marker in normalized_category
        for marker in WEEKLY_CATEGORY_MARKERS
    )


def weekly_bucket(timestamp: datetime | None = None) -> dict[str, object]:
    stamp = timestamp or datetime.now(timezone.utc)
    iso = stamp.isocalendar()
    return {
        "year": iso.year,
        "week": iso.week,
        "label": f"{iso.year}-W{iso.week:02d}",
    }


def weekly_log_path(root: Path, *, now: datetime | None = None) -> Path:
    bucket = weekly_bucket(now)
    return logs_root(root) / f"lightspeed_{bucket['year']}_W{int(bucket['week']):02d}.jsonl"


def _legacy_runtime_log_path(root: Path, *, now: datetime | None = None) -> Path:
    bucket = weekly_bucket(now)
    return logs_root(root) / str(bucket["year"]) / f"runtime_{bucket['label']}.jsonl"


def _merge_legacy_runtime_log(root: Path, *, now: datetime | None = None) -> None:
    target = weekly_log_path(root, now=now)
    legacy = _legacy_runtime_log_path(root, now=now)
    if not legacy.exists():
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as destination, legacy.open("r", encoding="utf-8", errors="replace") as source:
        for raw in source:
            raw = raw.rstrip("\n")
            if raw:
                destination.write(raw + "\n")
    legacy.unlink(missing_ok=True)
    try:
        parent = legacy.parent
        if parent != target.parent and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
    except Exception:
        pass


def append_weekly_log(
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
    _merge_legacy_runtime_log(root, now=stamp)
    entry = {
        "timestamp": stamp.isoformat(),
        "category": category,
        "level": level,
        "source": source,
        "message": message,
        "payload": payload or {},
    }
    path = weekly_log_path(root, now=stamp)
    persisted = should_persist_weekly(category=category, level=level)
    if persisted:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {
        "path": str(path),
        "entry": entry,
        "week": weekly_bucket(stamp),
        "persisted": persisted,
    }


def weekly_log_summary(root: Path, *, now: datetime | None = None, tail: int = 12) -> dict:
    stamp = now or datetime.now(timezone.utc)
    _merge_legacy_runtime_log(root, now=stamp)
    path = weekly_log_path(root, now=stamp)
    recent: deque[dict[str, Any]] = deque(maxlen=max(1, tail))
    line_count = 0

    if path.exists():
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue
                line_count += 1
                try:
                    recent.append(json.loads(raw))
                except Exception:
                    recent.append({"raw": raw, "category": "unparsed", "message": raw})

    latest = recent[-1] if recent else {}
    return {
        "path": str(path),
        "exists": path.exists(),
        "week": weekly_bucket(stamp),
        "entry_count": line_count,
        "latest_category": latest.get("category"),
        "latest_message": latest.get("message"),
        "recent_entries": list(recent),
    }
