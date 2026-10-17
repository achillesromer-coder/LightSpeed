#!/usr/bin/env python3
"""CGX UniSpace geometric byte shorthand, isolated reversible proof codec.

Exact bytes (R0) only. The geometric address is a deterministic index: it
cannot materialise missing source bytes. No live CGX permission, signature,
node transport, file execution, semantic classification or DBR promotion.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import time
import zlib

MAGIC = b'CGXS'
VERSION = 1
SCHEMA = 'cgx.unispace.geometric-byte-carrier.candidate.v1'
HEADER = struct.Struct('>4sBI')
MAX_SOURCE = 128 * 1024 * 1024
MAX_MANIFEST = 8 * 1024 * 1024
MAX_CHUNKS = 4096
MAX_PAYLOAD = MAX_SOURCE + MAX_CHUNKS * 4096
MAX_LAYERS = 128

class CodecError(ValueError):
    pass

def h(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()

def jpack(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=True, separators=(',', ':'), sort_keys=True).encode('ascii')

def morton3(x: int, y: int, z: int) -> int:
    if min(x, y, z) < 0 or max(x,y,z) >= (1 << 16):
        raise CodecError('Morton coordinates outside 16 bit range')
    result = 0
    for shift in range(16):
        result |= ((x >> shift) & 1) << (3*shift)
        result |= ((y >> shift) & 1) << (3*shift+1)
        result |= ((z >> shift) & 1) << (3*shift+2)
    return result

def unmorton3(code: int) -> tuple[int,int,int]:
    if not 0 <= code < (1 << 48):
        raise CodecError('Invalid Morton address')
    return tuple(sum(((code >> (3*i+j)) & 1) << i for i in range(16)) for j in range(3))

def lattice(i: int, side: int) -> tuple[int,int,int]:
    return i % side, (i // side) % side, i // side**2

def side_for(count: int) -> int:
    side=1
    while side**3 < max(count, 1): side *= 2
    return side

def chunk_map(paths: list[Path], chunk_size: int, max_cache_bytes: int = MAX_SOURCE) -> dict[str,bytes]:
    """Local cache fixture only: verified digest => exact chunk bytes."""
    mapping: dict[str,bytes] = {}
    total = 0
    for path in paths:
        size=path.stat().st_size
        total+=size
        if total>max_cache_bytes: raise CodecError('Local cache capacity exceeded')
        with path.open('rb') as f:
            while block:=f.read(chunk_size):
                mapping.setdefault(h(block),block)
    return mapping

def choose(data: bytes, *, cache: dict[str,bytes], prefer_fast: bool, cpu_byte_penalty: float) -> tuple[str,bytes,dict]:
    digest=h(data)
    if cache.get(digest)==data:
        return 'ref', b'', {'candidate_zlib_bytes':None,'candidate_encode_ns':0, 'cpu_byte_equiv':0}
    start=time.perf_counter_ns()
    z=zlib.compress(data,1 if prefer_fast else 6)
    ns=time.perf_counter_ns()-start
    # Compare actual bytes saved with a configurable proxy penalty for time:
    # CPU nanoseconds weighted into byte-equivalents, NOT joule measurements.
    cost = len(z)+cpu_byte_penalty*ns
    if cost < len(data):
        return 'zlib',z,{'candidate_zlib_bytes':len(z),'candidate_encode_ns':ns,'cpu_byte_equiv':round(cpu_byte_penalty*ns,3)}
    return 'raw',data,{'candidate_zlib_bytes':len(z),'candidate_encode_ns':ns,'cpu_byte_equiv':round(cpu_byte_penalty*ns,3)}

def encode_bytes(data: bytes, *, filename: str='payload.bin', layers: int=15,
                 chunk_size: int=65536, cache: dict[str,bytes]|None=None,
                 prefer_fast: bool=False, cpu_byte_penalty: float=0.0) -> tuple[bytes,dict]:
    if len(data)>MAX_SOURCE: raise CodecError('Demo source cap: 128 MiB')
    if not 1<=layers<=MAX_LAYERS: raise CodecError('Layers must be 1..128')
    if not 1024<=chunk_size<=1024*1024: raise CodecError('Chunk size must be 1KiB..1MiB')
    if cpu_byte_penalty<0 or not math.isfinite(cpu_byte_penalty):raise CodecError('Invalid CPU weight')
    if filename != os.path.basename(filename) or filename in {'.','..',''} or '\\' in filename:
        raise CodecError('Filename must be a basename')
    if len(filename)>150: raise CodecError('Filename too long')
    blocks=[data[i:i+chunk_size] for i in range(0,len(data),chunk_size)]
    if len(blocks)>MAX_CHUNKS:raise CodecError('Too many chunks')
    side=side_for(len(blocks))
    rows=[];parts=[];metrics={'raw_chunks':0,'zlib_chunks':0,'ref_chunks':0,'encode_cpu_ns':0}
    for i,block in enumerate(blocks):
        kind,payload,trace=choose(block,cache=cache or {},prefer_fast=prefer_fast,cpu_byte_penalty=cpu_byte_penalty)
        x,y,z=lattice(i,side)
        rows.append([morton3(x,y,z),i%layers,len(block),h(block),kind,len(payload)])
        parts.append(payload)
        metrics[kind+'_chunks']+=1
        metrics['encode_cpu_ns']+=trace['candidate_encode_ns']
    geometry={'layout':'morton3-16','index_basis':'chunk ordinal mapped onto power-of-two cubic lattice',
              'side':side,'layers':layers, 'chunk_size':chunk_size,
              'address_is_content':False,'semantic_lens_authority':'NONE'}
    record={'schema':SCHEMA,'original_name':filename,'original_bytes':len(data),
            'source_sha256':h(data),'geometry_root':h(jpack(geometry)),
            'geometry':geometry,'chunks':rows,
            'chunk_columns':['morton','layer','n_original','sha256','codec','n_wire'],
            'payload_license':'EXTERNAL_SOURCE_OWNER_REQUIRED',
            'preservation':'R0_EXACT', 'epistemic':'BYTE_VERIFIED_ONLY',
            'authority_transfer':False,'signed':False,'dbr_promotion':False,
            'meanings_are_derived':'Interpretation must use separately registered CGX lenses'}
    manifest=zlib.compress(jpack(record),9)
    if len(manifest)>MAX_MANIFEST:raise CodecError('Manifest too large')
    binary=HEADER.pack(MAGIC,VERSION,len(manifest))+manifest+b''.join(parts)
    if len(binary)>MAX_PAYLOAD:raise CodecError('Payload too large')
    stats={'original_bytes':len(data),'wire_bytes':len(binary),'manifest_compressed_bytes':len(manifest),
           'payload_bytes':sum(len(p) for p in parts),'geometry_root':record['geometry_root'],
           'source_sha256':record['source_sha256'],'chunks':len(blocks),
           'n_layers':layers,'full_initial_ratio':round(len(binary)/max(1,len(data)),5),
           'status':'REVERSIBLE_CANDIDATE_NOT_AUTHENTICATED',**metrics}
    return binary,stats

def _decompress_exact(blob: bytes, size: int) -> bytes:
    d=zlib.decompressobj()
    out=d.decompress(blob,size+1)
    if len(out)!=size or not d.eof or d.unused_data or d.unconsumed_tail:
        raise CodecError('Invalid zlib payload length or trailing bytes')
    if d.flush():raise CodecError('Unexpected trailing output')
    return out

def decode_bytes(binary: bytes, *,cache: dict[str,bytes]|None=None,
                 max_output: int=MAX_SOURCE) -> tuple[bytes,dict]:
    if len(binary)<HEADER.size or len(binary)>MAX_PAYLOAD:
        raise CodecError('Carrier length invalid')
    magic,version,mlen=HEADER.unpack_from(binary)
    if magic!=MAGIC or version!=VERSION or mlen>MAX_MANIFEST or HEADER.size+mlen>len(binary):
        raise CodecError('Invalid header or schema version')
    try:
        packed=binary[HEADER.size:HEADER.size+mlen]
        record=json.loads(_decompress_manifest(packed).decode('ascii'))
    except (ValueError,UnicodeError,TypeError,zlib.error) as exc:
        raise CodecError('Manifest invalid') from exc
    if record.get('schema')!=SCHEMA or record.get('preservation')!='R0_EXACT':
        raise CodecError('Unsupported manifest')
    geometry=record.get('geometry',{})
    if h(jpack(geometry))!=record.get('geometry_root'):
        raise CodecError('Geometry root mismatch')
    side=geometry.get('side');layers=geometry.get('layers');chunk_size=geometry.get('chunk_size')
    if (type(side)is not int or side<1 or side>256 or (side&(side-1)) or
        type(layers)is not int or not 1<=layers<=MAX_LAYERS or
        type(chunk_size)is not int or not 1024<=chunk_size<=1024*1024):
        raise CodecError('Unacceptable geometry')
    rows=record.get('chunks')
    if not isinstance(rows,list) or len(rows)>MAX_CHUNKS or side**3<len(rows):
        raise CodecError('Bad chunk index')
    expected=record.get('original_bytes')
    if type(expected)is not int or not 0<=expected<=max_output:
        raise CodecError('Output capacity exceeded')
    out=bytearray();offset=HEADER.size+mlen
    for i,row in enumerate(rows):
        if not isinstance(row,list) or len(row)!=6:raise CodecError('Malformed chunk row')
        mort,layer,n,digest,codec,wire=row
        if (type(mort)is not int or type(layer)is not int or type(n)is not int or type(wire)is not int or
            not 0<=layer<layers or n<0 or n>chunk_size or not 0<=wire<=MAX_SOURCE):
            raise CodecError('Invalid chunk dimensions')
        if mort!=morton3(*lattice(i,side)) or layer!=i%layers:
            raise CodecError('Geometry address differs from deterministic interpretation')
        if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
            raise CodecError('Invalid reference digest')
        if offset+wire>len(binary):raise CodecError('Incomplete source bytes')
        payload=binary[offset:offset+wire];offset+=wire
        if codec=='raw' and wire==n:part=payload
        elif codec=='zlib':
            try:part=_decompress_exact(payload,n)
            except zlib.error as exc:raise CodecError('Invalid compressed source') from exc
        elif codec=='ref' and wire==0:
            part=(cache or {}).get(digest)
            if part is None:raise CodecError('NOT_CACHED: referenced content unavailable')
        else:raise CodecError('Invalid codec or raw/ref length')
        if len(part)!=n or h(part)!=digest:raise CodecError('Source chunk digest mismatch')
        out.extend(part)
        if len(out)>expected:raise CodecError('Decoded size exceeded declared original')
    if offset!=len(binary) or len(out)!=expected or h(out)!=record.get('source_sha256'):
        raise CodecError('Final original source readback mismatch')
    return bytes(out),{'status':'R0_EXACT_BYTE_RECONSTRUCTION', 'source_sha256':h(out),
                       'geometry_root':record['geometry_root'],'original_bytes':len(out),
                       'reference_only_chunks':sum(x[4]=='ref' for x in rows),
                       'authority_verified':False,'transport_verified':False,
                       'semantic_equivalence_verified':False}

def _decompress_manifest(data: bytes) -> bytes:
    d=zlib.decompressobj()
    out=d.decompress(data,MAX_MANIFEST+1)
    if not d.eof or d.unused_data or d.unconsumed_tail or len(out)>MAX_MANIFEST:
        raise CodecError('Bad bounded manifest')
    tail=d.flush()
    if len(out)+len(tail)>MAX_MANIFEST:raise CodecError('Manifest decompression output exceeded capacity')
    return out+tail

def inspect(binary:bytes) -> dict:
    if len(binary)<HEADER.size:raise CodecError('Invalid carrier')
    magic,version,size=HEADER.unpack_from(binary)
    if magic!=MAGIC or version!=VERSION or size>MAX_MANIFEST or HEADER.size+size>len(binary):raise CodecError('Invalid carrier')
    doc=json.loads(_decompress_manifest(binary[HEADER.size:HEADER.size+size]))
    if doc.get('schema')!=SCHEMA:raise CodecError('Bad schema')
    return doc

def encode_delta_bytes(prior:bytes, current:bytes, *, filename:str="payload.bin",
                       layers:int=15,chunk_size:int=65536)->tuple[bytes,dict]:
    """Single-source-root sparse version update: one base key plus sparse byte edits.

    Identical-length changes only; edited content must already be authorised by
    the independent CGX source owner. A cold recipient must NOT decode a patch.
    """
    if len(current)>MAX_SOURCE or len(prior)>MAX_SOURCE:
        raise CodecError('Source exceeds safe local demonstration capacity')
    if not 1<=layers<=MAX_LAYERS or not 1024<=chunk_size<=1024*1024:
        raise CodecError('Invalid geometric parameters')
    if filename!=os.path.basename(filename) or not filename or '\\' in filename:
        raise CodecError('Invalid filename')
    if len(prior)!=len(current):
        blob,stats=encode_bytes(current,filename=filename,layers=layers,chunk_size=chunk_size)
        return blob,{**stats,'selection':'FULL_SOURCE_FALLBACK_DIFFERENT_LENGTH'}
    runs=[];parts=[];changed_chunks=[];patch_total=0
    max_payload=min(len(current)//2,MAX_SOURCE)
    # Skip unchanged coarse chunks; inspect bytes only within changed chunks.
    for chunk_no,off in enumerate(range(0,len(current),chunk_size)):
        old=prior[off:off+chunk_size];new=current[off:off+chunk_size]
        if old==new:continue
        changed_chunks.append(chunk_no)
        i=0
        while i<len(new):
            if old[i]==new[i]:i+=1;continue
            start=i
            while i<len(new) and old[i]!=new[i]:i+=1
            payload=new[start:i];runs.append([off+start,len(payload)]);parts.append(payload);patch_total+=len(payload)
            if len(runs)>4096 or patch_total>max_payload:
                blob,stats=encode_bytes(current,filename=filename,layers=layers,chunk_size=chunk_size)
                return blob,{**stats,'selection':'FULL_SOURCE_FALLBACK_HIGH_EDIT_ENTROPY'}
    geometry={'layout':'morton3-16','index_basis':'chunk ordinal mapped onto power-of-two cubic lattice',
              'side':side_for((len(current)+chunk_size-1)//chunk_size),
              'layers':layers,'chunk_size':chunk_size,
              'address_is_content':False,'semantic_lens_authority':'NONE'}
    record={'schema':SCHEMA,'mode':'baseline-root-sparse-patch','original_name':filename,
            'original_bytes':len(current),'source_sha256':h(current),'prior_sha256':h(prior),
            'geometry_root':h(jpack(geometry)),'geometry':geometry,'changed_morton':[morton3(*lattice(i,geometry['side'])) for i in changed_chunks],
            'runs':runs,'preservation':'R0_EXACT','authority_transfer':False,
            'signed':False,'dbr_promotion':False,'epistemic':'BYTE_VERIFIED_ONLY'}
    manifest=zlib.compress(jpack(record),9)
    payload=b''.join(parts)
    candidate=HEADER.pack(MAGIC,VERSION,len(manifest))+manifest+payload
    if len(candidate)>=len(current)//2:
        blob,stats=encode_bytes(current,filename=filename,layers=layers,chunk_size=chunk_size)
        if len(candidate)>=len(blob):
            return blob,{**stats,'selection':'FULL_SOURCE_FALLBACK_NO_WIRE_BENEFIT'}
    return candidate,{'selection':'ROOT_REFERENCE_SPARSE_PATCH','wire_bytes':len(candidate),
            'original_bytes':len(current),'prior_bytes_required':len(prior),
            'patch_runs':len(runs),'patch_bytes':len(payload),'changed_chunks':len(changed_chunks),
            'prior_sha256':record['prior_sha256'],'source_sha256':record['source_sha256'],
            'geometry_root':record['geometry_root'],'status':'R0_EXACT_CANDIDATE_WITH_CACHE_ONLY'}


def decode_delta_bytes(carrier:bytes,prior:bytes|None)->tuple[bytes,dict]:
    record=inspect(carrier)
    if record.get('mode')!='baseline-root-sparse-patch':
        return decode_bytes(carrier)
    if record.get('preservation')!='R0_EXACT' or type(record.get('original_bytes')) is not int or not 0<=record['original_bytes']<=MAX_SOURCE:
        raise CodecError('Unsupported or oversized prior-dependent patch')
    if prior is None:raise CodecError('NOT_CACHED: exact prior source required')
    if len(prior)!=record.get('original_bytes') or h(prior)!=record.get('prior_sha256'):
        raise CodecError('CONTEXT_MISMATCH: prior source SHA-256 differs')
    geometry=record.get('geometry',{})
    if h(jpack(geometry))!=record.get('geometry_root'):
        raise CodecError('Invalid geometric root')
    if type(geometry.get('side'))is not int or type(geometry.get('chunk_size'))is not int:
        raise CodecError('Invalid geometry')
    if type(record.get('changed_morton'))is not list:
        raise CodecError('Invalid changed geometry')
    output=bytearray(prior)
    runs=record.get('runs')
    if not isinstance(runs,list) or len(runs)>4096:raise CodecError('Invalid patch count')
    idx=HEADER.size+HEADER.unpack_from(carrier)[2]
    touched=set();last_end=0
    for row in runs:
        if not isinstance(row,list) or len(row)!=2 or any(type(x)is not int for x in row):
            raise CodecError('Invalid patch index')
        start,n=row
        if start<last_end or n<1 or start+n>len(prior) or idx+n>len(carrier):
            raise CodecError('Invalid patch bounds or order')
        output[start:start+n]=carrier[idx:idx+n];idx+=n;last_end=start+n
        touched.add(start//geometry['chunk_size'])
    side=geometry['side']
    expected=sorted(morton3(*lattice(i,side)) for i in touched)
    if expected!=sorted(record['changed_morton']) or idx!=len(carrier):
        raise CodecError('Changed geometric slice mismatch or trailing bytes')
    if h(output)!=record.get('source_sha256'):
        raise CodecError('Source root mismatch after patch')
    return bytes(output),{'status':'R0_EXACT_ROOT_RECONSTRUCTION','base_sha256':h(prior),
        'source_sha256':h(output),'patch_runs':len(runs),
        'same_baseline_confirmed':True,'signed':False,'semantic_equivalence_verified':False}

def main() -> int:
    p=argparse.ArgumentParser(description='CGX candidate geometric source byte carrier')
    sub=p.add_subparsers(dest='op',required=True)
    a=sub.add_parser('encode');a.add_argument('source',type=Path);a.add_argument('target',type=Path)
    a.add_argument('--layers',type=int,default=15);a.add_argument('--chunk',type=int,default=65536)
    a.add_argument('--known',type=Path,action='append',default=[])
    a.add_argument('--prefer-fast',action='store_true');a.add_argument('--cpu-weight',type=float,default=0.)
    d=sub.add_parser('delta');d.add_argument('prior',type=Path);d.add_argument('current',type=Path);d.add_argument('target',type=Path)
    d.add_argument('--layers',type=int,default=15);d.add_argument('--chunk',type=int,default=65536)
    e=sub.add_parser('apply');e.add_argument('prior',type=Path);e.add_argument('source',type=Path);e.add_argument('target',type=Path)
    b=sub.add_parser('decode');b.add_argument('source',type=Path);b.add_argument('target',type=Path)
    b.add_argument('--known',type=Path,action='append',default=[])
    c=sub.add_parser('inspect');c.add_argument('source',type=Path)
    args=p.parse_args()
    if args.op=='inspect': print(json.dumps(inspect(args.source.read_bytes()),indent=2));return 0
    if args.op=='delta':
        blob,stats=encode_delta_bytes(args.prior.read_bytes(),args.current.read_bytes(),filename=args.current.name,layers=args.layers,chunk_size=args.chunk)
        if args.target.exists():raise CodecError('No overwrite of prior carrier')
        args.target.write_bytes(blob);print(json.dumps(stats,indent=2));return 0
    if args.op=='apply':
        restored,receipt=decode_delta_bytes(args.source.read_bytes(),args.prior.read_bytes())
        if args.target.exists():raise CodecError('No overwrite of prior source')
        args.target.write_bytes(restored);print(json.dumps(receipt,indent=2));return 0
    if args.op=='encode':
        original=args.source.read_bytes()
        cache=chunk_map(args.known,args.chunk)
        blob,stats=encode_bytes(original,filename=args.source.name,layers=args.layers,chunk_size=args.chunk,cache=cache,prefer_fast=args.prefer_fast,cpu_byte_penalty=args.cpu_weight)
        args.target.write_bytes(blob)
        stats['cost_gate']= 'SHORTHAND_WIRE_SAVING' if len(blob)<len(original) else 'BYPASS_RAW_ON_FIRST_SHARE'
        print(json.dumps(stats,indent=2));return 0
    manifest=inspect(args.source.read_bytes())
    cache=chunk_map(args.known,manifest['geometry']['chunk_size'])
    restored,result=decode_bytes(args.source.read_bytes(),cache=cache)
    if args.target.exists():raise CodecError('Target already exists; never overwrite')
    args.target.write_bytes(restored)
    print(json.dumps(result,indent=2));return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (CodecError,OSError) as exc:
        print('CGX_HOLD: '+str(exc),file=__import__('sys').stderr)
        raise SystemExit(2)
