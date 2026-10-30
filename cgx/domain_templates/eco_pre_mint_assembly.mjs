/**
 * Athene Eco.cgx pre-Mint assembly: source-only, deterministic, no-write handoff.
 *
 * Reuses the existing Eco source-byte -> scoped alignment -> domain review
 * cascade. This is NOT a CGX mint, geometric reconstruction, CCC runtime, DBR
 * transaction, permission attestation, field measurement or public payload.
 * Caller retains authenticated original bytes privately; this function omits them.
 */
import {runEcoReviewCascade} from "./eco_review_cascade.mjs";
import {reviewEcoObservationShowcase} from "./eco_digital_mint_boundary.mjs";

export const ECO_PRE_MINT_SCHEMA="CGX-ECO-PRE-MINT-ASSEMBLY/0.1";
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const token=x=>typeof x==="string"&&x.length>0&&x.length<=256&&
  !/[\u0000-\u001f]/.test(x);
const SHA=/^[a-f0-9]{64}$/i;
const levels=["H0","H1","H2","H3","H4"];
const GEOMETRY_KINDS=new Set(["unknown","Point","LineString","Polygon",
  "MultiPoint","MultiLineString","MultiPolygon","mesh","voxel"]);
const geometryKeys=new Set(["source_ref","kind","dimension","source_geometry_ref",
  "crs_ref","coordinate_unit","time_frame_ref","vertical_datum_ref",
  "spatial_review_ref","rights_review_ref","stewardship_review_ref"]);
const ROUTES=Object.freeze({
  second_cycle_claim:"cgx/domain_templates/eco_second_cycle_claim_review.mjs",
  bioblock_monitoring:"cgx/domain_templates/eco_bioblock_monitoring_review.mjs"
});
const truth=x=>x!==null&&x!==undefined;

function reviewGeometryDescriptor(g,source_ref){
  if(g===null)return {
    state:"NO_GEOMETRY_SOURCE",kind:null,dimension:null,
    source_geometry_ref_present:false,crs_ref_present:false,
    time_frame_ref_present:false,actual_geometry_loaded:false,
    metric_geometry_validated:false,spatial_release_authorised:false,
    flags:["ORIGINAL_GEOMETRY_SOURCE_REQUIRED","COORDINATE_FRAME_AND_UNITS_REQUIRED"]
  };
  if(!obj(g)||Object.keys(g).some(k=>!geometryKeys.has(k))||
     g.source_ref!==source_ref||!GEOMETRY_KINDS.has(g.kind)||
     ![2,3].includes(g.dimension)||
     Object.entries(g).some(([k,v])=>k!=="dimension"&&k!=="kind"&&
       !token(v)))
    throw Error("INVALID_ECO_GEOMATRIX_DESCRIPTOR");
  // No coordinates, geometry bodies, arbitrary nested records or raw image
  // payloads can pass this closed-key source-only interface.
  const flags=["GEOMATRIX_REFERENCES_NOT_METRICALLY_OR_SPATIALLY_VALIDATED"];
  if(g.kind==="unknown")flags.push("GEOMETRY_KIND_UNRESOLVED");
  if(!truth(g.source_geometry_ref))flags.push("ORIGINAL_GEOMETRY_SOURCE_REQUIRED");
  if(!truth(g.crs_ref)||!truth(g.coordinate_unit))
    flags.push("COORDINATE_FRAME_AND_UNITS_REQUIRED");
  if(!truth(g.time_frame_ref))flags.push("GEOMETRY_TIME_FRAME_REQUIRED");
  if(g.dimension===3&&!truth(g.vertical_datum_ref))
    flags.push("VERTICAL_DATUM_REQUIRED_FOR_3D");
  if(!truth(g.spatial_review_ref))flags.push("SENSITIVE_LOCATION_REVIEW_REQUIRED");
  if(!truth(g.rights_review_ref)||!truth(g.stewardship_review_ref))
    flags.push("GEOMETRY_RIGHTS_AND_STEWARDSHIP_REVIEW_REQUIRED");
  return {
    state:flags.length>1?"INCOMPLETE_SOURCE_GEOMETRY_DESCRIPTOR":"REFERENCES_STAGED_NOT_ACCEPTED",
    kind:g.kind,dimension:g.dimension,
    source_geometry_ref_present:truth(g.source_geometry_ref),
    crs_ref_present:truth(g.crs_ref),
    time_frame_ref_present:truth(g.time_frame_ref),
    actual_geometry_loaded:false,metric_geometry_validated:false,
    spatial_release_authorised:false,flags
  };
}

