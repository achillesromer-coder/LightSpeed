#!/usr/bin/env python3
"""Deterministic, offline, digital-only CGX PrintSpace bundle build/check."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
from cgx.manufacturing.virtual_factory import load_catalogue
from cgx.manufacturing.printspace_cgx import (build_bundle, h0_handshake, pack_lite, unpack_lite,
                                              verify_back_down)

OUT=BASE/'cgx'/'manufacturing'
FILES={'printspace_cgx_bundle_v0_1.json':None,
       'printspace_cgx_h0_v0_1.json':None,
       'printspace_cgx_lite_v0_1.json':None}

def build(check: bool=False) -> dict:
    original=load_catalogue()
    bundle=build_bundle(original)
    h0=h0_handshake(bundle,expected_catalogue_sha256=bundle['source_catalogue_sha256'])
    lite=pack_lite(bundle)
    if unpack_lite(lite,expected_catalogue_sha256=bundle['source_catalogue_sha256']) != bundle:
        raise RuntimeError('PACK_LITE_ROUNDTRIP_MISMATCH')
    if verify_back_down(bundle,original)['state']!='PASS_DIGITAL_ONLY':
        raise RuntimeError('SOURCE_REPLAY_NOT_VERIFIED')
    files={'printspace_cgx_bundle_v0_1.json':bundle,
           'printspace_cgx_h0_v0_1.json':h0,
           'printspace_cgx_lite_v0_1.json':lite}
    for name,obj in files.items():
        content=json.dumps(obj,ensure_ascii=True,sort_keys=True,indent=2,allow_nan=False)+'\n'
        path=OUT/name
        if check:
            if not path.is_file() or path.read_text(encoding='utf-8')!=content:
                raise RuntimeError('CGX_BUNDLE_ARTIFACT_DRIFT:'+name)
        else:
            path.write_text(content,encoding='utf-8')
    return {'state':'PASS_DIGITAL_ONLY', 'bundle_sha256':bundle['bundle_sha256'],
            'catalogue_sha256':bundle['source_catalogue_sha256'],
            'objects':len(bundle['objects']),'aliases':len(bundle['aliases']),
            'transport_bytes':lite['compressed_bytes'],'raw_bytes':lite['raw_bytes'],
            'native_admitted':False,'machine_authorised':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true')
    opts=p.parse_args()
    print(json.dumps(build(check=opts.check),sort_keys=True,indent=2))
