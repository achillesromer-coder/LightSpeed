"""Independent pinned nlohmann Hedley REUSE-vs-SPDX source conflict tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from cgx.portable_node.nlohmann_hedley_notice_reconciliation import (
    HEADERS, TREE_SHAS, STALE_DEP5_PATH, _git_blob, _git_tree,
    resolve_hedley_notice,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "tests" / "fixtures" / "alexandria_nlohmann_json"
SCOPE = ROOT / "cgx" / "review" / "alexandria_nlohmann_json_source_scope_20261021.json"


def input_sources():
    return (
        json.loads(SCOPE.read_text(encoding="utf-8")),
        json.loads((BASE / "tree_chain.json").read_text(encoding="utf-8")),
        json.loads((BASE / "hedley_tree_chain.json").read_text(encoding="utf-8")),
        (BASE / ".reuse" / "dep5").read_bytes(),
        {name: (BASE / name).read_bytes() for name in HEADERS},
    )


def derive():
    return resolve_hedley_notice(*input_sources())


class HedleyNoticeReconciliationTests(unittest.TestCase):
    def test_source_tree_chain_proves_actual_paths_and_missing_old_path(self):
        _,old,new,_,original=input_sources()
        self.assertEqual(_git_tree(new["thirdparty"]), TREE_SHAS["thirdparty"])
        self.assertEqual(_git_tree(new["hedley"]), TREE_SHAS["hedley"])
        self.assertNotIn("hedley.hpp", {x["path"] for x in new["thirdparty"]["entries"]})
        self.assertEqual(new["thirdparty"]["entries"][0]["path"],"hedley")
        self.assertEqual(len(new["hedley"]["entries"]),2)
        self.assertEqual(old["trees"]["include_nlohmann"]["sha"],
                         "dac45ebdad919a94071601f427038b1456da1cbc")
        for path,original_sha in HEADERS.items():
            self.assertEqual(_git_blob(original[path]),original_sha)

    def test_preserves_conflicting_cc0_path_and_real_mit_headers_without_licence_promotion(self):
        out=derive()
        self.assertEqual(out["status"],"REUSE_PATH_MISMATCH_AND_SOURCE_SPDX_CONFLICT_CONFIRMED")
        self.assertEqual(out["dep5_path_declared_as_cc0"],STALE_DEP5_PATH)
        self.assertFalse(out["dep5_exact_path_exists_in_pinned_tree"])
        self.assertEqual(out["conflict"]["dep5_source_claim"],"CC0")
        self.assertEqual(out["conflict"]["real_header_spdx_claim"],"MIT")
        self.assertFalse(out["conflict"]["claimed_cc0_applied_to_real_files"])
        self.assertEqual(out["conflict"]["effective_legal_relicensing_conclusion"],"NOT_DETERMINED")
        self.assertTrue(out["conflict"]["requires_source_owner_or_legal_review"])
        self.assertFalse(out["distribution_approved"])
        self.assertFalse(out["source_bytes_embedded"])
        self.assertFalse(out["native_dbr_verified"])
        self.assertIsNone(out["canonical_object_id"])
        self.assertEqual([x["spdx_in_source_header"] for x in out["actual_header_paths_and_claims"]],
                         ["MIT","MIT"])

    def test_original_header_sha256_and_source_byte_counts(self):
        original=input_sources()[-1]
        for item in derive()["actual_header_paths_and_claims"]:
            raw=original[item["path"]]
            self.assertEqual(item["original_git_blob_sha1"],_git_blob(raw))
            self.assertEqual(item["sha256"],hashlib.sha256(raw).hexdigest())
            self.assertEqual(item["bytes"],len(raw))
            self.assertFalse(item["source_bytes_embedded"])

    def test_tampered_header_reuse_and_tree_hold(self):
        old,oldtree,new,dep,original=input_sources()
        forged=dict(original)
        forged[next(iter(HEADERS))] += b"\n// CC0 FORGED"
        with self.assertRaisesRegex(ValueError,"pinned Hedley header blob mismatch"):
            resolve_hedley_notice(old,oldtree,new,dep,forged)
        with self.assertRaisesRegex(ValueError,"REUSE original byte identity mismatch"):
            resolve_hedley_notice(old,oldtree,new,dep+b"\nFiles: fake\n",original)
        altered=copy.deepcopy(new)
        altered["hedley"]["entries"][0]["sha"]="f"*40
        with self.assertRaisesRegex(ValueError,"Hedley subtree Git hash mismatch"):
            resolve_hedley_notice(old,oldtree,altered,dep,original)

    def test_new_declaration_at_existing_path_invalidates_stale_path_conclusion(self):
        old,oldtree,new,dep,original=input_sources()
        altered=copy.deepcopy(new)
        altered["thirdparty"]["entries"].append({
            "path":"hedley.hpp","mode":"100644","type":"blob","sha":"f"*40})
        with self.assertRaisesRegex(ValueError,"Hedley subtree Git hash mismatch"):
            resolve_hedley_notice(old,oldtree,altered,dep,original)
        forged=copy.deepcopy(old)
        forged["licensing_review"]["distribution_approved"]=True
        with self.assertRaisesRegex(ValueError,"missing source-scope predecessor"):
            resolve_hedley_notice(forged,oldtree,new,dep,original)

    def test_deterministic_with_reordered_headers_and_no_canonical_promotion(self):
        old,oldtree,new,dep,original=input_sources()
        first=resolve_hedley_notice(old,oldtree,new,dep,original)
        second=resolve_hedley_notice(old,oldtree,new,dep,
                                     dict(reversed(list(original.items()))))
        self.assertEqual(first,second)
        self.assertIn("DO_NOT_RELICENSE_OR_PUBLISH_BASED_ON_STALE_DEP5_CLAIM",
                      first["frontier"])


if __name__=="__main__":
    unittest.main()
