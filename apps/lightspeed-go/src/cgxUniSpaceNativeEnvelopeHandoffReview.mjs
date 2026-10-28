/**
 * UniSpace private R0 preflight -> existing CGX-SOURCE-ENVELOPE/0.1
 * shape reconciliation. Pure, review-only, no bytes, upload, network, native
 * conversion, DBR, owner-session verification, or Vite public asset access.
 *
 * The envelope is CALLER-SUPPLIED and therefore UNTRUSTED. A matching
 * digest/shape is not proof of original bytes, issuer, rights, or admission.
 */
export const SCHEMA = "UNISPACE-NATIVE-ENVELOPE-HANDOFF-REVIEW/0.1";
const PARENT = "Cognigrex.cgx";
const CHILDREN = new Set(["Romer.cgx", "Eco.cgx", "EMASSC.cgx", "LS.cgx"]);
// Native source_intake.py::_adapter_for extension mapping; declarative only.
const NATIVE_ADAPTER_BY_EXTENSION = Object.freeze({
  txt:"text-stdlib-v0.1",md:"text-stdlib-v0.1",csv:"csv-stdlib-v0.1",json:"json-stdlib-v0.1",
  pdf:"pdf-pypdf-v0.1",png:"image-metadata-stdlib-v0.1",
  jpg:"image-metadata-stdlib-v0.1",jpeg:"image-metadata-stdlib-v0.1",
  webp:"image-reference-v0.1",obj:"obj-mesh-stdlib-v0.1",
  stl:"stl-mesh-stdlib-v0.1",glb:"gltf-stdlib-v0.1",gltf:"gltf-stdlib-v0.1"
});
const SHA256 = /^[0-9a-f]{64}$/i;
const SHA1 = /^[0-9a-f]{40}$/i;
const MAX_BYTES = 60 * 1024 * 1024;
// Exact source-envelope contract enum; a runtime-specific loss claim outside
// this enum remains Frontier until the native contract is reconciled.
const ROUND_TRIP = new Set([
  "NONE", "IDENTITY_REFERENCE_ONLY", "STRUCTURE_PRESERVED",
  "SEMANTIC_PROJECTION_ONLY", "LOSSLESS_FOR_DECLARED_FIELDS"
]);
const record = x => x !== null && typeof x === "object" && !Array.isArray(x);
const one = (xs, v) => Array.isArray(xs) && xs.length === 1 && xs[0] === v;
const hold = code => Object.freeze({
  schema: SCHEMA, state: "HOLD", hold_code: code,
  envelope_shape_matched: false, source_bytes_independently_verified: false,
  owner_session_verified: false, root_acl_verified: false,
  dbr_readback_verified: false, native_admitted: false,
  upload_performed: false, network_fetch: false, canonical_mutation: false,
  public_vite_asset: false, release_accepted: false
});

