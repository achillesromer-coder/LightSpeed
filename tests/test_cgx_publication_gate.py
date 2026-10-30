#!/usr/bin/env python3
"""C37 source-only publication stop-ship regressions.

These checks exercise the real CLI process. Synthetic assessment flags are
untrusted input and do not constitute signed DBR, ACL, or owner acceptance.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cgx_assurance_route import route as assurance_route
from resolve_cgx_extensions import resolve as custodial_resolve

PREFLIGHT = ROOT / "scripts" / "cgx_consequence_preflight.py"
REQUIRED_HOLD = "publication:authenticated-source-rights-and-owner-release-unverified"


def run_preflight(depth, tags="", cascade="C0", assurance=None, custodial=None):
    with tempfile.TemporaryDirectory(prefix="cgx-c37-test-") as tmp:
        args = [sys.executable, str(PREFLIGHT), "--domain", "romer",
                "--execution-depth", depth, "--cascade-class", cascade,
                "--tags", tags]
        for flag, payload, name in (
            ("--assurance-assessment-json", assurance, "assurance.json"),
            ("--custodial-assessment-json", custodial, "custodial.json"),
        ):
            if payload is not None:
                path = Path(tmp) / name
                path.write_text(json.dumps(payload), encoding="utf-8")
                args.extend([flag, str(path)])
        result = subprocess.run(args, capture_output=True, text=True,
                                check=False, timeout=15)
        if not result.stdout.strip():
            raise AssertionError(f"preflight had no JSON output: {result.stderr}")
        return result.returncode, json.loads(result.stdout)


class PublicationAuthorityGateTests(unittest.TestCase):
    def assert_publication_held(self, tags):
        code, receipt = run_preflight("publish", tags)
        self.assertEqual(code, 3, receipt)
        self.assertEqual(receipt["decision"], "HOLD")
        self.assertIn(REQUIRED_HOLD, receipt["hold_reasons"])
        self.assertEqual(receipt["context"]["execution_depth"], "publish")

    def test_untagged_publication_is_held(self):
        self.assert_publication_held("")

    def test_scientific_tags_cannot_replace_authority(self):
        self.assert_publication_held("scientific-asset,ephemeris,spatial-scale,provenance")

    def test_public_claim_is_held(self):
        self.assert_publication_held("public-claim")

    def test_public_projection_is_held(self):
        self.assert_publication_held("public-projection")

    def test_self_attested_complete_reviews_do_not_grant_publication(self):
        tags = ["public-claim", "public-projection"]
        ar = assurance_route("romer", "publish", "C0", tags)
        cr = custodial_resolve("romer", "publish", "standard", "C0", tags)
        assurance = {
            "source_verified": True,
            "method_receipts": {
                method: {"state": "BOUNDED", "evidence_ids": ["fixture:untrusted"]}
                for method in ar["required_methods"]
            },
            "blocking_findings": False,
        }
        custodial = {
            "source_verified": True,
            "authority_confirmed": True,
            "authority_phase": "PRE_LAUNCH",
            "authority_contract_verified": True,
            "root_authority_approved": True,
            "hard_predicates": {x: True for x in cr["hard_predicates"]},
            "release_class": "Public",
            "target_visibility": "public",
            "release_approval_state": "APPROVED",
            "source_release_classes": ["Public"],
            "contains_restricted_material": False,
        }
        code, receipt = run_preflight(
            "publish", ",".join(tags), assurance=assurance, custodial=custodial
        )
        self.assertEqual(receipt["assurance"]["decision"], "ALLOW")
        self.assertEqual(receipt["custodial"]["decision"], "ALLOW")
        self.assertEqual(code, 3)
        self.assertIn(REQUIRED_HOLD, receipt["hold_reasons"])

    def test_low_consequence_inspection_remains_available(self):
        code, receipt = run_preflight("inspect", "source-review")
        self.assertEqual(code, 0, receipt)
        self.assertEqual(receipt["decision"], "ALLOW_WITH_RECEIPTS")

    def test_unqualified_c2_execution_remains_held(self):
        code, receipt = run_preflight("execute", "", cascade="C2")
        self.assertEqual(code, 3, receipt)
        self.assertEqual(receipt["decision"], "HOLD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
