"""CGX T1K-012 / VGK-019 source-bound fluid regime screen, NOT a CFD solver.

This is a deterministic, synthetic-screening adapter to the existing Type-I
equation and volumetric families. SI dimensions, eligibility gates and
falsifiers are preserved. Even PASS means a qualified *equation candidate*,
never measured accuracy, safe hydraulic operation or native actuation.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EQUATION_PATH = "cgx/component_atlas/type1_equation_kernel_v0_1.json"
VOLUME_PATH = "cgx/component_atlas/type1_volumetric_kernel_v0_1.json"
INTERACTION_PATH = "cgx/component_atlas/component_interaction_map_v0_1.json"
UNITS = {
    "dynamic_viscosity": "Pa*s", "density": "kg/m^3",
    "length": "m", "radius": "m", "volumetric_flow": "m^3/s",
    "shear_rate": "1/s",
}
REQUIRED_MODEL = {
    "geometry": "CIRCULAR_STRAIGHT_CHANNEL",
    "constitutive_law": "NEWTONIAN_CONSTANT_MU",
    "continuity": "SINGLE_PHASE",
    "compressibility": "INCOMPRESSIBLE",
    "temporal": "STEADY",
    "inlet_state": "FULLY_DEVELOPED",
    "wall": "NO_SLIP_RIGID",
    "continuum": "VALID",
    "provenance_grade": "SYNTHETIC",
}
# Reynolds <2000 is an intentionally conservative *screening threshold*;
# it does not establish transition physics, roughness/entrance or stability.
MAX_SCREEN_RE = 2000.0


class RegimeHold(ValueError):
    """Expected failure of an unproved or invalid model assumption."""


def _number(value: Any, label: str, *, positive: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RegimeHold(f"NONNUMERIC_{label.upper()}")
    v = float(value)
    if not math.isfinite(v) or (v <= 0 if positive else False):
        raise RegimeHold(f"INVALID_{label.upper()}")
    return v


def _validate_source_family(root: Path) -> dict[str, str]:
    # A new adapter may *reference* these owners, not invent a duplicate family.
    files = [EQUATION_PATH, VOLUME_PATH, INTERACTION_PATH]
    source: dict[str, str] = {}
    for p in files:
        raw = (root / p).read_bytes()
        data = json.loads(raw)
        if p == EQUATION_PATH:
            if data.get("artifact_id") != "UTP-136" or not any(
                row.get("kernel_id") == "T1K-012"
                and "laminar" in row.get("law", "").lower()
                for row in data.get("kernels", [])
            ):
                raise RegimeHold("FLUID_EQUATION_OWNER_DRIFT")
        elif p == VOLUME_PATH:
            if data.get("artifact_id") != "UTP-137" or not all(
                any(r.get("kernel_id") == k for r in data.get("records", []))
                for k in ("VGK-019", "VGK-020")
            ):
                raise RegimeHold("VOLUMETRIC_KERNEL_OWNER_DRIFT")
        else:
            if not all(any(r.get("ID") == k for r in data.get("records", []))
                       for k in ("CIM-024", "CIM-026", "CIM-027")):
                raise RegimeHold("CROSS_DOMAIN_INTERACTION_OWNER_DRIFT")
        source[p] = hashlib.sha256(raw).hexdigest()
    return source


def newtonian_shear_stress(dynamic_viscosity_pa_s: float, shear_rate_per_s: float) -> dict[str, Any]:
    """Signed scalar shear stress tau = mu * gamma_dot for a Newtonian fluid.

    A scalar demonstration, not a shear-thinning, viscoelastic, 3D tensor or
    calibrated material law. Negative shear rate is direction, not negative mu.
    """
    mu = _number(dynamic_viscosity_pa_s, "dynamic_viscosity")
    rate = _number(shear_rate_per_s, "shear_rate", positive=False)
    return {
        "equation": "tau=mu*gamma_dot",
        "shear_stress_pa": mu * rate,
        "units": {"dynamic_viscosity": "Pa*s", "shear_rate": "1/s", "stress": "Pa"},
        "model_state": "SYNTHETIC_CONSTITUTIVE_EQUATION_ONLY",
        "validated_material": False,
    }


def poiseuille_channel_candidate(spec: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    """Model-screen synthetic steady Newtonian, laminar circular channel.

    Required input structure:
      quantities: radius, length, volumetric_flow, dynamic_viscosity, density
      units: exact SI unit map
      assumptions: exact REQUIRED_MODEL words
      evidence: synthetic source ID, explicitly scoped and not a credential
    No implicit unit conversions, physical qualification or web/host fetch.
    """
    if not isinstance(spec, dict):
        raise RegimeHold("INVALID_INPUT_ENVELOPE")
    units = spec.get("units")
    if units != {k: v for k, v in UNITS.items() if k != "shear_rate"}:
        raise RegimeHold("MISSING_OR_MISMATCHED_SI_UNITS")
    assumptions = spec.get("assumptions")
    if not isinstance(assumptions, dict):
        raise RegimeHold("MISSING_REGIME")
    for key, expected in REQUIRED_MODEL.items():
        if assumptions.get(key) != expected:
            raise RegimeHold(f"REGIME_HOLD_{key.upper()}")
    if set(assumptions) != set(REQUIRED_MODEL):
        raise RegimeHold("UNREVIEWED_EXTRA_MODEL_ASSUMPTIONS")
    evidence = spec.get("evidence")
    if not isinstance(evidence, dict) or not isinstance(evidence.get("synthetic_case_id"), str) \
            or not evidence["synthetic_case_id"].strip():
        raise RegimeHold("SYNTHETIC_PROVENANCE_REQUIRED")
    vals = spec.get("quantities")
    if not isinstance(vals, dict) or set(vals) != set(UNITS) - {"shear_rate"}:
        raise RegimeHold("MISSING_OR_EXTRA_QUANTITIES")
    r = _number(vals["radius"], "radius")
    L = _number(vals["length"], "length")
    Q = _number(vals["volumetric_flow"], "volumetric_flow")
    mu = _number(vals["dynamic_viscosity"], "dynamic_viscosity")
    rho = _number(vals["density"], "density")
    if L < 20*r:
        raise RegimeHold("SLENDER_CHANNEL_ASSUMPTION_HOLD")
    # For a circular channel: D=2r, U=Q/(pi*r^2),
    # Re=rho*U*D/mu=2*rho*Q/(pi*mu*r).
    try:
        re = 2.0*rho*Q/(math.pi*mu*r)
        if not math.isfinite(re) or re >= MAX_SCREEN_RE:
            raise RegimeHold("REYNOLDS_REGIME_HOLD")
        # Existing exact owner VGK-019 and T1K-012, not a novel solver.
        dp = 8.0*mu*L*Q/(math.pi*r**4)
        resistance = dp/Q
        shear = 4.0*mu*Q/(math.pi*r**3)
    except (OverflowError, ZeroDivisionError) as exc:
        raise RegimeHold("NUMERICAL_PRECISION_OR_RANGE_HOLD") from exc
    if not all(math.isfinite(v) for v in (dp, resistance, shear)):
        raise RegimeHold("NUMERICAL_OVERFLOW_HOLD")
    original_roots = _validate_source_family(root)
    return {
        "schema": "CGX-T1K-012-VGK-019-SCREEN/0.1",
        "parent": "Cognigrex.cgx", "existing_operator_ids": ["T1K-012", "VGK-019"],
        "cross_domain_reference_ids": ["VGK-020", "CIM-024", "CIM-026", "CIM-027"],
        "source_sha256": original_roots,
        "synthetic_case_id": evidence["synthetic_case_id"],
        "screen_state": "MODEL_CANDIDATE_NOT_PHYSICALLY_VALIDATED",
        "reynolds_screen": re, "pressure_drop_pa": dp,
        "hydraulic_resistance_pa_s_per_m3": resistance,
        "wall_shear_pa": shear,
        "model_units": {"pressure_drop": "Pa", "Re": "dimensionless",
                        "hydraulic_resistance": "Pa*s/m^3", "wall_shear": "Pa"},
        "assumptions": dict(assumptions),
        "physical_operation_approved": False, "native_peer_approved": False,
        "public_release_approved": False,
        "falsifiers": ["independent pressure/flow and wall-shear readback",
                       "calibrated viscosity versus shear rate and temperature",
                       "inlet development, curvature, roughness, cavitation and slip checks",
                       "multiphase, compressibility and energy/heat coupling diagnostics"],
    }
