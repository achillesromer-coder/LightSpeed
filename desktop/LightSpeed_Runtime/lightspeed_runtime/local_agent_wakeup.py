from __future__ import annotations

from collections import Counter, deque
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


CONTRACT_ID = "lightspeed_local_agent_wakeup_2026_05_29"
DEFAULT_MAX_SCAN_ENTRIES = 3000
SKIP_DIR_NAMES = {
    ".git",
    ".idea",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}

FLOOR_DIRS = {
    "Trinity": Path("Z Axis") / "Z+3_Trinity",
    "Neo": Path("Z Axis") / "Z+2_Neo",
    "Architect": Path("Z Axis") / "Z+1_Architect",
    "TheConstruct": Path("Z Axis") / "Z0_TheConstruct",
    "Morpheus": Path("Z Axis") / "Z-1_Morpheus",
    "Oracle": Path("Z Axis") / "Z-2_Oracle",
    "Smith": Path("Z Axis") / "Z-3_Smith",
    "Merovingian": Path("Z Axis") / "Z-4_Merovingian",
}

DEFAULT_FLOOR_ORDER = [
    "Merovingian",
    "Trinity",
    "Neo",
    "Smith",
    "Oracle",
    "Morpheus",
    "Architect",
    "TheConstruct",
]

FLOOR_DIRECTIVES = {
    "Merovingian": {
        "wake_goal": "Confirm health, ledger, process, and recovery state before any floor works.",
        "assimilation_role": "Record receipts, hashes, scan limits, failures, and system pressure evidence.",
        "draw_priority": ["logs", "data", "inventory reports", "runtime configs"],
    },
    "Trinity": {
        "wake_goal": "Keep the user surface readable and make N.py the single function centre.",
        "assimilation_role": "Collapse UI PDFs, N variants, and duplicate portal patterns into one bento/floor rail.",
        "draw_priority": ["LightSpeed UI.pdf", "N_updated.py", "COMPLETE_IMPLEMENTATION_GUIDE.md"],
    },
    "Neo": {
        "wake_goal": "Coordinate bounded local Ollama prompts through temp shells only.",
        "assimilation_role": "Stage local-agent task prompts and handoffs without permanent promotion.",
        "draw_priority": ["Ollama Responder.py", "N_updated.py", "GPT Export.16.11.2025"],
    },
    "Smith": {
        "wake_goal": "Route low-risk execution tasks and prevent uncontrolled expansion.",
        "assimilation_role": "Convert scripts, support packs, app folders, and inventories into queued receipts.",
        "draw_priority": ["LIGHTSPEED_ORGANIZE_FILES_*.ps1", "comprehensive_file_discovery.py", "Apps"],
    },
    "Oracle": {
        "wake_goal": "Attach sources and build provenance-first source tables.",
        "assimilation_role": "Index documents, inventories, PDFs, and archives as source receipts, not loose copies.",
        "draw_priority": ["2026 Documents", "LIGHTSPEED_FILE_INVENTORY_*.json", "NoteBookLM-*.zip"],
    },
    "Morpheus": {
        "wake_goal": "Review overlap, duplicates, contradictions, and promotion candidates.",
        "assimilation_role": "Compare guides, reports, and exports for same-function/different-tab duplication.",
        "draw_priority": ["PHASE_1_COMPLETE_ANALYSIS_AND_ROADMAP.md", "WEEK_1_IMMEDIATE_ACTION_GUIDE.md"],
    },
    "Architect": {
        "wake_goal": "Hold the build plan, approval gates, and release shape.",
        "assimilation_role": "Turn architecture, roadmap, launch, and support packs into gated implementation tasks.",
        "draw_priority": ["SYSTEM_ARCHITECTURE_FLOWCHART.md", "COMPLETE_IMPLEMENTATION_GUIDE.md"],
    },
    "TheConstruct": {
        "wake_goal": "Prepare proofed data spaces and render/simulation lanes without heavy auto-launch.",
        "assimilation_role": "Route blueprints, PDFs, empirical packs, and visual support packs to proofed datasets.",
        "draw_priority": ["LightSpeed UI.pdf", "mark_iii_vertebra_orthographic_blueprint.pdf", "IGP Return Tables.pdf"],
    },
}


def default_assimilation_source_root(root: Path) -> Path:
    return Path(root.anchor) / "To be assimilated"


def default_shell_root(root: Path) -> Path:
    return Path(root).parent / "Desktop_Hooks" / "LightSpeed"


def default_export_path(root: Path) -> Path:
    return Path(root) / "exports" / "agent_home" / "local_agent_wakeup_contract.json"


def default_shell_mirror_path(root: Path) -> Path:
    return default_shell_root(root) / "config" / "local_agent_wakeup_contract.json"


