"""Fail-closed automation and historical record intake regression tests."""
import hashlib
import unittest
from tools.cgx_automation_archive_review import INPUT, ROOT, ReviewHold, review, from_automations_peek

def row(**changes):
    r = {"source_system":"chatgpt_automation","source_kind":"automation_run",
         "source_id":"task-1","revision_id":"run-1","source_locator":"automation:task-1/run/run-1",
         "observed_at":"2026-11-22T20:00:00+10:00","domain":"cognigrex",
         "facet":"intelligence_space","content_text":"evidence text","is_active":True}
    r.update(changes)
    return r

def batch(*rows):
    return {"schema":INPUT,"canonical_root":ROOT,"observations":list(rows)}

class SourceReviewTests(unittest.TestCase):
    def test_content_hash_and_no_authority(self):
        r=review(batch(row()))
        self.assertEqual(r["observations"][0]["source_sha256"],
                         hashlib.sha256(b"evidence text").hexdigest())
        for key in ("archive_deletion_performed","native_dbr_write_performed",
                    "model_training_performed","public_release_performed","new_root_created"):
            self.assertFalse(r[key])
        self.assertFalse(r["observations"][0]["deletion_authorized"])

    def test_identical_run_is_deduplicated(self):
        r=review(batch(row(),row()))
        self.assertEqual((r["received"],r["unique"],r["duplicate_count"]),(2,1,1))

    def test_reused_identity_with_different_bytes_fails(self):
        with self.assertRaises(ReviewHold):
            review(batch(row(),row(content_text="different")))

    def test_invalid_claimed_hash_fails(self):
        with self.assertRaises(ReviewHold):
            review(batch(row(content_sha256="a"*64)))

    def test_metadata_only_hash_not_authentic(self):
        r=review(batch(row(content_text=None,content_sha256="a"*64)))
        self.assertEqual(r["held"],1)
        self.assertEqual(r["observations"][0]["hash_evidence"],"DECLARED_ONLY")

    def test_truncated_record_not_complete(self):
        r=review(batch(row(truncated=True)))
        self.assertEqual(r["observations"][0]["source_state"],"HOLD_TRUNCATED")

    def test_provider_copy_keeps_separate_identity(self):
        r=review(batch(row(),row(source_system="google_drive")))
        self.assertEqual(r["unique"],2)

    def test_order_does_not_change_manifest_hash(self):
        a,b=row(),row(source_id="task-2",revision_id="run-2")
        self.assertEqual(review(batch(a,b))["review_sha256"],review(batch(b,a))["review_sha256"])

    def test_reject_new_root(self):
        p=batch();p["canonical_root"]="cgx:root:other"
        with self.assertRaises(ReviewHold):review(p)

    def test_reject_unknown_facet(self):
        with self.assertRaises(ReviewHold):review(batch(row(facet="phantom")))

    def test_reject_bad_timestamp(self):
        with self.assertRaises(ReviewHold):review(batch(row(observed_at="2026-11-22")))

    def test_reject_invalid_flag(self):
        with self.assertRaises(ReviewHold):review(batch(row(is_active="false")))

    def test_reject_unbounded_content(self):
        with self.assertRaises(ReviewHold):review(batch(row(content_text="x"*1000001)))

    def test_peek_only_latest_result_and_task_metadata(self):
        peek={"automations":[{"id":"a","is_enabled":True,"updated_at":"2026-11-22T00:00:00Z",
                 "run_details":{"latest_result":{"run_id":"r1","content_text":"one","content_truncated":False}}},
                {"id":"b","is_enabled":False,"updated_at":"2026-11-22T00:00:00Z"}]}
        r=review(from_automations_peek(peek,"2026-11-22T20:00:00+10:00"))
        self.assertEqual((r["unique"],r["held"]),(3,2))
        self.assertFalse(r["historical_coverage_complete"])

    def test_peek_does_not_fabricate_missing_result_body(self):
        peek={"automations":[{"id":"a","is_enabled":True,
             "run_details":{"latest_result":{"run_id":"r1"}}}]}
        with self.assertRaises(ReviewHold):
            from_automations_peek(peek,"2026-11-22T20:00:00+10:00")

    def test_reject_non_string_source_type(self):
        with self.assertRaises(ReviewHold):review(batch(row(source_system=[])))

    def test_empty_batch_cannot_imply_ingestion(self):
        r=review(batch())
        self.assertEqual(r["unique"],0)
        self.assertFalse(r["native_dbr_write_performed"])

if __name__=="__main__":
    unittest.main()
