from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lightspeed_runtime.cgx_cross_analysis import source_hybridisation_candidates, CGXCrossAnalysisError

def test_duplicates_and_variants_preserve_occurrences():
    x=b"def f(x): return x+1"
    y=b"# wrapper\ndef f(x): return x+1"
    z=b"def f(x): return x-1"
    sources={"raphael":x,"ls":x,"wrapper":y,"variant":z}
    r=source_hybridisation_candidates(sources)
    assert r==source_hybridisation_candidates(dict(reversed(list(sources.items()))))
    assert r["distinct_payload_count"]==3
    assert r["exact_payload_groups"][0]["occurrences"]==["ls","raphael"]
    assert len(r["function_candidates"][0]["syntax_variants"])==2
    assert not r["semantic_equivalence_proven"] and not r["native_admitted"]

def test_context_and_duplicate_definitions_not_discarded():
    r=source_hybridisation_candidates({"a":b"v=1\ndef f(): return v\ndef f(): return v","b":b"v=2\ndef f(): return v"})
    c=r["function_candidates"][0]
    assert len(c["syntax_variants"][0]["occurrences"])==3
    assert "dependency_binding" in c["requires"]
    assert not r["execution_performed"]

def test_invalid_source_and_budget():
    r=source_hybridisation_candidates({"invalid":b"def :","never_run":b"raise RuntimeError('must not execute')"})
    assert r["unparsed_sources"]==["invalid"]
    with pytest.raises(CGXCrossAnalysisError): source_hybridisation_candidates({"a":b"x"*(5*1024*1024+1)})
    with pytest.raises(CGXCrossAnalysisError): source_hybridisation_candidates({"a":"not bytes"})



# Freeze the exact previously inspected legacy function, not the whole module.
# Only that function is executed; the wrapper and its GUI/main code never run.
LEGACY_KERNEL = """def mandelbrot_set(width, height, zoom, max_iter):
    \"\"\"
    Generates a Mandelbrot fractal set for a 2D projection.
    \"\"\"
    x = np.linspace(-2.0, 2.0, width) / zoom
    y = np.linspace(-2.0, 2.0, height) / zoom
    fractal = np.zeros((width, height))
    for i, x_val in enumerate(x):
        for j, y_val in enumerate(y):
            z = 0
            c = complex(x_val, y_val)
            for k in range(max_iter):
                if abs(z) > 2.0:
                    fractal[i, j] = k
                    break
                z = z * z + c
    return fractal
"""


def checked_legacy_kernel(raw):
    import ast
    import numpy as np
    assert len(raw) <= 256 * 1024
    tree = ast.parse(raw)
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name == "mandelbrot_set"]
    # A subsequent assignment/import could shadow a function in a real module.
    # This checks only the extracted body with explicit dependencies.
    assert len(nodes) == 1
    assert ast.dump(nodes[0], include_attributes=False) == ast.dump(
        ast.parse(LEGACY_KERNEL).body[0], include_attributes=False)
    env = {"np": np, "__builtins__": {"enumerate": enumerate, "range": range,
                                       "abs": abs, "complex": complex}}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<reviewed-kernel>", "exec"), env)
    return env["mandelbrot_set"]


CASES = [(1,1,1.0,1), (3,3,1.0,8), (5,7,.5,16), (17,11,1.7,32),
         (32,25,4.0,64), (9,13,.125,3)]


def test_actual_legacy_kernel_reuse():
    import numpy as np
    from lightspeed_runtime.cgx_cross_analysis import mandelbrot_grid_candidate
    repo = Path(__file__).resolve().parents[3]
    axis = repo / "desktop/Desktop_Hooks/LightSpeed/Z Axis"
    paths = [axis/"Z-4_Merovingian/core/physics/raphael/fractal_expansion.py",
             axis/"Z0_TheConstruct/cosmological/fractal_expansion.py"]
    for path in paths:
        legacy = checked_legacy_kernel(path.read_bytes())
        for case in CASES:
            result = mandelbrot_grid_candidate(*case)
            assert np.array_equal(result["grid"], legacy(*case))
            assert not result["native_admitted"]


