/**
 * Private host-side LOAD review packet -> browser-safe source-status DTO.
 * The Node/crypto source-bound hash checks remain HERE, never in browser UI.
 * This is not provider attestation, rights approval, a signed lease or DBR.
 */
import {projectUniSpace,SCHEMA as FAMILY_SCHEMA} from './cgxPremintFamilyProjection.mjs';
export const SCHEMA='CGX-PRIVATE-LOAD-BINDING-REVIEW/0.1';
const deny=reason=>({state:'DENIED',reason,canonical_mutation:false});
export function makePrivateLoadBinding(packet,{objectId,fileSpace}={}){
 const records=packet?.convergence?.source_records;
 if(packet?.schema!==FAMILY_SCHEMA||
    !['PREMINT_REVIEW_ONLY','REVIEW_WITH_HOLDS'].includes(packet?.state)||
    packet?.canonical_parent!=='cgx:root:cognigrex'||
    !Array.isArray(records)||records.length!==1||
    typeof objectId!=='string'||typeof fileSpace!=='string'||
    records[0]?.source_id!==objectId||records[0]?.family!==fileSpace||
    records[0]?.sha256!==packet?.envelope?.manifest?.source?.sha256)
  return deny('LOAD_PACKET_EXACT_SOURCE_FAMILY_MISMATCH');
 // An exact R0 source with only unresolved rights/ACL may appear in a PRIVATE
 // H0 review as a HOLD. All other blocking conditions remain denied.
 const rightsHold=packet.state==='REVIEW_WITH_HOLDS';
 if(rightsHold&&(!Array.isArray(packet.convergence.blockers)||
   packet.convergence.blockers.length!==1||
   packet.convergence.blockers[0]!==`UNCLASSIFIED_RIGHTS_OR_ACL:${objectId}@${packet.envelope.manifest.version}`))
  return deny('LOAD_PACKET_UNRELATED_BLOCKERS');
 const view=projectUniSpace(packet,{audience:'owner',requestedLeaves:[]});
 if(view.state!=='SOURCE_ONLY_PRIVATE_PROJECTION'||
    view.h0?.object_id!==objectId||
    view.hydration?.state!=='HOLD'||
    view.h4?.execution!=='DISABLED_AUTHORITY_HOLD')
  return deny('LOAD_PACKET_REVIEW_OR_INTEGRITY_HOLD');
 // Only these fixed fields are permitted to cross to the private browser.
 return {schema:SCHEMA,state:rightsHold?'SOURCE_RIGHTS_HOLD':'SOURCE_REVIEW_ONLY',
  object_id:objectId,file_space:fileSpace,
  manifest_digest:view.h0.manifest_digest,
  source_digest:view.h0.source_sha256,
  leaf_count:view.h1.leaf_count,
  hydration:'HOLD',source_qualified:false,
  native_admitted:false,network_transfer:false};
}
