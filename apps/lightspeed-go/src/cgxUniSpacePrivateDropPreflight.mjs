/**
 * UniSpace one-object private drag/drop R0 preflight. No upload, parse, source
 * storage, native mint, DBR, session authentication or Vite-public import.
 * Hashes caller-supplied bytes locally; never treats a client claim as rights.
 */
export const SCHEMA = "UNISPACE-PRIVATE-DROP-PREFLIGHT/0.1";
const MAX_BYTES = 60 * 1024 * 1024;
const DEFAULT_BYTES = 8 * 1024 * 1024;
const ID = /^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/;
const SHA1 = /^[a-f0-9]{40}$/i;
const SHA256 = /^[a-f0-9]{64}$/i;
const NAME = /^[A-Za-z0-9][A-Za-z0-9 _.()-]{0,127}$/;
const TYPES = Object.freeze({
  txt: ["text/plain"], md: ["text/markdown", "text/plain"],
  csv: ["text/csv", "text/plain"], json: ["application/json"],
  pdf: ["application/pdf"], png: ["image/png"],
  jpg: ["image/jpeg"], jpeg: ["image/jpeg"], webp: ["image/webp"],
  obj: ["text/plain", "application/octet-stream"],
  stl: ["model/stl", "application/octet-stream"],
  glb: ["model/gltf-binary", "application/octet-stream"],
  gltf: ["model/gltf+json", "application/json"]
});
const record = x => x !== null && typeof x === "object" && !Array.isArray(x);
const hold = code => Object.freeze({
  schema: SCHEMA, state: "HOLD", hold_code: code,
  native_admitted: false, host_verified: false, release_accepted: false,
  network_fetch: false, upload_performed: false, bytes_persisted: false,
  canonical_mutation: false, display_hydration: "NONE"
});
const exact = (a, value) => Array.isArray(a) && a.length === 1 && a[0] === value;

