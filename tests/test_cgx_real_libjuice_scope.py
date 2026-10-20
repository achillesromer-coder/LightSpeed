"""Original R0 libjuice sample and exact bounded rights classification tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from cgx.portable_node.project_gitlink_evidence import _git_blob, _git_tree
from cgx.portable_node.libjuice_source_scope import (
    BLOBS, SOURCE_COMMIT, SOURCE_TREE, compile_libjuice_scope
)

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/"tests"/"fixtures"/"alexandria_libjuice"
PARENT=ROOT/"cgx"/"review"/"alexandria_libdatachannel_source_scope_20261021.json"


def inputs():
    return (json.loads(PARENT.read_text(encoding="utf-8")),
            json.loads((FIX/"git_tree_chain.json").read_text(encoding="utf-8")),
            {name:(FIX/name).read_bytes() for name in BLOBS})


class LibjuiceSourceScopeTests(unittest.TestCase):
    def test_full_git_tree_objects_and_original_file_blobs(self):
        p,t,originals=inputs()
        self.assertEqual(t["root"]["sha"],SOURCE_TREE)
        self.assertEqual([len(t[key]["entries"]) for key in
                         ("root","src","include","include_juice")],[15,44,1,1])
        for key in ("root","src","include","include_juice"):
            self.assertEqual(_git_tree(t[key]),t[key]["sha"])
            self.assertFalse(t[key]["truncated"])
        for name,expected in BLOBS.items():
            with self.subTest(name=name):
                self.assertEqual(_git_blob(originals[name]),expected)

    def test_mpl_licence_and_picohash_claim_remain_distinct(self):
        result=compile_libjuice_scope(*inputs())
        self.assertEqual(result["source_root"],
                         "git:paullouisageneau/libjuice@"+SOURCE_COMMIT)
        self.assertEqual(result["status"],"FIVE_ORIGINAL_BLOBS_FOUR_GIT_TREES_PARTIAL_RIGHTS")
        self.assertEqual(result["original_file_count"],5)
        self.assertTrue(result["license_scopes"]["libjuice_first_party_mpl_2_0"]["original_license"])
        self.assertFalse(result["license_scopes"]["libjuice_first_party_mpl_2_0"]["all_repository_file_licences_reviewed"])
        self.assertEqual(result["license_scopes"]["bundled_picohash"]["claim"],
                         "PUBLIC_DOMAIN_AUTHOR_ASSERTION")
        self.assertFalse(result["license_scopes"]["bundled_picohash"]["independent_legal_validation"])
        self.assertFalse(result["license_scopes"]["bundled_picohash"]["rights_automatically_inherited_from_libjuice"])
        self.assertFalse(result["license_scopes"]["distribution_approved"])
        self.assertFalse(result["complete_repository_acquired"])
        self.assertFalse(result["native_dbr_verified"])
        self.assertFalse(result["capability_descriptor"]["network_connection_tested"])
        self.assertFalse(result["capability_descriptor"]["operational_transport_registered"])
        self.assertIsNone(result["canonical_object_id"])

    def test_original_byte_sha256_are_stable_and_order_independent(self):
        p,t,originals=inputs()
        result=compile_libjuice_scope(p,t,originals)
        self.assertEqual(result,compile_libjuice_scope(p,t,dict(reversed(list(originals.items())))))
        for row in result["original_file_proofs"]:
            data=originals[row["path"]]
            self.assertEqual(row["bytes"],len(data))
            self.assertEqual(row["sha256"],hashlib.sha256(data).hexdigest())
            self.assertEqual(row["git_blob_sha1"],_git_blob(data))
            self.assertFalse(row["embedded_in_r1"])

    def test_mutated_picohash_or_main_source_blob_fails_closed(self):
        p,t,originals=inputs()
        for name in ("src/picohash.h","src/juice.c","LICENSE"):
            bad=dict(originals)
            bad[name]+=b"\n// altered"
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,"Git blob mismatch"):
                compile_libjuice_scope(p,t,bad)

    def test_parent_gitlink_or_tree_ancestry_cannot_be_replaced(self):
        p,t,originals=inputs()
        forged=copy.deepcopy(p)
        next(x for x in forged["nested_gitlinks"] if x["path"]=="deps/libjuice")["pinned_commit_sha1"]="f"*40
        with self.assertRaisesRegex(ValueError,"ancestry"):
            compile_libjuice_scope(forged,t,originals)
        broken=copy.deepcopy(t)
        broken["root"]["entries"][0]["sha"]="f"*40
        with self.assertRaisesRegex(ValueError,"Git tree SHA-1 mismatch"):
            compile_libjuice_scope(p,broken,originals)
        broken=copy.deepcopy(t)
        broken["include"]["entries"][0]["path"]="different"
        with self.assertRaisesRegex(ValueError,"Git tree SHA-1 mismatch"):
            compile_libjuice_scope(p,broken,originals)

    def test_no_extra_or_missing_files_and_no_parent_promotion(self):
        p,t,originals=inputs()
        minus=dict(originals);minus.pop("LICENSE")
        with self.assertRaisesRegex(ValueError,"exact five"):
            compile_libjuice_scope(p,t,minus)
        extra=dict(originals);extra["secrets.txt"]=b"not allowed"
        with self.assertRaisesRegex(ValueError,"exact five"):
            compile_libjuice_scope(p,t,extra)
        elevated=copy.deepcopy(p);elevated["native_dbr_verified"]=True
        with self.assertRaisesRegex(ValueError,"untrusted parent"):
            compile_libjuice_scope(elevated,t,originals)

if __name__=="__main__":
    unittest.main()
