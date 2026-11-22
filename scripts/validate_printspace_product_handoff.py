#!/usr/bin/env python3
"""Deterministic PrintSpace software productisation/handoff auditor.

No service, scheduler, owner approval, deployment, native DBR or auto-mint.
Reads one canonical task register and source-controlled release/archive gates.
Optional --archive performs byte-for-byte RC and in-ZIP safety readback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / 'cgx/manufacturing/printspace_product_handoff_v0_1.json'
PRE_DBR = ROOT / 'cgx/manufacturing/printspace_pre_dbr_archive_register_v0_1.json'
SCHEMA = 'CGX-PRINTSPACE-PRODUCTISATION-HANDOFF/0.1'
VALID_CATEGORIES = {'software': 7, 'native': 4, 'physical': 5}
LANES = {'Achilles Römer','Neo LightSpeed','Athene Eco','Cognigrex Family','UniSpace Product'}
SHA = re.compile(r'^[0-9a-f]{64}$')
HEX40 = re.compile(r'^[0-9a-f]{40}$')
MAX_REGISTER_BYTES = 64 * 1024
MAX_ZIP_BYTES = 8 * 1024 * 1024

class HandoffHold(ValueError):
    pass


def read_json(path: Path, max_bytes: int = MAX_REGISTER_BYTES) -> dict:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > max_bytes:
        raise HandoffHold('MISSING_OR_UNSAFE_SOURCE:' + path.name)
    try:
        val = json.loads(path.read_text(encoding='utf-8'))
    except (UnicodeError, ValueError, OSError) as exc:
        raise HandoffHold('INVALID_JSON:' + path.name) from exc
    if not isinstance(val, dict):
        raise HandoffHold('ROOT_OBJECT_REQUIRED')
    return val


def audit(register: dict, pre_dbr: dict, *, archive: Path | None = None) -> dict:
    if not isinstance(register,dict) or register.get('schema') != SCHEMA:
        raise HandoffHold('HANDOFF_SCHEMA')
    if set(register) != {'schema','version','scope','canonical_repo','canonical_pr',
        'observed_source_head_baseline','private_candidate','source_refs','automation_mode',
        'release_sequence','open_workstreams','counts','external_reference_not_added_to_open_count',
        'conclusions','proof_ceiling','safety'}:
        raise HandoffHold('HANDOFF_TOPLEVEL_EXTRA_OR_MISSING')
    if register['scope']!='CURATED_PRINTSPACE_RELEASE_GATES_NOT_COMPLETE_PROJECT_DISCOVERY' or \
       register['canonical_repo']!='achillesromer-coder/LightSpeed' or register['canonical_pr']!=236 or \
       not isinstance(register['observed_source_head_baseline'],str) or \
       not HEX40.fullmatch(register['observed_source_head_baseline']):
        raise HandoffHold('SOURCE_IDENTITY_OR_SCOPE')
    if register['release_sequence']!=['PrintSpace','FileSpace','DataSpace','UniSpace','Grex operations and outreach']:
        raise HandoffHold('PRODUCT_SEQUENCE_REORDERED')
    rc=register['private_candidate']
    if rc.get('version')!='0.1.0-rc.2' or rc.get('scope')!='OWNER_PRIVATE_EVALUATION_ONLY' or \
       rc.get('state')!='VERIFIED_PRIVATE_DIGITAL_RC_ONLY' or \
       type(rc.get('bytes')) is not int or rc['bytes']<=0 or \
       not isinstance(rc.get('sha256'),str) or not SHA.fullmatch(rc['sha256']) or \
       rc.get('validated_regression_stages')!=27 or \
       not all(rc.get(x) is False for x in ['public_approved','owner_accepted','native_admitted','physical_machine_authorised']):
        raise HandoffHold('RC_VERSION_IDENTITY_OR_AUTHORITY')
    refs=register['source_refs']
    required=['release_gate','release_builder','pre_dbr','five_facet_dependency','pc01_witness']
    if set(refs)!=set(required) or any(not isinstance(refs[x],str) or not refs[x] for x in required):
        raise HandoffHold('SOURCE_REFERENCE_REQUIRED')
    if refs['pre_dbr']!='cgx/manufacturing/printspace_pre_dbr_archive_register_v0_1.json' or \
       refs['release_builder']!='scripts/package_printspace_software.py' or \
       refs['five_facet_dependency']!='https://github.com/achillesromer-coder/LightSpeed/pull/232':
        raise HandoffHold('CROSS_PR_SOURCE_REF_DRIFT')
    if not isinstance(pre_dbr,dict) or pre_dbr.get('schema')!='CGX-PRINTSPACE-PRE-DBR-ARCHIVE-REGISTER/0.1':
        raise HandoffHold('PRE_DBR_SCHEMA')
    policy=pre_dbr.get('invariant_policy',{})
    for key in ('archive_execution_authorised','delete_execution_authorised','overwrite_execution_authorised',
                'dbr_finalised','owner_approved'):
        if policy.get(key) is not False:raise HandoffHold('ARCHIVE_OR_OWNER_AUTHORITY_ESCALATED')
    if len(pre_dbr.get('candidates',[]))!=3 or len(pre_dbr.get('protected_active',[]))<80:
        raise HandoffHold('PRE_DBR_COUNT_REGRESSION')
    if policy.get('protected_remote_desktop_reserve_pct')!=25 or policy.get('emergency_remote_desktop_floor_pct')!=24:
        raise HandoffHold('RDC_RESERVE_POLICY_DRIFT')
    lanes=register['automation_mode']
    if set(lanes.get('roles',[]))!=LANES or len(lanes.get('roles',[]))!=5 or \
       lanes.get('exactly_five_existing_coordinators') is not True or \
       lanes.get('status')!='HANDOFF_SPECIFICATION_NOT_HOST_EXECUTION' or \
       lanes.get('next_product')!='FileSpace' or \
       lanes.get('read_only_review_allowed') is not True or \
       any(lanes.get(k) is not False for k in (
           'new_scheduler_allowed','next_product_auto_activation_allowed',
           'owner_acceptance_for_next_phase','native_mutation_allowed','public_launch_allowed','archive_move_allowed')) or \
       lanes.get('remote_desktop_normal_reserve_pct')!=25 or \
       lanes.get('remote_desktop_emergency_floor_pct')!=24:
        raise HandoffHold('AUTOMATION_OR_OWNER_ESCALATION')
    entries=register.get('open_workstreams')
    if not isinstance(entries,list) or len(entries)!=16:
        raise HandoffHold('OPEN_TASK_COUNT_OR_TYPE')
    cat=Counter()
    ids=set()
    for row in entries:
        if not isinstance(row,dict) or set(row)!={'id','category','name','coordinator','status',
                 'required_evidence','hold_code','automated_action','independently_verified'}:
            raise HandoffHold('TASK_FIELDS_INVALID')
        if row['category'] not in VALID_CATEGORIES or row['id'] in ids or \
           not re.fullmatch(r'(?:SW|NATIVE|PHYS)-\d\d',row['id']):
            raise HandoffHold('TASK_UNIQUE_ID_OR_CLASS')
        ids.add(row['id']);cat[row['category']]+=1
        if row['status']!='OPEN_VERIFICATION_OR_APPROVAL' or row['independently_verified'] is not False or \
           row['automated_action']!='READ_CHECK_REPORT_ONLY' or row['coordinator'] not in LANES or \
           any(not isinstance(row[k],str) or len(row[k])<8 for k in ('name','required_evidence','hold_code')):
            raise HandoffHold('TASK_FALSE_ACCEPTANCE_OR_MISSING_EVIDENCE')
    if dict(cat)!=VALID_CATEGORIES or register['counts']!={
            'software':7,'native':4,'physical':5,'total_open':16,
            'pre_dbr_archive_review_candidates':3,'automation_lanes_active_expected':5}:
        raise HandoffHold('TASK_BUCKET_COUNTS_MISMATCH')
    result=register['conclusions']
    if result.get('private_software_rc_verified') is not True or \
       any(result.get(k) is not False for k in (
           'software_final_release_approved','physical_product_qualified',
           'file_space_handoff_authorised','data_space_launch_authorised',
           'unispace_launch_authorised','grex_outreach_authorised')):
        raise HandoffHold('FALSE_PRODUCT_RELEASE_STATUS')
    if register.get('proof_ceiling')!='PRIVATE_DIGITAL_SOFTWARE_EVALUATION_ONLY_NO_PHYSICAL_CLAIMS' or \
       any(value is not True for value in register['safety'].values()):
        raise HandoffHold('SAFETY_OR_PROOF_CEILING_ESCALATION')
    if register['external_reference_not_added_to_open_count'].get('canonical_pr_draft') is not True:
        raise HandoffHold('MISREPRESENTED_DRAFT_STATE')
    archive_status='NOT_SUPPLIED_TO_THIS_CHECK'
    if archive is not None:
        if not archive.is_file() or archive.is_symlink() or archive.stat().st_size!=rc['bytes']:
            raise HandoffHold('RC2_ARCHIVE_MISSING_OR_WRONG_SIZE')
        raw=archive.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=rc['sha256']:
            raise HandoffHold('RC2_ARCHIVE_SHA256_MISMATCH')
        try:
            with zipfile.ZipFile(archive) as z:
                if z.testzip() is not None or 'MANIFEST.json' not in z.namelist():
                    raise HandoffHold('RC2_ARCHIVE_CORRUPT')
                doc=json.loads(z.read('MANIFEST.json'))
                if doc.get('version')!='0.1.0-rc.2' or \
                   doc.get('distribution_scope')!='OWNER_PRIVATE_EVALUATION_ONLY' or \
                   doc.get('software_release_ready_for_public') is not False or \
                   doc.get('independent_signing_attestation') is not False or \
                   any(v is not False for v in doc.get('safety_flags',{}).values()):
                    raise HandoffHold('RC2_ARCHIVE_FALSE_PUBLIC_AUTHORITY')
                archive_status='SHA256_AND_PRIVATE_SCOPE_VERIFIED'
        except (OSError,ValueError,zipfile.BadZipFile,KeyError) as exc:
            raise HandoffHold('RC2_ARCHIVE_READBACK_FAILED') from exc
    digest=hashlib.sha256(json.dumps(register,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
    return {'schema':'CGX-PRINTSPACE-HANDOFF-REVIEW-RECEIPT/0.1',
        'state':'PASS_HANDOFF_REGISTER_INVARIANTS_ONLY',
        'source_registry_sha256':digest,
        'release_version':rc['version'],'release_candidate_sha256':rc['sha256'],
        'private_archive_check':archive_status,'open_workstreams':16,
        'software_open':7,'native_open':4,'physical_open':5,
        'archive_review_candidates':3,'pre_dbr_protected':len(pre_dbr['protected_active']),
        'expected_existing_automations':5,'next_product':'FileSpace',
        'file_space_transition_authorised':False,
        'public_release_authorised':False,'owner_approval_verified':False,
        'real_data_space_or_hardware_verified':False,
        'source_authentication_independent':False,
        'native_dbr_written':False,'machine_authorised':False,
        'meaning':'TASK_INVENTORY_AND_SOURCE_ONLY_NOT_AN_OWNER_SIGNATURE'}


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,default=None)
    parser.add_argument('--emit',type=Path,default=None,help='Save non-authorising review receipt (not DBR)')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    try:
        res=audit(read_json(REGISTER),read_json(PRE_DBR,256*1024),archive=args.archive)
    except HandoffHold as exc:
        print(json.dumps({'state':'HOLD','reason':str(exc),'public_release_authorised':False}),file=sys.stderr)
        return 2
    if args.emit:
        args.emit.parent.mkdir(parents=True,exist_ok=True)
        args.emit.write_text(json.dumps(res,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(res,sort_keys=True,indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
