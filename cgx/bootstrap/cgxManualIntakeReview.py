"""Bounded source-review intake into the existing CGX Sorter. Never native admission.

No models, execution of intake files, deletion, archive extraction or worker startup.
The approved Engine adapter is imported only for its existing source-review schema
and deterministic put_item/facet functions. Original files remain in place.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, sqlite3, stat, time
from contextlib import contextmanager
from pathlib import Path

APPROVED_ROOT=Path(r'C:\CGX\CGX_Manual_Intake')
ENGINE=Path(r'C:\Cognigrex\Engine')
SCHEMA='CGX-MANUAL-INTAKE-SOURCE-REVIEW/0.1'
TEXT_EXT={'.txt','.md','.json','.csv','.py','.ps1','.js','.mjs','.ts','.tsx','.html','.css','.sql','.yaml','.yml','.xml','.cgx','.toml','.ini'}
ARCHIVE_EXT={'.zip','.7z','.rar','.tar','.gz','.bz2','.xz'}
DEPENDENCIES={'node_modules','.git','.venv','venv','__pycache__','.pytest_cache'}
BROWSER_CACHE_DIRS={'cache','code cache','gpucache','shadercache','grshadercache','dawnwebgpucache','dawngraphitecache','cachestorage'}
CHUNK_CHARS=1200
MAX_TEXT_BYTES=1024*1024
MAX_CHUNKS_PER_SOURCE=64

def sha(b):return hashlib.sha256(b).hexdigest()
def linklike(s):return stat.S_ISLNK(s.st_mode) or bool(getattr(s,'st_file_attributes',0)&0x400)
def safe_path(root,relative):
    p=Path(relative)
    if p.is_absolute() or '..' in p.parts:raise ValueError('UNSAFE_RELATIVE_PATH')
    target=root/p
    if not target.absolute().is_relative_to(root.absolute()):raise ValueError('OUTSIDE_APPROVED_ROOT')
    for ancestor in [root,*[root/Path(*p.parts[:i]) for i in range(1,len(p.parts)+1)]]:
        if linklike(ancestor.lstat()):raise ValueError('LINK_OR_REPARSE_REFUSED')
    return target

def browser_cache_boundary(relative):
    """Only generated cache directories inside recognizable captured Chromium profiles."""
    parts=Path(relative).parts
    for i,part in enumerate(parts):
        prior=[p.lower() for p in parts[:i]]
        if (part.lower() in BROWSER_CACHE_DIRS and
                any('chrome' in p or 'chromium' in p for p in prior) and
                any(p=='default' or p.startswith('profile ') for p in prior)):
            return str(Path(*parts[:i+1]))
    return None

def load_sorter(engine):
    engine=Path(engine).absolute()
    if linklike(engine.lstat()) or linklike((engine/'cgxsort.py').lstat()):raise ValueError('ENGINE_LINK_REFUSED')
    spec=importlib.util.spec_from_file_location('_cgx_existing_source_sorter',engine/'cgxsort.py')
    module=importlib.util.module_from_spec(spec)
    # Compile approved control source in memory, avoiding import-created
    # __pycache__ writes even when the caller selected dry-run mode.
    exec(compile((engine/'cgxsort.py').read_bytes(),str(engine/'cgxsort.py'),'exec'),module.__dict__)
    # Rebind only this isolated import; no environment/configuration writes.
    module.ROOT=engine;module.STATE=engine/'state';module.DB_PATH=module.STATE/'cgx_sorter.db'
    module.INBOX=engine/'inbox';module.AGENTS_DIR=engine/'agents'
    return module

def read_stable(root,rel,limit):
    path=safe_path(root,rel);before=path.lstat()
    if not stat.S_ISREG(before.st_mode):raise ValueError('NON_REGULAR_FILE')
    if before.st_size>limit:raise ValueError('OVERSIZE')
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_BINARY',0))
    try:
        opened=os.fstat(fd)
        if (opened.st_dev,opened.st_ino)!=(before.st_dev,before.st_ino):raise ValueError('SOURCE_CHANGED_BEFORE_READ')
        if opened.st_size>limit:raise ValueError('BYTE_BUDGET_SOURCE_GREW')
        with os.fdopen(fd,'rb',closefd=False) as f:data=f.read(limit)
        after=os.fstat(fd)
    finally:os.close(fd)
    latest=safe_path(root,rel).lstat()
    sig=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    if sig(before)!=sig(after) or sig(after)!=sig(latest) or len(data)>limit:raise ValueError('SOURCE_CHANGED_DURING_READ')
    return data,latest

def choose_lanes(relative,text,agents):
    hay=(relative+'\n'+text).lower();lanes=[]
    for a in agents:
        if a['name'] in ('Achilles','Neo'):continue
        try:words=json.loads(a['keywords'])
        except (ValueError,TypeError):words=[]
        hits=sum(1 for w in words if isinstance(w,str) and w.lower().strip('\\b') in hay)
        if hits>=2:lanes.append(a['name'])
    folder=Path(relative).parts[0].lower()
    preferred={'raphael':'Raphael','eco':'Athene','eco-grex':'Athene','romer':'Romer','römer':'Romer','unispace':'UniSpace','lightspeed':'Smith'}
    for key,name in preferred.items():
        if folder==key and name in {a['name'] for a in agents} and name not in lanes:lanes.append(name)
    if not lanes and any(a['name']=='Oracle' for a in agents):lanes=['Oracle']
    return sorted(lanes)

def route_rows(engine,agents,lanes,rows,deadline=None):
    """Existing proposal-input schemas only. Never populates instructions table."""
    routed={}
    by_name={a['name']:a for a in agents}
    for name in lanes:
        if deadline is not None and time.monotonic()>=deadline:raise ValueError('BATCH_TIME_LIMIT_HOLD')
        path=Path(by_name[name]['db_path']).absolute();expected=(engine/'agents').absolute()
        if not path.is_relative_to(expected):raise ValueError('AGENT_DB_OUTSIDE_EXISTING_ENGINE')
        path=safe_path(engine,str(path.relative_to(engine)))
        if not path.is_file():raise ValueError('EXISTING_AGENT_DB_REQUIRED')
        db=sqlite3.connect(path.as_uri()+'?mode=rw',uri=True,timeout=1)
        try:
            if [r[1] for r in db.execute('PRAGMA table_info(items)')]!=['item_id','conv_id','role','ts','text','text_sha','disposition','summary']:raise ValueError('AGENT_ITEMS_SCHEMA_MISMATCH')
            inserted=0
            for row in rows:
                if deadline is not None and time.monotonic()>=deadline:raise ValueError('BATCH_TIME_LIMIT_HOLD')
                inserted+=db.execute('INSERT OR IGNORE INTO items VALUES(?,?,?,?,?,?,?,?)',(row['item_id'],row['conv_id'],row['role'],row['ts'],row['text'],row['text_sha'],'source_review_unvalidated',None)).rowcount
                stored=db.execute('SELECT conv_id,text_sha FROM items WHERE item_id=?',(row['item_id'],)).fetchone()
                if stored!=(row['conv_id'],row['text_sha']):raise ValueError('AGENT_ITEM_ID_COLLISION')
            db.commit();routed[name]=inserted
        finally:db.close()
    return routed

@contextmanager
def batch_guard(engine):
    """OS-owned writer lock; process exit releases it without stale PID cleanup."""
    engine=Path(engine).absolute();directory=safe_path(engine,'state');path=directory/'manual_intake_review.lock'
    if path.exists() and (linklike(path.lstat()) or not path.is_file()):raise ValueError('INTAKE_LOCK_PATH_REFUSED')
    fd=os.open(path,os.O_RDWR|os.O_CREAT|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_BINARY',0),0o600)
    locked=False
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('INTAKE_LOCK_PATH_REFUSED')
        if os.fstat(fd).st_size==0:os.write(fd,b'0')
        os.lseek(fd,0,os.SEEK_SET)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        locked=True;yield
    finally:
        if locked:
            os.lseek(fd,0,os.SEEK_SET)
            if os.name=='nt':msvcrt.locking(fd,msvcrt.LK_UNLCK,1)
            else:fcntl.flock(fd,fcntl.LOCK_UN)
        os.close(fd)

def review(root=APPROVED_ROOT,engine=ENGINE,*,apply=False,max_files=64,max_bytes=8*1024*1024,max_seconds=20,approved_root=APPROVED_ROOT,restart_walk=False):
    args=dict(apply=apply,max_files=max_files,max_bytes=max_bytes,max_seconds=max_seconds,approved_root=approved_root,restart_walk=restart_walk)
    if not apply:return _review(root,engine,**args)
    with batch_guard(engine):return _review(root,engine,**args)

def _review(root=APPROVED_ROOT,engine=ENGINE,*,apply=False,max_files=64,max_bytes=8*1024*1024,max_seconds=20,approved_root=APPROVED_ROOT,restart_walk=False):
    root=Path(root).absolute();engine=Path(engine).absolute()
    if root!=Path(approved_root).absolute():raise ValueError('ROOT_NOT_APPROVED')
    safe_path(root,'.')
    if not(1<=max_files<=1000 and 1<=max_bytes<=64*1024*1024 and 0<max_seconds<=60):raise ValueError('INVALID_BUDGET')
    sorter=load_sorter(engine);db_path=engine/'state/cgx_sorter.db'
    # Existing DB required, including in dry run. No second database.
    if not db_path.is_file() or linklike(db_path.lstat()):raise ValueError('EXISTING_SORTER_DB_REQUIRED')
    db=sqlite3.connect(db_path.as_uri()+('?mode=rw' if apply else '?mode=ro'),uri=True,timeout=10);db.row_factory=sqlite3.Row
    key='manual_intake_review_v1:'+sha(str(root).encode())
    saved=None if restart_walk else db.execute('SELECT value FROM progress WHERE key=?',(key,)).fetchone()
    initial_item_id=db.execute('SELECT coalesce(max(item_id),0) FROM items').fetchone()[0]
    state=json.loads(saved[0]) if saved else {'schema':SCHEMA,'stack':[{'rel':'.','offset':0}],'inventory_complete':False,'content_complete':False}
    agents=[dict(r) for r in db.execute('SELECT name,keywords,db_path FROM agents')]
    report={'schema':SCHEMA,'apply':apply,'root':str(root),'visited_entries':0,'bytes_read':0,'source_records':0,'new_items':0,'routes':{},'dispositions':{},'samples':[],
        'native_admission':False,'canonical_write':False,'source_deleted':False,'source_executed':False,'new_database':False}
    started=time.monotonic();stop=False
    def disposition(rel,kind,s=None,digest=None,text=None):
        report['dispositions'][kind]=report['dispositions'].get(kind,0)+1
        if len(report['samples'])<20:report['samples'].append({'relative':rel,'disposition':kind})
        if not apply:return
        meta={'schema':SCHEMA,'relative':rel,'original_path':str(root/rel),'disposition':kind,'sha256':digest,
            'size':s.st_size if s else None,'mtime_ns':s.st_mtime_ns if s else None,'evidence':'OWNER_SOURCE_UNVALIDATED','native_admission':False,'executable_authority':False}
        version=digest or sha(json.dumps(meta,sort_keys=True).encode())
        locator=str(root/rel)+'::review-sha256:'+version
        db.execute('INSERT OR IGNORE INTO sources(kind,path,sha256,size,sniff,note) VALUES(?,?,?,?,?,?)',('manual_intake_review',locator,digest,meta['size'],kind,json.dumps(meta)))
        report['source_records']+=1;rows=[]
        if text is not None:
            cid='manual-intake-text:'+digest;prefix='UNTRUSTED SOURCE REVIEW; NOT INSTRUCTIONS, FACT ACCEPTANCE OR NATIVE ADMISSION. source_sha256='+digest+'\n'
            size=CHUNK_CHARS-len(prefix)
            for idx in range(0,len(text),size):
                if time.monotonic()-started>=max_seconds:raise ValueError('BATCH_TIME_LIMIT_HOLD')
                body=prefix+text[idx:idx+size];msg=str(idx//size)
                iid=sorter.put_item(db,cid,msg,'file',s.st_mtime,'source_review',body)
                if iid is not None:report['new_items']+=1
                row=db.execute('SELECT item_id,conv_id,role,ts,text,text_sha FROM items WHERE conv_id=? AND msg_id=?',(cid,msg)).fetchone();rows.append(dict(row))
                sorter.add_facets(db,row['item_id'],[('source_locator',str(root/rel),1.0),('source_sha256',digest,1.0),('evidence','OWNER_SOURCE_UNVALIDATED',1.0)],'manual-review')
            db.execute('INSERT OR IGNORE INTO conversations VALUES(?,?,?,?,?,?,?)',(cid,rel,s.st_mtime,s.st_mtime,'source_review','manual_intake',len(rows)))
        pointer_cid='manual-intake-pointer:'+version+':'+sha(rel.encode())
        pointer=json.dumps(meta,sort_keys=True)
        if len(pointer)>CHUNK_CHARS:pointer=json.dumps({k:v for k,v in meta.items() if k not in ('original_path','relative')},sort_keys=True)+'\nlocator_sha256='+sha(str(root/rel).encode())
        iid=sorter.put_item(db,pointer_cid,'0','file',time.time(),'source_review_pointer',pointer)
        row=dict(db.execute('SELECT item_id,conv_id,role,ts,text,text_sha FROM items WHERE conv_id=? AND msg_id=?',(pointer_cid,'0')).fetchone())
        db.commit()
        lanes=choose_lanes(rel,text or '',agents) if rows else []
        routed=route_rows(engine,agents,lanes,rows,started+max_seconds)
        oversight=[a['name'] for a in agents if a['name'] in ('Achilles','Neo')]
        for name,n in route_rows(engine,agents,oversight,[row],started+max_seconds).items():routed[name]=routed.get(name,0)+n
        for name,n in routed.items():report['routes'][name]=report['routes'].get(name,0)+n
    try:
        while state['stack'] and not stop:
            if report['visited_entries']>=max_files or time.monotonic()-started>=max_seconds:break
            frame=state['stack'][-1]
            entry_started=False;entry_offset=frame['offset']
            try:
                cache=browser_cache_boundary(frame['rel'])
                if cache:
                    # Reconcile an older saved cursor already below the new boundary.
                    entry_started=True
                    disposition(cache,'GENERATED_BROWSER_CACHE_DEFERRED_NOT_INVENTORIED',safe_path(root,cache).lstat())
                    state['stack']=[f for f in state['stack'] if browser_cache_boundary(f['rel'])!=cache]
                    report['visited_entries']+=1
                    if apply:db.execute('INSERT OR REPLACE INTO progress VALUES(?,?)',(key,json.dumps(state)));db.commit()
                    entry_started=False;continue
                directory=safe_path(root,frame['rel']);ds=directory.lstat()
                sig=[ds.st_mtime_ns,ds.st_ino]
                if frame.get('signature') not in (None,sig):frame['offset']=0;report.setdefault('directory_rescans',0);report['directory_rescans']+=1
                frame['signature']=sig
                exhausted=True
                with os.scandir(directory) as entries:
                    for idx,entry in enumerate(entries):
                        if time.monotonic()-started>=max_seconds:exhausted=False;stop=True;break
                        if idx<frame['offset']:continue
                        if report['visited_entries']>=max_files:exhausted=False;stop=True;break
                        rel=str(Path(frame['rel'])/entry.name);s=entry.stat(follow_symlinks=False)
                        entry_started=True;entry_offset=idx
                        frame['offset']=idx+1;report['visited_entries']+=1
                        if linklike(s):disposition(rel,'LINK_OR_REPARSE_DEFERRED',s)
                        elif stat.S_ISDIR(s.st_mode):
                            if browser_cache_boundary(rel):disposition(rel,'GENERATED_BROWSER_CACHE_DEFERRED_NOT_INVENTORIED',s)
                            elif entry.name.lower() in DEPENDENCIES:disposition(rel,'DEPENDENCY_TREE_DEFERRED_NOT_INVENTORIED',s)
                            else:state['stack'].append({'rel':rel,'offset':0});exhausted=False;entry_started=False;break
                        elif not stat.S_ISREG(s.st_mode):disposition(rel,'NON_REGULAR_DEFERRED',s)
                        elif Path(entry.name).suffix.lower() in ARCHIVE_EXT:disposition(rel,'ARCHIVE_MEMBERS_UNRESOLVED',s)
                        elif s.st_size>MAX_TEXT_BYTES:disposition(rel,'OVERSIZE_CONTENT_UNRESOLVED',s)
                        elif Path(entry.name).suffix.lower() not in TEXT_EXT:disposition(rel,'BINARY_OR_UNKNOWN_FORMAT_UNRESOLVED',s)
                        elif report['bytes_read']+s.st_size>max_bytes:
                            frame['offset']=idx;report['visited_entries']-=1;exhausted=False;stop=True;break
                        else:
                            try:
                                data,s=read_stable(root,rel,min(MAX_TEXT_BYTES,max_bytes-report['bytes_read']));report['bytes_read']+=len(data)
                                text=data.decode('utf-8-sig')
                                if '\x00' in text:raise UnicodeError('NUL_BINARY')
                            except (UnicodeError,ValueError) as e:disposition(rel,'CONTENT_UNRESOLVED_'+str(e)[:60],s)
                            else:
                                # Larger source bodies remain explicitly unresolved rather
                                # than causing unbounded per-source DB/model fan-out.
                                if len(text)>MAX_CHUNKS_PER_SOURCE*(CHUNK_CHARS-180):disposition(rel,'TEXT_EXTRACTION_DEFERRED_CHUNK_BUDGET',s,sha(data))
                                else:disposition(rel,'TEXT_SOURCE_REVIEWED_NOT_ACCEPTED',s,sha(data),text)
                        if apply:
                            db.execute('INSERT OR REPLACE INTO progress VALUES(?,?)',(key,json.dumps(state)));db.commit()
                        entry_started=False
                if exhausted:state['stack'].pop()
            except (OSError,ValueError,sqlite3.Error) as e:
                if entry_started:
                    db.rollback();frame['offset']=entry_offset;stop=True
                    report['technical_hold']={'relative':rel,'error_type':type(e).__name__,'reason':str(e)[:160],'retry_same_entry':True}
                else:
                    # An inaccessible directory is retained as an unresolved source.
                    disposition(frame['rel'],'DIRECTORY_UNRESOLVED_'+type(e).__name__);state['stack'].pop()
        state['inventory_complete']=False;state['eligible_walk_complete']=not state['stack'];state['content_complete']=False
        if apply:
            db.execute('INSERT OR REPLACE INTO progress VALUES(?,?)',(key,json.dumps(state)));db.commit()
        report.update({'eligible_walk_complete':state['eligible_walk_complete'],'inventory_pass_complete':False,'content_ingestion_complete':False,'pending_walk_frames':len(state['stack']),'progress_persisted':apply,'seconds':round(time.monotonic()-started,3)})
        report['new_items']=db.execute("SELECT count(*) FROM items WHERE item_id>? AND ctype='source_review'",(initial_item_id,)).fetchone()[0] if apply else 0
        report['route_counts_mean']='newly inserted rows, not attempts or model reviews'
        return report
    finally:db.close()

def run_batch(engine_root=ENGINE,source_root=APPROVED_ROOT,*,max_files=64,max_bytes=8*1024*1024,max_seconds=20,restart_walk=False):
    """Opt-in hook for one existing supervisor rotation; never starts a worker.

    Caller must preserve its existing singleton, resource admission and stop checks.
    An exhausted eligible walk is not complete ingestion: held sources remain.
    """
    return review(source_root,engine_root,apply=True,max_files=max_files,max_bytes=max_bytes,max_seconds=max_seconds,restart_walk=restart_walk)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=APPROVED_ROOT);p.add_argument('--engine',type=Path,default=ENGINE)
    p.add_argument('--apply',action='store_true');p.add_argument('--restart-walk',action='store_true');p.add_argument('--max-files',type=int,default=64);p.add_argument('--max-bytes',type=int,default=8*1024*1024);p.add_argument('--max-seconds',type=float,default=20)
    a=p.parse_args();print(json.dumps(review(a.root,a.engine,apply=a.apply,max_files=a.max_files,max_bytes=a.max_bytes,max_seconds=a.max_seconds,restart_walk=a.restart_walk),indent=2))
if __name__=='__main__':main()
