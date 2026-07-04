from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lightspeed_runtime.storage_paths import (
    active_generated_root,
    finalization_queue_root,
    publish_snapshot_root,
    runtime_exports_root,
)

SAFE_ZERO_BYTE_PLACEHOLDERS = {"nul", "empty.placeholder"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_closure_readiness_path(root: Path) -> Path:
    """Return the Merovingian-owned closure readiness report path."""
    return runtime_exports_root(root) / "closure_readiness.json"


def read_closure_readiness(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_closure_readiness_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _classify_outer_child(root: Path, path: Path) -> dict:
    try:
        stat = path.stat()
        size = stat.st_size if path.is_file() else None
    except Exception:
        size = None

    if path.resolve() == root.resolve():
        category = "live_application"
        action = "keep"
    elif path.name in {".claude", ".idea"}:
        category = "developer_metadata"
        action = "manual_review"
    elif path.is_file() and path.suffix.lower() == ".lnk":
        category = "launcher_shortcut"
        action = "manual_review"
    elif path.is_file() and size == 0:
        category = "zero_byte_placeholder"
        action = "safe_remove_candidate" if path.name.lower() in SAFE_ZERO_BYTE_PLACEHOLDERS else "manual_review"
    else:
        category = "outer_residual"
        action = "manual_review"

    return {
        "name": path.name,
        "path": str(path),
        "kind": "dir" if path.is_dir() else "file",
        "size": size,
        "category": category,
        "recommended_action": action,
    }


def _queue_closed(root: Path) -> bool:
    queue_path = finalization_queue_root(root) / "execution_queues.json"
    if not queue_path.exists():
        return False
    try:
        payload = json.loads(queue_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(payload.get("action_count")) and int(payload.get("pending_count", 1) or 0) == 0


def build_closure_readiness(root: Path, *, output_path: Path | None = None) -> dict:
    """Build the outer-container audit using canonical C-root inputs and snapshot destinations."""
    root = Path(root).resolve()
    outer = root.parent
    children: list[dict] = []
    try:
        for child in sorted(outer.iterdir(), key=lambda item: item.name.lower()):
            children.append(_classify_outer_child(root, child))
    except Exception:
        children = []

    app_children: list[str] = []
    try:
        app_children = sorted(child.name for child in root.iterdir())
    except Exception:
        app_children = []

    safe_remove_candidates = [
        item for item in children if item.get("recommended_action") == "safe_remove_candidate"
    ]
    manual_review = [item for item in children if item.get("recommended_action") == "manual_review"]

    return {
        "generated_at": utc_now_iso(),
        "owner_floor": "Merovingian",
        "control_floor": "Architect",
        "report_path": str(output_path or default_closure_readiness_path(root)),
        "light_speed_root": str(root),
        "source_root": str(root),
        "source_root_kind": "canonical_c_root",
        "outer_container": str(outer),
        "destination_roots": {
            "architect_publish_snapshot_root": str(publish_snapshot_root(root)),
            "merovingian_runtime_export_root": str(runtime_exports_root(root)),
        },
        "outer_child_count": len(children),
        "outer_children": children,
        "safe_remove_candidates": safe_remove_candidates,
        "manual_review_items": manual_review,
        "app_root_child_count": len(app_children),
        "app_root_children": app_children,
        "flat_generated_root_present": active_generated_root(root).exists(),
        "readiness": {
            "queue_closed": _queue_closed(root),
            "flat_generated_root_absent": not active_generated_root(root).exists(),
            "outer_safe_remove_count": len(safe_remove_candidates),
            "outer_manual_review_count": len(manual_review),
        },
        "policy": [
            "Only LightSpeed is required for the live application.",
            "Developer metadata and shortcuts are not removed automatically.",
            "Zero-byte outer placeholders may be removed when exact-match safe rules apply.",
            "Floor-owned archival roots remain inside LightSpeed until explicit archive deletion is approved.",
            "Publish destinations are snapshots; canonical C-root remains the source of truth.",
        ],
    }


def write_closure_readiness(root: Path, output_path: Path | None = None) -> dict:
    destination = output_path or default_closure_readiness_path(root)
    payload = build_closure_readiness(root, output_path=destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def remove_outer_zero_byte_placeholders(root: Path, output_path: Path | None = None) -> dict:
    root = Path(root).resolve()
    before = build_closure_readiness(root, output_path=output_path)
    removed: list[str] = []
    failed: list[dict] = []
    for item in before.get("safe_remove_candidates", []):
        path = Path(item.get("path", ""))
        try:
            if path.parent != root.parent:
                continue
            if path.name.lower() not in SAFE_ZERO_BYTE_PLACEHOLDERS:
                continue
            if not path.is_file() or path.stat().st_size != 0:
                continue
            path.unlink()
            removed.append(str(path))
        except Exception as exc:
            failed.append({"path": str(path), "error": str(exc)})

    after = write_closure_readiness(root, output_path=output_path)
    return {
        "removed": removed,
        "failed": failed,
        "before": before,
        "after": after,
        "report_path": after.get("report_path"),
    }
