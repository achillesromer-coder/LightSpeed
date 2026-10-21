"""Source-bound CGX fluid governing-operator cross-domain *review projection*.

Reuses original UTP-137 VGK-019/020/036/039, not a new CFD solver.
Only evaluates an explicitly hypothetical Hagen–Poiseuille example under
stated conditions. No physical authority, owner DBR, release or executable
third-party adapter is granted. This file does not modify the owner atlas.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "cgx/component_atlas/type1_volumetric_kernel_v0_1.json"
KERNEL_IDS = ("VGK-019", "VGK-020", "VGK-036", "VGK-039")
SOURCE_GIT_BLOB = "c5e92038495a15a66fb6008925a1bb3e92d7bd8b"

# Exponents of SI base M, L and T. These are identities, not observations.
DIMENSIONS = {
    "dynamic_viscosity_Pa_s": (1, -1, -1),
    "density_kg_m3": (1, -3, 0),
    "kinematic_viscosity_m2_s": (0, 2, -1),
    "velocity_m_s": (0, 1, -1),
    "length_m": (0, 1, 0),
    "flow_m3_s": (0, 3, -1),
    "pressure_Pa": (1, -1, -2),
    "dimensionless": (0, 0, 0),
}
ASSUMPTIONS = (
    "newtonian", "single_phase", "incompressible", "steady",
    "fully_developed", "no_slip", "rigid_circular_wall", "isothermal"
)
EXAMPLES = {
    "fluid_channel": {
        "kernels": ["VGK-019", "VGK-039"],
        "shared_operator": "mass_momentum_balance_with_constitutive_dynamic_viscosity",
        "domain_dependencies": ["exact circular geometry", "no slip", "Re and entrance length", "fluid mu(T),rho(T)"],
        "numeric_state": "CONDITIONAL_SYNTHETIC_EXAMPLE_ONLY",
    },
    "porous_or_wicking_flow": {
        "kernels": ["VGK-020", "VGK-039"],
        "shared_operator": "fluid_mass_balance_plus_effective_permeability",
        "domain_dependencies": ["measured permeability tensor", "Darcy regime", "saturation", "wetting/fouling"],
        "numeric_state": "SOURCE_ONLY_UNMEASURED_PERMEABILITY",
    },
    "external_aerodynamics": {
        "kernels": ["VGK-039"],
        "shared_operator": "mass_momentum_balance_plus_fluid_stress",
        "domain_dependencies": ["Mach/compressibility", "Re", "boundary layer", "turbulence closure", "atmospheric state"],
        "numeric_state": "SOURCE_ONLY_NO_CFD_OR_WIND_TUNNEL",
    },
    "printspace_resin_or_inert_gas": {
        "kernels": ["VGK-019", "VGK-039", "VGK-036"],
        "shared_operator": "flow_plus_constitutive_interface_and_process_state",
        "domain_dependencies": ["shear-dependent viscosity test", "cure/thermal history", "wetting", "directional X-to-Y compatibility", "gas state"],
        "numeric_state": "HOLD_MATERIAL_AND_PROCESS_DATA",
    },
    "corridor_misting": {
        "kernels": ["VGK-039", "VGK-036"],
        "shared_operator": "fluid_momentum_and_species_transport",
        "domain_dependencies": ["droplet size", "ambient wind", "multiphase deposition", "public exposure", "site controls"],
        "numeric_state": "HOLD_SITE_AND_MULTIPHASE_TESTS",
    },
    "orbital_propellant_and_microgravity": {
        "kernels": ["VGK-039", "VGK-036"],
        "shared_operator": "fluid_momentum_and_phase_interface",
        "domain_dependencies": ["acceleration history", "surface tension", "contact angle", "vapor/gas", "slosh", "thermal state"],
        "numeric_state": "HOLD_FLIGHT_RELEVANT_TESTS",
    },
}

def _source_qualified_kernels(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    path = root / SOURCE
    if path.is_symlink() or not path.is_file():
        raise ValueError("OWNER_KERNEL_SOURCE_MISSING_OR_SYMLINK")
    raw = path.read_bytes()
    if not raw or len(raw) > 2_000_000:
        raise ValueError("OWNER_KERNEL_SOURCE_SIZE_HOLD")
    git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()
    if git_blob != SOURCE_GIT_BLOB:
        raise ValueError("OWNER_KERNEL_SOURCE_CHANGED_REVIEW_REQUIRED")
    obj = json.loads(raw)
    if obj.get("schema") != "CGX-TYPE1-VOLUMETRIC-KERNEL/0.1" or obj.get("artifact_id") != "UTP-137":
        raise ValueError("OWNER_KERNEL_SCHEMA_HOLD")
    records = obj.get("records")
    if not isinstance(records, list) or len(records) != obj.get("record_count"):
        raise ValueError("OWNER_KERNEL_COUNT_HOLD")
    indexed = {r.get("kernel_id"): r for r in records if isinstance(r, dict)}
    if len(indexed) != len(records) or not all(id in indexed for id in KERNEL_IDS):
        raise ValueError("OWNER_KERNEL_MISSING_OR_DUPLICATE")
    for id in KERNEL_IDS:
        if not indexed[id].get("numeric_inference_gate") or not indexed[id].get("verification_falsifier"):
            raise ValueError("OWNER_KERNEL_UNQUALIFIED_GATE")
    return indexed, {"path": SOURCE, "git_blob_sha1": git_blob,
                     "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                     "owner_artifact": "UTP-137", "authority": "OWNER_ATLAS_NOT_MODIFIED"}

def project_fluid_reuse(root: Path = ROOT) -> dict[str, Any]:
    """Lightweight typed edges over the existing family; zero authority uplift."""
    rows, source = _source_qualified_kernels(root)
    return {
        "schema": "CGX-FLUID-CROSS-DOMAIN-SOURCE-PROJECTION/0.1",
        "state": "REVIEW_ONLY_NOT_A_SOLVER_OR_NEW_CGX_FAMILY",
        "parent": "Cognigrex.cgx",
        "existing_source": source,
        "referenced_original_kernels": [
            {"id": id, "compiler_token": rows[id]["compiler_token"],
             "numeric_inference_gate": rows[id]["numeric_inference_gate"],
             "verification_falsifier": rows[id]["verification_falsifier"]}
            for id in KERNEL_IDS
        ],
        "shared_property": {
            "dynamic_viscosity": {"symbol": "mu", "unit": "Pa*s",
                                  "depends_on": ["material identity", "temperature",
                                                 "pressure where relevant", "shear rate where relevant"]},
            "kinematic_viscosity": {"symbol": "nu", "unit": "m2/s",
                                    "definition": "mu/rho", "requires": ["mu>0", "rho>0"]},
        },
        "domain_bindings": EXAMPLES,
        "dimensions_MLT": DIMENSIONS,
        "numeric_execution": "HYPOTHETICAL_PIPE_BASELINE_ONLY",
        "independent_evidence": False,
        "physical_validation": False,
        "new_solver_installed": False,
        "material_licence_granted": False,
        "public_release_authorised": False,
        "native_two_node_accepted": False,
        "owner_dbr_promoted": False,
        "issues_held": [158, 161],
    }

def _positive_si(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("INVALID_SI_VALUE:" + field)
    v = float(value)
    if not math.isfinite(v) or not 0.0 < v <= 1e12:
        raise ValueError("INVALID_SI_VALUE:" + field)
    return v

def screen_pipe_baseline(params: dict[str, object], root: Path = ROOT) -> dict[str, Any]:
    """Synthetic circular-pipe law screen, NEVER a measured/approved pressure rating.

    Models laminar, steady, fully developed, Newtonian, single-phase,
    incompressible, no-slip, rigid circular, isothermal *assumptions*.
    Re < 2000 and estimated entrance length are conservative screening
    requirements, not sufficient real-world evidence to accept a process.
    """
    _, source = _source_qualified_kernels(root)
    if not isinstance(params, dict) or set(params) != {
        "dynamic_viscosity_Pa_s", "density_kg_m3", "volume_flow_m3_s",
        "radius_m", "length_m", "conditions"
    }:
        raise ValueError("REQUIRED_EXACT_PIPE_INPUT_SCHEMA")
    mu = _positive_si(params["dynamic_viscosity_Pa_s"], "dynamic_viscosity_Pa_s")
    rho = _positive_si(params["density_kg_m3"], "density_kg_m3")
    Q = _positive_si(params["volume_flow_m3_s"], "volume_flow_m3_s")
    r = _positive_si(params["radius_m"], "radius_m")
    L = _positive_si(params["length_m"], "length_m")
    conditions = params["conditions"]
    if not isinstance(conditions, dict) or set(conditions) != set(ASSUMPTIONS):
        raise ValueError("EXACT_CONDITION_FLAGS_REQUIRED")
    if any(not isinstance(conditions[k], bool) for k in ASSUMPTIONS):
        raise ValueError("CONDITIONS_MUST_BE_BOOLEAN")
    diameter = 2.0*r
    area = math.pi*r*r
    u = Q/area
    Re = rho*u*diameter/mu
    nu = mu/rho
    entrance_estimate_m = 0.05*Re*diameter
    if not all(math.isfinite(v) for v in (diameter, u, Re, nu, entrance_estimate_m)):
        raise ValueError("NONFINITE_DERIVED_SCREEN")
    holds = [k.upper()+"_NOT_ATTESTED" for k in ASSUMPTIONS if conditions[k] is not True]
    if Re >= 2000.0:
        holds.append("REYNOLDS_ABOVE_CONSERVATIVE_LAMINAR_SCREEN")
    if L <= entrance_estimate_m:
        holds.append("ENTRANCE_LENGTH_SCREEN_NOT_MET")
    if not math.isfinite(8.0*mu*L*Q/(math.pi*r**4)):
        holds.append("NUMERICAL_SCALE_UNRELIABLE")
    pressure_pa = None if holds else 8.0*mu*L*Q/(math.pi*r**4)
    return {
        "schema": "CGX-SYNTHETIC-FLUID-CIRCULAR-PIPE-SCREEN/0.1",
        "source": source,
        "kernel_id": "VGK-019",
        "viscosity_nu_m2_s": nu,
        "mean_velocity_m_s": u,
        "reynolds_dimensionless": Re,
        "entrance_estimate_m": entrance_estimate_m,
        "pressure_drop_Pa": pressure_pa,
        "screen_state": "SYNTHETIC_BASELINE_CONDITIONAL" if not holds else "HOLD_REGIME_OR_CONDITION",
        "holds": holds,
        "source_and_condition_quality": "USER_ASSERTED_SYNTHETIC_ONLY_NO_MEASURED_INPUTS",
        "physical_validation": False,
        "pressure_rating": None,
        "certification": False,
        "public_release_authorised": False,
        "owner_dbr_promoted": False,
    }
