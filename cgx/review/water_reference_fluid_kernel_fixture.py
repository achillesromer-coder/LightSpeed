"""Noncanonical CGX shared fluid STATE bridge; never a replacement solver.

One original-source-attributed, fixed liquid-water reference-correlation check row
feeds three DIFFERENT, regime-constrained synthetic analytical examples. Results
never claim owner DBR, experimental validation, rights or public/physical release.

Source: NIST 2009 Table 8 at 298.15 K and 0.1 MPa; original source PDF is
linked, NOT copied or separately SHA-attested in this review fixture.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from math import isfinite, pi
from pathlib import Path

FIXTURE = Path(__file__).with_name("water_reference_property_fixture_20261021.json")
SOURCE_ID = "nist-liquid-water-0p1mpa-table8-298p15k"
SOURCE_URL = "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=832373"
# Guards the locally transcribed, explicitly un-attested source CHECK ROW;
# it is NOT an original-PDF digest or a claim of provider signature.
TABLE_ROW = {
    "temperature_kelvin": "298.15",
    "pressure_pa": "100000",
    "density_kg_per_m3": "997.047013",
    "viscosity_micro_pa_s": "889.996774",
}
KERNEL_LINKS = {
    "laminar_tube": ("T1K-012", "VGK-019"),
    "porous_darcy": ("VGK-020",),
    "stokes_particle_drag": ("RFS_EMFF_MEDIUM_SWEEP",),
    "general_cfd_reference": ("VGK-039",),
}
EVIDENCE = "SOURCE_LINKED_REFERENCE_PLUS_SYNTHETIC_MODEL_TEST_ONLY"

class DomainHold(ValueError):
    """Invalid source, parameter, regime or attempted evidence promotion."""

@dataclass(frozen=True)
class FluidState:
    mu_pa_s: float
    rho_kg_m3: float
    temperature_kelvin: float
    pressure_pa: float
    source_id: str


def read_reference_state(path: Path = FIXTURE) -> FluidState:
    """Read only the one NIST Table-8 check point; reject modified authority."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 16_384:
        raise DomainHold("FIXTURE_MISSING_OR_UNSAFE")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        fields = doc["state_point"]
        if fields != TABLE_ROW:
            raise DomainHold("SOURCE_STATE_POINT_CHANGED")
        if doc["reference_id"] != SOURCE_ID or doc["source"]["url"] != SOURCE_URL:
            raise DomainHold("SOURCE_LOCATOR_CHANGED")
        if doc["state"] != "PUBLISHED_CORRELATION_CHECK_VALUE_NOT_MEASUREMENT":
            raise DomainHold("SOURCE_EVIDENCE_CLASS_CHANGED")
        for field in ("instrument_measured_here", "native_cgx_admitted", "owner_dbr_verified", "public_release_authorised"):
            if doc[field] is not False:
                raise DomainHold("UNSUPPORTED_AUTHORITY_ASSERTION")
        if doc["source"]["original_document_sha256"] is not None or doc["source"]["original_source_bytes_retrieved"] is not False or doc["source"]["source_rights_for_redistribution_verified"] is not False:
            raise DomainHold("SOURCE_BYTE_OR_RIGHTS_ATTESTATION_UNVERIFIED")
        viscosity = Decimal(fields["viscosity_micro_pa_s"]) * Decimal("0.000001")
        if viscosity != Decimal(doc["conversion"]["viscosity_pa_s"]):
            raise DomainHold("UNIT_CONVERSION_MISMATCH")
        rho = Decimal(fields["density_kg_per_m3"])
        temperature = Decimal(fields["temperature_kelvin"])
        pressure = Decimal(fields["pressure_pa"])
        if min(viscosity, rho, temperature, pressure) <= 0:
            raise DomainHold("PROPERTY_OUT_OF_RANGE")
        return FluidState(float(viscosity), float(rho), float(temperature), float(pressure), SOURCE_ID)
    except (KeyError, TypeError, ValueError, InvalidOperation, UnicodeError, OSError) as e:
        if isinstance(e, DomainHold):
            raise
        raise DomainHold("REFERENCE_FIXTURE_INVALID") from e


