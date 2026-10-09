export type ReviewObject = {
  id: string;
  label: string;
  role: string;
  level: string;
  source: string;
  render: string;
  geometry_state: string;
  physical_state: string;
  review_rules: string[];
  stats?: { vertices: number; faces: number; extents: number[]; bytes: number };
};

export type PrintableCatalogueRow = {
  archetype_id: string;
  domain?: string;
  family?: string;
  name?: string;
  print_path?: string;
  packet_state?: string;
  topology_kernel_ids?: string[];
  topology_tokens?: string[];
  geometry_parameter_slots?: string[];
  candidate_material_stack?: string;
  ports_interfaces?: string;
  consequential_optional_scopes?: string[];
  operation_sequence?: string[];
  acceptance_tests?: string;
  failure_modes?: string;
  evidence_state?: string;
  source_authority_class?: string;
  physical_execution: false;
};

export type PrintableCatalogue = {
  schema: string;
  artifact_id: string;
  archetype_count: number;
  compound_parent_decomposition_count: number;
  records: PrintableCatalogueRow[];
  authority_boundary: string;
};

export type ObjectReviewCatalogue = {
  schema: string;
  generated_from_git: string;
  status: string;
  authority: string;
  visual_system: {
    palette: Record<string, string>;
    rule: string;
    render_plate: string;
  };
  coverage: {
    printable_4d_archetypes: number;
    macro_source_meshes: number;
    symbolic_core_component_stack_plates: number;
    physical_tests_complete: number;
  };
  tiers: Array<{ id: string; label: string; description: string }>;
  micro_review_objects: ReviewObject[];
  macro_review_objects: ReviewObject[];
  catalogue_ref: string;
  pending_owner_layers: string[];
  boundary: string;
};

const esc = (value: string): string => value
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

const metric = (value: number | string, label: string): string =>
  `<div><strong>${esc(String(value))}</strong><span>${esc(label)}</span></div>`;

const card = (item: ReviewObject): string => `
  <article class="object-review-card" data-review-object data-search="${esc([
    item.id, item.label, item.role, item.level, item.geometry_state, item.physical_state,
  ].join(" ").toLowerCase())}">
    <a href="${esc(item.render)}" target="_blank" rel="noreferrer">
      <img src="${esc(item.render)}" loading="lazy" alt="${esc(item.label)} engineering review plate" />
    </a>
    <div class="object-review-copy">
      <div class="panel-head">
        <div><p class="eyebrow">${esc(item.level)}</p><h3>${esc(item.label)}</h3></div>
        <span class="badge">${esc(item.physical_state)}</span>
      </div>
      <p>${esc(item.role)}</p>
      <small class="cgx-uri">${esc(item.source)}</small>
      <div class="object-review-state"><strong>${esc(item.geometry_state)}</strong></div>
      ${item.stats ? `<small>${item.stats.vertices.toLocaleString()} vertices · ${item.stats.faces.toLocaleString()} triangles</small>` : ""}
      <ul class="compact-list">${item.review_rules.map((v) => `<li>${esc(v)}</li>`).join("")}</ul>
    </div>
  </article>`;

const printableTable = (catalogue: PrintableCatalogue): string => `
  <div class="object-catalogue-controls">
    <input id="object-catalogue-filter" type="search" placeholder="Filter 411 printable components by ID, family, topology, print path…" />
    <span class="badge" id="object-catalogue-count">${catalogue.records.length} / ${catalogue.records.length}</span>
  </div>
  <div class="table-scroll">
    <table class="graph-table object-catalogue-table">
      <thead><tr><th>ID</th><th>Component</th><th>Print path</th><th>Topology</th><th>Geometry slots</th><th>Evidence</th></tr></thead>
      <tbody>
        ${catalogue.records.map((row) => `<tr data-printable-row data-search="${esc([
          row.archetype_id,row.domain,row.family,row.name,row.print_path,
          ...(row.topology_kernel_ids || []),...(row.topology_tokens || []),
        ].filter(Boolean).join(" ").toLowerCase())}">
          <td><strong>${esc(row.archetype_id)}</strong><small>${esc(row.domain || "")}</small></td>
          <td>${esc(row.name || "")}<small>${esc(row.family || "")}</small></td>
          <td><span class="badge">${esc(row.print_path || "")}</span><small>${esc(row.packet_state || "")}</small></td>
          <td>${(row.topology_kernel_ids || []).map((v) => `<span class="state-chip">${esc(v)}</span>`).join(" ")}<small>${(row.topology_tokens || []).map(esc).join(" · ")}</small></td>
          <td>${(row.geometry_parameter_slots || []).map(esc).join(" · ") || "source/instance binding"}</td>
          <td>${esc(row.evidence_state || "")}<small>${esc(row.source_authority_class || "")}</small></td>
        </tr>`).join("")}
      </tbody>
    </table>
  </div>`;

