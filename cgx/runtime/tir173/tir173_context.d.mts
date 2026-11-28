import type {ShapeDictionary,ShapeCapsule} from './tir173_core.mjs';
export declare const GUIOS_CONTEXT_SCHEMA:'cgx.guios.tir173.context/0.1';
export declare const ENVIRONMENTS:readonly ['digital','physical','simulated','hybrid'];
export declare const SPATIAL_RELATIONS:readonly ['in','on','through','across','around','between'];
export declare const PERSPECTIVES:readonly ['top_down','bottom_up','intersection','side','void'];
export interface GuiosContextOptions {environment?:typeof ENVIRONMENTS[number];spatial?:typeof SPATIAL_RELATIONS[number];perspective?:typeof PERSPECTIVES[number];scale_ratio?:number;environment_ref?:string;source_ref?:string;evidence?:'UNRESOLVED'|'NO_DATA'|'NOT_AUTHORISED'|'NOT_CACHED'|'WITHHELD';}
export function projectGuiosContext(dictionary:ShapeDictionary,capsule:ShapeCapsule,options?:GuiosContextOptions):{
 context:{schema:typeof GUIOS_CONTEXT_SCHEMA;object_ref:string;shape_role:string;geometry_ref:string;
  environment:{kind:string;reference:string;source_ref:string;evidence:string};
  interaction:{spatial:string;relation_established:boolean;evidence:string};
  perspective:string;scale:{observed_magnitude:number;unit:string;frame:string};negative_space:{unresolved_fine:boolean;environment_constraints_unknown:boolean;empty_space_is_context:boolean};
  execution_performed:boolean;native_admitted:boolean;[key:string]:unknown};
 human:{object:string;shape:string;description:string;view_scale:string;environment_reference:string;evidence:string;negative_space:{[key:string]:unknown};authority:string};
 machine:{schema:typeof GUIOS_CONTEXT_SCHEMA;context:{[key:string]:unknown};identity_unchanged:boolean;source_dictionary_sha256:string};
};