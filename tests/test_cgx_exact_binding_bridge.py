from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from cgx.manufacturing import (
    create_witness_coupon_packet,
    find_instance,
    load_default_instance_population,
    resolve_binding_gate,
    resolve_binding_queue,
    validate_lot_passport,
    validate_tool_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
POP = load_default_instance_population()
EXPECTED = {
    "CGXI-P0-SH01-ID-A": "SOURCE_IDENTITY",
    "CGXI-P1-TRACE-001": "LOT_PASSPORT",
    "CGXI-P1-VIA-001": "PROCESS_ROUTE",
    "CGXI-P2-R-001": "LOT_PASSPORT",
    "CGXI-P2-C-001": "LOT_PASSPORT",
    "CGXI-P2-L-001": "LOT_PASSPORT",
    "CGXI-P3-LC-001": "UPSTREAM_EVIDENCE",
    "CGXI-P3-LOOP-001": "LOT_PASSPORT",
}


def test_all_eight_owner_instances_resolve_to_expected_first_open_gate() -> None:
    assert len(POP["records"]) == 8
    resolved = {
        row["instance_id"]: resolve_binding_gate(row, population=POP)["first_open_gate"]
        for row in POP["records"]
    }
    assert resolved == EXPECTED


def test_queue_preserves_stage_dependency_and_source_candidate_progress() -> None:
    queue = resolve_binding_queue(POP)
    assert queue["record_count"] == 8
    assert queue["physical_execution"] is False
    assert queue["queue"][0]["instance_id"] == "CGXI-P0-SH01-ID-A"

    by_id = {row["instance_id"]: row for row in queue["queue"]}
    source_bound = {
        "CGXI-P1-TRACE-001",
        "CGXI-P1-VIA-001",
        "CGXI-P2-R-001",
        "CGXI-P2-C-001",
        "CGXI-P2-L-001",
        "CGXI-P3-LOOP-001",
    }
    assert all(by_id[i]["binding_progress"] == "SOURCE_CANDIDATE_BOUND" for i in source_bound)
    assert all(by_id[i]["first_open_gate"] != "SOURCE_IDENTITY" for i in source_bound)


def test_p3_lc_waits_for_measured_p2_l_and_c_instead_of_resourcing() -> None:
    lc = resolve_binding_gate(find_instance(POP, "CGXI-P3-LC-001"), population=POP)
    assert lc["first_open_gate"] == "UPSTREAM_EVIDENCE"
    assert lc["upstream_dependencies"] == ["CGXI-P2-L-001", "CGXI-P2-C-001"]
    assert lc["upstream_physical_state"] == {
        "CGXI-P2-L-001": "NOT_RUN",
        "CGXI-P2-C-001": "NOT_RUN",
    }


def test_lot_passport_rejects_placeholder_identity_and_never_qualifies_performance() -> None:
    bad = validate_lot_passport(
        {
            "kind": "material",
            "manufacturer": "Example",
            "part_or_material": "Example ink",
            "lot_or_batch": "UNRESOLVED",
            "quantity": 1,
            "unit": "bottle",
            "received_state": "SEALED",
            "condition": "VISUALLY_INTACT",
            "declared_use": "P1 witness coupon",
            "disposition": "HOLD",
            "source_hashes": ["abc"],
        }
    )
    assert bad["lot_identity_bound"] is False
    assert "missing:lot_or_batch" in bad["blockers"]
    assert bad["performance_qualified"] is False

    good = validate_lot_passport(
        {
            "kind": "material",
            "manufacturer": "SYNTHETIC TEST MANUFACTURER",
            "part_or_material": "SYNTHETIC TEST MATERIAL",
            "lot_or_batch": "SYNTH-LOT-001",
            "quantity": 1,
            "unit": "bottle",
            "received_state": "SEALED",
            "condition": "VISUALLY_INTACT",
            "declared_use": "compiler fixture only",
            "disposition": "ACCEPT_DECLARED_USE",
            "source_hashes": ["sha256:synthetic-source-hash"],
        }
    )
    assert good["lot_identity_bound"] is True
    assert good["performance_qualified"] is False
    assert good["cgx_uri"].endswith("/SYNTH-LOT-001")


def test_tool_manifest_distinguishes_identity_from_current_calibrated_capability() -> None:
    unresolved = validate_tool_manifest(
        {
            "tool_id": "synthetic-meter",
            "identity": "Synthetic meter fixture",
            "configuration_hash": "cfg-001",
            "supported_operations": ["RESISTANCE_MEASURE"],
            "capability_envelope": {"range": "synthetic"},
            "calibration_state": "UNVERIFIED",
            "condition": "AVAILABLE",
        }
    )
    assert unresolved["structurally_valid"] is True
    assert unresolved["qualified_for_bound_operation"] is False
    assert "calibration:UNVERIFIED" in unresolved["blockers"]

    current = validate_tool_manifest(
        {
            "tool_id": "synthetic-meter",
            "identity": "Synthetic meter fixture",
            "configuration_hash": "cfg-001",
            "supported_operations": ["RESISTANCE_MEASURE"],
            "capability_envelope": {"range": "synthetic"},
            "calibration_state": "CURRENT",
            "calibration_ref": "SYNTH-CAL-001",
            "uncertainty": "synthetic test uncertainty only",
            "condition": "AVAILABLE",
        }
    )
    assert current["qualified_for_bound_operation"] is True


def test_witness_packet_stays_hold_until_all_structural_prerequisites_are_bound() -> None:
    trace = find_instance(POP, "CGXI-P1-TRACE-001")
    held = create_witness_coupon_packet(trace)
    assert held["execution_state"] == "HOLD"
    assert held["physical_execution"] is False
    assert {
        "geometry-not-frozen",
        "lot-passport-not-bound",
        "process-not-frozen",
        "tool-calibration-not-current",
        "measurement-method-not-bound",
    } <= set(held["blockers"])

    ready = create_witness_coupon_packet(
        trace,
        geometry={"revision": "SYNTH-GEO-v1", "geometry_hash": "sha256:synthetic-geometry"},
        lot_refs=["cgx://material/lot/SYNTH-LOT-001"],
        process={"revision": "SYNTH-PROC-v1", "process_hash": "sha256:synthetic-process"},
        tool_manifests=[
            {
                "tool_id": "synthetic-deposition-tool",
                "identity": "Synthetic deposition tool fixture",
                "configuration_hash": "cfg-tool",
                "supported_operations": ["DEPOSIT"],
                "capability_envelope": {"resolution": "synthetic"},
                "calibration_state": "CURRENT",
                "calibration_ref": "SYNTH-CAL-TOOL",
                "uncertainty": "synthetic",
                "condition": "AVAILABLE",
            }
        ],
        measurement_method={
            "method": "synthetic four-wire fixture",
            "calibration_ref": "SYNTH-CAL-MEASURE",
        },
    )
    assert ready["execution_state"] == "DIGITAL_PACKET_READY"
    assert ready["physical_execution"] is False
    assert ready["blockers"] == []


def test_binding_queue_cli_returns_same_owner_state_without_mutation() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "compile_cgx_manufacturing.py"),
            "binding",
            "--queue",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    out = json.loads(proc.stdout)
    assert out["record_count"] == 8
    assert out["counts_by_gate"]["LOT_PASSPORT"] == 5
    assert out["counts_by_gate"].get("REQUIREMENT_TARGET", 0) == 0
    assert out["counts_by_gate"]["SOURCE_IDENTITY"] == 1
    assert out["counts_by_gate"]["PROCESS_ROUTE"] == 1
    assert out["counts_by_gate"]["UPSTREAM_EVIDENCE"] == 1
    assert out["physical_execution"] is False

