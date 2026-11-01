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
import {reviewSecondCycleCoefficientRoles} from "./eco_second_cycle_claim_review.mjs";

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
 * Strict caller-text roundtrip candidate for three observed Unicode mojibake
 * sequences. Never edits source cells or treats text recovery as physical or
 * scientific equivalence. Unrecognised substitutions fail closed.
 */
function reviewDeclaredSymbolRoundtrip(original,related){
  const replacements=[["Ã—","×"],["Ï","ρ"],["Â²","²"]];
  let decoded=related,encoded=original,changed=false;
  for(const [broken,correct] of replacements){
    if(decoded.includes(broken))changed=true;
    decoded=decoded.split(broken).join(correct);
    encoded=encoded.split(correct).join(broken);
  }
  const candidate=changed&&decoded===original&&encoded===related;
  return {
    state:candidate?"R1_CALLER_TEXT_ROUNDTRIP_CANDIDATE":
      "NO_LOSSLESS_DECLARED_ENCODING_TRANSFORM",
    caller_text_roundtrip_candidate:candidate,
    transform_scope:"THREE_OBSERVED_UNICODE_MOJIBAKE_SEQUENCES_ONLY",
    provider_cells_verified:false,source_bytes_embedded:false,
    source_or_translation_modified:false,
    scientific_equivalence_verified:false,native_admitted:false
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
 * Attach a PRIVATE original-cell receipt to the existing Eco review chain.
 * Only caller-declared hashes and A1 anchors cross this boundary. The module
 * does not read the receipt, source cells, related provider, rights or DBR.
 * This is NOT issuer attestation, translation equivalence or an R2 model.
 */
function reviewDeclaredOriginalCellDigestCrosswalk(packet,source,lineage,evidenceClass){
  if(packet===null)return {state:"ORIGINAL_CELL_DIGEST_RECEIPT_NOT_SUPPLIED",
    independent_receipt_readback:false,original_cells_reread:false,
    native_admitted:false};
  const keys=new Set(["source_ref","source_revision","source_sha256",
    "related_source_ref","related_revision_ref","receipt_ref","receipt_sha256",
    "evidence_class","entries","translation_only_ids","unit_defect_refs"]);
  const entryKeys=new Set(["formula_id","original_anchor","translated_anchor",
    "original_text_sha256","translated_text_sha256","status",
    "original_id_anchor","translated_id_anchor"]);
  const cell=/^[A-Za-z0-9_]{1,64}![A-Z]{1,3}[1-9]\d{0,6}$/;
  const expression=/^[A-Za-z0-9_]{1,64}!B([1-9]\d{0,6})$/;
  const allowedStatuses=new Set(["TEXT_EXACT","REVERSIBLE_ENCODING_CANDIDATE"]);
  if(!obj(packet)||Object.keys(packet).some(k=>!keys.has(k))||
     !source.proof_hash||!obj(lineage)||
     packet.source_ref!==source.source_ref||
     packet.source_revision!==source.revision||
     packet.source_sha256!==source.proof_hash||
     packet.related_source_ref!==lineage.related_source_ref||
     packet.related_revision_ref!==lineage.related_revision_ref||
     packet.evidence_class!==evidenceClass||
     !token(packet.receipt_ref)||!SHA.test(packet.receipt_sha256)||
     !Array.isArray(packet.entries)||packet.entries.length<1||
     packet.entries.length>32||
     !Array.isArray(packet.translation_only_ids)||
     packet.translation_only_ids.length>32||
     !Array.isArray(packet.unit_defect_refs)||packet.unit_defect_refs.length>16)
    throw Error("INVALID_ECO_ORIGINAL_CELL_DIGEST_CROSSWALK");
  // Address binding is caller-declared only: A-row formula IDs must sit
  // beside the hashed B-row expressions in both independent sources.
  const rowBound=(idAnchor,expressionAnchor)=>{
    const m=/^([A-Za-z0-9_]{1,64})!B([1-9]\d{0,6})$/.exec(expressionAnchor);
    return Boolean(m)&&idAnchor===m[1]+"!A"+m[2];
  };
  const seen=new Set(),originalAnchors=new Set(),relatedAnchors=new Set();
  const records=[];
  for(const e of packet.entries){
    if(!obj(e)||Object.keys(e).some(k=>!entryKeys.has(k))||
       !/^FM-[0-9]{3}$/.test(e.formula_id)||
       !expression.test(e.original_anchor)||
       !expression.test(e.translated_anchor)||
       !SHA.test(e.original_text_sha256)||!SHA.test(e.translated_text_sha256)||
       !allowedStatuses.has(e.status)||
       seen.has(e.formula_id)||originalAnchors.has(e.original_anchor)||
       relatedAnchors.has(e.translated_anchor))
      throw Error("INVALID_ECO_ORIGINAL_CELL_DIGEST_ENTRY");
    const equal=e.original_text_sha256.toLowerCase()===
      e.translated_text_sha256.toLowerCase();
    if((e.status==="TEXT_EXACT")!==equal)
      throw Error("ECO_ORIGINAL_CELL_DIGEST_STATUS_CONFLICT");
    const bound=e.original_id_anchor!==undefined&&
      e.translated_id_anchor!==undefined;
    if((e.original_id_anchor===undefined)!==
         (e.translated_id_anchor===undefined)||
       (bound&&(!rowBound(e.original_id_anchor,e.original_anchor)||
                !rowBound(e.translated_id_anchor,e.translated_anchor))))
      throw Error("ECO_ORIGINAL_CELL_DIGEST_FORMULA_ID_ROW_BINDING_CONFLICT");
    seen.add(e.formula_id);originalAnchors.add(e.original_anchor);
    relatedAnchors.add(e.translated_anchor);
    records.push({formula_id:e.formula_id,
      original_anchor:e.original_anchor,translated_anchor:e.translated_anchor,
      original_text_sha256:e.original_text_sha256.toLowerCase(),
      translated_text_sha256:e.translated_text_sha256.toLowerCase(),
      status:e.status,
      original_id_cell_ref:bound?e.original_id_anchor:null,
      translated_id_cell_ref:bound?e.translated_id_anchor:null,
      formula_id_row_binding_declared:bound,
      formula_id_row_binding_provider_attested:false,
      original_source_preserved:true,
      cell_text_exposed:false,provider_cell_readback_by_module:false,
      mathematical_equivalence_verified:false});
  }
  const additions=new Set();
  for(const id of packet.translation_only_ids){
    if(typeof id!=="string"||!/^FM-[0-9]{3}$/.test(id)||
       additions.has(id)||seen.has(id))
      throw Error("ECO_TRANSLATION_ONLY_ID_ATTRIBUTION_CONFLICT");
    additions.add(id);
  }
  const units=new Set();
  for(const ref of packet.unit_defect_refs){
    if(typeof ref!=="string"||!cell.test(ref)||units.has(ref))
      throw Error("INVALID_ECO_TRANSLATION_UNIT_DEFECT_REFERENCE");
    units.add(ref);
  }
  return {state:"R1_CALLER_DECLARED_ORIGINAL_CELL_DIGESTS_HOLD",
    receipt_ref:packet.receipt_ref,receipt_sha256:packet.receipt_sha256.toLowerCase(),
    compared_count:records.length,
    formula_id_row_binding_declared_count:records.filter(x=>
      x.formula_id_row_binding_declared).length,
    formula_id_row_binding_required_count:records.filter(x=>
      !x.formula_id_row_binding_declared).length,
    mismatched_text_count:records.filter(x=>x.status!=="TEXT_EXACT").length,
    original_text_exact_count:records.filter(x=>x.status==="TEXT_EXACT").length,
    translation_only_formula_ids:[...additions].sort(),
    unqualified_unit_defect_refs:[...units].sort(),
    formula_records:records,
    receipt_sha256_cryptographically_verified_by_module:false,
    original_source_sha_bound_to_executed_cascade:true,
    original_cells_reread:false,related_cells_reread:false,
    issuer_authenticated:false,rights_verified:false,
    translation_equivalence_verified:false,unit_validity_verified:false,
    independent_science_verified:false,native_admitted:false,
    source_or_translation_modified:false,public_release_authorised:false};
}

/**
 * Reversible, cell-addressed review candidates for translated symbolic text.
 * Caller supplies independently retrieved source cells. No text is emitted,
 * rewritten or treated as authenticated by this module.
 */
function reviewSymbolicCorrectionBatch(batch,source,lineage,evidenceClass){
  if(batch===null)return {state:"SYMBOLIC_CORRECTION_BATCH_NOT_SUPPLIED",
    correction_records:[],source_cells_fetched_by_module:false,
    source_or_translation_modified:false};
  const keys=new Set(["source_ref","source_revision","source_sha256",
    "related_source_ref","related_revision_ref","entries"]);
  const entryKeys=new Set(["formula_id","original_cell","related_cell",
    "original_id_anchor","related_id_anchor","review_action"]);
  const idAnchorKeys=new Set(["sheet","cell","formula_id"]);
  const validIdAnchor=(a,c,id)=>obj(a)&&obj(c)&&
    Object.keys(a).every(k=>idAnchorKeys.has(k))&&
    a.sheet===c.sheet&&a.formula_id===id&&
    /^A[1-9]\d{0,6}$/.test(a.cell)&&
    /^B[1-9]\d{0,6}$/.test(c.cell)&&
    a.cell.slice(1)===c.cell.slice(1);
  if(!obj(batch)||Object.keys(batch).some(k=>!keys.has(k))||
     !obj(lineage)||!source.proof_hash||
     batch.source_ref!==source.source_ref||
     batch.source_revision!==source.revision||
     batch.source_sha256!==source.proof_hash||
     batch.related_source_ref!==lineage.related_source_ref||
     batch.related_revision_ref!==lineage.related_revision_ref||
     !Array.isArray(batch.entries)||batch.entries.length<1||
     batch.entries.length>32)
    throw Error("INVALID_ECO_SYMBOLIC_CORRECTION_BATCH");
  const seenIds=new Set(),seenOriginal=new Set(),seenRelated=new Set();
  const records=[];
  for(const e of batch.entries){
    if(!obj(e)||Object.keys(e).some(k=>!entryKeys.has(k))||
       typeof e.formula_id!=="string"||
       !/^FM-[0-9]{3}$/.test(e.formula_id)||
       !obj(e.original_cell)||!obj(e.related_cell)||
       !["REVIEW_TRANSLATION_ENCODING","PRESERVE_SOURCE_MATCH"].includes(e.review_action))
      throw Error("INVALID_ECO_SYMBOLIC_CORRECTION_ENTRY");
    // Caller-supplied A-row formula ID must bind to the adjacent B-row
    // expression in both R0 and translation; no provider attestation implied.
    const bound=e.original_id_anchor!==undefined&&
      e.related_id_anchor!==undefined;
    if((e.original_id_anchor===undefined)!==
         (e.related_id_anchor===undefined)||
       (bound&&(!validIdAnchor(e.original_id_anchor,e.original_cell,e.formula_id)||
                !validIdAnchor(e.related_id_anchor,e.related_cell,e.formula_id))))
      throw Error("ECO_SYMBOLIC_FORMULA_ID_ROW_BINDING_CONFLICT");
    const anchor={source_ref:source.source_ref,source_revision:source.revision,
      source_sha256:source.proof_hash,
      sheet:e.original_cell.sheet,cell:e.original_cell.cell};
    const pair={source_ref:source.source_ref,source_revision:source.revision,
      source_sha256:source.proof_hash,
      related_source_ref:lineage.related_source_ref,
      related_revision_ref:lineage.related_revision_ref,
      original_cell:e.original_cell,related_cell:e.related_cell};
    const checked=reviewSymbolicExpressionCrosswalk(
      pair,source,anchor,lineage,evidenceClass);
    const originalRef=e.original_cell.sheet+"!"+e.original_cell.cell;
    const relatedRef=e.related_cell.sheet+"!"+e.related_cell.cell;
    if(seenIds.has(e.formula_id)||seenOriginal.has(originalRef)||
       seenRelated.has(relatedRef))
      throw Error("DUPLICATE_ECO_SYMBOLIC_CORRECTION_ANCHOR");
    seenIds.add(e.formula_id);seenOriginal.add(originalRef);
    seenRelated.add(relatedRef);
    const discrepant=checked.state===
      "R1_CALLER_DECLARED_SYMBOLIC_EXPRESSION_DISCREPANCY_HOLD";
    const roundtrip=reviewDeclaredSymbolRoundtrip(
      e.original_cell.expression_text,e.related_cell.expression_text);
    if(e.review_action!==(discrepant?
       "REVIEW_TRANSLATION_ENCODING":"PRESERVE_SOURCE_MATCH"))
      throw Error("ECO_SYMBOLIC_CORRECTION_ACTION_CONFLICT");
    records.push({formula_id:e.formula_id,
      original_cell_ref:originalRef,translated_cell_ref:relatedRef,
      original_id_cell_ref:bound?e.original_id_anchor.sheet+"!"+e.original_id_anchor.cell:null,
      translated_id_cell_ref:bound?e.related_id_anchor.sheet+"!"+e.related_id_anchor.cell:null,
      formula_id_row_binding_declared:bound,
      formula_id_row_binding_provider_attested:false,
      review_action:e.review_action,
      caller_text_roundtrip_candidate:discrepant&&
        checked.original_encoding_valid&&roundtrip.caller_text_roundtrip_candidate,
      expression_text_match:checked.expression_text_match,
      original_encoding_valid:checked.original_encoding_valid,
      related_encoding_valid:checked.related_encoding_valid,
      original_text_preserved:true,translated_text_modified:false,
      source_bytes_embedded:false,provider_cells_fetched_by_module:false,
      repair_applied:false,scientific_equivalence_verified:false});
  }
  const count=records.filter(x=>x.review_action==="REVIEW_TRANSLATION_ENCODING").length;
  return {state:count?"R1_TRANSLATION_CORRECTION_CANDIDATES_HOLD":
      "R1_DECLARED_SYMBOLIC_TEXT_MATCHES_NOT_EQUIVALENCE",
    candidate_correction_count:count,compared_count:records.length,
    caller_text_roundtrip_candidate_count:records.filter(
      x=>x.caller_text_roundtrip_candidate).length,
    formula_id_row_binding_declared_count:records.filter(x=>x.formula_id_row_binding_declared).length,
    formula_id_row_binding_required_count:records.filter(x=>!x.formula_id_row_binding_declared).length,
    correction_records:records,source_cells_fetched_by_module:false,
    independent_provider_attestation:false,source_or_translation_modified:false,
    native_admitted:false,public_release_authorised:false};
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
    "symbolic_expression_crosswalk","formula_inventory",
    "symbolic_correction_batch","original_cell_digest_crosswalk","coefficient_roles"].includes(k)))
    throw Error("INVALID_ECO_PRE_MINT_REQUEST");
  const {cascade_input,geometry_descriptor=null,cell_anchor=null,
    requested_hydration="H3",observation_showcase=null,source_lineage=null,
    access_posture=null,related_access_posture=null,cell_crosswalk=null,
    symbolic_expression_crosswalk=null,formula_inventory=null,
    symbolic_correction_batch=null,original_cell_digest_crosswalk=null,
    coefficient_roles=null}=request;
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
  const symbolicCorrections=reviewSymbolicCorrectionBatch(symbolic_correction_batch,
    source,source_lineage,executed.evidence_class);
  const originalCellDigests=reviewDeclaredOriginalCellDigestCrosswalk(
    original_cell_digest_crosswalk,source,source_lineage,executed.evidence_class);
  // A source-bound digest receipt and formula inventory are two independent
  // caller-declared views. Reject contradictions before any R1 projection:
  // translated-only IDs cannot become original source-authored evidence.
  if(formula_inventory!==null&&original_cell_digest_crosswalk!==null){
    const originalIds=new Set(formula_inventory.original_ids);
    const relatedIds=new Set(formula_inventory.related_ids);
    const receiptIds=originalCellDigests.formula_records.map(x=>x.formula_id);
    const translatedOnly=originalCellDigests.translation_only_formula_ids;
    if(receiptIds.some(id=>!originalIds.has(id)||!relatedIds.has(id))||
       translatedOnly.some(id=>originalIds.has(id)||!relatedIds.has(id)))
      throw Error("ECO_FORMULA_RECEIPT_INVENTORY_CONFLICT");
  }
  let coeff={state:"COEFFICIENT_ROLES_NOT_SUPPLIED"};
  if(coefficient_roles!==null){
    if(!obj(coefficient_roles)||cascade_input.domain!=="second_cycle_claim"||
       !source.proof_hash||
       coefficient_roles.source_ref!==source.source_ref||
       coefficient_roles.source_revision!==source.revision||
       typeof coefficient_roles.source_sha256!=="string"||
       coefficient_roles.source_sha256.toLowerCase()!==source.proof_hash||
       executed.evidence_class!=="simulated")
      throw Error("ECO_COEFFICIENT_SOURCE_OR_EVIDENCE_CONFLICT");
    coeff=reviewSecondCycleCoefficientRoles(coefficient_roles);
  }
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
  if(symbolic_correction_batch!==null){
    blockers.push("SYMBOLIC_CORRECTION_BATCH_PROVIDER_ATTESTATION_REQUIRED");
    if(symbolicCorrections.formula_id_row_binding_required_count>0)
      blockers.push("FORMULA_ID_SOURCE_ROW_BINDING_REQUIRED");
    if(symbolicCorrections.candidate_correction_count>0)
      blockers.push("TRANSLATED_SYMBOLIC_TEXT_REPAIR_NOT_APPLIED");
  }
  if(formula_inventory!==null){
    blockers.push("FORMULA_INVENTORY_PROVIDER_ATTESTATION_REQUIRED");
    if(formulaInventory.state==="R1_TRANSLATION_FORMULA_INVENTORY_DELTA_HOLD")
      blockers.push("TRANSLATION_FORMULA_LIBRARY_DELTA_REQUIRES_PROVENANCE");
  }
  if(original_cell_digest_crosswalk!==null){
    blockers.push("PRIVATE_ORIGINAL_CELL_RECEIPT_NOT_INDEPENDENTLY_ATTESTED_BY_MODULE");
    if(originalCellDigests.formula_id_row_binding_required_count>0)
      blockers.push("ORIGINAL_CELL_DIGEST_FORMULA_ID_ROW_BINDING_REQUIRED");
    if(originalCellDigests.translation_only_formula_ids.length)
      blockers.push("TRANSLATION_ONLY_FORMULAS_NOT_ORIGINAL_SOURCE_EVIDENCE");
    if(originalCellDigests.unqualified_unit_defect_refs.length)
      blockers.push("TRANSLATED_PHYSICAL_UNITS_UNQUALIFIED");
  }
  if(coefficient_roles!==null){
    blockers.push("COEFFICIENT_ROLES_REQUIRE_PROVIDER_CELL_ATTESTATION");
    if(coeff.same_symbol_distinct_roles)
      blockers.push("SECOND_CYCLE_COEFFICIENT_SYMBOL_OVERLOAD_HOLD");
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
    symbolic_correction_batch_review:level>=2?symbolicCorrections:{state:"NOT_REQUESTED"},
    original_cell_digest_crosswalk_review:level>=2?originalCellDigests:{state:"NOT_REQUESTED"},
    coefficient_roles_review:level>=2?coeff:{state:"NOT_REQUESTED"},
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
      {layer:"symbolic_corrections",state:level>=2?symbolicCorrections.state:"NOT_REQUESTED"},
      {layer:"original_cell_digests",state:level>=2?originalCellDigests.state:"NOT_REQUESTED"},
      {layer:"coefficient_roles",state:level>=2?coeff.state:"NOT_REQUESTED"},
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
      "SYMBOLIC_CORRECTION_BATCH_NOT_APPLIED_TO_SOURCE",
      "ORIGINAL_CELL_DIGEST_RECEIPT_NOT_INDEPENDENTLY_RETRIEVED_BY_MODULE",
      "COEFFICIENT_ROLES_NOT_INDEPENDENTLY_PROVIDER_ATTESTED",
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
