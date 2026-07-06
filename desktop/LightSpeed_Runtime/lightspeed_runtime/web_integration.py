from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lightspeed_runtime.storage_paths import catalog_root


SITE_BASE_URL = "https://romer.industries"

LS_WEB_GO_WORKBOOK = {
    "id": "1wLNW2cC-vQ1ZTzNmgGQiSFE0wGp_dvupCW1ZGBtT_yw",
    "url": "https://docs.google.com/spreadsheets/d/1wLNW2cC-vQ1ZTzNmgGQiSFE0wGp_dvupCW1ZGBtT_yw/edit",
    "title": "LS_WEB_LS_GO_One_Cell_Embed_Block_Source_2026_06_02",
    "copy_cell": "01_One_Cell_Embed!A10",
    "status": "READY_FOR_COPY_PASTE",
    "gate": "COMP2_STAGED_WAITING_ON_COMP1",
    "boundary": "static shell only; no API, no secrets, no wallet/token/mint/payment/custody, no dataset merge",
}

LS_WEB_GO_WORKBOOK_SHEETS = [
    "01_One_Cell_Embed",
    "02_Routes",
    "03_Checks",
    "04_Shell_Link_Index",
    "05_Landing_Graph_Map",
    "06_Brand_Tokens",
    "07_Implementation_Log",
    "08_Archive_Amalgamation",
    "09_Canon_Buildout_Gates",
    "10_Canonical_Targets_Staging",
    "11_Git_Lanes_Staging",
    "12_Domain_Brackets",
    "13_Dashboard_Classification",
    "14_ZIP_Authority_Rules",
    "15_Logo_Earth_Policy",
]

LS_WEB_GO_ROUTES = [
    ("/data/achilles", "data", "Achilles Core Data Node", "COMP-2 staged"),
    ("/test/work", "workspace", "Workspace Test Shell", "test/no prod"),
    ("/test/data", "data", "Dataspace Test Shell", "no private data"),
    ("/workspaces", "workspace", "Workspace Hub", "staged"),
    ("/data", "data", "Dataspace Hub", "staged"),
    ("/w1/work", "workspace", "W1 Deposit Workspace", "no prod action"),
    ("/w1/data", "data", "Deposit Analysis Dataspace", "no reserves claim"),
    ("/w2/work", "workspace", "W2 Luke Workspace", "no prod action"),
    ("/w2/data", "data", "Luke II Dataspace", "no capture claim"),
    ("/w3/work", "workspace", "W3 RFS / EMFF Workspace", "claim-gated"),
    ("/w3/data", "data", "RFS & EMFF Dataspace", "no extraction claim"),
    ("/w4/work", "workspace", "W4 Supply Chain Workspace", "claim-gated"),
    ("/w4/data", "data", "Supply Chain Dataspace", "no throughput claim"),
    ("/w5/work", "workspace", "W5 GMAT Workspace", "simulation only"),
    ("/w5/data", "data", "GMAT Dataspace", "simulation only"),
    ("/w6/work", "workspace", "W6 Asset Library Workspace", "privacy review"),
    ("/w6/data", "data", "Asset Library Dataspace", "privacy review"),
    ("/ccc/test", "CCC", "CCC Builder Shell", "no wallet/token/mint"),
    ("/ccc/dash", "CCC", "CCC Member Dashboard", "private by default"),
    ("/build/portfolio", "builder", "Portfolio Builder", "draft/review"),
    ("/build/collective", "builder", "Collective Builder", "no governance activation"),
    ("/build/collection", "builder", "Collection Builder", "no mint/token"),
    ("/ls-go", "LS GO", "LightSpeed GO", "read/status/handoff only"),
    ("/ls-go/status", "LS GO", "LS GO Status", "no backend writes"),
    ("/ls-go/handoff", "LS GO", "LS GO Handoff", "compact handoff only"),
    ("/ls-go/agents", "LS GO", "LS GO Agents", "no autonomy escalation"),
    ("/ls-go/review", "LS GO", "LS GO Review", "claim-gated"),
    ("calculator routes", "special", "Calculator Route Hub", "calc not validation"),
    ("Raphael panels", "special", "Raphael Engine Panels", "proof routing only"),
    ("node globe", "special", "Achilles Node Globe", "privacy/claim gated"),
    ("SHFF / M1 panels", "special", "SHFF / M1 Claim-Safe Panels", "concept only"),
]

