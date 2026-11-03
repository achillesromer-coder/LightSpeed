#!/usr/bin/env python3
"""Achilles T2: non-effectful lease replay/consumption boundary audit.

Source-only synthetic fixtures; a successful audit run is NOT a security pass.
This calls Neo's existing validator, never a provider write or tool executor.
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_cgx_agent_runtime import validate_lease
from validate_cgx_execution_lease import base_lease, check

SCHEMA = "ACHILLES-LEASE-REPLAY-NEGATIVE-AUDIT/0.1"


def main() -> int:
    lease = base_lease()
    lease["root_authority_receipt_ref"] = "fixture:unverified-root"
    # Synthetic one-use constraint illustrates that the validator has no
    # authenticated consumption registry; not a claim that all leases are
    # inherently one-shot or that this extension is an accepted contract.
    lease["scope"]["max_uses"] = 1
    lease["scope"]["request_nonce"] = "fixture:nonce:one"

    first_ok, first_reasons, _ = check(lease)
    second_ok, second_reasons, _ = check(lease)
    accepted_parameters = set(inspect.signature(validate_lease).parameters)
    missing_replay_bindings = sorted(
        {"request_nonce", "consumption_registry", "request_principal"} - accepted_parameters
    )

    consumed = base_lease()
    consumed["root_authority_receipt_ref"] = "fixture:unverified-root"
    consumed["state"] = "CONSUMED"
    consumed_ok, consumed_reasons, _ = check(consumed)
    consumed_control = (
        not consumed_ok
        and any(r.startswith("lease-not-active") for r in consumed_reasons)
    )

    wrong_task = base_lease()
    wrong_task["root_authority_receipt_ref"] = "fixture:unverified-root"
    wrong_task["scope"]["task_ids"] = ["fixture:other-task"]
    task_ok, task_reasons, _ = check(wrong_task)
    task_control = (
        not task_ok
        and any("lease-task-out-of-scope" in r for r in task_reasons)
    )

    gap = first_ok and second_ok and len(missing_replay_bindings) == 3
    controls_ok = first_ok and consumed_control and task_control
    result = {
        "schema": SCHEMA,
        "candidate_filespace": "Cognigrex.cgx:/agents/leases",
        "evidence_class": "SOURCE_ONLY_SYNTHETIC_NEGATIVE",
        "first_use_observed": "ALLOW" if first_ok else "DENY",
        "same_lease_second_use_observed": "ALLOW" if second_ok else "DENY",
        "single_use_fixture_declared": True,
        "missing_authenticated_request_bindings": missing_replay_bindings,
        "controls": {
            "explicit_CONSUMED_state": "DENY" if consumed_control else "NOT_VERIFIED",
            "wrong_task": "DENY" if task_control else "NOT_VERIFIED",
        },
        "gate": "HOLD" if gap else "INDEPENDENT_DOWNSTREAM_PROOF_REQUIRED",
        "controls_verified": controls_ok,
        "authority_limit": (
            "The inspected source-level validator cannot prove nonce consumption, "
            "caller principal, or registry-backed replay rejection. This does not "
            "prove that a downstream tool gate permits replay. No effectful "
            "operation, signed issuer, revocation lookup, native DBR, or "
            "RootAuthority admission was exercised."
        ),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if controls_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
