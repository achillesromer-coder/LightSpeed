"""Hosted session status must never become native/peer/DBR authority."""
from __future__ import annotations

import copy
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

import pytest

from tools.cgx_unispace_native_acceptance_preflight import (
    NativeAcceptanceHold, assess, _gate_set,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "cgx/review/unispace_crossspace_gate_register_v0_1.json"


def gates():
    return json.loads(REGISTER.read_text("utf-8"))


def handshake():
    # Synthetic, deliberately public-safe. No token/session or private bytes.
    return {
        "schema": "cgx.lightspeed-go.handshake/1",
        "profile": "LOAD.Lite",
        "parent": "cgx:root:cognigrex",
        "surface": "lightspeed-go-uos",
        "identity": {"provider":"ChatGPT", "scope":"site-user", "authenticated":True},
        "capabilities":{
            "filespace":"hosted","dataspace":"hosted",
            "native":"held","peer":"unverified",
        },
        "authority":{
            "nativeAdmitted":False,"executionAuthorized":False,
            "canonicalWrite":False,"authorityTransfer":False,
        },
        "desktop":{"state":"stale","reportedAt":"2026-10-13T13:10:34.846Z"},
    }


def test_hosted_interface_is_not_native_even_when_authenticated():
    result = assess(gates(), handshake())
    assert result["root"] == "cgx:root:cognigrex"
    assert result["state"] == "NATIVE_AND_PUBLIC_RELEASE_HELD"
    assert result["original_gate_count"] == 51
    assert {"US-01","IM-01","FS-01","DS-02"} <= set(
        result["zero_dependency_review_gates"])
    assert result["source_observation"]["hosted_session_authenticated_claim"] is True
    assert result["source_observation"]["native_admitted_claim"] is False
    for key in ("native_admitted", "independent_native_signature_verified",
                "canonical_write_approved", "production_deploy_authorized",
                "model_training_executed", "mint_authorized",
                "peer_recovery_verified"):
        assert result[key] is False


def test_reproducible_receipt_and_no_source_mutation():
    register, hosted = gates(), handshake()
    before = copy.deepcopy((register, hosted))
    a = assess(register, hosted)
    b = assess(register, hosted)
    assert a["review_sha256"] == b["review_sha256"]
    assert (register, hosted) == before
    assert a["source_gate_registry_mutated"] is False
    assert a["priority_sequence"][0]["id"] == "US-01"


def test_forged_hosted_native_flag_never_satisfies_external_signer():
    hosted = handshake()
    hosted["authority"] = {key:True for key in hosted["authority"]}
    hosted["capabilities"]["native"] = "hosted"
    hosted["capabilities"]["peer"] = "hosted"
    result = assess(gates(), hosted)
    assert result["source_observation"]["native_admitted_claim"] is True
    assert result["native_admitted"] is False
    assert result["independent_native_signature_verified"] is False
    assert result["peer_recovery_verified"] is False


def test_unverified_anonymous_hosted_session_stays_held():
    hosted = handshake()
    hosted["identity"]["authenticated"] = False
    hosted["desktop"]["state"] = "unknown"
    result = assess(gates(), hosted)
    assert result["source_observation"]["hosted_session_authenticated_claim"] is False
    assert result["state"] == "NATIVE_AND_PUBLIC_RELEASE_HELD"


@pytest.mark.parametrize("bad", [
    {"schema":"unknown"},
    {"profile":"LOAD.Lite","parent":"cgx:root:other"},
])
def test_malformed_or_foreign_hosted_reports_fail_closed(bad):
    with pytest.raises(NativeAcceptanceHold):
        assess(gates(), bad)


def test_authority_and_desktop_fields_must_be_typed():
    for path, value in [
        (("authority","canonicalWrite"),"yes"),
        (("authority","nativeAdmitted"),None),
        (("identity","authenticated"),1),
        (("desktop","state"),{}),
        (("identity","scope"),""),
    ]:
        hosted=handshake()
        hosted[path[0]][path[1]]=value
        with pytest.raises(NativeAcceptanceHold):
            assess(gates(), hosted)


def test_original_51_gate_register_has_no_inferred_permissions():
    source=gates()
    keyed=_gate_set(source)
    assert len(keyed)==51
    assert all(x["state"]=="OPEN_REVIEW_ONLY" for x in keyed.values())
    assert all(x["effectful_action_authorised"] is False for x in keyed.values())
    assert all(x["owner_approval_observed"] is False for x in keyed.values())


@pytest.mark.parametrize("modifier", [
    lambda x: x.update(source_count=50),
    lambda x: x["task_groups"].pop(),
    lambda x: x["task_groups"][0].update(state="ADMITTED"),
    lambda x: x["task_groups"][0].update(effectful_action_authorised=True),
    lambda x: x["task_groups"][0].update(owner_approval_observed=True),
    lambda x: x["task_groups"][0].update(id="NOT A GATE"),
])
def test_gate_state_or_authority_tampering_refused(modifier):
    source=gates()
    modifier(source)
    with pytest.raises(NativeAcceptanceHold):
        assess(source, handshake())


def test_cycles_and_unresolved_dependencies_hold():
    source=gates()
    source["task_groups"][0]["proposed_dependencies"]=["SW-01"]
    with pytest.raises(NativeAcceptanceHold):
        assess(source, handshake())
    source=gates()
    source["task_groups"][0]["proposed_dependencies"]=["BAD-99"]
    with pytest.raises(NativeAcceptanceHold):
        assess(source, handshake())


def test_single_root_does_not_infer_private_source_or_model_training():
    result=assess(gates(), handshake())
    assert result["source_observation"]["independent_peer_verified"] is False
    assert result["priority_sequence"][0]["status"]=="OPEN_REQUIRES_INDEPENDENT_NATIVE_EVIDENCE"
    assert result["model_training_executed"] is False


def runtime_plan(*, now=None):
    timestamp = now or datetime(2026, 11, 23, 6, 18, tzinfo=UTC)
    return {
        "schema": "LIGHTSPEED-LIVE-RUNTIME-RECONCILIATION/0.1",
        "action": "plan",
        "generated_utc": timestamp.isoformat(),
        "git": {
            "branch": "ops/canonical-queue-index-20261115",
            "head": "a" * 40,
            "origin_main": "b" * 40,
            "clean": False,
        },
        "tracked_mapping_count": 757,
        "changed_mapping_count": 60,
        "open_service_ports": [4173, 8080, 8765],
        "deployment_readiness": {
            "status": "HOLD",
            "blockers": [
                "REVIEW_BRANCH_NOT_ACCEPTED_MAIN",
                "MAIN_NOT_ALIGNED_WITH_ORIGIN",
                "UNCOMMITTED_OR_UNTRACKED_SOURCE",
                "MANAGED_SERVICES_ACTIVE",
            ],
            "owner_approval_recorded": False,
            "services_were_stopped": False,
            "backup_verified": False,
            "runtime_installed": False,
            "native_mint_authorized": False,
            "data_space_network_mint_authorized": False,
        },
    }


def test_bouwerbase_style_read_only_plan_never_authorizes_install():
    stamp = datetime(2026, 11, 23, 6, 18, tzinfo=UTC)
    result = assess(gates(), handshake(), runtime_plan=runtime_plan(now=stamp),
                    now=stamp + timedelta(minutes=1))
    view = result["native_host_read_only_plan"]
    assert view["kind"] == "UNSIGNED_READ_ONLY_LOCAL_PLAN"
    assert view["fresh_within_15_minutes"] is True
    assert view["local_checkout_clean"] is False
    assert view["local_checkout_on_main"] is False
    assert view["local_checkout_matches_origin_main"] is False
    assert view["tracked_mapping_count"] == 757
    assert view["changed_mapping_count"] == 60
    assert view["active_managed_ports_count"] == 3
    assert len(view["deployment_blockers"]) == 4
    assert result["native_admitted"] is False
    assert view["automatic_install_permitted"] is False
    assert view["signed_dbr_readback_verified"] is False
    assert "D:\\LightSpeed" not in str(view)


def test_missing_local_plan_does_not_invent_local_current_state():
    result = assess(gates(), handshake())
    assert result["native_host_read_only_plan"] is None
    assert result["native_admitted"] is False


def test_old_local_snapshot_is_identified_as_stale():
    stamp = datetime(2026, 11, 23, 6, 18, tzinfo=UTC)
    result = assess(gates(), handshake(), runtime_plan=runtime_plan(now=stamp),
                    now=stamp + timedelta(minutes=20))
    assert result["native_host_read_only_plan"]["fresh_within_15_minutes"] is False
    assert result["native_host_read_only_plan"]["deployment_blockers"][-1] == "LOCAL_PLAN_STALE"


def test_future_host_plan_is_not_fresh():
    stamp = datetime(2026, 11, 23, 6, 18, tzinfo=UTC)
    result = assess(gates(), handshake(), runtime_plan=runtime_plan(now=stamp),
                    now=stamp - timedelta(minutes=3))
    assert result["native_host_read_only_plan"]["fresh_within_15_minutes"] is False


@pytest.mark.parametrize("mutator", [
    lambda p: p["deployment_readiness"]["blockers"].clear(),
    lambda p: p["deployment_readiness"].update(status="ELIGIBLE_FOR_OWNER_CONFIRMED_APPLY"),
    lambda p: p["deployment_readiness"].update(runtime_installed=True),
    lambda p: p["deployment_readiness"].update(owner_approval_recorded=True),
    lambda p: p["git"].update(clean="yes"),
    lambda p: p["git"].update(head="g"*40),
    lambda p: p["open_service_ports"].append(8443),
    lambda p: p["open_service_ports"].append(8765),
    lambda p: p.update(changed_mapping_count=900),
    lambda p: p.update(action="apply"),
])
def test_inconsistent_or_effectful_native_plan_is_rejected(mutator):
    stamp = datetime(2026, 11, 23, 6, 18, tzinfo=UTC)
    p = runtime_plan(now=stamp)
    mutator(p)
    with pytest.raises(NativeAcceptanceHold):
        assess(gates(), handshake(), runtime_plan=p, now=stamp)


def test_even_perfect_fake_local_plan_cannot_promote_native_or_peer():
    p = runtime_plan()
    p["git"]["branch"]="main"
    p["git"]["origin_main"]=p["git"]["head"]
    p["git"]["clean"]=True
    p["open_service_ports"]=[]
    p["changed_mapping_count"]=0
    p["deployment_readiness"]["blockers"]=[]
    p["deployment_readiness"]["status"]="ELIGIBLE_FOR_OWNER_CONFIRMED_APPLY"
    stamp = datetime(2026, 11, 23, 6, 18, tzinfo=UTC)
    result = assess(gates(), handshake(), runtime_plan=p, now=stamp)
    assert result["native_host_read_only_plan"]["deployment_blockers"] == []
    assert result["native_admitted"] is False
    assert result["production_deploy_authorized"] is False
    assert result["peer_recovery_verified"] is False
    assert result["native_host_read_only_plan"]["automatic_install_permitted"] is False
