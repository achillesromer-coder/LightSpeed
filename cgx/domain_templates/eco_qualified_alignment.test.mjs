import test from "node:test";
import assert from "node:assert/strict";
import {planEcoAlignment} from "./eco_qualified_alignment.mjs";
const base={semantic_type:"ecological_observation",source_refs:["src-a"],evidence_class:"observed",
 subject_kind:"taxon",subject_id:"taxon:1",taxon_id:"taxon:1",specimen_id:"spec:1",
 site_id:"site:1",station_id:"station:1",observed_at:"2026-10-01T12:00:00Z",
 method_id:"field-method:1",frame:"EPSG:4326",
 geometry:{type:"Point",crs:"EPSG:4326",coordinates:[153.1,-27.2]},
 measurement:{value:4.3,unit:"mg/L"},unit:"mg/L",environment_id:"marine",
 environment:{salinity_psu:35},configuration:"field-v1",epoch:"2026"};
const known={...base,object_id:"known:1",source_refs:["src-b"]};
const run=(a=base,b=known,opts={})=>planEcoAlignment({novel:a,known_objects:[b],
 authorised_object_ids:["known:1"],authorised_source_ids:["src-a","src-b"],...opts});
const flags=(a,b=known)=>run(a,b).candidates[0].checks;
const changed=(key,value)=>({...base,[key]:value});
test("disjoint permitted source lineage is a review difference, never native merge",()=>{
 const x=run();assert.equal(x.candidates[0].state,"REVIEW_DIFFERENCE");
 assert.ok(x.candidates[0].checks.includes("SOURCE_LINEAGE_DISJOINT_REVIEW"));
 assert.equal(x.candidates[0].auto_merge,false);assert.equal(x.object_ids_minted,0);
 assert.equal(x.accepted_native_identity,false);assert.equal(x.db_readback,false);
});
test("taxon change is not collapsed",()=>assert.ok(flags(changed("taxon_id","taxon:2")).some(x=>x.includes("TAXON_ID"))));
test("specimen change is not collapsed",()=>assert.ok(flags(changed("specimen_id","spec:2")).some(x=>x.includes("SPECIMEN_ID"))));
test("geographic point change is not collapsed",()=>assert.ok(flags(changed("geometry",{...base.geometry,coordinates:[153.2,-27.2]})).includes("GEOMETRY_DIFFERENT_OR_UNDECLARED")));
test("observed and simulated are distinct",()=>assert.ok(flags(changed("evidence_class","simulated")).includes("EVIDENCE_CLASS_DIFFERENT_OR_UNDECLARED")));
test("observation date is distinct",()=>assert.ok(flags(changed("observed_at","2026-10-02T12:00:00Z")).includes("OBSERVATION_TIME_DIFFERENT_OR_UNDECLARED")));
test("measurement method is distinct",()=>assert.ok(flags(changed("method_id","other")).includes("METHOD_DIFFERENT_OR_UNDECLARED")));
test("environment is distinct",()=>assert.ok(flags(changed("environment",{salinity_psu:36})).includes("ENVIRONMENT_CONTEXT_DIFFERENT")));
test("units require explicit conversion",()=>assert.ok(flags(changed("unit","ug/L")).includes("UNIT_CONVERSION_REQUIRED")));
test("observation timestamp missing is a gate",()=>assert.ok(flags(changed("observed_at",undefined)).includes("OBSERVATION_TIME_REQUIRED")));
test("observation subject missing is a gate",()=>assert.ok(flags(changed("subject_id",undefined)).includes("SUBJECT_IDENTITY_REQUIRED")));
test("observation site/station/geometry missing is a gate",()=>assert.ok(flags({...base,site_id:undefined,station_id:undefined,geometry:undefined}).includes("SPATIAL_CONTEXT_REQUIRED")));
test("3D point without vertical datum is held",()=>assert.ok(flags(changed("geometry",{type:"Point",crs:"EPSG:4326",coordinates:[153,-27,10]})).includes("VERTICAL_DATUM_REQUIRED")));
test("unpermitted sources cause evidence gap",()=>assert.ok(run(base,known,{authorised_source_ids:[]}).candidates[0].checks.includes("EVIDENCE_SOURCE_GAP")));
test("unpermitted object never appears",()=>assert.equal(run(base,known,{authorised_object_ids:[]}).candidate_count,0));
test("specimen and observation types cannot be conflated",()=>assert.equal(run(base,{...known,semantic_type:"specimen"}).candidate_count,0));
test("invalid WGS84 longitude is rejected",()=>assert.throws(()=>run(changed("geometry",{type:"Point",crs:"EPSG:4326",coordinates:[220,-27]})),/INVALID_WGS84/));
test("known Object_ID cannot be self-certified",()=>assert.equal(run({...base,object_id:"known:1"}).candidates[0].state,"SAME_ID_CLAIM_REQUIRES_PROOF"));
test("duplicate authorised Object_ID rejected",()=>assert.throws(()=>planEcoAlignment({novel:base,known_objects:[known,known],authorised_object_ids:["known:1"],authorised_source_ids:["src-a","src-b"]}),/DUPLICATE_AUTHORISED_OBJECT_ID/));
test("no ecological impact is verified by alignment",()=>assert.equal(run().ecological_effect_verified,false));
test("shared permitted source lineage can remain a typed candidate without native admission",()=>{
 const x=run(base,{...known,source_refs:["src-a"]});
 assert.equal(x.candidates[0].state,"TYPED_ALIGNMENT_CANDIDATE");
 assert.equal(x.candidates[0].auto_merge,false);
});
test("novel source references outside the authorised scope remain visibly partial",()=>{
 assert.ok(flags({...base,source_refs:["src-a","unapproved-src"]},{...known,source_refs:["src-a"]}).includes("NOVEL_SOURCE_SCOPE_PARTIAL"));
});
test("known source references outside the authorised scope remain visibly partial",()=>{
 assert.ok(flags(base,{...known,source_refs:["src-a","unapproved-src"]}).includes("KNOWN_SOURCE_SCOPE_PARTIAL"));
});