def test_reviewed_requirement_targets_advance_without_physical_uplift() -> None:
    resistor = find_instance(POP, "CGXI-P2-R-001")
    loop = find_instance(POP, "CGXI-P3-LOOP-001")

    assert "1.0 kΩ nominal" in resistor["electrical_mechanical_thermal_or_process_ratings"]
    assert "±20%" in resistor["acceptance_tests"]
    assert resolve_binding_gate(resistor, population=POP)["first_open_gate"] == "LOT_PASSPORT"

    assert "13.56 MHz" in loop["electrical_mechanical_thermal_or_process_ratings"]
    assert "±5%" in loop["acceptance_tests"]
    assert resolve_binding_gate(loop, population=POP)["first_open_gate"] == "LOT_PASSPORT"

    assert resistor["binding_state"] == loop["binding_state"] == "UNBOUND"
    assert resistor["physical_state"] == loop["physical_state"] == "NOT_RUN"

def test_build_ready_label_cannot_bypass_existing_owner_evidence_gate() -> None:
    cap = dict(find_instance(POP, "CGXI-P2-C-001"))
    cap["binding_state"] = "BUILD_READY"
    resolved = resolve_binding_gate(cap, population=POP)
    assert resolved["first_open_gate"] == "LOT_PASSPORT"
    assert resolved["physical_state"] == "NOT_RUN"


def test_build_ready_with_bound_digital_inputs_still_requires_physical_test_execution() -> None:
    synthetic = {
        "instance_id": "CGXI-SYNTH-BUILD-READY",
        "proof_stage": "P2",
        "binding_state": "BUILD_READY",
        "physical_state": "NOT_RUN",
        "source_locator_or_hash": "sha256:source-bound",
        "material_stack_and_lots": "lot:SYNTH-LOT-001",
        "material_passport_refs": "cgx://material/lot/SYNTH-LOT-001",
        "uncertainty": "declared synthetic uncertainty",
        "blocked_by_next_binding": "",
        "electrical_mechanical_thermal_or_process_ratings": "synthetic declared target",
        "geometry_revision": "SYNTH-GEO-v1",
        "dimensions_and_tolerances": "1 mm x 1 mm +/- 0.1 mm",
        "manufacturing_or_assembly_route": "synthetic print and cure route",
        "tool_and_calibration_refs": "cgx://tool/synthetic/current",
        "acceptance_tests": "synthetic measurement",
        "falsifiers": "outside declared synthetic tolerance",
        "source_hashes": "sha256:source",
        "configuration_hash": "sha256:configuration",
    }
    resolved = resolve_binding_gate(synthetic, population={"records": [synthetic]})
    assert resolved["first_open_gate"] == "TEST_EXECUTION"
    assert resolved["physical_state"] == "NOT_RUN"

    verified = dict(synthetic)
    verified["physical_state"] = "VERIFIED"
    assert resolve_binding_gate(verified, population={"records": [verified]})["first_open_gate"] == "CLOSED"