export function reviewNativeEnvelopeHandoff(input = {}) {
  if (!record(input)) return hold("INVALID_INPUT");
  const {preflight:p, envelope:e, selection:s, source:m, client:c} = input;
  if (!record(s) || s.parent_filespace !== PARENT ||
      !CHILDREN.has(s.filespace) ||
      typeof s.object_id !== "string" ||
      !/^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/.test(s.object_id) ||
      s.object_id === "cgx:root:cognigrex" ||
      s.object_id.startsWith("cgx:domain:") ||
      s.identity_status !== "SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED")
    return hold("UNQUALIFIED_OBJECT");
  if (!record(c) || c.mode !== "review_only" || c.revoked !== false ||
      !one(c.allowed_object_ids, s.object_id) ||
      !one(c.allowed_filespaces, s.filespace))
    return hold("CLIENT_SCOPE_MISMATCH");
  if (!record(m) || m.object_id !== s.object_id ||
      m.filespace !== s.filespace || (typeof m.mapping_blob_sha !== "string" || !SHA1.test(m.mapping_blob_sha)) ||
      (typeof m.r0_source_sha256 !== "string" || !SHA256.test(m.r0_source_sha256)) ||
      !["R0_R1_REFERENCE", "R0_R1_R2_REFERENCE"].includes(m.mapping_stage) ||
      !["UNRESOLVED", "PRIVATE_SCOPED", "PUBLIC_SAFE"].includes(m.rights) ||
      !["scientific", "creative", "mixed", "unknown"].includes(m.evidence_class))
    return hold("UNQUALIFIED_SOURCE_MAPPING");
  if (!record(p) || p.schema !== "UNISPACE-PRIVATE-DROP-PREFLIGHT/0.1" ||
      p.state !== "R0_HASHED_PREFLIGHT_HOLD" ||
      p.parent_filespace !== PARENT || p.candidate_object_id !== s.object_id ||
      p.child_filespace !== s.filespace ||
      p.source_mapping_id !== m.mapping_id ||
      p.evidence_class !== m.evidence_class ||
      (typeof p.candidate_r0_sha256 !== "string" || !SHA256.test(p.candidate_r0_sha256)) ||
      !Number.isSafeInteger(p.file_bytes) || p.file_bytes < 1 ||
      p.file_bytes > MAX_BYTES ||
      (typeof p.file_type !== "string" || !/^[a-z0-9]{2,8}$/.test(p.file_type)) ||
      p.source_reference_hash_verified !== false ||
      p.native_admitted !== false || p.host_verified !== false ||
      p.release_accepted !== false || p.canonical_mutation !== false ||
      p.upload_performed !== false || p.bytes_persisted !== false ||
      p.network_fetch !== false || p.display_hydration !== "H0_REFERENCE_ONLY")
    return hold("UNTRUSTED_PREFLIGHT");
  // The existing Python source_intake.py emits this envelope shape, but
  // only an authenticated native consumer may actually build/bind it.
  if (!record(e) || e.schema !== "CGX-SOURCE-ENVELOPE/0.1" ||
      Object.hasOwn(e, "admission_state") ||
      // Required by cgx/domain_templates/source_envelope_contract.json;
      // these are caller assertions, never provider authentication.
      typeof e.source_name !== "string" || !e.source_name ||
      typeof e.media_type !== "string" || !e.media_type ||
      typeof e.adapter_id !== "string" || !e.adapter_id ||
      e.adapter_id !== NATIVE_ADAPTER_BY_EXTENSION[p.file_type] ||
      typeof e.authority !== "string" || !e.authority ||
      typeof e.evidence_state !== "string" || !e.evidence_state ||
      typeof e.release_class !== "string" || !e.release_class ||
      !Array.isArray(e.projections) || !Array.isArray(e.warnings) ||
      !Array.isArray(e.unresolved) ||
      (typeof e.envelope_sha256 !== "string" || !SHA256.test(e.envelope_sha256)) ||
      (typeof e.sha256 !== "string" || !SHA256.test(e.sha256)) ||
      e.sha256.toLowerCase() !== p.candidate_r0_sha256.toLowerCase() ||
      e.source_id !== "src:" + e.sha256 ||
      e.byte_length !== p.file_bytes ||
      e.extension !== "." + p.file_type ||
      !record(e.native_preservation) ||
      e.native_preservation.source_sha256 !== e.sha256 ||
      e.native_preservation.source_byte_length !== e.byte_length ||
      !(e.native_preservation.source_ref === null ||
        (typeof e.native_preservation.source_ref === "string" &&
         e.native_preservation.source_ref.length > 0)) ||
      e.native_preservation.adapter_version !== "0.1" ||
      !ROUND_TRIP.has(e.native_preservation.round_trip_claim) ||
      !record(e.lineage) || e.lineage.canonical_mutation !== false ||
      e.lineage.projection_only !== true ||
      e.lineage.parent_source_id !== null)
    return hold("ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH");
  // envelope_sha256 is checked for SHAPE only, never recomputed or trusted.
  // Do not echo e.source_name, e.native_preservation.source_ref,
  // e.projections, private mapping locators, client credentials, or raw bytes.
  return Object.freeze({
    schema: SCHEMA, state: "NATIVE_ENVELOPE_SHAPE_MATCH_REVIEW_HOLD",
    parent_filespace: PARENT, candidate_object_id: s.object_id,
    child_filespace: s.filespace, source_mapping_id: m.mapping_id,
    evidence_class: m.evidence_class, candidate_source_id: e.source_id,
    candidate_r0_sha256: p.candidate_r0_sha256.toLowerCase(),
    envelope_shape_matched: true,
    registered_original_hash_string_match_only:
      m.r0_source_sha256.toLowerCase() === p.candidate_r0_sha256.toLowerCase(),
    source_bytes_independently_verified: false,
    registered_original_bytes_verified: false,
    source_rights_verified: false, owner_session_verified: false,
    root_acl_verified: false, dbr_readback_verified: false,
    conversion_plan_verified: false, r1_typed: false, r2_modelled: false,
    r3_live: false, native_admitted: false, host_verified: false,
    upload_performed: false, network_fetch: false, canonical_mutation: false,
    public_vite_asset: false, release_accepted: false,
    hydration: "H0_REFERENCE_ONLY", capability_mode: "DECLARATIVE_REVIEW_ONLY",
    next_gate: "AUTHENTICATED_CGX_NATIVE_SOURCE_ENVELOPE_CONVERSION_PLAN_AND_DBR",
    frontier: Object.freeze([
      "UNTRUSTED_CALLER_ENVELOPE_NOT_NATIVE_PROVIDER_READBACK",
      "SOURCE_RIGHTS_OWNER_AND_HASH_PROOF_REQUIRED",
      "ISSUE_158_STATIC_PRIVATE_BOUNDARY_HOLD",
      "ISSUE_161_TWO_NODE_DBR_ACCEPTANCE_HOLD"
    ]),
    claim_boundary: "Shape/digest comparison only; no R0 source admission, signed authority, authenticated host, rights clearance, native conversion, upload, or public R3 view."
  });
}
