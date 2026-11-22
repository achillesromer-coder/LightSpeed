"""Pre-DBR proposals are non-executing even when all syntactic checks pass."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "cgx/manufacturing/printspace_pre_dbr_archive_register_v0_1.json"
SOURCE = ROOT / "scripts/validate_printspace_pre_dbr.py"
spec = importlib.util.spec_from_file_location("printspace_pre_dbr", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def proposal() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_full_registry_stays_non_executing_and_reversible():
    report = module.validate_register(proposal())
    assert report["status"] == "PASS_REGISTER_INVARIANTS_ONLY"
    assert (report["candidate_count"], report["protected_count"]) == (3, 41)
    assert report["archive_executions"] == report["deletions"] == report["dbr_mutations"] == 0
    assert report["real_source_or_approval_reverified"] is False


@pytest.mark.parametrize("field", [
    "archive_execution_authorised",
    "delete_execution_authorised",
    "overwrite_execution_authorised",
    "dbr_finalised",
    "owner_approved",
    "receipts_synthetic",
])
def test_any_authority_escalation_fails(field):
    row = proposal()
    row["invariant_policy"][field] = True
    with pytest.raises(module.RegisterHold):
        module.validate_register(row)


def test_pre_dbr_is_never_approved_real_receipt():
    row = proposal()
    row["candidates"][0]["acknowledgement_receipt"] = "made-up-receipt"
    with pytest.raises(module.RegisterHold):
        module.validate_register(row)


@pytest.mark.parametrize("field", ["archive_allowed_now", "deletion_allowed_now"])
def test_candidate_move_or_delete_is_prohibited(field):
    row = proposal()
    row["candidates"][0][field] = True
    with pytest.raises(module.RegisterHold):
        module.validate_register(row)


def test_duplicate_candidate_id_holds():
    row = proposal()
    row["candidates"][1]["id"] = row["candidates"][0]["id"]
    with pytest.raises(module.RegisterHold):
        module.validate_register(row)


def test_missing_source_hash_holds():
    row = proposal()
    row["candidates"][0]["source"]["git_blob_sha1"] = "0" * 10
    with pytest.raises(module.RegisterHold):
        module.validate_register(row)


def test_unverified_distinct_ci_artifact_must_be_retained():
    row = proposal()
    row["candidates"][2]["disposition"] = "READY_FOR_ACHILLES_ARCHIVE_REVIEW"
    with pytest.raises(module.RegisterHold):
        module.validate_register(row)


def test_candidate_cannot_target_protected_canonical_code():
    row = proposal()
    row["candidates"][0]["source"]["path"] = "cgx/manufacturing/review_gate.py"
    with pytest.raises(module.RegisterHold):
        module.validate_register(row)


def test_material_contract_cannot_be_dropped_from_protection():
    row = proposal()
    row["protected_active"] = [
        x for x in row["protected_active"]
        if x.get("path") != "cgx/component_atlas/pc01_printceptor_operational_contract_v0_1.json"
    ]
    with pytest.raises(module.RegisterHold):
        module.validate_register(row)


def test_missing_human_review_gate_fails():
    row = proposal()
    row["archive_review_gates"].remove("ACHILLES_REVIEW_RECEIPT")
    with pytest.raises(module.RegisterHold):
        module.validate_register(row)


def test_no_false_byte_equivalence():
    row = proposal()
    row["candidates"][0]["unique_content_proven_identical"] = True
    with pytest.raises(module.RegisterHold):
        module.validate_register(row)


def test_no_unknown_source_without_legal_provenance():
    row = proposal()
    row["candidates"][0]["source"]["type"] = "local_deleted_unverified"
    with pytest.raises(module.RegisterHold):
        module.validate_register(row)


def test_public_archive_gate_never_applies_to_protected_source():
    row = proposal()
    row["protected_active"][0]["disposition"] = "READY_FOR_ACHILLES_ARCHIVE_REVIEW"
    with pytest.raises(module.RegisterHold):
        module.validate_register(row)


def test_stale_current_review_gate_git_blob_is_rejected():
    row = proposal()
    for protected in row["protected_active"]:
        if protected.get("path") == "cgx/manufacturing/review_gate.py":
            protected["git_blob_sha1"] = "0" * 40
            break
    else:
        raise AssertionError("current review gate is not protected")
    with pytest.raises(module.RegisterHold, match="stale protected active Git blob"):
        module.validate_register(row)
