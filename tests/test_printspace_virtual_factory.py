"""PrintSpace offline product/printer simulator: deterministic, non-actuating QA."""
from __future__ import annotations
import copy
import math
import pytest
from cgx.manufacturing.virtual_factory import (
    MODEL_BEDS_MM, MAX_SCENARIOS, canonical_digest, compile_scene,
    load_catalogue, reverse_scene, sweep_scenarios, validate_catalogue,
)

@pytest.fixture(scope='module')
def catalog():
    return load_catalogue()

def test_source_catalogue_accepts_known_printer_families(catalog):
    assert len(catalog['printer_families']) == 7
    assert {x['id'] for x in catalog['printer_families']} == set(MODEL_BEDS_MM)
    assert [x['id'] for x in catalog['products']] == ['diode','board','phone']
    assert set(catalog['source_refs']) >= {'pc01','raphael','equations','manufacturing_ir','materials','simulation','load'}
    assert all(v is False for v in catalog['attestations'].values())

def test_primitive_to_board_to_phone_nested_reference_lineage(catalog):
    refs={(p['id'],r['parent']) for p in catalog['products'] for r in p['parts'] if r['parent']}
    assert ('board','diode') in refs
    assert ('phone','board') in refs
    assert all(r['parent'] is None or r['parent'] != p['id'] for p in catalog['products'] for r in p['parts'])
    for p in catalog['products']:
        assert p['readiness'] in ('DIGITAL_ONLY','ASSEMBLY_CONCEPT_ONLY')

def test_stage_trajectory_is_visibility_projection_not_physical_motion(catalog):
    for product in catalog['products']:
        stages=len(product['steps'])
        previous=set()
        for i in range(stages):
            a=compile_scene(catalog,product['id'],'hybrid','terrestrial',1,i)
            assert a['state']=='EMULATED_DESIGN_ONLY'
            seen={r['id'] for r in a['selected_product']['parts'] if r['visible']}
            assert previous <= seen
            previous=seen
            assert all(s['real_operation_executed'] is False for s in a['sequence'])
            assert all(s['source_or_lot_receipt'] is None for s in a['sequence'])
            assert a['machine']['physical_motion_generated'] is False
            assert a['native_dbr_written'] is False
            assert a['physical_machine_authorised'] is False

def test_756_case_full_factorial_determinism_and_cross_scale(catalog):
    a=sweep_scenarios(catalog)
    b=sweep_scenarios(catalog)
    assert a==b and len(a['result_sha256'])==64
    assert a['case_count']==756 and len(a['cases'])==756
    assert len({(r['product_id'],r['family_id'],r['environment_id'],r['scale'],r['printer_scale']) for r in a['cases']})==756
    assert any(r['illustrative_bed_fit'] is False for r in a['cases'])
    assert any(r['illustrative_bed_fit'] is True for r in a['cases'])
    assert a['illustrative_fits']==sum(r['illustrative_bed_fit'] for r in a['cases'])
    assert all(r['release_authorised'] is False for r in a['cases'])
    assert not a['real_machine_and_environment_verified']
    assert not a['physical_machine_authorised']

def test_product_and_printer_scaling_are_independent(catalog):
    base=compile_scene(catalog,'phone','mobile','in_situ',1,5)
    large_product=compile_scene(catalog,'phone','mobile','in_situ',4,5)
    large_printer=compile_scene(catalog,'phone','mobile','in_situ',4,5,printer_scale=4)
    assert base['machine']['illustrative_bed_fit']
    assert large_product['machine']['illustrative_bed_fit'] is False
    assert large_printer['machine']['illustrative_bed_fit'] is True
    assert large_printer['machine']['synthetic_bed_mm']==[760,800,560]
    assert large_product['machine']['synthetic_bed_mm']==base['machine']['synthetic_bed_mm']
    assert base['scene_sha256'] != large_product['scene_sha256'] != large_printer['scene_sha256']

def test_offworld_environment_is_assumed_not_space_certified(catalog):
    env=compile_scene(catalog,'diode','mobile','in_situ',1,0)['environment']
    assert env['assumed_pressure_pa']==0
    assert env['assumed_gravity_m_s2']==1.62
    assert env['actual_process_condition'] is None
    assert env['emc_or_low_g_qualified'] is False

