from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from luke_ii_dimensional_audit import build_audit, classify_node, write_audit


class LukeIIDimensionalAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parameters = json.loads((HERE / "luke_ii_parameters.json").read_text(encoding="utf-8"))
        cls.rows, cls.summary = build_audit(cls.parameters)

    def test_all_named_nodes_are_registered_once(self):
        names = [row["node_name"] for row in self.rows]
        self.assertEqual(len(names), 96)
        self.assertEqual(len(set(names)), 96)
        self.assertEqual(self.summary["node_count"], 96)

    def test_mesh_quality_is_preserved(self):
        self.assertTrue(self.summary["all_nodes_watertight"])
        self.assertTrue(self.summary["all_nodes_winding_consistent"])

    def test_claim_sensitive_nodes_remain_bounded(self):
        self.assertEqual(classify_node("FIELD_GUIDE_RING_1")[1], "ILLUSTRATIVE_ONLY_NOT_PHYSICAL_FIELD")
        self.assertEqual(classify_node("PAYLOAD_ACTIVE")[1], "ILLUSTRATIVE_SEQUENCE_ONLY")
        self.assertEqual(classify_node("SYSTEM_DAMPING_PLACEHOLDER_1")[1], "CONCEPTUAL_SPECIALIST_REVIEW")
        self.assertEqual(classify_node("INTERFACE_PROVISIONAL_DOCKING_COLLAR_1")[1], "PROVISIONAL_INTERFACE")

    def test_audit_outputs_are_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_csv, first_json = write_audit(self.rows, self.summary, Path(first))
            second_csv, second_json = write_audit(self.rows, self.summary, Path(second))
            self.assertEqual(first_csv.read_bytes(), second_csv.read_bytes())
            self.assertEqual(first_json.read_bytes(), second_json.read_bytes())


if __name__ == "__main__":
    unittest.main()
