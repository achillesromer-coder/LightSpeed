from __future__ import annotations

from collections import Counter, defaultdict
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from lightspeed_runtime.domain_registry import get_source_type_definition
from lightspeed_runtime.local_agent_wakeup import build_local_agent_wakeup_contract

if TYPE_CHECKING:
    from lightspeed_runtime.runtime import LightSpeedRuntime


DEFAULT_STOPWORDS = {
    "about",
    "after",
    "against",
    "analysis",
    "and",
    "build",
    "current",
    "data",
    "desktop",
    "drive",
    "export",
    "final",
    "folder",
    "from",
    "handoff",
    "index",
    "internal",
    "lightspeed",
    "linkdrive",
    "logged",
    "master",
    "notes",
    "operations",
    "package",
    "previous",
    "project",
    "queue",
    "report",
    "romer",
    "sheet",
    "source",
    "system",
    "task",
    "truth",
    "update",
    "version",
    "web",
    "website",
    "with",
    "work",
    "workspace",
}
LOW_SIGNAL_FILENAMES = {
    ".gitignore",
    "misc.xml",
    "modules.xml",
    "package-lock.json",
    "package.json",
    "profiles_settings.xml",
    "workspace.xml",
}
LOW_SIGNAL_PATH_MARKERS = {
    ".idea/",
    ".venv/",
    "__pycache__/",
    "node_modules/",
}


def default_agent_home_config_path(root: Path) -> Path:
    return root / "config" / "agent_home.json"


def default_agent_home_export_dir(root: Path) -> Path:
    return root / "exports" / "agent_home"


def load_agent_home_config(root: Path, config_path: Path | None = None) -> dict:
    path = Path(config_path) if config_path else default_agent_home_config_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_json_file(path: Path) -> dict:
    try:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            return payload if isinstance(payload, dict) else {}
    except Exception:
        pass
    return {}


def build_agent_environment(
    runtime: "LightSpeedRuntime",
    *,
    config_path: Path | None = None,
    max_assets_per_source: int = 25,
) -> dict:
    config = load_agent_home_config(runtime.root, config_path=config_path)
    if not runtime.registry.manifests():
        runtime.bootstrap(index_limit_per_source=max_assets_per_source)

    environment = _environment_status(runtime, config)
    source_catalog = [_source_catalog_entry(manifest) for manifest in runtime.registry.manifests()]
    overlap = _build_overlap_bellcurve(runtime, config)
    queue = _build_consolidation_queue(runtime, overlap)
    floor_models = _build_floor_models(config)
    deployment_topology = _deployment_topology(config)
    host_runtime_policy = _host_runtime_policy(config)
    floor_stage_population = _floor_stage_population(config)
    construct_runtime = _construct_runtime(config, environment=environment)
    presence_roster = _presence_roster(config)
    neo_local_runtime = _neo_local_runtime(config)
    neo_realisation_runtime = _neo_realisation_runtime(config)
    upstream_inventory = _upstream_inventory(config)
    launch_control = _launch_control(config)
    agent_population = _agent_population(config)
    input_staging_matrix = _input_staging_matrix(config)
    workspace_lanes = _workspace_lanes(config)
    smart_floor_spaces = _smart_floor_spaces(config)
    gated_build_tasks = _gated_build_tasks(config)
    backend_frontend_build = _backend_frontend_build_contract(
        floor_models=floor_models,
        launch_control=launch_control,
        neo_local_runtime=neo_local_runtime,
        agent_population=agent_population,
        input_staging_matrix=input_staging_matrix,
        floor_stage_population=floor_stage_population,
        workspace_lanes=workspace_lanes,
        smart_floor_spaces=smart_floor_spaces,
        gated_build_tasks=gated_build_tasks,
    )
    floor_environment_realization = _floor_environment_realization_contract(
        backend_frontend_build=backend_frontend_build,
        floor_models=floor_models,
        launch_control=launch_control,
        neo_local_runtime=neo_local_runtime,
        agent_population=agent_population,
        floor_stage_population=floor_stage_population,
        workspace_lanes=workspace_lanes,
        gated_build_tasks=gated_build_tasks,
    )
    local_agent_wakeup = build_local_agent_wakeup_contract(
        runtime.root,
        realization_contract=floor_environment_realization,
        neo_local_runtime=neo_local_runtime,
        probe_ollama=False,
    )

    return {
        "generated_at": _utc_now_iso(),
        "profile_id": config.get("environment", {}).get("profile_id", "lightspeed_agent_home"),
        "environment": environment,
        "policy": config.get("intake_policy", {}),
        "truth_registry": _build_truth_registry(runtime, config),
        "floor_models": floor_models,
        "deployment_topology": deployment_topology,
        "host_runtime_policy": host_runtime_policy,
        "neo_local_runtime": neo_local_runtime,
        "neo_realisation_runtime": neo_realisation_runtime,
        "upstream_inventory": upstream_inventory,
        "launch_control": launch_control,
        "agent_population": agent_population,
        "input_staging_matrix": input_staging_matrix,
        "floor_stage_population": floor_stage_population,
        "construct_runtime": construct_runtime,
        "presence_roster": presence_roster,
        "workspace_lanes": workspace_lanes,
        "smart_floor_spaces": smart_floor_spaces,
        "gated_build_tasks": gated_build_tasks,
        "backend_frontend_build": backend_frontend_build,
        "floor_environment_realization": floor_environment_realization,
        "local_agent_wakeup": local_agent_wakeup,
        "source_catalog": source_catalog,
        "consolidation_queue": queue,
        "overlap_bellcurve": overlap,
    }


