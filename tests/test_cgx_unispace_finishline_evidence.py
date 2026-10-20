"""Validate the non-authoritative CGX/UniSpace finish-line evidence snapshot."""
from __future__ import annotations
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"cgx/review/cgx_unispace_finishline_evidence_20261021.json"

class FinishlineEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(PATH.read_text(encoding="utf-8"))
    def test_every_domain_has_five_explicit_gates_with_no_fake_partial_pass(self):
        domains=self.data["domains"]
        self.assertEqual(len(domains),9)
        self.assertEqual(len({d["id"] for d in domains}),len(domains))
        for domain in domains:
            self.assertEqual(len(domain["gates"]),5)
            self.assertEqual(len({g["label"] for g in domain["gates"]}),5)
            for gate in domain["gates"]:
                self.assertIn(gate["status"],("PASS","HOLD"))
                if gate["status"]=="PASS":
                    self.assertTrue(gate["evidence_refs"],(domain["id"],gate["label"]))
                    self.assertIsNone(gate["acceptance_needed"])
                else:
                    self.assertTrue(gate["acceptance_needed"],(domain["id"],gate["label"]))
    def test_fraction_is_generated_by_milestone_counts_not_guessed(self):
        g=[v for d in self.data["domains"] for v in d["gates"]]
        passed=sum(v["status"]=="PASS" for v in g)
        a=self.data["acceptance_summary"]
        self.assertEqual(a["milestones_pass"],passed)
        self.assertEqual(a["milestones_total"],len(g))
        self.assertEqual(a["checkpoint_coverage_percent"],round(100*passed/len(g)))
        self.assertEqual((passed,len(g)),(21,45))
        self.assertEqual(a["checkpoint_coverage_percent"],47)
    def test_every_pass_ref_has_source_lineage(self):
        known=self.data["source_heads"]
        for domain in self.data["domains"]:
            for gate in domain["gates"]:
                for reference in gate["evidence_refs"]:
                    self.assertIn(reference,known,(domain["id"],reference))
        for ref,sha in known.items():
            self.assertTrue(ref.startswith("PR"))
            self.assertRegex(sha,r"^[a-f0-9]{40}$")
    def test_public_native_and_physical_gate_cannot_be_declared_released(self):
        d=self.data
        self.assertEqual(d["release_state"],"HOLD_PUBLIC_158_AND_NATIVE_161")
        self.assertEqual(d["controls"]["protected_issues"],[158,161])
        self.assertTrue(d["controls"]["do_not_merge_main"])
        self.assertEqual(d["controls"]["known_public_review_assets_held"],61)
        for label in ("public_releases_approved","native_two_node_acceptances_verified",
                      "physical_build_qualifications_verified"):
            self.assertEqual(d["acceptance_summary"][label],0)
        for domain in d["domains"]:
            self.assertEqual(domain["gates"][-1]["status"],"HOLD")
    def test_new_alexandria_source_updates_are_not_silently_marked_installed(self):
        d=self.data["upstream_draft_update"]
        self.assertEqual(d["pr"],180)
        self.assertEqual(d["status"],"SOURCE_ONLY_NEW_R0_FILES_NOT_FULLY_FOLDED")
        self.assertEqual(d["head"],self.data["source_heads"]["PR180"])
        for p in d["specific_unfolded"]:
            self.assertFalse((ROOT/p).exists(),p)
    def test_existing_migration_scanner_and_kit_remain_in_stack(self):
        for path in (
            "cgx/review/private_object_asset_migration.py",
            "cgx/review/private_source_byte_disclosure_gate.py",
            "cgx/review/alexandria_basic_offline_kit.py",
            "apps/lightspeed-go/src/privateObjectReview.ts",
            "cgx/review/library_coverage_projection.py",
        ):
            self.assertTrue((ROOT/path).is_file(),path)

if __name__=="__main__":
    unittest.main()
