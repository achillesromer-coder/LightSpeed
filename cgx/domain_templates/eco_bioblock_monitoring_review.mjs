/**
 * Eco.cgx Bio-Blocks monitoring qualification: review-only typed boundary.
 * Source basis: original Embedded_Bio_Blocks_Digital_Twin_v0_1.xlsx,
 * Drive ID 1wgUWkkr1mQIPMmmF1V7eaweToUAu8UxK (modified 2026-05-19).
 * Source monitoring schedule and field schema are planning/examples, not field data.
 * No original source rows, private coordinates, or specimen details are copied.
 */
export const BIOBLOCK_MONITORING_SCHEMA="CGX-ECO-BIOBLOCK-MONITORING-REVIEW/0.1";
const ref=x=>typeof x==="string"&&x.length>0&&x.length<=256&&!/[\u0000-\u001f]/.test(x);
const count=x=>x===null||(Number.isSafeInteger(x)&&x>=0&&x<=1e9);
const numeric=x=>x===null||(typeof x==="number"&&Number.isFinite(x)&&x>=0);
const zoned=x=>{
 if(!ref(x))return false;
 const m=/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,9})?(Z|[+-](\d{2}):(\d{2}))$/.exec(x);
 if(!m)return false;
 const [y,mo,d,h,mi,s]=m.slice(1,7).map(Number);
 const leap=y%4===0&&(y%100!==0||y%400===0);
 const days=[31,leap?29:28,31,30,31,30,31,31,30,31,30,31];
 return y>=1&&mo>=1&&mo<=12&&d>=1&&d<=days[mo-1]&&h<=23&&mi<=59&&s<=59&&
  (m[7]==="Z"||(Number(m[8])<=14&&Number(m[9])<=59&&(Number(m[8])<14||Number(m[9])===0)));
};
const allowed=new Set(["evidence_class","source_ref","run_ref","block_ref","recipe_ref","site_ref",
 "taxon_ref","cohort_ref","replicate_ref","observed_at","monitoring_phase","seed_count",
 "germinated_count","surviving_count","weed_cover_pct","soil_moisture","soil_moisture_unit",
 "method_ref","baseline_ref","control_ref","raw_data_ref","photo_ref","calibration_ref",
 "rights_review_ref","spatial_review_ref","field_geometry_present"]);
export function reviewBioBlockMonitoringRecord(input={}){
 if(input===null||typeof input!=="object"||Array.isArray(input)||
  Object.keys(input).some(k=>!allowed.has(k)))throw Error("INVALID_BIOBLOCK_MONITORING_FIELDS");
 const x={evidence_class:"simulated",source_ref:null,run_ref:null,block_ref:null,recipe_ref:null,
  site_ref:null,taxon_ref:null,cohort_ref:null,replicate_ref:null,observed_at:null,
  monitoring_phase:"monthly",seed_count:null,germinated_count:null,surviving_count:null,
  weed_cover_pct:null,soil_moisture:null,soil_moisture_unit:null,method_ref:null,
  baseline_ref:null,control_ref:null,raw_data_ref:null,photo_ref:null,calibration_ref:null,
  rights_review_ref:null,spatial_review_ref:null,field_geometry_present:false,...input};
 const refs=["source_ref","run_ref","block_ref","recipe_ref","site_ref","taxon_ref","cohort_ref",
  "replicate_ref","method_ref","baseline_ref","control_ref","raw_data_ref","photo_ref",
  "calibration_ref","rights_review_ref","spatial_review_ref"];
 if(!["observed","simulated","source_asserted","hypothesised","inferred"].includes(x.evidence_class)||
  !["pre_deployment","deployment","week_2","monthly","quarterly","annual"].includes(x.monitoring_phase)||
  refs.some(k=>x[k]!==null&&!ref(x[k]))||
  !["seed_count","germinated_count","surviving_count"].every(k=>count(x[k]))||
  !numeric(x.weed_cover_pct)||!numeric(x.soil_moisture)||
  (x.weed_cover_pct!==null&&x.weed_cover_pct>100)||
  (x.soil_moisture_unit!==null&&!["percent","m3/m3"].includes(x.soil_moisture_unit))||
  (x.soil_moisture!==null&&x.soil_moisture_unit==="percent"&&x.soil_moisture>100)||
  (x.soil_moisture!==null&&x.soil_moisture_unit==="m3/m3"&&x.soil_moisture>1)||
  (x.observed_at!==null&&!ref(x.observed_at))||
  typeof x.field_geometry_present!=="boolean"||
  (x.seed_count!==null&&x.germinated_count!==null&&x.germinated_count>x.seed_count)||
  (x.germinated_count!==null&&x.surviving_count!==null&&x.surviving_count>x.germinated_count))
  throw Error("INVALID_BIOBLOCK_MONITORING_INPUT");
 const flags=["SOURCE_ONLY_NOT_FIELD_VERIFIED","COUNT_RATES_REQUIRE_MATCHED_COHORT_AND_METHOD_REVIEW"];
 if(!ref(x.source_ref))flags.push("SOURCE_PROVENANCE_REQUIRED");
 if(x.field_geometry_present)flags.push("PRIVATE_GEOMETRY_OUTSIDE_REVIEW_BOUNDARY");
 if(x.soil_moisture!==null&&(!x.soil_moisture_unit||!ref(x.method_ref)))
  flags.push("SOIL_MOISTURE_METHOD_AND_UNIT_REQUIRED");
 if(x.soil_moisture!==null&&!ref(x.calibration_ref))
  flags.push("SOIL_MOISTURE_CALIBRATION_REVIEW_REQUIRED");
 if(x.evidence_class==="observed"){
  flags.push("INDEPENDENT_FIELD_RECEIPT_AND_QA_REQUIRED");
  for(const k of ["run_ref","block_ref","recipe_ref","site_ref","taxon_ref","cohort_ref",
   "replicate_ref","method_ref","baseline_ref","control_ref","raw_data_ref","photo_ref",
   "rights_review_ref","spatial_review_ref"])
   if(!ref(x[k]))flags.push("MISSING_"+k.toUpperCase());
  if(!zoned(x.observed_at))flags.push("ZONED_OBSERVATION_TIMESTAMP_REQUIRED");
  if(["week_2","monthly","quarterly","annual"].includes(x.monitoring_phase)){
   if(x.seed_count===null)flags.push("SEED_DENOMINATOR_REQUIRED");
   if(x.germinated_count===null||x.surviving_count===null)flags.push("MONITORING_COUNTS_REQUIRED");
  }
 }else if(x.germinated_count!==null||x.surviving_count!==null){
  flags.push("NONOBSERVED_COUNTS_CANNOT_ESTABLISH_FIELD_SURVIVAL");
 }
 const rates={
  germinated_per_seed:x.seed_count>0&&x.germinated_count!==null?x.germinated_count/x.seed_count:null,
  surviving_per_germinated:x.germinated_count>0&&x.surviving_count!==null?
   x.surviving_count/x.germinated_count:null
 };
 return {schema:BIOBLOCK_MONITORING_SCHEMA,parent:"Cognigrex.cgx",owner_family:"Eco.cgx",
  evidence_class:x.evidence_class,monitoring_phase:x.monitoring_phase,units:{
   germinated_per_seed:"ratio (unverified)",surviving_per_germinated:"ratio (unverified)"},
  arithmetic_only_rates:rates,flags,source_only:true,native_object_id:null,
  db_readback:false,field_observation_verified:false,biodiversity_gain_verified:false,
  public_release_authorised:false,field_release_authorised:false};
}
