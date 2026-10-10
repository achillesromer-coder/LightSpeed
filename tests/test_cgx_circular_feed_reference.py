from __future__ import annotations

import json
from pathlib import Path

import pytest

from cgx.manufacturing.circular_feed import (
    CircularFeedInputError,
    compile_circular_feed_reference_packet,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "cgx" / "manufacturing" / "circular_feed_reference_control_v0_1.json").read_text(
        encoding="utf-8"
    )
)


def base_spec() -> dict:
    return {
        "packet_id": "UTP119-TEST-001",
        "recovered": {
            "lot_id": "RPET-LOT-001",
            "source_ref": "source:rpet:test",
            "polymer_class": "PET",
            "identity_evidence_ref": "evidence:rpet:identity",
            "sort_contamination_record_ref": "evidence:rpet:sort",
        },
        "control": {
            "lot_id": "VPET-LOT-001",
            "source_ref": "source:vpet:test",
            "polymer_class": "PET",
            "identity_evidence_ref": "evidence:vpet:identity",
        },
        "process": {
            "decontamination_sop_ref": "sop:test-only",
            "drying_condition_ref": "condition:dry:test",
            "coupon_fabrication_route_ref": "process:paired:test",
            "conditioning_ref": "condition:paired:test",
        },
        "coupon": {
            "geometry_ref": "geometry:paired:test",
            "geometry_hash": "sha256:test-geometry",
        },
        "tests": [
            {
                "test_id": "TENSILE",
                "method_ref": "method:test:tensile",
                "units": "MPa",
                "comparison_mode": "RATIO",
                "test_conditions_ref": "conditions:test:tensile",
                "required": True,
            }
        ],
    }


def test_utp119_contract_is_owner_bound_and_physical_not_run() -> None:
    assert CONTRACT["artifact_id"] == "UTP-119"
    assert CONTRACT["owner"]["owner_row"] == 70
    assert CONTRACT["physical_boundary"]["physical_execution"] is False
    assert CONTRACT["comparison_rules"]["thresholds"].startswith("No default")


def test_binding_complete_but_unmeasured_packet_holds_measurements() -> None:
    packet = compile_circular_feed_reference_packet(base_spec())
    assert packet["disposition"] == "HOLD_MEASUREMENTS"
    assert packet["missing_bindings"] == []
    assert packet["missing_measurements"] == ["TENSILE"]
    assert packet["material_qualified"] is False


def test_measured_pair_without_owner_threshold_requires_review() -> None:
    spec = base_spec()
    spec["tests"][0].update({"recovered_value": 42.0, "control_value": 50.0, "uncertainty": 1.0})
    packet = compile_circular_feed_reference_packet(spec)
    assert packet["disposition"] == "MEASURED_REVIEW_REQUIRED"
    assert packet["comparisons"][0]["retention_ratio"] == pytest.approx(0.84)
    assert packet["owner_thresholds_missing"] == ["TENSILE"]


def test_owner_bound_threshold_can_reach_review_or_reject_but_never_auto_qualify() -> None:
    spec = base_spec()
    spec["tests"][0].update(
        {
            "recovered_value": 42.0,
            "control_value": 50.0,
            "acceptance": {"min_retention_ratio": 0.8},
        }
    )
    packet = compile_circular_feed_reference_packet(spec)
    assert packet["disposition"] == "READY_FOR_OWNER_REVIEW"
    assert packet["material_qualified"] is False
    assert packet["printer_admission_authorized"] is False

    spec["tests"][0]["acceptance"] = {"min_retention_ratio": 0.9}
    rejected = compile_circular_feed_reference_packet(spec)
    assert rejected["disposition"] == "REJECT_OR_REPROCESS"
    assert rejected["failed_tests"] == ["TENSILE"]


def test_mismatched_polymer_or_geometry_fails_closed() -> None:
    spec = base_spec()
    spec["control"]["polymer_class"] = "PETG"
    with pytest.raises(CircularFeedInputError):
        compile_circular_feed_reference_packet(spec)

    spec = base_spec()
    spec["recovered_coupon_geometry_hash"] = "sha256:a"
    spec["control_coupon_geometry_hash"] = "sha256:b"
    with pytest.raises(CircularFeedInputError):
        compile_circular_feed_reference_packet(spec)


def test_zero_control_ratio_is_rejected_not_silently_divided() -> None:
    spec = base_spec()
    spec["tests"][0].update({"recovered_value": 1.0, "control_value": 0.0})
    with pytest.raises(CircularFeedInputError):
        compile_circular_feed_reference_packet(spec)
