from __future__ import annotations

import importlib.util
import json
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


def test_unhealthy_bridge_recovery_stops_only_verified_listener_tree(
    monkeypatch,
    stack_module,
) -> None:
    rows = [
        {
            "pid": 10,
            "parent_pid": 1,
            "created_ticks": 100,
            "command_line": "python run_ls_go_bridge.py",
        },
        {
            "pid": 11,
            "parent_pid": 10,
            "created_ticks": 101,
            "command_line": "bridge child",
        },
    ]
    calls: list[list[str]] = []
    monkeypatch.setattr(stack_module, "listening_pid", lambda _port: 11)
    monkeypatch.setattr(stack_module, "windows_command_processes", lambda _fragment: rows)

    def fake_run(command, **_kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(stack_module.subprocess, "run", fake_run)

    result = stack_module.stop_unhealthy_bridge_listener()

    assert result["verified_bridge_owner"] is True
    assert result["stopped_root_pid"] == 10
    assert calls == [["taskkill", "/PID", "10", "/T", "/F"]]


def test_unhealthy_bridge_recovery_preserves_unknown_listener(
    monkeypatch,
    stack_module,
) -> None:
    monkeypatch.setattr(stack_module, "listening_pid", lambda _port: 99)
    monkeypatch.setattr(stack_module, "windows_command_processes", lambda _fragment: [])

    def fail_run(*_args, **_kwargs):
        raise AssertionError("unknown listener must not be terminated")

    monkeypatch.setattr(stack_module.subprocess, "run", fail_run)

    result = stack_module.stop_unhealthy_bridge_listener()

    assert result == {
        "listener_pid": 99,
        "verified_bridge_owner": False,
        "stopped_root_pid": None,
    }


def test_stack_desporte_launch_requires_explicit_gate(
    monkeypatch,
    stack_module,
) -> None:
    monkeypatch.setenv("DESPORTE_EXECUTABLE", r"C:\configured\desporte.exe")

    def fail_start(*_args, **_kwargs):
        raise AssertionError("De Sporte must remain held without the explicit flag")

    monkeypatch.setattr(stack_module, "start_background", fail_start)

    assert stack_module.optional_desporte_start()["state"] == "held_by_gate"


def test_stack_desktop_health_requires_expected_server_identity(
    monkeypatch,
    stack_module,
) -> None:
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit: int) -> bytes:
            return json.dumps(
                {
                    "status": "operational",
                    "version": "3.1.0",
                    "server": "FastAPI + Three.js",
                }
            ).encode("utf-8")

    monkeypatch.setattr(
        stack_module,
        "port_open",
        lambda _host, port, timeout=0.35: port == 8081,
    )
    monkeypatch.setattr(stack_module, "urlopen", lambda *_args, **_kwargs: Response())

    health = stack_module.desktop_health_status()

    assert health["healthy"] is True
    assert health["port"] == 8081


def test_verified_process_stop_preserves_command_mismatch(
    monkeypatch,
    stack_module,
) -> None:
    monkeypatch.setattr(
        stack_module,
        "windows_command_processes",
        lambda _fragment: [
            {
                "name": "powershell.exe",
                "pid": 20,
                "parent_pid": 1,
                "created_ticks": 10,
                "command_line": r"python C:\unexpected\__main__.py",
            }
        ],
    )

    def fail_run(*_args, **_kwargs):
        raise AssertionError("identity mismatch must not be terminated")

    monkeypatch.setattr(stack_module.subprocess, "run", fail_run)

    result = stack_module.stop_verified_process_tree(
        20,
        process_fragment="__main__.py",
        required_command_fragment=r"D:\LightSpeed\App\__main__.py",
    )

    assert result["verified"] is False
    assert result["stopped_root_pid"] is None


