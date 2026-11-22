"""Deterministic CGX Git ancestry + cross-space negative regression tests."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from tools.cgx_unispace_branch_convergence import (
    ConvergenceHold, SNAPSHOT_SCHEMA, GATE_SCHEMA, ROOT, REPO, review_git_snapshot,
)

SNAPSHOT = Path(__file__).resolve().parents[1] / "cgx/review/unispace_git_pr_source_snapshot_20261122.json"

def row(n, head, base="main"):
    return {
        "number":n,"title":"Reviewed source","head_branch":head,"head_sha":"a"*40,
        "base_branch":base,"source_url":f"https://github.com/{REPO}/pull/{n}",
        "draft":True,"state":"open","mergeability":"NOT_REVALIDATED_FOR_SNAPSHOT",
        "owner_review":"OPEN_UNVERIFIED"
    }

def snap(*records):
    return {
        "schema":SNAPSHOT_SCHEMA,"canonical_root":ROOT,"repository":REPO,
        "scope":"PUBLIC_LIGHTSPEED_REPOSITORY_PR_METADATA_ONLY",
        "records":list(records),"total_open_prs":len(records),
        "selected_review_edges":[],"composition_ref":{"source_groups":51},
        "authority":dict.fromkeys(["merge","owner_approval","native_dbr","mint",
                                    "archive_delete","public_release"],False),
        "no_new_root":True,"no_new_scheduler":True,
    }

def gate_rows():
    return {
        "schema":GATE_SCHEMA,"canonical_root":ROOT,"source_count":51,
        "task_groups":[{"id":f"G-{i:02}","space":"FileSpace","state":"OPEN_REVIEW_ONLY",
                        "effectful_action_authorised":False,
                        "owner_approval_observed":False,"proposed_dependencies":
                        [f"G-{i-1:02}"] if i else []} for i in range(51)]
    }

class ConvergenceTests(unittest.TestCase):
    def test_real_dated_snapshot_is_review_only(self):
        r=review_git_snapshot(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
        self.assertEqual(r["observed_pr_count"],74)
        self.assertFalse(r["merge_performed"])
        self.assertFalse(r["native_dbr_write_performed"])
        self.assertFalse(r["public_release_performed"])
        self.assertFalse(r["source_gate_reviewed"])
        self.assertEqual(r["gate_count"],0)

    def test_dependency_order_and_no_promotion(self):
        r=review_git_snapshot(snap(row(1,"base"),row(2,"child","base")))
        self.assertEqual(r["dependency_layers"],[[1],[2]])
        self.assertEqual(r["branch_parent_links"],1)
        self.assertTrue(all(not p["approved_for_merge"] for p in r["review_order"]))

    def test_bytewise_determinism(self):
        s=snap(row(2,"child","base"),row(1,"base"))
        r=review_git_snapshot(s)
        s["records"].reverse()
        self.assertEqual(r["review_sha256"], review_git_snapshot(s)["review_sha256"])

    def test_unresolved_review_base_is_explicit(self):
        r=review_git_snapshot(snap(row(1,"child","missing-source-branch")))
        self.assertEqual(r["external_review_bases"][0]["pr"],1)

    def test_reject_wrong_root(self):
        s=snap();s["canonical_root"]="cgx:root:duplicate"
        with self.assertRaises(ConvergenceHold):review_git_snapshot(s)

    def test_reject_claimed_authority(self):
        s=snap();s["authority"]["merge"]=True
        with self.assertRaises(ConvergenceHold):review_git_snapshot(s)

    def test_reject_count_drift(self):
        s=snap(row(1,"a"));s["total_open_prs"]=2
        with self.assertRaises(ConvergenceHold):review_git_snapshot(s)

    def test_reject_duplicate_pr_identity(self):
        with self.assertRaises(ConvergenceHold):
            review_git_snapshot(snap(row(1,"a"),row(1,"b")))

    def test_reject_duplicate_branch_identity(self):
        with self.assertRaises(ConvergenceHold):
            review_git_snapshot(snap(row(1,"a"),row(2,"a")))

    def test_reject_invalid_sha(self):
        with self.assertRaises(ConvergenceHold):
            review_git_snapshot(snap(row(1,"a",head_sha="notsha")))

    def test_reject_self_base(self):
        with self.assertRaises(ConvergenceHold):
            review_git_snapshot(snap(row(1,"a","a")))

    def test_reject_cycles(self):
        with self.assertRaises(ConvergenceHold):
            review_git_snapshot(snap(row(1,"one","two"),row(2,"two","one")))

    def test_reject_curated_edge_not_in_source(self):
        s=snap(row(1,"a"),row(2,"b"))
        s["selected_review_edges"]=[{"from":1,"to":2,"relationship":"BASE_BRANCH_PARENT"}]
        with self.assertRaises(ConvergenceHold):review_git_snapshot(s)

    def test_reject_undocumented_mergeability(self):
        s=snap(row(1,"a"));s["records"][0]["mergeability"]="true"
        with self.assertRaises(ConvergenceHold):review_git_snapshot(s)

    def test_reject_unverified_approval(self):
        s=snap(row(1,"a"));s["records"][0]["owner_review"]="APPROVED"
        with self.assertRaises(ConvergenceHold):review_git_snapshot(s)

    def test_provided_gate_register_is_structurally_checked(self):
        r=review_git_snapshot(snap(row(1,"a")),gate_rows())
        self.assertEqual(r["gate_count"],51)
        self.assertEqual(r["gate_counts"]["FileSpace"],51)
        self.assertFalse(r["merge_performed"])

    def test_reject_promoted_gate(self):
        g=gate_rows();g["task_groups"][0]["owner_approval_observed"]=True
        with self.assertRaises(ConvergenceHold):
            review_git_snapshot(snap(),g)

    def test_reject_missing_gate(self):
        g=gate_rows();g["task_groups"].pop()
        with self.assertRaises(ConvergenceHold):
            review_git_snapshot(snap(),g)

    def test_reject_gate_dependency_cycle(self):
        g=gate_rows();g["task_groups"][0]["proposed_dependencies"]=["G-50"]
        with self.assertRaises(ConvergenceHold):
            review_git_snapshot(snap(),g)

    def test_reject_unknown_gate_space(self):
        g=gate_rows();g["task_groups"][0]["space"]="ExtraRoot"
        with self.assertRaises(ConvergenceHold):
            review_git_snapshot(snap(),g)

    def test_reject_new_scheduler(self):
        s=snap();s["no_new_scheduler"]=False
        with self.assertRaises(ConvergenceHold):review_git_snapshot(s)

    def test_reject_bad_original_link(self):
        s=snap(row(1,"a"));s["records"][0]["source_url"]="https://example.com"
        with self.assertRaises(ConvergenceHold):review_git_snapshot(s)

if __name__=="__main__":
    unittest.main()
