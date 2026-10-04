export const COMMAND_SCHEMA = "lightspeed-go-command-v2";
const LOCAL_DESKTOP_ORIGIN = "http://127.0.0.1:8765";

export const resolveDesktopOrigin = (configuredOrigin?: string): string => {
  const candidate = configuredOrigin?.trim();
  if (!candidate) return LOCAL_DESKTOP_ORIGIN;

  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    throw new TypeError("VITE_LIGHTSPEED_DESKTOP_ORIGIN must be an absolute URL");
  }

  const loopbackHosts = new Set(["127.0.0.1", "localhost", "::1", "[::1]"]);
  const isLoopback = loopbackHosts.has(parsed.hostname.toLowerCase());
  if (parsed.protocol !== "https:" && !(parsed.protocol === "http:" && isLoopback)) {
    throw new TypeError("Remote LightSpeed Desktop origins must use HTTPS");
  }
  if (parsed.username || parsed.password) {
    throw new TypeError("LightSpeed Desktop origins must not contain credentials");
  }
  if (parsed.pathname !== "/" || parsed.search || parsed.hash) {
    throw new TypeError("LightSpeed Desktop origins must not contain a path, query or fragment");
  }

  return parsed.origin;
};

export const DEFAULT_DESKTOP_ORIGIN = resolveDesktopOrigin(
  import.meta.env.VITE_LIGHTSPEED_DESKTOP_ORIGIN,
);

export const FLOORS = [
  "Achilles",
  "Neo",
  "Architect",
  "TheConstruct",
  "Morpheus",
  "Oracle",
  "Smith",
  "Merovingian",
  "Trinity",
] as const;

export type Floor = (typeof FLOORS)[number];
export type Priority = "critical" | "high" | "normal" | "low";
export type ExecutionMode = "review" | "queue";
export type CommandAction = "cognigrex_workflow" | "source_preserving_intake";
export type ReviewDecision = "approve" | "hold" | "reject";
export type RepresentationDecision =
  | "approve"
  | "provisional_approve"
  | "hold"
  | "reject"
  | "request_evidence"
  | "supersede";

export interface AuthorityContract {
  canonical_gate_id: string;
  owner_decision_ref: string;
  core_acceptance_ref: string;
  approval_or_hold_state: string;
  authorised_scope: string;
  prohibited_scope: string;
}

export interface CommandEnvelope {
  schema_version: typeof COMMAND_SCHEMA;
  command_id: string;
  created_utc: string;
  source: "LS GO";
  title: string;
  instruction: string;
  target_floor: Floor;
  oversight_floor: "Achilles";
  priority: Priority;
  execution_mode: ExecutionMode;
  action_type: CommandAction;
  action_payload?: { source_path: string; source_sha256: string };
  proof_required: true;
  public_safe: true;
  canonical_gate_id: string;
  owner_decision_ref: string;
  core_acceptance_ref: string;
  approval_or_hold_state: string;
  authorised_scope: string;
  prohibited_scope: string;
  requested_scope: string;
}

export interface CommandInput {
  title?: string;
  instruction: string;
  targetFloor?: Floor;
  priority?: Priority;
  executionMode?: ExecutionMode;
  actionType?: CommandAction;
  authorityContract?: AuthorityContract | null;
}

export interface ProjectRecord {
  project_id: string;
  name: string;
  path: string;
  root_id?: string;
  authority?: string;
  writable?: boolean;
  condition?: string;
  scan_truncated?: boolean;
  file_count?: number;
  significant_file_count?: number;
  size_bytes?: number;
  latest_modified_utc?: string | null;
  metadata?: Record<string, unknown>;
  file_browser?: {
    state: "available" | "restricted" | "unavailable";
    reason: string;
  };
}

export interface ProjectFileRecord {
  relative_path: string;
  name: string;
  extension: string;
  mime_type: string;
  kind: "text" | "binary_or_unknown";
  size_bytes: number;
  modified_utc?: string | null;
  preview_supported: boolean;
}

