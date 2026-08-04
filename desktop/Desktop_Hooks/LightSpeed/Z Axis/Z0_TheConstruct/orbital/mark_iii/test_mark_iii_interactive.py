from __future__ import annotations
import tempfile,unittest
from pathlib import Path
from mark_iii_interactive import build_html
from mark_iii_parametric import export_reference
from mark_iii_dimensional_audit import build_audit,write_audit
from mark_iii_serviceability_audit import build_audit as build_service,write as write_service
from mark_iii_glb_roundtrip_audit import audit
import json
ROOT=Path(__file__).resolve().parent;P=json.loads((ROOT/'mark_iii_parameters.json').read_text())
class MarkIIIInteractiveTests(unittest.TestCase):
 def test_interactive_surface_contains_required_controls(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);export_reference(ROOT/'mark_iii_parameters.json',out);rows,s=build_audit(P);write_audit(rows,s,out);sv=build_service(P);write_service(sv,out);rt=audit(P,out/'mark_iii_assembly.glb');(out/'mark_iii_glb_roundtrip_audit.json').write_text(json.dumps(rt))
   html=build_html(out/'mark_iii_assembly.glb',out/'mark_iii_component_manifest.json',ROOT/'mark_iii_parameters.json',out/'mark_iii_verification.json',out/'mark_iii_serviceability_audit.json',out/'mark_iii_glb_roundtrip_audit.json')
   self.assertGreater(len(html),900000);self.assertIn('Array review',html);self.assertIn('Explode',html);self.assertIn('Cutaway axis',html);self.assertIn('Known unknowns',html);self.assertIn('339 named nodes',html)
if __name__=='__main__':unittest.main()
