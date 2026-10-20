"""Real Hypersomnia project source qualification; strict bounded source scope."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import unittest

from cgx.portable_node.individual_game_source_scope import (
    BLOBS, PROJECT, PINNED_COMMIT, PINNED_TREE, SOURCE_ROOT,
    compile_project_source_candidate,
)

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/"tests"/"fixtures"/"alexandria_hypersomnia_project"
CATALOGUE=ROOT/"cgx"/"review"/"alexandria_game_catalogue_real_source_envelope_20261021.json"


def inputs():
    return {path:(FIX/path).read_bytes() for path in BLOBS}


def packet():
    return json.loads(CATALOGUE.read_text(encoding="utf-8"))


def git_blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


class HypersomniaSourceScopeTests(unittest.TestCase):
    def test_all_original_source_blobs_match_immutable_upstream_git(self):
        sources=inputs()
        self.assertEqual(set(sources),set(BLOBS))
        for path,expected in BLOBS.items():
            with self.subTest(path=path):
                self.assertEqual(git_blob(sources[path]),expected)
                self.assertGreater(len(sources[path]),0)

    def test_qualifies_four_files_but_not_whole_game_or_assets(self):
        result=compile_project_source_candidate(inputs(),packet())
        self.assertEqual(result["status"],"PINNED_FOUR_FILE_R0_SOURCE_VERIFIED_R1_CANDIDATE")
        self.assertEqual(result["repository"],PROJECT)
        self.assertEqual(result["source_root"],SOURCE_ROOT)
        self.assertEqual(result["git_commit"],PINNED_COMMIT)
        self.assertEqual(result["upstream_git_tree_sha1"],PINNED_TREE)
        self.assertEqual(result["source_file_count"],4)
        self.assertEqual(result["declared_submodule_count"],11)
        self.assertFalse(result["whole_repository_acquired"])
        self.assertFalse(result["all_dependencies_acquired"])
        self.assertFalse(result["all_assets_acquired"])
        self.assertFalse(result["source_bytes_embedded"])
        self.assertFalse(result["native_dbr_verified"])
        self.assertFalse(result["canon_admitted"])
        self.assertFalse(result["licence_release_approved"])
        self.assertIsNone(result["canonical_object_id"])
        self.assertEqual(result["project_licence"]["repository_declared"],"AGPL-3.0")
        self.assertEqual(result["project_licence"]["art_media_licensing"],"UNVERIFIED")
        self.assertEqual(result["project_licence"]["third_party_dependency_licences"],"UNVERIFIED")
        self.assertFalse(result["function_evidence"][0]["compiled"])
        self.assertFalse(result["function_evidence"][0]["functional_capability_admitted"])
        self.assertEqual(result["related_game_index_ref"].split(":")[-1],"28")
        for x in result["declared_submodules"]:
            self.assertFalse(x["licence_verified"])
            self.assertFalse(x["source_bytes_acquired"])
            self.assertIsNone(x["pinned_submodule_git_commit"])

    def test_committed_r1_project_scope_is_reproducible_from_original_bytes(self):
        receipt_path=ROOT/"cgx"/"review"/"alexandria_hypersomnia_project_source_scope_20261021.json"
        persisted=json.loads(receipt_path.read_text(encoding="utf-8"))
        derived=compile_project_source_candidate(inputs(),packet())
        self.assertEqual(persisted,derived)
        self.assertEqual(len(persisted["source_files"]),4)
        self.assertEqual(persisted["declared_submodule_count"],11)
        self.assertFalse(persisted["licence_release_approved"])
        self.assertFalse(persisted["all_assets_acquired"])

    def test_source_record_sha256_is_byte_exact_and_order_independent(self):
        sources=inputs()
        receipt=compile_project_source_candidate(sources,packet())
        reversed_sources=dict(reversed(list(sources.items())))
        self.assertEqual(receipt,compile_project_source_candidate(reversed_sources,packet()))
        for entry in receipt["source_files"]:
            raw=sources[entry["path"]]
            self.assertEqual(entry["byte_length"],len(raw))
            self.assertEqual(entry["sha256"],hashlib.sha256(raw).hexdigest())
            self.assertEqual(entry["upstream_git_blob_sha1"],git_blob(raw))
            self.assertFalse(entry["source_bytes_in_compact_projection"])

    def test_missing_added_or_mutated_file_is_rejected(self):
        sources=inputs()
        sources.pop("src/main.cpp")
        with self.assertRaisesRegex(ValueError,"exact four-file"):
            compile_project_source_candidate(sources,packet())
        sources=inputs()
        sources["rogue_script.py"]=b"print('do not execute')"
        with self.assertRaisesRegex(ValueError,"exact four-file"):
            compile_project_source_candidate(sources,packet())
        sources=inputs()
        sources["src/main.cpp"]+=b"\n// mutation"
        with self.assertRaisesRegex(ValueError,"Git blob mismatch"):
            compile_project_source_candidate(sources,packet())

    def test_mismatched_catalogue_or_forged_rights_cannot_promote(self):
        source=inputs()
        p=packet()
        p["source_envelope"]["lineage"]["pinned_commit"]="f"*40
        with self.assertRaisesRegex(ValueError,"catalogue origin mismatch"):
            compile_project_source_candidate(source,p)
        p=packet()
        p["source_envelope"]["projections"][0]["entries"][0]["upstream_rights"]="AGPL_CONFIRMED"
        with self.assertRaisesRegex(ValueError,"source index cannot authorize"):
            compile_project_source_candidate(source,p)

    def test_declared_dependency_urls_are_not_dependency_authorizations(self):
        result=compile_project_source_candidate(inputs(),packet())
        paths={x["declared_path"] for x in result["declared_submodules"]}
        self.assertIn("src/3rdparty/openal-soft",paths)
        self.assertIn("src/3rdparty/libdatachannel",paths)
        self.assertEqual(len(paths),11)
        self.assertIn("VERIFY_ARTWORK_AUDIO_MAPS_FONTS_AND_THIRD_PARTY_ASSETS",result["frontier"])
        self.assertIn("QUALIFY_ENGINE_BUILD_AND_RUNTIME",result["frontier"])


if __name__=="__main__":
    unittest.main()
