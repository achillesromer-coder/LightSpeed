from __future__ import annotations

import json
import re
from pathlib import Path

from lightspeed_runtime.contracts import utc_now_iso
from lightspeed_runtime.storage_paths import operations_root


def default_smith_router_path(root: Path) -> Path:
    return operations_root(root) / "smith_router.json"


ROUTE_MAP = {
    "knowledge_refresh": {"target_floor": "Oracle", "queue_id": "knowledge_alignment", "label": "Oracle knowledge refresh"},
    "knowns_declassification": {
        "target_floor": "Oracle",
        "queue_id": "knowledge_alignment",
        "label": "Oracle doctrine declassification",
    },
    "proofing_review": {"target_floor": "Morpheus", "queue_id": "knowledge_alignment", "label": "Morpheus proofing review"},
    "scientific_query_refresh": {
        "target_floor": "Oracle",
        "queue_id": "knowledge_alignment",
        "label": "Oracle scientific query refresh",
    },
    "heliocentric_zoning": {
        "target_floor": "TheConstruct",
        "queue_id": "operator_simulation",
        "label": "Construct heliocentric zoning run",
    },
    "simulation_run": {"target_floor": "TheConstruct", "queue_id": "operator_simulation", "label": "Construct simulation run"},
    "gmat_batch": {"target_floor": "TheConstruct", "queue_id": "operator_simulation", "label": "Construct GMAT batch"},
    "publish_package": {"target_floor": "Architect", "queue_id": "operator_simulation", "label": "Architect package publish"},
    "publish_snapshot": {"target_floor": "Architect", "queue_id": "operator_simulation", "label": "Architect publish snapshot"},
    "operator_brief": {"target_floor": "Neo", "queue_id": "operator_simulation", "label": "Neo operator brief"},
    "action_review": {"target_floor": "Neo", "queue_id": "operator_simulation", "label": "Neo action review"},
}


