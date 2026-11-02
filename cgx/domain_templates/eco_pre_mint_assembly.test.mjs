import test from "node:test";
import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {prepareEcoPreMintAssembly as prepare, reviewEcoFormulaNamespaceCollision as reviewNamespace,
  reviewEcoSiteReadiness as reviewSite} from "./eco_pre_mint_assembly.mjs";

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
 assert.equal(JSON.stringify(r).includes('"numeric_value":9.6'),false);
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

test("mojibake in physical units is a discrepancy even when strings match",()=>{
 for(const units of [["m²","mÂ²"],["kg/mÂ³","kg/mÂ³"]]){
  const pair={...cellPair,
   original_cell:{...cellPair.original_cell,unit:units[0]},
   related_cell:{...cellPair.related_cell,unit:units[1]}};
  const r=prepare(withCellPair(pair));
  assert.equal(r.source_cell_crosswalk_review.unit_encoding_valid,false);
  assert.equal(r.source_cell_crosswalk_review.state,
   "R1_CALLER_DECLARED_CELL_DISCREPANCY_HOLD");
  assert.equal(r.release.mint_allowed,false);
 }
});


// Pairwise ACL posture: synthetic snapshots only; never actual permission grants.
const translatedAcl={
 source_ref:lineage.related_source_ref,source_id:"synthetic:translated-id",
 source_revision:lineage.related_revision_ref,
 provider_observation_ref:"synthetic:related-acl-observation",
 permissions:[{type:"user",role:"owner"}]
};
test("original link-reader versus translated owner-only ACL classes remain held",()=>{
 const r=prepare({cascade_input:input,source_lineage:lineage,
   access_posture:acl,related_access_posture:translatedAcl});
 const a=r.related_access_posture_review;
 assert.equal(a.state,"R1_DECLARED_ACCESS_POSTURE_DIVERGENCE_HOLD");
 assert.equal(a.original_anyone_link_present,true);
 assert.equal(a.related_anyone_link_present,false);
 assert.equal(a.access_classes_divergent,true);
 assert.equal(a.acl_equivalent,false);
 assert.equal(a.independent_acl_readback_verified,false);
 assert.equal(r.release.mint_allowed,false);
 assert.ok(r.blocking_gates.includes("SOURCE_TRANSLATION_ACCESS_POSTURE_DIVERGENCE"));
 assert.equal(JSON.stringify(r).includes("synthetic:related-acl-observation"),false);
});
test("matching declared ACL classes still cannot establish equivalence or rights",()=>{
 const r=prepare({cascade_input:input,source_lineage:lineage,
   access_posture:acl,related_access_posture:{...translatedAcl,
     permissions:[{type:"anyone",role:"reader",allowFileDiscovery:false},
       {type:"user",role:"owner"}]}});
 assert.equal(r.related_access_posture_review.state,
   "R1_DECLARED_ACCESS_CLASSES_MATCH_NOT_EQUIVALENCE");
 assert.equal(r.related_access_posture_review.acl_equivalent,false);
 assert.equal(r.related_access_posture_review.rights_approved,false);
 assert.ok(r.blocking_gates.includes(
   "PAIRWISE_ACCESS_POSTURES_NOT_INDEPENDENTLY_ATTESTED"));
});
test("related ACL requires both source lineage and original ACL",()=>{
 for(const req of [
   {cascade_input:input,access_posture:acl,related_access_posture:translatedAcl},
   {cascade_input:input,source_lineage:lineage,related_access_posture:translatedAcl}
 ])assert.throws(()=>prepare(req),/INVALID_ECO_RELATED_ACCESS_POSTURE/);
});
test("related ACL rejects wrong source, stale revision and identity leakage",()=>{
 for(const bad of [
   {...translatedAcl,source_ref:"synthetic:unrelated"},
   {...translatedAcl,source_revision:"stale"},
   {...translatedAcl,source_id:""},
   {...translatedAcl,permissions:[{type:"user",role:"owner",
     emailAddress:"private@example.invalid"}]},
   {...translatedAcl,provider_authenticated:true}
 ])assert.throws(()=>prepare({cascade_input:input,source_lineage:lineage,
   access_posture:acl,related_access_posture:bad}),
   /INVALID_ECO_RELATED_ACCESS_POSTURE|INVALID_ECO_ACCESS_POSTURE/);
});
test("H0 omits pairwise access classes and never upgrades rights",()=>{
 const r=prepare({cascade_input:input,source_lineage:lineage,
   access_posture:acl,related_access_posture:translatedAcl,
   requested_hydration:"H0"});
 assert.deepEqual(r.related_access_posture_review,{state:"NOT_REQUESTED"});
 assert.equal(r.hydration.H2.state,"NOT_REQUESTED");
 assert.equal(r.permissions.public_publish,false);
});


