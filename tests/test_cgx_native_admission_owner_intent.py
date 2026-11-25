"""Owner instruction authorises a bounded test lane, not self-issued native authority."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "cgx/review/cgx_native_admission_owner_intent_20261123.json"
EXPECTED_GATES = {
    "host_owner_identity_independently_verified",
    "peer_independent_review_verified",
    "achilles_assurance_receipt_verified",
    "native_lease_signature_verified",
    "file_scope_acl_verified",
    "native_dbr_readback_verified",
    "independent_cold_recovery_verified",
    "deployed_runtime_exact_revision_verified",
}
EXPECTED_SEQUENCE = ("T0", "T1", "T2", "T3", "T4", "T5", "T6")


def source():
    return json.loads(SOURCE.read_text("utf-8"))


def check(data):
    assert data["schema"] == "CGX-NATIVE-ADMISSION-OWNER-INTENT/0.1"
    assert data["root"] == "cgx:root:cognigrex"
    assert data["record_class"] == "CHAT_RECORDED_OWNER_INTENT_NOT_NATIVE_SIGNED_LEASE"
    decision = data["instructions"]
    assert decision["native_admission"].startswith("OWNER_PERMITTED_CONDITIONAL")
    assert decision["canonical_writes"].startswith("OWNER_PERMITTED_CONDITIONAL")
    assert decision["onchain_mint"].startswith("HELD_SEPARATE")
    assert data["source_state"] == "OWNER_INTENT_PRESERVED_NATIVE_ACTIONS_HELD_UNTIL_WITNESSED"
    assert data["observations"]["local_checkout_dirty_count"] >= 1
    assert data["observations"]["main_merged"] is False
    checks = data["native_authority"]
    assert EXPECTED_GATES <= set(checks)
    assert all(checks[k] is False for k in EXPECTED_GATES)
    assert checks["current_native_execution_allowed"] is False
    assert checks["current_canonical_write_allowed"] is False
    assert checks["current_mint_allowed"] is False
    stages = data["bounded_test_chain"]
    assert tuple(x["id"] for x in stages) == EXPECTED_SEQUENCE
    assert all(x["passed_on_current_machine"] is False for x in stages)
    assert stages[-1]["effect"] == "OFFCHAIN_ONLY"
    forbidden = set(data["constraints"])
    assert {"NO_SELF_SIGNING_AGENT_APPROVAL", "NO_OVERWRITE_DIRTY_LOCAL_SOURCE",
            "NO_RESTART_WITHOUT_OWNER_STANDBY", "NO_MINT_BY_SOURCE_OR_CI_PASS"} <= forbidden


def test_founding_instruction_preserved_without_mint():
    check(source())


@pytest.mark.parametrize("field", sorted(EXPECTED_GATES | {
    "current_native_execution_allowed", "current_canonical_write_allowed",
    "current_mint_allowed",
}))
def test_claiming_native_authority_before_independent_proof_is_detected(field):
    data = source()
    data["native_authority"][field] = True
    with pytest.raises(AssertionError):
        check(data)


def test_attempt_to_self_mint_or_skip_peer_review_is_detected():
    data = source()
    data["instructions"]["onchain_mint"] = "APPROVED_TO_MINT_IMMEDIATELY"
    with pytest.raises(AssertionError):
        check(data)
    data = source()
    data["bounded_test_chain"] = [
        x for x in data["bounded_test_chain"] if x["id"] != "T3"
    ]
    with pytest.raises(AssertionError):
        check(data)


def test_cannot_claim_local_test_chain_executed_by_text():
    data = source()
    data["bounded_test_chain"][2]["passed_on_current_machine"] = True
    with pytest.raises(AssertionError):
        check(data)
