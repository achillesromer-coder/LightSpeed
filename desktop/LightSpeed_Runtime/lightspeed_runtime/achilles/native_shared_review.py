"""Cross-domain CGX-IM method reuse over the existing review collection carrier.

Synthetic review objects only. Domain labels and digests do not grant permissions.
No new storage service, native DBR, activation, external dispatch or publication.
"""
import json
import re
from collections import Counter
from lightspeed_runtime.achilles.native_geometry import digest, require
from lightspeed_runtime.achilles.native_model_review import build_model, verify_model, MAX_STAGES
from lightspeed_runtime.cgx_cross_analysis import write_review_collection, hydrate_review_collection

SCHEMA = "CGX-IM-SHARED-MODEL-REVIEW/0.1"
MAX_MODELS = 12


def _encode(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode("ascii")


def _decode(raw):
    def unique(pairs):
        out={}
        for k,v in pairs:
            require(k not in out,"duplicate JSON key")
            out[k]=v
        return out
    result=json.loads(raw,object_pairs_hook=unique)
    require(_encode(result)==raw,"noncanonical payload")
    return result


def _token(x):
    require(type(x) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}",x) is not None,"domain or identity")
    return x


def _hash(x):
    require(type(x) is str and re.fullmatch(r"[a-f0-9]{64}",x) is not None,"digest")
    return x


def occurrence(domain,identity,revision):
    return digest({"domain":_token(domain),"identity":_token(identity),"revision":_hash(revision)})


def _method_key(occ,h):
    # Both 64-character hashes would exceed the carrier's ID bound.
    return "method:"+digest({"occurrence":occ,"method":_hash(h)})


def pack_models(archive, records, *, task_id, source_revision):
    """Retain one logical occurrence per domain/model revision; canonical method bytes
    are physically reused by the existing ternary collection carrier.
    """
    require(type(records) is list and 1<=len(records)<=MAX_MODELS,"model count")
    payloads={};index={};counts=Counter()
    for entry in records:
        require(type(entry) is dict and set(entry)=={"domain","candidate"},"entry")
        domain=_token(entry["domain"]); envelope=verify_model(entry["candidate"])
        body=envelope["model"];revision=envelope["sha256"];identity=body["identity"]
        occ=occurrence(domain,identity,revision)
        require(occ not in index,"duplicate occurrence")
        header={"domain":domain,"identity":identity,"candidate_sha256":revision,
                "pipeline":body["pipeline"],"scope":"fixture"}
        header_key="model:"+occ
        payloads[header_key]=_encode(header)
        keys={}
        for h,method in body["methods"].items():
            key=_method_key(occ,h)
            payloads[key]=_encode(method);keys[h]=key;counts[h]+=1
        index[occ]={"header":header_key,"methods":keys,"domain":domain,"identity":identity,"revision":revision}
    descriptor,stamp=write_review_collection(archive,payloads,task_id=task_id,source_revision=source_revision)
    body={"schema":SCHEMA,"collection":descriptor,"collection_sha256":stamp,"index":index,
          "method_occurrences":sum(counts.values()),"unique_methods":len(counts),
          "native_admitted":False,"execution_authorized":False}
    return {"review":body,"sha256":digest(body)}


def hydrate_candidate(archive,envelope,expected_sha256,*,domain,identity,revision,
                      task_id,source_revision,scope_revision,max_bytes,authorise):
    """Restore selected historical candidate, not its current activation state.
    The caller must authenticate the expected root, domain and live occurrence grants.
    """
    require(type(envelope) is dict and set(envelope)=={"review","sha256"} and type(envelope["review"]) is dict,"review envelope")
    b=envelope["review"];_hash(expected_sha256)
    require(set(b)=={"schema","collection","collection_sha256","index","method_occurrences",
                    "unique_methods","native_admitted","execution_authorized"} and b["schema"]==SCHEMA
            and b["native_admitted"] is False and b["execution_authorized"] is False,"review schema")
    require(type(b["index"]) is dict and 1<=len(b["index"])<=MAX_MODELS,"index bounds")
    require(envelope["sha256"]==expected_sha256==digest(b),"review revision")
    occ=occurrence(domain,identity,revision)
    require(occ in b["index"],"unknown model occurrence")
    row=b["index"][occ]
    require(type(row) is dict and set(row)=={"header","methods","domain","identity","revision"},"index row")
    require((row["domain"],row["identity"],row["revision"])==(domain,identity,revision) and row["header"]=="model:"+occ,"occurrence binding")
    keys=row["methods"]
    require(type(keys) is dict and 1<=len(keys)<=MAX_STAGES and all(k==_method_key(occ,h) for h,k in keys.items()),"method bindings")
    selected=[row["header"]]+[keys[h] for h in sorted(keys)]
    raw,stats=hydrate_review_collection(archive,b["collection"],b["collection_sha256"],
        task_id=task_id,source_revision=source_revision,scope_revision=scope_revision,
        selected=selected,max_bytes=max_bytes,authorise=authorise)
    header=_decode(raw[row["header"]])
    require(type(header) is dict and set(header)=={"domain","identity","candidate_sha256","pipeline","scope"} and
            (header["domain"],header["identity"],header["candidate_sha256"],header["scope"])==(domain,identity,revision,"fixture"),"header binding")
    pipeline=header["pipeline"]
    require(type(pipeline) is list and 1<=len(pipeline)<=MAX_STAGES and all(type(h) is str and h in keys for h in pipeline) and set(pipeline)==set(keys),"pipeline")
    methods={h:_decode(raw[k]) for h,k in keys.items()}
    require(all(type(m) is dict and m.get("sha256")==h for h,m in methods.items()),"method digest")
    candidate=build_model(identity,[methods[h] for h in pipeline])
    require(candidate["sha256"]==revision,"candidate reconstruction")
    return candidate,{"schema":"CGX-IM-MODEL-RESTORE-REVIEW/0.1","review_sha256":expected_sha256,
                      "occurrence":occ,"candidate_sha256":revision,"selected_occurrences":selected,
                      "collection_stats":stats,"active_status_verified":False,
                      "native_admitted":False,"execution_authorized":False}