def export_agent_environment(
    runtime: "LightSpeedRuntime",
    output_dir: Path,
    *,
    config_path: Path | None = None,
    max_assets_per_source: int = 25,
) -> dict:
    payload = build_agent_environment(
        runtime,
        config_path=config_path,
        max_assets_per_source=max_assets_per_source,
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "agent_environment": output_dir / "agent_environment.json",
        "truth_registry": output_dir / "truth_registry.json",
        "floor_models": output_dir / "floor_models.json",
        "deployment_topology": output_dir / "deployment_topology.json",
        "host_runtime_policy": output_dir / "host_runtime_policy.json",
        "neo_local_runtime": output_dir / "neo_local_runtime.json",
        "neo_realisation_runtime": output_dir / "neo_realisation_runtime.json",
        "upstream_inventory": output_dir / "upstream_inventory.json",
        "launch_control": output_dir / "launch_control.json",
        "agent_population": output_dir / "agent_population.json",
        "input_staging_matrix": output_dir / "input_staging_matrix.json",
        "floor_stage_population": output_dir / "floor_stage_population.json",
        "construct_runtime": output_dir / "construct_runtime.json",
        "presence_roster": output_dir / "presence_roster.json",
        "workspace_lanes": output_dir / "workspace_lanes.json",
        "smart_floor_spaces": output_dir / "smart_floor_spaces.json",
        "gated_build_tasks": output_dir / "gated_build_tasks.json",
        "backend_frontend_build": output_dir / "backend_frontend_build_contract.json",
        "floor_environment_realization": output_dir / "floor_environment_realization_contract.json",
        "local_agent_wakeup": output_dir / "local_agent_wakeup_contract.json",
        "consolidation_queue": output_dir / "consolidation_queue.json",
        "overlap_bellcurve": output_dir / "overlap_bellcurve.json",
    }
    _write_json(files["agent_environment"], payload)
    _write_json(files["truth_registry"], payload["truth_registry"])
    _write_json(files["floor_models"], payload["floor_models"])
    _write_json(files["deployment_topology"], payload["deployment_topology"])
    _write_json(files["host_runtime_policy"], payload["host_runtime_policy"])
    _write_json(files["neo_local_runtime"], payload["neo_local_runtime"])
    _write_json(files["neo_realisation_runtime"], payload["neo_realisation_runtime"])
    _write_json(files["upstream_inventory"], payload["upstream_inventory"])
    _write_json(files["launch_control"], payload["launch_control"])
    _write_json(files["agent_population"], payload["agent_population"])
    _write_json(files["input_staging_matrix"], payload["input_staging_matrix"])
    _write_json(files["floor_stage_population"], payload["floor_stage_population"])
    _write_json(files["construct_runtime"], payload["construct_runtime"])
    _write_json(files["presence_roster"], payload["presence_roster"])
    _write_json(files["workspace_lanes"], payload["workspace_lanes"])
    _write_json(files["smart_floor_spaces"], payload["smart_floor_spaces"])
    _write_json(files["gated_build_tasks"], payload["gated_build_tasks"])
    _write_json(files["backend_frontend_build"], payload["backend_frontend_build"])
    _write_json(files["floor_environment_realization"], payload["floor_environment_realization"])
    _write_json(files["local_agent_wakeup"], payload["local_agent_wakeup"])
    _write_json(files["consolidation_queue"], payload["consolidation_queue"])
    _write_json(files["overlap_bellcurve"], payload["overlap_bellcurve"])

    shell_files = _write_shell_artifacts(payload)

    return {
        "generated_at": payload["generated_at"],
        "profile_id": payload["profile_id"],
        "output_dir": str(output_dir),
        "files": {key: str(path) for key, path in files.items()},
        "shell_files": shell_files,
        "queue_size": len(payload["consolidation_queue"]),
        "cluster_count": payload["overlap_bellcurve"]["summary"]["cluster_count"],
    }


def _environment_status(runtime: "LightSpeedRuntime", config: dict) -> dict:
    environment = dict(config.get("environment") or {})
    path_map = {
        "runtime_root": {
            "path": str(runtime.root.resolve()),
            "exists": runtime.root.exists(),
            "role": "contract_core",
        }
    }
    for key, role in (
        ("desktop_shell_root", "desktop_shell"),
        ("desktop_reference_root", "desktop_reference"),
        ("repo_reference_root", "repo_reference"),
        ("analysis_root", "analysis_surface"),
    ):
        value = environment.get(key)
        if not value:
            continue
        path = Path(value)
        path_map[key] = {
            "path": str(path),
            "exists": path.exists(),
            "role": role,
        }
    environment["paths"] = path_map
    return environment


def _build_truth_registry(runtime: "LightSpeedRuntime", config: dict) -> list[dict]:
    policy = config.get("intake_policy", {})
    blocked_inputs = list(policy.get("blocked_inputs") or [])
    extra_layers = list(config.get("truth_layers") or [])
    extra_by_source = {
        layer["source_id"]: layer
        for layer in extra_layers
        if isinstance(layer, dict) and layer.get("source_id")
    }
    used_layer_ids: set[str] = set()
    registry: list[dict] = []

    for manifest in runtime.registry.manifests():
        source_type_definition = get_source_type_definition(manifest.source_type)
        overlay = extra_by_source.get(manifest.source_id, {})
        if overlay.get("layer_id"):
            used_layer_ids.add(str(overlay["layer_id"]))
        registry.append(
            {
                "entry_id": manifest.source_id,
                "entry_type": "registered_source",
                "layer_id": overlay.get("layer_id"),
                "source_id": manifest.source_id,
                "source_label": overlay.get("label") or manifest.source_label or manifest.source_id,
                "source_type": manifest.source_type,
                "source_type_label": (
                    overlay.get("layer_type_label")
                    or (source_type_definition.label if source_type_definition else manifest.source_type)
                ),
                "classification": manifest.classification,
                "root_path": manifest.root_path,
                "root_resolution": manifest.root_resolution,
                "trusted_document_count": len(manifest.trusted_documents),
                "status": overlay.get("status") or "registered",
                "intake_decision": _intake_decision(manifest.classification),
                "allowed_for": overlay.get("allowed_for") or _default_allowed_for(manifest.classification),
                "publish_eligible": (
                    manifest.classification in {"canonical", "reference"}
                    and manifest.root_resolution != "configured_missing"
                ),
                "blocked_inputs": overlay.get("blocked_inputs") or blocked_inputs,
            }
        )

    for layer in extra_layers:
        if not isinstance(layer, dict):
            continue
        layer_id = str(layer.get("layer_id") or "")
        if layer_id and layer_id in used_layer_ids:
            continue
        registry.append(
            {
                "entry_id": layer_id or layer.get("label") or "truth_layer",
                "entry_type": "truth_layer",
                "layer_id": layer_id or None,
                "source_id": layer.get("source_id"),
                "source_label": layer.get("label") or layer.get("source_id") or "truth_layer",
                "source_type": layer.get("layer_type") or "truth_layer",
                "source_type_label": layer.get("layer_type_label") or layer.get("layer_type") or "truth_layer",
                "classification": layer.get("classification") or "planned",
                "root_path": layer.get("root_path"),
                "root_resolution": layer.get("root_resolution") or "external_planned",
                "trusted_document_count": int(layer.get("trusted_document_count") or 0),
                "status": layer.get("status") or "planned",
                "intake_decision": layer.get("intake_decision") or "gated_pending_connection",
                "allowed_for": layer.get("allowed_for") or [],
                "publish_eligible": bool(layer.get("publish_eligible")),
                "blocked_inputs": layer.get("blocked_inputs") or blocked_inputs,
            }
        )

    return registry


