"""Negative-path tests for the only CGX files allowed into the public site."""
from __future__ import annotations
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "apps" / "lightspeed-go" / "scripts" / "assemble_cgx_public_site.py"
SOURCE = ROOT / "apps" / "lightspeed-go" / "public" / "cgx"
spec = importlib.util.spec_from_file_location("cgx_public_assembler", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PublicSiteIsolationTests(unittest.TestCase):
    def test_only_explicit_public_assets_are_in_distribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "isolated-site"
            manifest = mod.assemble_cgx_public(SOURCE, output)
            self.assertEqual(manifest["allowed_file_count"], 12)
            self.assertFalse(manifest["live_deployment_verified"])
            self.assertFalse(manifest["rights_release_authorized"])
            self.assertFalse(manifest["native_cgx_authentication"])
            self.assertFalse(manifest["contains_internal_review_files"])
            self.assertTrue((output / "cgx" / "fs" / "index.html").is_file())
            self.assertTrue((output / "cgx" / "assets" / "viewer.js").is_file())
            self.assertTrue((output / "vercel.json").is_file())
            self.assertFalse((output / "index.html").exists())
            self.assertFalse((output / "data").exists())
            self.assertFalse((output / "review").exists())
            self.assertFalse((output / "ls-go").exists())
            self.assertFalse((output / "cgx" / "deployment").exists())
            self.assertEqual(len(list(output.rglob("*"))),
                             len(list((output / "cgx").rglob("*"))) + 2 + 1)
            receipt = json.loads((output / mod.MANIFEST_NAME).read_text())
            self.assertEqual(receipt, manifest)

    def test_source_bytes_and_digest_roundtrip(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "release"
            manifest = mod.assemble_cgx_public(SOURCE, output)
            for record in manifest["assets"]:
                data = (output / record["path"]).read_bytes()
                self.assertEqual(len(data), record["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])
                source_bytes = (SOURCE / Path(record["path"]).relative_to("cgx")).read_bytes()
                self.assertEqual(data, source_bytes)

    def test_unrelated_public_directory_content_is_never_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "public"
            isolated = source_root / "cgx"
            shutil.copytree(SOURCE, isolated)
            (source_root / "data").mkdir()
            (source_root / "data" / "private-preview.json").write_text(
                "SENSITIVE_LEGACY_PREVIEW", encoding="utf-8")
            (source_root / "review").mkdir()
            (source_root / "review" / "owner-source.json").write_text(
                "SENSITIVE_OWNER", encoding="utf-8")
            (source_root / "ls-go").mkdir()
            (source_root / "ls-go" / "index.html").write_text(
                "PRIVATE_APPLICATION", encoding="utf-8")
            manifest = mod.assemble_cgx_public(isolated, Path(tmp) / "out")
            self.assertEqual(manifest["allowed_file_count"], 12)
            rendered = b"".join(x.read_bytes() for x in (Path(tmp) / "out").rglob("*") if x.is_file())
            self.assertNotIn(b"SENSITIVE_LEGACY_PREVIEW", rendered)
            self.assertNotIn(b"SENSITIVE_OWNER", rendered)
            self.assertNotIn(b"PRIVATE_APPLICATION", rendered)

    def test_unlisted_asset_cannot_join_public_release_implicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            isolated = Path(tmp) / "cgx"
            shutil.copytree(SOURCE, isolated)
            (isolated / "assets" / "owner.json").write_text("SECRET")
            out = Path(tmp) / "release"
            manifest = mod.assemble_cgx_public(isolated, out)
            self.assertEqual(manifest["allowed_file_count"], 12)
            self.assertFalse((out / "cgx" / "assets" / "owner.json").exists())

    def test_forbidden_source_marker_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            isolated = Path(tmp) / "cgx"
            shutil.copytree(SOURCE, isolated)
            with (isolated / "assets" / "core.js").open("ab") as file:
                file.write(b"\n// /api/v1/secret\n")
            with self.assertRaisesRegex(ValueError, "Private or operational"):
                mod.assemble_cgx_public(isolated, Path(tmp) / "release")

    def test_symlinked_public_asset_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            isolated = Path(tmp) / "cgx"
            shutil.copytree(SOURCE, isolated)
            candidate = isolated / "assets" / "core.js"
            candidate.unlink()
            private = Path(tmp) / "private.js"
            private.write_text("sensitive")
            try:
                candidate.symlink_to(private)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            with self.assertRaisesRegex(ValueError, "linked or untrusted"):
                mod.assemble_cgx_public(isolated, Path(tmp) / "out")

    def test_release_build_does_not_mutate_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            out.mkdir()
            protected = out / "do-not-delete"
            protected.write_text("PRESERVE")
            with self.assertRaisesRegex(ValueError, "Refusing"):
                mod.assemble_cgx_public(SOURCE, out)
            self.assertEqual(protected.read_text(), "PRESERVE")

    def test_release_output_cannot_overlay_cgx_source(self):
        with self.assertRaisesRegex(ValueError, "separate"):
            mod.assemble_cgx_public(SOURCE, SOURCE / "release")
        with self.assertRaisesRegex(ValueError, "separate"):
            mod.assemble_cgx_public(SOURCE, SOURCE.parent.parent.parent)

    def test_release_policy_preserves_public_only_csp(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "isolated"
            mod.assemble_cgx_public(SOURCE, out)
            policy = json.loads((out / "vercel.json").read_text())
            csp = next(h["value"] for rule in policy["headers"]
                       for h in rule["headers"]
                       if h["key"] == "Content-Security-Policy")
            self.assertIn("connect-src 'none'", csp)
            self.assertIn("frame-ancestors https://romer.industries", csp)
            self.assertIn("form-action 'none'", csp)


if __name__ == "__main__":
    unittest.main()
