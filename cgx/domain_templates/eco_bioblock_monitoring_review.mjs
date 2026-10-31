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
const sha256=x=>typeof x==="string"&&/^[0-9a-fA-F]{64}$/.test(x);
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
const allowed=new Set(["evidence_class","source_ref","source_revision","source_sha256","run_ref","block_ref","recipe_ref","site_ref",
 "taxon_ref","cohort_ref","replicate_ref","observed_at","monitoring_phase","seed_count",
 "germinated_count","surviving_count","weed_cover_pct","soil_moisture","soil_moisture_unit",
 "method_ref","baseline_ref","control_ref","raw_data_ref","photo_ref","calibration_ref",
 "rights_review_ref","spatial_review_ref","field_geometry_present"]);
export function reviewBioBlockMonitoringRecord(input={}){
 if(input===null||typeof input!=="object"||Array.isArray(input)||
  Object.keys(input).some(k=>!allowed.has(k)))throw Error("INVALID_BIOBLOCK_MONITORING_FIELDS");
 const x={evidence_class:"simulated",source_ref:null,source_revision:null,source_sha256:null,run_ref:null,block_ref:null,recipe_ref:null,
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
  (x.source_revision!==null&&!ref(x.source_revision))||
  (x.source_sha256!==null&&!sha256(x.source_sha256))||
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

/**
 * Review-only comparison of successive monitoring records.
 * These checks are warnings, not ecological effect estimates or field validation.
 * Changes in counts can reflect recruitment, metric scope or sampling changes.
 */
export function reviewBioBlockMonitoringSeries(records){
 if(!Array.isArray(records)||records.length<2||records.length>100)
  throw Error("INVALID_BIOBLOCK_SERIES_LENGTH");
 const summaries=records.map(reviewBioBlockMonitoringRecord);
 const flags=new Set(["SOURCE_ONLY_NOT_FIELD_VERIFIED",
  "LONGITUDINAL_SERIES_REQUIRES_INDEPENDENT_QA"]);
 const fields=["run_ref","block_ref","recipe_ref","site_ref","taxon_ref",
  "cohort_ref","replicate_ref","method_ref","control_ref","baseline_ref"];
 const first=records[0];
 for(let i=0;i<records.length;i++){
  const row=records[i];
  if(fields.some(k=>!ref(row[k])))flags.add("INCOMPLETE_LONGITUDINAL_LINKAGE");
  if(i===0)continue;
  const prev=records[i-1];
  if(summaries[i].evidence_class!==summaries[0].evidence_class)
   flags.add("MIXED_EVIDENCE_CLASSES_NOT_COMPARABLE");
  for(const k of fields)
   if(ref(row[k])&&ref(first[k])&&row[k]!==first[k])
    flags.add("SERIES_"+k.toUpperCase()+"_MISMATCH");
  if(!zoned(row.observed_at)||!zoned(prev.observed_at)){
   flags.add("LONGITUDINAL_ZONED_TIMESTAMPS_REQUIRED");
   continue;
  }
  if(!(Date.parse(row.observed_at)>Date.parse(prev.observed_at))){
   flags.add("NONINCREASING_LONGITUDINAL_TIME");
   continue;
  }
  if(row.seed_count!==null&&prev.seed_count!==null&&row.seed_count!==prev.seed_count)
   flags.add("SEED_DENOMINATOR_CHANGED_REVIEW_REQUIRED");
  const comparable=summaries[i].evidence_class===summaries[0].evidence_class&&
   Number.isSafeInteger(row.seed_count)&&row.seed_count>0&&
   row.seed_count===prev.seed_count&&
   fields.every(k=>ref(row[k])&&ref(prev[k])&&row[k]===prev[k]);
  if(!comparable){
   flags.add("LONGITUDINAL_COUNTS_NOT_COMPARABLE");
   continue;
  }
  if(row.surviving_count!==null&&prev.surviving_count!==null&&
   row.surviving_count>prev.surviving_count)
   flags.add("SURVIVAL_INCREASE_REQUIRES_RECRUITMENT_OR_METHOD_REVIEW");
  if(row.germinated_count!==null&&prev.germinated_count!==null&&
   row.germinated_count<prev.germinated_count)
   flags.add("GERMINATION_DECREASE_REQUIRES_METRIC_SCOPE_REVIEW");
 }
 return {schema:BIOBLOCK_MONITORING_SCHEMA,parent:"Cognigrex.cgx",
  owner_family:"Eco.cgx",record_count:records.length,flags:[...flags],
  source_only:true,native_object_id:null,db_readback:false,
  longitudinal_field_evidence_verified:false,biodiversity_gain_verified:false,
  public_release_authorised:false,field_release_authorised:false};
}


/**
 * Source-only alignment with Bio-Blocks workbook "Monitoring Schedule":
 * pre-deployment, deployment day, week 2, months 1-12, quarterly after
 * year one, and annual review. Windows are conservative review heuristics,
 * not proof of protocol compliance or an enforced ecological field schedule.
 * Missing visits are assessed only when the caller declares a complete
 * dataset and supplies an explicit as_of time.
 */
export function reviewBioBlockMonitoringSchedule(records, options={}) {
 if(!Array.isArray(records)||records.length<1||records.length>100||
  options===null||typeof options!=="object"||Array.isArray(options)||
  Object.keys(options).some(k=>!["deployment_at","as_of","coverage_complete"].includes(k)))
  throw Error("INVALID_BIOBLOCK_SCHEDULE_INPUT");
 const {deployment_at,as_of=null,coverage_complete=false}=options;
 if(!zoned(deployment_at)||typeof coverage_complete!=="boolean"||
  (as_of!==null&&!zoned(as_of))||(coverage_complete&&as_of===null))
  throw Error("INVALID_BIOBLOCK_SCHEDULE_TIME");
 const deploy=Date.parse(deployment_at),asOf=as_of===null?null:Date.parse(as_of);
 if(asOf!==null&&asOf<deploy)throw Error("INVALID_BIOBLOCK_SCHEDULE_TIME");
 records.forEach(reviewBioBlockMonitoringRecord);
 const phases=["pre_deployment","deployment","week_2","monthly","quarterly","annual"];
 const phase_counts=Object.fromEntries(phases.map(k=>[k,0]));
 const qualifying_visits={monthly:[],quarterly:[],annual:[]};
 const flags=new Set(["SOURCE_ONLY_NOT_FIELD_VERIFIED",
  "MONITORING_SCHEDULE_IS_SOURCE_ASSERTED_PLANNING"]);
 const DAY=86400000;
 for(const r of records){
  phase_counts[r.monitoring_phase]++;
  if(!zoned(r.observed_at)){
   flags.add("MONITORING_TIMEPOINT_TIMESTAMP_REQUIRED");
   continue;
  }
  const observed=Date.parse(r.observed_at);
  if(asOf!==null&&observed>asOf){
   flags.add("MONITORING_RECORD_AFTER_AS_OF_REVIEW");
   continue;
  }
  const days=(observed-deploy)/DAY;
  if(r.monitoring_phase==="monthly"&&days>=21&&days<=366)
   qualifying_visits.monthly.push(observed);
  if(r.monitoring_phase==="quarterly"&&days>=365)
   qualifying_visits.quarterly.push(observed);
  if(r.monitoring_phase==="annual"&&days>=300)
   qualifying_visits.annual.push(observed);
  if(r.monitoring_phase==="pre_deployment"&&days>=0)
   flags.add("BASELINE_NOT_BEFORE_DEPLOYMENT_REVIEW");
  if(r.monitoring_phase==="deployment"&&(days<0||days>1))
   flags.add("DEPLOYMENT_DAY_TIMEPOINT_REVIEW");
  if(r.monitoring_phase==="week_2"&&(days<7||days>21))
   flags.add("WEEK_TWO_WINDOW_REVIEW");
  if(r.monitoring_phase==="monthly"&&(days<21||days>366))
   flags.add("FIRST_YEAR_MONTHLY_WINDOW_REVIEW");
  if(r.monitoring_phase==="quarterly"&&days<365)
   flags.add("POST_YEAR_ONE_QUARTERLY_WINDOW_REVIEW");
  if(r.monitoring_phase==="annual"&&days<300)
   flags.add("ANNUAL_REVIEW_WINDOW_REVIEW");
  if(r.monitoring_phase!=="pre_deployment"&&days<0)
   flags.add("POST_DEPLOYMENT_PHASE_PRECEDES_DEPLOYMENT");
 }
 if(coverage_complete){
  for(const [phase,flag] of [
   ["pre_deployment","BASELINE_NOT_IN_DECLARED_COMPLETE_SERIES"],
   ["deployment","DEPLOYMENT_LOG_NOT_IN_DECLARED_COMPLETE_SERIES"],
   ["week_2","WEEK_TWO_NOT_IN_DECLARED_COMPLETE_SERIES"]])
   if(phase_counts[phase]===0)flags.add(flag);
  const elapsed=(asOf-deploy)/DAY;
  const monthly=[...new Set(qualifying_visits.monthly)].sort((a,b)=>a-b);
  if(elapsed>=365&&monthly.length<12)
   flags.add("FIRST_YEAR_MONTHLY_COVERAGE_REVIEW");
  if(elapsed>=365&&phase_counts.monthly>=12&&monthly.length<phase_counts.monthly)
   flags.add("FIRST_YEAR_MONTHLY_DUPLICATE_TIMEPOINT_REVIEW");
  // Conservative spacing review only; no inferred site-local calendar or compliance.
  if(elapsed>=365&&monthly.some((t,i)=>i>0&&t-monthly[i-1]<21*DAY))
   flags.add("FIRST_YEAR_MONTHLY_VISIT_SPACING_REVIEW");
  if(elapsed>=455&&qualifying_visits.quarterly.length===0)
   flags.add("POST_YEAR_ONE_QUARTERLY_COVERAGE_REVIEW");
  if(elapsed>=365&&qualifying_visits.annual.length===0)
   flags.add("ANNUAL_REVIEW_COVERAGE_REVIEW");
 }
 return {schema:BIOBLOCK_MONITORING_SCHEMA,parent:"Cognigrex.cgx",
  owner_family:"Eco.cgx",phase_counts,coverage_complete_declared:coverage_complete,
  flags:[...flags],source_only:true,native_object_id:null,db_readback:false,
  schedule_compliance_verified:false,field_observation_verified:false,
  biodiversity_gain_verified:false,public_release_authorised:false,
  field_release_authorised:false};
}
