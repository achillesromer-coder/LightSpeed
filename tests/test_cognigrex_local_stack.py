from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = REPO_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def stack_module():
    return load_script("run_cognigrex_local_stack.py")


@pytest.fixture
def watchdog_module():
    return load_script("ensure_cognigrex_local_stack.py")


def test_web_bridge_is_optional_when_external_web_is_deferred(tmp_path: Path) -> None:
    bridge_path = (
        REPO_ROOT
        / "desktop"
        / "LightSpeed_Runtime"
        / "lightspeed_runtime"
        / "agent_home_bridge.py"
    )
    spec = importlib.util.spec_from_file_location("agent_home_bridge_test", bridge_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "agent_environment.json").write_text("{}\n", encoding="utf-8")

    bridge = module.AgentHomeBridge(tmp_path)

    assert bridge.web_drive_bridge() == {}


def test_select_root_prefers_canonical_namespace_over_stale_environment(
    tmp_path: Path,
    monkeypatch,
    stack_module,
) -> None:
    canonical = tmp_path / "canonical"
    stale = tmp_path / "stale"
    repository = tmp_path / "repository"
    marker = Path("lightspeed_runtime") / "__init__.py"
    for root in (canonical, stale, repository):
        (root / marker).parent.mkdir(parents=True)
        (root / marker).touch()
    monkeypatch.setattr(stack_module.os, "name", "nt")
    monkeypatch.setenv("LIGHTSPEED_RUNTIME_ROOT", str(stale))

    selected = stack_module.select_root(
        None,
        "LIGHTSPEED_RUNTIME_ROOT",
        canonical,
        tmp_path / "legacy",
        repository,
        marker,
    )

    assert selected == canonical.absolute()


def test_singleton_reconciliation_keeps_listener_tree(
    monkeypatch,
    stack_module,
) -> None:
    rows = [
        {"pid": 10, "parent_pid": 1, "created_ticks": 100, "command_line": "bridge root"},
        {"pid": 11, "parent_pid": 10, "created_ticks": 101, "command_line": "bridge child"},
        {"pid": 20, "parent_pid": 1, "created_ticks": 200, "command_line": "duplicate root"},
    ]
    calls: list[list[str]] = []

    monkeypatch.setattr(stack_module, "windows_command_processes", lambda _fragment: rows)

    def fake_run(command, **_kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(stack_module.subprocess, "run", fake_run)

    result = stack_module.reconcile_singleton("bridge", preferred_pid=11)

    assert result["kept_root_pid"] == 10
    assert result["duplicate_roots_stopped"] == [20]
    assert calls == [["taskkill", "/PID", "20", "/T", "/F"]]


def test_noncanonical_reconciliation_does_not_stop_canonical_tree(
    monkeypatch,
    stack_module,
) -> None:
    rows = [
        {
            "pid": 10,
            "parent_pid": 1,
            "created_ticks": 100,
            "command_line": r"python D:\LightSpeed\App\__main__.py",
        },
        {
            "pid": 20,
            "parent_pid": 1,
            "created_ticks": 200,
            "command_line": r"python C:\old\Desktop_Hooks\LightSpeed\__main__.py",
        },
    ]
    calls: list[list[str]] = []
    monkeypatch.setattr(stack_module, "windows_command_processes", lambda _fragment: rows)

    def fake_run(command, **_kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(stack_module.subprocess, "run", fake_run)

    result = stack_module.stop_noncanonical_process_roots(
        "__main__.py",
        r"D:\LightSpeed\App\__main__.py",
    )

    assert result["noncanonical_roots_stopped"] == [20]
    assert calls == [["taskkill", "/PID", "20", "/T", "/F"]]


def test_watchdog_observes_healthy_stack_without_repair(
    tmp_path: Path,
    monkeypatch,
    watchdog_module,
) -> None:
    monkeypatch.setattr(
        watchdog_module,
        "observe",
        lambda _root, max_heartbeat_age: {
            "bridge": True,
            "merovingian_heartbeat": True,
            "go_interface": True,
            "desktop": True,
        },
    )

    def fail_run(*_args, **_kwargs):
        raise AssertionError("healthy watchdog must not launch a repair")

    monkeypatch.setattr(watchdog_module.subprocess, "run", fail_run)

    result = watchdog_module.main(["--canonical-root", str(tmp_path)])
    receipt = tmp_path / "State" / "Health" / "cognigrex_watchdog_receipt.json"

    assert result == 0
    assert receipt.is_file()
    assert '"action": "observe"' in receipt.read_text(encoding="utf-8")


def test_watchdog_bounds_missing_repair_prerequisites(
    tmp_path: Path,
    monkeypatch,
    watchdog_module,
) -> None:
    monkeypatch.setattr(
        watchdog_module,
        "observe",
        lambda _root, max_heartbeat_age: {
            "bridge": False,
            "merovingian_heartbeat": False,
            "go_interface": False,
            "desktop": False,
        },
    )

    result = watchdog_module.main(["--canonical-root", str(tmp_path)])
    receipt = (
        tmp_path / "State" / "Health" / "cognigrex_watchdog_receipt.json"
    ).read_text(encoding="utf-8")

    assert result == 2
    assert '"launch_error": "canonical_python_or_launcher_missing"' in receipt
    assert '"automatic_deletion": false' in receipt
    assert '"public_export": false' in receipt
