/** CGX R0 public bootstrap. No device admission, network listener or execution path. */
export const PUBLIC_SCHEMA = "cgx-public-bootstrap-v1";
export const LOCAL_STATUS_URL = "http://127.0.0.1:8765/api/v1/status";
export const LOCAL_BOOTSTRAP_URL = "http://127.0.0.1:8765/api/v1/cgx/bootstrap";
export const MAX_STATUS_BYTES = 65536;

export function publicSkeleton() {
  return {
    schema_version: PUBLIC_SCHEMA,
    namespace: "cgx://CGX.cgx",
    publication_state: "PUBLIC_SAFE_TEMPLATE_NOT_DEPLOYED",
    root_authority: "UNASSIGNED",
    format: { media_type: "application/json", encoding: "utf-8", source: "versioned_open_dictionary" },
    object: {
      object_id: "CGX/PUBLIC/ALEXANDRIA/EMPTY",
      source_sha256: null, geometry_root: null,
      semantic_class: "dodecahedral_reference_frame",
      evidence_class: "TEMPLATE_ONLY",
    },
    geometry: {
      frame: "dimensionless_reference",
      vertex_count: 20, edge_count: 30, face_count: 12,
      euler_characteristic: 2,
      face_kind: "pentagon",
      cells: Array.from({ length: 12 }, (_, i) => ({
        id: "face-" + i, state: "NEUTRAL_UNBOUND", source_ref: null,
      })),
      occupied_object_count: 0,
      physical_volume_m3: null,
    },
    semantics: {
      known_states: ["OCCUPIED", "RESERVED", "FREE", "GROWTH_CANDIDATE",
                     "NEUTRAL_UNBOUND", "UNKNOWN", "WITHHELD", "CONFLICT"],
      distinction: "EMPTY_NOT_UNKNOWN_OR_WITHHELD",
      canonical_library: "existing_FileSpace_source_registry",
      projection: "local_lenses_from_authorised_content_roots",
      resolver: "requires_registered_schema_and_source_not_included",
    },
    network: {
      scope: "LOCAL_ONLY_BY_DEFAULT",
      transport: "EXISTING_LIGHTSPEED_LOOPBACK_CANDIDATE",
      remote_admission: "NOT_CONFIGURED",
      network_scan: false, gps: false, location_tracking: false,
      vpn: false, backscatter: false, telemetry: false,
      opt_in_required: true,
      initial_discovery_is_authentication: false,
    },
    phases: {
      initial: "PUBLIC_SKELETON_AND_LOOPBACK_STATUS",
      identity: "EXISTING_OWNER_SESSION_AND_DEVICE_SIGNING_REQUIRED",
      transfer: "SIGNED_PRIOR_ROOT_AND_CAPABILITY_NEGOTIATION_REQUIRED",
      execution: "AUTHORISED_QUEUE_LEASE_AND_RESULT_RECEIPT_REQUIRED",
      recheck: "SOURCE_ROOT_AND_CONSUMER_HEARTBEAT_READBACK_REQUIRED",
    },
    safety: {
      public_symbol_is_secret: false,
      script_execution: false, file_system_mutation: false,
      device_identity_verified: false, canonical_promotion_authorised: false,
    },
  };
}

export function classifyStatus(body) {
  if (!body || typeof body !== "object" || Array.isArray(body) ||
      body.bridge !== "ls-go" || typeof body.root !== "string") {
    return { state: "UNRECOGNISED_LOCAL_SERVICE", bridge_verified: false,
      consumer_verified: false, authenticated: false };
  }
  const healthy = body.ok === true;
  // /api/v1/status.ok currently confirms DB/storage/Merovingian only.
  // Never use it to assert that the Smith queue consumer executed a task.
  return {
    state: healthy ? "BRIDGE_RESPONSIVE_ONLY" : "BRIDGE_PRESENT_DEGRADED",
    bridge_verified: false,
    bridge_candidate: "ls-go",
    services_candidate: {
      database: body.services?.db === true,
      storage: body.services?.storage === true,
      merovingian: body.services?.merovingian === true,
    },
    consumer_state: "UNVERIFIED_NO_SIGNED_RECEIPT",
    queue_execution_state: "UNVERIFIED",
    device_identity_verified: false,
    authenticated: false,
    public_skeleton_available: true,
  };
}

async function boundedResponseText(response) {
  const contentLength = Number(response.headers?.get?.("content-length") ?? 0);
  if (Number.isFinite(contentLength) && contentLength > MAX_STATUS_BYTES) {
    throw new Error("STATUS_TOO_LARGE");
  }
  if (!response.body?.getReader) {
    const text = await response.text();
    if (Buffer.byteLength(text, "utf8") > MAX_STATUS_BYTES) throw new Error("STATUS_TOO_LARGE");
    return text;
  }
  const chunks = [];
  let total = 0;
  const reader = response.body.getReader();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > MAX_STATUS_BYTES) throw new Error("STATUS_TOO_LARGE");
      chunks.push(value);
    }
  } finally {
    await reader.cancel().catch(() => {});
  }
  return Buffer.concat(chunks.map(chunk => Buffer.from(chunk))).toString("utf8");
}

