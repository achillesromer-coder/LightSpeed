#!/usr/bin/env python3
"""Validate LightSpeed repository surfaces without executing applications or touching excluded physics lanes."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "desktop"
MANIFEST = DESKTOP / "source-manifest.json"

EXCLUDED_MARKERS = (
    "/raphael/",
    "raphael_",
    "/n3_",
    "/n^3/",
)

REQUIRED_SURFACES = [
    DESKTOP / "Desktop_Hooks" / "LightSpeed" / "__main__.py",
    DESKTOP / "Desktop_Hooks" / "LightSpeed" / "launcher_exe.py",
    DESKTOP / "LightSpeed_Runtime" / "lightspeed_runtime" / "operator_home.py",
    MANIFEST,
]


def sha256(path: Path) -> str:
    # Git normalises tracked text to LF, while a Windows checkout may expose
    # CRLF bytes.  The source manifest describes the portable Git content, so
    # normalise line endings before hashing the text-only allowlisted surface.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def is_excluded(path_text: str) -> bool:
    normalised = "/" + path_text.replace("\\", "/").lower().strip("/")
    return any(marker in normalised for marker in EXCLUDED_MARKERS)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for path in REQUIRED_SURFACES:
        if not path.is_file():
            errors.append(f"Missing required LightSpeed surface: {path.relative_to(ROOT)}")

    if not MANIFEST.is_file():
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: unreadable desktop/source-manifest.json: {exc}", file=sys.stderr)
        return 1

    records = payload.get("records")
    if not isinstance(records, list):
        errors.append("source-manifest.json must contain a records list")
        records = []

    seen: set[str] = set()
    checked = 0
    excluded = 0

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"Manifest record {index} is not an object")
            continue
        relative_text = record.get("path")
        expected = record.get("sha256")
        if not isinstance(relative_text, str) or not isinstance(expected, str):
            errors.append(f"Manifest record {index} lacks path or sha256")
            continue
        if relative_text in seen:
            errors.append(f"Duplicate manifest path: {relative_text}")
            continue
        seen.add(relative_text)

        if is_excluded(relative_text):
            excluded += 1
            continue

        target = (DESKTOP / relative_text).resolve()
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"Manifest path escapes repository: {relative_text}")
            continue
        if not target.is_file():
            errors.append(f"Manifest target missing: desktop/{relative_text}")
            continue
        checked += 1
        actual = sha256(target)
        if actual.lower() != expected.lower():
            errors.append(
                f"Manifest SHA mismatch: desktop/{relative_text} "
                f"expected={expected} actual={actual}"
            )

    if len(records) < 10:
        warnings.append("Desktop source manifest contains fewer than 10 records")

    print(
        f"Validated {checked} eligible desktop manifest records; "
        f"skipped {excluded} excluded Raphael/N3-adjacent records."
    )
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("LightSpeed surface validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
