export interface ShapeRole {slot:number;role:string;name:string;family:string;mesh_ref:string;evidence:string;lexical_tokens?:string[];}
export interface ShapeDictionary {schema:'cgx.t173.shape_dictionary/0.2';roles:ShapeRole[];source_sha256:string;sentinel:null;}
export type Trit=-1|0|1;
export type Validity='SUPPORTED'|'REFUTED'|'UNRESOLVED'|'CONFLICT'|'NO_DATA'|'WITHHELD'|'NOT_AUTHORISED'|'INVALID'|'NOT_CACHED';
export interface ShapeCapsule {schema:'cgx.tir173/0.2';authority:string;object_ref:string;local_path:number[];shape_role:string;geometry_ref:string;ordinal_address:string;state:{basis:string;trit:Trit;validity:Validity};[key:string]:unknown;}
export function validateDictionary(d:ShapeDictionary):{roles:number;unique_mesh_refs:number;source:string;status:string};
export function encodeOrdinal(n:number):string;
export function pack173(trits:Trit[]):Uint8Array;
export function makeCapsule(d:ShapeDictionary,opts:{path:number[];shape:number;label?:string;object_ref?:string;source_ref?:string;coarse?:{level:number;status:string;source_ref?:string;value?:unknown};fine?:{level:number;status:string;source_ref?:string;value?:unknown};state?:{basis:string;trit:Trit;validity:Validity};relations?:{predicate:string;target:string;evidence:Validity}[];[key:string]:unknown}):ShapeCapsule;
export function reconcileThreeVoices(voices:{voice:string;trit:Trit;validity:Validity;source_ref:string}[]):{conflict:boolean;epistemic:string;combined_state:Trit|null;automatic_promotion:boolean};
export function encodeBinaryTransport(value:unknown):Uint8Array;
export function hex(bytes:Uint8Array):string;

export function packThreeLines(lines:Record<"intuitive"|"deliberative"|"assurance",Trit[]>):Uint8Array;
export function unpackThreeLines(bytes:Uint8Array):Record<string,Trit[]>;