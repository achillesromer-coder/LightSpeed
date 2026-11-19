#!/usr/bin/env python3
"""Review-only restore-path confinement, symlink and original-preservation negatives."""
import hashlib,json,os,tempfile
from pathlib import Path
from CGX_Persistence_Core import FamilyStore
checks=[]
def ok(label,condition):
 if not condition:raise AssertionError(label)
 checks.append(label)
def deny(label,fn):
 try:fn()
 except (PermissionError,FileExistsError,ValueError):checks.append(label);return
 raise AssertionError(label+' did not fail closed')
with tempfile.TemporaryDirectory(prefix='cgx-restore-boundary-') as td:
 root=Path(td);src=root/'source';src.mkdir();data=b'Role-isolated restore source.\n'
 a=src/'a.md';a.write_bytes(data)
 state=root/'state';st=FamilyStore(state)
 h=st.ingest('Raphael',a,root=src)['sha256']
 ok('review original sha retained',h==hashlib.sha256(data).hexdigest())
 ok('scoped relative restore succeeds',st.restore_for_agent('Raphael',h,Path('nested/ok.md'))['verified'])
 recovered=state/'restores'/'Raphael'/'nested'/'ok.md'
 ok('role-scoped destination is confined',recovered.read_bytes()==data)
 ok('source original untouched',a.read_bytes()==data)
 deny('absolute destination rejected',lambda:st.restore_for_agent('Raphael',h,root/'outside.md'))
 deny('parent traversal rejected',lambda:st.restore_for_agent('Raphael',h,Path('../outside.md')))
 deny('nested traversal rejected',lambda:st.restore_for_agent('Raphael',h,Path('nested/../../outside.md')))
 deny('Windows drive/ADS rejected',lambda:st.restore_for_agent('Raphael',h,Path('C:\\Windows\\temp.txt')))
 deny('Windows backslash separator rejected',lambda:st.restore_for_agent('Raphael',h,Path('nested\\escape.md')))
 deny('protected secrets name rejected',lambda:st.restore_for_agent('Raphael',h,Path('.env')))
 deny('Windows reserved name rejected',lambda:st.restore_for_agent('Raphael',h,Path('CON.txt')))
 deny('existing output never overwritten',lambda:st.restore_for_agent('Raphael',h,Path('nested/ok.md')))
 ok('previous recovery remains exact',recovered.read_bytes()==data)
 deny('other specialist without grant denied',lambda:st.restore_for_agent('Neo',h,Path('denied.md')))
 ok('cross-role restore path not created',not (state/'restores'/'Neo'/'denied.md').exists())
 if hasattr(os,'symlink'):
  outside=root/'outside';outside.mkdir()
  link=state/'restores'/'Raphael'/'link'
  try:
   link.symlink_to(outside,target_is_directory=True)
  except (OSError,NotImplementedError):pass
  else:
   deny('symlinked intermediate directory rejected',lambda:st.restore_for_agent('Raphael',h,Path('link/escape.md')))
   ok('symlink cannot write outside',not (outside/'escape.md').exists())
   target=state/'restores'/'Raphael'/'target.md'
   target.symlink_to(outside/'target.md')
   deny('symlink target rejected',lambda:st.restore_for_agent('Raphael',h,Path('target.md')))
   ok('symlink target remains untouched',not (outside/'target.md').exists())
 st.close();st=FamilyStore(state)
 ok('restart retains stored sha',st.db.execute('SELECT sha FROM source WHERE sha=?',(h,)).fetchone()[0]==h)
 ok('restart still confines new recovery',st.restore_for_agent('Raphael',h,Path('after-restart.md'))['verified'])
 ok('restart confined output exact',(state/'restores'/'Raphael'/'after-restart.md').read_bytes()==data)
 ok('unsigned review audit remains valid',st.verify_events()['ok'] and not st.verify_events()['signed'])
 st.close()
print(json.dumps({'passed':len(checks),'checks':checks,'scope':'review-only','host_acl_verified':False,'native_admitted':False},indent=2))