def build_local_agent_wakeup_contract(
    root: Path,
    *,
    source_root: Path | None = None,
    shell_root: Path | None = None,
    realization_contract: dict[str, Any] | None = None,
    neo_local_runtime: dict[str, Any] | None = None,
    max_scan_entries: int = DEFAULT_MAX_SCAN_ENTRIES,
    probe_ollama: bool = True,
) -> dict[str, Any]:
    root = Path(root)
    source_root = Path(source_root) if source_root else default_assimilation_source_root(root)
    shell_root = Path(shell_root) if shell_root else default_shell_root(root)
    realization_contract = realization_contract or _read_json(shell_root / "config" / "floor_environment_realization_contract.json")
    neo_local_runtime = neo_local_runtime or _read_json(shell_root / "config" / "neo_local_runtime.json")

    endpoint = (neo_local_runtime.get("endpoint_policy") or {}).get("base_url") or "http://localhost:11434"
    installed_models = _probe_ollama_models(endpoint) if probe_ollama else []
    if not installed_models:
        installed_models = [str(item) for item in neo_local_runtime.get("available_models") or [] if item]

    source_inventory = build_assimilation_source_inventory(source_root, max_entries=max_scan_entries)
    floors = _build_floor_wakeup_rows(
        root=root,
        shell_root=shell_root,
        source_inventory=source_inventory,
        realization_contract=realization_contract,
        installed_models=installed_models,
        endpoint=endpoint,
    )
    buildout_phase = _build_buildout_phase(
        source_inventory=source_inventory,
        floors=floors,
        installed_models=installed_models,
        endpoint=endpoint,
    )

    enabled_count = sum(1 for item in floors if item["ollama_connection"]["enabled"])
    resident_count = sum(1 for item in floors if item["activation"]["mode"] == "resident")
    staged_count = sum(1 for item in floors if item["activation"]["mode"] == "staged")
    manual_heavy_count = sum(1 for item in floors if item["activation"]["mode"] == "manual_heavy")
    draw_count = sum(len(item["assimilation_draw"]["priority_paths"]) for item in floors)
    chat_ready_count = sum(1 for item in floors if item["ai_chat_enablement"]["state"] == "ready_packet_first")

    return {
        "contract_id": CONTRACT_ID,
        "generated_at": _utc_now_iso(),
        "purpose": "Bounded local-agent wake-up, Ollama routing, and assimilation draw plan for LightSpeed floors.",
        "root": str(root),
        "shell_root": str(shell_root),
        "source_root": str(source_root),
        "source_root_exists": source_root.exists(),
        "policy": {
            "local_only": True,
            "max_concurrent_ollama_sessions": 1,
            "load_models_concurrently": False,
            "recursive_ingest_enabled": False,
            "heavy_models_manual_only": True,
            "receipt_prompt_overrides": {"stream": False, "think": False, "num_predict": 512},
            "external_writes": "blocked_until_operator_approval",
            "promotion": "floor_packets_are_training_context_until_trinity_and_architect_accept",
        },
        "ollama": {
            "endpoint": endpoint,
            "available_models": installed_models,
            "connection_state": "available" if installed_models else "unconfirmed",
            "resident_model_policy": "keep one small/resident lane active; load heavy models only for explicit manual tasks",
        },
        "summary": {
            "floor_count": len(floors),
            "ollama_enabled_floor_count": enabled_count,
            "resident_floor_count": resident_count,
            "staged_floor_count": staged_count,
            "manual_heavy_floor_count": manual_heavy_count,
            "source_top_level_count": source_inventory["top_level_count"],
            "source_file_sample_count": source_inventory["sampled_file_count"],
            "assimilation_draw_path_count": draw_count,
            "chat_ready_floor_count": chat_ready_count,
            "buildout_stage_count": len(buildout_phase["stages"]),
            "ui_simplification_state": "single_function_centre_planned",
        },
        "source_inventory": source_inventory,
        "buildout_phase": buildout_phase,
        "wake_sequence": [
            {
                "order": index + 1,
                "floor": floor,
                "reason": _wake_reason(floor),
                "run_mode": "packet_first_then_optional_local_prompt",
            }
            for index, floor in enumerate(DEFAULT_FLOOR_ORDER)
        ],
        "floors": floors,
        "ui_simplification": {
            "entry_surface": "N.py -> Functions Hub",
            "user_rule": "one active floor surface at a time; everything else becomes a drawer, packet, or queued task",
            "backend_rule": "floor-owned tools register with Smith/Trinity and expose one route, one status, one output root",
            "collapse_targets": [
                "duplicate tabs with same function",
                "parallel popup workflows",
                "legacy N variants",
                "unbounded ingest buttons",
                "render/simulation controls outside TheConstruct",
            ],
            "function_centre_lanes": [
                "Operator shell",
                "Local LLM temp shells",
                "Knowledge and reservoir",
                "Review and corroboration",
                "Queue and execution",
                "Simulation and digital twin",
                "Publish and governance",
            ],
            "next_ui_build_task": "Add a Functions Hub wake-up panel that shows floor status, local model, source draw list, and next safe action.",
        },
    }


