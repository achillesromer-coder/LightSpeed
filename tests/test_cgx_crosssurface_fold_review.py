"""Non-destructive cross-repository and worktree fold regression tests."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

PATH=Path(__file__).resolve().parents[1]/"scripts"/"cgx_crosssurface_fold_review.py"
SPEC=importlib.util.spec_from_file_location("cgx_crosssurface_fold",PATH)
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def audit():
    return {
        "schema":"CGX-LOCAL-GIT-WORKTREE-LIFECYCLE-AUDIT/0.1",
        "source_deleted":0,"worktrees_deleted":0,"git_branch_deleted":0,
        "cross_surface_delete_ready":0,
        "registered_worktree_count":5,
        "tracked_clean":3,"tracked_dirty":2,"missing":0,
        "untracked_files_not_scanned":True,
        "independent_recovery_confirmed":False,
        "rows":[{"path":"C:\\PRIVATE\\do-not-publish","secret":"owner bytes"}]
    }


def overlaps():
    return [{"git_blob_sha":s,"repositories":["NCNBOUWER/Raphael","achillesromer-coder/Romer-MPL"]}
            for s in sorted(mod.EXPECTED_OVERLAPS)]


class CrossSurfaceFoldTests(unittest.TestCase):
    def test_aggregates_only_and_explicit_denials(self):
        x=mod.review(audit(),overlaps(),"a"*40)
        self.assertEqual(x["parent"],"cgx:root:cognigrex")
        self.assertEqual(x["sole_resolver"],"LOAD.cgx")
        self.assertEqual(len(x["public_repositories"]),5)
        self.assertEqual(sum(v["source_file_count"] for v in x["public_repositories"]),2194)
        self.assertEqual(len(x["functional_surfaces"]),8)
        self.assertEqual(x["local_worktree_review"]["registered"],5)
        self.assertEqual(x["cleanup"]["original_source_deletions"],0)
        self.assertFalse(x["release"]["native_mint_authorized"])
        self.assertFalse(x["release"]["public_launch_verified"])
        self.assertTrue(all(v=="HOLD" for v in x["release"]["gates"].values()))
        exported=json.dumps(x)
        self.assertNotIn("C:\\PRIVATE",exported)
        self.assertNotIn("owner bytes",exported)
        self.assertNotIn("client_secret",exported)

    def test_refuses_destruction_and_unqualified_recovery(self):
        for field in ("source_deleted","worktrees_deleted","git_branch_deleted",
                      "cross_surface_delete_ready"):
            x=audit()
            x[field]=1
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"DESTRUCTIVE"):
                mod.review(x,overlaps(),"a"*40)
        x=audit()
        x["independent_recovery_confirmed"]=True
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_WORKTREE"):
            mod.review(x,overlaps(),"a"*40)
        x=audit()
        x["untracked_files_not_scanned"]=False
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_WORKTREE"):
            mod.review(x,overlaps(),"a"*40)

    def test_exact_crossrepo_blob_refs_and_branch_heads_required(self):
        x=overlaps()
        x[0]["git_blob_sha"]="0"*40
        with self.assertRaisesRegex(ValueError,"EXACT_CROSSREPO"):
            mod.review(audit(),x,"a"*40)
        with self.assertRaisesRegex(ValueError,"SOURCE_COMMIT_HOLD"):
            mod.review(audit(),overlaps(),"not-a-commit")
        x=overlaps()
        x[0]["repositories"]=["unknown/repo"]
        with self.assertRaisesRegex(ValueError,"CROSSREPO_SOURCE"):
            mod.review(audit(),x,"a"*40)

    def test_count_invariant_blocks_unreconciled_missing_worktree(self):
        x=audit()
        x["tracked_dirty"]=1
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_WORKTREE"):
            mod.review(x,overlaps(),"a"*40)

    def test_injects_only_once_into_existing_source_of_truth(self):
        with TemporaryDirectory() as td:
            p=Path(td)/"existing_register.json"
            original={
                "schema":"CGX-OPEN-THREAD-EXECUTION-REGISTER/0.2",
                "state":"SOURCE_REVIEW_ONLY","release_ready":False,
                "deletion_ready_count":0,"git_crosslane_inventory_20261106":{"retained":True}
            }
            text=json.dumps(original,indent=2)+"\n"
            p.write_text(text,encoding="utf-8")
            x=mod.review(audit(),overlaps(),"a"*40)
            mod.insert_preserving_original(p,x)
            after=p.read_text(encoding="utf-8")
            self.assertIn('"retained": true',after)
            parsed=json.loads(after)
            self.assertEqual(parsed[mod.FIELD],x)
            self.assertEqual(parsed["git_crosslane_inventory_20261106"],{"retained":True})
            with self.assertRaisesRegex(ValueError,"CANONICAL_REGISTER_OR_EXISTING_FIELD"):
                mod.insert_preserving_original(p,x)


if __name__=="__main__":
    unittest.main()
