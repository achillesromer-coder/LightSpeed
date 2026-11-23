"""CGX source-only overlap classification regression tests."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from tools.cgx_unispace_overlap_review import (
    review_overlap, OverlapHold, classification, SCHEMA, ROOT, REPO,
)

SOURCE = Path(__file__).resolve().parents[1] / "cgx/review/unispace_source_path_overlap_20261122.json"

def record(number, paths):
    return {"pr": number, "head_sha":"f"*40, "compare_status":"ahead", "paths": paths}

def source(*prs):
    names = {row["pr"]: set(row["paths"]) for row in prs}
    pairs = []
    ns = sorted(names)
    for i, a in enumerate(ns):
        for b in ns[i+1:]:
            common = sorted(names[a] & names[b])
            if common:
                pairs.append({"a":a,"b":b,"shared_paths":common,
                              "review_class":"SOURCE_PATH_OVERLAP_NO_SEMANTIC_EQUIVALENCE"})
    return {"schema":SCHEMA, "canonical_root":ROOT, "repository":REPO,
            "status":"REVIEW_ONLY","source_pull_requests":list(prs),
            "overlapping_pairs":pairs,"authority":dict.fromkeys(
                ("merge","archive_delete","native_dbr","public_release","model_train"),False)}

class OverlapReviewTests(unittest.TestCase):
    def test_real_pinned_source_has_five_pairs(self):
        x=review_overlap(json.loads(SOURCE.read_text('utf-8')))
        self.assertEqual(x["source_pr_count"],7)
        self.assertEqual(x["overlap_pair_count"],5)
        self.assertGreaterEqual(x["unique_overlapping_paths"],19)
        self.assertFalse(x["source_bytes_inspected"])
        self.assertFalse(x["merge_performed"])
        self.assertTrue(all(not p["promotable"] and not p["delete_eligible"] for p in x["path_review"]))

    def test_empty_source_has_zero_assumed_conflicts(self):
        x=review_overlap(source())
        self.assertEqual(x["overlap_pair_count"],0)
        self.assertEqual(x["unique_overlapping_paths"],0)

    def test_shared_path_is_not_equivalence(self):
        x=review_overlap(source(record(1,["tools/a.py"]),record(2,["tools/a.py"])))
        self.assertEqual(x["unique_overlapping_paths"],1)
        self.assertEqual(x["path_review"][0]["semantic_equal"],"NOT_EVALUATED")
        self.assertEqual(x["path_review"][0]["branches"],[1,2])

    def test_symmetric_independent_of_input_order(self):
        a=record(2,["a.py","b.py"]); b=record(1,["b.py"])
        self.assertEqual(review_overlap(source(a,b))["review_sha256"],
                         review_overlap(source(b,a))["review_sha256"])

    def test_build_artifact_is_reproduced_not_source_merged(self):
        self.assertEqual(classification("apps/lightspeed-go/dist/index.html"),
                         "GENERATED_BUILD_REPRODUCE_FROM_VERIFIED_SOURCE")

    def test_python_source_requires_diff(self):
        self.assertEqual(classification("tools/cgx.py"),
                         "SOURCE_THREE_WAY_DIFF_AND_SEMANTIC_REGRESSION")

    def test_reject_stale_pair_list(self):
        x=source(record(1,["a.py"]),record(2,["a.py"]))
        x["overlapping_pairs"]=[]
        with self.assertRaises(OverlapHold):review_overlap(x)

    def test_reject_duplicate_changed_path(self):
        x=source(record(1,["a.py","a.py"]))
        with self.assertRaises(OverlapHold):review_overlap(x)

    def test_reject_bad_pr_head(self):
        x=source(record(1,["a.py"]));x["source_pull_requests"][0]["head_sha"]="bad"
        with self.assertRaises(OverlapHold):review_overlap(x)

    def test_reject_extra_root(self):
        x=source();x["canonical_root"]="cgx:root:second"
        with self.assertRaises(OverlapHold):review_overlap(x)

    def test_reject_unapproved_release(self):
        x=source();x["authority"]["public_release"]=True
        with self.assertRaises(OverlapHold):review_overlap(x)

    def test_reject_path_traversal(self):
        with self.assertRaises(OverlapHold):
            review_overlap(source(record(1,["../private"])))

    def test_reject_unknown_comparison_status(self):
        x=source(record(1,["a.py"]));x["source_pull_requests"][0]["compare_status"]="unknown"
        with self.assertRaises(OverlapHold):review_overlap(x)

    def test_reject_two_same_number_records(self):
        with self.assertRaises(OverlapHold):
            review_overlap(source(record(1,["a.py"]),record(1,["b.py"])))

    def test_no_source_copy_or_native_authority(self):
        x=review_overlap(source(record(1,["a.py"]),record(2,["a.py"])))
        for key in ("archive_deleted","native_dbr_performed","public_release_performed",
                    "new_root_created","semantic_equivalence_claimed"):
            self.assertFalse(x[key])

if __name__=="__main__":
    unittest.main()
