#!/usr/bin/env python3
"""Validate the PrintSpace pre-DBR archive review register; never mutate archives.

This is a syntax/invariant check of source-identification declarations, NOT a
verification of external Git blobs, CI downloads, semantic equivalence, or
Achilles/owner approvals. Archive/move/delete operations are deliberately absent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "cgx" / "manufacturing" / "printspace_pre_dbr_archive_register_v0_1.json"
SCHEMA = "CGX-PRINTSPACE-PRE-DBR-ARCHIVE-REGISTER/0.1"
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CANDIDATE_STATES = {"READY_FOR_ACHILLES_ARCHIVE_REVIEW", "HOLD_UNTIL_EVIDENCE_CAPTURE"}
PROTECTED_STATES = {"RETAIN_CANONICAL", "RETAIN_SOURCE_REFERENCE", "RETAIN_EVIDENCE"}
REQUIRED_GATES = {
    "EXACT_NATIVE_SOURCE_IDENTITY_AND_HASH_READBACK",
    "UNIQUE_CONTENT_AND_REFERENCE_SCAN",
    "SEMANTIC_CROSSWALK_AND_NONLOSS_PROOF",
    "RIGHTS_AND_PRIVACY_CLASSIFICATION",
    "PARENT_DESTINATION_AND_VERSIONED_RECOVERY_PROOF",
    "ACHILLES_REVIEW_RECEIPT",
    "SEPARATE_OWNER_AUTHORITY_FOR_MUTATION",
    "POST_ARCHIVE_READBACK_AND_ROLLBACK",
}
EXPECTED_PROTECTED = {
    "cgx/component_atlas/pc01_printceptor_operational_contract_v0_1.json",
    "cgx/manufacturing/review_gate.py",
    "cgx/manufacturing/printspace_owner_matrix_projection_v0_1.json",
    "cgx/manufacturing/compiler.py",
    "cgx/manufacturing/printstack.py",
    "cgx/manufacturing/binding.py",
    "cgx/manufacturing/volumetric.py",
    "cgx/component_atlas/component_geometry_atlas_v0_1.json",
    "cgx/component_atlas/raphael_component_geometry_search_v0_1.json",
}


class RegisterHold(ValueError):
    """A register is incomplete or could promote an unauthorised action."""


def _is_sha1(value: Any) -> bool:
    return isinstance(value, str) and SHA1.fullmatch(value) is not None


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def _fail(message: str) -> None:
    raise RegisterHold(message)


def validate_register(doc: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        _fail("unsupported pre-DBR schema")
    if doc.get("status") != "PROPOSED / READ_ONLY / NO_LIVE_DBR_MUTATION":
        _fail("pre-DBR status cannot be promoted by this document")
    if doc.get("domain") != "Romer.cgx / PrintSpace / PC01-NODE-001":
        _fail("unexpected archive domain")
    authority = doc.get("authorities")
    if not isinstance(authority, dict) or authority.get("archive_destination_semantics") != "Cognigrex.cgx:/archive-dbr":
        _fail("missing existing parent DBR destination")
    invariant = doc.get("invariant_policy")
    if not isinstance(invariant, dict):
        _fail("missing mutation invariants")
    for field in ("archive_execution_authorised", "delete_execution_authorised",
                  "overwrite_execution_authorised", "dbr_finalised",
                  "owner_approved", "receipts_synthetic", "no_file_moves_performed"):
        expected = field == "no_file_moves_performed"
        if invariant.get(field) is not expected:
            _fail("unsafe or missing mutation invariant: " + field)
    if invariant.get("git_history_and_legacy_bytes_retained") is not True:
        _fail("historical source retention cannot be waived")
    if invariant.get("unknown_references_are_holds") is not True:
        _fail("unknown source references must remain a hold")
    if invariant.get("protected_remote_desktop_reserve_pct") != 25 or invariant.get("emergency_remote_desktop_floor_pct") != 24:
        _fail("RDC normal/emergency reserves are changed")
    gates = doc.get("archive_review_gates")
    if not isinstance(gates, list) or len(gates) != len(set(gates)) or not REQUIRED_GATES.issubset(set(gates)):
        _fail("required archive review/rollback gates absent")
    if not isinstance(doc.get("next_safe_action"), str) or "do not" not in doc["next_safe_action"].lower():
        _fail("missing non-executing next action")
    candidates = doc.get("candidates")
    protected = doc.get("protected_active")
    if not isinstance(candidates, list) or not candidates or not isinstance(protected, list) or not protected:
        _fail("missing candidate or retained source register")
    ids: set[str] = set()
    source_keys: set[tuple[str, str]] = set()
    for row in candidates:
        if not isinstance(row, dict):
            _fail("invalid candidate")
        ident = row.get("id")
        if not isinstance(ident, str) or not ident.startswith("PC01-ARCH-") or ident in ids:
            _fail("duplicate or invalid archive candidate ID")
        ids.add(ident)
        if row.get("classification") not in ("SUPERSEDED", "EVIDENCE_ARCHIVE_CANDIDATE"):
            _fail("candidate has an invalid classification")
        if row.get("disposition") not in CANDIDATE_STATES:
            _fail("candidate cannot be declared archived or deletable")
        if row.get("archive_allowed_now") is not False or row.get("deletion_allowed_now") is not False or row.get("acknowledgement_receipt") is not None:
            _fail("candidate attempts to authorise archiving/deletion or invents a DBR receipt")
        if row.get("unique_content_proven_identical") is not False:
            _fail("semantic/byte identity cannot be asserted without comparison")
        for key in ("observed_state", "relationship", "restore", "action_for_achilles"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                _fail("candidate missing traceability: " + str(ident) + ":" + key)
        blockers = row.get("outstanding_gates")
        if not isinstance(blockers, list) or len(blockers) < 2 or not all(isinstance(v, str) and v.strip() for v in blockers):
            _fail("candidate missing independent review gates")
        source = row.get("source")
        successor = row.get("successor")
        if not isinstance(source, dict) or not isinstance(successor, dict):
            _fail("candidate source or successor not specified")
        if source.get("type") == "git_blob":
            if row.get("classification") != "SUPERSEDED" or not _is_sha1(source.get("git_blob_sha1")) or not _is_sha1(source.get("git_ref")):
                _fail("superseded source needs exact historical Git SHA1s")
            if source.get("readback_verified") is not True or source.get("repository") != "achillesromer-coder/LightSpeed":
                _fail("superseded source identity not independently read back")
            if successor.get("type") != "active_review_branch_file" or not _is_sha1(successor.get("git_blob_sha1")):
                _fail("successor must be identified by exact active blob SHA1")
            pair = ("git_blob", str(source.get("path")))
        elif source.get("type") == "github_actions_artifact":
            if row.get("classification") != "EVIDENCE_ARCHIVE_CANDIDATE" or row.get("disposition") != "HOLD_UNTIL_EVIDENCE_CAPTURE":
                _fail("CI artifact cannot be immediately archived")
            if not _is_sha256(source.get("archive_sha256")) or not isinstance(source.get("run_id"), int) or not isinstance(source.get("artifact_id"), int):
                _fail("CI artifact missing exact run and zip digest")
            if not _is_sha256(successor.get("archive_sha256")) or successor.get("type") != "github_actions_artifact":
                _fail("CI successor not source bound")
            if source["archive_sha256"] == successor["archive_sha256"]:
                _fail("distinct CI runs must not be misidentified as byte-duplicate copies")
            pair = ("github_actions_artifact", str(source["artifact_id"]))
        else:
            _fail("unknown archive candidate source type")
        if pair in source_keys:
            _fail("duplicate archive source reference")
        source_keys.add(pair)
    protected_ids: set[str] = set()
    protected_paths: set[str] = set()
    for row in protected:
        if not isinstance(row, dict) or row.get("disposition") not in PROTECTED_STATES:
            _fail("protected reference cannot be archived")
        ident = row.get("id")
        if not isinstance(ident, str) or not ident.startswith("PC01-PROT-") or ident in protected_ids:
            _fail("duplicate/invalid protected source")
        protected_ids.add(ident)
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            _fail("missing protected-source rationale")
        if row.get("path") is not None:
            if not isinstance(row["path"], str) or not _is_sha1(row.get("git_blob_sha1")):
                _fail("protected source must have exact Git identity")
            protected_paths.add(row["path"])
            # Verify protected active source against Git's blob identity, not
            # just syntactic SHA1. A stale "current" pointer must fail closed.
            rel = Path(row["path"])
            if rel.is_absolute() or ".." in rel.parts or "\\" in row["path"]:
                _fail("unsafe active-source path")
            active = ROOT / rel
            if not active.is_file():
                _fail("protected canonical source is missing: " + row["path"])
            original = active.read_bytes()
            git_blob_sha1 = hashlib.sha1(b"blob " + str(len(original)).encode("ascii") + b"\0" + original).hexdigest()
            if git_blob_sha1 != row["git_blob_sha1"]:
                _fail("stale protected active Git blob pointer: " + row["path"])
        elif not _is_sha256(row.get("archive_sha256")) or not isinstance(row.get("artifact_id"), int):
            _fail("protected CI artifact must have exact SHA256")
    if EXPECTED_PROTECTED - protected_paths:
        _fail("a canonical PrintSpace source is missing from the protected register")
    for row in candidates:
        if row["source"]["type"] == "git_blob" and row["source"]["path"] in protected_paths:
            _fail("current protected source incorrectly listed for archive review")
    return {
        "schema": "CGX-PRINTSPACE-PRE-DBR-VALIDATION/0.1",
        "status": "PASS_REGISTER_INVARIANTS_ONLY",
        "candidate_count": len(candidates),
        "protected_count": len(protected),
        "archive_executions": 0,
        "deletions": 0,
        "dbr_mutations": 0,
        "real_source_or_approval_reverified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, default=REGISTER)
    args = parser.parse_args()
    try:
        doc = json.loads(args.register.read_text(encoding="utf-8"))
        result = validate_register(doc)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"state": "HOLD", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
