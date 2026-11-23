"""Preserve historic source, prove branch overlay and reject false assimilation."""
import copy
import json
from pathlib import Path

import pytest

from tools.cgx_unispace_attempt_unification_review import AttemptHold, reconcile

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "cgx/review/unispace_all_attempt_convergence_overlay_20261123.json"


def source():
    return json.loads(PATH.read_text("utf-8"))


def test_retro_source_and_focal_branch_counts_are_independent():
    r = reconcile(ROOT, source())
    assert r["canonical_root"] == "cgx:root:cognigrex"
    assert r["original_open_snapshot_count"] == 74
    assert r["closed_unmerged_prior_attempts"] == [231, 235]
    assert r["currently_reobserved_focal_count"] == 9
    assert r["unique_public_pr_source_ids"] == 76
    assert r["original_crossspace_gate_count"] == 51
    assert r["historical_overlap_source_count"] == 7
    assert r["source_only_merge_authorized_by_ledger"] is False
    assert r["native_admitted"] is False
    assert r["production_published"] is False


def test_history_review_is_reproducible_and_originals_unchanged():
    assert reconcile(ROOT, source()) == reconcile(ROOT, source())
    r = reconcile(ROOT, source())
    assert len(r["review_sha256"]) == 64
    assert r["branch_ancestry_verified_from_declared_metadata"] is True
    assert r["branch_ancestry_verified_against_live_git"] is False


@pytest.mark.parametrize("field,value", [
    ("canonical_root", "cgx:root:second"),
    ("status", "NATIVE_ACCEPTED"),
    ("repository", "unexpected/parallel-repo"),
])
def test_wrong_parent_and_false_promotion_are_rejected(field, value):
    raw = source()
    raw[field] = value
    with pytest.raises(AttemptHold):
        reconcile(ROOT, raw)


def test_mutated_original_source_blob_is_rejected():
    raw = source()
    raw["historic_public_inputs"]["source_pr_snapshot"]["git_blob"] = "0" * 40
    with pytest.raises(AttemptHold, match="blob changed"):
        reconcile(ROOT, raw)


def test_branch_ancestry_cannot_skip_parent():
    raw = source()
    target = next(r for r in raw["current_focal_pr_observations"] if r["pr"] == 232)
    target["base_branch"] = "main"
    with pytest.raises(AttemptHold, match="ancestor"):
        reconcile(ROOT, raw)


def test_closed_source_attempt_cannot_be_represented_as_merged():
    raw = source()
    target = next(r for r in raw["current_focal_pr_observations"] if r["pr"] == 235)
    target["merged"] = True
    with pytest.raises(AttemptHold):
        reconcile(ROOT, raw)


def test_merge_queue_may_not_claim_public_deployment():
    raw = source()
    raw["merge_queue"][0]["public_deploy"] = True
    with pytest.raises(AttemptHold):
        reconcile(ROOT, raw)


def test_previous_source_candidate_may_not_be_lost():
    raw = source()
    raw["history_groups"][-1]["source_prs"].remove(232)
    with pytest.raises(AttemptHold, match="current attempts"):
        reconcile(ROOT, raw)


def test_overlapping_source_branches_may_not_gain_implicit_authority():
    raw = source()
    raw["invariants"]["source_branch_merged_in_this_manifest"] = True
    with pytest.raises(AttemptHold):
        reconcile(ROOT, raw)


def test_unresolved_rights_and_native_gates_cannot_be_removed():
    raw = source()
    raw["release_gates"] = []
    with pytest.raises(AttemptHold):
        reconcile(ROOT, raw)


def test_foreign_predecessor_ref_denied():
    raw = source()
    raw["history_groups"][0]["source_prs"].append(999999)
    with pytest.raises(AttemptHold, match="invented"):
        reconcile(ROOT, raw)
