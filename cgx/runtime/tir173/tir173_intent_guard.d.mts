import type {ShapeDictionary} from './tir173_core.mjs';
export declare const TIR173_INTENT_GUARD_SCHEMA:'cgx.tir173.intent_review/0.1';
export declare const TIR173_REVIEW_INTENTS:readonly [
  'SELECT','RELATE','TRIAD','PLAN_HYDRATE','PLAN_TRANSFORM','ENCODE_BYTES','DECODE_BYTES','ATLAS_RULE'
];
export interface IntentReviewMachine {
  schema:typeof TIR173_INTENT_GUARD_SCHEMA;
  status:'EXACT_CANONICAL_REVIEW_PLAN'|'ABSTAIN_REVIEW_REQUIRED';
  shape_role:string|null;
  address_trits:string|null;
  intent:string|null;
  reason?:string;
  explanation?:string;
  mesh_ref?:string;
  dictionary_source_sha256?:string;
  source_geometry_evidence?:string;
  required_inputs?:string[];
  all_inputs_qualified?:false;
  operation_complete?:false;
  authority:'REVIEW_ONLY';
  source_rights_verified:false;
  geometry_qualified:false;
  command_executed:false;
  native_admitted:false;
  model_approved:false;
  hydration_performed:false;
  simulation_performed:false;
  mint_performed:false;
  model_weights_changed:false;
  physical_rule_inferred:false;
}
export interface IntentReviewHuman {
  summary:string;
  status:string;
  missing:string;
  geometry?:string;
  authority:'Review only';
}
export declare function inspectTir173Intent(
  dictionary:ShapeDictionary,
  input:unknown,
  options?:{expected_role?:string|number|null}
):{machine:IntentReviewMachine;human:IntentReviewHuman};
