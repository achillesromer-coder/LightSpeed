#!/usr/bin/env python3
"""Run the bounded Merovingian soft-launch supervisor.

Normal mode initializes the essential database/event/storage runtime, inventories
canonical and legacy project roots, records cleanup evidence, prepares Drive/GO
review receipts and writes a health receipt. Watch mode refreshes at a bounded
interval. The runner never deletes, publishes, launches Web or mutates workbooks.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
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
        rows.append(Path(r"C:\LightSpeed_Consolidated\LightSpeed_Runtime"))
    rows.append(REPO_RUNTIME_ROOT)
    unique: list[Path] = []
    for row in rows:
        if row not in unique:
            unique.append(row)
    return unique


def _shell_candidates(explicit: Path | None = None) -> list[Path]:
    rows: list[Path] = []
    if explicit:
        rows.append(explicit)
    configured = os.environ.get("LIGHTSPEED_SHELL_ROOT")
    if configured:
        rows.append(Path(configured))
    if os.name == "nt":
        rows.append(Path(r"C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed"))
    rows.append(REPO_SHELL_ROOT)
    unique: list[Path] = []
    for row in rows:
        if row not in unique:
            unique.append(row)
    return unique


def _select(candidates: list[Path], marker: Path, label: str) -> Path:
    for candidate in candidates:
        if (candidate / marker).is_file():
            return candidate.resolve()
    checked = ", ".join(str(item) for item in candidates)
    raise FileNotFoundError(f"No {label} root found. Checked: {checked}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))
    if str(shell_root) not in sys.path:
        sys.path.insert(0, str(shell_root))

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
    receipt["receipt_path"] = str(receipt_path)
    return receipt


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

    runtime_root = _select(
        _runtime_candidates(args.runtime_root),
        Path("lightspeed_runtime") / "__init__.py",
        "LightSpeed Runtime",
    )
    shell_root = _select(
        _shell_candidates(args.shell_root),
        Path("N.py"),
        "LightSpeed Desktop shell",
    )

    if args.static_check:
        payload = static_check(runtime_root, shell_root)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["status"] == "pass" else 1

    interval = max(30, min(int(args.interval), 3600))
    while True:
        payload = run_once(
            runtime_root,
            shell_root,
            queue_changes=not args.no_queue_changes,
        )
        rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        print(rendered, end="")
        if args.json_output:
            _write_json(args.json_output, payload)
        if not args.watch:
            return 0 if payload["status"] == "pass" else 2
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