LS_WEB_GO_IMPLEMENTATION_LOG = [
    ("/ls-go", "UNCONFIRMED", "UNCONFIRMED", "PENDING", "PENDING", "read/status/handoff only", "Verify page and paste row-10 embed"),
    ("/ls-go/status", "UNCONFIRMED", "UNCONFIRMED", "PENDING", "PENDING", "status only; no backend writes", "Verify page and paste row-10 embed"),
    ("/ls-go/handoff", "SEEN_SCREENSHOT", "PARTIAL_RENDER_SEEN", "UNCONFIRMED", "UNCONFIRMED", "compact handoff only", "Confirm saved embed and preview both views"),
    ("/ls-go/agents", "UNCONFIRMED", "UNCONFIRMED", "PENDING", "PENDING", "no autonomy escalation", "Verify page exists and paste row-10 embed"),
    ("/ls-go/review", "UNCONFIRMED", "UNCONFIRMED", "PENDING", "PENDING", "claim-gated", "Verify page exists and paste row-10 embed"),
    ("/data/achilles", "UNCONFIRMED", "UNCONFIRMED", "PENDING", "PENDING", "not MCP server; dashboard only", "Verify/paste/preview"),
    ("/data", "UNCONFIRMED", "UNCONFIRMED", "PENDING", "PENDING", "staged data hub", "Verify/paste/preview"),
    ("/workspaces", "UNCONFIRMED", "UNCONFIRMED", "PENDING", "PENDING", "staged workspace hub", "Verify/paste/preview"),
]

LS_WEB_GO_BRAND_TOKENS = {
    "primary": "#156162",
    "secondary": "#235160",
    "dark": "#0A0C0B",
    "white": "#ECE4E2",
    "romer_gold": "#C9A24A",
    "ready_green": "#B7FF59",
    "pending_yellow": "#F2C94C",
    "blocked_red": "#D66A6A",
    "concept_velvet": "#5A2A4A",
}

LS_WEB_GO_CANON_GATES = [
    "Landing graph map is staging, not final authority yet.",
    "Comprehensive folder/file system waits until deletion reconciliation.",
    "Branding must come from canonical sources first.",
    "Final pages/docs should be unversioned in visible public surfaces.",
    "Archive is preservation-first: extract before marking for deletion.",
    "Secondary Z stack remains excluded.",
]

BLOCKED_PUBLIC_ACTIONS = [
    "publish",
    "deploy",
    "live_write",
    "secrets",
    "wallet",
    "token",
    "mint",
    "ipfs",
    "payment",
    "custody",
    "public_dataset_merge",
    "unsupported_claims",
]


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
    squarespace_routes = [
        {
            "route_id": f"R-{index:03d}",
            "route": route,
            "url": f"{SITE_BASE_URL}{route}" if route.startswith("/") else None,
            "group": group,
            "page_title": title,
            "shell_source": "Master one-cell",
            "copy_cell": LS_WEB_GO_WORKBOOK["copy_cell"],
            "gate": gate,
            "state": "staged",
        }
        for index, (route, group, title, gate) in enumerate(LS_WEB_GO_ROUTES, start=1)
    ]
    implementation_log = [
        {
            "route": route,
            "page_exists": page_exists,
            "embed_pasted": embed_pasted,
            "desktop_preview": desktop_preview,
            "mobile_preview": mobile_preview,
            "claim_gate": claim_gate,
            "next_action": next_action,
        }
        for (
            route,
            page_exists,
            embed_pasted,
            desktop_preview,
            mobile_preview,
            claim_gate,
            next_action,
        ) in LS_WEB_GO_IMPLEMENTATION_LOG
    ]

    return {
        "generated_at": utc_now_iso(),
        "owner_floor": "Oracle",
        "desktop_operator_floor": "Neo",
        "publish_owner_floor": "Architect",
        "support_floors": ["Smith", "Neo", "Morpheus", "TheConstruct", "Architect", "Trinity"],
        "contract_path": str(default_romer_web_integration_path(root)),
        "site_base_url": SITE_BASE_URL,
        "website_routes": routes,
        "squarespace_embed_source": {
            **LS_WEB_GO_WORKBOOK,
            "sheets": LS_WEB_GO_WORKBOOK_SHEETS,
            "blocked_actions": BLOCKED_PUBLIC_ACTIONS,
            "operator_instruction": (
                "Copy only cell A10 into Squarespace Embed/Code Block, preview desktop and mobile, "
                "then log Page Exists, Embed Pasted, Desktop Preview, Mobile Preview, Badges, "
                "Blocked Actions, and Claim Gate into 07_Implementation_Log."
            ),
        },
        "squarespace_routes": squarespace_routes,
        "squarespace_implementation_log": implementation_log,
        "brand_tokens": LS_WEB_GO_BRAND_TOKENS,
        "canon_gates": LS_WEB_GO_CANON_GATES,
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
            "Expose the LS Web/GO embed workbook state inside LightSpeed Desktop so Neo can see pending route proof without searching Drive.",
            "Verify /ls-go, /ls-go/status, /ls-go/handoff, /ls-go/agents, /ls-go/review, /data/achilles, /data, and /workspaces against 07_Implementation_Log.",
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
