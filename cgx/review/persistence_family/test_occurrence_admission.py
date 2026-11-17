#!/usr/bin/env python3
"""Negative rights, migration, recovery and native source-ABI preflight suite."""
import hashlib,json,sqlite3,subprocess,tempfile,zlib
from datetime import datetime,timedelta,timezone
from pathlib import Path
from CGX_Family_Supervisor import CoordinatorLock
from CGX_Persistence_Core import FamilyStore
from CGX_Native_ABI_Preflight import git_blob,inspect_sources,inspect_lease_structure,BLOB_PINS
checks=[]
def ok(name,val):
 if not val:raise AssertionError(name)
 checks.append(name)
def fails(name,fn,exc=Exception):
 try:fn()
 except exc:checks.append(name);return
 raise AssertionError(name+' did not fail')
with tempfile.TemporaryDirectory(prefix='cgx-abi-review-') as d:
 root=Path(d);src=root/'source';src.mkdir();home=root/'state';a=src/'a.md';b=src/'b.md';a.write_text('A source-bearing physics observation.','utf8');b.write_bytes(a.read_bytes())
 db=FamilyStore(home);p=db.ingest('Raphael',a,root=src);q=db.ingest('Athene',b,root=src,rights='review-only')
 ok('identical payload only stored once',db.status()['counts']['source']==1)
 ok('independent path occurrences retained',db.status()['counts']['source_path']==2 and db.status()['counts']['source_occurrence']==2)
 x=db.source_search('physics observation')[0]
 ok('mixed occurrence rights fail closed',x['rights']=='MIXED_NONPUBLIC' and not x['public_share_authorised'])
 ok('exact occurrence provenance',set((x['path'],x['rights']) for x in x['occurrences'])=={(str(a),'owner-private'),(str(b),'review-only')})
 fails('public rights self-certification rejected',lambda:db.ingest('Achilles',a,root=src,rights='public-licence-verified'),PermissionError)
 fails('same path silent rights escalation rejected',lambda:db.ingest('Raphael',a,root=src,rights='review-only'),PermissionError)
 old=a.read_bytes();a.write_text('A newly revised physics observation.','utf8');r=db.ingest('Raphael',a,root=src)
 ok('superseded source preserved',r['sha256']!=p['sha256'] and db.status()['counts']['source']==2)
 hist=db.db.execute('SELECT sha,prior_sha FROM source_occurrence WHERE path=? ORDER BY id',(str(a),)).fetchall()
 ok('occurrence history survives revision',hist==[(p['sha256'],None),(r['sha256'],p['sha256'])])
 ok('old occurrence hash still restorable',db.restore(p['sha256'],root/'old.md')['sha256']==p['sha256'] and (root/'old.md').read_bytes()==old)
 ok('source rights metadata not promoted by dedup',all(not x['public_share_authorised'] for x in db.source_search('physics observation')) and next(x for x in db.source_search('physics observation') if x['sha256']==p['sha256'])['rights']=='review-only')
 ok('audit chain follows transactional ingestion',db.verify_events()['ok'])
 db.close();db=FamilyStore(home)
 ok('restart preserves history',db.status()['counts']['source_occurrence']==3)
 ok('restart preserves audit chain',db.verify_events()['ok'])
 h=p['sha256'];compressed=bytearray(db.db.execute('SELECT compressed FROM source WHERE sha=?',(h,)).fetchone()[0]);compressed[-2]^=1;db.db.execute('UPDATE source SET compressed=? WHERE sha=?',(bytes(compressed),h))
 fails('corrupted compressed source blocked',lambda:db.restore(h,root/'corrupt.md'),Exception)
 ok('corrupt restore does not create output',not (root/'corrupt.md').exists())
 db.close()
 # Legacy review cache upgrade keeps raw bytes and labels restricted.
 legacy=root/'legacy';legacy.mkdir();cx=sqlite3.connect(legacy/'family.sqlite3')
 cx.executescript("""CREATE TABLE source(sha TEXT PRIMARY KEY,length INTEGER,mime TEXT,rights TEXT,compressed BLOB,content_note TEXT,first_at TEXT);
 CREATE TABLE source_path(path TEXT PRIMARY KEY,sha TEXT,seen_at TEXT);
 CREATE TABLE source_terms(sha TEXT PRIMARY KEY,text TEXT);
 CREATE TABLE facet(id TEXT PRIMARY KEY,agent TEXT,parent_id TEXT,key TEXT,value_json TEXT,source_sha TEXT,classification TEXT,status TEXT,created_at TEXT);
 CREATE TABLE sessions(agent TEXT PRIMARY KEY,epoch INTEGER,heartbeat TEXT,state_json TEXT);
 CREATE TABLE proposals(id TEXT PRIMARY KEY,agent TEXT,kind TEXT,body TEXT,source_sha TEXT,status TEXT,created_at TEXT);
 CREATE TABLE events(seq INTEGER PRIMARY KEY AUTOINCREMENT,stamp TEXT,agent TEXT,action TEXT,payload_sha TEXT,prior_hash TEXT,entry_hash TEXT);""")
 prior=b'legacy test source';sha=hashlib.sha256(prior).hexdigest()
 cx.execute('INSERT INTO source VALUES(?,?,?,?,?,?,?)',(sha,len(prior),'.txt','review-only',zlib.compress(prior),'legacy','2026-11-01T00:00:00Z'))
 cx.execute('INSERT INTO source_path VALUES(?,?,?)',('/historical/source.txt',sha,'2026-11-01T00:00:00Z'))
 cx.execute('INSERT INTO source_terms VALUES(?,?)',(sha,prior.decode()))
 cx.commit();cx.close();old_db=FamilyStore(legacy)
 ok('legacy table migrates losslessly',old_db.status()['counts']['source']==1 and old_db.status()['counts']['source_occurrence']==1)
 occ=old_db.db.execute('SELECT rights,agent FROM source_occurrence LIMIT 1').fetchone()
 ok('legacy role unverified and nonpublic',occ==('owner-private','legacy-unverified'))
 ok('legacy byte recovery retained',old_db.restore(sha,root/'legacy.out')['verified'] and (root/'legacy.out').read_bytes()==prior)
 # Ingestion and receipt share one transaction: a receipt failure rolls back all source state.
 fresh=src/'rollback.md';fresh.write_text('rollback gated', 'utf8')
 original_audit=old_db._audit_in_transaction
 def fail_audit(*args):raise RuntimeError('synthetic receipt failure')
 old_db._audit_in_transaction=fail_audit
 try: fails('receipt failure propagates',lambda:old_db.ingest('Neo',fresh,root=src),RuntimeError)
 finally:old_db._audit_in_transaction=original_audit
 ok('receipt failure leaves no partial source',old_db.status()['counts']['source']==1 and old_db.status()['counts']['source_path']==1)
 ok('legacy event chain remains valid',old_db.verify_events()['ok'])
 old_db.close()
 # A second review coordinator cannot concurrently mutate the local review set.
 supervisor=Path(__file__).resolve().parent/'CGX_Family_Supervisor.py'
 with CoordinatorLock(legacy):
  proc=subprocess.run(['python',str(supervisor),'once','--home',str(legacy)],capture_output=True,text=True,timeout=10)
  ok('concurrent coordinator blocked',proc.returncode!=0 and 'already running' in proc.stderr)
 proc=subprocess.run(['python',str(supervisor),'once','--home',str(legacy),'--watch',str(src),'--max-updates','0'],capture_output=True,text=True,timeout=10)
 ok('zero-intake budget respected',proc.returncode==0 and not json.loads(proc.stdout)['new_sources'])
 check=FamilyStore(legacy)
 ok('zero-intake did not mutate source cache',check.status()['counts']['source']==1)
 check.close()
 # Read-only host-source review never dispatches even if mock source pins match.
 repo=root/'repo';repo.mkdir();subprocess.run(['git','init','-q',str(repo)],check=True)
 for path in BLOB_PINS:
  fn=repo/path;fn.parent.mkdir(parents=True,exist_ok=True)
  if path.endswith('operator.py'):v=b'class AchillesOperator:\n def retrieve(self):pass\n def propose_action(self):pass\n def approve_action(self):pass\n def reject_action(self):pass\n'
  elif path.endswith('node_exchange.py'):v=b''.join(('def '+name+'():pass\n').encode() for name in ('build_transfer_envelope','execute_local_transfer','build_compute_request','execute_local_compute','resolve_node_root'))
  else:v=json.dumps({'required_fields':list(__import__('CGX_Native_ABI_Preflight').LEASE_FIELDS),'invariants':['missing-or-stale-lease-means-no-consequential-execution']}).encode()
  fn.write_bytes(v)
 subprocess.run(['git','-C',str(repo),'add','.'],check=True)
 subprocess.run(['git','-C',str(repo),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],check=True)
 head=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
 pins={path:git_blob((repo/path).read_bytes()) for path in BLOB_PINS}
 z=inspect_sources(repo,expected_head=head,expected_blobs=pins)
 ok('fixture ABI source parity',z['source_parity'])
 ok('positive source parity never grants execution',not z['dispatch_allowed'] and z['authority']=='HOLD')
 (repo/'desktop/LightSpeed_Runtime/lightspeed_runtime/achilles/operator.py').write_text('# tampered','utf8')
 z=inspect_sources(repo,expected_head=head,expected_blobs=pins)
 ok('modified operator denied',not z['source_parity'] and not z['dispatch_allowed'])
 z=inspect_sources(repo,expected_head='a'*40,expected_blobs=pins)
 ok('stale head denied',not z['source_parity'])
 now=datetime(2026,11,17,10,0,tzinfo=timezone.utc)
 sample={'lease_id':'x','lease_class':'READ_ONLY','state':'ACTIVE','issued_by':'Independent','subject_agent':'Raphael','valid_from':(now-timedelta(hours=1)).isoformat(),'valid_until':(now+timedelta(hours=1)).isoformat(),'domains':['geometry'],'execution_depths':['review'],'scope':{},'revocable':True,'authority_phase':'PRE_LAUNCH','authority_phase_ref':'source-claim'}
 inspect=lambda obj:inspect_lease_structure(obj,subject='Raphael',now_iso=now.isoformat())
 ok('no lease denied',not inspect(None)['dispatch_allowed'] and 'no lease' in inspect(None)['reasons'])
 ok('revoked lease denied',not inspect({**sample,'state':'REVOKED'})['structurally_eligible_for_independent_check'])
 ok('wrong role denied',not inspect({**sample,'subject_agent':'Neo'})['structurally_eligible_for_independent_check'])
 ok('expired lease denied',not inspect({**sample,'valid_until':(now-timedelta(seconds=1)).isoformat()})['structurally_eligible_for_independent_check'])
 ok('self-issued lease denied',not inspect({**sample,'issued_by':'Raphael'})['structurally_eligible_for_independent_check'])
 ok('nonrevocable lease denied',not inspect({**sample,'revocable':False})['structurally_eligible_for_independent_check'])
 ok('missing scope denied',not inspect({k:v for k,v in sample.items() if k!='scope'})['structurally_eligible_for_independent_check'])
 ok('structural lease never enough for execution',inspect(sample)['structurally_eligible_for_independent_check'] and not inspect(sample)['issuer_authenticated'] and not inspect(sample)['dispatch_allowed'])
print(json.dumps({'checks':len(checks),'passed':checks,'source_only':True,'host_mutated':False,'native_execution':False},indent=2))
