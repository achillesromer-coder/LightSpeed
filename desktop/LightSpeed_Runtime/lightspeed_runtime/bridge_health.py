from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lightspeed_runtime.storage_paths import trinity_root
from lightspeed_runtime.web_integration import build_romer_web_integration, read_romer_web_integration


PUBLIC_REQUIRED_ROUTES = {
    "/",
    "/operations",
    "/operations/w1",
    "/operations/w2",
    "/operations/w3",
    "/operations/w4",
    "/operations/w5",
    "/operations/w6",
    "/gmat",
    "/library",
    "/docs",
    "/dash",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_bridge_health_path(root: Path) -> Path:
    return trinity_root(root) / "ui" / "bridge_health.json"


def _status_counts(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("observed_status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _integration_payload(root: Path) -> dict:
    return read_romer_web_integration(root) or build_romer_web_integration(root)


def build_bridge_health(root: Path) -> dict:
    integration = _integration_payload(root)
    routes = list(integration.get("website_routes", []))
    route_map = {str(route.get("route") or ""): route for route in routes}
    public_routes = [route_map[path] for path in sorted(PUBLIC_REQUIRED_ROUTES) if path in route_map]
    data_routes = [route for route in routes if str(route.get("route") or "").startswith(("/data/", "/w"))]
    missing_public = sorted(PUBLIC_REQUIRED_ROUTES - set(route_map))
    public_failures = [
        route
        for route in public_routes
        if str(route.get("observed_status") or "") != "public_200"
    ]

    drive_sources = list(integration.get("drive_sources", []))
    spreadsheet_feeds = list(integration.get("spreadsheet_feeds", []))
    squarespace_routes = list(integration.get("squarespace_routes", []))
    squarespace_log = list(integration.get("squarespace_implementation_log", []))
    embed_source = integration.get("squarespace_embed_source") or {}
    pending_drive = [
        item
        for item in drive_sources
        if str(item.get("observed_status") or "") not in {"accessible", "enabled"}
    ]
    pending_sheets = [
        item
        for item in spreadsheet_feeds
        if str(item.get("observed_status") or "") not in {"accessible", "enabled"}
    ]
    pending_data_routes = [
        item
        for item in data_routes
        if str(item.get("observed_status") or "") not in {"public_200", "maintenance_stub", "json_200", "table_200"}
    ]
    unconfirmed_embed_rows = [
        item
        for item in squarespace_log
        if "UNCONFIRMED" in {
            str(item.get("page_exists") or ""),
            str(item.get("embed_pasted") or ""),
            str(item.get("desktop_preview") or ""),
            str(item.get("mobile_preview") or ""),
        }
        or "PENDING" in {
            str(item.get("desktop_preview") or ""),
            str(item.get("mobile_preview") or ""),
        }
    ]
    partially_seen_rows = [
        item
        for item in squarespace_log
        if str(item.get("page_exists") or "") == "SEEN_SCREENSHOT"
        or str(item.get("embed_pasted") or "") == "PARTIAL_RENDER_SEEN"
    ]

    blockers: list[str] = []
    warnings: list[str] = []
    if missing_public:
        blockers.append(f"Missing public routes: {', '.join(missing_public)}")
    if public_failures:
        blockers.append(f"Public route failures: {len(public_failures)}")
    if pending_data_routes:
        warnings.append("Dataspace endpoints need JSON/table payloads or explicit maintenance status.")
    if pending_drive:
        warnings.append("One or more Drive folders are not shared with the connector.")
    if pending_sheets:
        warnings.append("One or more Sheets are not shared with the connector.")
    if unconfirmed_embed_rows:
        warnings.append("Squarespace LS Web/GO embed routes still need page, paste, desktop, and mobile proof.")

    if blockers:
        overall_status = "blocked"
    elif warnings:
        overall_status = "ready_with_warnings"
    else:
        overall_status = "ready"

    public_pass_count = len(public_routes) - len(public_failures)
    required_count = len(PUBLIC_REQUIRED_ROUTES)
    readiness_numerator = public_pass_count + len(drive_sources) - len(pending_drive) + len(spreadsheet_feeds) - len(pending_sheets)
    readiness_denominator = required_count + len(drive_sources) + len(spreadsheet_feeds)
    readiness_percent = round((readiness_numerator / readiness_denominator) * 100, 1) if readiness_denominator else 0.0

    return {
        "generated_at": utc_now_iso(),
        "owner_floor": "Trinity",
        "support_floors": ["Oracle", "Smith", "Neo", "Morpheus", "TheConstruct", "Architect"],
        "health_path": str(default_bridge_health_path(root)),
        "source_contract": integration.get("contract_path"),
        "site_base_url": integration.get("site_base_url"),
        "overall_status": overall_status,
        "readiness_percent": readiness_percent,
        "walkthrough_ready": overall_status in {"ready", "ready_with_warnings"},
        "public_routes": {
            "required_count": required_count,
            "observed_count": len(public_routes),
            "pass_count": public_pass_count,
            "missing": missing_public,
            "failures": [route.get("route") for route in public_failures],
            "status_counts": _status_counts(public_routes),
        },
        "dataspace_routes": {
            "count": len(data_routes),
            "pending_count": len(pending_data_routes),
            "status_counts": _status_counts(data_routes),
            "policy": "During walkthrough, auth-gated endpoints are acceptable only when shown as known warnings. Before publish they need authenticated JSON/table payloads or explicit maintenance status.",
        },
        "squarespace_embed": {
            "source_workbook_id": embed_source.get("id"),
            "source_workbook_title": embed_source.get("title"),
            "copy_cell": embed_source.get("copy_cell"),
            "status": embed_source.get("status"),
            "gate": embed_source.get("gate"),
            "boundary": embed_source.get("boundary"),
            "route_count": len(squarespace_routes),
            "implementation_rows": len(squarespace_log),
            "unconfirmed_count": len(unconfirmed_embed_rows),
            "partial_seen_count": len(partially_seen_rows),
            "unconfirmed_routes": [item.get("route") for item in unconfirmed_embed_rows],
            "partial_seen_routes": [item.get("route") for item in partially_seen_rows],
            "blocked_actions": embed_source.get("blocked_actions") or [],
            "operator_instruction": embed_source.get("operator_instruction"),
        },
        "drive_sources": {
            "count": len(drive_sources),
            "accessible_count": len(drive_sources) - len(pending_drive),
            "pending": [item.get("id") for item in pending_drive],
        },
        "spreadsheet_feeds": {
            "count": len(spreadsheet_feeds),
            "accessible_count": len(spreadsheet_feeds) - len(pending_sheets),
            "pending": [item.get("id") for item in pending_sheets],
        },
        "bento_tile": {
            "id": "romer_bridge_health",
            "title": "Romer Bridge Health",
            "floor": "Trinity",
            "widget_type": "status",
            "state": overall_status,
            "primary_metric": f"{public_pass_count}/{required_count} public routes live",
            "secondary_metric": (
                f"{len(pending_data_routes)} data endpoints pending explicit payload/status; "
                f"{len(unconfirmed_embed_rows)} Squarespace embeds pending proof"
            ),
            "open_action": "Open bridge contract",
            "refresh_action": "Refresh route, Drive, and Sheet validation",
        },
        "warnings": warnings,
        "blockers": blockers,
        "walkthrough_sequence": [
            "Open Smart Bento Project Wall.",
            "Confirm Romer Bridge Health card is visible before selecting a project.",
            "Open public operations routes from the card or operations manager.",
            "Confirm permission-pending Drive/Sheets endpoints are shown as warnings, not crashes.",
            "Proceed with Oracle ingest, Morpheus proof, Smith handoff, TheConstruct sim, and Architect publish demo.",
        ],
        "next_actions": [
            "Share or disable the second Drive folder.",
            "Share or local-table-gate the desktop population Sheet.",
            "Convert connection_closed data endpoints to maintenance_stub, json_200, or table_200 before release.",
            "Paste and preview LS Web/GO one-cell embeds, then update 07_Implementation_Log in the Drive workbook.",
            "Keep W6 public as a compatibility facade while avoiding internal W6 filing.",
        ],
    }


def read_bridge_health(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_bridge_health_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_bridge_health(root: Path, output_path: Path | None = None) -> dict:
    destination = output_path or default_bridge_health_path(root)
    payload = build_bridge_health(root)
    payload["health_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
