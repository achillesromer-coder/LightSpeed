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

const observation={kind:"EcoObservation",synthetic:true,measured:false,
  evidence_class:"simulated",taxon:"synthetic:taxon",place:"synthetic:site",
  method:"synthetic:method",source_provenance:source.source_ref,
  source_revision_ref:source.revision,source_hash_sha256:digest,
  source_owner_ref:"synthetic:owner"};
test("EcoObservation showcase is reviewed by the existing boundary, not minted",()=>{
 const r=prepare({cascade_input:input,observation_showcase:observation});
 assert.equal(r.mint_showcase_review.state,"SCHEMA_BRIDGE_CANDIDATE_ONLY");
 assert.equal(r.mint_showcase_review.field_observation_verified,false);
 assert.equal(r.mint_showcase_review.native_object_id,null);
 assert.equal(r.mint_showcase_review.public_release_authorised,false);
 assert.ok(r.blocking_gates.includes(
  "ECO_OBSERVATION_SHOWCASE_NOT_NATIVE_MINT_OR_FIELD_EVIDENCE"));
 assert.equal(r.release.mint_allowed,false);
});
test("showcase source revision, digest and evidence must bind to executed cascade",()=>{
 for(const changed of [
  {...observation,source_provenance:"synthetic:other-source"},
  {...observation,source_revision_ref:"stale-revision"},
  {...observation,source_hash_sha256:"0".repeat(64)},
  {...observation,evidence_class:"observed"},
  {...observation,source_hash_sha256:undefined}
 ])assert.throws(()=>prepare({cascade_input:input,
  observation_showcase:changed}),/ECO_MINT_SHOWCASE_SOURCE_OR_EVIDENCE_CONFLICT/);
});
test("raw spatial content cannot cross from observation showcase to pre-Mint",()=>{
 for(const changed of [
  {...observation,latitude:-27.5,longitude:153.1},
  {...observation,metadata:{siteGeometry:{coordinates:[153.1,-27.5]}}},
  {...observation,place:"synthetic site -27.5000,153.1000"}
 ])assert.throws(()=>prepare({cascade_input:input,
  observation_showcase:changed}),/ECO_MINT_SHOWCASE_SPATIAL_PAYLOAD_HOLD/);
});
test("H0 cannot hydrate the optional mint showcase review",()=>{
 const r=prepare({cascade_input:input,observation_showcase:observation,
  requested_hydration:"H0"});
 assert.equal(r.mint_showcase_review.state,"NOT_REQUESTED_OR_NOT_SUPPLIED");
 assert.equal(r.hydration.H3.state,"NOT_REQUESTED");
});
test("unexpected top-level fields are rejected instead of silently ignored",()=>{
 assert.throws(()=>prepare({cascade_input:input,
  geometry:{coordinates:[153.1,-27.5]}}),/INVALID_ECO_PRE_MINT_REQUEST/);
});


