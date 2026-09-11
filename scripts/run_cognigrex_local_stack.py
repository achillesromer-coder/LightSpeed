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
from urllib.error import URLError
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_RUNTIME_ROOT = REPO_ROOT / "desktop" / "LightSpeed_Runtime"
REPO_SHELL_ROOT = REPO_ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed"
CANONICAL_ROOT = Path(os.environ.get("LIGHTSPEED_CANONICAL_ROOT", r"D:\LightSpeed"))
CANONICAL_DATABASE = CANONICAL_ROOT / "Data" / "db" / "lightspeed_unified.db"


def canonical_receipt_dir(shell_root: Path) -> Path:
    """Return the sole operator-owned receipt directory.

    Runtime exports under ``Core/exports`` are presentation context for the
    Desktop bridge. Operational receipts belong to the live Desktop shell so
    starting the split runtime cannot create a second receipt authority.
    """
    return (
        shell_root
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "runtime_exports"
    )


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
    # The operator namespace outranks stale machine variables from older
    # LightSpeed layouts. An explicit CLI path remains the diagnostic override.
    candidates = [explicit]
    if os.name == "nt":
        candidates.append(canonical)
    candidates.append(Path(os.environ[env_name]) if os.environ.get(env_name) else None)
    if os.name == "nt":
        candidates.append(legacy)
    candidates.append(repository)
    for candidate in candidates:
        if candidate and (candidate / marker).is_file():
            # Preserve D:\LightSpeed as the operator namespace instead of
            # resolving its junctions back to their physical C: targets.
            return candidate.absolute()
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


def heartbeat_fresh(path: Path, max_age_seconds: int = 255) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        stamp = datetime.fromisoformat(
            str(payload["heartbeat_utc"]).replace("Z", "+00:00")
        )
        age = (datetime.now(UTC) - stamp).total_seconds()
        return 0 <= age <= max_age_seconds
    except (OSError, KeyError, ValueError, TypeError, json.JSONDecodeError):
        return False


def wait_for_heartbeat(
    path: Path,
    pid: int,
    *,
    timeout_seconds: float = 30.0,
    max_age_seconds: int = 255,
) -> bool:
    deadline = time.monotonic() + max(1.0, timeout_seconds)
    while time.monotonic() < deadline:
        if lock_pid(path) == pid and pid_alive(pid) and heartbeat_fresh(
            path, max_age_seconds
        ):
            return True
        time.sleep(0.5)
    return False


def desktop_health_status(
    *,
    first_port: int = 8080,
    last_port: int = 8090,
    timeout_seconds: float = 2.0,
) -> dict[str, Any]:
    """Return only a bounded, identity-checked LightSpeed Desktop health result."""
    for port in range(first_port, last_port + 1):
        if not port_open("127.0.0.1", port):
            continue
        try:
            with urlopen(
                f"http://127.0.0.1:{port}/api/health",
                timeout=timeout_seconds,
            ) as response:
                if response.status != 200:
                    continue
                raw = response.read((64 * 1024) + 1)
        except (OSError, TimeoutError, URLError):
            continue
        if len(raw) > 64 * 1024:
            continue
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if (
            payload.get("status") == "operational"
            and payload.get("server") == "FastAPI + Three.js"
        ):
            return {
                "healthy": True,
                "port": port,
                "version": payload.get("version"),
                "server": payload.get("server"),
            }
    return {"healthy": False, "port": None, "version": None, "server": None}


def wait_for_desktop_health(timeout_seconds: float = 30.0) -> dict[str, Any]:
    deadline = time.monotonic() + max(1.0, timeout_seconds)
    latest = desktop_health_status()
    while not latest["healthy"] and time.monotonic() < deadline:
        time.sleep(1)
        latest = desktop_health_status()
    return latest


