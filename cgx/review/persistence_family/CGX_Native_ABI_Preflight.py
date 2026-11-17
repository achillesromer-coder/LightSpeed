#!/usr/bin/env python3
"""Non-dispatching CGX/LightSpeed source-contract preflight.

Read-only proof of *source* parity, NOT permission, execution lease, native
admission, LOAD readiness, signed DBR, or deployment. No network or imports of
native runtime modules. Existing live services are not touched.
"""
from __future__ import annotations
import argparse,ast,hashlib,json,subprocess
from pathlib import Path

REPO_HEAD='0376a7330f02adfc1a6c928f5428cc8df3082f63'
BLOB_PINS={
 'desktop/LightSpeed_Runtime/lightspeed_runtime/achilles/operator.py':'385a1ea3b1a531b32226486d0a7d6b8494efdafc',
 'desktop/LightSpeed_Runtime/lightspeed_runtime/node_exchange.py':'80f677fec0e197cbb54a0339a7155b7becedf29b',
 'cgx/domain_templates/execution_lease_contract.json':'637de5a3b904b5df0e865dd8f9477b3e7750c3d7',
}
OPERATOR_METHODS={'retrieve','propose_action','approve_action','reject_action'}
NODE_FUNCS={'build_transfer_envelope','execute_local_transfer','build_compute_request','execute_local_compute','resolve_node_root'}
LEASE_FIELDS={'lease_id','lease_class','state','issued_by','subject_agent','valid_from','valid_until','domains','execution_depths','scope','revocable','authority_phase','authority_phase_ref'}

def git_blob(data:bytes)->str:
 return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def inspect_sources(repo:Path,*,expected_head=REPO_HEAD,expected_blobs=BLOB_PINS)->dict:
 """Read only; even passing all checks cannot authorise tool dispatch."""
 findings=[];root=Path(repo).expanduser()
 if not root.is_dir():return {'source_parity':False,'findings':['repository missing'],'authority':'HOLD','dispatch_allowed':False}
 proc=subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],capture_output=True,text=True,timeout=10)
 head=proc.stdout.strip() if proc.returncode==0 else 'UNAVAILABLE'
 if head!=expected_head:findings.append('HEAD differs from pinned review commit; reconcile before admission')
 passed=head==expected_head
 source={}
 for relative,blob in expected_blobs.items():
  target=root/relative
  if target.is_symlink() or not target.is_file():
   findings.append('missing or linked: '+relative);passed=False;continue
  actual=target.read_bytes();ok=git_blob(actual)==blob
  source[relative]={'pinned_git_blob':blob,'matching':ok,'length':len(actual)}
  if not ok:findings.append('source differs from pinned blob: '+relative);passed=False
  if not ok:continue
  if relative.endswith('/achilles/operator.py'):
   tree=ast.parse(actual.decode('utf8'))
   cls=next((n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='AchillesOperator'),None)
   funcs={n.name for n in cls.body if isinstance(n,ast.FunctionDef)} if cls else set()
   if not OPERATOR_METHODS<=funcs:passed=False;findings.append('operator method contract missing')
  elif relative.endswith('/node_exchange.py'):
   tree=ast.parse(actual.decode('utf8'));funcs={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
   if not NODE_FUNCS<=funcs:passed=False;findings.append('node-exchange function contract missing')
  elif relative.endswith('/execution_lease_contract.json'):
   contract=json.loads(actual)
   if not LEASE_FIELDS<=set(contract.get('required_fields',[])) or 'missing-or-stale-lease-means-no-consequential-execution' not in contract.get('invariants',[]):
    passed=False;findings.append('execution-lease contract changed unexpectedly')
 return {'schema':'cgx.family.native.source-review.v1','pinned_head':expected_head,'observed_head':head,'source_parity':passed,'files':source,'findings':findings,'full_LOAD':'UNVERIFIED','lease_authentication':'NOT PERFORMED','native_mint':'HOLD','authority':'HOLD','dispatch_allowed':False,'source_review_only':True}


def inspect_lease_structure(candidate:dict|None,*,subject:str,now_iso:str)->dict:
 """Negative-gate inspection, not an issuer-signature validator."""
 from datetime import datetime,timezone
 reasons=[]
 if not isinstance(candidate,dict):reasons.append('no lease')
 else:
  missing=LEASE_FIELDS-set(candidate)
  if missing:reasons.append('required lease fields absent')
  if candidate.get('state')!='ACTIVE':reasons.append('lease not ACTIVE')
  if candidate.get('subject_agent')!=subject:reasons.append('subject mismatch')
  if candidate.get('revocable') is not True:reasons.append('revocation not guaranteed')
  if candidate.get('issued_by')==subject:reasons.append('agent cannot self-issue a consequential lease')
  try:
   now=datetime.fromisoformat(now_iso.replace('Z','+00:00'))
   a=datetime.fromisoformat(str(candidate['valid_from']).replace('Z','+00:00'))
   b=datetime.fromisoformat(str(candidate['valid_until']).replace('Z','+00:00'))
   if not all(v.tzinfo for v in (now,a,b)) or not a<=now<b:reasons.append('lease expired, future or timezone missing')
  except (TypeError,ValueError,KeyError):reasons.append('lease time invalid')
  if candidate.get('lease_class') not in {'READ_ONLY','COMPUTE_ONLY','DIGITAL_WRITE','EXTERNAL_ACTION','PHYSICAL_ACTUATION'}:
   reasons.append('unrecognised lease class')
 # Even a structurally eligible lease has no verified issuer, revocation list,
 # parent authority or scope binding in this review-only adapter.
 return {'structurally_eligible_for_independent_check':not reasons,'reasons':reasons,'issuer_authenticated':False,'revocation_checked':False,'dispatch_allowed':False,'authority':'HOLD'}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path,required=True)
 a=ap.parse_args();print(json.dumps(inspect_sources(a.repo),indent=2))