#!/usr/bin/env python3
"""Observe and repair only the bounded local Cognigrex service set."""

from __future__ import annotations

import argparse
import hashlib
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


DEFAULT_CANONICAL_ROOT = Path(
    os.environ.get("LIGHTSPEED_CANONICAL_ROOT", r"D:\LightSpeed")
)


def canonical_receipt_dir(root: Path) -> Path:
    """Return the sole Desktop-owned operational receipt directory."""
    return (
        root
        / "App"
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "runtime_exports"
    )


def utc_now() -> datetime:
    return datetime.now(UTC)


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


def paths_refer_to_same_location(left: Path, right: Path) -> bool:
    """Treat the canonical D: namespace and its C: junction target as one root."""
    left_text = os.path.normcase(os.path.normpath(str(left)))
    right_text = os.path.normcase(os.path.normpath(str(right)))
    if left_text == right_text:
        return True
    try:
        return os.path.samefile(left, right)
    except (OSError, ValueError, TypeError):
        return False


def bridge_status_healthy(root: Path, timeout_seconds: float = 10.0) -> bool:
    """Require a bounded, canonical HTTP status response from the LS GO bridge."""
    request = Request(
        "http://127.0.0.1:8765/api/v1/status",
        headers={"Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            if response.status != 200:
                return False
            raw = response.read((1024 * 1024) + 1)
    except (OSError, TimeoutError, URLError):
        return False

    if len(raw) > 1024 * 1024:
        return False

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False

    expected_root = root / "App"
    reported_root = Path(str(payload.get("root", "")))
    return payload.get("ok") is True and paths_refer_to_same_location(
        expected_root,
        reported_root,
    )


def go_interface_healthy(timeout_seconds: float = 3.0) -> bool:
    """Require the built LightSpeed Go surface to answer HTTP, not only TCP."""
    request = Request("http://127.0.0.1:4173/", headers={"Accept": "text/html"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            if response.status != 200:
                return False
            raw = response.read((1024 * 1024) + 1)
    except (OSError, TimeoutError, URLError):
        return False
    if len(raw) > 1024 * 1024:
        return False
    return b"<html" in raw.lower() or b"<!doctype html" in raw.lower()


def start_go_interface(root: Path, python: Path) -> str | None:
    """A failed health probe never grants permission to multiply listeners."""
    if go_interface_healthy():
        return None
    if port_open(4173):
        return "go_port_occupied_unhealthy_no_duplicate_spawn"
    distribution = root / "Apps" / "lightspeed-go" / "dist"
    server = root / "Automation" / "serve_lightspeed_go.py"
    if not python.is_file() or not server.is_file() or not (distribution / "index.html").is_file():
        return "canonical_python_or_go_distribution_missing"
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    process = None
    try:
        process = subprocess.Popen(
            [str(Path(getattr(sys, "_base_executable", python))), str(server), "--directory", str(distribution)],
            cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=creation_flags,
        )
        for _ in range(30):
            if process.poll() is not None:
                return "go_interface_process_exited"
            if go_interface_healthy(timeout_seconds=0.5):
                return None
            time.sleep(0.1)
        return "go_interface_start_timeout"
    except OSError:
        return "go_interface_start_failed"
    finally:
        if process is not None and process.poll() is None and not go_interface_healthy(timeout_seconds=0.5):
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


def desktop_health_status(
    *,
    first_port: int = 8080,
    last_port: int = 8090,
    timeout_seconds: float = 2.0,
) -> dict[str, Any]:
    """Require the bounded LightSpeed Desktop HTTP identity, not just a PID."""
    for port in range(first_port, last_port + 1):
        if not port_open(port):
            continue
        request = Request(
            f"http://127.0.0.1:{port}/api/health",
            headers={"Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
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


def heartbeat_fresh(lock_path: Path, max_age_seconds: int = 180) -> bool:
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        stamp = datetime.fromisoformat(str(payload["heartbeat_utc"]).replace("Z", "+00:00"))
        age = (utc_now() - stamp).total_seconds()
        return 0 <= age <= max_age_seconds
    except (OSError, KeyError, ValueError, TypeError, json.JSONDecodeError):
        return False


def process_command_running(fragment: str) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import psutil

        needle = fragment.casefold()
        python_script_fragment = fragment.casefold().endswith(".py")
        for process in psutil.process_iter(["cmdline", "name"]):
            try:
                process_name = str(process.info.get("name") or "").casefold()
                if python_script_fragment and process_name not in {
                    "python.exe",
                    "pythonw.exe",
                }:
                    continue
                command_line = " ".join(process.info.get("cmdline") or [])
                if needle in command_line.casefold():
                    return True
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
        return False
    except (ImportError, OSError):
        pass

    command = (
        "Get-CimInstance Win32_Process | ForEach-Object { "
        "if ($_.CommandLine) { Write-Output ($_.Name + \"`t\" + $_.CommandLine) } }"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                    capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    needle = fragment.casefold()
    python_script_fragment = fragment.casefold().endswith(".py")
    return completed.returncode == 0 and any(
        needle in parts[1].casefold()
        for line in completed.stdout.splitlines()
        if len(parts := line.split("\t", 1)) == 2
        and (
            not python_script_fragment
            or parts[0].casefold() in {"python.exe", "pythonw.exe"}
        )
    )



def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _git_value(repo: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def assurance_state(root: Path, *, max_heartbeat_age: int) -> dict[str, Any]:
    repo = root / "Repositories" / "LightSpeed_Canonical"
    head = _git_value(repo, "rev-parse", "HEAD") if repo.is_dir() else None
    origin_main = _git_value(repo, "rev-parse", "origin/main") if repo.is_dir() else None
    worktree = _git_value(repo, "status", "--porcelain") if repo.is_dir() else None
    source_consumer = (
        repo / "desktop" / "LightSpeed_Runtime" / "lightspeed_runtime" / "ls_go_job_consumer.py"
    )
    installed_consumer = root / "App" / "lightspeed_runtime" / "ls_go_job_consumer.py"
    exports = canonical_receipt_dir(root)
    consumer_lock = exports / "ls_go_job_consumer.lock.json"
    consumer_receipt = exports / "ls_go_job_consumer_receipt.json"
    lock_payload = _read_json(consumer_lock)
    receipt_payload = _read_json(consumer_receipt)

    root_config_path = Path(r"C:\Cognigrex\cognigrex.root.json")
    root_config = _read_json(root_config_path)
    founder_path = Path(
        r"C:\Cognigrex\State\Frontier\FounderReview\FOUNDER_APPROVAL_REGISTER_2026-10-10.json"
    )

    source_hash = _sha256(source_consumer)
    installed_hash = _sha256(installed_consumer)
    source_aligned = bool(head and origin_main and head == origin_main and worktree == "")
    consumer_fresh = heartbeat_fresh(consumer_lock, max_heartbeat_age)
    installed_matches_source = bool(source_hash and installed_hash and source_hash == installed_hash)
    root_declared_head = str(root_config.get("current_canonical_source_head") or "")
    root_matches_source = bool(head and root_declared_head and head == root_declared_head)

    holds: list[str] = []
    if not source_aligned:
        holds.append("SOURCE_CHECKOUT_NOT_ALIGNED")
    if not consumer_fresh:
        holds.append("CONSUMER_HEARTBEAT_STALE_OR_UNREADABLE")
    if not installed_matches_source:
        holds.append("INSTALLED_CONSUMER_DIFFERS_FROM_CURRENT_SOURCE_UPGRADE_HOLD")
    if not root_matches_source:
        holds.append("ROOT_SOURCE_POINTER_NOT_CURRENT")
    if not founder_path.is_file():
        holds.append("FOUNDER_REGISTER_UNAVAILABLE")

    return {
        "source": {
            "checkout": str(repo),
            "head": head,
            "origin_main": origin_main,
            "worktree_clean": worktree == "",
            "aligned_without_fetch": source_aligned,
            "network_fetch_performed": False,
        },
        "consumer": {
            "lock_path": str(consumer_lock),
            "lock_pid": lock_payload.get("pid"),
            "heartbeat_utc": lock_payload.get("heartbeat_utc"),
            "heartbeat_fresh": consumer_fresh,
            "receipt_state": receipt_payload.get("state"),
            "installed_sha256": installed_hash,
            "current_source_sha256": source_hash,
            "installed_matches_current_source": installed_matches_source,
        },
        "root": {
            "path": str(root_config_path),
            "exists": root_config_path.is_file(),
            "declared_source_head": root_declared_head or None,
            "matches_local_source_head": root_matches_source,
            "carrier_or_root_promotion": False,
        },
        "founder": {
            "register_path": str(founder_path),
            "register_exists": founder_path.is_file(),
            "register_sha256": _sha256(founder_path),
            "auto_approval": False,
        },
        "holds": holds,
        "upgrade_allowed": source_aligned and installed_matches_source and root_matches_source,
        "recovery_scope": "existing_installed_stack_only",
        "automatic_source_sync": False,
        "automatic_install_or_upgrade": False,
        "automatic_public_export": False,
        "automatic_physical_actuation": False,
        "automatic_root_or_carrier_promotion": False,
    }

def write_receipt(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def observe(root: Path, *, max_heartbeat_age: int) -> dict[str, Any]:
    lock_path = (
        root
        / "App"
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "runtime_exports"
        / "merovingian_supervisor.lock.json"
    )
    desktop_marker = str(root / "App" / "__main__.py")
    desktop_process = process_command_running(desktop_marker)
    desktop_http = desktop_health_status()
    return {
        "bridge": bridge_status_healthy(root),
        "bridge_tcp": port_open(8765),
        "merovingian_heartbeat": heartbeat_fresh(lock_path, max_heartbeat_age),
        "go_interface": go_interface_healthy(),
        "desktop_process": desktop_process,
        "desktop_http": bool(desktop_http["healthy"]),
        "desktop_port": desktop_http["port"],
        "desktop": desktop_process and bool(desktop_http["healthy"]),
        "assurance": assurance_state(root, max_heartbeat_age=max_heartbeat_age),
    }


def run_guard(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL_ROOT)
    parser.add_argument("--max-heartbeat-age", type=int, default=180)
    parser.add_argument("--repair-timeout", type=int, default=180)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    root = args.canonical_root.absolute()
    python = root / "Environment" / "Scripts" / "python.exe"
    launcher = root / "Automation" / "run_cognigrex_local_stack.py"
    receipt = root / "State" / "Health" / "cognigrex_watchdog_receipt.json"
    stack_receipt = canonical_receipt_dir(root) / "cognigrex_local_stack_receipt.json"

    before = observe(root, max_heartbeat_age=args.max_heartbeat_age)
    needs_stack_repair = not (
        before["bridge"] and before["merovingian_heartbeat"] and before["desktop"]
    )
    needs_go_repair = not before["go_interface"]
    needs_repair = needs_stack_repair or needs_go_repair
    launch_exit_code: int | None = None
    launch_error: str | None = None
    if needs_stack_repair:
        if not python.is_file() or not launcher.is_file():
            launch_error = "canonical_python_or_launcher_missing"
        else:
            try:
                completed = subprocess.run(
                    [
                        str(python),
                        str(launcher),
                        "--skip-desporte-population",
                        "--json-output",
                        str(stack_receipt),
                    ],
                    cwd=root,
                    check=False,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                    capture_output=True,
                    text=True,
                    timeout=max(1, int(args.repair_timeout)),
                )
                launch_exit_code = int(completed.returncode)
            except subprocess.TimeoutExpired:
                launch_error = "bounded_repair_timeout"

    go_launch_error: str | None = None
    if needs_go_repair:
        go_launch_error = start_go_interface(root, python)

    after = observe(root, max_heartbeat_age=args.max_heartbeat_age)
    operational_services_healthy = bool(
        after["bridge"] and after["merovingian_heartbeat"] and after["desktop"] and after["go_interface"]
    )
    consumer_fresh = bool((after.get("assurance") or {}).get("consumer", {}).get("heartbeat_fresh"))
    status = "pass" if operational_services_healthy and consumer_fresh else "review_required"
    payload = {
        "schema_version": "lightspeed-cognigrex-watchdog-v2",
        "generated_utc": utc_now().isoformat(timespec="seconds"),
        "status": status,
        "action": "repair" if needs_repair else "observe",
        "before": before,
        "after": after,
        "launch_exit_code": launch_exit_code,
        "launch_error": launch_error,
        "go_launch_error": go_launch_error,
        "canonical_root": str(root),
        "operational_services_healthy": operational_services_healthy,
        "assurance": after.get("assurance"),
        "repair_policy": "existing_installed_stack_only; source/install mismatch blocks upgrade, not bounded recovery",
        "automatic_deletion": False,
        "automatic_source_sync": False,
        "automatic_install_or_upgrade": False,
        "founder_auto_approval": False,
        "root_or_carrier_promotion": False,
        "physical_actuation": False,
        "public_export": False,
    }
    write_receipt(receipt, payload)
    if not args.quiet:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if status == "pass" else 2


def main(argv: list[str] | None = None) -> int:
    lock_path = Path(__file__).with_suffix(".lock")
    with lock_path.open("a+b") as guard_lock:
        if sys.platform == "win32":
            import msvcrt
            if guard_lock.seek(0, 2) == 0:
                guard_lock.write(b"0"); guard_lock.flush()
            guard_lock.seek(0)
            try:
                msvcrt.locking(guard_lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                return 0
        try:
            return run_guard(argv)
        finally:
            if sys.platform == "win32":
                guard_lock.seek(0); msvcrt.locking(guard_lock.fileno(), msvcrt.LK_UNLCK, 1)

if __name__ == "__main__":
    raise SystemExit(main())
