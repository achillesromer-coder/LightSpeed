/**
 * Review-only typed intent-to-EXISTING-component binding.
 * Reuses TIR173 dictionary/capsule, LOAD.cgx and original CGX interaction atlas.
 * No authority, source bytes, execution token, mint or model inference.
 */
import {validateDictionary,validateCapsule,TIRError} from './tir173_core.mjs';
import {inspectTir173Intent} from './tir173_intent_guard.mjs';
import {planExistingLoadTIR} from './tir173_load_bridge.mjs';
import {planAtlasInteraction} from './tir173_interaction.mjs';

export const TIR_INTENT_BINDING_SCHEMA='cgx.tir173.intent-existing-plan/0.1';
const need=(ok,reason)=>{if(!ok)throw new TIRError(reason);};
const hold=Object.freeze({
  authority:'REVIEW_ONLY',execution_performed:false,source_bytes_transferred:0,
  source_hydrated:false,rights_verified:false,geometry_verified:false,
  native_admitted:false,physical_interaction_established:false,
  model_inference_performed:false,model_weights_changed:false,
  mint_performed:false,signed_dbr:false,automatic_baseline_promotion:false
});
function validateContext(dictionary,capsule,context){
  validateDictionary(dictionary);validateCapsule(dictionary,capsule);
  need(context&&context.schema==='cgx.guios.tir173.context/0.1'&&
    context.authority==='REVIEW_ONLY'&&context.native_admitted===false&&
    context.execution_performed===false&&context.interaction?.relation_established===false,
    'REVIEW_GUIOS_CONTEXT_REQUIRED');
  need(context.shape_role===capsule.shape_role&&
    context.object_ref===capsule.object_ref&&
    context.geometry_ref===capsule.geometry_ref&&
    context.dictionary_source_sha256===dictionary.source_sha256,
    'GUIOS_CONTEXT_CAPSULE_IDENTITY_MISMATCH');
}
function humanView(status,review,adapted){
  return {
    summary:review.human.summary,
    interpretation:status==='ABSTAIN_REVIEW_REQUIRED'
      ? review.human.status
      : status==='EXISTING_LOAD_PLAN_REVIEW'
        ? 'Existing LOAD.cgx planning only. No hydration, rights or lease verified.'
        : status==='EXISTING_ATLAS_RULE_REVIEW'
          ? 'Original CGX atlas is a candidate engineering rule, not verified behaviour of this shape.'
          : 'Recognised shorthand has no admitted operation; inputs and independent evidence remain required.',
    missing_inputs:review.machine.required_inputs||[],
    linked_existing_component:adapted?.schema||null,
    next_action:'Source/rights qualification and independent review before any operation.',
    authority:'Review only'
  };
}
/**
 * Recomputes the exact command from text. Untrusted model guesses or forged
 * accepted-intent objects cannot bypass the parser. Existing plans must pass
 * their original strict authority checks.
 * loadPlan is the existing GUIOS/LOAD contract; atlasSelection is a candidate
 * rule ID and source-byte digest claim. No physical material is inferred.
 */
export function bindTirIntentToExistingPlans(
  dictionary,capsule,context,{command,loadPlan=null,atlas=null,atlasSelection=null}={}
){
  validateContext(dictionary,capsule,context);
  const intent_review=inspectTir173Intent(dictionary,command,{expected_role:capsule.shape_role});
  const parsed=intent_review.machine;
  need(parsed.schema==='cgx.tir173.intent_review/0.1','EXACT_INTENT_GUARD_REQUIRED');
  let status='ABSTAIN_REVIEW_REQUIRED',adapter=null;
  if(parsed.status==='EXACT_CANONICAL_REVIEW_PLAN'){
    need(parsed.dictionary_source_sha256===dictionary.source_sha256&&
      parsed.mesh_ref===capsule.geometry_ref&&parsed.shape_role===capsule.shape_role,
      'TIR_INTENT_DICTIONARY_IDENTITY_MISMATCH');
    if(parsed.intent==='PLAN_HYDRATE'&&loadPlan!==null){
      // The shared LOAD seam validates both levels and explicit offline degradation.
      adapter=planExistingLoadTIR(dictionary,capsule,loadPlan);
      need(adapter.source_bytes_transferred===0&&adapter.source_hydrated===false&&
        adapter.native_admitted===false&&adapter.execution_performed===false,
        'LOAD_AUTHORITY_ESCALATION');
      status='EXISTING_LOAD_PLAN_REVIEW';
    }else if(parsed.intent==='ATLAS_RULE'&&atlas!==null&&atlasSelection!==null){
      adapter=planAtlasInteraction(atlas,capsule,context,atlasSelection);
      need(adapter.status==='SOURCE_RULE_CANDIDATE_ONLY'&&
        adapter.execution_performed===false&&adapter.native_admitted===false&&
        adapter.physical_interaction_established===false&&adapter.rights_verified===false,
        'ATLAS_AUTHORITY_ESCALATION');
      status='EXISTING_ATLAS_RULE_REVIEW';
    }else{
      status=parsed.intent==='SELECT'?'DICTIONARY_REFERENCE_REVIEW':'OPERANDS_OR_ADAPTER_REQUIRED';
    }
  }
  const machine={
    schema:TIR_INTENT_BINDING_SCHEMA,status,
    identity:{object_ref:capsule.object_ref,shape_role:capsule.shape_role,
      geometry_ref:capsule.geometry_ref,source_dictionary_sha256:dictionary.source_sha256},
    selected_intent:parsed.intent,
    intent_status:parsed.status,
    existing_component:adapter?.schema||null,
    missing_inputs:parsed.required_inputs||[],
    adapter_result:adapter,
    ...hold
  };
  return {schema:TIR_INTENT_BINDING_SCHEMA,intent_review,
    machine,human:humanView(status,intent_review,adapter)};
}
