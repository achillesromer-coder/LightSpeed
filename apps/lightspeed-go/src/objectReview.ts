import { bindMeshViewerTriggers, meshViewerButtonMarkup } from "./meshViewer";
import { bindComponentPlateTriggers, componentPlateButtonMarkup } from "./componentVisualizer";

export type ReviewObject = {
  id: string;
  label: string;
  role: string;
  level: string;
  source: string;
  render: string;
  hero_render?: string;
  mesh_data?: string;
  source_sha256?: string;
  render_state?: string;
  geometry_state: string;
  physical_state: string;
  review_rules: string[];
  stats?: { vertices: number; faces: number; extents: number[]; bytes: number };
};

export type ComponentAtlasRecord = {
  ID: string;
  Domain?: string;
  Family?: string;
  "Component Archetype"?: string;
  "Primary Function"?: string;
  "Baseline Geometry"?: string;
  "Geometric Parameters"?: string;
  "Typical Material Stack"?: string;
  "Primary Physics"?: string;
  "Baseline Model / Equation"?: string;
  "Ports / Interfaces"?: string;
  "Current Manufacturing Route"?: string;
  "Current CGX Build Class"?: string;
  "Scale Band"?: string;
  "4D Fields"?: string;
  "Raphael Search Variables"?: string;
  "Acceptance Tests"?: string;
  "Failure Modes"?: string;
  "Evidence State"?: string;
  "Source Authority Class"?: string;
  "Existing CGX Links"?: string;
  Notes?: string;
};

export type ComponentAtlas = {
  schema: string;
  status: string;
  record_count: number;
  records: ComponentAtlasRecord[];
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
    brand_lockup?: string;
    hero_render?: string;
    interactive_mesh?: string;
    material_policy?: string;
    composition?: string;
  };
  coverage: {
    printable_4d_archetypes: number;
    macro_source_meshes: number;
    symbolic_core_component_stack_plates: number;
    source_mesh_interactive_views?: number;
    source_mesh_4k_hero_views?: number;
    symbolic_system_lineage_plates?: number;
    physical_tests_complete: number;
  };
  maturity_projection?: {
    artifact_id: string;
    status: string;
    physical_state: string;
    maturity_axes: string[];
    contradiction_states: string[];
    invalidation_triggers: string[];
    numeric_routes: string[];
    next_witness_ladder: string[];
    proof_fixture_count: number;
    authority_boundary: string;
  };
  tiers: Array<{ id: string; label: string; description: string }>;
  micro_review_objects: ReviewObject[];
  macro_review_objects: ReviewObject[];
  bridge_review_objects?: ReviewObject[];
  atlas_ref: string;
  pending_owner_layers: string[];
  boundary: string;
};

const esc = (value: string): string => value
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

const metric = (value: number | string, label: string): string =>
  `<div><strong>${esc(String(value))}</strong><span>${esc(label)}</span></div>`;

const card = (item: ReviewObject): string => {
  const preview=item.hero_render || item.render;
  const actions=[
    item.hero_render ? `<a class="button-secondary" href="${esc(item.hero_render)}" target="_blank" rel="noreferrer">4K hero</a>` : "",
    `<a class="button-secondary" href="${esc(item.render)}" target="_blank" rel="noreferrer">Engineering plate</a>`,
    item.mesh_data ? meshViewerButtonMarkup({
      url:item.mesh_data,
      label:item.label,
      source:item.source,
      sourceHash:item.source_sha256,
      physicalState:item.physical_state,
    }) : "",
  ].filter(Boolean).join("");
  return `
  <article class="object-review-card" data-review-object data-search="${esc([
    item.id, item.label, item.role, item.level, item.geometry_state, item.physical_state,
  ].join(" ").toLowerCase())}">
    <a href="${esc(preview)}" target="_blank" rel="noreferrer">
      <img src="${esc(preview)}" loading="lazy" alt="${esc(item.label)} source-faithful review render" />
    </a>
    <div class="object-review-copy">
      <div class="panel-head">
        <div><p class="eyebrow">${esc(item.level)}</p><h3>${esc(item.label)}</h3></div>
        <span class="badge">${esc(item.physical_state)}</span>
      </div>
      <p>${esc(item.role)}</p>
      <small class="cgx-uri">${esc(item.source)}</small>
      <div class="object-review-state"><strong>${esc(item.geometry_state)}</strong></div>
      ${item.render_state ? `<small>${esc(item.render_state)}</small>` : ""}
      ${item.stats ? `<small>${item.stats.vertices.toLocaleString()} vertices · ${item.stats.faces.toLocaleString()} triangles</small>` : ""}
      ${item.source_sha256 ? `<small class="cgx-uri">source SHA-256 ${esc(item.source_sha256.slice(0,24))}…</small>` : ""}
      <div class="object-review-actions">${actions}</div>
      <ul class="compact-list">${item.review_rules.map((v) => `<li>${esc(v)}</li>`).join("")}</ul>
    </div>
  </article>`;
};