export async function preflightPrivateObjectDrop(input = {}) {
  if (!record(input)) return hold("INVALID_INPUT");
  const {selection:s, card, client:c, source:p, drop, max_bytes = DEFAULT_BYTES} = input;
  if (!record(s) || s.parent_filespace !== "Cognigrex.cgx" ||
      !ID.test(s.object_id || "") || s.object_id === "cgx:root:cognigrex" ||
      s.object_id.startsWith("cgx:domain:") ||
      !["Romer.cgx", "Eco.cgx", "EMASSC.cgx", "LS.cgx"].includes(s.filespace) ||
      s.identity_status !== "SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED") return hold("UNQUALIFIED_SELECTION");
  if (!record(card) || card.schema !== "UNISPACE-PRIVATE-R3-CARD/0.1" ||
      card.state !== "R3_PRIVATE_VIEW_CANDIDATE" ||
      card.candidate_object_id !== s.object_id || card.child_filespace !== s.filespace ||
      card.parent_filespace !== s.parent_filespace ||
      card.native_admitted !== false || card.host_verified !== false ||
      card.release_accepted !== false || card.display_hydration !== "H0_REFERENCE_ONLY") return hold("UNTRUSTED_CARD");
  if (!record(c) || c.mode !== "review_only" || c.revoked !== false ||
      !exact(c.allowed_object_ids, s.object_id) || !exact(c.allowed_filespaces, s.filespace))
      return hold("CLIENT_SCOPE_MISMATCH");
  if (!record(p) || p.object_id !== s.object_id || p.filespace !== s.filespace ||
      p.mapping_id !== card.source_mapping_id || p.mapping_blob_sha !== card.source_mapping_blob_sha ||
      p.mapping_stage !== card.mapping_stage ||
      !["R0_R1_REFERENCE", "R0_R1_R2_REFERENCE"].includes(p.mapping_stage) ||
      !SHA1.test(p.mapping_blob_sha || "") || !SHA256.test(p.r0_source_sha256 || "") ||
      !["scientific", "creative", "mixed", "unknown"].includes(p.evidence_class) ||
      p.evidence_class !== card.evidence_class ||
      !["UNRESOLVED", "PRIVATE_SCOPED", "PUBLIC_SAFE"].includes(p.rights))
      return hold("SOURCE_PROVENANCE_MISMATCH");
  if (!Number.isSafeInteger(max_bytes) || max_bytes < 1 || max_bytes > MAX_BYTES)
      return hold("INVALID_TRANSFER_LIMIT");
  if (!record(drop) || !Array.isArray(drop.files) || drop.files.length !== 1)
      return hold("EXACTLY_ONE_FILE_REQUIRED");
  const file = drop.files[0];
  if (!record(file) || typeof file.name !== "string" || !NAME.test(file.name) ||
      file.name.includes("..") || file.name.endsWith(".") || file.name.startsWith("."))
      return hold("UNSAFE_FILE_NAME");
  const ext = file.name.split(".").pop()?.toLowerCase();
  if (!Object.hasOwn(TYPES, ext) || !TYPES[ext].includes(file.mime))
      return hold("UNSUPPORTED_TYPE_OR_MIME");
  if (!Number.isSafeInteger(file.size) || file.size < 1 || file.size > max_bytes ||
      !(file.bytes instanceof Uint8Array) || file.bytes.byteLength !== file.size)
      return hold("BYTE_LENGTH_OR_LIMIT_MISMATCH");
  if (file.claimed_sha256 !== undefined && !SHA256.test(file.claimed_sha256))
      return hold("INVALID_CLAIMED_HASH");
  if (!globalThis.crypto?.subtle?.digest) return hold("WEBCRYPTO_UNAVAILABLE");
  let digest;
  try {
    const hash = await globalThis.crypto.subtle.digest("SHA-256", file.bytes);
    digest = Array.from(new Uint8Array(hash), b => b.toString(16).padStart(2, "0")).join("");
  } catch {
    return hold("HASH_COMPUTATION_FAILED");
  }
  if (file.claimed_sha256 && file.claimed_sha256.toLowerCase() !== digest)
      return hold("HASH_MISMATCH");
  // This is a *new* R0 candidate hash, not verification of the registered source.
  // Rights, malware, format validity, duplicates, identity and ACL are not resolved.
  return Object.freeze({
    schema: SCHEMA, state: "R0_HASHED_PREFLIGHT_HOLD",
    parent_filespace: s.parent_filespace, candidate_object_id: s.object_id,
    child_filespace: s.filespace, source_mapping_id: p.mapping_id,
    evidence_class: p.evidence_class, file_type: ext, file_bytes: file.size,
    candidate_r0_sha256: digest, source_reference_hash_verified: false,
    rights_status: "UNVERIFIED", identity_collision_checked: false,
    format_parsed: false, malware_checked: false,
    r1_typed: false, r2_modelled: false, r3_live: false,
    frontier: Object.freeze([
      "SOURCE_RIGHTS_AND_OWNER_CLEARANCE_REQUIRED",
      "NATIVE_OBJECT_ID_COLLISION_AND_DBR_READBACK_REQUIRED",
      "ISSUE_158_PUBLIC_STATIC_BOUNDARY_HOLD",
      "ISSUE_161_TWO_NODE_ACCEPTANCE_HOLD"
    ]),
    recommended_route: "CGX_NATIVE_INTAKE_PRECHECK_ONLY",
    display_hydration: "H0_REFERENCE_ONLY", offline_display: "HASH_AND_TYPE_ONLY",
    network_fetch: false, upload_performed: false, bytes_persisted: false,
    source_bytes_embedded: false, public_vite_asset: false,
    native_admitted: false, host_verified: false, release_accepted: false,
    canonical_mutation: false,
    claim_boundary: "Local byte-hash preflight is not a qualified intake, malware scan, rights approval, accepted identity, authenticated host readback, or deployed R3 view."
  });
}