def build_assimilation_source_inventory(source_root: Path, *, max_entries: int = DEFAULT_MAX_SCAN_ENTRIES) -> dict[str, Any]:
    source_root = Path(source_root)
    if not source_root.exists():
        return {
            "root": str(source_root),
            "exists": False,
            "top_level_count": 0,
            "sampled_file_count": 0,
            "sampled_dir_count": 0,
            "scan_truncated": False,
            "top_level": [],
            "by_extension": {},
            "largest_files": [],
            "priority_paths": [],
        }

    top_level = []
    for child in sorted(source_root.iterdir(), key=lambda item: item.name.lower()):
        top_level.append(_path_row(child, source_root))

    queue: deque[Path] = deque([source_root])
    sampled_files: list[dict[str, Any]] = []
    sampled_dirs = 0
    by_extension: Counter[str] = Counter()
    largest_files: list[dict[str, Any]] = []
    priority_paths: list[dict[str, Any]] = []
    visited = 0
    truncated = False

    while queue:
        current = queue.popleft()
        try:
            children = sorted(current.iterdir(), key=lambda item: item.name.lower())
        except OSError:
            continue
        for child in children:
            if visited >= max_entries:
                truncated = True
                queue.clear()
                break
            visited += 1
            if child.is_dir():
                sampled_dirs += 1
                if child.name not in SKIP_DIR_NAMES:
                    queue.append(child)
                continue
            row = _path_row(child, source_root)
            sampled_files.append(row)
            by_extension[row["extension"]] += 1
            largest_files.append(row)
            if _priority_score(row) > 0:
                priority_paths.append(row | {"priority_score": _priority_score(row)})

    largest_files = sorted(largest_files, key=lambda item: item.get("size_bytes") or 0, reverse=True)[:25]
    priority_paths = sorted(
        priority_paths,
        key=lambda item: (-int(item.get("priority_score") or 0), str(item.get("relative_path") or "").lower()),
    )[:120]

    return {
        "root": str(source_root),
        "exists": True,
        "top_level_count": len(top_level),
        "sampled_file_count": len(sampled_files),
        "sampled_dir_count": sampled_dirs,
        "scan_limit": max_entries,
        "scan_truncated": truncated,
        "top_level": top_level,
        "by_extension": dict(sorted(by_extension.items())),
        "largest_files": largest_files,
        "priority_paths": priority_paths,
    }


def write_local_agent_wakeup_outputs(
    root: Path,
    *,
    source_root: Path | None = None,
    shell_root: Path | None = None,
    max_scan_entries: int = DEFAULT_MAX_SCAN_ENTRIES,
) -> dict[str, Any]:
    root = Path(root)
    contract = build_local_agent_wakeup_contract(
        root,
        source_root=source_root,
        shell_root=shell_root,
        max_scan_entries=max_scan_entries,
    )
    export_path = default_export_path(root)
    shell_path = default_shell_mirror_path(root)
    _write_json(export_path, contract)
    _write_json(shell_path, contract)
    packet_paths = _write_floor_packets(root, contract)
    task_path = _write_neo_active_task(root, contract)
    oracle_manifest_path = _write_oracle_intake_manifest(root, contract)
    report_path = _write_operator_report(root, contract)
    buildout_handoff_paths = _write_buildout_handoffs(root, contract)

    return {
        "contract": contract,
        "export_path": str(export_path),
        "shell_mirror_path": str(shell_path),
        "packet_paths": packet_paths,
        "neo_active_task_path": str(task_path),
        "oracle_intake_manifest_path": str(oracle_manifest_path),
        "operator_report_path": str(report_path),
        "buildout_handoff_paths": buildout_handoff_paths,
    }


