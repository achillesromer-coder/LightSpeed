"""Synthetic, source-only tests. Never claim these are a real Wikipedia ingest."""
import os
import tempfile
import unittest
from pathlib import Path

from wikimedia_source_projection import (
    MAX_SEGMENT, geometric_navigation_only, project_xml_segment,
    wayback_capture_reference,
)

def xml(page_id=12, revision=54, title="Dodecahedron", body="12 faces [[geometry]] and [[Platonic solid|solids]].", ns=0):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">
 <page><title>{title}</title><ns>{ns}</ns><id>{page_id}</id>
 <revision><id>{revision}</id><timestamp>2026-10-01T00:00:00Z</timestamp><text>{body}</text></revision>
 </page></mediawiki>""".encode()

class TestWikimedia(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "source.xml"
        self.path.write_bytes(xml())

    def tearDown(self):
        self.tmp.cleanup()

    def run_projection(self, **opts):
        return project_xml_segment(self.path, source_uri="https://dumps.wikimedia.org/other/synthetic", **opts)

    def test_source_bytes_and_revision_identity_are_distinct(self):
        output = self.run_projection()
        s = output["records"][0]["source"]
        self.assertEqual(len(output["source"]["sha256"]), 64)
        self.assertEqual(s["revision_key"], "wikimedia:enwiki:page:12:revision:54")
        self.assertEqual(s["page_key"], "wikimedia:enwiki:page:12")
        self.assertEqual(s["revision_id"], 54)
        self.assertNotEqual(s["decoded_text_sha256"], s["original_segment_sha256"])

    def test_navigation_not_authoritative_geometry(self):
        r = self.run_projection()["records"][0]
        nav = r["navigation"]
        self.assertEqual(nav["shape_basis"], {"faces": 12, "edges": 30, "vertices": 20})
        self.assertEqual(len(nav["face_path"]), 3)
        self.assertTrue(all(0 <= n <= 11 for n in nav["face_path"]))
        self.assertIsNone(nav["physical_geometry"])
        self.assertIsNone(nav["canonical_object_id"])
        self.assertEqual(nav["face_path"], geometric_navigation_only(r["source"]["revision_key"])["face_path"])

    def test_links_are_candidates_not_claims(self):
        r = self.run_projection()["records"][0]
        self.assertIn("geometry", r["resolution"]["lexical_link_candidates"])
        self.assertIn("Platonic solid", r["resolution"]["lexical_link_candidates"])
        self.assertEqual(r["resolution"]["asserted_facts"], [])
        self.assertIsNone(r["resolution"]["wikidata_qid"])
        self.assertIsNone(r["admission"]["native_object_id"])

    def test_revisions_do_not_coalesce_to_page_identity(self):
        a = self.run_projection()["records"][0]
        self.path.write_bytes(xml(revision=55))
        b = self.run_projection()["records"][0]
        self.assertEqual(a["source"]["page_key"], b["source"]["page_key"])
        self.assertNotEqual(a["source"]["revision_key"], b["source"]["revision_key"])

    def test_nonarticle_namespace_skipped(self):
        self.path.write_bytes(xml(ns=10, title="Template:Example"))
        d = self.run_projection()
        self.assertEqual(d["summary"]["articles"], 0)
        self.assertEqual(d["summary"]["skipped_namespaces"], 1)

    def test_no_duplicate_revision(self):
        page_a = xml().decode().split("<page>")[1].split("</page>")[0]
        self.path.write_text('<mediawiki><page>' + page_a + '</page><page>' + page_a + '</page></mediawiki>')
        with self.assertRaisesRegex(ValueError, "DUPLICATE_REVISION"):
            self.run_projection()

    def test_revision_identity_collision(self):
        page_a = xml().decode().split("<page>")[1].split("</page>")[0]
        self.path.write_text('<mediawiki><page>' + page_a + '</page><page>' +
                             page_a.replace("12 faces", "13 faces") + '</page></mediawiki>')
        with self.assertRaisesRegex(ValueError, "REVISION_IDENTITY_COLLISION"):
            self.run_projection()

    def test_max_articles_bounded(self):
        page = xml().decode().split("<page>")[1].split("</page>")[0]
        self.path.write_text('<mediawiki><page>' + page + '</page></mediawiki>')
        with self.assertRaisesRegex(ValueError, "INVALID_COUNT"):
            self.run_projection(max_articles=0)

    def test_no_promotion_or_source_copy(self):
        p = self.run_projection()
        self.assertEqual(p["summary"]["canonical_objects_created"], 0)
        self.assertEqual(p["summary"]["source_payloads_mirrored"], 0)
        self.assertFalse(p["records"][0]["admission"]["installed_tool"])
        self.assertFalse(p["records"][0]["admission"]["canonical_write"])

    def test_wayback_is_not_reuse_licence(self):
        w = wayback_capture_reference(
            original_url="https://example.org/page",
            capture_url="https://web.archive.org/web/20200101000000/https://example.org/page",
            timestamp="20200101000000", http_status=200)
        self.assertFalse(w["copy_source"])
        self.assertEqual(w["semantic_claims"], [])
        self.assertIn("REVIEW_REQUIRED", w["rights"])

    def test_unsafe_wayback_endpoint_rejected(self):
        with self.assertRaises(ValueError):
            wayback_capture_reference(original_url="file:///etc/passwd",
                capture_url="https://web.archive.org/web/20200101000000/https://example.org",
                timestamp="20200101000000", http_status=200)

    def test_segment_quota_source_code_proof(self):
        self.assertEqual(MAX_SEGMENT, 60 * 1024 * 1024)

if __name__ == "__main__":
    unittest.main()
