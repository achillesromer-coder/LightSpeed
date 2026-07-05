from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lightspeed_runtime.storage_paths import finalization_queue_root, publish_snapshot_root, runtime_exports_root


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_finalization_overview_path(root: Path) -> Path:
    return runtime_exports_root(root) / "finalization_overview.json"


def default_execution_control_path(root: Path) -> Path:
    return finalization_queue_root(root) / "execution_control.json"


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _short_action(action: dict) -> dict:
    return {
        "action_id": action.get("action_id"),
        "title": action.get("title"),
        "queue_id": action.get("queue_id"),
        "owner_floor": action.get("owner_floor"),
        "priority": action.get("priority"),
        "status": action.get("status", "pending"),
        "target_paths": action.get("target_paths", []),
        "summary": action.get("summary", ""),
    }


def read_finalization_overview(root: Path, output_path: Path | None = None) -> dict:
    return _read_json(output_path or default_finalization_overview_path(root))


def read_execution_control(root: Path, output_path: Path | None = None) -> dict:
    return _read_json(output_path or default_execution_control_path(root))


def build_finalization_overview(
    root: Path,
    *,
    execution_queues: dict | None = None,
    cleanup_report: dict | None = None,
    cleanup_candidates: dict | None = None,
    assimilation: dict | None = None,
    generated_layout_audit: dict | None = None,
    dataindex_reduction: dict | None = None,
    workflow_state: dict | None = None,
    smith_router: dict | None = None,
    closure_readiness: dict | None = None,
    activity_tables: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    execution_queues = execution_queues or {}
    cleanup_report = cleanup_report or {}
    cleanup_candidates = cleanup_candidates or {}
    assimilation = assimilation or {}
    generated_layout_audit = generated_layout_audit or {}
    dataindex_reduction = dataindex_reduction or {}
    workflow_state = workflow_state or {}
    smith_router = smith_router or {}
    closure_readiness = closure_readiness or {}
    activity_tables = activity_tables or {}

    legacy_audit = cleanup_report.get("legacy_audit") or {}
    legacy_diff = cleanup_report.get("legacy_diff") or {}
    legacy_roots = assimilation.get("legacy_roots") or {}
    cleanup_legacy_root_names = {"data_generated", "root_w6", "root_operations_w6"}
    archival_legacy_root_names = {
        "smith_legacy",
        "smith_legacy_w6_data",
        "smith_legacy_operations_w6_data",
        "merovingian_legacy_runtime_bundle",
    }
    cleanup_legacy_shells_present = [
        name
        for name, payload in legacy_roots.items()
        if name in cleanup_legacy_root_names and isinstance(payload, dict) and payload.get("present")
    ]
    archival_legacy_roots_present = [
        name
        for name, payload in legacy_roots.items()
        if name in archival_legacy_root_names and isinstance(payload, dict) and payload.get("present")
    ]
    top_actions = [_short_action(item) for item in (execution_queues.get("overall_active_actions") or [])[:8]]
    queue_completion = {
        (item.get("queue_id") or "unknown"): {
            "title": item.get("title"),
            "completed_count": item.get("completed_count", 0),
            "pending_count": item.get("pending_count", 0),
            "completion_ratio": item.get("completion_ratio", 0),
        }
        for item in execution_queues.get("queues", [])
    }

    operator_findings: list[str] = []
    if cleanup_legacy_shells_present:
        operator_findings.append("Flat/root legacy shells remain present; keep cleanup gated by rehome/audit reports.")
    else:
        operator_findings.append("Flat/root legacy shells are not active in the assimilation report.")
    if dataindex_reduction.get("moved_count", 0):
        operator_findings.append("Dataindex superseded/generated files have been rehomed under Merovingian reports.")
    if cleanup_candidates.get("empty_file_count", 0) or cleanup_candidates.get("empty_directory_count", 0):
        operator_findings.append("Empty files or directories remain candidates for a later targeted cleanup pass.")
    if top_actions:
        operator_findings.append(f"Next governed action is {top_actions[0].get('action_id')}: {top_actions[0].get('title')}.")

    return {
        "generated_at": utc_now_iso(),
        "owner_floor": "Merovingian",
        "control_floor": "Architect",
        "report_path": str(output_path or default_finalization_overview_path(root)),
        "source_root": str(root.resolve()),
        "source_root_kind": "canonical_c_root",
        "destination_roots": {
            "architect_finalization_queue_root": str(finalization_queue_root(root)),
            "architect_publish_snapshot_root": str(publish_snapshot_root(root)),
            "merovingian_runtime_export_root": str(runtime_exports_root(root)),
        },
        "purpose": "Consolidated operator-facing finalization overview for cleanup, assimilation, queue, snapshot, and workflow state.",
        "status": {
            "completed_actions": execution_queues.get("completed_count", 0),
            "pending_actions": execution_queues.get("pending_count", 0),
            "total_actions": execution_queues.get("action_count", 0),
            "safe_cache_targets": len(cleanup_report.get("safe_remove_candidates", [])),
            "empty_files": cleanup_candidates.get("empty_file_count", 0),
            "empty_directories": cleanup_candidates.get("empty_directory_count", 0),
            "legacy_code_references": legacy_audit.get("active_code_reference_count", 0),
            "legacy_runtime_diffs": legacy_diff.get("different_file_count", 0),
            "legacy_shells_present": cleanup_legacy_shells_present,
            "archival_legacy_roots_present": archival_legacy_roots_present,
            "dataindex_moved_count": dataindex_reduction.get("moved_count", 0),
            "workflow_count": workflow_state.get("workflow_count", 0),
            "resumable_workflows": workflow_state.get("resumable_count", 0),
            "smith_queued_jobs": smith_router.get("queued_count", 0),
            "outer_safe_remove_count": len(closure_readiness.get("safe_remove_candidates", []) or []),
            "outer_manual_review_count": len(closure_readiness.get("manual_review_items", []) or []),
            "flat_generated_root_present": bool(closure_readiness.get("flat_generated_root_present")),
            "activity_owner_floor": activity_tables.get("owner_floor", "Merovingian"),
            "activity_control_floor": activity_tables.get("control_floor", "Architect"),
            "activity_table_rows": (activity_tables.get("summary") or {}).get("table_rows", 0),
            "activity_source_events": (activity_tables.get("summary") or {}).get("total_source_events", 0),
            "legacy_operations_can_be_declassified": bool(
                generated_layout_audit.get("legacy_operations_can_be_declassified")
            ),
        },
        "queue_completion": queue_completion,
        "next_actions": top_actions,
        "operator_findings": operator_findings,
        "source_reports": {
            "execution_queues": execution_queues.get("queue_path"),
            "cleanup_report": cleanup_report.get("report_path"),
            "cleanup_candidates": cleanup_candidates.get("report_path"),
            "assimilation": assimilation.get("report_path"),
            "generated_layout_audit": generated_layout_audit.get("report_path"),
            "dataindex_reduction": dataindex_reduction.get("report_path"),
            "workflow_state": workflow_state.get("workflow_state_path"),
            "smith_router": smith_router.get("router_path"),
            "closure_readiness": closure_readiness.get("report_path"),
            "activity_tables": activity_tables.get("table_path"),
        },
        "reduction_policy": [
            "Use this overview as the operator-facing finalization status instead of opening scattered report files first.",
            "Run destructive cleanup only from explicit targeted actions after source reports confirm replacement or declassification.",
            "Keep raw reservoirs secondary to Oracle catalog and provenance views.",
            "Treat Architect execution control as the canonical next-action source of truth.",
            "Treat publish outputs as snapshot destinations, not source truth.",
        ],
    }


def write_finalization_overview(root: Path, output_path: Path | None = None, **kwargs: dict) -> dict:
    destination = output_path or default_finalization_overview_path(root)
    payload = build_finalization_overview(root, output_path=destination, **kwargs)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_execution_control(
    root: Path,
    *,
    execution_queues: dict | None = None,
    finalization_overview: dict | None = None,
    workflow_state: dict | None = None,
    output_path: Path | None = None,
) -> dict:
    root = Path(root)
    execution_queues = execution_queues or {}
    finalization_overview = finalization_overview or {}
    workflow_state = workflow_state or {}
    queues = execution_queues.get("queues") or []
    active_actions = [_short_action(item) for item in (execution_queues.get("overall_active_actions") or [])]
    lanes = []
    for queue in queues:
        lanes.append(
            {
                "queue_id": queue.get("queue_id"),
                "title": queue.get("title"),
                "owner_floor": queue.get("owner_floor"),
                "support_floor": queue.get("support_floor"),
                "pending_count": queue.get("pending_count", 0),
                "completed_count": queue.get("completed_count", 0),
                "completion_ratio": queue.get("completion_ratio", 0),
                "active_top_five": [_short_action(item) for item in queue.get("active_top_five", [])],
            }
        )

    return {
        "generated_at": utc_now_iso(),
        "owner_floor": "Architect",
        "report_path": str(output_path or default_execution_control_path(root)),
        "queue_root": str(finalization_queue_root(root)),
        "queue_root_kind": "canonical_architect_finalization_root",
        "publish_snapshot_root": str(publish_snapshot_root(root)),
        "publish_snapshot_root_kind": "architect_snapshot_destination",
        "overview_path": finalization_overview.get("report_path"),
        "purpose": "Architect-owned execution control for the remaining LightSpeed finalization queue and snapshot publish destinations.",
        "completion": {
            "completed_actions": execution_queues.get("completed_count", 0),
            "pending_actions": execution_queues.get("pending_count", 0),
            "total_actions": execution_queues.get("action_count", 0),
            "completion_ratio": round(
                (execution_queues.get("completed_count", 0) or 0) / max(execution_queues.get("action_count", 0) or 1, 1),
                4,
            ),
        },
        "lanes": lanes,
        "next_actions": active_actions[:10],
        "workflow_controls": {
            "workflow_count": workflow_state.get("workflow_count", 0),
            "resumable_count": workflow_state.get("resumable_count", 0),
            "resume_policy": "Resume through Smith job state; approve write/execute/publish work through Architect; write publishes to snapshot destinations only.",
        },
        "operator_controls": [
            {"label": "Refresh State", "kind": "read", "risk": "read"},
            {"label": "Build Finalization Overview", "kind": "write_report", "risk": "curate"},
            {"label": "Build Execution Control", "kind": "write_report", "risk": "curate"},
            {"label": "Advance Queue", "kind": "queue_update", "risk": "write", "approval_boundary": "validation-backed"},
            {"label": "Remove Caches", "kind": "cleanup", "risk": "write", "approval_boundary": "targeted_safe_cache_only"},
        ],
        "gates": [
            "Run targeted runtime tests after each queue window.",
            "Run shell smoke after UI/runtime entrypoint changes.",
            "Do not delete raw reservoirs or archive roots from this control surface.",
            "Keep final UX polish after queue and ownership state are stable.",
        ],
    }


def write_execution_control(root: Path, output_path: Path | None = None, **kwargs: dict) -> dict:
    destination = output_path or default_execution_control_path(root)
    payload = build_execution_control(root, output_path=destination, **kwargs)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
