"""Synthetic regression of the sequential receipt runner (no machine access)."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

SRC = Path(__file__).resolve().parents[1] / "scripts" / "run_cgx_printspace_batch.py"
spec = importlib.util.spec_from_file_location("cgx_batch", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def root(tmp):
    path = tmp / "checkout"
    (path / "cgx/manufacturing").mkdir(parents=True)
    (path / "cgx/manufacturing/compiler.py").write_text("# test only")
    return path


def execute(tmp, commands):
    return mod.run_sequence(commands, root=root(tmp), output=tmp / "receipts",
                            step_limit_s=10, total_limit_s=40, rest_s=0)


def test_fixed_plan_is_named_and_allowlisted():
    assert len(mod.fixed_plan("comprehensive")) == len(mod.SUITES)
    assert len(mod.fixed_plan("printspace")) == 5
    try:
        mod.fixed_plan("shell")
    except ValueError:
        pass
    else:
        raise AssertionError("arbitrary profile accepted")
    for name, cmd in mod.fixed_plan("comprehensive"):
        assert cmd[1:4] == ["-m", "pytest", "-q"]
        assert cmd[4].startswith("tests/test_") and cmd[4].endswith(".py")


def test_receipt_on_success(tmp_path):
    r = execute(tmp_path, [("ok-one", [sys.executable, "-c", "print('PASS1')"]),
                            ("ok-two", [sys.executable, "-c", "print('PASS2')"])])
    assert r["state"] == "PASS_TESTS_ONLY" and len(r["steps"]) == 2
    saved = json.loads((tmp_path / "receipts" / r["receipt_file"]).read_text())
    assert saved == r
    assert saved["physical_machine_authorised"] is False
    assert saved["mint_authorised"] is False
    assert saved["commercial_release_authorised"] is False
    assert saved["no_remote_desktop_calls"] is True
    for item in saved["steps"]:
        log = (tmp_path / "receipts" / item["log_file"]).read_bytes()
        assert item["log_sha256"] == mod.sha256(log)


def test_stop_on_first_failed_step(tmp_path):
    r = execute(tmp_path, [("fail", [sys.executable, "-c", "raise SystemExit(3)"]),
                           ("never", [sys.executable, "-c", "print('not run')"])])
    assert r["state"] == "HOLD_FAILURE" and r["failure_stage"] == "fail"
    assert len(r["steps"]) == 1 and r["steps"][0]["exit_code"] == 3


def test_reject_bad_cwd(tmp_path):
    try:
        mod.run_sequence([], root=tmp_path, output=tmp_path,
                         step_limit_s=4, total_limit_s=10, rest_s=0)
    except ValueError as e:
        assert "canonical" in str(e)
    else:
        raise AssertionError("bad checkout accepted")


def test_time_budget_rejection(tmp_path):
    try:
        mod.run_sequence([], root=root(tmp_path), output=tmp_path / "receipts",
                         step_limit_s=0, total_limit_s=10, rest_s=0)
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe time limit accepted")


def test_synthetic_timeout_stops_sequence(tmp_path):
    r = mod.run_sequence([("slow", [sys.executable, "-c", "import time;time.sleep(2)"]),
                          ("never", [sys.executable, "-c", "print(99)"])],
                         root=root(tmp_path), output=tmp_path / "receipts",
                         step_limit_s=1, total_limit_s=10, rest_s=0)
    assert r["state"] == "HOLD_FAILURE" and r["failure_stage"] == "slow"
    assert len(r["steps"]) == 1 and r["steps"][0]["status"] == "TIMEOUT"