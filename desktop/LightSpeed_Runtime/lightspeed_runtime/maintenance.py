from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
from typing import Any, Iterator

from lightspeed_runtime.operational_store import (
    OperationalStore,
    default_operational_db_path,
)
from lightspeed_runtime.weekly_log import append_weekly_log, weekly_bucket


class MaintenanceWindowClosed(RuntimeError):
    """Raised when automatic maintenance is requested outside its window."""


PROTECTED_EXTENSIONS = frozenset(
    {
        ".arrow",
        ".bin",
        ".db",
        ".feather",
        ".fits",
        ".fit",
        ".fts",
        ".gguf",
        ".h5",
        ".hdf5",
        ".nc",
        ".onnx",
        ".parquet",
        ".pt",
        ".pth",
        ".safetensors",
        ".sqlite",
        ".sqlite3",
        ".tif",
        ".tiff",
        ".xls",
        ".xlsm",
        ".xlsx",
    }
)
PROTECTED_SOURCE_EXTENSIONS = frozenset(
    {
        ".c",
        ".cfg",
        ".cpp",
        ".css",
        ".go",
        ".h",
        ".html",
        ".ini",
        ".java",
        ".js",
        ".jsx",
        ".md",
        ".ps1",
        ".py",
        ".rs",
        ".sh",
        ".toml",
        ".ts",
        ".tsx",
        ".yaml",
        ".yml",
    }
)
PROTECTED_PART_MARKERS = frozenset(
    {
        ".git",
        "_migration",
        "archive",
        "archives",
        "dataset",
        "datasets",
        "empirical",
        "model",
        "models",
        "reservoir",
        "reservoirs",
        "source",
        "sources",
        "vault",
        "vaults",
        "venv",
    }
)
LEGACY_STREAM_NAMES = frozenset(
    {
        "action_ledger.jsonl",
        "approval_ledger.jsonl",
        "otel_spans.jsonl",
    }
)
Z_DIRECT_STREAM_NAMES = frozenset(
    {
        "events.jsonl",
        "objects.jsonl",
        "inbox.jsonl",
        "outbox.jsonl",
    }
)