test("symbolic-expression crosswalk holds source-to-translation mojibake without repair",()=>{
 const symbolicAnchor={...anchor,sheet:"31_Formula_Library",cell:"B3"};
 const pair={source_ref:source.source_ref,source_revision:source.revision,
  source_sha256:digest,related_source_ref:lineage.related_source_ref,
  related_revision_ref:lineage.related_revision_ref,
  original_cell:{sheet:symbolicAnchor.sheet,cell:"B3",
   expression_text:"F = m × a",evidence_class:"simulated"},
  related_cell:{sheet:"SYNTHETIC_31_Formula_Library",cell:"B3",
   expression_text:"F = m Ã— a",evidence_class:"simulated"}};
 const r=prepare({cascade_input:input,cell_anchor:symbolicAnchor,
  source_lineage:lineage,symbolic_expression_crosswalk:pair});
 const c=r.source_symbolic_expression_crosswalk_review;
 assert.equal(c.state,"R1_CALLER_DECLARED_SYMBOLIC_EXPRESSION_DISCREPANCY_HOLD");
 assert.equal(c.expression_text_match,false);
 assert.equal(c.original_encoding_valid,true);
 assert.equal(c.related_encoding_valid,false);
 assert.ok(r.blocking_gates.includes("SOURCE_TRANSLATION_SYMBOLIC_EXPRESSION_DISCREPANCY"));
 assert.equal(r.release.mint_allowed,false);
 assert.equal(r.candidate_object_id,null);
 assert.equal(JSON.stringify(r).includes("F = m"),false);
 const clean={...pair,related_cell:{...pair.related_cell,
  expression_text:pair.original_cell.expression_text}};
 const ok=prepare({cascade_input:input,cell_anchor:symbolicAnchor,
  source_lineage:lineage,symbolic_expression_crosswalk:clean});
 assert.equal(ok.source_symbolic_expression_crosswalk_review.state,
  "R1_CALLER_DECLARED_SYMBOLIC_TEXT_MATCH_NOT_EQUIVALENCE");
 assert.equal(ok.source_symbolic_expression_crosswalk_review.scientific_equivalence_verified,false);
 assert.equal(ok.release.mint_allowed,false);
});
test("symbolic-expression crosswalk rejects stale provenance, wrong anchor, evidence and raw payload",()=>{
 const symbolicAnchor={...anchor,sheet:"31_Formula_Library",cell:"B3"};
 const pair={source_ref:source.source_ref,source_revision:source.revision,
  source_sha256:digest,related_source_ref:lineage.related_source_ref,
  related_revision_ref:lineage.related_revision_ref,
  original_cell:{sheet:symbolicAnchor.sheet,cell:"B3",
   expression_text:"F = m × a",evidence_class:"simulated"},
  related_cell:{sheet:"SYNTHETIC_31_Formula_Library",cell:"B3",
   expression_text:"F = m × a",evidence_class:"simulated"}};
 const call=p=>prepare({cascade_input:input,cell_anchor:symbolicAnchor,
  source_lineage:lineage,symbolic_expression_crosswalk:p});
 for(const bad of [
  {...pair,source_revision:"stale"},
  {...pair,source_sha256:"0".repeat(64)},
  {...pair,related_revision_ref:"stale"},
  {...pair,original_cell:{...pair.original_cell,cell:"B4"}},
  {...pair,related_cell:{...pair.related_cell,evidence_class:"observed"}},
  {...pair,related_cell:{...pair.related_cell,coordinates:[153,-27]}},
  {...pair,original_cell:{...pair.original_cell,expression_text:"line\nunsafe"}}
 ])assert.throws(()=>call(bad),/INVALID_ECO_SYMBOLIC_EXPRESSION_CROSSWALK/);
 const h0=prepare({cascade_input:input,cell_anchor:symbolicAnchor,
  source_lineage:lineage,symbolic_expression_crosswalk:pair,requested_hydration:"H0"});
 assert.equal(h0.source_symbolic_expression_crosswalk_review.state,"NOT_REQUESTED");
});

test("synthetic three-factor and Greek/superscript encoding regressions remain held",()=>{
 const symbolicAnchor={...anchor,sheet:"31_Formula_Library",cell:"B9"};
 const examples=[
  ["score = alpha × beta × gamma","score = alpha Ã— beta Ã— gamma"],
  ["pressure = 0.5ρv²","pressure = 0.5ÏvÂ²"]
 ];
 for(const [original,translated] of examples){
  const pair={source_ref:source.source_ref,source_revision:source.revision,
   source_sha256:digest,related_source_ref:"synthetic:translated-type1-sheet",
   related_revision_ref:"synthetic-related-provider-revision",
   original_cell:{sheet:"31_Formula_Library",cell:"B9",
    expression_text:original,evidence_class:"simulated"},
   related_cell:{sheet:"SYNTHETIC_31_Formula_Library",cell:"B9",
    expression_text:translated,evidence_class:"simulated"}};
  const sourceLineage={source_ref:source.source_ref,
   related_source_ref:pair.related_source_ref,
   relation_kind:"embedded_translation",
   manifest_location_ref:"01_Source_Manifest!A3:B3",
   manifest_source_sha256:digest,
   related_revision_ref:pair.related_revision_ref};
  const result=prepare({cascade_input:input,cell_anchor:symbolicAnchor,
   source_lineage:sourceLineage,symbolic_expression_crosswalk:pair});
  const review=result.source_symbolic_expression_crosswalk_review;
  assert.equal(review.state,"R1_CALLER_DECLARED_SYMBOLIC_EXPRESSION_DISCREPANCY_HOLD");
  assert.equal(review.expression_text_match,false);
  assert.equal(review.related_encoding_valid,false);
  assert.equal(review.scientific_equivalence_verified,false);
  assert.equal(result.release.mint_allowed,false);
  assert.equal(result.release.public_release_authorised,false);
  assert.equal(JSON.stringify(result).includes(original),false);
  assert.equal(JSON.stringify(result).includes(translated),false);
 }
});

test("formula inventory additions cannot inherit original provenance",()=>{
 const inventory={source_ref:source.source_ref,source_revision:source.revision,
   source_sha256:digest,related_source_ref:lineage.related_source_ref,
   related_revision_ref:lineage.related_revision_ref,
   original_ids:["FM-001","FM-002","FM-003","FM-004","FM-005","FM-006","FM-007"],
   related_ids:["FM-001","FM-002","FM-003","FM-004","FM-005","FM-006","FM-007","FM-008","FM-009"]};
 const r=prepare({cascade_input:input,source_lineage:lineage,
   formula_inventory:inventory});
 assert.equal(r.formula_inventory_review.state,
   "R1_TRANSLATION_FORMULA_INVENTORY_DELTA_HOLD");
 assert.deepEqual(r.formula_inventory_review.added_related_formula_ids,["FM-008","FM-009"]);
 assert.equal(r.formula_inventory_review.original_formula_count,7);
 assert.equal(r.formula_inventory_review.related_formula_count,9);
 assert.equal(r.formula_inventory_review.original_formula_inventory_authenticated_by_module,false);
 assert.equal(r.formula_inventory_review.independent_physics_validated,false);
 assert.ok(r.blocking_gates.includes("TRANSLATION_FORMULA_LIBRARY_DELTA_REQUIRES_PROVENANCE"));
 assert.equal(r.release.mint_allowed,false);
 assert.equal(r.candidate_object_id,null);
});
test("formula inventory rejects unpinned, duplicated and cross-source IDs",()=>{
 const base={source_ref:source.source_ref,source_revision:source.revision,
   source_sha256:digest,related_source_ref:lineage.related_source_ref,
   related_revision_ref:lineage.related_revision_ref,
   original_ids:["FM-001"],related_ids:["FM-001"]};
 for(const bad of [
   {...base,source_sha256:"0".repeat(64)},
   {...base,related_revision_ref:"stale"},
   {...base,original_ids:["FM-001","FM-001"]},
   {...base,related_ids:["FM-001","PRIVATE-RAW"]},
   {...base,related_source_ref:"synthetic:other"}
 ])assert.throws(()=>prepare({cascade_input:input,source_lineage:lineage,
   formula_inventory:bad}),/INVALID_ECO_FORMULA_INVENTORY/);
 const r=prepare({cascade_input:input,source_lineage:lineage,
   formula_inventory:base,requested_hydration:"H0"});
 assert.equal(r.formula_inventory_review.state,"NOT_REQUESTED");
 assert.equal(r.release.public_release_authorised,false);
});

