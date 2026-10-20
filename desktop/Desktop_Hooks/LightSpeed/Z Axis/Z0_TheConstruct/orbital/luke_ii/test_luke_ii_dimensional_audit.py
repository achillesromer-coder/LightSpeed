from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from luke_ii_dimensional_audit import build_audit, write_audit

EXPECTED_FINGERPRINT = "1e58a8e6c5643c4d7d6320de5740b5451a7919259c9aa7d886285ea9f8a3bf8a"

class LukeIIDimensionalAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parameters = json.loads((HERE / "luke_ii_parameters.json").read_text(encoding="utf-8"))
        cls.rows, cls.summary = build_audit(cls.parameters)

    def test_all_named_nodes_are_registered_once(self):
        names = [row["node_name"] for row in self.rows]
        self.assertEqual(len(names), 1357)
        self.assertEqual(len(set(names)), 1357)
        self.assertEqual(self.summary["node_count"], 1357)
        self.assertEqual(self.summary["physical_node_count"], 824)

    def test_mesh_quality_and_semantic_fingerprint(self):
        self.assertTrue(self.summary["all_nodes_watertight"])
        self.assertTrue(self.summary["all_nodes_winding_consistent"])
        self.assertEqual(self.summary["semantic_geometry_sha256"], EXPECTED_FINGERPRINT)

    def test_claim_sensitive_families_remain_bounded(self):
        by_name = {row["node_name"]: row for row in self.rows}
        self.assertIn("ILLUSTRATIVE", by_name["FIELD_GUIDE_RING_1"]["evidence_state"])
        self.assertIn("ILLUSTRATIVE", by_name["PAYLOAD_ACTIVE"]["evidence_state"])
        self.assertIn("SPECIALIST", by_name["SYSTEM_DAMPING_PLACEHOLDER_1"]["evidence_state"])
        self.assertIn("PROVISIONAL", by_name["INTERFACE_PROVISIONAL_DOCKING_COLLAR_1"]["evidence_state"])
        self.assertIn("PROVISIONAL", by_name["INTERFACE_MARK_III_ARM_UPPER_LINK"]["evidence_state"])

    def test_audit_outputs_are_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_csv, first_json = write_audit(self.rows, self.summary, Path(first))
            second_csv, second_json = write_audit(self.rows, self.summary, Path(second))
            self.assertEqual(first_csv.read_bytes(), second_csv.read_bytes())
            self.assertEqual(first_json.read_bytes(), second_json.read_bytes())

if __name__ == "__main__":
    unittest.main()