def read_smith_router_state(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_smith_router_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _normalize_job_type(job_type: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (job_type or "").strip().lower()).strip("_") or "job"


def _route_for_job(job_type: str, target_floor: str | None = None) -> dict:
    route = dict(ROUTE_MAP.get(_normalize_job_type(job_type), {}))
    route.setdefault("target_floor", target_floor or "Smith")
    route.setdefault("queue_id", "sweep_finalization")
    route.setdefault("label", job_type.replace("_", " ").title() or "Smith job")
    if target_floor:
        route["target_floor"] = target_floor
    return route


def _summarize_router(
    root: Path,
    jobs: list[dict],
    *,
    execution_queues: dict | None = None,
    output_path: Path | None = None,
    history: list[dict] | None = None,
) -> dict:
    queued = [job for job in jobs if job.get("status") == "queued"]
    in_progress = [job for job in jobs if job.get("status") == "in_progress"]
    completed = [job for job in jobs if job.get("status") == "completed"]
    route_counts: dict[str, int] = {}
    for job in jobs:
        floor = str(job.get("target_floor") or "Smith")
        route_counts[floor] = route_counts.get(floor, 0) + 1
    next_jobs = sorted(
        queued,
        key=lambda item: (
            int(item.get("priority", 99) or 99),
            str(item.get("created_at") or ""),
            str(item.get("job_id") or ""),
        ),
    )[:5]
    recommended_actions = []
    for item in (execution_queues or {}).get("overall_active_actions") or []:
        recommended_actions.append(
            {
                "action_id": item.get("action_id"),
                "title": item.get("title"),
                "queue_id": item.get("queue_id"),
                "owner_floor": item.get("owner_floor"),
                "priority": item.get("priority"),
            }
        )
        if len(recommended_actions) >= 5:
            break
    summary = (
        f"Smith-owned canonical router tracks {len(jobs)} jobs | queued={len(queued)} | "
        f"in progress={len(in_progress)} | completed={len(completed)}"
    )
    return {
        "generated_at": utc_now_iso(),
        "router_path": str(output_path or default_smith_router_path(root)),
        "router_root": str(operations_root(root)),
        "router_root_kind": "canonical_smith_operations_root",
        "owner_floor": "Smith",
        "control_floor": "Architect",
        "job_count": len(jobs),
        "queued_count": len(queued),
        "in_progress_count": len(in_progress),
        "completed_count": len(completed),
        "route_counts": route_counts,
        "next_jobs": next_jobs,
        "recommended_actions": recommended_actions,
        "jobs": jobs,
        "history": list(history or [])[-80:],
        "summary": summary,
    }


def write_smith_router_state(root: Path, *, execution_queues: dict | None = None, output_path: Path | None = None) -> dict:
    root = Path(root)
    existing = read_smith_router_state(root, output_path=output_path)
    jobs = list(existing.get("jobs") or [])
    history = list(existing.get("history") or [])
    destination = output_path or default_smith_router_path(root)
    payload = _summarize_router(
        root,
        jobs,
        execution_queues=execution_queues,
        output_path=destination,
        history=history,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def queue_smith_job(
    root: Path,
    job_type: str,
    *,
    source_floor: str,
    workspace_id: str,
    project_id: str,
    payload: dict | None = None,
    target_floor: str | None = None,
    priority: int = 3,
    note: str = "",
    execution_queues: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    existing = read_smith_router_state(root, output_path=output_path)
    jobs = list(existing.get("jobs") or [])
    history = list(existing.get("history") or [])
    route = _route_for_job(job_type, target_floor=target_floor)
    sequence = len(jobs) + 1
    job_id = f"SR-{sequence:04d}"
    job = {
        "job_id": job_id,
        "job_type": _normalize_job_type(job_type),
        "label": route["label"],
        "queue_id": route["queue_id"],
        "source_floor": source_floor,
        "target_floor": route["target_floor"],
        "workspace_id": workspace_id,
        "project_id": project_id,
        "priority": int(priority),
        "status": "queued",
        "payload": dict(payload or {}),
        "note": note,
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "result_ref": None,
    }
    jobs.append(job)
    history.append(
        {
            "timestamp": utc_now_iso(),
            "event": "queued",
            "job_id": job_id,
            "job_type": job["job_type"],
            "target_floor": job["target_floor"],
        }
    )
    destination = output_path or default_smith_router_path(root)
    router = _summarize_router(
        root,
        jobs,
        execution_queues=execution_queues,
        output_path=destination,
        history=history,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(router, indent=2), encoding="utf-8")
    return {
        "queued": True,
        "job_id": job_id,
        "target_floor": job["target_floor"],
        "queue_id": job["queue_id"],
        "router_path": str(destination),
        "router": router,
    }


def complete_smith_job(
    root: Path,
    job_id: str,
    *,
    result_ref: str | None = None,
    note: str = "",
    execution_queues: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    existing = read_smith_router_state(root, output_path=output_path)
    jobs = list(existing.get("jobs") or [])
    history = list(existing.get("history") or [])
    updated = False
    for job in jobs:
        if str(job.get("job_id") or "") != job_id:
            continue
        job["status"] = "completed"
        job["updated_at"] = utc_now_iso()
        job["completed_at"] = utc_now_iso()
        job["result_ref"] = result_ref
        if note:
            job["completion_note"] = note
        updated = True
        history.append(
            {
                "timestamp": utc_now_iso(),
                "event": "completed",
                "job_id": job_id,
                "result_ref": result_ref,
            }
        )
        break
    destination = output_path or default_smith_router_path(root)
    router = _summarize_router(
        root,
        jobs,
        execution_queues=execution_queues,
        output_path=destination,
        history=history,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(router, indent=2), encoding="utf-8")
    return {
        "updated": updated,
        "job_id": job_id,
        "result_ref": result_ref,
        "router_path": str(destination),
        "router": router,
    }
