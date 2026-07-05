from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lightspeed_runtime.storage_paths import trinity_root


@dataclass(frozen=True)
class SmartFloorVisualContract:
    floor: str
    floor_key: str
    z_level: int
    owner_role: str
    source_file: str
    manifest_dir: str
    primary_surface: str
    bento_widgets: tuple[dict[str, str], ...]
    charts: tuple[dict[str, str], ...]
    maps_3d: tuple[dict[str, str], ...]
    scientific_tools: tuple[dict[str, str], ...]
    simulation_hooks: tuple[dict[str, str], ...]
    data_objects: tuple[str, ...]
    handoffs: tuple[dict[str, str], ...]
    smoke_checks: tuple[str, ...]
    ui_prompts: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


FLOOR_VISUAL_CONTRACTS: dict[str, SmartFloorVisualContract] = {}


def _contract(
    floor: str,
    floor_key: str,
    z_level: int,
    owner_role: str,
    source_file: str,
    manifest_dir: str,
    primary_surface: str,
    bento_widgets: list[dict[str, str]],
    charts: list[dict[str, str]],
    maps_3d: list[dict[str, str]],
    scientific_tools: list[dict[str, str]],
    simulation_hooks: list[dict[str, str]],
    data_objects: list[str],
    handoffs: list[dict[str, str]],
    smoke_checks: list[str],
    ui_prompts: list[str],
) -> SmartFloorVisualContract:
    return SmartFloorVisualContract(
        floor=floor,
        floor_key=floor_key,
        z_level=z_level,
        owner_role=owner_role,
        source_file=source_file,
        manifest_dir=manifest_dir,
        primary_surface=primary_surface,
        bento_widgets=tuple(bento_widgets),
        charts=tuple(charts),
        maps_3d=tuple(maps_3d),
        scientific_tools=tuple(scientific_tools),
        simulation_hooks=tuple(simulation_hooks),
        data_objects=tuple(data_objects),
        handoffs=tuple(handoffs),
        smoke_checks=tuple(smoke_checks),
        ui_prompts=tuple(ui_prompts),
    )


