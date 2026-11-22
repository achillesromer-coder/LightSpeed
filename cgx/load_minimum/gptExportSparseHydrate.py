#!/usr/bin/env python3
"""LOAD/Alexandria: private, source-bound sparse R1 verification and selective hydration.

Uses the existing original-R0 manifest and shard validators. R1 is *not*
a standalone body store: the original owner-private R0 bytes are required.
No network, shell execution, public output, native DBR, mint or source mutation.
An embedding host must independently enforce ACL, lease and user consent.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Callable

from cgx.load_minimum.gptExportManifestIntake import IntakeHold, project_manifest_bytes
from cgx.load_minimum.gptExportShardReview import (
    RECORD_HASH_ALGORITHM, inspect_originals, inspect_raw_shard,
)

SCHEMA = "LOAD-ORIGINAL-R0-SPARSE-R1-HYDRATION/0.1"
R1_SCHEMA = "CGX-ALEXANDRIA-ORIGINAL-12-SHARD-SPARSE-R1/0.2"
R1_PARENT = "cgx:root:cognigrex"
R1_SCOPE = "SHARD_FILENAME_PLUS_RECORD_ORDINAL_PLUS_NODE_KEY"
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
MAX_INDEX_BYTES = 8 * 1024 * 1024
MAX_R0_BYTES = 128 * 1024 * 1024
RECORD_KEYS = {
    "mapping_nodes", "ordinal", "source_native_object_id_admitted",
    "source_record_bytes_canonical", "source_record_sha256",
}

def _require(condition: bool, code: str) -> None:
    if not condition:
        raise IntakeHold(code)

def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def _unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        _require(key not in obj, "DUPLICATE_JSON_OBJECT_KEY")
        obj[key] = value
    return obj

def _parse(raw: bytes, code: str):
    try:
        return json.loads(
            raw,
            object_pairs_hook=_unique_pairs,
            parse_constant=lambda name: (_ for _ in ()).throw(ValueError(name)),
        )
    except IntakeHold:
        # Preserve the precise fail-closed source-integrity code for diagnostics.
        raise
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise IntakeHold(code) from exc

def validate_sparse_index(manifest_raw: bytes, index_raw: bytes) -> tuple[dict, dict]:
    """Verify source-scoped R1 metadata against an independently supplied R0 manifest."""
    _require(isinstance(manifest_raw, bytes), "MANIFEST_BYTES_REQUIRED")
    manifest = project_manifest_bytes(manifest_raw)
    _require(isinstance(index_raw, bytes) and 0 < len(index_raw) <= MAX_INDEX_BYTES,
             "R1_INDEX_BYTES_BOUND")
    index = _parse(index_raw, "INVALID_SPARSE_R1_JSON")
    _require(isinstance(index, dict)
             and index.get("schema") == R1_SCHEMA
             and index.get("canonical_parent") == R1_PARENT
             and index.get("canonical_record_encoding") == RECORD_HASH_ALGORITHM
             and index.get("source_manifest_sha256") == _digest(manifest_raw)
             and index.get("source_sha256_algorithm") == "SHA-256 over original unmodified raw file bytes"
             and index.get("source_body_copied_into_index") is False
             and index.get("source_message_content_extracted") is False
             and index.get("native_mint") is False
             and index.get("dbr_written") is False
             and index.get("full_lossless_reconstruction_without_R0") is False,
             "R1_SOURCE_CLASSIFICATION_OR_MANIFEST_MISMATCH")
    shards = index.get("shards")
    declared = manifest["conversation_shards"]
    _require(isinstance(shards, list) and len(shards) == len(declared),
             "R1_SHARD_COUNT_MISMATCH")
    total_records = total_nodes = 0
    for shard, dec in zip(shards, declared):
        _require(isinstance(shard, dict)
                 and shard.get("filename") == dec["path"]
                 and isinstance(shard.get("R0_sha256"), str)
                 and HEX64.fullmatch(shard["R0_sha256"]) is not None
                 and shard.get("source_rights") == "UNRESOLVED_PRIVATE_DO_NOT_PUBLISH"
                 and shard.get("reconstruction") == "ORIGINAL_R0_REQUIRED_FOR_LOSSLESS_HYDRATION",
                 "R1_SHARD_REFERENCE_MISMATCH")
        rows = shard.get("records")
        _require(isinstance(rows, list) and 0 < len(rows) <= 1000
                 and shard.get("record_count") == len(rows), "R1_RECORD_COUNT_MISMATCH")
        for pos, row in enumerate(rows):
            _require(isinstance(row, dict) and set(row) == RECORD_KEYS
                     and type(row.get("ordinal")) is int and row["ordinal"] == pos
                     and row.get("source_native_object_id_admitted") is False
                     and type(row.get("mapping_nodes")) is int and row["mapping_nodes"] >= 0
                     and type(row.get("source_record_bytes_canonical")) is int
                     and row["source_record_bytes_canonical"] > 0
                     and isinstance(row.get("source_record_sha256"), str)
                     and HEX64.fullmatch(row["source_record_sha256"]) is not None,
                     "R1_RECORD_REFERENCE_MISMATCH")
            total_nodes += row["mapping_nodes"]
        total_records += len(rows)
    totals = index.get("totals")
    _require(isinstance(totals, dict)
             and totals.get("files") == len(shards)
             and totals.get("bytes") == manifest["summary"]["declared_conversation_bytes"]
             and totals.get("records") == total_records
             and totals.get("mapping_nodes") == total_nodes,
             "R1_SOURCE_TOTALS_MISMATCH")
    return manifest, index

def verify_all_originals(manifest_raw: bytes, index_raw: bytes,
                         private_directory: Path) -> dict:
    """Independently compare every original shard and canonical record hash to R1."""
    manifest, index = validate_sparse_index(manifest_raw, index_raw)
    original = inspect_originals(manifest_raw, Path(private_directory))
    _require(original["shard_count"] == index["totals"]["files"]
             and original["original_bytes"] == index["totals"]["bytes"]
             and original["records"] == index["totals"]["records"]
             and original["mapping_nodes"] == index["totals"]["mapping_nodes"],
             "R0_R1_TOTALS_DIVERGED")
    for raw_shard, indexed in zip(original["shards"], index["shards"]):
        _require(raw_shard["name"] == indexed["filename"]
                 and raw_shard["original_sha256"] == indexed["R0_sha256"],
                 "R0_R1_SHARD_HASH_DIVERGED")
        for actual, candidate in zip(raw_shard["record_index"], indexed["records"]):
            _require(actual["ordinal"] == candidate["ordinal"]
                     and actual["canonical_sha256"] == candidate["source_record_sha256"]
                     and actual["mapping_nodes"] == candidate["mapping_nodes"],
                     "R0_R1_CANONICAL_RECORD_DIVERGED")
    return {
        "schema": SCHEMA,
        "state": "OWNER_PRIVATE_R0_R1_CANONICAL_PARITY_VERIFIED_NOT_NATIVE",
        "canonical_root": R1_PARENT,
        "shards": original["shard_count"],
        "records": original["records"],
        "original_bytes": original["original_bytes"],
        "mapping_nodes": original["mapping_nodes"],
        "r0_manifest_sha256": _digest(manifest_raw),
        "r1_index_sha256": _digest(index_raw),
        "source_indexed_hydration_available": True,
        "originals_required": True,
        "host_acl_and_signed_lease_verified": False,
        "native_dbr_verified": False,
        "minted": False,
        "published": False,
        "raw_messages_in_receipt": False,
    }

def resolve_private_record(manifest_raw: bytes, index_raw: bytes,
                           private_directory: Path, shard_name: str, ordinal: int,
                           *, authorize_read: Callable[[dict], bool]) -> tuple[dict, dict]:
    """Hydrate one record in process, only following an explicit host-policy callback.

    The callback is *not* a signed-host proof. An authenticated embedding runtime
    must supply a real ACL/lease verifier; this function never transfers authority.
    The returned record is private and must not be logged, cached publicly or
    placed into static/public bundles.
    """
    manifest, index = validate_sparse_index(manifest_raw, index_raw)
    _require(type(ordinal) is int and isinstance(shard_name, str),
             "R1_INVALID_LOCATOR")
    declared = manifest["conversation_shards"]
    names = [d["path"] for d in declared]
    _require(shard_name in names, "R1_UNDECLARED_OR_UNSAFE_SHARD")
    position = names.index(shard_name)
    r1shard = index["shards"][position]
    _require(0 <= ordinal < len(r1shard["records"]), "R1_ORDINAL_OUT_OF_RANGE")
    _require(callable(authorize_read), "PRIVATE_HOST_POLICY_CALLBACK_REQUIRED")
    scope = {
        "action": "OWNER_PRIVATE_SOURCE_RECORD_READ",
        "canonical_root": R1_PARENT,
        "source_shard": shard_name,
        "source_record_ordinal": ordinal,
        "requested_capability": "SELECTIVE_SOURCE_HYDRATION",
    }
    try:
        accepted = authorize_read(dict(scope))
    except Exception as exc:
        raise IntakeHold("HOST_POLICY_CHECK_FAILED") from exc
    _require(accepted is True, "PRIVATE_HOST_POLICY_DENIED")
    directory = Path(private_directory).resolve(strict=True)
    _require(directory.is_dir(), "PRIVATE_SOURCE_DIRECTORY_REQUIRED")
    target = directory / shard_name
    _require(target.parent == directory and not target.is_symlink()
             and target.is_file() and target.resolve() == target
             and target.stat().st_size == declared[position]["declared_size_bytes"]
             and target.stat().st_size <= MAX_R0_BYTES,
             "PRIVATE_R0_FILE_OR_SIZE_HOLD")
    raw = target.read_bytes()
    _require(_digest(raw) == r1shard["R0_sha256"], "R1_SOURCE_SHA256_DIVERGED")
    contents = _parse(raw, "PRIVATE_SOURCE_JSON_INVALID")
    _require(isinstance(contents, list) and len(contents) == r1shard["record_count"],
             "R1_SOURCE_SHARD_CARDINALITY_HOLD")
    record = contents[ordinal]
    _require(isinstance(record, dict) and isinstance(record.get("mapping"), dict)
             and isinstance(record.get("id"), str) and bool(record["id"])
             and isinstance(record.get("conversation_id"), str)
             and bool(record["conversation_id"]), "INVALID_SOURCE_RECORD")
    try:
        canonical = json.dumps(
            record, sort_keys=True, separators=(",",":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
    except (TypeError, UnicodeError, ValueError, RecursionError) as exc:
        raise IntakeHold("R1_CANONICAL_SERIALISATION_FAILED") from exc
    row = r1shard["records"][ordinal]
    _require(_digest(canonical) == row["source_record_sha256"]
             and len(canonical) == row["source_record_bytes_canonical"]
             and len(record["mapping"]) == row["mapping_nodes"],
             "R1_TARGET_CANONICAL_RECORD_DIVERGED")
    receipt = {
        "schema": SCHEMA,
        "state": "OWNER_PRIVATE_SINGLE_RECORD_HYDRATED_IN_PROCESS",
        "canonical_root": R1_PARENT,
        "source_shard": shard_name,
        "source_ordinal": ordinal,
        "original_shard_sha256": _digest(raw),
        "canonical_record_sha256": _digest(canonical),
        "original_r0_required": True,
        "host_policy_callback_accepted": True,
        "independent_host_signature_verified": False,
        "native_dbr_verified": False,
        "minted": False,
        "published": False,
        "private_record_in_receipt": False,
    }
    return record, receipt