const atlasTable = (atlas: ComponentAtlas): string => `
  <div class="object-catalogue-controls">
    <input id="object-catalogue-filter" type="search" placeholder="Filter 411 components by ID, family, geometry, route, physics…" />
    <span class="badge" id="object-catalogue-count">${atlas.records.length} / ${atlas.records.length}</span>
  </div>
  <div class="table-scroll">
    <table class="graph-table object-catalogue-table">
      <thead><tr><th>ID</th><th>Component</th><th>Build / route</th><th>Geometry</th><th>4D / physics</th><th>Evidence</th></tr></thead>
      <tbody>
        ${atlas.records.map((row) => `<tr data-printable-row data-search="${esc([
          row.ID,row.Domain,row.Family,row["Component Archetype"],row["Current CGX Build Class"],
          row["Current Manufacturing Route"],row["Baseline Geometry"],row["Primary Physics"],row["4D Fields"],
        ].filter(Boolean).join(" ").toLowerCase())}">
          <td><strong>${esc(row.ID)}</strong><small>${esc(row.Domain || "")}</small>${componentPlateButtonMarkup(row.ID)}</td>
          <td>${esc(row["Component Archetype"] || "")}<small>${esc(row.Family || "")} · ${esc(row["Primary Function"] || "")}</small></td>
          <td><span class="badge">${esc(row["Current CGX Build Class"] || "")}</span><small>${esc(row["Current Manufacturing Route"] || "")}</small></td>
          <td>${esc(row["Baseline Geometry"] || "")}<small>${esc(row["Geometric Parameters"] || "")}</small></td>
          <td>${esc(row["Primary Physics"] || "")}<small>${esc(row["4D Fields"] || "")}</small></td>
          <td>${esc(row["Evidence State"] || "")}<small>${esc(row["Source Authority Class"] || "")}</small></td>
        </tr>`).join("")}
      </tbody>
    </table>
  </div>`;

