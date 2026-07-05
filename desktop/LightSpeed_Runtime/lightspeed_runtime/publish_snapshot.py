from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from lightspeed_runtime.storage_paths import publish_snapshot_root


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_root(root: Path) -> Path:
    return Path(root).resolve()


def default_publish_snapshot_destination(root: Path) -> Path:
    return publish_snapshot_root(normalize_root(root))


def normalize_destination(root: Path, destination_root: Path) -> Path:
    root = normalize_root(root)
    destination = Path(destination_root).resolve()
    if destination == root:
        raise ValueError("Publish snapshot destination cannot be the live source root.")
    try:
        destination.relative_to(root)
    except ValueError:
        return destination
    raise ValueError(f"Publish snapshot destination is inside the live source root: {destination}")


def build_publish_snapshot_plan(root: Path, destination_root: Path | None = None) -> Dict[str, Any]:
    """
    Build an overwrite-only publish snapshot plan.

    The live C-root source remains untouched. This planner only validates and
    describes the destination so release tooling can act later.
    """
    root = normalize_root(root)
    destination = normalize_destination(root, destination_root or default_publish_snapshot_destination(root))

    destination_drive = getattr(destination, "drive", "")
    source_drive = getattr(root, "drive", "")
    different_drive = bool(destination_drive and source_drive and destination_drive.lower() != source_drive.lower())

    return {
        "generated_at": utc_now_iso(),
        "source_root": str(root),
        "destination_root": str(destination),
        "overwrite_only": True,
        "preserves_source_root": True,
        "source_policy": "c_root_live",
        "destination_policy": "d_root_snapshot" if different_drive else "external_snapshot",
        "safe_destination": True,
        "refuses_live_source_overwrite": True,
        "summary": "Overwrite-only publish snapshot plan; source root remains read-only live state.",
        "destination_exists": destination.exists(),
    }
