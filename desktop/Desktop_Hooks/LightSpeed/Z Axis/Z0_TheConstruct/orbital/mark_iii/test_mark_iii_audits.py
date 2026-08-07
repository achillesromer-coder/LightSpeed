from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mark_iii_dimensional_audit import build_audit, write_audit
from mark_iii_manufacturing_audit import build_audit as build_manufacturing, write as write_manufacturing
from mark_iii_serviceability_audit import build_audit as build_serviceability, write as write_serviceability

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / "mark_iii_parameters.json").read_text())
SEMANTIC = "205912a4f248db9a444f30f5b258d78285dc5799e657b684af82e4fe1474a339"


class MarkIIIAuditTests(unittest.TestCase):
    def test_dimensional_register_covers_all_nodes(self) -> None:
        rows, summary = build_audit(P)
        self.assertEqual(len(rows), 786)
        self.assertEqual(summary["physical_node_count"], 486)
        self.assertTrue(summary["all_nodes_watertight"])
        self.assertEqual(summary["semantic_geometry_sha256"], SEMANTIC)
        self.assertEqual(summary["schema_version"], "mark-iii-dimensional-audit-v0.3.3")

    def test_serviceability_gate_passes(self) -> None:
        audit = build_serviceability(P)
        self.assertEqual(audit["status"], "PASS_SERVICEABILITY_REFERENCE_AUDIT")
        self.assertFalse(audit["failures"])
        self.assertEqual(audit["canonical_module_envelope_m"]["extents"], [0.75, 0.32, 0.32])

    def test_serviceability_counts_and_known_unknowns(self) -> None:
        audit = build_serviceability(P)
        self.assertEqual(audit["counts"]["physical_nodes"], 486)
        self.assertEqual(audit["counts"]["service_clearances"], 110)
        self.assertEqual(audit["counts"]["removal_paths"], 87)
        self.assertEqual(audit["counts"]["resonators"], 25)
        self.assertEqual(audit["counts"]["solenoid_nodes"], 18)
        self.assertEqual(audit["counts"]["print_reference_count"], 20)
        self.assertEqual(audit["counts"]["propulsion_interfaces"], 4)
        self.assertEqual(audit["counts"]["reservoir_placeholders"], 1)
        self.assertEqual(audit["counts"]["propulsion_service_ports"], 1)
        self.assertEqual(audit["counts"]["fluid_route_reservations"], 5)
        self.assertGreaterEqual(len(audit["known_unknowns"]), 16)

    def test_manufacturing_reference_gate_passes_but_release_is_blocked(self) -> None:
        audit = build_manufacturing(P)
        self.assertEqual(
            audit["status"], "PASS_MANUFACTURING_REFERENCE_CONTROLS_DEPLOYMENT_BLOCKED"
        )
        self.assertFalse(audit["failures"])
        self.assertEqual(audit["counts"]["panels"], 18)
        self.assertEqual(audit["counts"]["print_references"], 20)
        self.assertEqual(audit["manufacturing_release"], "BLOCKED")
        self.assertEqual(audit["flight_or_deployment_release"], "BLOCKED")

    def test_audit_outputs_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            rows, summary = build_audit(P)
            first_paths = write_audit(rows, summary, Path(first))
            second_paths = write_audit(rows, summary, Path(second))
            self.assertEqual(
                [path.read_bytes() for path in first_paths],
                [path.read_bytes() for path in second_paths],
            )

            service = build_serviceability(P)
            first_paths = write_serviceability(service, Path(first))
            second_paths = write_serviceability(service, Path(second))
            self.assertEqual(
                [path.read_bytes() for path in first_paths],
                [path.read_bytes() for path in second_paths],
            )

            manufacturing = build_manufacturing(P)
            first_paths = write_manufacturing(manufacturing, Path(first))
            second_paths = write_manufacturing(manufacturing, Path(second))
            self.assertEqual(
                [path.read_bytes() for path in first_paths],
                [path.read_bytes() for path in second_paths],
            )


if __name__ == "__main__":
    unittest.main()
