import type {ShapeDictionary,ShapeCapsule} from './tir173_core.mjs';
export declare const LOAD_SEAM_SCHEMA:'cgx.tir173.existing-load-seam/0.1';
export interface ExistingLoadReviewPlan {
 schema:'UNISPACE-CGX-LOAD-LENS-PLAN/0.1';
 state:'PLAN_ONLY_NOT_HYDRATED';alias:'LOAD.cgx';parent_filespace:'Cognigrex.cgx';object_id:string;
 native_admitted:false;hydrated:false;execution_performed:false;public_publish_authorized:false;
 canonical_mutation:false;host_context_readback_authenticated:false;source_rights_independently_verified:false;
 client_scope_independently_authenticated:false;requested_hydration:string;planned_hydration:'H0'|'H1'|'H2'|'H3';
}
export declare function planExistingLoadTIR(dictionary:ShapeDictionary,capsule:ShapeCapsule,plan:ExistingLoadReviewPlan):{
 schema:typeof LOAD_SEAM_SCHEMA;identity:string;parent:string;resolver_alias:string;grammar:string;shape_role:string;geometry_ref:string;
 ordinal_address:string;source_dictionary_sha256:string;requested_level:string;planned_level:string;source_layer:string;
 source_ref:string;source_hydrated:false;source_bytes_transferred:0;native_admitted:false;execution_performed:false;signed_dbr:false;
 claim_boundary:string;[key:string]:unknown;
};