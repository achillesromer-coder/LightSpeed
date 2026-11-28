/**
 * TIR173 to the EXISTING 411 component geometry archetypes and P0-P10 proof
 * ladder. Evidence review only: a shape role is NOT a measured material
 * instance or an automatically equivalent archetype.
 */
import {validateDictionary,validateCapsule,TIRError} from './tir173_core.mjs';

export const TIR_ARCHETYPE_EVIDENCE_SCHEMA='cgx.tir173.existing-archetype-review/0.1';
export const CGX_GEOMETRY_ATLAS_SCHEMA='CGX-COMPONENT-GEOMETRY-ATLAS/0.1';
export const CGX_PHYSICAL_LADDER_SCHEMA='CGX-G1-COMPONENT-PROOF-LADDER/0.1';
export const CGX_INSTANCE_PACKET_SCHEMA='CGX-COMPONENT-INSTANCE-BUILD-PACKET/0.1';
const need=(yes,code)=>{if(!yes)throw new TIRError(code);};
const sha=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
const text=x=>typeof x==='string'&&x.length>0&&x.length<1024&&!/[\u0000-\u001f]/.test(x);
const ID=/^CGA-[A-Z0-9]+-\d{3}$/;
const metadataKeys=['ID','Domain','Family','Component Archetype','Baseline Geometry',
  'Geometric Parameters','Scale Band','Evidence State','Source Authority Class'];
