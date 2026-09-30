#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DT = ROOT / "cgx" / "domain_templates"

def load(name):
    p = DT / name
    if not p.exists():
        raise AssertionError(f"missing required template: {name}")
    return json.loads(p.read_text(encoding="utf-8"))

def flatten_type_values(obj):
    out=[]
    if isinstance(obj, dict):
        for k,v in obj.items():
            if k in {"schema","status","domain","domains","rule","numeric_model_rule","host_local_default","pilot_additions"}:
                continue
            out.extend(flatten_type_values(v))
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v,str):
                out.append(v)
            elif isinstance(v,(dict,list)):
                out.extend(flatten_type_values(v))
    return out

def relation_ids(obj):
    out=set()
    if isinstance(obj, dict):
        if isinstance(obj.get("id"),str):
            out.add(obj["id"])
        for v in obj.values():
            out |= relation_ids(v)
    elif isinstance(obj,list):
        for v in obj:
            out |= relation_ids(v)
    return out

def main():
    failures=[]; warnings=[]
    try:
        domains=load("domains.json")
        shell=load("corpus_aware_base_shell_contract.json")
        receipt=load("pilot_fixture_validation_receipt_2026-09-23.json")
        views=load("semantic_view_lens_registry.json")
        shared_rel=load("relation_qualifier_contract.json")
        bridge=load("cross_domain_bridge_registry.json")
        ext_registry=load("custodial_extension_registry.json")
        cgp_policy=load("cgp_ies_policy_pack.json")
        cgp_fixtures=load("cgp_ies_fixture_scenarios.json")
        cgp_terminology=load("cgp_ies_terminology_map.json")
        cgp_adapters=load("cgp_ies_domain_adapter_registry.json")
        cgp_decision_receipt=load("cgp_ies_decision_receipt_schema.json")
        cgp_owner_values=load("cgp_ies_owner_confirmation_values.json")
        cgp_parent_hydration=load("cgp_ies_parent_extension_manifest.json")
        assurance_registry=load("assurance_method_registry.json")
        assurance_schema=load("unified_assurance_object_schema.json")
        assurance_matrix=load("assurance_selection_matrix.json")
        assurance_crosswalk=load("assurance_reference_crosswalk.json")
        assurance_fixtures=load("assurance_fixture_scenarios.json")
        technology_stack=load("technology_stack_registry.json")
        agent_runtime=load("agent_runtime_contract.json")
    except Exception as e:
        print(json.dumps({"status":"FAIL","failures":[str(e)]}))
        return 1

    if domains.get("schema")!="CGX-DOMAIN-TEMPLATES/0.4":
        failures.append("domains schema is not 0.4")
    if shell.get("schema")!="CGX-CORPUS-AWARE-BASE-SHELL/0.6":
        failures.append("base-shell contract is not 0.6")
    if domains.get("parent_filespace",{}).get("file")!="Cognigrex.cgx":
        failures.append("parent filespace is not Cognigrex.cgx")

    gp=domains.get("generation_policy",{})
    if gp.get("source_authority")!="latest-durably-observed-Recovery-authority-only":
        failures.append("generator seed is not Recovery-only")
    if "seed-from-unpromoted-validation-candidate" not in gp.get("forbidden",[]):
        failures.append("unpromoted Validation seed is not fail-closed")
    expected_seed={
        "state":"S91/v1.61",
        "sha256":"1138da5af4e1c66eb60120dd050e2037fc8d7799a9ccebb01ad48089b234785f",
        "content_root":"af640b499078853371196cf7c905979cebf0761c15552b6b8dfbf3ff3d04448d",
        "dbr_root":"18d43abf68b5f7857a21dcb480d9970e95cdacfc869c61b3b1497e900f0dcc64",
        "topology":"150e5267792f43f47807a9f5ca61f12db8077ac98153c2cc6c306a4177de937e",
    }
    if gp.get("current_recovery_at_2026_09_23")!=expected_seed["state"]:
        failures.append("current Recovery pointer is not S91/v1.61")
    if gp.get("current_recovery_sha256")!=expected_seed["sha256"]:
        failures.append("current Recovery SHA-256 mismatch")
    if gp.get("current_recovery_content_root")!=expected_seed["content_root"]:
        failures.append("current Recovery content-root mismatch")
    if gp.get("current_recovery_dbr_root")!=expected_seed["dbr_root"]:
        failures.append("current Recovery DBR-root mismatch")
    if gp.get("current_recovery_topology")!=expected_seed["topology"]:
        failures.append("current Recovery topology mismatch")
    if gp.get("accepted_later_candidate") not in (None,"",[]):
        warnings.append("later candidate remains populated after S91 Recovery promotion")
    promo=gp.get("recovery_promotion_evidence") or {}
    if not promo.get("exact_byte_match"):
        failures.append("S91 Recovery promotion lacks exact-byte-match receipt")

    shared=domains.get("shared_contracts",{})
    for key,name in shared.items():
        if not (DT/name).exists():
            failures.append(f"shared contract missing: {key} -> {name}")

    view_ids={x.get("id") for x in views.get("shared_view_families",[]) if isinstance(x,dict)}
    for key in ("eco_specialised_views","romer_specialised_views","emassc_ls_specialised_views"):
        view_ids.update(v for v in views.get(key,[]) if isinstance(v,str))

    domain_files={
        "romer":("romer_type_registry.json","romer_relation_registry.json"),
        "eco":("eco_type_registry.json","eco_relation_registry.json"),
        "emassc":("emassc_ls_type_registry.json","emassc_ls_relation_registry.json"),
    }
    shared_rel_ids=relation_ids(shared_rel)
    for domain,cfg in domains.get("domains",{}).items():
        if domain not in domain_files:
            continue
        tname,rname=domain_files[domain]
        typ=load(tname); rel=load(rname)
        vals=flatten_type_values(typ)
        dup=sorted({x for x in vals if vals.count(x)>1})
        if dup:
            warnings.append(f"{domain}: repeated type labels across registry groups: {dup}")
        if not relation_ids(rel):
            failures.append(f"{domain}: no typed relations")
        if not shared_rel_ids:
            failures.append("shared relation registry empty")
        for field in ("semantic_library","type_registry","relation_registry"):
            ref=cfg.get(field)
            if not ref or not (DT/ref).exists():
                failures.append(f"{domain}: unresolved {field}: {ref}")
        for v in cfg.get("default_views",[]):
            if v not in view_ids:
                failures.append(f"{domain}: unknown default view: {v}")

    ls=domains.get("domains",{}).get("emassc",{}).get("children",{}).get("lightspeed")
    if not ls or ls.get("file")!="LS.cgx":
        failures.append("LS.cgx is not bound beneath EMASSC")

    cgp=[x for x in ext_registry.get("extensions",[]) if x.get("id")=="cgp-ies"]
    if len(cgp)!=1:
        failures.append("cgp-ies shared extension missing or duplicated")
    else:
        cgp=cgp[0]
        if cgp.get("binding_mode")!="REFERENCE":
            failures.append("cgp-ies must bind by reference")
        if cgp.get("source_path")!="Cognigrex.cgx:/extensions/cgp-ies":
            failures.append("cgp-ies parent source path mismatch")
    if cgp_policy.get("schema")!="CGX-CGP-IES-POLICY/0.1":
        failures.append("cgp-ies policy schema mismatch")
    if len(cgp_fixtures.get("scenarios",[]))<18:
        failures.append("cgp-ies fixture coverage below eighteen scenarios")
    if cgp_terminology.get("schema")!="CGX-CGP-IES-TERMINOLOGY/0.1":
        failures.append("cgp-ies terminology schema mismatch")
    if cgp_adapters.get("schema")!="CGX-CGP-IES-DOMAIN-ADAPTERS/0.1":
        failures.append("cgp-ies domain adapter schema mismatch")
    if set(cgp_adapters.get("domains",{})) != {"romer","eco","emassc","lightspeed"}:
        failures.append("cgp-ies domain adapter coverage mismatch")
    if cgp_decision_receipt.get("schema")!="CGX-CGP-IES-DECISION-RECEIPT/0.1":
        failures.append("cgp-ies decision receipt schema mismatch")
    if cgp_owner_values.get("status","").find("REVIEW_REQUIRED")<0:
        failures.append("cgp-ies owner values must remain review-required before parent promotion")
    if cgp_parent_hydration.get("status")!="PRE_CANONICAL_CANDIDATE_ONLY":
        failures.append("cgp-ies parent hydration must remain pre-canonical candidate only")
    if cgp_parent_hydration.get("seed",{}).get("sha256")!=expected_seed["sha256"]:
        failures.append("cgp-ies parent hydration seed is not exact S91 Recovery")
    if "extensions/bindings" not in shell.get("required_sections",[]):
        failures.append("base shell does not require extension binding")

    if assurance_registry.get("location")!="Cognigrex.cgx:/assurance":
        failures.append("assurance parent source path mismatch")
    if assurance_schema.get("schema")!="CGX-UNIFIED-ASSURANCE-OBJECT/0.1":
        failures.append("unified assurance object schema mismatch")
    if assurance_matrix.get("schema")!="CGX-ASSURANCE-SELECTION-MATRIX/0.1":
        failures.append("assurance selection matrix schema mismatch")
    if assurance_crosswalk.get("status")!="applicability map / not certification":
        failures.append("assurance reference crosswalk must remain non-certification")
    if len(assurance_fixtures.get("scenarios",[]))<10:
        failures.append("assurance fixture coverage below ten scenarios")
    if "assurance/bindings" not in shell.get("required_sections",[]):
        failures.append("base shell does not require assurance binding")
    if "assurance" not in domains.get("parent_filespace",{}).get("shared_kernel",[]):
        failures.append("assurance missing from parent shared kernel")

    if technology_stack.get("schema")!="CGX-TECHNOLOGY-STACK/0.1":
        failures.append("technology stack schema mismatch")
    if technology_stack.get("location")!="Cognigrex.cgx:/stack":
        failures.append("technology stack parent path mismatch")
    if agent_runtime.get("schema")!="CGX-AGENT-RUNTIME-CONTRACT/0.1":
        failures.append("agent runtime contract schema mismatch")
    if "model-is-capability-not-agent-identity" not in agent_runtime.get("invariants",[]):
        failures.append("agent/model identity boundary missing")

    proof=receipt.get("proof",{})
    if proof.get("fixtures")!=3 or proof.get("failures")!=0:
        failures.append("pilot fixture proof is not 3 fixtures / 0 failures")
    if proof.get("warnings")!=2:
        warnings.append("pilot warning count changed from expected bounded value 2")
    if receipt.get("generator_gate") is None:
        failures.append("pilot receipt lacks generator gate")
    if bridge.get("location")!="Cognigrex.cgx:/graph/bridges":
        failures.append("cross-domain bridge registry is not parent-bound")

    result={
        "status":"PASS" if not failures else "FAIL",
        "failures":failures,
        "warnings":warnings,
        "recovery_seed":gp.get("current_recovery_at_2026_09_23"),
        "later_candidate":gp.get("accepted_later_candidate"),
        "fixture_bundle_sha256":receipt.get("fixture_bundle",{}).get("sha256"),
        "recovery_sha256":gp.get("current_recovery_sha256"),
        "recovery_content_root":gp.get("current_recovery_content_root"),
        "recovery_dbr_root":gp.get("current_recovery_dbr_root"),
        "recovery_topology":gp.get("current_recovery_topology"),
    }
    print(json.dumps(result,sort_keys=True))
    return 1 if failures else 0

if __name__=="__main__":
    sys.exit(main())
