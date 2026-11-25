from __future__ import annotations

import copy
import importlib.util
import json
import hashlib
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools/cgx_unispace_crossspace_review.py'
REG = ROOT / 'cgx/review/unispace_crossspace_gate_register_v0_1.json'
spec = importlib.util.spec_from_file_location('cgx_unispace_crossspace_review', SCRIPT)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    return json.loads(REG.read_text(encoding='utf-8'))


def receipt(x=None, mesh=None):
    data = fixture() if x is None else x
    return m.source_review(data, m.EXPECTED_SHA256, mesh)


def mock_source_mesh():
    facets = [{'id': facet, 'state': 'SOURCE_CONTRACTS_PRESENT',
               'execution_authorized': False, 'independent_native_admission': False}
              for facet in ('file_space','data_space','social_space','print_space','intelligence_space')]
    return {'mesh': {'schema': m.MESH_SCHEMA, 'canonical_root_id': m.ROOT,
                     'state': 'SOURCE_CONTRACT_MESH_OBSERVED', 'facet_count': 5,
                     'unique_contract_count': 12, 'unique_service_count': 7,
                     'new_root_created': False, 'new_database_created': False,
                     'model_weights_modified': False,
                     'native_execution_authorized': False,
                     'mint_or_network_authorized': False,
                     'source_hydration_performed': False,
                     'facets': facets}}


def test_exact_51_source_ids_and_no_authority():
    raw = REG.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == m.EXPECTED_SHA256
    r = receipt()
    assert r['state'] == 'SOURCE_REVIEW_ONLY_51_TASKS_OPEN'
    assert r['task_count'] == 51
    assert r['source_verified_printspace_open'] == 16
    assert r['proposed_crossspace_open'] == 35
    assert sum(r['group_counts'].values()) == 51
    assert r['source_mesh_observed'] is False
    for x in ('next_product_phase_authorised','native_admitted','archive_delete_authorised',
              'all_task_groups_closed','owner_acceptance_observed',
              'side_effects_performed','new_scheduler_created','new_root_created'):
        assert r[x] is False
    assert len(r['proposed_independent_review_roots']) == 8


def test_crossspace_mesh_reuses_existing_five_facet_contract_without_native_promotion():
    r = receipt(mesh=mock_source_mesh())
    assert r['source_mesh_observed'] is True
    assert r['source_contracts_present_not_native'] is True
    assert r['native_admitted'] is False
    assert r['owner_acceptance_observed'] is False
    assert r['source_heads_verified_current'] is False


def test_deterministic_receipt_and_dependency_graph():
    a, b = receipt(), receipt()
    assert a == b
    assert set(a['proposed_independent_review_roots']) == {
        'SW-01','SW-02','FS-01','DS-02','SS-01','IM-01','US-01','AR-01'}


@pytest.mark.parametrize('key', [
    'owner_acceptance','native_dbr_write','native_hydration','mint','machine_control',
    'archive_delete','new_root','new_scheduler','file_space_product_phase_active',
    'public_release',
])
def test_privilege_flag_cannot_promote_phase(key):
    x = fixture()
    x['authority'][key] = True
    with pytest.raises(m.CrossSpaceHold, match='privileged action'):
        receipt(x)


def test_mismatched_parent_and_sha_fail():
    x = fixture()
    x['canonical_root'] = 'cgx:root:second'
    with pytest.raises(m.CrossSpaceHold, match='wrong original parent'):
        receipt(x)
    y = fixture()
    y['checkpoint_sha256'] = '0'*64
    with pytest.raises(m.CrossSpaceHold, match='wrong original parent'):
        receipt(y)


def test_duplicate_or_missing_group_rejected():
    x = fixture()
    x['task_groups'][3]['id'] = x['task_groups'][2]['id']
    with pytest.raises(m.CrossSpaceHold, match='task ID'):
        receipt(x)
    x = fixture()
    x['task_groups'].pop()
    with pytest.raises(m.CrossSpaceHold, match='missing or extra'):
        receipt(x)


def test_fake_approved_and_private_field_rejected():
    x = fixture()
    x['task_groups'][0]['owner_approval_observed'] = True
    with pytest.raises(m.CrossSpaceHold, match='unproven task'):
        receipt(x)
    y = fixture()
    y['task_groups'][0]['host_secret'] = 'unsafe'
    with pytest.raises(m.CrossSpaceHold, match='task schema'):
        receipt(y)


def test_crossspace_source_candidate_not_promoted():
    x = fixture()
    x['task_groups'][16]['provenance'] = 'OPEN_SOURCE_VERIFIED'
    with pytest.raises(m.CrossSpaceHold, match='unproven task'):
        receipt(x)
    y = fixture()
    y['source_heads_are_currently_authenticated'] = True
    with pytest.raises(m.CrossSpaceHold, match='source-only authority'):
        receipt(y)


