#!/usr/bin/env python3
"""Achilles T1 independent source-only negative audit.

This deliberately tests the *existing* runtime lease validator, without
modifying Neo's execution code, issuing credentials, or calling effectful tools.
An audit script's successful exit means the test ran, NOT that lease security
passed. A forged acceptance is reported as a HOLD finding.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_cgx_execution_lease import base_lease, check


def main() -> int:
    lease = base_lease()
    lease["root_authority_receipt_ref"] = "fixture:unverified-root-ref"
    baseline_ok, baseline_reasons, _ = check(lease)
    if not baseline_ok:
        print(json.dumps({
            "schema": "ACHILLES-LEASE-ISSUER-NEGATIVE-AUDIT/0.1",
            "audit": "INCONCLUSIVE",
            "reason": "synthetic baseline was not accepted",
            "reasons": baseline_reasons,
            "authority": "NONE",
        }, sort_keys=True))
        return 1

    # T1-A: mutate the issuer to an arbitrary untrusted identifier. The
    # validator has no authenticated issuer registry input or signature proof.
    forged = dict(lease)
    forged["issued_by"] = "fixture:attacker-self-issued"
    forged_ok, forged_reasons, _ = check(forged)

    # T1-B: replace the RootAuthority reference with arbitrary unverified
    # text. String presence is not proof of signed authority.
    fabricated_ref = dict(lease)
    fabricated_ref["root_authority_receipt_ref"] = "fixture:attacker-asserted-root"
    fabricated_ok, fabricated_reasons, _ = check(fabricated_ref)

    # Positive denial control: an explicitly REVOKED state must be rejected.
    # This does NOT test externally revoked ACTIVE leases; no revocation
    # registry or authoritative provider readback is available here.
    revoked = dict(lease)
    revoked["state"] = "REVOKED"
    revoked_ok, revoked_reasons, _ = check(revoked)
    control_denied = not revoked_ok and any(
        reason.startswith("lease-not-active") for reason in revoked_reasons
    )

    result = {
        "schema": "ACHILLES-LEASE-ISSUER-NEGATIVE-AUDIT/0.1",
        "evidence_class": "SOURCE_ONLY_SYNTHETIC_NEGATIVE",
        "candidate_filespace": "Cognigrex.cgx:/assurance",
        "baseline_fixture_accepted": baseline_ok,
        "negative_checks": {
            "forged_issuer_expected": "DENY",
            "forged_issuer_observed": "ALLOW" if forged_ok else "DENY",
            "fabricated_root_ref_expected": "DENY",
            "fabricated_root_ref_observed": "ALLOW" if fabricated_ok else "DENY",
            "explicit_revoked_state_expected": "DENY",
            "explicit_revoked_state_observed": "DENY" if control_denied else "NOT_VERIFIED",
        },
        "gate": "HOLD" if forged_ok or fabricated_ok or not control_denied else "INDEPENDENT_PROVIDER_PROOF_STILL_REQUIRED",
        "native_dbr": "UNVERIFIED",
        "issuer_signature": "UNVERIFIED",
        "revocation_registry": "UNVERIFIED",
        "execution": "NONE",
        "authority_limit": "Audit completion is not an execution lease, issuer verification, owner approval, or release.",
    }
    print(json.dumps(result, sort_keys=True))
    # Fail the audit only if the test itself cannot establish its controls.
    # Do not treat exit 0 as security acceptance; inspect 'gate' and observed.
    return 0 if control_denied else 1


if __name__ == "__main__":
    raise SystemExit(main())
