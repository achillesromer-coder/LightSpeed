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