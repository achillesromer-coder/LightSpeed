"""Pinned nlohmann/json original Git tree, file-scope rights, and strict review gates."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from cgx.portable_node.nlohmann_json_source_scope import (
    BLOBS, ROOT_TREE, PINNED_COMMIT, _git_blob,
    compile_nlohmann_source_scope,
)
from cgx.portable_node.project_gitlink_evidence import _git_tree

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "alexandria_nlohmann_json"
PARENT = ROOT / "cgx" / "review" / "alexandria_libdatachannel_source_scope_20261021.json"


def originals():
    return (
        json.loads(PARENT.read_text(encoding="utf-8")),
        json.loads((FIX / "tree_chain.json").read_text(encoding="utf-8")),
        {name: (FIX / name).read_bytes() for name in BLOBS},
    )


def derive():
    return compile_nlohmann_source_scope(*originals())


class OriginalNlohmannSourceTests(unittest.TestCase):
    def test_seven_true_original_source_git_blob_identities(self):
        _, _, files = originals()
        self.assertEqual(len(files), 7)
        for path, known_sha in BLOBS.items():
            with self.subTest(path=path):
                self.assertEqual(_git_blob(files[path]), known_sha)

    def test_git_root_ancestor_chain_reproduced_cryptographically(self):
        _, trees, _ = originals()
        self.assertEqual(trees["root_sha"], ROOT_TREE)
        self.assertEqual(len(trees["trees"]), 7)
        for name, obj in trees["trees"].items():
            with self.subTest(name=name):
                self.assertFalse(obj["truncated"])
                self.assertEqual(_git_tree(obj), obj["sha"])

    def test_parent_gitlink_and_core_mit_source_admitted_only_as_evidence(self):
        result = derive()
        self.assertEqual(result["source_root"], f"git:nlohmann/json@{PINNED_COMMIT}")
        self.assertEqual(result["parent_gitlink_path"], "deps/json")
        self.assertEqual(result["version_declared"], "3.12.0")
        self.assertEqual(result["selected_original_file_count"], 7)
        self.assertEqual(result["repository_licence_declaration"], "MIT")
        self.assertTrue(result["licensing_review"]["first_party_mit_original_and_two_headers_verified"])
        self.assertFalse(result["licensing_review"]["distribution_approved"])
        self.assertFalse(result["licensing_review"]["all_files_and_asset_licences_qualified"])
        self.assertFalse(result["capability"]["compiled"])
        self.assertFalse(result["capability"]["parsed_json_tested"])
        self.assertFalse(result["capability"]["runtime_interoperability_verified"])
        self.assertFalse(result["whole_repository_source_acquired"])
        self.assertFalse(result["source_bytes_embedded"])
        self.assertFalse(result["native_dbr_verified"])
        self.assertIsNone(result["canonical_object_id"])

    def test_reuse_multiple_licences_and_thirdparty_scope_not_globally_mit(self):
        result=derive()
        mapping={x["source_glob"]: x["licence_declared"] for x in result["scoped_reuse_declarations"]}
        self.assertEqual(mapping["*"],"MIT")
        self.assertEqual(mapping["include/nlohmann/thirdparty/hedley.hpp"],"CC0")
        self.assertEqual(mapping["tests/thirdparty/Fuzzer/*"],"Apache-2.0")
        self.assertEqual(mapping["tests/thirdparty/imapdl/*"],"GPL-3.0-only")
        self.assertEqual(mapping["tools/amalgamate/*"],"BSD-3-Clause")
        self.assertFalse(result["licensing_review"]["third_party_hedley_manifest_path_consistency_verified"])
        self.assertIn("RECONCILE_REUSE_HEDLEY_PATH_VS_ORIGINAL_SOURCE_HEADERS",result["frontier"])

    def test_all_sha256s_exact_and_deterministic(self):
        a,b,sources=originals()
        one=compile_nlohmann_source_scope(a,b,sources)
        other=compile_nlohmann_source_scope(a,b,dict(reversed(list(sources.items()))))
        self.assertEqual(one,other)
        for record in one["selected_original_files"]:
            data=sources[record["path"]]
            self.assertEqual(record["bytes"],len(data))
            self.assertEqual(record["sha256"],hashlib.sha256(data).hexdigest())
            self.assertEqual(record["original_git_blob_sha1"],_git_blob(data))
            self.assertFalse(record["source_bytes_in_projection"])

    def test_corruption_missing_extra_originals_fail_closed(self):
        parent,trees,original=originals()
        bad=dict(original)
        bad["CMakeLists.txt"]+=b"\n# unauthorized edit"
        with self.assertRaisesRegex(ValueError,"original Git blob mismatch"):
            compile_nlohmann_source_scope(parent,trees,bad)
        bad=dict(original)
        del bad["CITATION.cff"]
        with self.assertRaisesRegex(ValueError,"exact seven"):
            compile_nlohmann_source_scope(parent,trees,bad)
        bad=dict(original)
        bad["PRIVATE_TOKEN"]="never publish"
        with self.assertRaisesRegex(ValueError,"exact seven"):
            compile_nlohmann_source_scope(parent,trees,bad)

    def test_forged_root_and_original_parent_fail_closed(self):
        parent,trees,original=originals()
        broken=copy.deepcopy(trees)
        broken["root_sha"]="f"*40
        with self.assertRaisesRegex(ValueError,"source Git tree identity mismatch"):
            compile_nlohmann_source_scope(parent,broken,original)
        broken=copy.deepcopy(trees)
        broken["trees"]["reuse"]["entries"][0]["sha"]="f"*40
        with self.assertRaisesRegex(ValueError,"original Git tree SHA-1 mismatch"):
            compile_nlohmann_source_scope(parent,broken,original)
        forged=copy.deepcopy(parent)
        forged["native_dbr_verified"]=True
        with self.assertRaisesRegex(ValueError,"untrusted parent"):
            compile_nlohmann_source_scope(forged,trees,original)
        forged=copy.deepcopy(parent)
        next(x for x in forged["nested_gitlinks"] if x["path"]=="deps/json")["pinned_commit_sha1"]="a"*40
        with self.assertRaisesRegex(ValueError,"exact upstream JSON Gitlink"):
            compile_nlohmann_source_scope(forged,trees,original)

    def test_claims_remain_licence_and_build_holds(self):
        result=derive()
        self.assertEqual(result["schema"],"CGX-ALEXANDRIA-NLOHMANN-SOURCE-SCOPE/0.1")
        self.assertEqual(result["status"],"SEVEN_ORIGINAL_R0_FILES_PINNED_R1_CANDIDATE")
        self.assertIn("TEST_REAL_CXX_TOOLCHAIN_BUILD_AND_JSON_ROUNDTRIP",result["frontier"])
        self.assertIn("VERIFY_NATIVE_SIGNED_OWNER_DBR_READBACK",result["frontier"])
        self.assertFalse(result["licensing_review"]["tooling_and_test_file_licenses_qualified"])
        self.assertFalse(result["capability"]["canonical_capability_admitted"])


if __name__=="__main__":
    unittest.main()
