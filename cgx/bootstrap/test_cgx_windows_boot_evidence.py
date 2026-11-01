"""Offline, fixture-only tests; never validates an actual S92 authority or host lease."""
from __future__ import annotations

from contextlib import closing
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
            "frontier_count": 0,
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
    with closing(sqlite3.connect(path)) as conn, conn:
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

    def test_required_family_children_cannot_be_omitted_or_reparented(self):
        # A syntactically valid acyclic registry is not sufficient for the
        # canonical Romer/Eco/EMASSC -> LS relationship.
        cases = ("missing_ls", "ls_reparented", "romer_id_changed", "eco_filespace_changed")
        path = self.repo / "cgx/domain_templates/domain_child_identity_registry.json"
        for case in cases:
            with self.subTest(case=case):
                source = family()
                if case == "missing_ls":
                    del source["children"]["lightspeed"]
                elif case == "ls_reparented":
                    source["children"]["lightspeed"]["parent_semantic_object_id"] = probe.SEMANTIC_ROOT
                elif case == "romer_id_changed":
                    source["children"]["romer"]["semantic_object_id"] = "cgx:domain:other-romer"
                else:
                    source["children"]["eco"]["filespace"] = "OtherEco.cgx"
                write_json(path, source)
                with self.assertRaisesRegex(ValueError, "FAMILY_REQUIRED_CHILD_MISSING_OR_MISBOUND"):
                    probe._family_identity(path)
                result = self.run_probe()
                self.assertIn("CANONICAL_FAMILY_REGISTRY_UNVERIFIED", result["holds"])
                self.assertFalse(result["boot"]["existing_stack_prerequisites_ready"])
        write_json(path, family())

    def test_additional_children_are_portable_and_casefold_collision_free(self):
        path = self.repo / "cgx/domain_templates/domain_child_identity_registry.json"
        source = family()
        source["children"]["science"] = {
            "semantic_object_id": "cgx:domain:science",
            "parent_semantic_object_id": "cgx:domain:emassc",
            "domain_id": "science",
            "filespace": "Other-Science.cgx",
        }
        write_json(path, source)
        accepted = probe._family_identity(path)
        self.assertEqual(len(accepted["children"]), 5)

        invalid = (
            "../escape.cgx", "..\\\\escape.cgx", "C:stream.cgx",
            "CON.cgx", "LPT1.cgx", "CONIN$.cgx", "CONOUT$.cgx",
            "bad" + chr(0x200b) + ".cgx", "bad" + chr(10) + ".cgx",
            "e" + chr(0x301) + ".cgx", "Other-Science.CGX",
            "ls.cgx", "cognigrex.cgx", "a%2fb.cgx",
        )
        for filespace in invalid:
            with self.subTest(filespace=filespace):
                source["children"]["science"]["filespace"] = filespace
                write_json(path, source)
                with self.assertRaisesRegex(ValueError, "FAMILY_ID_COLLISION_OR_INVALID"):
                    probe._family_identity(path)
                receipt = self.run_probe()
                self.assertIn("CANONICAL_FAMILY_REGISTRY_UNVERIFIED", receipt["holds"])
                self.assertFalse(receipt["boot"]["existing_stack_prerequisites_ready"])
        write_json(path, family())

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
        with closing(sqlite3.connect(self.db)) as con, con:
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
        with closing(sqlite3.connect(self.db)) as con, con:
            con.execute("UPDATE canonical_objects SET state='active'")
        (self.repo / "desktop/LightSpeed_Runtime/lightspeed_runtime").mkdir(parents=True, exist_ok=True)
        (self.repo / "desktop/LightSpeed_Runtime/lightspeed_runtime/cgx_family_ingestion.py").write_text("fixture")
        output = self.run_probe()
        self.assertTrue(output["boot"]["family_source_wiring_candidate"])
        self.assertFalse(output["boot"]["complete_integrated_cgx_ready"])
        self.assertFalse(output["mint"]["native_mint_authorised"])
        self.assertIn("ATOMIC_DBR_AND_INDEPENDENT_RECEIVER_NOT_VERIFIED", output["holds"])


    def test_loopback_health_non_object_json_fails_closed_without_network(self):
        # A localhost HTTP 200 response is not authenticated native authority.
        # Non-object JSON must not crash the read-only host diagnostic.
        class Response:
            status = 200
            def __init__(self, payload):
                self.payload = payload
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
            def read(self, limit):
                return self.payload[:limit]

        class Opener:
            def __init__(self, bridge_payload):
                self.bridge_payload = bridge_payload
            def open(self, request, timeout):
                if request.full_url.endswith("/api/v1/status"):
                    return Response(self.bridge_payload)
                return Response(b"<!doctype html><html></html>")

        for payload, expected in (
            (b"[]", "UNRECOGNISED_SERVICE"),
            (b"null", "UNRECOGNISED_SERVICE"),
            (b'"ls-go"', "UNRECOGNISED_SERVICE"),
            (b'{"bridge":"other"}', "UNRECOGNISED_SERVICE"),
            (b'{"bridge":"ls-go"}', "LS_GO_IDENTITY_SEEN"),
            (b"not-json", "NOT_VERIFIED"),
        ):
            with self.subTest(payload=payload):
                with patch.object(probe, "build_opener", return_value=Opener(payload)):
                    result = probe._loopback_status(False)
                self.assertEqual(result["bridge"], expected)
                self.assertEqual(result["go"], "HTTP_200")


    def test_extended_windows_filespace_abi_negative_names(self):
        # Source-only negative cases reconciled against the #206 handshake
        # basename review. Neither validator grants an Object_ID, lease or DBR.
        invalid = (
            "COM1.cgx", "COM9.cgx", "LPT9.cgx",
            "COM\u00b9.cgx", "LPT\u00b2.cgx", "COM\u00b3.cgx",
            "bad\u007f.cgx", "bad\u0085.cgx",
            "bad\u202e.cgx", "bad\ud800.cgx",
            "bad..cgx", "name:.cgx", "name%2e.cgx",
            "CON .cgx", "PRN .cgx", "COM1 .cgx", "LPT1 .cgx",
            "Ordinary .cgx", "Ordinary.v2 .cgx", "CON.v2 .cgx",
        )
        for name in invalid:
            with self.subTest(name=repr(name)):
                self.assertFalse(probe._portable_filespace(name))
        for name in ("Eco.cgx", "Other-Science.cgx", "caf\u00e9.cgx"):
            with self.subTest(name=name):
                self.assertTrue(probe._portable_filespace(name))


if __name__ == "__main__":
    unittest.main()
