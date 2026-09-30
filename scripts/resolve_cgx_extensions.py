#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DT=ROOT/"cgx"/"domain_templates"
RANK={"OFF":0,"OBSERVE":1,"ADVISE":2,"GATE":3,"ENFORCE_SAFETY":4}
CASCADE={"C0":0,"C1":1,"C2":2,"C3":3,"C4":4}

def load(name):
    return json.loads((DT/name).read_text(encoding="utf-8"))

def clamp_mode(mode, minimum=None, maximum=None):
    r=RANK[mode]
    if minimum is not None: r=max(r,RANK[minimum])
    if maximum is not None: r=min(r,RANK[maximum])
    return next(k for k,v in RANK.items() if v==r)

def _match(rule, ctx):
    w=rule.get("when",{})
    if "execution_depth" in w and ctx["execution_depth"] not in w["execution_depth"]: return False
    if "tags_any" in w and not (set(ctx["tags"]) & set(w["tags_any"])): return False
    c=CASCADE[ctx["cascade_class"]]
    if "cascade_min" in w and c<CASCADE[w["cascade_min"]]: return False
    if "cascade_max" in w and c>CASCADE[w["cascade_max"]]: return False
    return True

def resolve(domain, execution_depth, reasoning_depth="standard", cascade_class="C0", tags=None, requested_mode=None):
    tags=sorted(set(tags or []))
    reg=load("custodial_extension_registry.json")
    ext=next(x for x in reg["extensions"] if x["id"]=="cgp-ies")
    if domain not in ext["defaults"]: raise ValueError(f"unknown-domain:{domain}")
    if cascade_class not in CASCADE: raise ValueError(f"unknown-cascade:{cascade_class}")
    mode=requested_mode or ext["defaults"][domain]
    if mode not in RANK: raise ValueError(f"unknown-mode:{mode}")
    reasons=[f"default:{domain}={mode}" if requested_mode is None else f"requested:{mode}"]
    ctx={"domain":domain,"execution_depth":execution_depth,"reasoning_depth":reasoning_depth,"cascade_class":cascade_class,"tags":tags}
    for rule in ext.get("automatic_escalation",[]):
        if not _match(rule,ctx): continue
        before=mode
        mode=clamp_mode(mode,rule.get("minimum_mode"),rule.get("maximum_mode"))
        if mode!=before or rule.get("minimum_mode") or rule.get("maximum_mode"):
            reasons.append(rule.get("reason","rule"))
    policy=load(ext["source_template"])
    checks=[]
    if RANK[mode]>=RANK["OBSERVE"]:
        checks+=["evidence_and_domain_boundary","affected_party_enumeration"]
    if RANK[mode]>=RANK["ADVISE"]:
        checks+=["necessity_and_alternatives","reversibility_and_option_space","preserve_dissent"]
    if RANK[mode]>=RANK["GATE"]:
        checks+=["admissibility_hard_predicates","effective_ceiling","authority_and_representation","inheritance_and_safe_state"]
    if mode=="ENFORCE_SAFETY":
        checks+=["independent_safety_plane","replication_stop_containment_controls"]
    return {
      "schema":"CGX-CGP-IES-RESOLUTION/0.1",
      "extension_id":"cgp-ies","source_path":ext["source_path"],
      "source_status":reg["status"],"domain":domain,"mode":mode,"activation_reasons":reasons,
      "context":ctx,"checks":list(dict.fromkeys(checks)),
      "fail_behaviour":ext["fail_behaviour"],
      "authority_limit":"Extension may block/hold only under declared GATE or ENFORCE_SAFETY conditions; it cannot create new semantic, moral, ownership or execution authority.",
      "policy_receipt_fields":policy["required_receipt_fields"]
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--domain",required=True,choices=["romer","eco","emassc","lightspeed"])
    ap.add_argument("--execution-depth",required=True,choices=["inspect","propose","simulate","execute","build","publish"])
    ap.add_argument("--reasoning-depth",default="standard")
    ap.add_argument("--cascade-class",default="C0",choices=["C0","C1","C2","C3","C4"])
    ap.add_argument("--tags",default="")
    ap.add_argument("--mode",choices=list(RANK))
    args=ap.parse_args()
    out=resolve(args.domain,args.execution_depth,args.reasoning_depth,args.cascade_class,[x for x in args.tags.split(",") if x],args.mode)
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__": main()
