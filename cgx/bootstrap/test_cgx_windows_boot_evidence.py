"""Offline, fixture-only tests; never validates an actual S92 authority or host lease."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import cgxWindowsBootEvidence as probe


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def family():
    root = probe.SEMANTIC_ROOT
    return {
        "schema": probe.FAMILY_IDENTITY_SCHEMA,
        "root": {"semantic_object_id": root, "filespace": "Cognigrex.cgx"},
        "children": {
            "romer": {
                "semantic_object_id": "cgx:domain:romer", "parent_semantic_object_id": root,
                "domain_id": "romer", "filespace": "Romer.cgx",
            },
            "emassc": {
                "semantic_object_id": "cgx:domain:emassc", "parent_semantic_object_id": root,
                "domain_id": "emassc", "filespace": "EMASSC.cgx",
            },
            "lightspeed": {
                "semantic_object_id": "cgx:domain:lightspeed",
                "parent_semantic_object_id": "cgx:domain:emassc",
                "domain_id": "lightspeed", "filespace": "LS.cgx",
            },
            "eco": {
                "semantic_object_id": "cgx:domain:eco", "parent_semantic_object_id": root,
                "domain_id": "eco", "filespace": "Eco.cgx",
            },
        },
    }


def load_source():
    registry = "cgx/domain_templates/first_file_conversion_registry.json"
    return {
        "schema": probe.LOAD_SOURCE_SCHEMA,
        "state": "GIT_SOURCE_ONLY_NOT_CANONICAL",
        "parent": "Cognigrex.cgx",
        "file_space": "LOAD.cgx",
        "summary": {
            "record_count": 1, "record_categories": {"conversion_source": 1},
            "native_accepted": 0, "native_host_verified": False,
            "source_bodies_copied": 0,
        },
        "source_registries": {registry: {"git_blob": "a" * 40}},
        "records": [{
            "category": "conversion_source",
            "source_key": "FF-MARK3-XLSX-001",
            "source_registry": registry,
            "source_git_blob": "a" * 40,
            "admission": "SOURCE_REGISTRY_ONLY",
            "provider_private_locator": "DO_NOT_SURFACE",
        }],
        "frontier": [],
    }


def database(path, sha, *, state="candidate"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE canonical_objects(object_id TEXT, state TEXT);
            CREATE TABLE object_representations(
                object_id TEXT, representation_type TEXT, state TEXT,
                content_sha256 TEXT
            );
            CREATE TABLE object_identifiers(
                object_id TEXT, identifier_value TEXT, state TEXT
            );
        """)
        conn.execute(
            "INSERT INTO canonical_objects VALUES (?,?)", (probe.S92_INSTANCE, state),
        )
        conn.execute(
            "INSERT INTO object_representations VALUES (?,?,?,?)",
            (probe.S92_INSTANCE, "R0_source", state, sha),
        )
        conn.execute(
            "INSERT INTO object_identifiers VALUES (?,?,?)",
            (probe.S92_INSTANCE, probe.SEMANTIC_ROOT, "active"),
        )
    return path


class WindowsBootEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="cgx-windows-review-fixture-")
        self.addCleanup(self.workspace.cleanup)
        root = Path(self.workspace.name)
        self.repo = root / "repo"
        self.canonical = root / "LightSpeed"
        self.host = root / "Cognigrex"
        self.repo.mkdir()
        self.host.mkdir()
        self.fake_bytes = b"fixture-only-not-real-s92"
        self.fake_sha = hashlib.sha256(self.fake_bytes).hexdigest()
        write_json(
            self.repo / "cgx/domain_templates/domain_child_identity_registry.json",
            family(),
        )
        (self.host / "Cognigrex.cgx").write_bytes(self.fake_bytes)
        write_json(
            self.host / "cognigrex.root.json",
            {"root_carrier": {"object_id": probe.S92_INSTANCE, "sha256": self.fake_sha}},
        )
        self.db = database(
            self.canonical / "Data/db/lightspeed_unified.db", self.fake_sha,
        )
        for item in (
            self.canonical / "Environment/Scripts/python.exe",
            self.canonical / "Apps/lightspeed-go/dist/index.html",
            self.canonical / "Automation/run_cognigrex_local_stack.py",
            self.repo / "tools/launch_lightspeed.ps1",
            self.repo / "cgx/bootstrap/unifiedBootstrap.mjs",
            self.repo / "cgx/bootstrap/smartSetup.html",
        ):
            item.parent.mkdir(parents=True, exist_ok=True)
            item.write_text("fixture", encoding="utf-8")
        self.load = write_json(self.repo / "source-review.json", load_source())

    def run_probe(self, *, load=True):
        with patch.object(probe, "S92_SHA256", self.fake_sha):
            return probe.build_evidence(
                self.repo, self.canonical, self.host,
                load_registry=self.load if load else None, offline=True,
            )

    def test_single_family_parent_and_nested_lightspeed_identity(self):
        result = probe._family_identity(
            self.repo / "cgx/domain_templates/domain_child_identity_registry.json",
        )
        children = {c["domain"]: c for c in result["children"]}
        self.assertEqual(children["lightspeed"]["parent_semantic_object_id"], "cgx:domain:emassc")
        self.assertEqual(len(children), 4)

    def test_root_drift_and_parent_cycle_fail_closed(self):
        source = family()
        source["children"]["emassc"]["parent_semantic_object_id"] = "cgx:domain:lightspeed"
        write_json(self.repo / "cgx/domain_templates/domain_child_identity_registry.json", source)
        with self.assertRaisesRegex(ValueError, "CYCLE"):
            probe._family_identity(
                self.repo / "cgx/domain_templates/domain_child_identity_registry.json",
            )

    def test_source_only_load_does_not_expose_provider_locator(self):
        output = self.run_probe()
        self.assertEqual(output["load_alexandria"]["source_refs"], 1)
        self.assertFalse(output["mint"]["native_mint_authorised"])
        self.assertEqual(output["mint"]["object_ids_created"], 0)
        self.assertNotIn("DO_NOT_SURFACE", json.dumps(output))
        self.assertEqual(output["services"], {"bridge": "NOT_QUERIED", "go": "NOT_QUERIED"})

    def test_boot_preflight_and_mint_are_independent(self):
        output = self.run_probe()
        self.assertTrue(output["boot"]["existing_stack_prerequisites_ready"])
        self.assertFalse(output["boot"]["complete_integrated_cgx_ready"])
        self.assertEqual(output["operational"]["parent_instance_state"], "candidate")
        self.assertFalse(output["mint"]["native_mint_authorised"])
        self.assertFalse(output["s92_carrier"]["native_signature_verified"])

    def test_changed_r0_hash_blocks_boot(self):
        with sqlite3.connect(self.db) as con:
            con.execute(
                "UPDATE object_representations SET content_sha256=?",
                ("0" * 64,),
            )
        before = hashlib.sha256(self.db.read_bytes()).hexdigest()
        result = self.run_probe()
        self.assertFalse(result["boot"]["existing_stack_prerequisites_ready"])
        self.assertIn("OPERATIONAL_R0_HASH_UNVERIFIED", result["holds"])
        self.assertEqual(before, hashlib.sha256(self.db.read_bytes()).hexdigest())

    def test_forged_load_native_admission_fails_closed(self):
        source = load_source()
        source["summary"]["native_accepted"] = 1
        write_json(self.load, source)
        result = self.run_probe()
        self.assertEqual(result["load_alexandria"]["state"], "HOLD_UNTRUSTED_REFERENCE_PROJECTION")
        self.assertIn("LOAD_SOURCE_REGISTRY_HOLD", result["holds"])
        self.assertFalse(result["mint"]["native_mint_authorised"])

    def test_database_absence_never_creates_a_database(self):
        self.db.unlink()
        output = self.run_probe()
        self.assertIn("EXISTING_OPERATIONAL_DATABASE_NOT_READABLE", output["holds"])
        self.assertFalse(self.db.exists())

    def test_fake_active_operational_row_still_not_native_admission(self):
        with sqlite3.connect(self.db) as con:
            con.execute("UPDATE canonical_objects SET state='active'")
        (self.repo / "desktop/LightSpeed_Runtime/lightspeed_runtime").mkdir(parents=True, exist_ok=True)
        (self.repo / "desktop/LightSpeed_Runtime/lightspeed_runtime/cgx_family_ingestion.py").write_text("fixture")
        output = self.run_probe()
        self.assertTrue(output["boot"]["complete_integrated_cgx_ready"])
        self.assertFalse(output["mint"]["native_mint_authorised"])
        self.assertIn("ATOMIC_DBR_AND_INDEPENDENT_RECEIVER_NOT_VERIFIED", output["holds"])


if __name__ == "__main__":
    unittest.main()
