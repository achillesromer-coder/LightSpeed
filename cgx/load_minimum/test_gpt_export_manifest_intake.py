"""Synthetic LOAD GPT export source-only intake regression tests.

No real chat messages, private user data or provider credentials are fixtures.
"""
import copy
import hashlib
import json
import unittest

try:
    from .gptExportManifestIntake import IntakeHold, project_manifest_bytes, SCHEMA
except ImportError:
    from gptExportManifestIntake import IntakeHold, project_manifest_bytes, SCHEMA


def fixture():
    return {
        "version": 1,
        "manifest_file": "export_manifest.json",
        "export_files": [
            {"path": "ads.json", "size_bytes": 2},
            {"path": "conversations-000.json", "size_bytes": 12},
            {"path": "conversations-001.json", "size_bytes": 30},
            {"path": "assets/photo.png", "size_bytes": 20},
        ],
        "logical_files": {
            "ads.json": {"files": ["ads.json"], "sharded": False},
            "conversations.json": {
                "files": ["conversations-000.json", "conversations-001.json"],
                "sharded": True, "shard_count": 2,
            },
            "assets/photo.png": {"files": ["assets/photo.png"], "sharded": False},
        },
    }


def encode(value):
    return json.dumps(value, sort_keys=True).encode("utf-8")


class GPTExportIntakeTests(unittest.TestCase):
    def test_manifest_projection_has_no_authority_or_body_transfer(self):
        raw = encode(fixture())
        projected = project_manifest_bytes(raw)
        self.assertEqual(projected["schema"], SCHEMA)
        self.assertEqual(projected["state"], "R0_EXPORT_MANIFEST_BYTES_VERIFIED_ONLY")
        self.assertEqual(projected["source_manifest"]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(projected["summary"]["conversation_shard_count"], 2)
        self.assertEqual(projected["summary"]["declared_conversation_bytes"], 42)
        self.assertEqual(projected["summary"]["declared_physical_bytes"], 64)
        self.assertEqual(projected["effects"]["object_ids_minted"], 0)
        self.assertEqual(projected["effects"]["source_bodies_read"], 0)
        self.assertEqual(projected["admission"], "MANIFEST_R0_READ_ONLY_NOT_NATIVE")
        self.assertTrue(all(s["r0_body_sha256"] is None for s in projected["conversation_shards"]))
        self.assertNotIn("ads.json", json.dumps(projected))  # private non-shard paths never projected

    def test_refuses_path_traversal(self):
        for bad in ("../outside.json", "nested/../escape.json", "/etc/passwd", "C:/private", "sub\\file", "a//b"):
            obj = fixture()
            obj["export_files"][3]["path"] = bad
            with self.subTest(bad=bad), self.assertRaisesRegex(IntakeHold, "UNSAFE_MANIFEST_PATH"):
                project_manifest_bytes(encode(obj))

    def test_refuses_duplicate_source_path(self):
        obj = fixture()
        obj["export_files"].append(copy.deepcopy(obj["export_files"][0]))
        with self.assertRaisesRegex(IntakeHold, "DUPLICATE_EXPORT_PATH"):
            project_manifest_bytes(encode(obj))

    def test_refuses_missing_shard_body_declared(self):
        obj = fixture()
        obj["export_files"] = obj["export_files"][:2] + obj["export_files"][3:]
        with self.assertRaisesRegex(IntakeHold, "LOGICAL_SOURCE_MISSING"):
            project_manifest_bytes(encode(obj))

    def test_refuses_noncontiguous_or_out_of_order_shards(self):
        obj = fixture()
        obj["logical_files"]["conversations.json"]["files"].reverse()
        with self.assertRaisesRegex(IntakeHold, "NONCONTIGUOUS_CONVERSATION_SHARDS"):
            project_manifest_bytes(encode(obj))

    def test_refuses_conflicting_shard_count(self):
        obj = fixture()
        obj["logical_files"]["conversations.json"]["shard_count"] = 3
        with self.assertRaisesRegex(IntakeHold, "SHARD_COUNT_MISMATCH"):
            project_manifest_bytes(encode(obj))

    def test_refuses_invalid_declared_size(self):
        for value in (-1, True, "12"):
            obj = fixture()
            obj["export_files"][0]["size_bytes"] = value
            with self.subTest(value=value), self.assertRaisesRegex(IntakeHold, "INVALID_EXPORT_SIZE"):
                project_manifest_bytes(encode(obj))

    def test_refuses_oversized_manifest_and_invalid_json(self):
        with self.assertRaisesRegex(IntakeHold, "MANIFEST_SIZE_HOLD"):
            project_manifest_bytes(b" " * (5 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(IntakeHold, "INVALID_MANIFEST_JSON"):
            project_manifest_bytes(b'{"version": 1')

    def test_refuses_undeclared_shard_or_unexpected_file_shape(self):
        obj = fixture()
        obj["logical_files"]["conversations.json"]["sharded"] = False
        with self.assertRaisesRegex(IntakeHold, "CONVERSATION_SHARDS_UNDECLARED"):
            project_manifest_bytes(encode(obj))
        obj = fixture()
        obj["export_files"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(IntakeHold, "UNEXPECTED_EXPORT_FILE_SHAPE"):
            project_manifest_bytes(encode(obj))


if __name__ == "__main__":
    unittest.main()