// Type-I source manifest cases are synthetic: they exercise the verified
// relationship boundary without embedding owner-only Drive IDs or workbooks.
const lineage={
 source_ref:source.source_ref,
 related_source_ref:"synthetic:translated-type1-sheet",
 relation_kind:"embedded_translation",
 manifest_location_ref:"01_Source_Manifest!A2:B2",
 manifest_source_sha256:digest,
 related_revision_ref:"synthetic-related-provider-revision",
 claimed_translation_state:"translated_verified"
};
test("source lineage manifest hash may match original bytes without proving related-sheet equivalence",()=>{
 const r=prepare({cascade_input:input,source_lineage:lineage});
 assert.equal(r.source_lineage_review.state,"R1_SOURCE_LINEAGE_CANDIDATE_NOT_EQUIVALENCE");
 assert.equal(r.source_lineage_review.manifest_source_hash_matches_original_bytes_this_execution,true);
 assert.equal(r.source_lineage_review.related_source_hash_verified_this_execution,false);
 assert.equal(r.source_lineage_review.byte_equivalence_verified,false);
 assert.equal(r.source_lineage_review.related_provider_revision_authenticated_by_module,false);
 assert.equal(r.source_lineage_review.related_source_rights_verified,false);
 assert.equal(r.source_lineage_review.claimed_translation_state,"translated_verified");
 assert.equal(r.release.mint_allowed,false);
 assert.ok(r.blocking_gates.includes("RELATED_SOURCE_LINEAGE_NOT_INDEPENDENTLY_VERIFIED"));
});
test("unhashed original never borrows proof from an embedded manifest",()=>{
 const r=prepare({cascade_input:{...input,source_snapshot:undefined},source_lineage:lineage});
 assert.equal(r.source_lineage_review.manifest_source_hash_matches_original_bytes_this_execution,false);
 assert.equal(r.source_lineage_review.related_source_bytes_read_this_execution,false);
 assert.equal(r.source_lineage_review.byte_equivalence_verified,false);
 assert.equal(r.candidate_object_id,null);
});
test("stale or fabricated manifest source hash is rejected against actual original bytes",()=>{
 assert.throws(()=>prepare({cascade_input:input,
  source_lineage:{...lineage,manifest_source_sha256:"f".repeat(64)}}),
  /ECO_LINEAGE_MANIFEST_SOURCE_HASH_MISMATCH/);
});
test("related source must have a distinct identity; alias labels cannot collapse R0s",()=>{
 assert.throws(()=>prepare({cascade_input:input,
  source_lineage:{...lineage,related_source_ref:source.source_ref}}),
  /INVALID_ECO_SOURCE_LINEAGE/);
});
test("lineage descriptor cannot smuggle embedded workbook bytes, geometry or permissions",()=>{
 for(const bad of [
  {...lineage,source_bytes:Buffer.from("private")},
  {...lineage,coordinates:[153.1,-27.5]},
  {...lineage,owner_approved:true},
  {...lineage,relation_kind:"native_minted"}
 ])assert.throws(()=>prepare({cascade_input:input,source_lineage:bad}),
  /INVALID_ECO_SOURCE_LINEAGE/);
});
test("H0 suppresses source lineage identifiers and cannot be used as a public release",()=>{
 const r=prepare({cascade_input:input,source_lineage:lineage,requested_hydration:"H0"});
 assert.deepEqual(r.source_lineage_review,{state:"NOT_REQUESTED"});
 assert.equal(r.release.public_release_authorised,false);
 assert.equal(r.hydration.H4.source_bytes_emitted,false);
});
test("no related source requested retains original review route without lineage claims",()=>{
 const r=prepare({cascade_input:input});
 assert.deepEqual(r.source_lineage_review,{state:"NO_RELATED_SOURCE_REQUESTED"});
 assert.equal(r.stack_layers.find(x=>x.layer==="lineage").state,"NO_RELATED_SOURCE_REQUESTED");
});


// Access posture tests use synthetic provider ACLs, not real owner identities.
// Metadata visibility is not licence or consent for downstream source reuse.
const acl={source_ref:source.source_ref,source_id:source.id,
 provider_observation_ref:"synthetic:provider-acl-readback",
 permissions:[{type:"anyone",role:"reader",allowFileDiscovery:false},
  {type:"user",role:"owner",allowFileDiscovery:null}]};
