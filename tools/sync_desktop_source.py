"""Copy approved Desktop source from the canonical runtime into Git output."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Iterable, Sequence


CANONICAL_SOURCE_ROOT = Path(r"C:\LightSpeed_Consolidated")
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALLOWLIST_PATH = REPOSITORY_ROOT / "tools" / "source_allowlist.json"
DEFAULT_TARGET_ROOT = REPOSITORY_ROOT / "desktop"
DEFAULT_MANIFEST_NAME = "source-manifest.json"
DEFAULT_EXTENSIONS = (
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".md",
    ".ini",
    ".cfg",
)
BLOCKED_PARTS = frozenset(
    {
        "data",
        "archive",
        "ai_logs",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        "reservoirs",
        "vault",
        "venv",
        "legacy",
    }
)
_WINDOWS_RESERVED_STEMS = frozenset(
    {
        "con",
        "prn",
        "aux",
        "nul",
        "clock$",
        *(f"com{index}" for index in range(1, 10)),
        *(f"lpt{index}" for index in range(1, 10)),
    }
)
_REPARSE_POINT_FLAG = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def validate_relative_path(value: str) -> bool:
    """Return whether value is a safe, source-eligible relative path."""
    if not isinstance(value, str) or not value:
        return False

    normalized = value.replace("\\", "/")
    raw_parts = normalized.split("/")
    windows_path = PureWindowsPath(value)
    posix_path = PurePosixPath(normalized)
    if (
        posix_path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or windows_path.root
    ):
        return False
    if any(part in {"", ".", ".."} for part in raw_parts):
        return False
    if any(
        part != part.rstrip(" .")
        or ":" in part
        or part.split(".", 1)[0].casefold() in _WINDOWS_RESERVED_STEMS
        for part in raw_parts
    ):
        return False
    return not any(part.casefold() in BLOCKED_PARTS for part in raw_parts)


def _normalized_relative_path(value: str) -> str:
    if not validate_relative_path(value):
        raise ValueError(f"blocked source path: {value}")
    return PurePosixPath(value.replace("\\", "/")).as_posix()


def _normalized_extensions(extensions: Iterable[str]) -> tuple[str, ...]:
    normalized = []
    for extension in extensions:
        if (
            not isinstance(extension, str)
            or len(extension) < 2
            or not extension.startswith(".")
            or "/" in extension
            or "\\" in extension
        ):
            raise ValueError(f"invalid approved extension: {extension!r}")
        lowered = extension.casefold()
        if lowered not in normalized:
            normalized.append(lowered)
    if not normalized:
        raise ValueError("at least one approved extension is required")
    return tuple(normalized)


def _absolute_path(path: Path | str) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _is_reparse_point(path: Path) -> bool:
    try:
        file_stat = os.lstat(path)
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(file_stat.st_mode) or bool(
        getattr(file_stat, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    )


def _assert_no_reparse_points(path: Path) -> None:
    absolute = _absolute_path(path)
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if _is_reparse_point(current):
            raise ValueError(f"reparse point is not allowed: {current}")


def _contained_path(root: Path, relative: str) -> Path:
    root = _absolute_path(root)
    candidate = _absolute_path(root.joinpath(*PurePosixPath(relative).parts))
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes target root: {relative}") from exc
    return candidate


def _walk_approved_files(
    source_root: Path,
    directory: Path,
    approved_extensions: tuple[str, ...],
    records: set[str],
) -> None:
    with os.scandir(directory) as entries:
        ordered_entries = sorted(entries, key=lambda entry: (entry.name.casefold(), entry.name))

    for entry in ordered_entries:
        path = Path(entry.path)
        relative = path.relative_to(source_root).as_posix()
        if not validate_relative_path(relative) or _is_reparse_point(path):
            continue
        if entry.is_dir(follow_symlinks=False):
            _walk_approved_files(source_root, path, approved_extensions, records)
        elif entry.is_file(follow_symlinks=False):
            if path.suffix.casefold() in approved_extensions:
                records.add(relative)


def expand_source_paths(
    source_root: Path | str,
    roots: Sequence[str],
    extensions: Iterable[str] = DEFAULT_EXTENSIONS,
) -> list[str]:
    """Expand explicit files and directories into deterministic source paths."""
    source_root = _absolute_path(source_root)
    approved_extensions = _normalized_extensions(extensions)
    _assert_no_reparse_points(source_root)
    if not source_root.is_dir():
        raise FileNotFoundError(f"source root does not exist: {source_root}")

    records: set[str] = set()
    for value in roots:
        relative = _normalized_relative_path(value)
        source = _contained_path(source_root, relative)
        _assert_no_reparse_points(source)
        if not source.exists():
            raise FileNotFoundError(f"allowlisted source does not exist: {relative}")
        if source.is_file():
            if source.suffix.casefold() not in approved_extensions:
                raise ValueError(f"source does not use an approved extension: {relative}")
            records.add(relative)
        elif source.is_dir():
            _walk_approved_files(source_root, source, approved_extensions, records)
        else:
            raise ValueError(f"allowlisted source is not a regular file or directory: {relative}")

    return sorted(records, key=lambda value: (value.casefold(), value))


def load_allowlist(path: Path | str) -> dict[str, list[str]]:
    """Load and validate the source-root and extension allowlist."""
    allowlist_path = Path(path)
    payload = json.loads(allowlist_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("source allowlist must be a JSON object")

    roots = payload.get("roots")
    extensions = payload.get("extensions")
    if not isinstance(roots, list) or not roots or not all(
        isinstance(root, str) and validate_relative_path(root) for root in roots
    ):
        raise ValueError("source allowlist roots must be safe relative paths")
    if not isinstance(extensions, list):
        raise ValueError("source allowlist extensions must be a list")

    return {
        "roots": roots,
        "extensions": list(_normalized_extensions(extensions)),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_manifest(
    target_root: Path,
    manifest_path: Path,
    payload: dict[str, object],
) -> None:
    _assert_no_reparse_points(manifest_path.parent)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_reparse_points(manifest_path.parent)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{manifest_path.name}.",
        suffix=".tmp",
        dir=manifest_path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        if _contained_path(target_root, temporary_path.relative_to(target_root).as_posix()) != temporary_path:
            raise ValueError("temporary manifest path escapes target root")
        os.replace(temporary_path, manifest_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def sync_sources(
    source_root: Path | str,
    target_root: Path | str,
    paths: Sequence[str],
    *,
    extensions: Iterable[str] = DEFAULT_EXTENSIONS,
    dry_run: bool = False,
    manifest_name: str = DEFAULT_MANIFEST_NAME,
) -> dict[str, object]:
    """Synchronize approved source files and return the manifest records."""
    source_root = _absolute_path(source_root)
    target_root = _absolute_path(target_root)
    manifest_relative = _normalized_relative_path(manifest_name)
    expanded_paths = expand_source_paths(source_root, paths, extensions)
    if manifest_relative in expanded_paths:
        raise ValueError("manifest path conflicts with an allowlisted source file")

    _assert_no_reparse_points(target_root)
    copied = 0
    unchanged = 0
    records: list[dict[str, object]] = []
    for relative in expanded_paths:
        source = _contained_path(source_root, relative)
        destination = _contained_path(target_root, relative)
        _assert_no_reparse_points(source)
        _assert_no_reparse_points(destination)
        if not source.is_file():
            raise ValueError(f"source is not a regular file: {relative}")

        digest = _sha256(source)
        size = source.stat().st_size
        destination_matches = False
        if destination.exists():
            if not destination.is_file():
                raise ValueError(f"target is not a regular file: {relative}")
            destination_matches = (
                destination.stat().st_size == size and _sha256(destination) == digest
            )

        if destination_matches:
            unchanged += 1
        else:
            copied += 1
            if not dry_run:
                _assert_no_reparse_points(destination.parent)
                destination.parent.mkdir(parents=True, exist_ok=True)
                _assert_no_reparse_points(destination.parent)
                shutil.copy2(source, destination)

        records.append({"path": relative, "sha256": digest, "bytes": size})

    manifest = {"schema_version": 1, "records": records}
    manifest_path = _contained_path(target_root, manifest_relative)
    _assert_no_reparse_points(manifest_path)
    if not dry_run:
        _atomic_write_manifest(target_root, manifest_path, manifest)

    return {
        "mode": "dry-run" if dry_run else "sync",
        "copied": copied,
        "unchanged": unchanged,
        "manifest": manifest_relative,
        "records": records,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Synchronize approved source from C:\\LightSpeed_Consolidated "
            "into the repository Desktop boundary."
        )
    )
    parser.add_argument(
        "--allowlist",
        type=Path,
        default=DEFAULT_ALLOWLIST_PATH,
        help="JSON allowlist of active source roots and approved extensions",
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        default=DEFAULT_TARGET_ROOT,
        help="destination root (defaults to the repository desktop directory)",
    )
    parser.add_argument(
        "--manifest",
        default=DEFAULT_MANIFEST_NAME,
        help="relative manifest path inside the target root",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="report without writing")
    mode.add_argument("--sync", action="store_true", help="copy files and write manifest")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    allowlist = load_allowlist(args.allowlist)
    result = sync_sources(
        CANONICAL_SOURCE_ROOT,
        args.target_root,
        allowlist["roots"],
        extensions=allowlist["extensions"],
        dry_run=args.dry_run,
        manifest_name=args.manifest,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
