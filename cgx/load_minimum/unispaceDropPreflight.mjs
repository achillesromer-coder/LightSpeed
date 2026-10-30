import {planUniSpaceSourceInspector} from './unispaceSourceInspector.mjs';
/** UniSpace FileSpace drag/drop metadata preflight, source-only review.
 * Never reads file bytes, grants ACL, verifies a digest, mints an Object_ID,
 * uploads, hydrates, installs, or writes DBR. Host must independently decide.
 */
export const DROP_SCHEMA='UNISPACE-DROP-PREFLIGHT/0.1';
const MAX_BYTES=60*1024*1024;
const spaces=Object.freeze({eco:'Eco.cgx',romer:'Romer.cgx',emassc:'EMASSC.cgx',ls:'LS.cgx'});
const rights=new Set(['PUBLIC_SAFE','OWNER_PRIVATE','LICENSE_RESTRICTED','UNKNOWN']);
const classes=new Set(['creative','scientific','engineering','historical','operational']);
// Caller-declared rights state is a review hint, never a signed grant or DBR receipt.
const rightsStates=new Set(['ACTIVE','REVOKED','SUPERSEDED','UNRESOLVED']);
// An explicit revocation flag is non-vetoing ONLY when strictly boolean false.
// Ambiguous strings, numbers, null and even an own undefined value fail closed.
const revocationEvidence=x=>(Object.hasOwn(x,'revoked')&&x.revoked!==false)||
 (Object.hasOwn(x,'rights_revoked')&&x.rights_revoked!==false)||
 Object.hasOwn(x,'revoked_at')||Object.hasOwn(x,'superseded_by');
const mime=new Set(['application/json','text/plain','text/markdown','text/csv','application/pdf','image/png','image/jpeg','model/gltf-binary']);
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const label=x=>typeof x==='string'&&x.trim().length>0&&x.length<=256&&!/[\u0000-\u001f\u007f]/.test(x);
// Identity strings are opaque exact keys: reject alternate Unicode normalization
// and all default-ignorable controls, matching the private LOAD inspector.
// Do not silently normalize: the native resolver must decide any alias/collision.
const identityLabel=x=>label(x)&&x===x.normalize('NFC')&&
 !/[\p{Default_Ignorable_Code_Point}\p{Cc}]/u.test(x);
const digest=x=>typeof x==='string'&&/^[a-f0-9]{64}$/i.test(x);
const result=(reason,code='HOLD')=>({schema:DROP_SCHEMA,status:code,reason,bytes_read:0,uploaded:false,
 network_fetch:false,hash_verified:false,acl_verified:false,object_id_minted:false,
 native_admitted:false,public_release:false,canonical_mutation:false});