test("unzoned timestamps cannot qualify",()=>{
 const a={...base,observed_at:"2026-10-01T12:00:00"},b={...known,source_refs:["src-a"],observed_at:"2026-10-01T12:00:00"};
 const x=run(a,b).candidates[0];assert.equal(x.state,"REVIEW_DIFFERENCE");assert.ok(x.checks.includes("OBSERVATION_TIMESTAMP_INVALID_OR_UNZONED"));
});
test("invalid leap day cannot qualify",()=>{
 const a={...base,observed_at:"2026-02-29T12:00:00Z"},b={...known,source_refs:["src-a"],observed_at:"2026-02-29T12:00:00Z"};
 assert.ok(run(a,b).candidates[0].checks.includes("OBSERVATION_TIMESTAMP_INVALID_OR_UNZONED"));
});
test("invalid timezone offset cannot qualify",()=>{
 const a={...base,observed_at:"2026-10-01T12:00:00+15:00"},b={...known,source_refs:["src-a"],observed_at:"2026-10-01T12:00:00+15:00"};
 assert.ok(run(a,b).candidates[0].checks.includes("OBSERVATION_TIMESTAMP_INVALID_OR_UNZONED"));
});
test("valid leap day and offset retain typed candidate",()=>{
 const a={...base,observed_at:"2024-02-29T12:00:00+10:00"},b={...known,source_refs:["src-a"],observed_at:"2024-02-29T12:00:00+10:00"};
 assert.equal(run(a,b).candidates[0].state,"TYPED_ALIGNMENT_CANDIDATE");
});

