"""Read-only, conservative archive claim comparison and payoff proposal.

One source blob may underlie many semantic records. No canon changes; all outputs
are review candidates preserving source IDs, evidence and temporal frames.
"""
from __future__ import annotations
import json
import re
from datetime import date

HASH = re.compile(r"^[a-f0-9]{64}$")

def _validated(claim: dict) -> dict:
    if not isinstance(claim, dict):
        raise ValueError("claim must be a source-scoped record")
    for key in ("claim_id", "source_ref", "object_id", "field"):
        if not isinstance(claim.get(key), str) or not claim[key].strip():
            raise ValueError("missing claim identity or source field")
    if not isinstance(claim.get("sha256"), str) or not HASH.fullmatch(claim["sha256"]):
        raise ValueError("full source SHA-256 required")
    if "value" not in claim or claim["value"] is None:
        raise ValueError("claim value must be supplied explicitly, not imputed")
    if not isinstance(claim.get("unit"), str):
        raise ValueError("unit must be explicitly set; use empty string only for dimensionless values")
    if claim.get("effective_date") is not None:
        if not isinstance(claim["effective_date"], str):
            raise ValueError("invalid effective date")
        try: date.fromisoformat(claim["effective_date"])
        except ValueError as exc: raise ValueError("effective_date must be ISO date") from exc
    return claim

def classify_claim_pair(left: dict, right: dict) -> dict:
    a, b = _validated(left), _validated(right)
    same_value = (type(a["value"]) is type(b["value"]) and a["value"] == b["value"])
    date_a, date_b = a.get("effective_date"), b.get("effective_date")
    if a["object_id"] != b["object_id"]:
        kind, reason = "DIFFERENT_REFERENTS", "Object_ID differs; typed bridge or independently reviewed equivalence required"
    elif a["field"] != b["field"]:
        kind, reason = "NON_OVERLAPPING_ATTRIBUTES", "Different attributes may coexist; no overwriting"
    elif a["unit"] != b["unit"]:
        kind, reason = "UNIT_CONVERSION_FRONTIER", "Dimension/basis and qualified conversion required before comparison"
    elif same_value and a["sha256"] == b["sha256"] and date_a == date_b:
        kind, reason = "EXACT_SOURCE_CLAIM_CANDIDATE", "Same source bytes and typed claim fields; preserve independent references"
    elif same_value:
        kind, reason = "CORROBORATION_CANDIDATE", "Matching claim value is not proof of independent confirmation"
    elif date_a and date_b and date_a != date_b:
        kind, reason = "TEMPORAL_VARIANT", "Distinct effective dates; retain both versions pending domain chronology review"
    else:
        kind, reason = "CONTRADICTORY_HOLD", "Same referent/field/unit has incompatible values without sufficient temporal separation"
    receipt = {
        "schema": "CGX-ARCHIVE-PAYOFF-REVIEW/0.1", "state": "NONCANONICAL_REVIEW",
        "classification": kind, "reason": reason, "promote_canon": False,
        "source_claims": [{"claim_id":v["claim_id"], "source_ref":v["source_ref"],
                           "sha256":v["sha256"], "object_id":v["object_id"],
                           "effective_date":v.get("effective_date")}
                          for v in (a,b)],
        "loss_map": [], "preserve_originals": True,
        "tradeoffs": {
            "duplicate_bytes_savings": None,
            "actual_roundtrip_fidelity": "UNTESTED",
            "semantic_authority": "UNASSIGNED",
            "review_cost": "UNMEASURED",
            "reconstruction_requirement": "INDEPENDENT_SOURCE_CHECK",
            "rights": "REVIEW_REQUIRED"
        },
        "recommended_action": {
            "EXACT_SOURCE_CLAIM_CANDIDATE":"link and retain sources",
            "CORROBORATION_CANDIDATE":"test source independence and method",
            "TEMPORAL_VARIANT":"build time-indexed claims, do not erase",
            "CONTRADICTORY_HOLD":"hold parallel evidence for owner decision",
            "UNIT_CONVERSION_FRONTIER":"verify dimension and unit transform",
            "NON_OVERLAPPING_ATTRIBUTES":"link independently held attributes",
            "DIFFERENT_REFERENTS":"propose typed relation only"
        }[kind]
    }
    return receipt

if __name__ == "__main__":
    import sys
    data=json.load(sys.stdin)
    print(json.dumps(classify_claim_pair(data["left"],data["right"]),indent=2))
