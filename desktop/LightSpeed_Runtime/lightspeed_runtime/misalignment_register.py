from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from lightspeed_runtime.storage_paths import trinity_root


MISALIGNMENT_ITEMS: List[Dict[str, str]] = [
    {
        "id": "UX-MIS-001",
        "area": "Project Wall",
        "miss": "Project component sets were present but the Bento grid behaved too much like one flat board.",
        "change": "Keep component-set and subfolder selection scoped inside the wall with visible breadcrumbs and tile filtering.",
        "owner_floor": "Architect",
        "priority": "high",
    },
    {
        "id": "UX-MIS-002",
        "area": "Project Wall",
        "miss": "Static icons and smart widgets had different interaction language.",
        "change": "Use one action model: single click preview, double click open/run, right click grouped actions.",
        "owner_floor": "Trinity",
        "priority": "high",
    },
    {
        "id": "UX-MIS-003",
        "area": "Preview",
        "miss": "Images, PDFs, maps, spreadsheets, datasets, and simulations were treated as generic binary files.",
        "change": "Expose preview modes and route native/full render work to the owning floor or OS viewer.",
        "owner_floor": "Trinity",
        "priority": "high",
    },
    {
        "id": "UX-MIS-004",
        "area": "Z Floors",
        "miss": "Some floor tabs duplicated purpose, portal, and feature pages.",
        "change": "Keep each floor as one surface with purpose, feature/action list, inspector, and explicit full runtime routing.",
        "owner_floor": "Trinity",
        "priority": "high",
    },
    {
        "id": "UX-MIS-005",
        "area": "Settings",
        "miss": "Startup, setup, theme, and page settings were still partially split by legacy entrypoint.",
        "change": "Route all supported edits through Smart Settings Hub focus sections.",
        "owner_floor": "Trinity",
        "priority": "high",
    },
    {
        "id": "UX-MIS-006",
        "area": "Backgrounds",
        "miss": "Editable backgrounds were defined in contracts but not exposed as an operator control.",
        "change": "Expose base mode, gradient/color, uploaded picture path, environment reference, and scope.",
        "owner_floor": "Trinity",
        "priority": "medium",
    },
    {
        "id": "UX-MIS-007",
        "area": "Holospace",
        "miss": "Holospace could be interpreted as a competing top-level mode/button.",
        "change": "Keep Workspace and Z Floor top-level; make Holospace a Construct-owned opt-in surface.",
        "owner_floor": "TheConstruct",
        "priority": "medium",
    },
    {
        "id": "UX-MIS-008",
        "area": "Morpheus",
        "miss": "Review/search could drift into raw mentions instead of proofed definitions.",
        "change": "Prioritize dictionary, knowns, provenance, confidence, and source comparison before generic mention output.",
        "owner_floor": "Morpheus",
        "priority": "high",
    },
    {
        "id": "UX-MIS-009",
        "area": "Oracle",
        "miss": "Original files and extracted components were not always visually separated.",
        "change": "Make Oracle the original-file holder and show extracted objects/tables/tasks as handoffs.",
        "owner_floor": "Oracle",
        "priority": "high",
    },
    {
        "id": "UX-MIS-010",
        "area": "Z Direct",
        "miss": "Handoff receipts could look like loose files rather than stateful work packets.",
        "change": "Show received, updated, completed, deleted, and declassified states in one receipt table.",
        "owner_floor": "Smith",
        "priority": "medium",
    },
    {
        "id": "UX-MIS-011",
        "area": "Neo",
        "miss": "Neo risked becoming another chat page instead of a front-facing operator.",
        "change": "Keep Neo as internal monologue, task proposer, proof requestor, and floor orchestrator.",
        "owner_floor": "Neo",
        "priority": "high",
    },
    {
        "id": "UX-MIS-012",
        "area": "Achilles",
        "miss": "Achilles/Cognigrex oversight was implied but not always obvious in handoff flows.",
        "change": "Expose Achilles as approval-gated operator layer across Neo, Smith, and Architect.",
        "owner_floor": "Neo",
        "priority": "medium",
    },
    {
        "id": "UX-MIS-013",
        "area": "Performance",
        "miss": "Heavy widgets and popups could be loaded at startup or in fragile windows.",
        "change": "Use compact summaries first, lazy-load heavy viewers, and prefer inline panels over popup stacks.",
        "owner_floor": "Merovingian",
        "priority": "high",
    },
    {
        "id": "UX-MIS-014",
        "area": "Progress",
        "miss": "Long actions lacked clear progress/cancel states.",
        "change": "Add progress overlays for ingestion, diagnostics, simulation export, publishing, and dependency approval.",
        "owner_floor": "Merovingian",
        "priority": "medium",
    },
    {
        "id": "UX-MIS-015",
        "area": "Dependencies",
        "miss": "Missing dependencies were treated as errors rather than queued approvals.",
        "change": "Create empty landing tables and queue Neo/Smith dependency approval with install command evidence.",
        "owner_floor": "Smith",
        "priority": "medium",
    },
    {
        "id": "UX-MIS-016",
        "area": "Dictionary",
        "miss": "IT shorthand and floor abbreviations were requested but not yet complete as a searchable category.",
        "change": "Add IT category definitions and floor shorthand aliases into Oracle/Morpheus dictionary surfaces.",
        "owner_floor": "Oracle",
        "priority": "medium",
    },
    {
        "id": "UX-MIS-017",
        "area": "Simulation",
        "miss": "GMAT and ephemeris outputs could be visible but not clearly replayable.",
        "change": "Attach simulation parameters, ephemerides, and rerun metadata to Construct artifacts.",
        "owner_floor": "TheConstruct",
        "priority": "high",
    },
    {
        "id": "UX-MIS-018",
        "area": "Zoning",
        "miss": "Heliocentric zoning was specified but still needs richer UI hooks and shortlist export in the floor.",
        "change": "Expose zone summary, clusters, target shortlist, and GMAT batch export as Construct widgets.",
        "owner_floor": "TheConstruct",
        "priority": "high",
    },
    {
        "id": "UX-MIS-019",
        "area": "Library",
        "miss": "Empirical/library content was condensed but still needs stronger proof-first browsing.",
        "change": "Show knowns, values, units, provenance, and confidence as primary columns, not raw file names.",
        "owner_floor": "Oracle",
        "priority": "medium",
    },
    {
        "id": "UX-MIS-020",
        "area": "Controls",
        "miss": "Right-click availability varied by surface.",
        "change": "Back all context menus with typed action groups so every tile/page offers expected actions.",
        "owner_floor": "Trinity",
        "priority": "medium",
    },
    {
        "id": "UX-MIS-021",
        "area": "Navigation",
        "miss": "Folder depth could still feel like external file browsing.",
        "change": "Add breadcrumbs and in-wall folder drilldown before falling back to OS folder open.",
        "owner_floor": "Architect",
        "priority": "medium",
    },
    {
        "id": "UX-MIS-022",
        "area": "Data Tables",
        "miss": "Tables could be previewed but not yet fully edited like spreadsheet components.",
        "change": "Add row/cell editing, validation, save-as-datatable, and Morpheus proof status.",
        "owner_floor": "Morpheus",
        "priority": "medium",
    },
    {
        "id": "UX-MIS-023",
        "area": "External Tools",
        "miss": "API/tool toggles exist but are not yet uniformly shown in compact smart menus.",
        "change": "Expose external tools toggle and API status through Settings Hub and each relevant floor action list.",
        "owner_floor": "Trinity",
        "priority": "medium",
    },
    {
        "id": "UX-MIS-024",
        "area": "Publishing",
        "miss": "D-root publish destination should be snapshot-only and not a live work root.",
        "change": "Keep C-root as build/run source and add explicit overwrite snapshot packaging to D-root only at publish.",
        "owner_floor": "Architect",
        "priority": "high",
    },
    {
        "id": "UX-MIS-025",
        "area": "Blank Release",
        "miss": "Generated user/project/company data can reappear after proof runs.",
        "change": "Add a release-clean command that clears runtime rows, project workspaces, and caches after final validation.",
        "owner_floor": "Merovingian",
        "priority": "high",
    },
]


