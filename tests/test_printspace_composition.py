"""Synthetic geometry composites — no material evidence or machine access."""
import copy
import json

import pytest
from cgx.manufacturing.composition import compile_geometry_composition
from cgx.manufacturing import load_volumetric_kernel


def tetra():
    return {'shape_id':'tetra', 'units':'mm', 'rights_ref':'SYNTHETIC-ONLY', 'source_ref':'SYNTHETIC-GEOMETRY-NON-AUTHORITATIVE',
        'vertices_mm': [[0,0,0],[2,0,0],[0,2,0],[0,0,2]],
        'faces': [[0,2,1],[0,1,3],[0,3,2],[1,2,3]]}


def example():
    return {'schema':'CGX-PRINTSPACE-GEOMETRY-COMPOSITION/0.1',
        'composite_id':'test-composite',
        'manufacturing_ir_ref':'cgx://manufacturing/build/test-synthetic',
        'load_mode':'H0_REVIEW_ONLY',
        'source_shapes':[tetra()],
        'instances':[
            {'instance_id':'shell', 'shape_id':'tetra', 'kernel_id':'VGK-018','material_slot':'structural','translate_mm':[0,0,0]},
            {'instance_id':'insert', 'shape_id':'tetra', 'kernel_id':'VGK-001','material_slot':'conductive','translate_mm':[2,0,0]},
        ],
        'interfaces':[{'from':'shell','to':'insert','kind':'CONTACT_CANDIDATE','evidence_state':'UNTESTED'}],
    }


def codes(p):
    return compile_geometry_composition(p)['hold_codes']


def test_real_volumetric_kernel_reused():
    k=load_volumetric_kernel()
    assert k['schema']=='CGX-TYPE1-VOLUMETRIC-KERNEL/0.1'
    assert len(k['records'])==40
    assert {"VGK-001","VGK-018"} <= {r['kernel_id'] for r in k['records']}


def test_composed_object_has_stable_h0_and_no_physical_authority():
    a=compile_geometry_composition(example())
    assert a['state']=='REVIEW_ONLY'
    assert len(a['graph']['instances'])==2
    assert a['graph']['interfaces'][0]['bounds_relation']=='AABB_TOUCH_CANDIDATE_NOT_PROVEN'
    assert a['load_h0']['alias']=='LOAD.cgx'
    assert a['load_h0']['hydration']=='H0_METADATA_ONLY'
    assert a['load_h0']['source_bytes_hydrated']==0
    assert a['load_h0']['native_admitted'] is False
    for p in ('machine_authorised','native_load_admitted','mint_authorised','rights_verified','physical_evidence_verified','release_authorised'):
        assert a[p] is False
    assert a['graph']['boolean_union_computed'] is False


def test_reorder_instance_and_interface_does_not_change_hash():
    a=example();b=copy.deepcopy(a);b['instances'].reverse()
    assert compile_geometry_composition(a)['geometry_composite_hash']==compile_geometry_composition(b)['geometry_composite_hash']


def test_identical_shape_references_are_deduplicated_and_new_placement_changes_hash():
    a=example(); b=copy.deepcopy(a); b['instances'][1]['translate_mm']=[2,1,0]
    x=compile_geometry_composition(a)
    y=compile_geometry_composition(b)
    assert len(x['graph']['shape_catalogue'])==1
    assert x['geometry_composite_hash']!=y['geometry_composite_hash']


def test_t173_is_proposed_not_admitted():
    p=example();p['source_shapes'][0]['t173_position']=1
    x=compile_geometry_composition(p)
    assert x['state']=='HOLD' and 'T173_CANDIDATE_UNADMITTED' in x['hold_codes']
    assert x['graph']['t173_candidates'][0]['t173_position']==1


def test_t174_never_mintable():
    p=example();p['source_shapes'][0]['t173_position']=174
    assert 'T174_RESERVED_OR_INVALID' in codes(p)


def test_missing_kernel_is_hold():
    p=example();p['instances'][0]['kernel_id']='VGK-999'
    assert 'UNRESOLVED_SHAPE_OR_KERNEL' in codes(p)


def test_missing_shape_is_hold():
    p=example();p['instances'][0]['shape_id']='missing'
    assert 'UNRESOLVED_SHAPE_OR_KERNEL' in codes(p)


def test_wrong_mesh_orientation_holds():
    p=example();p['source_shapes'][0]['faces'][0].reverse()
    assert 'EXACT_CONVEX_GEOMETRY_INVALID' in codes(p)


