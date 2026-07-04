"""Copy approved Desktop source from the canonical runtime into Git output."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import BinaryIO, Callable, Iterable, Sequence


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
_RESERVOIR_SOURCE_PREFIX = (
    "lightspeed_runtime",
    "lightspeed_runtime",
    "reservoirs",
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
_BeforeReplace = Callable[[Path, Path], None]
_TemporaryWriter = Callable[[BinaryIO], None]
_PathIdentity = tuple[int, int]
_DestinationGuard = tuple[_PathIdentity, _PathIdentity, Path, Path]


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
    lowered_parts = tuple(part.casefold() for part in raw_parts)
    blocked = {
        part
        for part in lowered_parts
        if part in BLOCKED_PARTS
    }
    if not blocked:
        return True
    if blocked != {"reservoirs"}:
        return False
    if lowered_parts[: len(_RESERVOIR_SOURCE_PREFIX)] != _RESERVOIR_SOURCE_PREFIX:
        return False
    if len(lowered_parts) == len(_RESERVOIR_SOURCE_PREFIX):
        return True
    return (
        len(lowered_parts) == len(_RESERVOIR_SOURCE_PREFIX) + 1
        and PurePosixPath(normalized).suffix.casefold() == ".py"
    )


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


def _normalized_deny_patterns(patterns: Iterable[str]) -> tuple[str, ...]:
    normalized = []
    for pattern in patterns:
        if not isinstance(pattern, str) or not pattern or "\0" in pattern:
            raise ValueError(f"invalid source deny pattern: {pattern!r}")
        value = pattern.replace("\\", "/").casefold()
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _is_denied_source_path(relative: str, deny_patterns: tuple[str, ...]) -> bool:
    normalized = relative.replace("\\", "/").casefold()
    return any(
        fnmatch.fnmatchcase(normalized, pattern)
        or (
            pattern.startswith("**/")
            and fnmatch.fnmatchcase(normalized, pattern.removeprefix("**/"))
        )
        for pattern in deny_patterns
    )


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
    deny_patterns: tuple[str, ...],
    records: set[str],
) -> None:
    with os.scandir(directory) as entries:
        ordered_entries = sorted(entries, key=lambda entry: (entry.name.casefold(), entry.name))

    for entry in ordered_entries:
        path = Path(entry.path)
        relative = path.relative_to(source_root).as_posix()
        if (
            not validate_relative_path(relative)
            or _is_denied_source_path(relative, deny_patterns)
            or _is_reparse_point(path)
        ):
            continue
        if entry.is_dir(follow_symlinks=False):
            _walk_approved_files(
                source_root,
                path,
                approved_extensions,
                deny_patterns,
                records,
            )
        elif entry.is_file(follow_symlinks=False):
            if path.suffix.casefold() in approved_extensions:
                records.add(relative)


def expand_source_paths(
    source_root: Path | str,
    roots: Sequence[str],
    extensions: Iterable[str] = DEFAULT_EXTENSIONS,
    *,
    deny_patterns: Iterable[str] = (),
) -> list[str]:
    """Expand explicit files and directories into deterministic source paths."""
    source_root = _absolute_path(source_root)
    approved_extensions = _normalized_extensions(extensions)
    normalized_deny_patterns = _normalized_deny_patterns(deny_patterns)
    _assert_no_reparse_points(source_root)
    if not source_root.is_dir():
        raise FileNotFoundError(f"source root does not exist: {source_root}")

    records: set[str] = set()
    for value in roots:
        relative = _normalized_relative_path(value)
        if _is_denied_source_path(relative, normalized_deny_patterns):
            raise ValueError(f"denied source path: {relative}")
        source = _contained_path(source_root, relative)
        _assert_no_reparse_points(source)
        if not source.exists():
            raise FileNotFoundError(f"allowlisted source does not exist: {relative}")
        if source.is_file():
            if source.suffix.casefold() not in approved_extensions:
                raise ValueError(f"source does not use an approved extension: {relative}")
            records.add(relative)
        elif source.is_dir():
            _walk_approved_files(
                source_root,
                source,
                approved_extensions,
                normalized_deny_patterns,
                records,
            )
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
    deny_patterns = payload.get("deny_patterns")
    if not isinstance(roots, list) or not roots or not all(
        isinstance(root, str) and validate_relative_path(root) for root in roots
    ):
        raise ValueError("source allowlist roots must be safe relative paths")
    if not isinstance(extensions, list):
        raise ValueError("source allowlist extensions must be a list")
    if not isinstance(deny_patterns, list):
        raise ValueError("source allowlist deny_patterns must be a list")

    return {
        "roots": roots,
        "extensions": list(_normalized_extensions(extensions)),
        "deny_patterns": list(_normalized_deny_patterns(deny_patterns)),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path_identity(path: Path) -> _PathIdentity:
    path_stat = os.stat(path, follow_symlinks=False)
    return path_stat.st_dev, path_stat.st_ino


def _validate_destination(
    target_root: Path,
    destination: Path,
    *,
    expected_guard: _DestinationGuard | None = None,
) -> _DestinationGuard:
    target_root = _absolute_path(target_root)
    destination = _absolute_path(destination)
    try:
        destination.relative_to(target_root)
    except ValueError as exc:
        raise ValueError(f"destination escapes target root: {destination}") from exc

    _assert_no_reparse_points(target_root)
    _assert_no_reparse_points(destination.parent)
    if _is_reparse_point(destination):
        raise ValueError(f"reparse point is not allowed: {destination}")
    if not target_root.is_dir():
        raise ValueError(f"target root is not a directory: {target_root}")
    if not destination.parent.is_dir():
        raise ValueError(f"target parent is not a directory: {destination.parent}")

    resolved_root = target_root.resolve(strict=True)
    resolved_parent = destination.parent.resolve(strict=True)
    _assert_no_reparse_points(target_root)
    _assert_no_reparse_points(destination.parent)
    if _is_reparse_point(destination):
        raise ValueError(f"reparse point is not allowed: {destination}")
    try:
        resolved_parent.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(
            f"resolved target parent escapes target root: {destination.parent}"
        ) from exc

    resolved_destination = destination.resolve(strict=False)
    if _is_reparse_point(destination):
        raise ValueError(f"reparse point is not allowed: {destination}")
    if resolved_destination.parent != resolved_parent:
        raise ValueError(f"resolved target escapes verified parent: {destination}")
    try:
        resolved_destination.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"resolved target escapes target root: {destination}") from exc

    guard = (
        _path_identity(target_root),
        _path_identity(destination.parent),
        resolved_root,
        resolved_parent,
    )
    if expected_guard is not None and guard != expected_guard:
        raise ValueError(f"target root or parent changed before replace: {destination}")
    return guard


def _validate_temporary_file(
    temporary_path: Path,
    expected_guard: _DestinationGuard,
) -> None:
    _assert_no_reparse_points(temporary_path)
    if _is_reparse_point(temporary_path) or not temporary_path.is_file():
        raise ValueError(f"temporary path is not a regular file: {temporary_path}")
    resolved_temporary = temporary_path.resolve(strict=True)
    if resolved_temporary.parent != expected_guard[3]:
        raise ValueError(f"temporary path escaped verified parent: {temporary_path}")


def _atomic_replace_from_writer(
    target_root: Path,
    destination: Path,
    writer: _TemporaryWriter,
    *,
    before_replace: _BeforeReplace | None = None,
) -> None:
    _assert_no_reparse_points(destination.parent)
    destination.parent.mkdir(parents=True, exist_ok=True)
    initial_guard = _validate_destination(target_root, destination)

    descriptor: int | None = None
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            writer(handle)

        _validate_temporary_file(temporary_path, initial_guard)
        if before_replace is not None:
            before_replace(temporary_path, destination)
        _validate_temporary_file(temporary_path, initial_guard)
        _validate_destination(
            target_root,
            destination,
            expected_guard=initial_guard,
        )
        os.replace(temporary_path, destination)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _atomic_copy_source(
    target_root: Path,
    source: Path,
    destination: Path,
    *,
    expected_sha256: str,
    expected_size: int,
    before_replace: _BeforeReplace | None = None,
) -> None:
    def write_source(handle: BinaryIO) -> None:
        with source.open("rb") as source_handle:
            shutil.copyfileobj(source_handle, handle)

    def validate_staged_source(temporary_path: Path, target_path: Path) -> None:
        if (
            temporary_path.stat().st_size != expected_size
            or _sha256(temporary_path) != expected_sha256
        ):
            raise ValueError(f"staged source changed during copy: {source}")
        if before_replace is not None:
            before_replace(temporary_path, target_path)

    _atomic_replace_from_writer(
        target_root,
        destination,
        write_source,
        before_replace=validate_staged_source,
    )


def _atomic_write_manifest(
    target_root: Path,
    manifest_path: Path,
    payload: dict[str, object],
    *,
    before_replace: _BeforeReplace | None = None,
) -> None:
    manifest_bytes = (
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    def write_manifest(handle: BinaryIO) -> None:
        handle.write(manifest_bytes)

    _atomic_replace_from_writer(
        target_root,
        manifest_path,
        write_manifest,
        before_replace=before_replace,
    )


def sync_sources(
    source_root: Path | str,
    target_root: Path | str,
    paths: Sequence[str],
    *,
    extensions: Iterable[str] = DEFAULT_EXTENSIONS,
    deny_patterns: Iterable[str] = (),
    dry_run: bool = False,
    manifest_name: str = DEFAULT_MANIFEST_NAME,
    before_replace: _BeforeReplace | None = None,
) -> dict[str, object]:
    """Synchronize approved source files and return the manifest records."""
    source_root = _absolute_path(source_root)
    target_root = _absolute_path(target_root)
    manifest_relative = _normalized_relative_path(manifest_name)
    expanded_paths = expand_source_paths(
        source_root,
        paths,
        extensions,
        deny_patterns=deny_patterns,
    )
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
            destination_guard = _validate_destination(target_root, destination)
            if not destination.is_file():
                raise ValueError(f"target is not a regular file: {relative}")
            destination_matches = (
                destination.stat().st_size == size and _sha256(destination) == digest
            )
            _validate_destination(
                target_root,
                destination,
                expected_guard=destination_guard,
            )

        if destination_matches:
            unchanged += 1
        else:
            copied += 1
            if not dry_run:
                _atomic_copy_source(
                    target_root,
                    source,
                    destination,
                    expected_sha256=digest,
                    expected_size=size,
                    before_replace=before_replace,
                )

        records.append({"path": relative, "sha256": digest, "bytes": size})

    manifest = {"schema_version": 1, "records": records}
    manifest_path = _contained_path(target_root, manifest_relative)
    _assert_no_reparse_points(manifest_path)
    if not dry_run:
        _atomic_write_manifest(
            target_root,
            manifest_path,
            manifest,
            before_replace=before_replace,
        )

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
        deny_patterns=allowlist["deny_patterns"],
        dry_run=args.dry_run,
        manifest_name=args.manifest,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
