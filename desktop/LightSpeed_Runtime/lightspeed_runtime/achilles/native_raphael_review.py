"""Raphael engineering source binding for CGX-IM; review-only, no new engine."""
import hashlib,json,re
from lightspeed_runtime.achilles.native_geometry import digest,require
from lightspeed_runtime.cgx_capability_registry import REPO_ROOT,resolve_shortcall
from lightspeed_runtime.cgx_cross_analysis import atlas_review_workset,hydrate_atlas_review_rows

PATHS={
    "atlas":"cgx/component_atlas/component_geometry_atlas_v0_1.json",
    "kernel":"cgx/component_atlas/type1_equation_kernel_v0_1.json",
    "search":"cgx/component_atlas/raphael_component_geometry_search_v0_1.json",
    "online_projection":"apps/lightspeed-go/public/data/component_geometry_atlas_public_review.json",
}
MAX=5*1024*1024

def _read(key):
    path=REPO_ROOT/PATHS[key]
    require(path.resolve().is_relative_to(REPO_ROOT.resolve()),"source boundary")
    with path.open("rb") as f:raw=f.read(MAX+1)
    require(0<len(raw)<=MAX,"source size")
    return raw

def _sha(raw):return hashlib.sha256(raw).hexdigest()

def _records(raw,field,idfield,pattern):
    def unique(pairs):
        result={}
        for k,v in pairs:
            require(k not in result,"duplicate JSON key")
            result[k]=v
        return result
    doc=json.loads(raw,object_pairs_hook=unique)
    rows=doc[field]
    require(type(rows) is list and 1<=len(rows)<=2048,"records")
    result={}
    for row in rows:
        require(type(row) is dict and type(row.get(idfield)) is str and re.fullmatch(pattern,row[idfield]),"record id")
        key=row[idfield];require(key not in result,"duplicate record id")
        result[key]=row
    return doc,result

def _snapshot():
    raws={k:_read(k) for k in PATHS}
    hashes={k:_sha(v) for k,v in raws.items()}
    work=atlas_review_workset(raws["atlas"],expected_sha256=hashes["atlas"])
    kc,k=_records(raws["kernel"],"kernels","kernel_id",r"T1K-[0-9]{3}")
    sc,s=_records(raws["search"],"records","ID",r"RGS-[0-9]{3}")
    require(kc["artifact_id"]=="UTP-136" and kc["state"]=="DIGITAL ENGINEERING KERNEL / PHYSICAL_NOT_RUN","kernel scope")
    require(sc["record_count"]==len(s),"search count")
    require(all(all(type(row.get(f)) is str and row[f] for f in ("law","inputs","outputs","gate","falsifier")) for row in k.values()),"kernel evidence fields")
    require(all(all(type(row.get(f)) is str and row[f] for f in ("Conventional Baseline","Governing Kernel(s)","Measurement / Validation Gate","Failure / Residual Gate")) for row in s.values()),"search evidence fields")
    route=resolve_shortcall("Raphael","/sweep")
    require(route["route_id"]=="science.rfs_emff_sweep" and route["route"]["state"]=="available","solver registry changed")
    body={"schema":"CGX-IM-RAPHAEL-SOURCE-REVIEW/0.1","sources":{key:{"path":PATHS[key],"sha256":hashes[key]} for key in PATHS},
          "atlas_workset_sha256":work["workset_sha256"],"atlas_count":work["record_count"],
          "kernel_refs":{i:digest(v) for i,v in sorted(k.items())},
          "search_refs":{i:digest(v) for i,v in sorted(s.items())},
          "local_online_projection_byte_equal":raws["atlas"]==raws["online_projection"],
          "solver_route_id":route["route_id"],"solver_route_sha256":digest(route["route"]),
          "physical_instances_qualified":0,"native_admitted":False,"execution_authorized":False}
    return {"review":body,"sha256":digest(body)},raws,work,k,s

def source_review():
    return _snapshot()[0]

def resolve_review(expected_sha256,*,atlas_id,kernel_id,search_id,task_id,scope_revision,max_bytes,authorise):
    """Explicit caller-selected comparison context, not an inferred component-to-kernel mapping.
    Caller must authenticate the snapshot and authorisations. No solver invocation.
    """
    require(type(expected_sha256) is str and re.fullmatch(r"[a-f0-9]{64}",expected_sha256),"source digest")
    require(type(max_bytes) is int and 1<=max_bytes<=1024*1024,"budget")
    require(all(type(k) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}",k) for k in (atlas_id,kernel_id,search_id,task_id,scope_revision)),"request token")
    require(callable(authorise),"authority callback")
    selected=[("atlas",atlas_id),("kernel",kernel_id),("search",search_id)]
    def check(kind,key):
        if authorise(task_id,kind,key,scope_revision,expected_sha256) is not True:
            raise PermissionError("occurrence denied or revoked")
    for kind,key in selected:check(kind,key)
    env,raws,work,k,s=_snapshot()
    require(env["sha256"]==expected_sha256,"source revision changed")
    require(kernel_id in k and search_id in s and atlas_id in work["references"],"unknown occurrence")
    require(env["review"]["local_online_projection_byte_equal"],"projection divergence")
    rows={"kernel":k[kernel_id],"search":s[search_id]}
    cost=sum(len(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")) for v in rows.values())
    require(cost<max_bytes,"metadata budget")
    raw,receipt=hydrate_atlas_review_rows(raws["atlas"],expected_sha256=env["review"]["sources"]["atlas"]["sha256"],
          expected_workset_sha256=work["workset_sha256"],selected=[atlas_id],task_id=task_id,
          scope_revision=scope_revision,max_bytes=max_bytes-cost,
          authorise=lambda t,k,*_:authorise(t,"atlas",k,scope_revision,expected_sha256))
    rows["atlas"]=json.loads(raw[atlas_id])
    for kind,key in selected:check(kind,key)
    result={"schema":"CGX-IM-RAPHAEL-COMPARISON-CONTEXT/0.1","source_review_sha256":expected_sha256,
            "selected":dict(selected),"rows":rows,"atlas_receipt":receipt,
            "solver_route_id":env["review"]["solver_route_id"],"relationship_state":"CALLER_PROPOSED_NOT_VALIDATED",
            "physical_inference_authorized":False,"execution_authorized":False,"native_admitted":False}
    return {"review":result,"sha256":digest(result)}
