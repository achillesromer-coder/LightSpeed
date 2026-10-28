/** Source-only UniSpace Vite build-provenance review for ONE candidate Object_ID.
 * No HTTP, dist scan, signature verification, provider mutation, or release authority.
 */
export const SCHEMA='UNISPACE-BUILD-PROVENANCE-REVIEW/0.1';
const sha1=/^[a-f0-9]{40}$/,sha256=/^[a-f0-9]{64}$/,id=/^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/;
const children=new Set(['Romer.cgx','Eco.cgx','EMASSC.cgx','LS.cgx']);
const privateKeys=new Set(['token','cookie','password','secret','authorization','access_key','source_url','source_locator','source_bytes','private_path','public_path','asset_url','endpoint','url','uri','headers','response_body','payload','session','credential','carrier_path','dbr_root','state_root','path','filename','content','binary']);
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const keys=(x,allowed)=>obj(x)&&Object.keys(x).every(k=>allowed.includes(k));
function forbidden(x,seen=new Set(),depth=0){
 if(!x||typeof x!=='object')return false;
 if(depth>8||seen.has(x))return true;
 seen.add(x);
 for(const [k,v] of Object.entries(x)){if(privateKeys.has(k.toLowerCase())||forbidden(v,seen,depth+1))return true;}
 seen.delete(x);return false;
}
const hold=code=>Object.freeze({schema:SCHEMA,state:'HOLD',hold_code:code,source_verified:false,dist_verified:false,host_http_verified:false,release_accepted:false,canonical_mutation:false});
export function reviewUniSpaceBuildProvenance(input){
 if(!keys(input,['selection','client_permissions','source_review','entries'])||forbidden(input))return hold('INVALID_OR_PRIVATE_INPUT');
 const {selection:s,client_permissions:p,source_review:r,entries}=input;
 if(!keys(s,['parent_filespace','object_id','filespace','identity_status','evidence_class'])||
 s.parent_filespace!=='Cognigrex.cgx'||!id.test(s.object_id||'')||s.object_id.startsWith('cgx:domain:')||
 s.object_id==='cgx:root:cognigrex'||!children.has(s.filespace)||s.identity_status!=='SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED'||
 !['scientific','creative','mixed','unknown'].includes(s.evidence_class))return hold('EXACT_CANDIDATE_REQUIRED');
 if(!keys(p,['mode','revoked','allowed_object_ids','allowed_filespaces'])||p.mode!=='review_only'||p.revoked!==false||
 !Array.isArray(p.allowed_object_ids)||p.allowed_object_ids.length!==1||p.allowed_object_ids[0]!==s.object_id||
 !Array.isArray(p.allowed_filespaces)||p.allowed_filespaces.length!==1||p.allowed_filespaces[0]!==s.filespace)return hold('CLIENT_SCOPE_MISMATCH');
 if(!obj(r)||r.schema!=='UNISPACE-STATIC-ASSET-BOUNDARY-REVIEW/0.1'||r.state!=='SOURCE_REVIEW_ONLY'||
 r.parent_filespace!==s.parent_filespace||r.filespace!==s.filespace||r.candidate_object_id!==s.object_id||
 r.evidence_class!==s.evidence_class||r.source_scan_verified!==false||r.host_http_verified!==false||
 r.dist_verified!==false||r.release_accepted!==false||r.canonical_mutation!==false||
 !Array.isArray(r.assets)||r.assets.length<1||r.assets.length>16)return hold('SOURCE_REVIEW_BINDING_REQUIRED');
 const sourceMap=new Map();
 for(const a of r.assets){
 if(!keys(a,['asset_id','source_blob_sha','static_source_path','review_result','risk_codes'])||
 typeof a.asset_id!=='string'||!sha1.test(a.source_blob_sha||'')||typeof a.static_source_path!=='boolean'||
 !Array.isArray(a.risk_codes)||a.risk_codes.some(c=>typeof c!=='string')||sourceMap.has(a.asset_id))return hold('INVALID_SOURCE_ASSET');
 sourceMap.set(a.asset_id,a);
 }
 if(!Array.isArray(entries)||entries.length!==sourceMap.size)return hold('BUILD_ENTRY_PARITY_REQUIRED');
 const seen=new Set(),results=[];
 for(const e of entries){
 if(!keys(e,['asset_id','source_blob_sha','build_sha256','distribution_class','source_class','scope','rights','owner_clearance','object_id','filespace'])||
 !sourceMap.has(e.asset_id)||seen.has(e.asset_id)||!sha1.test(e.source_blob_sha||'')||!sha256.test(e.build_sha256||'')||
 !['PUBLIC_STATIC','AUTHENTICATED_PRIVATE'].includes(e.distribution_class)||
 !['INTERNAL_REVIEW','OWNER_PRIVATE','PUBLIC_CANDIDATE','UNKNOWN'].includes(e.source_class)||
 !['ONE_OBJECT','MULTI_OBJECT','UNKNOWN'].includes(e.scope)||
 !['CLEARED_PUBLIC','UNRESOLVED','RESTRICTED'].includes(e.rights)||typeof e.owner_clearance!=='boolean')return hold('INVALID_BUILD_ENTRY');
 if(e.object_id!==s.object_id||e.filespace!==s.filespace)return hold('CROSS_OBJECT_OR_FILESPACE_BUILD');
 seen.add(e.asset_id);
 const a=sourceMap.get(e.asset_id),risks=[];
 if(a.source_blob_sha!==e.source_blob_sha)risks.push('SOURCE_BLOB_MISMATCH');
 if(a.risk_codes.length)risks.push('UNRESOLVED_SOURCE_REVIEW_RISK');
 if(e.distribution_class==='PUBLIC_STATIC'){
 if(e.source_class!=='PUBLIC_CANDIDATE')risks.push('NONPUBLIC_SOURCE_IN_STATIC_BUILD');
 if(e.rights!=='CLEARED_PUBLIC'||!e.owner_clearance)risks.push('PUBLIC_RIGHTS_OR_CLEARANCE_HOLD');
 if(e.scope!=='ONE_OBJECT')risks.push('NOT_SINGLE_OBJECT');
 }else risks.push('PRIVATE_ROUTE_HOST_DENIAL_NOT_VERIFIED');
 results.push(Object.freeze({asset_id:e.asset_id,source_blob_sha:e.source_blob_sha,build_sha256:e.build_sha256,distribution_class:e.distribution_class,risk_codes:Object.freeze(risks),review_result:risks.length?'HOLD':'METADATA_ONLY_NO_RELEASE_PROOF'}));
 }
 return Object.freeze({schema:SCHEMA,state:'SOURCE_REVIEW_ONLY',parent_filespace:s.parent_filespace,candidate_object_id:s.object_id,filespace:s.filespace,evidence_class:s.evidence_class,
 alias:'LOAD.cgx',alias_role:'ALEXANDRIA_ENTRY_NOT_PARENT',assets:Object.freeze(results),asset_count:results.length,risk_count:results.filter(x=>x.risk_codes.length).length,
 gate:'HOLD_ISSUE_158_AND_161',next_step:'INDEPENDENT_DEPLOYED_DIST_MANIFEST_AND_ANONYMOUS_REVOKED_OWNER_HTTP_READBACK',
 source_verified:false,dist_verified:false,host_http_verified:false,release_accepted:false,canonical_mutation:false,network_fetch:false,source_bytes_transferred:0,offline_hydration:'H0_METADATA_ONLY',
 claim_boundary:'Caller-supplied source/build hashes are metadata, not deployed-build or HTTP readback.'});
}