export async function discoverLocal({ fetchImpl = globalThis.fetch, timeoutMs = 2000 } = {}) {
  if (typeof fetchImpl !== "function") throw new TypeError("CGX requires fetch");
  if (!Number.isInteger(timeoutMs) || timeoutMs < 100 || timeoutMs > 5000) {
    throw new RangeError("timeoutMs must be between 100 and 5000");
  }
  try {
    // Never follow redirects to a different origin. Status is a read-only probe.
    const response = await fetchImpl(LOCAL_STATUS_URL, {
      method: "GET", redirect: "error", cache: "no-store",
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (response.status !== 200 || !response.ok) {
      return { state: "LOCAL_BRIDGE_HTTP_ERROR", http_status: response.status,
        consumer_verified: false, authenticated: false };
    }
    const text = await boundedResponseText(response);
    let parsed;
    try { parsed = JSON.parse(text); }
    catch { return { state: "UNRECOGNISED_LOCAL_SERVICE", consumer_verified: false, authenticated: false }; }
    return classifyStatus(parsed);
  } catch {
    return { state: "LOCAL_BRIDGE_UNREACHABLE_OR_UNTRUSTED",
      consumer_verified: false, authenticated: false,
      fallback: "PUBLIC_SKELETON_AVAILABLE",
      local_host_offline_inferred: false };
  }
}


/** Discover the CGX-specific public advertisement before the legacy status fallback. */
export async function discoverCgx({ fetchImpl = globalThis.fetch, timeoutMs = 2000 } = {}) {
  if (typeof fetchImpl !== "function") throw new TypeError("CGX requires fetch");
  if (!Number.isInteger(timeoutMs) || timeoutMs < 100 || timeoutMs > 5000) {
    throw new RangeError("timeoutMs must be between 100 and 5000");
  }
  try {
    const response = await fetchImpl(LOCAL_BOOTSTRAP_URL, {
      method: "GET", redirect: "error", cache: "no-store",
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (response.status === 404) {
      return { ...(await discoverLocal({ fetchImpl, timeoutMs })),
        protocol: "LEGACY_LIGHTSPEED_STATUS_FALLBACK" };
    }
    if (response.status !== 200 || !response.ok) {
      return { state: "CGX_BOOTSTRAP_HTTP_ERROR", http_status: response.status,
        authenticated: false, consumer_verified: false };
    }
    let info;
    try { info = JSON.parse(await boundedResponseText(response)); }
    catch {
      return { state: "UNRECOGNISED_CGX_ADVERTISEMENT",
        authenticated: false, consumer_verified: false };
    }
    if (info?.schema_version !== "cgx-bootstrap-advertisement-v1" ||
        info.namespace_candidate !== "cgx://CGX.cgx" ||
        info.geometry?.vertex_count !== 20 ||
        info.geometry?.edge_count !== 30 ||
        info.geometry?.face_count !== 12 ||
        info.security?.device_authenticated !== false ||
        info.security?.consumer_receipt_verified !== false ||
        info.security?.commands_allowed !== false ||
        info.semantics?.source_root !== null) {
      return { state: "UNRECOGNISED_CGX_ADVERTISEMENT",
        authenticated: false, consumer_verified: false };
    }
    return {
      state: "CGX_PUBLIC_BOOTSTRAP_CANDIDATE",
      protocol: info.schema_version,
      namespace_candidate: info.namespace_candidate,
      geometric_reference: { vertices: 20, edges: 30, faces: 12 },
      public_skeleton_available: true,
      device_identity_verified: false,
      consumer_verified: false,
      session_restored: false,
      remote_transport_connected: false,
      authenticated: false,
    };
  } catch {
    return {
      state: "LOCAL_BOOTSTRAP_UNREACHABLE_OR_UNTRUSTED",
      consumer_verified: false, authenticated: false,
      public_skeleton_available: true,
      local_host_offline_inferred: false,
    };
  }
}

export async function observeLocal({
  samples = 3, intervalMs = 1000, discover = discoverCgx,
  sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms)),
  now = () => new Date().toISOString(),
} = {}) {
  if (!Number.isInteger(samples) || samples < 1 || samples > 5) {
    throw new RangeError("samples must be integer 1..5");
  }
  if (!Number.isInteger(intervalMs) || intervalMs < 0 || intervalMs > 30000) {
    throw new RangeError("intervalMs must be integer 0..30000");
  }
  const observations = [];
  for (let i = 0; i < samples; i++) {
    if (i) await sleep(intervalMs);
    const result = await discover();
    observations.push({ ...result, phase: i, observed_utc: now() });
  }
  return {
    schema_version: "cgx-minimum-observation-sequence-v1",
    observation_count: observations.length,
    source: "LOCAL_LOOPBACK_DIAGNOSTIC_ONLY",
    session_restored: false,
    device_pairing_performed: false,
    observations,
  };
}
