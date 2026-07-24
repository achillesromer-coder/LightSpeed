import { describe, expect, it } from "vitest";

import type { RepresentationGraph } from "./desktopBridge";
import { graphJudgment, renderRepresentationGraph, renderRepresentationGraphs } from "./representationGraphs";

const fixture = (objectId: string, missing = 1): RepresentationGraph => ({
  schema_version: "cognigrex-representation-edge-v1",
  object: {
    object_id: objectId,
    object_type: "proof_object",
    canonical_name: objectId,
    display_name: `Proof ${objectId}`,
    description: "A bounded proof graph.",
    authority: "Nathaniel",
    identity_confidence_numeric: 0.8,
    identity_confidence_class: "high",
    state: "candidate",
    metadata: {},
  },
  identifiers: [{
    identifier_id: `${objectId}:id`,
    namespace: "internal",
    identifier_value: objectId,
    identifier_type: "internal",
    authority: "Nathaniel",
    is_primary: 1,
    state: "active",
  }],
  representations: [
    {
      representation_id: `${objectId}:source`,
      object_id: objectId,
      representation_type: "empirical_source",
      locator_type: "git_file",
      locator: { repository: "owner/repo", commit_sha: "a".repeat(40), path: "data.json" },
      content_sha256: "b".repeat(64),
      source_authority: "test",
      confidence_numeric: 0.8,
      confidence_class: "high",
      evidence_class: "test",
      state: "active",
      claim_boundary: "Does not establish capability.",
    },
    ...Array.from({ length: missing }, (_, index) => ({
      representation_id: `${objectId}:missing:${index}`,
      object_id: objectId,
      representation_type: "mesh",
      locator_type: "missing",
      locator: {
        missing_state: "searched_not_found",
        reason: "Not found.",
        last_search: "2026-07-24 accepted evidence baseline",
        assigned_floor: "Oracle",
        next_evidence_action: "Search an approved source.",
        dependency_effect: "Recommendation remains provisional.",
      },
      content_sha256: null,
      source_authority: "none",
      confidence_numeric: 0,
      confidence_class: "unknown",
      evidence_class: "missing",
      state: "missing",
      claim_boundary: "No shape claim.",
    })),
    {
      representation_id: `${objectId}:recommendation`,
      object_id: objectId,
      representation_type: "recommendation",
      locator_type: "logical",
      locator: { next_highest_value_question: "What evidence closes the gap?" },
      content_sha256: "c".repeat(64),
      source_authority: "Architect",
      confidence_numeric: 0.4,
      confidence_class: "moderate",
      evidence_class: "candidate",
      state: "provisional",
      claim_boundary: "Candidate only.",
    },
  ],
  edges: [{
    edge_id: `${objectId}:edge`,
    from_representation_id: `${objectId}:recommendation`,
    to_representation_id: `${objectId}:source`,
    relation: "depends_on",
    evidence_bundle_id: null,
    confidence_numeric: 0.5,
    confidence_class: "moderate",
    claim_boundary: "Bounded.",
    created_by_floor: "Architect",
    review_state: "pending",
  }],
  missing: Array.from({ length: missing }, (_, index) => ({
    representation_id: `${objectId}:missing:${index}`,
    type: "mesh",
    missing_state: "searched_not_found",
    reason: "Not found.",
    last_search: "2026-07-24 accepted evidence baseline",
    assigned_floor: "Oracle",
    next_evidence_action: "Search an approved source.",
    dependency_effect: "Recommendation remains provisional.",
  })),
  conflicts: [],
  horizons: [{
    horizon_id: `${objectId}:horizon`,
    name: "Bounded horizon",
    horizon_type: "candidate",
    objective: "Answer one question.",
    assumptions: {},
    constraints: {},
    input_set_sha256: "d".repeat(64),
    sensitivity_summary: {},
    state: "candidate",
  }],
  review: {
    review_id: `${objectId}:review`,
    state: "pending_identity_review",
    review_stage: "identity",
    graph_sha256: "e".repeat(64),
  },
  decisions: [],
  canonical_state: "local_candidate_pending_owner_and_drive_readback",
});

describe("canonical representation graph view", () => {
  it("renders identity, representations, edges, missing, horizon and review actions", () => {
    const html = renderRepresentationGraph(fixture("ASPHA.0001"));
    expect(html).toContain("ASPHA.0001");
    expect(html).toContain("Representations (3)");
    expect(html).toContain("Edges (1)");
    expect(html).toContain("searched_not_found");
    expect(html).toContain("Last search: 2026-07-24 accepted evidence baseline");
    expect(html).toContain("Recommendation remains provisional.");
    expect(html).toContain("Bounded horizon");
    expect(html).toContain("Review identity first");
    expect(html).toContain('data-decision="supersede"');
    expect(html).toContain("What evidence closes the gap?");
    expect(html).not.toContain("D:\\");
  });

  it("renders all three proof graphs", () => {
    const html = renderRepresentationGraphs([
      fixture("ASPHA.0001"),
      fixture("engineering-twin:rfs-emff-sandbox", 5),
      fixture("de-sporte-05d89c2a", 2),
    ]);
    expect((html.match(/class="panel graph-panel"/g) || []).length).toBe(3);
  });

  it("reports bowl judgment from current evidence and missing links", () => {
    expect(graphJudgment(fixture("larger", 0))).toBe("larger bowl");
    expect(graphJudgment(fixture("unchanged", 1))).toBe("unchanged bowl");
    expect(graphJudgment(fixture("smaller", 3))).toBe("smaller bowl");
  });
});