def _build_floor_models(config: dict) -> list[dict]:
    assignments = config.get("floor_models") or {}
    rows: list[dict] = []
    for floor, payload in assignments.items():
        if not isinstance(payload, dict):
            continue
        rows.append(
            {
                "floor": floor,
                "provider": payload.get("provider", "ollama"),
                "model": payload.get("model", "llama3.2"),
                "persona": payload.get("persona", "general"),
                "enabled": bool(payload.get("enabled", True)),
                "approval_required": bool(payload.get("approval_required", True)),
                "max_parallel_tasks": int(payload.get("max_parallel_tasks", 1)),
                "queue_limit": int(payload.get("queue_limit", 3)),
                "timeout_s": int(payload.get("timeout_s", 30)),
                "recursion_guard": int(payload.get("recursion_guard", 2)),
                "workspace_scope": payload.get("workspace_scope", "global"),
            }
        )
    rows.sort(key=lambda item: item["floor"])
    return rows


def _deployment_topology(config: dict) -> dict:
    topology = dict(config.get("deployment_topology") or {})
    topology["authoritative_roots"] = _annotate_root_entries(topology.get("authoritative_roots"))
    topology["reference_roots"] = _annotate_root_entries(topology.get("reference_roots"))
    return topology


def _host_runtime_policy(config: dict) -> dict:
    return dict(config.get("host_runtime_policy") or {})


def _floor_stage_population(config: dict) -> dict:
    return dict(config.get("floor_stage_population") or {})


def _construct_runtime(config: dict, *, environment: dict | None = None) -> dict:
    construct = dict(config.get("construct_runtime") or {})
    shell_root = None
    paths = (environment or {}).get("paths") or {}
    shell_payload = paths.get("desktop_shell_root") if isinstance(paths, dict) else None
    if isinstance(shell_payload, dict):
        shell_root_value = shell_payload.get("path")
        if isinstance(shell_root_value, str) and shell_root_value:
            shell_root = Path(shell_root_value)

    surface_inventory = []
    for item in construct.get("surface_inventory") or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        value = row.get("path")
        if isinstance(value, str) and value:
            candidate = Path(value)
            if not candidate.is_absolute() and shell_root is not None:
                candidate = shell_root / value
                row["resolved_path"] = str(candidate)
            row["exists"] = candidate.exists()
        surface_inventory.append(row)
    construct["surface_inventory"] = surface_inventory
    return construct


def _presence_roster(config: dict) -> dict:
    return dict(config.get("presence_roster") or {})


def _neo_local_runtime(config: dict) -> dict:
    return dict(config.get("neo_local_runtime") or {})


def _neo_realisation_runtime(config: dict) -> dict:
    return dict(config.get("neo_realisation_runtime") or {})


def _upstream_inventory(config: dict) -> dict:
    return dict(config.get("upstream_inventory") or {})


def _launch_control(config: dict) -> dict:
    return dict(config.get("launch_control") or {})


def _agent_population(config: dict) -> dict:
    return dict(config.get("agent_population") or {})


def _input_staging_matrix(config: dict) -> dict:
    return dict(config.get("input_staging_matrix") or {})


def _workspace_lanes(config: dict) -> dict:
    return dict(config.get("workspace_lanes") or {})


def _smart_floor_spaces(config: dict) -> dict:
    return dict(config.get("smart_floor_spaces") or {})


def _gated_build_tasks(config: dict) -> dict:
    return dict(config.get("gated_build_tasks") or {})


_FLOOR_BUILD_SPINE = {
    "Trinity": {
        "backend_role": "settings, shell state, readable operator routing, and approval context",
        "frontend_surface": "N.py Functions Hub and Trinity operator home",
        "output_roots": ["config", "Z Axis/Z+3_Trinity/settings", "Z Axis/Z+3_Trinity/data/ui"],
        "next_safe_action": "Keep the operator shell readable and collapse duplicate navigation into one active context.",
    },
    "Neo": {
        "backend_role": "local Ollama orchestration, temp-shell staging, and De Sporte corunner handoff",
        "frontend_surface": "Neo workbench, local-runtime lane, and Trinity editor sync",
        "output_roots": ["config/neo_local_runtime.json", "Z Axis/Z+2_Neo/data/temp_shells"],
        "next_safe_action": "Stage bounded local tasks through Neo temp shells before permanent floor population.",
    },
    "Smith": {
        "backend_role": "build queue routing, workflow state, and low-risk execution records",
        "frontend_surface": "Smith route foundry and queue router",
        "output_roots": ["Z Axis/Z-3_Smith/data/staging", "Z Axis/Z-3_Smith/tasks"],
        "next_safe_action": "Keep all executable work in the gated Smith queue with owned-floor write scope.",
    },
    "Oracle": {
        "backend_role": "truth registry, provenance receipts, knowns, reservoirs, and attach-only source intake",
        "frontend_surface": "Oracle reservoir library and candidate-knowns workbench",
        "output_roots": ["Z Axis/Z-2_Oracle/Data/knowns", "Z Axis/Z-2_Oracle/Data/datatables", "Z Axis/Z-2_Oracle/data/reservoirs"],
        "next_safe_action": "Attach proofed source sets and receipts without rewriting upstream material.",
    },
    "Morpheus": {
        "backend_role": "corroboration, diff review, promotion proposals, and overlap pressure checks",
        "frontend_surface": "Morpheus review chamber",
        "output_roots": ["Z Axis/Z-1_Morpheus/data/reviews", "Z Axis/Z-1_Morpheus/organization"],
        "next_safe_action": "Review Oracle candidates and Smith evidence notes before promotion.",
    },
    "TheConstruct": {
        "backend_role": "dataset-backed scenario planning, render readiness, and bounded digital-twin runtime state",
        "frontend_surface": "TheConstruct digital twin atrium and manual-heavy render controls",
        "output_roots": ["Z Axis/Z0_TheConstruct/data/runtime", "Z Axis/Z0_TheConstruct/data/datasets", "Z Axis/Z0_TheConstruct/data/outputs"],
        "next_safe_action": "Keep immersive/render modes manual while proofed datasets populate scenario previews.",
    },
    "Architect": {
        "backend_role": "release packets, manual approvals, external-write gates, and publish topology",
        "frontend_surface": "Architect publish wall and approval checklist",
        "output_roots": ["Z Axis/Z+1_Architect/data/finalization", "Z Axis/Z+1_Architect/data/approvals"],
        "next_safe_action": "Hold GitHub, Drive, and web publish behind explicit yes/no artifact review.",
    },
    "Merovingian": {
        "backend_role": "telemetry, health checks, action ledgers, runtime database, and recovery evidence",
        "frontend_surface": "Merovingian evidence core and diagnostics panel",
        "output_roots": ["Z Axis/Z-4_Merovingian/data/audit", "Z Axis/Z-4_Merovingian/data/db", "Z Axis/Z-4_Merovingian/data/logs"],
        "next_safe_action": "Snapshot health and ledger state before deeper autonomous operation.",
    },
}


