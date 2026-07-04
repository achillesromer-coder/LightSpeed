from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lightspeed_runtime.storage_paths import catalog_root


SITE_BASE_URL = "https://romer.industries"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_romer_web_integration_path(root: Path) -> Path:
    return catalog_root(root) / "website" / "romer_web_integration.json"


def _route(path: str, title: str, owner_floor: str, workspace: str, role: str, status: str = "public_200") -> dict:
    return {
        "route": path,
        "url": f"{SITE_BASE_URL}{path}",
        "title": title,
        "owner_floor": owner_floor,
        "workspace": workspace,
        "role": role,
        "observed_status": status,
    }


def build_romer_web_integration(root: Path) -> dict:
    """Build the desktop-side contract for the public website, Drive folders, and Sheets feeds."""
    routes = [
        _route("/", "Romer Industries", "Architect", "Front", "front-facing company landing page"),
        _route("/operations", "Romer Industries Operations", "Smith", "Operations", "public operations index"),
        _route("/operations/w1", "Incoming Deposit Analysis", "Oracle", "W1", "deposit/target intake tracker"),
        _route("/operations/w2", "Geostationary Luke II", "TheConstruct", "W2", "EMFF catch-and-hold modelling tracker"),
        _route("/operations/w3", "RFS & EMFF Field Projections", "TheConstruct", "W3", "RFS/EMFF extraction modelling tracker"),
        _route("/operations/w4", "Inter-planetary Supply Chain Network", "Architect", "W4", "supply-chain closure tracker"),
        _route("/operations/w5", "Mission Mapping", "TheConstruct", "W5", "GMAT mission planning tracker"),
        _route("/operations/w6", "Asset Library", "Oracle", "W6", "legacy public asset-library compatibility facade"),
        _route("/gmat", "GMAT", "TheConstruct", "W5", "public GMAT reference and mission-analysis surface"),
        _route("/library", "Library", "Oracle", "Library", "public knowledge/library facade"),
        _route("/docs", "Docs", "Oracle", "Docs", "public document facade"),
        _route("/dash", "Dash", "Trinity", "Dash", "public dashboard facade"),
        _route("/data/achilles", "Achilles Dataspace", "Neo", "Achilles", "data endpoint for operator/backend sync", "requires_auth_401"),
        _route("/data/directory", "Data Directory", "Oracle", "Directory", "data endpoint for public directory sync", "requires_auth_401"),
    ]
    routes.extend(
        _route(
            f"/w{workspace}/data",
            f"W{workspace} Dataspace",
            "Smith",
            f"W{workspace}",
            "workspace dataspace endpoint referenced from operations pages",
            "requires_auth_401",
        )
        for workspace in range(1, 7)
    )

    return {
        "generated_at": utc_now_iso(),
        "owner_floor": "Oracle",
        "support_floors": ["Smith", "Neo", "Morpheus", "TheConstruct", "Architect", "Trinity"],
        "contract_path": str(default_romer_web_integration_path(root)),
        "site_base_url": SITE_BASE_URL,
        "website_routes": routes,
        "drive_sources": [
            {
                "id": "1clPyKU1C_Prd-a4g-Cbl2RZQybLL2oag",
                "url": "https://drive.google.com/drive/folders/1clPyKU1C_Prd-a4g-Cbl2RZQybLL2oag",
                "title": "Library",
                "observed_status": "accessible",
                "observed_children": [
                    "Solar System Archive",
                    "Web Scrape & Analysis",
                    "GMAT_R2025a",
                    "BioChem",
                    "Physics",
                    "Empirical Data",
                    "EMASSC",
                    "Raphael",
                    "JSON Library",
                ],
                "desktop_role": "Oracle source library and empirical/reference reservoir for Neo/Achilles tasks.",
            },
            {
                "id": "1eRmR6kkNimF-U6-r6bQI9C7pWskc27W9",
                "url": "https://drive.google.com/drive/folders/1eRmR6kkNimF-U6-r6bQI9C7pWskc27W9",
                "title": "Web/Lightspeed respective sheets",
                "observed_status": "accessible_empty_or_staging",
                "observed_children": [],
                "desktop_role": "Website/dataspace sheet staging folder and future web-hook source.",
            },
            {
                "id": "1PkXMyv26BBvvUbxShTRMTwhnEaK_a1qb",
                "url": "https://drive.google.com/drive/folders/1PkXMyv26BBvvUbxShTRMTwhnEaK_a1qb",
                "title": "Future LightSpeed GO",
                "observed_status": "accessible",
                "observed_children": [
                    "RAW AI Returns",
                    "Nathaniel Bouwer",
                    "Romer Industries",
                ],
                "desktop_role": "Future phone/light dash folder for Achilles Online, Achilles Desktop, LightSpeed, and Neo task sync.",
            },
        ],
        "spreadsheet_feeds": [
            {
                "id": "1POCTGwSyaznMCO-7rA79wNRWT7rReSjOsNx-CLn5u5E",
                "url": "https://docs.google.com/spreadsheets/d/1POCTGwSyaznMCO-7rA79wNRWT7rReSjOsNx-CLn5u5E/edit",
                "title": "Website Logs",
                "observed_status": "accessible",
                "tabs_observed": [
                    "Achilles Tasked Logs",
                    "Contents",
                    "Schema Dictionary",
                    "Engine Overview",
                    "Zone Overview",
                    "Scenario Overview",
                    "Handoff Protocols",
                    "Equation Constants",
                    "QA Validation",
                    "Changelog",
                    "Zone NEA",
                    "Zone IMB",
                    "Zone CB",
                    "Zone RE",
                    "Engine Zone",
                    "Engine Cluster",
                    "Engine Object Classification",
                    "Engine Transport Suitability",
                    "Engine Extraction Suitability",
                    "Engine Mission Readiness",
                    "Engine Handoff",
                    "Scenario's W1",
                    "Scenario's W2",
                    "Scenario's W3",
                    "Scenario's W4",
                    "Scenario's W5",
                    "W6 Index",
                    "00_Contents",
                ],
                "desktop_role": "Website-facing logs/schema feed; publish_flag gates external reporting.",
            },
            {
                "id": "1GOzjF5BESSTWDqxi1hpGIk4a5R2kyrEY6EUeYN3vm9M",
                "url": "https://docs.google.com/spreadsheets/d/1GOzjF5BESSTWDqxi1hpGIk4a5R2kyrEY6EUeYN3vm9M/edit",
                "title": "Desktop population sheet",
                "observed_status": "permission_denied_or_not_shared_to_connector",
                "tabs_observed": [],
                "desktop_role": "Desktop-side sheet to be populated from Oracle/Morpheus/Smith after permission is granted.",
                "tabs_required": ["Task Queue", "Handoff Receipts", "Knowns", "Datatables", "Publish Queue", "Device Sync"],
            },
            {
                "id": "future_lightspeed_go_queue",
                "url": "pending_sheet_inside_future_lightspeed_go_folder",
                "title": "Future LightSpeed GO queue",
                "observed_status": "planned",
                "tabs_observed": [],
                "desktop_role": "Future phone dash task queue and device command bridge.",
                "tabs_required": ["Phone Tasks", "Approvals", "Device Commands", "Results", "Sync Health"],
            },
        ],
        "webhook_contract": {
            "owner_floor": "Smith",
            "source_floor": "Neo",
            "proof_floor": "Morpheus",
            "approval_floor": "Architect",
            "policy": "External tools receive queued rows from Z Direct only after proof/approval.",
            "payload_fields": [
                "task_id",
                "source_system",
                "source_floor",
                "target_floor",
                "action",
                "payload_ref",
                "status",
                "proof_state",
                "approved_by",
                "created_at",
                "updated_at",
            ],
        },
        "handoff_policy": {
            "ingest": "Oracle stores original files and extracts components into knowns, datatables, object records, and task candidates.",
            "proof": "Morpheus validates extracted facts against schema dictionary, source_type, confidence_level, and publish_flag.",
            "route": "Smith/Z Direct queues floor updates and dataspace writes, including received/updated/deleted states.",
            "operate": "Neo and Achilles propose work, populate approved rows, and hand off to TheConstruct or Architect as required.",
            "publish": "Architect publishes only approved website-facing rows and V0.10.0 snapshots; D-root remains overwrite-only output.",
        },
        "pre_walkthrough_tasks": [
            "Confirm connector access for the second Drive folder and desktop population sheet.",
            "Normalize website route spellings and fix public typos before publishing.",
            "Replace W6 as an internal filing system with Oracle/Construct/Architect ownership while keeping public /operations/w6 as a compatibility facade.",
            "Map every public /w*/data endpoint to a desktop datasource table, queue, or stub with health state.",
            "Run startup wizard through project creation, bento artifact creation, file attach, Morpheus proof, Smith handoff, and Architect publish.",
            "Validate missing dependency flow creates Neo approval tasks instead of crashing.",
            "Verify startup/loading bars around Drive/Sheets fetches, dataset ingestion, GMAT runs, and Holospace rendering.",
            "Cull safe generated caches and archive stale dataindex notes into Merovingian reports before packaging.",
            "Run N.py smoke, pytest contracts, launch verifier, and route/Drive bridge validation.",
            "Package C-root canonical application to D-root snapshot only after walkthrough approval.",
        ],
    }


def read_romer_web_integration(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_romer_web_integration_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_romer_web_integration(root: Path, output_path: Path | None = None) -> dict:
    destination = output_path or default_romer_web_integration_path(root)
    payload = build_romer_web_integration(root)
    payload["contract_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