export interface ProjectFilesResponse {
  schema_version: "lightspeed-project-files-v1";
  state: "available" | "empty" | "restricted";
  project: Pick<ProjectRecord, "project_id" | "name" | "authority" | "condition">;
  files: ProjectFileRecord[];
  summary: {
    visible_file_count: number;
    blocked_file_count: number;
    skipped_file_count: number;
    scanned_file_count: number;
    scan_truncated: boolean;
    limit: number;
  };
  boundary: string;
}

export interface ProjectFileOpenResult {
  schema_version: "lightspeed-project-file-open-result-v1";
  state: "opened_read_only";
  project: Pick<ProjectRecord, "project_id" | "name" | "authority">;
  file: ProjectFileRecord;
  preview: {
    state: "available" | "empty" | "metadata_only" | "metadata_only_non_utf8";
    encoding: "utf-8" | null;
    truncated: boolean;
    text: string | null;
  };
  source_mutated: false;
  boundary: string;
}

export interface ResultReceiptMetadata {
  result_id: string;
  command_id?: string | null;
  task_id?: number | null;
  job_id?: number | null;
  status: string;
  action_type?: string | null;
  target_floor?: string | null;
  created_utc?: string | null;
  completed_utc?: string | null;
  public_safe_state: "true" | "false" | "unknown";
  proof_required_state: "true" | "false" | "unknown";
  public_publish_authorized: boolean;
  drive_write_executed: boolean;
  size_bytes: number;
  modified_utc: string;
  sha256: string;
}

export interface LocalResultsResponse {
  schema_version: "lightspeed-local-results-index-v1";
  state: "available" | "empty" | "restricted";
  results: ResultReceiptMetadata[];
  summary: {
    visible_result_count: number;
    invalid_file_count: number;
    scanned_file_count: number;
    limit: number;
    truncated: boolean;
    status_counts: Record<string, number>;
  };
  boundary: string;
}

export interface LocalResultOpenResponse {
  schema_version: "lightspeed-local-result-open-v1";
  state: "opened_read_only";
  identity: {
    result_id: string;
    size_bytes: number;
    modified_utc: string;
    sha256: string;
  };
  result: Record<string, unknown>;
  source_mutated: false;
  boundary: string;
}

export type ObjectContextDomain = "romer" | "eco" | "emassc" | "lightspeed";

export interface CGXObjectContext {
  schema: "CGX-OBJECT-CONTEXT/0.1";
  query: string;
  resolved_twin_id: string;
  semantic_domain: string;
  domain_identity: {
    semantic_object_id?: string | null;
    filespace?: string | null;
    namespace?: string | null;
  };
  semantic_resolution: {
    state: "exact_semantic_object" | "family_bound_only";
    semantic_object_id?: string | null;
    operations_current_object_id?: string | null;
    rule: string;
  };
  operations_binding: Record<string, unknown>;
  canonical_owner: Record<string, unknown>;
  source_name?: string | null;
  family_state?: string | null;
  representation: Record<string, unknown>;
  geometry_authority?: string | null;
  lineage: Record<string, unknown>;
  evidence_boundary: string;
  automatic_execution: false;
  canonical_mutation: false;
}

export interface ObjectContextResponse {
  object_context: CGXObjectContext;
  execution_performed: false;
  external_action_performed: false;
  canonical_mutation: false;
  authority_transfer: false;
}

export interface ReviewRecord {
  review_id: string;
  created_utc?: string;
  title?: string;
  summary?: string;
  event_type?: string;
  project_ids?: string[];
  artifact_paths?: string[];
  state?: string;
  proof_required?: boolean;
  drive_receipt_path?: string;
  drive_writeback_mode?: string;
  decision?: Record<string, unknown>;
}

export interface ReviewDecisionResponse {
  accepted?: boolean;
  receipt?: {
    review_id?: string;
    decision?: string;
    drive_writeback_mode?: string;
    decision_receipt_state?: string;
  };
}

