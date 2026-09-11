"""Side-effect-free Cognigrex KU/RP/RA validation adapter.

TASK-084 review-gated implementation. This module validates in-memory records
against the Data progression registry schema. It performs no Drive writes,
Z-Direct submission, deployment, model execution, or evidence promotion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence


RECORD_TYPES = {
    "known_unknowns": ("known_unknown_id", "KU-"),
    "research_proposals": ("proposal_id", "RP-"),
    "reanalysis_events": ("reanalysis_id", "RA-"),
}

PHYSICAL_NULL = "VALID_NULL"
NON_PHYSICAL_NULL_CLASSES = {"INVALID_HARNESS", "INVALID_INPUT", "MODEL_LIMITATION"}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    record_type: str
    record_id: str = ""


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    issues: Sequence[ValidationIssue]


def _record_id(record_type: str, record: Mapping[str, Any]) -> str:
    id_field, _ = RECORD_TYPES[record_type]
    value = record.get(id_field, "")
    return str(value) if value is not None else ""


def _stable_id_valid(record_type: str, value: str) -> bool:
    _, prefix = RECORD_TYPES[record_type]
    # Canonical pattern is PREFIX-<technology_or_domain>-<sequence>.
    return bool(re.fullmatch(rf"{re.escape(prefix)}[^-\s]+(?:-[^-\s]+)*-\d+", value))


def validate_record(
    record_type: str,
    record: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> ValidationResult:
    """Validate one KU/RP/RA record without mutating any external state."""
    if record_type not in RECORD_TYPES:
        issue = ValidationIssue("UNKNOWN_RECORD_TYPE", record_type, record_type)
        return ValidationResult(False, (issue,))

    registry = schema.get("registries", {}).get(record_type, {})
    rid = _record_id(record_type, record)
    issues: List[ValidationIssue] = []

    for field in registry.get("required_fields", []):
        if field not in record or record[field] is None or record[field] == "":
            issues.append(ValidationIssue("MISSING_REQUIRED_FIELD", field, record_type, rid))

    if rid and not _stable_id_valid(record_type, rid):
        issues.append(ValidationIssue("INVALID_STABLE_ID", rid, record_type, rid))

    status = record.get("status")
    allowed_statuses = registry.get("status_enum", [])
    if status and allowed_statuses and status not in allowed_statuses:
        issues.append(ValidationIssue("INVALID_STATUS", str(status), record_type, rid))

    if record_type == "known_unknowns":
        if status == "RESOLVED_EVIDENCE" and not record.get("closure_receipts"):
            issues.append(ValidationIssue(
                "MISSING_CLOSURE_RECEIPT",
                "RESOLVED_EVIDENCE requires attributable receipt(s)",
                record_type,
                rid,
            ))
        if status == "SUPERSEDED" and not record.get("supersession_receipts"):
            issues.append(ValidationIssue(
                "MISSING_SUPERSESSION_RECEIPT",
                "SUPERSEDED requires supersession receipt(s)",
                record_type,
                rid,
            ))

    if record_type == "reanalysis_events":
        if not record.get("prior_state_refs"):
            issues.append(ValidationIssue(
                "MISSING_PRIOR_STATE",
                "Reanalysis must retain prior state references",
                record_type,
                rid,
            ))

    outcome = record.get("outcome_classification")
    allowed_outcomes = schema.get("shared_evidence_controls", {}).get(
        "outcome_classification_enum", []
    )
    if outcome and allowed_outcomes and outcome not in allowed_outcomes:
        issues.append(ValidationIssue("INVALID_OUTCOME_CLASS", str(outcome), record_type, rid))

    return ValidationResult(not issues, tuple(issues))


def detect_duplicate_ids(record_type: str, records: Iterable[Mapping[str, Any]]) -> List[str]:
    """Return duplicate stable IDs without modifying the input records."""
    if record_type not in RECORD_TYPES:
        raise ValueError(f"Unknown record type: {record_type}")
    seen = set()
    duplicates = set()
    for record in records:
        rid = _record_id(record_type, record)
        if not rid:
            continue
        if rid in seen:
            duplicates.add(rid)
        seen.add(rid)
    return sorted(duplicates)


def validate_status_transition(
    record_type: str,
    previous_status: str,
    next_status: str,
    schema: Mapping[str, Any],
) -> ValidationResult:
    """Validate status membership and conservative transition rules.

    Terminal evidence states cannot silently return to active states. A changed
    conclusion should instead create a reanalysis/supersession record so prior
    state remains attributable.
    """
    registry = schema.get("registries", {}).get(record_type, {})
    allowed = set(registry.get("status_enum", []))
    issues: List[ValidationIssue] = []
    if previous_status not in allowed or next_status not in allowed:
        issues.append(ValidationIssue(
            "INVALID_STATUS_TRANSITION",
            f"{previous_status}->{next_status}",
            record_type,
        ))
    terminal = {
        "known_unknowns": {"RESOLVED_EVIDENCE", "SUPERSEDED"},
        "research_proposals": {"REJECTED", "SUPERSEDED"},
        "reanalysis_events": {"REANALYSED", "NO_MATERIAL_CHANGE", "SUPERSEDED"},
    }.get(record_type, set())
    if previous_status in terminal and next_status != previous_status:
        issues.append(ValidationIssue(
            "TERMINAL_STATE_REOPEN_BLOCKED",
            "Create attributable reanalysis/supersession lineage instead of overwriting terminal state",
            record_type,
        ))
    return ValidationResult(not issues, tuple(issues))


def preserve_null_boundary(outcome_classification: str) -> str:
    """Return classification unchanged while enforcing the physical-null boundary."""
    if outcome_classification in NON_PHYSICAL_NULL_CLASSES:
        return outcome_classification
    if outcome_classification == PHYSICAL_NULL:
        return PHYSICAL_NULL
    return outcome_classification