test("combined manifest status and symbolic corruption never authorise Eco admission",()=>{
 // Synthetic-only integration regression: a source manifest label is not
 // evidence that a translated scientific expression or inventory is faithful.
 const symbolicAnchor={...anchor,sheet:"31_Formula_Library",cell:"B3"};
 const pair={source_ref:source.source_ref,source_revision:source.revision,
  source_sha256:digest,related_source_ref:lineage.related_source_ref,
  related_revision_ref:lineage.related_revision_ref,
  original_cell:{sheet:symbolicAnchor.sheet,cell:"B3",
   expression_text:"score = x × y",evidence_class:"simulated"},
  related_cell:{sheet:"SYNTHETIC_31_Formula_Library",cell:"B3",
   expression_text:"score = x Ã— y",evidence_class:"simulated"}};
 const inventory={source_ref:source.source_ref,source_revision:source.revision,
  source_sha256:digest,related_source_ref:lineage.related_source_ref,
  related_revision_ref:lineage.related_revision_ref,
  original_ids:["FM-001"],related_ids:["FM-001","FM-008"]};
 const r=prepare({cascade_input:input,source_lineage:lineage,
  cell_anchor:symbolicAnchor,symbolic_expression_crosswalk:pair,
  formula_inventory:inventory});
 assert.equal(r.source_lineage_review.claimed_translation_state,"translated_verified");
 assert.equal(r.source_lineage_review.byte_equivalence_verified,false);
 assert.equal(r.source_symbolic_expression_crosswalk_review.state,
  "R1_CALLER_DECLARED_SYMBOLIC_EXPRESSION_DISCREPANCY_HOLD");
 assert.equal(r.formula_inventory_review.state,
  "R1_TRANSLATION_FORMULA_INVENTORY_DELTA_HOLD");
 assert.ok(r.blocking_gates.includes("SOURCE_TRANSLATION_SYMBOLIC_EXPRESSION_DISCREPANCY"));
 assert.ok(r.blocking_gates.includes("TRANSLATION_FORMULA_LIBRARY_DELTA_REQUIRES_PROVENANCE"));
 assert.equal(r.candidate_object_id,null);
 assert.equal(r.release.mint_allowed,false);
 assert.equal(r.release.public_release_authorised,false);
 assert.equal(r.canonical_write,false);
 assert.equal(JSON.stringify(r).includes("score = x"),false);
});


test("cell-addressed symbolic correction candidates preserve original and omit text",()=>{
 const base={source_ref:source.source_ref,source_revision:source.revision,
   source_sha256:digest,related_source_ref:lineage.related_source_ref,
   related_revision_ref:lineage.related_revision_ref};
 const entries=[
  {formula_id:"FM-001",original_cell:{sheet:"31_Formula_Library",cell:"B3",
    expression_text:"synthetic = x × y",evidence_class:"simulated"},
   related_cell:{sheet:"SYNTHETIC_31_Formula_Library",cell:"B3",
    expression_text:"synthetic = x Ã— y",evidence_class:"simulated"},
   review_action:"REVIEW_TRANSLATION_ENCODING"},
  {formula_id:"FM-005",original_cell:{sheet:"31_Formula_Library",cell:"B7",
    expression_text:"synthetic = x / y",evidence_class:"simulated"},
   related_cell:{sheet:"SYNTHETIC_31_Formula_Library",cell:"B7",
    expression_text:"synthetic = x / y",evidence_class:"simulated"},
   review_action:"PRESERVE_SOURCE_MATCH"}
 ];
 const r=prepare({cascade_input:input,source_lineage:lineage,
   symbolic_correction_batch:{...base,entries}});
 const p=r.symbolic_correction_batch_review;
 assert.equal(p.state,"R1_TRANSLATION_CORRECTION_CANDIDATES_HOLD");
 assert.equal(p.candidate_correction_count,1);
 assert.equal(p.compared_count,2);
 assert.deepEqual(p.correction_records.map(x=>x.formula_id),["FM-001","FM-005"]);
 assert.equal(p.correction_records[0].original_cell_ref,"31_Formula_Library!B3");
 assert.equal(p.correction_records[0].translated_cell_ref,
   "SYNTHETIC_31_Formula_Library!B3");
 assert.equal(p.correction_records[0].repair_applied,false);
 assert.equal(p.correction_records[1].review_action,"PRESERVE_SOURCE_MATCH");
 assert.equal(p.source_or_translation_modified,false);
 assert.equal(p.independent_provider_attestation,false);
 assert.equal(r.canonical_write,false);
 assert.equal(r.release.mint_allowed,false);
 assert.ok(r.blocking_gates.includes("TRANSLATED_SYMBOLIC_TEXT_REPAIR_NOT_APPLIED"));
 assert.equal(JSON.stringify(r).includes("synthetic = x"),false);
 const call=entries=>prepare({cascade_input:input,source_lineage:lineage,
   symbolic_correction_batch:{...base,entries}});
 assert.throws(()=>call([entries[0],{...entries[0]}]),
   /DUPLICATE_ECO_SYMBOLIC_CORRECTION_ANCHOR/);
 assert.throws(()=>call([{...entries[0],review_action:"PRESERVE_SOURCE_MATCH"}]),
   /ECO_SYMBOLIC_CORRECTION_ACTION_CONFLICT/);
 assert.throws(()=>call([{...entries[0],original_cell:{
   ...entries[0].original_cell,evidence_class:"observed"}}]),
   /INVALID_ECO_SYMBOLIC_EXPRESSION_CROSSWALK/);
 assert.throws(()=>prepare({cascade_input:input,source_lineage:lineage,
   symbolic_correction_batch:{...base,source_revision:"stale",entries}}),
   /INVALID_ECO_SYMBOLIC_CORRECTION_BATCH/);
 const h0=prepare({cascade_input:input,source_lineage:lineage,
   symbolic_correction_batch:{...base,entries},requested_hydration:"H0"});
 assert.equal(h0.symbolic_correction_batch_review.state,"NOT_REQUESTED");
});
test("symbolic correction plan rejects source-free, raw and fabricated records",()=>{
 const base={source_ref:source.source_ref,source_revision:source.revision,
   source_sha256:digest,related_source_ref:lineage.related_source_ref,
   related_revision_ref:lineage.related_revision_ref};
 const entry={formula_id:"FM-002",review_action:"REVIEW_TRANSLATION_ENCODING",
  original_cell:{sheet:"31_Formula_Library",cell:"B4",
   expression_text:"synthetic × x",evidence_class:"simulated"},
  related_cell:{sheet:"SYNTHETIC_31_Formula_Library",cell:"B4",
   expression_text:"synthetic Ã— x",evidence_class:"simulated"}};
 for(const bad of [
   {...entry,raw_source_bytes:"private"},
   {...entry,formula_id:"UNVERIFIED"},
   {...entry,related_cell:{...entry.related_cell,coordinates:[0,0]}}
 ])assert.throws(()=>prepare({cascade_input:input,source_lineage:lineage,
   symbolic_correction_batch:{...base,entries:[bad]}}),
   /INVALID_ECO_SYMBOLIC_CORRECTION_ENTRY|INVALID_ECO_SYMBOLIC_EXPRESSION_CROSSWALK/);
 assert.throws(()=>prepare({cascade_input:input,
   symbolic_correction_batch:{...base,entries:[entry]}}),
   /INVALID_ECO_SYMBOLIC_CORRECTION_BATCH/);
});


