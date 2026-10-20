"""Source-only private review migration: no deletion, no public promotion."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SRC=Path(__file__).resolve().parents[1]/"cgx/review/private_object_asset_migration.py"
spec=importlib.util.spec_from_file_location("asset_migration",SRC)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class PrivateAssetMigrationTests(unittest.TestCase):
    def setUp(self):
        self.workspace=tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        parent=Path(self.workspace.name)
        self.repo=parent/"checked_out_source"
        self.private=parent/"owner_approved_private_root"
        self.private.mkdir()
        self.pub=self.repo/"apps/lightspeed-go/public"
        for rel,value in {
            "data/cgx_object_review_catalogue.json":b'{"kind":"private","secret":"not-printed"}',
            "data/component_geometry_atlas_public_review.json":b'{"record_count":411}',
            "review/renders/diode.svg":b'<svg xmlns="http://www.w3.org/2000/svg"/>',
            "review/mesh/diode.json":b'{"vertices":[]}',
        }.items():
            dst=self.pub/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(value)
    def test_default_is_read_only_source_receipt_and_no_private_contents(self):
        p=module.private_review_source_plan(self.repo)
        self.assertEqual(p["count"],4)
        self.assertEqual(len(p["plan_sha256"]),64)
        self.assertFalse(p["owner_approval_recorded"])
        self.assertFalse(p["public_release_authorised"])
        self.assertEqual(list(self.private.iterdir()),[])
        self.assertNotIn("not-printed",json.dumps(p))
        self.assertEqual(p["records"],sorted(p["records"],key=lambda x:x["source_relative_path"]))
        self.assertTrue(all(len(x["sha256"])==64 for x in p["records"]))
    def test_explicit_exact_plan_can_copy_without_deleting_or_overwriting(self):
        p=module.private_review_source_plan(self.repo)
        result=module.stage_approved_private_copy(self.repo,self.private,p["plan_sha256"],4)
        self.assertEqual(result["copied_count"],4)
        self.assertFalse(result["public_release_authorised"])
        self.assertTrue(result["all_source_originals_retained"])
        for r in p["records"]:
            src=self.pub/r["source_relative_path"]
            dest=self.private/r["source_relative_path"]
            self.assertEqual(dest.read_bytes(),src.read_bytes())
            self.assertEqual(hashlib.sha256(dest.read_bytes()).hexdigest(),r["sha256"])
        with self.assertRaisesRegex(module.MigrationHold,"NO_OVERWRITE"):
            module.stage_approved_private_copy(self.repo,self.private,p["plan_sha256"],4)
    def test_wrong_count_or_changed_source_requires_new_review(self):
        p=module.private_review_source_plan(self.repo)
        with self.assertRaisesRegex(module.MigrationHold,"COUNT"):
            module.stage_approved_private_copy(self.repo,self.private,p["plan_sha256"],61)
        original=self.pub/"review/mesh/diode.json"
        original.write_text('{"vertices":[[0,0,0]]}',encoding="utf-8")
        with self.assertRaisesRegex(module.MigrationHold,"SOURCE_PLAN_CHANGED"):
            module.stage_approved_private_copy(self.repo,self.private,p["plan_sha256"],4)
        self.assertEqual(list(self.private.iterdir()),[])
    def test_invalid_static_destination_is_denied(self):
        p=module.private_review_source_plan(self.repo)
        other=self.repo/"private"
        other.mkdir(parents=True)
        with self.assertRaisesRegex(module.MigrationHold,"REPO_TREE_TARGET"):
            module.stage_approved_private_copy(self.repo,other,p["plan_sha256"],4)
        bad=self.private.parent/"public"
        bad.mkdir()
        with self.assertRaisesRegex(module.MigrationHold,"STATIC_TARGET_FORBIDDEN"):
            module.stage_approved_private_copy(self.repo,bad,p["plan_sha256"],4)
    def test_source_symlink_and_unknown_extension_hold(self):
        p=self.pub/"review/renders/not-a-review.exe"
        p.write_bytes(b"unknown")
        with self.assertRaisesRegex(module.MigrationHold,"UNEXPECTED_EXTENSION"):
            module.private_review_source_plan(self.repo)
        p.unlink()
        link=self.pub/"review/renders/shortcut.svg"
        try:
            link.symlink_to(self.pub/"review/renders/diode.svg")
        except (OSError,NotImplementedError):
            return
        with self.assertRaisesRegex(module.MigrationHold,"NONREGULAR_REFUSED"):
            module.private_review_source_plan(self.repo)
    def test_oversize_payload_denied(self):
        p=self.pub/"review/mesh/diode.json"
        with p.open("wb") as out:
            out.truncate(module.MAX_BYTES+1)
        with self.assertRaisesRegex(module.MigrationHold,"UNSUPPORTED_TYPE_OR_SIZE"):
            module.private_review_source_plan(self.repo)

if __name__=="__main__":
    unittest.main()
