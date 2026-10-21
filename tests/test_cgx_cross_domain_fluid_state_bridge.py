"""Source-transcription and domain-law nonpromotion tests; no external hardware."""
import copy
import importlib.util
import json
from math import isclose, pi
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
SOURCE = HERE / 'cgx/review/water_reference_fluid_kernel_fixture.py'
fixture = HERE / 'cgx/review/water_reference_property_fixture_20261021.json'
spec = importlib.util.spec_from_file_location('cgx_fluid_source_bridge', SOURCE)
m = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = m
spec.loader.exec_module(m)

TUBE = dict(steady=True,newtonian=True,incompressible=True,single_phase=True,circular=True,fully_developed=True,
            radius_m=.001,length_m=.1,flow_m3_s=1e-7)
DARCY = dict(newtonian=True,single_phase=True,darcy_regime_assumed=True,permeability_basis='synthetic_fixture_only',
             permeability_m2=1e-12,area_m2=1e-3,length_m=.02,pressure_drop_pa=100)
STOKES = dict(newtonian=True,incompressible=True,single_phase=True,spherical=True,isolated_sphere=True,
              creeping_flow_assumed=True,diameter_m=30e-6,relative_velocity_m_s=1e-4)

class CrossDomain(unittest.TestCase):
    def setUp(self):
        self.state=m.read_reference_state(fixture)
    def changed_fixture(self,change):
        doc=json.loads(fixture.read_text())
        change(doc)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'water.json'; p.write_text(json.dumps(doc))
            with self.assertRaises(m.DomainHold):m.read_reference_state(p)
    def test_existing_cgx_operator_registry_is_reused_when_present(self):
        contract = HERE / 'cgx/domain_templates/cross_domain_bridge_registry.json'
        lens = HERE / 'cgx/portable_node/cross_domain_method_lens.py'
        if not contract.is_file() or not lens.is_file():
            self.skipTest('existing CGX owner module resolved by GitHub CI, not duplicated in portable package')
        import importlib.util
        existing_spec = importlib.util.spec_from_file_location('existing_cgx_method_lens', lens)
        existing = importlib.util.module_from_spec(existing_spec)
        existing_spec.loader.exec_module(existing)
        registry = json.loads(contract.read_text(encoding='utf-8'))
        check = existing.validate_crosswalk(registry)
        self.assertEqual(check['status'], 'DIMENSIONAL_CONSISTENCY_TESTED_ONLY')
        p = existing.preview_method_reuse(registry, domain='eco',
                  law_id='NEWTONIAN_VISCOUS_SHEAR', quantity_name='mu_dynamic_viscosity',
                  si_dimension=[1,-1,-1,0,0,0,0])
        self.assertEqual(p['status'],'PROPOSED_METHOD_REUSE_ONLY')
        self.assertFalse(p['physical_model_validated'])
        self.assertFalse(p['solver_executed'])
        self.assertFalse(p['canonical_promotion'])

    def test_state_from_published_nist_pair(self):
        self.assertTrue(isclose(self.state.mu_pa_s,.000889996774,rel_tol=1e-14))
        self.assertTrue(isclose(self.state.rho_kg_m3,997.047013,rel_tol=1e-14))
        self.assertEqual((self.state.temperature_kelvin,self.state.pressure_pa),(298.15,100000.0))
    def test_unit_conversion_integrity(self):
        self.changed_fixture(lambda x:x['conversion'].update(viscosity_pa_s='0.000889'))
    def test_cannot_forge_source_state(self):
        self.changed_fixture(lambda x:x['state_point'].update(temperature_kelvin='300'))
    def test_cannot_forge_source_locator(self):
        self.changed_fixture(lambda x:x['source'].update(url='https://example.invalid'))
    def test_cannot_claim_instrument_measurement(self):
        self.changed_fixture(lambda x:x.update(instrument_measured_here=True))
    def test_cannot_claim_dbr(self):
        self.changed_fixture(lambda x:x.update(owner_dbr_verified=True))
    def test_cannot_claim_original_pdf_hash(self):
        self.changed_fixture(lambda x:x['source'].update(original_document_sha256='0'*64))
    def test_cannot_claim_rights(self):
        self.changed_fixture(lambda x:x['source'].update(source_rights_for_redistribution_verified=True))
    def test_tube_equation(self):
        r=m.screen('laminar_tube',TUBE,self.state)
        self.assertTrue(isclose(r['output']['pressure_drop_pa'],8*self.state.mu_pa_s*.1*1e-7/(pi*.001**4)))
        self.assertEqual(r['existing_kernel_links'],['T1K-012','VGK-019'])
        self.assertLess(r['details']['reynolds'],2000)
    def test_tube_missing_regime(self):
        p={**TUBE,'fully_developed':False}
        with self.assertRaisesRegex(m.DomainHold,'REGIME'):m.screen('laminar_tube',p)
    def test_tube_excess_flow_rejects(self):
        p={**TUBE,'flow_m3_s':1e-3}
        with self.assertRaisesRegex(m.DomainHold,'POISEUILLE'):m.screen('laminar_tube',p)
    def test_tube_short_entry_rejects(self):
        p={**TUBE,'length_m':.0001}
        with self.assertRaisesRegex(m.DomainHold,'POISEUILLE'):m.screen('laminar_tube',p)
    def test_tube_radius_nonpositive(self):
        with self.assertRaises(m.DomainHold):m.screen('laminar_tube',{**TUBE,'radius_m':0})
    def test_darcy_equation(self):
        r=m.screen('porous_darcy',DARCY)
        self.assertTrue(isclose(r['output']['flow_m3_s'],1e-12*1e-3*100/(self.state.mu_pa_s*.02)))
        self.assertFalse(r['details']['darcy_regime_independently_verified'])
    def test_darcy_cannot_invent_source_permeability(self):
        with self.assertRaisesRegex(m.DomainHold,'PERMEABILITY'):m.screen('porous_darcy',{**DARCY,'permeability_basis':'source_measured'})
    def test_darcy_needs_regime(self):
        with self.assertRaisesRegex(m.DomainHold,'REGIME'):m.screen('porous_darcy',{**DARCY,'darcy_regime_assumed':False})
    def test_stokes_equation(self):
        r=m.screen('stokes_particle_drag',STOKES)
        self.assertTrue(isclose(r['output']['drag_force_n'],3*pi*self.state.mu_pa_s*30e-6*1e-4))
        self.assertLess(r['details']['reynolds'],.1)
    def test_stokes_rejects_high_re(self):
        with self.assertRaisesRegex(m.DomainHold,'STOKES_RE'):m.screen('stokes_particle_drag',{**STOKES,'relative_velocity_m_s':.1})
    def test_stokes_rejects_nonsphere(self):
        with self.assertRaisesRegex(m.DomainHold,'REGIME'):m.screen('stokes_particle_drag',{**STOKES,'spherical':False})
    def test_no_general_cfd_pretence(self):
        with self.assertRaisesRegex(m.DomainHold,'NO_GENERAL_CFD'):m.screen('general_cfd_reference',{})
    def test_no_fake_typed_fluid_state(self):
        fake=m.FluidState(self.state.mu_pa_s*2,self.state.rho_kg_m3,self.state.temperature_kelvin,self.state.pressure_pa,self.state.source_id)
        with self.assertRaisesRegex(m.DomainHold,'STATE_NOT_PINNED'):m.screen('laminar_tube',TUBE,fake)
    def test_boolean_not_accepted_as_numeric(self):
        with self.assertRaises(m.DomainHold):m.screen('porous_darcy',{**DARCY,'permeability_m2':True})
    def test_no_canonical_releases(self):
        for kind,p in [('laminar_tube',TUBE),('porous_darcy',DARCY),('stokes_particle_drag',STOKES)]:
            result=m.screen(kind,p)
            self.assertFalse(result['physical_qualification'])
            self.assertFalse(result['native_dbr_admitted'])
            self.assertFalse(result['public_release_authorised'])
            self.assertEqual(result['source_reference_id'],m.SOURCE_ID)
    def test_non_interchangeable_kernels(self):
        results=[m.screen(k,p) for k,p in [('laminar_tube',TUBE),('porous_darcy',DARCY),('stokes_particle_drag',STOKES)]]
        self.assertEqual(len({x['output']['unit'] for x in results}),3)
        self.assertEqual(len({tuple(x['existing_kernel_links']) for x in results}),3)
        self.assertEqual(len({x['source_reference_id'] for x in results}),1)
    def test_invalid_nan_or_infinity(self):
        for value in (float('inf'),float('nan')):
            with self.assertRaises(m.DomainHold):m.screen('laminar_tube',{**TUBE,'flow_m3_s':value})

if __name__=='__main__':unittest.main()