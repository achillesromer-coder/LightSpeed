from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lightspeed_runtime.storage_paths import trinity_root


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_operator_os_contract_path(root: Path) -> Path:
    return trinity_root(root) / "ui" / "operator_os_contract.json"


def build_operator_os_contract(root: Path) -> dict:
    """Build the single Trinity-owned contract for bento, theme, mode, and control behavior."""
    return {
        "generated_at": utc_now_iso(),
        "owner_floor": "Trinity",
        "support_floors": ["Neo", "Oracle", "Morpheus", "TheConstruct", "Architect", "Smith", "Merovingian"],
        "contract_path": str(default_operator_os_contract_path(root)),
        "source_model": "C-root canonical application; D-root publish snapshot only.",
        "main_interface": {
            "name": "Smart Bento Project Wall",
            "default_surface": "project_dashboard",
            "shape": "curved_1_5m_glass_panel_wall",
            "navigation": "select_project_then_enter_component_sets",
            "rule": "A project opens into subfolders/component sets; each set exposes documents, tables, files, widgets, maps, simulations, and action buttons as editable bento artifacts.",
        },
        "project_artifact_model": {
            "project": "Top-level work container selected from the landing dashboard.",
            "component_set": "Project subfolder holding related files, widgets, tasks, tables, and visualizations.",
            "static_icon_tile": "Icon tile for a file or action; single click previews, double click opens full screen, missing file prompts attach-file.",
            "smart_preview_tile": "Tile that previews document/table/chart/simulation content directly and can resize/refit.",
            "editable_artifact": "Any tile-backed document, table, file, visualization, simulation, or task record that can be opened, edited, routed, and versioned.",
            "side_bento_tab": "Context strip showing widgets/actions relevant to the selected project, folder, artifact, floor, or mode.",
        },
        "floor_landing_contract": {
            "Trinity": "Settings/setup/theme/API/background controls through one shared settings library and guided wizard entrypoints.",
            "Neo": "Front-facing Achilles/Cognigrex operator console for briefs, project proposals, approvals, and guidance.",
            "Oracle": "Intelligence desk with searchable IT dictionary, neural tree/library, original files, knowns, definitions, and datatables.",
            "Morpheus": "Review desk/search engine for proofing extracted components before floor updates.",
            "TheConstruct": "3D lab sandbox, Google-Maps-like zoomable overlays, orbital maps, simulations, and ephemeris artifacts.",
            "Architect": "Governance, project planning, publish packages, approvals, and release readiness.",
            "Smith": "Z Direct queues, received/updated/deleted handoffs, workflow routing, and dependency-install tasks.",
            "Merovingian": "Compact activity tables, health, telemetry, database state, quality reports, and root hygiene.",
        },
        "oracle_ingestion_handoff": {
            "original_file_policy": "Oracle receives and preserves the original file for edit, project assignment, or component-set attachment.",
            "ingestion_outputs": [
                "file components",
                "object definitions",
                "strings",
                "tasks",
                "datatable rows",
                "partial object data",
                "source links",
            ],
            "review_policy": "Morpheus reviews extracted components before they update other floor records.",
            "handoff_policy": "Z Direct carries backlog/listing/queue records floor-to-floor with received, updated, completed, deleted, or declassified state.",
            "progressive_object_policy": "Partial object data should merge across future documents when later sources fill missing fields.",
        },
        "mode_dropdown": {
            "modes": ["Workspace", "Operator", "Review", "Holospace", "Publish", "Settings"],
            "behavior": "Mode changes are explicit through a dropdown or visible control; mode-specific shortcuts and panels only appear where valid.",
        },
        "controls": {
            "search": "Ctrl+S",
            "settings": "Ctrl+Shift+S",
            "command_palette": "Ctrl+K remains acceptable as advanced command/search access.",
            "primary_click": "select_open_or_activate_visible_target",
            "double_click": "open_full_screen_or_edit",
            "single_click": "near_full_screen_preview_when_supported",
            "right_click": "context menu with all available artifact/floor/project actions grouped by submenu",
            "wasd": "Holospace_or_immersive_only",
        },
        "backgrounds": {
            "base_themes": ["deep_space_laboratory_glass", "executive_bento_command", "futuristic_game_holospace"],
            "editable": ["solid_color", "multi_stop_gradient", "uploaded_image", "uploaded_environment_reference"],
            "scan_policy": "Dropped backgrounds are treated as visual references for a 3D-desktop feel; they should not force heavy physics traversal unless Holospace is explicitly active.",
            "performance_policy": "Use visual cues, lazy loading, and static fallbacks before heavy 3D rendering.",
        },
        "shared_control_protocols": {
            "color_control": "lightspeed_runtime.protocol_sequence_registry.shared_color_control_protocol",
            "loading_state": "lightspeed_runtime.protocol_sequence_registry.shared_loading_protocol",
            "z_direct_cache_preload": "lightspeed_runtime.protocol_sequence_registry.z_direct_cache_preload_protocol",
            "rule": "Call shared protocols by reference instead of adding bespoke color/loading/Z Direct controls per surface.",
        },
        "performance_contract": {
            "startup": "Show startup/loading bars while core services, floors, reservoirs, and optional tools initialize.",
            "heavy_jobs": "Route long work through Smith queues so the UI does not freeze.",
            "logs": "Use compact activity tables with counters and timestamp cells instead of many one-off log files.",
            "simulations": "Save results as revisable/shareable ephemeris artifacts where relevant.",
            "external_tools": "External tools are controlled by a settings/API toggle and missing dependencies create Neo approval tasks rather than crashes.",
        },
        "settings_unification": {
            "single_library": "Theme managers, settings dialogs, setup wizards, startup wizards, icon controls, background controls, and API controls must call the same Trinity-owned settings library.",
            "entrypoints": ["first_startup_wizard", "guided_settings_wizard", "floor_or_widget_settings", "Ctrl+Shift+S"],
            "save_scope": "Changes save to the selected app, floor, project, component set, artifact, or widget as appropriate.",
        },
    }


def read_operator_os_contract(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_operator_os_contract_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_operator_os_contract(root: Path, output_path: Path | None = None) -> dict:
    destination = output_path or default_operator_os_contract_path(root)
    payload = build_operator_os_contract(root)
    payload["contract_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
