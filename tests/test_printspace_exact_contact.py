"""Exact convex contact is geometric evidence only, never process qualification."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from cgx.manufacturing.exact_contact import exact_convex_contact, ContactHold
from cgx.manufacturing.composition import compile_geometry_composition

PILOT = Path(__file__).resolve().parents[1] / 'cgx/manufacturing/printspace_composite_pilot_v0_1.json'


def cube():
    return json.loads(PILOT.read_text())['source_shapes'][0]


def pair(a=(0,0,0), b=(4,0,0)):
    c=cube()
    return exact_convex_contact(c, list(a), c, list(b))


def pilot():
    return json.loads(PILOT.read_text())


def codes(record):
    return compile_geometry_composition(record)['hold_codes']


def test_shared_face_geometry_area_and_outward_direction():
    r=pair((0,0,0),(4,0,0))
    assert r['relation']=='FACE_CONTACT'
    assert r['intersection_affine_dimension']==2
    assert r['face_area_mm2_exact']=='8'
    assert r['face_area_squared_mm4']=='64'
    assert [1,0,0] in r['directed_face_normals_from_a_to_b']
    assert not r['material_interface_qualified']
    assert not r['boolean_mesh_emitted']


def test_partial_face_overlap_exact_area():
    r=pair((0,0,0),(4,1,0))
    assert r['relation']=='FACE_CONTACT'
    assert r['face_area_mm2_exact']=='6'  # overlap 3 mm wide by 2 mm high


def test_reverse_pair_flips_directed_contact_normal():
    r=pair((4,0,0),(0,0,0))
    assert r['relation']=='FACE_CONTACT'
    assert [-1,0,0] in r['directed_face_normals_from_a_to_b']
    assert r['face_area_mm2_exact']=='8'


def test_point_contact_is_not_bonded_face():
    r=pair((0,0,0),(4,4,2))
    assert r['relation']=='POINT_CONTACT'
    assert r['intersection_affine_dimension']==0
    assert r['contact_point_mm']==['4','4','2']
    assert 'face_area_mm2_exact' not in r


def test_edge_contact_is_zero_area():
    r=pair((0,0,0),(4,4,0))
    assert r['relation']=='EDGE_CONTACT'
    assert r['line_length_squared_mm2']=='4'
    assert 'face_area_mm2_exact' not in r


def test_volume_overlap_never_pretends_to_be_touch_only():
    r=pair((0,0,0),(2,0,0))
    assert r['relation']=='VOLUME_OVERLAP'
    assert r['intersection_affine_dimension']==3


def test_disjoint_geometry_explicit():
    r=pair((0,0,0),(5,0,0))
    assert r['relation']=='DISJOINT'
    assert r['intersection_affine_dimension'] is None


def test_same_shape_overlap_full_volume():
    assert pair((0,0,0),(0,0,0))['relation']=='VOLUME_OVERLAP'


def test_exact_convex_separation_despite_overlapping_bounds():
    tetra={
        'vertices_mm':[[0,0,0],[2,0,0],[0,2,0],[0,0,2]],
        'faces':[[0,2,1],[0,1,3],[0,3,2],[1,2,3]],
    }
    r=exact_convex_contact(tetra,[0,0,0],tetra,[1,1,1])
    assert r['relation']=='DISJOINT'


def test_pilot_composite_has_two_proven_exact_face_candidates():
    r=compile_geometry_composition(pilot())
    assert r['state']=='REVIEW_ONLY'
    assert len(r['graph']['interfaces'])==2
    assert all(e['exact_convex_contact']['relation']=='FACE_CONTACT' for e in r['graph']['interfaces'])
    assert all(e['exact_convex_contact']['face_area_mm2_exact']=='16' for e in r['graph']['interfaces'])
    assert all(e['directional_coupon_status']=='PENDING_BOTH_DIRECTIONS_INDEPENDENTLY' for e in r['graph']['interfaces'])
    assert not r['physical_evidence_verified']
    assert not r['machine_authorised']


def test_composite_contact_candidate_with_point_does_not_claim_adhesion():
    p=pilot()
    p['instances'][1]['translate_mm']=[4,4,2]
    p['instances'][2]['translate_mm']=[4,4,3]
    r=compile_geometry_composition(p)
    assert r['state']=='REVIEW_ONLY'  # only a digital *candidate*
    assert next(e for e in r['graph']['interfaces'] if e['from']=='structure')['exact_convex_contact']['relation']=='POINT_CONTACT'
    assert all(e['physical_compatibility']=='NOT_VERIFIED' for e in r['graph']['interfaces'])


def test_interlayer_requires_nonzero_face_area():
    p=pilot()
    p['instances'][1]['translate_mm']=[4,4,2]
    p['interfaces'][0]['kind']='INTERLAYER'
    assert 'INTERLAYER_NO_FINITE_CONTACT_AREA' in codes(p)


def test_composite_fails_closed_on_volume_interpenetration():
    p=pilot(); p['instances'][1]['translate_mm']=[0,0,1]
    assert 'UNRESOLVED_INTERPENETRATING_REGIONS' in codes(p)


def test_contact_disjoint_with_bounds_overlap_not_misclassified():
    p={
        'schema':'CGX-PRINTSPACE-GEOMETRY-COMPOSITION/0.1',
        'composite_id':'tetra-disjoint',
        'manufacturing_ir_ref':'cgx://manufacturing/build/tetra-synthetic',
        'load_mode':'H0_REVIEW_ONLY',
        'source_shapes':[{
            'shape_id':'tetra', 'units':'mm','source_ref':'SYNTHETIC', 'rights_ref':'SYNTHETIC',
            'vertices_mm':[[0,0,0],[2,0,0],[0,2,0],[0,0,2]],
            'faces':[[0,2,1],[0,1,3],[0,3,2],[1,2,3]],
        }],
        'instances':[
            {'instance_id':'a','shape_id':'tetra','translate_mm':[0,0,0],'kernel_id':'VGK-018','material_slot':'a'},
            {'instance_id':'b','shape_id':'tetra','translate_mm':[1,1,1],'kernel_id':'VGK-018','material_slot':'b'},
        ],
        'interfaces':[{'from':'a','to':'b','kind':'CONTACT_CANDIDATE','evidence_state':'UNTESTED'}],
    }
    assert 'DECLARED_CONTACT_DISJOINT' in codes(p)
    p['interfaces'][0]['kind']='SEPARATED'
    r=compile_geometry_composition(p)
    assert r['state']=='REVIEW_ONLY'
    assert r['graph']['interfaces'][0]['exact_convex_contact']['relation']=='DISJOINT'


def test_reversed_direction_remains_distinct_and_untested():
    p=pilot()
    before=compile_geometry_composition(p)
    p['interfaces'][0]['from'],p['interfaces'][0]['to']=p['interfaces'][0]['to'],p['interfaces'][0]['from']
    after=compile_geometry_composition(p)
    assert before['geometry_composite_hash'] != after['geometry_composite_hash']
    assert after['graph']['interfaces'][1]['physical_compatibility']=='NOT_VERIFIED'


def test_malformed_or_unreviewed_mesh_held():
    mesh=cube(); mesh['faces'][0].reverse()
    with pytest.raises(ContactHold, match='UNVERIFIED_CONVEX_GEOMETRY'):
        exact_convex_contact(mesh,[0,0,0],cube(),[4,0,0])


def test_bounded_complexity_fail_closed():
    mesh=cube()
    # Forcing an oversize face table cannot silently degrade to AABB evidence.
    mesh['faces'] = mesh['faces'] * 12
    with pytest.raises(ContactHold):
        exact_convex_contact(mesh,[0,0,0],cube(),[4,0,0])


def test_invalid_translation_rejected():
    with pytest.raises(ContactHold, match='INVALID_OR_UNBOUNDED_GEOMETRY'):
        exact_convex_contact(cube(),[0,True,0],cube(),[4,0,0])


def test_exact_boolean_and_physical_authorities_remain_false():
    p=pilot();r=compile_geometry_composition(p)
    for edge in r['graph']['interfaces']:
        x=edge['exact_convex_contact']
        assert x['integer_mm_rational_exact'] is True
        assert x['machine_execution_authorised'] is False
        assert x['material_interface_qualified'] is False
        assert edge['physical_compatibility']=='NOT_VERIFIED'
        assert 'SOURCE_TO_TARGET_DEPOSITION_COUPON' in edge['interface_qualification_plan']
        assert 'TARGET_TO_SOURCE_SEPARATE_COUPON' in edge['interface_qualification_plan']