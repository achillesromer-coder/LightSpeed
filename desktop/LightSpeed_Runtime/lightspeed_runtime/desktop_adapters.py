from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Iterable


_UI_STATE_LABELS = {
    "loading": "Loading",
    "empty": "Empty",
    "success": "Ready",
    "error": "Action needed",
    "info": "Info",
}


def _ui_state(kind: str, message: str) -> str:
    return f"{_UI_STATE_LABELS.get(kind, 'Info')}: {message}"


def format_search_empty_state(query: str, source_value: str) -> str:
    active_source = source_value if source_value not in {"", "All"} else "All configured sources"
    query_text = query or "(empty query)"
    return "\n".join(
        [
            "No matching canonical reservoir assets.",
            f"Query: {query_text}",
            f"Source filter: {active_source}",
            "Try a document title, a trusted known, or a source-specific term.",
        ]
    )


def format_workspace_snapshot(snapshot: dict) -> str:
    workspace = snapshot.get("workspace") or {}
    latest_runs = snapshot.get("latest_runs") or []
    actions = snapshot.get("actions") or []
    lines = [
        f"Workspace: {workspace.get('workspace_id', 'unknown')} | Project: {workspace.get('project_id', 'unknown')} | Floor: {workspace.get('active_floor', 'unknown')}",
        f"State: {workspace.get('status', 'open')} | Pending approvals: {workspace.get('approvals_pending', 0)}",
        f"Runs: {len(latest_runs)} | Actions: {len(actions)}",
    ]
    if snapshot.get("latest_publish_manifest"):
        lines.append("Publish manifest: available")
    if snapshot.get("latest_package_metadata"):
        lines.append("Package metadata: available")
    return "\n".join(lines)


def format_run_snapshot(run: dict) -> str:
    lines = [
        f"Run: {run.get('run_id', 'unknown')} | {run.get('lab_type', 'unknown')} | {run.get('status', 'unknown')}",
        f"Scenario: {run.get('scenario_id', 'unknown')} | Engine: {run.get('engine', 'unknown')}",
        f"Dataset refs: {len(run.get('dataset_refs') or [])} | Outputs: {len(run.get('outputs') or [])}",
    ]
    metrics = run.get("metrics") or {}
    if metrics:
        lines.append("Metrics: " + ", ".join(f"{key}={value}" for key, value in sorted(metrics.items())))
    return "\n".join(lines)


def format_operator_brief(brief: dict) -> str:
    results = brief.get("results") or []
    lines = [
        f"Operator: {brief.get('operator', 'Achilles')} | Query: {brief.get('query', '')}",
        f"Matches: {brief.get('retrieval_count', len(results))}",
    ]
    for item in results[:5]:
        lines.append(f"- {item.get('canonical_rank', 'reference')} | {item.get('source_label') or item.get('source_id')} | {item.get('title')}")
    return "\n".join(lines)


def resolve_runtime_bridge(app: object | None):
    if app is None:
        return None
    return getattr(app, "oracle_morpheus_bridge", None)


def resolve_runtime_shell_bridge(app: object | None):
    if app is None:
        return None
    return getattr(app, "trinity_shell_bridge", None)


def resolve_agent_home_bridge(app: object | None):
    if app is None:
        return None
    return getattr(app, "agent_home_bridge", None)


def _replace_text(widget: tk.Text, payload: str) -> None:
    try:
        widget.delete("1.0", "end")
    except Exception:
        return
    widget.insert("1.0", payload)


def format_agent_home_overview(summary: dict) -> str:
    truth = summary.get("truth_registry") or {}
    floors = summary.get("floor_models") or {}
    queue = summary.get("consolidation_queue") or {}
    overlap = summary.get("overlap_bellcurve") or {}
    active_truth = truth.get("active_truth_entries") or []
    by_priority = queue.get("by_priority") or {}
    return "\n".join(
        [
            f"Profile: {summary.get('profile_id', 'unknown')}",
            f"Generated: {summary.get('generated_at', 'unknown')}",
            (
                "Truth registry: "
                f"{truth.get('total_entries', 0)} entries | "
                f"{truth.get('registered_source_count', 0)} registered sources | "
                f"{truth.get('truth_layer_count', 0)} truth layers"
            ),
            (
                "Governance: "
                f"{len(active_truth)} active truth entries | "
                f"{truth.get('publish_eligible_count', 0)} publish eligible"
            ),
            (
                "Floor models: "
                f"{floors.get('enabled_count', 0)}/{floors.get('total_floors', 0)} enabled | "
                f"{floors.get('approval_required_count', 0)} approval gated"
            ),
            (
                "Consolidation queue: "
                f"{queue.get('total_items', 0)} items | "
                f"high={by_priority.get('high', 0)} | "
                f"medium={by_priority.get('medium', 0)}"
            ),
            (
                "Overlap bellcurve: "
                f"{overlap.get('cluster_count', 0)} clusters | "
                f"consensus={overlap.get('consensus_count', 0)} | "
                f"converging={overlap.get('converging_count', 0)} | "
                f"outlier={overlap.get('outlier_count', 0)}"
            ),
        ]
    )


def format_floor_model_focus(summary: dict, floor: str) -> str:
    floor_models = summary.get("floor_models") or {}
    assignment = (floor_models.get("by_floor") or {}).get(floor) or {}
    if not assignment:
        return f"{floor} model assignment unavailable."
    return (
        f"{floor} model: {assignment.get('model', 'unknown')} | "
        f"persona: {assignment.get('persona', 'unknown')} | "
        f"workspace: {assignment.get('workspace_scope', 'unknown')} | "
        f"enabled: {bool(assignment.get('enabled'))}"
    )


def format_host_runtime_policy_focus(summary: dict) -> str:
    host = summary.get("host_runtime_policy") or {}
    return "\n".join(
        [
            f"Host policy: {host.get('policy_id', 'unknown')}",
            (
                f"CPU: {host.get('cpu', 'unknown')} | "
                f"RAM: {host.get('ram_gb', 'n/a')} GB @ {host.get('ram_speed_mt_s', 'n/a')} MT/s | "
                f"GPU: {host.get('gpu', 'unknown')}"
            ),
            (
                f"Roots: Windows {host.get('windows_root', 'unknown')} | "
                f"Workspace {host.get('workspace_root', 'unknown')}"
            ),
            (
                f"Limits: boot_parallel={host.get('max_floor_boot_parallelism', 'n/a')} | "
                f"heavy_floors={host.get('max_active_heavy_floors', 'n/a')} | "
                f"ollama_jobs={host.get('max_concurrent_ollama_jobs', 'n/a')} | "
                f"construct_widgets={host.get('construct_widget_budget', 'n/a')}"
            ),
            (
                f"Interactive: mode={host.get('interactive_session_mode', 'unknown')} | "
                f"browser={host.get('interactive_browser', 'unknown')} | "
                f"chrome_headroom={host.get('chrome_reserved_ram_gb', 'n/a')}GB/"
                f"{host.get('chrome_reserved_threads', 'n/a')} threads | "
                f"ui_panels={host.get('lightspeed_max_resident_ui_panels', 'n/a')}"
            ),
            (
                f"Pressure handling: pause_on_pressure={bool(host.get('background_pause_on_pressure'))} | "
                f"chrome_mode={host.get('chrome_mode', 'unknown')} | "
                f"de_sporte={host.get('de_sporte_mode', 'unknown')}"
            ),
        ]
    )


def format_deployment_topology_focus(summary: dict) -> str:
    topology = summary.get("deployment_topology") or {}
    authoritative_roots = topology.get("authoritative_roots") or []
    reference_roots = topology.get("reference_roots") or []
    lines = [
        (
            f"Topology: {topology.get('topology_id', 'unknown')} | "
            f"authoritative={topology.get('authoritative_root_count', len(authoritative_roots))} | "
            f"reference={topology.get('reference_root_count', len(reference_roots))}"
        )
    ]
    if authoritative_roots:
        lines.append("Authoritative roots:")
        for item in authoritative_roots[:3]:
            lines.append(
                f"- {item.get('label', 'root')} | {item.get('role', 'unknown')} | exists={bool(item.get('exists'))}"
            )
    migration = topology.get("migration_policy") or {}
    if migration:
        lines.append(
            "Migration: "
            f"D={migration.get('d_drive_mode', 'unknown')} | "
            f"C={migration.get('c_drive_role', 'unknown')}"
        )
    return "\n".join(lines)


