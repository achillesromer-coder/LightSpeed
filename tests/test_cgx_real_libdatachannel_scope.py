"""Real pinned libdatachannel file notices, Git trees and nested dependencies."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import unittest

from cgx.portable_node.libdatachannel_source_scope import (
    BLOBS, PINNED_COMMIT, ROOT_SHA, compile_libdatachannel_scope,
)
from cgx.portable_node.project_gitlink_evidence import _git_blob, _git_tree

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT/"tests"/"fixtures"/"alexandria_libdatachannel"
PARENT = ROOT/"cgx"/"review"/"alexandria_hypersomnia_gitlinks_openal_scope_20261021.json"


def inputs():
    return (json.loads(PARENT.read_text(encoding="utf-8")),
            json.loads((FIXTURE/"git_tree_chain.json").read_text(encoding="utf-8")),
            {name:(FIXTURE/name).read_bytes() for name in BLOBS})


class LibdatachannelSourceScopeTests(unittest.TestCase):
    def test_real_source_git_blobs_and_two_complete_tree_hashes(self):
        _,trees,blobs=inputs()
        self.assertEqual(trees["root"]["sha"], ROOT_SHA)
        self.assertEqual(_git_tree(trees["root"]), ROOT_SHA)
        self.assertEqual(_git_tree(trees["deps"]), trees["deps"]["sha"])
        for name,expected in BLOBS.items():
            with self.subTest(name=name):
                self.assertEqual(_git_blob(blobs[name]),expected)

    def test_scope_verifies_mpl_first_party_and_five_unacquired_links(self):
        p,t,b=inputs()
        result=compile_libdatachannel_scope(p,t,b)
        self.assertEqual(result["source_root"],f"git:paullouisageneau/libdatachannel@{PINNED_COMMIT}")
        self.assertEqual(result["original_file_count"],5)
        self.assertEqual(result["nested_gitlink_count"],5)
        self.assertEqual(result["first_party_licensing"]["declared"],"MPL-2.0")
        self.assertTrue(result["first_party_licensing"]["two_source_file_headers_verified"])
        self.assertFalse(result["first_party_licensing"]["all_source_file_headers_verified"])
        self.assertFalse(result["first_party_licensing"]["release_rights_approved"])
        self.assertFalse(result["all_project_source_acquired"])
        self.assertFalse(result["nested_dependencies_acquired"])
        self.assertFalse(result["capability_claims"]["compiled"])
        self.assertFalse(result["capability_claims"]["network_interoperability_tested"])
        self.assertFalse(result["native_dbr_verified"])
        self.assertIsNone(result["canonical_object_id"])
        names={x["path"] for x in result["nested_gitlinks"]}
        self.assertEqual(names,{"deps/plog","deps/usrsctp","deps/libjuice",
                                "deps/json","deps/libsrtp"})
        for x in result["nested_gitlinks"]:
            self.assertFalse(x["source_acquired"])
            self.assertFalse(x["licence_verified"])
            self.assertEqual(len(x["pinned_commit_sha1"]),40)

    def test_corrupt_licensed_source_or_false_ancestor_is_rejected(self):
        p,t,b=inputs()
        altered=dict(b)
        altered["src/peerconnection.cpp"]+=b"\n// changed"
        with self.assertRaisesRegex(ValueError,"original source Git blob mismatch"):
            compile_libdatachannel_scope(p,t,altered)
        p=copy.deepcopy(p)
        next(x for x in p["resolved_gitlinks"] if
             x["declared_path"]=="src/3rdparty/libdatachannel")["pinned_gitlink_commit"]="f"*40
        with self.assertRaisesRegex(ValueError,"exact parent Gitlink"):
            compile_libdatachannel_scope(p,t,b)

    def test_missing_or_replaced_gitlink_cannot_inherit_original(self):
        p,t,b=inputs()
        modified=copy.deepcopy(t)
        modified["deps"]["entries"][0]["sha"]="f"*40
        with self.assertRaisesRegex(ValueError,"Git tree source bytes"):
            compile_libdatachannel_scope(p,modified,b)
        modified=copy.deepcopy(t)
        modified["root"]["entries"][0]["path"]="forged"
        with self.assertRaisesRegex(ValueError,"Git tree source bytes"):
            compile_libdatachannel_scope(p,modified,b)

    def test_unlisted_source_files_or_unverified_licences_do_not_promote(self):
        p,t,b=inputs()
        bad=dict(b)
        bad["unknown.txt"]=b"unrelated source"
        with self.assertRaisesRegex(ValueError,"exact five"):
            compile_libdatachannel_scope(p,t,bad)
        p=copy.deepcopy(p)
        p["canonical_promotion"]=True
        with self.assertRaisesRegex(ValueError,"untrusted parent"):
            compile_libdatachannel_scope(p,t,b)

    def test_source_digest_records_independent_of_input_order(self):
        p,t,b=inputs()
        first=compile_libdatachannel_scope(p,t,b)
        reverse=dict(reversed(list(b.items())))
        self.assertEqual(first,compile_libdatachannel_scope(p,t,reverse))
        for x in first["original_file_proofs"]:
            original=b[x["path"]]
            self.assertEqual(x["bytes"],len(original))
            self.assertEqual(x["sha256"],hashlib.sha256(original).hexdigest())
            self.assertEqual(x["git_blob_sha1"],_git_blob(original))
            self.assertFalse(x["embedded_in_r1"])


if __name__=="__main__":
    unittest.main()
