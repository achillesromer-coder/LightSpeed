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
const revocationEvidence=x=>x.revoked===true||x.rights_revoked===true||
 Object.hasOwn(x,'revoked_at')||Object.hasOwn(x,'superseded_by');
const mime=new Set(['application/json','text/plain','text/markdown','text/csv','application/pdf','image/png','image/jpeg','model/gltf-binary']);
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const label=x=>typeof x==='string'&&x.trim().length>0&&x.length<=256&&!/[\u0000-\u001f\u007f]/.test(x);
const identityLabel=x=>label(x)&&!/[\u061c\u200b-\u200f\u202a-\u202e\u2060\u2066-\u2069\ufeff]/u.test(x);
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