test("symbolic correction formula ID requires paired A-row identity anchors",()=>{
 const base={source_ref:source.source_ref,source_revision:source.revision,
  source_sha256:digest,related_source_ref:lineage.related_source_ref,
  related_revision_ref:lineage.related_revision_ref};
 const entry={formula_id:"FM-001",review_action:"REVIEW_TRANSLATION_ENCODING",
  original_cell:{sheet:"31_Formula_Library",cell:"B3",
   expression_text:"synthetic = v × A",evidence_class:"simulated"},
  related_cell:{sheet:"SYNTHETIC_31_Formula_Library",cell:"B3",
   expression_text:"synthetic = v Ã— A",evidence_class:"simulated"},
  original_id_anchor:{sheet:"31_Formula_Library",cell:"A3",formula_id:"FM-001"},
  related_id_anchor:{sheet:"SYNTHETIC_31_Formula_Library",cell:"A3",formula_id:"FM-001"}};
 const run=entries=>prepare({cascade_input:input,source_lineage:lineage,
  symbolic_correction_batch:{...base,entries}});
 const r=run([entry]),p=r.symbolic_correction_batch_review;
 assert.equal(p.formula_id_row_binding_declared_count,1);
 assert.equal(p.formula_id_row_binding_required_count,0);
 assert.equal(p.correction_records[0].original_id_cell_ref,"31_Formula_Library!A3");
 assert.equal(p.correction_records[0].translated_id_cell_ref,
  "SYNTHETIC_31_Formula_Library!A3");
 assert.equal(p.correction_records[0].formula_id_row_binding_provider_attested,false);
 assert.equal(r.release.mint_allowed,false);
 assert.equal(r.canonical_write,false);
 assert.equal(JSON.stringify(r).includes("synthetic = v"),false);
 const unbound=run([{...entry,original_id_anchor:undefined,related_id_anchor:undefined}]);
 assert.equal(unbound.symbolic_correction_batch_review.formula_id_row_binding_required_count,1);
 assert.ok(unbound.blocking_gates.includes("FORMULA_ID_SOURCE_ROW_BINDING_REQUIRED"));
 for(const bad of [
  {...entry,original_id_anchor:{...entry.original_id_anchor,formula_id:"FM-002"}},
  {...entry,original_id_anchor:{...entry.original_id_anchor,cell:"A4"}},
  {...entry,related_id_anchor:{...entry.related_id_anchor,sheet:"other"}},
  {...entry,related_id_anchor:undefined},
  {...entry,original_id_anchor:{...entry.original_id_anchor,raw_bytes:"secret"}}
 ])assert.throws(()=>run([bad]),/ECO_SYMBOLIC_FORMULA_ID_ROW_BINDING_CONFLICT/);
});

test("asymmetric original and translation row offsets retain six reversible text candidates",()=>{
 // Synthetic strings and coordinates model an offset translation; no Drive
 // workbook content, original provider assertion or ecological measurement.
 const rows=[
  ["q = v × A","q = v Ã— A"],
  ["mist = q × f","mist = q Ã— f"],
  ["pressure = 0.5ρv²","pressure = 0.5ÏvÂ²"],
  ["drag = 0.5ρAv²","drag = 0.5ÏAvÂ²"],
  ["margin = capacity / load","margin = capacity / load"],
  ["index = q × wind","index = q Ã— wind"],
  ["RPN = S × O × D","RPN = S Ã— O Ã— D"]
 ];
 const entries=rows.map(([original,related],i)=>{
  const id="FM-"+String(i+1).padStart(3,"0");
  return {formula_id:id,
   review_action:original===related?"PRESERVE_SOURCE_MATCH":
     "REVIEW_TRANSLATION_ENCODING",
   original_cell:{sheet:"SYNTHETIC_ORIGINAL_FORMULAS",cell:"B"+(i+2),
     expression_text:original,evidence_class:"simulated"},
   related_cell:{sheet:"SYNTHETIC_TRANSLATION_FORMULAS",cell:"B"+(i+3),
     expression_text:related,evidence_class:"simulated"},
   original_id_anchor:{sheet:"SYNTHETIC_ORIGINAL_FORMULAS",
     cell:"A"+(i+2),formula_id:id},
   related_id_anchor:{sheet:"SYNTHETIC_TRANSLATION_FORMULAS",
     cell:"A"+(i+3),formula_id:id}};
 });
 const base={source_ref:source.source_ref,source_revision:source.revision,
  source_sha256:digest,related_source_ref:lineage.related_source_ref,
  related_revision_ref:lineage.related_revision_ref};
 const run=entries=>prepare({cascade_input:input,source_lineage:lineage,
  symbolic_correction_batch:{...base,entries}});
 const r=run(entries),p=r.symbolic_correction_batch_review;
 assert.equal(p.compared_count,7);
 assert.equal(p.candidate_correction_count,6);
 assert.equal(p.caller_text_roundtrip_candidate_count,6);
 assert.equal(p.formula_id_row_binding_declared_count,7);
 assert.equal(p.formula_id_row_binding_required_count,0);
 assert.equal(p.correction_records[0].original_cell_ref,
  "SYNTHETIC_ORIGINAL_FORMULAS!B2");
 assert.equal(p.correction_records[0].translated_cell_ref,
  "SYNTHETIC_TRANSLATION_FORMULAS!B3");
 assert.equal(p.correction_records[4].caller_text_roundtrip_candidate,false);
 assert.equal(r.canonical_write,false);
 assert.equal(r.release.mint_allowed,false);
 assert.equal(JSON.stringify(r).includes("pressure ="),false);
 assert.throws(()=>run([{...entries[0],
   original_id_anchor:{...entries[0].original_id_anchor,cell:"A3"}}]),
   /ECO_SYMBOLIC_FORMULA_ID_ROW_BINDING_CONFLICT/);
 const unrecoverable=run([{...entries[0],
   related_cell:{...entries[0].related_cell,expression_text:"q = v Ã— A?"}}]);
 assert.equal(unrecoverable.symbolic_correction_batch_review
   .caller_text_roundtrip_candidate_count,0);
 assert.equal(unrecoverable.canonical_write,false);
});