def test_cycle_and_unavailable_dependency_rejected():
    x = fixture()
    x['task_groups'][1]['proposed_dependencies'] = ['SW-03']
    with pytest.raises(m.CrossSpaceHold, match='dependency cycle'):
        receipt(x)
    y = fixture()
    y['task_groups'][0]['proposed_dependencies'] = ['NATIVE-999']
    with pytest.raises(m.CrossSpaceHold, match='dependency escapes'):
        receipt(y)


def test_unsafe_or_missing_existing_mesh_rejected():
    x = mock_source_mesh()
    x['mesh']['new_database_created'] = True
    with pytest.raises(m.CrossSpaceHold, match='effectful action'):
        receipt(mesh=x)
    x = mock_source_mesh()
    x['mesh']['facets'][0]['independent_native_admission'] = True
    with pytest.raises(m.CrossSpaceHold, match='promoted'):
        receipt(mesh=x)
    x = mock_source_mesh()
    x['mesh']['facets'].pop()
    with pytest.raises(m.CrossSpaceHold, match='identity set'):
        receipt(mesh=x)
    with pytest.raises(m.CrossSpaceHold, match='not observed'):
        receipt(mesh={'mesh':{}})


def test_untrusted_sources_cannot_change_archive_candidate_count():
    x = fixture()
    x['archive_candidates_unchanged'] = 0
    with pytest.raises(m.CrossSpaceHold, match='count changed'):
        receipt(x)


def test_cli_read_only_receipt_reproducible_without_native_actions(tmp_path):
    result = subprocess.run([sys.executable, str(SCRIPT), '--repo', str(ROOT)],
                            check=False, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr + result.stdout
    r = json.loads(result.stdout)
    assert r == receipt()
    assert r['archive_delete_authorised'] is False
    assert r['side_effects_performed'] is False


def test_cli_drift_holds_and_writes_no_approval(tmp_path):
    folder = tmp_path/'cgx'/'review'
    folder.mkdir(parents=True)
    b = REG.read_bytes().replace(b'OPEN_REVIEW_ONLY', b'COMPLETED_NATIVE', 1)
    (folder/REG.name).write_bytes(b)
    run = subprocess.run([sys.executable,str(SCRIPT),'--repo',str(tmp_path)],
                         capture_output=True,text=True,timeout=20)
    assert run.returncode != 0
    r = json.loads(run.stdout)
    assert r['state'] == 'HOLD'
    assert r['native_admitted'] is False
    assert r['side_effects_performed'] is False


def test_current_execution_policy_does_not_rewrite_historical_review():
    contract = json.loads((ROOT / 'cgx/domain_templates/unispace_objectspace_current_contract.json').read_text(encoding='utf-8'))
    policy = contract['executionPolicy']
    historical = policy['historicalReviewCompatibility']
    assert (policy['normalRdcRemainingFloorPct'], policy['emergencyRdcRemainingFloorPct']) == (21, 20)
    assert historical['effectivePolicyRef'] == '#/executionPolicy'
    assert historical['historicalReviewRef']['normalRdcRemainingFloorPct'] == 25
    assert historical['historicalReviewRef']['emergencyRdcRemainingFloorPct'] == 24
    assert historical['preserveHistoricalBytes'] is True
    assert historical['requireFreshQuota'] is True
    assert historical['unknownQuota'] == 'HOLD'
    assert historical['normalEmergencySeparation'] is True
    assert historical['nativeEnforcementVerified'] is False


def test_science_crosswalk_cannot_promote_historical_physical_gates():
    contract = json.loads((ROOT / 'cgx/domain_templates/unispace_objectspace_current_contract.json').read_text(encoding='utf-8'))
    science = contract['crossGrex']['scientificAdmission']
    physical_ids = [row['id'] for row in fixture()['task_groups'] if row['space'] == 'PrintSpace' and row['id'].startswith('PHYS-')]
    assert science['existingRoot'] == contract['parent'] == m.ROOT
    assert science['gateRegister']['printspaceGateIds'] == physical_ids
    assert len(physical_ids) == 5
    assert science['classification']['visualPreset'] == 'VISUAL_PRESET_ONLY'
    assert science['classification']['synthetic'] != science['classification']['measurement']
    assert science['codec']['t173'] == 'CANDIDATE_REVERSIBLE_CODEC_NOT_PHYSICS_PROOF'
    assert science['codec']['t174'] == 'RESERVED_NONMINTABLE'
    assert science['sourceOccurrenceAclRequired'] is True
    assert science['gateClosureClaimed'] is False
    assert science['nativeAdmission'] is False
    assert science['physicalQualification']['meshPassIsNotMachineAuthority'] is True
    assert science['physicalQualification']['simulationPassIsNotMeasurement'] is True
    assert science['physicalQualification']['visualPresetIsNotMeteorology'] is True
    assert science['physicalQualification']['physicalActuationAuthorised'] is False
    assert all(value is False for value in contract['release'].values())