export interface DesktopStatus {
  ok: boolean;
  time_utc?: string;
  auth?: {
    configured?: boolean;
    mode?: string;
    username?: string;
    must_change?: boolean;
    reminder_due?: boolean;
    mandatory_due?: boolean;
    reminder_due_utc?: string | null;
    mandatory_due_utc?: string | null;
    state?: string;
  };
  remote_access?: {
    state?: "local_only" | "credential_gate" | "ready_for_private_relay_verification";
    private_https_origin_count?: number;
    owner_auth_configured?: boolean;
    owner_password_change_required?: boolean;
    off_device_verified?: boolean;
    public_direct_execution?: boolean;
    boundary?: string;
  };
  services?: { db?: boolean; storage?: boolean; merovingian?: boolean };
  merovingian?: {
    status?: string;
    receipt?: string;
    project_summary?: Record<string, unknown>;
    cleanup_summary?: Record<string, unknown>;
    drive_writeback?: { path?: string; mode?: string };
  };
  representation_edge?: {
    enabled?: boolean;
    migration_applied?: boolean;
    error?: string | null;
  };
  test_cascade?: {
    mode?: "corpus_bound";
    planning_endpoint?: string;
    activation_state?: "prepared_not_activated" | "active" | "held";
    semantic_states?: Array<"blocked" | "ready" | "underway" | "partial" | "complete">;
    result_policy?: string;
    dependency_gate?: string;
    execution_performed_by_status?: boolean;
  };
  object_context?: {
    mode?: "current_lineage_read_only";
    endpoint?: string;
    domains?: string[];
    automatic_execution?: boolean;
    canonical_mutation?: boolean;
    authority_transfer?: boolean;
  };
  node_exchange?: NodeExchangeStatus;
  authority_contract?: AuthorityContract;
}

export const remoteAccessPresentation = (
  remoteAccess?: DesktopStatus["remote_access"],
): { label: string; detail: string } => {
  if (remoteAccess?.state === "ready_for_private_relay_verification") {
    return {
      label: "Verify off-device",
      detail: "Private HTTPS origin configured; remote owner flow still needs readback.",
    };
  }
  if (remoteAccess?.state === "credential_gate") {
    return {
      label: "Credential held",
      detail: "Complete the owner password change before remote verification.",
    };
  }
  return {
    label: "Local only",
    detail: "No private HTTPS relay origin is configured.",
  };
};

export interface NodeExchangeStatus {
  schema_version?: "cgx-node-exchange-status-v1";
  node_id?: string;
  transport?: {
    mode?: string;
    verified_carriers?: string[];
    peer_transport_verified?: boolean;
  };
  compute?: {
    local_ready?: boolean;
    peer_nodes?: string[];
    peer_compute_verified?: boolean;
    lease_required?: boolean;
    heavy_execution_default?: boolean;
  };
  activation?: {
    host_root_registry_ready?: boolean;
    typed_transfer_queue_ready?: boolean;
    peer_compute_queue_ready?: boolean;
  };
  claim_boundary?: string;
  authority_transfer?: boolean;
  canonical_promotion_authorized?: boolean;
  transfer_planning_endpoint?: string;
  compute_planning_endpoint?: string;
  execution_route?: string;
}

export interface NodeTransferPlanInput {
  source_ref: string;
  source_sha256: string;
  size_bytes: number;
  file_name: string;
  source_node_id: string;
  target_node_id: string;
  source_root_id: string;
  target_root_id: string;
  object_id?: string;
}

export interface NodeComputePlanInput {
  instruction: string;
  task_id: string;
  run_id: string;
  project_id?: string;
  target_node_id: string;
  capability_id: string;
  lease_ref: string;
  input_receipts?: Record<string, unknown>[];
  resource_budget?: Record<string, unknown>;
}

export interface NodeExchangePlanResponse {
  execution_performed: false;
  authority_transfer: false;
  canonical_mutation: false;
  required_execution_lease_class: "COMPUTE_ONLY" | "DIGITAL_WRITE";
  activation_boundary: string;
  plan?: Record<string, unknown>;
  request?: Record<string, unknown>;
}

