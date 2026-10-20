"""Real pinned CC0 game-catalogue R0→R1 source and exact receipt regression.

Tests original *index* bytes and their complete 161 recorded source lines.
This does not acquire, validate or license the linked game repositories/assets.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from cgx.portable_node.pinned_catalogue_source_intake import (
    stage_pinned_catalogue, hydrate_catalogue_selection,
)

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "alexandria_game_catalogue"
INDEX = ROOT / "cgx" / "review" / "alexandria_external_reference_intake_20261020.json"
PACKET = ROOT / "cgx" / "review" / "alexandria_game_catalogue_real_source_envelope_20261021.json"
README_SHA = "b7c21b00b2dc88634a4a4dcbac773d01b6e72508c023600e0dd5e2bbd02a199f"
LICENSE_SHA = "a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499"
README_BLOB = "0a54e0898d52ffa31f83f843b66aee458c5a49b8"
LICENSE_BLOB = "0e259d42c996742e9e3cba14c677129b2c1b6311"
COMMIT = "3a9ab8fc892a2cdadf8989a72ba7624a11e39cec"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def original():
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    group = next(g for g in index["groups"]
                 if g["origin"]["name"] == "bobeff/open-source-games")
    return FIX.joinpath("README.md").read_bytes(), FIX.joinpath("LICENSE").read_bytes(), group


class RealGameCatalogueIntakeTests(unittest.TestCase):
    def test_r0_original_both_git_blobs_and_independent_sha256(self):
        readme, licence, group = original()
        self.assertEqual(len(readme), 37285)
        self.assertEqual(len(licence), 7048)
        self.assertEqual(sha256(readme), README_SHA)
        self.assertEqual(sha256(licence), LICENSE_SHA)
        self.assertEqual(git_blob(readme), README_BLOB)
        self.assertEqual(git_blob(licence), LICENSE_BLOB)
        self.assertEqual(group["origin"]["readme_blob"], README_BLOB)
        self.assertEqual(group["origin"]["commit"], COMMIT)
        self.assertIn(b"CC0 1.0 Universal", licence)

    def test_exact_full_compiler_packet_matches_committed_source_free_receipt(self):
        readme, licence, group = original()
        reconstructed = stage_pinned_catalogue(
            readme, licence, group, expected_source_sha256=README_SHA,
            expected_license_sha256=LICENSE_SHA, expected_license_git_blob=LICENSE_BLOB)
        persisted = json.loads(PACKET.read_text(encoding="utf-8"))
        self.assertEqual(persisted["source_envelope"], reconstructed["source_envelope"])
        self.assertEqual(persisted["conversion_receipt"], reconstructed["conversion_receipt"])
        self.assertEqual(persisted["source_envelope"]["projections"][0]["indexed_entries"], 161)
        self.assertEqual(persisted["source_envelope"]["projections"][0]["total_lines"], 459)
        self.assertEqual(persisted["source_proof"]["selected_lines_verified"], 161)
        self.assertEqual(persisted["upstream_project_bytes_acquired"], 0)
        self.assertEqual(persisted["publication_status"], "INTERNAL_REVIEW_SOURCE_FREE_NOT_PUBLISHED")
        self.assertFalse(persisted["conversion_receipt"]["native_dbr_verified"])
        self.assertFalse(persisted["source_envelope"]["native_preservation"]["source_bytes_embedded"])

    def test_every_game_line_hash_and_exact_offsets_match_original_bytes(self):
        readme, _, group = original()
        rows = json.loads(PACKET.read_text())["source_envelope"]["projections"][0]["entries"]
        self.assertEqual(len(rows), len(group["records"]))
        source_rows = {x["line"]: x for x in group["records"]}
        self.assertEqual(len(source_rows), 161)
        for row in rows:
            start, end = row["source_byte_start"], row["source_byte_end"]
            raw = readme[start:end]
            upstream = source_rows[row["source_line"]]
            self.assertTrue(0 <= start < end <= len(readme))
            self.assertEqual(sha256(raw), row["raw_line_sha256"])
            self.assertIn(row["label"].encode("utf-8"), raw)
            self.assertEqual(row["label"], upstream["title"])
            self.assertEqual(row["source_links"], upstream["sources"])
            for url in row["source_links"]:
                self.assertIn(url.encode("utf-8"), raw)
            self.assertEqual(row["upstream_rights"], "UNVERIFIED")
            self.assertIsNone(row["object_id"])
            self.assertFalse(row["project_bytes_acquired"])

    def test_hydrate_selected_game_requires_explicit_access_and_pinned_source(self):
        readme, _, _ = original()
        receipt = json.loads(PACKET.read_text())
        for title, line, expected_url in [
            ("Hypersomnia", 28, "https://github.com/TeamHypersomnia/Hypersomnia"),
            ("VCMI Project", 438, "https://github.com/vcmi/vcmi"),
        ]:
            ref = f"alexandria:external:index:{COMMIT}:{line}"
            result = hydrate_catalogue_selection(
                receipt, ref, source_bytes=readme, access_granted=True)
            self.assertEqual(result["status"], "SOURCE_PROVEN_R1_VIEW_CANDIDATE")
            self.assertEqual(result["title"], title)
            self.assertIn(expected_url, result["upstream_reference_urls"])
            self.assertEqual(result["source_sha256"], README_SHA)
            self.assertEqual(result["licence"], "CC0-1.0")
            self.assertEqual(result["linked_project_licence"], "UNVERIFIED")
            self.assertFalse(result["canonical_admission"])
            self.assertFalse(result["authenticated"])
            self.assertIsNone(result["object_id"])
            self.assertEqual(hydrate_catalogue_selection(
                receipt, ref, source_bytes=readme)["status"], "WITHHELD")
            self.assertEqual(hydrate_catalogue_selection(
                receipt, ref, access_granted=True)["status"], "NOT_CACHED")
            self.assertEqual(hydrate_catalogue_selection(
                receipt, ref, source_bytes=readme, access_granted=True,
                audience="PUBLIC")["status"], "WITHHELD")

    def test_corruption_and_rights_forgery_are_held(self):
        readme, licence, group = original()
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            stage_pinned_catalogue(
                readme + b"changed", licence, group,
                expected_source_sha256=README_SHA,
                expected_license_sha256=LICENSE_SHA,
                expected_license_git_blob=LICENSE_BLOB)
        receipt = json.loads(PACKET.read_text())
        broken = copy.deepcopy(receipt)
        broken["source_envelope"]["projections"][0]["entries"][0]["label"] = "FORGED"
        first = f"alexandria:external:index:{COMMIT}:28"
        self.assertEqual(hydrate_catalogue_selection(
            broken, first, source_bytes=readme, access_granted=True)["status"],
            "PROJECTION_MISMATCH")
        forged_group = copy.deepcopy(group)
        forged_group["records"][0]["rights"] = "PERMITTED_GAME_LICENSE"
        with self.assertRaisesRegex(ValueError, "implicitly promoted"):
            stage_pinned_catalogue(
                readme, licence, forged_group,
                expected_source_sha256=README_SHA,
                expected_license_sha256=LICENSE_SHA,
                expected_license_git_blob=LICENSE_BLOB)


if __name__ == "__main__":
    unittest.main()
