from __future__ import annotations

import json
import sqlite3

import pytest

from lightspeed_runtime.operational_store import (
    OperationalConflict,
    OperationalStore,
    default_operational_db_path,
)
from lightspeed_runtime.governance_ledgers import (
    append_action_ledger,
    append_approval_ledger,
    default_action_ledger_path,
    default_approval_ledger_path,
)
from lightspeed_runtime.telemetry import (
    append_otel_event,
    default_telemetry_path,
    telemetry_summary,
)
from core.services.dataspace import ZDirectService


def test_store_deduplicates_idempotent_events(tmp_path):
    store = OperationalStore(tmp_path / "runtime.db")
    event = {
        "event_id": "evt-1",
        "kind": "handoff",
        "source": "Trinity",
        "target": "Oracle",
        "payload": {"task": "T-1"},
    }

    first = store.record_event(event)
    duplicate = store.record_event(event)

    assert first["inserted"] is True
    assert first["duplicate_count"] == 0
    assert duplicate["inserted"] is False
    assert duplicate["duplicate_count"] == 1
    assert store.count("operational_events") == 1


def test_store_rejects_same_event_id_with_different_payload(tmp_path):
    store = OperationalStore(tmp_path / "runtime.db")
    store.record_event(
        {"event_id": "evt-1", "kind": "task", "payload": {"status": "queued"}}
    )

    with pytest.raises(OperationalConflict, match="evt-1"):
        store.record_event(
            {"event_id": "evt-1", "kind": "task", "payload": {"status": "done"}}
        )


def test_store_requires_event_identity_and_kind(tmp_path):
    store = OperationalStore(tmp_path / "runtime.db")

    with pytest.raises(ValueError, match="event_id"):
        store.record_event({"kind": "task", "payload": {}})
    with pytest.raises(ValueError, match="kind"):
        store.record_event({"event_id": "evt-1", "payload": {}})


def test_store_preserves_extensible_fields_in_payload_json(tmp_path):
    store = OperationalStore(tmp_path / "runtime.db")
    event = {
        "event_id": "evt-2",
        "kind": "queue",
        "priority": "critical",
        "status": "queued",
        "notes": "Review before launch",
        "extensions": {"icon": "warning", "sla_minutes": 15},
        "payload": {"artifact_id": "A-1"},
    }

    store.record_event(event)
    row = store.recent(limit=1)[0]

    persisted = json.loads(row["payload_json"])
    assert persisted["notes"] == "Review before launch"
    assert persisted["extensions"]["icon"] == "warning"
    assert persisted["payload"]["artifact_id"] == "A-1"


def test_store_uses_wal_and_indexes_status_priority(tmp_path):
    path = tmp_path / "runtime.db"
    OperationalStore(path)

    with sqlite3.connect(path) as connection:
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        indexes = {
            row[1]
            for row in connection.execute(
                "PRAGMA index_list('operational_events')"
            ).fetchall()
        }

    assert journal_mode.lower() == "wal"
    assert "idx_operational_events_status" in indexes


def test_default_operational_db_path_is_merovingian_owned(tmp_path):
    assert default_operational_db_path(tmp_path) == (
        tmp_path
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "db"
        / "lightspeed_unified.db"
    )


def test_governance_ledgers_write_sqlite_without_jsonl_mirrors(tmp_path):
    root = tmp_path / "LightSpeed"

    action = append_action_ledger(
        root,
        {
            "event_id": "action-1",
            "source_floor": "Neo",
            "target_floor": "Architect",
            "action_type": "publish_snapshot",
            "risk": "publish",
        },
    )
    approval = append_approval_ledger(
        root,
        {
            "event_id": "approval-1",
            "source_floor": "Architect",
            "target_floor": "Neo",
            "action_type": "build_heliocentric_zoning",
            "risk": "execute",
        },
    )

    store = OperationalStore(default_operational_db_path(root))
    kinds = {row["kind"] for row in store.recent(limit=10)}
    assert action["action_class"] == "publish"
    assert approval["action_class"] == "execute"
    assert kinds == {"governance_action", "governance_approval"}
    assert default_action_ledger_path(root) == default_operational_db_path(root)
    assert default_approval_ledger_path(root) == default_operational_db_path(root)
    assert not list(root.rglob("*.jsonl"))


def test_governance_retry_uses_action_id_as_idempotency_key(tmp_path, monkeypatch):
    root = tmp_path / "LightSpeed"
    timestamps = iter(
        (
            "2026-07-05T00:00:00+00:00",
            "2026-07-05T00:00:01+00:00",
        )
    )
    monkeypatch.setattr(
        "lightspeed_runtime.governance_ledgers.utc_now_iso",
        lambda: next(timestamps),
    )
    payload = {
        "action_id": "ACT-retry",
        "source_floor": "Neo",
        "target_floor": "Architect",
        "action_type": "publish_snapshot",
    }

    append_action_ledger(root, payload)
    append_action_ledger(root, payload)

    store = OperationalStore(default_operational_db_path(root))
    rows = store.recent(kind="governance_action", limit=10)
    assert len(rows) == 1
    assert rows[0]["duplicate_count"] == 1


def test_telemetry_writes_and_reads_operational_store(tmp_path):
    root = tmp_path / "LightSpeed"

    written = append_otel_event(
        root,
        category="test_event",
        message="Testing telemetry",
        source="Oracle",
        payload={"trace_id": "trace_test"},
    )
    summary = telemetry_summary(root, tail=5)

    assert written["telemetry_path"] == str(default_operational_db_path(root))
    assert default_telemetry_path(root) == default_operational_db_path(root)
    assert summary["span_count"] == 1
    assert summary["recent"][-1]["name"] == "lightspeed.test_event"
    assert not list(root.rglob("otel_spans.jsonl"))


def test_z_direct_deduplicates_payload_and_route_without_jsonl(tmp_path):
    root = tmp_path / "LightSpeed"
    floor_roots = {
        "Z+3": root / "Z Axis" / "Z+3_Trinity",
        "Z-3": root / "Z Axis" / "Z-3_Smith",
    }
    service = ZDirectService(root=root, floor_roots=floor_roots)
    envelope = {
        "schema_version": "z-direct-v1",
        "kind": "object",
        "channel": "Z+3",
        "z_context": "Trinity",
        "created_at": "2026-07-05T00:00:00+00:00",
        "source": "test",
        "payload": {"kind": "task", "id": "task-1", "title": "Review"},
    }

    object_path = service.append_object("Z+3", envelope)
    outbox_path = service.append_channel_outbox(
        from_channel="Z+3",
        to_channel="Z-3",
        payload=envelope,
    )
    inbox_path = service.append_channel_inbox(
        to_channel="Z-3",
        from_channel="Z+3",
        payload=envelope,
    )

    expected_path = default_operational_db_path(root)
    assert object_path == expected_path
    assert outbox_path == expected_path
    assert inbox_path == expected_path
    store = OperationalStore(expected_path)
    assert store.count(kind="z_direct_object") == 1
    assert len(store.routed(source="Z+3", target="Z-3", limit=10)) == 1
    assert service.tail_channel_outbox(
        from_channel="Z+3",
        to_channel="Z-3",
        limit=10,
    ) == [envelope]
    assert service.tail_channel_inbox(
        to_channel="Z-3",
        from_channel="Z+3",
        limit=10,
    ) == [envelope]
    assert not list(root.rglob("*.jsonl"))
