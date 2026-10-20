"""Regression tests for a complete but rights-held Alexandria Basic review ZIP."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"cgx/review/alexandria_basic_offline_kit.py"
spec=importlib.util.spec_from_file_location("alexandria_kit",P)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class AlexandriaBasicKitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first=mod.make_review_package()
        cls.second=mod.make_review_package()
        cls.zip=zipfile.ZipFile(io.BytesIO(cls.first))
    def test_reproducible_bytes_and_fixed_zip_entry_set(self):
        self.assertEqual(self.first,self.second)
        self.assertEqual(sorted(self.zip.namelist()),sorted(mod.ZIP_ENTRY_NAMES))
        self.assertTrue(all(x.date_time==(2020,1,1,0,0,0) for x in self.zip.infolist()))
    def test_every_manifested_file_has_exact_digest_and_length(self):
        manifest=json.loads(self.zip.read("manifest.json"))
        self.assertEqual(manifest["status"],"REVIEW_ONLY_NOT_PUBLIC_RELEASE")
        self.assertFalse(manifest["signed"])
        self.assertFalse(manifest["verified_on_second_device"])
        self.assertFalse(manifest["catalogue_canonical"])
        self.assertFalse(manifest["contains_private_cgx_assets"])
        self.assertFalse(manifest["contains_executables"])
        for item in manifest["content"]:
            raw=self.zip.read(item["name"])
            self.assertEqual(item["sha256"],hashlib.sha256(raw).hexdigest())
            self.assertEqual(item["bytes"],len(raw))
    def test_source_refs_stay_251_and_lessons_18(self):
        refs=json.loads(self.zip.read("catalogue.json"))
        lessons=json.loads(self.zip.read("lessons.json"))
        self.assertEqual(refs["source_count"],251)
        self.assertEqual(len(refs["references"]),251)
        self.assertEqual(len(lessons["modules"]),18)
        self.assertTrue(all(x["module_state"]=="UNEXECUTED_SOURCE_LINKED_EDUCATION"
                            for x in lessons["modules"]))
        self.assertTrue(all(x["rights"] in ("UNVERIFIED_FOR_REDISTRIBUTION",
                                           "UPSTREAM_LICENSE_UNVERIFIED","REFERENCE_ONLY_HOLD")
                            for x in refs["references"]))
    def test_no_external_scripts_and_private_render_root(self):
        html=self.zip.read("index.html").decode("utf-8")
        self.assertIn("Content-Security-Policy",html)
        self.assertIn("connect-src &#x27;none&#x27;",html)
        self.assertNotIn("<script src=",html)
        self.assertNotIn('src="https://',html)
        self.assertNotIn("fetch(",html)
        self.assertNotIn("component_geometry_atlas_public_review.json",html)
        self.assertNotIn("/review/renders/",html)
        self.assertNotIn("/review/mesh/",html)
        self.assertIn("not an authorised public release",html)
    def test_source_owner_references_preserve_original_hashes(self):
        manifest=json.loads(self.zip.read("manifest.json"))
        for name,proof in manifest["source_roots"].items():
            payload=(ROOT/"cgx/review"/name).read_bytes()
            self.assertEqual(proof["sha256"],hashlib.sha256(payload).hexdigest())
            self.assertEqual(proof["byte_length"],len(payload))
if __name__=="__main__":
    unittest.main()
