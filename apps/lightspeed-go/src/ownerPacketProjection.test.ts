import { describe, expect, it } from "vitest";
import { projectOwnerReviewPacket, projectPrivateSandboxManifest } from "./ownerPacketProjection";

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


// Synthetic manifest fixture only: no private GPT shards, filenames from
// owner sources, hashes, source titles, paths or raw content enter this file.
function syntheticManifest(): Record<string, unknown> {
  return {
    schema: "CGX-PRIVATE-SOURCE-SANDBOX/0.1",
    status: "SANDBOX_SOURCE_INDEX_READY_NOT_CANONICAL",
    canonical_target: "Cognigrex.cgx",
    semantic_root_reference: "cgx:root:cognigrex",
    data_protection: "PRIVATE_OWNER_ONLY; contains conversation titles and hashes; do not place in public Git",
    native_root_minted: false,
    physical_originals_modified: false,
    source_verification: Array.from({ length: 12 }, (_, i) => ({
      shard: `conversations-${String(i).padStart(3, "0")}.json`,
      expected_sha256: (i + 1).toString(16).padStart(64, "0"),
      observed_sha256: (i + 1).toString(16).padStart(64, "0"),
      verified: true, size: 100 + i,
    })),
    index_counts: { source_shards: 12, distinct_messages: 3 },
    raw_export_message_occurrences: 4,
    repeat_identity_occurrences: 1,
    gates: {
      full_R1_reversible_parse: "NOT_CLAIMED_SOURCE_INDEX_EXCLUDES_FULL_BODIES",
      rights_ACL: "HOLD_OWNER_REVIEW",
      native_DBR_mint: "HOLD",
      public_R3: "HOLD_PRIVATE_SOURCE",
    },
    raw_private_title: "SYNTHETIC SECRET TITLE",
    private_source_locator: "owner-private://SYNTHETIC",
  };
}
const rejectedManifest = (p: Record<string, unknown>) =>
  expect(() => projectPrivateSandboxManifest(p)).toThrow("OWNER_PACKET_REVIEW_HOLD");

describe("UniSpace private sandbox manifest metadata projection", () => {
  it("emits only owner-scope status with no selected Object_ID or private sources", () => {
    const input = syntheticManifest();
    const view = projectPrivateSandboxManifest(input);
    expect(view.semantic_parent).toBe("cgx:root:cognigrex");
    expect(view.presentation_scope).toBe("private_unispace_operator");
    expect(view.selected_object_id).toBeNull();
    expect(view.selected_filespace).toBeNull();
    expect(view.admission_stage).toBe("SANDBOX_SOURCE_INDEX_ONLY");
    expect(view.evidence_class).toBe("MANIFEST_REPORTED_NOT_INDEPENDENT_R0_READBACK");
    expect(view.distinct_message_refs).toBe(3);
    expect(view.repeated_message_occurrences).toBe(1);
    expect(view.can_execute).toBe(false);
    expect(view.signed_review_link).toBeNull();
    const serialized = JSON.stringify(view);
    for (const forbidden of [
      "SYNTHETIC SECRET TITLE", "owner-private://", "conversations-",
      "source_verification", "expected_sha256", "raw_private_title",
      (input.source_verification as Array<{ expected_sha256: string }>)[0].expected_sha256,
    ]) expect(serialized).not.toContain(forbidden);
    expect(Object.isFrozen(view)).toBe(true);
  });

  it("rejects fake native root, public rights and admission upgrades", () => {
    for (const [key, value] of [
      ["native_root_minted", true],
      ["physical_originals_modified", true],
      ["semantic_root_reference", "cgx:root:other"],
      ["data_protection", "PUBLIC"],
      ["status", "NATIVE_ADMITTED"],
    ] as const) {
      const p = syntheticManifest(); p[key] = value; rejectedManifest(p);
    }
    for (const [key, value] of [
      ["rights_ACL", "APPROVED"],
      ["native_DBR_mint", "PASS"],
      ["public_R3", "RELEASED"],
      ["full_R1_reversible_parse", "PASS"],
    ] as const) {
      const p = syntheticManifest(); p.gates = { ...(p.gates as object), [key]: value };
      rejectedManifest(p);
    }
  });

  it("rejects missing, reordered, forged or duplicate shard evidence", () => {
    const a = syntheticManifest();
    a.source_verification = (a.source_verification as unknown[]).slice(1);
    rejectedManifest(a);
    const b = syntheticManifest();
    (b.source_verification as Record<string, unknown>[])[0].observed_sha256 = "f".repeat(64);
    rejectedManifest(b);
    const c = syntheticManifest();
    (c.source_verification as Record<string, unknown>[])[1].expected_sha256 =
      (c.source_verification as Record<string, unknown>[])[0].expected_sha256;
    (c.source_verification as Record<string, unknown>[])[1].observed_sha256 =
      (c.source_verification as Record<string, unknown>[])[0].observed_sha256;
    rejectedManifest(c);
    const d = syntheticManifest();
    (d.source_verification as Record<string, unknown>[])[0].shard = "../../private.json";
    rejectedManifest(d);
  });

  it("rejects inconsistent unique/repeated occurrence counts", () => {
    const a = syntheticManifest(); a.repeat_identity_occurrences = 2; rejectedManifest(a);
    const b = syntheticManifest(); b.index_counts = { source_shards: 11, distinct_messages: 3 }; rejectedManifest(b);
    const c = syntheticManifest(); c.raw_export_message_occurrences = 2; rejectedManifest(c);
    const d = syntheticManifest(); d.index_counts = { source_shards: 12, distinct_messages: -1 }; rejectedManifest(d);
  });
});