test("anyone-reader link is not private even when undiscoverable",()=>{
 const r=prepare({cascade_input:input,access_posture:acl});
 assert.equal(r.access_posture_review.anyone_link_present,true);
 assert.equal(r.access_posture_review.provider_authenticated_by_module,false);
 assert.equal(r.access_posture_review.rights_approved,false);
 assert.equal(r.release.public_release_authorised,false);
 assert.ok(r.access_posture_review.flags.includes(
  "NON_DISCOVERABLE_LINK_STILL_ACCESSIBLE_TO_LINK_HOLDERS"));
 assert.ok(r.blocking_gates.includes("DECLARED_SOURCE_ACCESS_POSTURE_NOT_RIGHTS_APPROVAL"));
 assert.equal(JSON.stringify(r).includes("synthetic:provider-acl-readback"),false);
});
test("no anyone entry does not prove restricted source rights",()=>{
 const r=prepare({cascade_input:input,access_posture:{...acl,
  permissions:[{type:"user",role:"owner"}]}});
 assert.equal(r.access_posture_review.anyone_link_present,false);
 assert.ok(r.access_posture_review.flags.includes(
  "NO_ANYONE_ENTRY_DOES_NOT_PROVE_PRIVATE"));
 assert.equal(r.access_posture_review.source_reuse_rights_verified,false);
});
test("anyone writer is a stronger ACL risk and never an approval",()=>{
 const r=prepare({cascade_input:input,access_posture:{...acl,
  permissions:[{type:"anyone",role:"writer",allowFileDiscovery:true}]}});
 assert.ok(r.access_posture_review.flags.includes(
  "ANYONE_WRITE_OR_ADMIN_PERMISSION_REVIEW_REQUIRED"));
 assert.equal(r.release.mint_allowed,false);
});
test("domain and group scopes are not equivalent to private ACL",()=>{
 const r=prepare({cascade_input:input,access_posture:{...acl,
  permissions:[{type:"group",role:"reader"},{type:"domain",role:"reader"}]}});
 assert.equal(r.access_posture_review.broad_group_or_domain_present,true);
 assert.ok(r.access_posture_review.flags.includes(
  "GROUP_OR_DOMAIN_SCOPE_REVIEW_REQUIRED"));
});
test("ACL snapshot rejects unscoped IDs and sensitive identity fields",()=>{
 for(const bad of [
  {...acl,source_id:"other-source"},
  {...acl,source_ref:"other-ref"},
  {...acl,permissions:[{type:"user",role:"owner",emailAddress:"private@example.invalid"}]},
  {...acl,permissions:[{type:"domain",role:"reader",domain:"private.example"}]},
  {...acl,permissions:[{type:"anyone",role:"reader",allowFileDiscovery:"false"}]},
  {...acl,permissions:[{type:"public",role:"reader"}]},
  {...acl,provider_authenticated:true}
 ])assert.throws(()=>prepare({cascade_input:input,access_posture:bad}),
  /INVALID_ECO_ACCESS_POSTURE/);
});
test("H0 source-only viewport omits permission classification",()=>{
 const r=prepare({cascade_input:input,access_posture:acl,requested_hydration:"H0"});
 assert.deepEqual(r.access_posture_review,{state:"NOT_REQUESTED"});
 assert.equal(r.hydration.H2.state,"NOT_REQUESTED");
 assert.equal(r.release.public_release_authorised,false);
});
test("missing ACL snapshot is explicitly unverified and never a grant",()=>{
 const r=prepare({cascade_input:input});
 assert.equal(r.access_posture_review.state,"ACCESS_POSTURE_NOT_SUPPLIED");
 assert.ok(r.access_posture_review.flags.includes("CURRENT_PROVIDER_ACL_READBACK_REQUIRED"));
 assert.equal(r.access_posture_review.rights_approved,false);
});


// Pairwise source/embedded-sheet crosswalk: entirely synthetic fixtures.
// A formula/value match is not provider attestation or whole-workbook parity.
const cellPair={
 source_ref:source.source_ref,source_revision:source.revision,
 source_sha256:digest,related_source_ref:lineage.related_source_ref,
 related_revision_ref:lineage.related_revision_ref,
 original_cell:{sheet:anchor.sheet,cell:anchor.cell,
  formula:"=B3*B4*B5*1000",unit:"L/s",numeric_value:9.6,
  evidence_class:"simulated"},
 related_cell:{sheet:"SYNTHETIC_EMBEDDED_07_Flow_Mist_Model",cell:"B8",
  formula:"=B3*B4*B5*1000",unit:"L/s",numeric_value:9.6,
  evidence_class:"simulated"}
};
const withCellPair=(pair=cellPair)=>({cascade_input:input,
 cell_anchor:anchor,source_lineage:lineage,cell_crosswalk:pair});
