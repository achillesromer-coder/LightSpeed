from __future__ import annotations
import json,tempfile,unittest
from collections import Counter
from pathlib import Path
from mark_iii_geometry_fingerprint import semantic_geometry_fingerprint
from mark_iii_manifest_fingerprint import canonical_manifest_sha256
from mark_iii_parametric import build_print_references,build_reference,export_reference

ROOT=Path(__file__).resolve().parent
P=json.loads((ROOT/'mark_iii_parameters.json').read_text())

class MarkIIIParametricTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.scene,cls.records=build_reference(P);cls.rm={r['node_name']:r for r in cls.records};cls.fc=Counter(r['family'] for r in cls.records)
 def test_source_envelope_and_topology(self):
  self.assertEqual(P['source_parameters']['module_length_m']['value'],.75);self.assertEqual(P['source_parameters']['outer_radius_m']['value'],.16);self.assertEqual(P['source_parameters']['shell_sector_count']['value'],6)
 def test_component_counts(self):
  self.assertEqual(self.fc['shell_panel'],18);self.assertEqual(self.fc['solar_hull_skin'],6);self.assertEqual(self.fc['coupler_latch'],8);self.assertEqual(self.fc['resonator'],4);self.assertEqual(self.fc['sensor'],8);self.assertEqual(self.fc['damping'],4)
 def test_named_geometry_is_complete_and_manifold(self):
  self.assertEqual(len(self.scene.geometry),339);self.assertEqual(len(self.records),339);self.assertTrue(all(m.is_watertight and m.is_winding_consistent for m in self.scene.geometry.values()))
 def test_attachment_and_cable_references_resolve(self):
  names=set(self.rm);roots={'PRIMARY_STRUCTURE','ILLUSTRATIVE_REFERENCE_ROOT'}
  self.assertFalse([r['node_name'] for r in self.records if r['physical'] and r['attachment_parent'] not in names|roots])
  self.assertFalse([r['node_name'] for r in self.records if r['physical'] and r['cable_required'] and r['cable_route'] not in names])
 def test_two_arms_are_decomposed(self):
  self.assertEqual(sum(r['node_name'].endswith('_BASE_INTERFACE') for r in self.records),2);self.assertEqual(self.fc['arm_joint'],6);self.assertGreaterEqual(sum(r['subsystem']=='arm_system' for r in self.records),30)
 def test_array_guides_are_exact(self):
  for count in P['derived_configuration']['array_configurations']:
   self.assertEqual(sum(r['family']=='array_guide' and r['array_configuration']==str(count) for r in self.records),count)
 def test_print_references_are_watertight_and_fit(self):
  refs=build_print_references(P,self.scene,self.records);self.assertEqual(len(refs),5);self.assertTrue(all(m.is_watertight and m.is_winding_consistent and max(m.extents)<=280.000001 for m in refs.values()))
 def test_quarantined_claim_values_not_active(self):
  joined=json.dumps(P).lower();self.assertIn('quarantined',joined);self.assertNotIn('1000000',joined);self.assertGreaterEqual(len(P['claim_gates']),6)
 def test_semantic_fingerprint_is_stable(self):
  self.assertEqual(semantic_geometry_fingerprint(self.scene),'8ff2f295d0bebdd9cfb45c1942bda6dfe8dfd6493d7d9861fb97bf91458c2303')
 def test_manifest_canonical_meaning_is_stable(self):
  manifest={'schema_version':'mark-iii-component-manifest-v0.2','node_count':len(self.records),'components':self.records}
  self.assertEqual(canonical_manifest_sha256(manifest),'9f95b1c5a6e552a626f50a9e2448f45a2cfb8642e65f92b904f0211fee64d813')
 def test_generation_is_deterministic_for_portable_outputs(self):
  with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
   export_reference(ROOT/'mark_iii_parameters.json',Path(a));export_reference(ROOT/'mark_iii_parameters.json',Path(b))
   for n in ['mark_iii_component_manifest.json','mark_iii_full_module_1to5.stl','mark_iii_representative_panel_1to3.stl','mark_iii_coupler_1to2.stl','mark_iii_solenoid_cartridge_1to1.stl','mark_iii_arm_assembly_1to2.stl']:
    self.assertEqual((Path(a)/n).read_bytes(),(Path(b)/n).read_bytes(),n)
if __name__=='__main__':unittest.main()
