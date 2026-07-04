from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lightspeed_runtime.storage_paths import trinity_root


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_ui_polish_contract_path(root: Path) -> Path:
    return trinity_root(root) / "ui" / "ui_polish_contract.json"


def read_ui_polish_contract(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_ui_polish_contract_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_ui_polish_contract(root: Path) -> dict:
    return {
        "generated_at": utc_now_iso(),
        "owner_floor": "Trinity",
        "support_floors": ["Architect", "Neo", "Oracle", "Morpheus", "TheConstruct"],
        "contract_path": str(default_ui_polish_contract_path(root)),
        "purpose": "Final Bento/glass UI refinement contract for functional motion, spacing, hierarchy, help, and ownership cues.",
        "motion_policy": {
            "decorative_motion": "disabled_by_default",
            "allowed_motion": [
                "panel_open_close",
                "mode_transition",
                "selection_focus",
                "simulation_camera_orbit",
                "validation_state_change",
            ],
            "rule": "Motion must explain state, depth, causality, or simulation movement; do not use motion as ornament.",
        },
        "typography_and_spacing": {
            "font_stack": ["Segoe UI Variable", "Segoe UI", "Consolas for telemetry"],
            "scale": {
                "page_title": 16,
                "section_label": 12,
                "body": 10,
                "telemetry": 10,
            },
            "spacing_tokens_px": {
                "panel_outer": 12,
                "panel_inner": 10,
                "section_gap": 8,
                "action_gap": 8,
            },
            "rule": "Use compact but readable spacing; keep action density grouped by workflow instead of long flat rows.",
        },
        "glass_hierarchy": [
            {
                "level": "primary",
                "use": "Workspace, Operator, and Holospace mode containers",
                "guidance": "Strongest glass treatment only for primary mode structure.",
            },
            {
                "level": "secondary",
                "use": "Bento cards and floor panels",
                "guidance": "Moderate surface treatment for grouped work areas.",
            },
            {
                "level": "tertiary",
                "use": "Telemetry, preview, provenance, and status strips",
                "guidance": "Minimal treatment; text clarity wins over shine.",
            },
        ],
        "shortcut_hints": [
            "Ctrl+S opens search.",
            "Ctrl+K opens the advanced command/search palette.",
            "Ctrl+Shift+S opens visible settings.",
            "Tab moves focus; Enter activates; Escape closes or returns focus.",
            "WASD and mouse-look are Holospace-only and require an explicit immersive mode indicator.",
        ],
        "floor_ownership": {
            "Oracle": "Catalog, knowns, definitions, datatables, and provenance.",
            "Morpheus": "Review, proofing, comparison, and source inspection.",
            "TheConstruct": "Scenario design, simulation presets, zoning, and Holospace output.",
            "Architect": "Governance, approvals, publish packages, and finalization control.",
            "Neo": "Achilles/Cognigrex operator shell and manager-agent execution.",
            "Smith": "Job routing, resumable workflow state, and executor gateway.",
            "Merovingian": "Audit, telemetry, quality, reports, storage, and database ownership.",
            "Trinity": "Workspace shell, setup, menus, settings, and Bento interaction language.",
        },
        "page_pattern": {
            "header": "title / owner / page menu / short status / shortcut hint",
            "body": "curated cards first, provenance/raw source access second",
            "actions": "group by Refresh, Build, Review, Approve, Publish, Cleanup",
            "settings": "visible menu, ellipsis, or Ctrl+Shift+S; never hidden primary-click behavior",
        },
        "shell_surface_contract": {
            "primary_surface": "project Bento wall",
            "top_level_controls": [
                "Search / command palette",
                "Project selector",
                "One Z-floor dropdown",
                "Visible settings/theme control",
                "Help / keyboard defaults",
            ],
            "rule": "Do not add duplicate floor buttons, theme buttons, or feature pages when a page-local Bento action or dropdown route can call the same behavior.",
            "floor_launch_mode": "Z-floor entries are functions and handoff targets first; full floor windows are explicit drill-ins, not default pages.",
        },
        "bento_project_wall": {
            "project_navigation": "select project -> enter component sets -> enter subfolder or artifact group -> preview/edit documents, tables, files, icons, smart previews, tasks, maps, and simulations",
            "artifact_clicks": "single click previews; double click opens full-screen editor/viewer; right click lists grouped context actions",
            "keyboard_navigation": "Tab enters the wall, arrow keys move between tiles, Enter/Space opens the selected tile.",
            "loading_policy": "show loading/progress bars for startup, floor initialization, source indexing, long simulations, and dependency checks",
            "tile_families": [
                "project",
                "component_set",
                "subfolder",
                "document",
                "table_or_dataset",
                "chart_widget",
                "map_widget",
                "simulation_widget",
                "floor_action",
                "provenance",
            ],
            "document_workflow": {
                "preview": "single-click opens an in-wall preview or drawer with owner floor, path, type, and provenance.",
                "edit": "double-click opens the largest available editor/viewer without replacing the project wall route.",
                "handoff": "Z Direct and tile context actions send selected artifacts to the active floor with a receipt.",
                "subfolders": "folder and subfolder tiles filter the wall in place and keep breadcrumb/back behavior visible.",
            },
        },
        "z_floor_dropdown_contract": {
            "control_count": 1,
            "visible_label": "Z-floor dropdown",
            "placement": "shell header or project wall command strip; page-local links call this route instead of creating new launch controls",
            "default_actions": [
                "set active floor",
                "open owning floor function",
                "queue selected artifacts for Z Direct handoff",
                "open full floor shell only on explicit drill-in",
            ],
            "copy_rule": "Floor labels should read as capabilities/functions, not as competing pages.",
        },
        "known_interaction_defaults": {
            "selection": "single click selects and previews; double click opens the best editor/viewer; Escape closes overlays before leaving the page.",
            "keyboard": "Tab enters controls, arrow keys move across Bento tiles, Enter/Space activates, Ctrl+S opens search, Ctrl+K opens command/search, Ctrl+Shift+S opens settings.",
            "context_menu": "right click groups Preview, Open/Edit, Favorite, floor routing, copy, and provenance actions by availability.",
            "fullscreen": "F11 toggles shell fullscreen; media/map/simulation fullscreen is a tile-level explicit action.",
            "holospace": "WASD and mouse-look are only active when the Construct/Holospace indicator is visible.",
        },
        "loading_bar_contract": {
            "show_for": [
                "startup bootstrap",
                "floor initialization",
                "source indexing and ingestion",
                "file import and duplicate handling",
                "dependency checks or install requests",
                "long simulations",
                "publish/export packaging",
            ],
            "states": ["queued", "loading", "running", "blocked", "complete", "failed", "cancelled"],
            "visual_requirements": "Every loader shows owner floor, current stage, determinate percent when known, cancel availability, and last safe fallback state.",
            "fallback_rule": "If a dependency or renderer is missing, show a blocked loader with next action instead of a blank panel.",
        },
        "dynamic_widget_contract": {
            "source": "lightspeed_runtime.smart_floor_visuals descriptor catalog",
            "required_descriptor_fields": [
                "id",
                "owner_floor",
                "title",
                "source_artifact_ids",
                "renderer",
                "loading_state",
                "empty_state",
                "error_state",
                "fullscreen_action",
                "handoff_actions",
            ],
            "chart_widgets": "Render compact Bento summaries first; open full chart panels only from explicit tile actions.",
            "map_widgets": "Use static or low-cost previews in the wall; lazy-load 3D maps when visible, selected, or fullscreen.",
            "simulation_widgets": "Expose preset, queue/run, progress, cancel, result artifacts, and rerun handoff without leaving the project wall.",
        },
        "implemented_interactions": [
            "Global Ctrl+S search and Ctrl+Shift+S settings.",
            "Global right-click context menu for search, settings, workspace navigation, and Z Floor routing.",
            "Bento single-click preview, double-click open/run, Enter/Space open/run, and arrow-key tile traversal.",
            "Bento right-click menu with Preview, Open / Run, Favorite, Set Active Floor, Open Owning Floor, and copy actions.",
            "Project component wall after project selection with default folders, subfolders, static icon tiles, imported file tiles, custom smart widgets, and Z-floor handoffs.",
            "Project wall near-fullscreen preview/edit for text, markdown, JSON, CSV/TSV, code, SQL, GMAT, and ephemeris-style artifacts.",
            "Project wall Z Direct handoff receipts from selected artifacts to target smart floors.",
            "Manifest-backed smart-floor action palette for adding enabled floor components, services, and capabilities as project widgets.",
            "IT Portal dashboard uses compact DB-backed activity at startup; heavier activity widgets remain explicit drill-ins.",
            "IT Portal floor tabs use one single-surface smart-floor shell with purpose, feature list, inspector, manifest actions, and settings callaways instead of nested floor notebooks.",
            "Startup and autostart policy is read through one runtime adapter and surfaced in Trinity, Smith, Merovingian, and each smart-floor shell.",
            "Project wall component-set selection now scopes the Bento grid instead of leaving every tile in one flat board.",
            "Project wall artifact previews now expose typed preview modes for image, PDF, map, spreadsheet, dataset, simulation, table, text, and metadata artifacts.",
            "Project wall right-click menus now consume model-backed grouped action availability instead of hard-coded UI-only action lists.",
            "Trinity Settings Hub now exposes a Background Builder for base mode, gradient/color, uploaded image path, environment reference, and scope.",
            "Smart-floor visual catalog now maps every floor to shared Bento widgets, charts, 3D maps, scientific tools, simulation hooks, smoke checks, and lazy-load resource policy.",
            "A 25-item misalignment register is generated into Trinity UI data and dataindex for the next implementation queue.",
            "F11 fullscreen toggle.",
        ],
        "duplicate_surface_amalgamation": [
            {
                "old_pattern": "multiple settings/theme/wizard entrypoints",
                "current_contract": "one Trinity settings library called from first-run, Ctrl+Shift+S, page menu, and widget settings",
                "status": "implemented_contract_needs_visual_walkthrough",
            },
            {
                "old_pattern": "Holospace as a top-level button plus workspace controls",
                "current_contract": "Workspace remains default; Holospace is an opt-in Construct context, not a competing primary button",
                "status": "implemented",
            },
            {
                "old_pattern": "startup, autostart, and launch options split across separate wizard/config pages",
                "current_contract": "read through lightspeed_runtime.startup_options and edit supported global toggles through Trinity Settings Hub",
                "status": "implemented",
            },
            {
                "old_pattern": "floor pages eagerly loading heavy full runtimes inside IT Portal",
                "current_contract": "IT Portal uses lightweight single-surface floor shells with explicit full-hub routing only on request",
                "status": "implemented",
            },
        ],
        "missing_interactive_visual_elements": [
            {
                "item": "near-fullscreen artifact preview",
                "need": "text/table preview and editing exist; next pass should add richer PDF, image, map, and simulation preview renderers",
                "owner_floor": "Trinity",
                "priority": "high",
            },
            {
                "item": "background builder",
                "need": "theme colors and gradients are configured; uploaded image/environment preview and per-page assignment still need visual controls",
                "owner_floor": "Trinity",
                "priority": "medium",
            },
            {
                "item": "loading/progress overlays",
                "need": "long ingestion, floor runtime open, dependency install request, and simulation export should show progress and cancellation affordances",
                "owner_floor": "Merovingian",
                "priority": "medium",
            },
            {
                "item": "visual neural library desk",
                "need": "dictionary/search data exists; the neural graph/search-desk visualization remains a visual implementation task",
                "owner_floor": "Morpheus",
                "priority": "medium",
            },
            {
                "item": "floor visual renderers",
                "need": "the shared smart-floor catalog now defines widgets, charts, 3D maps, and simulation hooks; next UI pass should bind these descriptors to live renderers inside the project wall and IT Portal single-surface shell",
                "owner_floor": "Trinity",
                "priority": "high",
            },
        ],
        "theme_control": {
            "base_themes": ["deep_space_laboratory_glass", "executive_bento_command", "futuristic_game_holospace"],
            "editable_backgrounds": ["colors", "multi_stop_gradients", "uploaded_images", "uploaded_environment_references"],
            "settings_owner": "Trinity settings library is called by first-run wizard, guided settings wizard, floor settings, and widget settings.",
            "required_controls": [
                "base theme",
                "background mode",
                "color tokens",
                "multi-stop gradient",
                "uploaded image path",
                "environment reference",
                "scope: global / project / page / widget",
                "preview",
                "apply",
                "reset",
            ],
            "binding_rule": "Theme/background edits must be editable from the visible settings route and reflected in Bento tiles, smart-floor shells, previews, charts, maps, and simulation panels.",
        },
        "next_ui_binding_tasks": [
            "Bind project, component-set, subfolder, and document tiles to one page-local Bento navigation stack with visible breadcrumb/back state.",
            "Route every page-local floor action through the single Z-floor dropdown / active-floor handoff adapter.",
            "Attach loading bars to startup, floor activation, ingestion, dependency checks, simulation runs, and publish/export packaging.",
            "Map smart-floor chart/map/simulation descriptors to live Bento renderers with preview, fullscreen, empty, blocked, and error states.",
            "Wire Trinity Background Builder controls into shell, project wall, floor shell, preview drawer, chart, map, and simulation surfaces.",
        ],
        "completed_by_this_contract": ["UX-13", "UX-14", "UX-15", "UX-16", "UX-17", "UX-18", "UX-19"],
        "final_pass_notes": [
            "Keep the current Bento/fixed-panel model and avoid recreating old full-screen wizard pages.",
            "Prefer pop-up or inline toggles for secondary content over empty standalone pages.",
            "Treat raw JSON and raw archives as advanced provenance views, not the default experience.",
        ],
    }


def write_ui_polish_contract(root: Path, output_path: Path | None = None) -> dict:
    destination = output_path or default_ui_polish_contract_path(root)
    payload = build_ui_polish_contract(root)
    payload["contract_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
