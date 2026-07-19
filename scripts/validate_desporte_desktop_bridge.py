#!/usr/bin/env python3
"""Validate the De Sporte -> LightSpeed Desktop bridge without launching either app.

The default mode is CI-safe and validates committed control contracts only. On the
Windows host, pass --require-local to inspect the De Sporte root and expected
read-only population files. The script never starts a process, edits De Sporte,
or performs cross-application execution.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path, PureWindowsPath
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed" / "config"
TOPOLOGY_PATH = CONFIG_ROOT / "deployment_topology.json"
LAUNCH_CONTROL_PATH = CONFIG_ROOT / "launch_control.json"
AGENT_HOME_BRIDGE = (
    ROOT
    / "desktop"
    / "LightSpeed_Runtime"
    / "lightspeed_runtime"
    / "agent_home_bridge.py"
)
DESKTOP_ADAPTERS = (
    ROOT
    / "desktop"
    / "LightSpeed_Runtime"
    / "lightspeed_runtime"
    / "desktop_adapters.py"
)

EXPECTED_RELATIVE_FILES = {
    "persona_runtime": Path("Config/persona_model_runtime.json"),
    "resident_registry": Path("Config/resident_registry.json"),
    "overview_sync": Path("Data/Overseer/overview_sync.json"),
    "phone_dashboard": Path("Data/Overseer/phone_dashboard_payload.json"),
    "world_shell": Path("Data/World/world_shell_state.json"),
    "launch_handoff": Path("Data/Overseer/lightspeed_launch_handoff.json"),
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def clean_windows_path(value: str) -> str:
    return value.strip().rstrip("`'\"").strip()


def topology_desporte_root(topology: dict[str, Any]) -> str | None:
    for item in topology.get("authoritative_roots") or []:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").lower()
        role = str(item.get("role") or "").lower()
        if label == "de sporte" or role == "sibling_soft_launch_app":
            value = item.get("path")
            return clean_windows_path(value) if isinstance(value, str) else None
    return None


def resolve_local_root(configured: str | None) -> Path | None:
    override = os.environ.get("DESPORTE_ROOT") or os.environ.get("DE_SPORTE_ROOT")
    value = clean_windows_path(override or configured or "")
    if not value:
        return None
    if os.name == "nt":
        return Path(value)
    # A Windows path cannot be meaningfully probed by a Linux CI runner.
    if PureWindowsPath(value).drive:
        return None
    return Path(value)


def read_optional_json(path: Path) -> dict[str, Any]:
    try:
        return load_json(path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
        return {}


def build_receipt(*, require_local: bool) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for path in (TOPOLOGY_PATH, LAUNCH_CONTROL_PATH, AGENT_HOME_BRIDGE, DESKTOP_ADAPTERS):
        if not path.is_file():
            errors.append(f"Missing required bridge surface: {path.relative_to(ROOT)}")

    if errors:
        return {}, errors, warnings

    topology = load_json(TOPOLOGY_PATH)
    launch = load_json(LAUNCH_CONTROL_PATH)
    configured_root = topology_desporte_root(topology)
    if not configured_root:
        errors.append("Deployment topology has no De Sporte authoritative root")
    elif configured_root != clean_windows_path(configured_root):
        errors.append("De Sporte root contains trailing quote/backtick corruption")

    co_runner = launch.get("co_runner") if isinstance(launch.get("co_runner"), dict) else {}
    co_runner_root = co_runner.get("root_path")
    if not isinstance(co_runner_root, str) or not co_runner_root:
        errors.append("Launch control co_runner.root_path is missing")
    elif configured_root and clean_windows_path(co_runner_root) != configured_root:
        errors.append(
            "Launch control and deployment topology disagree on De Sporte root: "
            f"{co_runner_root!r} != {configured_root!r}"
        )

    launch_state = str(launch.get("state") or "")
    co_runner_state = str(co_runner.get("state") or "")
    if "held" in launch_state.lower() or "held" in co_runner_state.lower():
        errors.append("De Sporte remains globally held instead of bounded sandbox diagnostics")
    if co_runner.get("web_frontend_in_scope") is not False:
        errors.append("De Sporte soft launch must keep Web frontend out of scope")
    if co_runner.get("execution_policy") != "probe_read_only_then_receipt_backed_local_sync":
        errors.append("Unexpected De Sporte execution policy")

    bridge_text = AGENT_HOME_BRIDGE.read_text(encoding="utf-8")
    adapter_text = DESKTOP_ADAPTERS.read_text(encoding="utf-8")
    if "def de_sporte_runtime_summary" not in bridge_text:
        errors.append("AgentHomeBridge does not expose de_sporte_runtime_summary")
    if '"de_sporte_runtime": self.de_sporte_runtime_summary()' not in bridge_text:
        errors.append("AgentHomeBridge summary does not populate De Sporte")
    if "def format_de_sporte_runtime_focus" not in adapter_text:
        errors.append("Desktop adapters do not render the De Sporte runtime summary")

    local_root = resolve_local_root(configured_root)
    file_states: dict[str, dict[str, Any]] = {}
    root_exists: bool | None = None
    if local_root is None:
        if require_local:
            errors.append(
                "Local De Sporte root is not probeable. Run on Windows or set DESPORTE_ROOT."
            )
        else:
            warnings.append("Local De Sporte root not probed on this host")
    else:
        root_exists = local_root.is_dir()
        if require_local and not root_exists:
            errors.append(f"De Sporte root does not exist: {local_root}")
        for key, relative in EXPECTED_RELATIVE_FILES.items():
            target = local_root / relative
            payload = read_optional_json(target) if target.is_file() else {}
            file_states[key] = {
                "path": str(target),
                "exists": target.is_file(),
                "json_object": bool(payload),
                "bytes": target.stat().st_size if target.is_file() else 0,
            }
        essential = ("persona_runtime", "resident_registry", "overview_sync", "world_shell")
        missing_essential = [key for key in essential if not file_states[key]["exists"]]
        if require_local and missing_essential:
            errors.append("Missing essential De Sporte population files: " + ", ".join(missing_essential))

    receipt = {
        "receipt_id": "desporte_desktop_soft_launch_probe_2026_07_20",
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": "local_required" if require_local else "static_contract",
        "configured_root": configured_root,
        "local_root": str(local_root) if local_root is not None else None,
        "root_exists": root_exists,
        "launch_state": launch_state,
        "co_runner_state": co_runner_state,
        "desktop_population_surface": "AgentHomeBridge.de_sporte_runtime_summary",
        "desktop_render_surface": "desktop_adapters.format_de_sporte_runtime_focus",
        "web_frontend_in_scope": False,
        "file_states": file_states,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "warnings": warnings,
        "next_action": (
            "regenerate LightSpeed agent-home exports and verify the Desktop De Sporte panel"
            if require_local and not errors
            else "run this diagnostic on the canonical Windows host with --require-local"
        ),
    }
    return receipt, errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-local", action="store_true")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    receipt, errors, warnings = build_receipt(require_local=args.require_local)
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
