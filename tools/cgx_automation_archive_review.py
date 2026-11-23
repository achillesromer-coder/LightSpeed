#!/usr/bin/env python3
"""Read-only CGX projection of automation outputs, archives and historical records.

No source deletion, new authority, native DBR, model training or publication.
Original provider records remain authoritative. Inputs must be owner-approved
snapshots; this module never fetches provider content or runs a scheduler.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime
from collections import Counter
from pathlib import Path

SCHEMA = "CGX-AUTOMATION-ARCHIVE-REVIEW/0.1"
INPUT = "CGX-AUTOMATION-ARCHIVE-OBSERVATIONS/0.1"
ROOT = "cgx:root:cognigrex"
FACETS = {"file_space", "data_space", "social_space", "print_space", "intelligence_space"}
SYSTEMS = {"chatgpt_automation", "github", "google_drive", "canva", "local", "other"}
KINDS = {"automation_task", "automation_run", "artifact", "document", "repository_change", "historical_record"}
DOMAINS = {"cognigrex", "romer", "eco", "emassc", "lightspeed", "unassigned"}
GATES = (
    "ORIGINAL_PROVIDER_BYTES_AND_SOURCE_IDENTITY_READBACK",
    "COMPLETE_DEPENDENT_REFERENCE_AND_SEMANTIC_COVERAGE",
    "RIGHTS_PRIVACY_ACL_AND_RETENTION_REVIEW",
    "INDEPENDENT_SIGNED_DBR_READBACK_FROM_AUTHORISED_NODES",
    "INDEPENDENT_ARCHIVE_RESTORE_TEST",
    "EXACT_TARGET_OWNER_APPROVAL",
    "POST_ACTION_READBACK_AND_RECOVERY_RECEIPT",
)

class ReviewHold(ValueError):
    """The proposed evidence record cannot be reliably reconciled."""

def identifier(value, name):
    if not isinstance(value, str) or not value or len(value) > 240 or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ReviewHold("invalid " + name)
    return value

def timestamp(value):
    identifier(value, "timestamp")
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReviewHold("invalid timestamp") from exc
    if d.utcoffset() is None:
        raise ReviewHold("missing timestamp offset")
    return d.isoformat()

def review(payload):
    if not isinstance(payload, dict) or payload.get("schema") != INPUT or payload.get("canonical_root") != ROOT:
        raise ReviewHold("wrong source envelope or extra CGX root")
    source = payload.get("observations")
    if not isinstance(source, list) or len(source) > 1000:
        raise ReviewHold("invalid or unbounded observation batch")
    seen = {}
    duplicates = 0
    for item in source:
        if not isinstance(item, dict):
            raise ReviewHold("invalid observation")
        system, kind, domain, facet = (item.get(k) for k in ("source_system", "source_kind", "domain", "facet"))
        if not all(isinstance(x, str) for x in (system, kind, domain, facet)) or system not in SYSTEMS or kind not in KINDS or domain not in DOMAINS or facet not in FACETS:
            raise ReviewHold("unknown source or facet")
        sid = identifier(item.get("source_id"), "source_id")
        revision = identifier(item.get("revision_id"), "revision_id")
        locator = identifier(item.get("source_locator"), "source_locator")
        observed_at = timestamp(item.get("observed_at"))
        active = item.get("is_active", False)
        truncated = item.get("truncated", False)
        if not isinstance(active, bool) or not isinstance(truncated, bool):
            raise ReviewHold("invalid state flags")
        body = item.get("content_text")
        if body is not None and (not isinstance(body, str) or len(body) > 1000000):
            raise ReviewHold("invalid or unbounded source body")
        claimed = item.get("content_sha256")
        if claimed is not None and (not isinstance(claimed, str) or len(claimed) != 64 or any(x not in "0123456789abcdef" for x in claimed)):
            raise ReviewHold("invalid claimed SHA-256")
        computed = hashlib.sha256(body.encode("utf-8")).hexdigest() if body is not None else None
        if claimed and computed and computed != claimed:
            raise ReviewHold("conflicting source bytes for claimed digest")
        state = ("HOLD_TRUNCATED" if truncated else "HASHED_TEXT_OBSERVED" if computed
                 else "HOLD_METADATA_ONLY" if kind == "automation_task" else "HOLD_SOURCE_BYTES_UNOBSERVED")
        record = {
            "source_system": system, "source_kind": kind, "source_id": sid,
            "revision_id": revision, "source_locator": locator,
            "observed_at": observed_at, "is_active": active,
            "domain": domain, "facet": facet, "source_state": state,
            "source_sha256": computed or claimed,
            "hash_evidence": "HASHED_INLINE_TEXT" if computed else "DECLARED_ONLY" if claimed else "UNKNOWN",
            "truncated": truncated, "original_source_retained": True,
            "native_dbr_admitted": False, "semantics_admitted": False,
            "model_training_authorized": False, "public_release_authorized": False,
            "deletion_authorized": False,
        }
        key = (system, kind, sid, revision)
        if key in seen:
            if seen[key] != record:
                raise ReviewHold("conflicting duplicate identity / revision")
            duplicates += 1
        else:
            seen[key] = record
    records = [seen[k] for k in sorted(seen)]
    output = {
        "schema": SCHEMA, "canonical_root": ROOT,
        "status": "SOURCE_REVIEW_ONLY_NO_NATIVE_ADMISSION",
        "received": len(source), "unique": len(records), "duplicate_count": duplicates,
        "held": sum(r["source_state"].startswith("HOLD") for r in records),
        "facet_counts": dict(sorted(Counter(r["facet"] for r in records).items())),
        "observations": records, "pre_archive_gates": list(GATES),
        "archive_deletion_performed": False, "source_mutation_performed": False,
        "native_dbr_write_performed": False, "model_training_performed": False,
        "public_release_performed": False, "new_root_created": False,
        "new_scheduler_created": False, "historical_coverage_complete": False,
    }
    encoded = json.dumps(output, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    output["review_sha256"] = hashlib.sha256(encoded).hexdigest()
    return output

def from_automations_peek(peek, observed_at):
    """Normalise listed tasks and latest available results, never claim full history."""
    timestamp(observed_at)
    tasks = peek.get("automations") if isinstance(peek, dict) else None
    if not isinstance(tasks, list) or len(tasks) > 500:
        raise ReviewHold("bounded automation list required")
    observations = []
    for task in tasks:
        tid = identifier(task.get("id"), "task id")
        enabled = task.get("is_enabled")
        if not isinstance(enabled, bool):
            raise ReviewHold("missing enabled state")
        version = task.get("updated_at") or observed_at
        timestamp(version)
        base = {
            "source_system": "chatgpt_automation", "source_id": tid,
            "source_locator": "automation:" + tid, "domain": "cognigrex",
            "facet": "intelligence_space", "observed_at": observed_at,
            "is_active": enabled,
        }
        observations.append({**base, "source_kind": "automation_task", "revision_id": "task@" + version})
        latest = (task.get("run_details") or {}).get("latest_result")
        if latest is not None:
            runid = identifier(latest.get("run_id"), "run id")
            body = latest.get("content_text")
            if not isinstance(body, str):
                raise ReviewHold("latest result body absent")
            observations.append({
                **base, "source_kind": "automation_run", "revision_id": "run@" + runid,
                "source_locator": "automation:" + tid + "/run/" + runid,
                "content_text": body, "truncated": latest.get("content_truncated", False),
            })
    return {"schema": INPUT, "canonical_root": ROOT, "observations": observations}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--peek", action="store_true")
    p.add_argument("--observed-at")
    args = p.parse_args()
    if args.input.stat().st_size > 4000000:
        raise ReviewHold("input too large")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if args.peek:
        if not args.observed_at:
            raise ReviewHold("--observed-at required for peek")
        payload = from_automations_peek(payload, args.observed_at)
    print(json.dumps(review(payload), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
