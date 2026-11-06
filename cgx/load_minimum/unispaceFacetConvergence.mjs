/**
 * UniSpace NOV-01: source-only, non-installing facet route convergence.
 * Reuses #174/#188 public synthetic views, #192 private Objects and #205
 * LOAD inspector; it is NOT another router, engine, host ACL or CGX root.
 * Never import a private module into Vite public/static output (#158).
 */
import {planUniSpaceOperatorCockpit} from './unispaceSourceInspector.mjs';
// Private browser UI consumes only a sanitised server-side review binding.
// No Node crypto, raw source carrier, issuer or transport API is imported here.
const PACKET_SCHEMA='CGX-PRIVATE-LOAD-BINDING-REVIEW/0.1';

export const FACET_CONVERGENCE_SCHEMA='UNISPACE-FACET-CONVERGENCE/0.1';
const publicFacets=Object.freeze({
 '/cgx':       Object.freeze({facet:'overview',proof:'PUBLIC_SAFE_SYNTHETIC'}),
 '/cgx/fs':    Object.freeze({facet:'filespace',proof:'PUBLIC_SAFE_SYNTHETIC'}),
 '/cgx/ds':    Object.freeze({facet:'dataspace',proof:'SIMULATED_NOT_AUTHENTICATED'}),
 '/cgx/ps':    Object.freeze({facet:'printspace',proof:'NUMERIC_DEMO_NOT_PHYSICAL'}),
 '/cgx/doom':  Object.freeze({facet:'doom',proof:'CREATIVE_REFERENCE_NOT_GAME_ENGINE'}),
 '/cgx/romer': Object.freeze({facet:'romer',proof:'PUBLIC_SAFE_SYNTHETIC'}),
 '/cgx/eco':   Object.freeze({facet:'eco',proof:'PUBLIC_SAFE_SYNTHETIC'})
});
const deny=reason=>({schema:FACET_CONVERGENCE_SCHEMA,status:'DENIED',reason,
 host_authenticated:false,native_admitted:false,may_execute:false,
 provider_readback:false,deployed:false,public_release:false,canonical_mutation:false});

/** A pure review planner, not an authenticated route handler or static exporter.
 * Public routes must not receive any private selection/inspector/host evidence.
 * The sole private Objects route delegates exact identity and parent validation
 * to the existing LOAD cockpit planner; no second Object_ID resolver is minted.
 */
export function planUniSpaceFacetConvergence({
 surface=null,route=null,selection=null,inspector=null,offline=false,hostReceipt=null,sourcePacket=null
}={}){
 if(typeof offline!=='boolean'||typeof route!=='string'||route.length>128)
  return deny('INVALID_ROUTE_OR_MODE');
 if(surface==='public'){
  if(selection!==null||inspector!==null||hostReceipt!==null||sourcePacket!==null||offline)
   return deny('PUBLIC_ROUTE_PRIVATE_CONTEXT_FORBIDDEN');
  if(!Object.hasOwn(publicFacets,route))
   return deny('PUBLIC_ROUTE_NOT_ALLOWLISTED');
  const f=publicFacets[route];
  return {schema:FACET_CONVERGENCE_SCHEMA,status:'SOURCE_REVIEW_ONLY',
   route,facet:f.facet,evidence_ceiling:f.proof,
   source_prs:[174,188],render_mode:'SYNTHETIC_SOURCE_REVIEW',
   selected_object_id:null,selected_file_space:null,
   source_bytes_read:false,host_authenticated:false,native_admitted:false,
   may_execute:false,provider_readback:false,deployed:false,
   public_release:false,canonical_mutation:false};
 }
 if(surface!=='private')return deny('PRIVATE_OR_PUBLIC_SURFACE_REQUIRED');
 if(route!=='/operator/objects')return deny('PRIVATE_ROUTE_NOT_ALLOWLISTED');
 const p=planUniSpaceOperatorCockpit({surface,selection,inspector,offline,hostReceipt});
 if(p.state!=='SOURCE_REVIEW_ONLY')return deny(p.reason||'PRIVATE_INSPECTOR_HOLD');
 let sourceReview=null;
 if(sourcePacket!==null){
  // This is a strictly inert, redacted review DTO, never an authority receipt.
  const keys=['schema','state','object_id','file_space','manifest_digest','source_digest',
   'leaf_count','hydration','source_qualified','native_admitted','network_transfer'];
  const hex=/^[0-9a-f]{64}$/;
  if(!sourcePacket||typeof sourcePacket!=='object'||Array.isArray(sourcePacket)||
     Object.keys(sourcePacket).length!==keys.length||
     keys.some(key=>!Object.hasOwn(sourcePacket,key))||
     sourcePacket.schema!==PACKET_SCHEMA||sourcePacket.state!=='SOURCE_REVIEW_ONLY'||
     sourcePacket.object_id!==p.identity||sourcePacket.file_space!==p.file_space||
     !hex.test(sourcePacket.manifest_digest??'')||!hex.test(sourcePacket.source_digest??'')||
     !Number.isSafeInteger(sourcePacket.leaf_count)||sourcePacket.leaf_count<1||
     sourcePacket.leaf_count>1024||sourcePacket.hydration!=='HOLD'||
     sourcePacket.source_qualified!==false||sourcePacket.native_admitted!==false||
     sourcePacket.network_transfer!==false)
   return deny('LOAD_PACKET_EXACT_SOURCE_FAMILY_MISMATCH');
  sourceReview={manifest_digest:sourcePacket.manifest_digest,
   source_digest:sourcePacket.source_digest,leaf_count:sourcePacket.leaf_count,
   hydration:'HOLD',source_qualified:false,installed_capabilities_verified:false,
   native_admitted:false,network_transfer:false};
 }
 return {schema:FACET_CONVERGENCE_SCHEMA,status:'SOURCE_REVIEW_ONLY',
  route,facet:'private_object_inspector',source_prs:[192,205],
  selected_object_id:p.identity,selected_file_space:p.file_space,
  presentation_stage:p.presentation_stage,view:p.view,
  evidence_ceiling:p.evidence_ceiling,
  render_mode:'INERT_PRIVATE_REVIEW',source_review:sourceReview,
  source_bytes_read:false,host_authenticated:false,native_admitted:false,
  may_execute:false,provider_readback:false,deployed:false,
  public_release:false,canonical_mutation:false};
}
