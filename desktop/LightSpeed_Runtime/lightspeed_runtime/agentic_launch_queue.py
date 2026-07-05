from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
import argparse
import json
from pathlib import Path
from typing import Any


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = RUNTIME_ROOT / "exports" / "agent_home"
SHELL_ROOT = RUNTIME_ROOT.parent / "Desktop_Hooks" / "LightSpeed"
SMITH_STAGING = SHELL_ROOT / "Z Axis" / "Z-3_Smith" / "data" / "staging"
NEO_OUTPUTS = SHELL_ROOT / "Z Axis" / "Z+2_Neo" / "data" / "temp_shells"

FLOOR_ORDER = [
    "Merovingian",
    "Trinity",
    "Neo",
    "Smith",
    "Oracle",
    "Morpheus",
    "Architect",
    "TheConstruct",
]

PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def build_queue(export_dir: Path = EXPORT_DIR) -> dict[str, Any]:
    wakeup = load_json(export_dir / "local_agent_wakeup_contract.json", {})
    spaces = load_json(export_dir / "smart_floor_spaces.json", {})
    gated = load_json(export_dir / "gated_build_tasks.json", {})
    realization = load_json(export_dir / "floor_environment_realization_contract.json", {})
    host = load_json(export_dir / "host_runtime_policy.json", {})

    wake_by_floor = {
        str(item.get("floor")): item
        for item in wakeup.get("floors") or []
        if item.get("floor")
    }
    space_by_floor = {
        str(item.get("floor")): item
        for item in spaces.get("spaces") or []
        if item.get("floor")
    }
    realization_by_floor = {
        str(item.get("floor")): item
        for item in realization.get("floors") or []
        if item.get("floor")
    }

    tasks: list[dict[str, Any]] = []
    for order, floor_name in enumerate(FLOOR_ORDER, start=1):
        wake = wake_by_floor.get(floor_name) or {}
        conn = wake.get("ollama_connection") or {}
        activation = wake.get("activation") or {}
        draw = wake.get("assimilation_draw") or {}
        space = space_by_floor.get(floor_name) or {}
        real = realization_by_floor.get(floor_name) or {}
        heavy_manual = _is_heavy_or_manual(wake)
        tasks.append(
            {
                "task_id": f"floor_wakeup_{_safe_id(floor_name)}",
                "task_type": "floor_wakeup_receipt",
                "owner_floor": floor_name,
                "priority": "high" if floor_name in {"Trinity", "Neo", "Smith", "Merovingian"} else "medium",
                "state": "ready_no_risk_seed",
                "risk_level": "low" if not heavy_manual else "manual_heavy",
                "queue_lane": "local_ollama_floor_wakeup",
                "space_id": space.get("space_id"),
                "space_label": space.get("label"),
                "default_view": space.get("default_view"),
                "model": conn.get("model"),
                "endpoint": conn.get("endpoint") or (wakeup.get("ollama") or {}).get("endpoint"),
                "activation_mode": activation.get("mode"),
                "manual_heavy": heavy_manual,
                "safe_command": _runner_command(floor_name, execute=False),
                "execute_command": _runner_command(floor_name, execute=True) if not heavy_manual else None,
                "write_scope": _write_scope(floor_name),
                "source_draw_count": len(draw.get("priority_paths") or []),
                "goal": "Generate one bounded local wake-up receipt for this floor before any code, data, or UI mutation.",
                "done_when": [
                    "receipt is written to Neo or the owner floor",
                    "floor reports role, model, write scope, and one next safe action",
                    "no source files, Drive, repo, or web surfaces are changed",
                ],
                "next_safe_action": _next_safe_action(real, wake),
            }
        )

    for gated_task in gated.get("tasks") or []:
        if not isinstance(gated_task, dict):
            continue
        floor_name = str(gated_task.get("owner_floor") or "Smith")
        wake = wake_by_floor.get(floor_name) or {}
        conn = wake.get("ollama_connection") or {}
        space = space_by_floor.get(floor_name) or {}
        tasks.append(
            {
                "task_id": f"gated_{gated_task.get('task_id')}",
                "source_task_id": gated_task.get("task_id"),
                "task_type": "gated_floor_buildout",
                "owner_floor": floor_name,
                "priority": gated_task.get("priority") or "medium",
                "state": gated_task.get("state") or "ready_no_risk_seed",
                "risk_level": gated_task.get("risk_level") or "low",
                "queue_lane": gated_task.get("lane_id") or "queue_and_execution",
                "space_id": space.get("space_id"),
                "space_label": space.get("label"),
                "model": conn.get("model"),
                "endpoint": conn.get("endpoint") or (wakeup.get("ollama") or {}).get("endpoint"),
                "manual_heavy": _is_heavy_or_manual(wake),
                "write_scope": _write_scope(floor_name),
                "goal": gated_task.get("goal"),
                "done_when": gated_task.get("done_when") or [],
                "next_safe_action": "Route through Smith with manual yes/no approval before source mutation.",
            }
        )

    tasks.sort(key=lambda item: (PRIORITY_RANK.get(str(item.get("priority")), 9), FLOOR_ORDER.index(item["owner_floor"]) if item.get("owner_floor") in FLOOR_ORDER else 99, str(item.get("task_id"))))
    generated_at = datetime.now(UTC).isoformat()
    mirrors = {
        "runtime_export": str(export_dir / "agentic_launch_queue.json"),
        "desktop_config": str(SHELL_ROOT / "config" / "agentic_launch_queue.json"),
        "smith_staging": str(SMITH_STAGING / "agentic_launch_queue.json"),
        "neo_temp_shells": str(NEO_OUTPUTS / "agentic_launch_queue.json"),
    }
    payload = {
        "queue_id": "lightspeed_agentic_launch_queue_2026_06_22",
        "generated_at": generated_at,
        "state": "ready_no_risk_seed",
        "purpose": "Single no-risk launch queue for local Ollama smart floors, floor spaces, compaction, and gated desktop buildout.",
        "source_contracts": {
            "local_agent_wakeup": str(export_dir / "local_agent_wakeup_contract.json"),
            "smart_floor_spaces": str(export_dir / "smart_floor_spaces.json"),
            "gated_build_tasks": str(export_dir / "gated_build_tasks.json"),
            "floor_environment_realization": str(export_dir / "floor_environment_realization_contract.json"),
            "host_runtime_policy": str(export_dir / "host_runtime_policy.json"),
        },
        "policy": {
            "local_only": True,
            "max_concurrent_ollama_sessions": _max_ollama_sessions(host, wakeup),
            "active_runner_lock": str(RUNTIME_ROOT / "reports" / "local_floor_runner.active.lock"),
            "recursive_ingest_enabled": False,
            "mass_data_copy_enabled": False,
            "external_publish_blocked": True,
            "manual_approval_required_for": [
                "source file mutation",
                "heavy model execution",
                "Drive writeback",
                "Git push",
                "web publish",
                "bulk import from D:\\To be assimilated",
            ],
            "resource_guard": "one floor receipt at a time; keep Chrome responsive; do not install dependencies on D: while free space is below 2 GB",
        },
        "mirrors": mirrors,
        "summary": _summary(tasks),
        "tasks": tasks,
    }
    return payload


