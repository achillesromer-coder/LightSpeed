#!/usr/bin/env python3
"""Deterministic PrintSpace H0-to-UniSpace R0 review fixture builder.

No provider requests, ID registration, signing, mint, host side effects or source
hydration. The fixture intentionally has ZERO accepted candidate Object_IDs.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cgx.manufacturing.virtual_factory import load_catalogue
from cgx.manufacturing.printspace_cgx import build_bundle
from cgx.manufacturing.printspace_host_preflight import prepare_r0_host_review, verify_r0_host_review_back_down

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'cgx/manufacturing/printspace_host_r0_review_v0_1.json'

def build(*, check:bool=False)->dict:
    catalogue=load_catalogue()
    bundle=build_bundle(catalogue)
    plan=prepare_r0_host_review(bundle,catalogue)
    assert plan['state']=='R0_CANDIDATE_REVIEW_NOT_ADMITTED'
    assert plan['candidate_count']==0 and plan['product_count']==3
    assert verify_r0_host_review_back_down(plan,bundle,catalogue)['state']=='PASS_DIGITAL_ONLY'
    content=json.dumps(plan,sort_keys=True,indent=2,ensure_ascii=True)+'\n'
    if check:
        if not OUT.is_file() or OUT.read_text(encoding='utf-8')!=content:
            raise RuntimeError('PRINTSPACE_R0_CANONICAL_FIXTURE_DRIFT')
    else:
        OUT.write_text(content,encoding='utf-8')
    return {'state':'PASS_DIGITAL_ONLY','review_sha256':plan['plan_sha256'],
            'product_count':3,'native_admitted':False,'file_written':not check}

if __name__=='__main__':
    cli=argparse.ArgumentParser()
    cli.add_argument('--check',action='store_true')
    args=cli.parse_args()
    print(json.dumps(build(check=args.check),sort_keys=True))