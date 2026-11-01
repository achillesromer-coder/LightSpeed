import { describe, expect, it } from "vitest";
import { projectOwnerReviewPacket } from "./ownerPacketProjection";

const secretInstruction = "PRIVATE GPT TRANSCRIPT BODY NEVER DISPLAY";
const privateLocator = "owner-private://shard/conversations-008.json";
const hashA = "a".repeat(64);
const fingerprint = "b".repeat(64);

function packet(): Record<string, unknown> {
  return {
    schema: "CGX-ACHILLES-OWNER-REVIEW-PACKET/0.1",
    state: "REVIEW_ONLY_NOT_DISPATCHED",
    selector: "achilles",
    authority_domain: "emassc",
    semantic_parent: "cgx:root:cognigrex",
    source_admission: "NOT_INFERRED_FROM_IDENTIFIERS_OR_DIGESTS",
    runtime_host_readback: "NOT_PERFORMED",
    Task_ID: "ACHILLES-REVIEW-001",
    project_id: "UniSpace",
    idempotency_fingerprint: fingerprint,
    private_source_count: 1,
    private_source_id_hashes: [hashA],
    raw_instruction: secretInstruction,
    private_source_locator: privateLocator,
    authorization: {
      owner_decision: "PENDING", lease_verified: false,
      native_dbr_admitted: false, canonical_promotion_authorized: false,
      external_release_authorized: false, no_self_approval: true,
      effective_tool_permissions: [],
    },
    execution_request: {
      execute: false, preflight_only: true, execution_class: "READ_ONLY",
    },
    supervisor: { execution: false },
  };
}
const rejected = (p: Record<string, unknown>) =>
  expect(() => projectOwnerReviewPacket(p)).toThrow("OWNER_PACKET_REVIEW_HOLD");

describe("UniSpace private Achilles owner-packet source-only projection", () => {
  it("projects exactly one EMASSC-scoped task without private source bodies", () => {
    const view = projectOwnerReviewPacket(packet());
    expect(view.task_id).toBe("ACHILLES-REVIEW-001");
    expect(view.child_domain).toBe("emassc");
    expect(view.semantic_parent).toBe("cgx:root:cognigrex");
    expect(view.evidence_class).toBe("SOURCE_ONLY_REVIEW");
    expect(view.admission_stage).toBe("NOT_NATIVE_ADMITTED");
    expect(view.signed_review_link).toBeNull();
    expect(view.can_execute).toBe(false);
    const serialized = JSON.stringify(view);
    for (const forbidden of [secretInstruction, privateLocator, hashA,
      "private_source_id_hashes", "raw_instruction", "execution_request"]) {
      expect(serialized).not.toContain(forbidden);
    }
    expect(Object.isFrozen(view)).toBe(true);
  });

  it("rejects wrong parent, child, selector and schema", () => {
    for (const [key, value] of [
      ["semantic_parent", "cgx:root:other"],
      ["authority_domain", "eco"],
      ["selector", "neo"],
      ["schema", "CGX-ACHILLES-OWNER-REVIEW-PACKET/9"],
    ] as const) { const p = packet(); p[key] = value; rejected(p); }
  });

  it("rejects fabricated owner, lease, DBR, release or tool authority", () => {
    for (const [key, value] of [
      ["owner_decision", "APPROVED"],
      ["lease_verified", true],
      ["native_dbr_admitted", true],
      ["canonical_promotion_authorized", true],
      ["external_release_authorized", true],
      ["no_self_approval", false],
      ["effective_tool_permissions", ["execute"]],
    ] as const) {
      const p = packet(); p.authorization = { ...(p.authorization as object), [key]: value };
      rejected(p);
    }
  });

  it("rejects execution and forged host readback", () => {
    for (const [key, value] of [
      ["execute", true], ["preflight_only", false], ["execution_class", "WRITE"],
    ] as const) {
      const p = packet(); p.execution_request = { ...(p.execution_request as object), [key]: value };
      rejected(p);
    }
    const p = packet(); p.runtime_host_readback = "VERIFIED"; rejected(p);
    const q = packet(); q.supervisor = { execution: true }; rejected(q);
  });

  it("rejects untrusted task labels, fingerprints and source cardinality", () => {
    for (const id of ["../../private", "<img onerror=alert(1)>", "x".repeat(129)]) {
      const p = packet(); p.Task_ID = id; rejected(p);
    }
    const a = packet(); a.idempotency_fingerprint = "not-a-hash"; rejected(a);
    const b = packet(); b.private_source_count = 2; rejected(b);
    const c = packet(); c.private_source_id_hashes = [hashA, hashA]; c.private_source_count = 2; rejected(c);
  });

  it("rejects null, arrays and unknown source-admission state", () => {
    expect(() => projectOwnerReviewPacket(null)).toThrow();
    expect(() => projectOwnerReviewPacket([])).toThrow();
    const p = packet(); p.source_admission = "ADMITTED"; rejected(p);
  });
});
