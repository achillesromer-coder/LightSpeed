#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DT=ROOT/"cgx"/"domain_templates"
sys.path.insert(0,str(ROOT/"scripts"))
from cgx_assurance_route import route,STATE_RANK

def load(name):
    return json.loads((DT/name).read_text(encoding="utf-8"))

def main():
    failures=[]; warnings=[]
    try:
        registry=load("assurance_method_registry.json")
        schema=load("unified_assurance_object_schema.json")
        matrix=load("assurance_selection_matrix.json")
        crosswalk=load("assurance_reference_crosswalk.json")
        fixtures=load("assurance_fixture_scenarios.json")
    except Exception as e:
        print(json.dumps({"status":"FAIL","failures":[str(e)]})); return 1
    methods=[m.get("id") for m in registry.get("methods",[])]
    if len(methods)!=len(set(methods)): failures.append("duplicate assurance method ids")
    if registry.get("location")!="Cognigrex.cgx:/assurance": failures.append("assurance parent path mismatch")
    if "composite_score" not in schema.get("scalar_rules",{}): failures.append("anti-composite-score rule missing")
    if "RPN" in methods: warnings.append("RPN incorrectly modeled as method rather than FMEA field")
    if crosswalk.get("status")!="applicability map / not certification": failures.append("crosswalk certification boundary missing")
    if crosswalk.get("verified_at")!="2026-09-30": warnings.append("assurance crosswalk verification date changed")
    for f in fixtures.get("scenarios",[]):
        got=route(f["domain"],f["execution_depth"],f.get("cascade_class","C0"),f.get("tags",[]))
        missing=sorted(set(f.get("must_include",[]))-set(got["required_methods"]))
        if missing: failures.append(f'{f["id"]}: missing methods {missing}')
        if STATE_RANK[got["minimum_assurance_state"]]<STATE_RANK[f["minimum_state"]]:
            failures.append(f'{f["id"]}: state {got["minimum_assurance_state"]} < {f["minimum_state"]}')
    print(json.dumps({
      "status":"PASS" if not failures else "FAIL",
      "failures":failures,"warnings":warnings,
      "methods":len(methods),"fixtures":len(fixtures.get("scenarios",[])),
      "parent":"Cognigrex.cgx:/assurance"
    },sort_keys=True))
    return 1 if failures else 0
if __name__=="__main__":
    raise SystemExit(main())
