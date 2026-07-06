from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lightspeed_runtime.storage_paths import neo_actions_root, trinity_root


@dataclass(frozen=True)
class OperationSequence:
    id: str
    title: str
    owner_floor: str
    operators: tuple[str, ...]
    stages: tuple[dict[str, str], ...]
    z_direct_cache: str
    output: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_protocol_registry_path(root: Path) -> Path:
    return trinity_root(root) / "ui" / "protocol_sequence_registry.json"


def default_protocol_report_path(root: Path) -> Path:
    return Path(root) / "dataindex" / "26_PROTOCOL_SEQUENCE_REFINEMENT.md"


def default_achilles_handoff_path(root: Path) -> Path:
    return neo_actions_root(root) / "achilles_external_handoff.json"


def shared_color_control_protocol() -> dict[str, Any]:
    """One color-control contract reused by all theme, widget, floor, and chart surfaces."""
    return {
        "id": "shared.color_control",
        "owner_floor": "Trinity",
        "use_from": "Use this protocol anywhere a color, border, panel, chart, map, icon, or state token is changed.",
        "inputs": [
            "hex",
            "rgb",
            "rgba",
            "hsl",
            "hsla",
            "hsv",
            "alpha",
            "named_token",
            "palette_slot",
            "gradient_stop",
            "uploaded_image_sample",
        ],
        "controls": [
            "color_wheel",
            "rgb_sliders",
            "hsl_sliders",
            "alpha_slider",
            "eyedropper_or_sample_picker",
            "gradient_builder",
            "contrast_checker",
            "reset_to_floor_default",
        ],
        "outputs": {
            "canonical": "rgba",
            "derived": ["hex", "hsl", "contrast_ratio", "theme_token"],
            "save_scope": ["app", "floor", "project", "component_set", "artifact", "widget", "state"],
        },
        "rule": "No surface should implement a bespoke one-off color editor; call this shared protocol and save only the selected scope override.",
    }


def shared_loading_protocol() -> dict[str, Any]:
    return {
        "id": "shared.loading_state",
        "owner_floor": "Merovingian",
        "states": ["queued", "preloading", "loading", "running", "blocked", "complete", "failed", "cancelled"],
        "fields": ["owner_floor", "stage", "percent", "message", "started_at", "updated_at", "cancel_available", "fallback_action"],
        "use_from": [
            "startup",
            "floor activation",
            "Drive/Sheets sync",
            "Oracle ingestion",
            "Morpheus proof",
            "Smith queue execution",
            "Construct simulation",
            "Architect publish/export",
        ],
        "rule": "A blocked state with a next action is better than a blank panel or crash.",
    }


def z_direct_cache_preload_protocol() -> dict[str, Any]:
    return {
        "id": "z_direct.cache_preload",
        "owner_floor": "Smith",
        "cache_owner": "Z Direct",
        "preload_scope": [
            "floor manifest summaries",
            "smart-floor widget descriptors",
            "settings schema references",
            "route/action availability",
            "receipt state summaries",
            "external endpoint health",
        ],
        "do_not_preload": [
            "large original files",
            "full Drive folder contents beyond a bounded index",
            "raw AI logs",
            "full simulation artifacts",
            "private spreadsheet row payloads until explicitly requested",
        ],
        "handoff_states": ["received", "updated", "completed", "deleted", "declassified", "failed"],
        "cache_files": {
            "Trinity": "Z Axis/Z+3_Trinity/data/ui/smart_floor_widget_export.json",
            "Neo": "Z Axis/Z+2_Neo/data/actions/achilles_external_handoff.json",
            "Architect": "Z Axis/Z+1_Architect/data/finalization/consolidation_register.json",
            "Smith": "project component Z Direct Staging receipts",
        },
        "rule": "Z Direct caches descriptors and receipt summaries so floor calls are fast; owning floors keep canonical data.",
    }


