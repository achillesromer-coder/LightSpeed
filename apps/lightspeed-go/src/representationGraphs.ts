import type { RepresentationGraph } from "./desktopBridge";

const escapeHtml = (value: unknown): string =>
  String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

const truncateHash = (value?: string | null): string =>
  value ? `${value.slice(0, 12)}…${value.slice(-8)}` : "not available";

const locatorSummary = (locator: Record<string, unknown>): string => {
  if (locator.path_exposed === false) return String(locator.label || "private local evidence");
  const parts = [
    locator.repository,
    locator.commit_sha ? `commit ${String(locator.commit_sha).slice(0, 12)}` : null,
    locator.path,
    locator.drive_file_id ? `Drive ${locator.drive_file_id}` : null,
    locator.sheet_name,
    locator.stable_key || locator.content_key,
    locator.missing_state,
  ].filter(Boolean);
  return parts.map(escapeHtml).join(" · ") || escapeHtml(locator.locator_type || "logical");
};

const jsonSummary = (value: Record<string, unknown>): string =>
  escapeHtml(JSON.stringify(value, null, 2));

export const graphJudgment = (graph: RepresentationGraph): string => {
  const active = graph.representations.filter((item) => item.state === "active").length;
  const missing = graph.missing.length;
  if (!active && missing) return "unable to determine";
  if (missing > active) return "smaller bowl";
  if (active > missing) return "larger bowl";
  return "unchanged bowl";
};