export const nodeExchangePresentation = (
  exchange?: NodeExchangeStatus,
): { transfer: string; compute: string; boundary: string } => {
  const carriers = exchange?.transport?.verified_carriers?.length || 0;
  const peers = exchange?.compute?.peer_nodes?.length || 0;
  return {
    transfer: exchange?.transport?.peer_transport_verified
      ? `Peer transport verified · ${peers} peer node${peers === 1 ? "" : "s"}`
      : carriers
        ? `Carrier readback verified · ${carriers} carrier${carriers === 1 ? "" : "s"} · peer transport unproven`
        : "No verified carrier or peer transport",
    compute: exchange?.compute?.peer_compute_verified
      ? `Peer compute verified · ${peers} peer node${peers === 1 ? "" : "s"}`
      : exchange?.compute?.local_ready
        ? "Local compute ready · peer compute unproven"
        : "Compute unavailable or held",
    boundary: exchange?.claim_boundary || "Node-exchange status is unavailable.",
  };
};

export interface OwnerAuthResponse {
  authenticated: boolean;
  change_required: boolean;
  session_token?: string;
  password_change_token?: string;
  expires_utc?: string;
  credential?: {
    username?: string;
    must_change?: boolean;
    reminder_due?: boolean;
    mandatory_due?: boolean;
    reminder_due_utc?: string | null;
    mandatory_due_utc?: string | null;
  };
}

export interface RepresentationIdentifier {
  identifier_id: string;
  object_id?: string;
  namespace: string;
  identifier_value: string;
  identifier_type: string;
  authority: string;
  is_primary: number | boolean;
  state: string;
}

export interface ObjectRepresentation {
  representation_id: string;
  object_id: string;
  representation_type: string;
  locator_type: string;
  locator: Record<string, unknown>;
  content_sha256?: string | null;
  schema_id?: string | null;
  source_authority: string;
  confidence_numeric: number;
  confidence_class: string;
  evidence_class: string;
  horizon_id?: string | null;
  state: string;
  claim_boundary: string;
}

export interface RepresentationEdge {
  edge_id: string;
  from_representation_id: string;
  to_representation_id: string;
  relation: string;
  evidence_bundle_id?: string | null;
  confidence_numeric: number;
  confidence_class: string;
  claim_boundary: string;
  created_by_floor: string;
  review_state: string;
  owner_decision_id?: string | null;
}

export interface RepresentationHorizon {
  horizon_id: string;
  name: string;
  horizon_type: string;
  objective: string;
  assumptions: Record<string, unknown>;
  constraints: Record<string, unknown>;
  input_set_sha256: string;
  sensitivity_summary: Record<string, unknown>;
  state: string;
}

export interface RepresentationGraph {
  schema_version: string;
  object: {
    object_id: string;
    object_type: string;
    canonical_name: string;
    display_name: string;
    description: string;
    authority: string;
    identity_confidence_numeric: number;
    identity_confidence_class: string;
    state: string;
    metadata: Record<string, unknown>;
  };
  linked_objects?: Array<{
    object_id: string;
    canonical_name: string;
    display_name: string;
    state: string;
    metadata: Record<string, unknown>;
  }>;
  identifiers: RepresentationIdentifier[];
  linked_identifiers?: RepresentationIdentifier[];
  representations: ObjectRepresentation[];
  edges: RepresentationEdge[];
  evidence_bundles?: Array<{
    evidence_bundle_id: string;
    title: string;
    state: string;
    independence_group_count: number;
    duplicate_reference_count: number;
    source_weight_summary: Record<string, unknown>;
    confidence_effect: number;
    claim_boundary: string;
  }>;
  missing: Record<string, unknown>[];
  conflicts: Record<string, unknown>[];
  horizons: RepresentationHorizon[];
  review?: {
    review_id: string;
    state: string;
    review_stage: "identity" | "edges";
    graph_sha256: string;
  } | null;
  decisions: Record<string, unknown>[];
  canonical_state: string;
}

export interface CommandReceipt {
  accepted: boolean;
  task_id?: number;
  job?: Record<string, unknown>;
  command_id?: string;
  state?: string;
  detail?: string;
}

