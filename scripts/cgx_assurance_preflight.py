#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from cgx_assurance_route import route,STATE_RANK

ACCEPTED_METHOD_STATES={"COMPLETE","BOUNDED","NOT_APPLICABLE"}
SAFETY_TAGS={"replication-control","hard-stop","containment","life-support","hazard-control","planetary-protection","unknown-life","nuclear","radioactive"}

def read_json(path):
    if not path: return None
    return json.loads(Path(path).read_text(encoding="utf-8"))

def assess(resolution,assessment):
    required=resolution["required_methods"]
    state=resolution["minimum_assurance_state"]
    if state=="HOLD":
        return "HOLD",["router-hold:no-sufficient-method-route-for-high-consequence-action"]
    if STATE_RANK[state]<STATE_RANK["VERIFY"]:
        return "ALLOW_WITH_ASSURANCE_RECEIPT",[]
    if assessment is None:
        return "HOLD",["assurance-assessment-missing"]
    reasons=[]
    if not assessment.get("source_verified",False):
        reasons.append("assurance-source-not-verified")
    receipts=assessment.get("method_receipts",{})
    for method in required:
        rec=receipts.get(method)
        if not isinstance(rec,dict):
            reasons.append(f"method-receipt-missing:{method}"); continue
        if rec.get("state") not in ACCEPTED_METHOD_STATES:
            reasons.append(f"method-open:{method}:{rec.get('state','UNKNOWN')}")
        if rec.get("state")=="NOT_APPLICABLE" and not rec.get("rationale"):
            reasons.append(f"not-applicable-without-rationale:{method}")
        if not rec.get("evidence_ids") and rec.get("state")!="NOT_APPLICABLE":
            reasons.append(f"method-evidence-missing:{method}")
    if assessment.get("blocking_findings"):
        reasons.append("blocking-assurance-findings-open")
    if state=="SAFETY_CASE":
        if not assessment.get("control_verification_complete",False):
            reasons.append("control-verification-incomplete")
        tags=set(resolution["context"]["tags"])
        if tags & SAFETY_TAGS and not assessment.get("independent_stop_or_containment_verified",False):
            reasons.append("independent-stop-or-containment-unverified")
    return ("HOLD",reasons) if reasons else ("ALLOW",[])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--domain",required=True,choices=["romer","eco","emassc","lightspeed"])
    ap.add_argument("--execution-depth",required=True,choices=["inspect","propose","simulate","execute","build","publish"])
    ap.add_argument("--cascade-class",default="C0",choices=["C0","C1","C2","C3","C4"])
    ap.add_argument("--tags",default="")
    ap.add_argument("--assessment-json")
    args=ap.parse_args()
    resolution=route(args.domain,args.execution_depth,args.cascade_class,args.tags.split(","))
    assessment=read_json(args.assessment_json)
    decision,reasons=assess(resolution,assessment)
    out={
      "schema":"CGX-ASSURANCE-PREFLIGHT/0.1",
      "decision":decision,
      "hold_reasons":reasons,
      "resolution":resolution,
      "assessment_supplied":assessment is not None,
      "authority_limit":"A clear assurance preflight means required method evidence is bounded for this request. It is not risk acceptance, legal approval, certification, custodial approval or execution authority."
    }
    print(json.dumps(out,indent=2,sort_keys=True))
    return 3 if decision=="HOLD" else 0
if __name__=="__main__":
    raise SystemExit(main())
