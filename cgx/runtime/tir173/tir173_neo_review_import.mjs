/** User-selected, owner-local Neo triadic review. No model execution or native admission.
 * Treat all input as untrusted display data; preserve explicit provenance and uncertainty.
 */
const OPS=new Set(['SELECT','RELATE','TRIAD','PLAN_HYDRATE','PLAN_TRANSFORM','ENCODE_BYTES','DECODE_BYTES','ATLAS_RULE']);
const HEX=/^[0-9a-f]{64}$/;
const ROLE=/^T173:\d{3}$/;
const CANON=/^(SELECT|RELATE|TRIAD|PLAN_HYDRATE|PLAN_TRANSFORM|ENCODE_BYTES|DECODE_BYTES|ATLAS_RULE) (T173:\d{3})$/;
const required=(v,message)=>{if(!v)throw new Error(message);};
const record=(v)=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const boundedString=(v,limit)=>typeof v==='string'&&v.length>0&&v.length<=limit;
const effectFree=(m)=>m.native_admitted===false&&m.executed===false&&m.LOAD_hydration===false
  &&m.signed_DBR===false&&m.model_routing_changed===false;

/** Validate a local user-picked packet and return a bounded, display-only projection.
 * No user input ever becomes an executable CGX operation. Hashes here are claims;
 * the browser cannot validate the private model weights that generated a packet.
 */
export function reviewLocalNeoBatch(value){
 required(record(value)&&value.schema==='cgx.neo.triad_review_batch/0.1','NEO_REVIEW_SCHEMA');
 required(value.native_effects===0&&value.human_machine_consistent===true,'NEO_REVIEW_AUTHORITY');
 required(boundedString(value.source_checkpoint_sha256,64)&&HEX.test(value.source_checkpoint_sha256),'NEO_MODEL_HASH_CLAIM');
 required(Array.isArray(value.tests)&&value.tests.length>=1&&value.tests.length<=16,'NEO_REVIEW_COUNT');
 const items=value.tests.map((entry,index)=>{
  required(record(entry)&&record(entry.machine)&&record(entry.human),'NEO_REVIEW_CASE');
  const {machine:m,human:h}=entry;
  required(m.schema==='cgx.neo.triad_review_preview/0.1'
    &&boundedString(m.input,240)
    &&m.authority==='REVIEW_ONLY'
    &&m.candidate_cannot_override_guard===true
    &&m.model_sha256===value.source_checkpoint_sha256
    &&effectFree(m)
    &&m.physical_claim_qualified===false,'NEO_PREVIEW_EFFECT_HOLD');
  required(h.status==='NOT_EXECUTED'&&boundedString(h.summary,1024),'NEO_HUMAN_BOUNDARY');
  required(record(m.guard)&&effectFree({
    ...m.guard, executed:m.guard.command_executed,LOAD_hydration:m.guard.LOAD_hydration_performed,
    signed_DBR:false,model_routing_changed:false
  })&&m.guard.privileged_effects_authorised===false,'NEO_GUARD_EFFECT_HOLD');
  required(record(m.three_analytic_facets)&&
    ['intuitive','deliberative','assurance'].every(v=>
      record(m.three_analytic_facets[v])&&[-1,0,1].includes(m.three_analytic_facets[v].trit)
      &&boundedString(m.three_analytic_facets[v].status,160)),'NEO_THREE_FACETS');
  required(m.three_analytic_facets.assurance.status==='UNRESOLVED_SOURCE_RIGHTS_SHAPE_AND_AUTHORITY',
    'NEO_ASSURANCE_MUST_HOLD');
  required(m.learned_intent_candidate===null||OPS.has(m.learned_intent_candidate),'NEO_UNREGISTERED_MODEL_INTENT');
  const guardStatus=m.guard.status;
  required(['EXACT_CANONICAL_REVIEW_PLAN','ABSTAIN_REVIEW_REQUIRED'].includes(guardStatus),'NEO_GUARD_STATUS');
  if(guardStatus==='EXACT_CANONICAL_REVIEW_PLAN'){
    const syntax=CANON.exec(m.input);
    required(syntax&&m.guard.intent===syntax[1]&&m.guard.role===syntax[2]
      &&ROLE.test(syntax[2])&&Number(syntax[2].slice(-3))>=1&&Number(syntax[2].slice(-3))<=173
      &&m.guard.mode==='REVIEW_ONLY'&&m.three_analytic_facets.deliberative.trit===1,
      'NEO_CANONICAL_REVIEW_MISMATCH');
  }else{
    required(m.three_analytic_facets.deliberative.trit===-1,'NEO_ABSTENTION_NOT_PRESERVED');
  }
  return {
    index:index+1,input:m.input,status:guardStatus,
    human_summary:h.summary,guard_reason:m.guard.reason||null,
    model_candidate:m.learned_intent_candidate,
    intuitive:m.three_analytic_facets.intuitive.status,
    deliberative:m.three_analytic_facets.deliberative.status,
    assurance:m.three_analytic_facets.assurance.status,
    privileged_action:false
  };
 });
 const positives=items.filter(x=>x.status==='EXACT_CANONICAL_REVIEW_PLAN').length;
 const negatives=items.length-positives;
 required(value.canonical_exact_review_plans===positives&&value.guarded_abstentions===negatives,
   'NEO_BATCH_COUNTS');
 return {
  schema:'cgx.neo.guios_local_preview/0.1',
  owner_selected_file_only:true,
  imported_packet_unverified:true,
  checkpoint_sha256_claim:value.source_checkpoint_sha256,
  total_cases:items.length,
  exact_review_plans:positives,
  guarded_abstentions:negatives,
  native_effects:0,
  model_weights_verified_by_browser:false,
  items
 };
}
