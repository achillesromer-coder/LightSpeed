/**
 * Eco.cgx / Second Cycle: source-only scientific-claim boundary.
 * Original workbook identity, bytes, rights and any protected locations remain
 * in the controlled source federation, not in this review-only adapter.
 * This is NOT a flow solver, atmospheric model, field observation or CGX install.
 * Scientific-output stop-ship #209 applies throughout.
 */
export const SECOND_CYCLE_REVIEW_SCHEMA="CGX-ECO-SECOND-CYCLE-CLAIM-REVIEW/0.1";
const expectedUnits=Object.freeze({
 passive_flow:"L/s", mist_output:"L/s", hydraulic_power_proxy:"W",
 aerosol_residence_index:"arbitrary_index", mooring_margin:"ratio"
});
const kinds=new Set([...Object.keys(expectedUnits),
 "water_quality_change","habitat_outcome","weather_effect",
 "carbon_credit","field_deployment"]);
const classes=new Set(["observed","simulated","source_asserted","hypothesised","inferred"]);
const allowed=new Set(["claim_kind","evidence_class","numeric_value","unit",
 "source_ref","source_sha256","source_revision","issuer_ref","observed_at",
 "time_ref","frame_ref","origin_ref","method_ref","calibration_ref",
 "baseline_ref","control_ref","raw_data_ref","independent_qa_ref",
 "rights_review_ref","stewardship_review_ref","geometry_present"]);
const ref=x=>typeof x==="string"&&x.length>0&&x.length<=256&&
 !/[\u0000-\u001f]/.test(x);
