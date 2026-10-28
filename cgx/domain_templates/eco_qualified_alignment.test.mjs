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
test("same type and source-qualified context yields review candidate, never native merge",()=>{
 const x=run();assert.equal(x.candidates[0].state,"TYPED_ALIGNMENT_CANDIDATE");
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