def test_shared_grid_independent_known_points_and_negative_cases():
    from lightspeed_runtime.cgx_cross_analysis import mandelbrot_grid_candidate
    assert mandelbrot_grid_candidate(3,3,1,8)["grid"] == [[1,0,1],[2,0,2],[1,2,1]]
    assert mandelbrot_grid_candidate(3,3,1,1)["grid"] == [[0,0,0]]*3
    for case in [(0,3,1,8),(True,3,1,8),(3,3,0,8),(3,3,float("nan"),8),
                 (3,3,float("inf"),8),(128,128,1,256),(3,3,1,257)]:
        with pytest.raises(CGXCrossAnalysisError):
            mandelbrot_grid_candidate(*case)
    with pytest.raises(AssertionError):
        checked_legacy_kernel(LEGACY_KERNEL.replace("z = 0", "z = 1").encode())


def test_existing_route_resolves_compact_and_expanded_receipt():
    import hashlib
    import importlib
    import json
    from lightspeed_runtime.cgx_capability_registry import selector_profile
    for selector in ("Achilles", "Cognigrex"):
        profile = selector_profile(selector)
        route = profile["routes"]["science.fractal_grid"]
        assert route["state"] == "gated" and route["authority_transfer"] is False
    module, handler = route["handler"].split(":")
    run = getattr(importlib.import_module(module), handler)
    compact = run(17,11,1,32)
    expanded = run(17,11,1.0,32,include_grid=True)
    assert "grid" not in compact and not compact["payload_included"]
    assert expanded["payload_included"] and compact["review_sha256"] == expanded["review_sha256"]
    payload = json.dumps(expanded["grid"],separators=(",",":")).encode("ascii")
    assert len(payload) == compact["payload_bytes"]
    assert hashlib.sha256(payload).hexdigest() == compact["payload_sha256"]
    fields = {k:v for k,v in compact.items() if k not in ("review_sha256","payload_included")}
    assert hashlib.sha256(json.dumps(fields,sort_keys=True,separators=(",",":")).encode("ascii")).hexdigest() == compact["review_sha256"]
    assert compact["review_sha256"] != run(17,11,2,32)["review_sha256"]
    assert not compact["payload_persisted"] and not compact["native_admitted"]
    with pytest.raises(CGXCrossAnalysisError): run(17,11,1,32,include_grid="true")
    with pytest.raises(CGXCrossAnalysisError): run(128,128,1,256)



def test_ternary_recursive_payload_and_sparse_fetch():
    from lightspeed_runtime.cgx_cross_analysis import pack_nested_review_payload, hydrate_nested_review_payload
    raw=b"".join(bytes([i])*64 for i in range(27))
    root, objects=pack_nested_review_payload(raw,chunk_bytes=64)
    assert (root,objects)==pack_nested_review_payload(raw,chunk_bytes=64)
    full, f=hydrate_nested_review_payload(root,objects.__getitem__,allowed_prefixes=("",),max_bytes=100000)
    sub, s=hydrate_nested_review_payload(root,objects.__getitem__,"12",allowed_prefixes=("1",),max_bytes=10000)
    assert full==raw and sub==raw[15*64:18*64]
    assert s["fetched_objects"]<f["fetched_objects"] and s["fetched_bytes"]<f["fetched_bytes"]
    with pytest.raises(PermissionError):
        hydrate_nested_review_payload(root,objects.__getitem__,"",allowed_prefixes=("1",),max_bytes=100000)
    with pytest.raises(CGXCrossAnalysisError):
        hydrate_nested_review_payload(root,objects.__getitem__,"3",allowed_prefixes=("",),max_bytes=10000)
    with pytest.raises(CGXCrossAnalysisError):
        hydrate_nested_review_payload(root,lambda k: b"tampered",allowed_prefixes=("",),max_bytes=10000)
    with pytest.raises(CGXCrossAnalysisError):
        hydrate_nested_review_payload(root,objects.__getitem__,allowed_prefixes=("",),max_bytes=1)


def test_ternary_repeated_binary_and_empty_roundtrip():
    from lightspeed_runtime.cgx_cross_analysis import pack_nested_review_payload, hydrate_nested_review_payload
    for raw in (b"", bytes(range(64))*81, b"abc"*87):
        root, objects=pack_nested_review_payload(raw,chunk_bytes=64)
        out, stats=hydrate_nested_review_payload(root,objects.__getitem__,allowed_prefixes=("",),max_bytes=100000)
        assert out==raw
        if len(raw)==64*81: assert stats["fetched_objects"]<10


