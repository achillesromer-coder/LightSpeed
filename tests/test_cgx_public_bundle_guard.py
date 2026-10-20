"""UniSpace synthetic-only static bundle and private operator disclosure gates."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"apps/lightspeed-go/scripts/cgx_public_bundle_guard.py"
SPEC=importlib.util.spec_from_file_location("cgx_public_bundle_guard",FILE)
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class PublicBundleTests(unittest.TestCase):
    def test_exact_pr174_source_blobs_are_preserved(self):
        receipt=json.loads((ROOT/"cgx/review/unispace_public_source_fold_20261020.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["source_pr"],174)
        self.assertEqual(len(receipt["carried_source_files"]),18)
        for item in receipt["carried_source_files"]:
            raw=(ROOT/item["path"]).read_bytes()
            blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
            self.assertEqual(blob,item["git_blob_sha1"],item["path"])

    def test_existing_cgx_tree_exact_allowlist(self):
        report=mod.inspect_public_bundle()
        self.assertEqual(report["file_count"],12)
        self.assertEqual({x["path"] for x in report["assets"]},{"cgx/"+s for s in mod.APPROVED})
        self.assertFalse(report["operator_source_included"])
        self.assertFalse(report["external_host_live_verified"])
        self.assertFalse(report["source_licences_independently_cleared"])

    def test_fresh_package_contains_only_cgx_and_policy(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"release"
            review=mod.make_public_bundle(out)
            files={p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
            self.assertEqual(files,{"cgx/"+p for p in mod.APPROVED}|{"vercel.json","cgx-package-review.json"})
            self.assertFalse((out/"data").exists())
            self.assertFalse((out/"review").exists())
            self.assertFalse((out/"src").exists())
            self.assertFalse((out/"cgx/deployment").exists())
            for x in review["assets"]:
                raw=(out/x["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),x["sha256"])
            self.assertFalse(json.loads((out/"cgx-package-review.json").read_text())["external_host_live_verified"])

    def test_unreviewed_asset_is_not_automatically_packaged(self):
        with tempfile.TemporaryDirectory() as d:
            copy=Path(d)/"cgx"
            shutil.copytree(mod.SOURCE,copy)
            (copy/"internal_dump.json").write_text('{"private":true}',encoding="utf-8")
            with self.assertRaisesRegex(mod.BundleHold,"unexpected public payload"):
                mod.inspect_public_bundle(copy)

    def test_private_catalogue_or_native_api_reference_rejected(self):
        for attack in [
          'fetch("/data/cgx_object_review_catalogue.json")',
          'fetch("/api/v1/cgx/intake")',
          'import {x} from "../../../desktopBridge"',
          'const pwd = "sk-proj-DO_NOT_USE_TEST"',
        ]:
            with self.subTest(attack=attack),tempfile.TemporaryDirectory() as d:
                c=Path(d)/"cgx"
                shutil.copytree(mod.SOURCE,c)
                with (c/"assets/core.js").open("a",encoding="utf-8") as f:
                    f.write("\n"+attack)
                with self.assertRaises(mod.BundleHold):
                    mod.inspect_public_bundle(c)

    def test_no_symlink_intake(self):
        with tempfile.TemporaryDirectory() as d:
            c=Path(d)/"cgx"
            shutil.copytree(mod.SOURCE,c)
            (c/"internal_link").symlink_to(c/"assets/core.js")
            with self.assertRaises(mod.BundleHold):
                mod.inspect_public_bundle(c)

    def test_public_bundle_never_overwrites_existing_folder(self):
        with tempfile.TemporaryDirectory() as d:
            existing=Path(d)/"release"
            existing.mkdir()
            (existing/"keep.txt").write_text("owner bytes",encoding="utf-8")
            with self.assertRaisesRegex(mod.BundleHold,"overwrite"):
                mod.make_public_bundle(existing)
            self.assertEqual((existing/"keep.txt").read_text(),"owner bytes")

    def test_missing_release_headers_holds_and_removes_incomplete_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            c=Path(d)/"cgx"
            shutil.copytree(mod.SOURCE,c)
            p=c/"deployment/vercel.json"
            x=json.loads(p.read_text(encoding="utf-8"))
            x["headers"][0]["headers"]=[h for h in x["headers"][0]["headers"] if h["key"]!="Content-Security-Policy"]
            p.write_text(json.dumps(x),encoding="utf-8")
            output=Path(d)/"bundle"
            with self.assertRaisesRegex(mod.BundleHold,"content security policy"):
                mod.make_public_bundle(output,c)
            self.assertFalse(output.exists())

    def test_does_not_write_under_operator_public(self):
        with self.assertRaises(mod.BundleHold):
            mod.make_public_bundle(ROOT/"apps/lightspeed-go/public/new_release_subtree")

if __name__=="__main__":unittest.main()