def format_stage_population_focus(summary: dict, floor: str) -> str:
    stage = summary.get("floor_stage_population") or {}
    profiles = stage.get("floor_profiles") or {}
    profile = profiles.get(floor) or {}
    if not profile:
        return f"{floor} stage population unavailable."
    return "\n".join(
        [
            f"Stage policy: {stage.get('policy_id', 'unknown')}",
            (
                f"{floor} population: {profile.get('population_mode', 'unknown')} | "
                f"boot_priority={profile.get('boot_priority', 'n/a')}"
            ),
            (
                f"Resident={len(stage.get('resident_floors') or [])} | "
                f"staged={len(stage.get('staged_floors') or [])} | "
                f"manual_heavy={len(stage.get('manual_heavy_floors') or [])} | "
                f"heavy_limit={stage.get('heavy_floor_limit', 'n/a')}"
            ),
            f"Reason: {profile.get('reason', 'No reason exported.')}",
        ]
    )


def format_construct_runtime_focus(summary: dict) -> str:
    construct = summary.get("construct_runtime") or {}
    mode_targets = construct.get("mode_targets") or {}
    modes = construct.get("render_modes") or []
    mode_text = ", ".join(f"{mode}={mode_targets.get(mode, 'n/a')}fps" for mode in modes) if modes else "none"
    return "\n".join(
        [
            f"Construct runtime: {construct.get('profile_id', 'unknown')}",
            (
                f"Surface: {construct.get('default_surface', 'unknown')} | "
                f"hint={construct.get('stage_population_hint', 'unknown')} | "
                f"model={construct.get('theconstruct_model', 'unknown')}"
            ),
            f"Render modes: {mode_text}",
            (
                f"Resource guards: widgets={construct.get('max_visible_widgets', 'n/a')} | "
                f"texture_panels={construct.get('max_live_texture_panels', 'n/a')} | "
                f"smoke_lanes={construct.get('smoke_lane_count', 0)} | "
                f"manual_lanes={construct.get('manual_lane_count', 0)}"
            ),
        ]
    )


def format_presence_roster_focus(summary: dict) -> str:
    roster = summary.get("presence_roster") or {}
    weekly_rotation = roster.get("weekly_rotation") or []
    lines = [
        (
            f"Presence roster: {roster.get('roster_id', 'unknown')} | "
            f"mode={roster.get('schedule_model', 'unknown')} | "
            f"tz={roster.get('timezone', 'unknown')}"
        ),
        (
            f"Split: LightSpeed={roster.get('lightspeed_logged_in_percent', 'n/a')}% | "
            f"remaining={roster.get('remaining_window_percent', 'n/a')}% | "
            f"DeSporte idle={roster.get('de_sporte_idle_persistence_percent_of_remaining_window', 'n/a')}% | "
            f"DeSporte active={roster.get('de_sporte_active_percent_of_remaining_window', 'n/a')}%"
        ),
        (
            f"Cascade overlap={roster.get('cascade_overlap_percent', 'n/a')}% | "
            f"speed_factor={roster.get('interaction_speed_factor', 'n/a')} | "
            f"days={roster.get('rotation_day_count', len(weekly_rotation))}"
        ),
    ]
    callout_policy = roster.get("callout_policy") or {}
    if callout_policy:
        lines.append(
            "Callout: "
            f"{callout_policy.get('idle_presence_mode', 'unknown')} | "
            f"{callout_policy.get('reactivation_policy', 'unknown')}"
        )
    if weekly_rotation:
        first = weekly_rotation[0]
        lines.append(
            "Rotation sample: "
            f"{first.get('day', 'unknown')} -> "
            f"{', '.join(str(item) for item in (first.get('lightspeed_focus') or [])[:3])} | "
            f"overlap={', '.join(str(item) for item in (first.get('overlap_windows') or [])[:2])}"
        )
    return "\n".join(lines)


def format_neo_local_runtime_focus(summary: dict) -> str:
    payload = summary.get("neo_local_runtime") or {}
    lines = [
        (
            f"Neo local runtime: {payload.get('runtime_id', 'unknown')} | "
            f"state={payload.get('state', 'unknown')} | "
            f"profile={payload.get('active_profile', 'unknown')}"
        ),
        (
            f"Endpoint: {payload.get('provider', 'unknown')} @ {payload.get('base_url', 'unknown')} | "
            f"local_only={bool(payload.get('local_only', True))} | "
            f"auto_start={payload.get('auto_start_mode', 'unknown')}"
        ),
        (
            f"Models={payload.get('available_model_count', 0)} | "
            f"temp_shells={payload.get('temp_shell_count', 0)} | "
            f"editor={payload.get('editor_surface', 'unknown')}"
        ),
    ]
    available_models = payload.get("available_models") or []
    if available_models:
        lines.append("Available models: " + ", ".join(str(item) for item in available_models[:4]))
    return "\n".join(lines)


def format_de_sporte_runtime_focus(summary: dict) -> str:
    payload = summary.get("de_sporte_runtime") or {}
    lines = [
        (
            f"De Sporte runtime: {payload.get('label', 'unknown')} | "
            f"root_exists={bool(payload.get('root_exists'))} | "
            f"zone={payload.get('current_zone', 'unknown')}"
        ),
        (
            f"Residents={payload.get('resident_count', 0)} | "
            f"personas={payload.get('persona_count', 0)} | "
            f"support_exports={payload.get('support_export_count', 0)}"
        ),
        (
            f"Raphael={payload.get('raphael_model', 'unknown')} | "
            f"Achilles={payload.get('achilles_model', 'unknown')} | "
            f"Neo={payload.get('neo_model', 'unknown')}"
        ),
    ]
    if payload.get("habitat_anchor"):
        lines.append(f"Habitat anchor: {payload.get('habitat_anchor')}")
    if payload.get("resident_heartbeat_status"):
        lines.append(f"Resident heartbeat: {payload.get('resident_heartbeat_status')}")
    return "\n".join(lines)


def format_neo_realisation_focus(summary: dict) -> str:
    payload = summary.get("neo_realisation_runtime") or {}
    current = payload.get("current_wave") or {}
    lines = [
        (
            f"Neo realisation: {payload.get('runtime_id', 'unknown')} | "
            f"state={payload.get('state', 'unknown')} | "
            f"mode={payload.get('mentorship_mode', 'unknown')}"
        ),
        (
            f"Approval={payload.get('approval_mode', 'unknown')} | "
            f"waves={payload.get('wave_count', 0)} | "
            f"training_loops={payload.get('training_loop_count', 0)}"
        ),
        (
            f"Current wave: {payload.get('current_wave_label', 'unknown')} | "
            f"state={payload.get('current_wave_state', 'unknown')} | "
            f"tasks={payload.get('current_wave_task_count', 0)} | "
            f"training={payload.get('current_wave_training_loop_count', 0)}"
        ),
    ]
    if current.get("goal"):
        lines.append(f"Goal: {current.get('goal')}")
    guardrails = payload.get("guardrails") or []
    if guardrails:
        lines.append("Guardrails: " + "; ".join(str(item) for item in guardrails[:2]))
    return "\n".join(lines)


def format_upstream_inventory_focus(summary: dict) -> str:
    payload = summary.get("upstream_inventory") or {}
    drive_roots = payload.get("drive_roots") or []
    repo_names = payload.get("repo_names") or []
    spreadsheet_labels = payload.get("spreadsheet_labels") or []
    lines = [
        (
            f"Upstream inventory: {payload.get('inventory_id', 'unknown')} | "
            f"mode={payload.get('mode', 'unknown')}"
        ),
        (
            f"Repos={payload.get('connected_repo_count', 0)}/{payload.get('declared_repo_count', 0)} connected | "
            f"Drive roots={payload.get('drive_root_count', 0)} | "
            f"Sheets={payload.get('spreadsheet_count', 0)}"
        ),
    ]
    if repo_names:
        lines.append("Repos: " + ", ".join(str(item) for item in repo_names[:4]))
    if drive_roots:
        lines.append(
            "Drive roots: "
            + ", ".join(
                f"{item.get('label', 'root')} ({item.get('item_count', 0)})"
                for item in drive_roots[:3]
            )
        )
    if spreadsheet_labels:
        lines.append("Sheets: " + ", ".join(str(item) for item in spreadsheet_labels[:3]))
    return "\n".join(lines)


def format_launch_control_focus(summary: dict) -> str:
    payload = summary.get("launch_control") or {}
    co_runner = payload.get("co_runner") or {}
    lines = [
        (
            f"Launch control: {payload.get('control_id', 'unknown')} | "
            f"gate={payload.get('gate', 'unknown')} | "
            f"state={payload.get('state', 'unknown')}"
        ),
        (
            f"Focus: {payload.get('current_focus', 'unknown')} | "
            f"sequence={payload.get('sequence_ready_count', 0)}/{payload.get('sequence_total', 0)} | "
            f"readiness={payload.get('readiness_ready_count', 0)}/{payload.get('readiness_total', 0)}"
        ),
        (
            f"Blockers={payload.get('blocker_count', 0)} | "
            f"co-runner={co_runner.get('host_application', 'unknown')} | "
            f"handoff={bool(co_runner.get('handoff_exists'))}"
        ),
    ]
    next_actions = payload.get("next_actions") or []
    if next_actions:
        lines.append("Next: " + "; ".join(str(item) for item in next_actions[:2]))
    return "\n".join(lines)


