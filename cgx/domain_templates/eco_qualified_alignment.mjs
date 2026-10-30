/**
 * Eco.cgx source-only ecological identity discrimination for qualified LOAD candidates.
 * An Eco-specific review adapter, NOT a new canonical resolver or a second LOAD registry.
 * No data acquisition, coordinates transformation, inference, merging, Object_ID minting or DBR writes.
 */
export const ECO_ALIGNMENT_SCHEMA="CGX-ECO-QUALIFIED-ALIGNMENT/0.1";
const good=s=>typeof s==="string"&&s.trim().length>0&&s.length<=256&&!/[\u0000-\u001f]/.test(s);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const stringList=x=>Array.isArray(x)&&x.length<=5000&&x.every(good);
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const EVIDENCE=new Set(["observed","simulated","source_asserted","hypothesised","inferred","independently_reviewed"]);
const ECO_TYPES=new Set(["taxon","species","specimen","population","ecological_observation","sensor_reading","site","habitat","intervention","experiment","ecological_state_estimate","ecological_function","functional_guild","receiving_system","projection_result"]);
const IDENTITY=["taxon_id","specimen_id","population_id","site_id","station_id","subject_kind","subject_id","ecological_function_id","functional_guild_id","receiving_system_id"];
const OBSERVATIONS=new Set(["ecological_observation","sensor_reading"]);
// Validate absolute ISO timestamp and actual calendar date before aligning observations.
function validObservedAt(v){
 if(!good(v))return false;
 const m=/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,9})?(Z|[+-](\d{2}):(\d{2}))$/.exec(v);
 if(!m)return false;
 const [year,month,day,hour,minute,second]=m.slice(1,7).map(Number);
 const leap=year%4===0&&(year%100!==0||year%400===0);
 const days=[31,leap?29:28,31,30,31,30,31,31,30,31,30,31];
 if(year<1||month<1||month>12||day<1||day>days[month-1]||hour>23||minute>59||second>59)return false;
 if(m[7]!=="Z"){
  const h=Number(m[8]),mm=Number(m[9]);
  if(h>14||mm>59||(h===14&&mm!==0))return false;
 }
 return true;
}

