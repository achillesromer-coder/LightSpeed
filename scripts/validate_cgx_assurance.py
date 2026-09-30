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
        relations=load("assurance_relation_registry.json")
        mpl=load("mpl_assurance_adapter.json")
        threats=load("agentic_security_threat_registry.json")
        case=load("assurance_case_contract.json")
        roles=load("agent_assurance_role_matrix.json")
        lease=load("execution_lease_contract.json")
        domains=load("domains.json")
    except Exception as e:
        print(json.dumps({"status":"FAIL","failures":[str(e)]}))
        return 1

    methods=[m.get("id") for m in registry.get("methods",[])]
    required_methods={
        "FMEA","FMECA","HAZARD_ANALYSIS","HAZOP","FTA","ETA","BOW_TIE","STPA",
        "MPL","QRA_PRA","FUNCTIONAL_SAFETY","CYBER_THREAT","AI_IMPACT",
        "ECO_BIOSECURITY","SPACE_DEBRIS","PLANETARY_PROTECTION",
        "CONTINUITY_RECOVERY","LIFECYCLE_INHERITANCE","V_AND_V",
        "ASSURANCE_CASE","AGENTIC_SECURITY","SOFTWARE_SAFETY","HUMAN_FACTORS","LOPA"
    }
    missing_methods=sorted(required_methods-set(methods))
    if missing_methods: failures.append("missing assurance methods:"+",".join(missing_methods))
    if len(methods)!=len(set(methods)): failures.append("duplicate assurance method ids")
    if registry.get("location")!="Cognigrex.cgx:/assurance": failures.append("assurance parent path mismatch")
    if "composite_score" not in schema.get("scalar_rules",{}): failures.append("anti-composite-score rule missing")
    if "RPN" in methods: warnings.append("RPN incorrectly modeled as method rather than FMEA field")
    if crosswalk.get("status")!="applicability map / not certification": failures.append("crosswalk certification boundary missing")
    if crosswalk.get("verified_at")!="2026-09-30": warnings.append("assurance crosswalk verification date changed")

    required_refs={
        "IEC-60812-2018","ISO-IEC-IEEE-15026-2-2022","OWASP-AGENTIC-2026",
        "MITRE-ATLAS","NASA-STD-8739.8B","IEC-61025-2006","IEC-31010-2019","IEC-61511-SER-2026"
    }
    ref_ids={x.get("id") for x in crosswalk.get("references",[])}
    missing_refs=sorted(required_refs-ref_ids)
    if missing_refs: failures.append("missing assurance references:"+",".join(missing_refs))

    relation_ids={x.get("id") for x in relations.get("relations",[])}
    required_relations={
        "HAS_FAILURE_MODE","CAUSED_BY","CREATES_HAZARD","VERIFIED_BY",
        "HAS_RESIDUAL_RISK","ESTIMATES_CONSEQUENCE_OF","SUPPORTS_CLAIM",
        "CHALLENGES_CLAIM","BOUNDS_OPERATION_OF"
    }
    missing_rel=sorted(required_relations-relation_ids)
    if missing_rel: failures.append("missing assurance relations:"+",".join(missing_rel))

    does_not=set(mpl.get("does_not_satisfy",[]))
    for item in ("FMEA","FMECA","HAZARD_ANALYSIS","ASSURANCE_CASE","regulatory-approval"):
        if item not in does_not: failures.append("MPL boundary missing:"+item)
    aliases=mpl.get("prohibited_aliases",[])
    if not any(x.get("from")=="MPL.Failure_Modes" and x.get("to")=="engineering-FMEA-row" for x in aliases):
        failures.append("MPL Failure_Modes semantic boundary missing")

    threat_ids={x.get("id") for x in threats.get("threats",[])}
    expected_threats={f"ASI{i:02d}" for i in range(1,11)}
    if threat_ids!=expected_threats:
        failures.append("agentic threat set mismatch:"+",".join(sorted(threat_ids)))
    if threats.get("verified_at")!="2026-09-30":
        warnings.append("agentic threat registry verification date changed")

    if case.get("schema")!="CGX-ASSURANCE-CASE-CONTRACT/0.1":
        failures.append("assurance case schema mismatch")
    if "certification" not in case.get("output_rule","").lower():
        failures.append("assurance case authority boundary missing")
    if "defeaters" not in case.get("required",[]):
        failures.append("assurance case lacks defeaters")

    expected_agents={"Neo","Oracle","Morpheus","Smith","Architect","TheConstruct","Trinity","Merovingian","Achilles","Athene"}
    role_agents={x.get("agent") for x in roles.get("roles",[])}
    if not expected_agents.issubset(role_agents):
        failures.append("agent assurance role coverage incomplete")

    if lease.get("location")!="Cognigrex.cgx:/agents/leases":
        failures.append("execution lease parent path mismatch")
    lease_invariants=set(lease.get("invariants",[]))
    for inv in ("agent-cannot-issue-extend-or-revive-its-own-lease","missing-or-stale-lease-means-no-consequential-execution","historical-global-approval-manifest-is-not-an-active-execution-lease"):
        if inv not in lease_invariants: failures.append("execution lease invariant missing:"+inv)

    shared=domains.get("shared_contracts",{})
    for key,name in {
        "assurance_relations":"assurance_relation_registry.json",
        "mpl_assurance_adapter":"mpl_assurance_adapter.json",
        "execution_lease":"execution_lease_contract.json",
        "assurance_case":"assurance_case_contract.json",
        "agentic_security_threats":"agentic_security_threat_registry.json",
        "agent_assurance_roles":"agent_assurance_role_matrix.json",
    }.items():
        if shared.get(key)!=name: failures.append(f"domains shared contract mismatch:{key}")

    for f in fixtures.get("scenarios",[]):
        got=route(f["domain"],f["execution_depth"],f.get("cascade_class","C0"),f.get("tags",[]))
        missing=sorted(set(f.get("must_include",[]))-set(got["required_methods"]))
        if missing: failures.append(f'{f["id"]}: missing methods {missing}')
        if STATE_RANK[got["minimum_assurance_state"]]<STATE_RANK[f["minimum_state"]]:
            failures.append(f'{f["id"]}: state {got["minimum_assurance_state"]} < {f["minimum_state"]}')
        if got["minimum_assurance_state"]=="SAFETY_CASE" and "ASSURANCE_CASE" not in got["required_methods"]:
            failures.append(f'{f["id"]}: SAFETY_CASE missing ASSURANCE_CASE')

    # Unknown C2 consequential work is not silently routable.
    unknown=route("romer","execute","C2",[])
    if unknown.get("minimum_assurance_state")!="HOLD":
        failures.append("unclassified C2 execute does not fail closed")

    result={
      "status":"PASS" if not failures else "FAIL",
      "failures":failures,"warnings":warnings,
      "methods":len(methods),"fixtures":len(fixtures.get("scenarios",[])),
      "relations":len(relation_ids),"agentic_threats":len(threat_ids),
      "parent":"Cognigrex.cgx:/assurance"
    }
    print(json.dumps(result,sort_keys=True))
    return 1 if failures else 0

if __name__=="__main__":
    raise SystemExit(main())
