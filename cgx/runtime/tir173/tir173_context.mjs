/**
 * GUIOS contextual projection for the existing TIR/173 kernel.
 * One object/shape identity, multiple environmental and observational lenses.
 * A spatial word is a hypothesis until evidence/rights/host admission establish it.
 */
import {validateDictionary,validateCapsule,TIRError} from './tir173_core.mjs';
export const GUIOS_CONTEXT_SCHEMA='cgx.guios.tir173.context/0.1';
export const ENVIRONMENTS=Object.freeze(['digital','physical','simulated','hybrid']);
export const SPATIAL_RELATIONS=Object.freeze(['in','on','through','across','around','between']);
export const PERSPECTIVES=Object.freeze(['top_down','bottom_up','intersection','side','void']);
const requireCondition=(ok,code)=>{if(!ok)throw new TIRError(code);};
const isToken=(v)=>typeof v==='string'&&v.length<=150&&/^[A-Za-z0-9][A-Za-z0-9:./_#-]*$/.test(v);
/**
 * Produces a single deterministic read-only context record; it does not infer
 * an object's material, interaction physics, or geometric topology from its role.
 * 'void' is a meaningful view of unavailable constraints, not empty evidence.
 */
export function projectGuiosContext(dictionary,capsule,options={}){
 validateDictionary(dictionary);validateCapsule(dictionary,capsule);
 const {environment='digital',spatial='in',perspective='intersection',scale_ratio=1,
  environment_ref='review:environment',source_ref='review:context',evidence='UNRESOLVED'}=options;
 requireCondition(ENVIRONMENTS.includes(environment),'ENVIRONMENT_NOT_REGISTERED');
 requireCondition(SPATIAL_RELATIONS.includes(spatial),'SPATIAL_RELATION_NOT_REGISTERED');
 requireCondition(PERSPECTIVES.includes(perspective),'PERSPECTIVE_NOT_REGISTERED');
 requireCondition(typeof scale_ratio==='number'&&Number.isFinite(scale_ratio)&&scale_ratio>0&&scale_ratio<=1e12,'SCALE_RATIO_INVALID');
 requireCondition(isToken(environment_ref)&&isToken(source_ref),'CONTEXT_SOURCE_REQUIRED');
 requireCondition(['UNRESOLVED','NO_DATA','NOT_AUTHORISED','NOT_CACHED','WITHHELD'].includes(evidence),'EVIDENCE_REQUIRES_INDEPENDENT_PROOF');
 const context={
  schema:GUIOS_CONTEXT_SCHEMA,authority:'REVIEW_ONLY',object_ref:capsule.object_ref,shape_role:capsule.shape_role,
  geometry_ref:capsule.geometry_ref,dictionary_source_sha256:dictionary.source_sha256,
  environment:{kind:environment,reference:environment_ref,source_ref,evidence},
  interaction:{spatial,relation_established:false,evidence},
  perspective,scale:{source_magnitude:capsule.magnitude,ratio:scale_ratio,observed_magnitude:capsule.magnitude*scale_ratio,unit:capsule.unit,frame:capsule.frame},
  negative_space:{unresolved_fine:capsule.scale_lenses.fine?.status!=='HYDRATED',
   environment_constraints_unknown:evidence!=='SUPPORTED',empty_space_is_context:true},
  hydration:{resolver:'LOAD.cgx',status:'PLAN_ONLY_NOT_HYDRATED',requires_existing_acl_lease_rights:true},
  execution_performed:false,native_admitted:false,automatic_promotion:false
 };
 requireCondition(Number.isFinite(context.scale.observed_magnitude)&&context.scale.observed_magnitude>0,'SCALED_MAGNITUDE_OVERFLOW');
 return {context,
  human:{object:capsule.label||capsule.object_ref,shape:capsule.shape_role,
   description:'View '+perspective.replace('_',' ')+' of '+environment+' context: '+spatial+'; relation remains unverified.',
   view_scale:context.scale.observed_magnitude+' '+capsule.unit,environment_reference:environment_ref,
   evidence,negative_space:context.negative_space,authority:'review only'},
  machine:{schema:GUIOS_CONTEXT_SCHEMA,context,identity_unchanged:true,source_dictionary_sha256:dictionary.source_sha256}
 };
}