test("Second Cycle coefficient role collision is retained as held pre-Mint review",()=>{
 const roleInput={source_ref:source.source_ref,source_revision:source.revision,
   source_sha256:digest,
   flow:{formula_id:"FM-001",sheet_ref:"07_Flow_Mist_Model",
     parameter_cell_ref:"B5",role:"flow_coefficient",symbol:"Cd",
     numeric_value:0.5,unit:"ratio",evidence_class:"simulated"},
   drag:{formula_id:"FM-004",sheet_ref:"11_Anchor_Mooring",
     parameter_cell_ref:"B4",role:"drag_coefficient",symbol:"Cd",
     numeric_value:1.2,unit:"ratio",evidence_class:"simulated"}};
 const result=prepare({cascade_input:input,coefficient_roles:roleInput});
 assert.equal(result.coefficient_roles_review.state,"R1_COEFFICIENT_SYMBOL_OVERLOAD_HOLD");
 assert.ok(result.blocking_gates.includes("SECOND_CYCLE_COEFFICIENT_SYMBOL_OVERLOAD_HOLD"));
 assert.ok(result.blocking_gates.includes("COEFFICIENT_ROLES_REQUIRE_PROVIDER_CELL_ATTESTATION"));
 assert.equal(result.coefficient_roles_review.provider_source_cells_fetched_by_module,false);
 assert.equal(result.release.mint_allowed,false);
 assert.equal(result.canonical_write,false);
 assert.equal(result.candidate_object_id,null);
 assert.equal(JSON.stringify(result).includes("0.5"),false);
 const h0=prepare({cascade_input:input,coefficient_roles:roleInput,requested_hydration:"H0"});
 assert.equal(h0.coefficient_roles_review.state,"NOT_REQUESTED");
 for(const bad of [
   {...roleInput,source_revision:"stale"},
   {...roleInput,source_sha256:undefined},
   "invalid",
   {...roleInput,source_sha256:"0".repeat(64)},
   {...roleInput,drag:{...roleInput.drag,parameter_cell_ref:"B5"}},
   {...roleInput,flow:{...roleInput.flow,evidence_class:"observed"}}
 ])assert.throws(()=>prepare({cascade_input:input,coefficient_roles:bad}),
   /ECO_COEFFICIENT_SOURCE_OR_EVIDENCE_CONFLICT|INVALID_SECOND_CYCLE_COEFFICIENT_ROLES/);
});


test("original cell digest crosswalk binds receipt hashes without promoting private source or physics",()=>{
 const base={source_ref:source.source_ref,source_revision:source.revision,
  source_sha256:digest,related_source_ref:lineage.related_source_ref,
  related_revision_ref:lineage.related_revision_ref,
  receipt_ref:"synthetic:private-receipt",receipt_sha256:"a".repeat(64),
  evidence_class:"simulated"};
 const entries=[
  {formula_id:"FM-001",original_anchor:"31_Formula_Library!B3",
   original_id_anchor:"31_Formula_Library!A3",
   translated_id_anchor:"SYNTHETIC_31_Formula_Library!A3",
   translated_anchor:"SYNTHETIC_31_Formula_Library!B3",
   original_text_sha256:"1".repeat(64),translated_text_sha256:"2".repeat(64),
   status:"REVERSIBLE_ENCODING_CANDIDATE"},
  {formula_id:"FM-005",original_anchor:"31_Formula_Library!B7",
   original_id_anchor:"31_Formula_Library!A7",
   translated_id_anchor:"SYNTHETIC_31_Formula_Library!A7",
   translated_anchor:"SYNTHETIC_31_Formula_Library!B7",
   original_text_sha256:"3".repeat(64),translated_text_sha256:"3".repeat(64),
   status:"TEXT_EXACT"}];
 const packet={...base,entries,translation_only_ids:["FM-008","FM-009"],
   unit_defect_refs:["SYNTHETIC_07_Flow_Mist_Model!C4",
    "SYNTHETIC_07_Flow_Mist_Model!C7"]};
 const run=x=>prepare({cascade_input:input,source_lineage:lineage,
   original_cell_digest_crosswalk:x});
 const r=run(packet),p=r.original_cell_digest_crosswalk_review;
 assert.equal(p.state,"R1_CALLER_DECLARED_ORIGINAL_CELL_DIGESTS_HOLD");
 assert.equal(p.compared_count,2);
 assert.equal(p.formula_id_row_binding_declared_count,2);
 assert.equal(p.formula_id_row_binding_required_count,0);
 assert.equal(p.formula_records[0].formula_id_row_binding_provider_attested,false);
 assert.equal(p.formula_records[0].original_id_cell_ref,"31_Formula_Library!A3");
 assert.equal(p.mismatched_text_count,1);
 assert.equal(p.original_text_exact_count,1);
 assert.deepEqual(p.translation_only_formula_ids,["FM-008","FM-009"]);
 assert.equal(p.unqualified_unit_defect_refs.length,2);
 assert.equal(p.original_source_sha_bound_to_executed_cascade,true);
 assert.equal(p.receipt_sha256_cryptographically_verified_by_module,false);
 assert.equal(p.original_cells_reread,false);
 assert.equal(p.translation_equivalence_verified,false);
 assert.equal(r.canonical_write,false);
 assert.equal(r.release.mint_allowed,false);
 assert.ok(r.blocking_gates.includes("TRANSLATED_PHYSICAL_UNITS_UNQUALIFIED"));
 assert.ok(r.blocking_gates.includes("TRANSLATION_ONLY_FORMULAS_NOT_ORIGINAL_SOURCE_EVIDENCE"));
 assert.equal(JSON.stringify(r).includes("synthetic = v"),false);
 const unbound=run({...packet,entries:entries.map(({original_id_anchor,
  translated_id_anchor,...rest})=>rest)});
 assert.equal(unbound.original_cell_digest_crosswalk_review
  .formula_id_row_binding_required_count,2);
 assert.ok(unbound.blocking_gates.includes(
  "ORIGINAL_CELL_DIGEST_FORMULA_ID_ROW_BINDING_REQUIRED"));
 for(const bad of [
  {...entries[0],original_id_anchor:"31_Formula_Library!A4"},
  {...entries[0],translated_id_anchor:"SYNTHETIC_31_Formula_Library!A4"},
  {...entries[0],original_id_anchor:"OTHER!A3"},
  {...entries[0],translated_id_anchor:undefined},
  {...entries[0],original_id_anchor:"31_Formula_Library!A3",
   translated_id_anchor:"SYNTHETIC_31_Formula_Library!A4"}
 ])assert.throws(()=>run({...packet,entries:[bad]}),
  /ECO_ORIGINAL_CELL_DIGEST_FORMULA_ID_ROW_BINDING_CONFLICT/);
 assert.throws(()=>run({...packet,source_revision:"stale"}),
   /INVALID_ECO_ORIGINAL_CELL_DIGEST_CROSSWALK/);
 assert.throws(()=>run({...packet,source_sha256:"0".repeat(64)}),
   /INVALID_ECO_ORIGINAL_CELL_DIGEST_CROSSWALK/);
 assert.throws(()=>run({...packet,evidence_class:"observed"}),
   /INVALID_ECO_ORIGINAL_CELL_DIGEST_CROSSWALK/);
 assert.throws(()=>run({...packet,entries:[{...entries[0],status:"TEXT_EXACT"}]}),
   /ECO_ORIGINAL_CELL_DIGEST_STATUS_CONFLICT/);
 assert.throws(()=>run({...packet,translation_only_ids:["FM-001"]}),
   /ECO_TRANSLATION_ONLY_ID_ATTRIBUTION_CONFLICT/);
 assert.throws(()=>run({...packet,unit_defect_refs:["SYNTHETIC_07_Flow_Mist_Model!C4",
   "SYNTHETIC_07_Flow_Mist_Model!C4"]}),
   /INVALID_ECO_TRANSLATION_UNIT_DEFECT_REFERENCE/);
 assert.throws(()=>run({...packet,entries:[{...entries[0],raw_text:"private"}]}),
   /INVALID_ECO_ORIGINAL_CELL_DIGEST_ENTRY/);
 const h0=prepare({cascade_input:input,source_lineage:lineage,
  original_cell_digest_crosswalk:packet,requested_hydration:"H0"});
 assert.equal(h0.original_cell_digest_crosswalk_review.state,"NOT_REQUESTED");
});

