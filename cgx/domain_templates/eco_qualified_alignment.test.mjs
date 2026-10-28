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
