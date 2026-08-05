#!/usr/bin/env python3
"""Audit Mark III attachments, cabling, access, arms, arrays and print references."""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np
from mark_iii_parametric import ROOTS, build_print_references, build_reference

STRUCTURAL_EXEMPT={'primary_structure','shell_panel','solar_hull_skin','fastener','coupler','coupler_latch','cable_tray','harness','arm','arm_joint','arm_actuator','process_tunnel','plating_feature','plating_allowance','resonator_mount','coil_reference','arm_solenoid_reference','arm_gas_joint','energy_tray','probe_mast','collector_pad'}
CRITICAL_REMOVAL={'sample_cartridge','solenoid','resonator','energy','controller','comms','damping'}

def sha(path):
    h=hashlib.sha256();h.update(path.read_bytes());return h.hexdigest()

def trace(name,rm):
    seen={name};chain=[name];parent=rm[name]['attachment_parent']
    while parent not in ROOTS:
        if parent not in rm or parent in seen:return False,chain+[parent]
        seen.add(parent);chain.append(parent);parent=rm[parent]['attachment_parent']
    return True,chain+[parent]

def ancestor_has(record,key,rm):
    if record.get(key):return record[key] in rm
    parent=record['attachment_parent'];seen=set()
    while parent not in ROOTS and parent in rm and parent not in seen:
        seen.add(parent);pr=rm[parent]
        if pr.get(key):return pr[key] in rm
        parent=pr['attachment_parent']
    return False