def format_agent_population_focus(
    summary: dict,
    *,
    floors: Iterable[str] | None = None,
    top_n: int = 8,
) -> str:
    population = summary.get("agent_population") or {}
    rows = population.get("floor_assignments") or []
    focus_set = {item for item in (floors or []) if item}
    filtered_rows = [item for item in rows if not focus_set or item.get("floor") in focus_set]
    host = population.get("resident_host_application") or {}
    lines = [
        (
            f"Agent population: {population.get('contract_id', 'unknown')} | "
            f"rule={population.get('population_rule', 'unknown')} | "
            f"floors={population.get('floor_assignment_count', len(rows))}"
        )
    ]
    if host:
        lines.append(
            f"Resident host: {host.get('label', 'unknown')} | role={host.get('role', 'unknown')}"
        )
    cross_system_roles = population.get("cross_system_roles") or []
    if cross_system_roles:
        lines.append(
            "Cross-system roles: "
            + ", ".join(
                str(item.get("agent_id"))
                for item in cross_system_roles[:4]
                if item.get("agent_id")
            )
        )
    workset = filtered_rows or rows[: max(0, top_n)]
    if not workset:
        lines.append("Floor assignments: none exported.")
        return "\n".join(lines)
    lines.append("Floor assignments:")
    for item in workset[: max(0, top_n)]:
        lines.append(
            "- "
            f"{item.get('floor', 'unknown')} | "
            f"agent={item.get('assigned_agent_id', 'unknown')} | "
            f"support={item.get('de_sporte_support_resident_id', 'none')} | "
            f"space={item.get('primary_space_id', 'unknown')}"
        )
    return "\n".join(lines)


def format_input_staging_focus(
    summary: dict,
    *,
    floors: Iterable[str] | None = None,
    top_n: int = 8,
) -> str:
    matrix = summary.get("input_staging_matrix") or {}
    rows = matrix.get("floors") or []
    focus_set = {item for item in (floors or []) if item}
    filtered_rows = [item for item in rows if not focus_set or item.get("floor") in focus_set]
    lines = [
        (
            f"Input staging: {matrix.get('matrix_id', 'unknown')} | "
            f"floors={matrix.get('floor_count', len(rows))} | "
            f"components={matrix.get('live_component_count', 0)}/{matrix.get('total_components', 0)} live"
        )
    ]
    policy = matrix.get("policy")
    if policy:
        lines.append(f"Policy: {policy}")
    shared_rules = matrix.get("shared_rules") or []
    if shared_rules:
        lines.append("Rules: " + "; ".join(str(item) for item in shared_rules[:2]))
    workset = filtered_rows or rows[: max(0, top_n)]
    if not workset:
        lines.append("Floor components: none exported.")
        return "\n".join(lines)
    lines.append("Floor components:")
    for item in workset[: max(0, top_n)]:
        component_ids = item.get("component_ids") or []
        lines.append(
            "- "
            f"{item.get('floor', 'unknown')} | "
            f"space={item.get('space_id', 'unknown')} | "
            f"live={item.get('path_exists_count', 0)}/{item.get('component_count', 0)} | "
            f"{', '.join(str(component) for component in component_ids[:3]) or 'no components'}"
        )
    return "\n".join(lines)


def format_truth_registry_focus(summary: dict, *, top_n: int = 6) -> str:
    truth = summary.get("truth_registry") or {}
    active_truth = truth.get("active_truth_entries") or []
    if not active_truth:
        return "Active truth entries: none exported."
    lines = [f"Active truth entries ({len(active_truth)}):"]
    for entry in active_truth[: max(0, top_n)]:
        lines.append(f"- {entry}")
    return "\n".join(lines)


def format_queue_workset(summary: dict, *, focus_floors: Iterable[str] | None = None, top_n: int = 5) -> str:
    queue = summary.get("consolidation_queue") or {}
    by_target_floor = queue.get("by_target_floor") or {}
    top_items = queue.get("top_items") or []
    focus_set = {item for item in (focus_floors or []) if item}
    filtered_items = [
        item for item in top_items if not focus_set or item.get("target_floor") in focus_set
    ]
    target_pairs = sorted(
        (
            floor,
            count,
        )
        for floor, count in by_target_floor.items()
        if not focus_set or floor in focus_set
    )
    lines = []
    if target_pairs:
        lines.append(
            "Queue targets: " + ", ".join(f"{floor}={count}" for floor, count in target_pairs)
        )
    else:
        lines.append("Queue targets: none exported.")
    workset = filtered_items or top_items[: max(0, top_n)]
    if not workset:
        lines.append("Top routed items: none exported.")
        return "\n".join(lines)
    lines.append("Top routed items:")
    for item in workset[: max(0, top_n)]:
        lines.append(
            "- "
            f"{item.get('queue_id', 'unknown')} | "
            f"{item.get('priority', 'unknown')} | "
            f"{item.get('queue_type', 'unknown')} -> "
            f"{item.get('target_floor', 'unknown')} | "
            f"{item.get('cluster_key', 'unknown')} | "
            f"signal={item.get('signal_score', 'n/a')}"
        )
    return "\n".join(lines)


def format_overlap_snapshot(summary: dict, *, top_n: int = 5) -> str:
    overlap = summary.get("overlap_bellcurve") or {}
    top_clusters = overlap.get("top_clusters") or []
    if not top_clusters:
        return "Top overlap clusters: none exported."
    lines = ["Top overlap clusters:"]
    for item in top_clusters[: max(0, top_n)]:
        lines.append(
            "- "
            f"{item.get('cluster_key', 'unknown')} | "
            f"{item.get('bellcurve_position', 'unknown')} | "
            f"{item.get('cluster_type', 'unknown')} | "
            f"sources={item.get('source_count', 'n/a')} | "
            f"signal={item.get('signal_score', 'n/a')}"
        )
    return "\n".join(lines)


def format_workspace_lanes_focus(summary: dict, *, top_n: int = 6) -> str:
    lanes = summary.get("workspace_lanes") or {}
    lane_rows = lanes.get("lanes") or []
    manual_activation_lanes = lanes.get("manual_activation_lanes") or []
    avoid_patterns = lanes.get("avoid_patterns") or []
    lines = [
        (
            f"Lanes: {lanes.get('lane_set_id', 'unknown')} | "
            f"primary={lanes.get('primary_surface', 'unknown')} | "
            f"mode={lanes.get('interface_mode', 'unknown')} | "
            f"density={lanes.get('surface_density', 'unknown')}"
        ),
        (
            f"Ready lanes: {lanes.get('ready_lane_count', 0)}/{lanes.get('lane_count', len(lane_rows))} | "
            f"approval input={lanes.get('approval_input_mode', 'unknown')}"
        ),
    ]
    goal = lanes.get("minimum_system_goal")
    if goal:
        lines.append(f"Minimum system goal: {goal}")
    if lanes.get("chrome_safe_mode") is not None:
        lines.append(f"Chrome-safe mode: {bool(lanes.get('chrome_safe_mode'))}")
    if manual_activation_lanes:
        lines.append("Manual activation lanes: " + ", ".join(str(item) for item in manual_activation_lanes))
    navigation_contract = lanes.get("navigation_contract") or []
    if navigation_contract:
        lines.append("Navigation contract: " + ", ".join(str(item) for item in navigation_contract[:4]))
    if avoid_patterns:
        lines.append("Avoid: " + ", ".join(str(item) for item in avoid_patterns[:4]))
    if lane_rows:
        lines.append("Lane surfaces:")
        for item in lane_rows[: max(0, top_n)]:
            lines.append(
                "- "
                f"{item.get('lane_id', 'unknown')} | "
                f"{item.get('owner_floor', 'unknown')} | "
                f"{item.get('state', 'unknown')} | "
                f"{item.get('surface', 'unknown')}"
            )
    else:
        lines.append("Lane surfaces: none exported.")
    return "\n".join(lines)


