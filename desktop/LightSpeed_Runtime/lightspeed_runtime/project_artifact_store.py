from __future__ import annotations

from datetime import UTC, datetime
import fnmatch
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Iterable

from lightspeed_runtime.project_pipeline import ProjectPipeline

ARTIFACT_SCHEMA = "lightspeed-project-artifact-manifest-v1"
DEFAULT_BLOCKED_PATTERNS = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa*",
    "credentials*.json",
    "token*.json",
    "*.p12",
    "*.pfx",
)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _slug(value: str) -> str:
    output = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
    while "--" in output:
        output = output.replace("--", "-")
    return output[:80] or "project"


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _project_record(pipeline: ProjectPipeline, project_id: str) -> dict[str, Any]:
    registry = pipeline.refresh(force=True, queue_changes=False)
    for record in registry.get("projects") or []:
        if isinstance(record, dict) and str(record.get("project_id")) == project_id:
            return record
    raise KeyError(project_id)


def _limits(pipeline: ProjectPipeline) -> tuple[int, int, int, tuple[str, ...]]:
    config = pipeline.config.get("drive_writeback") or {}
    blocked = tuple(str(item) for item in config.get("blocked_artifact_patterns") or DEFAULT_BLOCKED_PATTERNS)
    return (
        max(1, min(int(config.get("max_artifact_files") or 50), 500)),
        max(1, int(config.get("max_artifact_total_bytes") or 268_435_456)),
        max(1, int(config.get("max_single_artifact_bytes") or 134_217_728)),
        blocked,
    )


def stage_project_artifacts(
    pipeline: ProjectPipeline,
    *,
    project_id: str,
    artifact_paths: Iterable[str],
) -> dict[str, Any]:
    """Copy explicitly named project files into an immutable Drive review folder.

    Only files resolving inside the registered project root are eligible. Source
    files are never modified or removed. Secret-like file patterns, directories,
    missing paths and files over configured limits are skipped with evidence.
    """

    project = _project_record(pipeline, project_id)
    project_root = Path(str(project.get("path") or "")).resolve()
    if not project_root.is_dir():
        raise FileNotFoundError(f"Registered project root is unavailable: {project_root}")

    max_files, max_total, max_single, blocked_patterns = _limits(pipeline)
    requested = [str(value).strip() for value in artifact_paths if str(value).strip()]
    if len(requested) > max_files:
        raise ValueError(f"Artifact request exceeds the {max_files}-file limit")

    drive_root, drive_mode = pipeline.resolve_drive_receipt_root()
    created = _utc_now_iso()
    seed = f"{project_id}|{created}|{'|'.join(requested)}"
    staging_id = f"LSGO-STAGE-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16].upper()}"
    stage_root = drive_root / "Project Reviews" / _slug(project_id) / staging_id
    artifact_root = stage_root / "artifacts"

    copied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    total_bytes = 0
    seen_sources: set[str] = set()

    for requested_path in requested:
        candidate = Path(requested_path)
        source = candidate if candidate.is_absolute() else project_root / candidate
        try:
            source = source.resolve(strict=True)
        except OSError:
            skipped.append({"requested_path": requested_path, "reason": "missing_or_unreadable"})
            continue

        source_key = str(source).casefold()
        if source_key in seen_sources:
            skipped.append({"requested_path": requested_path, "reason": "duplicate_request"})
            continue
        seen_sources.add(source_key)

        if not _inside(source, project_root):
            skipped.append({"requested_path": requested_path, "reason": "outside_registered_project_root"})
            continue
        if not source.is_file():
            skipped.append({"requested_path": requested_path, "reason": "not_a_file"})
            continue

        relative = source.relative_to(project_root)
        relative_text = relative.as_posix()
        if any(part in {".git", ".venv", "venv", "node_modules", "__pycache__"} for part in relative.parts):
            skipped.append({"requested_path": requested_path, "reason": "ignored_runtime_or_dependency_path"})
            continue
        if any(fnmatch.fnmatch(source.name, pattern) or fnmatch.fnmatch(relative_text, pattern) for pattern in blocked_patterns):
            skipped.append({"requested_path": requested_path, "reason": "blocked_secret_or_credential_pattern"})
            continue

        size = source.stat().st_size
        if size > max_single:
            skipped.append({"requested_path": requested_path, "reason": "single_file_limit", "size_bytes": size})
            continue
        if total_bytes + size > max_total:
            skipped.append({"requested_path": requested_path, "reason": "total_size_limit", "size_bytes": size})
            continue

        checksum = _sha256(source)
        destination = artifact_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            existing_checksum = _sha256(destination)
            if existing_checksum != checksum:
                raise FileExistsError(f"Immutable artifact destination already exists with different content: {destination}")
        else:
            shutil.copy2(source, destination)
        copied.append(
            {
                "requested_path": requested_path,
                "project_relative_path": relative_text,
                "source_path": str(source),
                "destination_path": str(destination),
                "size_bytes": size,
                "sha256": checksum,
                "copy_mode": "immutable_review_copy",
            }
        )
        total_bytes += size

    manifest = {
        "schema_version": ARTIFACT_SCHEMA,
        "staging_id": staging_id,
        "created_utc": created,
        "project_id": project_id,
        "project_name": project.get("name"),
        "project_authority": project.get("authority"),
        "project_root": str(project_root),
        "drive_writeback_mode": drive_mode,
        "stage_root": str(stage_root),
        "source_mutated": False,
        "automatic_deletion": False,
        "limits": {
            "max_files": max_files,
            "max_total_bytes": max_total,
            "max_single_artifact_bytes": max_single,
        },
        "requested_count": len(requested),
        "copied_count": len(copied),
        "skipped_count": len(skipped),
        "copied_total_bytes": total_bytes,
        "copied": copied,
        "skipped": skipped,
        "status": "pass" if copied or not requested else "review_required",
    }
    manifest_path = stage_root / "artifact_manifest.json"
    _write_json(manifest_path, manifest)
    return {**manifest, "manifest_path": str(manifest_path)}