def test_ternary_grid_reference_same_payload_hash():
    import hashlib,json
    from lightspeed_runtime.cgx_cross_analysis import fractal_grid_review_receipt,pack_nested_review_payload,hydrate_nested_review_payload
    r=fractal_grid_review_receipt(31,29,1.2,32,include_grid=True)
    raw=json.dumps(r["grid"],separators=(",",":")).encode("ascii")
    root,objects=pack_nested_review_payload(raw)
    hydrated,_=hydrate_nested_review_payload(root,objects.__getitem__,allowed_prefixes=("",),max_bytes=100000)
    assert hashlib.sha256(hydrated).hexdigest()==r["payload_sha256"]



def test_persisted_review_carrier_and_subset(tmp_path):
    import zipfile
    from lightspeed_runtime.cgx_cross_analysis import write_nested_review_archive,hydrate_nested_review_archive
    path=tmp_path/"review.zip"
    raw=b"".join(bytes([i])*64 for i in range(27))
    with zipfile.ZipFile(path,"w") as z:
        root=write_nested_review_archive(z,raw,chunk_bytes=64)
        with pytest.raises(CGXCrossAnalysisError): write_nested_review_archive(z,raw)
    with zipfile.ZipFile(path) as z:
        out, full=hydrate_nested_review_archive(z,root,allowed_prefixes=("",),max_bytes=100000)
        part, sub=hydrate_nested_review_archive(z,root,"2",allowed_prefixes=("2",),max_bytes=100000)
        assert out==raw and part==raw[18*64:]
        assert sub["fetched_bytes"]<full["fetched_bytes"]
        with pytest.raises(PermissionError):
            hydrate_nested_review_archive(z,root,"1",allowed_prefixes=("2",),max_bytes=100000)
        with pytest.raises(CGXCrossAnalysisError,match="missing"):
            hydrate_nested_review_archive(z,"0"*64,allowed_prefixes=("",),max_bytes=100000)


def test_review_carrier_rejects_tampering_and_wrong_namespace(tmp_path):
    import hashlib,zipfile
    from lightspeed_runtime.cgx_cross_analysis import hydrate_nested_review_archive
    root=hashlib.sha256(b"expected").hexdigest()
    p=tmp_path/"review.zip"
    with zipfile.ZipFile(p,"w") as z:
        z.writestr("review/objects/"+root,b"wrong")
    with zipfile.ZipFile(p) as z:
        with pytest.raises(CGXCrossAnalysisError,match="hash mismatch"):
            hydrate_nested_review_archive(z,root,allowed_prefixes=("",),max_bytes=100000)
    with zipfile.ZipFile(p,"w") as z:
        z.writestr("../outside",b"x")
    with zipfile.ZipFile(p) as z:
        with pytest.raises(CGXCrossAnalysisError,match="member"):
            hydrate_nested_review_archive(z,root,allowed_prefixes=("",),max_bytes=100000)



def test_existing_achilles_profile_semantic_roundtrip():
    import hashlib,json
    from lightspeed_runtime.cgx_cross_analysis import pack_achilles_profile_review,hydrate_achilles_profile_section
    source=(Path(__file__).resolve().parents[3]/"cgx/domain_templates/achilles_owner_operator_profile.json").read_bytes()
    original=json.loads(source)
    descriptor,stamp,objects=pack_achilles_profile_review(source)
    assert (descriptor,stamp,objects)==pack_achilles_profile_review(source)
    assert descriptor["source_sha256"]==hashlib.sha256(source).hexdigest()
    rebuilt={}
    for name in descriptor["sections"]:
        rebuilt[name],_=hydrate_achilles_profile_section(descriptor,stamp,name,objects.__getitem__,allowed_sections=(name,),max_bytes=1000000)
    assert rebuilt==original
    assert not descriptor["native_admitted"] and not descriptor["model_weights_included"]
    with pytest.raises(PermissionError):
        hydrate_achilles_profile_section(descriptor,stamp,"authority",objects.__getitem__,allowed_sections=("identity",),max_bytes=1000000)
    with pytest.raises(CGXCrossAnalysisError,match="descriptor hash"):
        hydrate_achilles_profile_section(dict(descriptor,agent="Other"),stamp,"identity",objects.__getitem__,allowed_sections=("identity",),max_bytes=1000000)
    with pytest.raises(CGXCrossAnalysisError):
        pack_achilles_profile_review(json.dumps(dict(original,identity={"agent":"Other"})).encode())
    with pytest.raises(CGXCrossAnalysisError):
        pack_achilles_profile_review(b'{"x":1,"x":2}')



