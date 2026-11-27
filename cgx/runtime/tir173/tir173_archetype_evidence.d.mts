import type {ShapeDictionary,ShapeCapsule} from './tir173_core.mjs';
export declare const TIR_ARCHETYPE_EVIDENCE_SCHEMA:'cgx.tir173.existing-archetype-review/0.1';
export declare const CGX_GEOMETRY_ATLAS_SCHEMA:'CGX-COMPONENT-GEOMETRY-ATLAS/0.1';
export declare const CGX_PHYSICAL_LADDER_SCHEMA:'CGX-G1-COMPONENT-PROOF-LADDER/0.1';
export declare const CGX_INSTANCE_PACKET_SCHEMA:'CGX-COMPONENT-INSTANCE-BUILD-PACKET/0.1';
export type ArchetypeReviewMachine={
 schema:typeof TIR_ARCHETYPE_EVIDENCE_SCHEMA;
 status:'EXPLICIT_ARCHETYPE_CANDIDATE_REVIEW'|'NO_ARCHETYPE_SELECTED';
 shape_role:string;object_ref:string;geometry_ref:string;shape_evidence:string;
 dictionary_source_sha256:string;archetype_id:string|null;
 declared_archetype:null|{
  name:string;family:string;domain:string;baseline_geometry:string;
  geometric_parameters:string;scale_band:string;atlas_evidence_label:string;
  source_authority_class:string;
 };
 proof_ladder_representative_stages:Array<{
  stage:string;name:string;physical_state:'NOT_RUN';hard_gate:string;representative_only:true}>;
 proof_stages_total:11;original_physical_state:'NOT_RUN';
 source_claims:{geometry_atlas_sha256:string;proof_ladder_sha256:string;instance_contract_sha256:string};
 source_claims_authenticated:false;archetype_to_shape_mapping_verified:false;
 exact_instance_bound:false;geometry_verified:false;material_verified:false;
 rights_verified:false;physical_test_performed:false;physical_evidence_established:false;
 model_inference_performed:false;execution_performed:false;source_bytes_transferred:0;
 mint_performed:false;native_admitted:false;signed_dbr:false;
 automatic_baseline_promotion:false;negative_space:string[];
 authority:'REVIEW_ONLY';
};
export declare function verifyOriginalGeometrySources(atlas:unknown,ladder:unknown,packet:unknown):{
 geometry_records:411;proof_stages:11;physical_test_stage_count:0;
 physical_state:'NOT_RUN';authority:'DRIVE_OWNED_GIT_MIRROR_REVIEW_ONLY';native_admitted:false
};
export declare function reviewTirComponentArchetype(
 dictionary:ShapeDictionary,capsule:ShapeCapsule,
 atlas:unknown,ladder:unknown,packet:unknown,
 opts?:{archetype_id?:string|null;source_claims:{
   geometry_atlas_sha256:string;proof_ladder_sha256:string;instance_contract_sha256:string}}
):{machine:ArchetypeReviewMachine;human:{
 summary:string;shape:string;interpretation:string;physical_state:string;
 proof_stages:string;outstanding:string;authority:string
}};
