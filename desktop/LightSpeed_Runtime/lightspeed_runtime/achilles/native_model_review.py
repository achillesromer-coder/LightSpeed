"""CGX-IM compositional model candidates: immutable review lineage, no new runtime."""
from copy import deepcopy
from lightspeed_runtime.achilles.native_geometry import Geometry, digest, require, validate
from lightspeed_runtime.achilles.native_methods import discover, apply, _apply_verified
from lightspeed_runtime.domain_registry import FLOOR_RUNTIME_MAPPING
from lightspeed_runtime.cgx_capability_registry import REPO_ROOT
import json
import re

MODEL_SCHEMA="CGX-IM-MODEL-CANDIDATE/0.1"
MAX_STAGES=32
MAX_HISTORY=256


def _id(x):
    require(type(x) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}",x) is not None,"model identity")
    return x


def _hash(x):
    require(type(x) is str and re.fullmatch(r"[a-f0-9]{64}",x) is not None,"revision digest")
    return x


def _method(e):
    require(type(e) is dict and set(e)=={"method","sha256"} and type(e["method"]) is dict,"method envelope")
    m=e["method"]
    require("training" in m and "holdout" in m,"method examples")
    rebuilt=discover(m["training"],m["holdout"])
    require(rebuilt==e,"method revision")
    return rebuilt


def build_model(identity, stages):
    """One ordered function pipeline; same exact method bytes stored once.
    Identity is a proposed label, not a minted identity or an authority grant.
    """
    _id(identity)
    require(type(stages) is list and 1<=len(stages)<=MAX_STAGES,"stage bound")
    methods={}; order=[]
    for e in stages:
        canonical=_method(e); h=canonical["sha256"]
        methods.setdefault(h,canonical);order.append(h)
    body={"schema":MODEL_SCHEMA,"identity":identity,"scope":"fixture","pipeline":order,
          "methods":methods,"native_admitted":False,"execution_authorized":False}
    return {"model":body,"sha256":digest(body)}


def verify_model(envelope):
    require(type(envelope) is dict and set(envelope)=={"model","sha256"} and type(envelope["model"]) is dict,"model envelope")
    b=envelope["model"]
    require(set(b)=={"schema","identity","scope","pipeline","methods","native_admitted","execution_authorized"},"model schema")
    require(type(b["pipeline"]) is list and 1<=len(b["pipeline"])<=MAX_STAGES and type(b["methods"]) is dict and 1<=len(b["methods"])<=MAX_STAGES,"model bounds")
    require(all(type(h) is str and h in b["methods"] for h in b["pipeline"]),"unresolved method")
    rebuilt=build_model(b["identity"],[b["methods"][h] for h in b["pipeline"]])
    require(rebuilt==envelope,"model revision")
    return rebuilt


def transition(identity, sequence, previous, candidate, action):
    """Construct a candidate event; history replay checks lifecycle invariants."""
    _id(identity);require(type(sequence) is int and 0<=sequence<MAX_HISTORY,"sequence")
    if previous is not None:_hash(previous)
    _hash(candidate);require(action in ("propose","supersede","revoke"),"action")
    body={"identity":identity,"seq":sequence,"prev":previous,"candidate":candidate,
          "action":action,"scope":"fixture"}
    return {"event":body,"sha256":digest(body)}


def resolve_history(events, expected_head, models):
    """Verify a single model history against a caller-pinned head; no native DBR/signature proof."""
    require(type(events) is list and 1<=len(events)<=MAX_HISTORY,"history bounds")
    _hash(expected_head)
    require(type(models) is dict and 1<=len(models)<=MAX_HISTORY,"store bounds")
    prev=None;identity=None;active=None;seen=set()
    for i,e in enumerate(events):
        require(type(e) is dict and set(e)=={"event","sha256"} and type(e["event"]) is dict,"event envelope")
        b=e["event"]
        require(set(b)=={"identity","seq","prev","candidate","action","scope"},"event schema")
        require(transition(b["identity"],i,prev,b["candidate"],b["action"])==e,"event integrity")
        if identity is None:identity=b["identity"]
        require(identity==b["identity"] and b["candidate"] in models,"identity or candidate missing")
        model=verify_model(models[b["candidate"]])
        require(model["sha256"]==b["candidate"] and model["model"]["identity"]==identity,"model binding")
        action=b["action"]; h=b["candidate"]
        if i==0:
            require(action=="propose","genesis action");active=h;seen.add(h)
        elif action=="supersede":
            require(active is not None and h not in seen,"invalid successor");active=h;seen.add(h)
        elif action=="revoke":
            require(active==h,"invalid revocation");active=None
        else:raise ValueError("duplicate genesis")
        prev=e["sha256"]
    require(prev==expected_head,"history head mismatch")
    return {"identity":identity,"active":active,"head":prev,"status":"review_candidate" if active else "revoked","native_admitted":False}


def run_active(events, expected_head, models, x, geometry, at, *, allowed, budget=243):
    """Resolve only current candidate; one aggregate fixture budget across pipeline stages."""
    require(type(budget) is int and 1<=budget<=243,"resource budget")
    state=resolve_history(events,expected_head,models)
    require(state["active"] is not None,"model revoked")
    b=models[state["active"]]["model"];remaining=budget;trace=[]
    value=deepcopy(validate(x));allowed=frozenset(allowed)
    for h in b["pipeline"]:
        require(remaining>0,"aggregate resource budget")
        out=apply(b["methods"][h],h,value,geometry,at,allowed=allowed,budget=remaining)
        cost=out["record"]["trace"]["record"]["cost"]
        require(type(cost) is int and 0<cost<=remaining,"invalid stage cost")
        remaining-=cost;value=out["record"]["result"];trace.append(out)
    result={"identity":state["identity"],"candidate":state["active"],"history_head":expected_head,
            "result":value,"trace":trace,"cost":budget-remaining,"scope":"fixture",
            "native_admitted":False,"execution_authorized":False}
    return {"record":result,"sha256":digest(result)}


