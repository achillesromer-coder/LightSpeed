#!/usr/bin/env python3
"""Observe and repair only the bounded local Cognigrex service set."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from typing import Any


DEFAULT_CANONICAL_ROOT = Path(
    os.environ.get("LIGHTSPEED_CANONICAL_ROOT", r"D:\LightSpeed")
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


def heartbeat_fresh(lock_path: Path, max_age_seconds: int = 180) -> bool:
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        stamp = datetime.fromisoformat(str(payload["heartbeat_utc"]).replace("Z", "+00:00"))
        return (utc_now() - stamp).total_seconds() <= max_age_seconds
    except (OSError, KeyError, ValueError, TypeError, json.JSONDecodeError):
        return False


def process_command_running(fragment: str) -> bool:
    if sys.platform != "win32":
        return False
    command = (
        "Get-CimInstance Win32_Process | ForEach-Object { "
        "if ($_.CommandLine) { Write-Output $_.CommandLine } }"
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
        return False
    needle = fragment.casefold()
    return completed.returncode == 0 and any(
        needle in line.casefold() for line in completed.stdout.splitlines()
    )


def write_receipt(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def observe(root: Path, *, max_heartbeat_age: int) -> dict[str, bool]:
    lock_path = (
        root
        / "App"
        / "Z Axis"
        / "Z-4_Merovingian"
        / "data"
        / "runtime_exports"
        / "merovingian_supervisor.lock.json"
    )
    return {
        "bridge": port_open(8765),
        "merovingian_heartbeat": heartbeat_fresh(lock_path, max_heartbeat_age),
        "go_interface": port_open(4173),
        "desktop": process_command_running(str(root / "App" / "__main__.py")),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL_ROOT)
    parser.add_argument("--max-heartbeat-age", type=int, default=180)
    parser.add_argument("--repair-timeout", type=int, default=180)
    args = parser.parse_args(argv)

    root = args.canonical_root.absolute()
    python = root / "Environment" / "Scripts" / "python.exe"
    launcher = root / "Automation" / "run_cognigrex_local_stack.py"
    receipt = root / "State" / "Health" / "cognigrex_watchdog_receipt.json"
    stack_receipt = (
        root / "Core" / "exports" / "agent_home" / "cognigrex_local_stack_receipt.json"
    )

    before = observe(root, max_heartbeat_age=args.max_heartbeat_age)
    needs_repair = not (
        before["bridge"] and before["merovingian_heartbeat"] and before["desktop"]
    )
    launch_exit_code: int | None = None
    launch_error: str | None = None
    if needs_repair:
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
                    capture_output=True,
                    text=True,
                    timeout=max(1, int(args.repair_timeout)),
                )
                launch_exit_code = int(completed.returncode)
            except subprocess.TimeoutExpired:
                launch_error = "bounded_repair_timeout"

    after = observe(root, max_heartbeat_age=args.max_heartbeat_age)
    status = (
        "pass"
        if after["bridge"] and after["merovingian_heartbeat"] and after["desktop"]
        else "review_required"
    )
    payload = {
        "schema_version": "lightspeed-cognigrex-watchdog-v1",
        "generated_utc": utc_now().isoformat(timespec="seconds"),
        "status": status,
        "action": "repair" if needs_repair else "observe",
        "before": before,
        "after": after,
        "launch_exit_code": launch_exit_code,
        "launch_error": launch_error,
        "canonical_root": str(root),
        "automatic_deletion": False,
        "public_export": False,
    }
    write_receipt(receipt, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