def _build_floor_wakeup_rows(
    *,
    root: Path,
    shell_root: Path,
    source_inventory: dict[str, Any],
    realization_contract: dict[str, Any],
    installed_models: list[str],
    endpoint: str,
) -> list[dict[str, Any]]:
    realization_by_floor = {
        str(item.get("floor")): item
        for item in realization_contract.get("floors") or []
        if isinstance(item, dict) and item.get("floor")
    }
    rows: list[dict[str, Any]] = []
    for order, floor in enumerate(DEFAULT_FLOOR_ORDER, start=1):
        realization = realization_by_floor.get(floor) or {}
        model = (realization.get("model") or {}).get("model") or _fallback_model_for_floor(floor)
        activation = _activation_for_floor(floor, realization)
        priority_paths = _select_floor_priority_paths(floor, source_inventory)
        directives = FLOOR_DIRECTIVES[floor]
        rows.append(
            {
                "floor": floor,
                "order": order,
                "floor_root": str(shell_root / FLOOR_DIRS[floor]),
                "packet_path": str(shell_root / FLOOR_DIRS[floor] / "data" / "wakeup" / "floor_wakeup_packet.json"),
                "environment_label": realization.get("environment_label") or floor,
                "agent": realization.get("agent") or {"agent_id": floor.lower(), "label": floor},
                "activation": activation,
                "ollama_connection": {
                    "provider": "ollama",
                    "endpoint": endpoint,
                    "model": model,
                    "enabled": model in installed_models,
                    "load_policy": _load_policy(model, activation["mode"]),
                    "session_policy": "one_floor_prompt_at_a_time",
                    "prompt_mode": "bounded_context_file_list_then_floor_summary",
                    "api_overrides": {"stream": False, "think": False, "num_predict": 512},
                },
                "training_context": {
                    "wake_goal": directives["wake_goal"],
                    "assimilation_role": directives["assimilation_role"],
                    "must_read_first": directives["draw_priority"],
                    "learning_sequence": _floor_learning_sequence(floor),
                    "do_not_do": [
                        "do not recursively rewrite source roots",
                        "do not promote derived claims without Oracle receipts and Morpheus review",
                        "do not open new tabs for same-function tools",
                        "do not use cloud or heavy models without explicit manual approval",
                    ],
                },
                "assimilation_draw": {
                    "source_root": source_inventory.get("root"),
                    "priority_paths": priority_paths,
                    "routing_rule": _routing_rule_for_floor(floor),
                },
                "ai_chat_enablement": _ai_chat_enablement_for_floor(floor, model, activation["mode"]),
                "next_safe_action": _next_safe_action(floor),
            }
        )
    return rows


def _build_buildout_phase(
    *,
    source_inventory: dict[str, Any],
    floors: list[dict[str, Any]],
    installed_models: list[str],
    endpoint: str,
) -> dict[str, Any]:
    model_order = _model_training_order(floors)
    floor_order = [str(item.get("floor")) for item in floors if item.get("floor")]
    return {
        "phase_id": "lightspeed_buildout_phase_shared_awareness",
        "state": "active_packet_first_local_llm_gated",
        "cadence": "slow_shared_awareness_one_floor_prompt_at_a_time",
        "endpoint": endpoint,
        "installed_models": installed_models,
        "floor_order": floor_order,
        "model_training_order": model_order,
        "shared_awareness": {
            "rule": "Every floor reads the same phase packet, then its own wake packet, before proposing changes.",
            "context_sources": [
                "agent-home exports",
                "backend/frontend build contract",
                "floor environment realization contract",
                "local agent wake-up contract",
                "D:\\To be assimilated attach-only source inventory",
            ],
            "communication": [
                "Neo coordinates prompts and current floor focus",
                "Smith records task receipts and blocks uncontrolled expansion",
                "Oracle keeps originals attached but read-only",
                "Morpheus reviews overlap before promotion",
                "Architect holds publish/repo/Drive/web gates closed",
                "Trinity keeps one readable shell and visible AI/chat state",
            ],
            "resource_guard": "one local Ollama prompt/session at a time; heavy models manual-only; no recursive ingest.",
        },
        "stages": [
            {
                "stage_id": "traditional_context_training",
                "label": "Traditional Context",
                "state": "ready",
                "goal": "Teach each local floor agent the stable platform rules, owner floor role, gates, and operator language before code work.",
                "inputs": ["agent_environment.json", "workspace_lanes.json", "presence_roster.json", "floor_wakeup_packet.json"],
                "done_when": "Each floor can summarize role, model, write scope, gates, and next safe action without opening new UI.",
            },
            {
                "stage_id": "functional_runtime_training",
                "label": "Functional Runtime",
                "state": "ready",
                "goal": "Teach each floor the actual backend/frontend contract and the functionable artifact model.",
                "inputs": [
                    "backend_frontend_build_contract.json",
                    "floor_environment_realization_contract.json",
                    "gated_build_tasks.json",
                    "smart_floor_spaces.json",
                ],
                "done_when": "Each floor proposes one bounded artifact/function route instead of another panel or tab.",
            },
            {
                "stage_id": "docs_to_be_assimilated_attach",
                "label": "Docs / To Be Assimilated",
                "state": "ready_attach_only" if source_inventory.get("exists") else "blocked_source_missing",
                "goal": "Attach D:\\To be assimilated as source truth candidates without bulk rewriting or promotion.",
                "inputs": [
                    str(source_inventory.get("root")),
                    f"{source_inventory.get('sampled_file_count', 0)} sampled files",
                    f"{source_inventory.get('top_level_count', 0)} top-level entries",
                ],
                "done_when": "Oracle receipts exist, Morpheus review queues are visible, and no source file is modified.",
            },
            {
                "stage_id": "enabled_agent_ui_code_consolidation",
                "label": "Enabled Agent Consolidation",
                "state": "ready_no_risk_seed",
                "goal": "Neo/Trinity use local LLM temp shells to consolidate UI and code architecture into one AI/chat enabled function centre.",
                "inputs": ["N.py Functions Hub", "Neo temp shell registry", "Trinity shell mirror", "Smith queue handoff"],
                "done_when": "LightSpeed shows one chat/operator surface, one active floor context, and functionable artifacts with explicit full-floor drill-in only.",
            },
            {
                "stage_id": "smart_floor_artifact_activation",
                "label": "Smart Floor Artifacts",
                "state": "queued_after_review",
                "goal": "Turn current floor widgets, tools, tables, docs, maps, charts, and simulations into smart artifacts reachable through chat and the project wall.",
                "inputs": ["smart_floor_visuals descriptors", "project wall artifacts", "Z Direct handoff receipts"],
                "done_when": "A selected artifact can be previewed, chatted about, routed to its owner floor, and approved or rejected from the single surface.",
            },
        ],
        "ui_target": {
            "target_shape": "AI chat enabled single function centre",
            "visible_entry": "Functions Hub / Ask Achilles",
            "floor_behavior": "floors are capabilities and artifact owners; full shells open only on explicit drill-in",
            "artifact_behavior": "documents, tables, code files, models, maps, charts, simulations, and receipts appear as functionable artifacts with provenance.",
        },
        "handover": {
            "neo": "owns the active buildout deck and local prompt sequencing",
            "trinity": "owns visible shell simplification and AI/chat entry",
            "smith": "owns queue receipts and no-risk task progression",
            "desporte": "receives a compact overseer handoff for companion awareness, not LightSpeed floor execution",
        },
    }


