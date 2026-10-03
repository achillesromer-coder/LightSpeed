import hashlib
import json
import sys
from pathlib import Path

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lightspeed_runtime.local_floor_runner import (
    LocalFloorRunnerError, verified_source_context, validate_grounded_response,
)
from lightspeed_runtime import cognigrex_supervisor as supervisor
from test_cognigrex_supervisor import write_contract


def bound_source(tmp_path):
    path = tmp_path / 'evidence.txt'
    path.write_text('AEI-035 remains unresolved. A model proposal is not acceptance.', encoding='utf-8')
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def test_changed_source_and_missing_required_binding_fail(tmp_path):
    binding = bound_source(tmp_path)
    assert verified_source_context({'source_context': [binding]})[0]['excerpt'].startswith('AEI-035')
    Path(binding['path']).write_text('Altered')
    with pytest.raises(LocalFloorRunnerError, match='changed'):
        verified_source_context({'source_context': [binding]})
    with pytest.raises(LocalFloorRunnerError, match='required'):
        verified_source_context({'policy': {'require_source_context': True}})


def test_citation_checks_actual_excerpt_and_rejects_invented_quote(tmp_path):
    binding = bound_source(tmp_path)
    sources = verified_source_context({'source_context': [binding]})
    body = {'floor_summary': 'Unresolved', 'safe_artifact_route': 'approved', 'blocker': None,
            'citations': [{**binding, 'quote': 'AEI-035 remains unresolved.'}]}
    assert not validate_grounded_response({'response': json.dumps(body)}, 'approved', sources)
    body['citations'][0]['quote'] = 'AEI-035 is accepted.'
    assert validate_grounded_response({'response': json.dumps(body)}, 'approved', sources)


def test_handoff_and_snapshot_survive_latest_receipt_overwrite(tmp_path):
    contract_path = write_contract(tmp_path)
    seen = []
    latest = tmp_path / 'latest.json'
    def runner(**kwargs):
        seen.append(json.loads(Path(kwargs['contract_path']).read_text()))
        receipt = {'status': 'completed', 'receipt_id': kwargs['floor'], 'receipt_path': str(latest),
                   'response_contract': {'floor_summary': 'Preserve AEI-035 as unresolved', 'blocker': 'missing source'}}
        latest.write_text(json.dumps(receipt))
        return receipt
    receipt = supervisor.run_supervised_workflow('Inspect source evidence', contract_path=contract_path,
                                                 dry_run=False, runner=runner)
    assert seen[0]['workflow_handoffs'] == []
    assert seen[1]['workflow_handoffs'][0]['floor_summary'] == 'Preserve AEI-035 as unresolved'
    latest.write_text('{}')
    for row in receipt['floors']:
        path = Path(row['snapshot_path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['snapshot_sha256']
        assert json.loads(path.read_text())['receipt_id'] == row['floor']
    assert receipt['semantic_acceptance'] == 'requires_independent_review'
