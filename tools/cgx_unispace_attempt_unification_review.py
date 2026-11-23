#!/usr/bin/env python3
"""One-root retrospective alignment of previous CGX consolidation attempts.

Combines the original 74-PR snapshot, 7-PR overlap sample, 51-gate register
and a strictly sourced overlay of current focal branches. It neither merges
nor deletes code, reads original private source bytes, executes a model,
modifies a scheduler, nor admits native DBR or public release.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from tools.cgx_unispace_branch_convergence import review_git_snapshot
from tools.cgx_unispace_overlap_review import review_overlap

SCHEMA = "CGX-UNISPACE-ALL-ATTEMPT-CONVERGENCE-OVERLAY/0.1"
ROOT = "cgx:root:cognigrex"
REPO = "achillesromer-coder/LightSpeed"
EXPECTED = {205, 228, 229, 230, 231, 232, 233, 235, 236}
CLOSED = {231, 235}
HEX = re.compile(r"^[a-f0-9]{40}$")
NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_./-]{0,175}$")
MAX_BYTES = 250_000


class AttemptHold(ValueError):
    """Source or merge-authority evidence is insufficient."""


def _read_tracked(repo: Path, path: str, expected_blob: str) -> dict:
    if not isinstance(path, str) or not NAME.fullmatch(path):
        raise AttemptHold("unsafe history source reference")
    if not isinstance(expected_blob, str) or not HEX.fullmatch(expected_blob):
        raise AttemptHold("invalid source Git blob identity")
    full = repo / path
    if (not full.is_file() or full.is_symlink()
            or not full.resolve().is_relative_to(repo)
            or not 0 < full.stat().st_size <= MAX_BYTES):
        raise AttemptHold("unavailable original history source")
    done = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "--error-unmatch", "--", path],
        check=False, capture_output=True, timeout=10)
    if done.returncode:
        raise AttemptHold("history is not tracked original source")
    blob = subprocess.run(
        ["git", "-C", str(repo), "hash-object", "--", path],
        check=False, capture_output=True, timeout=10)
    if blob.returncode or blob.stdout.decode().strip() != expected_blob:
        raise AttemptHold("history source Git blob changed")
    payload = json.loads(full.read_text("utf-8"))
    if not isinstance(payload, dict):
        raise AttemptHold("original history file not an object")
    return payload


def reconcile(repo: Path, overlay: dict[str, Any]) -> dict[str, Any]:
    repo = Path(repo).resolve(strict=True)
    if (not isinstance(overlay, dict) or overlay.get("schema") != SCHEMA
            or overlay.get("canonical_root") != ROOT
            or overlay.get("repository") != REPO
            or overlay.get("status") != "SOURCE_REVIEW_ONLY_NOT_NATIVE_ADMISSION"):
        raise AttemptHold("wrong source overlay or competing root")
    refs = overlay.get("historic_public_inputs")
    if not isinstance(refs, dict) or set(refs) != {
        "source_pr_snapshot", "changed_path_overlap", "crossspace_gates"
    }:
        raise AttemptHold("missing original historical evidence")
    originals = {name: _read_tracked(repo, ref["path"], ref["git_blob"])
                 for name, ref in refs.items()}
    original = originals["source_pr_snapshot"]
    overlap = originals["changed_path_overlap"]
    gates = originals["crossspace_gates"]
    if (len(original.get("records", [])) != 74
            or refs["source_pr_snapshot"].get("observed_open_prs") != 74
            or len(overlap.get("source_pull_requests", [])) != 7
            or refs["changed_path_overlap"].get("observed_prs") != 7
            or len(gates.get("task_groups", [])) != 51
            or refs["crossspace_gates"].get("observed_open_gate_groups") != 51):
        raise AttemptHold("retrospective source count changed")
    historical_plan = review_git_snapshot(original, gates)
    overlap_plan = review_overlap(overlap)
    if historical_plan["observed_pr_count"] != 74 or overlap_plan["source_pr_count"] != 7:
        raise AttemptHold("reused historical checks did not validate")
    historic_ids = {r["number"] for r in original["records"]}
    focal = overlay.get("current_focal_pr_observations")
    if not isinstance(focal, list) or len(focal) != len(EXPECTED):
        raise AttemptHold("missing current focal history")
    current = {}
    branches = {}
    for r in focal:
        if not isinstance(r, dict):
            raise AttemptHold("malformed branch evidence")
        n = r.get("pr")
        if not isinstance(n, int) or isinstance(n, bool) or n not in EXPECTED or n in current:
            raise AttemptHold("ambiguous/foreign PR number")
        if not isinstance(r.get("head_sha"), str) or not HEX.fullmatch(r["head_sha"]):
            raise AttemptHold("unverified focal revision")
        head, base = r.get("head_branch"), r.get("base_branch")
        if (not isinstance(head, str) or not NAME.fullmatch(head)
                or not isinstance(base, str) or not NAME.fullmatch(base)
                or head == base or head in branches):
            raise AttemptHold("competing or invalid branch identity")
        if (r.get("source_url") != f"https://github.com/{REPO}/pull/{n}"
                or r.get("merged") is not False
                or r.get("draft") is not True
                or r.get("state") != ("closed" if n in CLOSED else "open")):
            raise AttemptHold("retrospective status cannot be treated as accepted")
        branches[head] = n
        current[n] = r
    if set(current) != EXPECTED:
        raise AttemptHold("unmatched focal PR set")
    history_groups = overlay.get("history_groups")
    if not isinstance(history_groups, list) or len(history_groups) != 4:
        raise AttemptHold("missing prior attempt group coverage")
    grouped = set()
    for group in history_groups:
        if (not isinstance(group, dict)
                or not isinstance(group.get("id"), str)
                or not isinstance(group.get("policy"), str)
                or not isinstance(group.get("source_prs"), list)
                or len(group["source_prs"]) > 75):
            raise AttemptHold("invalid predecessor group")
        for n in group["source_prs"]:
            if (type(n) is not int or n not in historic_ids | set(current)
                    or n in grouped):
                raise AttemptHold("duplicate or invented predecessor")
            grouped.add(n)
    if not EXPECTED <= grouped:
        raise AttemptHold("current attempts not crosswalked into history")
    edges = overlay.get("verified_review_ancestry")
    expected_edges = {(230,228), (232,230), (229,228)}
    if (not isinstance(edges, list) or
            {(e.get("child_pr"),e.get("parent_pr")) for e in edges} != expected_edges
            or len(edges) != 3):
        raise AttemptHold("unexpected source-branch ancestry")
    for edge in edges:
        child, parent = current[edge["child_pr"]], current[edge["parent_pr"]]
        if (edge.get("relation") != "BASE_BRANCH"
                or edge.get("branch") != parent["head_branch"]
                or child["base_branch"] != parent["head_branch"]):
            raise AttemptHold("ancestor does not match current PR base")
    if overlay.get("closed_unmerged_attempts") != [231, 235]:
        raise AttemptHold("historical closed attempts not preserved")
    queue = overlay.get("merge_queue")
    if (not isinstance(queue, list) or len(queue) != 6
            or {x["pr"] for x in queue} != {205, 228, 230, 232, 233, 236}
            or any(x.get("public_deploy") is not False for x in queue)):
        raise AttemptHold("automatic public/production merge is unsupported")
    if (queue[0].get("pr") != 232
            or queue[0].get("target_pr") != 230
            or queue[0].get("target_branch") != current[232]["base_branch"]):
        raise AttemptHold("direct source integration must follow branch ancestry")
    flags = overlay.get("invariants")
    if (not isinstance(flags, dict)
            or flags.get("historical_source_snapshots_immutable") is not True
            or any(v is not False for k, v in flags.items()
                   if k != "historical_source_snapshots_immutable")):
        raise AttemptHold("historical metadata claims unauthorized effects")
    if not isinstance(overlay.get("release_gates"), list) or len(overlay["release_gates"]) < 6:
        raise AttemptHold("release gates must remain explicit")
    digest = hashlib.sha256(json.dumps(
        {"snap":refs, "focal":focal, "groups":history_groups, "ancestry":edges,
         "queue":queue, "gates":overlay["release_gates"]},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()).hexdigest()
    return {
        "schema": "CGX-UNISPACE-ALL-ATTEMPT-CONVERGENCE-REVIEW/0.1",
        "canonical_root": ROOT, "state": "SOURCE_CONVERGENCE_REVIEW_READY",
        "original_open_snapshot_count": len(historic_ids),
        "closed_unmerged_prior_attempts": list(CLOSED if False else [231, 235]),
        "currently_reobserved_focal_count": len(current),
        "unique_public_pr_source_ids": len(historic_ids | set(current)),
        "previous_attempt_group_refs": len(grouped),
        "branch_ancestry_verified_from_declared_metadata": True,
        "branch_ancestry_verified_against_live_git": False,
        "historical_overlap_source_count": overlap_plan["source_pr_count"],
        "original_crossspace_gate_count": historical_plan["gate_count"],
        "new_root_created": False, "native_admitted": False,
        "source_only_merge_authorized_by_ledger": False,
        "models_trained": False, "archive_deleted": False,
        "production_published": False, "private_source_ingested": False,
        "review_sha256": digest,
    }


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--overlay", type=Path)
    a = p.parse_args()
    path = a.overlay or a.repo / "cgx/review/unispace_all_attempt_convergence_overlay_20261123.json"
    if path.stat().st_size > MAX_BYTES:
        raise AttemptHold("unbounded convergence overlay")
    print(json.dumps(reconcile(a.repo, json.loads(path.read_text("utf-8"))),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
