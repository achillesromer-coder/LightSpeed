export type CgxReviewProjection = {
  schema: string;
  generated_from: string;
  visibility: string;
  authority: {
    engineering_owner: string;
    implementation_mirror: string;
    queue_id: string;
    physical_state: string;
  };
  headline: { title: string; state: string; note: string };
  metrics: Record<string, number>;
  gate_counts: Record<string, number>;
  instances: Array<{
    instance_id: string;
    proof_stage: string;
    archetype: string;
    binding_progress: string;
    first_open_gate: string;
    physical_state: string;
    binding_uri: string;
    target: string;
    next: string;
  }>;
  kernels: Array<{ kernel_id: string; primitive: string; model: string; gate: string }>;
  volumetric_kernels: Array<{ kernel_id: string; primitive: string; topology: string; token: string; gate: string }>;
  topology_coverage: {
    artifact_id: string;
    queue_id: string;
    baseline_generic_only: number;
    first_pass_generic_only: number;
    final_generic_only: number;
    specific_or_multi: number;
    total_archetypes: number;
    residual: string[];
    rule: string;
  };
  printable_4d: {
    artifact_id: string;
    state: string;
    packet_schema: string;
    stack_schema: string;
    catalogue_schema: string;
    template_count: number;
    exact_instance_inputs: number;
    coupled_stack_kernel: string;
    print_paths: Array<{ id: string; role: string }>;
    exact_examples: Array<{ instance_id: string; state: string; topology: string; next_gate: string }>;
    invariants: string[];
    compound_decomposition: {
      schema: string;
      count: number;
      state: string;
      parents: string[];
      rule: string;
    };
  };
  quantitative_invariants: {
    artifact_id: string;
    state: string;
    records: Array<{ id: string; role: string; equation: string; example: string; gate: string }>;
    rule: string;
  };
  dense_smart_stack: {
    artifact_id: string;
    cgx_uri: string;
    state: string;
    coupled_kernel: string;
    regions: Array<{ id: string; role: string; kernels: string; state: string }>;
    rule: string;
  };
  pipeline: Array<{ id: string; label: string; contract: string; state: string }>;
  showcase: {
    publication_state: string;
    title: string;
    summary: string;
    metrics: Array<{ value: string; label: string }>;
    safe_points: string[];
    excludes: string[];
  };
  boundary: string;
};