/**
 * Link an independently identified original to an embedded/translated reference
 * without treating a source manifest's "verified" label as byte equivalence.
 * This deliberately does not dereference the related provider, attest rights,
 * mint identities or return protected source contents.
 */
function reviewSourceLineage(link,source){
  if(link===null)return {state:"NO_RELATED_SOURCE_REQUESTED"};
  const allowed=new Set(["source_ref","related_source_ref","relation_kind",
    "manifest_location_ref","manifest_source_sha256",
    "related_revision_ref","claimed_translation_state"]);
  const kinds=new Set(["embedded_translation","source_manifest_reference",
    "claimed_duplicate","derived_view"]);
  if(!obj(link)||Object.keys(link).some(k=>!allowed.has(k))||
     link.source_ref!==source.source_ref||
     !token(link.related_source_ref)||link.related_source_ref===source.source_ref||
     !kinds.has(link.relation_kind)||!token(link.manifest_location_ref)||
     typeof link.manifest_source_sha256!=="string"||
     !SHA.test(link.manifest_source_sha256)||
     (link.related_revision_ref!==undefined&&!token(link.related_revision_ref))||
     (link.claimed_translation_state!==undefined&&
      !token(link.claimed_translation_state)))
    throw Error("INVALID_ECO_SOURCE_LINEAGE");
  const hashMatches=source.proof_hash!==null&&
    link.manifest_source_sha256.toLowerCase()===source.proof_hash;
  if(source.proof_hash!==null&&!hashMatches)
    throw Error("ECO_LINEAGE_MANIFEST_SOURCE_HASH_MISMATCH");
  return {
    state:"R1_SOURCE_LINEAGE_CANDIDATE_NOT_EQUIVALENCE",
    relation_kind:link.relation_kind,source_ref:source.source_ref,
    related_source_ref:link.related_source_ref,
    manifest_location_ref:link.manifest_location_ref,
    related_revision_ref:link.related_revision_ref??null,
    claimed_translation_state:link.claimed_translation_state??null,
    manifest_source_hash_matches_original_bytes_this_execution:hashMatches,
    related_source_bytes_read_this_execution:false,
    related_source_hash_verified_this_execution:false,
    related_provider_revision_authenticated_by_module:false,
    related_source_rights_verified:false,
    byte_equivalence_verified:false,related_source_native_admitted:false,
    original_preserved:true,public_release_authorised:false
  };
}

function reviewCellAnchor(anchor,source){
  if(anchor===null)return {state:"SOURCE_CELL_ANCHOR_REQUIRED",
    sheet_ref:null,cell_ref:null,declared_anchor_matched:false,
    source_cell_bytes_reread:false,formula_verified:false};
  if(!obj(anchor)||Object.keys(anchor).some(k=>![
      "source_ref","source_revision","source_sha256","sheet","cell"].includes(k))||
      anchor.source_ref!==source.source_ref||
      anchor.source_revision!==source.revision||
      !token(anchor.sheet)||anchor.sheet.length>64||
      !/^[A-Z]{1,3}[1-9]\d{0,6}$/.test(anchor.cell)||
      typeof anchor.source_sha256!=="string"||!SHA.test(anchor.source_sha256))
    throw Error("INVALID_ECO_CELL_ANCHOR");
  if(!source.proof_hash||anchor.source_sha256.toLowerCase()!==source.proof_hash)
    throw Error("ECO_CELL_ANCHOR_UNVERIFIED_SOURCE_DIGEST");
  return {state:"DECLARED_CELL_ANCHOR_NOT_CROSS_READ",sheet_ref:anchor.sheet,
    cell_ref:anchor.cell,declared_anchor_matched:true,
    source_cell_bytes_reread:false,formula_verified:false};
}

/**
 * Accept a review input, never an externally asserted "passed" receipt.
 * A fresh integrated cascade execution generates all actual executed flags.
 */
