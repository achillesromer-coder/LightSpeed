"""Side-effect-free contract tests for TASK-084 Cognigrex progression adapter.

These tests use only in-memory fixtures. They do not touch Z Direct, Drive,
local queues, network services, or canonical state.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ADAPTER_PATH = (
    PROJECT_ROOT
    / "Z Axis"
    / "Z+2_Neo"
    / "components"
    / "cognigrex_progression_adapter.py"
)
_spec = importlib.util.spec_from_file_location("cognigrex_progression_adapter", ADAPTER_PATH)
assert _spec and _spec.loader
adapter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adapter)


SCHEMA = {
    "registries": {
        "known_unknowns": {
            "required_fields": [
                "known_unknown_id", "technology_or_domain", "question_or_variable",
                "dependencies", "resolution_method", "falsifiable_next_step",
                "evidence_state", "source_ids", "created_at", "updated_at", "status",
            ],
            "status_enum": [
                "OPEN", "AWAITING_SOURCE", "AWAITING_RECEIPT", "AWAITING_OWNER",
                "RESOLVED_EVIDENCE", "SUPERSEDED",
            ],
        },
        "research_proposals": {
            "required_fields": [
                "proposal_id", "originating_known_unknown_ids", "hypothesis_or_question",
                "completed_current_task_comparison", "expected_information_gain",
                "priority_class", "priority_features", "falsifiable_method",
                "safety_or_acceptance_gates", "duplication_check", "evidence_state", "status",
            ],
            "status_enum": ["PROPOSED", "REVIEWED", "QUEUED", "HELD", "REJECTED", "SUPERSEDED"],
        },
        "reanalysis_events": {
            "required_fields": [
                "reanalysis_id", "trigger_evidence_ids", "affected_known_unknown_ids",
                "affected_proposal_ids", "affected_conclusion_or_task_ids", "materiality_reason",
                "prior_state_refs", "required_reanalysis", "status", "supersession_receipts",
            ],
            "status_enum": ["TRIGGERED", "IN_REVIEW", "REANALYSED", "NO_MATERIAL_CHANGE", "SUPERSEDED"],
        },
    },
    "shared_evidence_controls": {
        "outcome_classification_enum": [
            "VALID_POSITIVE", "VALID_NULL", "VALID_NEGATIVE", "OUTLIER", "INCONCLUSIVE",
            "INVALID_HARNESS", "INVALID_INPUT", "MODEL_LIMITATION", "SUPERSEDED",
        ]
    },
}


def ku(**updates):
    record = {
        "known_unknown_id": "KU-SOLARHULL-001",
        "technology_or_domain": "SOLARHULL",
        "question_or_variable": "Measured coupon efficiency?",
        "dependencies": [],
        "resolution_method": "calibrated coupon test",
        "falsifiable_next_step": "run coupon protocol",
        "evidence_state": "METHOD_READY",
        "source_ids": ["SRC-093"],
        "created_at": "2026-08-16T00:00:00Z",
        "updated_at": "2026-08-16T00:00:00Z",
        "status": "OPEN",
    }
    record.update(updates)
    return record


def rp(**updates):
    record = {
        "proposal_id": "RP-SOLARHULL-001",
        "originating_known_unknown_ids": ["KU-SOLARHULL-001"],
        "hypothesis_or_question": "Does the coupon meet its bounded test criterion?",
        "completed_current_task_comparison": "No duplicate active task",
        "expected_information_gain": "HIGH",
        "priority_class": "HIGH",
        "priority_features": {"dependency_unlock": "HIGH"},
        "falsifiable_method": "calibrated coupon test",
        "safety_or_acceptance_gates": ["lab approval"],
        "duplication_check": "CLEAR",
        "evidence_state": "PROPOSED_ONLY",
        "status": "PROPOSED",
    }
    record.update(updates)
    return record


def ra(**updates):
    record = {
        "reanalysis_id": "RA-SOLARHULL-001",
        "trigger_evidence_ids": ["EVID-001"],
        "affected_known_unknown_ids": ["KU-SOLARHULL-001"],
        "affected_proposal_ids": ["RP-SOLARHULL-001"],
        "affected_conclusion_or_task_ids": ["TASK-084"],
        "materiality_reason": "new attributable coupon evidence",
        "prior_state_refs": ["STATE-001"],
        "required_reanalysis": ["recompute bounded conclusion"],
        "status": "TRIGGERED",
        "supersession_receipts": [],
    }
    record.update(updates)
    return record


def test_valid_ku_record():
    assert adapter.validate_record("known_unknowns", ku(), SCHEMA).valid


def test_valid_rp_record():
    assert adapter.validate_record("research_proposals", rp(), SCHEMA).valid


def test_valid_ra_record():
    assert adapter.validate_record("reanalysis_events", ra(), SCHEMA).valid


def test_reject_missing_required_field():
    result = adapter.validate_record("known_unknowns", ku(question_or_variable=""), SCHEMA)
    assert not result.valid
    assert any(issue.code == "MISSING_REQUIRED_FIELD" for issue in result.issues)


def test_reject_illegal_status_transition():
    result = adapter.validate_status_transition(
        "known_unknowns", "RESOLVED_EVIDENCE", "OPEN", SCHEMA
    )
    assert not result.valid
    assert any(issue.code == "TERMINAL_STATE_REOPEN_BLOCKED" for issue in result.issues)


def test_reject_resolved_evidence_without_receipt():
    result = adapter.validate_record(
        "known_unknowns", ku(status="RESOLVED_EVIDENCE"), SCHEMA
    )
    assert not result.valid
    assert any(issue.code == "MISSING_CLOSURE_RECEIPT" for issue in result.issues)


def test_accept_resolved_evidence_with_receipt():
    result = adapter.validate_record(
        "known_unknowns",
        ku(status="RESOLVED_EVIDENCE", closure_receipts=["RECEIPT-001"]),
        SCHEMA,
    )
    assert result.valid


def test_detect_duplicate_stable_id():
    assert adapter.detect_duplicate_ids("known_unknowns", [ku(), ku()]) == ["KU-SOLARHULL-001"]


def test_preserve_invalid_harness_vs_valid_null_boundary():
    assert adapter.preserve_null_boundary("INVALID_HARNESS") == "INVALID_HARNESS"
    assert adapter.preserve_null_boundary("INVALID_INPUT") == "INVALID_INPUT"
    assert adapter.preserve_null_boundary("MODEL_LIMITATION") == "MODEL_LIMITATION"
    assert adapter.preserve_null_boundary("VALID_NULL") == "VALID_NULL"


def test_preserve_prior_state_on_reanalysis():
    result = adapter.validate_record("reanalysis_events", ra(prior_state_refs=[]), SCHEMA)
    assert not result.valid
    assert any(issue.code == "MISSING_REQUIRED_FIELD" or issue.code == "MISSING_PRIOR_STATE" for issue in result.issues)
