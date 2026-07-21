#!/usr/bin/env python3
"""Start the bounded local Cognigrex soft-launch stack.

The launcher starts or verifies Merovingian, the local LS GO bridge and
LightSpeed Desktop. It attempts the De Sporte population receipt first and can
optionally start a configured De Sporte executable. It never starts Web,
publishes, deletes, mutates workbooks or performs direct cross-app commands.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys
import time
from typing import Any
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_RUNTIME_ROOT = REPO_ROOT / "desktop" / "LightSpeed_Runtime"
REPO_SHELL_ROOT = REPO_ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed"


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def select_root(
    explicit: Path | None,
    env_name: str,
    canonical: Path,
    legacy: Path,
    repository: Path,
    marker: Path,
) -> Path:
    candidates = [explicit, Path(os.environ[env_name]) if os.environ.get(env_name) else None]
    if os.name == "nt":
        candidates.extend((canonical, legacy))
    candidates.append(repository)
    for candidate in candidates:
        if candidate and (candidate / marker).is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"No valid {env_name} root found")


def port_open(host: str, port: int, timeout: float = 0.35) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def pid_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_limited_information, False, int(pid)
        )
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def lock_pid(path: Path) -> int | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return int(payload.get("pid")) if isinstance(payload, dict) and payload.get("pid") else None
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def creation_flags() -> int:
    if os.name != "nt":
        return 0
    return (
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        | getattr(subprocess, "DETACHED_PROCESS", 0)
        | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )


def start_background(command: list[str], *, cwd: Path, log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_stream = log_path.open("a", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=log_stream,
        stderr=subprocess.STDOUT,
        creationflags=creation_flags(),
        start_new_session=os.name != "nt",
        close_fds=True,
    )
    log_stream.close()
    return int(process.pid)


def windows_command_running(fragment: str) -> bool:
    if os.name != "nt":
        return False
    # Do not embed ``fragment`` in the PowerShell command: doing so makes the
    # probe match its own command line and report every process as running.
    command = (
        "Get-CimInstance Win32_Process | ForEach-Object { "
        "if ($_.CommandLine) { Write-Output ($_.ProcessId.ToString() + \"`t\" + $_.CommandLine) } "
        "}"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if completed.returncode != 0:
        return False
    needle = fragment.casefold()
    return any(needle in line.casefold() for line in completed.stdout.splitlines())


def run_desporte_population(python: str, receipt_dir: Path) -> dict[str, Any]:
    script = REPO_ROOT / "scripts" / "populate_desporte_desktop.py"
    completed = subprocess.run(
        [python, str(script)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return {
        "status": "pass" if completed.returncode == 0 else "review_required",
        "exit_code": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
        "probe_receipt": str(receipt_dir / "desporte_soft_launch_receipt.json"),
        "population_receipt": str(receipt_dir / "desporte_desktop_population_receipt.json"),
    }


def optional_desporte_start() -> dict[str, Any]:
    executable_value = os.environ.get("DESPORTE_EXECUTABLE")
    if not executable_value:
        return {
            "state": "not_configured",
            "detail": "Set DESPORTE_EXECUTABLE to enable supervised process start; population receipts remain authoritative.",
        }
    executable = Path(executable_value)
    if not executable.is_file():
        return {"state": "missing", "path": str(executable)}
    if windows_command_running(executable.name):
        return {"state": "already_running", "path": str(executable)}
    # ``posix=False`` retains quote characters in Windows arguments, causing
    # the packaged app to receive a literal \"path\" value and exit.  The
    # configured argument contract is shell-style, so strip its grouping
    # quotes before passing the argument list to ``Popen``.
    args = shlex.split(os.environ.get("DESPORTE_LAUNCH_ARGS", ""), posix=True)
    pid = start_background([str(executable), *args], cwd=executable.parent, log_path=REPO_ROOT / "logs" / "desporte-launch.log")
    time.sleep(2)
    return {
        "state": "started" if pid_alive(pid) else "launch_failed",
        "path": str(executable),
        "pid": pid,
    }


def read_bridge_status() -> dict[str, Any]:
    try:
        with urlopen("http://127.0.0.1:8765/api/v1/status", timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload if isinstance(payload, dict) else {"ok": False}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def wait_for_bridge_status(timeout_seconds: float = 30.0) -> dict[str, Any]:
    deadline = time.monotonic() + max(1.0, timeout_seconds)
    latest: dict[str, Any] = {"ok": False, "error": "bridge readiness not checked"}
    while time.monotonic() < deadline:
        latest = read_bridge_status()
        if latest.get("ok"):
            return latest
        time.sleep(1)
    return latest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--shell-root", type=Path)
    parser.add_argument("--skip-desporte-population", action="store_true")
    parser.add_argument("--no-desktop-launch", action="store_true")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    runtime_root = select_root(
        args.runtime_root,
        "LIGHTSPEED_RUNTIME_ROOT",
        Path(r"D:\LightSpeed_Consolidated\LightSpeed_Runtime"),
        Path(r"C:\LightSpeed_Consolidated\LightSpeed_Runtime"),
        REPO_RUNTIME_ROOT,
        Path("lightspeed_runtime") / "__init__.py",
    )
    shell_root = select_root(
        args.shell_root,
        "LIGHTSPEED_SHELL_ROOT",
        Path(r"D:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed"),
        Path(r"C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed"),
        REPO_SHELL_ROOT,
        Path("N.py"),
    )
    python = os.environ.get("LIGHTSPEED_PYTHON") or sys.executable
    receipt_dir = runtime_root / "exports" / "agent_home"
    receipt_dir.mkdir(parents=True, exist_ok=True)

    desporte = (
        {"status": "skipped_by_operator"}
        if args.skip_desporte_population
        else run_desporte_population(python, receipt_dir)
    )
    desporte_process = optional_desporte_start()

    merovingian_lock = shell_root / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports" / "merovingian_supervisor.lock.json"
    merovingian_pid = lock_pid(merovingian_lock)
    if pid_alive(merovingian_pid):
        merovingian = {"state": "already_running", "pid": merovingian_pid}
    else:
        merovingian_pid = start_background(
            [
                python,
                str(REPO_ROOT / "scripts" / "run_merovingian_soft_launch.py"),
                "--watch",
                "--interval",
                "60",
                "--runtime-root",
                str(runtime_root),
                "--shell-root",
                str(shell_root),
            ],
            cwd=REPO_ROOT,
            log_path=shell_root / "Z Axis" / "Z-4_Merovingian" / "data" / "logs" / "merovingian-supervisor.log",
        )
        merovingian = {"state": "started", "pid": merovingian_pid}

    if port_open("127.0.0.1", 8765):
        bridge = {"state": "already_running", "origin": "http://127.0.0.1:8765"}
    else:
        bridge_pid = start_background(
            [python, str(REPO_ROOT / "tools" / "run_ls_go_bridge.py")],
            cwd=REPO_ROOT,
            log_path=shell_root / "Z Axis" / "Z-4_Merovingian" / "data" / "logs" / "ls-go-bridge.log",
        )
        bridge = {"state": "started", "pid": bridge_pid, "origin": "http://127.0.0.1:8765"}

    desktop_fragment = "Desktop_Hooks\\LightSpeed\\__main__.py"
    if args.no_desktop_launch:
        desktop = {"state": "skipped_by_operator"}
    elif windows_command_running(desktop_fragment):
        desktop = {"state": "already_running"}
    else:
        launcher = shell_root / "launcher_exe.py"
        completed = subprocess.run(
            [python, str(launcher)],
            cwd=shell_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        desktop = {
            "state": "started" if completed.returncode == 0 else "launch_failed",
            "exit_code": completed.returncode,
            "stderr_tail": completed.stderr[-1000:],
        }

    bridge_status = wait_for_bridge_status()
    required_states = {
        "merovingian": merovingian.get("state") in {"started", "already_running"},
        "bridge": bool(bridge_status.get("ok")),
        "desktop": desktop.get("state") in {"started", "already_running", "skipped_by_operator"},
        "desporte_population": desporte.get("status") in {"pass", "skipped_by_operator"},
        "desporte_process": desporte_process.get("state") in {"started", "already_running"},
    }
    receipt = {
        "schema_version": "lightspeed-cognigrex-local-stack-v1",
        "generated_utc": utc_now_iso(),
        "status": "pass" if all(required_states.values()) else "review_required",
        "runtime_root": str(runtime_root),
        "shell_root": str(shell_root),
        "checks": required_states,
        "desporte_population": desporte,
        "desporte_process": desporte_process,
        "merovingian": merovingian,
        "ls_go_bridge": bridge,
        "desktop": desktop,
        "bridge_status": bridge_status,
        "web_frontend_in_scope": False,
        "automatic_deletion": False,
        "next_action": (
            "Open LS GO Activity, review projects and receipts, then visually verify LightSpeed Desktop."
            if all(required_states.values())
            else "Resolve the failed local check before accepting holistic soft-launch operation."
        ),
    }
    output = args.json_output or receipt_dir / "cognigrex_local_stack_receipt.json"
    write_json(output, receipt)
    print(json.dumps({**receipt, "receipt_path": str(output)}, indent=2, sort_keys=True))
    return 0 if receipt["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
