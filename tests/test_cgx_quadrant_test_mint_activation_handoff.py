"""Unsigned Windows test mint evidence stays below actual native admission."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.cgx_agent_quadrant_test_mint import QUADRANTS, ROOT, AUTHORITY

BASE=Path(__file__).resolve().parents[1]
SOURCE=BASE/"cgx/review/cgx_quadrant_test_mint_activation_handoff_20261123.json"
LANES={"CGX Achilles Römer","CGX Neo LightSpeed","CGX Athene Eco",
       "CGX Cognigrex Family","CGX UniSpace Product"}
FLOORS={"Merovingian","Trinity","Neo","Smith","Oracle","Morpheus","Architect","TheConstruct"}


def load():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def assert_valid(a):
    assert a["schema"]=="CGX-QUADRANT-TEST-MINT-ACTIVATION-HANDOFF/0.1"
    assert a["root"]==ROOT
    assert a["provenance"]=="EXACT_LOCAL_EXECUTION_AND_UNSIGNED_SOURCE_FIXTURE_READBACK"
    evidence=a["evidence"]
    assert evidence["source_revision_verified"] is True
    assert evidence["source_ci"]["success"]==evidence["source_ci"]["total"]==10
    assert evidence["source_ci"]["head"]==a["source_commit"]
    assert evidence["local_test_count"]==18 and evidence["local_test_failures"]==0
    assert evidence["minted_test_source_objects"]==9
    assert evidence["logical_quadrants"]==4
    assert len(evidence["manifest_sha256"])==64
    assert evidence["manifest_verified_idempotent"] is True
    assert evidence["native_signed"] is False
    assert evidence["live_agent_processes_started"]==0
    assert evidence["model_calls_executed"]==0
    assert evidence["production_db_writes"]==0
    assert evidence["chain_transactions"]==0
    actors=evidence["principal_preflights"]
    assert {x["name"] for x in actors}=={"Achilles","Neo","Athene"}
    assert all(x["decision"]=="CLEARED_FOR_AUTHORITY_GATE" for x in actors)
    assert all(x["execution_requested"] is False for x in actors)
    field=a["field"]
    assert field["frame"]=="SYNTHETIC_CARTESIAN_TEST_ONLY"
    assert set(field["quadrants"])=={"QI","QII","QIII","QIV"}
    assert field["kernel_namespace_isolation_verified"] is False
    assert field["separate_root_or_scheduler_created"] is False
    assert field["source_agent_model_selector_count"]==9
    assert field["existing_principal_count"]==3
    assert field["existing_floor_count"]==8
    policy=a["continuation_policy"]
    assert policy["only_use_existing_five_coordinators"] is True
    assert policy["one_local_model_session_at_a_time"] is True
    assert policy["no_self_approval_or_self_mint"] is True
    assert policy["no_automatic_autonomy_escalation"] is True
    assert policy["no_effectful_run_without_current_scoped_lease"] is True
    assert policy["max_parallel_model_jobs_before_signed_lease"]==0
    assert policy["max_parallel_effectful_local_jobs"]==0
    assert policy["recursive_self_revision"]=="PROPOSAL_ONLY_IN_EXISTING_GIT_PR"
    assert policy["chain_mint"]=="HELD_SEPARATE_ISSUER_WALLET_TRANSACTION"
    assert policy["production_release"]=="HELD"
    rows=a["queued_packets"]
    assert len(rows)==9 and len({r["id"] for r in rows})==9
    assert {r["selector"] for r in rows}==set(QUADRANTS)
    assert {r["quadrant"] for r in rows}=={"QI","QII","QIII","QIV"}
    for r in rows:
        assert r["quadrant"]==QUADRANTS[r["selector"]][0]
        assert r["existing_floor"] in FLOORS
        assert r["owner_lane"] in LANES
        assert r["state"]=="QUEUED_FOR_EXISTING_COORDINATOR_REVIEW_NOT_DISPATCHED"
        assert r["mint_fixture_result"]=="PASS_ISOLATED_TEST_MINT_SOURCE_ONLY"
        assert all(r[k] is False for k in ("autonomous_self_launch_allowed",
            "onchain_mint_allowed","physical_effects_allowed"))
        assert r["requires_current_owner_scoped_lease_before_live_execution"] is True
        assert r["requires_independent_assurance_before_native_promotion"] is True
    assert a["status"]=="TEST_SOURCE_MINT_COMPLETE_NON_EFFECTFUL_AGENT_ACTIVATION_QUEUED"
    assert all(v is False for v in AUTHORITY.values())


def test_exact_windows_receipt_and_queued_nine_paths():
    assert_valid(load())


@pytest.mark.parametrize("edit",[
    lambda a: a["evidence"].update(native_signed=True),
    lambda a: a["evidence"].update(live_agent_processes_started=9),
    lambda a: a["continuation_policy"].update(max_parallel_effectful_local_jobs=9),
    lambda a: a["continuation_policy"].update(no_automatic_autonomy_escalation=False),
    lambda a: a["field"].update(kernel_namespace_isolation_verified=True),
    lambda a: a["queued_packets"][0].update(autonomous_self_launch_allowed=True),
    lambda a: a["queued_packets"][0].update(state="EXECUTING_WITH_LEASE"),
    lambda a: a["queued_packets"][1].update(onchain_mint_allowed=True),
    lambda a: a["continuation_policy"].update(chain_mint="ALLOW"),
])
def test_unwitnessed_promotion_or_self_spawn_cannot_be_claimed(edit):
    a=load()
    edit(a)
    with pytest.raises(AssertionError):
        assert_valid(a)


def test_source_object_matches_one_root_not_arbitrary_relabel():
    a=load()
    assert a["root"]==ROOT
    assert a["source_script"]=="tools/cgx_agent_quadrant_test_mint.py"
    assert a["source_tests"]=="tests/test_cgx_agent_quadrant_test_mint.py"
    assert a["source_commit"]=="9bd479250ce946f5c50b2fd6260a582edb2e0843"
