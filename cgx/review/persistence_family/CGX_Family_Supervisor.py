#!/usr/bin/env python3
"""Single coordinated foreground runtime for four specialist CGX review shells.
No service installation, background scheduler, model training or auto-promotion.
"""
from __future__ import annotations
import argparse,json,time,os
from pathlib import Path
from CGX_Persistence_Core import FamilyStore,ROLES,bounded_scan,get_source_bytes,digest,DEFAULT_HOME

class CoordinatorLock:
 """Local review-only OS file lock. Automatically released on process exit.
 Not a signed lease, native host singleton, or distributed authority grant.
 """
 def __init__(self,home:Path):self.path=Path(home).expanduser()/'.coordinator.lock';self.file=None
 def __enter__(self):
  self.path.parent.mkdir(parents=True,exist_ok=True)
  self.file=self.path.open('a+b')
  try:
   self.file.seek(0,os.SEEK_END)
   if self.file.tell()==0:self.file.write(b'0');self.file.flush()
   self.file.seek(0)
   if os.name=='nt':
    import msvcrt
    msvcrt.locking(self.file.fileno(),msvcrt.LK_NBLCK,1)
   else:
    import fcntl
    fcntl.flock(self.file.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  except (BlockingIOError,OSError) as exc:
   self.file.close();self.file=None
   raise RuntimeError('a local CGX review coordinator is already running') from exc
  return self
 def __exit__(self,exc_type,exc,tb):
  if self.file:
   self.file.seek(0)
   if os.name=='nt':
    import msvcrt
    msvcrt.locking(self.file.fileno(),msvcrt.LK_UNLCK,1)
   else:
    import fcntl
    fcntl.flock(self.file.fileno(),fcntl.LOCK_UN)
   self.file.close();self.file=None

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['once','run','status'])
 p.add_argument('--home',type=Path,default=DEFAULT_HOME)
 p.add_argument('--watch',type=Path,default=None,help='Explicit trusted source folder; never recurses across PC by default')
 p.add_argument('--interval',type=float,default=120);p.add_argument('--max-updates',type=int,default=32)
 a=p.parse_args(argv)
 if a.interval<30 or a.interval>3600:raise SystemExit('interval range 30..3600 seconds')
 if not 0<=a.max_updates<=128:raise SystemExit('max-updates range 0..128')
 store=FamilyStore(a.home);known={}
 def cycle():
  added=[]
  if a.watch and a.max_updates>0:
   root=a.watch.expanduser().resolve(strict=True)
   for path in bounded_scan(root):
    try:
     stat=path.stat();finger=(stat.st_mtime_ns,stat.st_size)
     if known.get(str(path))==finger:continue
     raw=get_source_bytes(path,root);h=digest(raw)
     prev=store.db.execute('SELECT sha FROM source_path WHERE path=?',(str(path.resolve()),)).fetchone()
     if prev and prev[0]==h:
      known[str(path)]=finger
      continue
     # New raw source is owner-private and NOT an approved/verified scientific claim.
     out=store.ingest('Achilles',path,root=root)
     known[str(path)]=finger
     added.append({'sha256':out['sha256'],'file':path.name})
     if len(added)>=a.max_updates:break
    except (ValueError,PermissionError,OSError):continue
  beats=[store.heartbeat(role,{'coordinator':'ONE_SHARED_FAMILY_REVIEW_RUNTIME','new_source_count':len(added)}) for role in ROLES]
  return {'at':beats[0]['at'],'roles':len(beats),'new_sources':added,'native_mint':False,'autonomous_weight_training':False}
 try:
  if a.command=='status':print(json.dumps(store.status(),indent=2));return 0
  with CoordinatorLock(a.home):
   if a.command=='once':print(json.dumps(cycle(),indent=2));return 0
   print(json.dumps({'status':'foreground_running','roles':list(ROLES),'database':str(store.database),'pid':os.getpid(),'network':'disabled','model_training':False,'singleton_scope':'LOCAL_REVIEW_ONLY'}),flush=True)
   while True:
    print(json.dumps(cycle()),flush=True);time.sleep(a.interval)
 except KeyboardInterrupt:return 0
 finally:store.close()
if __name__=='__main__':raise SystemExit(main())
