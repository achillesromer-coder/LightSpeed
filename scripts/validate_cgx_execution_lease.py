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

def check(lease, execution_depth="execute", action_class="execute", consequential=True):
    return validate_lease(
      lease,
      agent_id="Neo",
      domain="romer",
      execution_depth=execution_depth,
      cascade_class="C2",
      task_id="CGX-LAUNCH-006",
      project_id=None,
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

    print({"status":"PASS" if not failures else "FAIL","failures":failures})
    return 1 if failures else 0

if __name__=="__main__":
    raise SystemExit(main())
