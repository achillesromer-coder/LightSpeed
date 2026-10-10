from __future__ import annotations

from copy import deepcopy
from typing import Any

from .invariants import InvariantInputError, retention_ratio


class CircularFeedInputError(ValueError):
    pass


_BINDING_FIELDS = {
    "recovered": (
        "lot_id",
        "source_ref",
        "polymer_class",
        "identity_evidence_ref",
        "sort_contamination_record_ref",
    ),
    "control": (
        "lot_id",
        "source_ref",
        "polymer_class",
        "identity_evidence_ref",
    ),
    "process": (
        "decontamination_sop_ref",
        "drying_condition_ref",
        "coupon_fabrication_route_ref",
        "conditioning_ref",
    ),
    "coupon": ("geometry_ref", "geometry_hash"),
}
_TEST_FIELDS = ("test_id", "method_ref", "units", "comparison_mode", "test_conditions_ref")


def _missing_fields(record: dict[str, Any], fields: tuple[str, ...], prefix: str) -> list[str]:
    return [f"{prefix}.{field}" for field in fields if record.get(field) in (None, "", [])]


def _as_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CircularFeedInputError(f"{label} must be numeric when supplied")
    return float(value)


def _compare_test(test: dict[str, Any]) -> dict[str, Any]:
    result = {
        "test_id": test["test_id"],
        "method_ref": test["method_ref"],
        "units": test["units"],
        "comparison_mode": test["comparison_mode"],
        "test_conditions_ref": test["test_conditions_ref"],
        "required": bool(test.get("required", True)),
        "measurement_state": "MISSING",
        "acceptance_state": "NOT_EVALUATED",
    }
    recovered = test.get("recovered_value")
    control = test.get("control_value")
    if recovered is None or control is None:
        return result

    recovered_value = _as_number(recovered, f"{test['test_id']}.recovered_value")
    control_value = _as_number(control, f"{test['test_id']}.control_value")
    result["recovered_value"] = recovered_value
    result["control_value"] = control_value
    if test.get("uncertainty") is not None:
        result["uncertainty"] = _as_number(test["uncertainty"], f"{test['test_id']}.uncertainty")

    mode = str(test["comparison_mode"]).upper()
    if mode == "RATIO":
        try:
            result.update(retention_ratio(recovered_value=recovered_value, control_value=control_value))
        except InvariantInputError as exc:
            raise CircularFeedInputError(str(exc)) from exc
    elif mode == "ABSOLUTE_DIFFERENCE":
        result["absolute_difference"] = recovered_value - control_value
        result["absolute_difference_magnitude"] = abs(recovered_value - control_value)
    else:
        raise CircularFeedInputError(
            f"{test['test_id']}.comparison_mode must be RATIO or ABSOLUTE_DIFFERENCE"
        )
    result["measurement_state"] = "MEASURED_COMPARISON_AVAILABLE"

    acceptance = test.get("acceptance")
    if acceptance in (None, {}):
        result["acceptance_state"] = "OWNER_BOUND_NOT_SUPPLIED"
        return result
    if not isinstance(acceptance, dict):
        raise CircularFeedInputError(f"{test['test_id']}.acceptance must be an object")

    if mode == "RATIO":
        minimum = acceptance.get("min_retention_ratio")
        maximum = acceptance.get("max_retention_ratio")
        if minimum is None and maximum is None:
            raise CircularFeedInputError(
                f"{test['test_id']} ratio acceptance needs min_retention_ratio and/or max_retention_ratio"
            )
        value = result["retention_ratio"]
        passed = True
        if minimum is not None:
            passed = passed and value >= _as_number(minimum, f"{test['test_id']}.min_retention_ratio")
        if maximum is not None:
            passed = passed and value <= _as_number(maximum, f"{test['test_id']}.max_retention_ratio")
    else:
        maximum = acceptance.get("max_abs_delta")
        if maximum is None:
            raise CircularFeedInputError(
                f"{test['test_id']} difference acceptance needs max_abs_delta"
            )
        passed = result["absolute_difference_magnitude"] <= _as_number(
            maximum, f"{test['test_id']}.max_abs_delta"
        )

    result["acceptance_state"] = "PASS" if passed else "FAIL"
    result["acceptance"] = deepcopy(acceptance)
    return result


