#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "_mark_iii_v0_3_source_bundle.zip"
EXPECTED_SHA256 = "1fb38913a705bb799321fc2186c4e191a70c9603cc4501b27bb98e3dcb777a4a"

if not BUNDLE.is_file():
    raise SystemExit(0)
actual = hashlib.sha256(BUNDLE.read_bytes()).hexdigest()
if actual != EXPECTED_SHA256:
    raise RuntimeError(f"bundle hash mismatch: {actual}")
with zipfile.ZipFile(BUNDLE, "r") as archive:
    corrupt = archive.testzip()
    if corrupt is not None:
        raise RuntimeError(f"corrupt bundle member: {corrupt}")
    archive.extractall(ROOT)
BUNDLE.unlink()
Path(__file__).unlink()
print("Materialised Mark III v0.3 source and removed transport files.")
