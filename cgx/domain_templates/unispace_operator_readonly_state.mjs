/**
 * UniSpace FileSpace read-only R3 status adapter (source review only).
 * No authentication, provider access, DBR read, command dispatch or browser mount.
 * The caller MUST obtain every authority flag from a trusted server-side check;
 * a client-provided true value is not proof of permission.
 */
const HASH = /^[a-f0-9]{64}$/i;
const safeInt = (v) => Number.isSafeInteger(v) && v >= 0 ? v : null;
const RUN_STATES = new Set(["RUNNING", "COMPLETED", "FAIL_CLOSED", "HELD", "UNKNOWN"]);
const ERRORS = new Set(["SQLITE_LOCKED", "LEASE_EXPIRED", "SOURCE_UNAVAILABLE", "UNKNOWN"]);

export function projectReadOnlyOperatorState(input = {}) {
  const authority = input.authority ?? {};
  const verifiedOwner = ["issuer_verified", "session_valid", "scope_allows", "lease_valid", "revocation_checked", "root_acl_verified", "server_signed_attestation_verified"]
    .every((field) => authority[field] === true);
  const denied = {
    schema: "CGX-UNISPACE-READONLY-OPERATOR/0.1",
    view: "ACCESS_DENIED",
    hydration: "H0_NONE",
    object_id: null,
    child_filespace: null,
    bridge: "UNVERIFIED",
    consumer: "UNVERIFIED",
    dispatch_ready: false,
    progress: null,
    geometry: "FRONTIER_UNVERIFIED",
    release_authorised: false,
  };
  if (!verifiedOwner) return denied;

  const binding = input.binding ?? {};
  const qualified = typeof binding.object_id === "string" && binding.object_id.length > 0
    && typeof binding.child_filespace === "string" && binding.child_filespace.length > 0
    && binding.child_filespace === binding.authorised_child_filespace
    && typeof binding.source_version === "string" && binding.source_version.length > 0
    && HASH.test(binding.source_sha256 ?? "") && binding.rights === "QUALIFIED"
    && binding.resolver_receipt_verified === true && binding.owner_binding_verified === true;
  const admitted = qualified && binding.admission === "NATIVE_ADMITTED"
    && authority.dbr_readback_verified === true;

  const runtime = input.runtime ?? {};
  const bridge = runtime.bridge_http_ok === true ? "BRIDGE_REACHABLE" : "BRIDGE_UNVERIFIED";
  const consumer = runtime.consumer_state === "READY" && runtime.consumer_lease_verified === true
    && admitted ? "CONSUMER_READY_REPORTED" : "CONSUMER_HELD";

  const p = input.progress ?? {};
  const lastCommitted = p.committed_receipt_verified === true ? safeInt(p.last_committed) : null;
  const target = p.committed_receipt_verified === true ? safeInt(p.committed_target) : null;
  const attempted = safeInt(p.latest_attempted);
  const runState = RUN_STATES.has(p.latest_run_state) ? p.latest_run_state : "UNKNOWN";
  const progress = {
    latest_run_state: runState,
    latest_attempted: attempted,
    last_committed: lastCommitted,
    committed_target: target,
    error_code: ERRORS.has(p.error_code) ? p.error_code : null,
    checkpoint_state: lastCommitted === null ? "UNVERIFIED" : "RECEIPT_VERIFIED",
  };

  return {
    ...denied,
    view: admitted ? "R3_ELIGIBILITY_CANDIDATE_NOT_HYDRATED" : "OWNER_SOURCE_REVIEW_ONLY",
    hydration: admitted ? "H0_H2_ELIGIBILITY_ONLY_NO_FETCH" : "H0_REVIEW_METADATA_ONLY",
    object_id: admitted ? binding.object_id : null,
    child_filespace: admitted ? binding.child_filespace : null,
    bridge,
    consumer,
    progress,
    geometry: admitted && input.geometry?.source_verified === true
      && input.geometry?.frame_verified === true && input.geometry?.units_verified === true
      && input.geometry?.rights_verified === true ? "GEOMETRY_SOURCE_QUALIFIED_NOT_METRIC_VALIDATED" : "FRONTIER_UNVERIFIED",
  };
}