test("formula digest receipt cannot contradict the independently declared inventory",()=>{
 // All values are synthetic; the real Second Cycle source stays in Drive.
 const provenance={source_ref:source.source_ref,source_revision:source.revision,
  source_sha256:digest,related_source_ref:lineage.related_source_ref,
  related_revision_ref:lineage.related_revision_ref};
 const entry=(id,row,hash)=>({
  formula_id:id,original_anchor:"31_Formula_Library!B"+row,
  original_id_anchor:"31_Formula_Library!A"+row,
  translated_anchor:"SYNTHETIC_31_Formula_Library!B"+row,
  translated_id_anchor:"SYNTHETIC_31_Formula_Library!A"+row,
  original_text_sha256:hash.repeat(64),
  translated_text_sha256:hash.repeat(64),status:"TEXT_EXACT"});
 const receipt={...provenance,receipt_ref:"synthetic:cell-receipt",
  receipt_sha256:"a".repeat(64),evidence_class:"simulated",
  entries:[entry("FM-001",3,"1"),entry("FM-005",7,"5")],
  translation_only_ids:["FM-008","FM-009"],unit_defect_refs:[]};
 const inventory={...provenance,original_ids:["FM-001","FM-005"],
  related_ids:["FM-001","FM-005","FM-008","FM-009"]};
 const review=i=>prepare({cascade_input:input,source_lineage:lineage,
  formula_inventory:i,original_cell_digest_crosswalk:receipt});
 const ok=review(inventory);
 assert.equal(ok.original_cell_digest_crosswalk_review.compared_count,2);
 assert.deepEqual(ok.formula_inventory_review.added_related_formula_ids,
  ["FM-008","FM-009"]);
 assert.equal(ok.release.mint_allowed,false);
 assert.equal(ok.canonical_write,false);
 for(const bad of [
  {...inventory,original_ids:["FM-005"]},
  {...inventory,related_ids:["FM-005","FM-008","FM-009"]},
  {...inventory,original_ids:["FM-001","FM-005","FM-008"]},
  {...inventory,related_ids:["FM-001","FM-005","FM-008"]}
 ])assert.throws(()=>review(bad),/ECO_FORMULA_RECEIPT_INVENTORY_CONFLICT/);
 const h0=prepare({cascade_input:input,source_lineage:lineage,
  formula_inventory:inventory,original_cell_digest_crosswalk:receipt,
  requested_hydration:"H0"});
 assert.equal(h0.original_cell_digest_crosswalk_review.state,"NOT_REQUESTED");
 assert.equal(h0.release.public_release_authorised,false);
});

test("independent symbolic correction and digest views cannot contradict A1 identity or text status",()=>{
 // All strings/hashes are synthetic; no private original source is copied.
 const base={source_ref:source.source_ref,source_revision:source.revision,
  source_sha256:digest,related_source_ref:lineage.related_source_ref,
  related_revision_ref:lineage.related_revision_ref};
 const original={sheet:"SYNTHETIC_ORIGINAL",cell:"B3",
  expression_text:"q = v × A",evidence_class:"simulated"};
 const translated={sheet:"SYNTHETIC_TRANSLATION",cell:"B3",
  expression_text:"q = v Ã— A",evidence_class:"simulated"};
 const correction={formula_id:"FM-001",review_action:"REVIEW_TRANSLATION_ENCODING",
  original_cell:original,related_cell:translated,
  original_id_anchor:{sheet:original.sheet,cell:"A3",formula_id:"FM-001"},
  related_id_anchor:{sheet:translated.sheet,cell:"A3",formula_id:"FM-001"}};
 const digestEntry={formula_id:"FM-001",
  original_anchor:"SYNTHETIC_ORIGINAL!B3",
  translated_anchor:"SYNTHETIC_TRANSLATION!B3",
  original_id_anchor:"SYNTHETIC_ORIGINAL!A3",
  translated_id_anchor:"SYNTHETIC_TRANSLATION!A3",
  original_text_sha256:"1".repeat(64),translated_text_sha256:"2".repeat(64),
  status:"REVERSIBLE_ENCODING_CANDIDATE"};
 const receipt={...base,receipt_ref:"synthetic:receipt",
  receipt_sha256:"a".repeat(64),evidence_class:"simulated",
  entries:[digestEntry],translation_only_ids:["FM-008","FM-009"],
  unit_defect_refs:[]};
 const run=(c=correction,d=digestEntry)=>prepare({
  cascade_input:input,source_lineage:lineage,
  symbolic_correction_batch:{...base,entries:[c]},
  original_cell_digest_crosswalk:{...receipt,entries:[d]}});
 const ok=run();
 assert.equal(ok.symbolic_correction_batch_review.candidate_correction_count,1);
 assert.equal(ok.original_cell_digest_crosswalk_review.mismatched_text_count,1);
 assert.equal(ok.canonical_write,false);
 assert.equal(ok.release.mint_allowed,false);
 assert.equal(JSON.stringify(ok).includes("q = v"),false);
 for(const [c,d] of [
  [correction,{...digestEntry,formula_id:"FM-002"}],
  [correction,{...digestEntry,translated_anchor:"SYNTHETIC_TRANSLATION!B4",
    translated_id_anchor:"SYNTHETIC_TRANSLATION!A4"}],
  [correction,{...digestEntry,original_id_anchor:undefined,
    translated_id_anchor:undefined}],
  [correction,{...digestEntry,original_text_sha256:"1".repeat(64),
    translated_text_sha256:"1".repeat(64),status:"TEXT_EXACT"}]
 ])assert.throws(()=>run(c,d),/ECO_SYMBOLIC_CORRECTION_DIGEST_CONFLICT/);
 const same={...correction,review_action:"PRESERVE_SOURCE_MATCH",
  related_cell:{...translated,expression_text:original.expression_text}};
 const exact={...digestEntry,translated_text_sha256:"1".repeat(64),
  status:"TEXT_EXACT"};
 const match=run(same,exact);
 assert.equal(match.symbolic_correction_batch_review.candidate_correction_count,0);
 assert.equal(match.release.public_release_authorised,false);
 assert.throws(()=>run(same,digestEntry),
  /ECO_SYMBOLIC_CORRECTION_DIGEST_CONFLICT/);
});


