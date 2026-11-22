"""Node R0 batch runtime checks in the existing bounded Python regression runner.

The full three-role Ed25519 cross-sweep runs in LightSpeed GO's Vitest; this
suite verifies direct offline integration, schema, limits and safety ceilings
without npm, production secrets, host network or machine access.
"""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _js(script):
    if not shutil.which("node"):
        pytest.skip("Node unavailable; full signature tests run in LightSpeed GO CI")
    r = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT,
                       capture_output=True, text=True, timeout=20, check=False)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_direct_import_schema_budget_and_no_host_access():
    out = _js("""
import {SCHEMA,MAX_CASES,reviewPrintspaceR0Batch as run} from './apps/lightspeed-go/src/printspaceR0BatchSweep.mjs';
const a=run({schema:SCHEMA,cases:[],known_consumed_nonce_sha256:[]});
const b=run({schema:SCHEMA,cases:[{}],known_consumed_nonce_sha256:[]});
console.log(JSON.stringify({schema:SCHEMA,limit:MAX_CASES,empty:a,malformed:b}));
""")
    assert out['limit'] == 512
    assert out['empty']['state'] == 'HOLD'
    assert out['malformed']['state'] == 'BATCH_DIGITAL_REVIEW_ONLY'
    assert out['malformed']['invalid_count'] == 1
    for name in ('empty', 'malformed'):
        assert out[name]['native_admitted'] is False
        assert out[name]['challenge_consumption_recorded'] is False
        assert out[name]['machine_authorised'] is False
        assert out[name]['commercial_release_authorised'] is False


def test_untrusted_prior_nonce_hints_never_grant_admission():
    out = _js("""
import {SCHEMA,reviewPrintspaceR0Batch as run,replayPrintspaceR0Batch as back} from './apps/lightspeed-go/src/printspaceR0BatchSweep.mjs';
const input={schema:SCHEMA,cases:[{request:{challenge:{nonce:'a'.repeat(64)}},trust_pins:{},clock_seconds:1800000000}],known_consumed_nonce_sha256:[]};
const a=run(input),b=back(a,input),c=back({...a,machine_authorised:true},input);
console.log(JSON.stringify({a,b,c}));
""")
    assert out['a']['invalid_count'] == 1
    assert out['a']['review_valid_count'] == 0
    assert out['a']['historical_hints_independently_authenticated'] is False
    assert out['b']['state'] == 'PASS_DIGITAL_ONLY'
    assert out['c']['state'] == 'HOLD'


def test_synthetic_bulk_size_513_holds_and_does_not_run_verifier():
    out = _js("""
import {SCHEMA,MAX_CASES,reviewPrintspaceR0Batch as run} from './apps/lightspeed-go/src/printspaceR0BatchSweep.mjs';
const r=run({schema:SCHEMA,cases:Array(MAX_CASES+1).fill({}),known_consumed_nonce_sha256:[]});
console.log(JSON.stringify(r));
""")
    assert out['state'] == 'HOLD'
    assert out['hold_code'] == 'BATCH_SIZE_EXCEEDED'
    assert out['case_count'] == 0
    assert out['machine_authorised'] is False