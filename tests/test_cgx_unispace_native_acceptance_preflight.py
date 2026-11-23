"""Hosted session status must never become native/peer/DBR authority."""
from __future__ import annotations

import copy
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
