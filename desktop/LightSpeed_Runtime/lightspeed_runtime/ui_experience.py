from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lightspeed_runtime.storage_paths import trinity_root


def default_ui_experience_alignment_path(root: Path) -> Path:
    return trinity_root(root) / "ui" / "ui_experience_alignment.json"


def default_original_ui_pdf_path(root: Path) -> Path:
    root = Path(root)
    try:
        return root.parents[1] / "LightSpeed UI.pdf"
    except IndexError:
        return root.parent / "LightSpeed UI.pdf"


def _pdf_page_count(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        from PyPDF2 import PdfReader  # type: ignore

        return len(PdfReader(str(path)).pages)
    except Exception:
        return None


def build_ui_experience_alignment(root: Path, *, source_pdf_path: Path | None = None) -> dict:
    root = Path(root)
    source_pdf = Path(source_pdf_path) if source_pdf_path else default_original_ui_pdf_path(root)
    page_count = _pdf_page_count(source_pdf) or 14
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "owner_floor": "Trinity",
        "support_floors": ["Architect", "Neo", "Oracle", "Morpheus", "TheConstruct"],
        "source_pdf": str(source_pdf),
        "source_exists": source_pdf.exists(),
        "source_page_count": page_count,
        "visual_thesis": (
            "LightSpeed should read as a fixed curved 1.5m Bento panel wall over an optional holospace, "
            "with dense operational bento sections rather than old wizard-page sprawl."
        ),
        "content_plan": [
            {
                "mode": "Workspace",
                "owner_floor": "Trinity",
                "job": "Default project dashboard for folders, component sets, editable files, tables, bento widgets, notices, and visible page settings.",
            },
            {
                "mode": "Operator",
                "owner_floor": "Neo",
                "job": "Achilles/Cognigrex manager console for briefs, approvals, handoffs, and bounded action proposals.",
            },
            {
                "mode": "Review",
                "owner_floor": "Morpheus",
                "job": "Proofing desk for extracted components, source comparisons, dictionary lookups, and Z Direct handoff review.",
            },
            {
                "mode": "Holospace",
                "owner_floor": "TheConstruct",
                "job": "Immersive graph/render/simulation surface where WASD and mouse-look are expected and visibly indicated.",
            },
            {
                "mode": "Publish",
                "owner_floor": "Architect",
                "job": "Governance and publish packaging mode for approved project artifacts and simulation outputs.",
            },
            {
                "mode": "Settings",
                "owner_floor": "Trinity",
                "job": "Unified theme, background, icons, widgets, API tools, dependency approvals, and setup wizard surface.",
            },
        ],
        "original_page_patterns": [
            {
                "pattern": "file_analysis_gate",
                "source_pages": [1, 6, 11],
                "original_behavior": "Document/file name, business context, notes, live history, AI search, and Analyse Y/N gates.",
                "bento_destination": "Morpheus review cards with Oracle provenance and Architect approval/export controls.",
            },
            {
                "pattern": "company_user_project_wizards",
                "source_pages": [2, 3, 4, 5],
                "original_behavior": "Add Company, New User, Add Project, Add Sub-Project, Add File, with Achilles assist fields.",
                "bento_destination": "Compact modal/toggle flows launched from Workspace or Operator, not standalone blank pages.",
            },
            {
                "pattern": "menu_drilldown",
                "source_pages": [8, 9, 14],
                "original_behavior": "Main menu, projects menu, selected option, sub-options, blurbs, and Achilles input.",
                "bento_destination": "Command palette, visible page menu, and grouped action bars.",
            },
            {
                "pattern": "graph_render_context",
                "source_pages": [10],
                "original_behavior": "Graph/render title, live graph information, file name, business context, and Achilles help.",
                "bento_destination": "TheConstruct holospace panel with simulation overlays and bento-side context.",
            },
            {
                "pattern": "dashboard_notice_board",
                "source_pages": [12, 13],
                "original_behavior": "User notice board, project/task lists, profile/clearance context, quick links, and project actions.",
                "bento_destination": "Workspace shell operational signals plus Neo operator queue and Architect publish/governance state.",
            },
        ],
        "bento_translation_rules": [
            "Do not recreate old blank wizard pages when a modal, toggle, bento section, or grouped action bar can carry the job.",
            "Keep Ask Achilles persistent through Neo or an operator strip, not as duplicated ad hoc text inputs on every floor.",
            "Use primary click only to select, open, or activate visible targets.",
            "Put page settings in Ctrl+Shift+S, Settings, an ellipsis/page menu, or visible controls.",
            "Use Ctrl+S for search and Ctrl+K as an advanced command/search palette.",
            "Use Tab for focus traversal, arrows for list/grid movement, Enter to open/commit, and Escape to back out or close transient UI.",
            "Restrict WASD and mouse-look to explicit Holospace or Immersive contexts with an on-screen mode indicator.",
            "Route document history, notes, proofing, and AI search through Morpheus review surfaces backed by Oracle provenance.",
            "Route graph/render/simulation context through TheConstruct while keeping publishable outputs attached to Architect.",
            "Keep raw mounted files behind provenance/source actions; default views should be curated cards, tables, summaries, and presets.",
            "Let projects open into bento component sets where documents, icons, smart previews, tasks, maps, charts, and simulations can be edited or routed.",
            "Keep original source files in Oracle while extracted strings, object data, tasks, definitions, and tables move through Morpheus and Z Direct queues.",
        ],
        "fixed_panel_wall": {
            "approx_width_meters": 1.5,
            "form": "curved_bento_panel_wall",
            "behavior": "persistent desktop control surface with optional immersive expansion",
            "primary_density": "dense but readable operational bento",
            "avoid": ["blank pages", "long flat button rows", "raw JSON as primary UI", "implicit hidden click settings"],
        },
        "project_bento_model": {
            "project_selected_state": "main dashboard switches to the selected project and shows subfolders/component sets.",
            "component_set_contents": ["documents", "tables", "files", "static_icon_tiles", "smart_preview_tiles", "tasks", "visualizations", "simulations"],
            "single_click": "preview or near-fullscreen non-interactive read surface when supported",
            "double_click": "open full-screen editor/viewer or attach file if the tile has no file yet",
            "right_click": "show all available artifact, floor, project, and widget actions grouped in submenus",
            "resize_policy": "icons and smart preview tiles can resize and smart-refit inside the bento wall",
        },
        "background_control_model": {
            "base_theme_modes": ["minimal", "balanced", "futuristic_gamelike"],
            "editable_inputs": ["solid_color", "multi_stop_gradient", "uploaded_picture", "uploaded_environment_reference"],
            "3d_desktop_policy": "Dropped visual assets can create a 3D-desktop feel, but heavy traversal/rendering stays opt-in through Holospace.",
        },
        "queue_alignment": {
            "completed_by_this_contract": ["UX-05", "UX-06", "UX-07"],
            "next_candidate_tasks": ["OS-07", "OS-24", "OS-25", "OS-26", "OS-27", "SF-04"],
            "reason": (
                "This contract makes keyboard conventions, Holospace-specific movement, and visible mode switching explicit "
                "while preserving the original UI intent inside the Bento system."
            ),
        },
        "next_pass_notes": [
            "Convert project/company/user/file setup into compact modal actions in Trinity/Architect instead of page sprawl.",
            "Expose one small mode switcher in the shell header: Workspace, Operator, Holospace.",
            "Make Morpheus document history and AI search cards mirror the original file review pages without raw inspectors.",
            "Let TheConstruct use the graph/render pattern as a bento-side simulation context panel.",
        ],
    }


def read_ui_experience_alignment(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_ui_experience_alignment_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_ui_experience_alignment(
    root: Path,
    *,
    output_path: Path | None = None,
    source_pdf_path: Path | None = None,
) -> dict:
    destination = output_path or default_ui_experience_alignment_path(root)
    payload = build_ui_experience_alignment(root, source_pdf_path=source_pdf_path)
    payload["path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
