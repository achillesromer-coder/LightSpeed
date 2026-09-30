#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DT=ROOT/"cgx"/"domain_templates"
STATE_RANK={"LOG":0,"ANALYSE":1,"VERIFY":2,"SAFETY_CASE":3,"HOLD":4}
CASCADE={"C0":0,"C1":1,"C2":2,"C3":3,"C4":4}

def load(name):
    return json.loads((DT/name).read_text(encoding="utf-8"))

def max_state(a,b):
    return a if STATE_RANK[a]>=STATE_RANK[b] else b

def matches(match,ctx):
    if "domain" in match and ctx["domain"] not in [x.lower() for x in match["domain"]]:
        return False
    if "execution_depth" in match and ctx["execution_depth"] not in match["execution_depth"]:
        return False
    if "tags_any" in match:
        wanted={x.lower() for x in match["tags_any"]}
        if not (set(ctx["tags"]) & wanted):
            return False
    if "cascade_min" in match and CASCADE[ctx["cascade_class"]]<CASCADE[match["cascade_min"]]:
        return False
    if "cascade_max" in match and CASCADE[ctx["cascade_class"]]>CASCADE[match["cascade_max"]]:
        return False
    return True

def route(domain,execution_depth,cascade_class="C0",tags=None):
    matrix=load("assurance_selection_matrix.json")
    registry=load("assurance_method_registry.json")
    known={m["id"]:m for m in registry["methods"]}
    ctx={
      "domain":domain.lower(),
      "execution_depth":execution_depth,
      "cascade_class":cascade_class,
      "tags":sorted({x.strip().lower() for x in (tags or []) if x.strip()})
    }
    methods=[]; route_ids=[]; state="LOG"
    for r in matrix.get("routes",[]):
        if matches(r.get("match",{}),ctx):
            route_ids.append(r["id"])
            state=max_state(state,r.get("minimum_state","ANALYSE"))
            for m in r.get("methods",[]):
                if m not in known:
                    raise ValueError(f"unknown-assurance-method:{m}")
                if m not in methods:
                    methods.append(m)
    for rule in matrix.get("escalation",[]):
        if matches(rule.get("when",{}),ctx):
            state=max_state(state,rule.get("minimum_state","LOG"))
    # High-consequence work with no matched specialist method is not silently clear.
    if CASCADE[cascade_class]>=CASCADE["C3"] and execution_depth in ("execute","build") and not methods:
        state="HOLD"
    required_evidence=[]
    for m in methods:
        entry=known[m]
        required_evidence.extend(entry.get("outputs",[]))
    return {
      "schema":"CGX-ASSURANCE-ROUTE/0.1",
      "source_path":"Cognigrex.cgx:/assurance",
      "context":ctx,
      "matched_routes":route_ids,
      "required_methods":methods,
      "minimum_assurance_state":state,
      "required_evidence_classes":list(dict.fromkeys(required_evidence)),
      "authority_limit":"Assurance routing selects analyses and evidence requirements; it does not itself authorise execution, certify compliance, accept residual risk or determine collective good.",
      "next_planes":["evidence-qualification","cgp-ies-custodial-assessment","authority-and-execution-gate"]
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--domain",required=True,choices=["romer","eco","emassc","lightspeed"])
    ap.add_argument("--execution-depth",required=True,choices=["inspect","propose","simulate","execute","build","publish"])
    ap.add_argument("--cascade-class",default="C0",choices=["C0","C1","C2","C3","C4"])
    ap.add_argument("--tags",default="")
    args=ap.parse_args()
    print(json.dumps(route(args.domain,args.execution_depth,args.cascade_class,args.tags.split(",")),indent=2,sort_keys=True))
if __name__=="__main__":
    raise SystemExit(main())
