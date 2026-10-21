"""Read-only cross-scale Alexandria operator overlay, not a solver or DBR.

Reuses existing CGX/Raphael/assurance source blobs and validates mathematical
invariants with synthetic inputs. Never infers mission, environmental, radio,
public distribution, country-network or physical-product qualification.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OVERLAY = Path(__file__).with_name("alexandria_cross_scale_interaction_overlay_20261021.json")
EXPECTED_SCHEMA = "CGX-ALEXANDRIA-CROSS-SCALE-OPERATOR-OVERLAY/0.1"

class CrossScaleHold(ValueError):
    """Source/physics/rights cannot be promoted as accepted."""

def _positive(value: float, label: str, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise CrossScaleHold("NONFINITE_OR_BAD_" + label.upper())
    if value < 0 or (not allow_zero and value == 0):
        raise CrossScaleHold("NONPOSITIVE_" + label.upper())
    return float(value)

def _check_close(lhs: float, rhs: float, abs_tol: float = 1e-10, rel_tol: float = 1e-9) -> None:
    if not math.isclose(lhs, rhs, abs_tol=abs_tol, rel_tol=rel_tol):
        raise CrossScaleHold("CONSERVATION_RESIDUAL_UNCLOSED")

def mass_inventory_kg(*, source_in_kg: float, recovered_kg: float,
                      safely_stored_kg: float, emitted_kg: float,
                      unresolved_kg: float) -> dict:
    vals = {k: _positive(v, k, allow_zero=True) for k, v in {
        "source_in_kg": source_in_kg, "recovered_kg": recovered_kg,
        "safely_stored_kg": safely_stored_kg, "emitted_kg": emitted_kg,
        "unresolved_kg": unresolved_kg}.items()}
    total = vals["recovered_kg"] + vals["safely_stored_kg"] + vals["emitted_kg"] + vals["unresolved_kg"]
    _check_close(vals["source_in_kg"], total)
    return {"schema": "CGX-CROSS-SCALE-SYNTHETIC/0.1", "balance_closed": True,
            "measured": False, "environmentally_safe": False,
            "mitigation_verified": False, "units": "kg"}

def reynolds_candidate(*, density_kg_m3: float, velocity_m_s: float,
                       length_m: float, dynamic_viscosity_pa_s: float,
                       constitutive_regime: str) -> dict:
    if constitutive_regime != "newtonian_continuum":
        raise CrossScaleHold("CONSTITUTIVE_REGIME_UNVERIFIED")
    rho = _positive(density_kg_m3, "density")
    v = _positive(velocity_m_s, "velocity", allow_zero=True)
    L = _positive(length_m, "length")
    mu = _positive(dynamic_viscosity_pa_s, "viscosity")
    Re = rho*v*L/mu
    if not math.isfinite(Re):
        raise CrossScaleHold("NONFINITE_REYNOLDS")
    return {"Re": Re, "dimensionless": True, "applicable_after_regime_screen": True,
            "flow_solution": False, "turbulence_or_equivalent_behaviour_proved": False}

def passive_rf_budget_w(*, incident_w: float, local_supplied_w: float,
                        released_storage_w: float, harvested_w: float,
                        outgoing_w: float, dissipated_w: float,
                        stored_increase_w: float) -> dict:
    vals = {k: _positive(v, k, allow_zero=True) for k, v in {
        "incident_w": incident_w, "local_supplied_w": local_supplied_w,
        "released_storage_w": released_storage_w, "harvested_w": harvested_w,
        "outgoing_w": outgoing_w, "dissipated_w": dissipated_w,
        "stored_increase_w": stored_increase_w}.items()}
    incoming = vals["incident_w"] + vals["local_supplied_w"] + vals["released_storage_w"]
    outgoing = vals["harvested_w"] + vals["outgoing_w"] + vals["dissipated_w"] + vals["stored_increase_w"]
    _check_close(incoming, outgoing)
    return {"power_conservation_closed": True, "usable_output_w": vals["harvested_w"],
            "units": "W", "net_energy_generated": False,
            "solar_or_rf_harvesting_measured": False, "spectrum_rights_approved": False}

def two_body_orbital_energy_candidate(*, speed_m_s: float, radius_m: float,
                                      gravitational_parameter_m3_s2: float) -> dict:
    v = _positive(speed_m_s, "speed", allow_zero=True)
    radius = _positive(radius_m, "radius")
    mu = _positive(gravitational_parameter_m3_s2, "grav_parameter")
    epsilon = 0.5*v*v - mu/radius
    if not math.isfinite(epsilon):
        raise CrossScaleHold("ENERGY_UNRESOLVED")
    return {"specific_mechanical_energy_m2_s2": epsilon,
            "negative_two_body_energy": epsilon < 0,
            "stable_rendezvous_or_capture_proved": False,
            "ice_deposition_qualifies_orbital_absorption": False,
            "conjunction_and_collision_acceptance": "HOLD"}

def load_and_validate_overlay(root: Path = ROOT) -> dict:
    path = root / "cgx/review/alexandria_cross_scale_interaction_overlay_20261021.json"
    overlay = json.loads(path.read_text(encoding="utf-8"))
    if overlay.get("schema") != EXPECTED_SCHEMA or overlay.get("parent") != "Cognigrex.cgx":
        raise CrossScaleHold("NOT_EXISTING_CGX_OVERLAY")
    if overlay.get("surface") != "READ_ONLY_FRONTIER_PROJECTION_NOT_CANONICAL":
        raise CrossScaleHold("UNAUTHORIZED_CANONICAL_PROMOTION")
    sources = overlay.get("source_roots", [])
    if len(sources) != 3:
        raise CrossScaleHold("MISSING_EXISTING_DOMAIN_OWNERS")
    for entry in sources:
        source = (root / entry["path"]).resolve(strict=True)
        if not source.is_relative_to(root.resolve(strict=True)) or source.is_symlink():
            raise CrossScaleHold("SOURCE_PATH_ESCAPED")
        data = source.read_bytes()
        sha1 = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if sha1 != entry["git_blob_sha1"]:
            raise CrossScaleHold("SOURCE_BLOB_MISMATCH")
    families = overlay.get("operator_families", [])
    ids = {op["id"] for op in families}
    if len(families) != 7 or len(ids) != 7:
        raise CrossScaleHold("OPERATOR_DUPLICATION_OR_OMISSION")
    if len(overlay.get("scenario_links", [])) != 7:
        raise CrossScaleHold("SCENARIO_COUNT_DRIFT")
    for s in overlay["scenario_links"]:
        if not set(s["operators"]).issubset(ids):
            raise CrossScaleHold("UNKNOWN_LINKED_OPERATOR")
        if not s["qualification"] or s["grade"] == "OPERATIONALLY_ACCEPTED":
            raise CrossScaleHold("UNQUALIFIED_SCENARIO_PROMOTION")
    flags = overlay["status"]
    for k, value in flags.items():
        if k.endswith("_enabled") or k in (
                "physically_qualified", "installer_or_runtime_added",
                "source_bytes_copied", "governing_equation_unification_proved"):
            if value is not False:
                raise CrossScaleHold("UNSUPPORTED_CAPABILITY_PROMOTION")
    if flags["public_release_issue_158"] != "HOLD" or flags["native_peer_issue_161"] != "HOLD":
        raise CrossScaleHold("RELEASE_GATE_BYPASSED")
    if len(overlay["minimum_admission_fields"]) < 15:
        raise CrossScaleHold("MISSING_ACCEPTANCE_CONTRACT")
    return {"schema": EXPECTED_SCHEMA, "root": overlay["parent"],
            "source_roots_verified": len(sources), "operator_families": len(ids),
            "candidate_scenarios": len(overlay["scenario_links"]),
            "status": "FRONTIER_SOURCE_BOUND_NOT_EXECUTABLE",
            "public_release": "HOLD", "native_two_node": "HOLD",
            "AU_SAI_network_activated": False, "physical_model_accepted": False,
            "source_or_canonical_mutation": False}

if __name__ == "__main__":
    print(json.dumps(load_and_validate_overlay(), indent=2, sort_keys=True))