def creation_flags() -> int:
    if os.name != "nt":
        return 0
    return (
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        | getattr(subprocess, "DETACHED_PROCESS", 0)
        | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        | getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
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


def installed_or_repository_script(group: str, name: str) -> Path:
    installed = CANONICAL_ROOT / group / name
    if installed.is_file():
        return installed
    repository_group = "scripts" if group.casefold() == "automation" else "tools"
    return REPO_ROOT / repository_group / name


def windows_command_processes(fragment: str) -> list[dict[str, Any]]:
    if os.name != "nt":
        return []
    try:
        import psutil

        needle = fragment.casefold()
        rows: list[dict[str, Any]] = []
        python_script_fragment = fragment.casefold().endswith(".py")
        for process in psutil.process_iter(
            ["pid", "ppid", "create_time", "cmdline", "name"]
        ):
            try:
                process_name = str(process.info.get("name") or "").casefold()
                if python_script_fragment and process_name not in {
                    "python.exe",
                    "pythonw.exe",
                }:
                    continue
                command_line = " ".join(process.info.get("cmdline") or [])
                if needle not in command_line.casefold():
                    continue
                rows.append(
                    {
                        "pid": int(process.info["pid"]),
                        "parent_pid": int(process.info.get("ppid") or 0),
                        "created_ticks": int(
                            float(process.info.get("create_time") or 0.0)
                            * 10_000_000
                        ),
                        "name": process.info.get("name"),
                        "command_line": command_line,
                    }
                )
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
        return rows
    except (ImportError, OSError):
        pass

    # Do not embed ``fragment`` in the PowerShell command: doing so makes the
    # probe match its own command line and report every process as running.
    command = (
        "Get-CimInstance Win32_Process | ForEach-Object { "
        "if ($_.CommandLine) { Write-Output ("
        "$_.Name + \"`t\" + $_.ProcessId.ToString() + \"`t\" + $_.ParentProcessId.ToString() + \"`t\" + "
        "$_.CreationDate.ToUniversalTime().Ticks.ToString() + \"`t\" + $_.CommandLine) } "
        "}"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if completed.returncode != 0:
        return []
    needle = fragment.casefold()
    rows: list[dict[str, Any]] = []
    python_script_fragment = fragment.casefold().endswith(".py")
    for line in completed.stdout.splitlines():
        if needle not in line.casefold():
            continue
        parts = line.split("\t", 4)
        if len(parts) != 5:
            continue
        if python_script_fragment and parts[0].casefold() not in {
            "python.exe",
            "pythonw.exe",
        }:
            continue
        try:
            rows.append(
                {
                    "name": parts[0],
                    "pid": int(parts[1]),
                    "parent_pid": int(parts[2]),
                    "created_ticks": int(parts[3]),
                    "command_line": parts[4],
                }
            )
        except ValueError:
            continue
    return rows


def windows_command_running(fragment: str) -> bool:
    return bool(windows_command_processes(fragment))


def stop_verified_process_tree(
    pid: int,
    *,
    process_fragment: str,
    required_command_fragment: str,
) -> dict[str, Any]:
    """Stop one process tree only after its exact command identity is verified."""
    rows = windows_command_processes(process_fragment)
    by_pid = {int(row["pid"]): row for row in rows}
    row = by_pid.get(int(pid))
    required = required_command_fragment.casefold()
    row_name = str((row or {}).get("name") or "").casefold()
    python_script_required = required.endswith(".py")
    if (
        row is None
        or required not in str(row["command_line"]).casefold()
        or (
            python_script_required
            and row_name not in {"python.exe", "pythonw.exe"}
        )
    ):
        return {
            "verified": False,
            "requested_pid": int(pid),
            "stopped_root_pid": None,
        }
    root_pid = int(pid)
    while int(by_pid[root_pid]["parent_pid"]) in by_pid:
        root_pid = int(by_pid[root_pid]["parent_pid"])
    tree_pids = {root_pid}
    changed = True
    while changed:
        changed = False
        for candidate in rows:
            candidate_pid = int(candidate["pid"])
            if (
                candidate_pid not in tree_pids
                and int(candidate["parent_pid"]) in tree_pids
            ):
                tree_pids.add(candidate_pid)
                changed = True
    completed = subprocess.run(
        ["taskkill", "/PID", str(root_pid), "/T", "/F"],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    survivor_stops: list[int] = []
    if completed.returncode == 0:
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and any(
            pid_alive(candidate_pid) for candidate_pid in tree_pids
        ):
            time.sleep(0.25)
        current = {
            int(candidate["pid"]): candidate
            for candidate in windows_command_processes(process_fragment)
        }
        for candidate_pid in sorted(tree_pids):
            candidate = current.get(candidate_pid)
            candidate_name = str((candidate or {}).get("name") or "").casefold()
            if (
                candidate is None
                or not pid_alive(candidate_pid)
                or required not in str(candidate["command_line"]).casefold()
                or (
                    python_script_required
                    and candidate_name not in {"python.exe", "pythonw.exe"}
                )
            ):
                continue
            survivor = subprocess.run(
                ["taskkill", "/PID", str(candidate_pid), "/T", "/F"],
                capture_output=True,
                text=True,
                check=False,
                timeout=20,
            )
            if survivor.returncode == 0:
                survivor_stops.append(candidate_pid)
        if survivor_stops:
            time.sleep(0.5)
    unresolved = [
        candidate_pid
        for candidate_pid in tree_pids
        if pid_alive(candidate_pid)
    ]
    return {
        "verified": True,
        "requested_pid": int(pid),
        "stopped_root_pid": root_pid if completed.returncode == 0 else None,
        "exit_code": int(completed.returncode),
        "verified_tree_pids": sorted(tree_pids),
        "survivor_pids_stopped": survivor_stops,
        "unresolved_tree_pids": unresolved,
    }


def listening_pid(port: int) -> int | None:
    if os.name != "nt":
        return None
    try:
        import psutil

        for connection in psutil.net_connections(kind="tcp"):
            if (
                connection.status == psutil.CONN_LISTEN
                and connection.laddr
                and int(connection.laddr.port) == int(port)
            ):
                return int(connection.pid) if connection.pid else None
        return None
    except (ImportError, OSError):
        pass

    try:
        completed = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    for line in completed.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5 or parts[0].upper() != "TCP":
            continue
        local = parts[1]
        state = parts[3].upper()
        if state != "LISTENING" or not local.endswith(f":{int(port)}"):
            continue
        try:
            return int(parts[4])
        except ValueError:
            return None
    return None


def _root_processes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_pid = {int(row["pid"]): row for row in rows}
    return [row for row in rows if int(row["parent_pid"]) not in by_pid]


def reconcile_singleton(
    fragment: str,
    *,
    preferred_pid: int | None = None,
) -> dict[str, Any]:
    """Keep one matching Windows process tree and stop duplicate roots only."""
    rows = windows_command_processes(fragment)
    if not rows:
        return {"matching_processes": 0, "duplicate_roots_stopped": []}
    by_pid = {int(row["pid"]): row for row in rows}
    roots = _root_processes(rows)
    if len(roots) <= 1:
        return {"matching_processes": len(rows), "duplicate_roots_stopped": []}

    keep_root: int | None = None
    if preferred_pid in by_pid:
        cursor = int(preferred_pid)
        while int(by_pid[cursor]["parent_pid"]) in by_pid:
            cursor = int(by_pid[cursor]["parent_pid"])
        keep_root = cursor
    if keep_root is None:
        keep_root = int(min(roots, key=lambda row: int(row["created_ticks"]))["pid"])

    stopped: list[int] = []
    for root in roots:
        pid = int(root["pid"])
        if pid == keep_root:
            continue
        completed = subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        if completed.returncode == 0:
            stopped.append(pid)
    return {
        "matching_processes": len(rows),
        "kept_root_pid": keep_root,
        "duplicate_roots_stopped": stopped,
    }


def stop_noncanonical_process_roots(
    fragment: str,
    canonical_marker: str,
) -> dict[str, Any]:
    """Stop matching roots that do not execute through the canonical path."""
    rows = windows_command_processes(fragment)
    if not rows:
        return {"matching_processes": 0, "noncanonical_roots_stopped": []}
    marker = canonical_marker.casefold()
    stopped: list[int] = []
    for root in _root_processes(rows):
        if marker in str(root["command_line"]).casefold():
            continue
        pid = int(root["pid"])
        completed = subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        if completed.returncode == 0:
            stopped.append(pid)
    return {
        "matching_processes": len(rows),
        "noncanonical_roots_stopped": stopped,
    }


def stop_unhealthy_bridge_listener(port: int = 8765) -> dict[str, Any]:
    """Stop only a verified LS GO bridge tree that owns an unhealthy listener."""
    listener_pid = listening_pid(port)
    rows = windows_command_processes("run_ls_go_bridge.py")
    by_pid = {int(row["pid"]): row for row in rows}
    if listener_pid not in by_pid:
        return {
            "listener_pid": listener_pid,
            "verified_bridge_owner": False,
            "stopped_root_pid": None,
        }

    root_pid = int(listener_pid)
    while int(by_pid[root_pid]["parent_pid"]) in by_pid:
        root_pid = int(by_pid[root_pid]["parent_pid"])
    completed = subprocess.run(
        ["taskkill", "/PID", str(root_pid), "/T", "/F"],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    return {
        "listener_pid": listener_pid,
        "verified_bridge_owner": True,
        "stopped_root_pid": root_pid if completed.returncode == 0 else None,
        "exit_code": int(completed.returncode),
    }


def run_desporte_population(python: str, receipt_dir: Path) -> dict[str, Any]:
    script = installed_or_repository_script("Automation", "populate_desporte_desktop.py")
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


def optional_desporte_start(*, allowed: bool = False) -> dict[str, Any]:
    if not allowed:
        return {
            "state": "held_by_gate",
            "detail": "De Sporte process launch requires --allow-desporte-launch.",
        }
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
    pid = start_background(
        [str(executable), *args],
        cwd=executable.parent,
        log_path=CANONICAL_ROOT / "Logs" / "desporte-launch.log",
    )
    time.sleep(2)
    return {
        "state": "started" if pid_alive(pid) else "launch_failed",
        "path": str(executable),
        "pid": pid,
    }


def read_bridge_status(timeout_seconds: float = 8.0) -> dict[str, Any]:
    try:
        with urlopen(
            "http://127.0.0.1:8765/api/v1/status",
            timeout=max(0.1, timeout_seconds),
        ) as response:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--shell-root", type=Path)
    parser.add_argument("--skip-desporte-population", action="store_true")
    parser.add_argument("--allow-desporte-launch", action="store_true")
    parser.add_argument("--no-desktop-launch", action="store_true")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)

    runtime_root = select_root(
        args.runtime_root,
        "LIGHTSPEED_RUNTIME_ROOT",
        CANONICAL_ROOT / "Core",
        Path(r"C:\LightSpeed_Consolidated\LightSpeed_Runtime"),
        REPO_RUNTIME_ROOT,
        Path("lightspeed_runtime") / "__init__.py",
    )
    shell_root = select_root(
        args.shell_root,
        "LIGHTSPEED_SHELL_ROOT",
        CANONICAL_ROOT / "App",
        Path(r"C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed"),
        REPO_SHELL_ROOT,
        Path("N.py"),
    )
    runtime_policy_path = shell_root / "config" / "host_runtime_policy.json"
    runtime_limits: dict[str, Any] = {}
    try:
        runtime_policy = json.loads(runtime_policy_path.read_text(encoding="utf-8"))
        runtime_limits = dict(runtime_policy.get("runtime_limits") or {})
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        runtime_limits = {}
    cognigrex_speed_percent = max(
        10,
        min(int(runtime_limits.get("cognigrex_speed_percent", 100)), 100),
    )
    merovingian_interval_seconds = max(
        30,
        min(int(runtime_limits.get("merovingian_interval_seconds", 60)), 3600),
    )
    operating_profile = {
        "name": runtime_limits.get("active_operating_profile", "default"),
        "speed_percent": cognigrex_speed_percent,
        "background_process_priority": runtime_limits.get(
            "background_process_priority", "below_normal"
        ),
        "max_background_queue_workers": runtime_limits.get(
            "max_background_queue_workers", 1
        ),
        "max_concurrent_ollama_jobs": runtime_limits.get(
            "max_concurrent_ollama_jobs", 1
        ),
        "max_floor_boot_parallelism": runtime_limits.get(
            "max_floor_boot_parallelism", 2
        ),
        "merovingian_interval_seconds": merovingian_interval_seconds,
    }
    os.environ["LIGHTSPEED_CANONICAL_ROOT"] = str(CANONICAL_ROOT)
    os.environ["LIGHTSPEED_RUNTIME_ROOT"] = str(runtime_root)
    os.environ["LIGHTSPEED_SHELL_ROOT"] = str(shell_root)
    os.environ["LIGHTSPEED_CANONICAL_DB"] = str(CANONICAL_DATABASE)
    canonical_python = CANONICAL_ROOT / "Environment" / "Scripts" / "python.exe"
    python = (
        str(canonical_python)
        if canonical_python.is_file()
        else os.environ.get("LIGHTSPEED_PYTHON") or sys.executable
    )
    receipt_dir = canonical_receipt_dir(shell_root)
    receipt_dir.mkdir(parents=True, exist_ok=True)

    desporte = (
        {"status": "skipped_by_operator"}
        if args.skip_desporte_population
        else run_desporte_population(python, receipt_dir)
    )
    desporte_process = optional_desporte_start(
        allowed=bool(args.allow_desporte_launch)
    )

    merovingian_lock = (
        shell_root
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "runtime_exports"
        / "merovingian_supervisor.lock.json"
    )
    merovingian_script = installed_or_repository_script(
        "Automation",
        "run_merovingian_soft_launch.py",
    )
    merovingian_pid = lock_pid(merovingian_lock)
    merovingian_recovery: dict[str, Any] = {"action": "not_required"}
    should_start_merovingian = False
    if pid_alive(merovingian_pid) and heartbeat_fresh(merovingian_lock):
        merovingian = {"state": "already_running", "pid": merovingian_pid}
    elif pid_alive(merovingian_pid):
        merovingian_recovery = stop_verified_process_tree(
            int(merovingian_pid),
            process_fragment="run_merovingian_soft_launch.py",
            required_command_fragment=str(merovingian_script),
        )
        merovingian_recovery["action"] = "stale_heartbeat_repair"
        if (
            merovingian_recovery.get("stopped_root_pid")
            and not merovingian_recovery.get("unresolved_tree_pids")
        ):
            should_start_merovingian = True
            merovingian = {"state": "stale_process_stopped", "pid": merovingian_pid}
        else:
            merovingian = {
                "state": "stale_process_identity_unverified",
                "pid": merovingian_pid,
            }
    else:
        should_start_merovingian = True
        merovingian = {"state": "not_running", "pid": merovingian_pid}

    if should_start_merovingian:
        merovingian_pid = start_background(
            [
                python,
                str(merovingian_script),
                "--watch",
                "--interval",
                str(merovingian_interval_seconds),
                "--runtime-root",
                str(runtime_root),
                "--shell-root",
                str(shell_root),
            ],
            cwd=CANONICAL_ROOT if CANONICAL_ROOT.is_dir() else REPO_ROOT,
            log_path=(
                shell_root
                / "Z Axis"
                / "Z-4_Merovingian"
                / "data"
                / "logs"
                / "merovingian-supervisor.log"
            ),
        )
        merovingian_ready = wait_for_heartbeat(
            merovingian_lock,
            merovingian_pid,
            timeout_seconds=60,
        )
        merovingian = {
            "state": "started" if merovingian_ready else "launch_unverified",
            "pid": merovingian_pid,
            "heartbeat_fresh": merovingian_ready,
        }

    bridge_reconciliation = reconcile_singleton(
        "run_ls_go_bridge.py",
        preferred_pid=listening_pid(8765),
    )
    initial_bridge_status = read_bridge_status(timeout_seconds=10.0)
    bridge_root_matches = (
        os.path.normcase(os.path.normpath(str(initial_bridge_status.get("root", ""))))
        == os.path.normcase(os.path.normpath(str(shell_root)))
    )
    bridge_responding = (
        initial_bridge_status.get("bridge") == "ls-go"
        and bridge_root_matches
        and "error" not in initial_bridge_status
    )
    bridge_recovery: dict[str, Any] = {"action": "not_required"}
    if bridge_responding:
        bridge = {"state": "already_running", "origin": "http://127.0.0.1:8765"}
    else:
        bridge = {
            "state": "unhealthy_unrecovered",
            "origin": "http://127.0.0.1:8765",
        }
        if port_open("127.0.0.1", 8765):
            bridge_recovery = stop_unhealthy_bridge_listener(8765)
            if bridge_recovery.get("stopped_root_pid"):
                deadline = time.monotonic() + 10.0
                while port_open("127.0.0.1", 8765) and time.monotonic() < deadline:
                    time.sleep(0.25)
            elif port_open("127.0.0.1", 8765):
                bridge = {
                    "state": "unhealthy_unknown_listener",
                    "origin": "http://127.0.0.1:8765",
                }

        if not port_open("127.0.0.1", 8765):
            # A matching process without a listener is stale. Stop only its
            # verified bridge root before starting the canonical bridge.
            for row in _root_processes(windows_command_processes("run_ls_go_bridge.py")):
                subprocess.run(
                    ["taskkill", "/PID", str(row["pid"]), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=20,
                )
            bridge_pid = start_background(
                [python, str(installed_or_repository_script("Tools", "run_ls_go_bridge.py"))],
                cwd=CANONICAL_ROOT if CANONICAL_ROOT.is_dir() else REPO_ROOT,
                log_path=shell_root / "Z Axis" / "Z-4_Merovingian" / "data" / "logs" / "ls-go-bridge.log",
            )
            bridge = {
                "state": "started",
                "pid": bridge_pid,
                "origin": "http://127.0.0.1:8765",
            }

    canonical_desktop_marker = str(shell_root / "__main__.py")
    legacy_desktop_reconciliation = stop_noncanonical_process_roots(
        r"Desktop_Hooks\LightSpeed\__main__.py",
        canonical_desktop_marker,
    )
    desktop_reconciliation = reconcile_singleton(canonical_desktop_marker)
    desktop_rows = windows_command_processes(canonical_desktop_marker)
    desktop_health_before = desktop_health_status()
    desktop_recovery: dict[str, Any] = {"action": "not_required"}
    should_launch_desktop = False
    if args.no_desktop_launch:
        desktop = {
            "state": (
                "observed_healthy"
                if desktop_rows and desktop_health_before["healthy"]
                else "launch_skipped_unhealthy"
            ),
            "health": desktop_health_before,
        }
    elif desktop_rows and desktop_health_before["healthy"]:
        desktop = {"state": "already_running", "health": desktop_health_before}
    elif desktop_rows:
        desktop_target = min(
            _root_processes(desktop_rows),
            key=lambda row: int(row["created_ticks"]),
        )
        desktop_recovery = stop_verified_process_tree(
            int(desktop_target["pid"]),
            process_fragment=canonical_desktop_marker,
            required_command_fragment=canonical_desktop_marker,
        )
        desktop_recovery["action"] = "unhealthy_http_repair"
        if (
            desktop_recovery.get("stopped_root_pid")
            and not desktop_recovery.get("unresolved_tree_pids")
        ):
            should_launch_desktop = True
            desktop = {
                "state": "unhealthy_process_stopped",
                "health": desktop_health_before,
            }
        else:
            desktop = {
                "state": "unhealthy_process_identity_unverified",
                "health": desktop_health_before,
            }
    elif desktop_health_before["healthy"]:
        desktop = {
            "state": "healthy_listener_identity_unverified",
            "health": desktop_health_before,
        }
    else:
        should_launch_desktop = True
        desktop = {"state": "not_running", "health": desktop_health_before}

    if should_launch_desktop:
        launcher = shell_root / "launcher_exe.py"
        completed = subprocess.run(
            [python, str(launcher)],
            cwd=shell_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        desktop_health_after_launch = wait_for_desktop_health(timeout_seconds=45)
        desktop = {
            "state": (
                "started"
                if completed.returncode == 0 and desktop_health_after_launch["healthy"]
                else "launch_unverified"
            ),
            "exit_code": completed.returncode,
            "stderr_tail": completed.stderr[-1000:],
            "health": desktop_health_after_launch,
        }

    bridge_status = wait_for_bridge_status()
    desktop_process_verified = windows_command_running(canonical_desktop_marker)
    desktop_health_final = desktop_health_status()
    merovingian_verified = (
        lock_pid(merovingian_lock) == merovingian_pid
        and pid_alive(merovingian_pid)
        and heartbeat_fresh(merovingian_lock)
    )
    desporte_launch_gate_compliant = (
        desporte_process.get("state") in {"started", "already_running"}
        if args.allow_desporte_launch
        else desporte_process.get("state") == "held_by_gate"
    )
    required_states = {
        "merovingian": merovingian_verified,
        "bridge": bool(bridge_status.get("ok")),
        "desktop": desktop_process_verified and bool(desktop_health_final["healthy"]),
        "desporte_population": desporte.get("status") in {"pass", "skipped_by_operator"},
        "desporte_launch_gate": desporte_launch_gate_compliant,
    }
    receipt = {
        "schema_version": "lightspeed-cognigrex-local-stack-v1",
        "generated_utc": utc_now_iso(),
        "status": "pass" if all(required_states.values()) else "review_required",
        "canonical_root": str(CANONICAL_ROOT),
        "core_root": str(runtime_root),
        "app_root": str(shell_root),
        "checks": required_states,
        "desporte_population": desporte,
        "desporte_process": desporte_process,
        "merovingian": merovingian,
        "ls_go_bridge": bridge,
        "process_reconciliation": {
            "bridge": bridge_reconciliation,
            "bridge_recovery": bridge_recovery,
            "merovingian_recovery": merovingian_recovery,
            "desktop": desktop_reconciliation,
            "desktop_recovery": desktop_recovery,
            "legacy_desktop": legacy_desktop_reconciliation,
        },
        "desktop": {
            **desktop,
            "process_verified": desktop_process_verified,
            "final_health": desktop_health_final,
        },
        "bridge_status": bridge_status,
        "operating_profile": operating_profile,
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
