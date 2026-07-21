#!/usr/bin/env python3
"""Run the bounded Merovingian soft-launch supervisor.

Normal mode initializes the essential database/event/storage runtime, inventories
project roots, records cleanup evidence, prepares Drive/GO review receipts and
writes a health receipt. Watch mode uses a single-instance lock and heartbeat.
The runner never deletes, publishes, launches Web or mutates workbooks.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import errno
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_RUNTIME_ROOT = REPO_ROOT / "desktop" / "LightSpeed_Runtime"
REPO_SHELL_ROOT = REPO_ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed"


def _runtime_candidates(explicit: Path | None = None) -> list[Path]:
    rows: list[Path] = []
    if explicit:
        rows.append(explicit)
    configured = os.environ.get("LIGHTSPEED_RUNTIME_ROOT")
    if configured:
        rows.append(Path(configured))
    if os.name == "nt":
        rows.append(Path(r"D:\LightSpeed_Consolidated\LightSpeed_Runtime"))
        rows.append(Path(r"C:\LightSpeed_Consolidated\LightSpeed_Runtime"))
    rows.append(REPO_RUNTIME_ROOT)
    return list(dict.fromkeys(rows))


def _shell_candidates(explicit: Path | None = None) -> list[Path]:
    rows: list[Path] = []
    if explicit:
        rows.append(explicit)
    configured = os.environ.get("LIGHTSPEED_SHELL_ROOT")
    if configured:
        rows.append(Path(configured))
    if os.name == "nt":
        rows.append(Path(r"D:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed"))
        rows.append(Path(r"C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed"))
    rows.append(REPO_SHELL_ROOT)
    return list(dict.fromkeys(rows))


def _select(candidates: list[Path], marker: Path, label: str) -> Path:
    for candidate in candidates:
        if (candidate / marker).is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"No {label} root found. Checked: {', '.join(str(item) for item in candidates)}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _read_pid(lock_path: Path) -> int | None:
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        return int(payload.get("pid")) if isinstance(payload, dict) and payload.get("pid") else None
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def _pid_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    if pid == os.getpid():
        return True
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
    except OSError as exc:
        return exc.errno == errno.EPERM
    return True


def _acquire_lock(lock_path: Path, *, interval: int) -> None:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    for _attempt in range(2):
        try:
            descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            existing_pid = _read_pid(lock_path)
            if _pid_alive(existing_pid):
                raise RuntimeError(f"Merovingian supervisor is already running as PID {existing_pid}")
            try:
                lock_path.unlink()
            except OSError as exc:
                raise RuntimeError(f"Stale supervisor lock could not be removed: {exc}") from exc
            continue
        payload = {
            "schema_version": "lightspeed-merovingian-supervisor-lock-v1",
            "pid": os.getpid(),
            "started_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "heartbeat_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "interval_seconds": interval,
        }
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
        return
    raise RuntimeError("Could not acquire Merovingian supervisor lock")


def _heartbeat(lock_path: Path, *, interval: int, state: str) -> None:
    _write_json(lock_path, {
        "schema_version": "lightspeed-merovingian-supervisor-lock-v1",
        "pid": os.getpid(),
        "heartbeat_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "interval_seconds": interval,
        "state": state,
    })


def static_check(runtime_root: Path, shell_root: Path) -> dict[str, Any]:
    required = [
        runtime_root / "lightspeed_runtime" / "project_pipeline.py",
        runtime_root / "lightspeed_runtime" / "ls_go_bridge.py",
        shell_root / "config" / "project_routing.json",
        shell_root / "Z Axis" / "Z-4_Merovingian" / "core" / "__init__.py",
        shell_root / "Z Axis" / "Z-4_Merovingian" / "core" / "services" / "__init__.py",
        shell_root / "Z Axis" / "Z-4_Merovingian" / "core" / "services" / "database.py",
        shell_root / "Z Axis" / "Z-4_Merovingian" / "core" / "services" / "event_bus.py",
        shell_root / "Z Axis" / "Z-4_Merovingian" / "core" / "services" / "storage.py",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    return {
        "schema_version": "lightspeed-merovingian-static-check-v1",
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "pass" if not missing else "fail",
        "runtime_root": str(runtime_root),
        "shell_root": str(shell_root),
        "required_surface_count": len(required),
        "missing": missing,
        "web_frontend_in_scope": False,
        "automatic_deletion": False,
    }


def run_once(runtime_root: Path, shell_root: Path, *, queue_changes: bool) -> dict[str, Any]:
    for path in (runtime_root, shell_root):
        value = str(path)
        while value in sys.path:
            sys.path.remove(value)
        sys.path.insert(0, value)

    from lightspeed_runtime.project_pipeline import ProjectPipeline

    pipeline = ProjectPipeline(shell_root)
    registry = pipeline.refresh(force=True, queue_changes=queue_changes)
    health = registry.get("health") or {}
    receipt = {
        "schema_version": "lightspeed-merovingian-soft-launch-v1",
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "pass" if health.get("status") == "pass" else "degraded",
        "runtime_root": str(runtime_root),
        "shell_root": str(shell_root),
        "services": health.get("services") or {},
        "project_summary": registry.get("summary") or {},
        "cleanup_summary": registry.get("cleanup_summary") or {},
        "changes": registry.get("changes") or {},
        "review_packet": registry.get("review_packet"),
        "health_receipt": str(pipeline.health_path),
        "project_registry": str(pipeline.registry_path),
        "cleanup_candidates": str(pipeline.cleanup_path),
        "review_queue": str(pipeline.review_queue_path),
        "drive_writeback": (health.get("details") or {}).get("drive_writeback"),
        "automatic_deletion": False,
        "web_frontend_in_scope": False,
        "next_action": (
            "Review pending project packets in LS GO and keep cleanup candidates evidence-gated."
            if health.get("status") == "pass"
            else "Resolve the reported essential service or root-path fault before broader execution."
        ),
    }
    receipt_path = pipeline.runtime_exports / "merovingian_soft_launch_receipt.json"
    _write_json(receipt_path, receipt)
    return {**receipt, "receipt_path": str(receipt_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--shell-root", type=Path)
    parser.add_argument("--static-check", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--no-queue-changes", action="store_true")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    runtime_root = _select(_runtime_candidates(args.runtime_root), Path("lightspeed_runtime") / "__init__.py", "LightSpeed Runtime")
    shell_root = _select(_shell_candidates(args.shell_root), Path("N.py"), "LightSpeed Desktop shell")

    if args.static_check:
        payload = static_check(runtime_root, shell_root)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["status"] == "pass" else 1

    interval = max(30, min(int(args.interval), 3600))
    lock_path = shell_root / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports" / "merovingian_supervisor.lock.json"
    if args.watch:
        _acquire_lock(lock_path, interval=interval)

    try:
        while True:
            if args.watch:
                _heartbeat(lock_path, interval=interval, state="scanning")
            payload = run_once(runtime_root, shell_root, queue_changes=not args.no_queue_changes)
            rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
            print(rendered, end="")
            if args.json_output:
                _write_json(args.json_output, payload)
            if not args.watch:
                return 0 if payload["status"] == "pass" else 2
            _heartbeat(lock_path, interval=interval, state=payload["status"])
            time.sleep(interval)
    finally:
        if args.watch:
            try:
                if _read_pid(lock_path) == os.getpid():
                    lock_path.unlink()
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
