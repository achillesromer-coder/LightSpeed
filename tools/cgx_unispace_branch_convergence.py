#!/usr/bin/env python3
"""Deterministic source-only PR convergence plan for the existing UniSpace root.

Consumes pinned *public* GitHub metadata and optionally the existing PR #232
cross-space register. A source graph is not a Git merge, DBR or release receipt.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

SNAPSHOT_SCHEMA = "CGX-UNISPACE-GIT-PR-SOURCE-SNAPSHOT/0.1"
PLAN_SCHEMA = "CGX-UNISPACE-DEPENDENCY-CONVERGENCE-PLAN/0.1"
GATE_SCHEMA = "CGX-UNISPACE-CROSSSPACE-GATE-REGISTRY/0.1"
ROOT = "cgx:root:cognigrex"
REPO = "achillesromer-coder/LightSpeed"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
MAX_RECORDS = 150
CANONICAL = {
    205: "LOAD_ALEXANDRIA_SOURCE",
    206: "BOOTSTRAP_SOURCE",
    228: "PERSISTENCE_PARENT",
    229: "MOBILE_SECONDARY_ENDPOINT",
    230: "LIVING_CONSOLIDATION",
    232: "FIVE_SPACE_SOURCE_FACETS",
    233: "PUBLIC_GATEWAY_SOURCE",
    236: "PRINTSPACE_MANUFACTURING_SOURCE",
}
FACETS = {
    "FileSpace", "DataSpace", "SocialSpace",
    "PrintSpace", "IntelligenceSpace", "UniSpace", "ArchiveAndLegacy"
}

class ConvergenceHold(ValueError):
    """Unverified branch/source graph; no promotion or merge."""

def _string(value: Any, field: str, limit: int = 300) -> str:
    if (not isinstance(value, str) or not value or len(value) > limit
            or any(ord(x) < 32 or ord(x) == 127 for x in value)):
        raise ConvergenceHold("invalid " + field)
    return value

def _toposort(dependencies: dict[Any, set[Any]]) -> list[list[Any]]:
    """A stable topological layering; fail closed on any cycle or missing node."""
    nodes = set(dependencies)
    if any(not parents <= nodes for parents in dependencies.values()):
        raise ConvergenceHold("unresolved dependency in declared graph")
    pending = {node: set(parents) for node, parents in dependencies.items()}
    layers = []
    while pending:
        ready = sorted(x for x, deps in pending.items() if not deps)
        if not ready:
            raise ConvergenceHold("dependency graph contains a cycle")
        layers.append(ready)
        for node in ready:
            del pending[node]
        for deps in pending.values():
            deps.difference_update(ready)
    return layers

def review_git_snapshot(snapshot: dict[str, Any], gates: dict[str, Any] | None = None) -> dict[str, Any]:
    if (not isinstance(snapshot, dict) or snapshot.get("schema") != SNAPSHOT_SCHEMA
            or snapshot.get("canonical_root") != ROOT
            or snapshot.get("repository") != REPO
            or snapshot.get("scope") != "PUBLIC_LIGHTSPEED_REPOSITORY_PR_METADATA_ONLY"):
        raise ConvergenceHold("wrong snapshot or new canonical root")
    rows = snapshot.get("records")
    if not isinstance(rows, list) or len(rows) > MAX_RECORDS:
        raise ConvergenceHold("unbounded PR set")
    if snapshot.get("total_open_prs") != len(rows):
        raise ConvergenceHold("count mismatch")
    if any(snapshot.get("authority", {}).get(k) is not False
           for k in ("merge", "owner_approval", "native_dbr", "mint",
                     "archive_delete", "public_release")):
        raise ConvergenceHold("an observation cannot confer authority")
    if snapshot.get("no_new_root") is not True or snapshot.get("no_new_scheduler") is not True:
        raise ConvergenceHold("unexpected root or scheduler")
    nums: dict[int, dict[str, Any]] = {}
    branches: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ConvergenceHold("invalid PR row")
        n = row.get("number")
        if not isinstance(n, int) or isinstance(n, bool) or n <= 0 or n in nums:
            raise ConvergenceHold("duplicate or invalid PR number")
        if row.get("state") != "open" or not isinstance(row.get("draft"), bool):
            raise ConvergenceHold("not an observed open PR")
        head = _string(row.get("head_branch"), "head branch")
        base = _string(row.get("base_branch"), "base branch")
        sha = row.get("head_sha")
        if not isinstance(sha, str) or not HEX40.fullmatch(sha):
            raise ConvergenceHold("missing exact head")
        _string(row.get("title"), "title", 2000)
        if row.get("source_url") != f"https://github.com/{REPO}/pull/{n}":
            raise ConvergenceHold("unexpected source reference")
        if head in branches:
            raise ConvergenceHold("shared head branch ambiguity")
        if head == base:
            raise ConvergenceHold("self-base PR")
        if row.get("owner_review") != "OPEN_UNVERIFIED":
            raise ConvergenceHold("unsupported implicit PR approval")
        if row.get("mergeability") != "NOT_REVALIDATED_FOR_SNAPSHOT":
            raise ConvergenceHold("stale mergeability may not confer approval")
        branches[head] = n
        nums[n] = row

    dependencies: dict[int, set[int]] = {}
    external_bases: list[dict[str, Any]] = []
    for n, row in nums.items():
        base = row["base_branch"]
        parent = branches.get(base)
        dependencies[n] = {parent} if parent is not None else set()
        if parent is None and base != "main":
            external_bases.append({"pr": n, "base": base, "status": "HOLD_UNRESOLVED_REVIEW_BASE"})
    layers = _toposort(dependencies)
    for edge in snapshot.get("selected_review_edges", []):
        if (not isinstance(edge, dict) or edge.get("relationship") != "BASE_BRANCH_PARENT"
                or edge.get("from") not in nums or edge.get("to") not in nums
                or edge["from"] not in dependencies[edge["to"]]):
            raise ConvergenceHold("curated parent edge disagrees with GitHub metadata")

    gate_counts: dict[str, int] = {}
    source_gate_ref = snapshot.get("composition_ref")
    if not isinstance(source_gate_ref, dict) or source_gate_ref.get("source_groups") != 51:
        raise ConvergenceHold("source gate reference missing")
    if gates is not None:
        if (not isinstance(gates, dict) or gates.get("schema") != GATE_SCHEMA
                or gates.get("canonical_root") != ROOT
                or gates.get("source_count") != 51):
            raise ConvergenceHold("wrong 51-group source register")
        entries = gates.get("task_groups")
        if not isinstance(entries, list) or len(entries) != 51:
            raise ConvergenceHold("source gate list mismatch")
        by_id = {}
        for g in entries:
            if not isinstance(g, dict):
                raise ConvergenceHold("invalid gate")
            gid = _string(g.get("id"), "gate id")
            if gid in by_id or g.get("space") not in FACETS:
                raise ConvergenceHold("duplicate gate or unknown facet")
            if (g.get("state") != "OPEN_REVIEW_ONLY"
                    or g.get("owner_approval_observed") is not False
                    or g.get("effectful_action_authorised") is not False):
                raise ConvergenceHold("gate promoted without independent evidence")
            by_id[gid] = g
            gate_counts[g["space"]] = gate_counts.get(g["space"], 0) + 1
        gate_deps = {}
        for gid, g in by_id.items():
            parents = g.get("proposed_dependencies")
            if not isinstance(parents, list) or any(not isinstance(p, str) for p in parents):
                raise ConvergenceHold("invalid gate dependency list")
            gate_deps[gid] = set(parents)
        _toposort(gate_deps)

    stage = []
    for level, group in enumerate(layers):
        for n in group:
            row = nums[n]
            stage.append({
                "number": n, "title": row["title"], "source_url": row["source_url"],
                "head_sha": row["head_sha"], "base_branch": row["base_branch"],
                "parent_prs": sorted(dependencies[n]), "dependency_layer": level,
                "role": CANONICAL.get(n, "HISTORICAL_OR_CANDIDATE_SOURCE"),
                "state": "DRAFT_REVIEW_HOLD" if row["draft"] else "OPEN_REVIEW_HOLD",
                "mergeable_now": "NOT_EVALUATED", "approved_for_merge": False,
                "published_or_native": False,
            })
    result = {
        "schema": PLAN_SCHEMA, "canonical_root": ROOT,
        "status": "SOURCE_REVIEW_ONLY_NO_MERGE",
        "observed_pr_count": len(rows), "dependency_layers": layers,
        "branch_parent_links": sum(bool(parents) for parents in dependencies.values()),
        "external_review_bases": sorted(external_bases, key=lambda x: x["pr"]),
        "review_order": stage, "source_gate_ref": source_gate_ref,
        "source_gate_reviewed": gates is not None,
        "gate_counts": dict(sorted(gate_counts.items())),
        "gate_count": sum(gate_counts.values()),
        "overlap_holds": [
            "PR235_CLOSED_UNMERGED_GUI_SOURCE_COMPARE_WITH_PR232_NOT_BYTE_EQUIVALENT",
            "PR231_CLOSED_UNMERGED_SOURCE_MANIFEST_CHECK_SEPARATELY",
            "PR232_BEHIND_UPDATED_PR230_BASE_REQUIRES_ANCESTRY_RECONCILIATION",
            "PR236_PRINTSPACE_REVIEW_PASSES_SOFTWARE_CI_NOT_PHYSICAL_READINESS",
            "PR205_LOAD_REQUIRES_SEPARATE_SOURCE_RIGHTS_AND_PROVENANCE",
        ],
        "source_bytes_copied": False, "native_dbr_write_performed": False,
        "model_training_performed": False, "merge_performed": False,
        "archive_deleted": False, "public_release_performed": False,
        "new_root_created": False, "new_scheduler_created": False,
        "next_gate": "INDEPENDENT_SOURCE_DIFF_CI_RIGHTS_AND_OWNER_MERGE_REVIEW",
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    result["review_sha256"] = hashlib.sha256(payload).hexdigest()
    return result

def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--snapshot", type=Path, required=True)
    cli.add_argument("--gates", type=Path)
    args = cli.parse_args()
    if args.snapshot.stat().st_size > 250000 or args.gates and args.gates.stat().st_size > 500000:
        raise ConvergenceHold("unbounded input file")
    data = json.loads(args.snapshot.read_text(encoding="utf-8"))
    gates = json.loads(args.gates.read_text(encoding="utf-8")) if args.gates else None
    print(json.dumps(review_git_snapshot(data, gates), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