function validateConcept(x){
 if(!obj(x)||!ECO_TYPES.has(x.semantic_type)||!stringList(x.source_refs))throw Error("INVALID_ECO_CONCEPT");
 if(x.object_id!==undefined&&!good(x.object_id))throw Error("INVALID_OBJECT_ID");
 for(const f of [...IDENTITY,"observed_at","method_id","unit","frame","environment_id","configuration","epoch","aggregation_scope","baseline_id","observed_variable","native_interval","aggregation_period","station_instrument_id","qa_flag","missing_data_state","calibration_verification_ref","siting_metadata_ref","source_provenance_ref","measurement_basis","correction_method_id","uncertainty_basis","result_qualifier"]){
  if(x[f]!==undefined&&x[f]!==null&&!good(x[f]))throw Error("INVALID_ECO_FIELD_"+f);
 }
 if(x.sample_count!==undefined&&(!Number.isSafeInteger(x.sample_count)||x.sample_count<1))throw Error("INVALID_SAMPLE_COUNT");
 if(x.evidence_class!==undefined&&!EVIDENCE.has(x.evidence_class))throw Error("INVALID_EVIDENCE_CLASS");
 if(x.geometry!==undefined){
  const g=x.geometry;
  if(!obj(g)||g.type!=="Point"||!good(g.crs)||!Array.isArray(g.coordinates)||
   ![2,3].includes(g.coordinates.length)||!g.coordinates.every(v=>typeof v==="number"&&Number.isFinite(v)))
    throw Error("INVALID_GEOMETRY");
  if(g.crs==="EPSG:4326"&&(g.coordinates[0]<-180||g.coordinates[0]>180||g.coordinates[1]<-90||g.coordinates[1]>90))
    throw Error("INVALID_WGS84_COORDINATES");
  if(g.vertical_datum!==undefined&&!good(g.vertical_datum))throw Error("INVALID_VERTICAL_DATUM");
 }
 if(x.environment!==undefined&&(!obj(x.environment)||Object.keys(x.environment).length>50))throw Error("INVALID_ENVIRONMENT");
 if(x.measurement!==undefined){
  if(!obj(x.measurement)||typeof x.measurement.value!=="number"||!Number.isFinite(x.measurement.value)||
   !good(x.measurement.unit))throw Error("INVALID_MEASUREMENT");
 }
 // BioBlocks: native species identity does not establish biological movement safety.
 if(x.biological_transfer!==undefined){
  const b=x.biological_transfer;
  if(!obj(b)||typeof b.proposed!=="boolean"||!["none","seed","spore","inoculum","soil_root","plant_material","organic_substrate","equipment"].includes(b.carrier_class)||(b.proposed&&b.carrier_class==="none"))throw Error("INVALID_BIOLOGICAL_TRANSFER");
  for(const f of ["origin_ref","destination_ref","provenance_ref","movement_rule_ref","biosecurity_review_ref","custodial_authority_ref"]){
   if(b[f]!==undefined&&!good(b[f]))throw Error("INVALID_BIOLOGICAL_TRANSFER_"+f.toUpperCase());
  }
 }
 // BioBlocks seed lot and optional fungal-treatment source declarations: references are not approvals.
 if(x.seed_lot!==undefined){
  const s=x.seed_lot;
  if(!obj(s))throw Error("INVALID_SEED_LOT");
  for(const f of ["lot_id","taxon_id","parent_plant_ref","collection_site_ref","collection_year","qa_protocol_ref","sampling_ref","viability_ref","custody_ref","storage_history_ref","test_date"])
   if(s[f]!==undefined&&!good(s[f]))throw Error("INVALID_SEED_LOT_"+f.toUpperCase());
  if(s.collection_year!==undefined&&!/^\\d{4}$/.test(s.collection_year))throw Error("INVALID_SEED_COLLECTION_YEAR");
 }
 if(x.fungal_inoculation!==undefined){
  const f=x.fungal_inoculation;
  if(!obj(f)||!["HOLD","DO_NOT_INOCULATE","INOCULATE"].includes(f.disposition))throw Error("INVALID_FUNGAL_DISPOSITION");
  for(const k of ["tst004_ref","fm039_ref","pathogen_screen_ref","host_association_ref","strain_source_ref"])
   if(f[k]!==undefined&&!good(f[k]))throw Error("INVALID_FUNGAL_"+k.toUpperCase());
 }
 // Source-only ecological survey evidence: non-detection is not species absence.
 if(x.survey!==undefined){
  const s=x.survey;
  if(!obj(s)||!["detected","not_detected","not_surveyed","unknown"].includes(s.detection_status))throw Error("INVALID_ECO_SURVEY");
  for(const f of ["protocol_ref","effort_unit","survey_window","seasonal_context_ref","detectability_ref"]){
   if(s[f]!==undefined&&!good(s[f]))throw Error("INVALID_SURVEY_FIELD_"+f.toUpperCase());
  }
  if(s.effort_value!==undefined&&(typeof s.effort_value!=="number"||!Number.isFinite(s.effort_value)||s.effort_value<=0))
   throw Error("INVALID_SURVEY_EFFORT");
 }
 if(x.survey_comparison!==undefined){
  const c=x.survey_comparison;
  if(!obj(c)||typeof c.proposed!=="boolean")throw Error("INVALID_SURVEY_COMPARISON");
  for(const f of ["baseline_ref","control_ref","seasonal_alignment_ref","method_comparability_ref","detectability_model_ref","sampling_design_ref"])
   if(c[f]!==undefined&&!good(c[f]))throw Error("INVALID_SURVEY_COMPARISON_"+f.toUpperCase());
 }

 // Source-only receiving pathway declaration; a claimed link is not verified hydrology.
 if(x.receiving_pathway!==undefined){
  const p=x.receiving_pathway;
  if(!obj(p)||typeof p.proposed!=="boolean")throw Error("INVALID_RECEIVING_PATHWAY");
  for(const [field,allowed] of [
   ["pathway_kind",["surface_water","groundwater","coastal","unknown"]],
   ["outcome_claim",["none","hypothesised","simulated","source_asserted","observed"]],
   ["site_condition",["intact","self_repairing","degraded","unknown"]],
   ["action",["protect_monitor","intervene","undetermined"]]])
   if(p[field]!==undefined&&!allowed.includes(p[field]))throw Error("INVALID_RECEIVING_"+field.toUpperCase());
  for(const field of ["source_system_ref","target_system_ref","pathway_evidence_ref","spatial_frame_ref","baseline_ref","method_ref","counterevidence_ref","accounting_scope_ref","field_receipt_ref","custodial_review_ref"])
   if(p[field]!==undefined&&!good(p[field]))throw Error("INVALID_RECEIVING_"+field.toUpperCase());
 }

 // Proposed benefit accounting is a distinct claim ledger, not a measured receiving-system outcome.
 if(x.benefit_accounting!==undefined){
  const a=x.benefit_accounting;
  if(!obj(a)||typeof a.proposed!=="boolean"||
   (a.contribution_basis!==undefined&&!["hypothesised","simulated","source_asserted","observed"].includes(a.contribution_basis)))
   throw Error("INVALID_BENEFIT_ACCOUNTING");
  for(const f of ["claim_ref","receiving_system_ref","accounting_period","metric_id","unit","baseline_ref","allocation_method_ref","overlap_register_ref","source_revision_ref","counterevidence_ref","independent_receipt_ref"])
   if(a[f]!==undefined&&!good(a[f]))throw Error("INVALID_BENEFIT_ACCOUNTING_"+f.toUpperCase());
  if(a.reported_value!==undefined&&(typeof a.reported_value!=="number"||!Number.isFinite(a.reported_value)))
   throw Error("INVALID_BENEFIT_ACCOUNTING_VALUE");
 }
 // Formula-derived ecological projections are scenario evidence, never field observations.
 if(x.projection_result!==undefined){
  const p=x.projection_result;
  if(!obj(p))throw Error("INVALID_ECO_PROJECTION");
  for(const f of ["scenario_ref","metric_ref","formula_ref","parameter_set_ref","horizon_ref","baseline_ref","uncertainty_ref","model_version_ref","spatial_support_ref","unit"])
   if(p[f]!==undefined&&!good(p[f]))throw Error("INVALID_PROJECTION_"+f.toUpperCase());
  if(p.input_source_refs!==undefined&&!stringList(p.input_source_refs))throw Error("INVALID_PROJECTION_INPUT_SOURCES");
  if(p.estimated_value!==undefined&&(typeof p.estimated_value!=="number"||!Number.isFinite(p.estimated_value)))
   throw Error("INVALID_PROJECTION_ESTIMATE");
 }
 // An observation-to-projection comparison is a proposed validation plan, never an observed outcome.
 if(x.projection_observation_comparison!==undefined){
  const c=x.projection_observation_comparison;
  if(!obj(c)||typeof c.proposed!=="boolean")throw Error("INVALID_PROJECTION_OBSERVATION_COMPARISON");
  for(const f of ["observation_ref","observation_source_ref","metric_ref","unit","spatial_support_ref","temporal_support_ref","baseline_ref","method_ref","uncertainty_ref","observation_qa_ref","comparison_method_ref","counterevidence_ref"])
   if(c[f]!==undefined&&!good(c[f]))throw Error("INVALID_PROJECTION_OBSERVATION_"+f.toUpperCase());
 }
 // Proposed validation statistics remain unverified even when the numeric summary is complete.
 if(x.validation_statistics!==undefined){
  const v=x.validation_statistics;
  if(!obj(v)||typeof v.proposed!=="boolean"||
   !["rmse","mae","bias","interval_coverage"].includes(v.statistic_kind))
   throw Error("INVALID_VALIDATION_STATISTICS");
  for(const f of ["statistic_unit","validation_set_ref","validation_source_ref","independence_design_ref",
   "uncertainty_propagation_ref","benchmark_ref","residual_diagnostics_ref",
   "counterevidence_ref","evaluation_period_ref","evaluation_spatial_support_ref","training_set_ref","holdout_policy_ref","split_unit_ref","leakage_audit_ref",
   "training_spatial_support_ref","validation_spatial_support_ref","training_temporal_support_ref","validation_temporal_support_ref",
   "spatial_partition_ref","temporal_partition_ref","spatial_buffer_ref","temporal_embargo_ref","spatial_leakage_audit_ref","temporal_leakage_audit_ref","spatial_autocorrelation_assessment_ref","temporal_dependence_assessment_ref","sampling_unit_independence_ref","replicate_structure_ref"])
   if(v[f]!==undefined&&!good(v[f]))throw Error("INVALID_VALIDATION_STATISTICS_"+f.toUpperCase());
  if(v.value!==undefined&&(typeof v.value!=="number"||!Number.isFinite(v.value)))
   throw Error("INVALID_VALIDATION_STATISTIC_VALUE");
  if(v.sample_count!==undefined&&(!Number.isSafeInteger(v.sample_count)||v.sample_count<2))
   throw Error("INVALID_VALIDATION_SAMPLE_COUNT");
  if(v.statistic_kind==="interval_coverage"&&v.value!==undefined&&(v.value<0||v.value>100))
   throw Error("INVALID_INTERVAL_COVERAGE");
 }
 // Source-only geometry-export pointer: never an actual validated or released map.
 if(x.geometry_export!==undefined){
  const g=x.geometry_export;
  if(!obj(g)||typeof g.proposed!=="boolean"||
   !["Point","LineString","Polygon","MultiPoint","MultiLineString","MultiPolygon","unknown"].includes(g.geometry_kind)||
   !["restricted","internal","aggregate_candidate","public_candidate"].includes(g.release_class)||
   (g.public_release_requested!==undefined&&typeof g.public_release_requested!=="boolean")||
   (g.has_z!==undefined&&typeof g.has_z!=="boolean"))throw Error("INVALID_GEOMETRY_EXPORT");
  for(const f of ["source_geometry_ref","source_revision_ref","crs","coordinate_unit","spatial_support_ref","geometry_validation_ref","generalisation_method_ref","sensitivity_review_ref","rights_review_ref","stewardship_review_ref","public_permission_ref","vertical_datum_ref"])
   if(g[f]!==undefined&&!good(g[f]))throw Error("INVALID_GEOMETRY_EXPORT_"+f.toUpperCase());
 }
if(x.measurement_basis!==undefined&&["raw","corrected","derived","reference"].includes(x.measurement_basis)===false)throw Error("INVALID_MEASUREMENT_BASIS");
 if(x.measurement_uncertainty!==undefined){
  const u=x.measurement_uncertainty;
  if(!obj(u)||typeof u.value!=="number"||!Number.isFinite(u.value)||u.value<0||!good(u.unit))
   throw Error("INVALID_MEASUREMENT_UNCERTAINTY");
 }
 if(x.result_qualifier!==undefined&&!["quantified","below_detection_limit","below_quantification_limit","above_range"].includes(x.result_qualifier))throw Error("INVALID_RESULT_QUALIFIER");
 if(x.reporting_bound!==undefined){
  const b=x.reporting_bound;
  if(!obj(b)||!["LOD","LOQ","UPPER_RANGE"].includes(b.kind)||typeof b.value!=="number"||!Number.isFinite(b.value)||b.value<=0||!good(b.unit)||(b.method_ref!==undefined&&!good(b.method_ref)))throw Error("INVALID_REPORTING_BOUND");
 }
}
// Translation can preserve formula syntax while corrupting SI unit glyphs.
// A flagged unit is not silently repaired or converted into scientific proof.
const suspiciousUnitEncoding=s=>good(s)&&/(?:\u00c2[\u00a0-\u00bf]|\u00c3[\u0080-\u00bf]|\u00e2[\u0080-\u00bf])/.test(s);
const add=(checks,c)=>{if(!checks.includes(c))checks.push(c)};
function compare(a,b,checks){
 for(const f of IDENTITY){
  if(a[f]!==b[f]){
   add(checks,a[f]===undefined||b[f]===undefined?"IDENTITY_FIELD_MISSING_"+f.toUpperCase():"IDENTITY_DIFFERENCE_"+f.toUpperCase());
  }
 }
 if(a.aggregation_scope!==b.aggregation_scope)add(checks,"AGGREGATION_SCOPE_DIFFERENT_OR_UNDECLARED");
 if(a.sample_count!==b.sample_count)add(checks,"SAMPLE_COUNT_DIFFERENT_OR_UNDECLARED");
 if(a.baseline_id!==b.baseline_id)add(checks,"BASELINE_DIFFERENT_OR_UNDECLARED");
 // Source-declared variable identity and temporal support are not interchangeable.
 // Same numeric value/unit does not make DO, nutrients, native cadence or aggregates equivalent.
 for(const [field,flag] of [
  ["observed_variable","OBSERVED_VARIABLE_DIFFERENT_OR_UNDECLARED"],
  ["native_interval","NATIVE_INTERVAL_DIFFERENT_OR_UNDECLARED"],
  ["aggregation_period","AGGREGATION_PERIOD_DIFFERENT_OR_UNDECLARED"]]){
  if(a[field]!==b[field])add(checks,flag);
 }
 if(a.evidence_class!==b.evidence_class)add(checks,"EVIDENCE_CLASS_DIFFERENT_OR_UNDECLARED");
 if(a.observed_at!==b.observed_at)add(checks,"OBSERVATION_TIME_DIFFERENT_OR_UNDECLARED");
 if(a.method_id!==b.method_id)add(checks,"METHOD_DIFFERENT_OR_UNDECLARED");
 // Raw, corrected and derived readings must not collapse solely on value/unit.
 for(const [field,flag] of [
  ["measurement_basis","MEASUREMENT_BASIS_DIFFERENT_OR_UNDECLARED"],
  ["correction_method_id","CORRECTION_METHOD_DIFFERENT_OR_UNDECLARED"],
  ["uncertainty_basis","UNCERTAINTY_BASIS_DIFFERENT_OR_UNDECLARED"]]){
  if(a[field]!==b[field])add(checks,flag);
 }
 if(!equal(a.measurement_uncertainty??null,b.measurement_uncertainty??null))
  add(checks,"MEASUREMENT_UNCERTAINTY_DIFFERENT_OR_UNDECLARED");
 if(a.result_qualifier!==b.result_qualifier)add(checks,"RESULT_QUALIFIER_DIFFERENT_OR_UNDECLARED");
 if(!equal(a.reporting_bound??null,b.reporting_bound??null))add(checks,"REPORTING_BOUND_DIFFERENT_OR_UNDECLARED");
 if(!equal(a.biological_transfer??null,b.biological_transfer??null))add(checks,"BIOLOGICAL_TRANSFER_SCOPE_OR_PROVENANCE_DIFFERENT");
 if(!equal(a.seed_lot??null,b.seed_lot??null))add(checks,"SEED_LOT_IDENTITY_OR_QA_DIFFERENT");
 if(!equal(a.fungal_inoculation??null,b.fungal_inoculation??null))add(checks,"FUNGAL_TREATMENT_DISPOSITION_OR_EVIDENCE_DIFFERENT");
 if(!equal(a.survey??null,b.survey??null))add(checks,"SURVEY_EFFORT_METHOD_OR_DETECTION_DIFFERENT");
 if(!equal(a.survey_comparison??null,b.survey_comparison??null))add(checks,"SURVEY_COMPARISON_DESIGN_DIFFERENT");
 if(!equal(a.receiving_pathway??null,b.receiving_pathway??null))add(checks,"RECEIVING_PATHWAY_PROVENANCE_OR_SCOPE_DIFFERENT");
 if(!equal(a.benefit_accounting??null,b.benefit_accounting??null))add(checks,"BENEFIT_ACCOUNTING_CLAIM_SCOPE_OR_ATTRIBUTION_DIFFERENT");
 if(!equal(a.geometry_export??null,b.geometry_export??null))add(checks,"GEOMETRY_EXPORT_PROVENANCE_OR_RELEASE_SCOPE_DIFFERENT");
if(!equal(a.projection_result??null,b.projection_result??null))add(checks,"PROJECTION_SCENARIO_OR_MODEL_PROVENANCE_DIFFERENT");
 if(!equal(a.projection_observation_comparison??null,b.projection_observation_comparison??null))
  add(checks,"PROJECTION_OBSERVATION_VALIDATION_DESIGN_DIFFERENT");
 if(!equal(a.validation_statistics??null,b.validation_statistics??null))
  add(checks,"VALIDATION_STATISTICS_DESIGN_OR_RESULT_DIFFERENT");
 // Field QA, missingness and instrument provenance are independent of measured value.
 for(const [field,flag] of [
  ["station_instrument_id","INSTRUMENT_ID_DIFFERENT_OR_UNDECLARED"],
  ["qa_flag","QA_STATE_DIFFERENT_OR_UNDECLARED"],
  ["missing_data_state","MISSING_DATA_STATE_DIFFERENT_OR_UNDECLARED"],
  ["calibration_verification_ref","CALIBRATION_REF_DIFFERENT_OR_UNDECLARED"],
  ["siting_metadata_ref","SITING_REF_DIFFERENT_OR_UNDECLARED"],
  ["source_provenance_ref","PROVENANCE_REVISION_DIFFERENT_OR_UNDECLARED"]]){
  if(a[field]!==b[field])add(checks,flag);
 }
 if(a.frame!==b.frame)add(checks,"FRAME_TRANSFORM_OR_DEFINITION_REQUIRED");
 if(a.configuration!==b.configuration)add(checks,"CONFIGURATION_VARIANT");
 if(a.epoch!==b.epoch)add(checks,"TIME_VARIANT");
 if(a.environment_id!==b.environment_id||!equal(a.environment??null,b.environment??null))
  add(checks,"ENVIRONMENT_CONTEXT_DIFFERENT");
 if(a.unit!==b.unit&&a.unit!==undefined&&b.unit!==undefined)add(checks,"UNIT_CONVERSION_REQUIRED");
 else if((a.unit===undefined)!==(b.unit===undefined))add(checks,"UNIT_UNDECLARED");
 if(!equal(a.measurement??null,b.measurement??null)){
  if(a.measurement&&b.measurement&&a.measurement.unit!==b.measurement.unit)add(checks,"UNIT_CONVERSION_REQUIRED");
  add(checks,"MEASUREMENT_VALUE_OR_METHOD_DIFFERENT");
 }
 if(!equal(a.geometry??null,b.geometry??null)){
  if(a.geometry?.crs!==b.geometry?.crs)add(checks,"GEOMETRY_CRS_DIFFERENT_OR_UNDECLARED");
  add(checks,"GEOMETRY_DIFFERENT_OR_UNDECLARED");
 }
 if(a.geometry?.coordinates.length===3&&!a.geometry.vertical_datum||
    b.geometry?.coordinates.length===3&&!b.geometry.vertical_datum)add(checks,"VERTICAL_DATUM_REQUIRED");
}
function completeness(x,checks){
 const unitFields=[x.unit,x.measurement?.unit,x.measurement_uncertainty?.unit,
  x.reporting_bound?.unit,x.projection_result?.unit,x.benefit_accounting?.unit,
  x.geometry_export?.coordinate_unit,x.validation_statistics?.statistic_unit];
 if(unitFields.some(suspiciousUnitEncoding))add(checks,"SOURCE_UNIT_ENCODING_UNRESOLVED");
 if(!good(x.evidence_class))add(checks,"EVIDENCE_CLASS_REQUIRED");
 if(x.semantic_type==="sensor_reading"&&!x.measurement)add(checks,"SENSOR_MEASUREMENT_REQUIRED");
 if(x.semantic_type==="sensor_reading"&&!good(x.observed_variable))add(checks,"OBSERVED_VARIABLE_REQUIRED");
 if(x.semantic_type==="sensor_reading"&&!good(x.native_interval))add(checks,"NATIVE_INTERVAL_REQUIRED");
 if(["average","mean","accumulated","sum","rolling_average","rolling_sum"].includes(x.aggregation_scope?.toLowerCase())&&!good(x.aggregation_period))
  add(checks,"AGGREGATION_PERIOD_REQUIRED");
 if(x.measurement&&good(x.unit)&&x.unit!==x.measurement.unit)add(checks,"MEASUREMENT_UNIT_CONFLICT");
 if(x.measurement_basis==="corrected"&&!good(x.correction_method_id))add(checks,"CORRECTION_METHOD_REQUIRED");
 if(good(x.correction_method_id)&&!good(x.measurement_basis))add(checks,"MEASUREMENT_BASIS_REQUIRED");
 if(x.measurement_uncertainty){
  if(!x.measurement)add(checks,"UNCERTAINTY_WITHOUT_MEASUREMENT");
  if(!good(x.uncertainty_basis))add(checks,"UNCERTAINTY_BASIS_REQUIRED");
  if(x.measurement&&x.measurement_uncertainty.unit!==x.measurement.unit)add(checks,"UNCERTAINTY_UNIT_CONFLICT");
 }

 // Proposed movement always requires specialist and applicable custodial/statutory review.
 if(x.biological_transfer?.proposed){
  add(checks,"BIOLOGICAL_TRANSFER_REVIEW_REQUIRED");
  for(const [f,flag] of [["origin_ref","BIOLOGICAL_TRANSFER_ORIGIN_REQUIRED"],["destination_ref","BIOLOGICAL_TRANSFER_DESTINATION_REQUIRED"],["provenance_ref","BIOLOGICAL_TRANSFER_PROVENANCE_REQUIRED"],["movement_rule_ref","BIOLOGICAL_TRANSFER_MOVEMENT_RULE_REQUIRED"],["biosecurity_review_ref","BIOLOGICAL_TRANSFER_REVIEW_RECEIPT_REQUIRED"]]){
   if(!good(x.biological_transfer[f]))add(checks,flag);
  }
 }
 // A proposed seed transfer cannot be qualified from a species label alone.
 if(x.biological_transfer?.proposed&&x.biological_transfer.carrier_class==="seed"){
  if(!x.seed_lot)add(checks,"SEED_LOT_DESCRIPTOR_REQUIRED");
  else{
   for(const [f,flag] of [["lot_id","SEED_LOT_ID_REQUIRED"],["taxon_id","SEED_LOT_TAXON_REQUIRED"],["parent_plant_ref","SEED_PARENT_PROVENANCE_REQUIRED"],["collection_site_ref","SEED_COLLECTION_SITE_REQUIRED"],["qa_protocol_ref","SEED_QUALITY_PROTOCOL_REQUIRED"],["sampling_ref","SEED_SAMPLING_RATIONALE_REQUIRED"],["custody_ref","SEED_CUSTODY_REQUIRED"]])
    if(!good(x.seed_lot[f]))add(checks,flag);
   if(good(x.taxon_id)&&good(x.seed_lot.taxon_id)&&x.taxon_id!==x.seed_lot.taxon_id)add(checks,"SEED_LOT_TAXON_CONFLICT");
  }
 }
 // TST-004/FM-039 fungal disposition is a source claim, not movement or release authority.
 if(x.biological_transfer?.proposed&&["inoculum","spore"].includes(x.biological_transfer.carrier_class)){
  if(!x.fungal_inoculation)add(checks,"FUNGAL_DISPOSITION_REQUIRED");
  else if(x.fungal_inoculation.disposition==="DO_NOT_INOCULATE")add(checks,"FUNGAL_PROPOSED_TRANSFER_CONTRADICTS_EXCLUSION");
  else if(x.fungal_inoculation.disposition==="INOCULATE"){
   for(const [f,flag] of [["tst004_ref","FUNGAL_TST004_REQUIRED"],["fm039_ref","FUNGAL_FM039_REQUIRED"],["pathogen_screen_ref","FUNGAL_PATHOGEN_SCREEN_REQUIRED"],["host_association_ref","FUNGAL_HOST_EVIDENCE_REQUIRED"],["strain_source_ref","FUNGAL_STRAIN_PROVENANCE_REQUIRED"]])
    if(!good(x.fungal_inoculation[f]))add(checks,flag);
  }
 }
 // Ecology survey methods/frequencies are design declarations, not actual sampling receipts.
 // Even a properly documented zero-detection survey cannot prove biological absence.
 if(x.survey){
  const s=x.survey;
  if(s.detection_status==="not_surveyed"){
   add(checks,"SURVEY_NOT_CONDUCTED");
   if(x.evidence_class==="observed")add(checks,"OBSERVED_EVIDENCE_WITH_NO_SURVEY");
  }else if(s.detection_status==="unknown")add(checks,"SURVEY_DETECTION_STATUS_UNKNOWN");
  else{
   if(!good(s.protocol_ref))add(checks,"SURVEY_PROTOCOL_REQUIRED");
   if(!Number.isFinite(s.effort_value)||s.effort_value<=0||!good(s.effort_unit))add(checks,"SURVEY_EFFORT_REQUIRED");
   if(!good(s.survey_window))add(checks,"SURVEY_WINDOW_REQUIRED");
   if(s.detection_status==="not_detected"){
    add(checks,"NONDETECTION_NOT_ABSENCE");
    if(!good(s.detectability_ref))add(checks,"DETECTABILITY_UNVERIFIED");
   }
  }
 }
 // A proposed biodiversity change comparison is never proof of ecological impact.
 if(x.survey_comparison?.proposed){
  add(checks,"BIODIVERSITY_CHANGE_COMPARISON_REQUIRES_REVIEW");
  if(!x.survey||!["detected","not_detected"].includes(x.survey.detection_status))add(checks,"SURVEY_COMPARISON_OBSERVATION_REQUIRED");
  for(const [field,flag] of [
   ["baseline_ref","SURVEY_COMPARISON_BASELINE_REQUIRED"],
   ["control_ref","SURVEY_COMPARISON_CONTROL_REQUIRED"],
   ["seasonal_alignment_ref","SURVEY_COMPARISON_SEASONAL_ALIGNMENT_REQUIRED"],
   ["method_comparability_ref","SURVEY_COMPARISON_METHOD_ALIGNMENT_REQUIRED"],
   ["detectability_model_ref","SURVEY_COMPARISON_DETECTABILITY_REQUIRED"],
   ["sampling_design_ref","SURVEY_COMPARISON_SAMPLING_DESIGN_REQUIRED"]])
   if(!good(x.survey_comparison[field]))add(checks,flag);
 }

 // Receiving-system impact and intervention assertions require independent review.
 if(x.receiving_pathway?.proposed){
  const p=x.receiving_pathway;
  add(checks,"RECEIVING_PATHWAY_REVIEW_REQUIRED");
  for(const [field,flag] of [
   ["source_system_ref","RECEIVING_SOURCE_SYSTEM_REQUIRED"],
   ["target_system_ref","RECEIVING_TARGET_SYSTEM_REQUIRED"],
   ["pathway_kind","RECEIVING_PATHWAY_KIND_REQUIRED"],
   ["pathway_evidence_ref","RECEIVING_PATHWAY_EVIDENCE_REQUIRED"],
   ["spatial_frame_ref","RECEIVING_SPATIAL_FRAME_REQUIRED"],
   ["site_condition","RECEIVING_SITE_CONDITION_REQUIRED"],
   ["action","RECEIVING_ACTION_REQUIRED"],
   ["outcome_claim","RECEIVING_OUTCOME_BASIS_REQUIRED"]])
   if(!good(p[field]))add(checks,flag);
  if(good(p.source_system_ref)&&p.source_system_ref===p.target_system_ref)add(checks,"RECEIVING_SELF_LINK_REVIEW_REQUIRED");
  if(p.pathway_kind==="unknown")add(checks,"RECEIVING_PATHWAY_TYPE_UNRESOLVED");
  if(["intact","self_repairing"].includes(p.site_condition)&&p.action==="intervene")add(checks,"INTACT_SYSTEM_INTERVENTION_REVIEW_REQUIRED");
  if(p.outcome_claim&&p.outcome_claim!=="none"){
   add(checks,"RECEIVING_OUTCOME_NOT_VERIFIED");
   add(checks,"RECEIVING_NO_DOUBLE_COUNT_REVIEW_REQUIRED");
   for(const [field,flag] of [
    ["baseline_ref","RECEIVING_BASELINE_REQUIRED"],
    ["method_ref","RECEIVING_OUTCOME_METHOD_REQUIRED"],
    ["counterevidence_ref","RECEIVING_COUNTEREVIDENCE_REQUIRED"],
    ["accounting_scope_ref","RECEIVING_ACCOUNTING_SCOPE_REQUIRED"]])
    if(!good(p[field]))add(checks,flag);
   if(p.outcome_claim==="observed"){
    add(checks,"RECEIVING_OBSERVED_CLAIM_REQUIRES_INDEPENDENT_REVIEW");
    if(!good(p.field_receipt_ref))add(checks,"RECEIVING_FIELD_RECEIPT_REQUIRED");
   }
  }
 }

 // Shared receiving systems and upstream interventions cannot independently claim the same benefit.
 // Every proposed allocation stays unverified, even with a receipt or numeric contribution.
 if(x.benefit_accounting?.proposed){
  const a=x.benefit_accounting;
  add(checks,"BENEFIT_ACCOUNTING_NOT_VERIFIED");
  add(checks,"BENEFIT_ACCOUNTING_NO_DOUBLE_COUNT_REVIEW_REQUIRED");
  if(!x.receiving_pathway?.proposed)add(checks,"BENEFIT_ACCOUNTING_PATHWAY_REQUIRED");
  for(const [field,flag] of [
   ["claim_ref","BENEFIT_CLAIM_REF_REQUIRED"],
   ["receiving_system_ref","BENEFIT_RECEIVING_SYSTEM_REQUIRED"],
   ["accounting_period","BENEFIT_ACCOUNTING_PERIOD_REQUIRED"],
   ["metric_id","BENEFIT_METRIC_REQUIRED"],
   ["unit","BENEFIT_UNIT_REQUIRED"],
   ["baseline_ref","BENEFIT_BASELINE_REQUIRED"],
   ["allocation_method_ref","BENEFIT_ALLOCATION_METHOD_REQUIRED"],
   ["overlap_register_ref","BENEFIT_OVERLAP_REGISTER_REQUIRED"],
   ["source_revision_ref","BENEFIT_SOURCE_REVISION_REQUIRED"],
   ["counterevidence_ref","BENEFIT_COUNTEREVIDENCE_REQUIRED"],
   ["contribution_basis","BENEFIT_EVIDENCE_BASIS_REQUIRED"]])
   if(!good(a[field]))add(checks,flag);
  if(good(a.receiving_system_ref)&&good(x.receiving_pathway?.target_system_ref)&&
   a.receiving_system_ref!==x.receiving_pathway.target_system_ref)add(checks,"BENEFIT_RECEIVING_SYSTEM_CONFLICT");
  if(good(a.contribution_basis)&&good(x.receiving_pathway?.outcome_claim)&&
   a.contribution_basis!==x.receiving_pathway.outcome_claim)add(checks,"BENEFIT_OUTCOME_BASIS_CONFLICT");
  if(a.contribution_basis==="observed"){
   add(checks,"BENEFIT_OBSERVED_ATTRIBUTION_REQUIRES_INDEPENDENT_REVIEW");
   if(!good(a.independent_receipt_ref))add(checks,"BENEFIT_INDEPENDENT_RECEIPT_REQUIRED");
  }
 }
 // Receiving-system source geometry is not verified field geometry or public release.
 if(x.geometry_export?.proposed){
  const g=x.geometry_export;
  add(checks,"GEOMETRY_EXPORT_SOURCE_ONLY_REVIEW_REQUIRED");
  if(!["receiving_system","site","habitat"].includes(x.semantic_type))add(checks,"GEOMETRY_EXPORT_TYPE_REVIEW_REQUIRED");
  for(const [f,flag] of [
   ["source_geometry_ref","GEOMETRY_EXPORT_SOURCE_REQUIRED"],
   ["source_revision_ref","GEOMETRY_EXPORT_REVISION_REQUIRED"],
   ["crs","GEOMETRY_EXPORT_CRS_REQUIRED"],
   ["coordinate_unit","GEOMETRY_EXPORT_COORDINATE_UNIT_REQUIRED"],
   ["spatial_support_ref","GEOMETRY_EXPORT_SPATIAL_SUPPORT_REQUIRED"],
   ["geometry_validation_ref","GEOMETRY_EXPORT_VALIDATION_REQUIRED"],
   ["rights_review_ref","GEOMETRY_EXPORT_RIGHTS_REVIEW_REQUIRED"],
   ["stewardship_review_ref","GEOMETRY_EXPORT_STEWARDSHIP_REVIEW_REQUIRED"]])
   if(!good(g[f]))add(checks,flag);
  if(g.geometry_kind==="unknown")add(checks,"GEOMETRY_EXPORT_KIND_UNRESOLVED");
  if(g.has_z&&!good(g.vertical_datum_ref))add(checks,"GEOMETRY_EXPORT_VERTICAL_DATUM_REQUIRED");
  if(g.public_release_requested){
   add(checks,"GEOMETRY_EXPORT_PUBLIC_RELEASE_NOT_AUTHORISED");
   if(["restricted","internal"].includes(g.release_class))add(checks,"GEOMETRY_EXPORT_RELEASE_CLASS_CONFLICT");
   for(const [f,flag] of [
    ["generalisation_method_ref","GEOMETRY_EXPORT_GENERALISATION_REQUIRED"],
    ["sensitivity_review_ref","GEOMETRY_EXPORT_SENSITIVITY_REVIEW_REQUIRED"],
    ["public_permission_ref","GEOMETRY_EXPORT_PUBLIC_PERMISSION_REQUIRED"]])
    if(!good(g[f]))add(checks,flag);
  }
 }
// ONT-019: model projections are not field observations, even with an estimated number.
 if(x.semantic_type==="projection_result"){
  add(checks,"PROJECTION_NOT_FIELD_OBSERVATION");
  add(checks,"PROJECTION_REQUIRES_MODEL_REVIEW");
  if(x.evidence_class==="observed")add(checks,"PROJECTION_OBSERVED_EVIDENCE_CONFLICT");
  if(!x.projection_result)add(checks,"PROJECTION_DESCRIPTOR_REQUIRED");
  else{
   const p=x.projection_result;
   for(const [field,flag] of [
    ["scenario_ref","PROJECTION_SCENARIO_REQUIRED"],
    ["metric_ref","PROJECTION_METRIC_REQUIRED"],
    ["formula_ref","PROJECTION_FORMULA_REQUIRED"],
    ["parameter_set_ref","PROJECTION_PARAMETERS_REQUIRED"],
    ["horizon_ref","PROJECTION_HORIZON_REQUIRED"],
    ["baseline_ref","PROJECTION_BASELINE_REQUIRED"],
    ["uncertainty_ref","PROJECTION_UNCERTAINTY_REQUIRED"],
    ["model_version_ref","PROJECTION_MODEL_VERSION_REQUIRED"]])
    if(!good(p[field]))add(checks,flag);
   if(!p.input_source_refs?.length)add(checks,"PROJECTION_INPUT_SOURCES_REQUIRED");
   if(p.estimated_value!==undefined&&!good(p.unit))add(checks,"PROJECTION_ESTIMATE_UNIT_REQUIRED");
  }
 }
 // ONT-009 vs ONT-019: matching reference labels is not proof of predictive accuracy.
 if(x.projection_observation_comparison?.proposed){
  const c=x.projection_observation_comparison,p=x.projection_result;
  add(checks,"PROJECTION_OBSERVATION_COMPARISON_REQUIRES_REVIEW");
  if(x.semantic_type!=="projection_result")add(checks,"PROJECTION_COMPARISON_TYPE_CONFLICT");
  for(const [f,flag] of [
   ["observation_ref","PROJECTION_COMPARISON_OBSERVATION_REQUIRED"],
   ["observation_source_ref","PROJECTION_COMPARISON_OBSERVATION_SOURCE_REQUIRED"],
   ["metric_ref","PROJECTION_COMPARISON_METRIC_REQUIRED"],
   ["unit","PROJECTION_COMPARISON_UNIT_REQUIRED"],
   ["spatial_support_ref","PROJECTION_COMPARISON_SPATIAL_SUPPORT_REQUIRED"],
   ["temporal_support_ref","PROJECTION_COMPARISON_TEMPORAL_SUPPORT_REQUIRED"],
   ["baseline_ref","PROJECTION_COMPARISON_BASELINE_REQUIRED"],
   ["method_ref","PROJECTION_COMPARISON_OBSERVATION_METHOD_REQUIRED"],
   ["uncertainty_ref","PROJECTION_COMPARISON_OBSERVATION_UNCERTAINTY_REQUIRED"],
   ["observation_qa_ref","PROJECTION_COMPARISON_OBSERVATION_QA_REQUIRED"],
   ["comparison_method_ref","PROJECTION_COMPARISON_METHOD_REQUIRED"],
   ["counterevidence_ref","PROJECTION_COMPARISON_COUNTEREVIDENCE_REQUIRED"]])
   if(!good(c[f]))add(checks,flag);
  if(!good(p?.spatial_support_ref))add(checks,"PROJECTION_SPATIAL_SUPPORT_REQUIRED_FOR_COMPARISON");
  for(const [cf,pf,flag] of [
   ["metric_ref","metric_ref","PROJECTION_COMPARISON_METRIC_MISMATCH"],
   ["unit","unit","PROJECTION_COMPARISON_UNIT_MISMATCH"],
   ["spatial_support_ref","spatial_support_ref","PROJECTION_COMPARISON_SPATIAL_SUPPORT_MISMATCH"],
   ["temporal_support_ref","horizon_ref","PROJECTION_COMPARISON_TEMPORAL_SUPPORT_MISMATCH"],
   ["baseline_ref","baseline_ref","PROJECTION_COMPARISON_BASELINE_MISMATCH"]])
   if(good(c[cf])&&good(p?.[pf])&&c[cf]!==p[pf])add(checks,flag);
 }
 // A summary error statistic does not demonstrate predictive skill, uncertainty calibration or ecological benefit.
 if(x.validation_statistics?.proposed){
  const v=x.validation_statistics;
  add(checks,"VALIDATION_STATISTICS_INDEPENDENT_REVIEW_REQUIRED");
  if(x.semantic_type!=="projection_result"||!x.projection_observation_comparison?.proposed)
   add(checks,"VALIDATION_COMPARISON_DESIGN_REQUIRED");
  for(const [f,flag] of [
   ["statistic_unit","VALIDATION_STATISTIC_UNIT_REQUIRED"],
   ["validation_set_ref","VALIDATION_SET_REQUIRED"],
   ["training_set_ref","VALIDATION_TRAINING_SET_REQUIRED"],
   ["holdout_policy_ref","VALIDATION_HOLDOUT_POLICY_REQUIRED"],
   ["split_unit_ref","VALIDATION_SPLIT_UNIT_REQUIRED"],
   ["leakage_audit_ref","VALIDATION_LEAKAGE_AUDIT_REQUIRED"],
   ["validation_source_ref","VALIDATION_SOURCE_REQUIRED"],
   ["independence_design_ref","VALIDATION_INDEPENDENCE_DESIGN_REQUIRED"],
   ["uncertainty_propagation_ref","VALIDATION_UNCERTAINTY_PROPAGATION_REQUIRED"],
   ["benchmark_ref","VALIDATION_BENCHMARK_REQUIRED"],
   ["residual_diagnostics_ref","VALIDATION_RESIDUAL_DIAGNOSTICS_REQUIRED"],
   ["counterevidence_ref","VALIDATION_COUNTEREVIDENCE_REQUIRED"],
   ["evaluation_period_ref","VALIDATION_PERIOD_REQUIRED"],
   ["evaluation_spatial_support_ref","VALIDATION_SPATIAL_SUPPORT_REQUIRED"],
   ["training_spatial_support_ref","VALIDATION_TRAINING_SPATIAL_SUPPORT_REQUIRED"],
   ["validation_spatial_support_ref","VALIDATION_HOLDOUT_SPATIAL_SUPPORT_REQUIRED"],
   ["training_temporal_support_ref","VALIDATION_TRAINING_TEMPORAL_SUPPORT_REQUIRED"],
   ["validation_temporal_support_ref","VALIDATION_HOLDOUT_TEMPORAL_SUPPORT_REQUIRED"],
   ["spatial_partition_ref","VALIDATION_SPATIAL_PARTITION_REQUIRED"],
   ["temporal_partition_ref","VALIDATION_TEMPORAL_PARTITION_REQUIRED"],
   ["spatial_buffer_ref","VALIDATION_SPATIAL_BUFFER_REVIEW_REQUIRED"],
   ["temporal_embargo_ref","VALIDATION_TEMPORAL_EMBARGO_REVIEW_REQUIRED"],
   ["spatial_leakage_audit_ref","VALIDATION_SPATIAL_LEAKAGE_AUDIT_REQUIRED"],
   ["temporal_leakage_audit_ref","VALIDATION_TEMPORAL_LEAKAGE_AUDIT_REQUIRED"],
   ["spatial_autocorrelation_assessment_ref","VALIDATION_SPATIAL_AUTOCORRELATION_ASSESSMENT_REQUIRED"],
   ["temporal_dependence_assessment_ref","VALIDATION_TEMPORAL_DEPENDENCE_ASSESSMENT_REQUIRED"],
   ["sampling_unit_independence_ref","VALIDATION_SAMPLING_UNIT_INDEPENDENCE_REQUIRED"],
   ["replicate_structure_ref","VALIDATION_REPLICATE_STRUCTURE_REQUIRED"]])
   if(!good(v[f]))add(checks,flag);
  if(good(v.training_set_ref)&&good(v.validation_set_ref)&&v.training_set_ref===v.validation_set_ref)
   add(checks,"VALIDATION_TRAINING_AND_HOLDOUT_IDENTICAL");
  // Identical support can be valid for some designs, but is never independent by declaration alone.
  // These are review flags, not proofs of overlap or actual data leakage.
  if(good(v.training_spatial_support_ref)&&v.training_spatial_support_ref===v.validation_spatial_support_ref)
   add(checks,"VALIDATION_SPATIAL_SUPPORT_OVERLAP_REVIEW");
  if(good(v.training_temporal_support_ref)&&v.training_temporal_support_ref===v.validation_temporal_support_ref)
   add(checks,"VALIDATION_TEMPORAL_SUPPORT_OVERLAP_REVIEW");
  if(!Number.isSafeInteger(v.sample_count))add(checks,"VALIDATION_SAMPLE_COUNT_REQUIRED");
  if(v.value===undefined)add(checks,"VALIDATION_STATISTIC_VALUE_REQUIRED");
  if(["rmse","mae","bias"].includes(v.statistic_kind)&&
   good(v.statistic_unit)&&good(x.projection_result?.unit)&&v.statistic_unit!==x.projection_result.unit)
   add(checks,"VALIDATION_STATISTIC_UNIT_CONFLICT");
  if(v.statistic_kind==="interval_coverage"&&v.statistic_unit!=="percent")
   add(checks,"VALIDATION_COVERAGE_PERCENT_UNIT_REQUIRED");
  if(good(v.evaluation_period_ref)&&good(x.projection_observation_comparison?.temporal_support_ref)&&
   v.evaluation_period_ref!==x.projection_observation_comparison.temporal_support_ref)
   add(checks,"VALIDATION_EVALUATION_PERIOD_MISMATCH");
  if(good(v.evaluation_spatial_support_ref)&&good(x.projection_observation_comparison?.spatial_support_ref)&&
   v.evaluation_spatial_support_ref!==x.projection_observation_comparison.spatial_support_ref)
   add(checks,"VALIDATION_EVALUATION_SPACE_MISMATCH");
 }
 // Censored reports are bounds, not measured point values.
 if(x.reporting_bound&&!good(x.result_qualifier))add(checks,"RESULT_QUALIFIER_REQUIRED");
 if(x.reporting_bound){
  if(!good(x.reporting_bound.method_ref))add(checks,"REPORTING_BOUND_METHOD_REQUIRED");
  if(good(x.unit)&&x.reporting_bound.unit!==x.unit)add(checks,"REPORTING_BOUND_UNIT_CONFLICT");
 }
 const kinds={below_detection_limit:"LOD",below_quantification_limit:"LOQ",above_range:"UPPER_RANGE"};
 if(kinds[x.result_qualifier]){
  add(checks,"CENSORED_RESULT_REQUIRES_REVIEW");
  if(!x.reporting_bound)add(checks,"CENSORED_REPORTING_BOUND_REQUIRED");
  else if(x.reporting_bound.kind!==kinds[x.result_qualifier])add(checks,"CENSOR_BOUND_KIND_MISMATCH");
  if(x.measurement)add(checks,"CENSORED_RESULT_NUMERIC_POINT_CONFLICT");
 }
 if(OBSERVATIONS.has(x.semantic_type)){
  // These optional source QA fields must never silently certify an observation.
  if(["provisional","flagged","missing","not_run","untested","pending"].includes(x.qa_flag?.toLowerCase().replace(/[\s-]+/g,"_")))add(checks,"QA_STATE_REQUIRES_REVIEW");
  // A source-asserted validated sensor QA flag needs traceable instrument and verification references.
  // References are not proof that calibration or QA succeeded.
  if(x.semantic_type==="sensor_reading"&&["validated","verified","calibrated","qa_pass","passed"].includes(x.qa_flag?.toLowerCase().replace(/[\s-]+/g,"_"))){
   if(!good(x.station_instrument_id))add(checks,"QA_VALIDATION_INSTRUMENT_REQUIRED");
   if(!good(x.calibration_verification_ref))add(checks,"QA_VALIDATION_CALIBRATION_REF_REQUIRED");
  }
  if(x.missing_data_state&&x.missing_data_state.toLowerCase()!=="observed"){
   add(checks,"MISSING_OR_NONOBSERVED_DATA_STATE");
   if(x.measurement)add(checks,"MISSING_DATA_MEASUREMENT_CONFLICT");
   if(x.evidence_class==="observed")add(checks,"OBSERVED_EVIDENCE_WITH_MISSING_DATA");
  }
  if(!good(x.observed_at))add(checks,"OBSERVATION_TIME_REQUIRED");
  else if(!validObservedAt(x.observed_at))add(checks,"OBSERVATION_TIMESTAMP_INVALID_OR_UNZONED");
  if(!good(x.method_id))add(checks,"METHOD_REQUIRED");
  if(!good(x.subject_kind)||!good(x.subject_id))add(checks,"SUBJECT_IDENTITY_REQUIRED");
  if(!good(x.site_id)&&!good(x.station_id)&&!x.geometry)add(checks,"SPATIAL_CONTEXT_REQUIRED");
  if(x.measurement&&!good(x.measurement.unit))add(checks,"UNIT_REQUIRED");
  if(x.geometry&&!good(x.geometry.crs))add(checks,"GEOMETRY_CRS_REQUIRED");
 }
 if(x.semantic_type==="ecological_function"&&!good(x.ecological_function_id))add(checks,"ECOLOGICAL_FUNCTION_ID_REQUIRED");
 if(x.semantic_type==="functional_guild"&&!good(x.functional_guild_id))add(checks,"FUNCTIONAL_GUILD_ID_REQUIRED");
 if(x.semantic_type==="receiving_system"&&!good(x.receiving_system_id))add(checks,"RECEIVING_SYSTEM_ID_REQUIRED");
 if(x.semantic_type==="specimen"&&!good(x.specimen_id))add(checks,"SPECIMEN_ID_REQUIRED");
 if(["species","taxon"].includes(x.semantic_type)&&!good(x.taxon_id))add(checks,"TAXON_ID_REQUIRED");
 if(x.semantic_type==="population"&&(!good(x.population_id)||!good(x.taxon_id)))add(checks,"POPULATION_TAXON_ID_REQUIRED");
 if(x.geometry&&good(x.frame)&&x.frame!==x.geometry.crs)add(checks,"FRAME_CRS_RECONCILIATION_REQUIRED");
 if(x.geometry?.coordinates.length===3&&!x.geometry.vertical_datum)add(checks,"VERTICAL_DATUM_REQUIRED");
}
export function planEcoAlignment({novel,known_objects=[],authorised_object_ids=[],authorised_source_ids=[],max_candidates=20}={}){
 validateConcept(novel);
 if(!Array.isArray(known_objects)||known_objects.length>5000||!stringList(authorised_object_ids)||
 !stringList(authorised_source_ids)||!Number.isSafeInteger(max_candidates)||max_candidates<1||max_candidates>100)
  throw Error("INVALID_ECO_SCOPE");
 const allowedIds=new Set(authorised_object_ids),allowedSources=new Set(authorised_source_ids);
 const novelRefs=novel.source_refs.filter(s=>allowedSources.has(s));
 // Qualify incoming evidence even if there are no authorised known-object matches.
 // A zero-match result is not proof that the observation or source is complete.
 const novelChecks=[];
 completeness(novel,novelChecks);
 if(!novelRefs.length)add(novelChecks,"EVIDENCE_SOURCE_GAP");
 if(novelRefs.length<novel.source_refs.length)add(novelChecks,"NOVEL_SOURCE_SCOPE_PARTIAL");
 if(novel.projection_result?.input_source_refs?.some(s=>!allowedSources.has(s)))
  add(novelChecks,"NOVEL_PROJECTION_INPUT_SOURCE_SCOPE_PARTIAL");
 if(novel.projection_observation_comparison?.observation_source_ref&&
    !allowedSources.has(novel.projection_observation_comparison.observation_source_ref))
  add(novelChecks,"NOVEL_COMPARISON_OBSERVATION_SOURCE_SCOPE_PARTIAL");
 if(novel.validation_statistics?.validation_source_ref&&
    !allowedSources.has(novel.validation_statistics.validation_source_ref))
  add(novelChecks,"NOVEL_VALIDATION_SOURCE_SCOPE_PARTIAL");
 const seen=new Set(),out=[];
 for(const k of known_objects){
  validateConcept(k);
  if(!good(k.object_id)||!allowedIds.has(k.object_id))continue;
  if(seen.has(k.object_id))throw Error("DUPLICATE_AUTHORISED_OBJECT_ID");
  seen.add(k.object_id);
  if(k.semantic_type!==novel.semantic_type)continue;
  const checks=[];
  completeness(novel,checks);completeness(k,checks);compare(novel,k,checks);
  const refs=k.source_refs.filter(s=>allowedSources.has(s));
  if(!novelRefs.length||!refs.length)add(checks,"EVIDENCE_SOURCE_GAP");
  else if(!refs.some(s=>novelRefs.includes(s)))add(checks,"SOURCE_LINEAGE_DISJOINT_REVIEW");
  if(novelRefs.length<novel.source_refs.length)add(checks,"NOVEL_SOURCE_SCOPE_PARTIAL");
  if(refs.length<k.source_refs.length)add(checks,"KNOWN_SOURCE_SCOPE_PARTIAL");
 if(novel.projection_result?.input_source_refs?.some(s=>!allowedSources.has(s)))
  add(checks,"NOVEL_PROJECTION_INPUT_SOURCE_SCOPE_PARTIAL");
 if(k.projection_result?.input_source_refs?.some(s=>!allowedSources.has(s)))
  add(checks,"KNOWN_PROJECTION_INPUT_SOURCE_SCOPE_PARTIAL");
 if(novel.projection_observation_comparison?.observation_source_ref&&
    !allowedSources.has(novel.projection_observation_comparison.observation_source_ref))
  add(checks,"NOVEL_COMPARISON_OBSERVATION_SOURCE_SCOPE_PARTIAL");
 if(k.projection_observation_comparison?.observation_source_ref&&
    !allowedSources.has(k.projection_observation_comparison.observation_source_ref))
  add(checks,"KNOWN_COMPARISON_OBSERVATION_SOURCE_SCOPE_PARTIAL");
  if(k.validation_statistics?.validation_source_ref&&
     !allowedSources.has(k.validation_statistics.validation_source_ref))
   add(checks,"KNOWN_VALIDATION_SOURCE_SCOPE_PARTIAL");
  if(novel.validation_statistics?.validation_source_ref&&
     !allowedSources.has(novel.validation_statistics.validation_source_ref))
   add(checks,"NOVEL_VALIDATION_SOURCE_SCOPE_PARTIAL");
  const exactId=novel.object_id===k.object_id;
  out.push({known_object_id:k.object_id,
   state:exactId?"SAME_ID_CLAIM_REQUIRES_PROOF":checks.length?"REVIEW_DIFFERENCE":"TYPED_ALIGNMENT_CANDIDATE",
   checks,permitted_known_source_refs:refs,auto_merge:false,object_id_minted:false,source_rights_verified:false});
 }
 out.sort((a,b)=>a.checks.length-b.checks.length||a.known_object_id.localeCompare(b.known_object_id));
 return {schema:ECO_ALIGNMENT_SCHEMA,state:"SOURCE_ONLY_ECO_REVIEW",file_space:"Eco.cgx",
  parent:"Cognigrex.cgx",semantic_type:novel.semantic_type,
  candidate_count:out.length,candidates:out.slice(0,max_candidates),
  novel_qualification_state:novelChecks.length?"REVIEW_REQUIRED":"SCHEMA_QUALIFIED_SOURCE_ONLY",
  novel_checks:novelChecks,
  incomplete_coverage:out.length>max_candidates,novel_permitted_source_refs:novelRefs,
  distinct_r0_sources_preserved:true,accepted_native_identity:false,db_readback:false,
  object_ids_minted:0,ecological_effect_verified:false,compute_invoked:false,
  unresolved:["source licence and ownership","current root/ACL and DBR acceptance","independent field evidence and counterevidence","geometry and measurement method validation"]};
}
