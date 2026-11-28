import type {ShapeDictionary,ShapeCapsule} from './tir173_core.mjs';
import type {ExistingLoadReviewPlan,planExistingLoadTIR} from './tir173_load_bridge.mjs';
import type {AtlasInteractionPlan} from './tir173_interaction.mjs';
import type {IntentReviewMachine,IntentReviewHuman} from './tir173_intent_guard.mjs';
export declare const TIR_INTENT_BINDING_SCHEMA:'cgx.tir173.intent-existing-plan/0.1';
export type TirIntentExistingPlanMachine = {
 schema:typeof TIR_INTENT_BINDING_SCHEMA;
 status:'ABSTAIN_REVIEW_REQUIRED'|'EXISTING_LOAD_PLAN_REVIEW'|'EXISTING_ATLAS_RULE_REVIEW'|'DICTIONARY_REFERENCE_REVIEW'|'OPERANDS_OR_ADAPTER_REQUIRED';
 identity:{object_ref:string;shape_role:string;geometry_ref:string;source_dictionary_sha256:string};
 selected_intent:string|null;intent_status:string;existing_component:string|null;missing_inputs:string[];
 adapter_result:ReturnType<typeof planExistingLoadTIR>|AtlasInteractionPlan|null;
 authority:'REVIEW_ONLY';execution_performed:false;source_bytes_transferred:0;
 source_hydrated:false;rights_verified:false;geometry_verified:false;
 native_admitted:false;physical_interaction_established:false;
 model_inference_performed:false;model_weights_changed:false;mint_performed:false;
 signed_dbr:false;automatic_baseline_promotion:false;
};
export type TirIntentExistingPlanHuman = {
 summary:string;interpretation:string;missing_inputs:string[];
 linked_existing_component:string|null;next_action:string;authority:'Review only'
};
export declare function bindTirIntentToExistingPlans(
 dictionary:ShapeDictionary,capsule:ShapeCapsule,context:unknown,
 options?:{
  command:unknown;
  loadPlan?:ExistingLoadReviewPlan|null;
  atlas?:unknown;
  atlasSelection?:{
    rule_id:string;source_sha256:string;
    source_facet_ref?:string|null;target_facet_ref?:string|null;
    measured?:Record<string,{value:number;unit:string;source_ref:string}>
  }|null;
 }
):{
 schema:typeof TIR_INTENT_BINDING_SCHEMA;
 intent_review:{machine:IntentReviewMachine;human:IntentReviewHuman};
 machine:TirIntentExistingPlanMachine;
 human:TirIntentExistingPlanHuman;
};
