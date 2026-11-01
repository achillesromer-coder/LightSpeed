"""Fail-closed consumer-lock health tests; no host process or queue mutations."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import pytest

HERE = Path(__file__).resolve().parent
SCRIPT_DIR = HERE if (HERE / "achilles_lsgo_consumer_preflight.py").is_file() else HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from achilles_lsgo_consumer_preflight import (  # noqa: E402
    ConsumerHealthHold,
    CONSUMER_SCHEMA,
    inspect_heartbeat,
    inspect_lock_path,
    self_test,
)

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def lock(**kwargs):
    base = {
        "schema_version": CONSUMER_SCHEMA,
        "pid": 1234,
        "heartbeat_utc": "2026-10-30T04:28:10+00:00",
    }
    base.update(kwargs)
    return base


def process(name="python.exe", created="2026-10-29T00:00:00+00:00", pid=1234):
    return {"pid": pid, "name": name, "created_utc": created}


def test_built_in_self_test_is_repeatable():
    assert self_test()["tests"] == 8


def test_reused_pid_is_hold_before_other_checks():
    out = inspect_heartbeat(lock(), process(
        "node.exe", "2026-10-30T05:00:00+00:00"), now=NOW)
    assert out["state"] == "PID_REUSED_AFTER_HEARTBEAT_HOLD"
    assert out["lock_modified"] is False
    assert out["service_restarted"] is False


def test_stale_original_python_is_also_hold():
    out = inspect_heartbeat(lock(), process(), now=NOW)
    assert out["state"] == "STALE_CONSUMER_HEARTBEAT_HOLD"
    assert out["consumer_execution_authorized"] is False


def test_wrong_executable_and_mismatched_pid_are_holds():
    current = lock(heartbeat_utc="2026-11-01T11:59:10+00:00")
    assert inspect_heartbeat(current, process("node.exe"), now=NOW)["state"] == "NON_CONSUMER_PROCESS_HOLD"
    assert inspect_heartbeat(current, process(pid=5678), now=NOW)["state"] == "PROCESS_IDENTITY_UNVERIFIED_HOLD"


def test_even_fresh_process_not_authorized():
    current = lock(heartbeat_utc="2026-11-01T11:59:10+00:00")
    out = inspect_heartbeat(current, process(), now=NOW)
    assert out["state"] == "FRESH_CONSUMER_PROCESS_CANDIDATE_NOT_AUTHORISED"
    assert out["consumer_execution_authorized"] is False
    assert out["lease_verified"] is False


@pytest.mark.parametrize("incorrect", [
    {"schema_version": "forged"},
    {"pid": True},
    {"pid": -1},
    {"heartbeat_utc": "2026-10-30T04:28:10"},
    {"heartbeat_utc": "nonsense"},
])
def test_invalid_lock_properties_hold(incorrect):
    with pytest.raises(ConsumerHealthHold):
        inspect_heartbeat(lock(**incorrect), process(), now=NOW)


def test_future_heartbeat_is_hold():
    with pytest.raises(ConsumerHealthHold, match="FUTURE_HEARTBEAT_HOLD"):
        inspect_heartbeat(lock(heartbeat_utc="2026-11-02T12:00:00+00:00"),
                          process(), now=NOW)


def test_absent_or_oversized_lock_is_hold(tmp_path):
    absent = tmp_path / "consumer.json"
    with pytest.raises(ConsumerHealthHold, match="CONSUMER_LOCK_FILE_HOLD"):
        inspect_lock_path(absent)
    absent.write_text(" " * 20000, encoding="utf-8")
    with pytest.raises(ConsumerHealthHold, match="CONSUMER_LOCK_FILE_HOLD"):
        inspect_lock_path(absent)


def test_invalid_json_hold(tmp_path):
    candidate = tmp_path / "consumer.json"
    candidate.write_text("{malformed", encoding="utf-8")
    with pytest.raises(ConsumerHealthHold, match="CONSUMER_LOCK_JSON_HOLD"):
        inspect_lock_path(candidate)


@pytest.mark.parametrize("root", [[], None, "untrusted", 17, True])
def test_nonobject_json_root_is_deterministic_hold(tmp_path, root):
    candidate = tmp_path / "consumer.json"
    candidate.write_text(json.dumps(root), encoding="utf-8")
    with pytest.raises(ConsumerHealthHold, match="CONSUMER_LOCK_SCHEMA_HOLD"):
        inspect_lock_path(candidate)
