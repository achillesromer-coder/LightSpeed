/* Private LS GO owner-review packet projection.
 * Source-only adapter for the existing Achilles PR #217 review packet.
 * The caller MUST obtain the packet through an authenticated, scope-checked
 * private bridge. This pure function is NOT authentication or DBR admission.
 * Never import personal GPT/Drive bodies into Vite public/ or its dist.
 */
export type OwnerPacketProjection = Readonly<{
  task_id: string;
  project_id: string;
  semantic_parent: "cgx:root:cognigrex";
  child_domain: "emassc";
  evidence_class: "SOURCE_ONLY_REVIEW";
  admission_stage: "NOT_NATIVE_ADMITTED";
  state: "REVIEW_ONLY_NOT_DISPATCHED";
  owner_decision: "PENDING";
  review_fingerprint: string;
  private_source_count: number;
  runtime_host_readback: "NOT_PERFORMED";
  signed_review_link: null;
  can_execute: false;
}>;

const SHA256 = /^[0-9a-f]{64}$/i;
const TASK_ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$/;
const PROJECT_ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$/;
const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const hold = (): never => { throw new Error("OWNER_PACKET_REVIEW_HOLD"); };

/** Render-safe, deliberately minimal projection; never a credential check. */
export function projectOwnerReviewPacket(input: unknown): OwnerPacketProjection {
  if (!record(input)) throw new Error("OWNER_PACKET_REVIEW_HOLD");
  if (input.schema !== "CGX-ACHILLES-OWNER-REVIEW-PACKET/0.1" ||
      input.state !== "REVIEW_ONLY_NOT_DISPATCHED" ||
      input.selector !== "achilles" ||
      input.authority_domain !== "emassc" ||
      input.semantic_parent !== "cgx:root:cognigrex" ||
      input.source_admission !== "NOT_INFERRED_FROM_IDENTIFIERS_OR_DIGESTS" ||
      input.runtime_host_readback !== "NOT_PERFORMED") hold();

  const taskId = input.Task_ID;
  const projectId = input.project_id;
  const fingerprint = input.idempotency_fingerprint;
  if (typeof taskId !== "string" || !TASK_ID.test(taskId) ||
      typeof projectId !== "string" || !PROJECT_ID.test(projectId) ||
      typeof fingerprint !== "string" || !SHA256.test(fingerprint)) {
    throw new Error("OWNER_PACKET_REVIEW_HOLD");
  }

  const count = input.private_source_count;
  const digests = input.private_source_id_hashes;
  if (typeof count !== "number" || !Number.isSafeInteger(count) || count < 0 ||
      (count as number) > 100 || !Array.isArray(digests) ||
      digests.length !== count || new Set(digests).size !== digests.length ||
      !digests.every((digest: unknown) => typeof digest === "string" && SHA256.test(digest))) hold();

  const auth = input.authorization;
  const request = input.execution_request;
  const supervisor = input.supervisor;
  if (!record(auth) || !record(request) || !record(supervisor) ||
      auth.owner_decision !== "PENDING" ||
      auth.lease_verified !== false ||
      auth.native_dbr_admitted !== false ||
      auth.canonical_promotion_authorized !== false ||
      auth.external_release_authorized !== false ||
      auth.no_self_approval !== true ||
      !Array.isArray(auth.effective_tool_permissions) ||
      auth.effective_tool_permissions.length !== 0 ||
      request.execute !== false || request.preflight_only !== true ||
      request.execution_class !== "READ_ONLY" ||
      supervisor.execution !== false) hold();

  // Deliberately omit raw instructions, source IDs/digests, host paths,
  // execution arguments and untrusted review URLs. A signed link requires
  // an independently verified owner session and a separate server contract.
  return Object.freeze({
    task_id: taskId,
    project_id: projectId,
    semantic_parent: "cgx:root:cognigrex" as const,
    child_domain: "emassc" as const,
    evidence_class: "SOURCE_ONLY_REVIEW" as const,
    admission_stage: "NOT_NATIVE_ADMITTED" as const,
    state: "REVIEW_ONLY_NOT_DISPATCHED" as const,
    owner_decision: "PENDING" as const,
    review_fingerprint: fingerprint,
    private_source_count: count as number,
    runtime_host_readback: "NOT_PERFORMED" as const,
    signed_review_link: null,
    can_execute: false as const,
  });
}


