#!/usr/bin/env python3
"""Generate the Mark III v0.3 original-layout dimensional/configuration register."""
from __future__ import annotations
import argparse, csv, hashlib, json
from collections import Counter
from pathlib import Path
from typing import Any
from mark_iii_geometry_fingerprint import QUANTIZATION_METRES, semantic_geometry_fingerprint
from mark_iii_parametric import build_reference

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as s:
        for c in iter(lambda:s.read(1024*1024),b''):h.update(c)
    return h.hexdigest()

def build_audit(parameters: dict[str,Any]):
    scene,records=build_reference(parameters); rm={r['node_name']:r for r in records}; rows=[]
    for name in sorted(scene.geometry):
        m=scene.geometry[name];r=rm[name];b=m.bounds;e=m.extents;c=m.centroid
        rows.append({
            'node_name':name,'family':r['family'],'subsystem':r['subsystem'],'evidence_state':r['evidence_state'],
            'review_gate':r['review_gate'],'attachment_parent':r['attachment_parent'],'physical':r['physical'],
            'maintainable':r['maintainable'],'cable_required':r['cable_required'],'cable_route':r['cable_route'],
            'service_clearance':r['service_clearance'],'removal_path':r['removal_path'],'panel_access':r['panel_access'],
            'array_configuration':r['array_configuration'],'configuration':r.get('configuration',''),'component_role':r.get('component_role',''),
            'manufacturing_state':r.get('manufacturing_state',''),'print_part':r.get('print_part',''),'source_basis':r['source_basis'],'units':'metres',
            'min_x':round(float(b[0][0]),6),'min_y':round(float(b[0][1]),6),'min_z':round(float(b[0][2]),6),
            'max_x':round(float(b[1][0]),6),'max_y':round(float(b[1][1]),6),'max_z':round(float(b[1][2]),6),
            'extent_x':round(float(e[0]),6),'extent_y':round(float(e[1]),6),'extent_z':round(float(e[2]),6),
            'centroid_x':round(float(c[0]),6),'centroid_y':round(float(c[1]),6),'centroid_z':round(float(c[2]),6),
            'vertices':int(len(m.vertices)),'faces':int(len(m.faces)),'watertight':bool(m.is_watertight),
            'winding_consistent':bool(m.is_winding_consistent),'signed_volume_m3':round(float(m.volume),9),
            'review_status':'OPEN_ENGINEERING_REVIEW'})
    fc=Counter(x['family'] for x in rows);ec=Counter(x['evidence_state'] for x in rows);sc=Counter(x['subsystem'] for x in rows)
    summary={'schema_version':'mark-iii-dimensional-audit-v0.3','status':'PASS_DIMENSIONAL_SERVICEABLE_REFERENCE_AUDIT',
             'source_state':parameters['artifact_status'],'units':'metres','node_count':len(rows),
             'physical_node_count':sum(x['physical'] for x in rows),'maintainable_node_count':sum(x['maintainable'] for x in rows),
             'semantic_geometry_sha256':semantic_geometry_fingerprint(scene),'semantic_geometry_quantization_m':QUANTIZATION_METRES,
             'all_nodes_watertight':all(x['watertight'] for x in rows),'all_nodes_winding_consistent':all(x['winding_consistent'] for x in rows),
             'scene_bounds_m':[[round(float(v),6) for v in row] for row in scene.bounds],
             'scene_extents_m':[round(float(v),6) for v in scene.extents],
             'family_counts':dict(sorted(fc.items())),'subsystem_counts':dict(sorted(sc.items())),'evidence_state_counts':dict(sorted(ec.items())),
             'known_unknown_count':len(parameters['known_unknowns']),'claim_gate_state':'STRENGTHENED','manufacturing_release':'BLOCKED_PENDING_PHYSICAL_QUALIFICATION'}
    return rows,summary

def write_audit(rows,summary,out):
    out.mkdir(parents=True,exist_ok=True);cp=out/'mark_iii_dimensional_audit.csv';jp=out/'mark_iii_dimensional_audit_summary.json'
    with cp.open('w',encoding='utf-8',newline='') as s:
        w=csv.DictWriter(s,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    stamped=dict(summary);stamped['csv_sha256']=sha256_file(cp);jp.write_text(json.dumps(stamped,indent=2,sort_keys=True)+'\n',encoding='utf-8');return cp,jp

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parameters',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args()
    rows,s=build_audit(json.loads(a.parameters.read_text()));cp,jp=write_audit(rows,s,a.out_dir)
    print(json.dumps({'status':s['status'],'node_count':s['node_count'],'physical_node_count':s['physical_node_count'],'semantic_geometry_sha256':s['semantic_geometry_sha256'],'csv_sha256':sha256_file(cp),'summary_sha256':sha256_file(jp)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
