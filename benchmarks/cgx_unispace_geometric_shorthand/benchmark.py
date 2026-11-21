#!/usr/bin/env python3
"""Measured benchmark. Local CPU wall time is only a proxy; no joule claims."""
from __future__ import annotations
import io, hashlib, json, random, time, zipfile, zlib
from pathlib import Path
from cgx_geo import encode_bytes, decode_bytes, chunk_map, h, encode_delta_bytes,decode_delta_bytes

HERE=Path(__file__).parent
OUT=HERE/'benchmark_results.json'
def datasets(prism=None,wad=None,html=None,starterzip=None):
    items=[
      ('structured-JSON','generated reproducible structured semantics',json.dumps({'parts':[{'id':f'P-{i:05d}','role':'beam','location':[i%19,i//19,0],'unit':'mm','material':'aluminium','cost':12.5} for i in range(400)]},separators=(',',':')).encode(),False),
      ('small-script','CGX local codec code', (HERE/'cgx_geo.py').read_bytes(), False),
      ('random-binary','seeded high-entropy source',random.Random(55).randbytes(256*1024),False),
    ]
    for name,label,source,large in [
      ('CGX-Prism-HTML','source synthetic CGX prism demonstration',prism,False),
      ('ZIP-already-compressed','existing CGX DOOM starter ZIP',starterzip,False),
      ('real-Freedoom-WAD','source-verified real Freedoom Phase 1 0.13.0',wad,True),
      ('playable-DOOM-HTML','verified full-game onefile HTML',html,True),
    ]:
      if source is not None:
        source=Path(source)
        if not source.is_file():raise FileNotFoundError(f'Specified fixture {source} missing')
        items.append((name,label,source.read_bytes(),large))
    return items

def run(*,prism=None,wad=None,html=None,starterzip=None):
 result={'date':'2026-10-12','codecs':['CGXS-raw/zlib/ref','ordinary ZIP-DEFLATE'],
         'preservation':'R0_EXACT','not_measured':['energy_joules','live_network_transfer','real_device_cpu','semantic_equivalence','remote_access','application_execution'],'cases':[], 'updates':[]}
 for name,notes,data,large in datasets(prism,wad,html,starterzip):
  start=time.perf_counter_ns()
  carrier,stat=encode_bytes(data,filename=name+'.bin',layers=15,chunk_size=65536,prefer_fast=True)
  elapsed=(time.perf_counter_ns()-start)/1e6
  t=time.perf_counter_ns();decoded,receipt=decode_bytes(carrier);dt=(time.perf_counter_ns()-t)/1e6
  assert decoded==data and receipt['status']=='R0_EXACT_BYTE_RECONSTRUCTION'
  stream=io.BytesIO()
  start=time.perf_counter_ns()
  with zipfile.ZipFile(stream, 'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   z.writestr(name+'.bin',data)
  zip_time=(time.perf_counter_ns()-start)/1e6
  zipped=stream.getvalue()
  with zipfile.ZipFile(io.BytesIO(zipped)) as z:
   assert z.read(name+'.bin')==data
  score_weights=[0,1000,10000]
  candidates={
   'raw':{'bytes':len(data),'encode_ms':0},
   'cgxs':{'bytes':len(carrier),'encode_ms':round(elapsed,4)},
   'zip':{'bytes':len(zipped),'encode_ms':round(zip_time,4)}
  }
  choose={str(w):min(candidates,key=lambda k:candidates[k]['bytes']+w*candidates[k]['encode_ms']) for w in score_weights}
  result['cases'].append({'dataset':name,'source':notes,'original_bytes':len(data),'source_sha256':h(data),
                          'cgxs_bytes':len(carrier),'standard_zip_bytes':len(zipped),
                          'cgxs_encode_ms':round(elapsed,3),'cgxs_decode_ms':round(dt,3),'zip_encode_ms':round(zip_time,3),
                          'cgxs_chunk_modes':{k:stat[k+'_chunks'] for k in ['ref','zlib','raw']},
                          'candidate_choose_by_byte_equiv_per_ms':choose,
                          'cold_start_minimum_in_three':min(candidates,key=lambda k:candidates[k]['bytes']),
                          'cost_warning':'Wall-clock from one shared local runner only; do not extrapolate to a PC/mobile or energy Joules'})
  print(f'{name:22s} raw={len(data):10,d} CGXS={len(carrier):10,d} ZIP={len(zipped):10,d} times={elapsed:7.1f}/{dt:7.1f}ms')
  if large:
   # Controlled one-byte change AFTER cache initialised, not pretending first-transfer is free.
   n=len(data);edited=bytearray(data);edited[n//2]^=1
   tmp=HERE/'_reference.tmp';tmp.write_bytes(data)
   cache=chunk_map([tmp],65536);tmp.unlink()
   capsule,st=encode_bytes(bytes(edited),filename=name+'.bin',layers=15,chunk_size=65536,cache=cache,prefer_fast=True)
   assert decode_bytes(capsule,cache=cache)[0]==bytes(edited)
   try:decode_bytes(capsule)
   except Exception as exc: missing_result=type(exc).__name__+': '+str(exc)
   else:raise AssertionError('Reference decoder without cache accepted invalid transfer')
   p0=time.perf_counter_ns()
   patch,patch_stats=encode_delta_bytes(data,bytes(edited),filename=name+'.bin',layers=15,chunk_size=65536)
   patch_elapsed=(time.perf_counter_ns()-p0)/1e6
   assert decode_delta_bytes(patch,data)[0]==bytes(edited)
   try:decode_delta_bytes(patch,None)
   except Exception as exc:patch_cold_result=type(exc).__name__+': '+str(exc)
   else:raise AssertionError('Patch without base should never decode')
   result['updates'].append({'dataset':name,'known_source_bytes':len(data),'delta_bytes':len(capsule),
       'single_baseline_key_patch_bytes':len(patch),'patch_selection':patch_stats['selection'],
       'patch_encode_ms':round(patch_elapsed,3),'patch_receiver_without_base':patch_cold_result,
       'delta_to_full_source_ratio':round(len(capsule)/len(data),6),
       'reused_chunks':st['ref_chunks'],'changed_chunks':st['raw_chunks']+st['zlib_chunks'],
       'cache_sha256':h(data),'edited_sha256':h(edited),'receiver_without_prior_source':missing_result,
       'reference_requires_existing_exact_local_bytes':True,'not_measured':'real network/cryptographic auth/streaming/late join or executable validation'})
   print('  1-byte version delta:',len(capsule),'B chunk-cache, ',len(patch),'B single-root patch; changed chunks',st['raw_chunks']+st['zlib_chunks'])
 OUT.write_text(json.dumps(result,indent=2)+'\n')
 return result

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser()
 for x in ('prism','wad','html','starterzip'):parser.add_argument('--'+x)
 a=parser.parse_args()
 run(prism=a.prism,wad=a.wad,html=a.html,starterzip=a.starterzip)