def _model_training_order(floors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for floor in floors:
        connection = floor.get("ollama_connection") or {}
        model = str(connection.get("model") or "")
        floor_name = str(floor.get("floor") or "")
        key = (floor_name, model)
        if not floor_name or not model or key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "floor": floor_name,
                "model": model,
                "enabled": bool(connection.get("enabled")),
                "load_policy": connection.get("load_policy"),
                "packet_path": floor.get("packet_path"),
                "training_prompt_mode": "read shared buildout phase, read floor packet, return one bounded proposal",
                "api_overrides": connection.get("api_overrides") or {"stream": False, "think": False, "num_predict": 512},
            }
        )
    return rows


def _floor_learning_sequence(floor: str) -> list[str]:
    return [
        "read shared buildout_phase",
        "read floor wake packet and assigned model policy",
        "read backend/frontend and realization contract for this floor",
        "read only priority D:\\To be assimilated paths routed to this floor",
        "return a concise role summary, one safe artifact proposal, and one blocker if present",
    ]


def _ai_chat_enablement_for_floor(floor: str, model: str, activation_mode: str) -> dict[str, Any]:
    return {
        "state": "ready_packet_first",
        "entry_surface": "Functions Hub -> Ask Achilles -> selected floor context",
        "model": model,
        "activation_mode": activation_mode,
        "chat_modes": ["brief", "review", "stage_task", "artifact_route"],
        "artifact_policy": "chat creates or updates task/artifact packets; full floor UI opens only by explicit drill-in",
        "prompt_seed": (
            f"You are the {floor} smart floor agent. Use the shared buildout phase and your floor wake packet. "
            "Do not create new panels. Return one bounded functionable artifact route."
        ),
    }


def _write_floor_packets(root: Path, contract: dict[str, Any]) -> dict[str, str]:
    shell_root = Path(contract["shell_root"])
    packets: dict[str, str] = {}
    for floor in contract.get("floors") or []:
        floor_name = str(floor.get("floor"))
        packet_path = Path(floor["packet_path"])
        _write_json(packet_path, floor)
        report_path = packet_path.with_suffix(".md")
        report_path.write_text(_floor_packet_markdown(contract, floor), encoding="utf-8")
        packets[floor_name] = str(packet_path)
    return packets


