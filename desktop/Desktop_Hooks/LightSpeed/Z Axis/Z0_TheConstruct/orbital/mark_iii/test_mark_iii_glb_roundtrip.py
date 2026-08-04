from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from mark_iii_glb_roundtrip_audit import audit
from mark_iii_parametric import export_reference
ROOT=Path(__file__).resolve().parent;P=json.loads((ROOT/'mark_iii_parameters.json').read_text())
class MarkIIIGLBRoundtripTests(unittest.TestCase):
 def test_exported_glb_matches_source(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);export_reference(ROOT/'mark_iii_parameters.json',out);r=audit(P,out/'mark_iii_assembly.glb');self.assertEqual(r['status'],'PASS_GLB_ROUNDTRIP_REFERENCE');self.assertEqual(r['matched_nodes'],339);self.assertFalse(r['missing_nodes']);self.assertFalse(r['unexpected_nodes']);self.assertFalse(r['failures'])
if __name__=='__main__':unittest.main()
