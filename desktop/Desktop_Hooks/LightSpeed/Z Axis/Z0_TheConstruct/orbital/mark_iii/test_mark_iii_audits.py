from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from mark_iii_dimensional_audit import build_audit,write_audit
from mark_iii_serviceability_audit import build_audit as build_service,write as write_service
ROOT=Path(__file__).resolve().parent;P=json.loads((ROOT/'mark_iii_parameters.json').read_text())
class MarkIIIAuditTests(unittest.TestCase):
 def test_dimensional_register_covers_all_nodes(self):
  rows,s=build_audit(P);self.assertEqual(len(rows),339);self.assertEqual(s['physical_node_count'],192);self.assertTrue(s['all_nodes_watertight']);self.assertEqual(s['semantic_geometry_sha256'],'8ff2f295d0bebdd9cfb45c1942bda6dfe8dfd6493d7d9861fb97bf91458c2303')
 def test_serviceability_gate_passes(self):
  s=build_service(P);self.assertEqual(s['status'],'PASS_SERVICEABILITY_REFERENCE_AUDIT');self.assertFalse(s['failures']);self.assertEqual(s['canonical_module_envelope_m']['extents'],[.75,.32,.32])
 def test_serviceability_counts_and_known_unknowns(self):
  s=build_service(P);self.assertEqual(s['counts']['physical_nodes'],192);self.assertEqual(s['counts']['service_clearances'],50);self.assertEqual(s['counts']['removal_paths'],38);self.assertGreaterEqual(len(s['known_unknowns']),10)
 def test_audit_outputs_are_deterministic(self):
  with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
   rows,s=build_audit(P);ca,ja=write_audit(rows,s,Path(a));cb,jb=write_audit(rows,s,Path(b));self.assertEqual(ca.read_bytes(),cb.read_bytes());self.assertEqual(ja.read_bytes(),jb.read_bytes())
   sa=build_service(P);j1,c1=write_service(sa,Path(a));j2,c2=write_service(sa,Path(b));self.assertEqual(j1.read_bytes(),j2.read_bytes());self.assertEqual(c1.read_bytes(),c2.read_bytes())
if __name__=='__main__':unittest.main()
