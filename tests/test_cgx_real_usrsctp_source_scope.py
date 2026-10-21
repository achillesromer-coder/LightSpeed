"""Pinned upstream usrsctp source ancestry and mixed BSD per-file notice tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from cgx.portable_node.project_gitlink_evidence import _git_blob, _git_tree
from cgx.portable_node.usrsctp_source_scope import (
    BLOBS, TREE_SHA, COMMIT, compile_usrsctp_source_scope,
)

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT/"tests"/"fixtures"/"alexandria_usrsctp"
PARENT = ROOT/"cgx"/"review"/"alexandria_libdatachannel_source_scope_20261021.json"


def sources():
    return (json.loads(PARENT.read_text(encoding="utf-8")),
            json.loads((FIX/"pinned_tree_chain.json").read_text(encoding="utf-8")),
            {name:(FIX/name).read_bytes() for name in BLOBS})


class UsrsctpSourceScopeTests(unittest.TestCase):
    def test_original_five_git_blob_bytes_and_three_ancestor_tree_objects(self):
        parent, tree, blobs = sources()
        self.assertEqual(tree["root_tree_sha"], TREE_SHA)
        self.assertEqual(tree["pinned_commit"], COMMIT)
        for name in ("root", "usrsctplib", "netinet"):
            with self.subTest(tree=name):
                self.assertFalse(tree[name]["truncated"])
                self.assertEqual(_git_tree(tree[name]), tree[name]["sha"])
        for name, expected in BLOBS.items():
            with self.subTest(source=name):
                self.assertEqual(_git_blob(blobs[name]), expected)
                self.assertGreater(len(blobs[name]), 0)

    def test_bsd_style_notices_are_kept_separate_for_each_source(self):
        result = compile_usrsctp_source_scope(*sources())
        self.assertEqual(result["verified_git_tree_count"],3)
        self.assertEqual(result["verified_original_file_count"],5)
        self.assertEqual(result["git_commit"],COMMIT)
        self.assertEqual(result["source_root"],
             f"git:paullouisageneau/usrsctp@{COMMIT}")
        self.assertIn("BSD-3-Clause-style",result["rights"]["repository_licence_statement"])
        self.assertIn("BSD-2-Clause-style",result["rights"]["selected_user_environment_source"])
        self.assertIn("BSD-3-Clause",result["rights"]["selected_netinet_sctp_header"])
        self.assertFalse(result["rights"]["source_notice_coverage_complete"])
        self.assertFalse(result["rights"]["all_project_assets_cleared"])
        self.assertFalse(result["public_release_approved"])
        self.assertFalse(result["repository_source_complete"])
        self.assertFalse(result["source_bytes_embedded"])
        self.assertFalse(result["native_dbr_verified"])
        self.assertIsNone(result["canonical_object_id"])
        self.assertFalse(result["capability"]["compiled"])
        self.assertFalse(result["capability"]["protocol_interoperability_tested"])
        self.assertFalse(result["capability"]["CGX_Natural_Network_activated"])

    def test_source_byte_digests_and_deterministic_order(self):
        parent, tree, raw = sources()
        initial = compile_usrsctp_source_scope(parent,tree,raw)
        reversed_sources = dict(reversed(list(raw.items())))
        self.assertEqual(initial,
            compile_usrsctp_source_scope(parent,tree,reversed_sources))
        self.assertEqual(len(initial["source_files"]),5)
        for item in initial["source_files"]:
            self.assertEqual(item["size_bytes"],len(raw[item["path"]]))
            self.assertEqual(item["sha256"],hashlib.sha256(raw[item["path"]]).hexdigest())
            self.assertEqual(item["git_blob_sha1"],_git_blob(raw[item["path"]]))
            self.assertFalse(item["raw_bytes_in_projection"])

    def test_wrong_parent_gitlink_or_self_promoted_parent_rejected(self):
        parent,tree,raw = sources()
        forged = copy.deepcopy(parent)
        next(x for x in forged["nested_gitlinks"] if
             x["path"]=="deps/usrsctp")["pinned_commit_sha1"] = "f"*40
        with self.assertRaisesRegex(ValueError,"wrong libdatachannel pinned"):
            compile_usrsctp_source_scope(forged,tree,raw)
        forged = copy.deepcopy(parent)
        forged["native_dbr_verified"] = True
        with self.assertRaisesRegex(ValueError,"unsupported existing source ancestry"):
            compile_usrsctp_source_scope(forged,tree,raw)

    def test_changed_tree_hash_or_hidden_file_rejected(self):
        parent,tree,raw = sources()
        forged=copy.deepcopy(tree)
        forged["netinet"]["entries"][0]["sha"]="f"*40
        with self.assertRaisesRegex(ValueError,"cryptographic Git tree mismatch"):
            compile_usrsctp_source_scope(parent,forged,raw)
        forged=copy.deepcopy(tree)
        forged["root"]["entries"].append(copy.deepcopy(forged["root"]["entries"][0]))
        with self.assertRaises(ValueError):
            compile_usrsctp_source_scope(parent,forged,raw)

    def test_missing_extra_mutated_source_or_wrong_notice_rejected(self):
        parent,tree,raw=sources()
        altered=dict(raw);altered.pop("README.md")
        with self.assertRaisesRegex(ValueError,"exact five original source"):
            compile_usrsctp_source_scope(parent,tree,altered)
        altered=dict(raw);altered["evil.py"]=b"not source"
        with self.assertRaisesRegex(ValueError,"exact five original source"):
            compile_usrsctp_source_scope(parent,tree,altered)
        altered=dict(raw);altered["LICENSE.md"]+=b"modification"
        with self.assertRaisesRegex(ValueError,"original Git source bytes mismatch"):
            compile_usrsctp_source_scope(parent,tree,altered)

    def test_persisted_compact_receipt_matches_exact_original_r0(self):
        persisted_path=ROOT/"cgx"/"review"/"alexandria_usrsctp_source_scope_20261021.json"
        persisted=json.loads(persisted_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted,compile_usrsctp_source_scope(*sources()))
        self.assertEqual(persisted["verified_original_file_count"],5)
        self.assertFalse(persisted["rights"]["full_redistribution_review_complete"])
        self.assertFalse(persisted["capability"]["CGX_Natural_Network_activated"])
        self.assertIsNone(persisted["canonical_object_id"])

    def test_source_of_capability_is_description_not_live_qualification(self):
        result=compile_usrsctp_source_scope(*sources())
        self.assertEqual(result["capability"]["described"],"userland SCTP stack")
        self.assertFalse(result["capability"]["real_node_binding"])
        self.assertIn("TEST_REAL_SCTP_PROTOCOL_WITH_SIGNED_NODES",result["frontier"])
        self.assertIn("OWNER_DB_R_READBACK_REQUIRED",result["frontier"])


if __name__ == "__main__":
    unittest.main()
