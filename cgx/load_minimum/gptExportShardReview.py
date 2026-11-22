#!/usr/bin/env python3
"""LOAD.cgx original GPT export shard R0 read-only companion.

Never uploads bodies, assigns Object_IDs, mutates DBR, changes provider ACLs,
publishes a site, or deletes originals. Original R0 bytes remain necessary for
lossless reconstruction. Original rights and host identity are separate gates.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from cgx.load_minimum.gptExportManifestIntake import project_manifest_bytes, SHARD_RE, IntakeHold

SCHEMA="LOAD-GPT-ORIGINAL-SHARD-SOURCE-REVIEW/0.1"
MAX_SHARD_BYTES=128*1024*1024
MAX_RECORDS=1000
MAX_MAPPING_NODES=100000

def require(ok: bool, why: str) -> None:
    if not ok: raise IntakeHold(why)

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def inspect_raw_shard(raw: bytes, declaration: dict) -> tuple[dict,set[str],set[str]]:
    require(isinstance(declaration,dict),"BAD_SHARD_DECLARATION")
    name=declaration.get("path")
    limit=declaration.get("declared_size_bytes")
    require(isinstance(name,str) and SHARD_RE.fullmatch(name) is not None,"INVALID_SHARD_NAME")
    require(type(limit) is int and 0<limit<=MAX_SHARD_BYTES,"INVALID_DECLARED_SIZE")
    require(isinstance(raw,bytes) and len(raw)==limit,"SOURCE_BYTE_SIZE_MISMATCH")
    try:
        body=json.loads(raw,parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
    except (UnicodeError,ValueError) as exc: raise IntakeHold("INVALID_SOURCE_JSON") from exc
    require(isinstance(body,list) and 0<len(body)<=MAX_RECORDS,"INVALID_CONVERSATION_ARRAY")
    ids=set();convs=set();nodes=0;empty=0;index=[]
    for i,record in enumerate(body):
        require(isinstance(record,dict),"INVALID_RECORD")
        rid=record.get("id");cid=record.get("conversation_id")
        require(isinstance(rid,str) and rid and isinstance(cid,str) and cid,"MISSING_SOURCE_ID")
        require(rid not in ids and cid not in convs,"DUPLICATE_SOURCE_ID")
        ids.add(rid);convs.add(cid)
        mapping=record.get("mapping")
        require(isinstance(mapping,dict),"MISSING_SOURCE_MAPPING")
        nodes+=len(mapping)
        require(nodes<=MAX_MAPPING_NODES,"SHARD_NODE_BOUND_EXCEEDED")
        empty+=sum(1 for v in mapping.values() if isinstance(v,dict) and v.get("message") is None)
        try:
            canonical=json.dumps(record,sort_keys=True,ensure_ascii=False,
                separators=(",",":"),allow_nan=False).encode("utf-8")
        except (TypeError,ValueError,RecursionError) as exc:
            raise IntakeHold("INVALID_CANONICAL_RECORD") from exc
        index.append({"ordinal":i,"canonical_sha256":sha(canonical),
                      "mapping_nodes":len(mapping),"minted":False})
    return ({"name":name,"original_sha256":sha(raw),"original_bytes":len(raw),
             "records":len(body),"mapping_nodes":nodes,"null_message_nodes":empty,
             "record_index":index,"source_body_in_receipt":False,"native_dbr":False},
            ids,convs)

def inspect_originals(manifest_raw: bytes, directory: Path) -> dict:
    manifest=project_manifest_bytes(manifest_raw)
    directory=Path(directory).resolve(strict=True)
    require(directory.is_dir(),"PRIVATE_DIRECTORY_MISSING")
    rows=[];seen_ids=set();seen_convs=set();count=0;bytes_total=0;nodes_total=0
    for decl in manifest["conversation_shards"]:
        name=decl["path"];p=directory/name
        require(p.parent==directory and p.is_file() and not p.is_symlink(),
                "MISSING_OR_UNSAFE_SHARD")
        require(p.stat().st_size==decl["declared_size_bytes"],"SOURCE_SIZE_MISMATCH")
        record,ids,convs=inspect_raw_shard(p.read_bytes(),decl)
        require(not(seen_ids & ids) and not(seen_convs & convs),"CROSS_SHARD_ID_COLLISION")
        seen_ids.update(ids);seen_convs.update(convs)
        rows.append(record)
        count+=record["records"];bytes_total+=record["original_bytes"]
        nodes_total+=record["mapping_nodes"]
    require(count==len(seen_ids)==len(seen_convs),"SOURCE_ID_CARDINALITY_HOLD")
    return {"schema":SCHEMA,"status":"SOURCE_R0_VERIFIED_PRIVATE_NOT_NATIVE_ADMITTED",
      "root":"cgx:root:cognigrex","manifest_sha256":sha(manifest_raw),
      "shard_count":len(rows),"original_bytes":bytes_total,"records":count,
      "mapping_nodes":nodes_total,"shards":rows,
      "private_owner_scope":True,"public_published":False,"model_trained":False,
      "canonical_write":False,"mint":False,"dbr_verified":False,
      "node_restore_verified":False,"originals_preserved":True,
      "owner_rights_accepted":False,
      "hydration":"SOURCE_R0_REQUIRED_FOR_LOSSLESS_RECOVERY"}