def format_smart_floor_spaces_focus(
    summary: dict,
    *,
    floors: Iterable[str] | None = None,
    top_n: int = 8,
) -> str:
    spaces = summary.get("smart_floor_spaces") or {}
    rows = spaces.get("spaces") or []
    focus_set = {item for item in (floors or []) if item}
    filtered_rows = [item for item in rows if not focus_set or item.get("floor") in focus_set]
    lines = [
        (
            f"Smart floor spaces: {spaces.get('space_set_id', 'unknown')} | "
            f"ready={spaces.get('ready_count', 0)}/{spaces.get('space_count', len(rows))} | "
            f"no_risk_entry={spaces.get('no_risk_entry_count', 0)}"
        )
    ]
    contract = spaces.get("population_contract")
    if contract:
        lines.append(f"Population contract: {contract}")
    density = spaces.get("default_density")
    if density:
        lines.append(f"Default density: {density}")
    collapse_policy = spaces.get("collapse_policy")
    if collapse_policy:
        lines.append(f"Collapse policy: {collapse_policy}")
    goal = spaces.get("single_interface_goal")
    if goal:
        lines.append(f"Interface goal: {goal}")
    workset = filtered_rows or rows[: max(0, top_n)]
    if not workset:
        lines.append("Spaces: none exported.")
        return "\n".join(lines)
    lines.append("Spaces:")
    for item in workset[: max(0, top_n)]:
        lines.append(
            "- "
            f"{item.get('floor', 'unknown')} | "
            f"{item.get('label', item.get('space_id', 'unknown'))} | "
            f"{item.get('status', 'unknown')} | "
            f"view={item.get('default_view', 'unknown')}"
        )
    return "\n".join(lines)


def format_gated_build_tasks_focus(
    summary: dict,
    *,
    focus_floors: Iterable[str] | None = None,
    top_n: int = 6,
) -> str:
    tasks = summary.get("gated_build_tasks") or {}
    top_tasks = tasks.get("top_tasks") or []
    by_owner_floor = tasks.get("by_owner_floor") or {}
    by_lane = tasks.get("by_lane") or {}
    policy = tasks.get("approval_policy") or {}
    focus_set = {item for item in (focus_floors or []) if item}
    filtered_tasks = [item for item in top_tasks if not focus_set or item.get("owner_floor") in focus_set]
    lines = [
        (
            f"Build tasks: {tasks.get('task_set_id', 'unknown')} | "
            f"ready={tasks.get('ready_count', 0)}/{tasks.get('total_tasks', 0)} | "
            f"mode={tasks.get('execution_mode', 'unknown')}"
        )
    ]
    if policy:
        lines.append(
            "Approval gate: "
            f"input={policy.get('input_mode', 'unknown')} | "
            f"artifact_review={bool(policy.get('artifact_review_required'))} | "
            f"external_publish_blocked={bool(policy.get('external_publish_blocked'))}"
        )
    if by_owner_floor:
        owner_pairs = sorted(
            (floor, count) for floor, count in by_owner_floor.items() if not focus_set or floor in focus_set
        )
        if owner_pairs:
            lines.append("Task owners: " + ", ".join(f"{floor}={count}" for floor, count in owner_pairs))
    if by_lane:
        lane_pairs = sorted(by_lane.items())
        lines.append("Lane coverage: " + ", ".join(f"{lane}={count}" for lane, count in lane_pairs[:4]))
    workset = filtered_tasks or top_tasks[: max(0, top_n)]
    if not workset:
        lines.append("Top tasks: none exported.")
        return "\n".join(lines)
    lines.append("Top tasks:")
    for item in workset[: max(0, top_n)]:
        lines.append(
            "- "
            f"{item.get('task_id', 'unknown')} | "
            f"{item.get('owner_floor', 'unknown')} | "
            f"{item.get('priority', 'unknown')} | "
            f"{item.get('state', 'unknown')} | "
            f"risk={item.get('risk_level', 'unknown')}"
        )
    return "\n".join(lines)


def format_backend_frontend_build_focus(
    summary: dict,
    *,
    floors: Iterable[str] | None = None,
    top_n: int = 8,
) -> str:
    build = summary.get("backend_frontend_build") or {}
    rows = build.get("floors") or []
    by_floor = build.get("by_floor") or {}
    focus_set = {item for item in (floors or []) if item}
    if focus_set and by_floor:
        filtered_rows = [by_floor[floor] for floor in focus_set if floor in by_floor]
    else:
        filtered_rows = [item for item in rows if not focus_set or item.get("floor") in focus_set]

    lines = [
        (
            f"Backend/frontend build: {build.get('contract_id', 'not exported')} | "
            f"floors={build.get('floor_count', len(rows))} | "
            f"backend={build.get('backend_enabled_count', 0)} | "
            f"frontend={build.get('frontend_enabled_count', 0)}"
        )
    ]
    if build.get("launch_gate"):
        lines.append(f"Launch gate: {build.get('launch_gate')}")
    policy = build.get("policy") or {}
    if policy:
        lines.append(
            "Policy: "
            f"local_llm_first={bool(policy.get('local_llm_first'))} | "
            f"manual_approval={bool(policy.get('manual_approval_required'))} | "
            f"writes={policy.get('external_writes', 'unknown')}"
        )

    workset = filtered_rows or rows[: max(0, top_n)]
    if not workset:
        lines.append("Build spine: none exported.")
        return "\n".join(lines)

    lines.append("Build spine:")
    for item in workset[: max(0, top_n)]:
        agent = item.get("agent") or {}
        backend = item.get("backend") or {}
        frontend = item.get("frontend") or {}
        build_state = item.get("build") or {}
        lines.append(
            "- "
            f"{item.get('floor', 'unknown')} | "
            f"agent={agent.get('agent_id', 'unknown')} | "
            f"backend={'on' if backend.get('enabled') else 'off'} | "
            f"frontend={'on' if frontend.get('enabled') else 'off'} | "
            f"state={build_state.get('state', 'unknown')} | "
            f"surface={frontend.get('surface', 'unknown')}"
        )
    return "\n".join(lines)


def format_floor_environment_realization_focus(
    summary: dict,
    *,
    floors: Iterable[str] | None = None,
    top_n: int = 8,
) -> str:
    realization = summary.get("floor_environment_realization") or {}
    rows = realization.get("floors") or []
    by_floor = realization.get("by_floor") or {}
    focus_set = {item for item in (floors or []) if item}
    if focus_set and by_floor:
        filtered_rows = [by_floor[floor] for floor in focus_set if floor in by_floor]
    else:
        filtered_rows = [item for item in rows if not focus_set or item.get("floor") in focus_set]

    lines = [
        (
            f"Floor realization: {realization.get('contract_id', 'not exported')} | "
            f"floors={realization.get('floor_count', len(rows))} | "
            f"models={realization.get('floor_models_confirmed', 0)} confirmed | "
            f"cross-system={realization.get('cross_system_models_confirmed', 0)}/"
            f"{realization.get('cross_system_agent_count', 0)}"
        )
    ]
    if realization.get("realization_order"):
        lines.append(f"Order: {realization.get('realization_order')}")
    if realization.get("launch_gate"):
        lines.append(f"Launch gate: {realization.get('launch_gate')}")

    workset = filtered_rows or rows[: max(0, top_n)]
    if not workset:
        lines.append("Environment realization: none exported.")
        return "\n".join(lines)

    lines.append("Environment realization:")
    for item in workset[: max(0, top_n)]:
        model = item.get("model") or {}
        population = item.get("population") or {}
        ui = item.get("ui_realization") or {}
        post = item.get("post_population") or {}
        lines.append(
            "- "
            f"{item.get('outside_in_order', 'n/a')}. {item.get('floor', 'unknown')} | "
            f"{item.get('environment_label', 'environment')} | "
            f"model={model.get('model', 'unknown')} "
            f"({'confirmed' if model.get('confirmed_installed') else 'missing'}) | "
            f"mode={population.get('mode', 'unknown')} | "
            f"view={ui.get('default_view', 'unknown')} | "
            f"next={post.get('next_safe_action', 'not exported')}"
        )
    return "\n".join(lines)