const normalize = (value: string, maximum: number): string =>
  value.replace(/\s+/g, " ").trim().slice(0, maximum);

export const routeInstruction = (instruction: string): Floor => {
  const text = instruction.toLowerCase();
  if (/\b(ui|site|web|design|visual|layout|canva|accessibility)\b/.test(text)) return "Trinity";
  if (/\b(git|github|code|build|commit|branch|deploy|schema|api|runtime)\b/.test(text)) return "Smith";
  if (/\b(source|evidence|research|data|document|drive|sheet|workbook|citation)\b/.test(text)) return "Oracle";
  if (/\b(proof|claim|verify|conflict|confidence|audit)\b/.test(text)) return "Morpheus";
  if (/\b(simulate|simulation|model|gmat|trajectory|twin|physics)\b/.test(text)) return "TheConstruct";
  if (/\b(plan|mission|architecture|dependency|roadmap|system|project)\b/.test(text)) return "Architect";
  if (/\b(health|status|diagnostic|failure|error|monitor|storage|cleanup|archive)\b/.test(text)) return "Merovingian";
  if (/\b(coordinate|queue|handoff|agent|task|execute|run)\b/.test(text)) return "Neo";
  return "Achilles";
};

export const createCommandEnvelope = (input: CommandInput): CommandEnvelope => {
  const instruction = normalize(input.instruction, 4000);
  if (!instruction) throw new TypeError("instruction is required");
  const created = new Date().toISOString();
  const entropy = Math.random().toString(36).slice(2, 8).toUpperCase();
  const targetFloor = input.targetFloor ?? routeInstruction(instruction);
  const authority = input.authorityContract;
  if (!authority) throw new TypeError("Desktop authority contract is not available");
  const canonicalGateId = normalize(authority.canonical_gate_id, 160);
  const ownerDecisionRef = normalize(authority.owner_decision_ref, 160);
  const coreAcceptanceRef = normalize(authority.core_acceptance_ref, 160);
  const approvalState = normalize(authority.approval_or_hold_state, 40).toLowerCase();
  const authorisedScope = normalize(authority.authorised_scope, 1000);
  const prohibitedScope = normalize(authority.prohibited_scope, 1000);
  if (!canonicalGateId || !ownerDecisionRef || !coreAcceptanceRef || !authorisedScope || !prohibitedScope) {
    throw new TypeError("Desktop authority contract is incomplete");
  }
  if (!["approve", "approved", "operator_approved", "operator_authorized", "operator_authorised"].includes(approvalState)) {
    throw new TypeError("Desktop authority contract is held");
  }
  const executionMode = input.executionMode ?? "review";
  return {
    schema_version: COMMAND_SCHEMA,
    command_id: `LSGO-${created.replace(/\D/g, "").slice(0, 14)}-${entropy}`,
    created_utc: created,
    source: "LS GO",
    title: normalize(input.title || instruction, 160),
    instruction,
    target_floor: targetFloor,
    oversight_floor: "Achilles",
    priority: input.priority ?? "normal",
    execution_mode: executionMode,
    action_type: input.actionType ?? "cognigrex_workflow",
    proof_required: true,
    public_safe: true,
    canonical_gate_id: canonicalGateId,
    owner_decision_ref: ownerDecisionRef,
    core_acceptance_ref: coreAcceptanceRef,
    approval_or_hold_state: approvalState,
    authorised_scope: authorisedScope,
    prohibited_scope: prohibitedScope,
    requested_scope: `${targetFloor} private local ${executionMode} queue`,
  };
};

export class DesktopRequestError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "DesktopRequestError";
    this.status = status;
  }
}

const withTimeout = async <T>(url: string, init: RequestInit, timeoutMs = 3500): Promise<T> => {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal, cache: "no-store" });
    if (!response.ok) {
      let detail = `Desktop returned HTTP ${response.status}`;
      try {
        const value = await response.json() as { detail?: string };
        if (value.detail) detail = value.detail;
      } catch {
        // Keep the bounded HTTP detail.
      }
      throw new DesktopRequestError(response.status, detail);
    }
    return (await response.json()) as T;
  } finally {
    window.clearTimeout(timer);
  }
};

