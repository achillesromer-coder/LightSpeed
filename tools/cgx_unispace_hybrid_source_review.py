#!/usr/bin/env python3
"""Compose existing CGX archive, PR and cross-space source reviews into ONE projection.

No secondary scheduler, database, model, CGX root, native runtime, DBR, source
hydration, deployment, merge, mint, archive deletion or publication.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.cgx_automation_archive_review import review as review_archive
from tools.cgx_unispace_branch_convergence import review_git_snapshot, ROOT
from tools.cgx_unispace_overlap_review import review_overlap

SCHEMA = "CGX-UNISPACE-HYBRID-SOURCE-PROJECTION/0.1"
SPACES = ("FileSpace","DataSpace","SocialSpace","PrintSpace","IntelligenceSpace")
DOMAINS = (
    {"id":"romer","owner":"Romer.cgx","role":"engineering / enterprise"},
    {"id":"eco","owner":"Eco.cgx","role":"ecology / living systems"},
    {"id":"emassc","owner":"EMASSC.cgx","role":"research / methods / assurance"},
    {"id":"lightspeed","owner":"LS.cgx","parent":"EMASSC.cgx","role":"execution runtime"},
)

class HybridHold(ValueError):
    """Multiple source reviews cannot be joined under one qualified identity."""

def compose(snapshot, footprints, gates=None, observations=None):
    ancestry = review_git_snapshot(snapshot, gates)
    overlaps = review_overlap(footprints)
    archive = review_archive(observations) if observations is not None else None
    if ancestry["canonical_root"] != ROOT or overlaps["canonical_root"] != ROOT or (
        archive is not None and archive["canonical_root"] != ROOT
    ):
        raise HybridHold("source projection escaped canonical root")
    current = {r["number"]: r for r in snapshot["records"]}
    stale = []
    historical = []
    for p in footprints["source_pull_requests"]:
        n = p["pr"]
        if n not in current:
            historical.append(n)
        elif current[n]["head_sha"] != p["head_sha"]:
            stale.append({
                "pr":n,"snapshot_head":current[n]["head_sha"],
                "overlap_head":p["head_sha"],"state":"HOLD_SOURCE_HEAD_MOVED"
            })
    open_review_count = ancestry["observed_pr_count"]
    blockers = [
        {"id":"PR_SOURCE_REVIEW","state":"HOLD_NOT_OWNER_APPROVED"},
        {"id":"SOURCE_PATH_COLLISIONS","state":"HOLD_UNPROVEN_SEMANTIC_EQUIVALENCE"},
        {"id":"NATIVE_FILESPACE_DATASPACE_DBR","state":"HOLD_NO_SIGNED_INDEPENDENT_READBACK"},
        {"id":"RIGHTS_RETENTION_AND_RESTORE","state":"HOLD_OWNER_AND_SOURCE_PROOF"},
        {"id":"PUBLIC_RELEASE","state":"HOLD_NOT_AUTHORISED"},
    ]
    if not ancestry["source_gate_reviewed"]:
        blockers.append({"id":"CROSSSPACE_REGISTER","state":"HOLD_ORIGINAL_REGISTER_NOT_SUPPLIED"})
    if archive is None:
        blockers.append({"id":"AUTOMATION_HISTORY","state":"HOLD_PRIVATE_PROVIDER_RECORDS_NOT_SUPPLIED"})
    if stale:
        blockers.append({"id":"PINNED_HEAD_PARITY","state":"HOLD_SOURCE_REVISIONS_DIFFER"})
    if ancestry["external_review_bases"]:
        blockers.append({"id":"BRANCH_DEPENDENCY","state":"HOLD_BASE_NOT_IN_OPEN_PR_SNAPSHOT"})
    res = {
        "schema": SCHEMA,
        "canonical_root": ROOT,
        "projection_state":"OPEN_SOURCE_REVIEW_NO_NATIVE_PROMOTION",
        "domain_classes":list(DOMAINS),
        "facets":[{"id":s,"kind":"EXISTING_UNISPACE_WORKSPACE_PROJECTION",
                   "native_enabled":False,"source_only":True} for s in SPACES],
        "source_reviews": {
            "pr_graph_sha256":ancestry["review_sha256"],
            "changed_path_sha256":overlaps["review_sha256"],
            "automation_review_sha256":archive["review_sha256"] if archive else None,
        },
        "open_pr_records":open_review_count,
        "overlap_pairs":overlaps["overlap_pair_count"],
        "unique_overlapping_paths":overlaps["unique_overlapping_paths"],
        "cross_space_gates_read_back":ancestry["gate_count"],
        "historic_prs_in_comparison":sorted(historical),
        "source_head_mismatches":sorted(stale, key=lambda x:x["pr"]),
        "pending_conditions":blockers,
        "recommended_review_order":[
            "SOURCE_HEAD_AND_PROVIDER_IDENTITY_PARITY",
            "EXACT_DIFF_ANCESTRY_AND_RIGHTS",
            "ONE_COGNIGREX_PARENT_AND_REUSE_OF_CHILD_DOMAINS",
            "FILESPACE_R0_R3_REVERSIBLE_HYDRATION_VALIDATION",
            "DATASPACE_SIGNED_INDEPENDENT_TWO_NODE_DBR",
            "FIVE_FACET_UNISPACE_GUI_SECURITY_AND_UAT",
            "PRINTSPACE_SEPARATE_PHYSICAL_QUALIFICATION",
            "OWNER_RELEASE_PACKAGING_SUPPORT_AND_OUTREACH",
            "OWNER_TARGETED_ARCHIVE_CLEANUP_AFTER_RESTORE_PROOF",
        ],
        "historic_automation_run_history_complete": False,
        "source_body_hydrated": False,
        "native_dbr_performed": False,
        "merge_performed": False,
        "publish_performed": False,
        "archive_deleted": False,
        "new_root_created": False,
        "new_scheduler_created": False,
        "model_trained": False,
    }
    data = json.dumps(res, separators=(",",":"), sort_keys=True, ensure_ascii=True).encode("ascii")
    res["review_sha256"] = hashlib.sha256(data).hexdigest()
    return res

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--prs", type=Path,required=True)
    cli.add_argument("--overlaps",type=Path,required=True)
    cli.add_argument("--gates",type=Path)
    cli.add_argument("--observations",type=Path)
    args=cli.parse_args()
    files=[x for x in (args.prs,args.overlaps,args.gates,args.observations) if x]
    if any(p.stat().st_size>500000 for p in files):
        raise HybridHold("unbounded input")
    def load(p):
        return json.loads(p.read_text(encoding="utf-8")) if p else None
    print(json.dumps(compose(load(args.prs),load(args.overlaps),
                             load(args.gates),load(args.observations)),indent=2,sort_keys=True))

if __name__ == "__main__":
    main()
