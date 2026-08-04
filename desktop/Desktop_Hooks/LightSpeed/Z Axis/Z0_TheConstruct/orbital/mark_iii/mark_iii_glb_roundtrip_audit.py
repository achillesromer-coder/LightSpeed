#!/usr/bin/env python3
"""Verify exported Mark III GLB node identity, topology and bounded geometry."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any
import numpy as np
import trimesh
from mark_iii_parametric import build_reference

LINEAR=2e-5;REL=2e-5;ABS_VOL=1e-7;ABS_AREA=2e-6

def mx(a:Any,b:Any)->float:return float(np.max(np.abs(np.asarray(a,dtype=float)-np.asarray(b,dtype=float))))
def audit(parameters,glb):
    source,_=build_reference(parameters);exported=trimesh.load(glb,force='scene');sn=set(source.geometry);en=set(exported.geometry)
    missing=sorted(sn-en);unexpected=sorted(en-sn);fail=[];nodes={};maxe={'bounds_m':0.,'extents_m':0.,'centroid_m':0.,'relative_volume':0.,'relative_area':0.}
    if missing:fail.append(f'missing nodes: {missing}')
    if unexpected:fail.append(f'unexpected nodes: {unexpected}')
    for n in sorted(sn&en):
        a=source.geometry[n];b=exported.geometry[n];be=mx(a.bounds,b.bounds);ee=mx(a.extents,b.extents);ce=mx(a.centroid,b.centroid)
        av=abs(float(a.volume)-float(b.volume));aa=abs(float(a.area)-float(b.area));rv=av/max(abs(float(a.volume)),1e-12);ra=aa/max(abs(float(a.area)),1e-12)
        checks={'vertex_count_exact':len(a.vertices)==len(b.vertices),'face_count_exact':len(a.faces)==len(b.faces),
                'watertight_exact':bool(a.is_watertight)==bool(b.is_watertight),'winding_exact':bool(a.is_winding_consistent)==bool(b.is_winding_consistent),
                'bounds':be<=LINEAR,'extents':ee<=LINEAR,'centroid':ce<=LINEAR,'volume':rv<=REL or av<=ABS_VOL,'area':ra<=REL or aa<=ABS_AREA}
        if not all(checks.values()):fail.append(f"{n}: {[k for k,v in checks.items() if not v]}")
        nodes[n]={'vertices':len(b.vertices),'faces':len(b.faces),'watertight':bool(b.is_watertight),'winding_consistent':bool(b.is_winding_consistent),
                  'bounds_error_m':be,'extents_error_m':ee,'centroid_error_m':ce,'relative_volume_error':rv,'relative_area_error':ra,'checks':checks}
        maxe['bounds_m']=max(maxe['bounds_m'],be);maxe['extents_m']=max(maxe['extents_m'],ee);maxe['centroid_m']=max(maxe['centroid_m'],ce);maxe['relative_volume']=max(maxe['relative_volume'],rv);maxe['relative_area']=max(maxe['relative_area'],ra)
    return {'schema_version':'mark-iii-glb-roundtrip-v0.2','status':'PASS_GLB_ROUNDTRIP_REFERENCE' if not fail else 'FAIL_GLB_ROUNDTRIP_REFERENCE','glb_file':glb.name,
            'source_nodes':len(sn),'exported_nodes':len(en),'matched_nodes':len(sn&en),'missing_nodes':missing,'unexpected_nodes':unexpected,
            'linear_tolerance_m':LINEAR,'relative_measure_tolerance':REL,'maximum_observed_errors':maxe,'failures':fail,'nodes':nodes,'claim_gate_state':'UNCHANGED'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parameters',type=Path,required=True);ap.add_argument('--glb',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    r=audit(json.loads(a.parameters.read_text()),a.glb);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:r[k] for k in ('status','source_nodes','exported_nodes','matched_nodes','maximum_observed_errors')},indent=2));return 0 if r['status'].startswith('PASS') else 1
if __name__=='__main__':raise SystemExit(main())
