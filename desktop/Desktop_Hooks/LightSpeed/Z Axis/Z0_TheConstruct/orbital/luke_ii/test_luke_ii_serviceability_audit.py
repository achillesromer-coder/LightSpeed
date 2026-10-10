from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from luke_ii_serviceability_audit import build_audit, write_audit

class LukeIIServiceabilityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parameters = json.loads((HERE / "luke_ii_parameters.json").read_text(encoding="utf-8"))
        cls.audit = build_audit(cls.parameters)

    def test_serviceability_reference_audit_passes(self):
        self.assertEqual(self.audit["status"], "PASS_SERVICEABILITY_REFERENCE_AUDIT")
        self.assertFalse(self.audit["failures"])
        self.assertTrue(all(self.audit["checks"].values()))

    def test_attachment_and_cable_graphs_resolve(self):
        unresolved = self.audit["unresolved"]
        for key, values in unresolved.items():
            self.assertFalse(values, key)

    def test_access_window_walkway_and_arm_reservations(self):
        c = self.audit["counts"]
        self.assertEqual(c["window_layers"], 120)
        self.assertEqual(c["window_frame_parts"], 120)
        self.assertEqual(c["walkway_segments"], 25)
        self.assertEqual(c["egress_segments"], 25)
        self.assertGreaterEqual(c["service_clearances"], 250)
        self.assertGreaterEqual(c["removal_paths"], 200)
        self.assertEqual(c["mark_iii_interface_arm_nodes"], 23)

    def test_outputs_are_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_json, first_csv = write_audit(self.audit, Path(first))
            second_json, second_csv = write_audit(self.audit, Path(second))
            self.assertEqual(first_json.read_bytes(), second_json.read_bytes())
            self.assertEqual(first_csv.read_bytes(), second_csv.read_bytes())

if __name__ == "__main__":
    unittest.main()