export function verifyOriginalGeometrySources(atlas,ladder,packet) {
  need(atlas?.schema===CGX_GEOMETRY_ATLAS_SCHEMA&&Array.isArray(atlas.records)&&
    atlas.record_count===411&&atlas.records.length===411,
    'ORIGINAL_411_COMPONENT_GEOMETRY_ATLAS_REQUIRED');
  need(text(atlas.authority?.drive_sheet)&&text(atlas.authority?.rule),
    'GEOMETRY_DRIVE_AUTHORITY_MISSING');
  const seen=new Set();
  for(const r of atlas.records) {
    need(r&&metadataKeys.every(k=>text(r[k])), 'COMPONENT_ARCHETYPE_SOURCE_METADATA_MISSING');
    need(ID.test(r.ID)&&!seen.has(r.ID),'DUPLICATE_OR_BAD_COMPONENT_ARCHETYPE');
    seen.add(r.ID);
  }
  need(ladder?.schema===CGX_PHYSICAL_LADDER_SCHEMA&&
    ladder.stages?.length===11&&Array.isArray(ladder.common_packet_requirements),
    'ORIGINAL_P0_P10_PROOF_LADDER_REQUIRED');
  need(text(ladder.authority?.rule)&&text(ladder.progression_rule)&&
    ladder.common_packet_requirements.includes('DBR'),
    'PHYSICAL_PROOF_AUTHORITY_OR_RECEIPT_MISSING');
  for(let i=0;i<11;i++) {
    const stage=ladder.stages[i];
    need(stage?.id==='P'+i&&stage.physical_state==='NOT_RUN'&&
      Array.isArray(stage.representative_refs)&&text(stage.hard_gate),
      'PHYSICAL_STAGE_UNVERIFIED_OR_MUTATED');
  }
  need(packet?.schema===CGX_INSTANCE_PACKET_SCHEMA&&
    Array.isArray(packet.required_instance_fields)&&
    Array.isArray(packet.binding_states)&&text(packet.authority?.rule),
    'ORIGINAL_CGX_INSTANCE_CONTRACT_REQUIRED');
  for(const k of ['exact_source_authority','geometry_revision','material_stack_and_lots',
    'environment_profile','uncertainty','source_hashes','readback_receipt','dbr_pointer'])
    need(packet.required_instance_fields.includes(k),'SOURCE_INSTANCE_GATE_MISSING');
  for(const k of ['UNBOUND','SOURCE_BOUND','GEOMETRY_BOUND','MATERIAL_BOUND',
    'PROCESS_BOUND','TEST_DEFINED','BUILD_READY','BUILT','MEASURED','REVIEWED_PROMOTION'])
    need(packet.binding_states.includes(k),'INSTANCE_STATE_LADDER_MISSING');
  return {geometry_records:seen.size,proof_stages:ladder.stages.length,
    physical_test_stage_count:0,physical_state:'NOT_RUN',
    authority:'DRIVE_OWNED_GIT_MIRROR_REVIEW_ONLY',native_admitted:false};
}
/** A self-declared hash does not authenticate Drive or grant source rights. */
export function reviewTirComponentArchetype(
  dictionary,capsule,atlas,ladder,packet,
  {archetype_id=null,source_claims={}}={}
) {
  validateDictionary(dictionary);validateCapsule(dictionary,capsule);
  const original=verifyOriginalGeometrySources(atlas,ladder,packet);
  need(source_claims&&typeof source_claims==='object'&&!Array.isArray(source_claims)&&
    Object.keys(source_claims).length===3&&
    Object.keys(source_claims).every(k=>['geometry_atlas_sha256','proof_ladder_sha256',
      'instance_contract_sha256'].includes(k))&&
    Object.values(source_claims).every(sha),
    'THREE_SOURCE_BYTE_DIGEST_CLAIMS_REQUIRED');
  need(archetype_id===null||(typeof archetype_id==='string'&&ID.test(archetype_id)),
    'EXPLICIT_COMPONENT_ARCHETYPE_ID_REQUIRED');
  const selected=archetype_id===null?null:atlas.records.find(r=>r.ID===archetype_id);
  need(archetype_id===null||selected!==undefined,'COMPONENT_ARCHETYPE_NOT_IN_ORIGINAL_ATLAS');
  const related=selected?ladder.stages.filter(x=>x.representative_refs.includes(selected.ID))
    .map(x=>({stage:x.id,name:x.name,physical_state:x.physical_state,
      hard_gate:x.hard_gate,representative_only:true})):[];
  const negative_space=[
    'T173_ROLE_TO_COMPONENT_ARCHETYPE_EQUIVALENCE_UNVERIFIED',
    'EXACT_CAD_AND_REVISION_NOT_BOUND','MATERIAL_LOTS_AND_PASSPORTS_NOT_BOUND',
    'ENVIRONMENT_AND_PHYSICAL_MEASUREMENTS_NOT_BOUND',
    'SOURCE_BYTES_NOT_INDEPENDENTLY_AUTHENTICATED',
    'DRIVE_ORIGINAL_AND_RIGHTS_NOT_INDEPENDENTLY_READ_BACK',
    'NO_QUALIFIED_COMPONENT_INSTANCE','NO_SIGNED_DBR_OR_NATIVE_ADMISSION'
  ];
  const machine={
    schema:TIR_ARCHETYPE_EVIDENCE_SCHEMA,
    status:selected?'EXPLICIT_ARCHETYPE_CANDIDATE_REVIEW':'NO_ARCHETYPE_SELECTED',
    shape_role:capsule.shape_role,object_ref:capsule.object_ref,
    geometry_ref:capsule.geometry_ref,shape_evidence:capsule.geometry_evidence,
    dictionary_source_sha256:dictionary.source_sha256,
    archetype_id:selected?.ID||null,
    declared_archetype:selected?{
      name:selected['Component Archetype'],family:selected.Family,domain:selected.Domain,
      baseline_geometry:selected['Baseline Geometry'],
      geometric_parameters:selected['Geometric Parameters'],scale_band:selected['Scale Band'],
      atlas_evidence_label:selected['Evidence State'],
      source_authority_class:selected['Source Authority Class']
    }:null,
    proof_ladder_representative_stages:related,
    proof_stages_total:original.proof_stages,
    original_physical_state:original.physical_state,
    source_claims:{...source_claims},source_claims_authenticated:false,
    archetype_to_shape_mapping_verified:false,exact_instance_bound:false,
    geometry_verified:false,material_verified:false,rights_verified:false,
    physical_test_performed:false,physical_evidence_established:false,
    model_inference_performed:false,execution_performed:false,
    source_bytes_transferred:0,mint_performed:false,native_admitted:false,
    signed_dbr:false,automatic_baseline_promotion:false,
    negative_space,authority:'REVIEW_ONLY'
  };
  return {machine,human:{
    summary:selected?selected.ID+' · '+selected['Component Archetype']:'No component archetype selected',
    shape:capsule.shape_role+' · source geometry: '+capsule.geometry_ref,
    interpretation:selected
      ? 'Operator-selected '+selected.Family+' archetype; '+selected['Evidence State']+' is the atlas label, not proof of this shape or component instance.'
      : 'The T173 shape has no explicitly selected component archetype.',
    physical_state:'All original P0–P10 proof stages NOT_RUN; no empirical qualification',
    proof_stages:related.length?related.map(s=>s.stage).join(', '):'No directly listed representative stage',
    outstanding:negative_space.join(', '),
    authority:'Review only — no source hydration or physical execution'
  }};
}