def test_accumulative_context_roundtrip_and_aggregate_budget():
    import json
    from lightspeed_runtime.cgx_cross_analysis import pack_achilles_profile_review, resolve_achilles_review_context
    raw=(Path(__file__).resolve().parents[3]/"cgx/domain_templates/achilles_owner_operator_profile.json").read_bytes()
    d,h,o=pack_achilles_profile_review(raw)
    selected=("identity","dynamic_system_research","source_contract")
    calls=[]
    def fetch(k):
        calls.append(k)
        return o[k]
    values,receipt,stats=resolve_achilles_review_context(d,h,selected,fetch,allowed_sections=selected,max_bytes=1000000)
    assert values=={k:json.loads(raw)[k] for k in selected}
    assert len(calls)==len(set(calls))==stats["fetched_objects"]
    assert not receipt["complete_profile"] and not receipt["reasoning_evaluated"]
    assert resolve_achilles_review_context(d,h,selected[::-1],o.__getitem__,allowed_sections=selected,max_bytes=1000000)[:2]==(values,receipt)
    all_sections=tuple(d["sections"])
    rebuilt,full,_=resolve_achilles_review_context(d,h,all_sections,o.__getitem__,allowed_sections=all_sections,max_bytes=1000000)
    assert rebuilt==json.loads(raw) and full["complete_profile"]
    calls.clear()
    with pytest.raises(PermissionError):
        resolve_achilles_review_context(d,h,selected,fetch,allowed_sections=("identity",),max_bytes=1000000)
    assert calls==[]
    with pytest.raises(CGXCrossAnalysisError):
        resolve_achilles_review_context(d,h,selected,o.__getitem__,allowed_sections=selected,max_bytes=stats["fetched_bytes"]-1)
    with pytest.raises(CGXCrossAnalysisError):
        resolve_achilles_review_context(d,h,("identity","identity"),o.__getitem__,allowed_sections=selected,max_bytes=1000000)
    with pytest.raises(CGXCrossAnalysisError):
        resolve_achilles_review_context(d,h,selected,lambda k:b"tampered",allowed_sections=selected,max_bytes=1000000)


def test_accumulative_context_reuses_identical_section_objects():
    import json
    from lightspeed_runtime.cgx_cross_analysis import pack_achilles_profile_review, resolve_achilles_review_context
    raw=json.dumps({"identity":{"agent":"Achilles","canonical_semantic_parent":"cgx:root:cognigrex"},
                    "lifecycle":{"native_dbr_admission":False,"release_authorized":False},
                    "dynamic_system_research":{},"a":{"same":1},"b":{"same":1}}).encode()
    d,h,o=pack_achilles_profile_review(raw)
    v,r,s=resolve_achilles_review_context(d,h,("a","b"),o.__getitem__,allowed_sections=("a","b"),max_bytes=10000)
    assert v["a"]==v["b"] and len(r["sections"])==2
    assert s["reused_reads"]==2 and s["fetched_objects"]==2



