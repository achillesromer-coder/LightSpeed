#!/usr/bin/env python3
"""Canonical semantic hash for Mark III component-manifest meaning."""
from __future__ import annotations
import hashlib,json
from typing import Any

MANIFEST_SCHEMA='mark-iii-canonical-component-manifest-v1'
ROUND_DIGITS=8

def normalize(value:Any)->Any:
    if isinstance(value,float):
        r=round(value,ROUND_DIGITS)
        return 0.0 if r==0 else r
    if isinstance(value,list):return [normalize(v) for v in value]
    if isinstance(value,dict):return {k:normalize(value[k]) for k in sorted(value)}
    return value

def canonical_manifest_sha256(manifest:dict[str,Any])->str:
    payload={'schema':MANIFEST_SCHEMA,'manifest':normalize(manifest)}
    raw=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()
