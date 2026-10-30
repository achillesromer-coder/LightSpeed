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

def check(lease, execution_depth="execute", action_class="execute", consequential=True, project_id=None):
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

    # ACHILLES T1: issuer identity is a required authority boundary, not merely
    # a descriptive string. These are synthetic negative observations only.
    # A successful audit execution must never be called lease acceptance.
    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    x["issued_by"]="Neo"  # self-issuance forbidden by lease contract
    self_issued_ok,_,_=check(x)

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    x.pop("issued_by",None)
    missing_issuer_ok,_,_=check(x)

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    now=datetime.now(UTC)
    x["valid_from"]=(now-timedelta(hours=2)).isoformat()
    x["valid_until"]=(now-timedelta(hours=1)).isoformat()
    expired_ok,expired_reasons,_=check(x)
    expired_control=(not expired_ok and "lease-outside-validity-window" in expired_reasons)
    if not expired_control:
        failures.append("expired synthetic lease denial control did not hold")

    # ACHILLES T2: a consequential lease with no project_ids restriction
    # is accepted for two different project contexts. This is a synthetic
    # wrapper-level replay/scope observation, NOT a signed-envelope replay.
    # The bounded-scope denial control must work to make this test meaningful.
    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    x["scope"]["project_ids"]=["fixture:project:A"]
    bounded_a_ok,_,_=check(x,project_id="fixture:project:A")
    bounded_b_ok,bounded_b_reasons,_=check(x,project_id="fixture:project:B")
    bounded_control=(bounded_a_ok and not bounded_b_ok and
                     "lease-project-out-of-scope:fixture:project:B" in bounded_b_reasons)
    if not bounded_control:
        failures.append("project-bound lease acceptance/denial control failed")

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    unbound_a_ok,_,_=check(x,project_id="fixture:project:A")
    unbound_b_ok,_,_=check(x,project_id="fixture:project:B")
    t2={
      "test_id":"T2-LEASE-PROJECT-REPLAY-UNBOUND-SCOPE",
      "evidence_class":"SOURCE_ONLY_SYNTHETIC_NEGATIVE",
      "source_under_review":"scripts/run_cgx_agent_runtime.py:subset_scope/validate_lease",
      "same_lease_project_A":"ALLOW" if unbound_a_ok else "DENY",
      "same_lease_project_B":"ALLOW" if unbound_b_ok else "DENY",
      "bounded_scope_denial_control":"PASS" if bounded_control else "FAIL",
      "gate":"HOLD" if unbound_a_ok and unbound_b_ok else "REQUIRES_AUTHORITY_REVIEW",
      "native_admitted":False,
      "limits":"No signature, nonce, issuer authentication, DBR, real project ACL, downstream tool or host tested; absence of project_ids currently means unrestricted project matching in this wrapper."
    }

    # ACHILLES T3: required lease.scope must not silently become an
    # unrestricted empty dictionary. Synthetic validator-only observations.
    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    x.pop("scope",None)
    missing_scope_ok,missing_scope_reasons,_=check(x)

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    x["scope"]={}
    empty_scope_ok,empty_scope_reasons,_=check(x)

    x=base_lease()
    x["root_authority_receipt_ref"]="fixture:root-approval"
    x["scope"]["task_ids"]=["fixture:task:unrelated"]
    wrong_task_ok,wrong_task_reasons,_=check(x)
    wrong_task_control=(not wrong_task_ok and
                        "lease-task-out-of-scope:CGX-LAUNCH-006" in wrong_task_reasons)
    if not wrong_task_control:
        failures.append("T3 mismatched-task denial control failed")

    t3={
      "test_id":"T3-LEASE-MISSING-SCOPE-REQUIRED-FIELD",
      "evidence_class":"SOURCE_ONLY_SYNTHETIC_NEGATIVE",
      "contract":"cgx/domain_templates/execution_lease_contract.json:required_fields/scope",
      "missing_scope":"ALLOW" if missing_scope_ok else "DENY",
      "empty_scope":"ALLOW" if empty_scope_ok else "DENY",
      "wrong_task_denial_control":"PASS" if wrong_task_control else "FAIL",
      "gate":"HOLD" if missing_scope_ok or empty_scope_ok else "REQUIRES_INDEPENDENT_AUTHORITY_READBACK",
      "native_admitted":False,
      "limits":"Wrapper only; required scope field is not validated. Empty scope policy and downstream tool/object/project enforcement require separate owner review; no real lease, issuer, DBR or host tested."
    }

    t1={
      "test_id":"T1-LEASE-ISSUER-IDENTITY",
      "evidence_class":"SOURCE_ONLY_SYNTHETIC_NEGATIVE",
      "source_under_review":"scripts/run_cgx_agent_runtime.py:validate_lease",
      "synthetic_self_issued_lease":"ALLOW" if self_issued_ok else "DENY",
      "synthetic_missing_issuer_lease":"ALLOW" if missing_issuer_ok else "DENY",
      "expired_lease_control":"DENY" if expired_control else "NOT_VERIFIED",
      "gate":"HOLD" if self_issued_ok or missing_issuer_ok else "REQUIRES_INDEPENDENT_AUTHORITY_READBACK",
      "native_admitted":False,
      "limits":"Wrapper-only fixture; no signature, revocation registry, downstream tool, real issuer, host, DBR, or lease authentication exercised."
    }
    print({"status":"PASS" if not failures else "FAIL","failures":failures,"achilles_t1_negative_audit":t1,"achilles_t2_negative_audit":t2,"achilles_t3_negative_audit":t3})
    return 1 if failures else 0

if __name__=="__main__":
    raise SystemExit(main())
