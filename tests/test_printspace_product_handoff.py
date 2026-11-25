"""Fail-closed exact status and source-bounded PrintSpace handoff tests."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.validate_printspace_product_handoff import (
    HandoffHold, REGISTER, PRE_DBR, audit, read_json, ROOT
)


def docs():
    return read_json(REGISTER),read_json(PRE_DBR,256*1024)


def test_exact_private_handoff_16_open_and_no_authority():
    a,b=docs();r=audit(a,b)
    assert r['state']=='PASS_HANDOFF_REGISTER_INVARIANTS_ONLY'
    assert (r['software_open'],r['native_open'],r['physical_open'])==(7,4,5)
    assert r['open_workstreams']==16
    assert r['pre_dbr_protected']>=80
    assert r['file_space_transition_authorised'] is False
    assert r['public_release_authorised'] is False
    assert r['machine_authorised'] is False
    assert r['private_archive_check']=='NOT_SUPPLIED_TO_THIS_CHECK'


def test_ids_unique_categories_open_and_deterministic_digest():
    a,b=docs();x=audit(a,b);y=audit(copy.deepcopy(a),copy.deepcopy(b))
    assert x==y
    assert len(set(t['id'] for t in a['open_workstreams']))==16
    assert len(set(a['automation_mode']['roles']))==5


def test_owner_accepted_or_public_rights_forgery_holds():
    a,b=docs()
    a['private_candidate']['owner_accepted']=True
    with pytest.raises(HandoffHold,match='RC_VERSION_IDENTITY_OR_AUTHORITY'):audit(a,b)
    a,b=docs();a['conclusions']['software_final_release_approved']=True
    with pytest.raises(HandoffHold,match='FALSE_PRODUCT_RELEASE_STATUS'):audit(a,b)


def test_fake_task_completion_or_unknown_coordinator_holds():
    a,b=docs();a['open_workstreams'][0]['status']='COMPLETE'
    with pytest.raises(HandoffHold,match='TASK_FALSE_ACCEPTANCE'):audit(a,b)
    a,b=docs();a['open_workstreams'][1]['coordinator']='UNAUTHORISED_NEW_AGENT'
    with pytest.raises(HandoffHold,match='TASK_FALSE_ACCEPTANCE'):audit(a,b)


def test_duplicate_task_removed_task_and_count_forgery_holds():
    a,b=docs();a['open_workstreams'][1]['id']=a['open_workstreams'][0]['id']
    with pytest.raises(HandoffHold,match='TASK_UNIQUE_ID'):audit(a,b)
    a,b=docs();a['open_workstreams'].pop()
    with pytest.raises(HandoffHold,match='OPEN_TASK_COUNT'):audit(a,b)
    a,b=docs();a['counts']['total_open']=0
    with pytest.raises(HandoffHold,match='TASK_BUCKET_COUNTS'):audit(a,b)


def test_unauthorised_filespace_switch_or_scheduler_holds():
    a,b=docs();a['automation_mode']['next_product_auto_activation_allowed']=True
    with pytest.raises(HandoffHold,match='AUTOMATION_OR_OWNER_ESCALATION'):audit(a,b)
    a,b=docs();a['automation_mode']['new_scheduler_allowed']=True
    with pytest.raises(HandoffHold,match='AUTOMATION_OR_OWNER_ESCALATION'):audit(a,b)


def test_archive_mutation_or_loss_of_protected_refs_holds():
    a,b=docs();b['invariant_policy']['owner_approved']=True
    with pytest.raises(HandoffHold,match='ARCHIVE_OR_OWNER_AUTHORITY_ESCALATED'):audit(a,b)
    a,b=docs();b['protected_active']=[]
    with pytest.raises(HandoffHold,match='PRE_DBR_COUNT_REGRESSION'):audit(a,b)


def test_five_space_dependency_and_product_sequence_holds_when_wrong():
    a,b=docs();a['source_refs']['five_facet_dependency']='https://example.com/other'
    with pytest.raises(HandoffHold,match='CROSS_PR_SOURCE_REF_DRIFT'):audit(a,b)
    a,b=docs();a['release_sequence'][0]='FileSpace'
    with pytest.raises(HandoffHold,match='PRODUCT_SEQUENCE_REORDERED'):audit(a,b)


def test_real_private_rc2_archive_check_if_provided():
    p=Path('/mnt/data/PrintSpace_Software_0.1.0-rc.2_PRIVATE.zip')
    if not p.is_file():pytest.skip('Exact archived RC candidate not mounted in CI; archive validated in separate CI job')
    a,b=docs();r=audit(a,b,archive=p)
    assert r['private_archive_check']=='SHA256_AND_PRIVATE_SCOPE_VERIFIED'


def test_mismatched_archive_bytes_hold(tmp_path):
    a,b=docs();p=tmp_path/'misidentified.zip';p.write_bytes(b'not-the-pinned-archive')
    with pytest.raises(HandoffHold,match='RC2_ARCHIVE_MISSING_OR_WRONG_SIZE'):audit(a,b,archive=p)
