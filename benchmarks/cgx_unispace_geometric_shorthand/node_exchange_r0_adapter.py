"""Read-only candidate adapter for existing CGX FileSpace and Node Exchange.
No peer admission, transport activation, lease minting, ACL proof or DBR writes.
Any native/provider identity is an untrusted CLAIM until separately attested.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import time
import zipfile
from typing import Any
from cgx_geo import MAX_SOURCE, CodecError, h, encode_bytes, decode_bytes, encode_delta_bytes, decode_delta_bytes

SCHEMA="cgx.unispace.r0.source-node-candidate.v1"
MODES={"raw","zip-deflate","cgxs-full","cgxs-root-delta","no-change"}

class BridgeError(ValueError): pass

def source_context(meta:dict,content:bytes)->dict:
    if not isinstance(meta,dict):raise BridgeError("SOURCE_IDENTITY_REQUIRED")
    names=("object_id","native_provider","native_source_ref","native_revision","owner_ref","source_sha256")
    for name in names:
        if not isinstance(meta.get(name),str) or not 1<=len(meta[name].strip())<=512:
            raise BridgeError("SOURCE_IDENTITY_MISSING_"+name)
    if h(content)!=meta["source_sha256"]:raise BridgeError("SOURCE_READBACK_MISMATCH")
    return {name:meta[name] for name in names}

def zip_one(data:bytes)->bytes:
    sink=io.BytesIO()
    with zipfile.ZipFile(sink,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=False) as z:
        z.writestr("payload.bin",data)
    return sink.getvalue()

def unzip_one(data:bytes,max_output:int)->bytes:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            items=z.infolist()
            if len(items)!=1 or items[0].filename!="payload.bin" or items[0].compress_type!=zipfile.ZIP_DEFLATED:
                raise BridgeError("ZIP_LAYOUT_UNSUPPORTED")
            if items[0].file_size>max_output:raise BridgeError("ZIP_LIMIT")
            with z.open(items[0]) as stream:
                value=stream.read(max_output+1)
                if len(value)>max_output or stream.read(1):raise BridgeError("ZIP_LIMIT")
                return value
    except (zipfile.BadZipFile,EOFError,RuntimeError) as exc:
        raise BridgeError("ZIP_CORRUPT") from exc

def candidate(content:bytes,*,native:dict,baseline:bytes|None=None,
              receiver_claimed_root:str|None=None,layers:int=15,
              cpu_byte_equivalent_ms:float=0.0)->tuple[bytes,dict]:
    """Choose among *actual* payload lengths, including ZIP and raw bypass.
    The named prior root is not proof that the remote receiver owns it.
    """
    if not isinstance(content,bytes) or len(content)>MAX_SOURCE:raise BridgeError("SOURCE_BOUND")
    if type(cpu_byte_equivalent_ms) not in (float,int) or not 0<=cpu_byte_equivalent_ms<=1e6:
        raise BridgeError("COST_WEIGHT_BOUND")
    native=source_context(native,content)
    choices=[]
    def add(mode,payload,t0,prior_root=None):
        ms=0 if t0 is None else (time.perf_counter_ns()-t0)/1e6
        choices.append((mode,payload,ms,prior_root))
    add("raw",content,None)
    t=time.perf_counter_ns();z=zip_one(content);add("zip-deflate",z,t)
    t=time.perf_counter_ns();b,_=encode_bytes(content,filename="payload.bin",layers=layers,prefer_fast=True);add("cgxs-full",b,t)
    if baseline is not None:
        if not isinstance(baseline,bytes) or h(baseline)!=receiver_claimed_root:
            raise BridgeError("CONTEXT_MISMATCH")
        if baseline==content:add("no-change",b"",None,h(baseline))
        else:
            t=time.perf_counter_ns();d,_=encode_delta_bytes(baseline,content,filename="payload.bin",layers=layers)
            add("cgxs-root-delta",d,t,h(baseline))
    priority={"no-change":0,"raw":1,"zip-deflate":2,"cgxs-full":3,"cgxs-root-delta":4}
    mode,payload,ms,prior=min(choices,key=lambda x:(len(x[1])+x[2]*cpu_byte_equivalent_ms,priority[x[0]]))
    manifest={
        "schema":SCHEMA,"mode":mode,"native":native,"original_source_sha256":h(content),
        "original_size_bytes":len(content),"carrier_sha256":h(payload),"carrier_size_bytes":len(payload),
        "baseline_sha256":prior,"n_layers":layers,"initial_cache_cost_excluded":True,
        "wire_metadata_bytes_excluded":True,
        "alternatives":[{"mode":c[0],"payload_bytes":len(c[1]),"local_encode_ms":round(c[2],3)} for c in choices],
        "lease_validated":False,"peer_transport_verified":False,"acl_attested":False,
        "provider_revision_attested":False,"canonical_promotion_authorized":False,
        "public_publish_authorized":False,"physical_actuation_authorized":False,
        "status":"R0_REVIEW_ONLY",
    }
    return payload,manifest

def reconstruct(payload:bytes,plan:dict,*,prior:bytes|None=None,max_output:int=MAX_SOURCE)->tuple[bytes,dict]:
    if not isinstance(plan,dict) or plan.get("schema")!=SCHEMA:raise BridgeError("UNKNOWN_SCHEME")
    mode=plan.get("mode")
    if mode not in MODES:raise BridgeError("UNKNOWN_MODE")
    if not isinstance(payload,bytes) or len(payload)!=plan.get("carrier_size_bytes") or h(payload)!=plan.get("carrier_sha256"):
        raise BridgeError("CARRIER_HASH_MISMATCH")
    expected=plan.get("original_size_bytes")
    if type(expected)is not int or not 0<=expected<=max_output:raise BridgeError("OUTPUT_BOUND")
    if mode in {"cgxs-root-delta","no-change"}:
        if prior is None:raise BridgeError("NOT_CACHED")
        if h(prior)!=plan.get("baseline_sha256"):raise BridgeError("CONTEXT_MISMATCH")
    if mode=="raw":data=payload
    elif mode=="zip-deflate":data=unzip_one(payload,max_output)
    elif mode=="cgxs-full":data,_=decode_bytes(payload,max_output=max_output)
    elif mode=="cgxs-root-delta":data,_=decode_delta_bytes(payload,prior)
    else:
        if payload:raise BridgeError("NO_CHANGE_PAYLOAD_INVALID")
        data=prior
    if len(data)!=expected or h(data)!=plan.get("original_source_sha256"):
        raise BridgeError("FINAL_READBACK_MISMATCH")
    identity=source_context(plan.get("native"),data)
    return data,{"schema":"cgx.unispace.r0.local-receipt.v1","status":"R0_EXACT_LOCAL_READBACK",
        "source_sha256":h(data),"native_source_ref":identity["native_source_ref"],
        "object_id":identity["object_id"],"readback_exact":True,
        "source_attested":False,"peer_transport_verified":False,"lease_validated":False,
        "canonical_promotion_authorized":False}

def native_node_transfer_plan(*,staged_carrier:Path,plan:dict,
                              source_node_id:str,target_node_id:str,
                              source_root_id:str,target_root_id:str)->dict:
    """Bind to the actual current Node Exchange planner; cannot mint lease.
    Reads an already-staged local candidate, NOT the original source.
    """
    from lightspeed_runtime.node_exchange import build_transfer_envelope
    path=Path(staged_carrier)
    if plan.get("schema")!=SCHEMA:raise BridgeError("UNKNOWN_SCHEME")
    if not path.is_file() or path.stat().st_size!=plan.get("carrier_size_bytes") or h(path.read_bytes())!=plan.get("carrier_sha256"):
        raise BridgeError("STAGED_CARRIER_READBACK_MISMATCH")
    if plan.get("mode")=="no-change":
        return {"status":"NO_PAYLOAD_PLAN","envelope":None,"requires_receiver_prior":plan["baseline_sha256"],
                "peer_transport_verified":False,"canonical_promotion_authorized":False}
    env=build_transfer_envelope(path,source_node_id=source_node_id,
         target_node_id=target_node_id,source_root_id=source_root_id,
         target_root_id=target_root_id,object_id=plan["native"]["object_id"],
         max_bytes=MAX_SOURCE+MAX_SOURCE//8)
    return {"status":"NATIVE_NODE_EXCHANGE_ENVELOPE_PLANNED","envelope":env,
        "original_source_sha256":plan["original_source_sha256"],"carrier_sha256":plan["carrier_sha256"],
        "requires_receiver_prior":plan["baseline_sha256"],"lease_validated":False,
        "peer_transport_verified":False,"authority_transfer":False,
        "canonical_promotion_authorized":False}
