"""Private CGX manual intake: existing LOAD v17 carrier, occurrence-separated review.
No execution of source, network, new store, native admission or source deletion.
"""
from __future__ import annotations
import argparse, ast, collections, hashlib, json, math, os, re, stat, tempfile, zlib
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
MAGIC=b'CGXBYTE17'
MAX_FILE=2*1024*1024
MAX_BATCH=8*1024*1024
MAX_ITEMS=16

def sha(data): return hashlib.sha256(data).hexdigest()
def enc(value): return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode()
def strict_json(text):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise ValueError('DUPLICATE_JSON_KEY_HOLD')
            result[key]=value
        return result
    def reject(value): raise ValueError('NONFINITE_JSON_NUMBER_HOLD')
    def finite(value):
        number=float(value)
        if not math.isfinite(number): reject(value)
        return number
    return json.loads(text,object_pairs_hook=unique,parse_constant=reject,parse_float=finite)
def redirected(st): return stat.S_ISLNK(st.st_mode) or bool(getattr(st,'st_file_attributes',0)&0x400)
def stamp(st): return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns,st.st_nlink)
# Windows path stat and handle fstat may expose different creation/change times.
# Compare shared identity fields across interfaces, and full stamps within each.
def identity(st): return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_nlink)

def read_source(root,relative):
    if not isinstance(relative,str) or any(ord(c)<32 or ord(c)==127 for c in relative): raise ValueError('PATH_HOLD')
    r=PurePosixPath(relative)
    # Reject lexical aliases before hashing the occurrence; never merge distinct paths by byte digest.
    if r.as_posix()!=relative: raise ValueError('PATH_HOLD')
    if r.is_absolute() or not r.parts or any(p in ('.','..') or ':' in p or '\\' in p for p in r.parts): raise ValueError('PATH_HOLD')
    if redirected(root.lstat()): raise ValueError('ROOT_REDIRECT_HOLD')
    p=root
    for part in r.parts:
        p=p/part
        if redirected(p.lstat()): raise ValueError('SOURCE_REDIRECT_HOLD')
    if not p.resolve(strict=True).is_relative_to(root.resolve(strict=True)): raise ValueError('OUTSIDE_INTAKE_HOLD')
    before=p.stat()
    if not stat.S_ISREG(before.st_mode) or not 0<before.st_size<=MAX_FILE: raise ValueError('SOURCE_SIZE_OR_KIND_HOLD')
    with p.open('rb') as f:
        opened=os.fstat(f.fileno())
        if identity(opened)!=identity(before): raise ValueError('SOURCE_CHANGED_HOLD')
        raw=f.read(MAX_FILE+1)
        if stamp(os.fstat(f.fileno()))!=stamp(opened): raise ValueError('SOURCE_CHANGED_HOLD')
    if len(raw)!=before.st_size or stamp(p.stat())!=stamp(before): raise ValueError('SOURCE_CHANGED_HOLD')
    return p,before,raw

def restore(blob,expected):
    if len(blob)<49 or blob[:9]!=MAGIC: raise ValueError('CARRIER_MAGIC_HOLD')
    size=int.from_bytes(blob[9:17],'big')
    if not 0<size<=MAX_FILE or blob[17:49].hex()!=expected: raise ValueError('CARRIER_HEADER_HOLD')
    inflater=zlib.decompressobj();raw=inflater.decompress(blob[49:],size+1)
    if len(raw)!=size or not inflater.eof or inflater.unused_data or inflater.unconsumed_tail or sha(raw)!=expected: raise ValueError('CARRIER_INVERSE_HOLD')
    return raw

def put_exact(path,data):
    if path.exists():
        if redirected(path.lstat()) or path.read_bytes()!=data: raise ValueError('EXISTING_BYTES_COLLISION')
        return False
    fd,tmp=tempfile.mkstemp(prefix='.cgx-intake-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f: f.write(data);f.flush();os.fsync(f.fileno())
        try: os.link(tmp,path)
        except FileExistsError:
            if redirected(path.lstat()) or path.read_bytes()!=data: raise ValueError('CONCURRENT_BYTES_COLLISION')
            return False
        if path.read_bytes()!=data: raise ValueError('PERSISTENCE_READBACK_HOLD')
        return True
    finally: os.unlink(tmp)

class Structure(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True);self.tags=collections.Counter();self.ids=[]
    def handle_starttag(self,tag,attrs):
        self.tags[tag]+=1
        for k,v in attrs:
            if k=='id' and v and len(self.ids)<64:self.ids.append(v[:160])

def projection(raw,suffix):
    try:
        text=raw.decode('utf-8-sig',errors='strict')
        if suffix=='.py':
            tree=ast.parse(text);data={'functions':[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))][:128],'classes':[n.name for n in ast.walk(tree) if isinstance(n,ast.ClassDef)][:64]};kind='STATIC_CODE_STRUCTURE';purpose='capability candidate; never execute on intake'
        elif suffix in ('.html','.htm'):
            parser=Structure();parser.feed(text);parser.close();data={'tags':dict(parser.tags),'element_ids':parser.ids};kind='INERT_DOM_STRUCTURE';purpose='interface or engine candidate; isolate scripts until qualified'
        elif suffix=='.md':
            data={'headings':[x[:240] for x in re.findall(r'^#{1,6}\s+(.+)$',text,re.M)[:128]],'lines':len(text.splitlines())};kind='DOCUMENT_STRUCTURE';purpose='source-grounded knowledge candidate'
        elif suffix=='.json':
            value=strict_json(text);data={'type':type(value).__name__,'top_level_count':len(value) if isinstance(value,(list,dict)) else 1,'keys':list(value)[:128] if isinstance(value,dict) else []};kind='DATA_STRUCTURE';purpose='typed data candidate'
        else: return {'kind':'BYTE_ONLY','data':{},'semantic':{'status':'VIEW_HOLD','reason':'UNQUALIFIED_PARSER'}}
        return {'kind':kind,'data':data,'semantic':{'status':'REVIEW_CANDIDATE','purpose':purpose,'scientific_validation':False}}
    except (UnicodeError,ValueError,SyntaxError,RecursionError):return {'kind':'BYTE_ONLY','data':{},'semantic':{'status':'VIEW_HOLD','reason':'PARSE_FAILED'}}