def _backend_frontend_build_contract(
    *,
    floor_models: list[dict],
    launch_control: dict,
    neo_local_runtime: dict,
    agent_population: dict,
    input_staging_matrix: dict,
    floor_stage_population: dict,
    workspace_lanes: dict,
    smart_floor_spaces: dict,
    gated_build_tasks: dict,
) -> dict:
    """Build the compact backend/frontend spine each LightSpeed floor consumes."""
    model_by_floor = {str(item.get("floor")): item for item in floor_models if item.get("floor")}
    population_by_floor = {
        str(item.get("floor")): item
        for item in (agent_population.get("floor_assignments") or [])
        if isinstance(item, dict) and item.get("floor")
    }
    staging_by_floor = {
        str(item.get("floor")): item
        for item in (input_staging_matrix.get("floors") or [])
        if isinstance(item, dict) and item.get("floor")
    }
    spaces_by_floor = {
        str(item.get("floor")): item
        for item in (smart_floor_spaces.get("spaces") or [])
        if isinstance(item, dict) and item.get("floor")
    }
    lanes_by_floor: dict[str, list[dict]] = defaultdict(list)
    for lane in workspace_lanes.get("lanes") or []:
        if not isinstance(lane, dict):
            continue
        owner = str(lane.get("owner_floor") or "")
        if owner:
            lanes_by_floor[owner].append(lane)
        for floor in lane.get("attached_floors") or []:
            if floor and lane not in lanes_by_floor[str(floor)]:
                lanes_by_floor[str(floor)].append(lane)

    tasks_by_floor: dict[str, list[dict]] = defaultdict(list)
    for task in gated_build_tasks.get("tasks") or []:
        if isinstance(task, dict) and task.get("owner_floor"):
            tasks_by_floor[str(task["owner_floor"])].append(task)

    stage_profiles = floor_stage_population.get("floor_profiles") or {}
    display_order = list(floor_stage_population.get("boot_lane_order") or [])
    for floor in sorted(set(model_by_floor) | set(population_by_floor) | set(staging_by_floor) | set(spaces_by_floor)):
        if floor not in display_order:
            display_order.append(floor)

    endpoint_policy = neo_local_runtime.get("endpoint_policy") or {}
    resident_host = agent_population.get("resident_host_application") or {}
    manual_gate_ids = [
        str(item.get("gate_id"))
        for item in launch_control.get("manual_gates") or []
        if isinstance(item, dict) and item.get("gate_id")
    ]

    floors = []
    for floor in display_order:
        defaults = _FLOOR_BUILD_SPINE.get(floor, {})
        model = model_by_floor.get(floor) or {}
        population = population_by_floor.get(floor) or {}
        staging = staging_by_floor.get(floor) or {}
        space = spaces_by_floor.get(floor) or {}
        stage_profile = stage_profiles.get(floor) or {}
        lane_rows = lanes_by_floor.get(floor) or []
        task_rows = tasks_by_floor.get(floor) or []
        components = [item for item in (staging.get("components") or []) if isinstance(item, dict)]
        live_components = [
            item
            for item in components
            if str(item.get("status") or "").startswith(("live", "seeded"))
            or str(item.get("status") or "").endswith("export")
        ]
        input_paths = [
            str(item.get("path"))
            for item in live_components
            if isinstance(item.get("path"), str) and item.get("path")
        ]
        ready_tasks = [
            item
            for item in task_rows
            if str(item.get("state") or "").startswith("ready")
        ]
        lane_ids = sorted({str(item.get("lane_id")) for item in lane_rows if item.get("lane_id")})
        task_ids = [str(item.get("task_id")) for item in ready_tasks if item.get("task_id")]

        backend_enabled = bool(model.get("enabled", True)) and bool(input_paths or task_ids or defaults)
        frontend_enabled = bool(space.get("space_id") and space.get("no_risk_entry", True))
        floors.append(
            {
                "floor": floor,
                "agent": {
                    "agent_id": population.get("assigned_agent_id") or floor.lower(),
                    "label": population.get("assigned_agent_label") or floor,
                    "support_resident_id": population.get("de_sporte_support_resident_id"),
                    "support_state": population.get("support_state"),
                    "resident_host": resident_host.get("label") or population.get("resident_host_application"),
                },
                "model": {
                    "provider": model.get("provider", "ollama"),
                    "model": model.get("model"),
                    "persona": model.get("persona"),
                    "enabled": bool(model.get("enabled", True)),
                    "approval_required": bool(model.get("approval_required", True)),
                    "max_parallel_tasks": model.get("max_parallel_tasks"),
                    "queue_limit": model.get("queue_limit"),
                    "workspace_scope": model.get("workspace_scope"),
                },
                "runtime": {
                    "population_mode": stage_profile.get("population_mode"),
                    "boot_priority": stage_profile.get("boot_priority"),
                    "launch_gate": launch_control.get("gate"),
                    "local_endpoint": endpoint_policy.get("base_url"),
                    "external_writes": "blocked_until_operator_approval",
                },
                "backend": {
                    "enabled": backend_enabled,
                    "role": defaults.get("backend_role"),
                    "input_count": len(input_paths),
                    "input_paths": input_paths[:8],
                    "output_roots": defaults.get("output_roots") or [],
                    "write_scope": "owned_floor_paths_only",
                },
                "frontend": {
                    "enabled": frontend_enabled,
                    "surface": defaults.get("frontend_surface"),
                    "space_id": space.get("space_id") or population.get("primary_space_id"),
                    "default_view": space.get("default_view"),
                    "density": smart_floor_spaces.get("default_density"),
                    "collapse_policy": smart_floor_spaces.get("collapse_policy"),
                },
                "build": {
                    "state": "enabled_local_gated" if backend_enabled and frontend_enabled else "staged_local_gated",
                    "lane_ids": lane_ids,
                    "ready_task_ids": task_ids,
                    "risk_level": "low",
                    "manual_gates": manual_gate_ids,
                    "next_safe_action": defaults.get("next_safe_action"),
                },
            }
        )

    return {
        "contract_id": "lightspeed_backend_frontend_build_contract_2026_05_28",
        "purpose": "Boil each LightSpeed agent floor into one backend spine and one frontend surface.",
        "policy": {
            "single_active_frontend": True,
            "backend_write_scope": "owned_floor_paths_only",
            "external_writes": "blocked_until_operator_approval",
            "local_llm_first": True,
            "manual_approval_required": True,
        },
        "summary": {
            "floor_count": len(floors),
            "backend_enabled_count": sum(1 for item in floors if item["backend"]["enabled"]),
            "frontend_enabled_count": sum(1 for item in floors if item["frontend"]["enabled"]),
            "agent_count": len({item["agent"]["agent_id"] for item in floors}),
            "ready_task_count": sum(len(item["build"]["ready_task_ids"]) for item in floors),
            "launch_gate": launch_control.get("gate"),
        },
        "floors": floors,
    }


