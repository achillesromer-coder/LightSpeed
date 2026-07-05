from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path, PurePath
import shutil
import stat
from typing import Iterable, Iterator
import uuid


CANONICAL_ROOT = Path(r"C:\LightSpeed_Consolidated")
DEFAULT_DESTINATION_ROOT = CANONICAL_ROOT / "Sources" / "Historical LightSpeed"
DEFAULT_INVENTORY_ROOT = CANONICAL_ROOT / "_migration" / "historical_inventory"
DEFAULT_SUMMARY_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "migration" / "source_roots.json"
)

DEFAULT_ROOTS = {
    "cognigrex": Path(r"C:\Cognigrex\LightSpeed Consolidated"),
    "desktop": Path(r"C:\Users\acc\Desktop\LightSpeed Consolidated"),
    "isolated": Path(r"C:\LightSpeed_Isolated"),
    "emc2": Path(r"C:\Users\acc\Desktop\EMC^2; LightSpeed"),
    "emc2_escaped": Path(r"C:\Users\acc\Desktop\EMC^^2; LightSpeed"),
}

SOURCE_EXTENSIONS = {
    ".bat",
    ".c",
    ".cfg",
    ".cmd",
    ".cpp",
    ".cs",
    ".css",
    ".env.example",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".jsx",
    ".json",
    ".kt",
    ".mjs",
    ".ps1",
    ".py",
    ".pyi",
    ".rs",
    ".scss",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}
DOCUMENT_EXTENSIONS = {
    ".csv",
    ".doc",
    ".docx",
    ".drawio",
    ".epub",
    ".ipynb",
    ".md",
    ".ods",
    ".odt",
    ".pdf",
    ".ppt",
    ".pptx",
    ".rst",
    ".rtf",
    ".svg",
    ".tex",
    ".tsv",
    ".txt",
    ".xls",
    ".xlsm",
    ".xlsx",
}
MODEL_EXTENSIONS = {".bin", ".gguf", ".onnx", ".pt", ".pth", ".safetensors"}
DATABASE_EXTENSIONS = {".db", ".duckdb", ".sqlite", ".sqlite3"}
DATASET_EXTENSIONS = {
    ".arrow",
    ".feather",
    ".fits",
    ".h5",
    ".hdf5",
    ".npy",
    ".npz",
    ".parquet",
}
ARCHIVE_EXTENSIONS = {".7z", ".bak", ".bz2", ".gz", ".rar", ".tar", ".tgz", ".zip"}
GENERATED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "ai_logs",
    "build",
    "cache",
    "caches",
    "dist",
    "generated",
    "logs",
    "node_modules",
    "outputs",
    "receipts",
    "reports",
    "runtime_data",
    "venv",
}
ARCHIVE_PARTS = {"archive", "archives", "backup", "backups", "legacy"}


@dataclass(frozen=True)
class FileClassification:
    action: str
    source_classification: str
    proposed_owner: str
    reason: str


def _utc_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat().replace("+00:00", "Z")


def _is_reparse_point(entry: os.DirEntry[str]) -> bool:
    try:
        attributes = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def iter_physical_files(root: Path) -> Iterator[Path]:
    """Yield files under root without traversing symlinks or Windows junctions."""
    if not root.is_dir():
        return
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            entries = list(os.scandir(current))
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink() or _is_reparse_point(entry):
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    pending.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    yield Path(entry.path)
            except OSError:
                continue


