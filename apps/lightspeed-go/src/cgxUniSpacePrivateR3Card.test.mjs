/** Synthetic source-bound tests only; never exercise host, Vite dist, DBR or network. */
import {test} from "node:test";
import assert from "node:assert/strict";
import {planPrivateR3Card} from "./cgxUniSpacePrivateR3Card.mjs";

const fixture=()=>({
 selection:{parent_filespace:"Cognigrex.cgx",object_id:"WT-001",filespace:"Romer.cgx",identity_status:"SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED"},
 source:{object_id:"WT-001",filespace:"Romer.cgx",mapping_id:"FF-WATCHTOWER-FCSTD-001",
   r0_source_sha256:"c476f9f2f9946ab8e99e58dd399aa7b02bac630c5d9336b80ef66f5f2a397321",
   mapping_blob_sha:"15ac42e257220e0efd30c8521fe2c319b9a25013",
   evidence_class:"scientific",rights:"UNRESOLVED",mapping_stage:"R0_R1_R2_REFERENCE",
   geometry_state:"SOURCE_DERIVED_GEOMETRY",geometry_frame:null,geometry_units:null,
   private_source_locator:"NEVER_DISPLAY_OR_PUBLISH"},
 client:{mode:"review_only",revoked:false,allowed_object_ids:["WT-001"],allowed_filespaces:["Romer.cgx"]},
 request:{view:"3d",requested_hydration:"H2"}
});
test("one source-mapped candidate in correct child",()=>{
 const p=planPrivateR3Card(fixture());
 assert.equal(p.state,"R3_PRIVATE_VIEW_CANDIDATE");
 assert.equal(p.candidate_object_id,"WT-001");
 assert.equal(p.child_filespace,"Romer.cgx");
 assert.equal(p.source_mapping_id,"FF-WATCHTOWER-FCSTD-001");
 assert.equal(p.r0_hash_status,"REGISTERED_REFERENCE_NOT_BYTES_VERIFIED");
});
test("private source and locator never enter HTML or output",()=>{
 const p=planPrivateR3Card(fixture());
 assert.doesNotMatch(JSON.stringify(p),/NEVER_DISPLAY_OR_PUBLISH/);
 assert.doesNotMatch(p.html,/WT-001|c476f9f2|15ac42e2|<script>/);
 assert.equal(p.public_vite_asset,false);
 assert.equal(p.source_bytes_embedded,false);
});
test("3D Frontier without source frame and units",()=>{
 assert.ok(planPrivateR3Card(fixture()).frontier.includes("GEOMETRY_FRAME_UNITS_OR_AUTHORITY_FRONTIER"));
});
test("higher hydration never granted by source-only input",()=>{
 const p=planPrivateR3Card(fixture());
 assert.equal(p.display_hydration,"H0_REFERENCE_ONLY");
 assert.ok(p.frontier.includes("HYDRATION_ABOVE_H0_DENIED"));
});
test("revoked permission denied",()=>{
 const x=fixture();x.client.revoked=true;assert.equal(planPrivateR3Card(x).state,"HOLD");
});
test("cross-object swap denied",()=>{
 const x=fixture();x.source.object_id="WT-002";assert.equal(planPrivateR3Card(x).state,"HOLD");
});
test("cross-Grex swap denied",()=>{
 const x=fixture();x.selection.filespace="Eco.cgx";assert.equal(planPrivateR3Card(x).state,"HOLD");
});
test("malformed source hash denied",()=>{
 const x=fixture();x.source.r0_source_sha256="abc";assert.equal(planPrivateR3Card(x).state,"HOLD");
});
test("unqualified mapping denied",()=>{
 const x=fixture();x.source.mapping_id="unqualified";assert.equal(planPrivateR3Card(x).state,"HOLD");
});
test("root substitution denied",()=>{
 const x=fixture();x.selection.object_id="cgx:root:cognigrex";assert.equal(planPrivateR3Card(x).state,"HOLD");
});
test("H4 remains non-executable",()=>{
 const x=fixture();x.request.requested_hydration="H4";
 const p=planPrivateR3Card(x);
 assert.equal(p.executable,false);assert.equal(p.installable,false);
});
test("six views preserve object identity and permission boundary",()=>{
 for(const v of ["document","3d","chat","graph","interactive","matrix"]){
  const x=fixture();x.request.view=v;const p=planPrivateR3Card(x);
  assert.equal(p.selected_view,v);assert.equal(p.candidate_object_id,"WT-001");
  assert.equal(p.display_hydration,"H0_REFERENCE_ONLY");
 }
});
test("unsupported view rejected",()=>{
 const x=fixture();x.request.view="<script>";assert.equal(planPrivateR3Card(x).state,"HOLD");
});
test("source-only proof never asserts admission or host/release",()=>{
 const p=planPrivateR3Card(fixture());
 for(const k of ["native_admitted","host_verified","dist_verified","release_accepted","canonical_mutation","network_fetch","executable","installable"])assert.equal(p[k],false,k);
});
