"""Type-1-compatible review namespace sanity checks (not drawing acceptance)."""
from pathlib import Path
import json
import unittest
from xml.etree import ElementTree as ET
from cgx.manufacturing.modular_facility_projection import render_svg

SRC=Path(__file__).resolve().parents[1]/"cgx"/"manufacturing"/"fixtures"/"five_unit_relief_synthetic_v0_1.json"
def fixture(): return json.loads(SRC.read_text(encoding="utf-8"))
class ProjectionTests(unittest.TestCase):
    def test_synthetic_view_is_parseable_and_source_addressed(self):
        svg=render_svg(fixture())
        root=ET.fromstring(svg)
        namespace="{http://www.w3.org/2000/svg}"
        self.assertTrue(root.tag.endswith("svg"))
        self.assertEqual(len([e for e in root.iter() if e.get("data-cgx-unit")]),5)
        self.assertEqual(len([e for e in root.iter() if e.get("data-cgx-role")=="asset"]),10)
        self.assertEqual(len([e for e in root.iter() if e.get("data-cgx-role")=="reserved"]),15)
        self.assertIn("NOT FOR CONSTRUCTION",svg)
        self.assertIn("L70-INTERFACES",svg)
        self.assertEqual(len([e for e in root.iter() if e.get("data-cgx-link") is not None]),4)
    def test_preview_never_mislabels_synthetic_as_native_authority(self):
        svg=render_svg(fixture())
        self.assertIn("SYNTHETIC_TEST_ONLY",svg)
        self.assertIn("NATIVE CAD",svg)
    def test_source_labels_escaped(self):
        obj=fixture()
        obj["units"][0]["id"]='name\" onload=\"evil()'
        svg=render_svg(obj)
        ET.fromstring(svg)
        self.assertNotIn('id="name" onload=',svg)
    def test_missing_geometry_does_not_fake_plan(self):
        p=fixture();p["units"][0]["internal_envelope_m"]=None
        with self.assertRaises(ValueError):render_svg(p)
    def test_invalid_scale_rejected(self):
        with self.assertRaises(ValueError):render_svg(fixture(),scale=100000)
if __name__=="__main__":unittest.main()