export const readDesktopStatus = (origin = DEFAULT_DESKTOP_ORIGIN): Promise<DesktopStatus> =>
  withTimeout<DesktopStatus>(`${origin}/api/v1/status`, { method: "GET" }, 10000);

export const objectContextApiPath = (
  query: string,
  domain?: ObjectContextDomain,
): string => {
  const objectQuery = normalize(query, 160);
  if (!objectQuery) throw new TypeError("object query is required");
  const params = domain ? "?domain=" + encodeURIComponent(domain) : "";
  return "/api/v1/object-context/" + encodeURIComponent(objectQuery) + params;
};

export const resolveDesktopObjectContext = (
  query: string,
  domain?: ObjectContextDomain,
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<ObjectContextResponse> =>
  withTimeout<ObjectContextResponse>(
    origin + objectContextApiPath(query, domain),
    { method: "GET" },
    10000,
  );

export const loginDesktopOwner = (
  username: string,
  password: string,
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<OwnerAuthResponse> =>
  withTimeout<OwnerAuthResponse>(`${origin}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: normalize(username, 64), password: password.slice(0, 1024) }),
  }, 15000);

export const changeDesktopOwnerPassword = (
  username: string,
  currentPassword: string,
  newPassword: string,
  token: string,
  changeOnly: boolean,
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<OwnerAuthResponse> =>
  withTimeout<OwnerAuthResponse>(`${origin}/api/v1/auth/change-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      [changeOnly ? "X-LightSpeed-Password-Change" : "X-LightSpeed-Session"]: token.slice(0, 256),
    },
    body: JSON.stringify({
      username: normalize(username, 64),
      current_password: currentPassword.slice(0, 1024),
      new_password: newPassword.slice(0, 1024),
    }),
  }, 20000);

export const logoutDesktopOwner = (
  sessionToken: string,
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<{ authenticated: boolean }> =>
  withTimeout<{ authenticated: boolean }>(`${origin}/api/v1/auth/logout`, {
    method: "POST",
    headers: { "X-LightSpeed-Session": sessionToken.slice(0, 256) },
  }, 7000);

export const planNodeTransfer = (
  input: NodeTransferPlanInput,
  ownerSession: string,
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<NodeExchangePlanResponse> =>
  withTimeout<NodeExchangePlanResponse>(`${origin}/api/v1/node-exchange/transfer/plan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-LightSpeed-Session": ownerSession.slice(0, 256),
    },
    body: JSON.stringify(input),
  }, 10000);

export const planNodeCompute = (
  input: NodeComputePlanInput,
  ownerSession: string,
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<NodeExchangePlanResponse> =>
  withTimeout<NodeExchangePlanResponse>(`${origin}/api/v1/node-exchange/compute/plan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-LightSpeed-Session": ownerSession.slice(0, 256),
    },
    body: JSON.stringify(input),
  }, 10000);

export interface StagedSource {
  state: "staged";
  source_name: string;
  source_path: string;
  source_sha256: string;
  byte_length: number;
  queue_dispatched: false;
  canonical_mutation: false;
}

const MAX_INTAKE_BYTES = 64 * 1024 * 1024;

export const stageDesktopSource = async (
  file: File, sessionToken: string, origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<StagedSource> => {
  if (!sessionToken) throw new TypeError("Owner sign-in is required to stage a source");
  if (file.size > MAX_INTAKE_BYTES) throw new TypeError("Choose a file no larger than 64 MiB");
  const bytes = await file.arrayBuffer();
  if (bytes.byteLength !== file.size) throw new TypeError("Selected file changed while reading");
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const hash = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, "0")).join("");
  const query = new URLSearchParams({ source_name: file.name, source_sha256: hash });
  const receipt = await withTimeout<StagedSource>(`${origin}/api/v1/source-intake/stage?${query}`, {
    method: "POST", headers: { "Content-Type": "application/octet-stream", "X-LightSpeed-Session": sessionToken },
    body: bytes,
  }, 60000);
  if (receipt.state !== "staged" || receipt.source_name !== file.name || receipt.source_sha256 !== hash
      || receipt.byte_length !== bytes.byteLength || !receipt.source_path
      || receipt.queue_dispatched !== false || receipt.canonical_mutation !== false) {
    throw new TypeError("Desktop staging receipt did not match the selected source");
  }
  return receipt;
};

