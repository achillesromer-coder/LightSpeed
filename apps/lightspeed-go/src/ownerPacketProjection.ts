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