def format_local_agent_wakeup_focus(
    summary: dict,
    *,
    floors: Iterable[str] | None = None,
    top_n: int = 8,
) -> str:
    wakeup = summary.get("local_agent_wakeup") or {}
    rows = wakeup.get("floors") or []
    by_floor = wakeup.get("by_floor") or {}
    focus_set = {item for item in (floors or []) if item}
    if focus_set and by_floor:
        filtered_rows = [by_floor[floor] for floor in focus_set if floor in by_floor]
    else:
        filtered_rows = [item for item in rows if not focus_set or item.get("floor") in focus_set]

    ollama = wakeup.get("ollama") or {}
    lines = [
        (
            f"Local wake-up: {wakeup.get('contract_id', 'not exported')} | "
            f"floors={wakeup.get('floor_count', len(rows))} | "
            f"ollama={wakeup.get('ollama_enabled_floor_count', 0)} enabled | "
            f"source_files={wakeup.get('source_file_sample_count', 0)}"
        ),
        (
            f"Source: {wakeup.get('source_root', 'not exported')} | "
            f"exists={bool(wakeup.get('source_root_exists'))} | "
            f"endpoint={ollama.get('endpoint', 'unknown')} | "
            f"state={ollama.get('connection_state', 'unknown')}"
        ),
    ]
    ui = wakeup.get("ui_simplification") or {}
    if ui:
        lines.append(
            "UI: "
            f"{ui.get('entry_surface', 'N.py')} | "
            f"{ui.get('user_rule', 'single active floor surface')}"
        )

    workset = filtered_rows or rows[: max(0, top_n)]
    if not workset:
        lines.append("Wake-up packets: none exported.")
        return "\n".join(lines)

    lines.append("Wake-up packets:")
    for item in workset[: max(0, top_n)]:
        connection = item.get("ollama_connection") or {}
        activation = item.get("activation") or {}
        draw = item.get("assimilation_draw") or {}
        lines.append(
            "- "
            f"{item.get('order', 'n/a')}. {item.get('floor', 'unknown')} | "
            f"model={connection.get('model', 'unknown')} "
            f"({'enabled' if connection.get('enabled') else 'unconfirmed'}) | "
            f"mode={activation.get('mode', 'unknown')} | "
            f"draw={len(draw.get('priority_paths') or [])} | "
            f"next={item.get('next_safe_action', 'not exported')}"
        )
    return "\n".join(lines)


def format_floor_alignment_focus(summary: dict, floor: str) -> str:
    alignment = summary.get("floor_alignment") or {}
    floor_payload = (alignment.get("floors") or {}).get(floor) or {}
    if not floor_payload:
        return f"{floor} alignment unavailable."
    primary_space = floor_payload.get("primary_space") or {}
    lane_rows = floor_payload.get("lanes") or []
    task_rows = floor_payload.get("tasks") or []
    lines = [
        (
            f"{floor}: {floor_payload.get('primary_status', 'unknown')} | "
            f"mode={floor_payload.get('population_mode', 'unknown')} | "
            f"boot={floor_payload.get('boot_priority', 'n/a')}"
        ),
        (
            f"Model: {floor_payload.get('model', 'unknown')} | "
            f"persona={floor_payload.get('persona', 'unknown')} | "
            f"workspace={floor_payload.get('workspace_scope', 'unknown')}"
        ),
        (
            f"Space: {primary_space.get('label', 'unassigned')} | "
            f"status={primary_space.get('status', 'unknown')} | "
            f"view={primary_space.get('default_view', 'unknown')}"
        ),
        (
            f"Agent: {floor_payload.get('assigned_agent_id', 'unknown')} | "
            f"support={floor_payload.get('de_sporte_support_resident_id', 'none')} | "
            f"host={floor_payload.get('resident_host_application', 'unknown')}"
        ),
        (
            f"Alignment: lanes={floor_payload.get('lane_count', 0)} | "
            f"spaces={floor_payload.get('space_count', 0)} | "
            f"tasks={floor_payload.get('task_count', 0)} | "
            f"ready_tasks={floor_payload.get('ready_task_count', 0)}"
        ),
        (
            f"Staging: components={floor_payload.get('live_component_count', 0)}/"
            f"{floor_payload.get('staging_component_count', 0)} live"
        ),
    ]
    if floor_payload.get("stage_reason"):
        lines.append(f"Reason: {floor_payload.get('stage_reason')}")
    if lane_rows:
        lines.append("Lane owners: " + ", ".join(str(item.get("lane_id")) for item in lane_rows[:4] if item.get("lane_id")))
    if task_rows:
        lines.append("Top tasks: " + ", ".join(str(item.get("task_id")) for item in task_rows[:3] if item.get("task_id")))
    component_ids = floor_payload.get("component_ids") or []
    if component_ids:
        lines.append("Components: " + ", ".join(str(item) for item in component_ids[:4]))
    return "\n".join(lines)


def build_trinity_operator_home_panel(parent: tk.Misc, app: object | None):
    bridge = resolve_agent_home_bridge(app)
    if bridge is None:
        return None

    box = ttk.LabelFrame(parent, text="Agent Home")
    ttk.Label(
        box,
        text="Read-only operator surface over exported lanes, approvals, truth, and bounded floor population state.",
        justify="left",
    ).pack(anchor="w", padx=10, pady=(8, 6))

    overview = tk.Text(box, height=8, wrap="word", font=("Consolas", 9))
    overview.pack(fill="x", padx=10, pady=(0, 8))
    details = tk.Text(box, height=10, wrap="word", font=("Consolas", 9))
    details.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _refresh() -> None:
        try:
            summary = bridge.summary()
        except Exception as exc:
            _replace_text(overview, f"Agent home export unavailable:\n{exc}")
            _replace_text(details, "")
            return
        _replace_text(
            overview,
            "\n".join(
                [
                    format_agent_home_overview(summary),
                    "",
                    format_launch_control_focus(summary),
                    "",
                    format_floor_model_focus(summary, "Trinity"),
                    "",
                    format_de_sporte_runtime_focus(summary),
                    "",
                    format_neo_local_runtime_focus(summary),
                    "",
                    format_presence_roster_focus(summary),
                    "",
                    format_workspace_lanes_focus(summary),
                ]
            ),
        )
        _replace_text(
            details,
            "\n\n".join(
                [
                    format_agent_population_focus(summary),
                    format_backend_frontend_build_focus(
                        summary,
                        floors={"Trinity", "Neo", "Smith", "Oracle", "Morpheus", "Architect", "TheConstruct", "Merovingian"},
                        top_n=8,
                    ),
                    format_floor_environment_realization_focus(
                        summary,
                        floors={"Trinity", "Neo", "Smith", "Oracle", "Morpheus", "Architect", "TheConstruct", "Merovingian"},
                        top_n=8,
                    ),
                    format_local_agent_wakeup_focus(
                        summary,
                        floors={"Trinity", "Neo", "Smith", "Oracle", "Morpheus", "Architect", "TheConstruct", "Merovingian"},
                        top_n=8,
                    ),
                    format_input_staging_focus(
                        summary,
                        floors={"Trinity", "Neo", "Smith", "Oracle", "Morpheus", "Architect", "TheConstruct", "Merovingian"},
                        top_n=8,
                    ),
                    format_gated_build_tasks_focus(
                        summary,
                        focus_floors={"Trinity", "Smith", "Oracle", "TheConstruct", "Architect"},
                        top_n=6,
                    ),
                    format_smart_floor_spaces_focus(
                        summary,
                        floors={"Trinity", "Neo", "Smith", "Oracle", "Morpheus", "TheConstruct", "Architect", "Merovingian"},
                    ),
                    format_upstream_inventory_focus(summary),
                    format_truth_registry_focus(summary),
                    format_overlap_snapshot(summary, top_n=4),
                ]
            ),
        )

    actions = ttk.Frame(box)
    actions.pack(anchor="w", padx=10, pady=(0, 10))
    ttk.Button(actions, text="Refresh Agent Home", command=_refresh).pack(side="left")
    _refresh()
    return box


def build_smith_queue_router_panel(parent: tk.Misc, app: object | None):
    bridge = resolve_agent_home_bridge(app)
    if bridge is None:
        return None

    box = ttk.LabelFrame(parent, text="Queue Router")
    ttk.Label(
        box,
        text="Read-only routing view over bounded build tasks, consolidation work, and overlap pressure.",
        justify="left",
    ).pack(anchor="w", padx=10, pady=(8, 6))

    overview = tk.Text(box, height=7, wrap="word", font=("Consolas", 9))
    overview.pack(fill="x", padx=10, pady=(0, 8))
    workset = tk.Text(box, height=12, wrap="word", font=("Consolas", 9))
    workset.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _refresh() -> None:
        try:
            summary = bridge.summary()
        except Exception as exc:
            _replace_text(overview, f"Queue export unavailable:\n{exc}")
            _replace_text(workset, "")
            return
        _replace_text(
            overview,
            "\n".join(
                [
                    format_agent_home_overview(summary),
                    "",
                    format_floor_model_focus(summary, "Smith"),
                    "",
                    format_agent_population_focus(summary, floors={"Smith", "Oracle", "Morpheus", "Architect", "TheConstruct"}),
                    "",
                    format_workspace_lanes_focus(summary, top_n=4),
                ]
            ),
        )
        _replace_text(
            workset,
            "\n\n".join(
                [
                    format_input_staging_focus(
                        summary,
                        floors={"Smith", "Oracle", "Morpheus", "Architect", "TheConstruct"},
                        top_n=5,
                    ),
                    format_queue_workset(summary, focus_floors={"Oracle", "Morpheus", "TheConstruct", "Architect"}, top_n=6),
                    format_gated_build_tasks_focus(
                        summary,
                        focus_floors={"Smith", "Oracle", "Morpheus", "TheConstruct", "Architect"},
                        top_n=6,
                    ),
                    format_overlap_snapshot(summary, top_n=4),
                ]
            ),
        )

    actions = ttk.Frame(box)
    actions.pack(anchor="w", padx=10, pady=(0, 10))
    ttk.Button(actions, text="Refresh Queue", command=_refresh).pack(side="left")
    _refresh()
    return box