export const createSourceIntakeCommand = (
  source: StagedSource, authorityContract: AuthorityContract | null,
): CommandEnvelope => {
  if (source.state !== "staged" || !/^[a-f0-9]{64}$/.test(source.source_sha256)
      || !source.source_path || source.queue_dispatched !== false || source.canonical_mutation !== false) {
    throw new TypeError("A verified staging receipt is required");
  }
  return {
    ...createCommandEnvelope({
      title: `Review source: ${source.source_name}`,
      instruction: "Preserve the native source and extract an evidence envelope for independent semantic review. Do not promote or overwrite canonical facts.",
      targetFloor: "Neo", executionMode: "queue", actionType: "source_preserving_intake", authorityContract,
    }),
    action_payload: { source_path: source.source_path, source_sha256: source.source_sha256 },
  };
};

export const submitDesktopCommand = (
  command: CommandEnvelope,
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<CommandReceipt> =>
  withTimeout<CommandReceipt>(`${origin}/api/v1/ls-go/commands`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(command),
  }, 7000);

export const listDesktopTasks = async (origin = DEFAULT_DESKTOP_ORIGIN): Promise<Record<string, unknown>[]> => {
  const response = await withTimeout<{ tasks?: Record<string, unknown>[] }>(
    `${origin}/api/v1/tasks?limit=12`,
    { method: "GET" },
  );
  return Array.isArray(response.tasks) ? response.tasks : [];
};

export const listDesktopProjects = async (origin = DEFAULT_DESKTOP_ORIGIN): Promise<{
  projects: ProjectRecord[];
  summary: Record<string, unknown>;
  duplicateNames: Record<string, unknown>[];
  cleanupSummary: Record<string, unknown>;
}> => {
  const response = await withTimeout<{
    projects?: ProjectRecord[];
    summary?: Record<string, unknown>;
    duplicate_names?: Record<string, unknown>[];
    cleanup_summary?: Record<string, unknown>;
  }>(`${origin}/api/v1/projects`, { method: "GET" }, 15000);
  return {
    projects: Array.isArray(response.projects) ? response.projects : [],
    summary: response.summary || {},
    duplicateNames: Array.isArray(response.duplicate_names) ? response.duplicate_names : [],
    cleanupSummary: response.cleanup_summary || {},
  };
};

export const projectFileApiPath = (projectId: string, relativePath?: string): string => {
  const project = encodeURIComponent(projectId);
  if (relativePath === undefined) return `/api/v1/projects/${project}/files`;
  const path = relativePath.split("/").map((part) => encodeURIComponent(part)).join("/");
  return `/api/v1/projects/${project}/files/${path}`;
};