export const renderRepresentationGraph = (graph: RepresentationGraph): string => {
  const review = graph.review;
  const stage = review?.review_stage || "identity";
  const edgeIds = graph.edges.map((edge) => edge.edge_id).join("|");
  const controls = review ? `
    <div class="graph-actions" data-review-stage="${escapeHtml(stage)}">
      <strong>${stage === "identity" ? "Review identity first" : `Review ${graph.edges.length} bounded edges`}</strong>
      <div class="task-actions">
        <button data-representation-review="${escapeHtml(review.review_id)}" data-scope="${stage}" data-edge-ids="${escapeHtml(edgeIds)}" data-decision="approve">Approve</button>
        <button data-representation-review="${escapeHtml(review.review_id)}" data-scope="${stage}" data-edge-ids="${escapeHtml(edgeIds)}" data-decision="provisional_approve">Provisional</button>
        <button data-representation-review="${escapeHtml(review.review_id)}" data-scope="${stage}" data-edge-ids="${escapeHtml(edgeIds)}" data-decision="hold">Hold</button>
        <button data-representation-review="${escapeHtml(review.review_id)}" data-scope="${stage}" data-edge-ids="${escapeHtml(edgeIds)}" data-decision="request_evidence">Request evidence</button>
        <button data-representation-review="${escapeHtml(review.review_id)}" data-scope="${stage}" data-edge-ids="${escapeHtml(edgeIds)}" data-decision="reject">Reject</button>
        <button data-representation-review="${escapeHtml(review.review_id)}" data-scope="${stage}" data-edge-ids="${escapeHtml(edgeIds)}" data-decision="supersede">Supersede</button>
      </div>
      <small>${escapeHtml(review.state)} · graph ${truncateHash(review.graph_sha256)}</small>
    </div>` : `<p class="muted">Review packet has not been staged.</p>`;

  const representations = graph.representations.map((row) => `
    <tr>
      <td><strong>${escapeHtml(row.representation_type)}</strong><small>${escapeHtml(row.representation_id)}</small></td>
      <td>${locatorSummary(row.locator)}</td>
      <td>${escapeHtml(row.source_authority)}</td>
      <td>${truncateHash(row.content_sha256)}</td>
      <td>${escapeHtml(row.confidence_class)} (${Math.round(row.confidence_numeric * 100)}%)</td>
      <td><span class="state-chip" data-state="${escapeHtml(row.state)}">${escapeHtml(row.state)}</span></td>
      <td>${escapeHtml(row.claim_boundary)}</td>
    </tr>`).join("");

  const edges = graph.edges.map((edge) => `
    <tr>
      <td>${escapeHtml(edge.from_representation_id)}</td>
      <td><strong>${escapeHtml(edge.relation)}</strong></td>
      <td>${escapeHtml(edge.to_representation_id)}</td>
      <td>${escapeHtml(edge.evidence_bundle_id || "not required")}</td>
      <td>${escapeHtml(edge.review_state)}</td>
      <td>${escapeHtml(edge.claim_boundary)}</td>
    </tr>`).join("");

  const missing = graph.missing.length
    ? graph.missing.map((row) => `
      <article class="missing-card">
        <strong>${escapeHtml(row.type)} · ${escapeHtml(row.missing_state)}</strong>
        <span><b>Why:</b> ${escapeHtml(row.reason)}</span>
        <span><b>Next:</b> ${escapeHtml(row.next_evidence_action)}</span>
        <small>Last search: ${escapeHtml(row.last_search || "not recorded")} · Floor: ${escapeHtml(row.assigned_floor)} · Effect: ${escapeHtml(row.dependency_effect)}</small>
      </article>`).join("")
    : `<p class="muted">No required representation is currently missing.</p>`;

  const conflicts = graph.conflicts.length
    ? graph.conflicts.map((row) => `<article class="missing-card conflict"><strong>${escapeHtml(row.edge_id)}</strong><span>${escapeHtml(row.claim_boundary)}</span></article>`).join("")
    : `<p class="muted">No representation conflict is recorded.</p>`;

  const horizons = graph.horizons.length
    ? graph.horizons.map((horizon) => `
      <article class="horizon-card">
        <div><strong>${escapeHtml(horizon.name)}</strong><span>${escapeHtml(horizon.state)} · ${escapeHtml(horizon.horizon_type)}</span></div>
        <p>${escapeHtml(horizon.objective)}</p>
        <details><summary>Assumptions and constraints</summary><pre>${jsonSummary({ assumptions: horizon.assumptions, constraints: horizon.constraints })}</pre></details>
        <small>Input ${truncateHash(horizon.input_set_sha256)}</small>
      </article>`).join("")
    : `<p class="muted">No horizon is assigned.</p>`;

  const nextQuestion = graph.representations
    .find((row) => row.representation_type === "recommendation")
    ?.locator.next_highest_value_question;

  return `
    <article class="panel graph-panel" data-object-id="${escapeHtml(graph.object.object_id)}">
      <div class="panel-head">
        <div>
          <p class="eyebrow">${escapeHtml(graph.object.object_type)}</p>
          <h2>${escapeHtml(graph.object.display_name)}</h2>
          <p>${escapeHtml(graph.object.description)}</p>
        </div>
        <span class="badge">${escapeHtml(graph.canonical_state)}</span>
      </div>
      <div class="graph-summary">
        <div><span>Object ID</span><strong>${escapeHtml(graph.object.object_id)}</strong></div>
        <div><span>Authority</span><strong>${escapeHtml(graph.object.authority)}</strong></div>
        <div><span>Identity</span><strong>${escapeHtml(graph.object.identity_confidence_class)} · ${Math.round(graph.object.identity_confidence_numeric * 100)}%</strong></div>
        <div><span>Current horizon</span><strong>${escapeHtml(graph.horizons[0]?.name || "not assigned")}</strong></div>
        <div><span>Judgment</span><strong>${graphJudgment(graph)}</strong></div>
      </div>
      <details open><summary>Identifiers (${graph.identifiers.length})</summary><div class="identifier-list">${graph.identifiers.map((item) => `<span><strong>${escapeHtml(item.namespace)}</strong>${escapeHtml(item.identifier_value)} · ${escapeHtml(item.authority)}</span>`).join("")}</div></details>
      <details open><summary>Representations (${graph.representations.length})</summary><div class="table-scroll"><table class="graph-table"><thead><tr><th>Type</th><th>Locator</th><th>Authority</th><th>Hash/revision</th><th>Confidence</th><th>State</th><th>Claim boundary</th></tr></thead><tbody>${representations}</tbody></table></div></details>
      <details open><summary>Edges (${graph.edges.length})</summary><div class="table-scroll"><table class="graph-table"><thead><tr><th>Source</th><th>Relation</th><th>Destination</th><th>Evidence</th><th>Review</th><th>Boundary</th></tr></thead><tbody>${edges}</tbody></table></div></details>
      <div class="graph-grid">
        <section><h3>Missing</h3>${missing}</section>
        <section><h3>Conflicts</h3>${conflicts}</section>
      </div>
      <section><h3>Horizon</h3>${horizons}</section>
      <div class="next-question"><strong>Next highest-value question</strong><span>${escapeHtml(nextQuestion || "Owner review determines the next bounded question.")}</span></div>
      ${controls}
    </article>`;
};

export const renderRepresentationGraphs = (graphs: RepresentationGraph[]): string =>
  graphs.length
    ? graphs.map(renderRepresentationGraph).join("")
    : `<article class="panel"><p class="muted">The feature-gated representation edge is disabled or unavailable.</p></article>`;
