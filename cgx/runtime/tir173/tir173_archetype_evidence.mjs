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


/**
 * Inspect the EXISTING eight Drive-owned P0–P3 instance envelopes. They are
 * unbound digital review records, not a production register or test receipt.
 * The P0 SH01/PHYSOBJ record uses a distinct identity family and must NOT be
 * silently coerced into one of the 411 CGA archetypes.
 */
export const CGX_INSTANCE_REGISTER_SCHEMA='CGX-COMPONENT-INSTANCE-REGISTER/0.1';
const INSTANCE_ID=/^CGXI-P[0-3]-[A-Z0-9-]+$/;
const SOURCE_KEYS=['instance_id','proof_stage','archetype_id','binding_state',
  'revision','exact_source_authority','source_locator_or_hash',
  'geometry_source_type','geometry_revision','dimensions_and_tolerances',
  'material_stack_and_lots','material_passport_refs','ports_and_interfaces',
  'manufacturing_or_assembly_route','tool_and_calibration_refs',
  'environment_profile','evidence_ceiling','uncertainty','configuration_hash',
  'source_hashes','readback_receipt','dbr_pointer','physical_state'];
export function verifyOriginalInstancePopulation(population,packet,ladder) {
  need(population?.schema===CGX_INSTANCE_REGISTER_SCHEMA&&
    population.record_count===8&&Array.isArray(population.records)&&
    population.records.length===8,'EXISTING_EIGHT_INSTANCE_REGISTER_REQUIRED');
  need(text(population.authority?.drive_sheet)&&
    population.authority.drive_sheet==='31_CGX_Component_Instance_Register_v0_1'&&
    text(population.authority?.rule)&&
    population.common_state?.binding_state==='UNBOUND'&&
    population.common_state?.physical_state==='NOT_RUN',
    'DRIVE_INSTANCE_REGISTER_AUTHORITY_REQUIRED');
  need(packet?.schema===CGX_INSTANCE_PACKET_SCHEMA&&
    Array.isArray(packet.required_instance_fields)&&
    packet.required_instance_fields.includes('dbr_pointer')&&
    packet.required_instance_fields.includes('source_hashes'),
    'EXISTING_INSTANCE_PACKET_CONTRACT_REQUIRED');
  need(ladder?.schema===CGX_PHYSICAL_LADDER_SCHEMA&&
    Array.isArray(ladder.stages)&&ladder.stages.length===11,
    'EXISTING_PHYSICAL_PROOF_LADDER_REQUIRED');
  const ids=new Set(),cga=new Set();
  for(const r of population.records){
    need(r&&SOURCE_KEYS.every(k=>text(r[k]))&&INSTANCE_ID.test(r.instance_id),
      'INSTANCE_RECORD_REQUIRED_FIELD_MISSING');
    need(!ids.has(r.instance_id),'DUPLICATED_INSTANCE_ID');
    ids.add(r.instance_id);
    need(['P0','P1','P2','P3'].includes(r.proof_stage)&&
      r.instance_id.startsWith('CGXI-'+r.proof_stage+'-')&&
      ladder.stages.some(s=>s.id===r.proof_stage&&s.physical_state==='NOT_RUN'),
      'INSTANCE_PROOF_STAGE_MISMATCH');
    need(r.binding_state==='UNBOUND'&&r.physical_state==='NOT_RUN'&&
      r.geometry_revision==='UNRESOLVED'&&
      r.dimensions_and_tolerances==='UNRESOLVED'&&
      r.configuration_hash==='UNRESOLVED'&&r.source_hashes==='UNRESOLVED'&&
      r.readback_receipt==='UNRESOLVED'&&r.dbr_pointer==='UNRESOLVED',
      'INSTANCE_EVIDENCE_CEILING_CONTRADICTION');
    if(r.proof_stage==='P0'){
      need(r.instance_id==='CGXI-P0-SH01-ID-A'&&
        r.archetype_id==='SH01-ID-A / CGX-PHYSOBJ-001',
        'P0_NON_CGA_IDENTITY_MISMATCH');
    }else{
      need(ID.test(r.archetype_id),'INSTANCE_CGA_ARCHETYPE_ID_REQUIRED');
      cga.add(r.archetype_id);
    }
  }
  return {instance_count:ids.size,cga_related_instances:7,
    distinct_cga_ids:cga.size,non_cga_p0_instances:1,
    unbound_count:8,physical_tests_completed:0,
    authority:'DRIVE_OWNER_GIT_MIRROR_ONLY',native_admitted:false};
}
/**
 * Both the selected T173 role and selected CGA ID are still REVIEW objects.
 * An instance may be looked up only by its exact declared archetype ID.
 * No inferred equivalence, source-rights authentication or measurement occurs.
 */
