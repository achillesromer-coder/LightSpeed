#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from cgx_assurance_route import route as assurance_route
from cgx_assurance_preflight import assess as assurance_assess, read_json
from resolve_cgx_extensions import resolve as custodial_resolve
from cgx_custodial_preflight import assess_custodial

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--domain",required=True,choices=["romer","eco","emassc","lightspeed"])
    ap.add_argument("--execution-depth",required=True,choices=["inspect","propose","simulate","execute","build","publish"])
    ap.add_argument("--reasoning-depth",default="standard")
    ap.add_argument("--cascade-class",default="C0",choices=["C0","C1","C2","C3","C4"])
    ap.add_argument("--tags",default="")
    ap.add_argument("--assurance-assessment-json")
    ap.add_argument("--custodial-assessment-json")
    args=ap.parse_args()
    tags=[x for x in args.tags.split(",") if x]

    ar=assurance_route(args.domain,args.execution_depth,args.cascade_class,tags)
    aa=read_json(args.assurance_assessment_json)
    assurance_decision,assurance_reasons=assurance_assess(ar,aa)

    cr=custodial_resolve(args.domain,args.execution_depth,args.reasoning_depth,args.cascade_class,tags)
    ca=read_json(args.custodial_assessment_json)
    custodial_decision,custodial_reasons=assess_custodial(cr,ca)

    holds=[]
    if assurance_decision=="HOLD": holds.extend(["assurance:"+x for x in assurance_reasons])
    if custodial_decision=="HOLD": holds.extend(["custodial:"+x for x in custodial_reasons])
    consequential=args.execution_depth in ("execute","build","publish") or args.cascade_class in ("C2","C3","C4")
    overall="HOLD" if holds else ("CLEARED_FOR_AUTHORITY_GATE" if consequential else "ALLOW_WITH_RECEIPTS")

    receipt={
      "schema":"CGX-CONSEQUENCE-PREFLIGHT/0.1",
      "decision":overall,
      "hold_reasons":holds,
      "context":{
        "domain":args.domain,"execution_depth":args.execution_depth,
        "reasoning_depth":args.reasoning_depth,"cascade_class":args.cascade_class,
        "tags":sorted(set(x.lower() for x in tags))
      },
      "assurance":{
        "decision":assurance_decision,"hold_reasons":assurance_reasons,"resolution":ar
      },
      "custodial":{
        "decision":custodial_decision,"hold_reasons":custodial_reasons,"resolution":cr
      },
      "next_gate":"scoped authority / risk acceptance / execution lease" if overall!="HOLD" else "resolve blocking evidence or predicates",
      "authority_limit":"CLEARED_FOR_AUTHORITY_GATE is not execution permission. It only means the assurance and custodial preflights did not find an unresolved blocker for the declared scope."
    }
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 3 if overall=="HOLD" else 0

if __name__=="__main__":
    raise SystemExit(main())
