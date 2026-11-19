#!/usr/bin/env python3
"""Metadata-only privacy and atomic review-proposal contract.

Tests only an isolated owner-review SQLite store, never native LOAD/leases,
remote inference, model weight changes, Windows ACLs or peer signature.
"""
import json,tempfile
from pathlib import Path
from CGX_Persistence_Core import FamilyStore
passed=[]
def check(label,condition):
 if not condition:raise AssertionError(label)
 passed.append(label)
def denies(label,call,exc):
 try:call()
 except exc:passed.append(label);return
 raise AssertionError(label+': expected failure')
with tempfile.TemporaryDirectory(prefix='cgx-meta-atomic-') as folder:
 r=Path(folder);root=r/'inputs';root.mkdir();src=root/'a.md';src.write_text('Confidential thermal singularity source data.','utf8')
 db=FamilyStore(r/'cache')
 m=db.ingest('Raphael',src,root=root,store_bytes=False)
 check('metadata records exact SHA',m['sha256'] and len(m['sha256'])==64)
 check('metadata has no exact byte blob',m['reversible'] is False)
 check('metadata has no indexed excerpt',m['semantic_chars']==0)
 check('metadata search returns no plaintext',not db.source_search('Confidential thermal',agent='Raphael'))
 check('metadata underlying index is blank',db.db.execute('SELECT text FROM source_terms WHERE sha=?',(m['sha256'],)).fetchone()==('',))
 denies('metadata cannot restore source',lambda:db.restore_for_agent('Raphael',m['sha256'],r/'restore.txt'),(ValueError,PermissionError))
 check('denied restore creates no file',not (r/'restore.txt').exists())
 full=db.ingest('Raphael',src,root=root,store_bytes=True)
 check('hydration preserves same identity',m['sha256']==full['sha256'])
 check('source entry deduplicated',db.status()['counts']['source']==1)
 check('full intake indexes searchable text',len(db.source_search('Confidential thermal',agent='Raphael'))==1)
 check('full intake yields exact bytes',db.restore_for_agent('Raphael',full['sha256'],Path('restore.txt'))['verified'] and (db.home/'restores'/'Raphael'/'restore.txt').read_bytes()==src.read_bytes())
 check('other role cannot see source',not db.source_search('Confidential',agent='Neo'))
 before=(db.status()['counts']['proposals'],db.status()['counts']['events'])
 orig=db._audit_in_transaction
 def bad(*args,**kwargs):raise RuntimeError('synthetic receipt fail')
 db._audit_in_transaction=bad
 try:denies('proposal receipt failure propagates',lambda:db.propose('Raphael','observation',{'note':'receipt consistency'},full['sha256']),RuntimeError)
 finally:db._audit_in_transaction=orig
 after=(db.status()['counts']['proposals'],db.status()['counts']['events'])
 check('failed proposal atomic rollback',after==before)
 check('failed receipt does not corrupt chain',db.verify_events()['ok'])
 x=db.propose('Raphael','observation',{'note':'receipt consistency'},full['sha256'])
 check('accepted proposal is not model training',x['status']=='REVIEW_ONLY' and not x['trained_model'])
 check('proposal plus event committed',db.status()['counts']['proposals']==before[0]+1 and db.status()['counts']['events']==before[1]+1)
 check('review receipt chain remains unsigned',db.verify_events()['signed'] is False)
 db.close()

# A deterministic regression for the former unbounded read_bytes() path.
# All data are synthetic and stay inside the isolated test directory.
from unittest.mock import patch
from CGX_Persistence_Core import get_source_bytes,MAX_BYTES,digest
with tempfile.TemporaryDirectory(prefix='cgx-bounded-r0-') as folder:
 r=Path(folder);small=r/'stable.txt';small.write_bytes(b'bounded original source')
 with patch.object(Path,'read_bytes',side_effect=AssertionError('unbounded Path.read_bytes forbidden')):
  raw=get_source_bytes(small,r)
 check('R0 uses descriptor-bounded read, not Path.read_bytes',raw==b'bounded original source')
 check('bounded read retains exact SHA256',digest(raw)==digest(b'bounded original source'))
 at_limit=r/'limit.txt';at_limit.write_bytes(b'x'*MAX_BYTES)
 check('exact intake limit permitted',len(get_source_bytes(at_limit,r))==MAX_BYTES)
 over_limit=r/'over.txt'
 with over_limit.open('wb') as f:f.truncate(MAX_BYTES+1)
 denies('oversized original rejected before ingestion',lambda:get_source_bytes(over_limit,r),ValueError)
 check('original over-budget data retained',over_limit.stat().st_size==MAX_BYTES+1)
 alt=r/'outside.txt';alt.write_text('outside original','utf8')
 other=r/'sub';other.mkdir()
 denies('source outside explicit intake root denied',lambda:get_source_bytes(alt,other),PermissionError)
 link=r/'alias.txt'
 try:link.symlink_to(small)
 except (OSError,NotImplementedError):pass
 else:denies('symlink source rejected',lambda:get_source_bytes(link,r),PermissionError)

print(json.dumps({'passed':len(passed),'checks':passed,'native_admitted':False,'host_modified':False},indent=2))