def sha256_file(path: Path, *, chunk_size: int = 4 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_classification(path: Path) -> str:
    parts = {part.casefold() for part in PurePath(path).parts}
    suffix = path.suffix.casefold()
    if parts & ARCHIVE_PARTS or suffix in ARCHIVE_EXTENSIONS:
        return "archive"
    if suffix in MODEL_EXTENSIONS:
        return "model"
    if suffix in DATABASE_EXTENSIONS:
        return "database"
    if suffix in DATASET_EXTENSIONS:
        return "dataset"
    if parts & GENERATED_PARTS:
        return "generated"
    if suffix in SOURCE_EXTENSIONS or path.name.casefold().endswith(".env.example"):
        return "source"
    if suffix in DOCUMENT_EXTENSIONS:
        return "document"
    return "other"


def proposed_owner(path: Path) -> str:
    value = path.as_posix().casefold()
    owner_tokens = (
        ("merovingian", "Merovingian"),
        ("morpheous", "Morpheus"),
        ("morpheus", "Morpheus"),
        ("architect", "Architect"),
        ("trinity", "Trinity"),
        ("oracle", "Oracle"),
        ("smith", "Smith"),
        ("construct", "The Construct"),
        ("neo", "Neo"),
        ("achilles", "Achilles"),
        ("athene", "Athene"),
    )
    for token, owner in owner_tokens:
        if token in value:
            return owner
    return "Neo Review"


def classify_file(
    *,
    path: Path,
    canonical_hashes: set[str],
    modified_utc: str | None = None,
    digest: str | None = None,
) -> FileClassification:
    del modified_utc
    classification = source_classification(path)
    owner = proposed_owner(path)
    if digest is not None and digest in canonical_hashes:
        return FileClassification(
            action="reference_existing",
            source_classification=classification,
            proposed_owner=owner,
            reason="byte-identical content already exists in the canonical source set",
        )
    if classification in {"source", "document"}:
        return FileClassification(
            action="extract_candidate",
            source_classification=classification,
            proposed_owner=owner,
            reason="unique reviewable source or document",
        )
    return FileClassification(
        action="inventory_only",
        source_classification=classification,
        proposed_owner=owner,
        reason="runtime payload or unsupported artifact; indexed without copying",
    )


def _safe_root_label(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    return cleaned.strip("._") or "historical"


def extract_candidate(
    *,
    source: Path,
    source_root: Path,
    root_label: str,
    destination_root: Path,
    digest: str,
) -> dict[str, str]:
    relative = source.relative_to(source_root)
    target = destination_root / _safe_root_label(root_label) / relative
    if target.exists():
        if sha256_file(target) == digest:
            return {
                "destination": str(target),
                "sha256": digest,
                "status": "already_present",
            }
        target = target.with_name(f"{target.stem}.{digest[:12]}{target.suffix}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        shutil.copy2(source, temporary)
        copied_digest = sha256_file(temporary)
        if copied_digest != digest:
            raise OSError(f"checksum mismatch while extracting {source}")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return {"destination": str(target), "sha256": digest, "status": "copied"}


def _should_hash_for_canonical(path: Path) -> bool:
    relative_parts = {part.casefold() for part in path.parts}
    if relative_parts & {
        "_analysis_remote",
        "_migration",
        "_worktrees",
        "sources",
    }:
        return False
    return source_classification(path) in {"source", "document"}


def build_canonical_hashes(root: Path) -> set[str]:
    hashes: set[str] = set()
    for path in iter_physical_files(root):
        if not _should_hash_for_canonical(path):
            continue
        try:
            hashes.add(sha256_file(path))
        except OSError:
            continue
    return hashes


def _root_summary(root: Path) -> dict[str, object]:
    return {
        "path": str(root),
        "exists": root.is_dir(),
        "files": 0,
        "bytes": 0,
        "actions": {
            "extract_candidate": 0,
            "reference_existing": 0,
            "inventory_only": 0,
        },
        "classifications": {},
        "errors": 0,
        "extracted": 0,
    }


def inventory_roots(
    *,
    roots: dict[str, Path],
    canonical_root: Path,
    destination_root: Path,
    inventory_path: Path,
    execute_extract: bool,
    max_files: int | None = None,
) -> dict[str, object]:
    canonical_hashes = build_canonical_hashes(canonical_root)
    seen_historical_hashes: set[str] = set()
    summaries = {label: _root_summary(root) for label, root in roots.items()}
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    total_files = 0
    total_bytes = 0
    started = datetime.now(tz=UTC)

    with inventory_path.open("w", encoding="utf-8", newline="\n") as inventory:
        for label, root in roots.items():
            if not root.is_dir():
                continue
            summary = summaries[label]
            for path in iter_physical_files(root):
                if max_files is not None and total_files >= max_files:
                    break
                try:
                    file_stat = path.stat()
                    digest = sha256_file(path)
                except OSError as exc:
                    summary["errors"] = int(summary["errors"]) + 1
                    inventory.write(
                        json.dumps(
                            {
                                "root_label": label,
                                "path": str(path),
                                "error": str(exc),
                            },
                            ensure_ascii=True,
                            sort_keys=True,
                        )
                        + "\n"
                    )
                    continue
                classification = classify_file(
                    path=path,
                    canonical_hashes=canonical_hashes | seen_historical_hashes,
                    modified_utc=_utc_iso(file_stat.st_mtime),
                    digest=digest,
                )
                relative = path.relative_to(root)
                record: dict[str, object] = {
                    "root_label": label,
                    "root_path": str(root),
                    "path": str(path),
                    "relative_path": relative.as_posix(),
                    "bytes": file_stat.st_size,
                    "modified_utc": _utc_iso(file_stat.st_mtime),
                    "sha256": digest,
                    "duplicate_group": digest[:16],
                    **asdict(classification),
                }
                if classification.action == "extract_candidate" and execute_extract:
                    receipt = extract_candidate(
                        source=path,
                        source_root=root,
                        root_label=label,
                        destination_root=destination_root,
                        digest=digest,
                    )
                    record["extraction"] = receipt
                    summary["extracted"] = int(summary["extracted"]) + (
                        1 if receipt["status"] == "copied" else 0
                    )
                inventory.write(
                    json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n"
                )
                seen_historical_hashes.add(digest)
                summary["files"] = int(summary["files"]) + 1
                summary["bytes"] = int(summary["bytes"]) + file_stat.st_size
                actions = summary["actions"]
                assert isinstance(actions, dict)
                actions[classification.action] = int(actions[classification.action]) + 1
                classifications = summary["classifications"]
                assert isinstance(classifications, dict)
                current = int(classifications.get(classification.source_classification, 0))
                classifications[classification.source_classification] = current + 1
                total_files += 1
                total_bytes += file_stat.st_size
            if max_files is not None and total_files >= max_files:
                break

    finished = datetime.now(tz=UTC)
    return {
        "schema_version": "lightspeed-source-roots-v1",
        "generated_at": finished.isoformat(),
        "canonical_root": str(canonical_root),
        "destination_root": str(destination_root),
        "inventory_path": str(inventory_path),
        "execute_extract": execute_extract,
        "junctions_followed": False,
        "canonical_hash_count": len(canonical_hashes),
        "historical_unique_hash_count": len(seen_historical_hashes),
        "total_files": total_files,
        "total_bytes": total_bytes,
        "duration_seconds": round((finished - started).total_seconds(), 3),
        "roots": summaries,
    }


def _parse_root(value: str) -> tuple[str, Path]:
    label, separator, raw_path = value.partition("=")
    if not separator or not label or not raw_path:
        raise argparse.ArgumentTypeError("root must use LABEL=ABSOLUTE_PATH")
    path = Path(raw_path)
    if not path.is_absolute():
        raise argparse.ArgumentTypeError("root path must be absolute")
    return label, path


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory historical LightSpeed roots without following junctions."
    )
    parser.add_argument(
        "--root",
        action="append",
        type=_parse_root,
        help="Override roots with LABEL=ABSOLUTE_PATH; repeat for multiple roots.",
    )
    parser.add_argument("--canonical-root", type=Path, default=CANONICAL_ROOT)
    parser.add_argument(
        "--destination-root", type=Path, default=DEFAULT_DESTINATION_ROOT
    )
    parser.add_argument("--inventory-path", type=Path)
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--execute-extract", action="store_true")
    parser.add_argument("--max-files", type=int)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    roots = dict(args.root) if args.root else DEFAULT_ROOTS
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    inventory_path = args.inventory_path or (
        DEFAULT_INVENTORY_ROOT / f"lightspeed_inventory_{timestamp}.jsonl"
    )
    result = inventory_roots(
        roots=roots,
        canonical_root=args.canonical_root,
        destination_root=args.destination_root,
        inventory_path=inventory_path,
        execute_extract=args.execute_extract,
        max_files=args.max_files,
    )
    args.summary_path.parent.mkdir(parents=True, exist_ok=True)
    args.summary_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
