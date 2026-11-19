#!/usr/bin/env python3
"""Read-only CGX family-occurrence -> canonical FileSpace admission crosswalk.

No FamilyStore import, SQLite access, source-body read, content grant, signed
lease, native dispatch, mint or model training. Source-review role labels are
not host-authenticated roles. This produces a metadata-only adapter proposal.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA = "CGX-NATIVE-OCCURRENCE-CROSSWALK/0.1"
ROOT = "cgx:root:cognigrex"
DATABASE = "lightspeed_unified.db"
MAX_ROWS = 512
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ROLES = frozenset({"Raphael", "Achilles", "Neo", "Athene"})
RIGHTS = frozenset({"owner-private", "review-only", "public-licence-verified"})


class CrosswalkHold(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, ensure_ascii=True).encode("ascii")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(item: dict) -> dict:
    if not isinstance(item, dict):
        raise CrosswalkHold("occurrence must be a dictionary")
    path, sha, agent, rights = (item.get(x) for x in
                                ("path", "source_sha256", "agent", "rights"))
    granted = item.get("content_granted")
    if not isinstance(sha, str) or not HEX64.fullmatch(sha):
        raise CrosswalkHold("source SHA-256 invalid")
    if (not isinstance(path, str) or not 0 < len(path) <= 4096
            or any(x in path for x in ("\0", "\r", "\n"))):
        raise CrosswalkHold("source path invalid")
    if (not isinstance(agent, str) or agent not in ROLES
            or not isinstance(rights, str) or rights not in RIGHTS):
        raise CrosswalkHold("unrecognized review role or rights")
    if granted is not None and type(granted) is not bool:
        raise CrosswalkHold("invalid review content-grant field")
    identity = "review-occurrence:" + digest(canonical(
        {"path": path, "sha256": sha, "agent": agent}))
    holds = []
    if granted is None:
        holds.append("LEGACY_OR_UNSCOPED_GRANT_UNKNOWN")
    elif granted is False:
        holds.append("METADATA_ONLY_CONTENT_NOT_GRANTED")
    if rights == "public-licence-verified":
        holds.append("PUBLIC_LICENCE_REQUIRES_INDEPENDENT_ADMISSION")
    return {
        "provisional_occurrence_ref": identity,
        "source_sha256": sha,
        "review_agent_label": agent,
        "review_rights_label": rights,
        "content_granted_in_review": granted is True,
        "source_path_exported": False,
        "native_acl_verified": False,
        "native_issuer_verified": False,
        "native_lease_verified": False,
        "content_access_authorized": False,
        "hold_reasons": holds,
    }


def plan_occurrences(rows: list[dict]) -> dict:
    """Idempotent source-only plan: one occurrence per role/path/hash."""
    if type(rows) is not list or len(rows) > MAX_ROWS:
        raise CrosswalkHold("occurrence count exceeds bounded review")
    indexed = {}
    for item in rows:
        normalized = normalize(item)
        key = normalized["provisional_occurrence_ref"]
        if key in indexed and indexed[key] != normalized:
            raise CrosswalkHold("conflicting rights/grant for same occurrence")
        indexed[key] = normalized
    records = sorted(indexed.values(),
                     key=lambda item: item["provisional_occurrence_ref"])
    per_sha: dict[str, set[str]] = {}
    for row in records:
        per_sha.setdefault(row["source_sha256"], set()).add(
            row["provisional_occurrence_ref"])
    reasons = sorted({reason for row in records for reason in row["hold_reasons"]})
    receipt = {
        "schema": SCHEMA,
        "state": "REVIEW_REFERENCES_READY_FOR_NATIVE_ADAPTER"
        if records and not reasons else "HOLD_SOURCE_OCCURRENCE_GRANTS",
        "canonical_root": ROOT,
        "canonical_database": DATABASE,
        "occurrence_count": len(records),
        "distinct_source_sha_count": len(per_sha),
        "same_bytes_distinct_occurrence_sha": sorted(
            sha for sha, refs in per_sha.items() if len(refs) > 1),
        "records": records,
        "hold_reasons": reasons,
        "no_secondary_database_created": True,
        "native_acl_authenticated": False,
        "native_issuer_signature_verified": False,
        "native_content_access_authorized": False,
        "native_mint_authorized": False,
        "training_performed": False,
        "db_or_source_bytes_read": False,
        "native_execution_performed": False,
        "source_content_exported": False,
        "required_next_gate": "OWNER_VERIFIED_NATIVE_OCCURRENCE_ACL_LEASE_AND_DBR",
    }
    receipt["receipt_sha256"] = digest(canonical(receipt))
    return receipt


def from_review_search(results: list[dict]) -> dict:
    """Consume FamilyStore.source_search records without importing FamilyStore.

    Unscoped review searches omit content_granted; unknown is never upgraded
    based on the existence of the matching content-addressed blob.
    """
    if type(results) is not list or len(results) > MAX_ROWS:
        raise CrosswalkHold("unbounded review search")
    rows = []
    for result in results:
        if not isinstance(result, dict) or type(result.get("occurrences")) is not list:
            raise CrosswalkHold("invalid review search entry")
        sha = result.get("sha256")
        if not isinstance(sha, str) or not HEX64.fullmatch(sha):
            raise CrosswalkHold("review search SHA missing")
        for occ in result["occurrences"]:
            if not isinstance(occ, dict):
                raise CrosswalkHold("invalid source occurrence")
            rows.append({
                "path": occ.get("path"),
                "source_sha256": sha,
                "agent": occ.get("agent"),
                "rights": occ.get("rights"),
                "content_granted": occ.get("content_granted"),
            })
            if len(rows) > MAX_ROWS:
                raise CrosswalkHold("unbounded nested occurrence list")
    return plan_occurrences(rows)
