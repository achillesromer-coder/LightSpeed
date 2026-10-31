#!/usr/bin/env python3
from __future__ import annotations
from datetime import UTC, datetime, timedelta
import copy
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_cgx_agent_runtime import validate_lease

def base_lease():
    now=datetime.now(UTC)
    return {
      "lease_id":"fixture:lease:prelaunch",
      "lease_class":"DIGITAL_WRITE",
      "state":"ACTIVE",
      "issued_by":"fixture:root-authority",
      "subject_agent":"Neo",
      "valid_from":(now-timedelta(minutes=5)).isoformat(),
      "valid_until":(now+timedelta(hours=1)).isoformat(),
      "domains":["romer"],
      "execution_depths":["execute","publish"],
      "max_cascade_class":"C3",
      "allowed_floors":["Neo"],
      "scope":{"task_ids":["CGX-LAUNCH-006"],"action_classes":["execute","publish"]},
      "revocable":True,
      "rollback_or_recovery_ref":"fixture:rollback",
      "assurance_receipt_ref":"fixture:assurance",
      "custodial_receipt_ref":"fixture:custodial",
      "risk_acceptance_ref":"fixture:risk",
      "authority_phase":"PRE_LAUNCH",
      "authority_phase_ref":"cgx://internal/governance/root-authority-phase"
    }

def check(lease, execution_depth="execute", action_class="execute", consequential=True, project_id=None, object_id=None, tool_scope=None, configuration_id=None):
    return validate_lease(
      lease,
      agent_id="Neo",
      domain="romer",
      execution_depth=execution_depth,
      cascade_class="C2",
      task_id="CGX-LAUNCH-006",
      project_id=project_id,
      action_class=action_class,
      execution_class="DIGITAL_WRITE",
      planned_floors=["Neo"],
      consequential=consequential,
      object_id=object_id,
      tool_scope=tool_scope,
      configuration_id=configuration_id,
    )

