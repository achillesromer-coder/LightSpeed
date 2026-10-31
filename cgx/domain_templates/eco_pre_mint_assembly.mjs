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

/**
 * Read-only, caller-declared Drive permission snapshot. Metadata is not an
 * owner rights grant, provider-authenticated receipt or publication licence.
 * Only permission classes are emitted; no user identities or raw ACLs.
 */
function reviewAccessPosture(posture,source){
  if(posture===null)return {state:"ACCESS_POSTURE_NOT_SUPPLIED",
    provider_authenticated_by_module:false,rights_approved:false,
    public_release_authorised:false,
    flags:["CURRENT_PROVIDER_ACL_READBACK_REQUIRED"]};
  const types=new Set(["anyone","user","group","domain"]);
  const roles=new Set(["owner","writer","reader","commenter","organizer","fileOrganizer"]);
  if(!obj(posture)||Object.keys(posture).some(k=>![
      "source_ref","source_id","provider_observation_ref","permissions"].includes(k))||
      posture.source_ref!==source.source_ref||
      posture.source_id!==source.id||
      !token(posture.provider_observation_ref)||
      !Array.isArray(posture.permissions)||posture.permissions.length>100||
      posture.permissions.some(p=>!obj(p)||
        Object.keys(p).some(k=>!["type","role","allowFileDiscovery"].includes(k))||
        !types.has(p.type)||!roles.has(p.role)||
        (p.allowFileDiscovery!==undefined&&p.allowFileDiscovery!==null&&
         typeof p.allowFileDiscovery!=="boolean")))
    throw Error("INVALID_ECO_ACCESS_POSTURE");
  const anyone=posture.permissions.filter(p=>p.type==="anyone");
  const broad=posture.permissions.some(p=>p.type==="domain"||p.type==="group");
  const flags=["CALLER_ACL_SNAPSHOT_NOT_AUTHENTICATED_BY_MODULE",
    "SOURCE_REUSE_RIGHTS_AND_OWNER_APPROVAL_REQUIRED"];
  if(anyone.length)flags.push("ANYONE_LINK_ACCESS_PRESENT_NOT_PUBLICATION_LICENCE");
  if(anyone.some(p=>p.role!=="reader"&&p.role!=="commenter"))
    flags.push("ANYONE_WRITE_OR_ADMIN_PERMISSION_REVIEW_REQUIRED");
  if(anyone.some(p=>p.allowFileDiscovery===false))
    flags.push("NON_DISCOVERABLE_LINK_STILL_ACCESSIBLE_TO_LINK_HOLDERS");
  if(broad)flags.push("GROUP_OR_DOMAIN_SCOPE_REVIEW_REQUIRED");
  if(!anyone.length)flags.push("NO_ANYONE_ENTRY_DOES_NOT_PROVE_PRIVATE");
  return {state:"DECLARED_ACCESS_POSTURE_REVIEW_ONLY",
    anyone_link_present:anyone.length>0,
    broad_group_or_domain_present:broad,
    provider_authenticated_by_module:false,
    current_provider_acl_readback_verified_by_module:false,
    source_reuse_rights_verified:false,
    rights_approved:false,public_release_authorised:false,
    flags};
}


/**
 * Compare caller-declared ACL classes for an original and a translated source.
 * A permission-class match is NOT ACL equivalence, provider attestation,
 * licence, rights approval, or permission to publish.
 */
