export type Type1CatalogueProjection = {
  schema: string;
  generated_from: string;
  source_owner: { spreadsheet_id: string; authority: string };
  metrics: { archetypes: number; universal_matrix_fields: number; directional_4d_fields: number; quantitative_factorization_fields: number; primitive_basis_classes: number; equation_kernel_records: number; volumetric_topology_kernels: number };
  surfaces: Array<{ id: string; name: string; role: string }>;
  contracts: string[];
  inference_example: { label: string; equation: string; inputs: string; result: string; evidence: string };
  boundary: string;
};

const esc = (value: string): string => value
  .replace(/&/g, "&amp;")
  .replace(/</g, "&lt;")
  .replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;")
  .replace(/'/g, "&#39;");

export const renderType1CatalogueProjection = (p: Type1CatalogueProjection): string => `
  <article class="panel">
    <div class="panel-head">
      <div><p class="eyebrow">Type-I PrintSpace</p><h2>Universal 4D technology matrix</h2></div>
      <span class="badge">${p.metrics.archetypes} archetypes · ${p.metrics.universal_matrix_fields} fields</span>
    </div>
    <p class="muted">One Drive-owned evidence graph projected into volumetric build order, primitive/equivalent-network models, source-bound component instances and PC01 manufacturing packets. No duplicate catalogue is created here.</p>
    <div class="graph-summary">
      <div><strong>${p.metrics.archetypes}</strong><span>component archetypes</span></div>
      <div><strong>${p.metrics.directional_4d_fields}</strong><span>directional / 4D fields</span></div>
      <div><strong>${p.metrics.quantitative_factorization_fields}</strong><span>quantitative compiler fields</span></div>
      <div><strong>${p.metrics.primitive_basis_classes}</strong><span>primitive basis classes</span></div>\n      <div><strong>${p.metrics.equation_kernel_records}</strong><span>equation / constitutive kernels</span></div>
      <div><strong>${p.metrics.volumetric_topology_kernels}</strong><span>volumetric topology kernels</span></div>
      <div><strong>UTP-124/125</strong><span>stack + manufacturing compiler</span></div>
      <div><strong>READ ONLY</strong><span>owner matrix remains Drive</span></div>
    </div>
    <div class="table-scroll"><table class="graph-table"><thead><tr><th>Surface</th><th>Role</th></tr></thead><tbody>
      ${p.surfaces.map((s) => `<tr><td><strong>${esc(s.id)} · ${esc(s.name)}</strong></td><td>${esc(s.role)}</td></tr>`).join("")}
    </tbody></table></div>
    <div class="boundary"><strong>${esc(p.inference_example.label)}</strong><span>${esc(p.inference_example.equation)} · ${esc(p.inference_example.inputs)} → ${esc(p.inference_example.result)}. ${esc(p.inference_example.evidence)}</span></div>
    <p class="muted"><strong>Active contracts:</strong> ${p.contracts.map(esc).join(" · ")}</p>
    <p class="muted">${esc(p.boundary)}</p>
  </article>`;

export const loadType1CatalogueProjection = async (
  load: () => Promise<Type1CatalogueProjection>,
): Promise<string> => renderType1CatalogueProjection(await load());