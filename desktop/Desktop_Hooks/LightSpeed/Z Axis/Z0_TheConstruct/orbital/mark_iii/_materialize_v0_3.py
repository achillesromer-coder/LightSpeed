#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
READY = ROOT / "_mark_iii_v0_3_parts.ready"
EXPECTED_SHA256 = "1fb38913a705bb799321fc2186c4e191a70c9603cc4501b27bb98e3dcb777a4a"
PART_COUNT = 4

if not READY.is_file():
    print("Transport parts are not yet marked ready; materialisation deferred.")
    raise SystemExit(0)

part_paths = [ROOT / f"_mark_iii_v0_3_source_bundle.part{index:02d}.b64" for index in range(1, PART_COUNT + 1)]
missing = [path.name for path in part_paths if not path.is_file()]
if missing:
    raise RuntimeError(f"missing bundle parts: {missing}")

encoded = "".join(path.read_text(encoding="ascii").strip() for path in part_paths)
bundle_bytes = base64.b64decode(encoded, validate=True)
actual = hashlib.sha256(bundle_bytes).hexdigest()
if actual != EXPECTED_SHA256:
    raise RuntimeError(f"bundle hash mismatch: {actual}")

bundle = ROOT / "_mark_iii_v0_3_source_bundle.reconstructed.zip"
bundle.write_bytes(bundle_bytes)
with zipfile.ZipFile(bundle, "r") as archive:
    corrupt = archive.testzip()
    if corrupt is not None:
        raise RuntimeError(f"corrupt bundle member: {corrupt}")
    archive.extractall(ROOT)

for path in part_paths:
    path.unlink()
READY.unlink()
old_bundle = ROOT / "_mark_iii_v0_3_source_bundle.zip"
if old_bundle.exists():
    old_bundle.unlink()
bundle.unlink()
Path(__file__).unlink()
print("Materialised verified Mark III v0.3 source and removed all transport files.")
