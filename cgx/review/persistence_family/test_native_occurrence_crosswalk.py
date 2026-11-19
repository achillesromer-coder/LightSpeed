#!/usr/bin/env python3
"""Native-source crosswalk denies unintended rights, source-copy or DB promotion."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from CGX_Native_Occurrence_Crosswalk import (
    CrosswalkHold, SCHEMA, from_review_search, plan_occurrences,
)
from CGX_Persistence_Core import FamilyStore

SHA = hashlib.sha256(b"shared-raw-source").hexdigest()


def occ(path="C:/private/raphael.md", agent="Raphael", rights="owner-private",
        granted=True, sha=SHA):
    return {"path": path, "agent": agent, "rights": rights,
            "source_sha256": sha, "content_granted": granted}


class TestNativeOccurrenceCrosswalk(unittest.TestCase):
    def test_empty_holds_and_never_authorizes(self):
        r = plan_occurrences([])
        self.assertEqual(r["state"], "HOLD_SOURCE_OCCURRENCE_GRANTS")
        self.assertFalse(r["native_content_access_authorized"])
        self.assertTrue(r["no_secondary_database_created"])

    def test_full_review_still_not_native_grant(self):
        r = plan_occurrences([occ()])
        self.assertEqual(r["state"], "REVIEW_REFERENCES_READY_FOR_NATIVE_ADAPTER")
        self.assertEqual(r["canonical_database"], "lightspeed_unified.db")
        self.assertFalse(r["native_acl_authenticated"])
        self.assertFalse(r["native_content_access_authorized"])
        self.assertFalse(r["native_issuer_signature_verified"])
        self.assertFalse(r["native_mint_authorized"])
        self.assertFalse(r["native_execution_performed"])
        self.assertFalse(r["training_performed"])

    def test_private_path_not_in_receipt(self):
        raw_path = "C:/private/never-include-sensitive-folder/raphael.md"
        result = plan_occurrences([occ(path=raw_path)])
        self.assertNotIn(raw_path, json.dumps(result))
        self.assertTrue(result["records"][0]["source_path_exported"] is False)

    def test_cross_role_identical_blob_keeps_separate_occurrences(self):
        result = plan_occurrences([
            occ(),
            occ(path="C:/private/athene.md", agent="Athene", rights="review-only"),
        ])
        self.assertEqual(result["occurrence_count"], 2)
        self.assertEqual(result["distinct_source_sha_count"], 1)
        self.assertEqual(result["same_bytes_distinct_occurrence_sha"], [SHA])
        self.assertNotEqual(result["records"][0]["provisional_occurrence_ref"],
                            result["records"][1]["provisional_occurrence_ref"])
        self.assertIs(result["native_content_access_authorized"], False)
        for record in result["records"]:
            self.assertIs(record["content_access_authorized"], False)

    def test_metadata_only_never_becomes_content_grant(self):
        result = plan_occurrences([occ(granted=False)])
        self.assertEqual(result["state"], "HOLD_SOURCE_OCCURRENCE_GRANTS")
        self.assertIn("METADATA_ONLY_CONTENT_NOT_GRANTED", result["hold_reasons"])

    def test_legacy_unknown_does_not_become_granted(self):
        record = occ()
        record.pop("content_granted")
        result = plan_occurrences([record])
        self.assertIn("LEGACY_OR_UNSCOPED_GRANT_UNKNOWN", result["hold_reasons"])
        self.assertFalse(result["records"][0]["content_granted_in_review"])

    def test_unscoped_review_search_is_explicit_hold(self):
        result = from_review_search([{
            "sha256": SHA,
            "occurrences": [{"path": "C:/private/r.md", "agent": "Raphael",
                             "rights": "owner-private"}]
        }])
        self.assertIn("LEGACY_OR_UNSCOPED_GRANT_UNKNOWN", result["hold_reasons"])
        self.assertFalse(result["native_content_access_authorized"])

    def test_public_rights_never_self_qualified(self):
        result = plan_occurrences([occ(rights="public-licence-verified")])
        self.assertIn("PUBLIC_LICENCE_REQUIRES_INDEPENDENT_ADMISSION", result["hold_reasons"])
        self.assertFalse(result["native_content_access_authorized"])

    def test_idempotence_sorted_order_and_duplicates(self):
        a = occ()
        b = occ(path="C:/private/a.md", agent="Athene")
        self.assertEqual(plan_occurrences([b, a, a]), plan_occurrences([a, b]))

    def test_conflicting_same_occurrence_cannot_escalate(self):
        with self.assertRaisesRegex(CrosswalkHold, "conflicting"):
            plan_occurrences([occ(granted=False), occ(granted=True)])
        with self.assertRaisesRegex(CrosswalkHold, "conflicting"):
            plan_occurrences([occ(rights="owner-private"), occ(rights="review-only")])

    def test_malformed_and_oversized_denied(self):
        for row in [
            occ(sha="bad"),
            occ(agent="rogue"),
            occ(rights="public"),
            occ(path="../private\ntrace"),
            occ(granted="true"),
            occ(agent=[]),
            occ(rights=[]),
        ]:
            with self.subTest(row=row):
                with self.assertRaises(CrosswalkHold):
                    plan_occurrences([row])
        with self.assertRaises(CrosswalkHold):
            plan_occurrences([occ()] * 513)
        with self.assertRaises(CrosswalkHold):
            from_review_search([{"sha256": SHA, "occurrences": [None]}])

    def test_family_store_real_scoped_review_readback(self):
        with tempfile.TemporaryDirectory(prefix="cgx-crosswalk-") as temp:
            root = Path(temp)
            source = root / "approved"
            source.mkdir()
            file_a = source / "a.md"
            file_b = source / "b.md"
            file_a.write_text("source occurrence crosswalk validation", encoding="utf-8")
            file_b.write_bytes(file_a.read_bytes())
            store = FamilyStore(root / "review-only")
            try:
                source_a = store.ingest("Raphael", file_a, root=source)
                store.ingest("Athene", file_b, root=source, rights="review-only",
                             store_bytes=False)
                scoped = store.source_search("crosswalk", agent="Raphael")
                native = from_review_search(scoped)
                self.assertEqual(native["occurrence_count"], 1)
                self.assertEqual(native["records"][0]["source_sha256"], source_a["sha256"])
                self.assertFalse(native["native_content_access_authorized"])
                self.assertEqual(store.source_search("crosswalk", agent="Athene"), [])
                global_preview = from_review_search(store.source_search("crosswalk"))
                self.assertEqual(global_preview["state"], "HOLD_SOURCE_OCCURRENCE_GRANTS")
                self.assertFalse(global_preview["native_content_access_authorized"])
                # Ensure this bridge creates NO DB beyond the deliberately isolated
                # existing FamilyStore fixture and never reaches an actual host DB.
                self.assertFalse((root / "lightspeed_unified.db").exists())
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
