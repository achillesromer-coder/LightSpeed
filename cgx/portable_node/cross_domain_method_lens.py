"""Read-only, fail-closed cross-domain method lens over existing CGX /graph/bridges.

A matched SI dimension is not a matched physical quantity, constitutive law,
licence, Object_ID, execution lease or independently verified simulation.
No new graph root, physics solver, runtime, network client or DBR writer.
"""
from __future__ import annotations

from typing import Any

EXPECTED = {
    "NEWTONIAN_VISCOUS_SHEAR": ("mu_dynamic_viscosity", "strain_rate", "deviatoric_stress", "product"),
    "KINEMATIC_VISCOSITY_CONVERSION": ("mu_dynamic_viscosity", "rho_density", "nu_kinematic_viscosity", "ratio"),
    "FOURIER_CONDUCTION": ("k_conductivity", "temperature_gradient", "heat_flux", "product"),
    "FICK_DIFFUSION": ("species_diffusivity", "concentration_gradient", "species_flux", "product"),
}

def _dim(x: Any) -> tuple[int, ...]:
    if not isinstance(x, list) or len(x) != 7 or any(type(a) is not int or abs(a) > 12 for a in x):
        raise ValueError("seven integer SI base-exponents required")
    return tuple(x)


def validate_crosswalk(registry: dict) -> dict:
    if not isinstance(registry, dict) or registry.get("schema") != "CGX-CROSS-DOMAIN-BRIDGE-REGISTRY/0.1":
        raise ValueError("existing CGX bridge registry required")
    cross = registry.get("operator_family_crosswalk")
    if (not isinstance(cross, dict)
        or cross.get("status") != "PROPOSED_METHOD_REUSE_NOT_PHYSICAL_EQUIVALENCE"
        or cross.get("dimension_order") != ["kg", "m", "s", "K", "A", "mol", "cd"]):
        raise ValueError("method/review dimensional authority boundary not declared")
    ops = cross.get("operators", [])
    if not isinstance(ops, list) or not ops:
        raise ValueError("missing operator definitions")
    ids = [x.get("id") for x in ops if isinstance(x, dict)]
    if len(ids) != len(ops) or len(ids) != len(set(ids)) or not all(ids):
        raise ValueError("duplicated operator family")
    for x in ops:
        if x.get("derived_physics_claim") is not False or not x.get("required_qualifiers"):
            raise ValueError("operator asserted physical authority or omitted qualifiers")
    examples = cross.get("constitutive_examples")
    if not isinstance(examples, list) or {x.get("id") for x in examples if isinstance(x, dict)} != set(EXPECTED) or len(examples) != len(EXPECTED):
        raise ValueError("review examples must match independently specified laws")
    for item in examples:
        if item.get("admission") != "proposed" or item.get("operator") not in ids or not item.get("non_equivalence"):
            raise ValueError("automatic promotion or unsupported law equivalence")
        quantities = item.get("quantities")
        if not isinstance(quantities, list) or len(quantities) != 3:
            raise ValueError("requires two operands and one output")
        a, b, out, operation = EXPECTED[item["id"]]
        if [q.get("name") for q in quantities] != [a, b, out]:
            raise ValueError("changed physical quantity identity")
        d0, d1, d2 = (_dim(q.get("si_dimension")) for q in quantities)
        predicted = tuple(x + y if operation == "product" else x - y for x, y in zip(d0, d1))
        if predicted != d2:
            raise ValueError("physical dimension mismatch")
    apps = cross.get("cross_domain_application_candidates")
    if not isinstance(apps, list) or not apps:
        raise ValueError("cross-domain applicability not declared")
    for app in apps:
        if (app.get("relationship") != "METHOD_APPLIES_TO"
            or app.get("status") != "proposed"
            or not isinstance(app.get("operator_ids"), list)
            or any(x not in ids for x in app["operator_ids"])):
            raise ValueError("unqualified cross-domain method admission")
    if "METHOD_APPLIES_TO" not in [b.get("id") for b in registry.get("bridge_types", [])]:
        raise ValueError("existing CGX METHOD_APPLIES_TO bridge type missing")
    return {"schema": "CGX-CROSS-DOMAIN-METHOD-CHECK/0.1",
            "status": "DIMENSIONAL_CONSISTENCY_TESTED_ONLY",
            "validated_examples": sorted(EXPECTED),
            "operator_families": ids,
            "physical_model_validated": False,
            "native_dbr_verified": False,
            "canonical_promotion": False}


def preview_method_reuse(registry: dict, *, domain: str,
                         law_id: str, quantity_name: str,
                         si_dimension: list[int]) -> dict:
    """Return a noncanonical, no-execution decision for a user-selected method."""
    validate_crosswalk(registry)
    cross = registry["operator_family_crosswalk"]
    base = {"schema": "CGX-CROSS-DOMAIN-METHOD-VIEW/0.1",
            "status": "FRONTIER", "domain": domain,
            "law_id": law_id, "quantity_name": quantity_name,
            "operator_family": None,
            "physical_model_validated": False,
            "solver_executed": False,
            "right_to_publish": False,
            "canonical_promotion": False,
            "native_dbr_verified": False,
            "object_id": None}
    if not isinstance(domain, str) or not isinstance(law_id, str) or not isinstance(quantity_name, str):
        raise ValueError("typed method selectors required")
    requested_dim = _dim(si_dimension)
    law = next((x for x in cross["constitutive_examples"] if x["id"] == law_id), None)
    app = next((x for x in cross["cross_domain_application_candidates"] if x["domain"] == domain), None)
    if not law or not app or law["operator"] not in app["operator_ids"]:
        return {**base, "reason": "MISSING_APPLICABILITY_OR_METHOD_EVIDENCE"}
    q = next((x for x in law["quantities"] if x["name"] == quantity_name), None)
    if not q or tuple(q["si_dimension"]) != requested_dim:
        return {**base, "reason": "MISMATCHED_OR_UNKNOWN_PHYSICAL_QUANTITY"}
    return {
        **base,
        "status": "PROPOSED_METHOD_REUSE_ONLY",
        "operator_family": law["operator"],
        "related_existing_bridge_type": "METHOD_APPLIES_TO",
        "constitutive_conditions": list(law["conditions"]),
        "non_equivalence": list(law["non_equivalence"]),
        "remaining_gates": ["owner/counterparty method review", "source evidence and licence",
                            "constitutive model applicability", "measured coefficients",
                            "boundary/initial conditions and units", "independent solver residual/tests",
                            "ACL and signed native DBR receipt"],
    }
