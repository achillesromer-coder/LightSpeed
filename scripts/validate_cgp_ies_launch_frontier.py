#!/usr/bin/env python3
from __future__ import annotations
import json
import hashlib
import argparse
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DT=ROOT/"cgx"/"domain_templates"

def load(name):
    return json.loads((DT/name).read_text(encoding="utf-8"))

def frontier_review(queue):
    """A dependency review projection, not an executor or an authority grant."""
    tasks=queue["tasks"]
    by_id={t["task_id"]:t for t in tasks}
    if len(by_id)!=len(tasks):raise ValueError("duplicate frontier identity")
    rows=[]
    for t in tasks:
        tid=t["task_id"]
        blocked=[d for d in t["depends_on"] if by_id[d]["state"]!="COMPLETE"]
        if t["state"]=="COMPLETE":state="RECORDED_COMPLETE_REVIEW_ONLY"
        elif blocked:state="DEPENDENCY_HOLD"
        elif t["evidence_class"] in {"PHYSICAL_FIELD_EVIDENCE","HOST_SECURITY_EVIDENCE"}:state="EMPIRICAL_EVIDENCE_HOLD"
        elif t["execution_class"]=="COMPUTE_ONLY" and t["state"]=="READY_FOR_DATA_ASSEMBLY":
            state="SOURCE_ASSEMBLY_CANDIDATE"
        else:state="AUTHORITY_OR_FRONTIER_REVIEW"
        data=json.dumps(t,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")
        rows.append({"task_id":tid,"record_sha256":hashlib.sha256(data).hexdigest(),
            "owner":t["owner"],"state":state,"source_state":t["state"],"blocked_dependencies":blocked,
            "execution_authorized":False})
    return rows


_OBJECT_SOURCE_CANDIDATES={
    "CGX-OBJ-001":("romer",("cgx/domain_templates/romer_semantic_library.json",
        "cgx/domain_templates/mark3_legacy_engineering_model_audit_2026-10-05.json",
        "docs/engineering/MARK_III_MULTI_UNIT_SCREENING_CONTRACT.md")),
    "CGX-OBJ-002":("romer",("cgx/domain_templates/romer_semantic_library.json",
        "apps/operations/asteroid-cluster-sequence/source-capture-status.md",
        "apps/public/asteroids/apophis/data/object-public-contract.json")),
    "CGX-OBJ-003":("eco",("cgx/domain_templates/eco_semantic_library.json",)),
    "CGX-OBJ-004":("romer",("cgx/domain_templates/romer_semantic_library.json",
        "apps/lightspeed-go/public/review/mesh/intersol.json")),
    "CGX-OBJ-005":("lightspeed",("cgx/domain_templates/agent_runtime_contract.json",
        "cgx/domain_templates/achilles_owner_operator_profile.json")),
}


def object_source_review(queue,schema):
    """Bind candidate source revisions and existing policy checks to five task IDs.

    Domain definitions, model audits, preview meshes and agent profiles are not
    evidence of the target object's actual parameters or safety. No new object
    ID, numeric value, executable authority or lifecycle state is synthesised.
    """
    root=ROOT.resolve()
    rows={r["task_id"]:r for r in frontier_review(queue)}
    adapters=load("cgp_ies_domain_adapter_registry.json")
    required=schema["required_fields"]
    if (type(required) is not list or len(set(required))!=len(required)
            or schema["replication_budget"]["default_if_open"]!="0 consequential autonomous children"):
        raise ValueError("object schema or safe default changed")
    def source_ref(rel):
        p=root/rel
        if not p.resolve().is_relative_to(root) or not p.is_file():
            raise ValueError("object candidate source unavailable")
        with p.open("rb") as stream:raw=stream.read(5*1024*1024+1)
        if not 1<=len(raw)<=5*1024*1024:raise ValueError("object candidate source budget")
        return {"source_path":rel,"source_sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),
                "binding_state":"CANDIDATE_REVIEW_ONLY"}
    results=[]
    shared={}
    for task,(domain,paths) in _OBJECT_SOURCE_CANDIDATES.items():
        row=rows[task]
        if row["state"]!="SOURCE_ASSEMBLY_CANDIDATE":
            raise ValueError("object source assembly no longer eligible")
        adapter=adapters["domains"][domain]
        for path in paths:
            if path not in shared:shared[path]=source_ref(path)
        results.append({"task_id":task,"task_sha256":row["record_sha256"],
           "adapter":domain,"owner":row["owner"],"candidate_sources":list(paths),
           "required_checks":adapter["required_checks"],"required_object_fields":required,
           "bound_instance_fields":{},"unresolved_instance_fields":required,
           "replication_default":schema["replication_budget"]["default_if_open"],
           "disposition":"SOURCE_REFERENCES_BOUND_INSTANCE_EVIDENCE_OPEN",
           "execution_authorized":False,"native_admitted":False})
    policy_path="cgx/domain_templates/cgp_ies_domain_adapter_registry.json"
    schema_path="cgx/domain_templates/cgp_ies_object_envelope_schema.json"
    # A caller-supplied schema must match the canonical file, not just its name.
    if schema!=load("cgp_ies_object_envelope_schema.json"):raise ValueError("object schema source mismatch")
    receipt={"schema":"CGX-FRONTIER-OBJECT-SOURCE-REVIEW/0.1","source_refs":dict(sorted(shared.items())),
        "schema_ref":source_ref(schema_path),"adapter_ref":source_ref(policy_path),
        "objects":results,"execution_authorized":False,"native_admitted":False}
    raw=json.dumps(receipt,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")
    return {**receipt,"review_sha256":hashlib.sha256(raw).hexdigest()}


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--workset-review",action="store_true")
    args=parser.parse_args(argv)
    failures=[]
    queue=load("cgp_ies_launch_frontier_queue.json")
    schema=load("cgp_ies_object_envelope_schema.json")
    if queue.get("schema")!="CGX-CGP-IES-LAUNCH-FRONTIER/0.1":
        failures.append("launch frontier queue schema")
    if schema.get("schema")!="CGX-CGP-IES-OBJECT-ENVELOPE/0.1":
        failures.append("object envelope schema")
    tasks=queue.get("tasks",[])
    ids=[x.get("task_id") for x in tasks]
    if len(ids)!=len(set(ids)):
        failures.append("duplicate task ids")
    known=set(ids)
    for t in tasks:
        for dep in t.get("depends_on",[]):
            if dep not in known:
                failures.append(f'{t.get("task_id")}: unknown dependency {dep}')
        if t.get("evidence_class") in {"PHYSICAL_FIELD_EVIDENCE","HOST_SECURITY_EVIDENCE"} and t.get("synthetic_closure_forbidden") is not True:
            failures.append(f'{t.get("task_id")}: empirical task permits synthetic closure')
    # cycle check
    graph={t["task_id"]:list(t.get("depends_on",[])) for t in tasks}
    visiting=set(); visited=set()
    def visit(n):
        if n in visiting:
            failures.append("dependency cycle:"+n); return
        if n in visited: return
        visiting.add(n)
        for d in graph.get(n,[]): visit(d)
        visiting.remove(n); visited.add(n)
    for n in graph: visit(n)

    required=set(schema.get("required_fields",[]))
    must={"object_id","effective_ceiling","mvsl","authority","replication_budget","stop_safe_state","restart","inheritance","open_evidence"}
    if not must.issubset(required):
        failures.append("object envelope misses mandatory executable fields")
    if schema.get("replication_budget",{}).get("default_if_open")!="0 consequential autonomous children":
        failures.append("replication default is not fail-closed")
    if queue.get("policy",{}).get("no_synthetic_empirical_closure") is not True:
        failures.append("queue empirical closure rule missing")
    if args.workset_review and not failures:
        runtime=ROOT/"desktop/LightSpeed_Runtime"
        if str(runtime) not in sys.path:sys.path.insert(0,str(runtime))
        from lightspeed_runtime.cgx_cross_analysis import atlas_review_workset
        path=ROOT/"cgx/component_atlas/component_geometry_atlas_v0_1.json"
        with path.open("rb") as stream:raw=stream.read(5*1024*1024+1)
        atlas=atlas_review_workset(raw,expected_sha256=hashlib.sha256(raw).hexdigest())
        from collections import Counter
        review=frontier_review(queue)
        object_review=object_source_review(queue,schema)
        print(json.dumps({"schema":"CGX-LAUNCH-WORKSET-REVIEW/0.1",
            "object_source_review_sha256":object_review["review_sha256"],
            "object_source_count":len(object_review["source_refs"]),
            "object_review_count":len(object_review["objects"]),
            "frontier":review,"frontier_states":dict(Counter(x["state"] for x in review)),
            "atlas_records":atlas["record_count"],"atlas_unique_metadata":atlas["unique_metadata_count"],
            "atlas_source_sha256":atlas["source_sha256"],"atlas_workset_sha256":atlas["workset_sha256"],
            "physical_instances_qualified":0,"implementation_units_completed":0,"execution_authorized":False,
            "native_admitted":False},sort_keys=True))
    print({"status":"PASS" if not failures else "FAIL","failures":failures,"tasks":len(tasks)})
    return 1 if failures else 0

if __name__=="__main__":
    raise SystemExit(main())