def run_batch_review(events, expected_head, models, inputs, geometry, at, *, allowed,
                     current_head, per_input_budget=243, total_budget=8192):
    """Bounded fixture batch with one private verified model snapshot.

    The caller supplies an authenticated current-head reader in real integration;
    this review function cannot authenticate it. No cache survives the call.
    Abort the entire batch on a changed head, invalid input or exhausted budget.
    The output matches run_active at each input with its effective budget.
    """
    require(type(inputs) in (list,tuple) and 1<=len(inputs)<=512,"batch size")
    require(type(per_input_budget) is int and 1<=per_input_budget<=243,"input budget")
    require(type(total_budget) is int and 1<=total_budget<=65536,"batch budget")
    require(type(geometry) is Geometry and callable(current_head),"batch context")
    _hash(expected_head)
    def check():
        require(current_head()==expected_head,"head changed or revoked")
    check()
    # Copy only the referenced bounded candidates, never an unbounded foreign store.
    require(type(events) is list and 1<=len(events)<=MAX_HISTORY,"history bounds")
    require(type(models) is dict and 1<=len(models)<=MAX_HISTORY,"store bounds")
    require(all(type(e) is dict and type(e.get("event")) is dict for e in events),"history shape")
    history=deepcopy(events)
    refs={_hash(e["event"]["candidate"]) for e in history}
    require(refs<=models.keys(),"missing candidate")
    snapshot={h:verify_model(models[h]) for h in refs}
    state=resolve_history(history,expected_head,snapshot)
    require(state["active"] is not None,"model revoked")
    body=snapshot[state["active"]]["model"]
    # The geometry is a deterministic fixture. Rebuild privately so a caller
    # cannot mutate its adjacency or edge permissions during the batch.
    g=Geometry(geometry.depth)
    require(geometry.edges==g.edges and geometry.adj==g.adj and geometry.volumes==g.volumes,"geometry changed")
    edges=frozenset(allowed)
    require(edges<=g.edges and at in g.leaves,"boundary")
    values=[deepcopy(validate(x)) for x in inputs]
    output=[];remaining=total_budget
    for value in values:
        check()
        budget=min(per_input_budget,remaining)
        require(budget>0,"aggregate batch budget")
        left=budget;trace=[]
        for h in body["pipeline"]:
            require(left>0,"aggregate input budget")
            out=_apply_verified(body["methods"][h]["method"],h,value,g,at,allowed=edges,budget=left)
            cost=out["record"]["trace"]["record"]["cost"]
            require(type(cost) is int and 0<cost<=left,"invalid stage cost")
            left-=cost;value=out["record"]["result"];trace.append(out)
        record={"identity":state["identity"],"candidate":state["active"],"history_head":expected_head,
                "result":value,"trace":trace,"cost":budget-left,"scope":"fixture",
                "native_admitted":False,"execution_authorized":False}
        remaining-=record["cost"]
        output.append({"record":record,"sha256":digest(record)})
        check()
    check()
    receipt={"schema":"CGX-IM-BOUNDED-BATCH-REVIEW/0.1","history_head":expected_head,
             "candidate":state["active"],"count":len(output),"cost":total_budget-remaining,
             "result_digests":[v["sha256"] for v in output],"native_admitted":False,
             "execution_authorized":False,"caller_authentication_verified":False}
    return output,{"receipt":receipt,"sha256":digest(receipt)}


def release_review(events, expected_head, models):
    """Reuse existing Z-stack mapping and activation limits; review metadata only."""
    state=resolve_history(events,expected_head,models)
    require(state["active"] is not None,"model revoked")
    p=REPO_ROOT/"desktop/Desktop_Hooks/LightSpeed/config/floor_environment_realization_contract.json"
    cfg=json.loads(p.read_text(encoding="utf-8-sig"))
    floors={f["floor"]:f for f in cfg["floors"]}
    require(set(floors)==set(FLOOR_RUNTIME_MAPPING) and len(cfg["floors"])==len(floors),"floor reconciliation")
    require(set(cfg["runtime_boot_order"])==set(floors) and len(cfg["runtime_boot_order"])==len(floors),"boot order")
    rows=[]
    for name in cfg["runtime_boot_order"]:
        f=floors[name]; m=f["model"]
        require(type(m["max_parallel_tasks"]) is int and m["max_parallel_tasks"]>=1,"capacity")
        rows.append({"floor":name,"runtime_domain":FLOOR_RUNTIME_MAPPING[name],"activation":m["activation"],
                     "max_parallel_tasks":m["max_parallel_tasks"],"queue_limit":m["queue_limit"]})
    payload={"schema":"CGX-IM-RELEASE-REVIEW/0.1","identity":state["identity"],
             "candidate":state["active"],"history_head":expected_head,
             "floor_contract":cfg["contract_id"],"floor_contract_digest":digest(cfg),
             "floors":rows,"status":"HOLD_INDEPENDENT_ACCEPTANCE","execution_authorized":False,
             "publication_authorized":False,"native_admitted":False}
    return {"review":payload,"sha256":digest(payload)}
