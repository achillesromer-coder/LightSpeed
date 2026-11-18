#!/usr/bin/env python3
"""Isolated role-scoped *review* exposure tests (not native ACL or signed identity)."""
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
from CGX_Persistence_Core import FamilyStore
HERE=Path(__file__).resolve().parent
passed=[]
def ok(name,condition):
 if not condition:raise AssertionError(name)
 passed.append(name)
def deny(name,fn,cls=PermissionError):
 try:fn()
 except cls:passed.append(name);return
 raise AssertionError(f'{name}: should fail closed')
with tempfile.TemporaryDirectory(prefix='cgx-role-scope-') as d:
 root=Path(d);home=root/'cache';src=root/'source';src.mkdir()
 rap=src/'raphael.md';rap.write_text('Raphael private physics test source',encoding='utf8')
 neo=src/'neo.md';neo.write_text('Neo private runtime ABI test source',encoding='utf8')
 same=src/'athene.md';same.write_bytes(rap.read_bytes())
 store=FamilyStore(home)
 a=store.ingest('Raphael',rap,root=src)
 n=store.ingest('Neo',neo,root=src)
 ok('Raphael own query',len(store.source_search('physics',agent='Raphael'))==1)
 ok('Raphael cannot enumerate Neo content',store.source_search('runtime',agent='Raphael')==[])
 ok('Neo cannot enumerate Raphael content',store.source_search('physics',agent='Neo')==[])
 ok('Athene cannot enumerate unobserved source',store.source_search('physics',agent='Athene')==[])
 try:store.source_search('physics',agent='unregistered')
 except ValueError:passed.append('unknown specialist query rejected')
 else:raise AssertionError('unregistered query passed')
 deny('Neo cannot restore Raphael SHA',lambda:store.restore_for_agent('Neo',a['sha256'],root/'bad.out'))
 ok('unauthorised restore creates no file',not (root/'bad.out').exists())
 deny('Athene cannot cite unobserved Raphael source',lambda:store.propose('Athene','observation',{'claim':'private source'},a['sha256']))
 ok('Raphael own sourced observation allowed',store.propose('Raphael','observation',{'claim':'review only'},a['sha256'])['status']=='REVIEW_ONLY')
 o=store.ingest('Athene',same,root=src,rights='review-only')
 ok('dedup byte shared across two sources',o['sha256']==a['sha256'] and store.status()['counts']['source']==2)
 x=store.source_search('physics',agent='Athene')
 ok('Athene sees only its own occurrence',len(x)==1 and len(x[0]['occurrences'])==1 and x[0]['occurrences'][0]['path']==str(same))
 x=store.source_search('physics',agent='Raphael')
 ok('Raphael sees only its own occurrence',len(x)==1 and len(x[0]['occurrences'])==1 and x[0]['occurrences'][0]['path']==str(rap))
 ok('different agent keeps distinct rights',x[0]['rights']=='owner-private' and store.source_search('physics',agent='Athene')[0]['rights']=='review-only')
 ok('Athene can restore observed same bytes',store.restore_for_agent('Athene',a['sha256'],Path('restored.out'))['verified'] and (home/'restores'/'Athene'/'restored.out').read_bytes()==rap.read_bytes())
 # History survives a same-path revision and still belongs to the observing role.
 rap.write_text('Raphael updated quantum physics test source',encoding='utf8')
 newer=store.ingest('Raphael',rap,root=src)
 ok('old source observed by Raphael',bool(store.occurrences_for_agent('Raphael',a['sha256'])))
 ok('new source observed by Raphael',bool(store.occurrences_for_agent('Raphael',newer['sha256'])))
 ok('Athene not granted revised source',store.source_search('quantum',agent='Athene')==[])
 deny('Neo denied old revision',lambda:store.restore_for_agent('Neo',a['sha256'],root/'neo-old.out'))
 ok('no legacy cross-agent listing',all(o['agent']=='Raphael' for o in store.occurrences_for_agent('Raphael',newer['sha256'])))
 store.close()
 # Confirm role-scoped exposure is wired to the actual CLI, not just an unused helper.
 def run(role,cmd,*args):
  return subprocess.run([sys.executable,str(HERE/f'{role}.cgx.py'),'--home',str(home),cmd,*args],capture_output=True,text=True,timeout=8)
 p=run('Neo','query','quantum')
 ok('Neo CLI own-only query',p.returncode==0 and json.loads(p.stdout)==[])
 p=run('Raphael','query','quantum')
 ok('Raphael CLI own query',p.returncode==0 and len(json.loads(p.stdout))==1)
 p=run('Neo','restore',newer['sha256'],str(root/'unsafe.out'))
 ok('Neo CLI forbidden restoration',p.returncode!=0 and not (root/'unsafe.out').exists())
 p=run('Raphael','restore',newer['sha256'],'good.out')
 ok('Raphael CLI own restore',p.returncode==0 and (home/'restores'/'Raphael'/'good.out').read_bytes()==rap.read_bytes())
print(json.dumps({'passed':len(passed),'checks':passed,'scope':'local role-labelled review only','native_acl_verified':False,'issuer_verified':False},indent=2))
