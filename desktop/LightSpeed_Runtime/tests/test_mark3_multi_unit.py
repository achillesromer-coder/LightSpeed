from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from lightspeed_runtime.mark3_multi_unit import (
    EVIDENCE_CLASS,
    Interlock,
    JointMove,
    Placement,
    ScreeningInputError,
    TraverseLeg,
    UnitSpec,
    simulate_scenario,
    sweep_delta_v,
)


def unit(unit_id: str, propellant: float = 10.0) -> UnitSpec:
    return UnitSpec(
        unit_id=unit_id,
        dry_mass_kg=100.0,
        propellant_mass_kg=propellant,
        isp_s=300.0,
        bounding_radius_m=0.5,
    )


def scenario(**overrides):
    values = {
        "scenario_id": "SYN-M3-MULTI-001",
        "units": [unit("M3-01"), unit("M3-02")],
        "legs": [
            TraverseLeg(
                leg_id="LEG-01",
                delta_v_m_s=20.0,
                duration_s=100.0,
                active_unit_ids=("M3-01", "M3-02"),
            )
        ],
        "moves": [
            JointMove(
                move_id="MOVE-01",
                unit_id="M3-01",
                appendage_id=1,
                delta_angle_rad=0.5,
                torque_nm=4.0,
                drive_efficiency=0.8,
            )
        ],
        "placements": [
            Placement("M3-01", 0.0, 0.0, 0.0),
            Placement("M3-02", 2.0, 0.0, 0.0),
        ],
        "interlocks": [Interlock("LOCK-01", "M3-01", 1, "M3-02", 1)],
    }
    values.update(overrides)
    return simulate_scenario(**values)


def test_scenario_returns_bounded_receipt() -> None:
    result = scenario()
    assert result["evidence_class"] == EVIDENCE_CLASS
    assert result["owner_topology"]["appendages_per_unit"] == 3
    assert result["summary"]["screening_pass"] is True
    assert result["summary"]["total_propellant_used_kg"] > 0
    assert result["summary"]["manipulator_electrical_work_lower_bound_j"] == 2.5
    assert len(result["limitations"]) >= 5
    assert len(result["input_sha256"]) == 64


def test_input_fingerprint_is_deterministic_and_change_sensitive() -> None:
    first = scenario()
    second = scenario()
    changed = scenario(
        legs=[TraverseLeg("LEG-01", 21.0, 100.0, ("M3-01", "M3-02"))]
    )
    assert first["input_sha256"] == second["input_sha256"]
    assert first["input_sha256"] != changed["input_sha256"]


def test_zero_delta_v_is_null_control() -> None:
    result = scenario(
        legs=[TraverseLeg("NULL", 0.0, 1.0, ("M3-01", "M3-02"))],
        moves=[],
    )
    assert result["summary"]["total_propellant_used_kg"] == pytest.approx(0.0)
    assert result["summary"]["manipulator_electrical_work_lower_bound_j"] == 0


def test_insufficient_propellant_fails_screening_without_negative_mass() -> None:
    result = scenario(
        units=[unit("M3-01", 0.01), unit("M3-02", 0.01)],
        legs=[TraverseLeg("HIGH-DV", 1000.0, 10.0, ("M3-01", "M3-02"))],
    )
    assert result["summary"]["all_burns_feasible"] is False
    assert result["summary"]["screening_pass"] is False
    assert all(
        value == pytest.approx(0.01)
        for value in result["summary"]["propellant_remaining_kg_by_unit"].values()
    )
    assert all(
        burn["propellant_after_kg"] is None and burn["propellant_shortfall_kg"] > 0
        for burn in result["legs"][0]["burns"].values()
    )


def test_static_overlap_fails_screening() -> None:
    result = scenario(
        placements=[
            Placement("M3-01", 0.0, 0.0, 0.0),
            Placement("M3-02", 0.5, 0.0, 0.0),
        ]
    )
    assert result["static_clearance"][0]["static_overlap"] is True
    assert result["summary"]["screening_pass"] is False


def test_current_topology_rejects_non_three_appendage_unit() -> None:
    with pytest.raises(ScreeningInputError, match="exactly 3 appendages"):
        scenario(
            units=[
                UnitSpec("M3-01", 100, 10, 300, 0.5, appendage_count=2),
                unit("M3-02"),
            ]
        )


def test_interlock_endpoint_cannot_be_double_booked() -> None:
    with pytest.raises(ScreeningInputError, match="cannot serve two interlocks"):
        scenario(
            units=[unit("M3-01"), unit("M3-02"), unit("M3-03")],
            placements=[
                Placement("M3-01", 0, 0, 0),
                Placement("M3-02", 2, 0, 0),
                Placement("M3-03", 4, 0, 0),
            ],
            interlocks=[
                Interlock("L1", "M3-01", 1, "M3-02", 1),
                Interlock("L2", "M3-01", 1, "M3-03", 1),
            ],
        )


def test_unknown_leg_unit_fails_closed() -> None:
    with pytest.raises(ScreeningInputError, match="unknown units"):
        scenario(legs=[TraverseLeg("BAD", 1, 1, ("M3-UNKNOWN",))])


def test_missing_placement_fails_closed() -> None:
    with pytest.raises(ScreeningInputError, match="required for every unit"):
        scenario(placements=[Placement("M3-01", 0, 0, 0)])


def test_delta_v_sweep_is_monotonic_for_propellant() -> None:
    rows = sweep_delta_v(
        scenario_id="SWEEP",
        units=[unit("M3-01"), unit("M3-02")],
        legs=[TraverseLeg("L1", 10, 100, ("M3-01", "M3-02"))],
        moves=[],
        placements=[
            Placement("M3-01", 0, 0, 0),
            Placement("M3-02", 2, 0, 0),
        ],
        delta_v_scale=[0.5, 1.0, 2.0],
    )
    used = [row["total_propellant_used_kg"] for row in rows]
    assert used == sorted(used)
    assert all(row["evidence_class"] == EVIDENCE_CLASS for row in rows)


def test_invalid_scale_fails_closed() -> None:
    with pytest.raises(ScreeningInputError, match="delta_v_scale"):
        sweep_delta_v(
            scenario_id="SWEEP",
            units=[unit("M3-01")],
            legs=[TraverseLeg("L1", 1, 1, ("M3-01",))],
            moves=[],
            placements=[Placement("M3-01", 0, 0, 0)],
            delta_v_scale=[0],
        )


def test_machine_readable_input_schema_preserves_topology_lock() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    schema = json.loads(
        (
            repo_root / "schemas" / "mark3_multi_unit_screening_input.schema.json"
        ).read_text(encoding="utf-8")
    )
    unit_properties = schema["properties"]["units"]["items"]["properties"]
    assert unit_properties["appendage_count"] == {"const": 3}
    assert schema["additionalProperties"] is False


def test_cli_writes_a_derived_receipt(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    input_path = repo_root / "tests" / "fixtures" / "mark3_multi_unit_synthetic.json"
    output_path = tmp_path / "receipt.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "run_mark3_multi_unit_screening.py"),
            str(input_path),
            str(output_path),
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(output_path.read_text(encoding="utf-8"))
    summary = json.loads(completed.stdout)
    assert receipt["evidence_class"] == EVIDENCE_CLASS
    assert len(receipt["delta_v_sweep"]) == 3
    assert summary["screening_pass"] is True