export function prepareEcoPreMintAssembly(request={}){
  if(!obj(request)||Object.keys(request).some(k=>![
    "cascade_input","geometry_descriptor","cell_anchor",
    "requested_hydration","observation_showcase","source_lineage"].includes(k)))
    throw Error("INVALID_ECO_PRE_MINT_REQUEST");
  const {cascade_input,geometry_descriptor=null,cell_anchor=null,
    requested_hydration="H3",observation_showcase=null,source_lineage=null}=request;
  if(!obj(cascade_input)||!levels.includes(requested_hydration))
    throw Error("INVALID_ECO_PRE_MINT_REQUEST");
  const executed=runEcoReviewCascade(cascade_input);
  if(executed.family!=="Cognigrex.cgx/Eco.cgx"||
     executed.stage!=="R1_REVIEW_ONLY"||
     executed.step_receipts.scoped_alignment.executed!==true||
     executed.step_receipts.ecological_review.executed!==true)
    throw Error("ECO_EXECUTED_REVIEW_CONTRACT_MISMATCH");
  const level=levels.indexOf(requested_hydration);
  const source={source_ref:executed.source_reference.source_ref,
    revision:executed.source_reference.revision,
    proof_hash:executed.source_proof?.sha256??null};
  const geom=reviewGeometryDescriptor(geometry_descriptor,source.source_ref);
  const anchor=reviewCellAnchor(cell_anchor,source);
  const lineage=reviewSourceLineage(source_lineage,source);
  let showcase=null;
  if(observation_showcase!==null){
    if(!obj(observation_showcase)||
       observation_showcase.source_provenance!==source.source_ref||
       observation_showcase.source_revision_ref!==source.revision||
       observation_showcase.evidence_class!==executed.evidence_class||
       (source.proof_hash!==null&&
        (typeof observation_showcase.source_hash_sha256!=="string"||
         observation_showcase.source_hash_sha256.toLowerCase()!==source.proof_hash)))
      throw Error("ECO_MINT_SHOWCASE_SOURCE_OR_EVIDENCE_CONFLICT");
    showcase=reviewEcoObservationShowcase({
      record:observation_showcase,
      authorised_source_refs:[source.source_ref],
      public_release_requested:false
    });
    if(showcase.checks.includes("RAW_SPATIAL_COORDINATES_NOT_ACCEPTED_IN_SOURCE_ONLY_BRIDGE")||
       showcase.checks.includes("SPATIAL_PAYLOAD_REVIEW_LIMIT_EXCEEDED"))
      throw Error("ECO_MINT_SHOWCASE_SPATIAL_PAYLOAD_HOLD");
  }
  const blockers=["CANONICAL_OBJECT_ID_NOT_MINTED","SIGNED_ROOT_AND_DBR_READBACK_REQUIRED",
    "SOURCE_RIGHTS_ACL_AND_STEWARDSHIP_NOT_VERIFIED",
    "INDEPENDENT_SCIENCE_AND_PHYSICAL_GEOMETRY_NOT_VERIFIED",
    "ISSUE_158_PUBLIC_STATIC_PRIVACY_HOLD",
    "ISSUE_161_TWO_NODE_DATASPACE_HOLD","ISSUE_209_SCIENTIFIC_OUTPUT_HOLD"];
  if(!executed.source_reference.hash_verified_this_execution)
    blockers.push("ORIGINAL_BYTES_NOT_HASHED_IN_THIS_EXECUTION");
  if(anchor.state!=="DECLARED_CELL_ANCHOR_NOT_CROSS_READ")
    blockers.push("SOURCE_CELL_ANCHOR_MISSING");
  if(geom.state!=="REFERENCES_STAGED_NOT_ACCEPTED")
    blockers.push("GEOMETRY_SOURCE_FRAME_OR_REVIEW_INCOMPLETE");
  if(source_lineage!==null)
    blockers.push("RELATED_SOURCE_LINEAGE_NOT_INDEPENDENTLY_VERIFIED");
  if(showcase!==null)
    blockers.push("ECO_OBSERVATION_SHOWCASE_NOT_NATIVE_MINT_OR_FIELD_EVIDENCE");

  const hydrate={
    H0:{state:"CANDIDATE_IDENTITY_ONLY",family:executed.family,
      object_id:null,source_ref:source.source_ref},
    H1:level>=1?{state:"TYPED_REVIEW_EXECUTED",
      evidence_class:executed.evidence_class,
      domain:cascade_input.domain,source_cell:anchor,
      qualified_alignment_state:executed.step_receipts.scoped_alignment.state}
      :{state:"NOT_REQUESTED"},
    H2:level>=2?{state:source.proof_hash?"HASHED_SOURCE_REFERENCE_ONLY":"SOURCE_HASH_UNVERIFIED",
      source_provider:executed.source_reference.provider,
      source_id:executed.source_reference.id,source_revision:source.revision,
      source_sha256:source.proof_hash,
      bytes_read_and_hashed_this_execution:executed.source_reference.hash_verified_this_execution,
      source_provider_authenticated_by_module:false,
      source_rights_verified:false}
      :{state:"NOT_REQUESTED"},
    H3:level>=3?{state:"EXECUTED_REVIEW_ROUTE_NOT_RUNTIME_CAPABILITY",
      executed_review_module:ROUTES[cascade_input.domain],
      eco_alignment_executed:true,
      actual_ccc_registration:false,installed_operator:false}
      :{state:"NOT_REQUESTED"},
    H4:{state:"DENIED_PENDING_NATIVE_ACL_AND_ROOT_ADMISSION",
      source_bytes_emitted:false,geometry_emitted:false,
      host_tool_invoked:false}
  };
  return {
    schema:ECO_PRE_MINT_SCHEMA,parent:"Cognigrex.cgx",
    file_space_candidate:"Eco.cgx",owner_lane:"Athene",
    candidate_family_path:"Cognigrex.cgx/Eco.cgx",
    draft_mint_target:"SOURCE_QUALIFIED_ECO_REVIEW_CANDIDATE",
    candidate_object_id:null,requested_hydration,
    stage:"R1_PRE_MINT_REVIEW_PACKET",canonical_write:false,
    source_original_preserved:true,source_bytes_embedded:false,
    evidence_class:executed.evidence_class,
    factual_outcome_verified:false,
    executed_review:{schema:executed.schema,
      alignment:executed.step_receipts.scoped_alignment,
      ecological_review:executed.step_receipts.ecological_review},
    hydration:hydrate,geomatrix:geom,
    source_lineage_review:level>=2?lineage:{state:"NOT_REQUESTED"},
    mint_showcase_review:level>=3&&showcase!==null?{
      schema:showcase.schema,state:showcase.state,
      checks:showcase.checks,
      field_observation_verified:false,native_object_id:null,
      public_release_authorised:false,geometry_emitted:false
    }:{state:"NOT_REQUESTED_OR_NOT_SUPPLIED"},
    stack_layers:[
      {layer:"source",state:source.proof_hash?"HASH_REFERENCE_VERIFIED":"R0_UNVERIFIED_THIS_RUN"},
      {layer:"lineage",state:level>=2?lineage.state:"NOT_REQUESTED"},
      {layer:"semantic",state:"R1_REVIEW_ONLY"},
      {layer:"geometry",state:geom.state},
      {layer:"temporal",state:geom.time_frame_ref_present?"REFERENCE_ONLY":"MISSING_SOURCE_TIME_FRAME"},
      {layer:"capability",state:level>=3?"REVIEW_FUNCTION_EXECUTED":"NOT_REQUESTED"},
      {layer:"native",state:"NOT_ADMITTED"}
    ],
    loss_ledger:["RAW_WORKBOOK_OR_PDF_BYTES_NOT_REPRODUCED",
      "NO_SOURCE_CELL_CONTENT_OR_FORMULA_READBACK",
      "NO_METRIC_GEOMETRY_OR_CRS_TRANSFORM",
      "NO_R2_ONTOLOGY_OR_NATIVE_OBJECT_ID_PROOF",
      "NO_NATIVE_CCC_INSTALL_OR_DATASPACE_SYNC",
      "NO_RELATED_SOURCE_BYTE_EQUIVALENCE_OR_OWNER_PERMISSION_PROOF"],
    blocking_gates:[...new Set(blockers.concat(geom.flags))],
    permissions:{file_space_write:false,data_space_write:false,
      device_automation:false,public_publish:false,
      physical_actuation:false,token_transaction:false},
    release:{mint_allowed:false,db_readback:false,
      installed:false,live_verified:false,owner_accepted:false,
      public_release_authorised:false},
    next_gate:"OWNER_RIGHTS_AND_NATIVE_ROOT_DBR_PLUS_INDEPENDENT_MODEL_GEOMETRY_QA"
  };
}
