"""Fixture-only regression of Achilles' Windows host test runner.

This test suite does not start a bridge, read a real native DB, or permit a
GitHub/cloud result to masquerade as a BouwerBase receipt.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zipfile


SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "achilles_bouwerbase_stage35.py"
SPEC = importlib.util.spec_from_file_location("achilles_bouwerbase_stage35", SOURCE)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class Stage35PureTests(unittest.TestCase):
    def test_schema_non_authorising(self):
        self.assertEqual(runner.SCHEMA, "CGX-ACHILLES-ISOLATED-ACCEPTANCE/35.1")
        self.assertEqual(len(runner.TEST_SELECTIONS), 2)
        self.assertNotIn("deploy", [name for name, _ in runner.TEST_SELECTIONS])

    def test_windows_line_endings_are_only_normalisation(self):
        self.assertEqual(runner.normalized(b"abc\r\ndef\r\n"), runner.normalized(b"abc\ndef\n"))
        self.assertEqual(runner.normalized(b"\xef\xbb\xbfabc\r\n"), "abc\n")
        self.assertNotEqual(runner.normalized(b"print(1)"), runner.normalized(b"print(2)"))

    def test_receipt_size_and_object_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "stage34.json"
            file.write_text("[]", encoding="utf-8")
            with self.assertRaises(runner.Stage35Hold):
                runner.read_json(file)
            file.write_text('{"state":"STAGED_REVIEW_ONLY_NOT_DEPLOYED"}', encoding="utf-8")
            self.assertEqual(runner.read_json(file)["state"], "STAGED_REVIEW_ONLY_NOT_DEPLOYED")

    def test_native_snapshot_reads_without_writing_or_creating(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "native.db"
            with self.assertRaises(runner.Stage35Hold):
                runner.native_snapshot(db)
            self.assertFalse(db.exists())
            with sqlite3.connect(db) as con:
                con.executescript("""
                    CREATE TABLE canonical_objects(object_id TEXT, state TEXT);
                    CREATE TABLE object_representations(
                        object_id TEXT, representation_type TEXT, state TEXT, content_sha256 TEXT
                    );
                    CREATE TABLE representation_review_packets(object_id TEXT);
                """)
                con.execute("INSERT INTO canonical_objects VALUES (?, ?)", (runner.ROOT_OBJECT, "candidate"))
                con.execute(
                    "INSERT INTO object_representations VALUES (?,?,?,?)",
                    (runner.ROOT_OBJECT, "R0_source", "candidate", runner.R0_SHA),
                )
            before = hashlib.sha256(db.read_bytes()).hexdigest()
            result = runner.native_snapshot(db)
            self.assertEqual(result["parent"], [("candidate",)])
            self.assertEqual(result["review_count"], 0)
            self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(), before)

    def test_source_archive_rejects_extra_files_and_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original_path = "desktop/LightSpeed_Runtime/lightspeed_runtime/cgx_family_ingestion.py"
            payload = b"print('fixture source')\n"
            proof = {
                "path": original_path,
                "git_blob_content_sha256": runner.digest(payload),
            }
            receipt = {
                "source_bundle": {"sha256": ""},
                "source_proofs": [proof] * 5,
            }
            zip_path = root / "source.zip"
            manifest = {
                "schema": runner.BUNDLE_SCHEMA,
                "state": "REVIEW_ONLY_NOT_INSTALLED",
                "source_commit": runner.FAMILY_COMMIT,
            }
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("source/" + original_path, payload)
                archive.writestr("manifest.json", json.dumps(manifest))
                archive.writestr("extra.json", "{}")
            receipt["source_bundle"].update(sha256=runner.digest(zip_path.read_bytes()), readback_pass=True)
            with patch.object(runner, "git", return_value=payload):
                with self.assertRaises(runner.Stage35Hold) as found:
                    runner.check_bundle(root, receipt, zip_path)
            self.assertIn("UNEXPECTED_MEMBER", str(found.exception))

    def test_unreachable_bridge_fails_closed(self):
        with patch.object(runner, "build_opener") as build:
            build.return_value.open.side_effect = OSError("host offline")
            with self.assertRaisesRegex(runner.Stage35Hold, "BRIDGE_LOOPBACK_UNREACHABLE"):
                runner.bridge_status()

    def test_non_windows_execution_is_rejected(self):
        with patch.object(runner.os, "name", "posix"):
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                with self.assertRaisesRegex(runner.Stage35Hold, "WINDOWS_ONLY"):
                    runner.run(
                        repo=root, stage34_file=root / "a", bundle=root / "b",
                        downloads=root, core=root, frontend=root, db=root / "c",
                        python=root / "d",
                    )

    def test_script_cannot_start_remote_agent_or_native_mint(self):
        source = SOURCE.read_text(encoding="utf-8")
        for dangerous in (
            "desktop-commander@latest remote",
            "ExecutionPolicy Bypass",
            "taskkill /F",
            "npx.cmd",
            "run_cognigrex_local_stack.py",
        ):
            self.assertNotIn(dangerous, source)


if __name__ == "__main__":
    unittest.main()
