#!/usr/bin/env python3
"""ACHILLES T3 source-only lease scope audit (no effectful execution).

Exercises Neo's existing validator without changing its implementation.
An audit exit code of zero means the negative experiment ran and controls
were meaningful; it does NOT grant execution or establish a safe tool gate.
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

SCHEMA = "ACHILLES-LEASE-SCOPE-NEGATIVE-AUDIT/0.1"


def run():
    lease = base_lease()
    lease["root_authority_receipt_ref"] = "fixture:unverified-root"
    baseline_ok, baseline_reasons, _ = check(lease)

    # The lease declares narrow object/tool/resource bounds. The runtime
    # validator has no requested object/tool/resource arguments, so it cannot
    # compare a particular operation against these declared constraints.
    narrow = base_lease()
    narrow["root_authority_receipt_ref"] = "fixture:unverified-root"
    narrow["scope"] = {
        **narrow["scope"],
        "object_ids": ["fixture:object:allowed-only"],
        "tool_scopes": ["fixture:tool:allowed-only"],
        "resource_budgets": {"compute_seconds": 1},
    }
    narrow_ok, narrow_reasons, _ = check(narrow)
    accepted_parameters = set(inspect.signature(validate_lease).parameters)
    absent_request_bindings = sorted(
        {"object_id", "tool_id", "resource_usage"} - accepted_parameters
    )

    # Existing scope controls establish the experiment is not merely a
    # universal allow; these should continue to deny mismatched requests.
    wrong_task = base_lease()
    wrong_task["root_authority_receipt_ref"] = "fixture:unverified-root"
    wrong_task["scope"]["task_ids"] = ["fixture:other-task"]
    wrong_task_ok, wrong_task_reasons, _ = check(wrong_task)
    task_control = (not wrong_task_ok and any(
        "lease-task-out-of-scope" in r for r in wrong_task_reasons
    ))

    wrong_action = base_lease()
    wrong_action["root_authority_receipt_ref"] = "fixture:unverified-root"
    wrong_action["scope"]["action_classes"] = ["inspect"]
    wrong_action_ok, wrong_action_reasons, _ = check(wrong_action)
    action_control = (not wrong_action_ok and any(
        "lease-action-class-out-of-scope" in r for r in wrong_action_reasons
    ))

    wrong_domain = base_lease()
    wrong_domain["root_authority_receipt_ref"] = "fixture:unverified-root"
    wrong_domain["domains"] = ["eco"]
    wrong_domain_ok, wrong_domain_reasons, _ = check(wrong_domain)
    domain_control = (not wrong_domain_ok and any(
        "lease-domain-out-of-scope" in r for r in wrong_domain_reasons
    ))

    controls_ok = baseline_ok and task_control and action_control and domain_control
    scope_gap = narrow_ok and len(absent_request_bindings) == 3
    output = {
        "schema": SCHEMA,
        "evidence_class": "SOURCE_ONLY_SYNTHETIC_NEGATIVE",
        "candidate_filespace": "Cognigrex.cgx:/agents/leases",
        "baseline_fixture_accepted": baseline_ok,
        "narrow_object_tool_budget_lease_observed": "ALLOW" if narrow_ok else "DENY",
        "requested_object_tool_budget_bindings_absent": absent_request_bindings,
        "controls": {
            "mismatched_task": "DENY" if task_control else "NOT_VERIFIED",
            "mismatched_action": "DENY" if action_control else "NOT_VERIFIED",
            "mismatched_domain": "DENY" if domain_control else "NOT_VERIFIED",
        },
        "gate": "HOLD" if scope_gap else "INDEPENDENT_DOWNSTREAM_PROOF_REQUIRED",
        "authority_limit": (
            "No unauthorized object/tool/resource operation was executed. "
            "This test identifies missing request binding in the inspected "
            "wrapper, not a proven downstream tool bypass, issuer validation, "
            "signed DBR, revocation readback or native admission."
        ),
        "controls_verified": controls_ok,
        "source_only": True,
    }
    print(json.dumps(output, sort_keys=True))
    return 0 if controls_ok else 1


if __name__ == "__main__":
    raise SystemExit(run())