def test_achilles_revision_reuse_and_inverse():
    import json
    from lightspeed_runtime.cgx_cross_analysis import (
        pack_achilles_profile_review, resolve_achilles_review_context,
        resolve_achilles_revision_context)
    raw=(Path(__file__).resolve().parents[3]/"cgx/domain_templates/achilles_owner_operator_profile.json").read_bytes()
    d,h,o=pack_achilles_profile_review(raw)
    keys=("identity","source_contract","dynamic_system_research")
    before,receipt,baseline=resolve_achilles_review_context(d,h,keys,o.__getitem__,allowed_sections=keys,max_bytes=1000000)
    revised=json.loads(raw)
    revised["dynamic_system_research"]["synthetic_revision_test_only"]=True
    d2,h2,o2=pack_achilles_profile_review(json.dumps(revised).encode())
    after,proof,transition,stats=resolve_achilles_revision_context(
        d2,h2,keys,o2.__getitem__,allowed_sections=keys,max_bytes=1000000,
        prior_values=before,prior_receipt=receipt,expected_prior_review_sha256=receipt["review_sha256"])
    assert after=={k:revised[k] for k in keys}
    assert transition["reused_sections"]==["identity","source_contract"]
    assert transition["resolved_sections"]==["dynamic_system_research"]
    assert stats["external_bytes"]<stats["fetched_bytes"]
    assert not transition["native_admitted"]
    cold=resolve_achilles_review_context(d2,h2,keys,o2.__getitem__,allowed_sections=keys,max_bytes=1000000)
    assert cold[:2]==(after,proof)
    restored,restored_proof,_,_=resolve_achilles_revision_context(
        d,h,keys,o.__getitem__,allowed_sections=keys,max_bytes=1000000,
        prior_values=after,prior_receipt=proof,expected_prior_review_sha256=proof["review_sha256"])
    assert restored==before and restored_proof==receipt
    def never_fetch(k):
        raise AssertionError("unnecessary external read")
    again,again_proof,_,again_stats=resolve_achilles_revision_context(
        d,h,keys,never_fetch,allowed_sections=keys,max_bytes=1000000,
        prior_values=before,prior_receipt=receipt,expected_prior_review_sha256=receipt["review_sha256"])
    assert again==before and again_proof==receipt and again_stats["external_bytes"]==0
    args=dict(prior_values=before,prior_receipt=receipt,expected_prior_review_sha256=receipt["review_sha256"])
    with pytest.raises(PermissionError):
        resolve_achilles_revision_context(d2,h2,keys,never_fetch,allowed_sections=("identity",),max_bytes=1000000,**args)
    with pytest.raises(CGXCrossAnalysisError):
        resolve_achilles_revision_context(d2,h2,keys,o2.__getitem__,allowed_sections=keys,max_bytes=1,**args)
    with pytest.raises(CGXCrossAnalysisError):
        resolve_achilles_revision_context(d2,h2,keys,never_fetch,allowed_sections=keys,max_bytes=1000000,**dict(args,prior_values=dict(before,identity={})))
    with pytest.raises(CGXCrossAnalysisError):
        resolve_achilles_revision_context(d2,h2,keys,never_fetch,allowed_sections=keys,max_bytes=1000000,**dict(args,expected_prior_review_sha256="0"*64))



def test_revision_preprocessing_limits_before_warm_repack(monkeypatch):
    import json
    import lightspeed_runtime.cgx_cross_analysis as m
    raw=(Path(__file__).resolve().parents[3]/"cgx/domain_templates/achilles_owner_operator_profile.json").read_bytes()
    d,h,o=m.pack_achilles_profile_review(raw)
    k=("identity",)
    vals,receipt,_=m.resolve_achilles_review_context(d,h,k,o.__getitem__,allowed_sections=k,max_bytes=1000000)
    calls=[]
    orig=m.pack_nested_review_payload
    def spy(*a,**kw):
        calls.append("pack")
        return orig(*a,**kw)
    monkeypatch.setattr(m,"pack_nested_review_payload",spy)
    def run(prior,budget):
        return m.resolve_achilles_revision_context(d,h,k,o.__getitem__,allowed_sections=k,max_bytes=budget,
            prior_values=prior,prior_receipt=receipt,expected_prior_review_sha256=receipt["review_sha256"])
    with pytest.raises(CGXCrossAnalysisError): run(vals,1)
    assert calls==[]
    with pytest.raises(CGXCrossAnalysisError,match="byte budget"): run({"identity":"x"*1000000},1000000)
    cyc=[];cyc.append(cyc)
    with pytest.raises(CGXCrossAnalysisError,match="shape budget"): run({"identity":cyc},1000000)
    assert calls==[]
    assert run(vals,1000000)[0]==vals and calls==["pack"]