export const listDesktopProjectFiles = async (
  projectId: string,
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<ProjectFilesResponse> =>
  withTimeout<ProjectFilesResponse>(
    `${origin}${projectFileApiPath(projectId)}?limit=200`,
    { method: "GET" },
    15000,
  );

export const openDesktopProjectFile = async (
  projectId: string,
  relativePath: string,
  ownerSession: string,
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<ProjectFileOpenResult> =>
  withTimeout<ProjectFileOpenResult>(
    `${origin}${projectFileApiPath(projectId, relativePath)}`,
    {
      method: "GET",
      headers: { "X-LightSpeed-Session": ownerSession.slice(0, 256) },
    },
    10000,
  );

export const resultReceiptApiPath = (resultId?: string): string => {
  if (resultId === undefined) return "/api/v1/results";
  return `/api/v1/results/${encodeURIComponent(resultId)}`;
};

export const listDesktopResults = async (
  origin = DEFAULT_DESKTOP_ORIGIN,
  limit = 50,
): Promise<LocalResultsResponse> =>
  withTimeout<LocalResultsResponse>(
    `${origin}${resultReceiptApiPath()}?limit=${Math.max(1, Math.min(limit, 200))}`,
    { method: "GET" },
    10000,
  );

export const openDesktopResult = async (
  resultId: string,
  ownerSession: string,
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<LocalResultOpenResponse> =>
  withTimeout<LocalResultOpenResponse>(
    `${origin}${resultReceiptApiPath(resultId)}`,
    {
      method: "GET",
      headers: { "X-LightSpeed-Session": ownerSession.slice(0, 256) },
    },
    10000,
  );

export const listDesktopReviews = async (
  origin = DEFAULT_DESKTOP_ORIGIN,
  limit = 50,
): Promise<ReviewRecord[]> => {
  const response = await withTimeout<{ reviews?: ReviewRecord[] }>(
    `${origin}/api/v1/reviews?limit=${Math.max(1, Math.min(limit, 200))}`,
    { method: "GET" },
    10000,
  );
  return Array.isArray(response.reviews) ? response.reviews : [];
};

export const decideDesktopReview = async (
  reviewId: string,
  decision: ReviewDecision,
  note = "",
  ownerSession = "",
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<ReviewDecisionResponse> =>
  withTimeout<ReviewDecisionResponse>(
    `${origin}/api/v1/reviews/${encodeURIComponent(reviewId)}/decision`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-LightSpeed-Session": ownerSession.slice(0, 256),
      },
      body: JSON.stringify({ decision, note: normalize(note, 1000) }),
    },
    7000,
  );

export const reviewDecisionOutcomeMessage = (
  reviewId: string,
  decision: ReviewDecision,
  response: ReviewDecisionResponse,
): string => {
  const mode = response.receipt?.drive_writeback_mode;
  if (mode === "owner_approved_exact_drive_target") {
    return `${reviewId} marked ${decision}. Owner-approved Drive decision receipt written by Desktop.`;
  }
  if (mode === "local_outbox_pending_drive_sync") {
    return `${reviewId} marked ${decision}. Local outbox receipt staged; Drive sync remains pending.`;
  }
  return `${reviewId} marked ${decision}. Decision receipt recorded; destination requires verification.`;
};

export const listRepresentationGraphs = async (
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<RepresentationGraph[]> => {
  const response = await withTimeout<{ graphs?: RepresentationGraph[] }>(
    `${origin}/api/v1/representation-graphs`,
    { method: "GET" },
    15000,
  );
  return Array.isArray(response.graphs) ? response.graphs : [];
};

export const decideRepresentationReview = async (
  reviewId: string,
  decision: RepresentationDecision,
  scope: "identity" | "edges",
  edgeIds: string[] = [],
  note = "",
  ownerSession = "",
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<Record<string, unknown>> =>
  withTimeout<Record<string, unknown>>(
    `${origin}/api/v1/representation-reviews/${encodeURIComponent(reviewId)}/decision`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-LightSpeed-Session": ownerSession.slice(0, 256),
      },
      body: JSON.stringify({
        decision,
        scope,
        edge_ids: edgeIds.slice(0, 100),
        note: normalize(note, 1000),
      }),
    },
    10000,
  );

const STORAGE_KEY = "lightspeed-go-pending-commands-v1";

export const readPendingCommands = (): CommandEnvelope[] => {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]") as unknown;
    return Array.isArray(value) ? (value as CommandEnvelope[]) : [];
  } catch {
    return [];
  }
};

export const storePendingCommand = (command: CommandEnvelope): CommandEnvelope[] => {
  const current = readPendingCommands().filter((item) => item.command_id !== command.command_id);
  const next = [command, ...current].slice(0, 30);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
};

export const removePendingCommand = (commandId: string): CommandEnvelope[] => {
  const next = readPendingCommands().filter((item) => item.command_id !== commandId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
};

export const downloadCommand = (command: CommandEnvelope): void => {
  const blob = new Blob([JSON.stringify(command, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${command.command_id}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
};