function reviewRelatedAccessPosture(related,original,lineage,source){
  if(related===null)return {state:"RELATED_ACCESS_POSTURE_NOT_SUPPLIED",
    provider_authenticated_by_module:false,acl_equivalent:false,
    rights_approved:false,public_release_authorised:false};
  if(!obj(lineage)||!obj(original)||!obj(related)||
     Object.keys(related).some(k=>![
       "source_ref","source_id","source_revision",
       "provider_observation_ref","permissions"].includes(k))||
     related.source_ref!==lineage.related_source_ref||
     related.source_revision!==lineage.related_revision_ref||
     !token(related.source_id))
    throw Error("INVALID_ECO_RELATED_ACCESS_POSTURE");
  const a=reviewAccessPosture(original,source);
  const b=reviewAccessPosture({
    source_ref:related.source_ref,source_id:related.source_id,
    provider_observation_ref:related.provider_observation_ref,
    permissions:related.permissions
  },{source_ref:lineage.related_source_ref,id:related.source_id});
  const divergent=a.anyone_link_present!==b.anyone_link_present||
    a.broad_group_or_domain_present!==b.broad_group_or_domain_present;
  return {
    state:divergent?"R1_DECLARED_ACCESS_POSTURE_DIVERGENCE_HOLD":
      "R1_DECLARED_ACCESS_CLASSES_MATCH_NOT_EQUIVALENCE",
    original_anyone_link_present:a.anyone_link_present,
    related_anyone_link_present:b.anyone_link_present,
    original_broad_group_or_domain_present:a.broad_group_or_domain_present,
    related_broad_group_or_domain_present:b.broad_group_or_domain_present,
    access_classes_divergent:divergent,
    provider_authenticated_by_module:false,
    related_provider_revision_authenticated_by_module:false,
    independent_acl_readback_verified:false,
    acl_equivalent:false,source_reuse_rights_verified:false,
    rights_approved:false,public_release_authorised:false
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
 * Pairwise cell crosswalk for an original workbook and an independently
 * identified translated Sheet. The caller supplies bounded cell observations
 * from its authenticated provider boundary. This module does NOT fetch either
 * provider, attest the observations, or establish workbook equivalence.
 * Only comparison flags are returned; no formulas or cell values are emitted.
 */
function reviewCellCrosswalk(pair,source,anchor,lineage,evidenceClass){
  if(pair===null)return {state:"CELL_CROSSWALK_NOT_SUPPLIED",
    caller_declared_pair_compared:false,provider_cells_fetched_by_module:false,
    original_and_translation_equivalent:false};
  const allowed=new Set(["source_ref","source_revision","source_sha256",
    "related_source_ref","related_revision_ref","original_cell","related_cell"]);
  const cellAllowed=new Set(["sheet","cell","formula","unit","numeric_value",
    "evidence_class"]);
  const validCell=c=>obj(c)&&Object.keys(c).every(k=>cellAllowed.has(k))&&
    token(c.sheet)&&c.sheet.length<=64&&
    /^[A-Z]{1,3}[1-9]\d{0,6}$/.test(c.cell)&&
    typeof c.formula==="string"&&
    /^=[A-Za-z0-9+*\/(). ^-]{1,128}$/.test(c.formula)&&
    token(c.unit)&&c.unit.length<=32&&
    Number.isFinite(c.numeric_value)&&Math.abs(c.numeric_value)<=1e12&&
    c.evidence_class===evidenceClass;
  if(!obj(pair)||Object.keys(pair).some(k=>!allowed.has(k))||
    !source.proof_hash||!obj(anchor)||!obj(lineage)||
    pair.source_ref!==source.source_ref||
    pair.source_revision!==source.revision||
    pair.source_sha256!==source.proof_hash||
    pair.related_source_ref!==lineage.related_source_ref||
    pair.related_revision_ref!==lineage.related_revision_ref||
    !validCell(pair.original_cell)||!validCell(pair.related_cell)||
    pair.original_cell.sheet!==anchor.sheet||
    pair.original_cell.cell!==anchor.cell)
    throw Error("INVALID_ECO_SOURCE_CELL_CROSSWALK");
  const a=pair.original_cell,b=pair.related_cell;
  const formulaMatch=a.formula===b.formula;
  const unitMatch=a.unit===b.unit;
  // Common UTF-8/Latin-1 mojibake must not qualify as a physical unit,
  // even if the original and translated strings happen to be identical.
  const unitEncodingValid=!/[ÂÃ�]/.test(a.unit+b.unit);
  const scale=Math.max(1,Math.abs(a.numeric_value),Math.abs(b.numeric_value));
  const valueMatch=Math.abs(a.numeric_value-b.numeric_value)<=1e-10*scale;
  const consistent=formulaMatch&&unitMatch&&unitEncodingValid&&valueMatch;
  return {
    state:consistent?"R1_CALLER_DECLARED_PAIRWISE_MATCH_NOT_EQUIVALENCE":
      "R1_CALLER_DECLARED_CELL_DISCREPANCY_HOLD",
    original_anchor_ref:anchor.sheet+"!"+anchor.cell,
    related_cell_ref:b.sheet+"!"+b.cell,
    formula_match:formulaMatch,unit_match:unitMatch,
    unit_encoding_valid:unitEncodingValid,
    numeric_value_match:valueMatch,evidence_class_match:true,
    caller_declared_pair_compared:true,
    provider_cells_fetched_by_module:false,
    provider_origin_authenticated_by_module:false,
    independent_cell_readback_verified:false,
    original_and_translation_equivalent:false,
    source_rights_verified:false,geometry_validated:false,
    field_outcome_verified:false,native_admitted:false
  };
}

/**
 * R1 source/translation crosswalk for human-readable symbolic expressions.
 * Unlike executable spreadsheet formulas, these are source-authored text
 * (e.g. scientific notation). Do not silently repair mojibake or infer
 * formula correctness. Raw expression strings are never returned.
 */
function reviewSymbolicExpressionCrosswalk(pair,source,anchor,lineage,evidenceClass){
  if(pair===null)return {state:"SYMBOLIC_EXPRESSION_CROSSWALK_NOT_SUPPLIED",
    caller_declared_pair_compared:false,provider_cells_fetched_by_module:false,
    scientific_equivalence_verified:false};
  const allowed=new Set(["source_ref","source_revision","source_sha256",
    "related_source_ref","related_revision_ref","original_cell","related_cell"]);
  const cellAllowed=new Set(["sheet","cell","expression_text","evidence_class"]);
  const validCell=c=>obj(c)&&Object.keys(c).every(k=>cellAllowed.has(k))&&
    token(c.sheet)&&c.sheet.length<=64&&
    /^[A-Z]{1,3}[1-9]\d{0,6}$/.test(c.cell)&&
    token(c.expression_text)&&c.expression_text.length<=256&&
    c.evidence_class===evidenceClass;
  if(!obj(pair)||Object.keys(pair).some(k=>!allowed.has(k))||
    !source.proof_hash||!obj(anchor)||!obj(lineage)||
    pair.source_ref!==source.source_ref||
    pair.source_revision!==source.revision||
    pair.source_sha256!==source.proof_hash||
    pair.related_source_ref!==lineage.related_source_ref||
    pair.related_revision_ref!==lineage.related_revision_ref||
    !validCell(pair.original_cell)||!validCell(pair.related_cell)||
    pair.original_cell.sheet!==anchor.sheet||
    pair.original_cell.cell!==anchor.cell)
    throw Error("INVALID_ECO_SYMBOLIC_EXPRESSION_CROSSWALK");
  const a=pair.original_cell,b=pair.related_cell;
  // Review flag only; Unicode symbols in the original remain unchanged.
  const suspectedMojibake=s=>/[\u00c2\u00c3\u00cf\ufffd]/u.test(s);
  const originalEncodingValid=!suspectedMojibake(a.expression_text);
  const relatedEncodingValid=!suspectedMojibake(b.expression_text);
  const textMatch=a.expression_text===b.expression_text;
  const consistent=originalEncodingValid&&relatedEncodingValid&&textMatch;
  return {
    state:consistent?"R1_CALLER_DECLARED_SYMBOLIC_TEXT_MATCH_NOT_EQUIVALENCE":
      "R1_CALLER_DECLARED_SYMBOLIC_EXPRESSION_DISCREPANCY_HOLD",
    original_anchor_ref:anchor.sheet+"!"+anchor.cell,
    related_cell_ref:b.sheet+"!"+b.cell,
    expression_text_match:textMatch,
    original_encoding_valid:originalEncodingValid,
    related_encoding_valid:relatedEncodingValid,
    caller_declared_pair_compared:true,
    provider_cells_fetched_by_module:false,
    provider_origin_authenticated_by_module:false,
    independent_cell_readback_verified:false,
    scientific_equivalence_verified:false,
    source_rights_verified:false,native_admitted:false,
    public_release_authorised:false
  };
}

/**
 * Compare formula ID inventories observed by the caller at the authenticated
 * original/translated provider boundary. Added translation-only entries are
 * NOT retroactively part of the original workbook or independent evidence.
 * The module cannot attest either provider read, formula, or physics.
 */
function reviewFormulaInventoryDelta(inventory,source,lineage){
  if(inventory===null)return {state:"FORMULA_INVENTORY_NOT_SUPPLIED",
    provider_cells_fetched_by_module:false,original_and_translation_equivalent:false};
  const keys=new Set(["source_ref","source_revision","source_sha256",
    "related_source_ref","related_revision_ref","original_ids","related_ids"]);
  const ids=a=>Array.isArray(a)&&a.length>0&&a.length<=128&&
    a.every(x=>typeof x==="string"&&/^FM-[0-9]{3}$/.test(x))&&
    new Set(a).size===a.length;
  if(!obj(inventory)||Object.keys(inventory).some(k=>!keys.has(k))||
    !obj(lineage)||!source.proof_hash||
    inventory.source_ref!==source.source_ref||
    inventory.source_revision!==source.revision||
    inventory.source_sha256!==source.proof_hash||
    inventory.related_source_ref!==lineage.related_source_ref||
    inventory.related_revision_ref!==lineage.related_revision_ref||
    !ids(inventory.original_ids)||!ids(inventory.related_ids))
    throw Error("INVALID_ECO_FORMULA_INVENTORY");
  const original=new Set(inventory.original_ids);
  const related=new Set(inventory.related_ids);
  const added=[...related].filter(id=>!original.has(id)).sort();
  const missing=[...original].filter(id=>!related.has(id)).sort();
  const divergent=added.length>0||missing.length>0;
  return {
    state:divergent?"R1_TRANSLATION_FORMULA_INVENTORY_DELTA_HOLD":
      "R1_CALLER_DECLARED_FORMULA_IDS_MATCH_NOT_EQUIVALENCE",
    original_formula_count:original.size,related_formula_count:related.size,
    added_related_formula_ids:added,missing_related_formula_ids:missing,
    original_formula_ids_in_related:[...original].filter(id=>related.has(id)).length,
    translation_only_entries_not_original_evidence:added.length>0,
    caller_declared_inventory_compared:true,
    provider_cells_fetched_by_module:false,
    original_formula_inventory_authenticated_by_module:false,
    related_formula_inventory_authenticated_by_module:false,
    formula_semantics_validated:false,independent_physics_validated:false,
    original_and_translation_equivalent:false,
    source_rights_verified:false,native_admitted:false,
    public_release_authorised:false
  };
}

/**
 * Accept a review input, never an externally asserted "passed" receipt.
 * A fresh integrated cascade execution generates all actual executed flags.
 */
export function prepareEcoPreMintAssembly(request={}){
  if(!obj(request)||Object.keys(request).some(k=>![
    "cascade_input","geometry_descriptor","cell_anchor",
    "requested_hydration","observation_showcase","source_lineage","access_posture",
    "related_access_posture","cell_crosswalk",
    "symbolic_expression_crosswalk","formula_inventory"].includes(k)))
    throw Error("INVALID_ECO_PRE_MINT_REQUEST");
  const {cascade_input,geometry_descriptor=null,cell_anchor=null,
    requested_hydration="H3",observation_showcase=null,source_lineage=null,
    access_posture=null,related_access_posture=null,cell_crosswalk=null,
    symbolic_expression_crosswalk=null,formula_inventory=null}=request;
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
  const access=reviewAccessPosture(access_posture,{...source,id:executed.source_reference.id});
  const relatedAccess=reviewRelatedAccessPosture(related_access_posture,
    access_posture,source_lineage,{...source,id:executed.source_reference.id});
  const pair=reviewCellCrosswalk(cell_crosswalk,source,cell_anchor,source_lineage,executed.evidence_class);
  const symbolic=reviewSymbolicExpressionCrosswalk(symbolic_expression_crosswalk,
    source,cell_anchor,source_lineage,executed.evidence_class);
  const formulaInventory=reviewFormulaInventoryDelta(formula_inventory,source,source_lineage);
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
  if(cell_crosswalk!==null){
    blockers.push("CELL_CROSSWALK_PROVIDER_ATTESTATION_AND_FULL_EQUIVALENCE_REQUIRED");
    if(pair.state==="R1_CALLER_DECLARED_CELL_DISCREPANCY_HOLD")
      blockers.push("SOURCE_TRANSLATION_CELL_DISCREPANCY");
  }
  if(symbolic_expression_crosswalk!==null){
    blockers.push("SYMBOLIC_EXPRESSION_PROVIDER_ATTESTATION_REQUIRED");
    if(symbolic.state==="R1_CALLER_DECLARED_SYMBOLIC_EXPRESSION_DISCREPANCY_HOLD")
      blockers.push("SOURCE_TRANSLATION_SYMBOLIC_EXPRESSION_DISCREPANCY");
  }
  if(formula_inventory!==null){
    blockers.push("FORMULA_INVENTORY_PROVIDER_ATTESTATION_REQUIRED");
    if(formulaInventory.state==="R1_TRANSLATION_FORMULA_INVENTORY_DELTA_HOLD")
      blockers.push("TRANSLATION_FORMULA_LIBRARY_DELTA_REQUIRES_PROVENANCE");
  }
  if(access_posture!==null)
    blockers.push("DECLARED_SOURCE_ACCESS_POSTURE_NOT_RIGHTS_APPROVAL");
  if(related_access_posture!==null){
    blockers.push("PAIRWISE_ACCESS_POSTURES_NOT_INDEPENDENTLY_ATTESTED");
    if(relatedAccess.access_classes_divergent)
      blockers.push("SOURCE_TRANSLATION_ACCESS_POSTURE_DIVERGENCE");
  }
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
    source_cell_crosswalk_review:level>=2?pair:{state:"NOT_REQUESTED"},
    source_symbolic_expression_crosswalk_review:level>=2?symbolic:{state:"NOT_REQUESTED"},
    formula_inventory_review:level>=2?formulaInventory:{state:"NOT_REQUESTED"},
    access_posture_review:level>=2?access:{state:"NOT_REQUESTED"},
    related_access_posture_review:level>=2?relatedAccess:{state:"NOT_REQUESTED"},
    mint_showcase_review:level>=3&&showcase!==null?{
      schema:showcase.schema,state:showcase.state,
      checks:showcase.checks,
      field_observation_verified:false,native_object_id:null,
      public_release_authorised:false,geometry_emitted:false
    }:{state:"NOT_REQUESTED_OR_NOT_SUPPLIED"},
    stack_layers:[
      {layer:"source",state:source.proof_hash?"HASH_REFERENCE_VERIFIED":"R0_UNVERIFIED_THIS_RUN"},
      {layer:"lineage",state:level>=2?lineage.state:"NOT_REQUESTED"},
      {layer:"access",state:level>=2?access.state:"NOT_REQUESTED"},
      {layer:"related_access",state:level>=2?relatedAccess.state:"NOT_REQUESTED"},
      {layer:"cell_crosswalk",state:level>=2?pair.state:"NOT_REQUESTED"},
      {layer:"symbolic_expression",state:level>=2?symbolic.state:"NOT_REQUESTED"},
      {layer:"formula_inventory",state:level>=2?formulaInventory.state:"NOT_REQUESTED"},
      {layer:"semantic",state:"R1_REVIEW_ONLY"},
      {layer:"geometry",state:geom.state},
      {layer:"temporal",state:geom.time_frame_ref_present?"REFERENCE_ONLY":"MISSING_SOURCE_TIME_FRAME"},
      {layer:"capability",state:level>=3?"REVIEW_FUNCTION_EXECUTED":"NOT_REQUESTED"},
      {layer:"native",state:"NOT_ADMITTED"}
    ],
    loss_ledger:["RAW_WORKBOOK_OR_PDF_BYTES_NOT_REPRODUCED",
      "NO_SOURCE_CELL_CONTENT_OR_FORMULA_READBACK",
      "CALLER_DECLARED_PAIRWISE_CELLS_NOT_INDEPENDENT_PROVIDER_ATTESTATION",
      "SYMBOLIC_EXPRESSION_TEXT_NOT_INDEPENDENTLY_VERIFIED_OR_REPAIRED",
      "NO_METRIC_GEOMETRY_OR_CRS_TRANSFORM",
      "NO_R2_ONTOLOGY_OR_NATIVE_OBJECT_ID_PROOF",
      "NO_NATIVE_CCC_INSTALL_OR_DATASPACE_SYNC",
      "NO_RELATED_SOURCE_BYTE_EQUIVALENCE_OR_OWNER_PERMISSION_PROOF",
      "NO_INDEPENDENT_ACL_RIGHTS_ATTESTATION",
      "NO_PAIRWISE_PROVIDER_ACL_EQUIVALENCE_PROOF"],
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