def test_occurrence_permissions_are_not_payload_identity():
    import hashlib,json
    from lightspeed_runtime.cgx_cross_analysis import pack_nested_review_payload,resolve_review_occurrence
    root,objects=pack_nested_review_payload(b"shared bytes")
    def occurrence(oid):
        x=dict(occurrence_id=oid,source_revision="r1",scope_revision="acl1",root=root,allowed_prefixes=[""])
        return x,hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
    a,ha=occurrence("A"); b,hb=occurrence("B")
    calls=[]
    def fetch(oid,k):
        calls.append(oid)
        return objects[k]
    def auth(oid,rev,scope,prefix): return oid=="A" and scope=="acl1"
    assert resolve_review_occurrence(a,ha,fetch,auth,max_bytes=1000)[0]==b"shared bytes"
    before=list(calls)
    with pytest.raises(PermissionError): resolve_review_occurrence(b,hb,fetch,auth,max_bytes=1000)
    with pytest.raises(CGXCrossAnalysisError): resolve_review_occurrence(b,ha,fetch,auth,max_bytes=1000)
    assert calls==before
    def revoked(oid,rev,scope,prefix): return len(calls)==len(before)
    with pytest.raises(PermissionError): resolve_review_occurrence(a,ha,fetch,revoked,max_bytes=1000)
    assert len(calls)==len(before)+1



def test_provider_occurrence_binding_and_pretransfer_budget():
    import hashlib,json
    from lightspeed_runtime.cgx_cross_analysis import pack_nested_review_payload,resolve_provider_review_occurrence
    root,objects=pack_nested_review_payload(b"provider fixture")
    o=dict(occurrence_id="A",source_revision="r1",scope_revision="acl1",root=root,allowed_prefixes=[""])
    stamp=hashlib.sha256(json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
    calls=[]
    def gate(*a):return a==("review-001b","A","r1","acl1","")
    def provider(q):
        calls.append(q)
        return {**q,"payload":objects[q["object_sha256"]]}
    def run(read=provider,auth=gate,budget=10000):
        return resolve_provider_review_occurrence(o,stamp,read,auth,task_id="review-001b",max_bytes=budget)
    raw,stats=run()
    assert raw==b"provider fixture" and stats["provider_bytes"]==sum(len(objects[k["object_sha256"]]) for k in calls)
    assert not stats["provider_authentication_performed"]
    for key,value in [("occurrence_id","B"),("source_revision","r2"),("scope_revision","acl2"),("task_id","other")]:
        with pytest.raises(CGXCrossAnalysisError,match="binding mismatch"):
            run(lambda q:{**provider(q),key:value})
    before=len(calls)
    with pytest.raises(PermissionError):run(auth=lambda *a:False)
    assert len(calls)==before
    checks=iter([True,True,False])
    with pytest.raises(PermissionError):run(auth=lambda *a:next(checks))
    with pytest.raises(CGXCrossAnalysisError,match="byte budget"):
        run(budget=1)
    assert calls[-1]["max_bytes"]==1



def test_review_collection_shared_storage_separate_occurrences():
    import io,zipfile
    from lightspeed_runtime.cgx_cross_analysis import write_review_collection,hydrate_review_collection
    mem=io.BytesIO()
    payloads={"A":b"shared"*1024,"B":b"shared"*1024,"C":b"other"}
    with zipfile.ZipFile(mem,"w") as z:
        d,h=write_review_collection(z,payloads,task_id="review-001a",source_revision="r1")
        assert d["entries"]["A"]==d["entries"]["B"]
        assert len(set(z.namelist()))==len(z.namelist())
    with zipfile.ZipFile(io.BytesIO(mem.getvalue())) as z:
        def read(selected,auth=lambda *a:True,budget=100000,stamp=h):
            return hydrate_review_collection(z,d,stamp,task_id="review-001a",source_revision="r1",
                scope_revision="acl1",selected=selected,max_bytes=budget,authorise=auth)
        raw,stats=read(["A","C"]);assert raw=={"A":payloads["A"],"C":payloads["C"]}
        assert not stats["native_admitted"]
        with pytest.raises(PermissionError):read(["B"],auth=lambda t,k,*a:k=="A")
        with pytest.raises(CGXCrossAnalysisError):read(["A"],budget=1)
        with pytest.raises(CGXCrossAnalysisError):read(["A"],stamp="0"*64)
        seq=iter([True,True,False])
        with pytest.raises(PermissionError):read(["A"],auth=lambda *a:next(seq))