_OUTSIDE_IN_REALIZATION_ORDER = [
    "Trinity",
    "Neo",
    "Architect",
    "TheConstruct",
    "Morpheus",
    "Oracle",
    "Smith",
    "Merovingian",
]


_REALIZATION_BLUEPRINTS = {
    "Trinity": {
        "environment_label": "Readable Operator Atrium",
        "ui_adapts_to": [
            "operator focus and visual load",
            "active approval gate",
            "current floor and queue pressure",
        ],
        "tool_transform": [
            "settings, themes, setup, approvals, and routing collapse into one operator rail",
            "secondary tools open as drawers or one active detail pane, not parallel windows",
        ],
        "post_population_path": [
            "show current floor, gate, and next safe action first",
            "make readability controls immediate and persistent",
            "route each floor action through the visible approval context",
        ],
    },
    "Neo": {
        "environment_label": "Local Orchestrator Console",
        "ui_adapts_to": [
            "active temp shell",
            "model budget",
            "handoff state between LightSpeed and De Sporte",
        ],
        "tool_transform": [
            "local prompts, file context, and task staging become one bounded orchestration deck",
            "Neo drafts into temp shells before Smith or Architect can promote work",
        ],
        "post_population_path": [
            "brief the current floor state",
            "stage the next local task",
            "hand off completed artifacts to Trinity review or Smith routing",
        ],
    },
    "Architect": {
        "environment_label": "Manual Publish Wall",
        "ui_adapts_to": [
            "approval state",
            "release packet completeness",
            "external write risk",
        ],
        "tool_transform": [
            "publish, repo, Drive, and web controls become one explicit yes/no gate",
            "release evidence is shown before any external mutation path",
        ],
        "post_population_path": [
            "assemble release packet",
            "validate source, proof, destination, and rollback",
            "wait for explicit operator approval before external writes",
        ],
    },
    "TheConstruct": {
        "environment_label": "Bounded Digital Twin Atrium",
        "ui_adapts_to": [
            "dataset proof level",
            "render budget",
            "scenario readiness",
        ],
        "tool_transform": [
            "datasets, scenario previews, render readiness, and virtual-space tests become one manual-heavy lab",
            "immersive mode remains explicit and reversible",
        ],
        "post_population_path": [
            "attach proofed datasets only",
            "generate scenario preview and missing-variable matrix",
            "run smoke render lanes before manual-heavy immersive activation",
        ],
    },
    "Morpheus": {
        "environment_label": "Review And Corroboration Chamber",
        "ui_adapts_to": [
            "evidence agreement",
            "diff pressure",
            "promotion readiness",
        ],
        "tool_transform": [
            "diffs, proof queues, and overlap evidence become one review split-view",
            "promotion proposals route back through Smith and Architect",
        ],
        "post_population_path": [
            "compare Oracle receipts and Smith notes",
            "mark consensus, converging, and held items",
            "produce promotion recommendation without self-promoting",
        ],
    },
    "Oracle": {
        "environment_label": "Reservoir And Provenance Library",
        "ui_adapts_to": [
            "source family",
            "receipt quality",
            "knowns and unknowns state",
        ],
        "tool_transform": [
            "reservoirs, receipts, datatables, and candidate knowns become one provenance workbench",
            "source attachment stays non-destructive and receipt-backed",
        ],
        "post_population_path": [
            "attach source roots",
            "extract receipts and compact tables",
            "send candidates to Morpheus for corroboration",
        ],
    },
    "Smith": {
        "environment_label": "Route Foundry",
        "ui_adapts_to": [
            "queue pressure",
            "write scope",
            "task risk",
        ],
        "tool_transform": [
            "build tasks, execution routes, and evidence notes become one gated queue",
            "workers remain owned-floor scoped with rollback evidence",
        ],
        "post_population_path": [
            "route no-risk tasks first",
            "record evidence note and owned write scope",
            "send promotion or publish candidates to Architect",
        ],
    },
    "Merovingian": {
        "environment_label": "Evidence Core",
        "ui_adapts_to": [
            "system pressure",
            "runtime health",
            "ledger and recovery state",
        ],
        "tool_transform": [
            "health, logs, ledgers, database checks, and recovery become one evidence panel",
            "failures are recorded as visible evidence rather than silent state",
        ],
        "post_population_path": [
            "snapshot process and model state",
            "append action ledger",
            "surface recovery or rollback requirements before deeper autonomy",
        ],
    },
}


