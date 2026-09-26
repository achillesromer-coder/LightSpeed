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


def view_ids_from_registry(views):
    ids={x.get("id") for x in views.get("shared_view_families",[]) if isinstance(x,dict) and isinstance(x.get("id"),str)}
    for key in ("eco_specialised_views","romer_specialised_views","emassc_ls_specialised_views"):
        ids.update(v for v in views.get(key,[]) if isinstance(v,str))
    return ids

def validate_view_selection_policy(policy, view_ids):
    failures=[]
    if policy.get("schema")!="CGX-VIEW-SELECTION-POLICY/0.1":
        failures.append("view-selection policy schema is not 0.1")
    if policy.get("status") not in {"review-blueprint","active"}:
        failures.append("view-selection policy status is not recognised")

    inputs=policy.get("inputs_in_priority_order")
    if not isinstance(inputs,list) or not inputs or inputs[0]!="security_and_admission":
        failures.append("view-selection policy does not place security_and_admission first")
    elif len(set(inputs))!=len(inputs):
        failures.append("view-selection policy priority inputs contain duplicates")

    required_constraints={
        "never show data outside admission/security lease",
        "never raise evidence ceiling because a public/investor/operator lens prefers certainty",
        "user preference cannot override security, authority, evidence or accessibility requirements",
        "Host-local session state remains outside canonical roots by default",
    }
    constraints=set(policy.get("hard_constraints") or [])
    missing_constraints=sorted(required_constraints-constraints)
    if missing_constraints:
        failures.append("view-selection policy missing hard constraints: "+", ".join(missing_constraints))

    task_mapping=policy.get("task_mapping")
    if not isinstance(task_mapping,dict) or not task_mapping:
        failures.append("view-selection policy task mapping is empty")
    else:
        for task,mapped in sorted(task_mapping.items()):
            if not isinstance(mapped,list) or not mapped:
                failures.append(f"view-selection task {task} has no views")
                continue
            unknown=sorted({v for v in mapped if v not in view_ids})
            if unknown:
                failures.append(f"view-selection task {task} references unknown views: {unknown}")

    hybrid=policy.get("hybridisation_policy") or {}
    if hybrid.get("max_primary_views")!=1:
        failures.append("view-selection hybrid policy must keep exactly one primary view")
    if "same stable object set" not in str(hybrid.get("combine_if","")):
        failures.append("view-selection hybrid policy is not bound to the same stable object set")

    output=policy.get("output") or {}
    if output.get("canonical_mutation") is not False:
        failures.append("view-selection output must not mutate canon")
    required_output={"security_scope","evidence_ceiling","source_root_binding"}
    output_fields=set(output.get("fields") or [])
    missing_output=sorted(required_output-output_fields)
    if missing_output:
        failures.append("view-selection output missing fields: "+", ".join(missing_output))

    return failures

def main():
    failures=[]; warnings=[]
    try:
        domains=load("domains.json")
        shell=load("corpus_aware_base_shell_contract.json")
        receipt=load("pilot_fixture_validation_receipt_2026-09-23.json")
        views=load("semantic_view_lens_registry.json")
        view_policy=load("view_selection_policy.json")
        shared_rel=load("relation_qualifier_contract.json")
        bridge=load("cross_domain_bridge_registry.json")
    except Exception as e:
        print(json.dumps({"status":"FAIL","failures":[str(e)]}))
        return 1

    if domains.get("schema")!="CGX-DOMAIN-TEMPLATES/0.2":
        failures.append("domains schema is not 0.2")
    if shell.get("schema")!="CGX-CORPUS-AWARE-BASE-SHELL/0.4":
        failures.append("base-shell contract is not 0.4")
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

    view_ids=view_ids_from_registry(views)
    failures.extend(validate_view_selection_policy(view_policy,view_ids))

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
