"""Source-only R0 transport subset from PR175: trust and byte-lineage boundaries."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"cgx/review/r0_subset_source_fold_20261020.json"
CONTRACT=ROOT/"cgx/domain_templates/unispace_geometric_shorthand_candidate.json"

class R0SubsetSourceFoldTests(unittest.TestCase):
    def test_six_files_exact_provenance(self):
        m=json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(len(m["carried_source_files"]),6)
        for item in m["carried_source_files"]:
            raw=(ROOT/item["path"]).read_bytes()
            blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
            self.assertEqual(blob,item["git_blob_sha1"],item["path"])
    def test_owner_restricted_projection_not_accidentally_forked(self):
        m=json.loads(MANIFEST.read_text(encoding="utf-8"))
        for p in m["excluded_owner_sources"]:
            self.assertFalse((ROOT/p).exists(),p)
    def test_security_and_native_leases_remain_held(self):
        j=json.loads(CONTRACT.read_text(encoding="utf-8"))
        sec=j["security"]
        self.assertFalse(sec["codec_authenticated"])
        self.assertFalse(sec["device_admission"])
        self.assertFalse(sec["canonical_promotion_authorised"])
        self.assertFalse(sec["licence_attested"])
        self.assertEqual(j["status"],"ISOLATED_VALIDATED_BYTE_CODEC_REVIEW_ONLY")
    def test_nonempty_local_source_lines_and_prior_context_hold(self):
        d=json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(d["owner_gate"],161)
        self.assertTrue(any("ZIP often smaller" in x for x in d["limits"]))
        self.assertTrue(any("prior cache hash" in x for x in d["limits"]))
if __name__=="__main__":
    unittest.main()
