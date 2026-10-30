import test from "node:test";
import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {prepareEcoPreMintAssembly as prepare} from "./eco_pre_mint_assembly.mjs";

// Synthetic fixtures only. Original Drive workbook/PDF bytes are never stored in Git.
const source={provider:"drive",id:"synthetic-drive-id",
  revision:"synthetic-revision",source_ref:"synthetic:eco-source"};
const bytes=Buffer.from("private-workbook-fixture-not-an-original","utf8");
const digest=createHash("sha256").update(bytes).digest("hex");
const metadata={id:source.id,revision:source.revision,
  modified_time:"2026-05-19T23:33:23.000Z",size:bytes.byteLength,
  mime_type:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"};
const snapshot={metadata,original_bytes:bytes,expected_sha256:digest};
const scope={authorised_source_ids:[source.source_ref]};
const novel={semantic_type:"ecological_state_estimate",
  source_refs:[source.source_ref],evidence_class:"simulated"};
const record={claim_kind:"passive_flow",evidence_class:"simulated",
  source_ref:source.source_ref,source_revision:source.revision,
  source_sha256:digest,numeric_value:6,unit:"L/s"};
const input={source,source_snapshot:snapshot,scope,novel,
  domain:"second_cycle_claim",record};
const anchor={source_ref:source.source_ref,source_revision:source.revision,
  source_sha256:digest,sheet:"07_Flow_Mist_Model",cell:"B8"};
const geometry={source_ref:source.source_ref,kind:"Polygon",dimension:2,
  source_geometry_ref:"synthetic:geometry-file",crs_ref:"synthetic:crs",
  coordinate_unit:"synthetic:metre",time_frame_ref:"synthetic:time",
  spatial_review_ref:"synthetic:spatial-review",rights_review_ref:"synthetic:rights",
  stewardship_review_ref:"synthetic:stewardship"};

test("one executable chain hashes bytes, reviews Eco claim and prepares held mint layers",()=>{
 const result=prepare({cascade_input:input,cell_anchor:anchor,
   geometry_descriptor:geometry});
 assert.equal(result.stage,"R1_PRE_MINT_REVIEW_PACKET");
 assert.equal(result.hydration.H2.source_sha256,digest);
 assert.equal(result.hydration.H2.bytes_read_and_hashed_this_execution,true);
 assert.equal(result.hydration.H3.eco_alignment_executed,true);
 assert.equal(result.hydration.H3.installed_operator,false);
 assert.equal(result.hydration.H1.source_cell.formula_verified,false);
 assert.equal(result.geomatrix.state,"REFERENCES_STAGED_NOT_ACCEPTED");
 assert.equal(result.geomatrix.actual_geometry_loaded,false);
 assert.equal(result.release.mint_allowed,false);
 assert.equal(result.release.db_readback,false);
 assert.equal(result.candidate_object_id,null);
 assert.equal(result.canonical_write,false);
 assert.equal(result.permissions.public_publish,false);
 assert.ok(result.executed_review.ecological_review.flags.includes(
   "HYDRODYNAMIC_BENCH_CALIBRATION_REQUIRED"));
 assert.equal(JSON.stringify(result).includes("private-workbook-fixture"),false);
});
test("H0 minimises exposed hydration without pretending metadata is full source",()=>{
 const r=prepare({cascade_input:input,requested_hydration:"H0"});
 assert.equal(r.hydration.H1.state,"NOT_REQUESTED");
 assert.equal(r.hydration.H2.state,"NOT_REQUESTED");
 assert.equal(r.hydration.H3.state,"NOT_REQUESTED");
 assert.equal(r.hydration.H4.state,"DENIED_PENDING_NATIVE_ACL_AND_ROOT_ADMISSION");
 assert.equal(r.source_bytes_embedded,false);
});
test("H4 request still cannot expose source, install a tool or mint",()=>{
 const r=prepare({cascade_input:input,requested_hydration:"H4"});
 assert.equal(r.hydration.H4.source_bytes_emitted,false);
 assert.equal(r.hydration.H4.host_tool_invoked,false);
 assert.equal(r.release.installed,false);
 assert.equal(r.release.mint_allowed,false);
});
test("missing source snapshot produces explicit R0 and cell proof holds",()=>{
 const r=prepare({cascade_input:{...input,source_snapshot:undefined}});
 assert.equal(r.hydration.H2.state,"SOURCE_HASH_UNVERIFIED");
 assert.ok(r.blocking_gates.includes("ORIGINAL_BYTES_NOT_HASHED_IN_THIS_EXECUTION"));
 assert.equal(r.hydration.H1.source_cell.source_cell_bytes_reread,false);
});
test("a declared cell anchor is not a workbook cell-content receipt",()=>{
 const r=prepare({cascade_input:input,cell_anchor:anchor});
 assert.equal(r.hydration.H1.source_cell.declared_anchor_matched,true);
 assert.equal(r.hydration.H1.source_cell.formula_verified,false);
 assert.ok(r.loss_ledger.includes("NO_SOURCE_CELL_CONTENT_OR_FORMULA_READBACK"));
});
test("stale source-cell revision or altered digest cannot be attached",()=>{
 assert.throws(()=>prepare({cascade_input:input,
  cell_anchor:{...anchor,source_revision:"stale"}}),/INVALID_ECO_CELL_ANCHOR/);
 assert.throws(()=>prepare({cascade_input:input,
  cell_anchor:{...anchor,source_sha256:"0".repeat(64)}}),
  /ECO_CELL_ANCHOR_UNVERIFIED_SOURCE_DIGEST/);
});
test("cell anchor requires explicit spreadsheet A1 address",()=>{
 assert.throws(()=>prepare({cascade_input:input,
  cell_anchor:{...anchor,cell:"B8:C10"}}),/INVALID_ECO_CELL_ANCHOR/);
 assert.throws(()=>prepare({cascade_input:input,
  cell_anchor:{...anchor,sheet:"X\nprivate"}}),/INVALID_ECO_CELL_ANCHOR/);
});
test("raw spatial coordinates and unknown object payload are rejected",()=>{
 for(const bad of [
  {...geometry,coordinates:[153.1,-27.5]},
  {...geometry,metadata:{lat:-27.5}},
  {...geometry,geometry:{type:"Point"}},
  {...geometry,crs_ref:"x",unknown:"value"}
 ])assert.throws(()=>prepare({cascade_input:input,
  geometry_descriptor:bad}),/INVALID_ECO_GEOMATRIX_DESCRIPTOR/);
});
test("geometry source must match the bound workbook",()=>{
 assert.throws(()=>prepare({cascade_input:input,
  geometry_descriptor:{...geometry,source_ref:"different-source"}}),
  /INVALID_ECO_GEOMATRIX_DESCRIPTOR/);
});
test("3D geomatrix without vertical datum stays unresolved and never renders geometry",()=>{
 const r=prepare({cascade_input:input,geometry_descriptor:{
  ...geometry,dimension:3,kind:"mesh"}});
 assert.ok(r.geomatrix.flags.includes("VERTICAL_DATUM_REQUIRED_FOR_3D"));
 assert.equal(r.geomatrix.metric_geometry_validated,false);
 assert.equal(r.release.public_release_authorised,false);
});
test("geometry with complete-looking references still needs independent assurance",()=>{
 const r=prepare({cascade_input:input,geometry_descriptor:{
  ...geometry,dimension:3,kind:"mesh",
  vertical_datum_ref:"synthetic:vertical"}});
 assert.equal(r.geomatrix.state,"REFERENCES_STAGED_NOT_ACCEPTED");
 assert.equal(r.geomatrix.spatial_release_authorised,false);
 assert.equal(r.stack_layers.find(x=>x.layer==="native").state,"NOT_ADMITTED");
});
test("original-byte tamper blocks entire pre-Mint chain",()=>{
 assert.throws(()=>prepare({cascade_input:{...input,
  source_snapshot:{...snapshot,original_bytes:Buffer.alloc(bytes.length)}}}),
  /ECO_SOURCE_ORIGINAL_BYTES_HASH_MISMATCH/);
});
test("source scope denial blocks entire chain before any handoff",()=>{
 assert.throws(()=>prepare({cascade_input:{...input,
  scope:{authorised_source_ids:[]}}}),/UNAUTHORISED_OR_INVALID/);
});
test("evidence class mismatch blocks chain rather than papering over it",()=>{
 assert.throws(()=>prepare({cascade_input:{...input,
  record:{...record,evidence_class:"observed"}}}),
  /ECO_DOMAIN_EVIDENCE_OR_SOURCE_CONFLICT/);
});
test("BioBlocks follows the same verified source-hydration path without field promotion",()=>{
 const bioNovel={...novel,semantic_type:"ecological_observation"};
 const bioRecord={evidence_class:"simulated",source_ref:source.source_ref,
  source_revision:source.revision,source_sha256:digest,
  seed_count:100,germinated_count:45,surviving_count:20};
 const r=prepare({cascade_input:{...input,novel:bioNovel,
  domain:"bioblock_monitoring",record:bioRecord},cell_anchor:anchor});
 assert.match(r.hydration.H3.executed_review_module,/eco_bioblock_monitoring_review.mjs$/);
 assert.equal(r.evidence_class,"simulated");
 assert.ok(r.executed_review.ecological_review.flags.includes(
  "NONOBSERVED_COUNTS_CANNOT_ESTABLISH_FIELD_SURVIVAL"));
 assert.equal(r.factual_outcome_verified,false);
});
test("non-Eco and unrecognized domains cannot inherit an Eco mint path",()=>{
 assert.throws(()=>prepare({cascade_input:{...input,domain:"romer_claim"}}),
  /ECO_DOMAIN_EVIDENCE_OR_SOURCE_CONFLICT/);
 assert.throws(()=>prepare({cascade_input:input,requested_hydration:"H5"}),
  /INVALID_ECO_PRE_MINT_REQUEST/);
});