const zoned=x=>{
 if(!ref(x))return false;
 const m=/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,9})?(Z|[+-](\d{2}):(\d{2}))$/.exec(x);
 if(!m)return false;
 const [y,mo,d,h,mi,s]=m.slice(1,7).map(Number);
 const leap=y%4===0&&(y%100!==0||y%400===0);
 const days=[31,leap?29:28,31,30,31,30,31,31,30,31,30,31];
 return y>=1&&mo>=1&&mo<=12&&d>=1&&d<=days[mo-1]&&h<=23&&mi<=59&&s<=59&&
  (m[7]==="Z"||(Number(m[8])<=14&&Number(m[9])<=59&&
  (Number(m[8])<14||Number(m[9])===0)));
};
export function reviewSecondCycleClaim(input){
 if(input===null||typeof input!=="object"||Array.isArray(input)||
  Object.keys(input).some(k=>!allowed.has(k)))
  throw Error("INVALID_SECOND_CYCLE_REVIEW_FIELDS");
 const x={numeric_value:null,unit:null,source_ref:null,source_sha256:null,
  source_revision:null,issuer_ref:null,observed_at:null,time_ref:null,
  frame_ref:null,origin_ref:null,method_ref:null,calibration_ref:null,
  baseline_ref:null,control_ref:null,raw_data_ref:null,independent_qa_ref:null,
  rights_review_ref:null,stewardship_review_ref:null,geometry_present:false,...input};
 if(!kinds.has(x.claim_kind)||!classes.has(x.evidence_class)||
  typeof x.geometry_present!=="boolean"||
  (x.numeric_value!==null&&
   (typeof x.numeric_value!=="number"||!Number.isFinite(x.numeric_value)||
    x.numeric_value<0))||
  (x.numeric_value===null&&x.unit!==null)||
  (x.numeric_value!==null&&
   (!Object.hasOwn(expectedUnits,x.claim_kind)||
    x.unit!==expectedUnits[x.claim_kind]))||
  (x.source_sha256!==null&&
   (typeof x.source_sha256!=="string"||!/^[a-f0-9]{64}$/i.test(x.source_sha256)))||
  ["source_ref","source_revision","issuer_ref","time_ref","frame_ref",
   "origin_ref","method_ref","calibration_ref","baseline_ref","control_ref",
   "raw_data_ref","independent_qa_ref","rights_review_ref",
   "stewardship_review_ref"].some(k=>x[k]!==null&&!ref(x[k]))||
  (x.observed_at!==null&&!zoned(x.observed_at)))
  throw Error("INVALID_SECOND_CYCLE_REVIEW_INPUT");
 const flags=["SOURCE_ONLY_NO_NATIVE_ADMISSION",
  "NO_INDEPENDENT_PHYSICAL_OR_ECOLOGICAL_VALIDATION"];
 if(!ref(x.source_ref)||!ref(x.issuer_ref)||!ref(x.source_revision))
  flags.push("R0_SOURCE_ISSUER_REVISION_INCOMPLETE");
 if(!x.source_sha256)flags.push("R0_ORIGINAL_BYTE_HASH_REQUIRED");
 else flags.push("HASH_DECLARATION_REQUIRES_PROVIDER_BYTE_MATCH");
 if(!ref(x.rights_review_ref))flags.push("SOURCE_REUSE_RIGHTS_UNRESOLVED");
 if(!ref(x.stewardship_review_ref))flags.push("LEGAL_CULTURAL_STEWARDSHIP_REVIEW_REQUIRED");
 if(x.geometry_present)flags.push("SPATIAL_SENSITIVITY_REVIEW_REQUIRED");
 if(x.numeric_value!==null){
  flags.push("NUMERIC_VALUE_NOT_INDEPENDENTLY_VALIDATED");
  if(!ref(x.time_ref)||!ref(x.frame_ref)||!ref(x.origin_ref))
   flags.push("NUMERIC_TIME_FRAME_ORIGIN_REQUIRED");
  if(!ref(x.method_ref)||!ref(x.baseline_ref))
   flags.push("METRIC_METHOD_AND_BASELINE_REQUIRED");
 }
 if(x.evidence_class==="observed"){
  flags.push("OBSERVATION_RECEIPT_AND_INDEPENDENT_QA_REQUIRED");
  if(!zoned(x.observed_at)||!ref(x.raw_data_ref)||!ref(x.independent_qa_ref))
   flags.push("OBSERVATION_EVIDENCE_INCOMPLETE");
 }else if(x.evidence_class==="simulated"){
  flags.push("SIMULATION_NOT_FIELD_OBSERVATION");
 }else if(x.evidence_class==="source_asserted"){
  flags.push("SOURCE_ASSERTION_NOT_MEASUREMENT_OR_VALIDATED_OUTCOME");
 }else if(x.evidence_class==="hypothesised"){
  flags.push("HYPOTHESIS_REQUIRES_TESTABLE_BASELINE_CONTROL_AND_FALSIFIER");
 }else if(x.evidence_class==="inferred"){
  flags.push("INFERENCE_REQUIRES_INPUT_EVIDENCE_AND_UNCERTAINTY");
 }
 switch(x.claim_kind){
  case "passive_flow":flags.push("HYDRODYNAMIC_BENCH_CALIBRATION_REQUIRED");break;
  case "mist_output":flags.push("NO_ATMOSPHERIC_EFFECT_INFERRED");break;
  case "hydraulic_power_proxy":
   flags.push("HYDRAULIC_POWER_PROXY_NOT_NET_OR_EXTRACTABLE_POWER");
   flags.push("SAME_INPUT_ALGEBRA_NOT_INDEPENDENT_PHYSICAL_VALIDATION");
   flags.push("HYDRAULIC_LOSSES_GEOMETRY_AND_BENCH_CALIBRATION_REQUIRED");break;
  case "aerosol_residence_index":
   flags.push("ARBITRARY_INDEX_NOT_DIMENSIONLESS_PHYSICAL_METRIC");break;
  case "mooring_margin":flags.push("MOORING_ENGINEERING_SIGNOFF_REQUIRED");break;
  case "water_quality_change":
   flags.push("CALIBRATED_CONTROLLED_WATER_MONITORING_REQUIRED");break;
  case "habitat_outcome":
   flags.push("ECOLOGICAL_OUTCOME_NOT_VERIFIED");break;
  case "weather_effect":
   flags.push("WEATHER_CAUSALITY_NOT_ESTABLISHED");break;
  case "carbon_credit":
   flags.push("CREDIT_METHODOLOGY_AND_VERIFICATION_REQUIRED");break;
  case "field_deployment":
   flags.push("PERMITS_BIOSECURITY_NAVIGATION_AND_CUSTODIAL_GATE_HOLD");break;
 }
 return {schema:SECOND_CYCLE_REVIEW_SCHEMA,parent:"Cognigrex.cgx",
  owner_family:"Eco.cgx",claim_kind:x.claim_kind,evidence_class:x.evidence_class,
  declared_unit:x.unit,numeric_value_present:x.numeric_value!==null,
  flags,admission_stage:"R1_REVIEW_ONLY",source_only:true,
  native_object_id:null,db_readback:false,runtime_verified:false,
  physical_metric_verified:false,field_observation_verified:false,
  ecological_effect_verified:false,owner_accepted:false,
  public_release_authorised:false,field_deployment_authorised:false};
}
