#!/usr/bin/env python3
"""Validate the public-safe COIN protocol topology record.

This script deliberately validates only topology and negative gates. It does not
fetch the private/canonical archive, compile contracts, or imply deployment.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs" / "web4" / "COIN_PROTOCOL_CANON_2026-07-29.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def fail(message: str) -> None:
    raise SystemExit(f"web4 protocol canon validation failed: {message}")


def main() -> int:
    data = json.loads(RECORD.read_text(encoding="utf-8"))

    if data.get("canonical_store") != "google_drive":
        fail("canonical_store must remain google_drive")

    drive = data.get("drive") or {}
    if drive.get("readback_verified") is not True:
        fail("Drive readback must be verified")
    if not SHA256_RE.fullmatch(str(drive.get("archive_sha256", ""))):
        fail("archive_sha256 must be 64 lowercase hex characters")
    if int(drive.get("archive_size_bytes", 0)) <= 0:
        fail("archive_size_bytes must be positive")

    implementation = data.get("implementation") or {}
    if implementation.get("full_source_published_to_public_git") is not False:
        fail("public Git source publication is not approved")
    if implementation.get("solidity_compiled") is not False:
        fail("record must not claim a successful Solidity compile")
    if implementation.get("independent_security_audit_complete") is not False:
        fail("record must not claim an independent audit")

    enabled = sorted(name for name, value in (data.get("feature_gates") or {}).items() if value is not False)
    if enabled:
        fail(f"prohibited feature gates enabled: {', '.join(enabled)}")

    digest = hashlib.sha256(RECORD.read_bytes()).hexdigest()
    print(json.dumps({"ok": True, "record": str(RECORD.relative_to(ROOT)), "record_sha256": digest}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
