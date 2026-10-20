"""Regression tests for non-destructive archive claim correlation."""
import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1]/"cgx"/"portable_node"/"archive_claim_reconciliation_plan.py"
spec=importlib.util.spec_from_file_location("archive_claim_reconciliation_plan",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def claim(**overrides):
    x={"claim_id":"claim:a", "source_ref":"provider:doc:1","sha256":"a"*64,
       "object_id":"cgx:object:birch-example","field":"diameter","value":2.0,
       "unit":"m","effective_date":"2026-08-01"}
    x.update(overrides)
    return x

class ArchiveReconciliationTests(unittest.TestCase):
    def test_same_blob_and_claim_does_not_authorize_deletion(self):
        r=m.classify_claim_pair(claim(),claim(claim_id="claim:b"))
        self.assertEqual(r["classification"],"EXACT_SOURCE_CLAIM_CANDIDATE")
        self.assertTrue(r["preserve_originals"])
        self.assertFalse(r["promote_canon"])
    def test_different_object_never_auto_merges(self):
        r=m.classify_claim_pair(claim(),claim(object_id="cgx:object:game-birch",field="diameter"))
        self.assertEqual(r["classification"],"DIFFERENT_REFERENTS")
        self.assertEqual(len(r["source_claims"]),2)
    def test_different_dates_retained(self):
        r=m.classify_claim_pair(claim(),claim(value=2.3,effective_date="2026-09-01"))
        self.assertEqual(r["classification"],"TEMPORAL_VARIANT")
    def test_same_date_disagreement_is_hold(self):
        r=m.classify_claim_pair(claim(),claim(value=3.8))
        self.assertEqual(r["classification"],"CONTRADICTORY_HOLD")
        self.assertIsNone(r["tradeoffs"]["duplicate_bytes_savings"])
    def test_missing_date_disagreement_is_hold(self):
        r=m.classify_claim_pair(claim(effective_date=None),claim(value=3.8,effective_date=None))
        self.assertEqual(r["classification"],"CONTRADICTORY_HOLD")
    def test_different_units_need_real_conversion(self):
        r=m.classify_claim_pair(claim(),claim(value=200.0,unit="cm"))
        self.assertEqual(r["classification"],"UNIT_CONVERSION_FRONTIER")
    def test_matching_values_different_sources_are_not_independent_proof(self):
        r=m.classify_claim_pair(claim(),claim(sha256="b"*64,source_ref="provider:doc:2"))
        self.assertEqual(r["classification"],"CORROBORATION_CANDIDATE")
        self.assertEqual(r["tradeoffs"]["actual_roundtrip_fidelity"],"UNTESTED")
    def test_distinct_attributes_are_kept(self):
        r=m.classify_claim_pair(claim(),claim(field="height",value=4.5))
        self.assertEqual(r["classification"],"NON_OVERLAPPING_ATTRIBUTES")
    def test_reject_invalid_source_and_date(self):
        for v in (claim(sha256="bad"),claim(effective_date="2026-99-99"),claim(unit=None)):
            with self.subTest(v=v),self.assertRaises(ValueError):
                m.classify_claim_pair(claim(),v)

if __name__=="__main__":
    unittest.main()
