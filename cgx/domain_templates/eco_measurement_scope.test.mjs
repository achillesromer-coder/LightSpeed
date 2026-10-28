import test from "node:test";
import assert from "node:assert/strict";
import {planEcoAlignment} from "./eco_qualified_alignment.mjs";

// Synthetic only: no environmental measurement, site claim or ecological outcome.
const base={semantic_type:"ecological_observation",source_refs:["fixture:novel"],
 evidence_class:"source_asserted",subject_kind:"taxon",subject_id:"fixture:taxon",
 taxon_id:"fixture:taxon",site_id:"fixture:site",
 observed_at:"2026-01-01T00:00:00Z",method_id:"fixture:method",
 measurement:{value:4,unit:"kg C"},unit:"kg C"};
const known={...base,object_id:"fixture:known",source_refs:["fixture:known-source"]};
const flags=(novel,existing=known)=>planEcoAlignment({novel,known_objects:[existing],
 authorised_object_ids:["fixture:known"],
 authorised_source_ids:["fixture:novel","fixture:known-source"]}).candidates[0].checks;
test("batch and block aggregation are distinct despite identical units and values",()=>{
 const a={...base,aggregation_scope:"per_batch",sample_count:699};
 const b={...known,aggregation_scope:"per_block",sample_count:1};
 const c=flags(a,b);
 assert.ok(c.includes("AGGREGATION_SCOPE_DIFFERENT_OR_UNDECLARED"));
 assert.ok(c.includes("SAMPLE_COUNT_DIFFERENT_OR_UNDECLARED"));
});
test("specified versus undeclared aggregation scope remains a review difference",()=>{
 assert.ok(flags({...base,aggregation_scope:"per_block"}).includes("AGGREGATION_SCOPE_DIFFERENT_OR_UNDECLARED"));
});
test("different baselines are not silently aligned",()=>{
 assert.ok(flags({...base,baseline_id:"fixture:baseline-a"},{...known,baseline_id:"fixture:baseline-b"})
  .includes("BASELINE_DIFFERENT_OR_UNDECLARED"));
});
test("matching declared scope, count and baseline does not add spurious differences",()=>{
 const a={...base,aggregation_scope:"per_block",sample_count:1,baseline_id:"fixture:baseline-a"};
 const b={...known,aggregation_scope:"per_block",sample_count:1,baseline_id:"fixture:baseline-a"};
 assert.deepEqual(flags(a,b),[]);
});
test("invalid sample count rejected",()=>{
 assert.throws(()=>flags({...base,sample_count:0}),/INVALID_SAMPLE_COUNT/);
});
test("scope qualification never verifies ecological outcomes or admits identities",()=>{
 const r=planEcoAlignment({novel:{...base,aggregation_scope:"per_batch",sample_count:699},
 known_objects:[{...known,aggregation_scope:"per_block",sample_count:1}],
 authorised_object_ids:["fixture:known"],authorised_source_ids:["fixture:novel","fixture:known-source"]});
 assert.equal(r.ecological_effect_verified,false);
 assert.equal(r.object_ids_minted,0);
 assert.equal(r.accepted_native_identity,false);
 assert.equal(r.db_readback,false);
});

test("sensor reading with no measurement is held even when both candidates omit it",()=>{
 const a={...base,semantic_type:"sensor_reading",measurement:undefined,unit:undefined};
 const b={...known,semantic_type:"sensor_reading",measurement:undefined,unit:undefined};
 assert.ok(flags(a,b).includes("SENSOR_MEASUREMENT_REQUIRED"));
});
test("declared top-level and measured units cannot contradict silently",()=>{
 const a={...base,measurement:{value:4,unit:"mg/L"},unit:"kg"};
 const b={...known,measurement:{value:4,unit:"mg/L"},unit:"kg"};
 assert.ok(flags(a,b).includes("MEASUREMENT_UNIT_CONFLICT"));
});
test("consistent measurement units avoid false conflict",()=>{
 const a={...base,measurement:{value:4,unit:"mg/L"},unit:"mg/L"};
 const b={...known,measurement:{value:4,unit:"mg/L"},unit:"mg/L"};
 assert.ok(!flags(a,b).includes("MEASUREMENT_UNIT_CONFLICT"));
});