def test_verified_process_stop_targets_only_verified_tree(
    monkeypatch,
    stack_module,
) -> None:
    rows = [
        {
            "name": "python.exe",
            "pid": 20,
            "parent_pid": 1,
            "created_ticks": 10,
            "command_line": r"python D:\LightSpeed\App\__main__.py",
        },
        {
            "name": "python.exe",
            "pid": 21,
            "parent_pid": 20,
            "created_ticks": 11,
            "command_line": r"python D:\LightSpeed\App\__main__.py --child",
        },
    ]
    calls: list[list[str]] = []
    monkeypatch.setattr(stack_module, "windows_command_processes", lambda _fragment: rows)
    monkeypatch.setattr(stack_module, "pid_alive", lambda _pid: False)

    def fake_run(command, **_kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(stack_module.subprocess, "run", fake_run)

    result = stack_module.stop_verified_process_tree(
        21,
        process_fragment="__main__.py",
        required_command_fragment=r"D:\LightSpeed\App\__main__.py",
    )

    assert result["verified"] is True
    assert result["stopped_root_pid"] == 20
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
            "bridge_tcp": True,
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
            "bridge_tcp": False,
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


def test_bridge_health_requires_http_ok_and_canonical_root(
    tmp_path: Path,
    monkeypatch,
    watchdog_module,
) -> None:
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit: int) -> bytes:
            return json.dumps(
                {"ok": True, "root": str(tmp_path / "App")}
            ).encode("utf-8")

    monkeypatch.setattr(watchdog_module, "urlopen", lambda *_args, **_kwargs: Response())

    assert watchdog_module.bridge_status_healthy(tmp_path)

    monkeypatch.setattr(
        watchdog_module,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError()),
    )
    assert not watchdog_module.bridge_status_healthy(tmp_path)


def test_desktop_health_requires_lightspeed_http_identity(
    monkeypatch,
    watchdog_module,
) -> None:
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit: int) -> bytes:
            return json.dumps(
                {
                    "status": "operational",
                    "version": "3.1.0",
                    "server": "FastAPI + Three.js",
                }
            ).encode("utf-8")

    monkeypatch.setattr(
        watchdog_module,
        "port_open",
        lambda port: port in {8080, 8081},
    )
    monkeypatch.setattr(watchdog_module, "urlopen", lambda request, **_kwargs: (
        (_ for _ in ()).throw(TimeoutError())
        if ":8080/" in request.full_url
        else Response()
    ))

    health = watchdog_module.desktop_health_status()

    assert health["healthy"] is True
    assert health["port"] == 8081


def test_desktop_health_rejects_wrong_or_unresponsive_service(
    monkeypatch,
    watchdog_module,
) -> None:
    class WrongResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit: int) -> bytes:
            return b'{"status":"operational","server":"Tabby"}'

    monkeypatch.setattr(watchdog_module, "port_open", lambda port: port == 8080)
    monkeypatch.setattr(watchdog_module, "urlopen", lambda *_args, **_kwargs: WrongResponse())

    assert watchdog_module.desktop_health_status()["healthy"] is False


def test_observe_rejects_tcp_only_bridge_health(
    tmp_path: Path,
    monkeypatch,
    watchdog_module,
) -> None:
    monkeypatch.setattr(watchdog_module, "port_open", lambda _port: True)
    monkeypatch.setattr(
        watchdog_module,
        "bridge_status_healthy",
        lambda _root: False,
    )
    monkeypatch.setattr(
        watchdog_module,
        "heartbeat_fresh",
        lambda _path, _age: True,
    )
    monkeypatch.setattr(
        watchdog_module,
        "process_command_running",
        lambda _fragment: True,
    )
    monkeypatch.setattr(
        watchdog_module,
        "desktop_health_status",
        lambda: {"healthy": False, "port": None},
    )

    observed = watchdog_module.observe(tmp_path, max_heartbeat_age=180)

    assert observed["bridge_tcp"] is True
    assert observed["bridge"] is False
    assert observed["desktop_process"] is True
    assert observed["desktop_http"] is False
    assert observed["desktop"] is False


def test_heartbeat_rejects_future_timestamp(
    tmp_path: Path,
    monkeypatch,
    watchdog_module,
) -> None:
    lock = tmp_path / "lock.json"
    lock.write_text(
        json.dumps({"heartbeat_utc": "2099-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )

    assert not watchdog_module.heartbeat_fresh(lock)
