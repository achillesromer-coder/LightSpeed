export declare const TIR_ATLAS_SEAM_SCHEMA: 'cgx.tir173.component-interaction-plan/0.1';
export declare const ATLAS_SCHEMA: 'CGX-COMPONENT-INTERACTION-MAP/0.1';
export declare class InteractionSeamError extends Error { readonly code:string; constructor(code:string); }
export type AtlasCandidate = {id:string;source_family:string;target_family:string;interaction:string;source_evidence:string};
export type AtlasInteractionPlan = {
 schema:string;status:'SOURCE_RULE_CANDIDATE_ONLY';native_admitted:false;rights_verified:false;geometry_verified:false;
 physical_interaction_established:false;simulation_performed:false;execution_performed:false;mint_performed:false;
 source:{atlas_schema:string;atlas_sha256_claim:string;atlas_row:string;authority_reference:string;source_evidence_state:string;source_family:string;target_family:string;source_facet_ref:string|null;target_facet_ref:string|null};
 geometry:{object_ref:string;shape_role:string;geometry_ref:string;spatial_relation:string;environment_kind:string;frame:string;unit:string;observed_magnitude:number};
 required_variables:{geometry:string[];state:string[]};missing_variables:string[];measurements_self_declared:string[];
 interaction:{name:string;mechanism_as_described_by_source:string;baseline_model:string;higher_order_trigger:string|null;source_design_rule:string|null;source_validation_test:string;mitigation:string|null};
 holds:string[];human:{title:string;summary:string;interpretation:string;next_test:string;boundary:string};
 machine:{typed_role:string;object_ref:string;source_dictionary_sha256:string;atlas_rule_id:string;atlas_sha256_claim:string;relation_established:false;authority:'REVIEW_ONLY'};
};
export declare function verifyComponentInteractionAtlas(atlas:unknown):{schema:string;records:number;authority:string;native_admitted:false};
export declare function listAtlasInteractions(atlas:unknown,filters?:{source_family?:string|null;target_family?:string|null;limit?:number}):AtlasCandidate[];
export declare function planAtlasInteraction(atlas:unknown,capsule:unknown,lens:unknown,opts?:{rule_id:string;source_sha256:string;source_facet_ref?:string|null;target_facet_ref?:string|null;measured?:Record<string,{value:number;unit:string;source_ref:string}>}):AtlasInteractionPlan;