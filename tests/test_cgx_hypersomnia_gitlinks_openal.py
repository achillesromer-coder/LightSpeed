"""R0 cryptographic Git-tree proof and bounded OpenAL source-notice evidence."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import unittest

from cgx.portable_node.project_gitlink_evidence import (
    PROJECT_TREE, LINKED_OPENAL_COMMIT, OPENAL_BLOBS,
    _git_blob, _git_tree, compile_submodule_scope,
)

ROOT=Path(__file__).resolve().parents[1]
HYP=ROOT/"tests"/"fixtures"/"alexandria_hypersomnia_project"
OPENAL=ROOT/"tests"/"fixtures"/"alexandria_hypersomnia_openal"
SCOPE=ROOT/"cgx"/"review"/"alexandria_hypersomnia_project_source_scope_20261021.json"


def sources():
    return (json.loads((HYP/"pinned_tree_chain.json").read_text(encoding="utf-8")),
            (HYP/".gitmodules").read_bytes(),
            {name:(OPENAL/name).read_bytes() for name in OPENAL_BLOBS},
            json.loads(SCOPE.read_text(encoding="utf-8")))


def derive():
    return compile_submodule_scope(*sources())


class PinnedGitlinkSourceTests(unittest.TestCase):
    def test_git_tree_hashes_and_root_chain_recomputed_from_complete_entries(self):
        tree, _, _, _=sources()
        self.assertEqual(tree["root"]["sha"],PROJECT_TREE)
        self.assertEqual(tree["root_tree_sha"],PROJECT_TREE)
        for name in ("root","src","cmake","src_3rdparty"):
            with self.subTest(tree=name):
                self.assertFalse(tree[name]["truncated"])
                self.assertEqual(_git_tree(tree[name]),tree[name]["sha"])
        self.assertEqual(len(tree["root"]["entries"]),21)
        self.assertEqual(len(tree["src"]["entries"]),21)
        self.assertEqual(len(tree["cmake"]["entries"]),31)
        self.assertEqual(len(tree["src_3rdparty"]["entries"]),26)

    def test_all_11_gitlink_commits_are_verified_but_not_fully_ingested(self):
        candidate=derive()
        self.assertEqual(candidate["schema"],"CGX-ALEXANDRIA-PINNED-GITLINK-EVIDENCE/0.1")
        self.assertEqual(candidate["verified_gitlink_count"],11)
        self.assertEqual(len(candidate["resolved_gitlinks"]),11)
        self.assertEqual({r["declared_path"] for r in candidate["resolved_gitlinks"]},
                         {"src/3rdparty/"+name for name in (
                            "polypartition","rectpack2D","openal-soft","lodepng",
                            "Catch","imgui","yojimbo","rapidjson","libdatachannel",
                            "datachannel-wasm")} | {"cmake/Introspector-generator"})
        self.assertEqual(next(x["pinned_gitlink_commit"] for x in candidate["resolved_gitlinks"]
                              if x["declared_path"]=="src/3rdparty/openal-soft"),LINKED_OPENAL_COMMIT)
        for row in candidate["resolved_gitlinks"]:
            self.assertEqual(len(row["pinned_gitlink_commit"]),40)
            self.assertFalse(row["third_party_source_complete"])
            self.assertFalse(row["licence_release_approved"])
        self.assertFalse(candidate["all_11_dependency_sources_acquired"])
        self.assertFalse(candidate["all_11_dependency_licences_qualified"])
        self.assertFalse(candidate["all_game_assets_rights_qualified"])
        self.assertFalse(candidate["live_build_executed"])
        self.assertFalse(candidate["native_dbr_verified"])
        self.assertFalse(candidate["canonical_promotion"])
        self.assertFalse(candidate["source_bytes_embedded"])

    def test_persisted_source_free_submodule_receipt_matches_full_recompile(self):
        saved=ROOT/"cgx"/"review"/"alexandria_hypersomnia_gitlinks_openal_scope_20261021.json"
        persisted=json.loads(saved.read_text(encoding="utf-8"))
        current=derive()
        self.assertEqual(persisted,current)
        self.assertEqual(persisted["verified_gitlink_count"],11)
        self.assertFalse(persisted["all_11_dependency_licences_qualified"])
        self.assertFalse(persisted["native_dbr_verified"])
        self.assertFalse(persisted["source_bytes_embedded"])

    def test_openal_three_real_git_blobs_keep_pffft_notice_distinct(self):
        candidate=derive()
        documents={p:raw for p,raw in sources()[2].items()}
        self.assertEqual(candidate["openal_licensing"]["readme_claim"],
                         "LGPL-licensed OpenAL Soft implementation")
        self.assertEqual(candidate["openal_licensing"]["bundled_copying_text"],
                         "GNU Library General Public License version 2")
        self.assertFalse(candidate["openal_licensing"]["distribution_approved"])
        self.assertEqual(candidate["openal_licensing"]["exact_source_code_licence_for_every_file"],
                         "UNVERIFIED")
        self.assertEqual(len(candidate["openal_notice_originals"]),3)
        for row in candidate["openal_notice_originals"]:
            data=documents[row["path"]]
            self.assertEqual(row["byte_length"],len(data))
            self.assertEqual(row["sha256"],hashlib.sha256(data).hexdigest())
            self.assertEqual(row["git_blob_sha1"],_git_blob(data))
        self.assertIn("A modified PFFFT",documents["LICENSE-pffft"].decode())

    def test_mutated_tree_entry_cannot_inherit_parent_commit(self):
        tree, mods, third, scope=sources()
        tree=copy.deepcopy(tree)
        tree["src_3rdparty"]["entries"][0]["sha"]="f"*40
        with self.assertRaisesRegex(ValueError,"Git tree object SHA-1 mismatch"):
            compile_submodule_scope(tree,mods,third,scope)
        tree, mods, third, scope=sources()
        tree=copy.deepcopy(tree)
        tree["root"]["entries"][0]["path"]="tampered"
        with self.assertRaisesRegex(ValueError,"Git tree object SHA-1 mismatch"):
            compile_submodule_scope(tree,mods,third,scope)

    def test_forged_declaration_and_incorrect_openal_text_fail_closed(self):
        tree, mods, third, scope=sources()
        with self.assertRaisesRegex(ValueError,"Git submodule declarations"):
            compile_submodule_scope(tree,mods+b"# forged\n",third,scope)
        altered=dict(third)
        altered["LICENSE-pffft"]+=b"not original\n"
        with self.assertRaisesRegex(ValueError,"OpenAL original notice"):
            compile_submodule_scope(tree,mods,altered,scope)

    def test_missing_tree_or_hidden_gitlink_path_rejected(self):
        tree, mods, third, scope=sources()
        bad=copy.deepcopy(tree)
        bad.pop("cmake")
        with self.assertRaises(ValueError):
            compile_submodule_scope(bad,mods,third,scope)
        bad=copy.deepcopy(tree)
        bad["src_3rdparty"]["entries"].append(copy.deepcopy(bad["src_3rdparty"]["entries"][0]))
        with self.assertRaises(ValueError):
            compile_submodule_scope(bad,mods,third,scope)

    def test_no_canonical_upgrade_from_base_scope_or_notice_only(self):
        tree,mods,third,scope=sources()
        bad=copy.deepcopy(scope)
        bad["canon_admitted"]=True
        with self.assertRaisesRegex(ValueError,"ancestry"):
            compile_submodule_scope(tree,mods,third,bad)
        bad=copy.deepcopy(scope)
        bad["source_root"]="git:unrelated/repository@"+("a"*40)
        with self.assertRaisesRegex(ValueError,"ancestry"):
            compile_submodule_scope(tree,mods,third,bad)


if __name__=="__main__":
    unittest.main()
