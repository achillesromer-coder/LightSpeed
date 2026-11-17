#!/usr/bin/env python3
"""Fail-closed review-level content grants; metadata hashes never imply content access.

No OS identity, native lease, model weights or network authority is validated here.
"""
import json,sqlite3,tempfile
from pathlib import Path
from CGX_Persistence_Core import FamilyStore

checks=[]
def ok(label,value):
 if not value:raise AssertionError(label)
 checks.append(label)
def denied(label,fn):
 try:fn()
 except PermissionError:checks.append(label);return
 raise AssertionError(label+': not denied')

with tempfile.TemporaryDirectory(prefix='cgx-content-grant-') as directory:
 root=Path(directory);inputs=root/'input';inputs.mkdir()
 a=inputs/'raphael.md'; b=inputs/'neo.md'; c=inputs/'athene.md'
 original=b'Unpublished Raphael coherence experiment and measured audit.\n'
 for p in (a,b,c):p.write_bytes(original)
 store=FamilyStore(root/'state')
 ra=store.ingest('Raphael',a,root=inputs)
 ne=store.ingest('Neo',b,root=inputs,store_bytes=False)
 ok('same bytes remain deduplicated',ra['sha256']==ne['sha256'] and store.status()['counts']['source']==1)
 ok('metadata Neo occurrence exists',len(store.occurrences_for_agent('Neo',ne['sha256']))==1)
 ok('metadata Neo content grant absent',not store.occurrences_for_agent('Neo',ne['sha256'],content_only=True))
 ok('metadata Neo search denied despite global lexical index',store.source_search('coherence experiment',agent='Neo')==[])
 denied('metadata Neo restore denied despite global blob',lambda:store.restore_for_agent('Neo',ne['sha256'],root/'stolen.md'))
 ok('metadata denied output never created',not (root/'stolen.md').exists())
 denied('metadata Neo scientific proposal denied',lambda:store.propose('Neo','observation',{'claim':'read secret'},ne['sha256']))
 ok('Raphael full source remains searchable',len(store.source_search('coherence experiment',agent='Raphael'))==1)
 # Even repeated metadata observations cannot launder a full source grant.
 cnt=store.status()['counts']['source_occurrence']
 store.ingest('Neo',b,root=inputs,store_bytes=False)
 ok('repeated metadata occurrence idempotent',store.status()['counts']['source_occurrence']==cnt)
 ok('repeated metadata does not upgrade access',store.source_search('coherence',agent='Neo')==[])
 store.close();store=FamilyStore(root/'state')
 ok('restart keeps metadata access denied',store.source_search('coherence',agent='Neo')==[])
 ok('old full source still searchable after restart',len(store.source_search('coherence',agent='Raphael'))==1)
 full=store.ingest('Neo',b,root=inputs,store_bytes=True)
 ok('explicit full intake grants role-level content access',full['content_granted'] and len(store.occurrences_for_agent('Neo',full['sha256'],content_only=True))==1)
 ok('metadata-to-full upgrade retains source sha',full['sha256']==ra['sha256'])
 ok('metadata-to-full upgrade keeps occurrence history length',store.status()['counts']['source_occurrence']==cnt)
 ok('new content grant enables scoped retrieval',len(store.source_search('coherence',agent='Neo'))==1)
 ok('new content grant enables reversible restore',store.restore_for_agent('Neo',ra['sha256'],root/'neo-restored.md')['verified'] and (root/'neo-restored.md').read_bytes()==original)
 ok('new content grant enables proposed review only',store.propose('Neo','observation',{'claim':'review'},ra['sha256'])['status']=='REVIEW_ONLY')
 store.ingest('Athene',c,root=inputs,store_bytes=False)
 ok('Athene metadata alone is not a grant',store.source_search('coherence',agent='Athene')==[])
 denied('Athene restore denied',lambda:store.restore_for_agent('Athene',ra['sha256'],root/'athene-stolen.md'))
 # Existing full grants are not silently revoked by a metadata-only receipt.
 store.ingest('Neo',b,root=inputs,store_bytes=False)
 ok('metadata receipt does not revoke an existing full grant',len(store.source_search('coherence',agent='Neo'))==1)
 ok('content grants are explicitly recorded per occurrence',store.db.execute('SELECT content_granted FROM source_occurrence WHERE path=? AND agent=?',(str(b),'Neo')).fetchone()==(1,))
 ok('audit chain remains valid',store.verify_events()['ok'])
 store.close()

 # Simulate a pre-grant schema with a full blob and a previously unqualified
 # occurrence. A re-open must fail CLOSED rather than infer full access.
 home=root/'legacy';p=inputs/'old.md';p.write_bytes(b'Legacy private source experimental model.')
 old=FamilyStore(home); legacy=old.ingest('Raphael',p,root=inputs)
 old.close()
 cx=sqlite3.connect(home/'family.sqlite3')
 try:
  cx.execute('ALTER TABLE source_occurrence DROP COLUMN content_granted')
  cx.commit()
 finally:cx.close()
 upgraded=FamilyStore(home)
 ok('legacy schema gains bounded content grant column',any(x[1]=='content_granted' for x in upgraded.db.execute('PRAGMA table_info(source_occurrence)')))
 ok('legacy unqualified occurrence defaults to denial',upgraded.occurrences_for_agent('Raphael',legacy['sha256'],content_only=True)==[])
 ok('legacy lexical index not exposed by role query',upgraded.source_search('experimental model',agent='Raphael')==[])
 denied('legacy blob not retrievable by role without re-intake',lambda:upgraded.restore_for_agent('Raphael',legacy['sha256'],root/'legacy-stolen.md'))
 fresh=upgraded.ingest('Raphael',p,root=inputs)
 ok('explicit owner full re-intake unlocks without new content record',fresh['sha256']==legacy['sha256'] and upgraded.status()['counts']['source']==1)
 ok('upgraded legacy role can query after re-intake',len(upgraded.source_search('experimental model',agent='Raphael'))==1)
 upgraded.close()

print(json.dumps({'passed':len(checks),'checks':checks,'source_review_only':True,'native_acl_or_issuer_verified':False},indent=2))