def build_audit(parameters:dict[str,Any]):
    scene,records=build_reference(parameters);rm={r['node_name']:r for r in records};physical=[r for r in records if r['physical']];maint=[r for r in physical if r['maintainable']];cable=[r for r in physical if r['cable_required']]
    missing_parent=[r['node_name'] for r in physical if not r['attachment_parent']]
    bad_parent=[r['node_name'] for r in physical if r['attachment_parent'] not in ROOTS and r['attachment_parent'] not in rm]
    unrooted=[]
    for r in physical:
        ok,chain=trace(r['node_name'],rm)
        if not ok:unrooted.append({'node':r['node_name'],'chain':chain})
    missing_route=[r['node_name'] for r in cable if not r['cable_route'] or r['cable_route'] not in rm]
    missing_clearance=[r['node_name'] for r in maint if r['family'] not in STRUCTURAL_EXEMPT and not ancestor_has(r,'service_clearance',rm)]
    missing_removal=[r['node_name'] for r in maint if r['family'] in CRITICAL_REMOVAL and not ancestor_has(r,'removal_path',rm)]
    bad_panel=[r['node_name'] for r in maint if r['panel_access'] and r['panel_access'] not in rm]
    # Coupler and panel counts.
    fc=Counter(r['family'] for r in records);sc=Counter(r['subsystem'] for r in records)
    arrays={}
    for count in parameters['derived_configuration']['array_configurations']:
        rows=[r for r in records if r['family']=='array_guide' and r['array_configuration']==str(count)]
        centres=[np.asarray(r['centroid_m'],float) for r in rows]
        nearest=[]
        for i,a in enumerate(centres):
            ds=[float(np.linalg.norm(a-b)) for j,b in enumerate(centres) if i!=j]
            if ds:nearest.append(min(ds))
        arrays[str(count)]={'node_count':len(rows),'minimum_centre_spacing_m':min(nearest) if nearest else 0.0,'illustrative_only':True}
    refs=build_print_references(parameters,scene,records);print_rows=[]
    bed=parameters['derived_configuration']['print_bed_mm'];bed_sorted=sorted(float(v) for v in bed)
    for name,m in sorted(refs.items()):
        dims=sorted(float(v) for v in m.extents)
        fits=all(a<=b+1e-6 for a,b in zip(dims,bed_sorted))
        print_rows.append({'file':name,'watertight':bool(m.is_watertight),'winding_consistent':bool(m.is_winding_consistent),
                           'extent_x_mm':round(float(m.extents[0]),6),'extent_y_mm':round(float(m.extents[1]),6),'extent_z_mm':round(float(m.extents[2]),6),
                           'largest_extent_mm':round(float(max(m.extents)),6),'fits_reference_bed_by_orientation':fits})
    # Canonical shell envelope only, excluding arms/guides/antenna.
    module_names=[r['node_name'] for r in records if r['physical'] and r['subsystem'] not in {'arm_system','probe_system'} and not r['node_name'].startswith('M3_COMMS_ANTENNA_')]
    mins=np.min([scene.geometry[n].bounds[0] for n in module_names],axis=0);maxs=np.max([scene.geometry[n].bounds[1] for n in module_names],axis=0)
    envelope=(maxs-mins).tolist()
    expected_len=parameters['source_parameters']['module_length_m']['value'];expected_diam=2*parameters['source_parameters']['outer_radius_m']['value']
    checks={
      'all_geometry_watertight':all(m.is_watertight for m in scene.geometry.values()),
      'all_geometry_winding_consistent':all(m.is_winding_consistent for m in scene.geometry.values()),
      'all_physical_nodes_have_parent':not missing_parent,
      'all_physical_nodes_resolve_to_root':not bad_parent and not unrooted,
      'all_cable_required_nodes_have_route':not missing_route,
      'all_nonstructural_maintainable_nodes_have_clearance':not missing_clearance,
      'all_critical_components_have_removal_path':not missing_removal,
      'all_declared_panel_access_resolves':not bad_panel,
      'source_shell_panel_count':fc['shell_panel']==18,
      'source_solar_skin_sector_count':fc['solar_hull_skin']==6,
      'source_coupling_node_count':fc['coupler_latch']==8,
      'source_reconciled_solenoid_count':fc['solenoid']==18,
      'source_reconciled_resonator_count':fc['resonator']==25,
      'source_sensor_count':sum(1 for r in records if r['node_name'].startswith('M3_SENSOR_NODE_'))==8,
      'source_damping_count':fc['damping']==4,
      'original_appendage_decomposition_present':sum(1 for r in records if r['node_name'].startswith('M3_ARM_') and r['node_name'].endswith('_BASE_INTERFACE'))==2 and any(r['node_name']=='M3_CENTRAL_PROBE_BASE_INTERFACE' for r in records) and fc['arm_joint']>=22,
      'array_configuration_counts_exact':all(arrays[str(c)]['node_count']==c for c in parameters['derived_configuration']['array_configurations']),
      'array_spacing_not_less_than_reference':all(v['minimum_centre_spacing_m']+1e-9>=parameters['derived_configuration']['array_spacing_m'] for k,v in arrays.items() if int(k)>1),
      'canonical_module_length_preserved':abs(envelope[0]-expected_len)<=1e-6,
      'canonical_module_diameter_preserved':envelope[1]<=expected_diam+1e-6 and envelope[2]<=expected_diam+1e-6,
      'all_print_references_watertight':all(r['watertight'] for r in print_rows),
      'all_print_references_winding_consistent':all(r['winding_consistent'] for r in print_rows),
      'all_print_references_fit_reference_bed':all(r['fits_reference_bed_by_orientation'] for r in print_rows),
      'claim_gates_present':len(parameters['claim_gates'])>=6,
      'known_unknowns_explicit':len(parameters['known_unknowns'])>=15,
      'source_conflicts_explicit':len(parameters['source_conflicts'])>=4,
    }
    failures=[k for k,v in checks.items() if not v]
    result={'schema_version':'mark-iii-serviceability-audit-v0.3','status':'PASS_SERVICEABILITY_REFERENCE_AUDIT' if not failures else 'FAIL_SERVICEABILITY_REFERENCE_AUDIT',
            'checks':checks,'failures':failures,'counts':{'geometry_nodes':len(records),'physical_nodes':len(physical),'maintainable_nodes':len(maint),'cable_required_nodes':len(cable),
              'shell_panels':fc['shell_panel'],'solar_hull_skins':fc['solar_hull_skin'],'coupler_latches':fc['coupler_latch'],'solenoid_nodes':fc['solenoid'],
              'resonators':fc['resonator'],'resonator_mounts':fc['resonator_mount'],'sensors_total':fc['sensor'],'body_sensor_nodes':sum(1 for r in records if r['node_name'].startswith('M3_SENSOR_NODE_')),'damping_placeholders':fc['damping'],'service_clearances':fc['service_clearance'],
              'connector_access_envelopes':fc['connector_access'],'cable_bend_spaces':fc['cable_bend_space'],'removal_paths':fc['removal_path'],'arm_nodes':sc['arm_system'],'probe_nodes':sc['probe_system'],'print_reference_count':len(print_rows)},
            'canonical_module_envelope_m':{'extents':envelope,'source_length':expected_len,'source_diameter':expected_diam},
            'arrays':arrays,'print_references':print_rows,'missing':{'parent':missing_parent,'bad_parent':bad_parent,'unrooted':unrooted,'cable_route':missing_route,'clearance':missing_clearance,'removal':missing_removal,'panel_access':bad_panel},
            'known_unknowns':parameters['known_unknowns'],'claim_gate_state':'STRENGTHENED','manufacturing_release':'BLOCKED_PENDING_PROCESS_AND_ENVIRONMENTAL_QUALIFICATION'}
    return result

def write(result,out):
    out.mkdir(parents=True,exist_ok=True);jp=out/'mark_iii_serviceability_audit.json';cp=out/'mark_iii_print_and_array_audit.csv'
    jp.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    rows=[]
    for r in result['print_references']:rows.append({'record_type':'print_reference','id':r['file'],'count_or_value':r['largest_extent_mm'],'status':'PASS' if r['fits_reference_bed_by_orientation'] and r['watertight'] else 'FAIL','notes':'largest extent mm'})
    for k,v in result['arrays'].items():rows.append({'record_type':'array_configuration','id':k,'count_or_value':v['minimum_centre_spacing_m'],'status':'ILLUSTRATIVE','notes':f"{v['node_count']} module guides; minimum centre spacing m"})
    with cp.open('w',newline='',encoding='utf-8') as s:w=csv.DictWriter(s,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return jp,cp

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parameters',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args()
    r=build_audit(json.loads(a.parameters.read_text()));jp,cp=write(r,a.out_dir);print(json.dumps({'status':r['status'],'counts':r['counts'],'canonical_module_envelope_m':r['canonical_module_envelope_m'],'json_sha256':sha(jp),'csv_sha256':sha(cp)},indent=2));return 0 if r['status'].startswith('PASS') else 1
if __name__=='__main__':raise SystemExit(main())
