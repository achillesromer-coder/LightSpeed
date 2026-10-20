"""Alexandria heterogeneous source intake + known Vite-public privacy gate tests."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(relative):
    path=ROOT/relative
    spec=importlib.util.spec_from_file_location(path.stem,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

al=load("cgx/review/alexandria_library_projection.py")
gate=load("cgx/review/unispace_public_asset_boundary.py")
catalogue=load("cgx/review/library_coverage_projection.py")

class AlexandriaLibraryReviewTests(unittest.TestCase):
    def test_curated_and_legacy_catalogues_are_source_bound(self):
        p=al.project_alexandria_index(ROOT)
        self.assertEqual(p["counts"]["curated_repository_entries"],31)
        self.assertEqual(p["counts"]["official_reference_roots"],13)
        self.assertEqual(p["counts"]["legacy_list_entries"],207)
        self.assertEqual(p["counts"]["learning_tracks"],6)
        self.assertTrue(p["all_upstreams_without_release_grants"])
        self.assertTrue(p["all_upstreams_without_runtime_acceptance"])
        self.assertEqual(p["status"],"DERIVED_DISCOVERY_ONLY_NO_PROVIDER_EXECUTION")
        for s in p["source_roots"].values():
            self.assertEqual(s["sha256"],hashlib.sha256((ROOT/s["path"]).read_bytes()).hexdigest())

    def test_normalisation_does_not_mistake_files_and_user_tokens_for_repo(self):
        good={"https://github.com/nasa/fprime":"nasa/fprime",
              "https://github.com/NASA/FPrime/":"nasa/fprime",
              "https://github.com/NASA/FPrime.git":"nasa/fprime"}
        for url,value in good.items():
            self.assertEqual(al.github_repo_identity(url),value)
        for bad in (
            "http://github.com/nasa/fprime",
            "https://github.com/nasa/fprime/tree/main",
            "https://evil.com/nasa/fprime",
            "https://github.com/user:password@nasa/fprime",
            "https://github.com/nasa/fprime?token=secret",
            "https://github.com/nasa/fprime#anchor",
            "https://github.com/nasa/fprime/README.md",
            "file:///private/source"
        ):
            with self.subTest(bad=bad):
                self.assertIsNone(al.github_repo_identity(bad))

    def test_no_unverified_licenses_become_public_pack_source(self):
        src=json.loads((ROOT/"cgx/review/alexandria_curated_upstream_tools_20261020.json").read_text())
        self.assertEqual(len(src["repositories"]),31)
        self.assertTrue(all(x["admission"]=="REFERENCE_ONLY_HOLD" and
                            not x["source_code_downloaded"] and
                            not x["redistribution_authorised"] and
                            not x["license_file_verified"] for x in src["repositories"]))
        self.assertTrue(any(x["github_licence_metadata"]=="NOASSERTION" for x in src["repositories"]))
        self.assertEqual(len([x for x in src["repositories"] if x["observed_commit"]]),8)

    def test_learning_tracks_reference_only_real_catalogue_ids(self):
        p=al.project_alexandria_index(ROOT)
        self.assertGreaterEqual(p["counts"]["unique_normalized_upstream_repo_candidates"],31)
        self.assertEqual(len(p["domain_counts"]),11)
        self.assertEqual(sum(p["domain_counts"].values()),31)

    def test_original_cgx_registers_stay_distinct_and_unqualified(self):
        p=catalogue.build_library_coverage(ROOT)
        self.assertEqual(p["counts"]["declared_file_profiles"],33)
        self.assertEqual(p["counts"]["total_distinct_lenses"],34)
        self.assertEqual(p["counts"]["toolkits"],12)
        self.assertEqual(p["counts"]["volumetric_kernels"],40)
        self.assertEqual(p["status"],"DERIVED_READ_ONLY_NOT_AUTHORITY_NOT_LIVE_CAPABILITY_PROOF")

    def test_fixture_private_static_routes_are_detected_without_exposing_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            d=root/"apps/lightspeed-go/public/data"
            d.mkdir(parents=True)
            (d/"cgx_object_review_catalogue.json").write_text('{"secret":"never-in-a-report"}')
            review=root/"apps/lightspeed-go/public/review/renders"
            review.mkdir(parents=True)
            (review/"hidden.svg").write_text("<svg>private-asset</svg>")
            report=gate.audit_public_assets(root)
            self.assertEqual(report["state"],"HOLD_PUBLIC_RELEASE")
            self.assertEqual(report["known_internal_static_file_count"],2)
            self.assertNotIn("never-in-a-report",json.dumps(report))
            self.assertFalse(report["release_authorised"])

    def test_strict_command_rejects_static_private_fixture(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); p=root/"apps/lightspeed-go/public/data"
            p.mkdir(parents=True);(p/"component_geometry_atlas_public_review.json").write_text("{}")
            proc=subprocess.run([sys.executable,str(ROOT/"cgx/review/unispace_public_asset_boundary.py"),
                                 "--root",str(root),"--strict"],capture_output=True,text=True)
            self.assertEqual(proc.returncode,2)
            self.assertIn("HOLD_PUBLIC_RELEASE",proc.stdout)

    def test_clean_fixture_is_not_a_false_release_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            report=gate.audit_public_assets(Path(temp))
            self.assertEqual(report["state"],"NO_KNOWN_PATH_BLOCKERS_UNVERIFIED")
            self.assertFalse(report["release_authorised"])
            self.assertEqual(report["negative_live_http_tests"],"NOT_PERFORMED")

    def test_real_repo_audit_never_claims_release_without_live_http(self):
        p=gate.audit_public_assets(ROOT)
        self.assertFalse(p["release_authorised"])
        self.assertEqual(p["private_server_acl"],"NOT_VERIFIED")
        self.assertEqual(p["negative_live_http_tests"],"NOT_PERFORMED")
        if p["known_internal_static_file_count"]:
            self.assertEqual(p["state"],"HOLD_PUBLIC_RELEASE")
if __name__=="__main__":
    unittest.main()
