#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DT=ROOT/"cgx"/"domain_templates"
sys.path.insert(0,str(ROOT/"scripts"))
from resolve_cgx_extensions import resolve, RANK

def load(name):
    return json.loads((DT/name).read_text(encoding="utf-8"))

def main():
    failures=[]; warnings=[]
    try:
        reg=load("custodial_extension_registry.json")
        policy=load("cgp_ies_policy_pack.json")
        fixtures=load("cgp_ies_fixture_scenarios.json")
    except Exception as e:
        print(json.dumps({"status":"FAIL","failures":[str(e)]})); return 1
    if reg.get("schema")!="CGX-EXTENSION-REGISTRY/0.1": failures.append("extension registry schema")
    if policy.get("schema")!="CGX-CGP-IES-POLICY/0.1": failures.append("policy schema")
    ext=[x for x in reg.get("extensions",[]) if x.get("id")=="cgp-ies"]
    if len(ext)!=1: failures.append("cgp-ies extension missing or duplicated")
    else:
        ext=ext[0]
        if ext.get("binding_mode")!="REFERENCE": failures.append("cgp-ies must bind by REFERENCE")
        if ext.get("source_path")!="Cognigrex.cgx:/extensions/cgp-ies": failures.append("cgp-ies parent source path")
        if "ENFORCE_SAFETY" not in ext.get("toggle_modes",[]): failures.append("safety mode missing")
    if policy.get("collective_good_rule","").lower().find("sovereign score")<0:
        warnings.append("collective-good anti-scalar wording changed")
    for f in fixtures.get("scenarios",[]):
        got=resolve(f["domain"],f["execution_depth"],f.get("reasoning_depth","standard"),f.get("cascade_class","C0"),f.get("tags",[]))
        if RANK[got["mode"]]<RANK[f["expected_minimum"]]:
            failures.append(f'{f["id"]}: {got["mode"]} < {f["expected_minimum"]}')
    print(json.dumps({"status":"PASS" if not failures else "FAIL","failures":failures,"warnings":warnings,"fixtures":len(fixtures.get("scenarios",[]))},sort_keys=True))
    return 1 if failures else 0
if __name__=="__main__": raise SystemExit(main())