/** One selected existing identity and one incoming source, not an ingestion transaction. */
export function planUniSpaceDropPreflight({target,file,source,access,existing_sources=[],surface='private',offline=false}={}){
 if(!obj(target)||!obj(file)||!obj(source)||!obj(access)||!Array.isArray(existing_sources)||existing_sources.length>512)
  return result('INVALID_PREFLIGHT_INPUT');
 if(!identityLabel(target.object_id)||!identityLabel(target.file_space)||!identityLabel(target.domain)||!identityLabel(target.owner)||
    !Object.hasOwn(spaces,target.domain)||spaces[target.domain]!==target.file_space)
  return result('EXACT_CHILD_FILESPACE_UNRESOLVED');
 if(!Array.isArray(access.authorized_object_ids)||!Array.isArray(access.authorized_file_spaces)||
    !access.authorized_object_ids.includes(target.object_id)||!access.authorized_file_spaces.includes(target.file_space))
  return result('TARGET_SCOPE_NOT_DECLARED');
 if(!label(file.name)||file.name==='.'||file.name==='..'||file.name.includes('..')||/[\\/:]/.test(file.name)||
    !Number.isSafeInteger(file.size)||file.size<1||file.size>MAX_BYTES||!mime.has(file.type)||
    /[\u061c\u200b-\u200f\u202a-\u202e\u2060\u2066-\u2069\ufeff]/u.test(file.name))
  return result('FILE_METADATA_OR_SIZE_UNSUPPORTED');
 if(!identityLabel(source.source_id)||!identityLabel(source.version)||!identityLabel(source.owner)||!digest(source.sha256)||
    !rights.has(source.rights)||!classes.has(source.proof_class))
  return result('SOURCE_QUALIFICATION_INCOMPLETE');
 if(source.rights_state!==undefined&&!rightsStates.has(source.rights_state))
  return result('SOURCE_RIGHTS_STATE_UNQUALIFIED');
 if(revocationEvidence(source)||(source.rights_state!==undefined&&source.rights_state!=='ACTIVE'))
  return result('SOURCE_RIGHTS_NOT_ACTIVE');
 if(surface!=='private'&&surface!=='public')return result('UNSUPPORTED_SURFACE');
 if(source.rights==='UNKNOWN'||source.rights==='LICENSE_RESTRICTED')return result('RIGHTS_REVIEW_REQUIRED');
 if(surface==='public'&&source.rights!=='PUBLIC_SAFE')return result('PRIVATE_SOURCE_PUBLIC_BOUNDARY');
 // A public-safe incoming source does not make its destination Object_ID public.
 // Caller declarations are preflight hints only, never host ACL/rights receipts.
 if(surface==='public'&&target.rights!=='PUBLIC_SAFE')return result('TARGET_PUBLIC_RIGHTS_UNVERIFIED');
 // #158: PUBLIC_SAFE is a caller declaration, not a signed public grant.
 // A browser/static route cannot independently establish host root, ACL,
 // revocation or DBR. Never return source IDs/digests as public candidates.
 if(surface==='public')return result('PUBLIC_ROUTE_REQUIRES_VERIFIED_NATIVE_ACL');
 // Existing references are collision hints only; caller-provided list is not DBR.
 if(existing_sources.some(x=>!obj(x)||!identityLabel(x.source_id)||!digest(x.sha256)))
  return result('EXISTING_SOURCE_REGISTRY_UNQUALIFIED');
 const matching=existing_sources.filter(x=>x.source_id===source.source_id);
 if(matching.length>1||matching.some(x=>x.sha256.toLowerCase()!==source.sha256.toLowerCase()))
  return result('SOURCE_IDENTITY_COLLISION');
 if(matching.length===1){
  // A matching digest alone does not prove that two observations, revisions,
  // rights grants or proof classes are the same qualified R0 source.
  // Legacy id+hash hints cannot authorize a duplicate-suppression decision.
  const prior=matching[0];
  if(!identityLabel(prior.version)||!identityLabel(prior.owner)||!rights.has(prior.rights)||!classes.has(prior.proof_class))
   return result('EXISTING_SOURCE_IDENTITY_UNQUALIFIED');
  // Identical R0 evidence can legitimately be referenced by different objects.
  // A source match alone must not suppress intake for another child FileSpace.
  if(!identityLabel(prior.object_id)||!identityLabel(prior.file_space))
   return result('EXISTING_REFERENCE_SCOPE_UNQUALIFIED');
  if(prior.object_id!==target.object_id||prior.file_space!==target.file_space)
   return result('EXISTING_REFERENCE_SCOPE_COLLISION');
  if(prior.version!==source.version||prior.owner!==source.owner||prior.rights!==source.rights||prior.proof_class!==source.proof_class)
   return result('SOURCE_IDENTITY_COLLISION');
  // NOOP is rights-dependent: legacy/missing state and any revocation/supersession
  // must fail closed. ACTIVE is still unverified until independent host/DBR proof.
  if(prior.rights_state!==undefined&&!rightsStates.has(prior.rights_state))
   return result('EXISTING_RIGHTS_STATE_UNQUALIFIED');
  if(revocationEvidence(prior)||(prior.rights_state!==undefined&&prior.rights_state!=='ACTIVE'))
   return result('EXISTING_RIGHTS_NOT_ACTIVE');
  if(prior.rights_state!=='ACTIVE'||source.rights_state!=='ACTIVE')
   return result('RIGHTS_STATE_UNQUALIFIED');
  return result('EXISTING_REFERENCE_NO_DUPLICATE','NOOP_REVIEW');
 }
 if(offline)return result('OFFLINE_METADATA_ONLY');
 return {...result('HOST_AND_DBR_REVALIDATION_REQUIRED','REVIEW_CANDIDATE'),
  target:{object_id:target.object_id,file_space:target.file_space,domain:target.domain},
  proposed_source:{source_id:source.source_id,version:source.version,proof_class:source.proof_class,
   rights:source.rights,sha256_claim:source.sha256.toLowerCase(),hash_status:'DECLARED_UNVERIFIED'},
  file_metadata:{name:file.name,mime:file.type,size:file.size},
  next_action:'HOST_POLICY_SOURCE_BYTES_HASH_RIGHTS_COLLISION_AND_DBR_PREFLIGHT'};
}


/**
 * Private UniSpace FileSpace inspector → qualified R0 intake handoff.
 * Reuses the existing inspector and drag/drop preflight, so the selected
 * Object_ID and child FileSpace cannot silently change between views.
 * Caller ACL/rights/host flags are NEVER independent native proof.
 * This function does not read, upload, hydrate, install or admit anything.
 */