def _is_reparse_point(path: Path) -> bool:
    try:
        info = path.stat(follow_symlinks=False)
    except OSError:
        return True
    attributes = getattr(info, "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _walk_files(root: Path) -> Iterator[Path]:
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept_directories: list[str] = []
        for directory in directories:
            candidate = current_path / directory
            normalized = directory.strip().lower()
            if normalized in PROTECTED_PART_MARKERS:
                continue
            if _is_reparse_point(candidate):
                continue
            kept_directories.append(directory)
        directories[:] = kept_directories
        for filename in files:
            candidate = current_path / filename
            if candidate.is_symlink() or _is_reparse_point(candidate):
                continue
            yield candidate


def _normalized_parts(path: Path) -> tuple[str, ...]:
    return tuple(part.strip().lower() for part in path.parts)


def classify_candidate(relative_path: Path) -> str | None:
    parts = _normalized_parts(relative_path)
    suffix = relative_path.suffix.lower()
    name = relative_path.name.lower()
    if suffix in PROTECTED_EXTENSIONS or suffix in PROTECTED_SOURCE_EXTENSIONS:
        return None
    if any(part in PROTECTED_PART_MARKERS for part in parts):
        return None
    if (
        len(parts) == 2
        and parts[0] == "reports"
        and name.startswith("run_")
        and suffix == ".json"
    ):
        return "timestamped_generated_report"
    if name in LEGACY_STREAM_NAMES:
        return "superseded_operational_stream"
    if name in Z_DIRECT_STREAM_NAMES and "z direct" in parts:
        return "superseded_z_direct_stream"
    if (
        "temp_shells" in parts
        and "outputs" in parts
        and (name.startswith("local_floor_runner_receipt_") or name.startswith("wake_packet_"))
        and suffix in {".json", ".jsonl", ".txt"}
    ):
        return "superseded_temporary_receipt"
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _consolidation_root(runtime_root: Path) -> Path:
    runtime_root = runtime_root.resolve()
    for candidate in (runtime_root, *runtime_root.parents):
        if candidate.name.lower() == "lightspeed_consolidated":
            return candidate
    return runtime_root


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    temporary.replace(path)


def _checkpoint_operational_store(root: Path) -> dict[str, Any]:
    path = default_operational_db_path(root)
    OperationalStore(path)
    with sqlite3.connect(path, timeout=30) as connection:
        checkpoint = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        connection.execute("PRAGMA optimize")
    return {
        "path": str(path),
        "wal_checkpoint": list(checkpoint or ()),
        "optimized": True,
    }


def _quarantine_destination(
    quarantine_root: Path,
    relative_path: Path,
    digest: str,
) -> Path:
    destination = quarantine_root / relative_path
    if not destination.exists():
        return destination
    try:
        if _sha256(destination) == digest:
            return destination
    except OSError:
        pass
    return destination.with_name(
        f"{destination.stem}_{digest[:12]}{destination.suffix}"
    )


def _prune_verified_quarantines(
    parent: Path,
    *,
    current_label: str,
    retain: int = 4,
) -> list[str]:
    if not parent.exists():
        return []
    directories = sorted(
        (
            item
            for item in parent.iterdir()
            if item.is_dir() and item.name != current_label
        ),
        key=lambda item: item.name,
        reverse=True,
    )
    removed: list[str] = []
    for candidate in directories[max(0, retain - 1) :]:
        manifest_path = candidate / "manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        entries = manifest.get("entries")
        if not isinstance(entries, list) or not entries:
            continue
        if not all(entry.get("second_copy_verified") is True for entry in entries):
            continue
        shutil.rmtree(candidate)
        removed.append(str(candidate))
    return removed


def run_maintenance(
    root: Path,
    *,
    now: datetime | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    runtime_root = Path(root).resolve()
    stamp = now or datetime.now().astimezone()
    if not force and (stamp.weekday() != 4 or stamp.hour < 19):
        raise MaintenanceWindowClosed(
            "weekly maintenance requires Friday at or after 19:00 local time"
        )
    if not runtime_root.exists():
        raise FileNotFoundError(runtime_root)

    candidates: list[dict[str, Any]] = []
    for path in _walk_files(runtime_root):
        try:
            relative = path.resolve().relative_to(runtime_root)
        except (OSError, ValueError):
            continue
        classification = classify_candidate(relative)
        if classification is None:
            continue
        candidates.append(
            {
                "source": path,
                "source_relative": relative,
                "classification": classification,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )

    bucket = weekly_bucket(stamp)
    label = str(bucket["label"])
    quarantine_parent = (
        _consolidation_root(runtime_root)
        / "_migration"
        / "weekly_quarantine"
    )
    quarantine_root = quarantine_parent / label
    if dry_run:
        return {
            "status": "dry_run",
            "week": label,
            "candidate_count": len(candidates),
            "quarantined": 0,
            "manifest_path": None,
            "candidates": [
                {
                    key: str(value) if isinstance(value, Path) else value
                    for key, value in record.items()
                }
                for record in candidates
            ],
        }

    entries: list[dict[str, Any]] = []
    for candidate in candidates:
        source = candidate["source"]
        relative = candidate["source_relative"]
        destination = _quarantine_destination(
            quarantine_root,
            relative,
            candidate["sha256"],
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and _sha256(destination) == candidate["sha256"]:
            source.unlink()
        else:
            source.replace(destination)
        entries.append(
            {
                "source_relative": relative.as_posix(),
                "quarantine_path": str(destination),
                "classification": candidate["classification"],
                "bytes": candidate["bytes"],
                "sha256": candidate["sha256"],
                "second_copy_verified": False,
            }
        )

    database = _checkpoint_operational_store(runtime_root)
    manifest_path = quarantine_root / "manifest.json"
    manifest = {
        "schema_version": "lightspeed-weekly-quarantine-v1",
        "generated_at": stamp.isoformat(),
        "runtime_root": str(runtime_root),
        "week": label,
        "entry_count": len(entries),
        "entries": entries,
        "database_maintenance": database,
    }
    _atomic_json(manifest_path, manifest)
    removed_quarantines = _prune_verified_quarantines(
        quarantine_parent,
        current_label=label,
    )
    append_weekly_log(
        runtime_root,
        category="maintenance_complete",
        message=f"Weekly maintenance quarantined {len(entries)} generated files.",
        source="Merovingian",
        payload={
            "manifest_path": str(manifest_path),
            "quarantined": len(entries),
            "removed_verified_quarantines": removed_quarantines,
        },
        timestamp=stamp,
    )
    return {
        "status": "complete",
        "week": label,
        "candidate_count": len(candidates),
        "quarantined": len(entries),
        "manifest_path": manifest_path,
        "database_maintenance": database,
        "removed_verified_quarantines": removed_quarantines,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run bounded LightSpeed weekly maintenance."
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = run_maintenance(
        args.root,
        force=args.force,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
