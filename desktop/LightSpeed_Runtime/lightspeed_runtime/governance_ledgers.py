from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lightspeed_runtime.contracts import classify_action_risk, utc_now_iso
from lightspeed_runtime.operational_store import (
    OperationalStore,
    default_operational_db_path,
)


def default_action_ledger_path(root: Path) -> Path:
    """Return the Merovingian-owned operational database path."""
    return default_operational_db_path(root)


def default_approval_ledger_path(root: Path) -> Path:
    """Return the shared operational database used for Architect approvals."""
    return default_operational_db_path(root)


def _event_id(record: dict, *, ledger_kind: str) -> str:
    explicit = record.get("event_id")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    action_id = record.get("action_id")
    if isinstance(action_id, str) and action_id.strip():
        return f"governance:{ledger_kind}:{action_id.strip()}"
    trace_id = record.get("trace_id")
    if isinstance(trace_id, str) and trace_id.strip():
        event = str(record.get("event") or record.get("action_type") or ledger_kind)
        return f"governance:{ledger_kind}:{trace_id.strip()}:{event}"
    canonical = json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"governance:{ledger_kind}:{digest}"


def _record_governance(root: Path, payload: dict, *, ledger_kind: str) -> dict:
    record = dict(payload)
    event_id = _event_id(record, ledger_kind=ledger_kind)
    supplied_timestamp = bool(record.get("recorded_at"))
    record.setdefault("recorded_at", utc_now_iso())
    record.setdefault("event_id", event_id)
    stored_record = dict(record)
    if not supplied_timestamp:
        stored_record.pop("recorded_at", None)
    store_event = {
        "event_id": event_id,
        "kind": f"governance_{ledger_kind}",
        "source": record.get("source_floor") or record.get("source"),
        "target": record.get("target_floor") or record.get("target"),
        "project_id": record.get("project_id"),
        "priority": record.get("priority"),
        "risk": record.get("risk") or record.get("risk_level"),
        "status": record.get("approval_state") or record.get("status"),
        "recorded_at": record["recorded_at"],
        "payload": stored_record,
    }
    OperationalStore(default_operational_db_path(root)).record_event(store_event)
    return record


def append_action_ledger(root: Path, payload: dict) -> dict:
    """Record a Merovingian action entry with normalized action class metadata."""
    record = dict(payload)
    record.setdefault("action_class", classify_action_risk(record.get("action_type", record.get("risk", ""))))
    record.setdefault("ledger_floor", "Merovingian")
    record.setdefault("ledger_kind", "action")
    return _record_governance(root, record, ledger_kind="action")


def append_approval_ledger(root: Path, payload: dict) -> dict:
    """Record an Architect approval entry with normalized action class metadata."""
    record = dict(payload)
    record.setdefault("action_class", classify_action_risk(record.get("action_type", record.get("risk", ""))))
    record.setdefault("ledger_floor", "Architect")
    record.setdefault("ledger_kind", "approval")
    return _record_governance(root, record, ledger_kind="approval")
