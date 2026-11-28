/**
 * Existing-CGX-atlas / TIR173 physical-interaction seam, v0.1.
 * Inert, deterministic and review-only. It neither confers physical evidence
 * nor executes a simulation, source hydration, actuator or native operation.
 */
export const TIR_ATLAS_SEAM_SCHEMA = 'cgx.tir173.component-interaction-plan/0.1';
export const ATLAS_SCHEMA = 'CGX-COMPONENT-INTERACTION-MAP/0.1';
export class InteractionSeamError extends Error { constructor(code) { super(code); this.code = code; } }
const requireValue = (condition, code) => { if (!condition) throw new InteractionSeamError(code); };
const own = (a, k) => Object.prototype.hasOwnProperty.call(a, k);
const goodText = x => typeof x === 'string' && x.length > 0 && x.length <= 300 && !/[\u0000-\u001f]/.test(x);
const ref = x => typeof x === 'string' && x.length > 0 && x.length <= 160 && /^[A-Za-z0-9][A-Za-z0-9:./_#-]*$/.test(x);
const sha = x => typeof x === 'string' && /^[a-f0-9]{64}$/.test(x);
const properties = x => x.split(';').map(s => s.trim()).filter(Boolean);
const TYPES = Object.freeze(['physical','hybrid','simulated','digital']);
export function verifyComponentInteractionAtlas(atlas) {
  requireValue(atlas && atlas.schema === ATLAS_SCHEMA && Array.isArray(atlas.records), 'NOT_EXISTING_CGX_INTERACTION_ATLAS');
  requireValue(atlas.records.length > 0 && atlas.records.length <= 4096 && atlas.record_count === atlas.records.length, 'ATLAS_RECORD_COUNT_MISMATCH');
  requireValue(atlas.authority && goodText(atlas.authority.drive_sheet) && goodText(atlas.authority.rule), 'ORIGINAL_ATLAS_AUTHORITY_MISSING');
  const ids = new Set();
  for (const entry of atlas.records) {
    requireValue(entry && /^CIM-\d{3}$/.test(entry.ID) && !ids.has(entry.ID), 'INVALID_OR_DUPLICATE_INTERACTION_ID');
    ids.add(entry.ID);
    for(const key of ['Source Family','Target Family','Interaction Type','Mechanism','Baseline Model','Evidence State','Validation Test'])
      requireValue(goodText(entry[key]), 'ATLAS_SOURCE_FIELD_MISSING');
  }
  return {schema:ATLAS_SCHEMA,records:ids.size,authority:'EXISTING_CGX_COMPONENT_MAP',native_admitted:false};
}
/** No geometry-class / material-family inference is performed. */
export function listAtlasInteractions(atlas,{source_family=null,target_family=null,limit=75}={}) {
  verifyComponentInteractionAtlas(atlas);
  requireValue(Number.isInteger(limit) && limit > 0 && limit <= 4096, 'INVALID_RESULT_LIMIT');
  for (const family of [source_family,target_family]) requireValue(family === null || goodText(family), 'INVALID_FAMILY_SELECTOR');
  return atlas.records.filter(e => (source_family === null || e['Source Family'] === source_family) && (target_family === null || e['Target Family'] === target_family))
    .slice(0,limit).map(e => ({id:e.ID,source_family:e['Source Family'],target_family:e['Target Family'],interaction:e['Interaction Type'],source_evidence:e['Evidence State']}));
}
/**
 * Returns only a conditional source-rule match and a validation plan.
 * `source_sha256` identifies the exact review bytes; a supplied digest is a
 * lineage *claim* until checked by an authenticated independent resolver.
 * This function deliberately has NO 'allow_execution' parameter.
 */
export function planAtlasInteraction(atlas, capsule, lens, {rule_id, source_sha256, source_facet_ref = null, target_facet_ref = null, measured = {}} = {}) {
  verifyComponentInteractionAtlas(atlas);
  requireValue(typeof rule_id === 'string' && /^CIM-\d{3}$/.test(rule_id), 'INTERACTION_ID_REQUIRED');
  requireValue(sha(source_sha256), 'ATLAS_BYTE_DIGEST_REQUIRED');
  requireValue(capsule && capsule.schema === 'cgx.tir173/0.2' && capsule.authority === 'REVIEW_ONLY' && capsule.native_admitted === false && capsule.execution_performed === false,
    'REVIEW_CAPSULE_REQUIRED');
  requireValue(lens && lens.schema === 'cgx.guios.tir173.context/0.1' && lens.authority === 'REVIEW_ONLY' && lens.native_admitted === false && lens.execution_performed === false && lens.interaction?.relation_established === false,
    'UNPRIVILEGED_CONTEXT_REQUIRED');
  requireValue(lens.object_ref === capsule.object_ref && lens.geometry_ref === capsule.geometry_ref && lens.shape_role === capsule.shape_role && lens.dictionary_source_sha256 === capsule.dictionary_source_sha256,
    'LENS_CAPSULE_IDENTITY_MISMATCH');
  requireValue(TYPES.includes(lens.environment?.kind), 'ENVIRONMENT_TYPE_NOT_ALLOWED');
  const rule = atlas.records.find(e=>e.ID === rule_id);
  requireValue(rule !== undefined, 'SOURCE_INTERACTION_ID_NOT_FOUND');
  requireValue((source_facet_ref === null && target_facet_ref === null) || (ref(source_facet_ref) && ref(target_facet_ref)), 'BOTH_COMPONENT_BINDINGS_REQUIRED');
  requireValue(measured && typeof measured === 'object' && !Array.isArray(measured) && Object.keys(measured).length <= 60, 'BAD_MEASUREMENT_MAP');
  for (const [name,m] of Object.entries(measured)) {
    requireValue(goodText(name) && m && typeof m === 'object' && !Array.isArray(m) && Object.keys(m).every(k=>['value','unit','source_ref'].includes(k)),'BAD_MEASUREMENT_ENTRY');
    requireValue(typeof m.value === 'number' && Number.isFinite(m.value) && goodText(m.unit) && ref(m.source_ref), 'MEASUREMENT_VALUE_UNIT_PROVENANCE_REQUIRED');
  }
  const required = {geometry:properties(rule['Geometry Variables']||''),state:properties(rule['State Variables']||'')};
  const missing = [...required.geometry,...required.state].filter(n=>!own(measured,n));
  const bound = source_facet_ref !== null;
  const blockers = [
    ...(!bound ? ['COMPONENT_BINDINGS_NOT_SUPPLIED'] : ['COMPONENT_BINDINGS_SELF_DECLARED_NOT_VERIFIED']),
    ...(missing.length ? ['REQUIRED_VARIABLES_NOT_COMPLETELY_SUPPLIED'] : []),
    'ATLAS_BYTE_HASH_REQUIRES_INDEPENDENT_READBACK',
    'SOURCE_RIGHTS_AND_LEASE_REQUIRE_HOST_VERIFICATION',
    'PHYSICAL_MODEL_NOT_RUN_OR_VALIDATED_FOR_THIS_OBJECT'
  ];
  const geometry = {object_ref:capsule.object_ref,shape_role:capsule.shape_role,geometry_ref:capsule.geometry_ref,
    spatial_relation:lens.interaction.spatial,environment_kind:lens.environment.kind,
    frame:lens.scale.frame,unit:lens.scale.unit,observed_magnitude:lens.scale.observed_magnitude};
  const source = {atlas_schema:ATLAS_SCHEMA,atlas_sha256_claim:source_sha256,atlas_row:rule.ID,
    authority_reference:atlas.authority.drive_sheet,source_evidence_state:rule['Evidence State'],
    source_family:rule['Source Family'],target_family:rule['Target Family'],source_facet_ref,target_facet_ref};
  return {
    schema:TIR_ATLAS_SEAM_SCHEMA,status:'SOURCE_RULE_CANDIDATE_ONLY',native_admitted:false,
    rights_verified:false,geometry_verified:false,physical_interaction_established:false,
    simulation_performed:false,execution_performed:false,mint_performed:false,
    source,geometry,required_variables:required,missing_variables:missing,
    measurements_self_declared:Object.keys(measured).sort(),
    interaction:{name:rule['Interaction Type'],mechanism_as_described_by_source:rule.Mechanism,
      baseline_model:rule['Baseline Model'],higher_order_trigger:rule['Higher-Order Trigger']||null,
      source_design_rule:rule['Design Rule']||null,source_validation_test:rule['Validation Test'],mitigation:rule['Mitigation / Control']||null},
    holds:blockers,
    human:{title:`${rule.ID}: ${rule['Interaction Type']}`,summary:`The existing CGX atlas describes ${rule['Source Family']} → ${rule['Target Family']}. ${rule.Mechanism}.`,
      interpretation:`${lens.interaction.spatial} is a spatial description; it does not establish that this physical interaction occurs in the selected object.`,
      next_test:rule['Validation Test'],boundary:'Candidate rule only. No source hydration, physical execution or native admission.'},
    machine:{typed_role:capsule.shape_role,object_ref:capsule.object_ref,source_dictionary_sha256:capsule.dictionary_source_sha256,
      atlas_rule_id:rule.ID,atlas_sha256_claim:source_sha256,relation_established:false,authority:'REVIEW_ONLY'}
  };
}