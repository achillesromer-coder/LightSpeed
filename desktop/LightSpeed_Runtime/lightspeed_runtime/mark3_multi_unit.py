"""Fail-closed Mark III multi-unit screening model.

The model performs deterministic bookkeeping on explicitly supplied SI inputs.
It is not trajectory design, contact dynamics, structural analysis, or flight
qualification. Results are always classified as derived screening evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from itertools import combinations
import json
from math import exp, isfinite
from typing import Mapping, Sequence


G0_M_S2 = 9.80665
EVIDENCE_CLASS = "DERIVED_SCREENING"
REQUIRED_APPENDAGE_COUNT = 3
SOLVER_VERSION = "0.1.0"


class ScreeningInputError(ValueError):
    """Raised when execution would require inventing an input."""


def _positive(name: str, value: float) -> float:
    value = float(value)
    if not isfinite(value) or value <= 0:
        raise ScreeningInputError(f"{name} must be finite and > 0")
    return value


def _non_negative(name: str, value: float) -> float:
    value = float(value)
    if not isfinite(value) or value < 0:
        raise ScreeningInputError(f"{name} must be finite and >= 0")
    return value


@dataclass(frozen=True)
class UnitSpec:
    unit_id: str
    dry_mass_kg: float
    propellant_mass_kg: float
    isp_s: float
    bounding_radius_m: float
    appendage_count: int = REQUIRED_APPENDAGE_COUNT

    def validate(self) -> None:
        if not self.unit_id.strip():
            raise ScreeningInputError("unit_id is required")
        _positive("dry_mass_kg", self.dry_mass_kg)
        _non_negative("propellant_mass_kg", self.propellant_mass_kg)
        _positive("isp_s", self.isp_s)
        _positive("bounding_radius_m", self.bounding_radius_m)
        if self.appendage_count != REQUIRED_APPENDAGE_COUNT:
            raise ScreeningInputError(
                "current owner-canonical Mark III topology requires exactly "
                f"{REQUIRED_APPENDAGE_COUNT} appendages"
            )


@dataclass(frozen=True)
class TraverseLeg:
    leg_id: str
    delta_v_m_s: float
    duration_s: float
    active_unit_ids: tuple[str, ...]

    def validate(self) -> None:
        if not self.leg_id.strip():
            raise ScreeningInputError("leg_id is required")
        _non_negative("delta_v_m_s", self.delta_v_m_s)
        _positive("duration_s", self.duration_s)
        if not self.active_unit_ids:
            raise ScreeningInputError("each traverse leg requires active_unit_ids")
        if len(self.active_unit_ids) != len(set(self.active_unit_ids)):
            raise ScreeningInputError("active_unit_ids must be unique within a leg")


@dataclass(frozen=True)
class JointMove:
    move_id: str
    unit_id: str
    appendage_id: int
    delta_angle_rad: float
    torque_nm: float
    drive_efficiency: float

    def validate(self) -> None:
        if not self.move_id.strip():
            raise ScreeningInputError("move_id is required")
        if not 1 <= self.appendage_id <= REQUIRED_APPENDAGE_COUNT:
            raise ScreeningInputError("appendage_id must be 1, 2, or 3")
        _non_negative("delta_angle_rad", abs(self.delta_angle_rad))
        _non_negative("torque_nm", abs(self.torque_nm))
        efficiency = float(self.drive_efficiency)
        if not isfinite(efficiency) or not 0 < efficiency <= 1:
            raise ScreeningInputError("drive_efficiency must be in (0, 1]")


@dataclass(frozen=True)
class Placement:
    unit_id: str
    x_m: float
    y_m: float
    z_m: float

    def validate(self) -> None:
        for name, value in (("x_m", self.x_m), ("y_m", self.y_m), ("z_m", self.z_m)):
            if not isfinite(float(value)):
                raise ScreeningInputError(f"{name} must be finite")


@dataclass(frozen=True)
class Interlock:
    interlock_id: str
    unit_a: str
    appendage_a: int
    unit_b: str
    appendage_b: int
    role: str = "SECONDARY_TO_SECONDARY"

    def validate(self) -> None:
        if not self.interlock_id.strip():
            raise ScreeningInputError("interlock_id is required")
        if self.unit_a == self.unit_b:
            raise ScreeningInputError("an interlock must join distinct units")
        if self.role not in {
            "SECONDARY_TO_SECONDARY",
            "MARK_III_TO_MARK_V_PRIMARY_LAUNCH",
        }:
            raise ScreeningInputError("unsupported interlock role")
        for value in (self.appendage_a, self.appendage_b):
            if not 1 <= value <= REQUIRED_APPENDAGE_COUNT:
                raise ScreeningInputError("interlock appendage IDs must be 1, 2, or 3")


def _rocket_burn(unit: UnitSpec, propellant_before_kg: float, delta_v_m_s: float) -> dict:
    wet_before = unit.dry_mass_kg + propellant_before_kg
    mass_after = wet_before / exp(delta_v_m_s / (unit.isp_s * G0_M_S2))
    propellant_used = wet_before - mass_after
    feasible = propellant_used <= propellant_before_kg + 1e-12
    propellant_after = (
        max(0.0, propellant_before_kg - propellant_used) if feasible else None
    )
    return {
        "wet_mass_before_kg": wet_before,
        "propellant_used_kg": propellant_used,
        "propellant_after_kg": propellant_after,
        "propellant_shortfall_kg": max(0.0, propellant_used - propellant_before_kg),
        "burn_feasible": feasible,
    }


def _validate_interlocks(interlocks: Sequence[Interlock], known_units: set[str]) -> None:
    occupied: set[tuple[str, int]] = set()
    for interlock in interlocks:
        interlock.validate()
        if interlock.unit_a not in known_units or interlock.unit_b not in known_units:
            raise ScreeningInputError("interlock references an unknown unit")
        endpoints = {
            (interlock.unit_a, interlock.appendage_a),
            (interlock.unit_b, interlock.appendage_b),
        }
        if occupied.intersection(endpoints):
            raise ScreeningInputError("an appendage endpoint cannot serve two interlocks")
        occupied.update(endpoints)


def _clearance_rows(
    units: Mapping[str, UnitSpec], placements: Sequence[Placement]
) -> list[dict]:
    placement_by_id: dict[str, Placement] = {}
    for placement in placements:
        placement.validate()
        if placement.unit_id not in units:
            raise ScreeningInputError("placement references an unknown unit")
        if placement.unit_id in placement_by_id:
            raise ScreeningInputError("each unit may have only one placement")
        placement_by_id[placement.unit_id] = placement
    if set(placement_by_id) != set(units):
        raise ScreeningInputError("a static placement is required for every unit")

    rows = []
    for left_id, right_id in combinations(sorted(units), 2):
        left = placement_by_id[left_id]
        right = placement_by_id[right_id]
        distance = (
            (left.x_m - right.x_m) ** 2
            + (left.y_m - right.y_m) ** 2
            + (left.z_m - right.z_m) ** 2
        ) ** 0.5
        required = (
            units[left_id].bounding_radius_m + units[right_id].bounding_radius_m
        )
        rows.append(
            {
                "unit_a": left_id,
                "unit_b": right_id,
                "centre_distance_m": distance,
                "required_static_separation_m": required,
                "static_clearance_m": distance - required,
                "static_overlap": distance < required,
            }
        )
    return rows


def simulate_scenario(
    *,
    scenario_id: str,
    units: Sequence[UnitSpec],
    legs: Sequence[TraverseLeg],
    moves: Sequence[JointMove],
    placements: Sequence[Placement],
    interlocks: Sequence[Interlock] = (),
) -> dict:
    """Return a deterministic, claim-bounded multi-unit receipt."""
    if not scenario_id.strip():
        raise ScreeningInputError("scenario_id is required")
    if not units:
        raise ScreeningInputError("at least one Mark III unit is required")
    unit_map = {unit.unit_id: unit for unit in units}
    if len(unit_map) != len(units):
        raise ScreeningInputError("unit_id values must be unique")
    for unit in units:
        unit.validate()
    _validate_interlocks(interlocks, set(unit_map))

    canonical_input = {
        "scenario_id": scenario_id,
        "units": [asdict(unit) for unit in units],
        "legs": [asdict(leg) for leg in legs],
        "moves": [asdict(move) for move in moves],
        "placements": [asdict(placement) for placement in placements],
        "interlocks": [asdict(interlock) for interlock in interlocks],
    }
    input_sha256 = hashlib.sha256(
        json.dumps(
            canonical_input,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    propellant = {unit.unit_id: unit.propellant_mass_kg for unit in units}
    leg_rows = []
    for leg in legs:
        leg.validate()
        unknown = set(leg.active_unit_ids) - set(unit_map)
        if unknown:
            raise ScreeningInputError(
                "traverse leg references unknown units: " + ", ".join(sorted(unknown))
            )
        burns = {}
        for unit_id in leg.active_unit_ids:
            burn = _rocket_burn(unit_map[unit_id], propellant[unit_id], leg.delta_v_m_s)
            burns[unit_id] = burn
            if burn["burn_feasible"]:
                propellant[unit_id] = burn["propellant_after_kg"]
        leg_rows.append(
            {
                **asdict(leg),
                "burns": burns,
                "leg_feasible": all(row["burn_feasible"] for row in burns.values()),
            }
        )

    move_rows = []
    for move in moves:
        move.validate()
        if move.unit_id not in unit_map:
            raise ScreeningInputError("joint move references an unknown unit")
        mechanical_work_j = abs(move.torque_nm * move.delta_angle_rad)
        move_rows.append(
            {
                **asdict(move),
                "mechanical_work_j": mechanical_work_j,
                "electrical_work_lower_bound_j": mechanical_work_j
                / move.drive_efficiency,
            }
        )

    clearance_rows = _clearance_rows(unit_map, placements)
    all_burns_feasible = all(row["leg_feasible"] for row in leg_rows)
    static_clearance_pass = not any(row["static_overlap"] for row in clearance_rows)
    total_propellant_used = sum(
        unit.propellant_mass_kg - propellant[unit.unit_id] for unit in units
    )
    total_move_energy = sum(
        row["electrical_work_lower_bound_j"] for row in move_rows
    )
    return {
        "schema": "lightspeed-mark3-multi-unit-screening-v1",
        "solver_version": SOLVER_VERSION,
        "input_sha256": input_sha256,
        "scenario_id": scenario_id,
        "evidence_class": EVIDENCE_CLASS,
        "owner_topology": {
            "hardware_lineage": "MARK_III",
            "appendages_per_unit": REQUIRED_APPENDAGE_COUNT,
            "source_rule": "OD-050",
        },
        "units": [asdict(unit) for unit in units],
        "interlocks": [asdict(interlock) for interlock in interlocks],
        "legs": leg_rows,
        "moves": move_rows,
        "static_clearance": clearance_rows,
        "summary": {
            "unit_count": len(units),
            "total_delta_v_m_s": sum(leg.delta_v_m_s for leg in legs),
            "total_duration_s": sum(leg.duration_s for leg in legs),
            "total_propellant_used_kg": total_propellant_used,
            "propellant_remaining_kg_by_unit": propellant,
            "manipulator_electrical_work_lower_bound_j": total_move_energy,
            "all_burns_feasible": all_burns_feasible,
            "static_clearance_pass": static_clearance_pass,
            "screening_pass": all_burns_feasible and static_clearance_pass,
        },
        "limitations": [
            "delta-v and duration are supplied inputs, not computed trajectories",
            "rocket-equation bookkeeping omits reserve, residual, ullage, losses, and finite-burn effects",
            "manipulator work omits inertia, friction, damping, harness, contact, and control losses",
            "clearance is static bounding-sphere screening, not swept-volume or contact dynamics",
            "interlock role validation does not establish geometry, strength, latch, release, or Mark V compatibility",
            "no result is empirical, flight-qualified, or a target/route recommendation",
        ],
    }


def sweep_delta_v(
    *,
    scenario_id: str,
    units: Sequence[UnitSpec],
    legs: Sequence[TraverseLeg],
    moves: Sequence[JointMove],
    placements: Sequence[Placement],
    interlocks: Sequence[Interlock] = (),
    delta_v_scale: Sequence[float],
) -> list[dict]:
    """Repeat a scenario over explicit positive delta-v scale factors."""
    rows = []
    for scale in delta_v_scale:
        scale = _positive("delta_v_scale", scale)
        scaled_legs = [
            TraverseLeg(
                leg_id=leg.leg_id,
                delta_v_m_s=leg.delta_v_m_s * scale,
                duration_s=leg.duration_s,
                active_unit_ids=leg.active_unit_ids,
            )
            for leg in legs
        ]
        result = simulate_scenario(
            scenario_id=f"{scenario_id}:dv-scale={scale:g}",
            units=units,
            legs=scaled_legs,
            moves=moves,
            placements=placements,
            interlocks=interlocks,
        )
        rows.append(
            {
                "delta_v_scale": scale,
                **result["summary"],
                "evidence_class": EVIDENCE_CLASS,
            }
        )
    return rows