def test_reverse_replay_rejects_tampered_output_and_changed_source(catalog):
    scene=compile_scene(catalog,'board','hybrid','controlled',1,6)
    assert reverse_scene(scene,catalog)['state']=='PASS_DIGITAL_ONLY'
    modified=copy.deepcopy(scene)
    modified['physical_machine_authorised']=True
    assert reverse_scene(modified,catalog)['state']=='HOLD'
    modified=copy.deepcopy(scene)
    modified['selected_product']['parts'][0]['size_mm'][0]=999
    assert reverse_scene(modified,catalog)['state']=='HOLD'
    old_catalog=copy.deepcopy(catalog)
    old_catalog['products'][1]['parts'][0]['size'][0]+=1
    assert reverse_scene(scene,old_catalog)['state']=='HOLD'

def test_wrong_schema_and_unsafe_provenance_rejected(catalog):
    for update in ({'status':'PHYSICALLY_QUALIFIED'}, {'schema':'INVALID'}):
        value=copy.deepcopy(catalog);value.update(update)
        with pytest.raises(ValueError):validate_catalogue(value)
    value=copy.deepcopy(catalog);value['attestations']['physical_machine_authorised']=True
    with pytest.raises(ValueError,match='AUTHORITY_ESCALATION'):validate_catalogue(value)

def test_external_critical_modules_unqualified(catalog):
    phone=next(x for x in catalog['products'] if x['id']=='phone')
    lookup={r['id']:r for r in phone['parts']}
    for name in ('p-battery','p-soc','p-rf','p-display','p-camera'):
        assert lookup[name]['origin']=='external'
        assert lookup[name]['status']=='SOURCE_REQUIRED'
    assert catalog['attestations']['printed_functionality_verified'] if 'printed_functionality_verified' in catalog['attestations'] else True

def test_invalid_scale_and_stage_fail_closed(catalog):
    for x in [0,6,True,float('nan'),float('inf'),None]:
        assert compile_scene(catalog,'diode','hybrid','terrestrial',scale=x)['state']=='HOLD'
    for x in [-1,5,True,float('nan'),None]:
        assert compile_scene(catalog,'diode','hybrid','terrestrial',printer_scale=x)['state']=='HOLD'
    assert compile_scene(catalog,'diode','hybrid','terrestrial',stage=-1)['state']=='HOLD'
    assert compile_scene(catalog,'diode','hybrid','terrestrial',stage=300)['state']=='HOLD'
    assert compile_scene(catalog,'unknown','hybrid','terrestrial')['state']=='HOLD'

def test_user_added_new_product_is_supported_without_new_code(catalog):
    v=copy.deepcopy(catalog)
    new=copy.deepcopy(v['products'][0]);new['id']='custom_test';new['title']='Custom printable fixture (concept)'
    for part in new['parts']:part['parent']=None
    v['products'].append(new)
    validate_catalogue(v)
    scene=compile_scene(v,'custom_test','structural','terrestrial',1,1)
    assert scene['state']=='EMULATED_DESIGN_ONLY'
    assert scene['selected_product']['title']==new['title']
    assert not scene['commercial_release_authorised']

def test_cycle_and_missing_reference_rejected(catalog):
    value=copy.deepcopy(catalog)
    value['products'][0]['parts'][0]['parent']='phone'
    with pytest.raises(ValueError,match='PRODUCT_REFERENCE_CYCLE'):validate_catalogue(value)
    value=copy.deepcopy(catalog)
    value['products'][0]['parts'][0]['parent']='missing'
    with pytest.raises(ValueError):validate_catalogue(value)

def test_rejects_embedded_geometry_outside_nominal_illustrative_bounds(catalog):
    value=copy.deepcopy(catalog)
    value['products'][0]['parts'][0]['size'][0]=500
    with pytest.raises(ValueError,match='INVALID_PART_GEOMETRY'):validate_catalogue(value)

def test_sweep_bounded_scaling_and_case_limit(catalog):
    with pytest.raises(ValueError,match='UNBOUNDED_SWEEP_SCALES'):
        sweep_scenarios(catalog,scales=(float('nan'),))
    with pytest.raises(ValueError,match='UNBOUNDED_PRINTER_SCALES'):
        sweep_scenarios(catalog,printer_scales=(True,))
    with pytest.raises(ValueError,match='SWEEP_LIMIT'):
        sweep_scenarios(catalog,scales=(.3,.5,.7,1,1.5,2),printer_scales=(.5,1,2,4))