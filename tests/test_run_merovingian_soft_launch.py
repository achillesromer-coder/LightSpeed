from __future__ import annotations

import importlib.util
import json
from pathlib import Path


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