/** Owner-private R0 index manifest view, NOT source verification or native admission.
 * Caller must obtain the original manifest from an authenticated owner-scoped
 * provider. This pure projection neither authenticates nor reads GPT shards.
 * A manifest's self-reported digest match is NOT independent byte readback.
 */
export type PrivateSandboxManifestProjection = Readonly<{
  semantic_parent: "cgx:root:cognigrex";
  presentation_scope: "private_unispace_operator";
  selected_object_id: null;
  selected_filespace: null;
  evidence_class: "MANIFEST_REPORTED_NOT_INDEPENDENT_R0_READBACK";
  admission_stage: "SANDBOX_SOURCE_INDEX_ONLY";
  source_shard_count: 12;
  distinct_message_refs: number;
  repeated_message_occurrences: number;
  rights_state: "HOLD_OWNER_REVIEW";
  runtime_host_readback: "NOT_PERFORMED";
  signed_review_link: null;
  can_execute: false;
}>;

export function projectPrivateSandboxManifest(input: unknown): PrivateSandboxManifestProjection {
  if (!record(input)) throw new Error("OWNER_PACKET_REVIEW_HOLD");
  if (input.schema !== "CGX-PRIVATE-SOURCE-SANDBOX/0.1" ||
      input.status !== "SANDBOX_SOURCE_INDEX_READY_NOT_CANONICAL" ||
      input.canonical_target !== "Cognigrex.cgx" ||
      input.semantic_root_reference !== "cgx:root:cognigrex" ||
      input.data_protection !== "PRIVATE_OWNER_ONLY; contains conversation titles and hashes; do not place in public Git" ||
      input.native_root_minted !== false ||
      input.physical_originals_modified !== false) hold();

  const counts = input.index_counts;
  const gates = input.gates;
  const entries = input.source_verification;
  const occurrences = input.raw_export_message_occurrences;
  const duplicates = input.repeat_identity_occurrences;
  if (!record(counts) || !record(gates) || !Array.isArray(entries) ||
      entries.length !== 12 || counts.source_shards !== 12 ||
      !Number.isSafeInteger(counts.distinct_messages) ||
      (counts.distinct_messages as number) < 0 ||
      !Number.isSafeInteger(occurrences) || !Number.isSafeInteger(duplicates) ||
      (occurrences as number) < (counts.distinct_messages as number) ||
      (duplicates as number) < 0 ||
      (occurrences as number) - (counts.distinct_messages as number) !== duplicates ||
      gates.full_R1_reversible_parse !== "NOT_CLAIMED_SOURCE_INDEX_EXCLUDES_FULL_BODIES" ||
      gates.rights_ACL !== "HOLD_OWNER_REVIEW" ||
      gates.native_DBR_mint !== "HOLD" ||
      gates.public_R3 !== "HOLD_PRIVATE_SOURCE") hold();

  const seen = new Set<string>();
  for (let i = 0; i < 12; i++) {
    const entry: unknown = entries[i];
    if (!record(entry)) throw new Error("OWNER_PACKET_REVIEW_HOLD");
    if (entry.shard !== `conversations-${String(i).padStart(3, "0")}.json` ||
        entry.verified !== true ||
        typeof entry.expected_sha256 !== "string" ||
        !SHA256.test(entry.expected_sha256) ||
        entry.expected_sha256 !== entry.observed_sha256 ||
        seen.has(entry.expected_sha256) ||
        !Number.isSafeInteger(entry.size) || (entry.size as number) <= 0) hold();
    seen.add(entry.expected_sha256);
  }

  // Never emit private filenames, SHA values, source titles, message bodies,
  // candidate domain assignments, raw locators or executable permissions.
  return Object.freeze({
    semantic_parent: "cgx:root:cognigrex" as const,
    presentation_scope: "private_unispace_operator" as const,
    selected_object_id: null,
    selected_filespace: null,
    evidence_class: "MANIFEST_REPORTED_NOT_INDEPENDENT_R0_READBACK" as const,
    admission_stage: "SANDBOX_SOURCE_INDEX_ONLY" as const,
    source_shard_count: 12 as const,
    distinct_message_refs: counts.distinct_messages as number,
    repeated_message_occurrences: duplicates as number,
    rights_state: "HOLD_OWNER_REVIEW" as const,
    runtime_host_readback: "NOT_PERFORMED" as const,
    signed_review_link: null,
    can_execute: false as const,
  });
}
