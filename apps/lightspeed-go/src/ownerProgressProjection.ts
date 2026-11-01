/**
 * Owner-only UniSpace/LS GO presentation contract, SOURCE REVIEW ONLY.
 * The authenticated host must verify session, issuer/handshake, root and
 * object ACLs, source revision and rights BEFORE constructing this envelope.
 * These input booleans are NOT authentication, DBR admission or execution grants.
 * No browser fetch, local file access, credentials or private source bytes here.
 */
export interface OwnerProgressEnvelope {
  gateway?: {
    session_verified?: boolean;
    host_handshake_verified?: boolean;
    root_acl_verified?: boolean;
    object_acl_verified?: boolean;
    source_rights_verified?: boolean;
  };
  source?: {
    object_id?: string | null;
    filespace?: string;
    revision?: string | null;
  };
  bridge?: { reachable?: boolean };
  consumer?: {
    heartbeat_fresh?: boolean;
    pid_identity_verified?: boolean;
    lock_verified?: boolean;
    lease_verified?: boolean;
    dispatch_ready?: boolean;
  };
  checkpoint?: {
    reported_completed?: number | null;
    independently_verified_committed?: number | null;
    database_integrity_verified?: boolean;
  };
  latest?: {
    state?: string;
    completed?: number | null;
    target?: number | null;
    observed_attempted?: number | null;
    error?: string | null;
  };
}

const boundedCount = (value: unknown): number | null =>
  typeof value === "number" && Number.isSafeInteger(value) && value >= 0
    ? value : null;

const validObjectId = (value: unknown): value is string =>
  typeof value === "string" && value.startsWith("Cognigrex.cgx:/FileSpace/") &&
  /^[A-Za-z0-9][A-Za-z0-9._:/-]{1,159}$/.test(value);

const validRevision = (value: unknown): value is string =>
  typeof value === "string" && /^[a-fA-F0-9]{40,64}$/.test(value);

const failureClass = (error: unknown): string | null => {
  if (typeof error !== "string" || !error.trim()) return null;
  if (/database is locked|sqlite.*locked/i.test(error)) return "SQLITE_DATABASE_LOCKED";
  return "REDACTED_FAILURE";
};

/** Project only allowlisted scalars. Never spread/serialize the incoming envelope. */
export function projectOwnerProgress(input: OwnerProgressEnvelope | null | undefined) {
  const g = input?.gateway;
  const scoped = g?.session_verified === true &&
    g.host_handshake_verified === true && g.root_acl_verified === true &&
    g.object_acl_verified === true && g.source_rights_verified === true;
  const held = {
    schema: "unispace-owner-progress-projection-v1" as const,
    access: "HOLD_PRIVATE_SCOPE" as const,
    object_id: null,
    filespace: null,
    source_revision: null,
    evidence: "NO_PRIVATE_R3" as const,
    bridge: "BRIDGE_WITHHELD" as const,
    consumer: "CONSUMER_HELD" as const,
    progress: null,
    native_admitted: false as const,
    dispatch_authorized: false as const,
    public_publish_authorized: false as const,
  };
  if (!scoped) return held;

  const source = input?.source;
  const child = source?.filespace === "Cognigrex.cgx/FileSpace";
  const qualifiedIdentity = child && validObjectId(source?.object_id) &&
    validRevision(source?.revision);
  // A verified gateway is insufficient to expose another or unqualified child.
  // Hold the entire private projection until the exact FileSpace identity binds.
  if (!qualifiedIdentity) return { ...held, access: "HOLD_SOURCE_IDENTITY" as const };
  const checkpoint = input?.checkpoint;
  const latest = input?.latest;
  const state = latest?.state === "FAIL_CLOSED" || failureClass(latest?.error)
    ? "FAIL_CLOSED"
    : latest?.state === "CANDIDATE_INDEX_COMPLETE" ? "CANDIDATE_INDEX_COMPLETE"
    : latest?.state === "RUNNING" ? "RUNNING" : "UNKNOWN";
  const consumer = input?.consumer;
  const consumerReadyClaim = consumer?.heartbeat_fresh === true &&
    consumer.pid_identity_verified === true && consumer.lock_verified === true &&
    consumer.lease_verified === true && consumer.dispatch_ready === true;
  const verifiedCommitted = checkpoint?.database_integrity_verified === true
    ? boundedCount(checkpoint.independently_verified_committed) : null;

  return {
    schema: held.schema,
    access: qualifiedIdentity ? "PRIVATE_SOURCE_REVIEW" as const : "HOLD_SOURCE_IDENTITY" as const,
    object_id: qualifiedIdentity ? source!.object_id! : null,
    filespace: child ? "Cognigrex.cgx/FileSpace" as const : null,
    source_revision: qualifiedIdentity ? source!.revision! : null,
    evidence: "SOURCE_ONLY_UNADMITTED" as const,
    bridge: input?.bridge?.reachable === true ? "BRIDGE_REACHABLE" as const : "BRIDGE_OFFLINE" as const,
    consumer: consumerReadyClaim ? "CONSUMER_READY_CLAIM_NOT_AUTHORITY" as const : "CONSUMER_HELD" as const,
    progress: {
      reported_checkpoint: boundedCount(checkpoint?.reported_completed),
      independently_verified_committed: verifiedCommitted,
      observed_attempted: boundedCount(latest?.observed_attempted),
      latest_completed: boundedCount(latest?.completed),
      latest_target: boundedCount(latest?.target),
      latest_state: state,
      error_class: failureClass(latest?.error),
    },
    native_admitted: false as const,
    dispatch_authorized: false as const,
    public_publish_authorized: false as const,
  };
}
