"""Adversarial synthetic checks for private CGX source-byte Vite release guard."""
from __future__ import annotations
import base64
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"cgx/review/private_source_byte_disclosure_gate.py"
spec=importlib.util.spec_from_file_location("_cgx_byte_gate",SOURCE)
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class PrivateByteReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.temp_root=Path(self.temp.name)
        self.repo=self.temp_root/"synthetic_repository"
        self.public=self.repo/"apps/lightspeed-go/public"
        self.dist=self.repo/"apps/lightspeed-go/dist"
        self.dist.mkdir(parents=True)
        long_text=b'{"engineering":"INTERNAL_EXAMPLE_ONLY","notes":"Private source line\\nrepeat", "scope":"review"}'*3
        self.fixture={
            "data/cgx_object_review_catalogue.json":long_text,
            "data/component_geometry_atlas_public_review.json":b'{"object_count":411}',
            "review/renders/test.svg":b"<svg>Private/source-only drawing repeated to be deliberately long enough for an embedded-byte match</svg>"*2,
            "review/mesh/test.json":b'{"vertices":[0,1,2],"rights":"PRIVATE"}',
        }
        for name,raw in self.fixture.items():
            f=self.public/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw)
    def write_dist(self,name,raw):
        p=self.dist/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(raw)
        return p
    def scan(self,**kwargs):
        return gate.scan_public_distribution(repository_root=self.repo,scan_root=self.dist,**kwargs)

    def test_unrelated_bundle_is_not_public_release_authority(self):
        self.write_dist("assets/index-a.js",b"console.log('synthetic harmless app')")
        out=self.scan()
        self.assertEqual(out["private_byte_matches"],0)
        self.assertEqual(out["source_items_verified"],4)
        self.assertEqual(out["state"],"NO_MATCHING_COMPLETE_PRIVATE_BYTES_UNVERIFIED")
        self.assertFalse(out["public_release_authorised"])
        self.assertEqual(out["live_http_negative_tests"],"NOT_PERFORMED")

    def test_same_private_file_renamed_to_unrecognized_route_blocks(self):
        self.write_dist("assets/innocent-looking.bin",self.fixture["data/component_geometry_atlas_public_review.json"])
        out=self.scan()
        self.assertEqual(out["private_byte_matches"],1)
        self.assertEqual(out["matches"][0]["match"],"EXACT_RENAMED_OR_ORIGINAL_FILE")
        self.assertNotIn("component_geometry_atlas",json.dumps(out))
        self.assertNotIn("INTERNAL_EXAMPLE_ONLY",json.dumps(out))

    def test_complete_source_blob_embedded_inside_javascript_blocks(self):
        self.write_dist("assets/safe-looking.js",b"const q="+self.fixture["data/cgx_object_review_catalogue.json"]+b";")
        out=self.scan()
        self.assertEqual(out["private_byte_matches"],1)
        self.assertEqual(out["matches"][0]["match"],"EMBEDDED_ORIGINAL_BYTES")

    def test_base64_derived_bundle_blocks(self):
        self.write_dist("assets/chunks.js",b'window.x="'+base64.b64encode(self.fixture["review/renders/test.svg"])+b'";')
        out=self.scan()
        self.assertTrue(any(m["match"]=="ENCODED_COMPLETE_SOURCE" for m in out["matches"]))

    def test_json_escaped_complete_source_blocks(self):
        source=self.fixture["data/cgx_object_review_catalogue.json"].decode("utf-8")
        encoded=json.dumps(source,ensure_ascii=True)[1:-1].encode()
        self.write_dist("index.html",b"<script>window.payload='"+encoded+b"'</script>")
        out=self.scan()
        self.assertEqual(out["matches"][0]["match"],"ENCODED_COMPLETE_SOURCE")

    def test_symlink_output_file_is_hold_not_ignored(self):
        other=self.write_dist("assets/normal.js",b"ok")
        link=self.dist/"assets/shared.js"
        try: link.symlink_to(other)
        except (OSError,NotImplementedError): self.skipTest("platform cannot create symlink")
        with self.assertRaisesRegex(gate.DisclosureHold,"SYMLINK"):
            self.scan()

    def test_missing_distribution_root_fails_closed(self):
        self.dist.rmdir()
        with self.assertRaisesRegex(gate.DisclosureHold,"PUBLIC_SCAN_ROOT_MISSING"):
            self.scan()

    def test_scanner_does_not_read_unbounded_build_tree(self):
        huge=self.write_dist("assets/huge.js",b"0")
        with huge.open("wb") as f:f.truncate(gate.MAX_SCAN_BYTES+1)
        with self.assertRaisesRegex(gate.DisclosureHold,"TOTAL_SIZE_BOUND"):
            self.scan()

    def test_owner_private_root_with_exact_external_plan_works_after_static_source_removed(self):
        migration=gate._migration()
        plan=migration.private_review_source_plan(self.repo)
        private=self.temp_root/"owner-private"
        private.mkdir()
        migration.stage_approved_private_copy(self.repo,private,plan["plan_sha256"],4)
        approval_file=self.temp_root/"source-plan.json"
        approval_file.write_text(json.dumps(plan))
        self.write_dist("assets/renamed.js",self.fixture["review/mesh/test.json"])
        for f in self.public.rglob("*"):
            if f.is_file():f.unlink()
        scan=self.scan(private_root=private,approved_plan_file=approval_file)
        self.assertEqual(scan["private_byte_matches"],1)
        self.assertEqual(scan["source_plan_sha256"],plan["plan_sha256"])
        self.assertFalse(scan["owner_acl_verified"])

    def test_mutated_owner_private_source_is_hold_even_with_matching_metadata(self):
        migration=gate._migration()
        plan=migration.private_review_source_plan(self.repo)
        private=self.temp_root/"owner-private"
        private.mkdir()
        migration.stage_approved_private_copy(self.repo,private,plan["plan_sha256"],4)
        approval_file=self.temp_root/"source-plan.json"
        approval_file.write_text(json.dumps(plan))
        (private/"review/mesh/test.json").write_bytes(b"tampered")
        with self.assertRaisesRegex(gate.DisclosureHold,"SOURCE_PLAN_READBACK_MISMATCH"):
            self.scan(private_root=private,approved_plan_file=approval_file)

    def test_tampered_approval_file_and_repo_hosted_manifest_are_denied(self):
        migration=gate._migration()
        plan=migration.private_review_source_plan(self.repo)
        private=self.temp_root/"owner-private"
        private.mkdir()
        migration.stage_approved_private_copy(self.repo,private,plan["plan_sha256"],4)
        approval_file=self.temp_root/"source-plan.json"
        changed={**plan,"plan_sha256":"0"*64}
        approval_file.write_text(json.dumps(changed))
        with self.assertRaisesRegex(gate.DisclosureHold,"PLAN_CONTENT_DIGEST_MISMATCH"):
            self.scan(private_root=private,approved_plan_file=approval_file)
        inside=self.repo/"owner-plan.json"
        inside.write_text(json.dumps(plan))
        with self.assertRaisesRegex(gate.DisclosureHold,"OWNER_PLAN_MUST_BE_PRIVATE"):
            self.scan(private_root=private,approved_plan_file=inside)

    def test_cli_returns_hold_without_leaking_source_contents(self):
        self.write_dist("data/exposed-renamed.json",self.fixture["data/cgx_object_review_catalogue.json"])
        result=subprocess.run([sys.executable,str(SOURCE),"--root",str(self.repo),
                               "--scan-root",str(self.dist)],capture_output=True,text=True)
        self.assertEqual(result.returncode,2,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report["state"],"HOLD_PRIVATE_SOURCE_BYTES_PRESENT")
        self.assertNotIn("INTERNAL_EXAMPLE_ONLY",result.stdout)
        self.assertFalse(report["public_release_authorised"])

if __name__=="__main__":unittest.main()
