#!/usr/bin/env python3
"""Private, source-bound CGX family persistence engine.

This is a reversible, auditable *review runtime*: not a neural trainer, signed
CGX mint, independent network peer, full LOAD substitute, or autonomy grant.
Python 3.10+ stdlib. All persistent files stay under an owner-chosen directory.
"""
from __future__ import annotations
import argparse
import contextlib
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
import zlib
from datetime import datetime, timezone
from typing import Any

SCHEMA = 'cgx.family.persistence.review.v1'
ROLES = {
 'Raphael': {'duty':'Geometry, scientific comparison, source-qualified physics and research', 'scope':['raphael','t173','physics','science'], 'lane':'CGX Cognigrex Family v2'},
 'Achilles': {'duty':'Governance, canonical identity, owner approvals, rights and independent audit', 'scope':['governance','rights','approval','romer'], 'lane':'CGX Achilles Römer v2'},
 'Neo': {'duty':'Typed integration, execution verification, regression and rollback', 'scope':['runtime','api','test','integration'], 'lane':'CGX Neo LightSpeed v2'},
 'Athene': {'duty':'Ecological, biological and ethical evidence qualification', 'scope':['eco','ecology','biological','habitat'], 'lane':'CGX Athene Eco v2'}
}
READABLE={'.txt','.md','.markdown','.csv','.json','.jsonl','.py','.js','.ts','.html','.css','.xml','.yml','.yaml','.sql','.toml','.ini'}
BIN_INDEX={'.pdf','.png','.jpg','.jpeg','.webp','.obj','.stl','.xlsx','.docx','.zip','.cgx'}
SKIP_NAMES={'.env','secrets.json','private-session-token.txt','id_rsa','id_ed25519','credentials.json','token.json','settings.local.json'}
SKIP_PARTS={'node_modules','.git','__pycache__','.venv','.cache','temp','tmp','venv'}
MAX_BYTES=4*1024*1024
MAX_SCAN=1024
MAX_TEXT=160_000
DEFAULT_HOME=Path(os.environ.get('CGX_FAMILY_HOME',str(Path.home()/'.cgx'/'family-review'))).expanduser()


