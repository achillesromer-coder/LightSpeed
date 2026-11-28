/**
 * Neo / GUIOS TIR173 exact-intent review gate.
 * A strict interface to the EXISTING shape dictionary, not a language model
 * or independent execution engine. No native action occurs in this module.
 */
import {validateDictionary,normaliseRole,encodeOrdinal,slotName} from './tir173_core.mjs';

export const TIR173_INTENT_GUARD_SCHEMA = 'cgx.tir173.intent_review/0.1';
export const TIR173_REVIEW_INTENTS = Object.freeze([
  'SELECT','RELATE','TRIAD','PLAN_HYDRATE','PLAN_TRANSFORM',
  'ENCODE_BYTES','DECODE_BYTES','ATLAS_RULE'
]);
const CANONICAL = /^(SELECT|RELATE|TRIAD|PLAN_HYDRATE|PLAN_TRANSFORM|ENCODE_BYTES|DECODE_BYTES|ATLAS_RULE) (T173:\d{3})$/;
const ROLE_PATTERN = /T173:\d{3}/g;
const NEEDS = Object.freeze({
  SELECT:['GEOMETRY_SOURCE_RIGHTS','OBJECT_IDENTITY'],
  RELATE:['SECOND_ROLE_OR_OBJECT','RELATION_PREDICATE','RELATION_EVIDENCE'],
  TRIAD:['THREE_INDEPENDENT_FACET_STATES','STATE_SOURCE_AND_EVIDENCE'],
  PLAN_HYDRATE:['LOAD_ACL','LEASE','SOURCE_RIGHTS','HYDRATION_SCOPE'],
  PLAN_TRANSFORM:['NUMERIC_TRANSFORM','FRAME','UNIT','TOLERANCE','RIGHTS'],
  ENCODE_BYTES:['INPUT_STATES_OR_BYTES','EXACT_PAYLOAD_AND_VERSION'],
  DECODE_BYTES:['BINARY_CARRIER','CODEC_VERSION','VALIDATION'],
  ATLAS_RULE:['EXISTING_ATLAS_RULE_ID','MATERIAL_FACET','MEASUREMENTS','SOURCE_RIGHTS']
});
const boundary = {
  authority:'REVIEW_ONLY',source_rights_verified:false,geometry_qualified:false,
  command_executed:false,native_admitted:false,model_approved:false,
  hydration_performed:false,simulation_performed:false,mint_performed:false,
  model_weights_changed:false,physical_rule_inferred:false
};
const human = machine => machine.status === 'EXACT_CANONICAL_REVIEW_PLAN' ?
  {
    summary:machine.intent+' · '+machine.shape_role+' ('+machine.address_trits+')',
    status:'Parsed as an incomplete review plan; no operation executed',
    missing:machine.required_inputs.join(', '),
    geometry:'Reference '+machine.mesh_ref+'; source evidence: '+machine.source_geometry_evidence,
    authority:'Review only'
  } : {
    summary:'No executable interpretation',
    status:'Abstain: '+machine.reason,
    missing:machine.explanation,
    authority:'Review only'
  };
function abstain(reason, explanation, role=null, trits=null) {
  const machine={schema:TIR173_INTENT_GUARD_SCHEMA,status:'ABSTAIN_REVIEW_REQUIRED',
    reason,explanation,shape_role:role,address_trits:trits,intent:null,
    ...boundary};
  return {machine,human:human(machine)};
}
/**
 * Binds a typed command to the chosen GUIOS object when expected_role is set.
 * Unknown/ambiguous text MUST abstain; it is never inferred from a model guess.
 * Returned context is a plan, without argument values or privileged effects.
 */
export function inspectTir173Intent(dictionary,input,{expected_role=null}={}) {
  validateDictionary(dictionary);
  if (typeof input !== 'string' || input.length<1 || input.length>240)
    return abstain('INPUT_BOUNDS','Text must be 1–240 characters');
  const value=input.trim();
  if (!value)return abstain('INPUT_EMPTY','No shorthand command supplied');
  const matches=value.match(ROLE_PATTERN)||[];
  if (matches.length !== 1)
    return abstain('ROLE_ARITY','Exactly one T173 role is required');
  let role;
  try {role=normaliseRole(matches[0]);}
  catch {return abstain('ROLE_INVALID','Valid shape roles are 001–173; 174 is reserved');}
  const name=slotName(role),trits=encodeOrdinal(role);
  const match=CANONICAL.exec(value);
  if (!match)
    return abstain('NONCANONICAL_OR_AMBIGUOUS',
      'Use an exact registered operation followed by one T173 role, with no additional effects',
      name,trits);
  if(expected_role!==null) {
    let expected;
    try {expected=normaliseRole(expected_role);}
    catch {return abstain('INVALID_GUIOS_SELECTION','Current object role is invalid',name,trits);}
    if(expected!==role)
      return abstain('ROLE_CONTEXT_MISMATCH',
        'Command role does not match the selected GUIOS object',name,trits);
  }
  const intent=match[1];
  const selected=dictionary.roles[role-1];
  const machine={
    schema:TIR173_INTENT_GUARD_SCHEMA,status:'EXACT_CANONICAL_REVIEW_PLAN',
    intent,shape_role:name,address_trits:trits,mesh_ref:selected.mesh_ref,
    dictionary_source_sha256:dictionary.source_sha256,
    source_geometry_evidence:selected.evidence,
    required_inputs:[...NEEDS[intent]],all_inputs_qualified:false,
    operation_complete:false,
    ...boundary
  };
  return {machine,human:human(machine)};
}
