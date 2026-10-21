"""Pinned plog original file, MIT scope and dependency ancestry tests."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from cgx.portable_node.plog_source_scope import BLOBS,REV,TREE,compile_plog_scope
from cgx.portable_node.project_gitlink_evidence import _git_blob,_git_tree

ROOT=Path(__file__).resolve().parents[1]
F=ROOT/"tests"/"fixtures"/"alexandria_plog"
P=ROOT/"cgx"/"review"/"alexandria_libdatachannel_source_scope_20261021.json"
def original():
    return (json.loads(P.read_text(encoding="utf-8")),
            json.loads((F/"git_tree_chain.json").read_text(encoding="utf-8")),
            {p:(F/p).read_bytes() for p in BLOBS})

class PlogSourceScopeTests(unittest.TestCase):
    def test_original_git_trees_and_blobs_are_cryptographic(self):
        parent,trees,raw=original()
        self.assertEqual(trees["root"]["sha"],TREE)
        for part in ("root","include","include_plog"):
            self.assertFalse(trees[part]["truncated"])
            self.assertEqual(_git_tree(trees[part]),trees[part]["sha"])
        for name,digest in BLOBS.items():
            with self.subTest(name=name):
                self.assertEqual(_git_blob(raw[name]),digest)

    def test_mit_licence_and_cxx_source_declaration_are_not_runtime_proofs(self):
        d=compile_plog_scope(*original())
        self.assertEqual(d["schema"],"CGX-ALEXANDRIA-PLOG-SOURCE-SCOPE/0.1")
        self.assertEqual(d["original_file_count"],5)
        self.assertEqual(d["licensing"]["repository_declared"],"MIT")
        self.assertTrue(d["licensing"]["permission_and_copyright_notice_retention_required"])
        self.assertFalse(d["licensing"]["distribution_approved"])
        self.assertFalse(d["licensing"]["all_headers_and_third_party_notices_verified"])
        self.assertTrue(d["packaging"]["header_interface_library_declared"])
        self.assertFalse(d["packaging"]["compiled"])
        self.assertFalse(d["capability"]["canon_admitted"])
        self.assertFalse(d["native_dbr_verified"])
        self.assertFalse(d["whole_repository_acquired"])
        self.assertIsNone(d["canonical_object_id"])

    def test_deterministic_proofs_are_byte_accurate(self):
        parent,trees,raw=original()
        result=compile_plog_scope(parent,trees,raw)
        self.assertEqual(result,compile_plog_scope(parent,trees,dict(reversed(list(raw.items())))))
        for proof in result["original_file_proofs"]:
            b=raw[proof["path"]]
            self.assertEqual(proof["git_blob_sha1"],_git_blob(b))
            self.assertEqual(proof["sha256"],hashlib.sha256(b).hexdigest())
            self.assertEqual(proof["bytes"],len(b))

    def test_persisted_noncanonical_receipt_exactly_recompiles(self):
        saved=ROOT/"cgx"/"review"/"alexandria_plog_source_scope_20261021.json"
        actual=json.loads(saved.read_text(encoding="utf-8"))
        self.assertEqual(actual,compile_plog_scope(*original()))
        self.assertFalse(actual["licensing"]["distribution_approved"])
        self.assertFalse(actual["native_dbr_verified"])
        self.assertFalse(actual["whole_repository_acquired"])

    def test_source_mutation_and_extra_file_are_rejected(self):
        parent,trees,raw=original()
        for key in ("LICENSE","include/plog/Log.h","library.json"):
            altered=dict(raw);altered[key]+=b"x"
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,"original Git blob mismatch"):
                compile_plog_scope(parent,trees,altered)
        altered=dict(raw);altered["unexpected.py"]=b"do not import"
        with self.assertRaisesRegex(ValueError,"exact 5-file"):
            compile_plog_scope(parent,trees,altered)

    def test_replaced_root_and_parent_promotion_fail_closed(self):
        parent,trees,raw=original()
        changed=copy.deepcopy(trees)
        changed["root"]["entries"][0]["sha"]="f"*40
        with self.assertRaisesRegex(ValueError,"Git tree mismatch"):
            compile_plog_scope(parent,changed,raw)
        changed=copy.deepcopy(parent)
        next(x for x in changed["nested_gitlinks"] if x["path"]=="deps/plog")["pinned_commit_sha1"]="f"*40
        with self.assertRaisesRegex(ValueError,"gitlink mismatch"):
            compile_plog_scope(changed,trees,raw)
        changed=copy.deepcopy(parent);changed["native_dbr_verified"]=True
        with self.assertRaisesRegex(ValueError,"untrusted parent"):
            compile_plog_scope(changed,trees,raw)

if __name__=="__main__":
    unittest.main()