export function reviewTirExistingInstance(
  dictionary,capsule,atlas,ladder,packet,population,
  {archetype_id=null,instance_id=null,source_claims={}}={}
){
  const original=verifyOriginalInstancePopulation(population,packet,ladder);
  need(source_claims&&typeof source_claims==='object'&&
    !Array.isArray(source_claims)&&
    Object.keys(source_claims).length===4&&
    ['geometry_atlas_sha256','proof_ladder_sha256',
      'instance_contract_sha256','instance_register_sha256']
      .every(k=>sha(source_claims[k])),
    'FOUR_SOURCE_DIGEST_CLAIMS_REQUIRED');
  const compared=reviewTirComponentArchetype(dictionary,capsule,atlas,ladder,packet,{
    archetype_id,
    source_claims:{
      geometry_atlas_sha256:source_claims.geometry_atlas_sha256,
      proof_ladder_sha256:source_claims.proof_ladder_sha256,
      instance_contract_sha256:source_claims.instance_contract_sha256
    }
  });
  need(instance_id===null||(typeof instance_id==='string'&&INSTANCE_ID.test(instance_id)),
    'EXPLICIT_REGISTERED_INSTANCE_ID_REQUIRED');
  need(instance_id===null||compared.machine.status==='EXPLICIT_ARCHETYPE_CANDIDATE_REVIEW',
    'INSTANCE_CANNOT_PRECEDE_ARCHETYPE_SELECTION');
  const eligible=archetype_id===null?[]:
    population.records.filter(r=>r.archetype_id===archetype_id)
      .map(r=>r.instance_id);
  const selected=instance_id===null?null:
    population.records.find(r=>r.instance_id===instance_id);
  need(instance_id===null&&selected===null||selected!==undefined,
    'UNKNOWN_INSTANCE_IN_ORIGINAL_REGISTER');
  need(!selected||selected.archetype_id===archetype_id,
    'INSTANCE_ARCHETYPE_IDENTITY_MISMATCH');
  const outstanding=[
    'T173_SHAPE_TO_CGA_EQUIVALENCE_NOT_VERIFIED',
    'CGA_ARCHETYPE_TO_EXACT_INSTANCE_NOT_QUALIFIED',
    'CAD_REVISION_AND_TOLERANCES_UNRESOLVED',
    'EXACT_MATERIAL_LOTS_AND_PASSPORTS_UNVERIFIED',
    'SOURCE_RIGHTS_AND_DRIVE_READBACK_UNVERIFIED',
    'PROCESS_TOOLS_ENVIRONMENT_AND_CALIBRATION_UNVERIFIED',
    'CONFIGURATION_AND_SOURCE_HASHES_UNRESOLVED',
    'MEASUREMENTS_AND_UNCERTAINTY_NOT_PROVIDED',
    'PHYSICAL_STAGE_NOT_RUN','SIGNED_DBR_AND_NATIVE_ADMISSION_ABSENT'
  ];
  const machine={
    schema:'cgx.tir173.existing-instance-review/0.1',
    status:selected?'EXPLICIT_REGISTERED_INSTANCE_CANDIDATE':'NO_INSTANCE_SELECTED',
    shape_role:capsule.shape_role,object_ref:capsule.object_ref,
    geometry_ref:capsule.geometry_ref,archetype_id:archetype_id||null,
    eligible_existing_instance_ids:eligible,
    instance_id:selected?.instance_id||null,
    selected_record:selected?{
      instance_id:selected.instance_id,proof_stage:selected.proof_stage,
      archetype_id:selected.archetype_id,instance_type:selected.instance_type,
      source_revision:selected.revision,binding_state:selected.binding_state,
      physical_state:selected.physical_state,
      geometry_revision:selected.geometry_revision,
      dimensions_and_tolerances:selected.dimensions_and_tolerances,
      exact_source_authority:selected.exact_source_authority,
      candidate_materials:selected.material_stack_and_lots,
      missing_next_binding:selected.blocked_by_next_binding,
      evidence_ceiling:selected.evidence_ceiling,
      source_hashes:selected.source_hashes,
      readback_receipt:selected.readback_receipt,dbr_pointer:selected.dbr_pointer
    }:null,
    source_claims:{...source_claims},source_claims_authenticated:false,
    original_register_instance_count:original.instance_count,
    original_unbound_count:original.unbound_count,
    p0_identity_separate_from_cga:true,
    archetype_to_shape_mapping_verified:false,
    exact_instance_bound:false,geometry_verified:false,material_verified:false,
    rights_verified:false,source_verified_against_drive:false,
    physical_test_performed:false,measurement_verified:false,
    execution_performed:false,source_bytes_transferred:0,
    native_admitted:false,signed_dbr:false,mint_performed:false,
    model_inference_performed:false,model_weights_changed:false,
    authority:'REVIEW_ONLY',negative_space:outstanding
  };
  return {machine,human:{
    summary:selected?selected.instance_id+' · '+selected.archetype_id:
      'No registered component instance selected',
    interpretation:selected?
      'Existing '+selected.proof_stage+' candidate; binding='+selected.binding_state+
      ', physical='+selected.physical_state+'. Neither T173 correspondence nor exact material/geometry is proven.':
      'Select an original CGA archetype first, then independently choose a matching registered instance.',
    next_binding:selected?.blocked_by_next_binding||
      'Exact instance identification and evidence review required',
    missing:outstanding.join(', '),
    authority:'Review only — no native receipt, rights, fabrication or validation'
  }};
}