def _floor_environment_realization_contract(
    *,
    backend_frontend_build: dict,
    floor_models: list[dict],
    launch_control: dict,
    neo_local_runtime: dict,
    agent_population: dict,
    floor_stage_population: dict,
    workspace_lanes: dict,
    gated_build_tasks: dict,
) -> dict:
    available_models = {
        str(model)
        for model in (neo_local_runtime.get("available_models") or [])
        if model
    }
    model_by_floor = {str(item.get("floor")): item for item in floor_models if item.get("floor")}
    build_by_floor = {
        str(item.get("floor")): item
        for item in (backend_frontend_build.get("floors") or [])
        if isinstance(item, dict) and item.get("floor")
    }
    stage_profiles = floor_stage_population.get("floor_profiles") or {}
    lane_by_id = {
        str(item.get("lane_id")): item
        for item in (workspace_lanes.get("lanes") or [])
        if isinstance(item, dict) and item.get("lane_id")
    }
    tasks_by_floor: dict[str, list[dict]] = defaultdict(list)
    for task in gated_build_tasks.get("tasks") or []:
        if isinstance(task, dict) and task.get("owner_floor"):
            tasks_by_floor[str(task["owner_floor"])].append(task)

    floors = []
    for index, floor in enumerate(_OUTSIDE_IN_REALIZATION_ORDER, start=1):
        build = build_by_floor.get(floor) or {}
        model = model_by_floor.get(floor) or (build.get("model") or {})
        blueprint = _REALIZATION_BLUEPRINTS.get(floor, {})
        build_state = build.get("build") or {}
        backend = build.get("backend") or {}
        frontend = build.get("frontend") or {}
        agent = build.get("agent") or {}
        model_tag = model.get("model")
        lane_ids = [str(item) for item in (build_state.get("lane_ids") or []) if item]
        ready_tasks = [
            item
            for item in tasks_by_floor.get(floor, [])
            if str(item.get("state") or "").startswith("ready")
        ]
        floors.append(
            {
                "floor": floor,
                "outside_in_order": index,
                "environment_label": blueprint.get("environment_label", floor),
                "agent": {
                    "agent_id": agent.get("agent_id") or floor.lower(),
                    "label": agent.get("label") or floor,
                    "support_resident_id": agent.get("support_resident_id"),
                    "resident_host": agent.get("resident_host"),
                },
                "model": {
                    "provider": model.get("provider", "ollama"),
                    "model": model_tag,
                    "persona": model.get("persona"),
                    "confirmed_installed": bool(model_tag in available_models),
                    "activation": "resident" if (stage_profiles.get(floor) or {}).get("population_mode") == "resident" else "on_demand_gated",
                    "max_parallel_tasks": model.get("max_parallel_tasks"),
                    "queue_limit": model.get("queue_limit"),
                },
                "population": {
                    "mode": (stage_profiles.get(floor) or {}).get("population_mode"),
                    "boot_priority": (stage_profiles.get(floor) or {}).get("boot_priority"),
                    "backend_ready": bool(backend.get("enabled")),
                    "frontend_ready": bool(frontend.get("enabled")),
                    "launch_gate": launch_control.get("gate"),
                    "external_writes": "blocked_until_operator_approval",
                },
                "ui_realization": {
                    "surface": frontend.get("surface"),
                    "space_id": frontend.get("space_id"),
                    "default_view": frontend.get("default_view"),
                    "adapts_to": blueprint.get("ui_adapts_to") or [],
                    "density": frontend.get("density"),
                    "collapse_policy": frontend.get("collapse_policy"),
                },
                "tool_realization": {
                    "backend_role": backend.get("role"),
                    "tool_transform": blueprint.get("tool_transform") or [],
                    "lane_ids": lane_ids,
                    "lanes": [
                        {
                            "lane_id": lane_id,
                            "label": (lane_by_id.get(lane_id) or {}).get("label"),
                            "owner_floor": (lane_by_id.get(lane_id) or {}).get("owner_floor"),
                            "state": (lane_by_id.get(lane_id) or {}).get("state"),
                        }
                        for lane_id in lane_ids
                    ],
                    "input_paths": backend.get("input_paths") or [],
                    "output_roots": backend.get("output_roots") or [],
                },
                "post_population": {
                    "path": blueprint.get("post_population_path") or [],
                    "ready_task_ids": [str(item.get("task_id")) for item in ready_tasks if item.get("task_id")],
                    "next_safe_action": build_state.get("next_safe_action"),
                    "manual_gates": build_state.get("manual_gates") or [],
                },
            }
        )

    cross_system_agents = []
    persona_runtime_path = Path(str((agent_population.get("resident_host_application") or {}).get("path") or "")) / "Config" / "persona_model_runtime.json"
    persona_runtime = _read_json_file(persona_runtime_path) if persona_runtime_path else {}
    for persona in persona_runtime.get("personas") or []:
        if not isinstance(persona, dict):
            continue
        model_tag = persona.get("primary_model_tag")
        cross_system_agents.append(
            {
                "persona_id": persona.get("persona_id"),
                "display_name": persona.get("display_name"),
                "host": "De Sporte",
                "primary_model": model_tag,
                "confirmed_installed": bool(model_tag in available_models),
                "lightspeed_scope": persona.get("lightspeed_scope"),
                "activation": "de_sporte_hosted_manual_or_policy",
            }
        )

    confirmed_floor_models = sum(1 for item in floors if (item.get("model") or {}).get("confirmed_installed"))
    return {
        "contract_id": "lightspeed_floor_environment_realization_2026_05_28",
        "purpose": "Tailor each populated floor into a concrete environment with UI, tools, model, and post-population path.",
        "realization_order": "outside_in_tailoring_with_stable_runtime_boot",
        "outside_in_order": _OUTSIDE_IN_REALIZATION_ORDER,
        "runtime_boot_order": floor_stage_population.get("boot_lane_order") or [],
        "model_confirmation_source": "neo_local_runtime.available_models",
        "policy": {
            "single_active_frontend": True,
            "resident_boot_stays_bounded": True,
            "staged_and_manual_heavy_floors_activate_on_demand": True,
            "all_external_writes_manual_gated": True,
            "avoid_previous_smart_floor_failure_modes": [
                "placeholder-only floors",
                "hyper-tabbed shells",
                "parallel popup workflows",
                "ungated background loops",
                "unconfirmed model routing",
            ],
        },
        "summary": {
            "floor_count": len(floors),
            "floor_models_confirmed": confirmed_floor_models,
            "cross_system_agent_count": len(cross_system_agents),
            "cross_system_models_confirmed": sum(1 for item in cross_system_agents if item.get("confirmed_installed")),
            "ready_task_count": sum(len((item.get("post_population") or {}).get("ready_task_ids") or []) for item in floors),
            "launch_gate": launch_control.get("gate"),
        },
        "floors": floors,
        "cross_system_agents": cross_system_agents,
    }


def _source_catalog_entry(manifest) -> dict:
    source_type_definition = get_source_type_definition(manifest.source_type)
    root = Path(manifest.root_path)
    return {
        "source_id": manifest.source_id,
        "source_label": manifest.source_label or manifest.source_id,
        "source_type": manifest.source_type,
        "source_type_label": source_type_definition.label if source_type_definition else manifest.source_type,
        "classification": manifest.classification,
        "root_path": manifest.root_path,
        "root_exists": root.exists(),
        "root_resolution": manifest.root_resolution,
        "trusted_document_count": len(manifest.trusted_documents),
    }


def _build_overlap_bellcurve(runtime: "LightSpeedRuntime", config: dict) -> dict:
    rules = config.get("consolidation_rules") or {}
    stopwords = {token.lower() for token in (rules.get("stopwords") or DEFAULT_STOPWORDS)}
    min_length = int(rules.get("minimum_token_length", 4))
    consensus_ratio = float((rules.get("corroboration_thresholds") or {}).get("consensus_ratio", 0.66))
    converging_ratio = float((rules.get("corroboration_thresholds") or {}).get("converging_ratio", 0.33))

    total_sources = max(1, len(runtime.registry.manifests()))
    assets = []
    for manifest in runtime.registry.manifests():
        for asset in runtime.registry.get_assets(manifest.source_id):
            if _is_low_signal_asset(asset.relative_path):
                continue
            assets.append(
                {
                    "source_id": manifest.source_id,
                    "source_label": manifest.source_label or manifest.source_id,
                    "classification": manifest.classification,
                    "canonical_rank": asset.canonical_rank,
                    "media_type": asset.media_type,
                    "title": asset.title,
                    "relative_path": asset.relative_path,
                }
            )

    title_groups: dict[str, list[dict]] = defaultdict(list)
    token_groups: dict[str, list[dict]] = defaultdict(list)
    for asset in assets:
        title_key = _normalize_title(asset["title"])
        if title_key:
            title_groups[title_key].append(asset)
        for token in _tokenize(asset["title"], stopwords=stopwords, min_length=min_length):
            token_groups[token].append(asset)

    clusters: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()
    for title_key, group in title_groups.items():
        cluster = _cluster_from_group(
            title_key,
            group,
            cluster_type="title",
            total_sources=total_sources,
            consensus_ratio=consensus_ratio,
            converging_ratio=converging_ratio,
        )
        if cluster:
            seen_keys.add(("title", title_key))
            clusters.append(cluster)

    for token, group in token_groups.items():
        if ("title", token) in seen_keys:
            continue
        cluster = _cluster_from_group(
            token,
            group,
            cluster_type="token",
            total_sources=total_sources,
            consensus_ratio=consensus_ratio,
            converging_ratio=converging_ratio,
        )
        if cluster:
            seen_keys.add(("token", token))
            clusters.append(cluster)

    clusters.sort(key=lambda item: (-item["signal_score"], item["cluster_key"]))
    summary = Counter(cluster["bellcurve_position"] for cluster in clusters)
    return {
        "summary": {
            "cluster_count": len(clusters),
            "consensus": summary.get("consensus", 0),
            "converging": summary.get("converging", 0),
            "outlier": summary.get("outlier", 0),
        },
        "clusters": clusters[: max(10, len(clusters))],
    }


