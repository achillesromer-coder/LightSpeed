#!/usr/bin/env python3
"""Recompute desktop/source-manifest.json hashes from the current Git checkout.

This does not add new paths or copy source. It refreshes only the records already
approved in the manifest, preserving the source boundary while repairing hash
and byte-count drift after reviewed repository changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "desktop"
DEFAULT_MANIFEST = DESKTOP / "source-manifest.json"


def portable_content(path: Path) -> bytes:
    # Git may materialize text files with CRLF on Windows while CI checks them
    # out with LF. The validator already hashes normalized content, so the
    # refresher must use the same portable content for hashes and byte counts.
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(portable_content(path)).hexdigest()


def refresh(manifest_path: Path) -> dict[str, object]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("source manifest must contain a records list")

    refreshed: list[dict[str, object]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise ValueError(f"manifest record {index} lacks a path")
        relative = record["path"]
        target = (DESKTOP / relative).resolve()
        target.relative_to(ROOT.resolve())
        if not target.is_file():
            raise FileNotFoundError(f"manifest target missing: desktop/{relative}")
        content = portable_content(target)
        refreshed.append(
            {
                "bytes": len(content),
                "path": relative,
                "sha256": sha256(target),
            }
        )

    return {
        "schema_version": payload.get("schema_version", 1),
        "records": refreshed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = refresh(args.manifest)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