def main():
    failures=[]
    x=base_lease()
    ok,reasons,_=check(x)
    if ok or "lease-root-authority-receipt-ref-missing" not in reasons:
        failures.append("prelaunch consequential lease did not require root-authority receipt")

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    ok,reasons,_=check(x)
    if not ok:
        failures.append("complete prelaunch consequential lease failed: "+",".join(reasons))

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    ok,reasons,_=check(x,execution_depth="publish",action_class="publish")
    if ok or "lease-release-receipt-ref-missing" not in reasons:
        failures.append("publish lease did not require release receipt")

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    x["release_receipt_ref"]="fixture:release"
    ok,reasons,_=check(x,execution_depth="publish",action_class="publish")
    if not ok:
        failures.append("complete publish lease failed: "+",".join(reasons))

    x=base_lease()
    x["authority_phase"]="DISTRIBUTED_OPERATION"
    x.pop("root_authority_receipt_ref",None)
    ok,reasons,_=check(x)
    if not ok:
        failures.append("distributed-operation lease incorrectly inherited prelaunch root receipt requirement: "+",".join(reasons))

    # Synthetic scope-only regressions: no host call, signature or DBR acceptance.
    scope_negatives = [
        ("scope-absent", None, "lease-scope-invalid"),
        ("scope-not-object", [], "lease-scope-invalid"),
        ("task-allowlist-absent", {"action_classes":["execute"]}, "lease-task-scope-missing"),
        ("task-allowlist-empty", {"task_ids":[], "action_classes":["execute"]}, "lease-task-scope-invalid"),
        ("action-allowlist-absent", {"task_ids":["CGX-LAUNCH-006"]}, "lease-action-class-scope-missing"),
        ("action-allowlist-empty", {"task_ids":["CGX-LAUNCH-006"], "action_classes":[]}, "lease-action-class-scope-invalid"),
        ("task-not-allowed", {"task_ids":["OTHER"], "action_classes":["execute"]}, "lease-task-out-of-scope:CGX-LAUNCH-006"),
        ("action-not-allowed", {"task_ids":["CGX-LAUNCH-006"], "action_classes":["publish"]}, "lease-action-class-out-of-scope:execute"),
    ]
    for label, scope_value, expected_reason in scope_negatives:
        x=base_lease()
        x["root_authority_receipt_ref"]="fixture:root-approval"
        if scope_value is None:
            x.pop("scope",None)
        else:
            x["scope"]=copy.deepcopy(scope_value)
        ok,reasons,_=check(x)
        if ok or expected_reason not in reasons:
            failures.append(label + ": expected " + expected_reason + "; got " + ",".join(reasons))

    # Invalid envelope/identity types must fail closed, even when other
    # lease fields look valid. These are NOT signature-verification tests.
    for bad_envelope in ([], "lease", 42):
        ok,reasons,_=check(bad_envelope)
        if ok or "execution-lease-invalid" not in reasons:
            failures.append("non-object lease envelope accepted: " + repr(bad_envelope))
    malformed_identity = [
        ("lease_id", None, "lease-lease-id-invalid"),
        ("lease_id", "", "lease-lease-id-invalid"),
        ("lease_id", 17, "lease-lease-id-invalid"),
        ("lease_id", "   ", "lease-lease-id-invalid"),
        ("issued_by", None, "lease-issued-by-invalid"),
        ("issued_by", [], "lease-issued-by-invalid"),
        ("issued_by", "   ", "lease-issued-by-invalid"),
        ("subject_agent", None, "lease-subject-agent-invalid"),
        ("subject_agent", {}, "lease-subject-agent-invalid"),
        ("subject_agent", "   ", "lease-subject-agent-invalid"),
    ]
    for field, bad_value, expected_reason in malformed_identity:
        x=base_lease()
        x["root_authority_receipt_ref"]="fixture:root-approval"
        x[field]=copy.deepcopy(bad_value)
        ok,reasons,_=check(x)
        if ok or expected_reason not in reasons:
            failures.append(field + " invalid identity type not rejected: " + ",".join(reasons))

    # Typed allowlists reject malformed and mixed-type values, even when the
    # requested legitimate entry is also present. Source-only; not issuer proof.
    malformed_allowlists = [
        ("domains", ["romer", 42], "lease-domains-allowlist-invalid"),
        ("domains", "romer", "lease-domains-allowlist-invalid"),
        ("domains", None, "lease-domains-allowlist-invalid"),
        ("execution_depths", ["execute", None], "lease-execution-depths-allowlist-invalid"),
        ("execution_depths", "execute", "lease-execution-depths-allowlist-invalid"),
        ("allowed_floors", ["Neo", {"unexpected": "claim"}], "lease-allowed-floors-allowlist-invalid"),
        ("allowed_floors", ["Neo", " "], "lease-allowed-floors-allowlist-invalid"),
        ("allowed_floors", {"0": "Neo"}, "lease-allowed-floors-allowlist-invalid"),
    ]
    for field, bad_value, expected_reason in malformed_allowlists:
        x=base_lease()
        x["root_authority_receipt_ref"]="fixture:root-approval"
        x[field]=copy.deepcopy(bad_value)
        ok,reasons,_=check(x)
        if ok or expected_reason not in reasons:
            failures.append(field + " malformed typed allowlist was not rejected: " + ",".join(reasons))

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    ok,reasons,_=check(x,project_id="PROJECT-ONE")
    if ok or "lease-project-scope-missing" not in reasons:
        failures.append("requested project without allowlist was not rejected")
    x["scope"]["project_ids"]=["PROJECT-ONE"]
    ok,reasons,_=check(x,project_id="PROJECT-ONE")
    if not ok:
        failures.append("explicitly scoped project fixture failed: " + ",".join(reasons))

    # Request-bound CCC tool/object/configuration scopes. These checks verify
    # typed structural allowlists, NOT signature, revocation, nonce consumption,
    # host permission, tool installation or signed DBR admission.
    for field, argument, value, label in (
        ("object_ids", "object_id", "cgx://review/object-1", "object"),
        ("tool_scopes", "tool_scope", "ccc:review:science.query", "tool"),
        ("configuration_ids", "configuration_id", "review-config-1", "configuration"),
    ):
        x=base_lease()
        x["root_authority_receipt_ref"]="fixture:root-approval"
        ok,reasons,_=check(x, **{argument:value})
        if ok or f"lease-{label}-scope-missing" not in reasons:
            failures.append(f"{label}: requested scope without explicit allowlist accepted: {reasons}")

        x["scope"][field]=[value]
        ok,reasons,_=check(x, **{argument:value})
        if not ok:
            failures.append(f"{label}: explicit requested scope rejected: {reasons}")

        x["scope"][field]=["other"]
        ok,reasons,_=check(x, **{argument:value})
        if ok or f"lease-{label}-out-of-scope:{value}" not in reasons:
            failures.append(f"{label}: out-of-scope request accepted: {reasons}")

        x["scope"][field]=[value, None]
        ok,reasons,_=check(x, **{argument:value})
        if ok or f"lease-{label}-scope-invalid" not in reasons:
            failures.append(f"{label}: mixed-type allowlist accepted: {reasons}")

        x["scope"][field]=[value]
        ok,reasons,_=check(x)
        if ok or f"lease-scope-requires-{label}" not in reasons:
            failures.append(f"{label}: declared scope without request target accepted: {reasons}")

    print({"status":"PASS" if not failures else "FAIL","failures":failures})
    return 1 if failures else 0

if __name__=="__main__":
    raise SystemExit(main())
