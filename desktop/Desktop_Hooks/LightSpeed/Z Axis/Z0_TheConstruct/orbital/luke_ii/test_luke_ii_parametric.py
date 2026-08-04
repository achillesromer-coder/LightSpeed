from __future__ import annotations
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from luke_ii_parametric import build_print_references, build_reference


class LukeIIParametricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = json.loads((HERE / "luke_ii_parameters.json").read_text(encoding="utf-8"))
        cls.scene, cls.records = build_reference(cls.params)
        cls.counts = Counter(r["family"] for r in cls.records)

    def test_source_geometry_and_task_gate(self):
        p = self.params
        self.assertEqual(p["source_parameters"]["major_radius_m"]["value"], 12.0)
        self.assertEqual(p["source_parameters"]["body_minor_radius_m"]["value"], 2.0)
        self.assertEqual(p["source_parameters"]["field_sector_count"]["value"], 16)
        self.assertAlmostEqual(p["derived_geometry"]["central_aperture_diameter_m"], 20.0)
        self.assertEqual(p["closure_revision"]["task_state"], "CURRENT_NEXT_TASK_LUKE_CLOSURE_BEFORE_MARK_III")

    def test_habitation_volume_reservations_are_ordered(self):
        h = self.params["habitation"]
        self.assertGreater(h["gross_clear_volume_m3"], h["pressure_liner_clear_volume_m3"])
        self.assertGreater(h["pressure_liner_clear_volume_m3"], h["service_allocated_reference_volume_m3"])
        self.assertGreater(h["service_allocated_reference_volume_m3"], 0)
        self.assertIn("NOT_HUMAN_RATED", h["volume_revision_state"])

    def test_scene_geometry_is_manifold_and_complete(self):
        self.assertEqual(len(self.scene.geometry), 1357)
        self.assertEqual(len(self.records), 1357)
        self.assertEqual(len({r["node_name"] for r in self.records}), 1357)
        for name, geometry in self.scene.geometry.items():
            self.assertTrue(geometry.is_watertight, name)
            self.assertTrue(geometry.is_winding_consistent, name)

    def test_panel_window_walkway_and_arm_counts(self):
        self.assertEqual(self.counts["solar_hull_panel"], 162)
        self.assertEqual(self.counts["solar_hull_panel"] + self.counts["pressure_window"] // 4, 192)
        self.assertEqual(self.counts["pressure_window"], 120)
        self.assertEqual(self.counts["window_frame"], 120)
        self.assertEqual(self.counts["habitat_walkway"], 25)
        self.assertEqual(self.counts["egress_path"], 25)
        self.assertEqual(self.counts["habitat_bulkhead"], 24)
        self.assertEqual(self.counts["cable_tray"], 32)
        arm_count = sum(v for k, v in self.counts.items() if k.startswith("mark_iii"))
        self.assertEqual(arm_count, 23)

    def test_attachment_cable_and_access_reservations_exist(self):
        physical = [r for r in self.records if r["physical"]]
        self.assertTrue(all(r["attachment_parent"] for r in physical))
        self.assertGreaterEqual(self.counts["service_clearance"], 250)
        self.assertGreaterEqual(self.counts["removal_path"], 200)
        self.assertGreaterEqual(self.counts["power_harness"] + self.counts["data_harness"] + self.counts["habitat_harness"] + self.counts["arm_harness"], 50)

    def test_print_references_are_watertight_and_display_sized(self):
        refs = build_print_references(self.params, self.scene, self.records)
        self.assertEqual(len(refs), 4)
        for name, mesh in refs.items():
            self.assertTrue(mesh.is_watertight, name)
            self.assertTrue(mesh.is_winding_consistent, name)
            self.assertLessEqual(max(mesh.extents), 280.0 + 1e-6, name)

    def test_unverified_field_values_are_quarantined(self):
        q = self.params["legacy_simulation_quarantine"]
        self.assertIn("QUARANTINED", q["state"])
        self.assertNotIn("field_current_a", self.params.get("derived_geometry", {}))


if __name__ == "__main__":
    unittest.main()
