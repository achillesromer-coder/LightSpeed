/** Integrates a qualified TIR/173 capsule into the EXISTING LOAD review-plan contract.
 * The adapter never consumes caller 'rights cleared' as native authority. */
import {validateCapsule,validateDictionary,TIRError} from './tir173_core.mjs';
export const LOAD_SEAM_SCHEMA='cgx.tir173.existing-load-seam/0.1';
export function planExistingLoadTIR(dictionary,capsule,loadPlan){
 validateDictionary(dictionary);validateCapsule(dictionary,capsule);
 if(!loadPlan||loadPlan.schema!=='UNISPACE-CGX-LOAD-LENS-PLAN/0.1'||loadPlan.state!=='PLAN_ONLY_NOT_HYDRATED'||loadPlan.alias!=='LOAD.cgx'||
  loadPlan.parent_filespace!=='Cognigrex.cgx'||loadPlan.object_id!==capsule.object_ref||loadPlan.native_admitted!==false||
  loadPlan.hydrated!==false||loadPlan.execution_performed!==false||loadPlan.public_publish_authorized!==false||loadPlan.canonical_mutation!==false||
  loadPlan.host_context_readback_authenticated!==false||loadPlan.source_rights_independently_verified!==false||loadPlan.client_scope_independently_authenticated!==false)
  throw new TIRError('EXISTING_LOAD_REVIEW_PLAN_REQUIRED');
 if(!['H0','H1','H2','H3'].includes(loadPlan.planned_hydration))throw new TIRError('INVALID_HYDRATION_LEVEL');
 return {schema:LOAD_SEAM_SCHEMA,identity:capsule.object_ref,parent:'Cognigrex.cgx',resolver_alias:'LOAD.cgx',
  grammar:capsule.schema,shape_role:capsule.shape_role,geometry_ref:capsule.geometry_ref,ordinal_address:capsule.ordinal_address,
  source_dictionary_sha256:dictionary.source_sha256,requested_level:loadPlan.requested_hydration,planned_level:loadPlan.planned_hydration,
  source_layer:'R0_REVIEW_PLAN',source_ref:capsule.source_ref,
  proposed_scales:capsule.scale_lenses,unknown_detail:capsule.scale_lenses?.fine?.status!=='HYDRATED',
  source_hydrated:false,source_bytes_transferred:0,native_admitted:false,execution_performed:false,signed_dbr:false,
  claim_boundary:'This is a typed LOAD planning crosswalk. Host must independently verify rights/lease/source checksum/ACL before any source access.'};
}