def ingest(root,load,relative):
    p,st,raw=read_source(root,relative);h=sha(raw)
    packs=load/'R0_PACKS_private';receipts=load/'Local_batch_receipts'
    if not packs.is_dir() or not receipts.is_dir():raise ValueError('EXISTING_LOAD_STORE_REQUIRED')
    try:
        guard=strict_json((load/'INTEGRITY_AND_GC_GATES.review.json').read_text(encoding='utf-8-sig'))
    except (ValueError, RecursionError) as exc:
        raise ValueError('LOAD_CONTRACT_HOLD') from exc
    if not isinstance(guard,dict) or guard.get('schema')!='CGX-LOAD-INTAKE-AUDIT/0.17':raise ValueError('LOAD_CONTRACT_HOLD')
    carrier=packs/(h+'.cgxpre');blob=MAGIC+len(raw).to_bytes(8,'big')+bytes.fromhex(h)+zlib.compress(raw,9)
    if carrier.exists():
        if redirected(carrier.lstat()) or restore(carrier.read_bytes(),h)!=raw:raise ValueError('EXISTING_CARRIER_HOLD')
        created=False
    else:created=put_exact(carrier,blob)
    disk=carrier.read_bytes()
    if restore(disk,h)!=raw or stamp(p.stat())!=stamp(st) or sha(p.read_bytes())!=h:raise ValueError('SOURCE_REPLAY_HOLD')
    occurrence=sha(enc({'root':str(root.resolve()),'relative':relative,'sha256':h}))
    view=projection(raw,p.suffix.lower());receipt={'schema':'CGX-MANUAL-INTAKE-OCCURRENCE-REVIEW/1','parent':'Cognigrex.cgx','load':'LOAD.cgx','occurrence_id':occurrence,'relative_path':relative,'source_sha256':h,'source_size':len(raw),'source_mtime_ns':st.st_mtime_ns,'source_links':st.st_nlink,'carrier_sha256':sha(disk),'carrier_name':carrier.name,'exact_inverse':True,'data_projection':view['data'],'semantic_projection':view['semantic'],'view_kind':view['kind'],'rights':'UNREVIEWED_PRIVATE','acl_verified':False,'native_admitted':False,'data_space_admitted':False,'source_deleted':False,'delete_gate':'HOLD_RIGHTS_ACL_SEMANTIC_ADMISSION_INDEPENDENT_REPLAY'}
    # Occurrence receipts do not replace existing digest-keyed legacy receipts.
    receipt_bytes=enc(receipt);rp=receipts/('manual-intake-'+occurrence+'-'+sha(receipt_bytes)[:16]+'.review.json')
    put_exact(rp,receipt_bytes)
    return {'relative':relative,'sha256':h,'bytes':len(raw),'carrier_bytes':len(disk),'new_carrier':created,'occurrence':occurrence,'receipt':rp.name,'receipt_sha256':sha(receipt_bytes),'view_kind':view['kind'],'semantic_state':view['semantic']['status'],'exact_inverse':True,'source_deleted':False,'native_admitted':False}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True,type=Path);parser.add_argument('--load',required=True,type=Path);parser.add_argument('files',nargs='+');a=parser.parse_args()
    if len(a.files)>MAX_ITEMS or len(set(a.files))!=len(a.files):raise SystemExit('BATCH_SIZE_OR_DUPLICATE_HOLD')
    sizes=[len(read_source(a.root,r)[2]) for r in a.files]
    if sum(sizes)>MAX_BATCH:raise SystemExit('BATCH_BYTES_HOLD')
    results=[]
    for r in a.files:results.append(ingest(a.root,a.load.resolve(strict=True),r))
    print(json.dumps({'state':'PRIVATE_R0_CAPTURE_REVIEW_ONLY','count':len(results),'source_bytes':sum(x['bytes'] for x in results),'source_deletions':0,'native_admission':False,'results':results},sort_keys=True))
if __name__=='__main__': main()
