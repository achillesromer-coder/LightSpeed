#!/usr/bin/env python3
"""Read-only verification of the private historical COIN archive.

Use the pinned COIN topology record as authority. Never extract or publish
archive contents. PASS is exact R0 integrity, not compilation, finality or
decentralised network acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

DIGEST = re.compile(r"^[a-f0-9]{64}$")
MAX_FILES = 2000
MAX_UNCOMPRESSED = 64 * 1024 * 1024
MAX_ENTRY = 16 * 1024 * 1024

class ArchiveHold(ValueError):
    pass

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def audit(archive: Path, canon: dict) -> dict:
    if not isinstance(canon, dict) or canon.get("record_id") != "coin-protocol-canon-2026-07-29":
        raise ArchiveHold("COIN canonical locator unavailable")
    drive = canon.get("drive")
    impl = canon.get("implementation")
    gates = canon.get("feature_gates")
    if not isinstance(drive, dict) or not isinstance(impl, dict) or not isinstance(gates, dict) or not gates:
        raise ArchiveHold("canonical record incomplete")
    expected = drive.get("archive_sha256")
    if not isinstance(expected, str) or not DIGEST.fullmatch(expected):
        raise ArchiveHold("invalid pinned archive hash")
    if not all(value is False for value in gates.values()):
        raise ArchiveHold("COIN value or production gate enabled")
    for field in ("full_source_published_to_public_git", "solidity_compiled", "independent_security_audit_complete"):
        if impl.get(field) is not False:
            raise ArchiveHold("unsupported compile/audit/publication claim")
    try:
        expected_size = int(drive.get("archive_size_bytes"))
        st = archive.stat()
    except (OSError, ValueError, TypeError) as exc:
        raise ArchiveHold("archive missing or canonical size invalid") from exc
    if st.st_size != expected_size or st.st_size > 32 * 1024 * 1024:
        raise ArchiveHold("archive size does not match canonical receipt")
    h = hashlib.sha256()
    with archive.open("rb") as f:
        for buf in iter(lambda: f.read(1024 * 1024), b""):
            h.update(buf)
    if h.hexdigest() != expected:
        raise ArchiveHold("archive SHA256 does not match canonical receipt")
    try:
        with zipfile.ZipFile(archive) as z:
            infos = z.infolist()
            if not infos or len(infos) > MAX_FILES:
                raise ArchiveHold("archive member limit")
            seen = set()
            roots = set()
            members = {}
            total = 0
            for info in infos:
                path = info.filename
                if "\\" in path or "\x00" in path or path.startswith("/") or ":" in path:
                    raise ArchiveHold("unsafe archive path")
                parts = PurePosixPath(path).parts
                if not parts or "." in parts or ".." in parts:
                    raise ArchiveHold("unsafe archive path")
                if path in seen:
                    raise ArchiveHold("duplicate archive member")
                seen.add(path)
                roots.add(parts[0])
                if info.flag_bits & 1 or stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                    raise ArchiveHold("encrypted or symlinked archive member")
                if info.is_dir():
                    continue
                total += info.file_size
                if info.file_size > MAX_ENTRY or total > MAX_UNCOMPRESSED:
                    raise ArchiveHold("expanded archive limit")
                if info.file_size > 0 and info.compress_size == 0:
                    raise ArchiveHold("invalid compressed size")
                if info.compress_size > 0 and info.file_size / info.compress_size > 300:
                    raise ArchiveHold("excessive compression ratio")
                members[path] = info
            if len(roots) != 1:
                raise ArchiveHold("archive contains multiple roots")
            root = next(iter(roots))
            manifest_path = root + "/protocol-manifest.json"
            receipt_path = root + "/BUILD_RECEIPT.json"
            if manifest_path not in members or receipt_path not in members:
                raise ArchiveHold("missing internal manifest or receipt")
            manifest = json.loads(z.read(manifest_path))
            receipt = json.loads(z.read(receipt_path))
            if manifest.get("production_authorised") is not False or receipt.get("production_authorised") is not False:
                raise ArchiveHold("unapproved archive activation")
            rows = manifest.get("files")
            if not isinstance(rows, list) or not rows:
                raise ArchiveHold("manifest inventory absent")
            if receipt.get("inventory", {}).get("manifested_files") != len(rows):
                raise ArchiveHold("inventory count mismatch")
            if len(members) != len(rows) + 1:
                raise ArchiveHold("unmanifested or missing archive files")
            claimed = set()
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                    raise ArchiveHold("invalid inventory entry")
                rel = row["path"]
                if rel in claimed or rel == "protocol-manifest.json" or PurePosixPath(rel).is_absolute() or ".." in PurePosixPath(rel).parts:
                    raise ArchiveHold("duplicate or unsafe inventory entry")
                claimed.add(rel)
                path = root + "/" + rel
                if path not in members:
                    raise ArchiveHold("manifested file missing")
                raw = z.read(path)  # CRC checked by ZipFile.
                if row.get("size_bytes") != len(raw) or row.get("sha256") != _sha(raw):
                    raise ArchiveHold("manifested payload hash/size mismatch")
            if set(members) != {manifest_path} | {root + "/" + rel for rel in claimed}:
                raise ArchiveHold("archive inventory not exact")
            return {
                "status": "ARCHIVE_VERIFIED_NOT_DEPLOYED",
                "archive_sha256": expected,
                "archive_size_bytes": st.st_size,
                "manifested_files_verified": len(rows),
                "schema_count_reported": receipt.get("inventory", {}).get("json_schemas"),
                "source_count_reported": receipt.get("inventory", {}).get("default_solidity_sources"),
                "disabled_template_count_reported": receipt.get("inventory", {}).get("gated_disabled_templates"),
                "native_dbr_finality_proven": False,
                "peer_network_proven": False,
                "contract_compilation_proven": False,
                "drive_sharing_changed": False,
            }
    except (OSError, zipfile.BadZipFile, RuntimeError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ArchiveHold("archive validation failed") from exc

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--canon", type=Path, required=True)
    args = p.parse_args()
    try:
        result = audit(args.archive, json.loads(args.canon.read_text(encoding="utf-8")))
    except (ArchiveHold, OSError, json.JSONDecodeError) as exc:
        p.exit(2, f"COIN_ARCHIVE_HOLD: {exc}\n")
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