def build_misalignment_register(root: Path) -> Dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "owner_floor": "Trinity",
        "purpose": "Remaining missed or misinterpreted implementation points causing UI/system alignment drift.",
        "item_count": len(MISALIGNMENT_ITEMS),
        "items": MISALIGNMENT_ITEMS,
    }


def default_misalignment_register_path(root: Path) -> Path:
    return trinity_root(root) / "ui" / "misalignment_register.json"


def write_misalignment_register(root: Path, output_path: Path | None = None) -> Dict[str, Any]:
    destination = output_path or default_misalignment_register_path(root)
    payload = build_misalignment_register(root)
    payload["path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def write_misalignment_markdown(root: Path, output_path: Path | None = None) -> Path:
    destination = output_path or Path(root) / "dataindex" / "14_MISALIGNMENT_REGISTER.md"
    payload = build_misalignment_register(root)
    lines = [
        "# Misalignment Register",
        "",
        f"Generated: {payload['generated_at']}",
        "Owner: Trinity",
        "Status: active implementation backlog",
        "",
        "These are the next 25 implementation changes that appear missed, partially implemented, or misinterpreted across the current build.",
        "",
    ]
    for item in payload["items"]:
        lines.extend(
            [
                f"## {item['id']} - {item['area']}",
                "",
                f"- Miss: {item['miss']}",
                f"- Change: {item['change']}",
                f"- Owner floor: {item['owner_floor']}",
                f"- Priority: {item['priority']}",
                "",
            ]
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    return destination
