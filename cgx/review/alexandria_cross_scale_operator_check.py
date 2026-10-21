"""Read-only CGX Alexandria cross-scale operator regression surface.

This is a noncanonical source-linked projection over existing VGK, CIM and
CGX object/assurance registries. The arithmetic checks dimensional toy
balances only. No CFD, Maxwell, orbital capture, SAI networking or material
qualification is performed or implied.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECTION = Path(__file__).with_name("alexandria_cross_scale_operator_projection_20261021.json")
MINIMAL_HOLD = ("REVIEW_ONLY", "PHYSICAL", "HOLD")

class OperatorHold(ValueError):
    """A quantity, source family or physical validity gate is not satisfied."""

def _positive(name: str, value: float, *, zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise OperatorHold("NOT_NUMERIC_" + name)
    x = float(value)
    if not math.isfinite(x) or x < 0 or (not zero and x <= 0):
        raise OperatorHold("NON_PHYSICAL_" + name)
    return x

def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def validate_source_projection(root: Path = ROOT) -> dict:
    payload = json.loads((root / PROJECTION.relative_to(ROOT)).read_text(encoding="utf-8"))
    if payload.get("root") != "Cognigrex.cgx" or payload.get("kind") != "NONCANONICAL_SOURCE_LINKED_FRONTIER_READ_MODEL":
        raise OperatorHold("CANONICAL_IDENTITY_COLLISION")
    if payload.get("owner_stage") != "HOLD_NO_SOURCE_MOVE_NO_PUBLIC_RELEASE_NO_LIVE_ACTUATION":
        raise OperatorHold("RELEASE_STATE_CHANGED")
    if sorted(payload.get("protected_issues", [])) != [158, 161]:
        raise OperatorHold("PUBLIC_OR_PEER_GATES_MISSING")
    sources = {}
    for anchor in payload["source_anchors"]:
        path = root / anchor["path"]
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise OperatorHold("SOURCE_ANCHOR_UNAVAILABLE")
        actual = git_blob_sha(path.read_bytes())
        if actual != anchor["git_blob_sha1"]:
            raise OperatorHold("ORIGINAL_SOURCE_BLOB_MISMATCH")
        sources[anchor["path"]] = json.loads(path.read_text())
    vgk = {x["kernel_id"] for x in sources["cgx/component_atlas/type1_volumetric_kernel_v0_1.json"]["records"]}
    cim = {x["ID"] for x in sources["cgx/component_atlas/component_interaction_map_v0_1.json"]["records"]}
    ids = set()
    for op in payload["operators"]:
        if op["id"] in ids or not op["domains"] or not op["dimensions"] or not op["falsifier"]:
            raise OperatorHold("OPERATOR_DUPLICATE_OR_INCOMPLETE")
        ids.add(op["id"])
        for ref in op["existing"]:
            if not ((ref in vgk and ref.startswith("VGK-")) or (ref in cim and ref.startswith("CIM-"))):
                raise OperatorHold("UNPINNED_SOURCE_KERNEL")
        if op["numeric_profile"].startswith("RUNNABLE") or any(not x["qualification"] for x in op["domains"]):
            raise OperatorHold("UNVERIFIED_CAPABILITY_PROMOTION")
    if len(ids) != 6:
        raise OperatorHold("CROSS_DOMAIN_COVERAGE_DRIFT")
    if len(payload["frontier_held"]) != 6 or any("HOLD" not in x["status"] and x["status"] != "ONTOLOGY_ANALOGY_ONLY" for x in payload["frontier_held"]):
        raise OperatorHold("PHYSICS_FRONTIER_NOT_HELD")
    return {
        "schema": "CGX-ALEXANDRIA-OPERATOR-REGRESSION-RECEIPT/0.1",
        "status": "SOURCE_PROJECTION_VERIFIED_NONCANONICAL",
        "operator_count": len(ids),
        "source_anchor_git_sha1": {a["path"]: a["git_blob_sha1"] for a in payload["source_anchors"]},
        "original_source_anchors_unchanged": True,
        "independent_physical_tests": 0,
        "native_peer_accepted": False,
        "public_release_authorised": False,
        "owner_staging_executed": False,
    }

def laminar_circular_tube(*, density_kg_m3: float, viscosity_pa_s: float,
                           mean_speed_m_s: float, radius_m: float, length_m: float) -> dict:
    """Reduced, fully-developed Newtonian laminar tube law for a synthetic ideal tube.

    Cannot assert a printing nozzle, space propellant loop, bubbly mist,
    non-Newtonian resin, porous membrane or full-3D CFD calibration.
    """
    rho = _positive("density", density_kg_m3)
    mu = _positive("viscosity", viscosity_pa_s)
    u = _positive("mean_speed", mean_speed_m_s, zero=True)
    r = _positive("radius", radius_m)
    length = _positive("length", length_m)
    re = rho * u * (2.0 * r) / mu
    if not math.isfinite(re) or re >= 2000.0:
        raise OperatorHold("REDUCED_LAMINAR_REGIME_NOT_DEMONSTRATED")
    q = u * math.pi * r*r
    dp = 8 * mu * length * q / (math.pi * r**4)
    return {"flow_m3_s": q, "reynolds": re, "pressure_drop_pa": dp,
            "kinematic_viscosity_m2_s": mu/rho,
            "status": "SYNTHETIC_REDUCED_MODEL_ONLY_NOT_CALIBRATED"}

def passive_incident_capture(*, irradiance_w_m2: float, aperture_m2: float,
                             coupling_efficiency: float, converter_efficiency: float) -> dict:
    flux = _positive("irradiance", irradiance_w_m2, zero=True)
    area = _positive("aperture", aperture_m2)
    coupling = _positive("coupling_efficiency", coupling_efficiency, zero=True)
    conversion = _positive("converter_efficiency", converter_efficiency, zero=True)
    if coupling > 1 or conversion > 1:
        raise OperatorHold("POSSIBLE_OUTPUT_GREATER_THAN_INCIDENT_INPUT")
    pin = flux * area
    if not math.isfinite(pin):
        raise OperatorHold("INVALID_POWER_BUDGET")
    return {"incident_power_w": pin,
            "coupled_power_w": pin*coupling,
            "upper_bound_delivered_power_w": pin*coupling*conversion,
            "status": "BOUND_ONLY_NO_MEASURED_RF_OR_SOLAR_HARVEST"}

def encounter_relative_energy(*, moving_mass_kg: float, target_mass_kg: float,
                              relative_speed_m_s: float) -> dict:
    a = _positive("moving_mass", moving_mass_kg)
    b = _positive("target_mass", target_mass_kg)
    speed = _positive("relative_speed", relative_speed_m_s, zero=True)
    reduced = a*b/(a+b)
    energy = 0.5*reduced*speed**2
    if not math.isfinite(energy):
        raise OperatorHold("INVALID_KINETIC_ENERGY")
    return {"reduced_mass_kg": reduced, "center_of_mass_relative_energy_j": energy,
            "status": "KINEMATIC_LOWER_ORDER_ACCOUNTING_NOT_ORBITAL_CAPTURE",
            "capture_demonstrated": False, "environmental_fate_demonstrated": False}

def power_balance(*, incident_power_w: float, useful_power_w: float,
                  thermal_loss_w: float, stored_power_w: float, tolerance_w: float = 1e-9) -> dict:
    pin = _positive("incident_power", incident_power_w, zero=True)
    useful = _positive("useful_power", useful_power_w, zero=True)
    thermal = _positive("thermal_loss", thermal_loss_w, zero=True)
    stored = _positive("stored_power", stored_power_w, zero=True)
    tolerance = _positive("tolerance", tolerance_w, zero=True)
    residual = pin - useful - thermal - stored
    if residual < -tolerance:
        raise OperatorHold("OUTPUTS_EXCEED_INPUTS")
    return {"unallocated_power_residual_w": residual,
            "closed_within_declared_tolerance": abs(residual) <= tolerance,
            "status": "ACCOUNTING_IDENTITY_NOT_EXPERIMENTAL_EFFICIENCY"}

def two_body_specific_orbital_energy(*, speed_m_s: float,
                                     orbital_radius_m: float,
                                     central_mu_m3_s2: float) -> dict:
    """Only the instantaneous ideal two-body specific-energy diagnostic.

    Negative epsilon implies an elliptic conic under strict point-mass,
    Keplerian two-body assumptions. It does NOT establish impact avoidance,
    capture following a maneuver, ice deposition, stable storage, collision
    probability, compliance, or a receipted orbit/mission.
    """
    speed = _positive("speed", speed_m_s, zero=True)
    radius = _positive("orbital_radius", orbital_radius_m)
    mu = _positive("central_mu", central_mu_m3_s2)
    eps = 0.5 * speed*speed - mu/radius
    if not math.isfinite(eps):
        raise OperatorHold("INVALID_TWO_BODY_SPECIFIC_ENERGY")
    return {
        "specific_energy_m2_s2": eps,
        "ideal_two_body_negative_energy": eps < 0,
        "orbit_and_target_frames_verified": False,
        "safe_rendezvous_or_capture_demonstrated": False,
        "passive_regolith_or_ice_absorption_demonstrated": False,
        "conjunction_debris_environmental_qualification": "HOLD",
        "status": "SYNTHETIC_KEPLERIAN_DIAGNOSTIC_NOT_MISSION_OR_CAPTURE_PROOF"
    }


if __name__ == "__main__":
    print(json.dumps(validate_source_projection(), indent=2, sort_keys=True))