def _cluster_from_group(
    cluster_key: str,
    group: list[dict],
    *,
    cluster_type: str,
    total_sources: int,
    consensus_ratio: float,
    converging_ratio: float,
) -> dict | None:
    source_ids = sorted({item["source_id"] for item in group})
    source_count = len(source_ids)
    if source_count < 2 and len(group) < 2:
        return None
    media_types = {str(item.get("media_type") or "") for item in group}
    if source_count == 1 and media_types == {"image"}:
        return None

    canonical_hits = sum(1 for item in group if item["canonical_rank"] == "canonical")
    reference_hits = sum(1 for item in group if item["canonical_rank"] == "reference")
    archive_hits = sum(1 for item in group if item["canonical_rank"] == "archive")
    coverage_ratio = source_count / max(1, total_sources)
    if coverage_ratio >= consensus_ratio:
        position = "consensus"
    elif coverage_ratio >= converging_ratio:
        position = "converging"
    else:
        position = "outlier"

    signal_score = round(
        ((canonical_hits * 2.0) + reference_hits + (archive_hits * 0.5)) * coverage_ratio,
        3,
    )
    items = []
    for entry in group[:8]:
        items.append(
            {
                "source_id": entry["source_id"],
                "source_label": entry["source_label"],
                "classification": entry["classification"],
                "canonical_rank": entry["canonical_rank"],
                "title": entry["title"],
                "relative_path": entry["relative_path"],
            }
        )
    return {
        "cluster_key": cluster_key,
        "cluster_type": cluster_type,
        "source_count": source_count,
        "coverage_ratio": round(coverage_ratio, 3),
        "bellcurve_position": position,
        "signal_score": signal_score,
        "canonical_hits": canonical_hits,
        "reference_hits": reference_hits,
        "archive_hits": archive_hits,
        "items": items,
    }


def _build_consolidation_queue(runtime: "LightSpeedRuntime", overlap: dict) -> list[dict]:
    queue: list[dict] = []
    cluster_lookup = {
        cluster["cluster_key"]: cluster
        for cluster in overlap.get("clusters", [])
    }
    for cluster in overlap.get("clusters", []):
        if cluster["bellcurve_position"] == "consensus":
            queue_type = "promote_overlap_to_known"
            priority = "high"
        elif cluster["bellcurve_position"] == "converging":
            queue_type = "corroborate_overlap"
            priority = "medium"
        else:
            queue_type = "review_outlier"
            priority = "low"
        queue.append(
            {
                "queue_id": f"queue_{cluster['cluster_type']}_{cluster['cluster_key']}",
                "queue_type": queue_type,
                "priority": priority,
                "cluster_key": cluster["cluster_key"],
                "bellcurve_position": cluster["bellcurve_position"],
                "signal_score": cluster["signal_score"],
                "source_count": cluster["source_count"],
                "target_floor": "Oracle" if queue_type != "review_outlier" else "Morpheus",
                "suggested_action": _suggested_action(queue_type, cluster),
            }
        )

    known_clusters = set(cluster_lookup)
    for manifest in runtime.registry.manifests():
        for asset in runtime.registry.get_assets(manifest.source_id):
            title_key = _normalize_title(asset.title)
            if asset.canonical_rank != "canonical":
                continue
            if title_key in known_clusters:
                continue
            queue.append(
                {
                    "queue_id": f"queue_corroborate_{asset.asset_id}",
                    "queue_type": "corroborate_canonical",
                    "priority": "medium",
                    "cluster_key": title_key or asset.asset_id,
                    "bellcurve_position": "outlier",
                    "signal_score": 1.0,
                    "source_count": 1,
                    "target_floor": "Morpheus",
                    "suggested_action": (
                        f"Find corroborating empirical or reference support for canonical asset '{asset.title}'."
                    ),
                }
            )

    queue.sort(
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}.get(item["priority"], 3),
            -float(item["signal_score"]),
            item["queue_id"],
        )
    )
    return queue


def _suggested_action(queue_type: str, cluster: dict) -> str:
    if queue_type == "promote_overlap_to_known":
        return (
            f"Promote overlap cluster '{cluster['cluster_key']}' into proofed knowns and attach source receipts."
        )
    if queue_type == "corroborate_overlap":
        return (
            f"Corroborate converging cluster '{cluster['cluster_key']}' against empirical tables before promotion."
        )
    return (
        f"Review outlier cluster '{cluster['cluster_key']}' for archive drift, duplicate naming, or false overlap."
    )


def _intake_decision(classification: str) -> str:
    if classification == "canonical":
        return "active_truth"
    if classification == "reference":
        return "supporting_truth"
    return "archive_reference"


def _default_allowed_for(classification: str) -> list[str]:
    if classification == "canonical":
        return ["knowns", "briefing", "publish_review"]
    if classification == "reference":
        return ["corroboration", "labs", "proofing"]
    return ["backtracking", "recovery"]


def _normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _tokenize(value: str, *, stopwords: set[str], min_length: int) -> list[str]:
    tokens = []
    for token in re.findall(r"[A-Za-z0-9]+", value.lower()):
        if len(token) < min_length or token in stopwords:
            continue
        tokens.append(token)
    return tokens


