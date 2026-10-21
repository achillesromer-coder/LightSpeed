"""Read-only Alexandria cross-scale review overlay validator.

This is a method/source ontology check, not a universal physics solver,
engineering simulator, planetary capture algorithm, SAI operator or DBR writer.
It validates projections against existing shared CGX bridge schema only.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REVIEW_PATH = HERE / "alexandria_cross_scale_interaction_review_20261021.json"
REGISTRY_PATH = HERE.parent / "domain_templates" / "cross_domain_bridge_registry.json"
OPERATOR_IDS = {
    "mass_energy_interface", "momentum_transfer", "maxwell_boundary",
    "wave_propagation", "typed_information_flow",
}
REQUIRED_HOLDS = {
    "new_physical_solver", "verified_planet_manufacture", "verified_orbital_capture",
    "net_energy_gain_from_ambient", "verified_elf_broadband_network",
    "SAI_enabled", "cross_country_network_enabled", "public_release_authorized",
    "native_dbr_accepted",
}
SYSTEM_IDS = {
    "PRINTSPACE_4D", "MARK_III_MOTION", "LUKE_II_EM_BOUNDARY",
    "ASTEROID_SPACEJUNK_CAPTURE", "ICE_REGOLITH_PLANETARY_COMPOSITION",
    "POLLUTANT_ECOLOGICAL_REHAB", "SOLAR_SPECTROSCOPY",
    "AMBIENT_BISTATIC_RADAR", "APOSTLES_EM_COUNTERFIELD",
    "SCHUMANN_ELF_MEASUREMENT", "CGX_DATA_EXCHANGE", "SAI_AU_REGION",
}
ANALOGY_TYPES = {
    "STRUCTURAL_ANALOGY_ONLY", "REUSE_KINEMATIC_METHOD_WITH_CONDITIONS",
    "SHARED_MASS_MOMENTUM_BOOKKEEPING", "REUSE_SPECTRAL_METHOD_WITH_CONDITIONS",
    "SHARED_MAXWELL_OPERATOR_NOT_DEVICE_VALIDATION", "METAPHOR_ONLY",
    "SHARED_MATERIAL_ACCOUNTING_NOT_ECO_EQUIVALENCE",
    "POLICY_BINDING_NOT_NETWORK_ACTIVATION",
}


def review_cross_scale(corpus: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(corpus, dict) or corpus.get("schema") != "CGX-ALEXANDRIA-CROSS-SCALE-INTERACTION-REVIEW/0.1":
        raise ValueError("Cross-scale candidate schema missing")
    if corpus.get("status") != "OWNER_REVIEW_NONCANONICAL" or corpus.get("parent") != "Cognigrex.cgx":
        raise ValueError("Not owner review or changed parent")
    if not isinstance(registry, dict) or registry.get("schema") != "CGX-CROSS-DOMAIN-BRIDGE-REGISTRY/0.1":
        raise ValueError("Existing CGX cross-domain bridge required")
    if corpus.get("bridge_location") != registry.get("location") or corpus["bridge_location"] != "Cognigrex.cgx:/graph/bridges":
        raise ValueError("Duplicated/relocated graph root")
    if corpus.get("unit_basis") != ["kg", "m", "s", "K", "A", "mol", "cd"]:
        raise ValueError("SI basis mismatch")
    required_extensions = {
        "CGX-CROSS-DOMAIN-BRIDGE-REGISTRY/0.1",
        "CGX-SOURCE-ENVELOPE/0.1", "CGX-UNIVERSAL-OBJECT-EXTENSION/0.1",
    }
    if set(corpus.get("extends_existing", [])) != required_extensions:
        raise ValueError("Existing source/identity contracts replaced")
    flags = corpus.get("authority_flags")
    if not isinstance(flags, dict) or set(flags) != REQUIRED_HOLDS or any(v is not False for v in flags.values()):
        raise ValueError("Unverified engineering or authority silently promoted")
    operators = corpus.get("operators")
    if not isinstance(operators, list) or {x.get("id") for x in operators if isinstance(x, dict)} != OPERATOR_IDS or len(operators) != len(OPERATOR_IDS):
        raise ValueError("Cross-scale operator family mismatch")
    for op in operators:
        if op.get("authority") is None or "only" not in op["authority"].lower() or not op.get("not_equal"):
            raise ValueError("Operator claimed physics equivalence")
    profiles = corpus.get("cross_scale_records")
    if not isinstance(profiles, list) or len(profiles) != len(SYSTEM_IDS):
        raise ValueError("Missing cross-domain family")
    ids = [x.get("id") for x in profiles if isinstance(x, dict)]
    if len(ids) != len(SYSTEM_IDS) or set(ids) != SYSTEM_IDS:
        raise ValueError("Missing or duplicated source profile")
    for profile in profiles:
        if profile.get("operator_ref") not in OPERATOR_IDS or profile.get("owner_domain") not in {"romer","emassc","eco","lightspeed"}:
            raise ValueError("Invalid operator or owner authority")
        if any(profile.get(k) is not False for k in ("canonical", "executable", "rights_clearance")):
            raise ValueError("Physical execution or rights promoted")
        if profile.get("object_id") is not None:
            raise ValueError("Fabricated canonical Object_ID")
        if profile.get("source_state") != "SOURCE_POINTERS_ONLY_PENDING_ITEMIZED_LINKAGE":
            raise ValueError("Unverified per-object source lineage promoted")
        for key in ("exchange_carriers","required_qualification"):
            if not isinstance(profile.get(key), list) or len(profile[key]) < 2 or not all(isinstance(s,str) and s.strip() for s in profile[key]):
                raise ValueError("Insufficient exchange/qualification data")
        if not isinstance(profile.get("non_equivalence"),str) or not profile["non_equivalence"]:
            raise ValueError("Cross-scale non-equivalence omitted")
    edges = corpus.get("analogies")
    if not isinstance(edges, list) or len(edges) != len(ANALOGY_TYPES):
        raise ValueError("Missing cross-scale adjacency")
    if {x.get("relation") for x in edges} != ANALOGY_TYPES or len({x.get("id") for x in edges}) != len(edges):
        raise ValueError("Analogy relation type duplicated/missing")
    for edge in edges:
        if edge.get("a") not in SYSTEM_IDS or edge.get("b") not in SYSTEM_IDS or edge["a"] == edge["b"]:
            raise ValueError("Unresolved or self-referential cross-family relation")
        if not edge.get("distinct") or not edge.get("overlap"):
            raise ValueError("Analogy falsely equivalent")
    ledgers = corpus.get("conservation_ledgers",{})
    if not isinstance(ledgers,dict) or set(ledgers) != {
        "mass_kg","energy_J","momentum_kg_m_s","charge_C","spectral_W","signal","information"
    }:
        raise ValueError("Missing conservation/transfer bookkeeping")
    if not isinstance(corpus.get("validation_gates"),list) or len(corpus["validation_gates"]) != 7:
        raise ValueError("Independent qualification gates absent")
    if not isinstance(corpus.get("frontier"),list) or len(corpus["frontier"]) < 4:
        raise ValueError("Critical unresolved physics suppressed")
    return {
        "schema": "CGX-ALEXANDRIA-CROSS-SCALE-REVIEW-RECEIPT/0.1",
        "state": "SOURCE_ONLY_REVIEW_NO_DB_R_OR_PUBLIC_RELEASE",
        "operator_count": len(operators),
        "profile_count": len(profiles),
        "bridge_count": len(edges),
        "source_qualified_objects": 0,
        "functional_simulations": 0,
        "canonical_mutations": 0,
        "physical_authority_granted": False,
        "sai_authority_granted": False,
        "natural_network_verified": False,
        "public_release_authorized": False,
        "native_dbr_verified": False,
        "issues_held": [158,161],
    }


def _nonnegative_number(value: Any) -> Decimal:
    if isinstance(value,bool) or not isinstance(value, (int,float,str,Decimal)):
        raise ValueError("Finite nonnegative scalar required")
    try:
        v = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid scalar") from exc
    if not v.is_finite() or v < 0:
        raise ValueError("Finite nonnegative scalar required")
    return v


def screen_flux_ledger(*, incoming: Any, outgoing: Any, stored_delta: Any,
                       tolerance: Any = "0.00000001", unit: str) -> dict:
    """Synthetic accounting identity only; not a physical dynamics model.

    All flows crossing a defined boundary must be included by the caller,
    including emitted waste heat or released pollutant mass.
    """
    if unit not in ("kg", "J", "C"):
        raise ValueError("Unsupported ledger unit; no unit coercion")
    a, b = _nonnegative_number(incoming), _nonnegative_number(outgoing)
    if isinstance(stored_delta,bool) or not isinstance(stored_delta,(int,float,str,Decimal)):
        raise ValueError("Invalid signed storage delta")
    try:
        c = Decimal(str(stored_delta))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid signed storage delta") from exc
    t = _nonnegative_number(tolerance)
    if not c.is_finite() or t >= 1:
        raise ValueError("Nonfinite delta or excessive tolerance")
    residual = a - b - c
    reference = max(abs(a), abs(b), abs(c), Decimal("1"))
    return {
        "unit": unit, "residual": str(residual),
        "relative_residual": str(abs(residual)/reference),
        "status": "ACCOUNTING_IDENTITY_PASSED_SYNTHETIC_ONLY" if abs(residual) <= t*reference
                  else "HOLD_UNBALANCED_FLUX",
        "empirical_validation": False,
        "native_dbr_verified": False,
    }


def screen_passive_power(*, incident_w_m2: Any, area_m2: Any, efficiency: Any,
                         claimed_harvest_w: Any) -> dict:
    flux, area, eta, claim = (_nonnegative_number(v) for v in
                            (incident_w_m2,area_m2,efficiency,claimed_harvest_w))
    if eta > 1:
        raise ValueError("Efficiency cannot exceed unity")
    bound = flux*area*eta
    return {
        "available_upper_bound_w": str(bound),
        "status": "BOUND_COMPATIBLE_SYNTHETIC_ONLY" if claim <= bound
                  else "HOLD_PASSIVE_ENERGY_VIOLATION",
        "empirical_validation": False,
        "usable_energy_verified": False,
        "source_irradiance_measured": False,
    }


def load_and_review(root: Path | None = None) -> dict:
    base = root or HERE
    corpus = json.loads((base / REVIEW_PATH.name).read_text(encoding="utf-8"))
    registry = json.loads((base.parent / "domain_templates" / REGISTRY_PATH.name).read_text(encoding="utf-8"))
    return review_cross_scale(corpus, registry)


if __name__ == "__main__":
    print(json.dumps(load_and_review(),sort_keys=True))