def write_queue(payload: dict[str, Any]) -> list[Path]:
    mirror_paths = [Path(str(path)) for path in (payload.get("mirrors") or {}).values()]
    for path in mirror_paths:
        write_json(path, payload)
    return mirror_paths


def _summary(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    by_floor = Counter(str(item.get("owner_floor") or "unknown") for item in tasks)
    by_state = Counter(str(item.get("state") or "unknown") for item in tasks)
    by_priority = Counter(str(item.get("priority") or "unknown") for item in tasks)
    by_type = Counter(str(item.get("task_type") or "unknown") for item in tasks)
    return {
        "task_count": len(tasks),
        "ready_count": sum(1 for item in tasks if str(item.get("state") or "").startswith("ready")),
        "manual_heavy_count": sum(1 for item in tasks if item.get("manual_heavy")),
        "floor_count": len(by_floor),
        "by_floor": dict(sorted(by_floor.items())),
        "by_state": dict(sorted(by_state.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "by_type": dict(sorted(by_type.items())),
    }


def _runtime_limit(host: dict[str, Any], key: str, default: int) -> int:
    limits = host.get("runtime_limits") if isinstance(host.get("runtime_limits"), dict) else {}
    try:
        return int(limits.get(key, default))
    except Exception:
        return default


def _max_ollama_sessions(host: dict[str, Any], wakeup: dict[str, Any]) -> int:
    host_limit = _runtime_limit(host, "max_concurrent_ollama_jobs", 1)
    wake_policy = wakeup.get("policy") if isinstance(wakeup.get("policy"), dict) else {}
    try:
        wake_limit = int(wake_policy.get("max_concurrent_ollama_sessions", 1))
    except Exception:
        wake_limit = 1
    return max(1, min(host_limit, wake_limit))


def _safe_id(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")


def _is_heavy_or_manual(wake: dict[str, Any]) -> bool:
    activation = str((wake.get("activation") or {}).get("mode") or "")
    conn = wake.get("ollama_connection") or {}
    model = str(conn.get("model") or "").lower()
    load_policy = str(conn.get("load_policy") or "").lower()
    return (
        activation == "manual_heavy"
        or "manual_heavy" in load_policy
        or any(marker in model for marker in ("27b", "70b", "120b", "405b", "671b", "cloud"))
    )


def _runner_command(floor: str, *, execute: bool) -> str:
    python_exe = RUNTIME_ROOT.parent / "venv" / "Scripts" / "python.exe"
    runner = RUNTIME_ROOT / "lightspeed_runtime" / "local_floor_runner.py"
    parts = [str(python_exe), str(runner), "--floor", floor, "--receipt-target", "neo", "--num-predict", "320"]
    if execute:
        parts.append("--execute")
    return " ".join(f'"{part}"' if " " in part else part for part in parts)


def _write_scope(floor: str) -> list[str]:
    return [
        str(SHELL_ROOT / "Z Axis" / _floor_dir(floor) / "data"),
        str(SHELL_ROOT / "Z Axis" / _floor_dir(floor) / "Z Direct"),
        str(RUNTIME_ROOT / "reports"),
    ]


def _floor_dir(floor: str) -> str:
    mapping = {
        "Merovingian": "Z-4_Merovingian",
        "Smith": "Z-3_Smith",
        "Oracle": "Z-2_Oracle",
        "Morpheus": "Z-1_Morpheus",
        "TheConstruct": "Z0_TheConstruct",
        "Architect": "Z+1_Architect",
        "Neo": "Z+2_Neo",
        "Trinity": "Z+3_Trinity",
    }
    return mapping.get(floor, floor)


def _next_safe_action(realization: dict[str, Any], wake: dict[str, Any]) -> str:
    post_population = realization.get("post_population") if isinstance(realization.get("post_population"), dict) else {}
    return (
        str(wake.get("next_safe_action") or "")
        or str(post_population.get("next_safe_action") or "")
        or "Create a dry-run receipt, then wait for manual approval before mutation."
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the local LightSpeed agentic launch queue.")
    parser.add_argument("--export-dir", type=Path, default=EXPORT_DIR)
    parser.add_argument("--write", action="store_true", help="Write runtime/config/Smith/Neo queue mirrors.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    payload = build_queue(args.export_dir)
    if args.write:
        paths = write_queue(payload)
    else:
        paths = []
    print(json.dumps({"summary": payload["summary"], "written": [str(path) for path in paths]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
