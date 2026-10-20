"""Selective R0 Alexandria fold: exact original Git blobs and independent source rights."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
FOLD=ROOT/"cgx/review/alexandria_source_subset_fold_20261021.json"

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

class SelectiveAlexandriaSourceFold(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads(FOLD.read_text(encoding="utf-8"))
    def test_every_carried_original_file_has_exact_upstream_git_blob(self):
        rows=self.m["exact_git_blobs"]
        self.assertEqual(len(rows),29)
        seen=set()
        for row in rows:
            path=row["path"]
            self.assertNotIn(path,seen);seen.add(path)
            self.assertFalse(path.startswith("apps/"))
            self.assertFalse(path.startswith("desktop/"))
            self.assertEqual(blob((ROOT/path).read_bytes()),row["blob_sha1"],path)
    def test_rights_and_runtime_admission_remain_hold(self):
        m=self.m
        self.assertEqual(m["source_pr"],180)
        self.assertEqual(m["parent"],"Cognigrex.cgx")
        self.assertRegex(m["source_head"],r"^[a-f0-9]{40}$")
        r=m["rights"]
        for k in ("all_dependencies_complete","all_assets_relicensed",
                  "redistribution_approved","compiled","network_handshake_verified",
                  "canonical_promotion"):
            self.assertIs(r[k],False,k)
        self.assertEqual(len(m["held_paths"]),1)
        self.assertEqual(m["held_paths"][0]["status"],"SOURCE_FETCH_UNRESOLVED")
    def test_existing_private_review_source_and_identity_are_unchanged(self):
        for path in ("apps/lightspeed-go/src/privateObjectReview.ts",
                     "desktop/LightSpeed_Runtime/lightspeed_runtime/ls_go_bridge.py",
                     "desktop/source-manifest.json",
                     "cgx/review/private_source_byte_disclosure_gate.py"):
            self.assertTrue((ROOT/path).is_file())
        source=json.loads((ROOT/"desktop/source-manifest.json").read_text())
        self.assertEqual(len(source["records"]),736)
        self.assertEqual(self.m["excluded_conflicts"],
                         ["apps/lightspeed-go/src/main.ts",
                          "apps/lightspeed-go/src/desktopBridge.ts",
                          "desktop/LightSpeed_Runtime/lightspeed_runtime/ls_go_bridge.py",
                          "desktop/source-manifest.json",
                          "desktop/LightSpeed_Runtime/tests/test_owner_credentials.py"])
    def test_original_project_scope_still_refuses_complete_build_claim(self):
        a=json.loads((ROOT/"cgx/review/alexandria_hypersomnia_project_source_scope_20261021.json").read_text())
        b=json.loads((ROOT/"cgx/review/alexandria_libdatachannel_source_scope_20261021.json").read_text())
        self.assertEqual(a["source_file_count"],4)
        self.assertEqual(b["original_file_count"],5)
        self.assertFalse(a["all_assets_acquired"])
        self.assertFalse(a["all_dependencies_acquired"])
        self.assertFalse(a["licence_release_approved"])
        self.assertFalse(b["all_project_source_acquired"])
        self.assertFalse(b["capability_claims"]["compiled"])
        self.assertFalse(b["capability_claims"]["network_interoperability_tested"])
    def test_missing_requested_libjuice_header_not_silently_reconstructed(self):
        held=self.m["held_paths"][0]["path"]
        self.assertFalse((ROOT/held).exists())
        self.assertIn("fetch",self.m["held_paths"][0]["reason"].lower())
if __name__=="__main__":
    unittest.main()
