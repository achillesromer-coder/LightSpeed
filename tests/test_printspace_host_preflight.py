"""One canonical PrintSpace -> UniSpace R0 handshake; no native rights claim."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import pytest

from cgx.manufacturing.virtual_factory import load_catalogue
from cgx.manufacturing.printspace_cgx import build_bundle
from cgx.manufacturing.printspace_host_preflight import (
    SCHEMA, prepare_r0_host_review, verify_r0_host_review_back_down,
)


def sources():
    catalogue = load_catalogue()
    return catalogue, build_bundle(catalogue)


def mappings():
    # DELIBERATELY SYNTHETIC: not a source registry, no native Object_ID minted.
    return [dict(product_id=product, candidate_object_id=f'PS-{product.upper()}-CANDIDATE-001',
                 twin_id=f'{product}-candidate',lineage_git_blob_sha='1'*40,
                 registry_git_blob_sha='2'*40)
            for product in ('diode','board','phone')]


def test_unbound_h0_review_has_three_products_zero_identity_claims():
    c,b=sources()
    r=prepare_r0_host_review(b,c)
    assert r['schema']==SCHEMA
    assert r['state']=='R0_CANDIDATE_REVIEW_NOT_ADMITTED'
    assert r['product_count']==3
    assert r['candidate_count']==0
    assert len(r['r0_cases'])==3
    assert [x['product_id'] for x in r['r0_cases']]==['board','diode','phone']
    assert all(x['candidate_object_id'] is None and not x['host_context_request_ready']
               for x in r['r0_cases'])
    assert r['source_bytes_hydrated']==0
    assert 'PARENT_RIGHTS_ACL_AND_DB_REVIEW_PENDING' in r['hold_codes']
    assert not r['trusted_host_authenticated']
    assert not r['native_admitted']
    assert not r['machine_authorised']
    assert not r['native_dbr_written']
    assert not r['mint_authorised']
    assert not r['commercial_release_authorised']
    assert verify_r0_host_review_back_down(r,b,c)['state']=='PASS_DIGITAL_ONLY'


def test_synthetic_candidates_are_unique_and_still_untrusted():
    c,b=sources()
    p=prepare_r0_host_review(b,c,mappings())
    assert p['candidate_count']==3
    assert all(x['host_context_request_ready'] for x in p['r0_cases'])
    assert len({x['candidate_object_id'] for x in p['r0_cases']})==3
    assert all(x['destination_filespace']=='Romer.cgx' and x['parent_filespace']=='Cognigrex.cgx'
               for x in p['r0_cases'])
    assert all(x['child_domain']=={'semantic_object_id':'cgx:domain:romer',
                                   'filespace':'Romer.cgx','domain':'romer'}
               for x in p['r0_cases'])
    assert all(not x['source_lineage_independently_verified'] and not x['source_rights_independently_verified']
               for x in p['r0_cases'])
    assert not p['native_admitted']
    assert verify_r0_host_review_back_down(p,b,c,mappings())['state']=='PASS_DIGITAL_ONLY'
    assert p==prepare_r0_host_review(b,c,list(reversed(mappings())))


def test_one_source_pin_change_invalidates_source_replay():
    c,b=sources();p=prepare_r0_host_review(b,c,mappings())
    mutated=copy.deepcopy(b);mutated['bundle_sha256']='sha256:'+'0'*64
    assert prepare_r0_host_review(mutated,c)['state']=='HOLD'
    assert verify_r0_host_review_back_down(p,mutated,c,mappings())['state']=='HOLD'
    altered=copy.deepcopy(c);altered['catalogue_id']='ALTERED'
    assert verify_r0_host_review_back_down(p,b,altered,mappings())['state']=='HOLD'


def test_case_alias_and_authority_tamper_fail_backtrace():
    c,b=sources();p=prepare_r0_host_review(b,c,mappings())
    for fn in [lambda x:x['r0_cases'][0].update(product_alias='product/other'),
               lambda x:x.update(native_admitted=True),
               lambda x:x['r0_cases'][0].update(source_rights_independently_verified=True),
               lambda x:x.update(plan_sha256='0'*64)]:
        q=copy.deepcopy(p);fn(q)
        assert verify_r0_host_review_back_down(q,b,c,mappings())['state']=='HOLD'


def test_missing_mapping_is_not_native_id_evidence():
    c,b=sources()
    p=prepare_r0_host_review(b,c,mappings()[:1])
    assert p['candidate_count']==1
    assert sum(x['host_context_request_ready'] for x in p['r0_cases'])==1
    assert not p['trusted_host_authenticated']


def test_duplicate_product_and_native_semantic_ids_rejected():
    c,b=sources()
    q=mappings();q[1]['product_id']=q[0]['product_id']
    assert 'UNKNOWN_OR_DUPLICATE_PRODUCT_BINDING' in prepare_r0_host_review(b,c,q)['hold_codes']
    q=mappings();q[1]['candidate_object_id']=q[0]['candidate_object_id']
    assert 'NATIVE_SEMANTIC_ID_COLLISION_CANDIDATE' in prepare_r0_host_review(b,c,q)['hold_codes']


@pytest.mark.parametrize('value',[None,'cgx:domain:romer','cgx:root:cognigrex','LOAD.cgx',
                                  'PrintSpace.cgx','PS-\n01','/private/object','',1])
def test_invalid_candidate_ids_never_become_native(value):
    c,b=sources();q=mappings();q[0]['candidate_object_id']=value
    assert prepare_r0_host_review(b,c,q)['state']=='HOLD'


def test_unknown_product_twin_and_bad_source_hashes_rejected():
    c,b=sources()
    q=mappings();q[0]['product_id']='unlisted'
    assert 'UNKNOWN_OR_DUPLICATE_PRODUCT_BINDING' in prepare_r0_host_review(b,c,q)['hold_codes']
    q=mappings();q[0]['twin_id']=''
    assert 'INVALID_TWIN_CANDIDATE' in prepare_r0_host_review(b,c,q)['hold_codes']
    q=mappings();q[0]['registry_git_blob_sha']='not-real'
    assert 'INVALID_REGISTRY_OR_LINEAGE_SHA1' in prepare_r0_host_review(b,c,q)['hold_codes']


@pytest.mark.parametrize('key',['token','password','source_bytes','private_path','lease','machine_command','signed_licence'])
def test_private_or_unauthorised_fields_hold(key):
    c,b=sources();q=mappings();q[0][key]='untrusted'
    assert prepare_r0_host_review(b,c,q)['state']=='HOLD'


def test_nonfinite_oversize_and_nonjson_inputs_fail():
    c,b=sources()
    q=mappings();q[0]['nested']={'measured':float('nan')}
    assert prepare_r0_host_review(b,c,q)['state']=='HOLD'
    q=mappings();q[0]['nested']='x'*40000
    assert prepare_r0_host_review(b,c,q)['state']=='HOLD'
    assert prepare_r0_host_review(None,c)['state']=='HOLD'
    assert prepare_r0_host_review(b,None)['state']=='HOLD'


def test_read_only_result_reveals_no_authorisation_or_source_bodies():
    c,b=sources();p=prepare_r0_host_review(b,c,mappings())
    encoded=json.dumps(p)
    for term in ['PRIVATE_SOURCE.xlsx','Bearer ', 'secret-session','/private/', 'BEGIN PRIVATE KEY']:
        assert term not in encoded
    assert p['r0_cases'][0]['r_layer']=='R0'
    assert p['r0_cases'][0]['hydration']=='H0'


def test_source_snapshot_fixture_is_exact_and_reproducible():
    root=Path(__file__).resolve().parents[1]
    fixture=json.loads((root/'cgx/manufacturing/printspace_host_r0_review_v0_1.json').read_text(encoding='utf-8'))
    c,b=sources()
    assert prepare_r0_host_review(b,c)==fixture
    assert verify_r0_host_review_back_down(fixture,b,c)['exact_replay_matched'] is True