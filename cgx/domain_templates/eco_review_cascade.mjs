/**
 * Athene Eco.cgx: executable, read-only provider-reference -> scoped semantic
 * resolution -> ecological claim qualification -> held release-manifest slice.
 * Consumes qualified references supplied by an authenticated caller; it does not
 * authenticate them, fetch bytes, mint Object_IDs, submit mutations or deploy.
 * This is not a second resolver or canonical Family Set.
 */
import {planEcoAlignment} from "./eco_qualified_alignment.mjs";
import {reviewSecondCycleClaim} from "./eco_second_cycle_claim_review.mjs";
import {reviewBioBlockMonitoringRecord} from "./eco_bioblock_monitoring_review.mjs";

export const ECO_CASCADE_SCHEMA = "CGX-ECO-REVIEW-CASCADE/0.1";
const valid = v => typeof v === "string" && v.length > 0 &&
  v.length <= 256 && !/[\u0000-\u001f]/.test(v);
const allowedProvider = new Set(["drive", "github"]);

export function runEcoReviewCascade(input) {
  if (!input || typeof input !== "object" || Array.isArray(input) ||
    Object.keys(input).some(k => !["source","novel","domain","scope","record"].includes(k)))
    throw Error("INVALID_ECO_CASCADE_INPUT");
  const {source, novel, domain, scope, record} = input;
  if (!source || typeof source !== "object" || Array.isArray(source) ||
    Object.keys(source).some(k => !["provider","id","revision","source_ref"].includes(k)) ||
    !allowedProvider.has(source.provider) || !valid(source.id) ||
    !valid(source.revision) || !valid(source.source_ref))
    throw Error("INVALID_ECO_SOURCE_IDENTITY");
  if (!scope || !Array.isArray(scope.authorised_source_ids) ||
    !scope.authorised_source_ids.includes(source.source_ref) ||
    !scope.authorised_source_ids.every(valid) ||
    (scope.authorised_object_ids !== undefined &&
      (!Array.isArray(scope.authorised_object_ids) ||
       !scope.authorised_object_ids.every(valid))) ||
    (scope.known_objects !== undefined && !Array.isArray(scope.known_objects)))
    throw Error("UNAUTHORISED_OR_INVALID_ECO_SOURCE_SCOPE");
  if (!novel || !Array.isArray(novel.source_refs) ||
    !novel.source_refs.includes(source.source_ref) || novel.geometry !== undefined)
    throw Error("ECO_SOURCE_LINEAGE_OR_PRIVATE_GEOMETRY_HOLD");
  if (!record || typeof record !== "object" || Array.isArray(record) ||
    !["second_cycle_claim","bioblock_monitoring"].includes(domain) ||
    record.source_ref !== source.source_ref ||
    record.evidence_class !== novel.evidence_class ||
    (domain === "bioblock_monitoring" && record.field_geometry_present))
    throw Error("ECO_DOMAIN_EVIDENCE_OR_SOURCE_CONFLICT");

  // Reuse the established Eco qualified alignment module, not a parallel resolver.
  const alignment = planEcoAlignment({
    novel, known_objects:scope.known_objects ?? [],
    authorised_source_ids:scope.authorised_source_ids,
    authorised_object_ids:scope.authorised_object_ids ?? [],
    max_candidates:20
  });
  const qualification = domain === "second_cycle_claim"
    ? reviewSecondCycleClaim(record)
    : reviewBioBlockMonitoringRecord(record);
  if (alignment.parent !== "Cognigrex.cgx" ||
      qualification.parent !== "Cognigrex.cgx" ||
      alignment.file_space !== "Eco.cgx" ||
      qualification.owner_family !== "Eco.cgx" ||
      qualification.source_only !== true)
    throw Error("ECO_FAMILY_OR_QUALIFICATION_CONTRACT_MISMATCH");

  return {
    schema:ECO_CASCADE_SCHEMA,
    family:"Cognigrex.cgx/Eco.cgx",
    file_space_candidate:"Eco.cgx",
    source_reference:{...source, bytes_read_this_execution:false,
      hash_verified_this_execution:false, reuse_rights_verified:false},
    step_receipts:{
      scoped_alignment:{executed:true, state:alignment.state,
        permitted_source_refs:alignment.novel_permitted_source_refs,
        candidate_count:alignment.candidate_count, checks:alignment.novel_checks},
      ecological_review:{executed:true, schema:qualification.schema,
        evidence_class:qualification.evidence_class,
        flags:qualification.flags}
    },
    evidence_class:record.evidence_class,
    stage:"R1_REVIEW_ONLY",
    release_gates:{object_id_minted:false, native_admitted:false,
      db_readback:false, runtime_verified:false,
      independent_science_validated:false, owner_accepted:false,
      public_release_authorised:false},
    next_gate:"AUTHENTICATED_ORIGINAL_BYTES_RIGHTS_AND_NATIVE_DBR_PROOF_REQUIRED"
  };
}
