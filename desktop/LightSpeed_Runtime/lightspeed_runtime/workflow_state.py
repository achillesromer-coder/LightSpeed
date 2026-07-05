from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.contracts import deterministic_id, utc_now_iso
from lightspeed_runtime.storage_paths import operations_root


def default_workflow_state_path(root: Path) -> Path:
    return operations_root(root) / "workflow_state.json"


def _workflow_from_job(job: dict) -> dict:
    status = str(job.get("status") or "queued")
    if status == "completed":
        phase = "complete"
        checkpoint = "result_recorded"
    elif status == "in_progress":
        phase = "execute"
        checkpoint = "floor_tool_running"
    else:
        phase = "queued"
        checkpoint = "awaiting_dispatch"
    job_id = str(job.get("job_id") or "job")
    updated_at = str(job.get("updated_at") or job.get("created_at") or "")
    return {
        "workflow_id": deterministic_id("workflow", job_id, str(job.get("job_type") or ""), str(job.get("project_id") or "")),
        "resume_token": deterministic_id("resume", job_id, status, updated_at),
        "job_id": job_id,
        "job_type": job.get("job_type"),
        "label": job.get("label"),
        "workspace_id": job.get("workspace_id"),
        "project_id": job.get("project_id"),
        "source_floor": job.get("source_floor"),
        "target_floor": job.get("target_floor"),
        "status": status,
        "phase": phase,
        "checkpoint": checkpoint,
        "priority": job.get("priority"),
        "result_ref": job.get("result_ref"),
        "payload": job.get("payload") or {},
        "resume_policy": {
            "strategy": "idempotent_resume",
            "safe_to_resume": status in {"queued", "in_progress", "staged_for_review"},
            "requires_approval": status not in {"completed", "cancelled", "failed"},
        },
        "checkpoint_order": [
            "awaiting_dispatch",
            "input_validated",
            "floor_tool_running",
            "artifacts_written",
            "result_recorded",
        ],
    }


def build_resumable_workflow_state(root: Path, *, smith_router: dict, simulation_presets: dict | None = None) -> dict:
    workflows = [_workflow_from_job(job) for job in smith_router.get("jobs") or []]
    resumable = [item for item in workflows if (item.get("resume_policy") or {}).get("safe_to_resume")]
    return {
        "generated_at": utc_now_iso(),
        "workflow_state_path": str(default_workflow_state_path(root)),
        "owner_floor": "Smith",
        "support_floors": ["Neo", "TheConstruct", "Architect", "Merovingian"],
        "workflow_count": len(workflows),
        "resumable_count": len(resumable),
        "completed_count": sum(1 for item in workflows if item.get("status") == "completed"),
        "router_path": smith_router.get("router_path"),
        "simulation_presets_path": (simulation_presets or {}).get("preset_path"),
        "presets_available": (simulation_presets or {}).get("preset_count", 0),
        "workflows": workflows,
        "summary": (
            f"Smith resumable workflow state tracks {len(workflows)} workflows | "
            f"resumable={len(resumable)} | completed={sum(1 for item in workflows if item.get('status') == 'completed')}"
        ),
    }


def read_resumable_workflow_state(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_workflow_state_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_resumable_workflow_state(
    root: Path,
    *,
    smith_router: dict,
    simulation_presets: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    destination = output_path or default_workflow_state_path(root)
    payload = build_resumable_workflow_state(root, smith_router=smith_router, simulation_presets=simulation_presets)
    payload["workflow_state_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