test("source-local FM labels reused by distinct Eco child namespaces never alias",()=>{
 const left={source_ref:"fixture:eco-child-a",source_revision:"v1",
   sheet:"CHILD_A_Formula_Library",cell:"B10",formula_id:"FM-008",
   expression_sha256:"a".repeat(64),evidence_class:"model_derived"};
 const right={...left,source_ref:"fixture:eco-child-b",
   sheet:"CHILD_B_Formula_Library",expression_sha256:"b".repeat(64),
   evidence_class:"source_asserted"};
 const r=reviewNamespace({left,right});
 assert.equal(r.state,"R1_CROSS_NAMESPACE_LOCAL_ID_COLLISION_HOLD");
 assert.equal(r.same_source_namespace,false);
 assert.equal(r.cross_source_alias_accepted,false);
 assert.equal(r.native_object_id,null);
 assert.equal(r.formula_semantics_equivalent,false);
 assert.equal(r.provider_cells_read_by_module,false);
 assert.equal(r.public_release_authorised,false);
 // A coincident digest cannot collapse two original source identities.
 assert.equal(reviewNamespace({left,right:{...right,expression_sha256:left.expression_sha256}}).state,
   "R1_CROSS_NAMESPACE_LOCAL_ID_COLLISION_HOLD");
});

test("formula namespace guard preserves revisions, conflicts and distinct IDs",()=>{
 const a={source_ref:"fixture:child",source_revision:"v1",
   sheet:"CHILD_Formula_Library",cell:"B10",formula_id:"FM-009",
   expression_sha256:"a".repeat(64),evidence_class:"simulated"};
 const review=b=>reviewNamespace({left:a,right:b});
 assert.equal(review({...a,source_revision:"v2"}).state,
   "R1_VERSIONED_FORMULA_VARIANT_HOLD");
 assert.equal(review({...a,expression_sha256:"b".repeat(64)}).state,
   "R1_SAME_REVISION_FORMULA_DIGEST_CONFLICT_HOLD");
 assert.equal(review({...a}).state,
   "R1_DECLARED_FORMULA_REFERENCE_MATCH_NOT_ATTESTED");
 assert.equal(review({...a,formula_id:"FM-010"}).state,
   "R1_DISTINCT_LOCAL_FORMULA_IDS");
 assert.equal(review({...a,sheet:"OTHER_Formula_Library"}).state,
   "R1_CROSS_NAMESPACE_LOCAL_ID_COLLISION_HOLD");
});

test("formula namespace guard rejects unqualified IDs, locations and raw expression",()=>{
 const a={source_ref:"fixture:child",source_revision:"v1",
   sheet:"CHILD_Formula_Library",cell:"B10",formula_id:"FM-008",
   expression_sha256:"a".repeat(64),evidence_class:"source_asserted"};
 const review=x=>reviewNamespace({left:a,right:x});
 for(const bad of [
   {...a,formula_id:"FM-8"}, {...a,cell:"B0"},
   {...a,cell:"A10"}, {...a,source_revision:""},
   {...a,expression_sha256:"invalid"},
   {...a,evidence_class:"observed"},
   {...a,expression_text:"protected expression"},
   {...a,source_ref:"fixture:child",sheet:"bad name"}
 ])assert.throws(()=>review(bad),/INVALID_ECO_FORMULA_NAMESPACE_PAIR/);
 assert.throws(()=>reviewNamespace({left:a,right:a,owner_approval:true}),
   /INVALID_ECO_FORMULA_NAMESPACE_PAIR/);
});

// Source-only water-quality schema comparison; all rows below are synthetic.

const wqRow={sheet:"20_WQ_DataSchema",row:6,
 parameter:"Conductivity / salinity",unit:"µS/cm or PSU",
 required:"Yes",qa_method:"Calibration solution",frequency:"5-15 min",
 claim_status:"Measurable",source_rationale:"Mixing/salinity context"};
const wqTranslated={...wqRow,sheet:"SECON0E3E_20_WQ_DataSchema",
 unit:"ÂµS/cm or PSU",qa_method:"Validated conductivity sensor",
 frequency:"DQO-defined; continuous or fixed interval",
 source_rationale:"SRC-020 method map"};
const wqInput={source_ref:source.source_ref,source_revision:source.revision,
 source_sha256:digest,related_source_ref:lineage.related_source_ref,
 related_revision_ref:lineage.related_revision_ref,
 rows:[{original:wqRow,translated:wqTranslated}]};