def build_construct_runtime_panel(parent: tk.Misc, app: object | None):
    bridge = resolve_agent_home_bridge(app)
    if bridge is None:
        return None

    box = ttk.LabelFrame(parent, text="Construct Runtime")
    ttk.Label(
        box,
        text="D-drive runtime profile for TheConstruct render modes, smart-floor space, and bounded digital-twin population.",
        justify="left",
    ).pack(anchor="w", padx=10, pady=(8, 6))

    overview = tk.Text(box, height=10, wrap="word", font=("Consolas", 9))
    overview.pack(fill="x", padx=10, pady=(0, 8))
    details = tk.Text(box, height=12, wrap="word", font=("Consolas", 9))
    details.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _refresh() -> None:
        try:
            summary = bridge.summary()
        except Exception as exc:
            _replace_text(overview, f"Construct runtime export unavailable:\n{exc}")
            _replace_text(details, "")
            return
        _replace_text(
            overview,
            "\n\n".join(
                [
                    format_construct_runtime_focus(summary),
                    format_floor_model_focus(summary, "TheConstruct"),
                    format_agent_population_focus(summary, floors={"TheConstruct", "Oracle", "Morpheus", "Merovingian"}),
                    format_host_runtime_policy_focus(summary),
                ]
            ),
        )
        _replace_text(
            details,
            "\n\n".join(
                [
                    format_stage_population_focus(summary, "TheConstruct"),
                    format_input_staging_focus(summary, floors={"TheConstruct", "Oracle", "Morpheus"}, top_n=4),
                    format_smart_floor_spaces_focus(summary, floors={"TheConstruct", "Oracle", "Morpheus"}),
                    format_gated_build_tasks_focus(summary, focus_floors={"TheConstruct", "Oracle", "Morpheus"}, top_n=4),
                    format_deployment_topology_focus(summary),
                ]
            ),
        )

    actions = ttk.Frame(box)
    actions.pack(anchor="w", padx=10, pady=(0, 10))
    ttk.Button(actions, text="Refresh Construct Runtime", command=_refresh).pack(side="left")
    _refresh()
    return box


def build_oracle_population_panel(parent: tk.Misc, app: object | None):
    bridge = resolve_agent_home_bridge(app)
    if bridge is None:
        return None

    box = ttk.LabelFrame(parent, text="Oracle Workbench")
    ttk.Label(
        box,
        text="Proofed knowns, provenance, and live intake roots for Oracle's compact library surface.",
        justify="left",
    ).pack(anchor="w", padx=10, pady=(8, 6))

    overview = tk.Text(box, height=8, wrap="word", font=("Consolas", 9))
    overview.pack(fill="x", padx=10, pady=(0, 8))
    details = tk.Text(box, height=12, wrap="word", font=("Consolas", 9))
    details.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _refresh() -> None:
        try:
            summary = bridge.summary()
        except Exception as exc:
            _replace_text(overview, f"Oracle workbench export unavailable:\n{exc}")
            _replace_text(details, "")
            return
        _replace_text(
            overview,
            "\n\n".join(
                [
                    format_floor_alignment_focus(summary, "Oracle"),
                    format_agent_population_focus(summary, floors={"Oracle", "Morpheus", "Smith"}),
                    format_input_staging_focus(summary, floors={"Oracle"}, top_n=3),
                ]
            ),
        )
        _replace_text(
            details,
            "\n\n".join(
                [
                    format_smart_floor_spaces_focus(summary, floors={"Oracle", "Morpheus"}),
                    format_gated_build_tasks_focus(summary, focus_floors={"Oracle", "Morpheus", "Smith"}, top_n=4),
                    format_truth_registry_focus(summary),
                ]
            ),
        )

    actions = ttk.Frame(box)
    actions.pack(anchor="w", padx=10, pady=(0, 10))
    ttk.Button(actions, text="Refresh Oracle Workbench", command=_refresh).pack(side="left")
    _refresh()
    return box


def build_morpheus_review_panel(parent: tk.Misc, app: object | None):
    bridge = resolve_agent_home_bridge(app)
    if bridge is None:
        return None

    box = ttk.LabelFrame(parent, text="Morpheus Review Chamber")
    ttk.Label(
        box,
        text="Single review chamber for corroboration, overlap, and promotion proposals.",
        justify="left",
    ).pack(anchor="w", padx=10, pady=(8, 6))

    overview = tk.Text(box, height=8, wrap="word", font=("Consolas", 9))
    overview.pack(fill="x", padx=10, pady=(0, 8))
    details = tk.Text(box, height=12, wrap="word", font=("Consolas", 9))
    details.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _refresh() -> None:
        try:
            summary = bridge.summary()
        except Exception as exc:
            _replace_text(overview, f"Morpheus review export unavailable:\n{exc}")
            _replace_text(details, "")
            return
        _replace_text(
            overview,
            "\n\n".join(
                [
                    format_floor_alignment_focus(summary, "Morpheus"),
                    format_agent_population_focus(summary, floors={"Morpheus", "Oracle", "Smith"}),
                    format_input_staging_focus(summary, floors={"Morpheus"}, top_n=3),
                ]
            ),
        )
        _replace_text(
            details,
            "\n\n".join(
                [
                    format_queue_workset(summary, focus_floors={"Oracle", "Morpheus", "TheConstruct"}, top_n=5),
                    format_gated_build_tasks_focus(summary, focus_floors={"Morpheus", "Oracle", "Smith"}, top_n=4),
                    format_overlap_snapshot(summary, top_n=4),
                ]
            ),
        )

    actions = ttk.Frame(box)
    actions.pack(anchor="w", padx=10, pady=(0, 10))
    ttk.Button(actions, text="Refresh Morpheus Review", command=_refresh).pack(side="left")
    _refresh()
    return box


def build_architect_workbench_panel(parent: tk.Misc, app: object | None):
    bridge = resolve_agent_home_bridge(app)
    if bridge is None:
        return None

    box = ttk.LabelFrame(parent, text="Architect Workbench")
    ttk.Label(
        box,
        text="Single planning lane for active projects, staged build tasks, and controlled publish routing.",
        justify="left",
    ).pack(anchor="w", padx=10, pady=(8, 6))

    overview = tk.Text(box, height=8, wrap="word", font=("Consolas", 9))
    overview.pack(fill="x", padx=10, pady=(0, 8))
    details = tk.Text(box, height=12, wrap="word", font=("Consolas", 9))
    details.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _refresh() -> None:
        try:
            summary = bridge.summary()
        except Exception as exc:
            _replace_text(overview, f"Architect workbench export unavailable:\n{exc}")
            _replace_text(details, "")
            return
        _replace_text(
            overview,
            "\n\n".join(
                [
                    format_floor_alignment_focus(summary, "Architect"),
                    format_agent_population_focus(summary, floors={"Architect", "Trinity", "Smith", "TheConstruct"}),
                    format_launch_control_focus(summary),
                    format_input_staging_focus(summary, floors={"Architect"}, top_n=3),
                ]
            ),
        )
        _replace_text(
            details,
            "\n\n".join(
                [
                    format_workspace_lanes_focus(summary, top_n=4),
                    format_gated_build_tasks_focus(summary, focus_floors={"Architect", "Smith", "Trinity", "TheConstruct"}, top_n=5),
                    format_upstream_inventory_focus(summary),
                    format_deployment_topology_focus(summary),
                ]
            ),
        )

    actions = ttk.Frame(box)
    actions.pack(anchor="w", padx=10, pady=(0, 10))
    ttk.Button(actions, text="Refresh Architect Workbench", command=_refresh).pack(side="left")
    _refresh()
    return box