def _write_neo_active_task(root: Path, contract: dict[str, Any]) -> Path:
    shell_root = Path(contract["shell_root"])
    path = (
        shell_root
        / "Z Axis"
        / "Z+2_Neo"
        / "data"
        / "temp_shells"
        / "active_tasks"
        / "local_agent_wakeup_2026_05_29.json"
    )
    payload = {
        "task_id": "local_agent_wakeup_2026_05_29",
        "state": "staged_packet_first",
        "owner_floor": "Neo",
        "contract_path": str(default_shell_mirror_path(root)),
        "source_root": contract["source_root"],
        "floor_count": contract["summary"]["floor_count"],
        "ollama_enabled_floor_count": contract["summary"]["ollama_enabled_floor_count"],
        "manual_gate": "Trinity review then Architect approval for promotion or external writes",
        "next_action": "Run one local floor prompt at a time from the floor wake-up packets.",
        "buildout_phase": contract.get("buildout_phase") or {},
    }
    receipts = _preserved_local_agent_receipts(path)
    if receipts:
        payload["state"] = "neo_first_wakeup_completed_packet_first"
        payload["local_agent_receipts"] = receipts
        payload["next_action"] = (
            "Continue one-floor-at-a-time wake sequence; stage Trinity/Smith only after Neo receipt review, "
            "keep source promotion blocked."
        )
    _write_json(path, payload)
    return path


def _write_oracle_intake_manifest(root: Path, contract: dict[str, Any]) -> Path:
    shell_root = Path(contract["shell_root"])
    path = (
        shell_root
        / "Z Axis"
        / "Z-2_Oracle"
        / "Data"
        / "knowns"
        / "staged"
        / "to_be_assimilated_2026_05_29"
        / "intake_manifest.json"
    )
    payload = {
        "manifest_id": "to_be_assimilated_2026_05_29",
        "state": "attached_not_ingested",
        "source_root": contract["source_root"],
        "source_inventory": contract["source_inventory"],
        "promotion_state": "not_approved",
        "review_path": "Morpheus corroboration before any knowns promotion",
    }
    _write_json(path, payload)
    return path