FLOOR_VISUAL_CONTRACTS.update(
    {
        "Trinity": _contract(
            floor="Trinity",
            floor_key="trinity",
            z_level=3,
            owner_role="Workspace shell, Bento language, settings, setup, themes, and first-run control.",
            source_file="Z Axis/Trinity.py",
            manifest_dir="Z Axis/Z+3_Trinity",
            primary_surface="single glass workspace with project wall, compact smart menu, and settings library callaways",
            bento_widgets=[
                {"id": "project_wall", "label": "Project Wall", "mode": "folder_bento", "opens": "project_components"},
                {"id": "settings_hub", "label": "Settings Hub", "mode": "drawer", "opens": "shared_settings_library"},
                {"id": "theme_builder", "label": "Theme Builder", "mode": "inline_editor", "opens": "background_builder"},
                {"id": "z_floor_dropdown", "label": "Z Floor", "mode": "dropdown", "opens": "floor_routes"},
            ],
            charts=[
                {"id": "startup_progress", "type": "stacked_progress", "purpose": "show loading and dependency readiness"},
                {"id": "floor_readiness", "type": "radar", "purpose": "compare floor readiness without opening heavy UIs"},
            ],
            maps_3d=[
                {"id": "bento_wall_depth", "type": "curved_panel_layout", "purpose": "1.5m fixed curved panel placement cues"},
                {"id": "floor_route_graph", "type": "network_depth_map", "purpose": "show active Z-axis navigation routes"},
            ],
            scientific_tools=[
                {"id": "settings_schema_validator", "purpose": "validate shared settings before saving to a page, widget, or wizard"},
                {"id": "artifact_preview_router", "purpose": "select correct editor, preview, or full-screen surface by file type"},
            ],
            simulation_hooks=[
                {"id": "render_budget_gate", "purpose": "defer expensive visual layers until selected or opened"},
                {"id": "loading_overlay", "purpose": "show progress and cancellation for long imports, renders, and floor loads"},
            ],
            data_objects=["theme_profile", "workspace_layout", "project_wall_state", "widget_contract", "startup_option"],
            handoffs=[
                {"to": "Neo", "intent": "operator prompt and guided action queue"},
                {"to": "Architect", "intent": "approved publish and setup governance changes"},
            ],
            smoke_checks=["manifest present", "project wall widget present", "settings route present", "startup progress descriptor present"],
            ui_prompts=[
                "Single click previews; double click opens full editor.",
                "Ctrl+S opens search; Ctrl+Shift+S opens visible settings.",
                "Keep Holospace as an opt-in Construct context, not a top-level duplicate workspace button.",
            ],
        ),
        "Neo": _contract(
            floor="Neo",
            floor_key="neo",
            z_level=2,
            owner_role="Achilles/Cognigrex operator shell, agent handoff, approvals, and task reasoning.",
            source_file="Z Axis/Neo.py",
            manifest_dir="Z Axis/Z+2_Neo",
            primary_surface="operator briefing desk with queue, proposal cards, approvals, and model/tool status",
            bento_widgets=[
                {"id": "operator_brief", "label": "Operator Brief", "mode": "live_panel", "opens": "neo_context"},
                {"id": "task_graph", "label": "Task Graph", "mode": "network", "opens": "action_handoffs"},
                {"id": "approval_queue", "label": "Approvals", "mode": "table", "opens": "gated_actions"},
                {"id": "tool_status", "label": "Tool Status", "mode": "status_strip", "opens": "api_management"},
            ],
            charts=[
                {"id": "task_bellcurve", "type": "confidence_distribution", "purpose": "rank pending actions by risk and confidence"},
                {"id": "agent_throughput", "type": "timeline", "purpose": "show active, complete, blocked, and deferred handoffs"},
            ],
            maps_3d=[
                {"id": "agent_neural_route", "type": "knowledge_network", "purpose": "display current operator reasoning route"},
                {"id": "handoff_depth_map", "type": "floor_stack_map", "purpose": "show where proposed actions will land"},
            ],
            scientific_tools=[
                {"id": "proof_gate_selector", "purpose": "send scientific claims to Morpheus before applying results"},
                {"id": "dependency_approval_router", "purpose": "create Smith dependency approval tasks for missing packages"},
            ],
            simulation_hooks=[
                {"id": "neo_project_builder", "purpose": "turn a selected project objective into floor-scoped work packets"},
                {"id": "agent_run_replay", "purpose": "replay action chain results without re-running expensive tools"},
            ],
            data_objects=["operator_prompt", "action_envelope", "approval_record", "tool_capability", "handoff_receipt"],
            handoffs=[
                {"to": "Smith", "intent": "execute approved queued action"},
                {"to": "Morpheus", "intent": "proof claims and compare sources"},
                {"to": "Architect", "intent": "request governance approval for publish or destructive actions"},
            ],
            smoke_checks=["manifest present", "operator widget present", "approval queue present", "tool status descriptor present"],
            ui_prompts=[
                "Show suggested next action and risk before execution.",
                "Every external tool or install request creates an approval-gated receipt.",
            ],
        ),
    }
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_visual_catalog_path(root: Path) -> Path:
    return trinity_root(root) / "ui" / "smart_floor_visual_catalog.json"


def default_visual_report_path(root: Path) -> Path:
    return Path(root) / "dataindex" / "22_SMART_FLOOR_VISUAL_ANALYSIS.md"


def default_smart_floor_widget_export_path(root: Path) -> Path:
    return trinity_root(root) / "ui" / "smart_floor_widget_export.json"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _relative_or_string(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except Exception:
        return str(path)


def analyze_floor_python_file(root: Path, floor: str) -> dict[str, Any]:
    root = Path(root)
    contract = FLOOR_VISUAL_CONTRACTS[floor]
    source = root / contract.source_file
    if not source.exists():
        return {
            "source_file": contract.source_file,
            "present": False,
            "line_count": 0,
            "class_count": 0,
            "function_count": 0,
            "notebook_mentions": 0,
            "bento_mentions": 0,
            "chart_mentions": 0,
            "map_mentions": 0,
            "simulation_mentions": 0,
            "smoke_mentions": 0,
            "interaction_terms": [],
            "analysis": "missing floor entrypoint",
        }

    text = source.read_text(encoding="utf-8", errors="ignore")
    lowered = text.lower()
    interaction_terms = [
        term
        for term in ("Notebook", "Canvas", "Treeview", "Bento", "3D", "simulation", "chart", "map", "diagnostic")
        if term.lower() in lowered
    ]
    return {
        "source_file": _relative_or_string(root, source),
        "present": True,
        "size_bytes": source.stat().st_size,
        "line_count": len(text.splitlines()),
        "class_count": len(re.findall(r"^\s*class\s+", text, flags=re.MULTILINE)),
        "function_count": len(re.findall(r"^\s*def\s+", text, flags=re.MULTILINE)),
        "notebook_mentions": text.count("Notebook"),
        "bento_mentions": len(re.findall(r"bento", text, flags=re.IGNORECASE)),
        "chart_mentions": len(re.findall(r"chart|graph|plot", text, flags=re.IGNORECASE)),
        "map_mentions": len(re.findall(r"\bmap\b|3d|visualization", text, flags=re.IGNORECASE)),
        "simulation_mentions": len(re.findall(r"simulation|scenario|gmat|ephemer", text, flags=re.IGNORECASE)),
        "smoke_mentions": len(re.findall(r"smoke|diagnostic|health", text, flags=re.IGNORECASE)),
        "interaction_terms": interaction_terms,
        "analysis": (
            "entrypoint has direct UI surfaces"
            if "Notebook" in interaction_terms or "Bento" in interaction_terms
            else "entrypoint needs UI descriptor consumption"
        ),
    }


def analyze_floor_python_files(root: Path) -> dict[str, dict[str, Any]]:
    return {floor: analyze_floor_python_file(root, floor) for floor in FLOOR_VISUAL_CONTRACTS}


def read_floor_manifest_summary(root: Path, floor: str) -> dict[str, Any]:
    root = Path(root)
    contract = FLOOR_VISUAL_CONTRACTS[floor]
    manifest_path = root / contract.manifest_dir / "_FLOOR_MANIFEST.json"
    manifest = _read_json(manifest_path)
    components = manifest.get("components") if isinstance(manifest.get("components"), list) else []
    enabled_components = [component for component in components if component.get("enabled", True)]
    return {
        "path": _relative_or_string(root, manifest_path),
        "present": bool(manifest),
        "floor_name": manifest.get("floor_name", contract.floor),
        "floor_id": manifest.get("floor_id"),
        "version": manifest.get("version"),
        "description": manifest.get("description"),
        "color": manifest.get("color"),
        "component_count": len(components),
        "enabled_component_count": len(enabled_components),
        "primary_components": [
            {
                "id": component.get("id"),
                "name": component.get("name"),
                "priority": component.get("priority"),
                "source_file": component.get("source_file"),
            }
            for component in enabled_components[:8]
        ],
    }


def floor_visual_widgets(floor: str) -> list[dict[str, str]]:
    return list(FLOOR_VISUAL_CONTRACTS[floor].bento_widgets)


def smoke_matrix(root: Path, *, include_catalog: bool = True) -> dict[str, Any]:
    root = Path(root)
    rows: list[dict[str, Any]] = []
    for floor, contract in FLOOR_VISUAL_CONTRACTS.items():
        source = analyze_floor_python_file(root, floor)
        manifest = read_floor_manifest_summary(root, floor)
        fidelity_checks = floor_fidelity_checks(floor)
        checks = [
            {"check": "manifest_present", "status": "pass" if manifest["present"] else "fail"},
            {"check": "source_present", "status": "pass" if source["present"] else "fail"},
            {"check": "bento_widgets_declared", "status": "pass" if contract.bento_widgets else "fail"},
            {"check": "charts_declared", "status": "pass" if contract.charts else "fail"},
            {"check": "maps_3d_declared", "status": "pass" if contract.maps_3d else "fail"},
            {"check": "scientific_tools_declared", "status": "pass" if contract.scientific_tools else "fail"},
            {"check": "simulation_hooks_declared", "status": "pass" if contract.simulation_hooks else "fail"},
            {"check": "smoke_checks_declared", "status": "pass" if contract.smoke_checks else "fail"},
        ]
        checks.extend(
            {"check": item["id"], "status": item["status"]}
            for item in fidelity_checks
        )
        rows.append(
            {
                "floor": floor,
                "z_level": contract.z_level,
                "status": "pass" if all(check["status"] == "pass" for check in checks) else "warn",
                "checks": checks,
                "fidelity_checks": fidelity_checks,
            }
        )
    totals = {
        "floors": len(rows),
        "pass": sum(1 for row in rows if row["status"] == "pass"),
        "warn": sum(1 for row in rows if row["status"] == "warn"),
        "fail": sum(1 for row in rows if row["status"] == "fail"),
    }
    payload: dict[str, Any] = {"generated_at": utc_now_iso(), "totals": totals, "rows": rows}
    if include_catalog:
        payload["catalog_path"] = str(default_visual_catalog_path(root))
    return payload


def build_smart_floor_visual_catalog(root: Path) -> dict[str, Any]:
    root = Path(root)
    python_analysis = analyze_floor_python_files(root)
    floors: dict[str, dict[str, Any]] = {}
    for floor, contract in FLOOR_VISUAL_CONTRACTS.items():
        floor_record = contract.to_dict()
        floor_record["manifest"] = read_floor_manifest_summary(root, floor)
        floor_record["python_analysis"] = python_analysis[floor]
        floor_record["visual_result_analysis"] = {
            "preview": "near-fullscreen preview or graph/map panel",
            "edit": "inline editor for supported docs, tables, settings, and descriptors",
            "proof": "Morpheus proof state or Oracle provenance shown as chips",
            "export": "JSON, table, chart image, or simulation artifact where supported",
            "loading": "progress/cancel overlay for long indexing, simulation, or dependency actions",
        }
        floor_record["resource_policy"] = {
            "default": "lazy_load_heavy_widgets",
            "maps_3d": "defer_until_visible_or_fullscreen",
            "charts": "render_from_cached_tables_first",
            "simulations": "require explicit run or replay action",
        }
        floors[floor] = floor_record

    return {
        "generated_at": utc_now_iso(),
        "root": str(root),
        "purpose": "Shared smart-floor UI, visualization, simulation, and smoke-test contract for the Bento OS shell.",
        "interaction_thesis": {
            "visual": "minimal glass bento command surface with scientific maps and proof state surfaced only when useful",
            "content": "project wall first, smart-floor actions second, raw provenance available but not default",
            "motion": "motion only for loading, selection, handoff routing, and simulation camera movement",
        },
        "floors": floors,
        "smoke_matrix": smoke_matrix(root, include_catalog=False),
        "project_wall_widgets": project_wall_smart_widget_descriptors(),
        "widget_templates": smart_floor_widget_templates(),
        "fidelity_matrix": smart_floor_fidelity_matrix(),
    }


def visual_result_analysis_plan(root: Path) -> dict[str, Any]:
    catalog = build_smart_floor_visual_catalog(root)
    wall_widgets = {widget["floor"]: widget for widget in catalog["project_wall_widgets"]}
    return {
        "generated_at": catalog["generated_at"],
        "surfaces": [
            {
                "floor": floor,
                "primary_surface": data["primary_surface"],
                "project_wall_widget_id": wall_widgets.get(floor, {}).get("id", ""),
                "widgets": [widget["id"] for widget in data["bento_widgets"]],
                "charts": [chart["id"] for chart in data["charts"]],
                "maps_3d": [item["id"] for item in data["maps_3d"]],
                "simulation_hooks": [hook["id"] for hook in data["simulation_hooks"]],
                "fidelity_checks": [check["id"] for check in floor_fidelity_checks(floor)],
            }
            for floor, data in catalog["floors"].items()
        ],
        "analysis_outputs": [
            "per-floor readiness matrix",
            "Bento widget availability table",
            "chart/map/simulation descriptor catalog",
            "project-wall smart widget descriptor export",
            "proof/provenance and handoff coverage report",
            "resource-gated render plan for heavy views",
        ],
    }


def write_smart_floor_visual_catalog(root: Path, output_path: Path | None = None) -> dict[str, Any]:
    destination = output_path or default_visual_catalog_path(root)
    payload = build_smart_floor_visual_catalog(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def write_smart_floor_visual_report(root: Path, output_path: Path | None = None) -> dict[str, Any]:
    root = Path(root)
    destination = output_path or default_visual_report_path(root)
    catalog = build_smart_floor_visual_catalog(root)
    smoke_by_floor = {row["floor"]: row["status"] for row in catalog["smoke_matrix"]["rows"]}
    lines = [
        "# Smart Floor Visual Analysis",
        "",
        f"Generated: {catalog['generated_at']}",
        "",
        "This pass consolidates floor Python analysis, manifest summaries, Bento widgets, chart/map contracts, simulation hooks, and smoke checks into one Trinity-owned visual catalog.",
        "",
        "## Floor Coverage",
        "",
        "| Floor | Z | Source lines | Widgets | Charts | 3D maps | Tools | Sim hooks | Status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for floor, data in catalog["floors"].items():
        lines.append(
            "| {floor} | {z} | {lines_count} | {widgets} | {charts} | {maps} | {tools} | {hooks} | {status} |".format(
                floor=floor,
                z=data["z_level"],
                lines_count=data["python_analysis"]["line_count"],
                widgets=len(data["bento_widgets"]),
                charts=len(data["charts"]),
                maps=len(data["maps_3d"]),
                tools=len(data["scientific_tools"]),
                hooks=len(data["simulation_hooks"]),
                status=smoke_by_floor.get(floor, "unknown"),
            )
        )
    lines.extend(
        [
            "",
            "## Fidelity Checks",
            "",
            "| Floor | Check | Status |",
            "| --- | --- | --- |",
        ]
    )
    for row in catalog["fidelity_matrix"]["rows"]:
        for check in row["checks"]:
            lines.append(f"| {row['floor']} | {check['label']} | {check['status']} |")
    lines.extend(
        [
            "",
            "## Operating Notes",
            "",
            "- Heavy maps, charts, dependency checks, and simulations are descriptor-backed and lazy-loaded until visible or explicitly opened.",
            "- Oracle holds originals and derived components; Morpheus proofs claims; Smith routes receipts; Merovingian visualizes diagnostics and release health.",
            "- TheConstruct owns heliocentric zoning, cluster overlays, GMAT batches, ephemerides, and replayable simulation artifacts.",
            "- Trinity exposes the shared settings, theme/background builder, project wall, Z-floor dropdown, and artifact preview language.",
        ]
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"path": str(destination), "catalog": catalog}

FLOOR_VISUAL_CONTRACTS.update(
    {
        "Smith": _contract(
            floor="Smith",
            floor_key="smith",
            z_level=-3,
            owner_role="Queue execution, receipts, dependency approvals, resumable workflow state, and action routing.",
            source_file="Z Axis/Smith.py",
            manifest_dir="Z Axis/Z-3_Smith",
            primary_surface="execution gateway with resumable queues, receipt table, dependency approvals, and Z Direct routing",
            bento_widgets=[
                {"id": "execution_queue", "label": "Queue", "mode": "job_table", "opens": "queued_actions"},
                {"id": "receipt_state", "label": "Receipts", "mode": "state_table", "opens": "handoff_receipts"},
                {"id": "dependency_approvals", "label": "Dependencies", "mode": "approval_table", "opens": "pip_or_tool_requests"},
                {"id": "z_direct_router", "label": "Z Direct", "mode": "router", "opens": "floor_routes"},
            ],
            charts=[
                {"id": "queue_health", "type": "throughput_chart", "purpose": "show active, blocked, failed, and complete jobs"},
                {"id": "receipt_age", "type": "aging_histogram", "purpose": "find stale handoffs and overdue confirmations"},
            ],
            maps_3d=[
                {"id": "handoff_route_map", "type": "floor_stack_map", "purpose": "show queued routes and confirmation path"},
                {"id": "job_dependency_graph", "type": "dependency_network", "purpose": "show blockers before execution"},
            ],
            scientific_tools=[
                {"id": "dependency_table_creator", "purpose": "create empty landing tables and approval tasks for missing dependencies"},
                {"id": "job_payload_validator", "purpose": "verify source, target, action, and rollback metadata before execution"},
            ],
            simulation_hooks=[
                {"id": "queue_dry_run", "purpose": "preview filesystem, project, or data movement before execution"},
                {"id": "handoff_replay", "purpose": "rebuild or resume state from receipts"},
            ],
            data_objects=["job_record", "receipt", "dependency_request", "approval_gate", "route_record"],
            handoffs=[
                {"to": "Neo", "intent": "request decision or instruction when blocked"},
                {"to": "Merovingian", "intent": "write audit and diagnostics for execution"},
                {"to": "All floors", "intent": "route confirmed work to the owning floor"},
            ],
            smoke_checks=["manifest present", "queue widget present", "receipt table present", "dependency approval descriptor present"],
            ui_prompts=[
                "Every route must show received, updated, complete, deleted, declassified, or failed state.",
                "Do not auto-install missing dependencies; create approval tasks and empty landing tables first.",
            ],
        ),
        "Merovingian": _contract(
            floor="Merovingian",
            floor_key="merovingian",
            z_level=-4,
            owner_role="Core services, audit, diagnostics, performance, storage, reports, and quality gates.",
            source_file="Z Axis/Merovingian.py",
            manifest_dir="Z Axis/Z-4_Merovingian",
            primary_surface="diagnostics and release desk with performance charts, smoke tests, audit tables, and cleanup reports",
            bento_widgets=[
                {"id": "diagnostics", "label": "Diagnostics", "mode": "status_matrix", "opens": "system_checks"},
                {"id": "performance", "label": "Performance", "mode": "chart_panel", "opens": "cpu_ram_io"},
                {"id": "release_clean", "label": "Release Clean", "mode": "checklist", "opens": "file_cull_report"},
                {"id": "audit_log", "label": "Audit", "mode": "table", "opens": "event_log"},
            ],
            charts=[
                {"id": "smoke_results", "type": "pass_warning_fail_bar", "purpose": "summarize launch, diagnostics, and tests"},
                {"id": "resource_budget", "type": "timeseries", "purpose": "track CPU, RAM, IO, and expensive widget gating"},
            ],
            maps_3d=[
                {"id": "system_dependency_graph", "type": "dependency_network", "purpose": "show runtime, tests, databases, and floor ownership"},
                {"id": "file_cull_map", "type": "artifact_tree_depth", "purpose": "show stale roots, retained data, and cleanup candidates"},
            ],
            scientific_tools=[
                {"id": "smoke_test_runner", "purpose": "run launch readiness, diagnostics, and targeted tests"},
                {"id": "telemetry_sampler", "purpose": "sample performance and defer heavy widgets when budgets are exceeded"},
            ],
            simulation_hooks=[
                {"id": "readiness_replay", "purpose": "re-run the last proof/test matrix and compare deltas"},
                {"id": "release_cull_dry_run", "purpose": "preview old logs, cache, and stale data removals before cull"},
            ],
            data_objects=["diagnostic_result", "smoke_result", "audit_event", "performance_sample", "cleanup_candidate"],
            handoffs=[
                {"to": "Architect", "intent": "report release readiness and cleanup status"},
                {"to": "Trinity", "intent": "surface progress bars, warnings, and loading state"},
                {"to": "Smith", "intent": "queue safe cleanup or maintenance actions"},
            ],
            smoke_checks=["manifest present", "diagnostics widget present", "performance chart present", "release clean descriptor present"],
            ui_prompts=[
                "One table/log per week or release run; avoid one-file-per-trivial-action logs.",
                "Use visual result analysis for pass/warn/fail, not hidden console-only output.",
            ],
        ),
    }
)

FLOOR_VISUAL_CONTRACTS.update(
    {
        "Morpheus": _contract(
            floor="Morpheus",
            floor_key="morpheus",
            z_level=-1,
            owner_role="Proofing, source comparison, validation, research desk, and confidence analysis.",
            source_file="Z Axis/Morpheus.py",
            manifest_dir="Z Axis/Z-1_Morpheus",
            primary_surface="review desk with split-source inspection, bellcurve confidence, and evidence comparison",
            bento_widgets=[
                {"id": "proof_queue", "label": "Proof Queue", "mode": "review_table", "opens": "pending_claims"},
                {"id": "source_compare", "label": "Compare", "mode": "split_view", "opens": "source_pairs"},
                {"id": "confidence_curve", "label": "Confidence", "mode": "chart", "opens": "proof_distribution"},
                {"id": "research_desk", "label": "Research Desk", "mode": "search_panel", "opens": "library_search"},
            ],
            charts=[
                {"id": "confidence_bellcurve", "type": "bellcurve", "purpose": "show proof confidence and unresolved tails"},
                {"id": "source_disagreement", "type": "matrix", "purpose": "compare source conflicts and stale assumptions"},
            ],
            maps_3d=[
                {"id": "evidence_network", "type": "knowledge_graph", "purpose": "show sources, claims, proofs, and downstream artifacts"},
                {"id": "definition_neural_tree", "type": "semantic_depth_graph", "purpose": "visualize known terms and missing links"},
            ],
            scientific_tools=[
                {"id": "claim_extractor", "purpose": "separate claims, values, units, assumptions, and confidence fields"},
                {"id": "unit_consistency_checker", "purpose": "flag unit, date, and numeric mismatches before storage"},
            ],
            simulation_hooks=[
                {"id": "validation_replay", "purpose": "rerun proof decisions against updated Oracle or Construct artifacts"},
                {"id": "source_staleness_scan", "purpose": "identify facts that need re-verification before use"},
            ],
            data_objects=["proof_record", "claim_record", "source_pair", "confidence_score", "validation_note"],
            handoffs=[
                {"to": "Oracle", "intent": "write proofed knowns and definitions"},
                {"to": "Neo", "intent": "return validated next-action context"},
                {"to": "TheConstruct", "intent": "approve simulation input assumptions"},
            ],
            smoke_checks=["manifest present", "proof queue present", "source compare descriptor present", "confidence chart present"],
            ui_prompts=[
                "Do not bury proof state in prose; show confidence, source, and unresolved fields.",
                "Search results should become the main panel, with the knowledge graph as context/background.",
            ],
        ),
        "Oracle": _contract(
            floor="Oracle",
            floor_key="oracle",
            z_level=-2,
            owner_role="Original source custody, ingestion, library, dictionary, datatables, and provenance.",
            source_file="Z Axis/Oracle.py",
            manifest_dir="Z Axis/Z-2_Oracle",
            primary_surface="original-source and extracted-component desk with editable documents, tables, dictionary, and provenance",
            bento_widgets=[
                {"id": "originals_vault", "label": "Originals", "mode": "source_browser", "opens": "canonical_files"},
                {"id": "ingestion_pipeline", "label": "Ingestion", "mode": "pipeline", "opens": "extract_tasks"},
                {"id": "dictionary_it", "label": "Dictionary.IT", "mode": "search_table", "opens": "known_terms"},
                {"id": "datatable_builder", "label": "Datatables", "mode": "editable_table", "opens": "structured_objects"},
            ],
            charts=[
                {"id": "ingestion_breakdown", "type": "stacked_bar", "purpose": "show knowns, tables, tasks, strings, and objects extracted"},
                {"id": "provenance_density", "type": "sunburst", "purpose": "show source-to-object lineage and proof state"},
            ],
            maps_3d=[
                {"id": "library_neural_index", "type": "semantic_depth_graph", "purpose": "browse dictionary, library, encyclopedia, and datatable links"},
                {"id": "source_lineage_map", "type": "artifact_tree_depth", "purpose": "show original files, derived components, and handoffs"},
            ],
            scientific_tools=[
                {"id": "object_definition_extractor", "purpose": "extract terms, dimensions, units, entities, and incomplete object records"},
                {"id": "dictionary_category_classifier", "purpose": "classify new dictionary categories and queue Neo review where needed"},
            ],
            simulation_hooks=[
                {"id": "ingestion_dry_run", "purpose": "preview extracted components before writing to floor data"},
                {"id": "knowns_rebuild", "purpose": "rebuild derived known tables from originals and proof records"},
            ],
            data_objects=["original_file", "extracted_component", "dictionary_term", "datatable_row", "provenance_record"],
            handoffs=[
                {"to": "Morpheus", "intent": "proof extracted claims and definitions"},
                {"to": "TheConstruct", "intent": "send simulation-ready datasets"},
                {"to": "Smith", "intent": "queue ingestion or filesystem work"},
            ],
            smoke_checks=["manifest present", "originals widget present", "dictionary.IT descriptor present", "datatable builder present"],
            ui_prompts=[
                "Hold originals intact and editable through Oracle custody.",
                "Derived extracted components move through Morpheus before becoming trusted knowns.",
            ],
        ),
    }
)

FLOOR_VISUAL_CONTRACTS.update(
    {
        "Architect": _contract(
            floor="Architect",
            floor_key="architect",
            z_level=1,
            owner_role="Governance, project planning, approvals, D-root publishing, and finalization queues.",
            source_file="Z Axis/Architect.py",
            manifest_dir="Z Axis/Z+1_Architect",
            primary_surface="project governance board with timeline, approvals, publish snapshot, and finalization queue",
            bento_widgets=[
                {"id": "project_manager", "label": "Projects", "mode": "tree_table", "opens": "project_registry"},
                {"id": "approval_board", "label": "Approvals", "mode": "kanban_table", "opens": "governed_changes"},
                {"id": "publish_snapshot", "label": "Publish", "mode": "wizard_drawer", "opens": "d_root_snapshot"},
                {"id": "finalization_queue", "label": "Finalization", "mode": "checklist", "opens": "release_tasks"},
            ],
            charts=[
                {"id": "project_timeline", "type": "gantt", "purpose": "show stage, owner, and blocked status"},
                {"id": "publish_readiness", "type": "progress_matrix", "purpose": "summarize tests, culls, docs, and approvals"},
            ],
            maps_3d=[
                {"id": "governance_route_map", "type": "floor_stack_map", "purpose": "visualize approval routes across floors"},
                {"id": "publish_snapshot_map", "type": "artifact_tree_depth", "purpose": "show C-root to D-root publish inclusion"},
            ],
            scientific_tools=[
                {"id": "change_impact_analyzer", "purpose": "check which floors and project objects are affected by a change"},
                {"id": "release_contract_validator", "purpose": "verify V0.10.0 smoke, docs, culls, and package requirements"},
            ],
            simulation_hooks=[
                {"id": "publish_dry_run", "purpose": "simulate D-root overwrite snapshot before actual publish"},
                {"id": "workflow_timeline_projection", "purpose": "estimate completion and blocking dependencies"},
            ],
            data_objects=["project_record", "approval_record", "publish_manifest", "finalization_task", "release_gate"],
            handoffs=[
                {"to": "Trinity", "intent": "apply approved UI/settings changes"},
                {"to": "Merovingian", "intent": "verify release, storage, diagnostics, and audit state"},
                {"to": "Smith", "intent": "schedule approved filesystem or project registry actions"},
            ],
            smoke_checks=["manifest present", "project registry present", "publish snapshot descriptor present", "finalization queue present"],
            ui_prompts=[
                "Do not touch D-root until publish approval.",
                "Treat C-root as the live source of truth and D-root as overwrite-only output.",
            ],
        ),
        "TheConstruct": _contract(
            floor="TheConstruct",
            floor_key="construct",
            z_level=0,
            owner_role="Scientific simulation, Holospace, heliocentric zoning, GMAT batches, and 3D visual output.",
            source_file="Z Axis/TheConstruct.py",
            manifest_dir="Z Axis/Z0_TheConstruct",
            primary_surface="scenario lab with physics calculators, 3D map widgets, zoning grids, and replayable simulation artifacts",
            bento_widgets=[
                {"id": "heliocentric_grid", "label": "Heliocentric Grid", "mode": "3d_map", "opens": "zoning_engine"},
                {"id": "asteroid_clusters", "label": "Clusters", "mode": "heatmap", "opens": "cluster_engine"},
                {"id": "gmat_batch", "label": "GMAT Batch", "mode": "mission_table", "opens": "mission_exports"},
                {"id": "scenario_lab", "label": "Scenario Lab", "mode": "sandbox", "opens": "simulation_workspace"},
            ],
            charts=[
                {"id": "zone_summary", "type": "voxel_summary_table", "purpose": "count, density, metal proxy, accessibility by zone"},
                {"id": "target_shortlist", "type": "ranked_scatter", "purpose": "rank top N mission targets by cluster and accessibility"},
            ],
            maps_3d=[
                {"id": "orbital_rings", "type": "threejs_or_plotly_3d", "purpose": "render AU bands, asteroid cloud, and clusters"},
                {"id": "holospace_sandbox", "type": "interactive_3d_environment", "purpose": "navigate scenario objects with explicit immersive controls"},
            ],
            scientific_tools=[
                {"id": "assign_zone", "purpose": "classify asteroid rows by semi-major axis, eccentricity, and inclination"},
                {"id": "cluster_engine", "purpose": "run KMeans, HDBSCAN, or histogram peaks after zoning"},
                {"id": "gmat_exporter", "purpose": "export discrete top targets, ephemerides, and batch mission inputs"},
            ],
            simulation_hooks=[
                {"id": "ephemeris_rerun", "purpose": "save scenario parameters and ephemerides for replay or sharing"},
                {"id": "pds_refinement_layer", "purpose": "apply PDS mission datasets only after target selection for micro-validation"},
            ],
            data_objects=["zone_summary", "cluster_record", "target_shortlist", "ephemeris", "gmat_batch", "scenario_run"],
            handoffs=[
                {"to": "Oracle", "intent": "store input datasets, extracted parameters, and output artifacts"},
                {"to": "Morpheus", "intent": "proof source data and validation assumptions"},
                {"to": "Architect", "intent": "publish approved simulation package"},
            ],
            smoke_checks=["manifest present", "zoning widget present", "3D map descriptor present", "simulation rerun descriptor present"],
            ui_prompts=[
                "Use zoning and clustering before RFS/EMFF target classification.",
                "GMAT receives discrete top targets, not bulk asteroid catalogs.",
                "PDS data is a refinement layer, not the bulk macro map.",
            ],
        ),
    }
)


FLOOR_FIDELITY_REQUIREMENTS: dict[str, tuple[dict[str, Any], ...]] = {
    "TheConstruct": (
        {
            "id": "construct_zoning",
            "label": "TheConstruct zoning grid and cluster flow",
            "requires": {
                "bento_widgets": ("heliocentric_grid", "asteroid_clusters"),
                "scientific_tools": ("assign_zone", "cluster_engine"),
                "data_objects": ("zone_summary", "cluster_record"),
            },
        },
        {
            "id": "construct_gmat_batch",
            "label": "TheConstruct GMAT target export flow",
            "requires": {
                "bento_widgets": ("gmat_batch",),
                "scientific_tools": ("gmat_exporter",),
                "data_objects": ("target_shortlist", "gmat_batch"),
            },
        },
        {
            "id": "construct_ephemeris_rerun",
            "label": "TheConstruct ephemeris replay flow",
            "requires": {
                "simulation_hooks": ("ephemeris_rerun",),
                "data_objects": ("ephemeris", "scenario_run"),
            },
        },
    ),
    "Oracle": (
        {
            "id": "oracle_originals_to_proof",
            "label": "Oracle originals, dictionary, and proof handoff",
            "requires": {
                "bento_widgets": ("originals_vault", "dictionary_it", "datatable_builder"),
                "data_objects": ("original_file", "dictionary_term", "datatable_row", "provenance_record"),
                "handoffs": ("Morpheus",),
            },
        },
    ),
    "Morpheus": (
        {
            "id": "morpheus_proof_flow",
            "label": "Morpheus proof queue, comparison, and confidence flow",
            "requires": {
                "bento_widgets": ("proof_queue", "source_compare", "confidence_curve"),
                "charts": ("confidence_bellcurve",),
                "data_objects": ("proof_record", "claim_record", "confidence_score"),
                "handoffs": ("Oracle",),
            },
        },
    ),
    "Smith": (
        {
            "id": "smith_receipt_flow",
            "label": "Smith receipt and resumable handoff flow",
            "requires": {
                "bento_widgets": ("execution_queue", "receipt_state"),
                "data_objects": ("job_record", "receipt", "route_record"),
                "simulation_hooks": ("handoff_replay",),
            },
        },
        {
            "id": "smith_dependency_gate",
            "label": "Smith dependency approval gate",
            "requires": {
                "bento_widgets": ("dependency_approvals",),
                "scientific_tools": ("dependency_table_creator", "job_payload_validator"),
            },
        },
    ),
    "Merovingian": (
        {
            "id": "merovingian_diagnostics",
            "label": "Merovingian diagnostics, performance, and release clean flow",
            "requires": {
                "bento_widgets": ("diagnostics", "performance", "release_clean"),
                "charts": ("smoke_results", "resource_budget"),
                "data_objects": ("diagnostic_result", "performance_sample", "cleanup_candidate"),
            },
        },
        {
            "id": "merovingian_release_replay",
            "label": "Merovingian smoke replay and release dry-run flow",
            "requires": {
                "scientific_tools": ("smoke_test_runner", "telemetry_sampler"),
                "simulation_hooks": ("readiness_replay", "release_cull_dry_run"),
            },
        },
    ),
}


def _contract_id_set(contract: SmartFloorVisualContract, field_name: str) -> set[str]:
    value = getattr(contract, field_name)
    if field_name == "data_objects":
        return set(value)
    if field_name == "handoffs":
        return {str(item.get("to")) for item in value}
    return {str(item.get("id")) for item in value}


def floor_fidelity_checks(floor: str) -> list[dict[str, Any]]:
    contract = FLOOR_VISUAL_CONTRACTS[floor]
    checks: list[dict[str, Any]] = []
    for requirement in FLOOR_FIDELITY_REQUIREMENTS.get(floor, ()):
        missing: dict[str, list[str]] = {}
        for field_name, required_values in requirement["requires"].items():
            available = _contract_id_set(contract, field_name)
            missing_values = [value for value in required_values if value not in available]
            if missing_values:
                missing[field_name] = missing_values
        checks.append(
            {
                "id": requirement["id"],
                "label": requirement["label"],
                "floor": floor,
                "status": "pass" if not missing else "fail",
                "requires": {
                    field_name: list(values)
                    for field_name, values in requirement["requires"].items()
                },
                "missing": missing,
            }
        )
    return checks


def smart_floor_fidelity_matrix() -> dict[str, Any]:
    rows = []
    for floor in FLOOR_VISUAL_CONTRACTS:
        checks = floor_fidelity_checks(floor)
        rows.append(
            {
                "floor": floor,
                "status": "pass" if all(check["status"] == "pass" for check in checks) else "warn",
                "checks": checks,
            }
        )
    checked_rows = [row for row in rows if row["checks"]]
    return {
        "generated_at": utc_now_iso(),
        "checked_floor_count": len(checked_rows),
        "check_count": sum(len(row["checks"]) for row in checked_rows),
        "pass": sum(1 for row in checked_rows if row["status"] == "pass"),
        "warn": sum(1 for row in checked_rows if row["status"] == "warn"),
        "rows": rows,
    }


def smart_floor_widget_templates(floor: str | None = None) -> list[dict[str, Any]]:
    floors = [floor] if floor else list(FLOOR_VISUAL_CONTRACTS)
    templates: list[dict[str, Any]] = []
    for floor_name in floors:
        contract = FLOOR_VISUAL_CONTRACTS[floor_name]
        for widget in contract.bento_widgets:
            widget_id = str(widget["id"])
            label = str(widget.get("label") or widget_id.replace("_", " ").title())
            templates.append(
                {
                    "id": f"{contract.floor_key}.{widget_id}",
                    "widget_id": widget_id,
                    "label": label,
                    "floor": contract.floor,
                    "floor_key": contract.floor_key,
                    "z_level": contract.z_level,
                    "mode": str(widget.get("mode") or "panel"),
                    "opens": str(widget.get("opens") or ""),
                    "owner_role": contract.owner_role,
                    "primary_surface": contract.primary_surface,
                    "folder": "component_sets/Smart Widgets",
                    "tile_kind": "smart_widget",
                    "export": {"supported": True, "formats": ["json", "project_wall_tile"]},
                    "tile_template": {
                        "kind": "smart_widget",
                        "label": label,
                        "folder": "component_sets/Smart Widgets",
                        "floor": contract.floor,
                        "target": str(widget.get("opens") or contract.primary_surface),
                        "mode": str(widget.get("mode") or "panel"),
                        "preview": contract.owner_role,
                    },
                }
            )
    return templates


def project_wall_smart_widget_descriptors(floor: str | None = None) -> list[dict[str, Any]]:
    floors = [floor] if floor else list(FLOOR_VISUAL_CONTRACTS)
    descriptors: list[dict[str, Any]] = []
    for floor_name in floors:
        contract = FLOOR_VISUAL_CONTRACTS[floor_name]
        templates = smart_floor_widget_templates(floor_name)
        fidelity_checks = floor_fidelity_checks(floor_name)
        descriptors.append(
            {
                "id": f"floor.{contract.floor_key}",
                "label": f"{contract.floor} Smart Floor",
                "floor": contract.floor,
                "floor_key": contract.floor_key,
                "z_level": contract.z_level,
                "mode": "floor_contract",
                "target": contract.primary_surface,
                "opens": contract.primary_surface,
                "purpose": contract.owner_role,
                "source_contract": contract.source_file,
                "manifest_dir": contract.manifest_dir,
                "contract_widgets": [template["widget_id"] for template in templates],
                "widget_templates": templates,
                "fidelity_checks": fidelity_checks,
                "export": {"supported": True, "formats": ["json", "project_wall_tile"]},
            }
        )
    return descriptors


def build_smart_floor_widget_export(root: Path) -> dict[str, Any]:
    root = Path(root)
    widget_templates = smart_floor_widget_templates()
    project_wall_widgets = project_wall_smart_widget_descriptors()
    return {
        "generated_at": utc_now_iso(),
        "root": str(root),
        "widget_template_count": len(widget_templates),
        "project_wall_widget_count": len(project_wall_widgets),
        "widget_templates": widget_templates,
        "project_wall_widgets": project_wall_widgets,
        "fidelity_matrix": smart_floor_fidelity_matrix(),
    }


def write_smart_floor_widget_export(root: Path, output_path: Path | None = None) -> dict[str, Any]:
    output_path = output_path or default_smart_floor_widget_export_path(root)
    payload = build_smart_floor_widget_export(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