def build_neo_orchestration_panel(parent: tk.Misc, app: object | None):
    bridge = resolve_agent_home_bridge(app)
    if bridge is None:
        return None

    box = ttk.LabelFrame(parent, text="Neo Orchestration Deck")
    ttk.Label(
        box,
        text="Primary orchestration lane for models, staged plans, and governed cross-floor actions.",
        justify="left",
    ).pack(anchor="w", padx=10, pady=(8, 6))

    overview = tk.Text(box, height=8, wrap="word", font=("Consolas", 9))
    overview.pack(fill="x", padx=10, pady=(0, 8))
    details = tk.Text(box, height=12, wrap="word", font=("Consolas", 9))
    details.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _refresh() -> None:
        try:
            summary = bridge.summary()
        except Exception as exc:
            _replace_text(overview, f"Neo orchestration export unavailable:\n{exc}")
            _replace_text(details, "")
            return
        _replace_text(
            overview,
            "\n\n".join(
                [
                    format_floor_alignment_focus(summary, "Neo"),
                    format_agent_population_focus(summary, floors={"Neo", "Trinity", "Smith", "Architect"}),
                    format_launch_control_focus(summary),
                    format_de_sporte_runtime_focus(summary),
                    format_neo_local_runtime_focus(summary),
                    format_input_staging_focus(summary, floors={"Neo"}, top_n=3),
                ]
            ),
        )
        _replace_text(
            details,
            "\n\n".join(
                [
                    format_neo_realisation_focus(summary),
                    format_upstream_inventory_focus(summary),
                    format_workspace_lanes_focus(summary, top_n=4),
                    format_gated_build_tasks_focus(summary, focus_floors={"Neo", "Trinity", "Smith", "Architect"}, top_n=5),
                    format_presence_roster_focus(summary),
                ]
            ),
        )

    actions = ttk.Frame(box)
    actions.pack(anchor="w", padx=10, pady=(0, 10))
    ttk.Button(actions, text="Refresh Neo Orchestration", command=_refresh).pack(side="left")
    _refresh()
    return box


def mount_oracle_reservoir_overview(parent: ttk.Frame, app: object | None) -> bool:
    bridge = resolve_runtime_bridge(app)
    if bridge is None:
        return False

    box = ttk.LabelFrame(parent, text="Canonical Reservoir Sources")
    box.pack(fill="both", expand=True, padx=12, pady=(12, 8))

    panes = ttk.PanedWindow(box, orient="horizontal")
    panes.pack(fill="both", expand=True, padx=10, pady=10)

    left = ttk.Frame(panes)
    center = ttk.Frame(panes)
    right = ttk.Frame(panes)
    try:
        panes.add(left, weight=2)
        panes.add(center, weight=2)
        panes.add(right, weight=3)
    except Exception:
        panes.add(left)
        panes.add(center)
        panes.add(right)

    ttk.Label(left, text="Sources", font=("Consolas", 11, "bold")).pack(anchor="w", pady=(0, 6))
    source_list = tk.Listbox(left, height=16, font=("Consolas", 10))
    source_list.pack(fill="both", expand=True)

    ttk.Label(center, text="Assets", font=("Consolas", 11, "bold")).pack(anchor="w", pady=(0, 6))
    asset_list = tk.Listbox(center, height=16, font=("Consolas", 10))
    asset_list.pack(fill="both", expand=True)

    ttk.Label(right, text="Provenance", font=("Consolas", 11, "bold")).pack(anchor="w", pady=(0, 6))
    details = tk.Text(right, wrap="word", font=("Consolas", 9))
    details.pack(fill="both", expand=True)

    state: dict[str, list[dict]] = {"sources": [], "assets": []}

    def _render(payload: str | None) -> None:
        try:
            details.delete("1.0", "end")
        except Exception:
            pass
        if payload is None:
            return
        details.insert("1.0", payload)

    def _load_sources() -> None:
        source_list.delete(0, "end")
        state["sources"] = []
        try:
            for manifest in bridge.runtime.registry.manifests():
                overview = bridge.source_overview(manifest.source_id)
                state["sources"].append(overview)
                source_list.insert(
                    "end",
                    (
                        f"{overview['source_label']} | {overview['total_assets']} assets | "
                        f"c={overview['by_rank'].get('canonical', 0)} "
                        f"r={overview['by_rank'].get('reference', 0)} "
                        f"a={overview['by_rank'].get('archive', 0)}"
                    ),
                )
        except Exception as exc:
            _render(f"Source overview unavailable:\n{exc}")

    def _load_assets(index: int) -> None:
        asset_list.delete(0, "end")
        state["assets"] = []
        if not (0 <= index < len(state["sources"])):
            return
        source_id = state["sources"][index]["source_id"]
        state["assets"] = bridge.source_assets(source_id, limit=100)
        for item in state["assets"]:
            asset_list.insert("end", f"{item['canonical_rank'][0].upper()} | {item['title']}")
        _render(bridge.render_source_overview(source_id))

    def _on_source_select(_evt=None) -> None:
        try:
            sel = source_list.curselection()
            if not sel:
                return
            _load_assets(int(sel[0]))
        except Exception:
            return

    def _on_asset_select(_evt=None) -> None:
        try:
            sel = asset_list.curselection()
            if not sel:
                return
            _render(bridge.render_asset_detail(state["assets"][int(sel[0])]["asset_id"]))
        except Exception:
            return

    source_list.bind("<<ListboxSelect>>", _on_source_select)
    asset_list.bind("<<ListboxSelect>>", _on_asset_select)
    _load_sources()
    if state["sources"]:
        source_list.selection_set(0)
        _load_assets(0)
    return True


def mount_morpheus_runtime_search(parent: ttk.Frame, app: object | None) -> bool:
    bridge = resolve_runtime_bridge(app)
    if bridge is None:
        return False

    ttk.Label(parent, text="Canonical Reservoir Search", font=("Consolas", 14, "bold")).pack(pady=(10, 6))
    ttk.Label(
        parent,
        text="Searches the mounted doctrine, calculator, and Raphael sources through the canonical runtime.",
        justify="left",
    ).pack(anchor="w", padx=12, pady=(0, 10))

    controls = ttk.Frame(parent)
    controls.pack(fill="x", padx=12, pady=(0, 10))
    controls.columnconfigure(1, weight=1)

    ttk.Label(controls, text="Query:").grid(row=0, column=0, sticky="w")
    query_var = tk.StringVar(value="Romer GMAT")
    ttk.Entry(controls, textvariable=query_var, width=50).grid(row=0, column=1, sticky="ew", padx=(8, 8))
    ttk.Label(controls, text="Source:").grid(row=0, column=2, sticky="w")
    source_var = tk.StringVar(value="All")
    source_values = ["All"] + [manifest.source_id for manifest in bridge.runtime.registry.manifests()]
    source_combo = ttk.Combobox(controls, textvariable=source_var, values=source_values, state="readonly", width=22)
    source_combo.grid(row=0, column=3, sticky="w", padx=(8, 8))

    panes = ttk.PanedWindow(parent, orient="horizontal")
    panes.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    left = ttk.Frame(panes)
    right = ttk.Frame(panes)
    try:
        panes.add(left, weight=2)
        panes.add(right, weight=3)
    except Exception:
        panes.add(left)
        panes.add(right)

    listbox = tk.Listbox(left, height=18, font=("Consolas", 10))
    listbox.pack(fill="both", expand=True)

    details = tk.Text(right, wrap="word", font=("Consolas", 10))
    details.pack(fill="both", expand=True)

    state: dict[str, list[dict]] = {"results": []}

    def _render_details(payload: str | None) -> None:
        try:
            details.delete("1.0", "end")
        except Exception:
            pass
        if not payload:
            return
        details.insert("1.0", payload)

    def _search() -> None:
        query = (query_var.get() or "").strip()
        source_value = source_var.get()
        allowed = None if source_value in {"", "All"} else [source_value]
        results = [item.to_dict() for item in bridge.search(query, sources=allowed, limit=25)] if query else []
        state["results"] = results
        listbox.delete(0, "end")
        for item in results:
            source_label = item.get("source_label") or item["source_id"]
            listbox.insert("end", f"{item['canonical_rank'][0].upper()} | {source_label} | {item['title']}")
        if results:
            _render_details(bridge.render_asset_detail(results[0]["asset_id"]))
        else:
            _render_details(format_search_empty_state(query, source_value))

    def _on_select(_evt=None) -> None:
        try:
            sel = listbox.curselection()
            if not sel:
                return
            _render_details(bridge.render_asset_detail(state["results"][int(sel[0])]["asset_id"]))
        except Exception:
            return

    ttk.Button(controls, text="Search", command=_search).grid(row=0, column=2, sticky="e")
    source_combo.bind("<<ComboboxSelected>>", lambda _evt: _search())
    listbox.bind("<<ListboxSelect>>", _on_select)
    _search()
    return True


