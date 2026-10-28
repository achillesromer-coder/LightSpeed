/**
 * Source-only UniSpace/Vite static-asset boundary review for ONE candidate object.
 * Consumes provider-supplied source metadata; never performs HTTP or a dist scan.
 * A Git source-path risk is not proof of a deployed disclosure or a safe release.
 */
export const STATIC_BOUNDARY_SCHEMA='UNISPACE-STATIC-ASSET-BOUNDARY-REVIEW/0.1';
const CHILDREN=new Set(['Romer.cgx','Eco.cgx','EMASSC.cgx','LS.cgx']);
const ID=/^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/;
const SHA=/^[a-f0-9]{40}$/;
const ASSET_ID=/^[a-z][a-z0-9_-]{0,63}$/;
const PRIVATE_KEYS=new Set(['token','cookie','password','secret','authorization','access_key','source_url','source_locator','source_bytes','private_path','asset_url','endpoint','url','uri','headers','response_body','payload','session','credential','dbr_root','state_root']);
const record=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const exactKeys=(o,allowed)=>record(o)&&Object.keys(o).every(k=>allowed.includes(k));
function forbidden(x,seen=new Set(),depth=0){
 if(!x||typeof x!=='object')return false;
 if(seen.has(x)||depth>8)return true;
 seen.add(x);
 for(const [k,v] of Object.entries(x)){
  if(PRIVATE_KEYS.has(k.toLowerCase())||forbidden(v,seen,depth+1))return true;
 }
 seen.delete(x);return false;
}
const hold=code=>Object.freeze({schema:STATIC_BOUNDARY_SCHEMA,state:'HOLD',hold_code:code,source_scan_verified:false,host_http_verified:false,dist_verified:false,release_accepted:false,canonical_mutation:false});
const pathOk=p=>typeof p==='string'&&p.length<=240&&p.startsWith('apps/lightspeed-go/')&&!p.startsWith('/')&&!p.includes('\\')&&!p.includes('..')&&!p.includes('%')&&!p.includes('?')&&!p.includes('#')&&!/[\u0000-\u001f]/.test(p)&&/^[A-Za-z0-9_./-]+$/.test(p);
const staticPath=p=>p.startsWith('apps/lightspeed-go/public/')||p.startsWith('apps/lightspeed-go/dist/');
export function reviewUniSpaceStaticAssetBoundary(input){
 if(!exactKeys(input,['selection','client_permissions','assets'])||forbidden(input))return hold('INVALID_OR_PRIVATE_INPUT');
 const s=input.selection,p=input.client_permissions,a=input.assets;
 if(!exactKeys(s,['parent_filespace','object_id','filespace','identity_status','evidence_class'])||s.parent_filespace!=='Cognigrex.cgx'||!ID.test(s.object_id||'')||s.object_id.startsWith('cgx:domain:')||s.object_id==='cgx:root:cognigrex'||!CHILDREN.has(s.filespace)||s.identity_status!=='SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED'||!['scientific','creative','mixed','unknown'].includes(s.evidence_class))return hold('EXACT_CANDIDATE_REQUIRED');
 if(!exactKeys(p,['mode','revoked','allowed_object_ids','allowed_filespaces'])||p.mode!=='review_only'||p.revoked!==false||!Array.isArray(p.allowed_object_ids)||p.allowed_object_ids.length!==1||p.allowed_object_ids[0]!==s.object_id||!Array.isArray(p.allowed_filespaces)||p.allowed_filespaces.length!==1||p.allowed_filespaces[0]!==s.filespace)return hold('CLIENT_SCOPE_MISMATCH');
 if(!Array.isArray(a)||a.length<1||a.length>16)return hold('ASSET_COUNT_OUT_OF_RANGE');
 const seen=new Set(),results=[];
 for(const item of a){
  if(!exactKeys(item,['asset_id','repository_path','blob_sha','source_class','scope','rights','owner_clearance'])||!ASSET_ID.test(item.asset_id||'')||seen.has(item.asset_id)||!pathOk(item.repository_path)||!SHA.test(item.blob_sha||'')||!['INTERNAL_REVIEW','OWNER_PRIVATE','PUBLIC_CANDIDATE','UNKNOWN'].includes(item.source_class)||!['ONE_OBJECT','MULTI_OBJECT','UNKNOWN'].includes(item.scope)||!['CLEARED_PUBLIC','UNRESOLVED','RESTRICTED'].includes(item.rights)||typeof item.owner_clearance!=='boolean')return hold('INVALID_ASSET_EVIDENCE');
  seen.add(item.asset_id);
  const isStatic=staticPath(item.repository_path);
  const risks=[];
  if(isStatic&&['INTERNAL_REVIEW','OWNER_PRIVATE'].includes(item.source_class))risks.push('INTERNAL_SOURCE_IN_STATIC_TREE');
  if(isStatic&&item.rights!=='CLEARED_PUBLIC')risks.push('PUBLIC_RIGHTS_NOT_CLEARED');
  if(isStatic&&!item.owner_clearance)risks.push('OWNER_CLEARANCE_MISSING');
  if(item.scope!=='ONE_OBJECT')risks.push('NOT_EXACT_OBJECT_SCOPED');
  if(item.source_class==='UNKNOWN')risks.push('SOURCE_CLASS_UNKNOWN');
  results.push(Object.freeze({asset_id:item.asset_id,source_blob_sha:item.blob_sha,static_source_path:isStatic,review_result:risks.length?'SOURCE_RISK_HOLD':'SOURCE_METADATA_ONLY_NOT_RELEASE_PROOF',risk_codes:Object.freeze(risks)}));
 }
 const riskCount=results.filter(r=>r.risk_codes.length>0).length;
 return Object.freeze({schema:STATIC_BOUNDARY_SCHEMA,state:'SOURCE_REVIEW_ONLY',parent_filespace:'Cognigrex.cgx',filespace:s.filespace,candidate_object_id:s.object_id,evidence_class:s.evidence_class,alias:'LOAD.cgx',alias_role:'ALEXANDRIA_ENTRY_NOT_PARENT',asset_count:results.length,source_risk_count:riskCount,assets:Object.freeze(results),risk_signal:riskCount?'SOURCE_STATIC_BOUNDARY_REVIEW_REQUIRED':'NO_SOURCE_RISK_IN_SUPPLIED_METADATA',source_scan_verified:false,host_http_verified:false,dist_verified:false,release_accepted:false,canonical_mutation:false,network_fetch:false,source_bytes_transferred:0,offline_hydration:'H0_METADATA_ONLY',gate:'HOLD_ISSUE_158_AND_161',next_step:'INDEPENDENT_ANONYMOUS_REVOKED_OWNER_HTTP_AND_BUILT_DIST_READBACK',claim_boundary:'Provider-supplied Git metadata is not an authenticated deployed host/browser test; no public-release inference.'});
}
