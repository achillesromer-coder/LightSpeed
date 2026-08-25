from __future__ import annotations

from datetime import UTC, datetime
import fnmatch
import mimetypes
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from lightspeed_runtime.project_artifact_store import DEFAULT_BLOCKED_PATTERNS
from lightspeed_runtime.project_pipeline import ProjectPipeline, ProjectRoot


LIST_SCHEMA = "lightspeed-project-files-v1"
OPEN_SCHEMA = "lightspeed-project-file-open-result-v1"
DEFAULT_IGNORED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}
DEFAULT_IGNORED_FILES = {".DS_Store", "Thumbs.db"}
TEXT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cfg",
    ".conf",
    ".cpp",
    ".css",
    ".csv",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsonl",
    ".jsx",
    ".log",
    ".md",
    ".mjs",
    ".py",
    ".rst",
    ".rs",
    ".scss",
    ".sh",
    ".sql",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
MAX_LIST_FILES = 500
MAX_SCAN_FILES = 5_000
MAX_PREVIEW_BYTES = 64 * 1024


class ProjectFileNotFound(LookupError):
    pass


class ProjectFilePathRejected(ValueError):
    pass


class ProjectFileBlocked(PermissionError):
    pass


class ProjectFileUnavailable(OSError):
    pass


def _normal_absolute(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _scan_policy(pipeline: ProjectPipeline) -> dict[str, Any]:
    value = pipeline.config.get("scan_policy")
    return value if isinstance(value, dict) else {}


def _browser_policy(pipeline: ProjectPipeline) -> dict[str, Any]:
    value = pipeline.config.get("project_file_browser")
    return value if isinstance(value, dict) else {}


def _blocked_patterns(pipeline: ProjectPipeline) -> tuple[str, ...]:
    writeback = pipeline.config.get("drive_writeback")
    writeback = writeback if isinstance(writeback, dict) else {}
    configured = writeback.get("blocked_artifact_patterns")
    values = configured if isinstance(configured, list) else DEFAULT_BLOCKED_PATTERNS
    return tuple(str(item).casefold() for item in values if str(item).strip())


def _is_blocked(relative_path: str, patterns: tuple[str, ...]) -> bool:
    folded_path = relative_path.casefold()
    folded_name = PurePosixPath(relative_path).name.casefold()
    return any(
        fnmatch.fnmatchcase(folded_path, pattern)
        or fnmatch.fnmatchcase(folded_name, pattern)
        for pattern in patterns
    )


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _authorised_project(
    pipeline: ProjectPipeline,
    project_id: str,
) -> tuple[dict[str, Any], Path]:
    # scan_projects is read-only. It re-establishes the project identity from
    # configured roots instead of trusting a stale/tampered runtime receipt.
    registry = pipeline.scan_projects()
    project = next(
        (
            item
            for item in registry.get("projects") or []
            if isinstance(item, dict) and str(item.get("project_id") or "") == project_id
        ),
        None,
    )
    if project is None:
        raise ProjectFileNotFound("Registered project not found")

    root_id = str(project.get("root_id") or "")
    authority_root: ProjectRoot | None = next(
        (item for item in pipeline.project_roots() if item.root_id == root_id),
        None,
    )
    record_path = Path(str(project.get("path") or ""))
    if authority_root is None or _normal_absolute(record_path.parent) != _normal_absolute(
        authority_root.path
    ):
        raise ProjectFileUnavailable("Registered project authority could not be re-established")
    if record_path.is_symlink():
        raise ProjectFileUnavailable("Symlinked project roots are not eligible for browsing")
    try:
        resolved_authority_root = authority_root.path.resolve(strict=True)
        resolved_root = record_path.resolve(strict=True)
    except OSError as exc:
        raise ProjectFileUnavailable("Registered project root is unavailable") from exc
    if resolved_root.parent != resolved_authority_root or not resolved_root.is_dir():
        raise ProjectFileUnavailable("Registered project root is unavailable")
    return project, resolved_root


def _validated_relative_path(value: str) -> PurePosixPath:
    text = str(value or "").strip().replace("\\", "/")
    if not text or len(text) > 1000 or "\x00" in text:
        raise ProjectFilePathRejected("A bounded project-relative file path is required")
    posix_path = PurePosixPath(text)
    windows_path = PureWindowsPath(text)
    if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise ProjectFilePathRejected("Absolute filesystem paths are not accepted")
    if any(part in {"", ".", ".."} or ":" in part for part in posix_path.parts):
        raise ProjectFilePathRejected("Traversal and alternate filesystem paths are not accepted")
    return posix_path


def _file_kind(path: Path, mime_type: str) -> str:
    if mime_type.startswith("text/") or path.suffix.casefold() in TEXT_EXTENSIONS:
        return "text"
    return "binary_or_unknown"


def _file_record(path: Path, *, relative_path: str) -> dict[str, Any]:
    stat = path.stat()
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    kind = _file_kind(path, mime_type)
    return {
        "relative_path": relative_path,
        "name": path.name,
        "extension": path.suffix.casefold(),
        "mime_type": mime_type,
        "kind": kind,
        "size_bytes": int(stat.st_size),
        "modified_utc": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(
            timespec="seconds"
        ),
        "preview_supported": kind == "text",
    }


def list_project_files(
    pipeline: ProjectPipeline,
    *,
    project_id: str,
    limit: int = 200,
) -> dict[str, Any]:
    project, project_root = _authorised_project(pipeline, project_id)
    bounded_limit = max(1, min(int(limit), MAX_LIST_FILES))
    policy = _scan_policy(pipeline)
    browser_policy = _browser_policy(pipeline)
    ignored_directories = DEFAULT_IGNORED_DIRECTORIES | {
        str(item) for item in policy.get("ignored_directories") or []
    }
    ignored_files = DEFAULT_IGNORED_FILES | {
        str(item) for item in policy.get("ignored_files") or []
    }
    max_scan_files = max(
        bounded_limit,
        min(int(browser_policy.get("max_scan_files") or MAX_SCAN_FILES), 50_000),
    )
    blocked_patterns = _blocked_patterns(pipeline)
    files: list[dict[str, Any]] = []
    blocked_count = 0
    skipped_count = 0
    scanned_count = 0
    scan_truncated = False

    for current, directories, filenames in os.walk(project_root, followlinks=False):
        current_path = Path(current)
        safe_directories: list[str] = []
        for name in sorted(directories, key=str.casefold):
            if name in ignored_directories:
                continue
            try:
                resolved = (current_path / name).resolve(strict=True)
            except OSError:
                skipped_count += 1
                continue
            if _inside(resolved, project_root):
                safe_directories.append(name)
            else:
                skipped_count += 1
        directories[:] = safe_directories

        for filename in sorted(filenames, key=str.casefold):
            if filename in ignored_files:
                continue
            if scanned_count >= max_scan_files:
                scan_truncated = True
                directories[:] = []
                break
            scanned_count += 1
            lexical_path = current_path / filename
            try:
                relative_path = lexical_path.relative_to(project_root).as_posix()
                resolved_path = lexical_path.resolve(strict=True)
            except (OSError, ValueError):
                skipped_count += 1
                continue
            if not _inside(resolved_path, project_root) or not resolved_path.is_file():
                skipped_count += 1
                continue
            if _is_blocked(relative_path, blocked_patterns):
                blocked_count += 1
                continue
            if len(files) >= bounded_limit:
                scan_truncated = True
                directories[:] = []
                break
            try:
                files.append(_file_record(resolved_path, relative_path=relative_path))
            except OSError:
                skipped_count += 1
        if scan_truncated:
            break

    state = "available"
    if not files:
        state = "restricted" if blocked_count else "empty"
    return {
        "schema_version": LIST_SCHEMA,
        "state": state,
        "project": {
            "project_id": project_id,
            "name": project.get("name"),
            "authority": project.get("authority"),
            "condition": project.get("condition"),
        },
        "files": files,
        "summary": {
            "visible_file_count": len(files),
            "blocked_file_count": blocked_count,
            "skipped_file_count": skipped_count,
            "scanned_file_count": scanned_count,
            "scan_truncated": scan_truncated,
            "limit": bounded_limit,
        },
        "boundary": (
            "Read-only project-relative metadata; dependency trees, runtime caches, "
            "credential-like files, and paths outside the registered project are withheld."
        ),
    }


def open_project_file(
    pipeline: ProjectPipeline,
    *,
    project_id: str,
    relative_path: str,
) -> dict[str, Any]:
    project, project_root = _authorised_project(pipeline, project_id)
    requested = _validated_relative_path(relative_path)
    requested_text = requested.as_posix()
    if _is_blocked(requested_text, _blocked_patterns(pipeline)):
        raise ProjectFileBlocked("Credential-like project files cannot be opened in LS GO")

    ignored_directories = DEFAULT_IGNORED_DIRECTORIES | {
        str(item) for item in _scan_policy(pipeline).get("ignored_directories") or []
    }
    if any(part in ignored_directories for part in requested.parts[:-1]):
        raise ProjectFileBlocked("Runtime, dependency, and repository internals are withheld")

    candidate = project_root.joinpath(*requested.parts)
    try:
        resolved_path = candidate.resolve(strict=True)
    except OSError as exc:
        raise ProjectFileNotFound("Project file not found") from exc
    if not _inside(resolved_path, project_root):
        raise ProjectFilePathRejected("Resolved file is outside the registered project root")
    if not resolved_path.is_file():
        raise ProjectFilePathRejected("Requested project path is not a file")

    try:
        file_record = _file_record(resolved_path, relative_path=requested_text)
    except OSError as exc:
        raise ProjectFileUnavailable("Project file metadata is unavailable") from exc
    preview: dict[str, Any] = {
        "state": "metadata_only",
        "encoding": None,
        "truncated": False,
        "text": None,
    }
    if file_record["kind"] == "text":
        try:
            with resolved_path.open("rb") as stream:
                content = stream.read(MAX_PREVIEW_BYTES + 1)
        except OSError as exc:
            raise ProjectFileUnavailable("Project file preview is unavailable") from exc
        truncated = len(content) > MAX_PREVIEW_BYTES
        content = content[:MAX_PREVIEW_BYTES]
        try:
            text = content.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            preview["state"] = "metadata_only_non_utf8"
        else:
            preview = {
                "state": "empty" if not text else "available",
                "encoding": "utf-8",
                "truncated": truncated,
                "text": text,
            }

    return {
        "schema_version": OPEN_SCHEMA,
        "state": "opened_read_only",
        "project": {
            "project_id": project_id,
            "name": project.get("name"),
            "authority": project.get("authority"),
        },
        "file": file_record,
        "preview": preview,
        "source_mutated": False,
        "boundary": "Read-only bounded preview; this result does not execute, edit, upload, or publish the file.",
    }