def mount_architect_publish_center(parent: ttk.Frame, app: object | None) -> bool:
    shell_bridge = resolve_runtime_shell_bridge(app)
    runtime = getattr(app, "canonical_runtime", None) if app is not None else None
    if shell_bridge is None or runtime is None:
        return False

    targets = runtime.load_intermediary_targets().get("website_bridge", {})
    box = ttk.LabelFrame(parent, text="Romer Publish Center")
    box.pack(fill="x", padx=12, pady=(12, 8))
    ttk.Label(
        box,
        text=f"Intermediary: {targets.get('label', 'Not configured')}",
        justify="left",
    ).pack(anchor="w", padx=10, pady=(8, 2))
    ttk.Label(
        box,
        text=targets.get("url", "No intermediary URL configured."),
        justify="left",
    ).pack(anchor="w", padx=10, pady=(0, 8))
    ttk.Label(
        box,
        text=f"Package root: {runtime.resolve_package_output_dir('Romer')}",
        justify="left",
    ).pack(anchor="w", padx=10, pady=(0, 8))

    preview = tk.Text(box, height=10, wrap="word", font=("Consolas", 9))
    preview.pack(fill="x", padx=10, pady=(0, 10))
    status_text = tk.Text(box, height=12, wrap="word", font=("Consolas", 9))
    status_text.pack(fill="x", padx=10, pady=(0, 10))

    export_status = tk.StringVar(value="")
    ttk.Label(box, textvariable=export_status, justify="left").pack(anchor="w", padx=10, pady=(0, 8))

    def _refresh() -> None:
        state = shell_bridge.workspace_status("w6", "Romer", active_floor="Architect")
        manifest = shell_bridge.publish_workspace(
            "w6",
            "Romer",
            summary="Romer publish preview from Architect through the canonical runtime.",
            artifact_refs=[],
        )
        try:
            preview.delete("1.0", "end")
        except Exception:
            pass
        preview.insert("1.0", f"Publish manifest ready at {manifest['published_at']}\n\n{format_workspace_snapshot(state)}")
        try:
            status_text.delete("1.0", "end")
        except Exception:
            pass
        status_text.insert("1.0", format_workspace_snapshot(state))

    def _export_package() -> None:
        try:
            package = shell_bridge.export_workspace_package(
                runtime.resolve_package_output_dir("Romer"),
                workspace_id="w6",
                project_id="Romer",
                summary="Romer approved desktop export package.",
                artifact_refs=[],
                metadata={"intermediary": targets},
            )
            export_status.set(f"Exported package metadata: {package['files']['package_metadata']}")
        except Exception as exc:
            export_status.set(f"Export failed: {exc}")

    actions = ttk.Frame(box)
    actions.pack(anchor="w", padx=10, pady=(0, 10))
    ttk.Button(actions, text="Refresh Publish Preview", command=_refresh).pack(side="left")
    ttk.Button(actions, text="Export Romer Package", command=_export_package).pack(side="left", padx=(8, 0))
    _refresh()
    return True


def mount_construct_scenario_lab(parent: ttk.Frame, app: object | None) -> bool:
    shell_bridge = resolve_runtime_shell_bridge(app)
    runtime = getattr(app, "canonical_runtime", None) if app is not None else None
    if shell_bridge is None or runtime is None:
        return False

    box = ttk.LabelFrame(parent, text="Scenario Lab")
    box.pack(fill="x", padx=12, pady=(12, 8))
    ttk.Label(
        box,
        text="Dataset-backed scenario runs for Romer. Uses canonical reservoir ids and lab contracts.",
        justify="left",
    ).pack(anchor="w", padx=10, pady=(8, 8))

    source_ids = [manifest.source_id for manifest in runtime.registry.manifests()]
    ttk.Label(box, text=f"Available datasets: {', '.join(source_ids)}", justify="left").pack(anchor="w", padx=10, pady=(0, 8))

    out = tk.Text(box, height=8, wrap="word", font=("Consolas", 9))
    out.pack(fill="x", padx=10, pady=(0, 10))
    gmat_out = tk.Text(box, height=8, wrap="word", font=("Consolas", 9))
    gmat_out.pack(fill="x", padx=10, pady=(0, 10))
    state: dict[str, str | None] = {"run_id": None}

    def _stage_run() -> None:
        run = shell_bridge.launch_lab_run(
            "w6",
            "Romer",
            lab_type="gmat",
            scenario_id="romer_intermediary_transfer",
            dataset_refs=source_ids,
            parameter_set={"intermediary": "google_drive_bridge"},
            engine="gmat",
        )
        state["run_id"] = run.run_id
        try:
            out.delete("1.0", "end")
        except Exception:
            pass
        out.insert("1.0", format_run_snapshot(run.to_dict()))

    def _complete_run() -> None:
        run_id = state.get("run_id")
        if not run_id:
            try:
                out.delete("1.0", "end")
            except Exception:
                pass
            out.insert("1.0", "No active run. Create a scenario run first.")
            return
        payload = shell_bridge.complete_lab_run(
            run_id,
            metrics={"status": "approved", "delta_v": 3.8},
            outputs=[{"artifact": "romer_intermediary_transfer.json"}, {"artifact": "gmat_bundle.json"}],
        )
        try:
            out.delete("1.0", "end")
        except Exception:
            pass
        out.insert("1.0", format_run_snapshot(payload))

    def _emit_gmat_manifest() -> None:
        try:
            payload = shell_bridge.generate_gmat_manifest("w6", "Romer", mission_name="Romer Desktop Transfer")
            try:
                gmat_out.delete("1.0", "end")
            except Exception:
                pass
            gmat_out.insert("1.0", format_run_snapshot(payload))
        except Exception as exc:
            try:
                gmat_out.delete("1.0", "end")
            except Exception:
                pass
            gmat_out.insert("1.0", f"GMAT manifest unavailable: {exc}")

    actions = ttk.Frame(box)
    actions.pack(anchor="w", padx=10, pady=(0, 10))
    ttk.Button(actions, text="Create Scenario Run", command=_stage_run).pack(side="left")
    ttk.Button(actions, text="Complete Run", command=_complete_run).pack(side="left", padx=(8, 0))
    ttk.Button(actions, text="Emit GMAT Manifest", command=_emit_gmat_manifest).pack(side="left", padx=(8, 0))
    return True


def mount_neo_achilles_console(parent: ttk.Frame, app: object | None) -> bool:
    bridge = getattr(app, "neo_achilles_bridge", None) if app is not None else None
    if bridge is None:
        return False

    box = ttk.LabelFrame(parent, text="Achilles Operator Console")
    box.pack(fill="both", expand=True, padx=12, pady=(12, 8))

    controls = ttk.Frame(box)
    controls.pack(fill="x", padx=10, pady=(8, 8))
    controls.columnconfigure(1, weight=1)

    ttk.Label(controls, text="Query:").grid(row=0, column=0, sticky="w")
    query_var = tk.StringVar(value="Romer GMAT")
    ttk.Entry(controls, textvariable=query_var, width=50).grid(row=0, column=1, sticky="ew", padx=(8, 8))

    out = tk.Text(box, height=12, wrap="word", font=("Consolas", 9))
    out.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    status = tk.Text(box, height=10, wrap="word", font=("Consolas", 9))
    status.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    state: dict[str, str | None] = {"action_id": None}

    def _retrieve() -> None:
        brief = bridge.build_operator_brief(query_var.get(), limit=5)
        try:
            out.delete("1.0", "end")
        except Exception:
            pass
        out.insert("1.0", format_operator_brief(brief))

    def _propose() -> None:
        action = bridge.propose_operator_action(
            workspace="w6",
            target_scope="project/romer",
            action_type="website_publish_sync",
            inputs={"bridge": "google_drive_intermediary", "query": query_var.get()},
            requires_approval=True,
        )
        try:
            out.delete("1.0", "end")
        except Exception:
            pass
        out.insert("1.0", f"Action: {action.action_id} | {action.action_type} | {action.approval_state}\nScope: {action.target_scope}")
        state["action_id"] = action.action_id
        _refresh_status()

    def _approve() -> None:
        action_id = state.get("action_id")
        if not action_id:
            try:
                out.delete("1.0", "end")
            except Exception:
                pass
            out.insert("1.0", "No pending action. Propose an action first.")
            return
        payload = bridge.approve_operator_action("w6", action_id, audit_ref="audit_manual_approval")
        try:
            out.delete("1.0", "end")
        except Exception:
            pass
        out.insert("1.0", f"Action approved: {payload.get('action_id')} | state={payload.get('approval_state')} | audit={payload.get('audit_ref')}")
        _refresh_status()

    def _refresh_status() -> None:
        payload = bridge.workspace_status("w6")
        try:
            status.delete("1.0", "end")
        except Exception:
            pass
        status.insert("1.0", format_workspace_snapshot(payload))

    ttk.Button(controls, text="Retrieve Brief", command=_retrieve).grid(row=0, column=2, sticky="e")
    ttk.Button(controls, text="Propose Action", command=_propose).grid(row=0, column=3, sticky="e", padx=(8, 0))
    ttk.Button(controls, text="Approve Action", command=_approve).grid(row=0, column=4, sticky="e", padx=(8, 0))
    _retrieve()
    _refresh_status()
    return True
