"""Reproducible source-faceted CGX PrintSpace; no native/published authority."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import pytest

from cgx.manufacturing.virtual_factory import load_catalogue,canonical_digest
from cgx.manufacturing.printspace_cgx import (
    CGXHold, SCHEMA,build_bundle,check_bundle,h0_handshake,hydrate,
    pack_lite,unpack_lite,verify_back_down,_raw,_sha,
    project_space_context, verify_space_context_back_down, SPACE_FACETS,
)
from scripts.build_printspace_cgx_bundle import build as build_assets

BASE=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def data():
    c=load_catalogue()
    b=build_bundle(c)
    return c,b


def test_hash_index_integrity_and_r0_rights_hold(data):
    c,b=data
    assert b['schema']==SCHEMA
    assert b['source_catalogue_sha256']==canonical_digest(c)
    assert len(b['objects'])==len(b['aliases'])==80
    assert b['native_load_hydration'] is False
    assert b['machine_authorised'] is False
    assert b['mint_authorised'] is False
    assert b['commercial_release_authorised'] is False
    r=check_bundle(b,expected_catalogue_sha256=canonical_digest(c))
    assert r['objects']==80 and r['source_bodies_authenticated'] is False
    assert all(obj['device_authorised'] is False and obj['native_admitted'] is False for obj in b['objects'].values())
    assert all(not obj['payload'].get('real_toolheads_verified',False) for obj in b['objects'].values())


def test_h0_handshake_hydrates_zero_object_bodies(data):
    c,b=data
    h=h0_handshake(b,expected_catalogue_sha256=canonical_digest(c))
    assert h['state']=='H0_NONHYDRATING_SOURCE_INDEX_ONLY'
    assert h['source_bytes_hydrated']==0
    assert sorted(h['products'])==['product/board','product/diode','product/phone']
    assert h['parent_dbr_receipt'] is None
    p=hydrate(b,mode='H0')
    assert p['objects']=={} and p['objects_hydrated']==0


def test_selective_hydration_resolves_nested_phone_board_diode(data):
    _,b=data
    a=hydrate(b,product_id='diode')
    x=hydrate(b,product_id='board')
    y=hydrate(b,product_id='phone')
    assert 0<a['objects_hydrated']<x['objects_hydrated']<y['objects_hydrated']
    assert y['objects_hydrated']<len(b['objects'])
    assert set(['product/board','product/diode','product/phone'])<=set(y['aliases'])
    for facet in y['objects'].values():
        assert facet['device_authorised'] is False
    assert y['source_bytes_hydrated']==0
    assert y['external_asset_downloads']==0
    assert y['native_load_hydrated'] is False


def test_reused_box_geometry_facet_deduplicated(data):
    _,b=data
    primitives=[o for o in b['objects'].values() if o['kind']=='illustrative-geometry-primitive']
    parts=[o for o in b['objects'].values() if o['kind']=='product-part-placement']
    assert len(primitives)<len(parts)
    assert len([o for o in parts if o['payload']['source_kind']=='external'])>=5
    assert all(o['payload']['status']=='SOURCE_REQUIRED'
               for o in parts if o['payload']['source_kind']=='external')


def test_transport_round_trip_and_bounded_compression(data):
    c,b=data
    pack=pack_lite(b,expected_catalogue_sha256=canonical_digest(c))
    assert pack['native_ternary_encoder'] is False
    assert pack['compressed_bytes']<pack['raw_bytes']
    assert pack['compressed_bytes']<20000
    assert unpack_lite(pack,expected_catalogue_sha256=canonical_digest(c))==b
    assert pack_lite(b)==pack


def test_full_digital_hydration_preserves_immutability(data):
    _,b=data
    full=hydrate(b,mode='ALL_DIGITAL')
    assert full['objects_hydrated']==len(b['objects'])
    full['objects'][b['root']]['payload']['product_ids'].clear()
    assert b['objects'][b['root']]['payload']['product_ids']
    assert full['machine_authorised'] is False


def test_original_source_back_down_and_tamper_rejected(data):
    c,b=data
    assert verify_back_down(b,c)['state']=='PASS_DIGITAL_ONLY'
    tampered=copy.deepcopy(b)
    facet=next(k for k,o in tampered['objects'].items() if o['kind']=='nested-digital-assembly')
    tampered['objects'][facet]['payload']['title']='FORGED'
    with pytest.raises(CGXHold,match='OBJECT_HASH_MISMATCH'):
        check_bundle(tampered)
    assert verify_back_down(tampered,c)['state']=='HOLD'
    tampered=copy.deepcopy(b)
    tampered['machine_authorised']=True
    with pytest.raises(CGXHold,match='AUTHORITY_ESCALATION'):
        check_bundle(tampered)


def test_trusted_source_revision_required(data):
    c,b=data
    with pytest.raises(CGXHold,match='TRUSTED_CATALOGUE_SHA_MISMATCH'):
        check_bundle(b,expected_catalogue_sha256='0'*64)
    revised=copy.deepcopy(c)
    revised['products'][0]['parts'][0]['title']='DIFFERENT SOURCE REVISION'
    assert verify_back_down(b,revised)['state']=='HOLD'
    assert build_bundle(revised)['bundle_sha256']!=b['bundle_sha256']


def test_broken_alias_or_dependency_rejected(data):
    _,b=data
    bad=copy.deepcopy(b)
    bad['aliases']['product/phone']='sha256:'+'f'*64
    with pytest.raises(CGXHold,match='BROKEN_ALIAS'):check_bundle(bad)
    bad=copy.deepcopy(b)
    bad['objects'][bad['root']]['deps'].append('sha256:'+'0'*64)
    with pytest.raises(CGXHold,match='INVALID_DEPENDENCY_REFERENCE'):check_bundle(bad)


def test_unexpected_machine_code_or_source_body_rejected(data):
    _,b=data
    v=copy.deepcopy(b)
    v['objects'][v['root']]['payload']['machine_command']='HOME ALL'
    with pytest.raises(CGXHold,match='UNAUTHORISED_NATIVE_OR_MACHINE_FIELD'):check_bundle(v)
    v=copy.deepcopy(b)
    v['objects'][v['root']]['payload']['cad_source_bytes']='unlicensed'
    with pytest.raises(CGXHold,match='UNAUTHORISED_NATIVE_OR_MACHINE_FIELD'):check_bundle(v)


def test_request_budgets_and_invalid_modes_hold(data):
    _,b=data
    with pytest.raises(CGXHold,match='NATIVE_OR_UNSUPPORTED_HYDRATION_REQUEST'):hydrate(b,mode='NATIVE_LOAD')
    with pytest.raises(CGXHold,match='UNKNOWN_PRODUCT_ALIAS'):hydrate(b,product_id='supercomputer')
    with pytest.raises(CGXHold,match='HYDRATION_NODE_BUDGET'):hydrate(b,product_id='phone',max_nodes=2)
    with pytest.raises(CGXHold,match='HYDRATION_BYTE_BUDGET'):hydrate(b,product_id='phone',max_bytes=1024)
    with pytest.raises(CGXHold,match='NODE_BUDGET_INVALID'):hydrate(b,max_nodes=True)
    with pytest.raises(CGXHold,match='PRODUCT_SELECTOR_IN_FULL_MODE'):hydrate(b,product_id='phone',mode='ALL_DIGITAL')


def test_lite_transport_modified_sha_payload_and_size_rejected(data):
    _,b=data
    for change in ('raw_sha256','compressed_bytes','payload_b64','native_ternary_encoder'):
        env=pack_lite(b)
        if change=='raw_sha256':env[change]='f'*64
        elif change=='compressed_bytes':env[change]+=1
        elif change=='payload_b64':env[change]='$$$'
        else:env[change]=True
        with pytest.raises((CGXHold,ValueError,TypeError)):unpack_lite(env)


def test_canonical_rebuild_files_and_studio_generation(data):
    assert build_assets(check=True)['state']=='PASS_DIGITAL_ONLY'
    original=load_catalogue()
    b=build_bundle(original)
    stored=json.loads((BASE/'cgx/manufacturing/printspace_cgx_bundle_v0_1.json').read_text())
    assert b==stored
    lite=json.loads((BASE/'cgx/manufacturing/printspace_cgx_lite_v0_1.json').read_text())
    assert unpack_lite(lite)==stored
    studio=(BASE/'cgx/manufacturing/printspace_studio_v0_1.html').read_text()
    assert 'cgxBundleBtn' in studio and 'cgxH0Btn' in studio
    assert 'CGX-PRINTSPACE-FILESPACE-BUNDLE/0.1' in studio
    assert 'H0_NONHYDRATING_SOURCE_INDEX_ONLY' in studio


def test_dynamic_custom_product_no_new_root_or_material_authority(data):
    c,_=data
    revised=copy.deepcopy(c)
    clone=copy.deepcopy(revised['products'][0]);clone['id']='new-facet';clone['key']='CGX-NEW-TEST'
    for part in clone['parts']:part['parent']=None
    revised['products'].append(clone)
    b=build_bundle(revised)
    assert 'product/new-facet' in b['aliases']
    assert hydrate(b,product_id='new-facet')['state']=='DIGITAL_SYMBOLIC_FACETS_ONLY'
    assert b['commercial_release_authorised'] is False


# This edits the existing regression suite rather than adding a competing
# cross-space schema, database or native resolver.
def original_parent_sources():
    domain_path=BASE/'cgx/domain_templates/domains.json'
    parent_path=BASE/'cgx/domain_templates/cognigrex_parent_topology.json'
    if domain_path.is_file() and parent_path.is_file():
        return json.loads(domain_path.read_text()),json.loads(parent_path.read_text())
    # The isolated package-under-test has only the source-shape contracts. The
    # full GitHub repository tests against its real tracked parent source bytes.
    return (
        {'schema':'CGX-DOMAIN-TEMPLATES/0.4',
         'parent_filespace':{'file':'Cognigrex.cgx'},
         'domains':{'romer':{'file':'Romer.cgx',
                             'namespace':'cgx://romer.industries/romer'}}},
        {'schema':'CGX-COGNIGREX-PARENT-TOPOLOGY/0.2',
         'root':{'file':'Cognigrex.cgx',
                 'children':[{'id':'romer','file':'Romer.cgx'}]}}
    )


@pytest.mark.parametrize('product', ['diode','board','phone'])
@pytest.mark.parametrize('facet', sorted(SPACE_FACETS))
def test_one_canonical_root_for_each_existing_space_facet(data,product,facet):
    c,b=data
    domains,topology=original_parent_sources()
    x=project_space_context(b,c,domains,topology,product_id=product,facet=facet)
    assert x['root_carrier']=='Cognigrex.cgx'
    assert x['child_carrier']=='Romer.cgx'
    assert x['canonical_child_namespace']=='cgx://romer.industries/romer'
    assert x['product_facet_sha256']==b['aliases']['product/'+product]
    assert x['selected_space']==facet
    assert x['native_dbr_written'] is False and x['machine_authorised'] is False
    assert x['source_rights_authenticated'] is False
    assert x['t173_exact_mesh_admitted'] is False
    assert x['native_ternary_encoded'] is False
    assert x['native_file_or_data_space_attached'] is False
    if facet=='print_space':
        assert x['facet_view']['payload_objects']>0
        assert x['facet_view']['geometry']=='SYNTHETIC_AXIS_ALIGNED_BOX_MM'
        assert x['facet_view']['real_toolpath'] is None
    else:
        assert x['facet_view']['payload_objects']==0
    assert verify_space_context_back_down(x,b,c,domains,topology,
             product_id=product,facet=facet)['state']=='PASS_DIGITAL_ONLY'


def test_h0_subordinate_root_namespace_and_zero_hydration(data):
    c,b=data
    h=h0_handshake(b,expected_catalogue_sha256=canonical_digest(c))
    assert h['root_namespace']=='cgx://romer.industries/romer/printspace/'
    assert h['source_bytes_hydrated']==0 and h['native_admitted'] is False
    assert h['parent_dbr_receipt'] is None


def test_ternary_and_t173_cannot_be_promoted_from_illustrative_geometry(data):
    c,b=data
    dom,top=original_parent_sources()
    for mode,hold in [('t173','T173_EXACT_MESH_AND_RIGHTS_ADMISSION_MISSING'),
                      ('ternary','NATIVE_TERNARY_TRANSPORT_NOT_ADMITTED'),
                      ('imaginary','UNKNOWN_REPRESENTATION')]:
        with pytest.raises(CGXHold,match=hold):
            project_space_context(b,c,dom,top,representation=mode)
    with pytest.raises(CGXHold,match='UNKNOWN_SPACE_OR_PRODUCT'):
        project_space_context(b,c,dom,top,facet='new_rival_filespace')


def test_unauthorised_parent_child_or_source_change_fails_closed(data):
    c,b=data
    dom,top=original_parent_sources()
    changes=[('parent', 'ROOT'),('child','RIVAL'),('namespace','cgx://new-root'),
             ('duplicate','Romer.cgx')]
    for action,value in changes:
        d,t=copy.deepcopy(dom),copy.deepcopy(top)
        if action=='parent': t['root']['file']=value
        elif action=='child':d['domains']['romer']['file']=value
        elif action=='namespace':d['domains']['romer']['namespace']=value
        else:t['root']['children'].append({'id':'romer','file':value})
        with pytest.raises(CGXHold,match='CANONICAL_PARENT_SOURCE_MISMATCH|ROMER_CHILD_SOURCE_MISMATCH'):
            project_space_context(b,c,d,t)
    d,t=copy.deepcopy(dom),copy.deepcopy(top)
    c2=copy.deepcopy(c);c2['catalogue_id']+='-forged'
    with pytest.raises(CGXHold,match='ORIGINAL_CATALOGUE_REPLAY_REQUIRED'):
        project_space_context(b,c2,d,t)


def test_back_down_rejects_false_dbr_or_modified_view_without_mutating_sources(data):
    c,b=data
    dom,top=original_parent_sources()
    before=copy.deepcopy((b,c,dom,top))
    result=project_space_context(b,c,dom,top,product_id='phone',facet='data_space')
    fake=copy.deepcopy(result);fake['native_dbr_written']=True
    assert verify_space_context_back_down(fake,b,c,dom,top,
           product_id='phone',facet='data_space')['state']=='HOLD'
    fake=copy.deepcopy(result);fake['facet_view']['measured_readings']=[{'fake':1}]
    assert verify_space_context_back_down(fake,b,c,dom,top,
           product_id='phone',facet='data_space')['state']=='HOLD'
    assert before==(b,c,dom,top)