def test_non_integer_transform_holds():
    p=example();p['instances'][0]['translate_mm']=[0,0.1,0]
    assert 'TRANSFORM_OR_MATERIAL_INVALID' in codes(p)


def test_directional_interface_not_reversible():
    p=example();p['interfaces']=[{'from':'insert','to':'shell','kind':'CONTACT_CANDIDATE','evidence_state':'UNTESTED'}]
    x=compile_geometry_composition(p)
    assert x['state']=='REVIEW_ONLY'
    assert x['geometry_composite_hash']!=compile_geometry_composition(example())['geometry_composite_hash']


def test_disjoint_contact_holds():
    p=example();p['instances'][1]['translate_mm']=[5,0,0]
    assert 'DECLARED_CONTACT_DISJOINT' in codes(p)


def test_disjoint_separation_review():
    p=example();p['instances'][1]['translate_mm']=[5,0,0]
    p['interfaces'][0]['kind']='SEPARATED'
    x=compile_geometry_composition(p)
    assert x['state']=='REVIEW_ONLY'
    assert x['graph']['interfaces'][0]['bounds_relation']=='AABB_DISJOINT'


def test_unproven_separation_holds():
    p=example();p['interfaces'][0]['kind']='SEPARATED'
    assert 'SEPARATION_NOT_DEMONSTRATED_BY_BOUNDS' in codes(p)


def test_false_physical_qualification_holds():
    p=example();p['interfaces'][0]['evidence_state']='QUALIFIED'
    assert 'FALSE_QUALIFICATION_ATTEMPT' in codes(p)


def test_duplicate_instance_holds():
    p=example();p['instances'][1]['instance_id']='shell'
    assert 'DUPLICATE_OR_INVALID_INSTANCE' in codes(p)


def test_malformed_input_holds():
    assert compile_geometry_composition([1,2])['state']=='HOLD'
    p=example();p['instances'][0]['translate_mm']=[0,float('nan'),0]
    assert 'NONCANONICAL_REQUEST' in codes(p)


def test_h1_unavailable_and_no_native_load():
    p=example();p['load_mode']='H1'
    assert 'LOAD_NATIVE_HYDRATION_DENIED' in codes(p)


def test_budget_bound():
    p=example();p['instances']*=30
    assert 'COMPOSITION_BUDGET_OR_SHAPE' in codes(p)


def test_unconnected_composition_holds():
    p=example();p['interfaces']=[]
    assert 'UNCONNECTED_COMPOSITION' in codes(p)


def test_untrusted_rights_presence_is_not_rights_verification():
    p=example();p['source_shapes'][0]['rights_ref']='CLAIMED-LICENCE'
    out=compile_geometry_composition(p)
    assert out['state']=='REVIEW_ONLY' and out['rights_verified'] is False


def test_disconnected_instance_graph_holds():
    p=example()
    p['instances'].append({'instance_id':'orphan','shape_id':'tetra','kernel_id':'VGK-018','material_slot':'dielectric','translate_mm':[10,0,0]})
    assert 'DISCONNECTED_COMPONENT_GRAPH' in codes(p)


def test_missing_source_provenance_fails():
    p=example();p['source_shapes'][0].pop('source_ref')
    assert 'GEOMETRY_UNITS_OR_RIGHTS_UNBOUND' in codes(p)


def test_canonical_build_uri_is_bounded():
    p=example();p['manufacturing_ir_ref']='cgx://manufacturing/build/correct/../../fake'
    assert 'CANONICAL_MANUFACTURING_REF_REQUIRED' in codes(p)


def test_three_layer_ground_up_digital_composite_fixture():
    from pathlib import Path
    source=Path(__file__).resolve().parents[1]/'cgx/manufacturing/printspace_composite_pilot_v0_1.json'
    p=json.loads(source.read_text(encoding='utf-8'))
    out=compile_geometry_composition(p)
    assert out['state']=='REVIEW_ONLY', out.get('hold_codes')
    assert len(out['graph']['shape_catalogue'])==2
    assert len(out['graph']['instances'])==3
    assert len(out['graph']['interfaces'])==2
    assert {r['bounds_relation'] for r in out['graph']['interfaces']}=={'AABB_TOUCH_CANDIDATE_NOT_PROVEN'}
    assert out['graph']['boolean_union_computed'] is False
    assert out['load_h0']['network_fetch'] is False
    assert out['load_h0']['source_bytes_hydrated']==0