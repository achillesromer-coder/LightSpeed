from __future__ import annotations

from lightspeed_runtime.runtime import LightSpeedRuntime
from lightspeed_runtime.contracts import stable_id, utc_now_iso


def _baseline_latest_run(
    *,
    dataset_refs: list[str] | None,
    artifact_refs: list[dict] | None,
) -> dict:
    return {
        "run_id": stable_id("baseline"),
        "lab_type": "baseline_export",
        "scenario_id": "d_drive_baseline_staging",
        "dataset_refs": list(dataset_refs or []),
        "parameter_set": {
            "scope": "configured_light_speed_reservoirs",
            "external_publish": False,
            "drive_writeback": False,
        },
        "engine": "bootstrap_runtime",
        "outputs": list(artifact_refs or []),
        "metrics": {
            "dataset_ref_count": len(dataset_refs or []),
            "artifact_ref_count": len(artifact_refs or []),
            "manual_gate_required": True,
        },
        "status": "completed",
        "published": False,
        "uncertainty_summary": "staged_baseline_pending_external_review",
        "confidence_score": 0.66,
        "completed_at": utc_now_iso(),
    }


def build_romer_publish_manifest(
    runtime: LightSpeedRuntime,
    *,
    workspace_id: str = "romer",
    project_id: str = "Romer",
    overview: str,
    artifact_refs: list[dict] | None = None,
    dataset_refs: list[str] | None = None,
    visibility: str = "internal",
) -> dict:
    intermediary = runtime.load_intermediary_targets().get("website_bridge", {})
    latest_runs = runtime.labs.list_runs()
    if not latest_runs:
        latest_runs = [_baseline_latest_run(dataset_refs=dataset_refs, artifact_refs=artifact_refs)]
    manifest = runtime.publishing.create_workspace_manifest(
        workspace_id=workspace_id,
        project_id=project_id,
        summary_blocks=[
            {"title": "Romer Overview", "body": overview},
            {
                "title": "Data Reservoirs",
                "body": ", ".join(dataset_refs or []) if dataset_refs else "No dataset refs attached yet.",
            },
        ],
        artifacts=artifact_refs or [],
        visualizations=[
            {"type": "mission_status", "label": "Romer Mission Status"},
            {"type": "dataset_lineage", "label": "Reservoir Provenance"},
        ],
        latest_runs=latest_runs,
        links=[
            {"label": "NotebookLM Doctrine", "source_id": "notebooklm_2026"},
            {"label": "Calculator Library", "source_id": "library_calculators"},
            {"label": "Raphael Archive", "source_id": "raphael_archive"},
            {"label": intermediary.get("label", "Website Bridge"), "url": intermediary.get("url")},
        ],
        visibility=visibility,
        status="ready",
    )
    payload = manifest.to_dict()
    if latest_runs and latest_runs[0].get("scenario_id") == "d_drive_baseline_staging":
        payload["validation_state"] = "staged_baseline"
        payload["validation_summary"] = (
            "Baseline run record generated from configured D-drive reservoirs. "
            "External Drive, GitHub, Netlify, and web publish remain manually gated."
        )
    if intermediary:
        payload["intermediary_bridge"] = intermediary
    return payload