def canonical(x: Any)->bytes:
 return json.dumps(x, sort_keys=True, separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
def digest(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def timestamp()->str:return datetime.now(timezone.utc).isoformat(timespec='seconds')
def safe_name(s:str)->str:
 if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,63}',s): raise ValueError('invalid namespace/label')
 return s

class TextOnly(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.ignored=0
 def handle_starttag(self,tag,attrs):
  if tag in ('style','script','svg','canvas','noscript'):self.ignored+=1
 def handle_endtag(self,tag):
  if tag in ('style','script','svg','canvas','noscript'):self.ignored=max(0,self.ignored-1)
 def handle_data(self,d):
  if not self.ignored and d.strip():self.parts.append(d.strip())

def text_from(name:str,raw:bytes)->str:
 ext=Path(name).suffix.lower()
 if ext not in READABLE:return ''
 try: decoded=raw.decode('utf8')
 except UnicodeDecodeError:return ''
 if ext=='.html':
  p=TextOnly();p.feed(decoded);decoded=' '.join(p.parts)
 return decoded[:MAX_TEXT]

def terms(s:str)->list[str]:return re.findall(r'[a-z][a-z0-9_-]{2,}',s.lower())

def get_source_bytes(p:Path,root:Path|None=None)->bytes:
 if p.is_symlink():raise PermissionError('symlink sources not ingested')
 p=p.expanduser().resolve(strict=True)
 if root and not p.is_relative_to(root.expanduser().resolve(strict=True)):raise PermissionError('outside approved intake root')
 if not p.is_file():raise ValueError('not a regular file')
 relative_parts = p.relative_to(root.expanduser().resolve(strict=True)).parts if root else p.parts[-2:]
 if p.name.lower() in SKIP_NAMES or any(x.lower() in SKIP_PARTS for x in relative_parts[:-1]):raise PermissionError('protected path')
 if p.suffix.lower() not in READABLE|BIN_INDEX:raise ValueError('unsupported file type; use explicit metadata-only source record')
 if p.stat().st_size>MAX_BYTES:raise ValueError('source too large for bounded intake')
 return p.read_bytes()

class FamilyStore:
 def __init__(self,home:Path=DEFAULT_HOME):
  self.home=Path(home).expanduser();self.home.mkdir(mode=0o700,parents=True,exist_ok=True)
  if os.name!='nt': os.chmod(self.home,0o700)
  self.database=self.home/'family.sqlite3'
  self.db=sqlite3.connect(str(self.database),timeout=6,isolation_level=None)
  if os.name!='nt': os.chmod(self.database,0o600)
  self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA busy_timeout=5000')
  self.db.executescript('''
  CREATE TABLE IF NOT EXISTS source(sha TEXT PRIMARY KEY,length INTEGER NOT NULL,mime TEXT NOT NULL,rights TEXT NOT NULL,compressed BLOB,content_note TEXT NOT NULL,first_at TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS source_path(path TEXT PRIMARY KEY,sha TEXT NOT NULL,seen_at TEXT NOT NULL,FOREIGN KEY(sha) REFERENCES source(sha));
  CREATE TABLE IF NOT EXISTS source_occurrence(id INTEGER PRIMARY KEY AUTOINCREMENT,path TEXT NOT NULL,sha TEXT NOT NULL,rights TEXT NOT NULL,agent TEXT NOT NULL,observed_at TEXT NOT NULL,prior_sha TEXT,FOREIGN KEY(sha) REFERENCES source(sha));
  CREATE INDEX IF NOT EXISTS occurrence_path ON source_occurrence(path,id);
  CREATE TABLE IF NOT EXISTS source_terms(sha TEXT PRIMARY KEY,text TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS facet(id TEXT PRIMARY KEY,agent TEXT NOT NULL,parent_id TEXT,key TEXT NOT NULL,value_json TEXT NOT NULL,source_sha TEXT NOT NULL,classification TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS sessions(agent TEXT PRIMARY KEY,epoch INTEGER NOT NULL,heartbeat TEXT NOT NULL,state_json TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY,agent TEXT NOT NULL,kind TEXT NOT NULL,body TEXT NOT NULL,source_sha TEXT,status TEXT NOT NULL,created_at TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,stamp TEXT NOT NULL,agent TEXT NOT NULL,action TEXT NOT NULL,payload_sha TEXT NOT NULL,prior_hash TEXT NOT NULL,entry_hash TEXT NOT NULL);
  CREATE INDEX IF NOT EXISTS facet_src ON facet(source_sha);
  CREATE INDEX IF NOT EXISTS proposal_agent ON proposals(agent,status);
  ''')
  # Existing pre-admission databases are migrated in-place, without changing
  # the legacy byte table. Previously stored source rights are never elevated.
  cols={r[1] for r in self.db.execute('PRAGMA table_info(source_path)')}
  if 'rights' not in cols:self.db.execute("ALTER TABLE source_path ADD COLUMN rights TEXT NOT NULL DEFAULT 'owner-private'")
  if 'agent' not in cols:self.db.execute("ALTER TABLE source_path ADD COLUMN agent TEXT NOT NULL DEFAULT 'legacy-unverified'")
  self.db.execute('''INSERT INTO source_occurrence(path,sha,rights,agent,observed_at,prior_sha)
  SELECT p.path,p.sha,p.rights,'legacy-unverified',p.seen_at,NULL FROM source_path p
  WHERE NOT EXISTS (SELECT 1 FROM source_occurrence h WHERE h.path=p.path)''')
 def close(self):self.db.close()
 def _audit_in_transaction(self,agent:str,action:str,payload:dict)->dict:
  safe_name(agent);raw=digest(canonical(payload));stamp=timestamp()
  row=self.db.execute('SELECT entry_hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
  prev=row[0] if row else '0'*64
  h=digest(canonical([stamp,agent,action,raw,prev]))
  self.db.execute('INSERT INTO events(stamp,agent,action,payload_sha,prior_hash,entry_hash) VALUES(?,?,?,?,?,?)',(stamp,agent,action,raw,prev,h))
  seq=self.db.execute('SELECT last_insert_rowid()').fetchone()[0]
  return {'seq':seq,'hash':h,'signed':False}
 def audit(self,agent:str,action:str,payload:dict)->dict:
  self.db.execute('BEGIN IMMEDIATE')
  try:
   receipt=self._audit_in_transaction(agent,action,payload)
   self.db.execute('COMMIT')
   return receipt
  except Exception:self.db.execute('ROLLBACK');raise
 def verify_events(self)->dict:
  previous='0'*64;count=0
  for seq,stamp,agent,act,payload,prior,entry in self.db.execute('SELECT seq,stamp,agent,action,payload_sha,prior_hash,entry_hash FROM events ORDER BY seq'):
   expect=digest(canonical([stamp,agent,act,payload,previous]))
   if prior!=previous or expect!=entry:return {'ok':False,'failure_at':seq,'signed':False}
   previous=entry;count+=1
  return {'ok':True,'count':count,'last':previous,'signed':False}
 def ingest(self,agent:str,p:Path,*,root:Path|None=None,rights='owner-private',store_bytes=True)->dict:
  if agent not in ROLES:raise ValueError('unknown role')
  if rights not in ('owner-private','review-only','public-licence-verified'):raise ValueError('rights must be explicit')
  # Self-asserted public rights are not enough to publish a source. Native
  # rights evidence and the existing release gate must issue that promotion.
  if rights=='public-licence-verified':raise PermissionError('public rights require independent licence admission; review store cannot self-certify')
  original=Path(p).expanduser()
  before=original.stat(follow_symlinks=False)
  raw=get_source_bytes(original,root)
  after=original.stat(follow_symlinks=False)
  if (before.st_size,before.st_mtime_ns,before.st_ino,before.st_dev)!=(after.st_size,after.st_mtime_ns,after.st_ino,after.st_dev):
   raise RuntimeError('source changed during intake; retry after stabilising original')
  h=digest(raw);text=text_from(str(original),raw) if store_bytes else '';rel=str(original.resolve())
  ext=original.suffix.lower();blob=zlib.compress(raw,9) if store_bytes else None
  note='exact reversible content, NOT NTFS ACL/ADS recovery' if store_bytes else 'hash and metadata only; original bytes required'
  self.db.execute('BEGIN IMMEDIATE')
  try:
   current=self.db.execute('SELECT sha,rights FROM source_path WHERE path=?',(rel,)).fetchone()
   if current and current[1]!=rights:
    raise PermissionError('rights transition at same path needs independent approval; original occurrence retained')
   existing=self.db.execute('SELECT length,compressed FROM source WHERE sha=?',(h,)).fetchone()
   if existing and existing[0]!=len(raw):raise RuntimeError('stored source length conflicts with SHA identity')
   self.db.execute('INSERT OR IGNORE INTO source VALUES(?,?,?,?,?,?,?)',(h,len(raw),ext,rights,blob,note,timestamp()))
   if existing and existing[1] is None and blob is not None:
    self.db.execute('UPDATE source SET compressed=?,content_note=? WHERE sha=?',(blob,note,h))
    # Earlier metadata-only review omitted textual bytes deliberately.
    # Hydrating the same owner-approved SHA also hydrates its lexical index.
    self.db.execute('UPDATE source_terms SET text=? WHERE sha=?',(text,h))
   self.db.execute('INSERT OR IGNORE INTO source_terms VALUES(?,?)',(h,text))
   self.db.execute('INSERT INTO source_path(path,sha,seen_at,rights,agent) VALUES(?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET sha=excluded.sha,seen_at=excluded.seen_at',(rel,h,timestamp(),rights,agent))
   last=self.db.execute('SELECT sha,rights,agent FROM source_occurrence WHERE path=? ORDER BY id DESC LIMIT 1',(rel,)).fetchone()
   if last!=(h,rights,agent):
    self.db.execute('INSERT INTO source_occurrence(path,sha,rights,agent,observed_at,prior_sha) VALUES(?,?,?,?,?,?)',(rel,h,rights,agent,timestamp(),last[0] if last else None))
   receipt=self._audit_in_transaction(agent,'source-intake',{'sha':h,'size':len(raw),'type':ext,'rights':rights,'path':rel,'prior_sha':current[0] if current else None})
   self.db.execute('COMMIT')
  except Exception:
   self.db.execute('ROLLBACK');raise
  return {'sha256':h,'size':len(raw),'source':rel,'rights':rights,'reversible':store_bytes or (existing is not None and existing[1] is not None),'semantic_chars':len(text),'status':'INDEXED_REVIEW_NOT_CANONICAL','receipt':receipt}
 def restore(self,h:str,out:Path)->dict:
  if not re.fullmatch(r'[0-9a-f]{64}',h):raise ValueError('invalid sha')
  row=self.db.execute('SELECT length,compressed FROM source WHERE sha=?',(h,)).fetchone()
  if not row or row[1] is None:raise ValueError('not stored reversibly')
  if row[0]<0 or row[0]>MAX_BYTES:raise ValueError('source exceeds bounded byte recovery')
  decoder=zlib.decompressobj()
  raw=decoder.decompress(row[1],MAX_BYTES+1)
  if len(raw)>MAX_BYTES or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:
   raise ValueError('compressed source corrupt or exceeds bounded recovery')
  if len(raw)!=row[0] or digest(raw)!=h:raise ValueError('stored source content hash mismatch')
  out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
  # Never overwrite a real original, including after a previous partial restore.
  with out.open('xb') as f:f.write(raw)
  return {'restored':str(out),'sha256':h,'verified':True,'scope':'EXACT_BYTES_ONLY_NO_NTFS_ACL_ADS_OWNER'}
 def occurrences_for_agent(self,agent:str,h:str)->list[dict]:
  """Return source references explicitly observed by one specialist.

  A shell name is NOT an authenticated identity. This is a least-exposure
  review filter, subordinate to Windows ACLs and the native LOAD/lease layer.
  Older revisions remain visible to the agent that observed them. Imported
  legacy-unverified records grant no specialist access.
  """
  if agent not in ROLES:raise ValueError('unknown specialist role')
  return [{'path':p,'rights':r,'agent':agent} for p,r in self.db.execute(
   'SELECT DISTINCT path,rights FROM source_occurrence WHERE sha=? AND agent=? ORDER BY path,rights',(h,agent))]
 def restore_for_agent(self,agent:str,h:str,out:Path)->dict:
  """Role-filtered local CLI restoration; never a native authorisation."""
  if not self.occurrences_for_agent(agent,h):
   raise PermissionError('source not observed by this specialist; explicit native sharing required')
  return self.restore(h,out)
 def source_search(self,q:str,limit=8,*,agent:str|None=None)->list[dict]:
  """Owner review when unscoped; specialist CLI always passes its role."""
  if agent is not None and agent not in ROLES:raise ValueError('unknown specialist role')
  query=set(terms(q));results=[]
  for h,t,ln in self.db.execute('SELECT s.sha,st.text,s.length FROM source s JOIN source_terms st ON st.sha=s.sha'):
   if not t:continue
   tokens=set(terms(t));score=len(query&tokens)
   if score:
    start=min((t.lower().find(term) for term in query if term in t.lower()),default=0)
    occurrences=(self.occurrences_for_agent(agent,h) if agent is not None else
     [{'path':p,'rights':rights,'agent':owner} for p,rights,owner in self.db.execute(
      'SELECT DISTINCT path,rights,agent FROM source_occurrence WHERE sha=? ORDER BY path,rights,agent',(h,))])
    if not occurrences:continue
    rights_set={o['rights'] for o in occurrences}
    # No content-level rights promotion from deduplication. The only
    # permissible policy is the intersection of all attached occurrences.
    rights=list(rights_set)[0] if len(rights_set)==1 else 'MIXED_NONPUBLIC'
    results.append({'sha256':h,'path':occurrences[0]['path'],'rights':rights,'occurrences':occurrences,'size':ln,'score':score,'excerpt':t[max(0,start-100):start+350],'source_qualified':True,'public_share_authorised':False})
  return sorted(results,key=lambda x:(-x['score'],x['sha256']))[:max(1,min(25,int(limit)))]
 def propose(self,agent:str,kind:str,body:dict,source_sha:str|None=None)->dict:
  if agent not in ROLES or kind not in ('observation','hypothesis','correction','integration','training-example','approval-request','qualified-facet'):raise ValueError('unregistered role or kind')
  if len(canonical(body))>64*1024:raise ValueError('proposal exceeds budget')
  if kind in ('observation','qualified-facet','training-example') and not source_sha:raise ValueError('source-bound proposal required')
  if source_sha and not self.db.execute('SELECT 1 FROM source WHERE sha=?',(source_sha,)).fetchone():raise ValueError('unknown source sha')
  if source_sha and not self.occurrences_for_agent(agent,source_sha):
   raise PermissionError('specialist has no source occurrence; source-bound proposals require owner-reviewed sharing')
  pid=digest(canonical([agent,kind,body,source_sha]))
  # Proposal and unsigned event are one transaction; no orphaned learning
  # candidate may persist if event append or validation fails.
  self.db.execute('BEGIN IMMEDIATE')
  try:
   self.db.execute('INSERT OR IGNORE INTO proposals VALUES(?,?,?,?,?,?,?)',(pid,agent,kind,canonical(body).decode('utf8'),source_sha,'REVIEW_ONLY',timestamp()))
   self._audit_in_transaction(agent,'proposal-review',{'id':pid,'kind':kind,'source':source_sha})
   self.db.execute('COMMIT')
  except Exception:
   self.db.execute('ROLLBACK');raise
  return {'id':pid,'status':'REVIEW_ONLY','auto_promoted':False,'trained_model':False}
 def heartbeat(self,agent:str,state:dict|None=None)->dict:
  if agent not in ROLES:raise ValueError('unknown role')
  if state is None:state={}
  if len(canonical(state))>20*1024:raise ValueError('state too large')
  old=self.db.execute('SELECT epoch FROM sessions WHERE agent=?',(agent,)).fetchone();epoch=old[0]+1 if old else 1
  self.db.execute('INSERT INTO sessions VALUES(?,?,?,?) ON CONFLICT(agent) DO UPDATE SET epoch=excluded.epoch,heartbeat=excluded.heartbeat,state_json=excluded.state_json',(agent,epoch,timestamp(),canonical(state).decode()))
  return {'agent':agent,'epoch':epoch,'at':timestamp(),'mode':'REVIEW_PERSISTENCE_NOT_LOCAL_INFERENCE'}
 def status(self,agent:str|None=None)->dict:
  sessions={a:{'epoch':epoch,'last_heartbeat':stamp} for a,epoch,stamp in self.db.execute('SELECT agent,epoch,heartbeat FROM sessions')}
  counts={table:self.db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in ('source','source_path','source_occurrence','facet','proposals','events')}
  return {'schema':SCHEMA,'roles':list(ROLES) if agent is None else [agent],'db':str(self.database),'counts':counts,'sessions':sessions,'receipt_chain':self.verify_events(),'full_LOAD':'REQUIRED_EXTERNAL','local_model':'NOT VERIFIED','native_mint':'HOLD'}
 def list_proposals(self,agent:str|None=None):
  q='SELECT id,agent,kind,source_sha,status,created_at FROM proposals'+(' WHERE agent=?' if agent else '')+' ORDER BY created_at DESC LIMIT 40'
  return [{'id':r[0],'agent':r[1],'kind':r[2],'source_sha':r[3],'status':r[4],'at':r[5]} for r in self.db.execute(q,(agent,) if agent else ())]

def bounded_scan(root:Path)->list[Path]:
 root=Path(root).expanduser().resolve(strict=True)
 if not root.is_dir():raise ValueError('intake must be directory')
 found=[]
 for base,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=sorted(d for d in dirs if d.lower() not in SKIP_PARTS and not (Path(base)/d).is_symlink())
  for name in sorted(files):
   p=Path(base)/name
   if name.lower() in SKIP_NAMES or p.is_symlink() or p.suffix.lower() not in READABLE|BIN_INDEX:continue
   if p.stat().st_size<=MAX_BYTES:found.append(p)
   if len(found)>=MAX_SCAN:return found
 return found

def role_main(agent:str,argv=None):
 parser=argparse.ArgumentParser(prog=f'{agent}.cgx.py',description='Owner-controlled CGX specialist review persistence')
 parser.add_argument('--home',type=Path,default=DEFAULT_HOME,help='Private shared family state root')
 sub=parser.add_subparsers(dest='command',required=True)
 sub.add_parser('status');sub.add_parser('verify');sub.add_parser('proposals');sub.add_parser('capabilities')
 p=sub.add_parser('ingest');p.add_argument('path',type=Path);p.add_argument('--root',type=Path);p.add_argument('--rights',default='owner-private',choices=['owner-private','review-only','public-licence-verified']);p.add_argument('--metadata-only',action='store_true')
 p=sub.add_parser('restore');p.add_argument('sha');p.add_argument('output',type=Path)
 p=sub.add_parser('query');p.add_argument('text',nargs='+')
 p=sub.add_parser('propose');p.add_argument('kind',choices=['observation','hypothesis','correction','integration','training-example','approval-request','qualified-facet']);p.add_argument('json_file',type=Path);p.add_argument('--source-sha')
 p=sub.add_parser('run');p.add_argument('--once',action='store_true');p.add_argument('--interval',type=float,default=60);p.add_argument('--watch',type=Path,help='Explicit single owner-approved folder to re-index bounded files')
 args=parser.parse_args(argv)
 if args.command=='capabilities':
  manifest=Path(__file__).resolve().with_name('CGX_Capability_Registry.json')
  print(manifest.read_text(encoding='utf8'));return 0
 store=FamilyStore(args.home)
 try:
  if args.command=='status':out=store.status(agent)
  elif args.command=='verify':out=store.verify_events()
  elif args.command=='proposals':out=store.list_proposals(agent)
  elif args.command=='ingest':out=store.ingest(agent,args.path,root=args.root,rights=args.rights,store_bytes=not args.metadata_only)
  elif args.command=='restore':out=store.restore_for_agent(agent,args.sha,args.output)
  elif args.command=='query':out=store.source_search(' '.join(args.text),agent=agent)
  elif args.command=='propose':out=store.propose(agent,args.kind,json.loads(args.json_file.read_text('utf8')),args.source_sha)
  elif args.command=='run':
   if args.interval<15 or args.interval>3600:raise ValueError('interval must be between 15 and 3600s')
   def tick():
    indexed=0
    if args.watch:
     root=args.watch.resolve(strict=True)
     for file in bounded_scan(root):
      try:
       data=get_source_bytes(file,root);h=digest(data)
       old=store.db.execute('SELECT sha FROM source_path WHERE path=?',(str(file.resolve()),)).fetchone()
       if not old or old[0]!=h:store.ingest(agent,file,root=root);indexed+=1
      except (OSError,PermissionError,ValueError):pass
    return {'beat':store.heartbeat(agent,{'watch':str(args.watch) if args.watch else None,'new_sources':indexed}),'new_sources':indexed}
   if args.once:out=tick()
   else:
    print(json.dumps({'agent':agent,'status':'running in foreground','pid':os.getpid(),'auto_native_mint':False}),flush=True)
    try:
     while True:print(json.dumps(tick()),flush=True);time.sleep(args.interval)
    except KeyboardInterrupt:return 0
  else:raise ValueError('unknown command')
  print(json.dumps(out,indent=2,ensure_ascii=False));return 0
 finally:store.close()

if __name__=='__main__':
 raise SystemExit('Call role-specific .cgx.py shell')
