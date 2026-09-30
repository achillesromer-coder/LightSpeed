#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DT=ROOT/"cgx"/"domain_templates"

def load(name):
    return json.loads((DT/name).read_text(encoding="utf-8"))

def main():
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
    print({"status":"PASS" if not failures else "FAIL","failures":failures,"tasks":len(tasks)})
    return 1 if failures else 0

if __name__=="__main__":
    raise SystemExit(main())
