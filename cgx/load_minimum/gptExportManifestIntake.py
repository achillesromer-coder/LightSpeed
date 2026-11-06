#!/usr/bin/env python3
"""LOAD.cgx: bounded, non-authoritative ChatGPT export-manifest R0 intake.

This examines an explicitly supplied local export_manifest.json only. It does
not open, parse, extract, mirror or upload conversation bodies, assets or chats.
It can stage a private metadata projection; no provider rights or Object_ID
authority are created by a valid export manifest. Source body access is an
independent, authenticated, scoped next step.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

SCHEMA = "LOAD-GPT-EXPORT-MANIFEST-INTAKE/0.1"
MAX_MANIFEST_BYTES = 5 * 1024 * 1024
MAX_FILES = 100_000
MAX_LOGICAL = 100_000
MAX_PATH_LENGTH = 500
SHARD_RE = re.compile(r"conversations-(\d{3})\.json\Z")


class IntakeHold(ValueError):
    """Source manifest is not a valid safe source-reference input."""


def _safe_path(path: object) -> str:
    if not isinstance(path, str) or not path or len(path) > MAX_PATH_LENGTH:
        raise IntakeHold("UNSAFE_MANIFEST_PATH")
    if (path.startswith(("/", "~")) or "\\" in path
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in path)
            or ":" in path):
        raise IntakeHold("UNSAFE_MANIFEST_PATH")
    parts = PurePosixPath(path).parts
    if not parts or any(part in ("..", ".") for part in path.split("/")):
        raise IntakeHold("UNSAFE_MANIFEST_PATH")
    if PurePosixPath(path).as_posix() != path:
        raise IntakeHold("UNSAFE_MANIFEST_PATH")
    return path


def project_manifest_bytes(raw: bytes) -> dict:
    if not raw or len(raw) > MAX_MANIFEST_BYTES:
        raise IntakeHold("MANIFEST_SIZE_HOLD")
    try:
        manifest = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise IntakeHold("INVALID_MANIFEST_JSON") from exc

    if (not isinstance(manifest, dict)
            or type(manifest.get("version")) is not int
            or manifest["version"] != 1
            or not isinstance(manifest.get("export_files"), list)
            or not isinstance(manifest.get("logical_files"), dict)
            or manifest.get("manifest_file") != "export_manifest.json"):
        raise IntakeHold("MANIFEST_SCHEMA_HOLD")

    files = manifest["export_files"]
    logical = manifest["logical_files"]
    if len(files) > MAX_FILES or len(logical) > MAX_LOGICAL:
        raise IntakeHold("MANIFEST_ENTRY_LIMIT")

    sizes = {}
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "size_bytes"}:
            raise IntakeHold("UNEXPECTED_EXPORT_FILE_SHAPE")
        name = _safe_path(item["path"])
        size = item["size_bytes"]
        if type(size) is not int or size < 0 or size > 10**13:
            raise IntakeHold("INVALID_EXPORT_SIZE")
        if name in sizes:
            raise IntakeHold("DUPLICATE_EXPORT_PATH")
        sizes[name] = size

    if set(logical) == set():
        raise IntakeHold("LOGICAL_INDEX_EMPTY")
    physical_usage = set()
    for logical_name, record in logical.items():
        _safe_path(logical_name)
        if not isinstance(record, dict) or not isinstance(record.get("files"), list):
            raise IntakeHold("INVALID_LOGICAL_MEMBER")
        filenames = record["files"]
        if not filenames or len(filenames) > MAX_FILES:
            raise IntakeHold("INVALID_LOGICAL_MEMBER")
        if len(set(map(str, filenames))) != len(filenames):
            raise IntakeHold("DUPLICATE_LOGICAL_MEMBER")
        for member in filenames:
            member = _safe_path(member)
            if member not in sizes:
                raise IntakeHold("LOGICAL_SOURCE_MISSING")
            physical_usage.add(member)
        if not isinstance(record.get("sharded"), bool):
            raise IntakeHold("LOGICAL_SHARD_FLAG_INVALID")
        if "shard_count" in record:
            if (type(record["shard_count"]) is not int
                    or record["shard_count"] != len(filenames)):
                raise IntakeHold("SHARD_COUNT_MISMATCH")

    con = logical.get("conversations.json")
    if not isinstance(con, dict) or con.get("sharded") is not True:
        raise IntakeHold("CONVERSATION_SHARDS_UNDECLARED")
    if con.get("shard_count") != len(con["files"]):
        raise IntakeHold("CONVERSATION_COUNT_MISMATCH")
    names = con["files"]
    if not all(isinstance(name, str) and SHARD_RE.fullmatch(name) for name in names):
        raise IntakeHold("CONVERSATION_SHARD_NAME_HOLD")
    if names != [f"conversations-{i:03d}.json" for i in range(len(names))]:
        raise IntakeHold("NONCONTIGUOUS_CONVERSATION_SHARDS")

    shards = [{"path": name, "declared_size_bytes": sizes[name],
               "r0_body_sha256": None, "body_bytes_verified": False}
              for name in names]

    return {
        "schema": SCHEMA,
        "state": "R0_EXPORT_MANIFEST_BYTES_VERIFIED_ONLY",
        "file_space": "LOAD.cgx",
        "parent": "Cognigrex.cgx",
        "source_manifest": {
            "file_name": "export_manifest.json",
            "byte_size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "version": 1,
        },
        "summary": {
            "physical_entries_declared": len(files),
            "logical_entries_declared": len(logical),
            "declared_physical_bytes": sum(sizes.values()),
            "conversation_shard_count": len(shards),
            "declared_conversation_bytes": sum(sizes[x] for x in names),
            "logical_referenced_file_count": len(physical_usage),
            "declared_only": True,
        },
        "conversation_shards": shards,
        "privacy": {
            "classification": "RESTRICTED_PRIVATE_CHAT_EXPORT_METADATA",
            "source_owner_acl": "PROVIDER_VERIFICATION_REQUIRED",
            "source_rights": "OWNER_ONLY_UNTIL_RIGHTS_REVIEW",
            "no_public_original_body_transfer": True,
        },
        "effects": {
            "source_bodies_read": 0,
            "source_bodies_copied": 0,
            "network_fetches": 0,
            "object_ids_minted": 0,
            "canonical_db_writes": 0,
        },
        "admission": "MANIFEST_R0_READ_ONLY_NOT_NATIVE",
        "frontier": [
            "Actual conversation shard bytes and per-shard SHA-256 not verified",
            "Provider original ACL, consent and identity need individual review",
            "Manifest entries are declarations, not actual external file availability",
            "Native RootAuthority, signed lease, DBR and child receiver readback pending",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        if (not args.manifest.is_file()
                or args.manifest.stat().st_size > MAX_MANIFEST_BYTES):
            raise IntakeHold("MANIFEST_FILE_NOT_PRESENT_OR_TOO_LARGE")
        projection = project_manifest_bytes(args.manifest.read_bytes())
    except (IntakeHold, OSError) as exc:
        print(json.dumps({"schema": SCHEMA, "state": "HOLD",
                          "reason": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(projection, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