def _is_low_signal_asset(relative_path: str) -> bool:
    lowered = relative_path.lower().replace("\\", "/")
    if any(marker in lowered for marker in LOW_SIGNAL_PATH_MARKERS):
        return True
    name = Path(lowered).name
    return name in LOW_SIGNAL_FILENAMES


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _annotate_root_entries(entries: object, *, path_key: str = "path") -> list[dict]:
    rows: list[dict] = []
    for item in entries or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        value = row.get(path_key)
        if isinstance(value, str) and value:
            row["exists"] = Path(value).exists()
        rows.append(row)
    return rows


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_shell_artifacts(payload: dict) -> dict[str, str]:
    environment = payload.get("environment") or {}
    paths = environment.get("paths") or {}
    shell_root_payload = paths.get("desktop_shell_root") if isinstance(paths, dict) else None
    shell_root_value = shell_root_payload.get("path") if isinstance(shell_root_payload, dict) else None
    if not isinstance(shell_root_value, str) or not shell_root_value:
        return {}

    shell_root = Path(shell_root_value)
    if not shell_root.exists():
        return {}

    outputs = {
        "deployment_topology": shell_root / "config" / "deployment_topology.json",
        "host_runtime_policy": shell_root / "config" / "host_runtime_policy.json",
        "presence_roster": shell_root / "config" / "presence_roster.json",
        "neo_local_runtime": shell_root / "config" / "neo_local_runtime.json",
        "neo_realisation_runtime": shell_root / "config" / "neo_realisation_runtime.json",
        "upstream_inventory": shell_root / "config" / "upstream_inventory.json",
        "launch_control": shell_root / "config" / "launch_control.json",
        "agent_population": shell_root / "config" / "agent_population.json",
        "input_staging_matrix": shell_root / "config" / "input_staging_matrix.json",
        "backend_frontend_build": shell_root / "config" / "backend_frontend_build_contract.json",
        "floor_environment_realization": shell_root / "config" / "floor_environment_realization_contract.json",
        "local_agent_wakeup": shell_root / "config" / "local_agent_wakeup_contract.json",
        "workspace_lanes": shell_root / "config" / "workspace_lanes.json",
        "neo_temp_shell_registry": shell_root / "Z Axis" / "Z+2_Neo" / "data" / "temp_shells" / "temp_shell_registry.json",
        "floor_stage_population": shell_root / "Z Axis" / "Z-3_Smith" / "data" / "staging" / "floor_stage_population.json",
        "gated_build_tasks": shell_root / "Z Axis" / "Z-3_Smith" / "data" / "staging" / "gated_build_tasks.json",
        "construct_runtime_profile": shell_root / "Z Axis" / "Z0_TheConstruct" / "data" / "runtime" / "construct_runtime_profile.json",
        "smart_floor_spaces": shell_root / "Z Axis" / "Z0_TheConstruct" / "data" / "runtime" / "smart_floor_spaces.json",
        "virtual_space_test_matrix": shell_root / "Z Axis" / "Z0_TheConstruct" / "data" / "runtime" / "virtual_space_test_matrix.json",
    }
    _write_json(outputs["deployment_topology"], payload.get("deployment_topology") or {})
    _write_json(outputs["host_runtime_policy"], payload.get("host_runtime_policy") or {})
    _write_json(outputs["presence_roster"], payload.get("presence_roster") or {})
    _write_json(outputs["neo_local_runtime"], payload.get("neo_local_runtime") or {})
    _write_json(outputs["neo_realisation_runtime"], payload.get("neo_realisation_runtime") or {})
    _write_json(outputs["upstream_inventory"], payload.get("upstream_inventory") or {})
    _write_json(outputs["launch_control"], payload.get("launch_control") or {})
    _write_json(outputs["agent_population"], payload.get("agent_population") or {})
    _write_json(outputs["input_staging_matrix"], payload.get("input_staging_matrix") or {})
    _write_json(outputs["backend_frontend_build"], payload.get("backend_frontend_build") or {})
    _write_json(outputs["floor_environment_realization"], payload.get("floor_environment_realization") or {})
    _write_json(outputs["local_agent_wakeup"], payload.get("local_agent_wakeup") or {})
    _write_json(outputs["workspace_lanes"], payload.get("workspace_lanes") or {})
    neo_local_runtime = payload.get("neo_local_runtime") or {}
    _write_json(
        outputs["neo_temp_shell_registry"],
        {
            "runtime_id": neo_local_runtime.get("runtime_id"),
            "primary_floor": neo_local_runtime.get("primary_floor"),
            "local_endpoint": (neo_local_runtime.get("endpoint_policy") or {}).get("base_url"),
            "temp_shells": neo_local_runtime.get("temp_shells") or [],
            "handoff_contract": neo_local_runtime.get("handoff_contract") or {},
        },
    )
    _write_json(outputs["floor_stage_population"], payload.get("floor_stage_population") or {})
    _write_json(outputs["gated_build_tasks"], payload.get("gated_build_tasks") or {})
    _write_json(outputs["construct_runtime_profile"], payload.get("construct_runtime") or {})
    _write_json(outputs["smart_floor_spaces"], payload.get("smart_floor_spaces") or {})
    construct_runtime = payload.get("construct_runtime") or {}
    virtual_space_test_matrix = {
        "profile_id": construct_runtime.get("profile_id"),
        "default_surface": construct_runtime.get("default_surface"),
        "resource_guards": construct_runtime.get("resource_guards") or {},
        "secondary_data_policy": construct_runtime.get("secondary_data_policy") or {},
        "virtual_space_tests": construct_runtime.get("virtual_space_tests") or {},
    }
    _write_json(outputs["virtual_space_test_matrix"], virtual_space_test_matrix)

    launch_control = payload.get("launch_control") or {}
    co_runner = launch_control.get("co_runner") or {}
    handoff_path_value = co_runner.get("handoff_path")
    co_runner_state = str(co_runner.get("state") or "").strip().lower()
    handoff_enabled = (
        bool(co_runner_state)
        and not any(marker in co_runner_state for marker in ("hold", "disabled", "paused", "offline"))
        and any(marker in co_runner_state for marker in ("active", "connected", "detected", "running"))
    )
    handoff_output = None
    if handoff_enabled and isinstance(handoff_path_value, str) and handoff_path_value:
        handoff_output = Path(handoff_path_value)
        _write_json(
            handoff_output,
            {
                "handoff_id": launch_control.get("control_id"),
                "generated_at": payload.get("generated_at"),
                "gate": launch_control.get("gate"),
                "state": launch_control.get("state"),
                "current_focus": launch_control.get("current_focus"),
                "launch_targets": launch_control.get("launch_targets") or [],
                "local_runtime": {
                    "profile_id": payload.get("profile_id"),
                    "primary_surface": (payload.get("workspace_lanes") or {}).get("primary_surface"),
                    "neo_runtime_id": (payload.get("neo_local_runtime") or {}).get("runtime_id"),
                    "de_sporte_root": ((payload.get("agent_population") or {}).get("resident_host_application") or {}).get("path"),
                },
                "upstream_refs": ((payload.get("upstream_inventory") or {}).get("primary_sources") or []),
                "next_actions": launch_control.get("next_actions") or [],
                "manual_gates": launch_control.get("manual_gates") or [],
            },
        )

    shell_files = {key: str(path) for key, path in outputs.items()}
    if handoff_output is not None:
        shell_files["co_runner_handoff"] = str(handoff_output)
    return shell_files