def compile_circular_feed_reference_packet(spec: dict[str, Any]) -> dict[str, Any]:
    """Compile the Drive-owned UTP-119 rPET/control plan into a fail-closed digital packet.

    This function never qualifies material or authorizes physical work. It only checks
    that paired evidence is structurally attributable and computes comparisons where
    measured recovered/control values are present.
    """
    if not isinstance(spec, dict):
        raise CircularFeedInputError("spec must be an object")

    packet_id = spec.get("packet_id")
    if not packet_id:
        raise CircularFeedInputError("packet_id is required")

    missing: list[str] = []
    records: dict[str, dict[str, Any]] = {}
    for key, fields in _BINDING_FIELDS.items():
        value = spec.get(key)
        if not isinstance(value, dict):
            value = {}
            missing.append(key)
        records[key] = value
        missing.extend(_missing_fields(value, fields, key))

    recovered_polymer = str(records["recovered"].get("polymer_class") or "").strip().upper()
    control_polymer = str(records["control"].get("polymer_class") or "").strip().upper()
    if recovered_polymer and control_polymer and recovered_polymer != control_polymer:
        raise CircularFeedInputError("recovered and control polymer_class must match")
    if recovered_polymer and recovered_polymer != "PET":
        raise CircularFeedInputError("UTP-119 first route is PET; other polymers need a separate owner route")

    tests = spec.get("tests")
    if not isinstance(tests, list) or not tests:
        missing.append("tests")
        tests = []

    compiled_tests: list[dict[str, Any]] = []
    for index, raw in enumerate(tests):
        if not isinstance(raw, dict):
            raise CircularFeedInputError(f"tests[{index}] must be an object")
        test_missing = _missing_fields(raw, _TEST_FIELDS, f"tests[{index}]")
        missing.extend(test_missing)
        if not test_missing:
            compiled_tests.append(_compare_test(raw))

    shared_geometry = records["coupon"].get("geometry_hash")
    recovered_geometry = spec.get("recovered_coupon_geometry_hash", shared_geometry)
    control_geometry = spec.get("control_coupon_geometry_hash", shared_geometry)
    if recovered_geometry and control_geometry and recovered_geometry != control_geometry:
        raise CircularFeedInputError("recovered/control coupon geometry hashes must match for UTP-119 comparison")

    required_tests = [row for row in compiled_tests if row["required"]]
    missing_measurements = [
        row["test_id"] for row in required_tests if row["measurement_state"] != "MEASURED_COMPARISON_AVAILABLE"
    ]
    failed = [row["test_id"] for row in required_tests if row["acceptance_state"] == "FAIL"]
    unevaluated = [
        row["test_id"]
        for row in required_tests
        if row["measurement_state"] == "MEASURED_COMPARISON_AVAILABLE"
        and row["acceptance_state"] == "OWNER_BOUND_NOT_SUPPLIED"
    ]

    if missing:
        disposition = "HOLD_BINDING"
    elif missing_measurements:
        disposition = "HOLD_MEASUREMENTS"
    elif failed:
        disposition = "REJECT_OR_REPROCESS"
    elif unevaluated:
        disposition = "MEASURED_REVIEW_REQUIRED"
    else:
        disposition = "READY_FOR_OWNER_REVIEW"

    return {
        "schema": "CGX-CIRCULAR-FEED-REFERENCE-PACKET/0.1",
        "artifact_id": "UTP-119",
        "packet_id": packet_id,
        "horizon": spec.get("horizon", "H-TERR-SITE"),
        "disposition": disposition,
        "missing_bindings": sorted(set(missing)),
        "missing_measurements": missing_measurements,
        "failed_tests": failed,
        "owner_thresholds_missing": unevaluated,
        "recovered_lot_id": records["recovered"].get("lot_id"),
        "control_lot_id": records["control"].get("lot_id"),
        "polymer_class": recovered_polymer or control_polymer or None,
        "coupon_geometry_hash": shared_geometry,
        "comparisons": compiled_tests,
        "physical_execution": False,
        "material_qualified": False,
        "printer_admission_authorized": False,
        "public_release_authorized": False,
        "next_gate": {
            "HOLD_BINDING": "Bind exact source/lot/process/coupon/test identity.",
            "HOLD_MEASUREMENTS": "Execute owner-approved paired physical tests and attach raw measurements.",
            "MEASURED_REVIEW_REQUIRED": "Owner/test authority supplies application-specific acceptance bounds.",
            "REJECT_OR_REPROCESS": "Reject or reprocess the recovered lot; do not admit as functional feed.",
            "READY_FOR_OWNER_REVIEW": "Owner reviews measured packet for declared application; no automatic qualification.",
        }[disposition],
        "boundary": (
            "Digital comparison never promotes recovered PET into qualified PrintSpace feed by itself. "
            "Actual lot/process/coupon evidence and owner acceptance remain required."
        ),
    }
