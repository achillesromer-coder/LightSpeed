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



def screen_passive_bistatic_inputs(*, reference: dict | None,
                                  surveillance: dict | None,
                                  geometry: dict | None) -> dict:
    """Metadata-only passive bistatic sensing screen; NO signal processing.

    The synthetic 'candidate' geometry is a hypothesis, not a located target.
    All supplied provenance/calibration identifiers are caller assertions:
    original bytes, instrument calibration, rights and measurements are
    NEVER independently verified by this function.
    """
    from decimal import Decimal
    from datetime import datetime, timezone
    c_m_s = Decimal("299792458")
    required_channel = {
        "channel_id", "source_locator", "center_hz", "bandwidth_hz",
        "sampling_hz", "epoch_utc", "timebase_id", "calibration_id",
        "noise_floor_dbm",
    }
    required_geometry = {
        "frame_id", "epoch_utc", "tx_rx_m",
        "tx_to_hypothesis_m", "hypothesis_to_rx_m",
    }
    holds: list[str] = []
    def ident(v: object, label: str) -> str:
        if not isinstance(v, str) or not v.strip() or len(v) > 256:
            raise ValueError("Invalid typed identifier: " + label)
        return v.strip()
    def instant(v: object) -> str:
        s = ident(v, "epoch_utc")
        if not s.endswith("Z"):
            raise ValueError("Explicit UTC epoch required")
        try:
            parsed = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError("Invalid UTC epoch") from e
        if parsed.utcoffset() != timezone.utc.utcoffset(None):
            raise ValueError("Invalid UTC offset")
        return parsed.isoformat()
    def positive(v: object, label: str) -> Decimal:
        d = _nonnegative_number(v)
        if d == 0 or d > Decimal("1e15"):
            raise ValueError("Invalid positive physical input: " + label)
        return d
    def channel(name: str, obj: dict | None) -> dict | None:
        if obj is None:
            holds.append("MISSING_" + name.upper() + "_CHANNEL")
            return None
        if not isinstance(obj, dict) or set(obj) != required_channel:
            raise ValueError("Exact " + name + " channel schema required")
        out = {k: ident(obj[k], name + "." + k) for k in
               ("channel_id", "source_locator", "timebase_id", "calibration_id")}
        out["epoch_utc"] = instant(obj["epoch_utc"])
        for key in ("center_hz", "bandwidth_hz", "sampling_hz"):
            out[key] = positive(obj[key], name + "." + key)
        if isinstance(obj["noise_floor_dbm"], bool):
            raise ValueError("Invalid asserted noise-floor metadata")
        try:
            out["noise_floor_dbm"] = Decimal(str(obj["noise_floor_dbm"]))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("Invalid asserted noise-floor metadata") from exc
        if not out["noise_floor_dbm"].is_finite():
            raise ValueError("Invalid asserted noise-floor metadata")
        if out["bandwidth_hz"] >= out["sampling_hz"]:
            holds.append(name.upper() + "_BANDWIDTH_NOT_BELOW_SAMPLE_RATE")
        return out
    a = channel("reference", reference)
    b = channel("surveillance", surveillance)
    delay = None
    if a is not None and b is not None:
        if a["channel_id"] == b["channel_id"]:
            holds.append("INDEPENDENT_CHANNEL_IDENTITIES_REQUIRED")
        if a["epoch_utc"] != b["epoch_utc"] or a["timebase_id"] != b["timebase_id"]:
            holds.append("COMMON_TIMEBASE_NOT_DECLARED")
        low = max(a["center_hz"] - a["bandwidth_hz"]/2,
                  b["center_hz"] - b["bandwidth_hz"]/2)
        high = min(a["center_hz"] + a["bandwidth_hz"]/2,
                   b["center_hz"] + b["bandwidth_hz"]/2)
        if high <= low:
            holds.append("NO_SHARED_DECLARED_RF_BAND")
    if geometry is None:
        holds.append("MISSING_BISTATIC_GEOMETRY")
    else:
        if not isinstance(geometry, dict) or set(geometry) != required_geometry:
            raise ValueError("Exact hypothetical bistatic geometry required")
        ident(geometry["frame_id"], "geometry.frame_id")
        epoch = instant(geometry["epoch_utc"])
        if (a is not None and epoch != a["epoch_utc"] or
            b is not None and epoch != b["epoch_utc"]):
            holds.append("GEOMETRY_EPOCH_MISMATCH")
        direct = positive(geometry["tx_rx_m"], "tx_rx_m")
        d1 = positive(geometry["tx_to_hypothesis_m"], "tx_to_hypothesis_m")
        d2 = positive(geometry["hypothesis_to_rx_m"], "hypothesis_to_rx_m")
        if d1+d2 < direct or d1+direct < d2 or d2+direct < d1:
            holds.append("GEOMETRIC_TRIANGLE_INCONSISTENT")
        else:
            delay = (d1 + d2 - direct) / c_m_s
    return {
        "schema": "CGX-PASSIVE-BISTATIC-INPUT-REVIEW/0.1",
        "status": ("HOLD_MISSING_OR_INCOMPATIBLE_INPUTS" if holds
                   else "SYNTHETIC_METADATA_SHAPE_COMPLETE_ONLY"),
        "holds": sorted(set(holds)),
        "hypothetical_excess_path_delay_s": str(delay) if delay is not None else None,
        "physical_source_class": "EXTERNAL_ILLUMINATOR_OF_OPPORTUNITY",
        "existing_profile": "AMBIENT_BISTATIC_RADAR",
        "original_source_bytes_verified": False,
        "calibration_independently_verified": False,
        "measured_signal_processed": False,
        "target_detected_or_tracked": False,
        "transmitter_activated": False,
        "right_to_publish": False,
        "owner_dbr_verified": False,
        "sai_or_country_network_enabled": False,
        "remaining_gates": [
            "original two-channel bytes/source hashes and lawful rights",
            "coherent timebase and independently calibrated receiver/noise",
            "real geometry/epoch and error covariance",
            "actual measured delay-Doppler processing and false-alarm controls",
            "owner ACL/native DBR and release approvals",
        ],
    }


def load_and_review(root: Path | None = None) -> dict:
    base = root or HERE
    corpus = json.loads((base / REVIEW_PATH.name).read_text(encoding="utf-8"))
    registry = json.loads((base.parent / "domain_templates" / REGISTRY_PATH.name).read_text(encoding="utf-8"))
    return review_cross_scale(corpus, registry)


if __name__ == "__main__":
    print(json.dumps(load_and_review(),sort_keys=True))