const esc = (value: string): string => value
  .replace(/&/g, "&amp;")
  .replace(/</g, "&lt;")
  .replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;")
  .replace(/'/g, "&#39;");

const metric = (value: number | string, label: string): string =>
  `<div><strong>${esc(String(value))}</strong><span>${esc(label)}</span></div>`;

const renderOverview = (p: CgxReviewProjection): string => `
  <section class="cgx-lens-panel active" data-cgx-lens-panel="overview">
    <div class="graph-summary">
      ${metric(p.metrics.archetypes, "archetypes")}
      ${metric(p.metrics.matrix_fields, "matrix fields")}
      ${metric(p.metrics.equation_kernels, "equation kernels")}
      ${metric(p.metrics.volumetric_kernels, "volumetric kernels")}
      ${metric(p.metrics.printable_4d_templates, "printable 4D templates")}
      ${metric(p.metrics.quantitative_invariants, "quantitative invariants")}
      ${metric(p.metrics.smart_stack_regions, "smart-stack regions")}
      ${metric(p.metrics.compound_decomposition_templates, "compound decompositions")}
      ${metric(p.metrics.initial_instances, "proof instances")}
      ${metric(p.metrics.requirement_targets_open, "open target gates")}
      ${metric(p.metrics.physical_tests_run, "physical tests complete")}
    </div>
    <div class="flow cgx-pipeline">
      ${p.pipeline.map((step) => `<span title="${esc(step.contract)}">${esc(step.label)} · ${esc(step.state)}</span>`).join("<i>→</i>")}
    </div>
    <div class="boundary"><strong>${esc(p.headline.state)}</strong><span>${esc(p.headline.note)}</span></div>
  </section>`;

const renderInstances = (p: CgxReviewProjection): string => `
  <section class="cgx-lens-panel" data-cgx-lens-panel="instances" hidden>
    <div class="graph-summary">
      ${Object.entries(p.gate_counts).map(([gate, count]) => metric(count, gate.replace(/_/g, " ").toLowerCase())).join("")}
    </div>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>CGXI</th><th>Stage</th><th>Current gate</th><th>Target</th><th>Next evidence</th></tr></thead>
        <tbody>
          ${p.instances.map((item) => `<tr>
            <td><strong>${esc(item.instance_id)}</strong><small class="cgx-uri">${esc(item.binding_uri)}</small><small>${esc(item.binding_progress)} · ${esc(item.physical_state)}</small></td>
            <td>${esc(item.proof_stage)}<br><small>${esc(item.archetype)}</small></td>
            <td><span class="badge">${esc(item.first_open_gate)}</span></td>
            <td>${esc(item.target)}</td>
            <td>${esc(item.next)}</td>
          </tr>`).join("")}
        </tbody>
      </table>
    </div>
  </section>`;

const renderKernels = (p: CgxReviewProjection): string => `
  <section class="cgx-lens-panel" data-cgx-lens-panel="kernels" hidden>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>Kernel</th><th>Primitive</th><th>Model family</th><th>Inference gate</th></tr></thead>
        <tbody>
          ${p.kernels.map((k) => `<tr><td><strong>${esc(k.kernel_id)}</strong></td><td>${esc(k.primitive)}</td><td>${esc(k.model)}</td><td>${esc(k.gate)}</td></tr>`).join("")}
        </tbody>
      </table>
    </div>
  </section>`;

const renderVolumetricKernels = (p: CgxReviewProjection): string => `
  <section class="cgx-lens-panel" data-cgx-lens-panel="volumetric" hidden>
    <div class="graph-summary">
      ${metric(p.metrics.volumetric_kernels, "volumetric kernels")}
      ${metric(p.topology_coverage.specific_or_multi, "specific / explicit multi-kernel archetypes")}
      ${metric(p.topology_coverage.final_generic_only, "intentional generic-coupled archetypes")}
      ${metric(`${p.topology_coverage.baseline_generic_only} → ${p.topology_coverage.final_generic_only}`, "generic fallback refinement")}
    </div>
    <div class="boundary"><strong>UTP-140 coverage closure</strong><span>${esc(p.topology_coverage.rule)} Residual: ${p.topology_coverage.residual.map(esc).join(" · ")}</span></div>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>Kernel</th><th>Primitive</th><th>Topology / geometry</th><th>Compiler token</th><th>Numeric gate</th></tr></thead>
        <tbody>
          ${p.volumetric_kernels.map((k) => `<tr><td><strong>${esc(k.kernel_id)}</strong></td><td>${esc(k.primitive)}</td><td>${esc(k.topology)}</td><td><small class="cgx-uri">${esc(k.token)}</small></td><td>${esc(k.gate)}</td></tr>`).join("")}
        </tbody>
      </table>
    </div>
  </section>`;

const renderPrintable4d = (p: CgxReviewProjection): string => `
  <section class="cgx-lens-panel" data-cgx-lens-panel="printable" hidden>
    <div class="panel-head">
      <div><p class="eyebrow">UTP-138 · BUILD-070</p><h3>Printable 4D component + stack packets</h3></div>
      <span class="badge">${esc(p.printable_4d.state)}</span>
    </div>
    <div class="graph-summary">
      ${metric(p.printable_4d.template_count, "derived catalogue templates")}
      ${metric(p.printable_4d.exact_instance_inputs, "current exact-instance inputs")}
      ${metric(p.printable_4d.coupled_stack_kernel, "coupled stack kernel")}
      ${metric("READ ONLY", "no machine authority")}
    </div>
    <p class="muted">Schemas: ${esc(p.printable_4d.packet_schema)} · ${esc(p.printable_4d.stack_schema)} · ${esc(p.printable_4d.catalogue_schema)}</p>
    <div class="two-column">
      <div>
        <strong>Print paths</strong>
        <div class="stack-list">
          ${p.printable_4d.print_paths.map((path) => `<article class="task-card"><div><strong>${esc(path.id)}</strong><small>${esc(path.role)}</small></div></article>`).join("")}
        </div>
      </div>
      <div>
        <strong>Exact packet examples</strong>
        <div class="stack-list">
          ${p.printable_4d.exact_examples.map((item) => `<article class="task-card"><div><strong>${esc(item.instance_id)}</strong><span>${esc(item.state)}</span><small>${esc(item.topology)} · next: ${esc(item.next_gate)}</small></div></article>`).join("")}
        </div>
      </div>
    </div>
    <div class="boundary"><strong>Compiler invariants</strong><span>${p.printable_4d.invariants.map(esc).join(" · ")}</span></div>
    <div class="boundary"><strong>${String(p.printable_4d.compound_decomposition.count)} compound-parent grammars</strong><span>${esc(p.printable_4d.compound_decomposition.state)} · ${p.printable_4d.compound_decomposition.parents.map(esc).join(" · ")}</span></div>
    <p class="muted">${esc(p.printable_4d.compound_decomposition.rule)}</p>
  </section>`;

const renderSmartStack = (p: CgxReviewProjection): string => `
  <section class="cgx-lens-panel" data-cgx-lens-panel="smartstack" hidden>
    <div class="panel-head">
      <div><p class="eyebrow">UTP-139 · BUILD-071</p><h3>Quantitative invariants + dense 4D smart stack</h3></div>
      <span class="badge">${esc(p.quantitative_invariants.state)}</span>
    </div>
    <div class="graph-summary">
      ${metric(p.metrics.quantitative_invariants, "reusable invariants")}
      ${metric(p.metrics.smart_stack_regions, "smart-stack regions")}
      ${metric(p.dense_smart_stack.coupled_kernel, "coupled assembly kernel")}
      ${metric("NUMERIC_IF", "evidence/regime conditional")}
    </div>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>Invariant</th><th>Role</th><th>Equation</th><th>Current bounded example</th><th>Gate</th></tr></thead>
        <tbody>
          ${p.quantitative_invariants.records.map((item) => `<tr><td><strong>${esc(item.id)}</strong></td><td>${esc(item.role)}</td><td><small class="cgx-uri">${esc(item.equation)}</small></td><td>${esc(item.example)}</td><td>${esc(item.gate)}</td></tr>`).join("")}
        </tbody>
      </table>
    </div>
    <div class="boundary"><strong>Invariant rule</strong><span>${esc(p.quantitative_invariants.rule)}</span></div>
    <p class="muted"><strong>Smart-stack:</strong> <span class="cgx-uri">${esc(p.dense_smart_stack.cgx_uri)}</span> · ${esc(p.dense_smart_stack.state)}</p>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>Region</th><th>Functional role</th><th>Topology kernels</th><th>State</th></tr></thead>
        <tbody>
          ${p.dense_smart_stack.regions.map((item) => `<tr><td><strong>${esc(item.id)}</strong></td><td>${esc(item.role)}</td><td><small class="cgx-uri">${esc(item.kernels)}</small></td><td><span class="badge">${esc(item.state)}</span></td></tr>`).join("")}
        </tbody>
      </table>
    </div>
    <div class="boundary"><strong>Stack rule</strong><span>${esc(p.dense_smart_stack.rule)}</span></div>
  </section>`;

const renderShowcase = (p: CgxReviewProjection): string => `
  <section class="cgx-lens-panel" data-cgx-lens-panel="showcase" hidden>
    <div class="panel-head">
      <div><p class="eyebrow">Public-safe candidate</p><h3>${esc(p.showcase.title)}</h3></div>
      <span class="badge">${esc(p.showcase.publication_state)}</span>
    </div>
    <p>${esc(p.showcase.summary)}</p>
    <div class="graph-summary">${p.showcase.metrics.map(({ value, label }) => metric(value, label)).join("")}</div>
    <div class="two-column">
      <div><strong>Safe showcase points</strong><ul class="compact-list">${p.showcase.safe_points.map((v) => `<li>${esc(v)}</li>`).join("")}</ul></div>
      <div><strong>Excluded from publication</strong><ul class="compact-list">${p.showcase.excludes.map((v) => `<li>${esc(v)}</li>`).join("")}</ul></div>
    </div>
  </section>`;

export const renderCgxReviewProjection = (p: CgxReviewProjection): string => `
  <article class="panel cgx-review-lens">
    <div class="panel-head">
      <div><p class="eyebrow">.cgx interactive review lens</p><h2>${esc(p.headline.title)}</h2></div>
      <span class="badge">${esc(p.authority.queue_id)} · ${esc(p.authority.physical_state)}</span>
    </div>
    <p class="muted">Drive remains engineering/evidence authority. This local UI is a read-only projection over existing CGXI, UTP and manufacturing contracts.</p>
    <div class="cgx-lens-tabs" role="tablist" aria-label="CGX review lens">
      <button class="active" type="button" data-cgx-lens="overview">Overview</button>
      <button type="button" data-cgx-lens="instances">CGXI queue</button>
      <button type="button" data-cgx-lens="kernels">Equation kernels</button>
      <button type="button" data-cgx-lens="volumetric">Volumetric kernels</button>
      <button type="button" data-cgx-lens="printable">Printable 4D</button>
      <button type="button" data-cgx-lens="smartstack">Invariants + Smart Stack</button>
      <button type="button" data-cgx-lens="showcase">Showcase-safe</button>
    </div>
    ${renderOverview(p)}
    ${renderInstances(p)}
    ${renderKernels(p)}
    ${renderVolumetricKernels(p)}
    ${renderPrintable4d(p)}
    ${renderSmartStack(p)}
    ${renderShowcase(p)}
    <p class="muted">${esc(p.boundary)}</p>
  </article>`;

export const bindCgxReviewProjection = (root: HTMLElement): void => {
  const buttons = [...root.querySelectorAll<HTMLButtonElement>("[data-cgx-lens]")];
  const panels = [...root.querySelectorAll<HTMLElement>("[data-cgx-lens-panel]")];
  const activate = (name: string): void => {
    buttons.forEach((button) => {
      const active = button.dataset.cgxLens === name;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", String(active));
    });
    panels.forEach((panel) => {
      const active = panel.dataset.cgxLensPanel === name;
      panel.classList.toggle("active", active);
      panel.hidden = !active;
    });
  };
  buttons.forEach((button) => button.addEventListener("click", () => activate(button.dataset.cgxLens || "overview")));
  activate("overview");
};

export const loadCgxReviewProjection = async (
  load: () => Promise<CgxReviewProjection>,
): Promise<{ data: CgxReviewProjection; html: string }> => {
  const data = await load();
  return { data, html: renderCgxReviewProjection(data) };
};