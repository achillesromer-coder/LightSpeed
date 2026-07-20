#!/usr/bin/env python3
"""Populate De Sporte's verified local state into LightSpeed Desktop exports.

This helper is intentionally local and bounded. It does not launch LightSpeed,
launch De Sporte, send cross-app commands, modify De Sporte source data, or touch
Web. It first runs the read-only De Sporte probe. It then either regenerates the
existing LightSpeed agent-home export through the current runtime configuration
or patches only the generated agent_population export when that is the only
available canonical export. Finally it reads the result through AgentHomeBridge
and writes a population receipt.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_SCRIPT = REPO_ROOT / "scripts" / "validate_desporte_desktop_bridge.py"
REPO_RUNTIME_ROOT = REPO_ROOT / "desktop" / "LightSpeed_Runtime"
REPO_SHELL_ROOT = REPO_ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def runtime_candidates() -> list[Path]:
    values: list[Path] = []
    override = os.environ.get("LIGHTSPEED_RUNTIME_ROOT")
    if override:
        values.append(Path(override))
    if os.name == "nt":
        values.append(Path(r"C:\LightSpeed_Consolidated\LightSpeed_Runtime"))
    values.extend([REPO_RUNTIME_ROOT, REPO_ROOT / "LightSpeed_Runtime"])
    unique: list[Path] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def select_runtime_root(explicit: Path | None = None) -> Path:
    candidates = [explicit] if explicit else runtime_candidates()
    for candidate in candidates:
        if candidate and (candidate / "lightspeed_runtime" / "__init__.py").is_file():
            return candidate
    rendered = ", ".join(str(item) for item in candidates if item)
    raise FileNotFoundError(f"No LightSpeed runtime package found. Checked: {rendered}")


def select_shell_root(explicit: Path | None = None) -> Path:
    if explicit:
        return explicit
    override = os.environ.get("LIGHTSPEED_SHELL_ROOT")
    if override:
        return Path(override)
    if os.name == "nt":
        canonical = Path(r"C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed")
        if canonical.is_dir():
            return canonical
    return REPO_SHELL_ROOT


def de_sporte_root() -> Path:
    return Path(os.environ.get("DESPORTE_ROOT") or os.environ.get("DE_SPORTE_ROOT") or r"D:\De Sporte")


def static_check() -> dict[str, Any]:
    required = [
        PROBE_SCRIPT,
        REPO_RUNTIME_ROOT / "lightspeed_runtime" / "runtime.py",
        REPO_RUNTIME_ROOT / "lightspeed_runtime" / "operator_home.py",
        REPO_RUNTIME_ROOT / "lightspeed_runtime" / "agent_home_bridge.py",
        REPO_RUNTIME_ROOT / "lightspeed_runtime" / "desktop_adapters.py",
        REPO_SHELL_ROOT / "config" / "deployment_topology.json",
        REPO_SHELL_ROOT / "config" / "launch_control.json",
    ]
    missing = [str(path.relative_to(REPO_ROOT)) for path in required if not path.is_file()]
    return {
        "mode": "static_check",
        "status": "pass" if not missing else "fail",
        "required_surface_count": len(required),
        "missing": missing,
    }


def run_probe(receipt_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(PROBE_SCRIPT),
            "--require-local",
            "--json-output",
            str(receipt_path),
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    if not receipt_path.is_file():
        raise RuntimeError("De Sporte probe did not produce a receipt")
    receipt = read_json(receipt_path)
    if completed.returncode or receipt.get("status") != "pass":
        raise RuntimeError("De Sporte local probe failed; review its JSON receipt")
    return receipt


def merged_agent_home_config(
    source: dict[str, Any],
    *,
    desporte: Path,
    shell_root: Path,
) -> dict[str, Any]:
    config = dict(source)
    population = dict(config.get("agent_population") or {})
    resident_host = dict(population.get("resident_host_application") or {})
    resident_host.update(
        {
            "label": "De Sporte",
            "role": "sibling_soft_launch_app",
            "path": str(desporte),
            "runtime_state": "local_probe_passed",
            "population_policy": "read_only_receipt_backed",
        }
    )
    population["resident_host_application"] = resident_host
    config["agent_population"] = population

    launch = dict(config.get("launch_control") or {})
    launch.update(
        {
            "state": "sandbox_local_probe_passed",
            "current_focus": "desporte_desktop_population",
        }
    )
    co_runner = dict(launch.get("co_runner") or {})
    co_runner.update(
        {
            "host_application": "De Sporte",
            "root_path": str(desporte),
            "state": "local_probe_passed",
            "execution_policy": "probe_read_only_then_receipt_backed_local_sync",
            "web_frontend_in_scope": False,
        }
    )
    launch["co_runner"] = co_runner
    config["launch_control"] = launch

    environment = dict(config.get("environment") or {})
    environment.setdefault("desktop_shell_root", str(shell_root))
    config["environment"] = environment
    return config


def regenerate_from_config(
    *,
    runtime_root: Path,
    shell_root: Path,
    export_dir: Path,
    desporte: Path,
) -> dict[str, Any] | None:
    config_path = runtime_root / "config" / "agent_home.json"
    if not config_path.is_file():
        return None

    config = merged_agent_home_config(read_json(config_path), desporte=desporte, shell_root=shell_root)
    export_dir.mkdir(parents=True, exist_ok=True)
    overlay_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            prefix="desporte_agent_home_",
            dir=export_dir,
            encoding="utf-8",
            delete=False,
        ) as handle:
            json.dump(config, handle, indent=2, sort_keys=True)
            handle.write("\n")
            overlay_path = Path(handle.name)

        sys.path.insert(0, str(runtime_root))
        from lightspeed_runtime.operator_home import export_agent_environment
        from lightspeed_runtime.runtime import LightSpeedRuntime

        runtime = LightSpeedRuntime(runtime_root)
        return export_agent_environment(
            runtime,
            export_dir,
            config_path=overlay_path,
            max_assets_per_source=5,
        )
    finally:
        if overlay_path and overlay_path.exists():
            overlay_path.unlink()


def patch_existing_population(*, export_dir: Path, desporte: Path) -> dict[str, Any]:
    path = export_dir / "agent_population.json"
    if not path.is_file():
        raise FileNotFoundError(
            "No runtime config or existing agent_population export is available; "
            "run the canonical LightSpeed agent-home export once before population."
        )
    payload = read_json(path)
    population = merged_agent_home_config(
        {"agent_population": payload},
        desporte=desporte,
        shell_root=select_shell_root(),
    )["agent_population"]
    write_json(path, population)
    return {"mode": "patched_existing_agent_population", "path": str(path)}


def build_population_receipt(
    *,
    runtime_root: Path,
    export_dir: Path,
    probe: dict[str, Any],
    export_result: dict[str, Any],
) -> dict[str, Any]:
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))
    from lightspeed_runtime.agent_home_bridge import AgentHomeBridge

    summary = AgentHomeBridge(export_dir).summary()
    desporte_summary = summary.get("de_sporte_runtime") or {}
    checks = {
        "root_exists": bool(desporte_summary.get("root_exists")),
        "config_exists": bool(desporte_summary.get("config_exists")),
        "data_exists": bool(desporte_summary.get("data_exists")),
        "bridge_functional": desporte_summary.get("bridge_functional") is True,
        "desktop_summary_present": bool(desporte_summary),
    }
    required = ("root_exists", "config_exists", "data_exists", "desktop_summary_present")
    passed = all(checks[key] for key in required)
    return {
        "receipt_id": "desporte_desktop_population_2026_07_20",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "pass" if passed else "review_required",
        "runtime_root": str(runtime_root),
        "export_dir": str(export_dir),
        "probe_receipt_id": probe.get("receipt_id"),
        "probe_status": probe.get("status"),
        "export_result": export_result,
        "checks": checks,
        "de_sporte_runtime": desporte_summary,
        "web_frontend_in_scope": False,
        "next_action": (
            "Open LightSpeed Desktop and visually verify the De Sporte runtime panel."
            if passed
            else "Review missing De Sporte Config/Data or bridge state before Desktop acceptance."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--shell-root", type=Path)
    parser.add_argument("--static-check", action="store_true")
    args = parser.parse_args()

    if args.static_check:
        result = static_check()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] == "pass" else 1

    runtime_root = select_runtime_root(args.runtime_root)
    shell_root = select_shell_root(args.shell_root)
    export_dir = runtime_root / "exports" / "agent_home"
    probe_path = export_dir / "desporte_soft_launch_receipt.json"
    population_path = export_dir / "desporte_desktop_population_receipt.json"
    desporte = de_sporte_root()

    probe = run_probe(probe_path)
    export_result = regenerate_from_config(
        runtime_root=runtime_root,
        shell_root=shell_root,
        export_dir=export_dir,
        desporte=desporte,
    )
    if export_result is None:
        export_result = patch_existing_population(export_dir=export_dir, desporte=desporte)

    receipt = build_population_receipt(
        runtime_root=runtime_root,
        export_dir=export_dir,
        probe=probe,
        export_result=export_result,
    )
    write_json(population_path, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
