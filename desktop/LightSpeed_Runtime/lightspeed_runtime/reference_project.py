from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.contracts import utc_now_iso
from lightspeed_runtime.storage_paths import publish_root


def default_romer_reference_path(root: Path) -> Path:
    return publish_root(root) / "romer" / "reference_project_path.json"


def build_romer_reference_path(
    root: Path,
    *,
    ui_alignment: dict | None = None,
    simulation_presets: dict | None = None,
    workflow_state: dict | None = None,
    latest_package: dict | None = None,
) -> dict:
    ui_alignment = ui_alignment or {}
    simulation_presets = simulation_presets or {}
    workflow_state = workflow_state or {}
    latest_package = latest_package or {}
    return {
        "generated_at": utc_now_iso(),
        "reference_project_path": str(default_romer_reference_path(root)),
        "report_path": str(default_romer_reference_path(root)),
        "source_label": "Romer reference project",
        "workspace_id": "romer",
        "project_id": "Romer",
        "owner_floor": "Architect",
        "manager_floor": "Neo",
        "operator_notes": "Use proofed knowns and empirical datasets as the reference path for finalization and handoff.",
        "operating_modes": [item.get("mode") for item in ui_alignment.get("content_plan", [])] or [
            "Workspace",
            "Operator",
            "Holospace",
        ],
        "end_to_end_steps": [
            {
                "step": 1,
                "floor": "Oracle",
                "action": "Use proofed knowns, definitions, empirical catalog, and dataset catalog as source truth.",
            },
            {
                "step": 2,
                "floor": "Morpheus",
                "action": "Review source/provenance cards and proofing records before simulation or publish.",
            },
            {
                "step": 3,
                "floor": "Neo",
                "action": "Let Achilles propose bounded work using tools first, with explicit approval for write/execute/publish.",
            },
            {
                "step": 4,
                "floor": "Smith",
                "action": "Route long-running jobs through resumable workflow state and preserve resume tokens.",
            },
            {
                "step": 5,
                "floor": "TheConstruct",
                "action": "Run Romer heliocentric zoning or target-refinement presets from compact empirical roles.",
            },
            {
                "step": 6,
                "floor": "Architect",
                "action": "Package completed outputs into governed workspace bundles with checkpoints and metadata.",
            },
        ],
        "active_contracts": {
            "ui_alignment": ui_alignment.get("path"),
            "simulation_presets": simulation_presets.get("preset_path"),
            "workflow_state": workflow_state.get("workflow_state_path"),
            "latest_governed_bundle": ((latest_package.get("files") or {}).get("governed_bundle")),
        },
        "preset_count": simulation_presets.get("preset_count", 0),
        "workflow_count": workflow_state.get("workflow_count", 0),
        "publish_bundle_shape": (
            (latest_package.get("governed_bundle") or {}).get("bundle_shape_version")
            or "1.0"
        ),
        "summary": "Romer is the reference end-to-end path for LightSpeed finalization and workflow proofing.",
    }


def read_romer_reference_path(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_romer_reference_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_romer_reference_path(
    root: Path,
    *,
    ui_alignment: dict | None = None,
    simulation_presets: dict | None = None,
    workflow_state: dict | None = None,
    latest_package: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    destination = output_path or default_romer_reference_path(root)
    payload = build_romer_reference_path(
        root,
        ui_alignment=ui_alignment,
        simulation_presets=simulation_presets,
        workflow_state=workflow_state,
        latest_package=latest_package,
    )
    payload["reference_project_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
