/** UniSpace ONE-Object_ID read-only view-plan gate.
 * Caller supplies existing CGX registry binding, rights, lease and receipts.
 * No resolver, provider fetch, native write, source bytes or public endpoint.
 */
const HEX40=/^[a-f0-9]{40}$/i, HEX64=/^[a-f0-9]{64}$/i;
const LAYERS=['R0','R1','R2','R3'];
const hold=(code,p)=>Object.freeze({schema:'UNISPACE-CGX-ONE-OBJECT-VIEW-PLAN/0.1',state:'HOLD',hold_code:code,object_id:typeof p?.requested_object_id==='string'?p.requested_object_id:null,filespace:null,source_bytes_included:false,native_admitted:false,canonical_mutation:false,execution_performed:false,public_publish_authorized:false});
export function projectCgxOneObjectView(p){
  if(!p||typeof p!=='object'||Array.isArray(p))return hold('INVALID_REQUEST',p);
  const {requested_object_id:id,binding:b,source:s,access:a,evidence:e={}}=p;
  if(typeof id!=='string'||!id||id.length>255||b?.semantic_object_id!==id||typeof b.filespace!=='string'||!/^[A-Za-z][A-Za-z0-9_.-]*\.cgx$/.test(b.filespace))return hold('EXACT_ID_OR_FILESPACE_MISMATCH',p);
  if(s?.provider!=='github'||!s.repository||!s.registry_path||!HEX40.test(s.registry_git_blob_sha||'')||s.binding_readback_verified!==true)return hold('SOURCE_BINDING_UNVERIFIED',p);
  if(a?.state!=='verified_owner'||!Array.isArray(a.allowed_object_ids)||!a.allowed_object_ids.includes(id))return hold('ACCESS_NOT_VERIFIED',p);
  if(s.rights!=='cleared'||s.visibility!=='owner_private')return hold('RIGHTS_OR_VISIBILITY_UNRESOLVED',p);
  if(!HEX64.test(s.source_sha256||'')||s.source_bytes_readback_verified!==true)return hold('SOURCE_BYTES_UNVERIFIED',p);
  const level=LAYERS.indexOf(p.requested_layer);
  if(level<0)return hold('UNSUPPORTED_LAYER',p);
  if(level>=1&&!HEX64.test(e.r1_parse_receipt_sha256||''))return hold('R1_PARSE_UNVERIFIED',p);
  if(level>=2&&!HEX64.test(e.r2_overlay_receipt_sha256||''))return hold('R2_OVERLAY_UNVERIFIED',p);
  if(level>=3&&(!HEX64.test(e.r3_view_receipt_sha256||'')||e.owner_private_route_verified!==true||e.dbr_readback_verified!==true))return hold('R3_PRIVATE_ROUTE_OR_DBR_UNVERIFIED',p);
  if(['view_url','source_bytes','token'].some(k=>Object.prototype.hasOwnProperty.call(p,k)))return hold('UNSAFE_INLINE_PAYLOAD',p);
  return Object.freeze({schema:'UNISPACE-CGX-ONE-OBJECT-VIEW-PLAN/0.1',state:'PLAN_ONLY_NOT_HYDRATED',object_id:id,filespace:b.filespace,requested_layer:p.requested_layer,source_registry_git_blob_sha:s.registry_git_blob_sha,hydration:{mode:'on_demand_existing_cgx_provider',max_bytes:Number.isSafeInteger(p.max_bytes)&&p.max_bytes>0?Math.min(p.max_bytes,1000000):1000000,byte_transfer_performed:false},source_locator_exposed:false,source_bytes_included:false,native_admitted:false,execution_performed:false,canonical_mutation:false,public_publish_authorized:false,claim_boundary:'Caller evidence flags are not independently authenticated by this view planner.'});
}

/** Revalidate a planned view against current caller-authenticated evidence.
 * The caller must obtain fresh access and source records; this does not fetch
 * or authenticate them, and it never authorises a native operation.
 */
export function recheckCgxOneObjectView(previous, original, current){
  const fresh=projectCgxOneObjectView(current);
  if(fresh.state==='HOLD')return fresh;
  const before=projectCgxOneObjectView(original);
  if(before.state!=='PLAN_ONLY_NOT_HYDRATED'||previous?.state!==before.state)
    return hold('ORIGINAL_PLAN_UNVERIFIED',current);
  const binding=v=>JSON.stringify([v.object_id,v.filespace,v.requested_layer,
    v.source_registry_git_blob_sha,v.hydration?.max_bytes]);
  if(binding(previous)!==binding(before)||binding(before)!==binding(fresh))
    return hold('PLAN_BINDING_CHANGED',current);
  const rev=original?.access?.scope_revision;
  if(typeof rev!=='string'||!rev||rev.length>256||current.access.scope_revision!==rev)
    return hold('ACCESS_REVISION_CHANGED',current);
  if(original.source.source_sha256!==current.source.source_sha256||
     original.source.repository!==current.source.repository||
     original.source.registry_path!==current.source.registry_path||
     ['r1_parse_receipt_sha256','r2_overlay_receipt_sha256','r3_view_receipt_sha256'].some(k=>original.evidence?.[k]!==current.evidence?.[k]))
    return hold('SOURCE_OR_EVIDENCE_CHANGED',current);
  return Object.freeze({...fresh,state:'RECHECKED_PLAN_ONLY_NOT_HYDRATED',
    scope_revision:rev,provider_authentication_required:true});
}
