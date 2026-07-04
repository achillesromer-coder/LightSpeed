from __future__ import annotations

import json
import re
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from lightspeed_runtime.smart_floor_visuals import project_wall_smart_widget_descriptors


WALL_FILENAME = "project_wall.json"
TEXT_EDITABLE_SUFFIXES = {
    ".txt",
    ".md",
    ".markdown",
    ".json",
    ".csv",
    ".tsv",
    ".py",
    ".sql",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".log",
    ".gmat",
    ".eph",
}
TABLE_SUFFIXES = {".csv", ".tsv"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tif", ".tiff"}
PDF_SUFFIXES = {".pdf"}
SPREADSHEET_SUFFIXES = {".xlsx", ".xls"}
DATASET_SUFFIXES = {".parquet", ".duckdb", ".sqlite", ".db"}
MAP_SUFFIXES = {".geojson", ".kml", ".czml"}
SIMULATION_SUFFIXES = {".gmat", ".eph", ".bsp", ".spk", ".oem"}
BINARY_RENDER_SUFFIXES = PDF_SUFFIXES | IMAGE_SUFFIXES | SPREADSHEET_SUFFIXES | DATASET_SUFFIXES | SIMULATION_SUFFIXES
BINARY_PREVIEW_SUFFIXES = PDF_SUFFIXES | IMAGE_SUFFIXES | SPREADSHEET_SUFFIXES | DATASET_SUFFIXES | SIMULATION_SUFFIXES

DEFAULT_COMPONENT_SETS = [
    {
        "id": "documents",
        "label": "Documents",
        "folder": "component_sets/Documents",
        "purpose": "Original docs, notes, source previews, and Oracle provenance.",
        "icon": "[DOC]",
    },
    {
        "id": "tables",
        "label": "Tables",
        "folder": "component_sets/Tables",
        "purpose": "Extracted rows, datatables, calculations, and proof fields.",
        "icon": "[TAB]",
    },
    {
        "id": "static_icons",
        "label": "Static Icons",
        "folder": "component_sets/Static Icons",
        "purpose": "Pinned files, folders, links, and actions shown as icon tiles.",
        "icon": "[ICO]",
    },
    {
        "id": "smart_widgets",
        "label": "Smart Widgets",
        "folder": "component_sets/Smart Widgets",
        "purpose": "Interactive Bento widgets and floor actions attached to the project.",
        "icon": "[WID]",
    },
    {
        "id": "simulations",
        "label": "Simulations",
        "folder": "component_sets/Simulations",
        "purpose": "Construct maps, GMAT runs, ephemerides, zoning outputs, and scenario artifacts.",
        "icon": "[SIM]",
    },
    {
        "id": "z_direct_staging",
        "label": "Z Direct Staging",
        "folder": "component_sets/Z Direct Staging",
        "purpose": "Queued handoffs, review packets, approvals, and floor receipts.",
        "icon": "[Z]",
    },
]

DEFAULT_SMART_WIDGETS = project_wall_smart_widget_descriptors()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._ -]+", "", str(value or "")).strip()
    text = re.sub(r"\s+", " ", text)
    return text or "Untitled"


def tile_id_fragment(value: str) -> str:
    safe = slugify(value).lower().replace(" ", "_")
    safe = re.sub(r"[^a-z0-9._-]+", "_", safe)
    return safe.strip("._-") or "untitled"