export const renderObjectReview = (manifest: ObjectReviewCatalogue, catalogue: PrintableCatalogue): string => `
  <article class="panel object-review-panel">
    <div class="panel-head">
      <div><p class="eyebrow">CGX object review catalogue</p><h2>Component → stack → Luke / Mark / InterSol</h2></div>
      <span class="badge">${esc(manifest.status)}</span>
    </div>
    <p class="muted">${esc(manifest.authority)}</p>
    <div class="graph-summary">
      ${metric(manifest.coverage.printable_4d_archetypes, "printable 4D archetypes")}
      ${metric(manifest.coverage.symbolic_core_component_stack_plates, "CGX symbolic 4K plates")}
      ${metric(manifest.coverage.macro_source_meshes, "source-mesh 4K plates")}
      ${metric(manifest.coverage.physical_tests_complete, "physical tests complete")}
    </div>
    <div class="flow">${manifest.tiers.map((t) => `<span title="${esc(t.description)}">${esc(t.id)} · ${esc(t.label)}</span>`).join("<i>→</i>")}</div>
    <div class="boundary"><strong>Visual rule</strong><span>${esc(manifest.visual_system.rule)}</span></div>

    <div class="cgx-lens-tabs object-review-tabs" role="tablist" aria-label="Object review catalogue">
      <button class="active" type="button" data-object-review-tab="gallery">Review plates</button>
      <button type="button" data-object-review-tab="catalogue">411 printable components</button>
      <button type="button" data-object-review-tab="frontier">Pending owner layers</button>
    </div>

    <section data-object-review-panel="gallery">
      <div class="object-review-search"><input id="object-review-filter" type="search" placeholder="Filter review plates…" /></div>
      <h3>CGX-derived component / stack plates</h3>
      <div class="object-review-grid">${manifest.micro_review_objects.map(card).join("")}</div>
      <h3>Corpus source meshes</h3>
      <div class="object-review-grid">${manifest.macro_review_objects.map(card).join("")}</div>
    </section>

    <section data-object-review-panel="catalogue" hidden>
      <div class="boundary"><strong>${esc(catalogue.schema)}</strong><span>${esc(catalogue.authority_boundary)}</span></div>
      ${printableTable(catalogue)}
    </section>

    <section data-object-review-panel="frontier" hidden>
      <div class="stack-list">
        ${manifest.pending_owner_layers.map((item) => `<article class="task-card"><div><strong>Current owner frontier</strong><small>${esc(item)}</small></div></article>`).join("")}
      </div>
      <div class="boundary"><strong>Evidence boundary</strong><span>${esc(manifest.boundary)}</span></div>
    </section>
  </article>`;

export const bindObjectReview = (root: HTMLElement): void => {
  const tabs=[...root.querySelectorAll<HTMLButtonElement>("[data-object-review-tab]")];
  const panels=[...root.querySelectorAll<HTMLElement>("[data-object-review-panel]")];
  const activate=(name:string):void=>{
    tabs.forEach((tab)=>tab.classList.toggle("active",tab.dataset.objectReviewTab===name));
    panels.forEach((panel)=>panel.hidden=panel.dataset.objectReviewPanel!==name);
  };
  tabs.forEach((tab)=>tab.addEventListener("click",()=>activate(tab.dataset.objectReviewTab || "gallery")));
  activate("gallery");

  const filter=root.querySelector<HTMLInputElement>("#object-review-filter");
  const cards=[...root.querySelectorAll<HTMLElement>("[data-review-object]")];
  filter?.addEventListener("input",()=>{
    const q=(filter.value || "").trim().toLowerCase();
    cards.forEach((item)=>item.hidden=!!q && !(item.dataset.search || "").includes(q));
  });

  const printable=root.querySelector<HTMLInputElement>("#object-catalogue-filter");
  const rows=[...root.querySelectorAll<HTMLTableRowElement>("[data-printable-row]")];
  const count=root.querySelector<HTMLElement>("#object-catalogue-count");
  printable?.addEventListener("input",()=>{
    const q=(printable.value || "").trim().toLowerCase();
    let visible=0;
    rows.forEach((row)=>{
      const show=!q || (row.dataset.search || "").includes(q);
      row.hidden=!show;
      if(show) visible+=1;
    });
    if(count) count.textContent=`${visible} / ${rows.length}`;
  });
};

export const loadObjectReview = async (
  loadManifest: () => Promise<ObjectReviewCatalogue>,
  loadCatalogue: () => Promise<PrintableCatalogue>,
): Promise<{ manifest: ObjectReviewCatalogue; catalogue: PrintableCatalogue; html: string }> => {
  const [manifest,catalogue]=await Promise.all([loadManifest(),loadCatalogue()]);
  return {manifest,catalogue,html:renderObjectReview(manifest,catalogue)};
};
