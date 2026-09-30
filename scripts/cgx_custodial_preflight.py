#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from resolve_cgx_extensions import resolve, RANK

def load_assessment(path):
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))

def assess_custodial(resolution, assessment):
    decision="ALLOW"
    reasons=[]
    if RANK[resolution["mode"]]>=RANK["GATE"]:
        if assessment is None:
            decision="HOLD"
            reasons.append("gate-assessment-missing")
        else:
            if not assessment.get("source_verified",False):
                decision="HOLD"
                reasons.append("extension-source-not-verified")
            if not assessment.get("authority_confirmed",False):
                decision="HOLD"
                reasons.append("authority-not-confirmed")
            hp=assessment.get("hard_predicates",{})
            required=list(resolution.get("hard_predicates") or [])
            if not required:
                decision="HOLD"
                reasons.append("source-hard-predicate-contract-missing")
            missing=[x for x in required if hp.get(x) is not True]
            if missing:
                decision="HOLD"
                reasons.append("hard-predicates-open:"+",".join(missing))
    elif resolution["mode"] in ("OBSERVE","ADVISE"):
        decision="ALLOW_WITH_RECEIPT"
    return decision,reasons

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--domain",required=True,choices=["romer","eco","emassc","lightspeed"])
    ap.add_argument("--execution-depth",required=True,choices=["inspect","propose","simulate","execute","build","publish"])
    ap.add_argument("--reasoning-depth",default="standard")
    ap.add_argument("--cascade-class",default="C0",choices=["C0","C1","C2","C3","C4"])
    ap.add_argument("--tags",default="")
    ap.add_argument("--mode",choices=["OFF","OBSERVE","ADVISE","GATE","ENFORCE_SAFETY"])
    ap.add_argument("--assessment-json")
    args=ap.parse_args()

    resolution=resolve(
        args.domain,args.execution_depth,args.reasoning_depth,args.cascade_class,
        [x for x in args.tags.split(",") if x],args.mode
    )
    assessment=load_assessment(args.assessment_json)
    decision,reasons=assess_custodial(resolution,assessment)
    receipt={
      "schema":"CGX-CUSTODIAL-PREFLIGHT/0.1",
      "decision":decision,
      "hold_reasons":reasons,
      "resolution":resolution,
      "assessment_supplied":assessment is not None,
      "source_driven_hard_predicates":resolution.get("hard_predicates",[]),
      "decision_receipt_schema":resolution.get("shared_components",{}).get("decision_receipt"),
      "authority_limit":"Custodial preflight applies parent-owned source policy and may HOLD only under declared gate/safety conditions. It does not create moral, semantic, ownership, representation or execution authority."
    }
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 3 if decision=="HOLD" else 0

if __name__=="__main__":
    raise SystemExit(main())