def unique_destination_path(path: Path) -> Path:
    path = Path(path)
    if not path.exists():
        return path
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem} ({index}){path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def project_relative_path(project_root: Path, path: Path) -> str:
    project_root = Path(project_root).resolve()
    path = Path(path).resolve()
    try:
        return str(path.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        return str(path)


def normalize_wall_path(value: Any) -> str:
    return str(value or "").replace("\\", "/").strip("/")


def tile_belongs_to_folder(tile: Mapping[str, Any], folder: str) -> bool:
    """Return whether a tile should appear inside a component-set/folder view."""
    wanted = normalize_wall_path(folder)
    if not wanted:
        return True
    tile_folder = normalize_wall_path(tile.get("folder"))
    tile_target = normalize_wall_path(tile.get("target"))
    if tile_folder == wanted or tile_target == wanted:
        return True
    return tile_folder.startswith(wanted + "/") or tile_target.startswith(wanted + "/")


def tile_path_segments(project_root: Path, tile: Mapping[str, Any]) -> List[Dict[str, str]]:
    """
    Return breadcrumb-style segments for a tile within the project wall.

    The result is model data only; callers can render it as breadcrumb chips,
    path segments, or nested drilldown controls.
    """
    project_root = Path(project_root).resolve()
    if str(tile.get("kind") or "").lower() == "smart_widget":
        folder = normalize_wall_path(tile.get("folder") or "component_sets/Smart Widgets")
        parts = [part for part in folder.split("/") if part]
        segments = [{"label": "project", "path": ""}]
        running: list[str] = []
        for part in parts:
            running.append(part)
            segments.append({"label": part, "path": "/".join(running)})
        return segments

    path = resolve_tile_target(project_root, tile)
    if path is None:
        folder = normalize_wall_path(tile.get("folder"))
        if not folder:
            return []
        parts = [part for part in folder.split("/") if part]
        segments = [{"label": "project", "path": ""}]
        running: list[str] = []
        for part in parts:
            running.append(part)
            segments.append({"label": part, "path": "/".join(running)})
        return segments

    try:
        rel = Path(path).resolve().relative_to(project_root)
    except Exception:
        rel = Path(project_relative_path(project_root, path))

    segments = [{"label": "project", "path": ""}]
    running: list[str] = []
    for part in rel.parts:
        running.append(part)
        segments.append({"label": part, "path": "/".join(running)})
    return segments


def resolve_child_folder_target(project_root: Path, tile: Mapping[str, Any], child_name: str = "") -> Path | None:
    """
    Resolve a child folder target inside the project root.

    This intentionally returns a Path only. It never opens the OS folder.
    """
    project_root = Path(project_root).resolve()
    base = resolve_tile_target(project_root, tile)
    if base is None:
        return None
    base = Path(base).resolve()
    try:
        base.relative_to(project_root)
    except Exception:
        return None
    if child_name:
        candidate = (base / str(child_name)).resolve()
    else:
        candidate = base
    try:
        candidate.relative_to(project_root)
    except Exception:
        return None
    return candidate


def tile_size_hint(tile: Mapping[str, Any], preview_mode: str | None = None) -> str:
    kind = str(tile.get("kind") or "").lower()
    mode = str(preview_mode or tile.get("preview_mode") or "").lower()
    if kind == "folder":
        return "wide"
    if kind == "smart_widget":
        return "medium"
    if mode in {"image", "pdf", "map", "simulation", "spreadsheet", "dataset"}:
        return "large"
    if mode in {"table", "text", "json"}:
        return "medium"
    if kind == "static_icon":
        return "small"
    return "medium"


def table_editing_contract(project_root: Path, tile: Mapping[str, Any], preview: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """
    Return a declarative editing contract for table-like artifacts.

    This is metadata only. The UI can use it to render editable grids or route
    the file to Oracle/Morpheus-style proofing before saving.
    """
    preview = dict(preview or {})
    path = resolve_tile_target(project_root, tile)
    suffix = path.suffix.lower() if path else Path(str(tile.get("target") or "")).suffix.lower()
    table_data = preview.get("table") if isinstance(preview.get("table"), dict) else None
    columns = [str(col or "").strip() for col in (table_data or {}).get("columns") or []]
    if not columns:
        columns = [str(col or "").strip() for col in (tile.get("columns") or []) if str(col or "").strip()]
    editable_cells = []
    for index, column in enumerate(columns):
        editable_cells.append(
            {
                "column": column,
                "column_index": index,
                "editable": True,
                "validation": "non_empty" if column else "any",
            }
        )
    return {
        "kind": "table_editing_contract",
        "artifact_kind": str(tile.get("kind") or "unknown"),
        "suffix": suffix,
        "columns": columns,
        "editable_cells": editable_cells,
        "validation_notes": [
            "Validate CSV/TSV column count before save.",
            "Preserve Oracle provenance and Morpheus proof tags where present.",
            "Route non-table or binary outputs to Open External instead of inline save.",
        ],
        "save_target_policy": {
            "mode": "project_relative",
            "allowed": suffix in TABLE_SUFFIXES or suffix in TEXT_EDITABLE_SUFFIXES,
            "target": project_relative_path(project_root, path) if path else "",
            "fallback": "Open External",
        },
        "route": "table_editor" if suffix in TABLE_SUFFIXES else "metadata",
    }


def provenance_proof_tags(tile: Mapping[str, Any], preview: Mapping[str, Any] | None = None) -> List[Dict[str, str]]:
    """Build compact tags for Oracle provenance and Morpheus proofing state."""
    preview = dict(preview or {})
    tags: List[Dict[str, str]] = []
    provenance = str(tile.get("provenance") or preview.get("provenance") or tile.get("source_floor") or "").strip()
    proof_state = str(tile.get("proof_state") or preview.get("proof_state") or tile.get("proof_status") or "").strip()
    if provenance:
        tags.append({"kind": "provenance", "label": f"Oracle: {provenance}", "floor": "Oracle"})
    if proof_state:
        tags.append({"kind": "proof", "label": f"Morpheus: {proof_state}", "floor": "Morpheus"})
    if not tags and preview.get("source_floor"):
        tags.append({"kind": "provenance", "label": f"Oracle: {preview.get('source_floor')}", "floor": str(preview.get("source_floor"))})
    return tags


def smart_widget_descriptor(tile: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a model-only descriptor for a contract-backed smart widget tile."""
    templates = [dict(item) for item in (tile.get("widget_templates") or []) if isinstance(item, Mapping)]
    checks = [dict(item) for item in (tile.get("fidelity_checks") or []) if isinstance(item, Mapping)]
    floor = str(tile.get("floor") or "Trinity")
    floor_key = str(tile.get("floor_key") or tile_id_fragment(floor))
    widget_ids = [str(item.get("widget_id") or item.get("id")) for item in templates]
    failing = [item for item in checks if item.get("status") != "pass"]
    summary_parts = [
        str(tile.get("preview") or tile.get("purpose") or "Contract-backed smart-floor widget."),
        f"Templates: {', '.join(widget_ids) if widget_ids else 'none declared'}.",
    ]
    if checks:
        summary_parts.append(
            f"Fidelity: {len(checks) - len(failing)}/{len(checks)} checks pass."
        )
    return {
        "kind": "smart_widget_descriptor",
        "id": str(tile.get("id") or f"widget.floor.{floor_key}"),
        "label": str(tile.get("label") or floor),
        "floor": floor,
        "floor_key": floor_key,
        "z_level": tile.get("z_level"),
        "mode": str(tile.get("mode") or "floor_contract"),
        "target": str(tile.get("opens") or tile.get("target") or ""),
        "source_contract": str(tile.get("source_contract") or ""),
        "manifest_dir": str(tile.get("manifest_dir") or ""),
        "contract_widgets": list(tile.get("contract_widgets") or widget_ids),
        "widget_templates": templates,
        "fidelity_checks": checks,
        "summary": " ".join(part for part in summary_parts if part),
        "export": dict(tile.get("export") or {"supported": True, "formats": ["json", "project_wall_tile"]}),
        "actions": [
            {"id": "open_floor_widget", "label": f"Open {floor}", "reason": "Open the owning smart-floor route."},
            {"id": "inspect_widget_contract", "label": "Inspect Contract", "reason": "Show widget templates and fidelity checks."},
            {"id": "export_widget_contract", "label": "Export Contract", "reason": "Export descriptor JSON for Bento/project wall use."},
        ],
    }


def action_schema_for_tile_kind(tile: Mapping[str, Any], action_groups: Mapping[str, List[Mapping[str, Any]]] | None = None) -> Dict[str, Any]:
    """Return the canonical action schema for a tile kind."""
    kind = str(tile.get("kind") or "unknown").lower()
    groups = dict(action_groups or {})
    schema_groups: Dict[str, List[Dict[str, Any]]] = {}
    for group_name in ("inspect", "open", "handoff", "copy"):
        actions = [dict(action) for action in groups.get(group_name, []) if isinstance(action, Mapping)]
        schema_groups[group_name] = actions if actions else [{"id": "unavailable", "label": "Unavailable", "reason": f"{group_name} actions are not available for {kind}."}]
    for group_name, actions in groups.items():
        if group_name in schema_groups:
            continue
        schema_groups[group_name] = [dict(action) for action in actions if isinstance(action, Mapping)]
    return {
        "tile_kind": kind,
        "groups": schema_groups,
        "required_groups": ["inspect", "open", "handoff", "copy"],
        "has_unavailable": any(any(action.get("id") == "unavailable" for action in actions) for actions in schema_groups.values()),
    }


def preview_drawer_descriptor(project_root: Path, tile: Mapping[str, Any], preview: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Return a reusable drawer contract for project artifacts."""
    preview = dict(preview or {})
    renderer = dict(preview.get("renderer_descriptor") or preview_renderer_descriptor(project_root, tile))
    action_groups = dict(preview.get("action_groups") or artifact_action_groups(project_root, tile))
    tags = provenance_proof_tags(tile, preview)
    chips = [{"kind": "mode", "label": str(preview.get("preview_mode") or renderer.get("preview_mode") or "metadata")}]
    if preview.get("tile_size_hint") or renderer.get("display_hint"):
        chips.append({"kind": "density", "label": str(preview.get("tile_size_hint") or renderer.get("display_hint"))})
    for tag in tags:
        chips.append({"kind": tag["kind"], "label": tag["label"]})
    return {
        "title": str(preview.get("title") or tile.get("label") or tile.get("id") or "Artifact Drawer"),
        "mode": str(preview.get("preview_mode") or renderer.get("preview_mode") or "metadata"),
        "renderer": renderer,
        "actions": action_schema_for_tile_kind(tile, action_groups),
        "metadata_chips": chips,
        "fallback": {
            "route": "open_external" if renderer.get("route") != "metadata" else "metadata",
            "title": str(preview.get("title") or tile.get("label") or "Artifact"),
            "reason": "Use native preview or OS viewer when the wall cannot render this artifact inline.",
        },
    }


def search_project_wall_items(project_root: Path, state: Mapping[str, Any], query: str) -> Dict[str, Any]:
    """
    Search across the project wall model and return filtered tiles/component sets.

    The search spans folders, files, widgets, labels, targets, floors, preview text,
    and path segments so the UI can keep a single searchable surface.
    """
    project_root = Path(project_root)
    normalized = str(query or "").strip().lower()
    tiles = [tile for tile in state.get("tiles", []) if isinstance(tile, Mapping)]
    if not normalized:
        return {
            "query": "",
            "count": len(tiles),
            "tiles": tiles,
            "component_sets": list(state.get("component_sets", [])),
        }

    matched_tiles = []
    for tile in tiles:
        preview = read_artifact_preview(project_root, tile)
        haystack = " ".join(
            str(part)
            for part in [
                tile.get("id"),
                tile.get("kind"),
                tile.get("label"),
                tile.get("folder"),
                tile.get("target"),
                tile.get("floor"),
                tile.get("preview"),
                preview.get("content"),
                preview.get("title"),
                preview.get("relative_path"),
                " ".join(segment.get("label", "") for segment in preview.get("path_segments", []) if isinstance(segment, Mapping)),
            ]
            if part
        ).lower()
        if normalized in haystack:
            matched_tiles.append(tile)

    matched_component_sets = []
    for component in state.get("component_sets", []) or []:
        if not isinstance(component, Mapping):
            continue
        haystack = " ".join(
            str(part)
            for part in [
                component.get("label"),
                component.get("purpose"),
                component.get("folder"),
                component.get("path"),
            ]
            if part
        ).lower()
        if normalized in haystack:
            matched_component_sets.append(component)

    return {
        "query": query,
        "count": len(matched_tiles),
        "tiles": matched_tiles,
        "component_sets": matched_component_sets,
    }


def resolve_tile_target(project_root: Path, tile: Mapping[str, Any]) -> Path | None:
    target = tile.get("target") or tile.get("folder")
    if not target:
        return None
    path = Path(str(target))
    if not path.is_absolute():
        path = Path(project_root) / path
    return path


def _read_text_lossy(path: Path, max_chars: int) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[preview truncated]"
    return text


def _table_preview(path: Path, delimiter: str) -> Dict[str, Any]:
    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        for index, row in enumerate(reader):
            rows.append(row)
            if index >= 15:
                break
    return {
        "columns": rows[0] if rows else [],
        "rows": rows[1:] if len(rows) > 1 else [],
        "row_preview_count": max(len(rows) - 1, 0),
    }


def preview_mode_for_suffix(suffix: str) -> str:
    suffix = str(suffix or "").lower()
    if suffix in TABLE_SUFFIXES:
        return "table"
    if suffix == ".json":
        return "json"
    if suffix in MAP_SUFFIXES:
        return "map"
    if suffix in SIMULATION_SUFFIXES:
        return "simulation"
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in PDF_SUFFIXES:
        return "pdf"
    if suffix in SPREADSHEET_SUFFIXES:
        return "spreadsheet"
    if suffix in DATASET_SUFFIXES:
        return "dataset"
    if suffix in TEXT_EDITABLE_SUFFIXES:
        return "text"
    if suffix in BINARY_PREVIEW_SUFFIXES:
        return "binary"
    return "metadata"


def preview_subtype_for_suffix(suffix: str) -> str:
    suffix = str(suffix or "").lower()
    if suffix == ".gmat":
        return "gmat"
    if suffix in {".eph", ".bsp", ".spk", ".oem"}:
        return "ephemeris"
    return preview_mode_for_suffix(suffix)


def preview_renderer_descriptor(project_root: Path, tile: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Return a declarative renderer contract for an artifact tile.

    The UI consumes this as a model-level hint and should not need to infer
    the preview route from the raw file extension.
    """
    path = resolve_tile_target(project_root, tile)
    suffix = path.suffix.lower() if path else Path(str(tile.get("target") or "")).suffix.lower()
    mode = preview_mode_for_suffix(suffix)
    subtype = preview_subtype_for_suffix(suffix)
    label = str(tile.get("label") or tile.get("id") or "Artifact")
    kind = str(tile.get("kind") or "unknown")

    if kind == "smart_widget":
        widget = smart_widget_descriptor(tile)
        return {
            "renderer_id": f"smart_widget.{widget['floor_key']}",
            "artifact_kind": kind,
            "artifact_subtype": widget["mode"],
            "preview_mode": "smart_widget",
            "label": label,
            "title": label,
            "route": "smart_floor_widget",
            "display_hint": tile_size_hint(tile, "metadata"),
            "owner_floor": widget["floor"],
            "proof_floor": "Morpheus",
            "source_floor": "Oracle",
            "metadata_fields": [
                "floor",
                "floor_key",
                "z_level",
                "mode",
                "target",
                "contract_widgets",
                "fidelity_checks",
            ],
            "actions": widget["actions"],
            "export": widget["export"],
            "rerun": {
                "supported": widget["floor"] == "TheConstruct",
                "owner_floor": widget["floor"],
                "formats": ["gmat", "eph"] if widget["floor"] == "TheConstruct" else [],
            },
        }

    descriptor: Dict[str, Any] = {
        "renderer_id": f"{mode}.{subtype}" if subtype != mode else mode,
        "artifact_kind": kind,
        "artifact_subtype": subtype,
        "preview_mode": mode,
        "label": label,
        "title": label,
        "route": "metadata",
        "display_hint": tile_size_hint(tile, mode),
        "owner_floor": "Trinity",
        "proof_floor": "Morpheus",
        "source_floor": "Oracle",
        "metadata_fields": ["path", "relative_path", "status", "suffix", "size", "preview_mode", "tile_size_hint"],
        "actions": [],
        "export": {"supported": False, "formats": []},
        "rerun": {"supported": False, "owner_floor": "", "formats": []},
    }

    if mode == "pdf":
        descriptor.update(
            {
                "route": "external_viewer",
                "display_hint": "near_fullscreen",
                "source_floor": "Oracle",
                "proof_floor": "Morpheus",
                "actions": [
                    {"id": "preview", "label": "Preview"},
                    {"id": "open_external", "label": "Open External"},
                    {"id": "extract_text", "label": "Extract Text"},
                ],
                "export": {"supported": True, "formats": ["text", "notes"]},
            }
        )
    elif mode == "image":
        descriptor.update(
            {
                "route": "inline_image_preview",
                "display_hint": "near_fullscreen",
                "actions": [
                    {"id": "preview", "label": "Preview"},
                    {"id": "open_external", "label": "Open External"},
                ],
                "export": {"supported": True, "formats": ["png", "jpg"]},
            }
        )
    elif mode == "map":
        descriptor.update(
            {
                "route": "construct_map_preview",
                "display_hint": "large",
                "owner_floor": "TheConstruct",
                "actions": [
                    {"id": "preview", "label": "Preview"},
                    {"id": "open_external", "label": "Open External"},
                    {"id": "export_geojson", "label": "Export GeoJSON"},
                    {"id": "send_construct", "label": "Send to Construct"},
                ],
                "export": {"supported": True, "formats": ["geojson", "kml", "czml"]},
            }
        )
    elif mode == "spreadsheet":
        descriptor.update(
            {
                "route": "table_viewer",
                "display_hint": "large",
                "owner_floor": "Oracle",
                "actions": [
                    {"id": "preview", "label": "Preview"},
                    {"id": "open_external", "label": "Open External"},
                    {"id": "edit_rows", "label": "Edit Rows"},
                    {"id": "save_as_datatable", "label": "Save as Datatable"},
                ],
                "export": {"supported": True, "formats": ["csv", "tsv"]},
            }
        )
    elif mode == "dataset":
        descriptor.update(
            {
                "route": "oracle_dataset_preview",
                "display_hint": "large",
                "owner_floor": "Oracle",
                "proof_floor": "Morpheus",
                "actions": [
                    {"id": "preview", "label": "Preview"},
                    {"id": "open_external", "label": "Open External"},
                    {"id": "register_knowns", "label": "Register Knowns"},
                    {"id": "proof_dataset", "label": "Proof Dataset"},
                ],
                "export": {"supported": True, "formats": ["parquet", "sqlite", "db"]},
            }
        )
    elif mode == "simulation":
        descriptor.update(
            {
                "route": "construct_simulation_preview",
                "display_hint": "large",
                "owner_floor": "TheConstruct",
                "actions": [
                    {"id": "preview", "label": "Preview"},
                    {"id": "open_external", "label": "Open External"},
                    {"id": "rerun", "label": "Rerun"},
                    {"id": "export", "label": "Export"},
                ],
                "export": {"supported": True, "formats": ["json", "jsonl", "eph", "gmat"]},
                "rerun": {"supported": True, "owner_floor": "TheConstruct", "formats": ["gmat", "eph"]},
            }
        )
        if subtype == "ephemeris":
            descriptor["route"] = "construct_ephemeris_preview"
            descriptor["actions"] = [
                {"id": "preview", "label": "Preview"},
                {"id": "open_external", "label": "Open External"},
                {"id": "rerun", "label": "Rerun"},
                {"id": "export_ephemeris", "label": "Export Ephemeris"},
            ]
            descriptor["export"] = {"supported": True, "formats": ["eph", "json", "jsonl"]}
    else:
        descriptor["actions"] = [{"id": "preview", "label": "Preview"}]

    return descriptor


def artifact_action_groups(project_root: Path, tile: Mapping[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """
    Return grouped context actions for a project wall tile.

    The UI consumes this so right-click menus do not drift away from the model.
    Handlers still live in the host UI; this function owns action availability.
    """
    path = resolve_tile_target(project_root, tile)
    suffix = path.suffix.lower() if path else Path(str(tile.get("target") or "")).suffix.lower()
    mode = preview_mode_for_suffix(suffix)
    kind = str(tile.get("kind") or "")
    is_smart_widget = kind == "smart_widget"
    has_target = bool(path or tile.get("target") or tile.get("folder")) and not is_smart_widget
    exists = bool(path and path.exists())
    editable = bool(path and path.exists() and path.is_file() and suffix in TEXT_EDITABLE_SUFFIXES and path.stat().st_size <= 2_000_000)

    groups: Dict[str, List[Dict[str, str]]] = {
        "inspect": [{"id": "preview", "label": "Preview", "reason": "Show inspector summary."}],
        "handoff": [{"id": "queue_z_direct", "label": "Queue to Z Direct", "reason": "Send artifact or tile to another smart floor."}],
        "copy": [{"id": "copy_tile_id", "label": "Copy Tile ID", "reason": "Reference this tile in notes or tasks."}],
    }
    if kind == "folder":
        groups.setdefault("drilldown", []).append(
            {"id": "open_folder", "label": "Open Folder", "reason": "Drill into the folder in-wall before using OS fallback."}
        )
    if kind in {"file", "static_icon"} and not str(tile.get("target") or "").strip():
        groups.setdefault("attach", []).append(
            {"id": "attach_file", "label": "Attach File", "reason": "Attach or assign a file target to this tile."}
        )
    if is_smart_widget:
        widget = smart_widget_descriptor(tile)
        groups.setdefault("open", []).append(
            {"id": "open_floor_widget", "label": f"Open {widget['floor']}", "reason": "Run owning smart-floor action."}
        )
        groups["inspect"].append(
            {"id": "inspect_widget_contract", "label": "Inspect Contract", "reason": "Show widget templates and fidelity checks."}
        )
        groups.setdefault("export", []).append(
            {"id": "export_widget_contract", "label": "Export Contract", "reason": "Export this widget descriptor as JSON."}
        )
        groups["copy"].append(
            {"id": "copy_widget_contract", "label": "Copy Widget Contract", "reason": "Reference the smart-floor contract."}
        )
    if has_target:
        groups.setdefault("open", []).append({"id": "open_external", "label": "Open External", "reason": "Use native OS viewer when needed."})
        groups["copy"].append({"id": "copy_target", "label": "Copy Target", "reason": "Reference project-relative target."})
        if not exists and kind in {"file", "static_icon"}:
            groups.setdefault("attach", []).append(
                {"id": "replace_target", "label": "Replace Target", "reason": "Relink the tile to a different existing file target."}
            )
    if editable:
        groups["inspect"].append({"id": "edit", "label": "Preview / Edit", "reason": "Edit supported text/table/code artifacts inside the wall."})
    elif mode in {"image", "pdf", "map", "simulation", "spreadsheet", "dataset"}:
        groups["inspect"].append({"id": f"preview_{mode}", "label": f"{mode.title()} Preview", "reason": "Open near-fullscreen preview surface with native fallback."})
    return groups


def read_artifact_preview(project_root: Path, tile: Mapping[str, Any], *, max_chars: int = 20000) -> Dict[str, Any]:
    path = resolve_tile_target(project_root, tile)
    label = str(tile.get("label") or tile.get("id") or "Artifact")
    kind = str(tile.get("kind") or "unknown")
    if kind == "smart_widget":
        widget = smart_widget_descriptor(tile)
        preview: Dict[str, Any] = {
            "title": label,
            "kind": kind,
            "status": "ok",
            "preview_mode": "smart_widget",
            "tile_size_hint": tile_size_hint(tile, "metadata"),
            "path_segments": tile_path_segments(project_root, tile),
            "editable": False,
            "content": widget["summary"],
            "smart_widget": widget,
            "action_groups": artifact_action_groups(project_root, tile),
            "renderer_descriptor": preview_renderer_descriptor(project_root, tile),
            "provenance_tags": provenance_proof_tags(tile),
        }
        preview["drawer_descriptor"] = preview_drawer_descriptor(project_root, tile, preview)
        return preview

    if path is None:
        return {
            "title": label,
            "kind": kind,
            "status": "no_target",
            "preview_mode": "detached_tile",
            "tile_size_hint": tile_size_hint(tile, "metadata"),
            "path_segments": tile_path_segments(project_root, tile),
            "editable": False,
            "action_groups": artifact_action_groups(project_root, tile),
            "content": str(tile.get("preview") or "No target attached."),
        }

    path = Path(path)
    if not path.exists():
        return {
            "title": label,
            "kind": kind,
            "path": str(path),
            "status": "missing",
            "preview_mode": "missing",
            "tile_size_hint": tile_size_hint(tile, "metadata"),
            "path_segments": tile_path_segments(project_root, tile),
            "editable": False,
            "action_groups": artifact_action_groups(project_root, tile),
            "content": "Target does not exist.",
        }

    if path.is_dir():
        children = []
        for child in sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))[:80]:
            children.append(
                {
                    "name": child.name,
                    "kind": "folder" if child.is_dir() else "file",
                    "size": child.stat().st_size if child.is_file() else None,
                }
            )
        return {
            "title": label,
            "kind": "folder",
            "path": str(path),
            "status": "ok",
            "preview_mode": "folder",
            "tile_size_hint": tile_size_hint(tile, "folder"),
            "path_segments": tile_path_segments(project_root, tile),
            "editable": False,
            "children": children,
            "action_groups": artifact_action_groups(project_root, tile),
            "content": "\n".join(f"{item['kind']}: {item['name']}" for item in children) or "Folder is empty.",
        }

    suffix = path.suffix.lower()
    preview_mode = preview_mode_for_suffix(suffix)
    size = path.stat().st_size
    preview: Dict[str, Any] = {
        "title": label,
        "kind": kind,
        "path": str(path),
        "relative_path": project_relative_path(project_root, path),
        "status": "ok",
        "suffix": suffix,
        "preview_mode": preview_mode,
        "tile_size_hint": tile_size_hint(tile, preview_mode),
        "path_segments": tile_path_segments(project_root, tile),
        "size": size,
        "editable": suffix in TEXT_EDITABLE_SUFFIXES and size <= 2_000_000,
        "action_groups": artifact_action_groups(project_root, tile),
        "renderer_descriptor": preview_renderer_descriptor(project_root, tile),
        "provenance_tags": provenance_proof_tags(tile),
        "drawer_descriptor": preview_drawer_descriptor(project_root, tile),
    }
    if suffix in MAP_SUFFIXES:
        preview["editable"] = False
        preview["content"] = "Map artifact. Use Construct map/simulation tooling or Open External for full rendering."
        if suffix == ".geojson":
            try:
                payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
                features = payload.get("features") if isinstance(payload, dict) else None
                if isinstance(features, list):
                    preview["feature_count"] = len(features)
                    preview["content"] = f"GeoJSON map artifact with {len(features)} feature(s)."
            except Exception:
                pass
        return preview
    if suffix in TABLE_SUFFIXES:
        preview["table"] = _table_preview(path, "\t" if suffix == ".tsv" else ",")
        preview["content"] = _read_text_lossy(path, max_chars)
        preview["table_editing_contract"] = table_editing_contract(project_root, tile, preview)
        return preview
    if suffix == ".json":
        try:
            preview["content"] = json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2)
        except Exception:
            preview["content"] = _read_text_lossy(path, max_chars)
        return preview
    if suffix in TEXT_EDITABLE_SUFFIXES:
        preview["content"] = _read_text_lossy(path, max_chars)
        if suffix in SIMULATION_SUFFIXES:
            preview["content"] = (
                "Simulation/ephemeris artifact. Text is editable here; use Construct or GMAT tooling for execution.\n\n"
                + str(preview["content"])
            )
        if suffix in SIMULATION_SUFFIXES:
            preview["table_editing_contract"] = {
                "kind": "table_editing_contract",
                "artifact_kind": kind,
                "suffix": suffix,
                "columns": [],
                "editable_cells": [],
                "validation_notes": [
                    "Simulation and ephemeris files are line-oriented and should be edited as text, not row grids.",
                    "Preserve rerun metadata in the renderer descriptor instead of mutating the source format.",
                ],
                "save_target_policy": {
                    "mode": "project_relative",
                    "allowed": True,
                    "target": preview.get("relative_path", ""),
                    "fallback": "Open External",
                },
                "route": "construct_simulation_editor",
            }
        return preview
    if suffix in BINARY_PREVIEW_SUFFIXES:
        preview["editable"] = False
        preview_labels = {
            "image": "Image artifact. Use near-fullscreen preview or Open External for pixel-level inspection.",
            "pdf": "PDF artifact. Use Open External for full rendering; Oracle/Morpheus should own extraction and proofing.",
            "spreadsheet": "Spreadsheet artifact. Use Open External or import/export to Tables for editable rows.",
            "dataset": "Dataset artifact. Use Oracle/Morpheus datatable ingestion before editing.",
            "simulation": "Simulation artifact. Use Construct/GMAT tooling for execution or ephemeris review.",
        }
        preview["content"] = preview_labels.get(preview_mode, f"{suffix or 'binary'} artifact. Use Open External for full rendering.")
        return preview

    preview["editable"] = False
    preview["content"] = "Preview is limited to metadata for this file type."
    return preview


def write_artifact_text(project_root: Path, tile: Mapping[str, Any], content: str) -> Dict[str, Any]:
    path = resolve_tile_target(project_root, tile)
    if path is None:
        raise ValueError("Tile has no writable target.")
    project_root = Path(project_root).resolve()
    path = Path(path).resolve()
    try:
        path.relative_to(project_root)
    except ValueError as exc:
        raise ValueError("Refusing to write outside the project wall root.") from exc
    if path.suffix.lower() not in TEXT_EDITABLE_SUFFIXES:
        raise ValueError(f"{path.suffix or 'This file type'} is not editable inside the project wall.")
    path.write_text(content, encoding="utf-8")
    return {
        "updated_at": utc_now_iso(),
        "path": str(path),
        "relative_path": project_relative_path(project_root, path),
        "size": path.stat().st_size,
    }


def create_z_direct_handoff(
    project_root: Path,
    tile: Mapping[str, Any],
    *,
    target_floor: str,
    action: str,
    note: str = "",
) -> Dict[str, Any]:
    project_root = Path(project_root)
    staging = project_root / "component_sets" / "Z Direct Staging"
    staging.mkdir(parents=True, exist_ok=True)
    tile_id = str(tile.get("id") or tile.get("label") or "artifact")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = tile_id_fragment(f"{timestamp}_{target_floor}_{tile_id}")
    destination = unique_destination_path(staging / f"{safe_name}.json")
    target_path = resolve_tile_target(project_root, tile)
    payload = {
        "handoff_id": destination.stem,
        "created_at": utc_now_iso(),
        "status": "queued",
        "source": "project_component_wall",
        "source_floor": "Trinity",
        "target_floor": slugify(target_floor),
        "requested_action": slugify(action),
        "note": note,
        "tile": {
            "id": tile.get("id"),
            "kind": tile.get("kind"),
            "label": tile.get("label"),
            "folder": tile.get("folder"),
            "target": tile.get("target"),
        },
        "artifact_path": str(target_path) if target_path else "",
        "project_relative_path": project_relative_path(project_root, target_path) if target_path else "",
        "receipt_policy": "target floor confirms received, updated, completed, deleted, or declassified state.",
    }
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {
        "payload": payload,
        "path": str(destination),
        "relative_path": project_relative_path(project_root, destination),
    }


def build_floor_action_catalog(app_root: Path) -> Dict[str, Any]:
    app_root = Path(app_root)
    z_axis = app_root / "Z Axis"
    floors: list[dict[str, Any]] = []
    if not z_axis.exists():
        return {"floor_count": 0, "action_count": 0, "floors": []}

    for manifest_path in sorted(z_axis.glob("*/_FLOOR_MANIFEST.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        floor_name = str(manifest.get("floor_name") or manifest_path.parent.name)
        floor_actions: list[dict[str, Any]] = []
        for component in manifest.get("components") or []:
            if not isinstance(component, dict) or component.get("enabled") is False:
                continue
            floor_actions.append(
                {
                    "kind": "component",
                    "id": component.get("id"),
                    "label": component.get("name") or component.get("id"),
                    "target": component.get("name") or component.get("id"),
                    "description": component.get("description") or "",
                    "priority": component.get("priority") or "",
                }
            )
        for service in manifest.get("services") or []:
            if not isinstance(service, dict):
                continue
            floor_actions.append(
                {
                    "kind": "service",
                    "id": service.get("name"),
                    "label": service.get("name"),
                    "target": service.get("name"),
                    "description": service.get("description") or "",
                    "priority": service.get("status") or "",
                }
            )
        for capability in manifest.get("capabilities") or []:
            floor_actions.append(
                {
                    "kind": "capability",
                    "id": str(capability),
                    "label": str(capability).replace("_", " ").title(),
                    "target": str(capability),
                    "description": f"{floor_name} capability from floor manifest.",
                    "priority": "",
                }
            )
        floors.append(
            {
                "floor": floor_name,
                "z_level": manifest.get("z_level"),
                "description": manifest.get("description") or "",
                "color": manifest.get("color") or "",
                "action_count": len(floor_actions),
                "actions": floor_actions,
            }
        )
    return {
        "floor_count": len(floors),
        "action_count": sum(int(floor.get("action_count", 0)) for floor in floors),
        "floors": floors,
    }


def unique_tile_id(payload: Mapping[str, Any], base_id: str) -> str:
    existing = {str(tile.get("id")) for tile in payload.get("tiles", []) if isinstance(tile, dict)}
    if base_id not in existing:
        return base_id
    index = 2
    while f"{base_id}.{index}" in existing:
        index += 1
    return f"{base_id}.{index}"


def project_value(project: Mapping[str, Any] | Any, key: str, default: Any = None) -> Any:
    if isinstance(project, Mapping):
        return project.get(key, default)
    try:
        return project[key]
    except Exception:
        return getattr(project, key, default)


def project_name(project: Mapping[str, Any] | Any) -> str:
    return slugify(str(project_value(project, "name", "Untitled Project")))


def resolve_project_root(
    app_root: Path,
    project: Mapping[str, Any] | Any,
    *,
    projects_root: Path | None = None,
) -> Path:
    app_root = Path(app_root)
    candidate = project_value(project, "path")
    if candidate:
        path = Path(str(candidate))
        if not path.is_absolute():
            path = app_root / path
        return path

    if projects_root is None:
        projects_root = app_root / "Z Axis" / "Z+1_Architect" / "projects"
    return Path(projects_root) / project_name(project)


def default_wall_payload(project: Mapping[str, Any] | Any, project_root: Path) -> Dict[str, Any]:
    name = project_name(project)
    tiles: List[Dict[str, Any]] = []

    for item in DEFAULT_COMPONENT_SETS:
        tiles.append(
            {
                "id": f"folder.{item['id']}",
                "kind": "folder",
                "label": item["label"],
                "icon": item["icon"],
                "folder": item["folder"],
                "interactive": True,
                "preview": item["purpose"],
            }
        )

    for widget in DEFAULT_SMART_WIDGETS:
        tiles.append(
            {
                "id": f"widget.{widget['id']}",
                "kind": "smart_widget",
                "label": widget["label"],
                "icon": "[RUN]",
                "folder": "component_sets/Smart Widgets",
                "floor": widget["floor"],
                "floor_key": widget.get("floor_key"),
                "z_level": widget.get("z_level"),
                "mode": widget.get("mode", "floor_contract"),
                "target": widget.get("target") or widget.get("opens"),
                "opens": widget.get("opens") or widget.get("target"),
                "interactive": True,
                "preview": widget.get("purpose", ""),
                "source_contract": widget.get("source_contract", ""),
                "manifest_dir": widget.get("manifest_dir", ""),
                "contract_widgets": list(widget.get("contract_widgets", [])),
                "widget_templates": list(widget.get("widget_templates", [])),
                "fidelity_checks": list(widget.get("fidelity_checks", [])),
                "export": dict(widget.get("export", {})),
            }
        )

    return {
        "version": "2026.04.project_wall",
        "generated_at": utc_now_iso(),
        "project_name": name,
        "project_root": str(project_root),
        "interaction_model": {
            "single_click": "preview tile or folder contents",
            "double_click": "open folder, file, widget, or full-screen editor",
            "right_click": "show grouped actions for artifact, project, and floor routing",
            "enter_space": "open selected tile",
            "arrow_keys": "move tile focus",
        },
        "component_sets": DEFAULT_COMPONENT_SETS,
        "tiles": tiles,
    }


def ensure_project_wall(project_root: Path, project: Mapping[str, Any] | Any, *, create: bool = False) -> Dict[str, Any]:
    project_root = Path(project_root)
    wall_path = project_root / WALL_FILENAME

    if create:
        project_root.mkdir(parents=True, exist_ok=True)
        for item in DEFAULT_COMPONENT_SETS:
            (project_root / item["folder"]).mkdir(parents=True, exist_ok=True)

    if wall_path.exists():
        try:
            payload = json.loads(wall_path.read_text(encoding="utf-8"))
        except Exception:
            payload = default_wall_payload(project, project_root)
    else:
        payload = default_wall_payload(project, project_root)

    payload["project_root"] = str(project_root)
    payload["wall_path"] = str(wall_path)

    existing_ids = {str(tile.get("id")) for tile in payload.get("tiles", []) if isinstance(tile, dict)}
    for tile in default_wall_payload(project, project_root)["tiles"]:
        if tile["id"] not in existing_ids:
            payload.setdefault("tiles", []).append(tile)

    if create:
        wall_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return payload


def add_folder_tile(project_root: Path, label: str, *, parent_folder: str = "component_sets") -> Dict[str, Any]:
    project_root = Path(project_root)
    wall_path = project_root / WALL_FILENAME
    payload = ensure_project_wall(project_root, {"name": project_root.name}, create=True)
    safe = slugify(label)
    parent = str(parent_folder or "component_sets").strip("/\\")
    rel = f"{parent}/{safe}".replace("\\", "/")
    (project_root / rel).mkdir(parents=True, exist_ok=True)
    tile = {
        "id": unique_tile_id(payload, f"folder.custom.{tile_id_fragment(parent)}.{tile_id_fragment(safe)}"),
        "kind": "folder",
        "label": safe,
        "icon": "[DIR]",
        "folder": rel,
        "interactive": True,
        "preview": "Custom project component folder.",
    }
    payload.setdefault("tiles", []).append(tile)
    payload["updated_at"] = utc_now_iso()
    wall_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return tile


def add_static_icon_tile(project_root: Path, label: str, *, target: str = "") -> Dict[str, Any]:
    project_root = Path(project_root)
    wall_path = project_root / WALL_FILENAME
    payload = ensure_project_wall(project_root, {"name": project_root.name}, create=True)
    safe = slugify(label)
    tile = {
        "id": unique_tile_id(payload, f"icon.{tile_id_fragment(safe)}"),
        "kind": "static_icon",
        "label": safe,
        "icon": "[PIN]",
        "folder": "component_sets/Static Icons",
        "target": target,
        "interactive": bool(target),
        "preview": "Static icon tile. Attach a target file or folder to make it openable.",
    }
    payload.setdefault("tiles", []).append(tile)
    payload["updated_at"] = utc_now_iso()
    wall_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return tile


def add_file_tile(project_root: Path, label: str, *, target: str, folder: str = "component_sets/Documents") -> Dict[str, Any]:
    project_root = Path(project_root)
    wall_path = project_root / WALL_FILENAME
    payload = ensure_project_wall(project_root, {"name": project_root.name}, create=True)
    safe = slugify(label)
    suffix = Path(str(target)).suffix.lower()
    icon = "[DOC]"
    if suffix in {".csv", ".tsv", ".xlsx", ".xls", ".parquet", ".json"}:
        icon = "[TAB]"
    elif suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        icon = "[IMG]"
    elif suffix in {".py", ".js", ".ts", ".tsx", ".sql", ".md"}:
        icon = "[COD]"
    elif suffix in {".gmat", ".bsp", ".eph"}:
        icon = "[SIM]"

    tile = {
        "id": unique_tile_id(payload, f"file.{tile_id_fragment(safe)}"),
        "kind": "file",
        "label": safe,
        "icon": icon,
        "folder": folder,
        "target": target,
        "interactive": True,
        "preview": "Project file tile. Single click previews metadata; double click opens the file.",
    }
    payload.setdefault("tiles", []).append(tile)
    payload["updated_at"] = utc_now_iso()
    wall_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return tile


def add_smart_widget_tile(
    project_root: Path,
    label: str,
    *,
    floor: str = "Neo",
    target: str = "Planner",
    purpose: str = "Custom project smart widget.",
) -> Dict[str, Any]:
    project_root = Path(project_root)
    wall_path = project_root / WALL_FILENAME
    payload = ensure_project_wall(project_root, {"name": project_root.name}, create=True)
    safe = slugify(label)
    tile = {
        "id": unique_tile_id(payload, f"widget.custom.{tile_id_fragment(floor)}.{tile_id_fragment(safe)}"),
        "kind": "smart_widget",
        "label": safe,
        "icon": "[RUN]",
        "folder": "component_sets/Smart Widgets",
        "floor": slugify(floor),
        "target": slugify(target),
        "interactive": True,
        "preview": purpose or "Custom project smart widget.",
    }
    payload.setdefault("tiles", []).append(tile)
    payload["updated_at"] = utc_now_iso()
    wall_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return tile


def build_wall_state(project_root: Path, project: Mapping[str, Any] | Any) -> Dict[str, Any]:
    payload = ensure_project_wall(project_root, project, create=False)
    project_root = Path(project_root)

    component_sets = []
    for item in payload.get("component_sets", []):
        if not isinstance(item, dict):
            continue
        folder = project_root / str(item.get("folder", ""))
        file_count = 0
        folder_count = 0
        if folder.exists():
            for child in folder.iterdir():
                if child.is_dir():
                    folder_count += 1
                elif child.is_file():
                    file_count += 1
        out = dict(item)
        out["path"] = str(folder)
        out["file_count"] = file_count
        out["folder_count"] = folder_count
        component_sets.append(out)

    return {
        "project_name": payload.get("project_name") or project_name(project),
        "project_root": str(project_root),
        "wall_path": payload.get("wall_path") or str(project_root / WALL_FILENAME),
        "component_sets": component_sets,
        "tiles": [tile for tile in payload.get("tiles", []) if isinstance(tile, dict)],
        "interaction_model": payload.get("interaction_model", {}),
    }


def summarize_wall_tiles(tiles: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for tile in tiles:
        kind = str(tile.get("kind") or "unknown")
        counts[kind] = counts.get(kind, 0) + 1
    return counts
