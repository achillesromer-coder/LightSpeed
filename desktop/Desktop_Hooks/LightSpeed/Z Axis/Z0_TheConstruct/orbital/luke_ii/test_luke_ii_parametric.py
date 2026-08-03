from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from luke_ii_parametric import build_print_shell, build_scene


class LukeIIParametricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = json.loads((HERE / "luke_ii_parameters.json").read_text(encoding="utf-8"))

    def test_source_geometry(self):
        p = self.params
        self.assertEqual(p["source_parameters"]["major_radius_m"]["value"], 12.0)
        self.assertEqual(p["source_parameters"]["body_minor_radius_m"]["value"], 2.0)
        self.assertEqual(p["source_parameters"]["field_sector_count"]["value"], 16)
        self.assertAlmostEqual(p["derived_geometry"]["central_aperture_diameter_m"], 20.0)

    def test_habitation_volume_exceeds_explicit_analogues(self):
        h = self.params["habitation"]
        self.assertGreaterEqual(h["modelled_habitable_volume_m3"], h["iss_scaled_baseline_m3"])
        self.assertGreaterEqual(h["modelled_habitable_volume_m3"], h["deep_space_linear_3_crew_comparator_m3"])

    def test_scene_geometry_is_manifold(self):
        scene = build_scene(self.params)
        self.assertEqual(len(scene.geometry), 96)
        for name, geometry in scene.geometry.items():
            self.assertTrue(geometry.is_watertight, name)
            self.assertTrue(geometry.is_winding_consistent, name)

    def test_print_shell_is_watertight(self):
        shell = build_print_shell(self.params)
        self.assertTrue(shell.is_watertight)
        self.assertTrue(shell.is_winding_consistent)
        self.assertAlmostEqual(shell.extents[0], 280.0, places=2)
        self.assertAlmostEqual(shell.extents[1], 280.0, places=2)
        self.assertAlmostEqual(shell.extents[2], 40.0, places=2)

    def test_unverified_field_values_are_quarantined(self):
        q = self.params["legacy_simulation_quarantine"]
        self.assertIn("QUARANTINED", q["state"])
        self.assertNotIn("field_current_a", self.params.get("derived_geometry", {}))


if __name__ == "__main__":
    unittest.main()