export const PRIVATE_OBJECT_DROP_SCHEMA='UNISPACE-PRIVATE-OBJECT-DROP-HANDOFF/0.1';
const dropHandoffDeny=reason=>({
 schema:PRIVATE_OBJECT_DROP_SCHEMA,state:'DENIED',reason,
 bytes_read:0,uploaded:false,hash_verified:false,acl_verified:false,
 host_authenticated:false,provider_readback:false,native_admitted:false,
 public_release:false,canonical_mutation:false
});
export function planUniSpacePrivateObjectDrop({
 surface=null,inspectorInput=null,dropInput=null,offline=false
}={}){
 // Public Vite routes and browser-originated "private" flags are not host
 // authentication. This is a private source-review UI contract only (#158).
 if(surface!=='private')return dropHandoffDeny('PRIVATE_OPERATOR_SURFACE_REQUIRED');
 if(offline!==false)return dropHandoffDeny('OFFLINE_INTAKE_FORBIDDEN');
 if(!obj(inspectorInput)||!obj(dropInput)||!obj(dropInput.target)||
    inspectorInput.surface!=='private'||
    (dropInput.surface!==undefined&&dropInput.surface!=='private')||
    // A child widget cannot claim offline while its parent requests online intake.
    // Reject ambiguous strings and contradictory nested flags, not just true.
    (inspectorInput.offline!==undefined&&inspectorInput.offline!==false)||
    (dropInput.offline!==undefined&&dropInput.offline!==false))
  return dropHandoffDeny('INCONSISTENT_PRIVATE_REVIEW_CONTEXT');
 // No second independently supplied ACL array is accepted for this handoff:
 // the source inspector's exact selected scope is reused, never widened.
 if(dropInput.access!==undefined)
  return dropHandoffDeny('DUPLICATE_ACCESS_CONTEXT_FORBIDDEN');
 if(inspectorInput.focus_id!==dropInput.target.object_id||
    inspectorInput.file_space!==dropInput.target.file_space)
  return dropHandoffDeny('OBJECT_OR_CHILD_FILESPACE_CHANGED');
 let inspector;
 try{
  inspector=planUniSpaceSourceInspector({
   ...inspectorInput,surface:'private',offline:false,view:'document',
   budgets:{max_nodes:1,max_hops:0,max_cross_domains:0,max_cross_edges:0,
    max_evidence_refs:32,max_transfer_bytes:0}
  });
 }catch{
  return dropHandoffDeny('INSPECTOR_PROJECTION_FAILED');
 }
 if(inspector.status!=='SOURCE_REVIEW_ONLY'||inspector.identity!==dropInput.target.object_id||
    inspector.selected_file_space!==dropInput.target.file_space)
  return dropHandoffDeny('INSPECTOR_EXACT_SCOPE_NOT_RESOLVED');
 if(!inspector.h0||!identityLabel(inspector.h0.owner)||
    inspector.h0.owner!==dropInput.target.owner)
  return dropHandoffDeny('OBJECT_OWNER_UNRESOLVED_OR_MISMATCHED');
 // An R0 source ID already referenced by this selected object cannot be
 // reintroduced as a "new" drop. Equal bytes do not establish a duplicate;
 // changed bytes/version require native identity and rights resolution.
 // Caller node data is a veto hint, not authenticated DBR proof.
 const selectedNode=inspectorInput.nodes.find(n=>n.object_id===inspector.identity);
 if(selectedNode.source_refs.includes(dropInput.source?.source_id))
  return dropHandoffDeny('SELECTED_R0_SOURCE_ID_REQUIRES_NATIVE_RESOLUTION');
 // A missing/revoked source rights state cannot become a qualified intake
 // proposal merely because a browser reports a plausible licence.
 if(!obj(dropInput.source)||dropInput.source.rights_state!=='ACTIVE'||
    revocationEvidence(dropInput.source))
  return dropHandoffDeny('INCOMING_SOURCE_RIGHTS_NOT_ACTIVE');
 const preflight=planUniSpaceDropPreflight({
  target:dropInput.target,file:dropInput.file,source:dropInput.source,
  access:{authorized_object_ids:[inspector.identity],
   authorized_file_spaces:[inspector.selected_file_space]},
  existing_sources:dropInput.existing_sources??[],surface:'private',offline:false
 });
 if(preflight.status!=='REVIEW_CANDIDATE'&&preflight.status!=='NOOP_REVIEW')
  return dropHandoffDeny('SOURCE_PREFLIGHT_'+preflight.reason);
 return {
  schema:PRIVATE_OBJECT_DROP_SCHEMA,state:'SOURCE_REVIEW_ONLY',
  family:'Cognigrex.cgx',selected_object_id:inspector.identity,
  selected_file_space:inspector.selected_file_space,
  source_view_state:inspector.viewport.state,
  inspector_stage:inspector.admission_stage,
  intake_preflight:preflight.status,
  source:preflight.status==='REVIEW_CANDIDATE'?preflight.proposed_source:null,
  file_metadata:preflight.status==='REVIEW_CANDIDATE'?preflight.file_metadata:null,
  source_proof:'CALLER_DECLARATION_NOT_PROVIDER_VERIFIED',
  next_action:'INDEPENDENT_NATIVE_R0_HASH_RIGHTS_COLLISION_ROOT_LEASE_DBR_REVIEW',
  blockers:['SOURCE_BYTES_AND_SHA256_NOT_INDEPENDENTLY_VERIFIED',
   'RIGHTS_OWNER_ACL_AND_REVOCATION_NOT_PROVIDER_VERIFIED',
   'SIGNED_NATIVE_OBJECT_ID_ROOT_LEASE_DBR_NOT_VERIFIED',
   'ISSUE_158_PRIVATE_ROUTE_NEGATIVE_TESTS_REQUIRED'],
  bytes_read:0,uploaded:false,network_fetch:false,hash_verified:false,
  acl_verified:false,host_authenticated:false,provider_readback:false,
  native_admitted:false,installed:false,public_release:false,
  canonical_mutation:false
 };
}
