#!/usr/bin/env python3
"""Source-only CGX surface fold into the EXISTING open-thread register.

Consumes a PRIVATE local worktree audit but exports counts and GitHub-public
source-tree references only. Never moves files, deletes worktrees, merges
repos, issues objects, or writes a second master registry.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

FIELD = "cross_surface_fold_review_20261111"
SCHEMA = "CGX-CROSS-SURFACE-FOLD-REVIEW/0.1"
GATES = tuple("G%02d" % n for n in range(1, 8))
TREE = [
    ("NCNBOUWER/Raphael", "02b0d869e2fad14c3565fe8a1822fa143637182c",
     184, "Raphael geometry and mathematical evidence"),
    ("achillesromer-coder/Romer-MPL", "58a8f2f1c6f8853047e2450e2a25a0a763273d54",
     40, "Romer MPL and engineering proof"),
    ("achillesromer-coder/LightSpeed", "e46ca5e888dac9035f41f4b52a1cdd297b4c8cac",
     1739, "CGX integration code and LS orchestration"),
    ("achillesromer-coder/Operations", "506cf3afbf6f44cdafb44d01176bf7d148d4a44b",
     29, "Operational workflows and calculators"),
    ("achillesromer-coder/Data", "dbff21bffb4d726d5422081133f7001fb081db60",
     202, "Schemas and source-qualified datasets"),
]
EXPECTED_OVERLAPS = frozenset((
    "67b737d466a4ef225857fde70061d4f9686ee4c5",
    "72ceb61ae624e48bd6c7ae8f670a10595ceb17be",
    "8b137891791fe96927ad78e64b0aad7bded08bdc",
    "df26a8d6805c030481a02a304977232676b2e0ec",
))


def review(audit: dict, overlaps: list[dict], source_head: str) -> dict:
    if audit.get("schema") != "CGX-LOCAL-GIT-WORKTREE-LIFECYCLE-AUDIT/0.1":
        raise ValueError("PRIVATE_AUDIT_SCHEMA_HOLD")
    if any(audit.get(k) != 0 for k in
           ("source_deleted", "worktrees_deleted", "git_branch_deleted",
            "cross_surface_delete_ready")):
        raise ValueError("DESTRUCTIVE_LIFECYCLE_HOLD")
    n = audit.get("registered_worktree_count")
    counts = tuple(audit.get(k) for k in ("tracked_clean", "tracked_dirty", "missing"))
    if type(n) is not int or n < 1 or any(type(k) is not int or k < 0 for k in counts):
        raise ValueError("WORKTREE_COUNT_HOLD")
    if sum(counts) != n or audit.get("untracked_files_not_scanned") is not True or \
       audit.get("independent_recovery_confirmed") is not False:
        raise ValueError("INCOMPLETE_WORKTREE_SOURCE_HOLD")
    if not re.fullmatch("[0-9a-f]{40}", source_head):
        raise ValueError("SOURCE_COMMIT_HOLD")
    if len(overlaps) != len(EXPECTED_OVERLAPS) or \
       {k.get("git_blob_sha") for k in overlaps} != EXPECTED_OVERLAPS:
        raise ValueError("EXACT_CROSSREPO_BLOB_EVIDENCE_HOLD")
    allowed = {x[0] for x in TREE}
    for entry in overlaps:
        if len(set(entry["repositories"])) < 2 or \
           any(r not in allowed for r in entry["repositories"]):
            raise ValueError("CROSSREPO_SOURCE_IDENTITY_HOLD")
    return {
        "schema": SCHEMA, "status": "SOURCE_ONLY_NO_NATIVE_AUTHORITY",
        "as_of": "2026-11-11", "parent": "cgx:root:cognigrex",
        "sole_resolver": "LOAD.cgx",
        "integration_pr": 206,
        "integration_branch": "review/cgx-ls-unified-bootstrap-20261028",
        "as_of_integration_head": source_head,
        "public_repositories": [
            {"name": name, "default_branch": "main", "tree_sha": sha,
             "source_file_count": count, "scope": scope,
             "disposition": "RETAIN_DISTINCT_ORIGINAL_SOURCE",
             "snapshot_is_live": False} for name, sha, count, scope in TREE
        ],
        "exact_blob_overlap_groups": [
            {"git_blob_sha": r["git_blob_sha"],
             "repositories": sorted(r["repositories"]),
             "deletion_authorized": False} for r in overlaps
        ],
        "local_worktree_review": {
            "registered": n, "tracked_clean": counts[0],
            "tracked_dirty": counts[1], "missing": counts[2],
            "untracked_not_scanned": True,
            "stale_prune_candidates": 0,
            "worktrees_deleted": 0, "branches_deleted": 0,
            "junction_is_independent_source": False, "closeout_ready": False
        },
        "connected_surfaces": {
            "drive": "PRIVATE_METADATA_POINTERS_ONLY",
            "canva": "CONCURRENT_OWNER_LANE_NO_WRITE",
            "live_source_acl_verified": False,
            "individual_private_assets_exported": False
        },
        "functional_surfaces": [
            {"id": "cognigrex_parent", "owner": "Cognigrex.cgx",
             "contract": "cgx/bootstrap/cgxPhaseAcceptance_v01.json", "state": "SOURCE_ONLY"},
            {"id": "load_resolver", "owner": "LOAD.cgx",
             "contract": "cgx/bootstrap/cgxPremintFamilyProjection.mjs", "state": "SOURCE_ONLY"},
            {"id": "file_space", "owner": "Cognigrex.cgx",
             "contract": "cgx/bootstrap/cgxBatchConvergence.mjs", "state": "NATIVE_ADMISSION_HOLD"},
            {"id": "data_space", "owner": "Cognigrex.cgx",
             "contract": "cgx/domain_templates/payload_capsule_dbr_2026-10-05.json", "state": "INDEPENDENT_DBR_HOLD"},
            {"id": "unispace_product", "owner": "UniSpace",
             "contract": "cgx/load_minimum/unispacePrivateCockpitDom.mjs", "state": "SOURCE_REVIEW_ONLY"},
            {"id": "ls_go_operator", "owner": "EMASSC.cgx",
             "contract": "cgx/bootstrap/smart_setup_surface_contract.json", "state": "HOST_QUALIFICATION_HOLD"},
            {"id": "public_viewer", "owner": "UniSpace",
             "contract": "apps/lightspeed-go/scripts/cgx_public_bundle_guard.py", "state": "PUBLIC_RELEASE_HOLD"},
            {"id": "local_devnet", "owner": "Cognigrex.cgx",
             "contract": "cgx/bootstrap/cgxGenesisPeerReview.py", "state": "LOCAL_REVIEW_HOLD"}
        ],
        "owner_automations": {
            "enabled": 3, "disabled": 2,
            "auto_restart_disabled": False
        },
        "cleanup": {
            "original_source_deletions": 0, "repos_archived": 0,
            "unapproved_archive_moves": 0, "unqualified_delete_candidates": 0,
            "independent_recovery_verified": False, "closure_ready": False,
            "rule": "REQUIRE_EXACT_PROVENANCE_RBAC_CONSUMERS_ACCEPTED_SUCCESSOR_AND_RESTORE_PROOF"
        },
        "release": {
            "gates": {g: "HOLD" for g in GATES},
            "native_mint_authorized": False,
            "independent_dbr_verified": False,
            "production_merge_completed": False,
            "public_launch_verified": False
        },
        "source_evidence": {
            "repo_tree_shas_are_snapshots": True,
            "worktree_private_receipt_sha256": None,
            "provider_readback_required_before_mutation": True
        },
    }


def read_audit(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 3_000_000:
        raise ValueError("PRIVATE_WORKTREE_AUDIT_MISSING_OR_UNTRUSTED")
    return json.loads(path.read_text("utf-8"))


def insert_preserving_original(register_path: Path, payload: dict) -> None:
    raw = register_path.read_text("utf-8")
    root = json.loads(raw)
    if root.get("schema") != "CGX-OPEN-THREAD-EXECUTION-REGISTER/0.2" or \
       root.get("state") != "SOURCE_REVIEW_ONLY" or \
       root.get("release_ready") is not False or \
       root.get("deletion_ready_count") != 0 or FIELD in root:
        raise ValueError("CANONICAL_REGISTER_OR_EXISTING_FIELD_HOLD")
    index = raw.rfind("\n}")
    if index < 0 or raw[index+2:].strip():
        raise ValueError("CANONICAL_FORMAT_HOLD")
    prefix = raw[:index].rstrip()
    block = json.dumps(payload, indent=2, ensure_ascii=False)
    written = prefix + ',\n  "' + FIELD + '": ' + block.replace("\n", "\n  ") + "\n}\n"
    check = json.loads(written)
    if check[FIELD] != payload:
        raise ValueError("REVIEW_WRITE_ROUNDTRIP_HOLD")
    register_path.write_text(written, encoding="utf-8", newline="\n")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--register", type=Path, required=True)
    p.add_argument("--private-audit", type=Path, required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--overlaps-json", type=Path, required=True)
    p.add_argument("--write", action="store_true")
    args = p.parse_args()
    if not args.write:
        raise SystemExit("EXPLICIT_NON_DESTRUCTIVE_WRITE_FLAG_REQUIRED")
    audit_path = args.private_audit
    overlap_list = json.loads(args.overlaps_json.read_text("utf-8"))
    payload = review(read_audit(audit_path), overlap_list, args.head)
    source_root = args.register.resolve().parents[2]
    if any(not (source_root / entry["contract"]).is_file()
           for entry in payload["functional_surfaces"]):
        raise ValueError("FUNCTIONAL_SURFACE_SOURCE_CONTRACT_MISSING")
    payload["source_evidence"]["worktree_private_receipt_sha256"] = \
        hashlib.sha256(audit_path.read_bytes()).hexdigest()
    insert_preserving_original(args.register, payload)
    print(json.dumps({
        "state": "SOURCE_ONLY_REVIEW_COMMITTED_TO_EXISTING_REGISTER",
        "source_repos": len(payload["public_repositories"]),
        "tracked_worktrees": payload["local_worktree_review"]["registered"],
        "original_source_deleted": 0, "repository_archived": 0,
        "native_mint": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
