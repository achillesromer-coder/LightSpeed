from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import time


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_merovingian_soft_launch.py"
SPEC = importlib.util.spec_from_file_location("run_merovingian_soft_launch", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_supervisor_json_write_retries_transient_reader_lock(tmp_path, monkeypatch):
    target = tmp_path / "supervisor.json"
    original_replace = Path.replace
    attempts = {"count": 0}

    def transient_lock(path, destination):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise PermissionError("simulated reader lock")
        return original_replace(path, destination)

    monkeypatch.setattr(Path, "replace", transient_lock)
    monkeypatch.setattr(MODULE.time, "sleep", lambda _seconds: None)

    MODULE._write_json(target, {"status": "pass"})

    assert attempts["count"] == 3
    assert json.loads(target.read_text(encoding="utf-8")) == {"status": "pass"}
    assert not list(tmp_path.glob("supervisor.json.tmp.*"))


def test_supervisor_pulses_heartbeat_during_long_scan(tmp_path, monkeypatch):
    calls = []

    def record(lock_path, *, interval, state):
        calls.append((lock_path, interval, state))

    monkeypatch.setattr(MODULE, "_heartbeat", record)
    lock_path = tmp_path / "supervisor.lock.json"

    with MODULE._heartbeat_pulse(lock_path, interval=120, pulse_seconds=0.01):
        deadline = time.monotonic() + 1.0
        while len(calls) < 2 and time.monotonic() < deadline:
            time.sleep(0.01)

    assert len(calls) >= 2
    assert all(call == (lock_path, 120, "scanning") for call in calls)


def test_select_preserves_the_configured_operator_namespace(tmp_path, monkeypatch):
    candidate = tmp_path / "operator-alias"
    marker = Path("runtime") / "marker.py"
    (candidate / marker).parent.mkdir(parents=True)
    (candidate / marker).write_text("# marker\n", encoding="utf-8")
    expected = candidate.absolute()

    def reject_resolution(_path):
        raise AssertionError("_select must not resolve governed junction aliases")

    monkeypatch.setattr(Path, "resolve", reject_resolution)

    assert MODULE._select([candidate], marker, "test root") == expected