def _write_operator_report(root: Path, contract: dict[str, Any]) -> Path:
    path = Path(root) / "reports" / "local_agent_wakeup_2026_05_29.md"
    lines = [
        "# Local Agent Wake-Up",
        "",
        f"Generated: {contract['generated_at']}",
        f"Source root: `{contract['source_root']}`",
        f"Ollama endpoint: `{contract['ollama']['endpoint']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in contract["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Wake Sequence", ""])
    for step in contract["wake_sequence"]:
        lines.append(f"- {step['order']}. {step['floor']}: {step['reason']}")
    lines.extend(["", "## UI Simplification", ""])
    ui = contract["ui_simplification"]
    lines.append(f"- Entry surface: `{ui['entry_surface']}`")
    lines.append(f"- User rule: {ui['user_rule']}")
    lines.append(f"- Backend rule: {ui['backend_rule']}")
    lines.append(f"- Next UI build task: {ui['next_ui_build_task']}")
    phase = contract.get("buildout_phase") or {}
    lines.extend(["", "## Buildout Phase", ""])
    lines.append(f"- State: `{phase.get('state', 'unknown')}`")
    lines.append(f"- Cadence: `{phase.get('cadence', 'unknown')}`")
    lines.append(f"- UI target: `{(phase.get('ui_target') or {}).get('target_shape', 'unknown')}`")
    for stage in phase.get("stages") or []:
        lines.append(f"- {stage.get('stage_id')}: {stage.get('state')} - {stage.get('goal')}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_buildout_handoffs(root: Path, contract: dict[str, Any]) -> dict[str, str]:
    shell_root = Path(contract["shell_root"])
    phase = contract.get("buildout_phase") or {}
    payload = {
        "handoff_id": "lightspeed_buildout_phase_handoff_2026_05_29",
        "generated_at": contract.get("generated_at"),
        "contract_id": contract.get("contract_id"),
        "state": phase.get("state"),
        "cadence": phase.get("cadence"),
        "source_root": contract.get("source_root"),
        "ollama": contract.get("ollama") or {},
        "ui_target": phase.get("ui_target") or {},
        "shared_awareness": phase.get("shared_awareness") or {},
        "stages": phase.get("stages") or [],
        "model_training_order": phase.get("model_training_order") or [],
        "handover": phase.get("handover") or {},
        "manual_gate": "external writes, source promotion, repo push, Drive writeback, and web publish remain blocked until operator approval",
        "next_action": "Neo runs one floor packet at a time; Trinity keeps the visible shell compact; Smith records receipts.",
    }
    paths = {
        "trinity_shell": shell_root / "config" / "buildout_phase_contract.json",
        "neo_handoff": shell_root / "Z Axis" / "Z+2_Neo" / "data" / "actions" / "buildout_phase_handoff.json",
        "smith_queue": shell_root / "Z Axis" / "Z-3_Smith" / "data" / "staging" / "buildout_phase_queue.json",
    }
    de_sporte_path = Path(root.anchor) / "De Sporte`" / "Data" / "Overseer" / "lightspeed_buildout_handoff.json"
    if de_sporte_path.parent.exists():
        paths["de_sporte_overseer"] = de_sporte_path
    for path in paths.values():
        output_payload = dict(payload)
        receipts = _preserved_local_agent_receipts(path)
        if receipts:
            output_payload["state"] = "neo_first_wakeup_completed_packet_first"
            output_payload["local_agent_receipts"] = receipts
            output_payload["next_action"] = (
                "Continue one-floor-at-a-time wake sequence; stage Trinity/Smith only after Neo receipt review, "
                "keep source promotion blocked."
            )
        _write_json(path, output_payload)
    return {key: str(path) for key, path in paths.items()}


def _preserved_local_agent_receipts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    receipts = existing.get("local_agent_receipts") if isinstance(existing, dict) else None
    return receipts if isinstance(receipts, list) else []


def _floor_packet_markdown(contract: dict[str, Any], floor: dict[str, Any]) -> str:
    lines = [
        f"# {floor['floor']} Wake-Up Packet",
        "",
        f"Contract: `{contract['contract_id']}`",
        f"Model: `{floor['ollama_connection']['model']}`",
        f"Endpoint: `{floor['ollama_connection']['endpoint']}`",
        f"Enabled: `{floor['ollama_connection']['enabled']}`",
        f"Activation: `{floor['activation']['mode']}`",
        "",
        "## Wake Goal",
        "",
        floor["training_context"]["wake_goal"],
        "",
        "## Assimilation Role",
        "",
        floor["training_context"]["assimilation_role"],
        "",
        "## Priority Draw",
        "",
    ]
    for item in floor["assimilation_draw"]["priority_paths"][:20]:
        lines.append(f"- `{item['relative_path']}`")
    if not floor["assimilation_draw"]["priority_paths"]:
        lines.append("- No priority files matched in this bounded scan.")
    lines.extend(["", "## Learning Sequence", ""])
    for item in floor["training_context"].get("learning_sequence") or []:
        lines.append(f"- {item}")
    chat = floor.get("ai_chat_enablement") or {}
    lines.extend(["", "## AI Chat Enablement", ""])
    lines.append(f"- Entry: `{chat.get('entry_surface', 'Functions Hub')}`")
    lines.append(f"- Modes: `{', '.join(chat.get('chat_modes') or [])}`")
    lines.append(f"- Artifact policy: {chat.get('artifact_policy', 'packet-first')}")
    lines.append(f"- Prompt seed: {chat.get('prompt_seed', '')}")
    lines.extend(["", "## Next Safe Action", "", floor["next_safe_action"], ""])
    return "\n".join(lines)


def _select_floor_priority_paths(floor: str, source_inventory: dict[str, Any]) -> list[dict[str, Any]]:
    priorities = source_inventory.get("priority_paths") or []
    rows = []
    for item in priorities:
        targets = _classify_targets(str(item.get("relative_path") or ""), str(item.get("extension") or ""))
        if floor in targets:
            rows.append(item)
    if rows:
        return rows[:24]
    top = source_inventory.get("top_level") or []
    return [item for item in top if floor in _classify_targets(str(item.get("relative_path") or ""), str(item.get("extension") or ""))][:12]


def _classify_targets(relative_path: str, extension: str) -> set[str]:
    lower = relative_path.lower()
    targets: set[str] = {"Oracle"}
    if any(term in lower for term in ("ui", "n_updated", "theme", "dashboard", "portal")):
        targets.add("Trinity")
    if any(term in lower for term in ("architecture", "roadmap", "implementation", "guide", "phase", "week")):
        targets.add("Architect")
    if any(term in lower for term in ("ollama", "gpt", "claude", "responder")):
        targets.add("Neo")
    if any(term in lower for term in ("inventory", "organize", "discovery", ".ps1", "apps", "nodejs", "jetbrains", "support_pack")):
        targets.add("Smith")
    if any(term in lower for term in ("blueprint", "igp", "emc", "emff", "pdf", "cvb", "vertebra")):
        targets.add("TheConstruct")
    if any(term in lower for term in ("analysis", "report", "roadmap", "returns", "export")):
        targets.add("Morpheus")
    if any(term in lower for term in ("log", "data", "settings", "runtime")):
        targets.add("Merovingian")
    if extension in {".py", ".ps1", ".bat", ".cmd", ".js", ".ts"}:
        targets.add("Smith")
    if extension in {".pdf", ".zip"}:
        targets.update({"Oracle", "TheConstruct"})
    if extension in {".md", ".txt"}:
        targets.update({"Oracle", "Morpheus", "Architect"})
    if extension in {".json", ".csv", ".xlsx", ".xls"}:
        targets.update({"Oracle", "Merovingian"})
    return targets


def _routing_rule_for_floor(floor: str) -> str:
    return {
        "Merovingian": "logs, settings, runtime evidence, and system health receipts",
        "Trinity": "UI files, N variants, portal layouts, readable operator controls",
        "Neo": "local-agent prompts, LLM bridges, temp-shell orchestration notes",
        "Smith": "scripts, apps, support packs, queues, and execution receipts",
        "Oracle": "all original source attachments and provenance manifests",
        "Morpheus": "reviews, reports, duplicate-function analysis, proof notes",
        "Architect": "architecture, roadmaps, approval gates, release plans",
        "TheConstruct": "PDFs, blueprints, empirical datasets, visual/render assets",
    }[floor]


def _activation_for_floor(floor: str, realization: dict[str, Any]) -> dict[str, Any]:
    population = realization.get("population") or {}
    mode = str(population.get("mode") or "staged")
    if floor == "TheConstruct":
        mode = "manual_heavy"
    return {
        "mode": mode,
        "boot_priority": population.get("boot_priority"),
        "launch_gate": population.get("launch_gate") or "CL-3 DESKTOP_READY",
        "wake_state": "ready_packet_staged",
    }


def _fallback_model_for_floor(floor: str) -> str:
    if floor in {"Oracle", "Morpheus"}:
        return "deepseek-r1:8b"
    if floor == "TheConstruct":
        return "gemma3:27b"
    return "qwen3:8b"


def _load_policy(model: str, mode: str) -> str:
    if model in {"gpt-oss:120b", "deepseek-v3.1:671b-cloud"}:
        return "manual_only"
    if mode == "manual_heavy":
        return "manual_heavy_short"
    if mode == "resident":
        return "resident_or_short_hot_path"
    return "on_demand_short"


def _priority_score(row: dict[str, Any]) -> int:
    rel = str(row.get("relative_path") or "").lower()
    ext = str(row.get("extension") or "")
    score = 0
    if ext in {".md", ".txt", ".py", ".json", ".pdf", ".zip", ".ps1"}:
        score += 2
    for token in (
        "architecture",
        "implementation",
        "guide",
        "roadmap",
        "inventory",
        "lightspeed",
        "ui",
        "ollama",
        "blueprint",
        "support_pack",
        "phase",
        "week",
    ):
        if token in rel:
            score += 2
    return score


def _path_row(path: Path, source_root: Path) -> dict[str, Any]:
    try:
        rel = str(path.relative_to(source_root))
    except ValueError:
        rel = str(path)
    is_file = path.is_file()
    size = path.stat().st_size if is_file else None
    return {
        "name": path.name,
        "relative_path": rel,
        "path": str(path),
        "kind": "file" if is_file else "directory",
        "extension": path.suffix.lower() if is_file else "",
        "size_bytes": size,
        "last_write_time": datetime.fromtimestamp(path.stat().st_mtime, UTC).replace(microsecond=0).isoformat(),
    }


def _probe_ollama_models(endpoint: str) -> list[str]:
    url = endpoint.rstrip("/") + "/api/tags"
    try:
        with urlopen(url, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return []
    models = []
    for item in payload.get("models") or []:
        name = item.get("name")
        if isinstance(name, str) and name:
            models.append(name)
    return sorted(set(models))


def _wake_reason(floor: str) -> str:
    return FLOOR_DIRECTIVES[floor]["wake_goal"]


def _next_safe_action(floor: str) -> str:
    return {
        "Merovingian": "Snapshot process/model state and accept only ledger/report writes.",
        "Trinity": "Show wake-up state in the Functions Hub and collapse duplicate controls into one surface.",
        "Neo": "Stage one local prompt at a time from floor wake-up packets.",
        "Smith": "Turn file movement, scripts, and support packs into no-risk queued tasks.",
        "Oracle": "Attach source-root receipts and keep originals read-only.",
        "Morpheus": "Review overlap and duplicate-function reports before promotion.",
        "Architect": "Hold publish/repo/Drive gates closed while release packets mature.",
        "TheConstruct": "Prepare proofed visual/data lanes without launching immersive heavy mode.",
    }[floor]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}
    return {}


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Write LightSpeed local-agent wake-up contract.")
    parser.add_argument("--root", default=str(Path.cwd()))
    parser.add_argument("--source-root", default=None)
    parser.add_argument("--max-scan-entries", type=int, default=DEFAULT_MAX_SCAN_ENTRIES)
    args = parser.parse_args()
    result = write_local_agent_wakeup_outputs(
        Path(args.root),
        source_root=Path(args.source_root) if args.source_root else None,
        max_scan_entries=args.max_scan_entries,
    )
    print(
        json.dumps(
            {
                "export_path": result["export_path"],
                "shell_mirror_path": result["shell_mirror_path"],
                "floor_count": result["contract"]["summary"]["floor_count"],
                "ollama_enabled_floor_count": result["contract"]["summary"]["ollama_enabled_floor_count"],
                "source_file_sample_count": result["contract"]["summary"]["source_file_sample_count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
