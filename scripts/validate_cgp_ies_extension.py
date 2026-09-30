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
        terminology=load("cgp_ies_terminology_map.json")
        adapters=load("cgp_ies_domain_adapter_registry.json")
        receipt_schema=load("cgp_ies_decision_receipt_schema.json")
        authority_ref=load("cgp_ies_authority_phase_ref.json")
        visibility=load("cgp_ies_release_visibility_policy.json")
        owner_values=load("cgp_ies_owner_confirmation_values.json")
    except Exception as e:
        print(json.dumps({"status":"FAIL","failures":[str(e)]})); return 1
    if reg.get("schema")!="CGX-EXTENSION-REGISTRY/0.1": failures.append("extension registry schema")
    if policy.get("schema")!="CGX-CGP-IES-POLICY/0.1": failures.append("policy schema")
    if terminology.get("schema")!="CGX-CGP-IES-TERMINOLOGY/0.1": failures.append("terminology schema")
    if adapters.get("schema")!="CGX-CGP-IES-DOMAIN-ADAPTERS/0.1": failures.append("domain adapter schema")
    if receipt_schema.get("schema")!="CGX-CGP-IES-DECISION-RECEIPT/0.1": failures.append("decision receipt schema")
    if authority_ref.get("schema")!="CGX-CGP-IES-AUTHORITY-PHASE-REF/0.1": failures.append("authority phase ref schema")
    if visibility.get("schema")!="CGX-CGP-IES-RELEASE-VISIBILITY/0.1": failures.append("release visibility schema")
    if authority_ref.get("detailed_contract_class")!="Restricted": failures.append("authority details must remain Restricted")
    if "detailed root-authority topology" not in visibility.get("public_projection_deny",[]): failures.append("authority topology missing from public deny list")
    if "ACCEPTED_BASELINES" not in owner_values.get("status",""): failures.append("owner baselines not accepted")
    ext=[x for x in reg.get("extensions",[]) if x.get("id")=="cgp-ies"]
    if len(ext)!=1: failures.append("cgp-ies extension missing or duplicated")
    else:
        ext=ext[0]
        if ext.get("binding_mode")!="REFERENCE": failures.append("cgp-ies must bind by REFERENCE")
        if ext.get("source_path")!="Cognigrex.cgx:/extensions/cgp-ies": failures.append("cgp-ies parent source path")
        if "ENFORCE_SAFETY" not in ext.get("toggle_modes",[]): failures.append("safety mode missing")
        components=ext.get("components",{})
        for key in ("policy","terminology","domain_adapters","decision_receipt","fixtures","authority_phase","release_visibility"):
            if not components.get(key): failures.append("extension component missing:"+key)
    if policy.get("collective_good_rule","").lower().find("sovereign score")<0:
        warnings.append("collective-good anti-scalar wording changed")
    terms={x.get("preferred") for x in terminology.get("rules",[])}
    for required_term in ("intelligent_collective","operational_intelligence","moral_patient_uncertainty","protective_perpetuity","option_space","inter_special"):
        if required_term not in terms: failures.append("terminology missing:"+required_term)
    if set(adapters.get("domains",{})) != {"romer","eco","emassc","lightspeed"}:
        failures.append("domain adapter coverage")
    if receipt_schema.get("sentience_uncertainty_default")!="STRUCTURED_EVIDENCE_NO_SCALAR":
        failures.append("sentience uncertainty scalarisation")
    if "sovereign moral total" not in receipt_schema.get("option_object",{}).get("comparison_rule","").lower():
        warnings.append("receipt anti-scalar wording changed")
    scenarios=fixtures.get("scenarios",[])
    if len(scenarios)<22: failures.append("fixture coverage below 22 scenarios")
    required_ids={f"F{i}" for i in range(1,23)}
    if not required_ids.issubset({f.get("id") for f in scenarios}): failures.append("fixture ids incomplete")
    for f in scenarios:
        got=resolve(f["domain"],f["execution_depth"],f.get("reasoning_depth","standard"),f.get("cascade_class","C0"),f.get("tags",[]))
        if RANK[got["mode"]]<RANK[f["expected_minimum"]]:
            failures.append(f'{f["id"]}: {got["mode"]} < {f["expected_minimum"]}')
        if got.get("hard_predicates") != policy.get("admissibility_hard_predicates"):
            failures.append(f'{f["id"]}: resolver hard predicates drift from policy')
        if got.get("domain_adapter",{}).get("source_ref")!="cgp_ies_domain_adapter_registry.json":
            failures.append(f'{f["id"]}: domain adapter source ref missing')
    print(json.dumps({"status":"PASS" if not failures else "FAIL","failures":failures,"warnings":warnings,"fixtures":len(fixtures.get("scenarios",[])),"source_driven":True},sort_keys=True))
    return 1 if failures else 0
if __name__=="__main__": raise SystemExit(main())