export const renderObjectReview = (manifest: ObjectReviewCatalogue, atlas: ComponentAtlas): string => `
  <article class="panel object-review-panel">
    <div class="panel-head">
      <div><p class="eyebrow">CGX object review catalogue</p><h2>Component → stack → Luke / Mark / InterSol</h2></div>
      <span class="badge">${esc(manifest.status)}</span>
    </div>
    <p class="muted">${esc(manifest.authority)}</p>
    <div class="graph-summary">
      ${metric(manifest.coverage.printable_4d_archetypes, "component archetypes")}
      ${metric(manifest.coverage.symbolic_core_component_stack_plates, "CGX symbolic plates")}
      ${metric(manifest.coverage.source_mesh_4k_hero_views ?? manifest.coverage.macro_source_meshes, "4K source-mesh heroes")}
      ${metric(manifest.coverage.source_mesh_interactive_views ?? manifest.coverage.macro_source_meshes, "interactive source meshes")}
      ${metric(manifest.coverage.symbolic_system_lineage_plates ?? 0, "system lineage plates")}
      ${metric(manifest.coverage.physical_tests_complete, "physical tests complete")}
    </div>
    <div class="flow">${manifest.tiers.map((t) => `<span title="${esc(t.description)}">${esc(t.id)} · ${esc(t.label)}</span>`).join("<i>→</i>")}</div>
    <div class="boundary"><strong>Visual rule</strong><span>${esc(manifest.visual_system.rule)}</span></div>

    <div class="cgx-lens-tabs object-review-tabs" role="tablist" aria-label="Object review catalogue">
      <button class="active" type="button" data-object-review-tab="gallery">Review plates</button>
      <button type="button" data-object-review-tab="catalogue">411 component catalogue</button>
      <button type="button" data-object-review-tab="maturity">Maturity / ingest</button>
      <button type="button" data-object-review-tab="frontier">Current frontier</button>
    </div>

    <section data-object-review-panel="gallery">
      <div class="object-review-search"><input id="object-review-filter" type="search" placeholder="Filter review plates…" /></div>
      <h3>CGX-derived component / stack plates</h3>
      <div class="object-review-grid">${manifest.micro_review_objects.map(card).join("")}</div>
      <h3>System lineage / bridge plates</h3>
      <div class="object-review-grid">${(manifest.bridge_review_objects || []).map(card).join("")}</div>
      <h3>Corpus source meshes</h3>
      <div class="object-review-grid">${manifest.macro_review_objects.map(card).join("")}</div>
    </section>

    <section data-object-review-panel="catalogue" hidden>
      <div class="boundary"><strong>${esc(atlas.schema)}</strong><span>Canonical component atlas exposed as a read-only LS GO projection. Printable-4D packet, topology and invariant semantics remain in the adjacent CGX lens rather than being duplicated here.</span></div>
      ${atlasTable(atlas)}
    </section>

    <section data-object-review-panel="maturity" hidden>
      ${manifest.maturity_projection ? `
        <div class="panel-head"><div><p class="eyebrow">${esc(manifest.maturity_projection.artifact_id)}</p><h3>Evidence maturation / ingest projection</h3></div><span class="badge">${esc(manifest.maturity_projection.physical_state)}</span></div>
        <p class="muted">${esc(manifest.maturity_projection.status)}</p>
        <div class="graph-summary">
          ${metric(manifest.maturity_projection.maturity_axes.length, "independent maturity axes")}
          ${metric(manifest.maturity_projection.contradiction_states.length, "contradiction states")}
          ${metric(manifest.maturity_projection.invalidation_triggers.length, "invalidation triggers")}
          ${metric(manifest.maturity_projection.proof_fixture_count, "bounded proof fixtures")}
        </div>
        <div class="boundary"><strong>Numeric routing</strong><span>${esc(manifest.maturity_projection.numeric_routes.join(" · "))}</span></div>
        <div class="stack-list">
          <article class="task-card"><div><strong>Maturity vector</strong><small>${esc(manifest.maturity_projection.maturity_axes.join(" → "))}</small></div></article>
          <article class="task-card"><div><strong>Contradiction states</strong><small>${esc(manifest.maturity_projection.contradiction_states.join(" · "))}</small></div></article>
          <article class="task-card"><div><strong>Invalidation triggers</strong><small>${esc(manifest.maturity_projection.invalidation_triggers.join(" · "))}</small></div></article>
          <article class="task-card"><div><strong>Next witness ladder</strong><small>${esc(manifest.maturity_projection.next_witness_ladder.join(" → "))}</small></div></article>
        </div>
        <div class="boundary"><strong>Authority boundary</strong><span>${esc(manifest.maturity_projection.authority_boundary)}</span></div>
      ` : `<div class="boundary"><strong>Maturity projection</strong><span>Not present in this generated review packet.</span></div>`}
    </section>

    <section data-object-review-panel="frontier" hidden>
      <div class="stack-list">
        ${manifest.pending_owner_layers.map((item) => `<article class="task-card"><div><strong>Current owner frontier</strong><small>${esc(item)}</small></div></article>`).join("")}
      </div>
      <div class="boundary"><strong>Evidence boundary</strong><span>${esc(manifest.boundary)}</span></div>
    </section>
  </article>`;

export const bindObjectReview = (root: HTMLElement, atlas: ComponentAtlas): void => {
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

  const componentFilter=root.querySelector<HTMLInputElement>("#object-catalogue-filter");
  const rows=[...root.querySelectorAll<HTMLTableRowElement>("[data-printable-row]")];
  const count=root.querySelector<HTMLElement>("#object-catalogue-count");
  componentFilter?.addEventListener("input",()=>{
    const q=(componentFilter.value || "").trim().toLowerCase();
    let visible=0;
    rows.forEach((row)=>{
      const show=!q || (row.dataset.search || "").includes(q);
      row.hidden=!show;
      if(show) visible+=1;
    });
    if(count) count.textContent=`${visible} / ${rows.length}`;
  });

  bindMeshViewerTriggers(root);
  bindComponentPlateTriggers(root, atlas.records);
};

export const loadObjectReview = async (
  loadManifest: () => Promise<ObjectReviewCatalogue>,
  loadAtlas: () => Promise<ComponentAtlas>,
): Promise<{ manifest: ObjectReviewCatalogue; atlas: ComponentAtlas; html: string }> => {
  const [manifest,atlas]=await Promise.all([loadManifest(),loadAtlas()]);
  return {manifest,atlas,html:renderObjectReview(manifest,atlas)};
};