def _positive(parameters: dict, name: str) -> float:
    value = parameters.get(name)
    if type(value) not in (float, int) or not isfinite(value) or value <= 0:
        raise DomainHold("MISSING_OR_NONPOSITIVE_" + name.upper())
    return float(value)


def _require(parameters: dict, *flags: str) -> None:
    for field in flags:
        if parameters.get(field) is not True:
            raise DomainHold("REGIME_NOT_ATTESTED_" + field.upper())


def _result(kind: str, name: str, value: float, units: str, state: FluidState, details: dict) -> dict:
    if not isfinite(value):
        raise DomainHold("NONFINITE_CALCULATION")
    return {
        "model": kind,
        "existing_kernel_links": list(KERNEL_LINKS[kind]),
        "output": {name: value, "unit": units},
        "source_reference_id": state.source_id,
        "source_properties": {"mu_pa_s": state.mu_pa_s, "rho_kg_m3": state.rho_kg_m3,
                              "temperature_kelvin": state.temperature_kelvin, "pressure_pa": state.pressure_pa},
        "details": details,
        "evidence": EVIDENCE,
        "physical_qualification": False,
        "native_dbr_admitted": False,
        "public_release_authorised": False,
    }


def screen(kind: str, params: dict, state: FluidState | None = None) -> dict:
    """Run separate illustrative laws, never a generalized CFD or measured solution."""
    if kind not in KERNEL_LINKS or kind == "general_cfd_reference":
        raise DomainHold("NO_GENERAL_CFD_NUMERIC_ADAPTER")
    if not isinstance(params, dict):
        raise DomainHold("PARAMETERS_MUST_BE_OBJECT")
    state = state or read_reference_state()
    # No silent fluid-state substitution or reuse at a different T/p.
    if state != read_reference_state():
        raise DomainHold("STATE_NOT_PINNED_TO_REFERENCE_POINT")
    if kind == "laminar_tube":
        _require(params, "steady", "newtonian", "incompressible", "single_phase", "circular", "fully_developed")
        radius = _positive(params, "radius_m")
        length = _positive(params, "length_m")
        q = _positive(params, "flow_m3_s")
        area = pi * radius * radius
        velocity = q / area
        re = state.rho_kg_m3 * velocity * (2 * radius) / state.mu_pa_s
        length_entry = .05 * re * (2 * radius)
        if re >= 2000 or length < length_entry:
            raise DomainHold("POISEUILLE_RE_OR_ENTRANCE_INVALID")
        delta_p = 8 * state.mu_pa_s * length * q / (pi * radius**4)
        return _result(kind, "pressure_drop_pa", delta_p, "Pa", state,
                       {"reynolds": re, "entrance_estimate_m": length_entry,
                        "entrance_criterion": "0.05 Re D approximate laminar entry length",
                        "geometry_basis": "synthetic"})
    if kind == "porous_darcy":
        _require(params, "newtonian", "single_phase", "darcy_regime_assumed")
        if params.get("permeability_basis") != "synthetic_fixture_only":
            raise DomainHold("PERMEABILITY_FIELD_EVIDENCE_MISSING")
        k = _positive(params, "permeability_m2")
        area = _positive(params, "area_m2")
        length = _positive(params, "length_m")
        delta_p = _positive(params, "pressure_drop_pa")
        q = k * area * delta_p / (state.mu_pa_s * length)
        return _result(kind, "flow_m3_s", q, "m3/s", state,
                       {"permeability_basis": "synthetic_fixture_only",
                        "darcy_regime_independently_verified": False,
                        "source_permeability_measurement": None})
    _require(params, "newtonian", "incompressible", "single_phase", "spherical", "isolated_sphere", "creeping_flow_assumed")
    diameter = _positive(params, "diameter_m")
    velocity = _positive(params, "relative_velocity_m_s")
    re = state.rho_kg_m3 * velocity * diameter / state.mu_pa_s
    if re >= .1:
        raise DomainHold("STOKES_RE_INVALID")
    drag = 3 * pi * state.mu_pa_s * diameter * velocity
    return _result(kind, "drag_force_n", drag, "N", state,
                   {"reynolds": re, "wall_corrections_not_included": True,
                    "particle_geometry_basis": "synthetic", "field_verified": False})