test("paired original/translated synthetic cells compare without equivalence promotion",()=>{
 const r=prepare(withCellPair());
 const c=r.source_cell_crosswalk_review;
 assert.equal(c.state,"R1_CALLER_DECLARED_PAIRWISE_MATCH_NOT_EQUIVALENCE");
 assert.equal(c.formula_match,true);
 assert.equal(c.numeric_value_match,true);
 assert.equal(c.unit_match,true);
 assert.equal(c.provider_cells_fetched_by_module,false);
 assert.equal(c.independent_cell_readback_verified,false);
 assert.equal(c.original_and_translation_equivalent,false);
 assert.equal(r.release.mint_allowed,false);
 assert.equal(r.candidate_object_id,null);
 assert.ok(r.blocking_gates.includes(
  "CELL_CROSSWALK_PROVIDER_ATTESTATION_AND_FULL_EQUIVALENCE_REQUIRED"));
 assert.equal(JSON.stringify(r).includes("=B3*B4*B5*1000"),false);
 assert.equal(JSON.stringify(r).includes("numeric_value"),false);
});
test("formula, value and unit discrepancies remain explicit held variants",()=>{
 for(const changed of [
  {...cellPair.related_cell,formula:"=B3*B4*B5"},
  {...cellPair.related_cell,numeric_value:9.7},
  {...cellPair.related_cell,unit:"m3/s"}
 ]){
  const r=prepare(withCellPair({...cellPair,related_cell:changed}));
  assert.equal(r.source_cell_crosswalk_review.state,
   "R1_CALLER_DECLARED_CELL_DISCREPANCY_HOLD");
  assert.ok(r.blocking_gates.includes("SOURCE_TRANSLATION_CELL_DISCREPANCY"));
  assert.equal(r.release.mint_allowed,false);
 }
});
test("crosswalk cannot claim a stale revision or mismatched original digest",()=>{
 for(const bad of [
  {...cellPair,source_revision:"stale"},
  {...cellPair,source_sha256:"0".repeat(64)},
  {...cellPair,related_revision_ref:"stale-related"},
  {...cellPair,related_source_ref:"synthetic:unrelated"},
  {...cellPair,original_cell:{...cellPair.original_cell,cell:"C9"}}
 ])assert.throws(()=>prepare(withCellPair(bad)),
  /INVALID_ECO_SOURCE_CELL_CROSSWALK/);
});
test("crosswalk rejects observed-label promotion and hidden raw payloads",()=>{
 for(const bad of [
  {...cellPair,related_cell:{...cellPair.related_cell,evidence_class:"observed"}},
  {...cellPair,related_cell:{...cellPair.related_cell,coordinates:[153,-27]}},
  {...cellPair,original_cell:{...cellPair.original_cell,raw_file:"private"}},
  {...cellPair,source_bytes:"private"}
 ])assert.throws(()=>prepare(withCellPair(bad)),
  /INVALID_ECO_SOURCE_CELL_CROSSWALK/);
});
test("crosswalk requires a distinct related source lineage and anchored original",()=>{
 assert.throws(()=>prepare({cascade_input:input,cell_anchor:anchor,
  cell_crosswalk:cellPair}),/INVALID_ECO_SOURCE_CELL_CROSSWALK/);
 assert.throws(()=>prepare({cascade_input:input,source_lineage:lineage,
  cell_crosswalk:cellPair}),/INVALID_ECO_SOURCE_CELL_CROSSWALK/);
});
test("H0 never exposes the crosswalk even if caller supplied a pair",()=>{
 const r=prepare({...withCellPair(),requested_hydration:"H0"});
 assert.deepEqual(r.source_cell_crosswalk_review,{state:"NOT_REQUESTED"});
 assert.equal(r.hydration.H2.state,"NOT_REQUESTED");
 assert.equal(r.release.public_release_authorised,false);
});