test("WQ original/translation source schema delta preserves rights, QA and unit holds",()=>{
 const r=prepare({cascade_input:input,source_lineage:lineage,
   water_quality_schema_delta:wqInput});
 const w=r.water_quality_schema_review;
 assert.equal(w.state,"R1_TRANSLATED_WQ_SCHEMA_DELTA_HOLD");
 assert.equal(w.changed_row_count,1);
 assert.equal(w.row_reviews[0].flags.includes("TRANSLATION_UNIT_ENCODING_DEFECT"),true);
 assert.equal(w.row_reviews[0].flags.includes("SAMPLING_POLICY_CHANGED_NOT_EQUIVALENCE"),true);
 assert.equal(w.row_reviews[0].flags.includes("CONDUCTIVITY_SALINITY_QUANTITY_AND_UNIT_SPLIT_REQUIRED"),true);
 assert.equal(w.measurement_observed,false);
 assert.equal(w.source_rights_verified,false);
 assert.equal(r.release.mint_allowed,false);
 assert.equal(r.blocking_gates.includes("WQ_TRANSLATION_SCHEMA_DELTA_HOLD"),true);
});
test("WQ schema source-only review never grants matching-row equivalence",()=>{
 const original={sheet:"20_WQ_DataSchema",row:3,parameter:"Temperature",
   unit:"°C",required:"Yes",qa_method:"Calibrated probe",
   frequency:"5-15 min",claim_status:"Measurable",
   source_rationale:"Water-quality context"};
 const translated={...original,sheet:"SECON0E3E_20_WQ_DataSchema"};
 const r=prepare({cascade_input:input,source_lineage:lineage,
   water_quality_schema_delta:{...wqInput,rows:[{original,translated}]}});
 assert.equal(r.water_quality_schema_review.state,
   "R1_CALLER_DECLARED_WQ_SCHEMA_MATCH_NOT_EQUIVALENCE");
 assert.equal(r.water_quality_schema_review.field_qa_verified,false);
 assert.equal(r.water_quality_schema_review.original_and_translation_provider_cells_read_by_module,false);
});
test("WQ schema source hash and related revision fail closed",()=>{
 for(const bad of [
  {...wqInput,source_sha256:"f".repeat(64)},
  {...wqInput,related_revision_ref:"stale-revision"}
 ])assert.throws(()=>prepare({cascade_input:input,source_lineage:lineage,
    water_quality_schema_delta:bad}),/ECO_WQ_SCHEMA_SOURCE_LINEAGE_CONFLICT/);
 assert.throws(()=>prepare({cascade_input:input,
    water_quality_schema_delta:wqInput}),/ECO_WQ_SCHEMA_SOURCE_LINEAGE_CONFLICT/);
});
test("WQ schema rejects duplicate row, mismatched parameter and measured payload",()=>{
 const pair=wqInput.rows[0];
 for(const rows of [
  [pair,pair],
  [{original:pair.original,translated:{...pair.translated,parameter:"Turbidity"}}],
  [{original:{...pair.original,measurement:42},translated:pair.translated}]
 ])assert.throws(()=>prepare({cascade_input:input,source_lineage:lineage,
   water_quality_schema_delta:{...wqInput,rows}}),
   /ECO_WQ_SCHEMA_ROW_IDENTITY_OR_DUPLICATE_CONFLICT/);
});

const siteCriteria=[
 ["Legal/permitting feasibility",0.18,"Blocks deployment"],
 ["Navigation/public safety",0.15,"Blocks deployment"],
 ["Hydrodynamic suitability",0.14,"Recipe/design selection"],
 ["Ecological compatibility",0.18,"Blocks deployment"],
 ["Biosecurity clearance",0.16,"Blocks habitat features"],
 ["Maintenance/access feasibility",0.08,"Operations"],
 ["Community/custodial pathway",0.11,"Public/social gate"]
];
const siteInput={source_ref:source.source_ref,source_revision:source.revision,
 source_sha256:digest,rows:siteCriteria.map(([criterion,weight,gate])=>
 ({criterion,weight,score:0,gate,evidence_ref:null}))};
test("site-score zero defaults remain unmeasured and all critical gates held",()=>{
 const r=reviewSite(siteInput);
 assert.equal(r.criteria_count,7);
 assert.equal(r.zero_score_count,7);
 assert.equal(r.critical_gate_count,5);
 assert.equal(r.weighted_score_declared,0);
 assert.equal(r.zero_means_unsuitable_verified,false);
 assert.equal(r.site_suitability_verified,false);
 assert.equal(r.permits_verified,false);
 assert.equal(r.geospatial_coordinates_verified,false);
 assert.equal(r.native_admitted,false);
});
test("positive weighted score and evidence reference cannot approve site",()=>{
 const rows=siteInput.rows.map((r,i)=>i===0?
   {...r,score:5,evidence_ref:"source-only:unreviewed"}:r);
 const r=reviewSite({...siteInput,rows});
 assert.ok(Math.abs(r.weighted_score_declared-0.9)<1e-12);
 assert.equal(r.critical_gate_count,5);
 assert.equal(r.site_suitability_verified,false);
 assert.equal(r.biosecurity_approved,false);
 assert.equal(r.cultural_stewardship_approved,false);
});
test("site-score input rejects invented geometry, missing criteria and weight drift",()=>{
 for(const bad of [
  {...siteInput,rows:siteInput.rows.slice(1)},
  {...siteInput,rows:siteInput.rows.map((r,i)=>i===0?{...r,weight:0.2}:r)},
  {...siteInput,rows:siteInput.rows.map((r,i)=>i===0?{...r,coordinates:[1,2]}:r)},
  {...siteInput,rows:siteInput.rows.map((r,i)=>i===0?{...r,score:6}:r)}
 ])assert.throws(()=>reviewSite(bad),/ECO_SITE_ASSESSMENT/);
});
test("site-score review is integrated into existing pre-mint chain with source pin",()=>{
 const r=prepare({cascade_input:input,site_assessment:siteInput});
 assert.equal(r.site_assessment_review.state,"R1_SITE_SCORE_SOURCE_ONLY_DEPLOYMENT_HOLD");
 assert.equal(r.site_assessment_review.zero_score_count,7);
 assert.equal(r.stack_layers.find(x=>x.layer==="site_assessment").state,
   "R1_SITE_SCORE_SOURCE_ONLY_DEPLOYMENT_HOLD");
 assert.equal(r.blocking_gates.includes("SITE_CRITICAL_PERMIT_BIOSECURITY_AND_ECOLOGY_GATES_OPEN"),true);
 assert.equal(r.release.mint_allowed,false);
 assert.equal(r.release.public_release_authorised,false);
 for(const bad of [
  {...siteInput,source_revision:"stale"},
  {...siteInput,source_sha256:"f".repeat(64)}
 ])assert.throws(()=>prepare({cascade_input:input,site_assessment:bad}),
   /ECO_SITE_ASSESSMENT_SOURCE_CONFLICT/);
});
