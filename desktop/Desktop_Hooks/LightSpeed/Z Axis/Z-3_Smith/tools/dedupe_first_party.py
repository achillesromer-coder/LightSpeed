#!/usr/bin/env python
"""
First-Party Deduplication Report Generator

Goal:
- Identify byte-identical duplicates across the Z Axis while ignoring vendored/legacy trees.
- Produce a report so we can eliminate double-ups safely while preserving archival copies in Morpheus/Oracle.

This script is intentionally conservative: it does NOT delete or move files.

Outputs:
- Z Axis/Z-1_Morpheus/documentation/_dedupe/first_party_duplicates.json
- Z Axis/Z-1_Morpheus/documentation/_dedupe/first_party_duplicates.md
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for cand in (start, *start.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return start


LS_ROOT = _find_lightspeed_root(Path(__file__))
Z_AXIS = LS_ROOT / "Z Axis"


EXCLUDE_DIR_PARTS = {
    "__pycache__",
    ".git",
    ".idea",
    "node_modules",
    "legacy",
}

# Exclude vendored + massive archives (keep them for ingestion, but do not treat as "dedupe targets").
EXCLUDE_PATH_SUBSTRINGS = (
    str(Path("tools") / "GMAT"),
    str(Path("tools") / "Tabby"),
    str(Path("_CRYSTALLIZATION_BACKUP_")),
    str(Path("archive") / "vault"),
    str(Path("archive") / "inbox"),
)

# Extensions considered first-party assets/config/docs worth deduping.
INCLUDE_EXTENSIONS = {
    ".py",
    ".json",
    ".md",
    ".txt",
    ".sql",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
}


@dataclass(frozen=True)
class FileInfo:
    rel: str
    abs: str
    size: int
    sha256: str


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def is_excluded(path: Path) -> bool:
    rel = path.as_posix()
    for part in path.parts:
        if part in EXCLUDE_DIR_PARTS:
            return True
    for sub in EXCLUDE_PATH_SUBSTRINGS:
        if sub.replace("\\", "/") in rel:
            return True
    return False


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        # mutate dirnames in-place to prune walk
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_PARTS]
        for name in filenames:
            p = Path(dirpath) / name
            if is_excluded(p):
                continue
            if p.suffix.lower() not in INCLUDE_EXTENSIONS:
                continue
            yield p


def choose_canonical(paths: List[str]) -> str:
    """
    Heuristic: prefer non-Morpheus legacy archives and shorter paths.
    """
    def score(p: str) -> Tuple[int, int]:
        rp = p.replace("\\", "/")
        # lower score is better
        penalty = 0
        if "/Z-1_Morpheus/organization/legacy/" in rp:
            penalty += 10
        if "/Z-2_Oracle/" in rp and "/archive/" in rp:
            penalty += 8
        if "/_FloorDocs/" in rp:
            penalty += 7
        return (penalty, len(rp))

    return sorted(paths, key=score)[0]


def main() -> int:
    out_dir = Z_AXIS / "Z-1_Morpheus" / "documentation" / "_dedupe"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "first_party_duplicates.json"
    out_md = out_dir / "first_party_duplicates.md"

    files: List[FileInfo] = []
    by_hash: Dict[str, List[FileInfo]] = {}

    for p in iter_files(Z_AXIS):
        try:
            rel = str(p.relative_to(LS_ROOT))
        except Exception:
            rel = str(p)
        try:
            st = p.stat()
            size = int(st.st_size)
        except Exception:
            continue
        try:
            digest = sha256_file(p)
        except Exception:
            continue
        info = FileInfo(rel=rel, abs=str(p), size=size, sha256=digest)
        files.append(info)
        by_hash.setdefault(digest, []).append(info)

    dup_groups = {h: lst for h, lst in by_hash.items() if len(lst) > 1}

    # Build report objects
    groups: List[Dict[str, object]] = []
    total_dup_files = 0
    total_dup_bytes = 0
    for h, lst in sorted(dup_groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        paths = [x.rel for x in sorted(lst, key=lambda x: x.rel)]
        canonical = choose_canonical(paths)
        size = int(lst[0].size)
        total_dup_files += len(lst)
        total_dup_bytes += size * (len(lst) - 1)
        groups.append(
            {
                "sha256": h,
                "size_bytes": size,
                "count": len(lst),
                "canonical": canonical,
                "paths": paths,
            }
        )

    payload = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "root": str(Z_AXIS),
        "file_count_scanned": len(files),
        "duplicate_groups": len(groups),
        "duplicate_files_total": total_dup_files,
        "duplicate_bytes_wasted_estimate": total_dup_bytes,
        "exclusions": {
            "dir_parts": sorted(EXCLUDE_DIR_PARTS),
            "path_substrings": list(EXCLUDE_PATH_SUBSTRINGS),
            "extensions": sorted(INCLUDE_EXTENSIONS),
        },
        "groups": groups,
    }

    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Minimal markdown summary
    lines: List[str] = []
    lines.append("# First-Party Duplicate Report")
    lines.append("")
    lines.append(f"- Generated: `{payload['generated_at']}`")
    lines.append(f"- Scanned files: `{payload['file_count_scanned']}`")
    lines.append(f"- Duplicate groups: `{payload['duplicate_groups']}`")
    lines.append(f"- Duplicate files (total): `{payload['duplicate_files_total']}`")
    lines.append(f"- Estimated wasted bytes: `{payload['duplicate_bytes_wasted_estimate']}`")
    lines.append("")
    lines.append("## Top Groups")
    lines.append("")
    for g in groups[:25]:
        lines.append(f"- `{g['count']}` copies ({g['size_bytes']} bytes) canonical: `{g['canonical']}`")
        for p in list(g["paths"])[:6]:
            lines.append(f"  - `{p}`")
        if len(list(g["paths"])) > 6:
            lines.append("  - …")
    lines.append("")
    lines.append("## Notes")
    lines.append("- This report excludes vendored tools (GMAT/Tabby), legacy backups, and Oracle vault/inbox trees.")
    lines.append("- Use the canonical path per group when consolidating; archive removed variants in Morpheus/Oracle if needed.")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[dedupe] wrote {out_json}")
    print(f"[dedupe] wrote {out_md}")
    print(f"[dedupe] duplicate groups: {len(groups)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