def external_endpoint_registry() -> dict[str, Any]:
    return {
        "drive_folders": [
            {
                "id": "library_base",
                "title": "Library base",
                "url": "https://drive.google.com/drive/folders/1clPyKU1C_Prd-a4g-Cbl2RZQybLL2oag",
                "connector_status": "accessible",
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
                "owner_floor": "Oracle",
                "role": "reference/library reservoir for knowns, empirical data, GMAT, physics, and source refinement",
            },
            {
                "id": "web_lightspeed_sheets",
                "title": "Web/Lightspeed respective sheets",
                "url": "https://drive.google.com/drive/folders/1eRmR6kkNimF-U6-r6bQI9C7pWskc27W9",
                "connector_status": "accessible_empty_or_staging",
                "observed_children": [],
                "owner_floor": "Smith",
                "role": "staging folder for website/dataspace sheet contracts and future web hooks",
            },
            {
                "id": "future_lightspeed_go",
                "title": "Future LightSpeed GO",
                "url": "https://drive.google.com/drive/folders/1PkXMyv26BBvvUbxShTRMTwhnEaK_a1qb",
                "connector_status": "accessible",
                "observed_children": ["RAW AI Returns", "Nathaniel Bouwer", "Romer Industries"],
                "owner_floor": "Neo",
                "role": "future phone/light dash handoff folder for Achilles Online, Achilles Desktop, LightSpeed, and Neo task sync",
            },
        ],
        "spreadsheet_books": [
            {
                "id": "website_feed",
                "url": "https://docs.google.com/spreadsheets/d/1POCTGwSyaznMCO-7rA79wNRWT7rReSjOsNx-CLn5u5E/edit",
                "owner_floor": "Oracle",
                "role": "website schema/log feed with publish gates",
                "tabs_required": ["Contents", "Schema Dictionary", "Handoff Protocols", "QA Validation", "Changelog"],
            },
            {
                "id": "desktop_population",
                "url": "https://docs.google.com/spreadsheets/d/1GOzjF5BESSTWDqxi1hpGIk4a5R2kyrEY6EUeYN3vm9M/edit",
                "owner_floor": "Smith",
                "role": "desktop queue/book to populate from Oracle, Morpheus, Smith, Construct, and Architect outputs",
                "tabs_required": ["Task Queue", "Handoff Receipts", "Knowns", "Datatables", "Publish Queue", "Device Sync"],
            },
        ],
        "drive_queue_contracts": [
            {
                "id": "future_lightspeed_go_drive_queue",
                "url": "https://drive.google.com/drive/folders/1PkXMyv26BBvvUbxShTRMTwhnEaK_a1qb",
                "owner_floor": "Neo",
                "connector_status": "folder_ready_sheet_not_created",
                "role": "folder-first future phone dash task queue and device command bridge",
                "required_tables": ["Phone Tasks", "Approvals", "Device Commands", "Results", "Sync Health"],
            },
        ],
        "webhook_contract": {
            "owner_floor": "Smith",
            "policy": "Sheets and web tools receive queued rows from Z Direct only after owner-floor proof/approval.",
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
    }


def condensed_file_policy() -> dict[str, Any]:
    return {
        "owner_floor": "Merovingian",
        "policy": "Prefer compact indexed tables and weekly logs over hundreds of small standalone evidence files.",
        "by_type": {
            "ai_logs": "outer_archive_after_final_pass",
            "task_events": "Smith receipt table or JSONL ledger",
            "definitions": "Oracle Dictionary.IT table by category",
            "knowns": "Oracle knowns/library/encyclopedia/datatable records",
            "simulation_outputs": "Construct scenario artifact plus ephemeris/rerun metadata",
            "release_evidence": "Merovingian report directory with one readiness run pair per proof cycle",
            "ui_protocols": "Trinity JSON contracts generated from runtime functions",
        },
        "rule": "If a file only says that a task happened, fold it into the owner floor table/report. Preserve source documents and proof artifacts.",
    }


def operation_sequences() -> list[OperationSequence]:
    return [
        OperationSequence(
            id="startup_preload",
            title="Startup preload and shell readiness",
            owner_floor="Trinity",
            operators=("Trinity", "Smith", "Merovingian"),
            stages=(
                {"stage": "load_settings", "owner": "Trinity", "result": "shared settings/color/loading protocols available"},
                {"stage": "preload_descriptors", "owner": "Smith", "result": "Z Direct cache holds manifests, widget descriptors, routes"},
                {"stage": "health_gate", "owner": "Merovingian", "result": "readiness and dependency states visible"},
            ),
            z_direct_cache="preload descriptors only; do not load heavy artifacts until selected",
            output="operator shell opens with project wall, Z-floor dropdown, and loading state",
        ),
        OperationSequence(
            id="project_artifact_workflow",
            title="Project, folders, documents, widgets, and component sets",
            owner_floor="Trinity",
            operators=("Trinity", "Oracle", "Morpheus", "Smith"),
            stages=(
                {"stage": "select_project", "owner": "Trinity", "result": "project wall and component sets"},
                {"stage": "preview_or_edit", "owner": "Trinity", "result": "drawer/fullscreen/editor via shared renderer"},
                {"stage": "handoff", "owner": "Smith", "result": "Z Direct receipt with target floor/action"},
                {"stage": "proof_if_needed", "owner": "Morpheus", "result": "proof tags and confidence update"},
            ),
            z_direct_cache="cache selected tile descriptor, path, provenance, proof state, and target floor",
            output="artifact stays in project wall; floor-specific work is a handoff, not a duplicate page",
        ),
        OperationSequence(
            id="oracle_ingest_morpheus_proof",
            title="Oracle ingestion and Morpheus proofing",
            owner_floor="Oracle",
            operators=("Oracle", "Morpheus", "Neo", "Smith"),
            stages=(
                {"stage": "preserve_original", "owner": "Oracle", "result": "original file retained and editable"},
                {"stage": "extract_components", "owner": "Oracle", "result": "definitions, rows, strings, tasks, partial objects"},
                {"stage": "proof_claims", "owner": "Morpheus", "result": "source, unit, confidence, publish gate"},
                {"stage": "write_knowns", "owner": "Oracle", "result": "Dictionary.IT, library, encyclopedia, datatables"},
            ),
            z_direct_cache="cache extraction receipt and proof state, not full originals",
            output="condensed knowns/datatable records with provenance",
        ),
        OperationSequence(
            id="construct_simulation_flow",
            title="Construct zoning, simulation, GMAT, and ephemeris flow",
            owner_floor="TheConstruct",
            operators=("TheConstruct", "Oracle", "Morpheus", "Architect"),
            stages=(
                {"stage": "zone", "owner": "TheConstruct", "result": "heliocentric zone summary"},
                {"stage": "cluster", "owner": "TheConstruct", "result": "candidate clusters and value layers"},
                {"stage": "classify", "owner": "Morpheus", "result": "proofed RFS/EMFF and source assumptions"},
                {"stage": "export", "owner": "TheConstruct", "result": "GMAT batch, ephemeris, rerun metadata"},
            ),
            z_direct_cache="cache scenario parameters and output references for replay",
            output="simulation artifacts are shareable/replayable without loading the full engine at startup",
        ),
        OperationSequence(
            id="external_achilles_handoff",
            title="External website, Sheets, Achilles, and LightSpeed GO handoff",
            owner_floor="Neo",
            operators=("Neo", "Smith", "Oracle", "Architect"),
            stages=(
                {"stage": "queue_task", "owner": "Neo", "result": "operator/action envelope"},
                {"stage": "approve_route", "owner": "Architect", "result": "publish/external write gate"},
                {"stage": "write_sheet_row", "owner": "Smith", "result": "Sheets/webhook payload"},
                {"stage": "sync_result", "owner": "Oracle", "result": "result row, proof state, and source link indexed"},
            ),
            z_direct_cache="cache external endpoint health, sheet schema, pending row count, and last sync status",
            output="future device/app bridge can queue tasks without coupling phone UI to desktop internals",
        ),
    ]


def build_protocol_sequence_registry(root: Path) -> dict[str, Any]:
    return {
        "generated_at": utc_now_iso(),
        "root": str(Path(root)),
        "owner_floor": "Trinity",
        "support_floors": ["Neo", "Oracle", "Morpheus", "TheConstruct", "Architect", "Smith", "Merovingian"],
        "contract_path": str(default_protocol_registry_path(root)),
        "shared_protocols": {
            "color_control": shared_color_control_protocol(),
            "loading_state": shared_loading_protocol(),
            "z_direct_cache_preload": z_direct_cache_preload_protocol(),
            "condensed_file_policy": condensed_file_policy(),
        },
        "operation_sequences": [sequence.to_dict() for sequence in operation_sequences()],
        "external_endpoints": external_endpoint_registry(),
        "rules": [
            "Define a protocol once, then call it from floor, widget, project, artifact, and settings scopes.",
            "Z Direct preloads descriptor/cache state and receipts; owner floors keep canonical data.",
            "Drive, Sheets, website, and future phone dash integrations are endpoint contracts until write approvals are explicit.",
            "Small proof/log/task files are collapsed into owner-floor tables, JSONL ledgers, or weekly reports before packaging.",
        ],
    }


def build_achilles_external_handoff(root: Path) -> dict[str, Any]:
    registry = build_protocol_sequence_registry(root)
    endpoints = registry["external_endpoints"]
    return {
        "generated_at": registry["generated_at"],
        "owner_floor": "Neo",
        "contract_path": str(default_achilles_handoff_path(root)),
        "purpose": "Achilles/Neo external handoff contract for website, Sheets, desktop, online, and future LightSpeed GO sync.",
        "queue_owner": "Smith",
        "proof_owner": "Morpheus",
        "source_owner": "Oracle",
        "approval_owner": "Architect",
        "drive_folders": endpoints["drive_folders"],
        "spreadsheet_books": endpoints["spreadsheet_books"],
        "webhook_contract": endpoints["webhook_contract"],
        "minimum_phone_dash_fields": [
            "task_id",
            "title",
            "status",
            "priority",
            "source_floor",
            "target_floor",
            "next_action",
            "approval_required",
            "result_ref",
            "updated_at",
        ],
        "safe_defaults": {
            "phone_dash": "read_queue_write_intent_only",
            "external_writes": "approval_required",
            "large_payloads": "store_reference_not_full_payload",
            "offline_mode": "queue_until_desktop_or_achilles_online_confirms_received",
        },
    }


def write_protocol_sequence_registry(root: Path, output_path: Path | None = None) -> dict[str, Any]:
    destination = output_path or default_protocol_registry_path(root)
    payload = build_protocol_sequence_registry(root)
    payload["contract_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def write_achilles_external_handoff(root: Path, output_path: Path | None = None) -> dict[str, Any]:
    destination = output_path or default_achilles_handoff_path(root)
    payload = build_achilles_external_handoff(root)
    payload["contract_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def write_protocol_sequence_report(root: Path, output_path: Path | None = None) -> dict[str, Any]:
    destination = output_path or default_protocol_report_path(root)
    registry = build_protocol_sequence_registry(root)
    lines = [
        "# Protocol Sequence Refinement",
        "",
        f"Generated: {registry['generated_at']}",
        "",
        "## Shared Protocols",
        "",
    ]
    for name, protocol in registry["shared_protocols"].items():
        protocol_id = protocol.get("id", name)
        lines.append(f"- {name}: {protocol['owner_floor']} owns `{protocol_id}`")
    lines.extend(["", "## Operation Sequences", ""])
    for sequence in registry["operation_sequences"]:
        lines.append(f"- {sequence['id']}: {sequence['owner_floor']} -> {sequence['output']}")
    lines.extend(["", "## External Endpoints", ""])
    for folder in registry["external_endpoints"]["drive_folders"]:
        lines.append(f"- {folder['id']}: {folder['connector_status']} -> {folder['role']}")
    lines.extend(["", "## Rules", ""])
    lines.extend(f"- {rule}" for rule in registry["rules"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"path": str(destination), "registry": registry}