// Incoming evidence must be qualified independently of the known-object catalogue.
test("zero known candidates: valid incoming schema is only source-qualified, never admitted",()=>{
 const x=planEcoAlignment({novel:base,known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.equal(x.candidate_count,0);assert.equal(x.novel_qualification_state,"SCHEMA_QUALIFIED_SOURCE_ONLY");
 assert.equal(x.accepted_native_identity,false);assert.equal(x.db_readback,false);
});
test("zero known candidates: missing observation timestamp remains an explicit gate",()=>{
 const x=planEcoAlignment({novel:{...base,observed_at:undefined},known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.equal(x.novel_qualification_state,"REVIEW_REQUIRED");assert.ok(x.novel_checks.includes("OBSERVATION_TIME_REQUIRED"));
});
test("zero known candidates: no authorised source and partial scope remain explicit",()=>{
 const x=planEcoAlignment({novel:base,known_objects:[],authorised_object_ids:[],authorised_source_ids:[]});
 assert.ok(x.novel_checks.includes("EVIDENCE_SOURCE_GAP"));assert.ok(x.novel_checks.includes("NOVEL_SOURCE_SCOPE_PARTIAL"));
});
test("zero known candidates: impossible calendar date is not qualified",()=>{
 const x=planEcoAlignment({novel:{...base,observed_at:"2026-02-29T12:00:00Z"},known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.equal(x.novel_qualification_state,"REVIEW_REQUIRED");assert.ok(x.novel_checks.includes("OBSERVATION_TIMESTAMP_INVALID_OR_UNZONED"));
});
test("zero known candidates: schema example without measurement/evidence is not an observed sensor reading",()=>{
 const x=planEcoAlignment({novel:{...base,semantic_type:"sensor_reading",measurement:undefined,evidence_class:undefined},known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(x.novel_checks.includes("EVIDENCE_CLASS_REQUIRED"));assert.ok(x.novel_checks.includes("SENSOR_MEASUREMENT_REQUIRED"));
});

test("distinct source QA states are not aligned by identical values",()=>{
 const a={...base,qa_flag:"flagged"},b={...known,source_refs:["src-a"],qa_flag:"validated"};
 const x=run(a,b).candidates[0];
 assert.equal(x.state,"REVIEW_DIFFERENCE");
 assert.ok(x.checks.includes("QA_STATE_DIFFERENT_OR_UNDECLARED"));
 assert.ok(x.checks.includes("QA_STATE_REQUIRES_REVIEW"));
});
test("missing field data with numeric zero cannot become observed evidence",()=>{
 const a={...base,semantic_type:"sensor_reading",missing_data_state:"missing",measurement:{value:0,unit:"mg/L"}};
 const x=planEcoAlignment({novel:a,known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.equal(x.novel_qualification_state,"REVIEW_REQUIRED");
 assert.ok(x.novel_checks.includes("MISSING_DATA_MEASUREMENT_CONFLICT"));
 assert.ok(x.novel_checks.includes("OBSERVED_EVIDENCE_WITH_MISSING_DATA"));
});
test("provisional QA remains a review gate even with zero known candidates",()=>{
 const x=planEcoAlignment({novel:{...base,qa_flag:"provisional"},known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(x.novel_checks.includes("QA_STATE_REQUIRES_REVIEW"));
 assert.equal(x.novel_qualification_state,"REVIEW_REQUIRED");
});
test("instrument and calibration source changes remain distinct",()=>{
 const a={...base,station_instrument_id:"sensor-2",calibration_verification_ref:"cal-2"};
 const b={...known,source_refs:["src-a"],station_instrument_id:"sensor-1",calibration_verification_ref:"cal-1"};
 const c=run(a,b).candidates[0].checks;
 assert.ok(c.includes("INSTRUMENT_ID_DIFFERENT_OR_UNDECLARED"));
 assert.ok(c.includes("CALIBRATION_REF_DIFFERENT_OR_UNDECLARED"));
});
test("source provenance revisions and station siting cannot silently collapse",()=>{
 const a={...base,source_provenance_ref:"dataset-v2",siting_metadata_ref:"site-rev2"};
 const b={...known,source_refs:["src-a"],source_provenance_ref:"dataset-v1",siting_metadata_ref:"site-rev1"};
 const c=run(a,b).candidates[0].checks;
 assert.ok(c.includes("PROVENANCE_REVISION_DIFFERENT_OR_UNDECLARED"));
 assert.ok(c.includes("SITING_REF_DIFFERENT_OR_UNDECLARED"));
});


test("declared coordinate frame inconsistent with geometry CRS is a review gate even without known candidates",()=>{
 const x=planEcoAlignment({novel:{...base,frame:"EPSG:3857"},known_objects:[],
  authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(x.novel_checks.includes("FRAME_CRS_RECONCILIATION_REQUIRED"));
 assert.equal(x.novel_qualification_state,"REVIEW_REQUIRED");
});
test("matching known records do not conceal an internally inconsistent coordinate frame",()=>{
 const a={...base,frame:"EPSG:3857"},b={...known,source_refs:["src-a"],frame:"EPSG:3857"};
 const x=run(a,b).candidates[0];
 assert.ok(x.checks.includes("FRAME_CRS_RECONCILIATION_REQUIRED"));
 assert.equal(x.state,"REVIEW_DIFFERENCE");
});
test("Not run QA cannot qualify as measured observation",()=>{
 const x=planEcoAlignment({novel:{...base,qa_flag:"Not run"},known_objects:[],
  authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(x.novel_checks.includes("QA_STATE_REQUIRES_REVIEW"));
 assert.equal(x.novel_qualification_state,"REVIEW_REQUIRED");
});


// Source-backed negative cases: Type 1 Eco-Grex Second Cycle field schema, not field data.
test("different water-quality variables sharing mg/L cannot align",()=>{
 const a={...base,semantic_type:"sensor_reading",observed_variable:"dissolved_oxygen",native_interval:"PT1M"};
 const b={...known,...a,object_id:"known:1",source_refs:["src-a"],observed_variable:"nitrate"};
 const x=run(a,b).candidates[0];
 assert.equal(x.state,"REVIEW_DIFFERENCE");
 assert.ok(x.checks.includes("OBSERVED_VARIABLE_DIFFERENT_OR_UNDECLARED"));
});
test("missing sensor variable remains held with zero known candidates",()=>{
 const a={...base,semantic_type:"sensor_reading",native_interval:"PT1M"};
 const x=planEcoAlignment({novel:a,known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(x.novel_checks.includes("OBSERVED_VARIABLE_REQUIRED"));
 assert.equal(x.novel_qualification_state,"REVIEW_REQUIRED");
});
test("missing native sampling interval remains explicit",()=>{
 const a={...base,semantic_type:"sensor_reading",observed_variable:"dissolved_oxygen"};
 const x=planEcoAlignment({novel:a,known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(x.novel_checks.includes("NATIVE_INTERVAL_REQUIRED"));
});
test("different native intervals cannot silently collapse",()=>{
 const a={...base,semantic_type:"sensor_reading",observed_variable:"dissolved_oxygen",native_interval:"PT1M"};
 const b={...known,...a,object_id:"known:1",source_refs:["src-a"],native_interval:"PT5M"};
 assert.ok(run(a,b).candidates[0].checks.includes("NATIVE_INTERVAL_DIFFERENT_OR_UNDECLARED"));
});
test("different aggregation periods are separate even with equal numeric values",()=>{
 const a={...base,semantic_type:"sensor_reading",observed_variable:"dissolved_oxygen",native_interval:"PT1M",aggregation_scope:"average",aggregation_period:"PT1H"};
 const b={...known,...a,object_id:"known:1",source_refs:["src-a"],aggregation_period:"PT24H"};
 assert.ok(run(a,b).candidates[0].checks.includes("AGGREGATION_PERIOD_DIFFERENT_OR_UNDECLARED"));
});
test("aggregated reading with undeclared period requires review",()=>{
 const a={...base,semantic_type:"sensor_reading",observed_variable:"dissolved_oxygen",native_interval:"PT1M",aggregation_scope:"average"};
 const x=planEcoAlignment({novel:a,known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(x.novel_checks.includes("AGGREGATION_PERIOD_REQUIRED"));
});
test("matching declared variable and temporal support remains source-only candidate",()=>{
 const a={...base,semantic_type:"sensor_reading",observed_variable:"dissolved_oxygen",native_interval:"PT1M",aggregation_scope:"average",aggregation_period:"PT1H"};
 const b={...known,...a,object_id:"known:1",source_refs:["src-a"]};
 const x=run(a,b).candidates[0];
 assert.equal(x.state,"TYPED_ALIGNMENT_CANDIDATE");
 assert.equal(x.auto_merge,false);
});


// Source-backed method/uncertainty distinctions: Type 1 Eco-Grex WQ schema and QA register.
// All numeric values below are synthetic fixtures, never observed field measurements.
test("raw and corrected DO readings with equal values cannot silently align",()=>{
 const a={...base,semantic_type:"sensor_reading",observed_variable:"dissolved_oxygen",native_interval:"PT1M",measurement_basis:"raw"};
 const b={...known,...a,object_id:"known:1",source_refs:["src-a"],measurement_basis:"corrected",correction_method_id:"salinity-correction:v1"};
 const x=run(a,b).candidates[0];
 assert.equal(x.state,"REVIEW_DIFFERENCE");
 assert.ok(x.checks.includes("MEASUREMENT_BASIS_DIFFERENT_OR_UNDECLARED"));
});
test("corrected sensor data without correction method remains held even with zero candidates",()=>{
 const a={...base,semantic_type:"sensor_reading",observed_variable:"dissolved_oxygen",native_interval:"PT1M",measurement_basis:"corrected"};
 const x=planEcoAlignment({novel:a,known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(x.novel_checks.includes("CORRECTION_METHOD_REQUIRED"));
 assert.equal(x.novel_qualification_state,"REVIEW_REQUIRED");
});
test("different correction method revisions require review",()=>{
 const a={...base,measurement_basis:"corrected",correction_method_id:"salinity-correction:v2"};
 const b={...known,...a,object_id:"known:1",source_refs:["src-a"],correction_method_id:"salinity-correction:v1"};
 assert.ok(run(a,b).candidates[0].checks.includes("CORRECTION_METHOD_DIFFERENT_OR_UNDECLARED"));
});
test("uncertainty units must agree with measured quantity units",()=>{
 const a={...base,measurement_uncertainty:{value:0.2,unit:"ug/L"},uncertainty_basis:"standard_1sigma"};
 const x=planEcoAlignment({novel:a,known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(x.novel_checks.includes("UNCERTAINTY_UNIT_CONFLICT"));
});
test("same measurement with different stated uncertainty requires review",()=>{
 const a={...base,measurement_uncertainty:{value:0.2,unit:"mg/L"},uncertainty_basis:"standard_1sigma"};
 const b={...known,...a,object_id:"known:1",source_refs:["src-a"],measurement_uncertainty:{value:0.4,unit:"mg/L"}};
 assert.ok(run(a,b).candidates[0].checks.includes("MEASUREMENT_UNCERTAINTY_DIFFERENT_OR_UNDECLARED"));
});
test("negative uncertainty is invalid input",()=>{
 assert.throws(()=>run({...base,measurement_uncertainty:{value:-0.1,unit:"mg/L"}}),/INVALID_MEASUREMENT_UNCERTAINTY/);
});
test("uncertainty without basis cannot qualify",()=>{
 const a={...base,measurement_uncertainty:{value:0.2,unit:"mg/L"}};
 const x=planEcoAlignment({novel:a,known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(x.novel_checks.includes("UNCERTAINTY_BASIS_REQUIRED"));
});
test("fully declared corrected sensor fixture remains source-only, not native or empirically validated",()=>{
 const a={...base,semantic_type:"sensor_reading",observed_variable:"dissolved_oxygen",native_interval:"PT1M",
  measurement_basis:"corrected",correction_method_id:"synthetic:salinity-correction",
  measurement_uncertainty:{value:0.2,unit:"mg/L"},uncertainty_basis:"standard_1sigma"};
 const b={...known,...a,object_id:"known:1",source_refs:["src-a"]};
 const x=run(a,b);
 assert.equal(x.candidates[0].state,"TYPED_ALIGNMENT_CANDIDATE");
 assert.equal(x.ecological_effect_verified,false);
 assert.equal(x.accepted_native_identity,false);
 assert.equal(x.db_readback,false);
});

const bound={kind:"LOD",value:0.02,unit:"mg/L",method_ref:"synthetic:lab-v1"};
const noKnown=a=>planEcoAlignment({novel:a,known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
test("censored zero is not an observed point",()=>{
 const x=noKnown({...base,result_qualifier:"below_detection_limit",reporting_bound:bound,measurement:{value:0,unit:"mg/L"}});
 assert.ok(x.novel_checks.includes("CENSORED_RESULT_NUMERIC_POINT_CONFLICT"));assert.equal(x.novel_qualification_state,"REVIEW_REQUIRED");
});
test("missing censor bound is held",()=>assert.ok(noKnown({...base,result_qualifier:"below_quantification_limit"}).novel_checks.includes("CENSORED_REPORTING_BOUND_REQUIRED")));
test("LOD cannot replace LOQ",()=>{
 const a={...base,result_qualifier:"below_quantification_limit",reporting_bound:bound};
 assert.ok(run(a,{...known,...a,object_id:"known:1",source_refs:["src-a"]}).candidates[0].checks.includes("CENSOR_BOUND_KIND_MISMATCH"));
});
test("censor bound unit conflict is held",()=>assert.ok(noKnown({...base,result_qualifier:"below_detection_limit",reporting_bound:{...bound,unit:"ug/L"}}).novel_checks.includes("REPORTING_BOUND_UNIT_CONFLICT")));
test("different reporting limits remain distinct",()=>{
 const a={...base,result_qualifier:"quantified",reporting_bound:bound};
 const b={...known,...a,object_id:"known:1",source_refs:["src-a"],reporting_bound:{...bound,value:0.05}};
 assert.ok(run(a,b).candidates[0].checks.includes("REPORTING_BOUND_DIFFERENT_OR_UNDECLARED"));
});
test("bound-only censored reading never implies admission",()=>{
 const x=noKnown({...base,measurement:undefined,result_qualifier:"below_detection_limit",reporting_bound:bound});
 assert.ok(x.novel_checks.includes("CENSORED_RESULT_REQUIRES_REVIEW"));assert.equal(x.accepted_native_identity,false);
});
test("negative detection limit rejected",()=>assert.throws(()=>run({...base,reporting_bound:{...bound,value:-1}}),/INVALID_REPORTING_BOUND/));
test("missing reporting method is held",()=>assert.ok(noKnown({...base,result_qualifier:"below_detection_limit",reporting_bound:{kind:"LOD",value:0.02,unit:"mg/L"}}).novel_checks.includes("REPORTING_BOUND_METHOD_REQUIRED")));

// Synthetic QA provenance checks: no claim of an actually calibrated probe.
test("validated sensor QA without instrument and calibration evidence remains held",()=>{
 const a={...base,semantic_type:"sensor_reading",observed_variable:"dissolved_oxygen",native_interval:"PT1M",qa_flag:"validated"};
 const x=planEcoAlignment({novel:a,known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(x.novel_checks.includes("QA_VALIDATION_INSTRUMENT_REQUIRED"));
 assert.ok(x.novel_checks.includes("QA_VALIDATION_CALIBRATION_REF_REQUIRED"));
 assert.equal(x.novel_qualification_state,"REVIEW_REQUIRED");
});
test("traceable sensor QA references avoid missing-proof flags but never verify calibration",()=>{
 const a={...base,semantic_type:"sensor_reading",observed_variable:"dissolved_oxygen",native_interval:"PT1M",qa_flag:"validated",station_instrument_id:"synthetic:probe-1",calibration_verification_ref:"synthetic:check-1"};
 const x=planEcoAlignment({novel:a,known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(!x.novel_checks.includes("QA_VALIDATION_INSTRUMENT_REQUIRED"));
 assert.ok(!x.novel_checks.includes("QA_VALIDATION_CALIBRATION_REF_REQUIRED"));
 assert.equal(x.accepted_native_identity,false);assert.equal(x.db_readback,false);
});

// Synthetic BioBlocks biological-transfer fixtures; no release or clearance.
const transfer={proposed:true,carrier_class:"inoculum"};
test("proposed inoculum transfer without provenance remains held with zero candidates",()=>{
 const x=planEcoAlignment({novel:{...base,semantic_type:"intervention",biological_transfer:transfer},known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 for(const flag of ["BIOLOGICAL_TRANSFER_REVIEW_REQUIRED","BIOLOGICAL_TRANSFER_ORIGIN_REQUIRED","BIOLOGICAL_TRANSFER_DESTINATION_REQUIRED","BIOLOGICAL_TRANSFER_PROVENANCE_REQUIRED","BIOLOGICAL_TRANSFER_MOVEMENT_RULE_REQUIRED","BIOLOGICAL_TRANSFER_REVIEW_RECEIPT_REQUIRED"])assert.ok(x.novel_checks.includes(flag));
 assert.equal(x.accepted_native_identity,false);
});
test("source-declared biosecurity references are not evidence of actual clearance",()=>{
 const x=planEcoAlignment({novel:{...base,semantic_type:"intervention",biological_transfer:{...transfer,origin_ref:"synthetic:origin",destination_ref:"synthetic:destination",provenance_ref:"synthetic:provenance",movement_rule_ref:"synthetic:rule",biosecurity_review_ref:"synthetic:review"}},known_objects:[],authorised_object_ids:[],authorised_source_ids:["src-a"]});
 assert.ok(x.novel_checks.includes("BIOLOGICAL_TRANSFER_REVIEW_REQUIRED"));assert.equal(x.novel_qualification_state,"REVIEW_REQUIRED");assert.equal(x.ecological_effect_verified,false);
});
test("different biological carrier or origin cannot silently align",()=>{
 const a={...base,semantic_type:"intervention",biological_transfer:{...transfer,origin_ref:"synthetic:site-a"}};
 const b={...known,...a,object_id:"known:1",source_refs:["src-a"],biological_transfer:{...transfer,carrier_class:"seed",origin_ref:"synthetic:site-b"}};
 const x=run(a,b).candidates[0];assert.equal(x.state,"REVIEW_DIFFERENCE");assert.ok(x.checks.includes("BIOLOGICAL_TRANSFER_SCOPE_OR_PROVENANCE_DIFFERENT"));
});
test("invalid biological transfer declaration is rejected",()=>assert.throws(()=>run({...base,biological_transfer:{proposed:true,carrier_class:"none"}}),/INVALID_BIOLOGICAL_TRANSFER/));


const seedScope={proposed:true,carrier_class:"seed"};
const fungusScope={proposed:true,carrier_class:"inoculum"};
test("proposed seed movement without lot is held",()=>{
 const x=noKnown({...base,semantic_type:"intervention",biological_transfer:seedScope});
 assert.ok(x.novel_checks.includes("SEED_LOT_DESCRIPTOR_REQUIRED"));assert.equal(x.accepted_native_identity,false);
});
test("seed lot requires provenance sampling and custody",()=>{
 const x=noKnown({...base,semantic_type:"intervention",biological_transfer:seedScope,seed_lot:{lot_id:"synthetic:lot-1",taxon_id:"taxon:1"}});
 for(const flag of ["SEED_PARENT_PROVENANCE_REQUIRED","SEED_COLLECTION_SITE_REQUIRED","SEED_QUALITY_PROTOCOL_REQUIRED","SEED_SAMPLING_RATIONALE_REQUIRED","SEED_CUSTODY_REQUIRED"])assert.ok(x.novel_checks.includes(flag));
});
test("different seed lot identity remains distinct",()=>{
 const a={...base,semantic_type:"intervention",biological_transfer:seedScope,seed_lot:{lot_id:"synthetic:lot-a",taxon_id:"taxon:1"}};
 const b={...known,...a,object_id:"known:1",source_refs:["src-a"],seed_lot:{...a.seed_lot,lot_id:"synthetic:lot-b"}};
 assert.ok(run(a,b).candidates[0].checks.includes("SEED_LOT_IDENTITY_OR_QA_DIFFERENT"));
});
test("fungal movement without TST-004 disposition is held",()=>{
 assert.ok(noKnown({...base,semantic_type:"intervention",biological_transfer:fungusScope}).novel_checks.includes("FUNGAL_DISPOSITION_REQUIRED"));
});
test("proposed fungal movement contradicts do-not-inoculate disposition",()=>{
 assert.ok(noKnown({...base,semantic_type:"intervention",biological_transfer:fungusScope,fungal_inoculation:{disposition:"DO_NOT_INOCULATE"}}).novel_checks.includes("FUNGAL_PROPOSED_TRANSFER_CONTRADICTS_EXCLUSION"));
});
test("INOCULATE without TST-004 FM-039 and specialist evidence remains held",()=>{
 const x=noKnown({...base,semantic_type:"intervention",biological_transfer:fungusScope,fungal_inoculation:{disposition:"INOCULATE"}});
 for(const flag of ["FUNGAL_TST004_REQUIRED","FUNGAL_FM039_REQUIRED","FUNGAL_PATHOGEN_SCREEN_REQUIRED","FUNGAL_HOST_EVIDENCE_REQUIRED","FUNGAL_STRAIN_PROVENANCE_REQUIRED"])assert.ok(x.novel_checks.includes(flag));
 assert.ok(x.novel_checks.includes("BIOLOGICAL_TRANSFER_REVIEW_REQUIRED"));assert.equal(x.ecological_effect_verified,false);
});

// Synthetic biodiversity survey cases. No observed population absence or field survey is asserted.
test("no-match non-detection requires survey method effort and window",()=>{
 const x=noKnown({...base,measurement:undefined,survey:{detection_status:"not_detected"}});
 for(const f of ["SURVEY_PROTOCOL_REQUIRED","SURVEY_EFFORT_REQUIRED","SURVEY_WINDOW_REQUIRED","NONDETECTION_NOT_ABSENCE","DETECTABILITY_UNVERIFIED"])assert.ok(x.novel_checks.includes(f));
 assert.equal(x.candidate_count,0);assert.equal(x.novel_qualification_state,"REVIEW_REQUIRED");
});
test("complete non-detection survey is still not biological absence",()=>{
 const s={detection_status:"not_detected",protocol_ref:"synthetic:visual-transect",effort_value:20,effort_unit:"min",survey_window:"synthetic:2026-Q1",detectability_ref:"synthetic:review"};
 const x=noKnown({...base,measurement:undefined,survey:s});
 assert.ok(x.novel_checks.includes("NONDETECTION_NOT_ABSENCE"));
 assert.ok(!x.novel_checks.includes("SURVEY_EFFORT_REQUIRED"));
 assert.equal(x.ecological_effect_verified,false);assert.equal(x.accepted_native_identity,false);
});
test("not surveyed cannot be recorded as an observed ecological survey",()=>{
 const x=noKnown({...base,measurement:undefined,survey:{detection_status:"not_surveyed"}});
 assert.ok(x.novel_checks.includes("SURVEY_NOT_CONDUCTED"));
 assert.ok(x.novel_checks.includes("OBSERVED_EVIDENCE_WITH_NO_SURVEY"));
});
test("distinct survey effort and detection method do not silently align",()=>{
 const s={detection_status:"detected",protocol_ref:"synthetic:photo-quadrat",effort_value:5,effort_unit:"quadrats",survey_window:"synthetic:2026-Q1"};
 const a={...base,survey:s};
 const b={...known,...a,object_id:"known:1",source_refs:["src-a"],survey:{...s,effort_value:20}};
 assert.ok(run(a,b).candidates[0].checks.includes("SURVEY_EFFORT_METHOD_OR_DETECTION_DIFFERENT"));
});
test("negative survey effort is invalid",()=>assert.throws(()=>run({...base,survey:{detection_status:"detected",effort_value:-2}}),/INVALID_SURVEY_EFFORT/));
test("fully declared detection still does not establish ecology efficacy or DBR",()=>{
 const s={detection_status:"detected",protocol_ref:"synthetic:photo-quadrat",effort_value:5,effort_unit:"quadrats",survey_window:"synthetic:2026-Q1"};
 const x=noKnown({...base,survey:s});
 assert.ok(!x.novel_checks.includes("SURVEY_EFFORT_REQUIRED"));
 assert.equal(x.accepted_native_identity,false);assert.equal(x.db_readback,false);assert.equal(x.ecological_effect_verified,false);
});
