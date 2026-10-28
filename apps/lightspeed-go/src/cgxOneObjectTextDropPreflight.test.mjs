import { test } from 'vitest';
import assert from 'node:assert/strict';
import { preflightCgxOneObjectTextDrop as preflight } from './cgxOneObjectTextDropPreflight.mjs';
const plan = () => ({
  schema:'UNISPACE-CGX-HOST-CONTEXT-GATE/0.1',state:'PLAN_ONLY_NOT_HYDRATED',
  object_id:'WT-001',filespace:'Romer.cgx',
  source_lineage_git_blob_sha:'75d913822e4da42e64ab8a2274c84d6f853340b3',
  source_registry_git_blob_sha:'c2e03b1137ba844209e6c80e94c9fc7532f0db11',
  native_admitted:false,canonical_mutation:false,execution_performed:false,
  private_hydration_authorized:false,public_publish_authorized:false,
  host_context_readback_authenticated:false,source_registry_independently_verified:false
});
const make = () => ({
  intake_mode:'review_only',requested_layer:'R0',target_object_id:'WT-001',
  destination_filespace:'Romer.cgx',context_plan:plan(),
  files:[{name:'notes.txt',size:240,type:'text/plain'}]
});
const reject = (p,code) => assert.equal(preflight(p).hold_code,code);
test('exact one-object text metadata returns non-authoritative R0 preflight',()=>{
  const v=preflight(make());
  assert.equal(v.state,'PREFLIGHT_ONLY_NOT_UPLOADED');
  assert.equal(v.object_id,'WT-001'); assert.equal(v.filespace,'Romer.cgx');
  for(const k of ['uploaded','native_admitted','canonical_mutation','source_bytes_read',
    'source_sha256_verified','rights_verified','acl_verified','owner_session_verified',
    'provider_readback_verified','private_route_authorized','public_publish_authorized'])
    assert.equal(v[k],false,k);
  assert.equal(JSON.stringify(v).includes('notes.txt'),false);
});
test('no file or multiple files fail closed',()=>{
  const p=make();p.files=[];reject(p,'EXACTLY_ONE_FILE_REQUIRED');
  const q=make();q.files.push({name:'more.txt',size:2,type:''});reject(q,'EXACTLY_ONE_FILE_REQUIRED');
});
test('only R0 review is allowed',()=>{
  const p=make();p.requested_layer='R1';reject(p,'UNSUPPORTED_INTAKE_MODE_OR_LAYER');
  const q=make();q.intake_mode='upload';reject(q,'UNSUPPORTED_INTAKE_MODE_OR_LAYER');
});
test('cross-domain or mismatched object cannot be routed',()=>{
  const p=make();p.destination_filespace='Eco.cgx';reject(p,'OBJECT_ID_OR_CHILD_FILESPACE_MISMATCH');
  const q=make();q.target_object_id='cgx:domain:romer';reject(q,'OBJECT_ID_OR_CHILD_FILESPACE_MISMATCH');
});
test('unverified or escalated host plan is never an intake authority',()=>{
  const p=make();p.context_plan.host_context_readback_authenticated=true;reject(p,'CONTEXT_PLAN_IS_NOT_SAFE_REVIEW_BOUNDARY');
  const q=make();q.context_plan.private_hydration_authorized=true;reject(q,'CONTEXT_PLAN_IS_NOT_SAFE_REVIEW_BOUNDARY');
  const r=make();r.context_plan.state='HOLD';reject(r,'CONTEXT_PLAN_IS_NOT_SAFE_REVIEW_BOUNDARY');
});
test('registry lineage digests must be Git blob SHA shape',()=>{
  const p=make();p.context_plan.source_lineage_git_blob_sha='bad';reject(p,'OBJECT_ID_OR_CHILD_FILESPACE_MISMATCH');
});
test('reject path traversal, hidden files, unsupported formats and control characters',()=>{
  for(const name of ['../notes.txt','/tmp/a.txt','C:\\private\\a.txt','.secret.txt','image.png','a\nb.txt']){
    const p=make();p.files[0].name=name;reject(p,'UNSUPPORTED_OR_UNSAFE_FILE_NAME');
  }
});
test('reject zero, negative, fractional and oversized byte counts',()=>{
  for(const size of [0,-1,1.5,1048577,Number.MAX_SAFE_INTEGER+1]){
    const p=make();p.files[0].size=size;reject(p,'FILE_SIZE_OUT_OF_BOUNDS');
  }
});
test('reject inconsistent MIME, accept browser-empty MIME without trusting it',()=>{
  const p=make();p.files[0].type='text/html';reject(p,'MIME_EXTENSION_MISMATCH');
  const q=make();q.files[0].type='';assert.equal(preflight(q).state,'PREFLIGHT_ONLY_NOT_UPLOADED');
});
test('reject inline tokens, bytes, upload URL and public paths',()=>{
  for(const k of ['token','authorization','source_bytes','payload','upload_url','public_path','file_path']){
    const p=make();p[k]='private';reject(p,'UNSAFE_INLINE_OR_ROUTE_INPUT');
  }
  const p=make();p.files[0].content='secret';reject(p,'UNSAFE_FILE_PAYLOAD_OR_PATH');
  const q=make();q.files[0].webkitRelativePath='../secret.txt';reject(q,'UNSAFE_FILE_PAYLOAD_OR_PATH');
});
test('private source name, bytes and tokens never echo in holds',()=>{
  const p=make();p.files[0].name='private.txt';p.files[0].content='sensitive';
  const s=JSON.stringify(preflight(p));
  assert.equal(s.includes('private.txt'),false);
  assert.equal(s.includes('sensitive'),false);
});
test('invalid request and malformed file descriptor fail closed',()=>{
  reject(null,'INVALID_REQUEST');
  const p=make();p.files=[null];reject(p,'INVALID_FILE_DESCRIPTOR');
});
