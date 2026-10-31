/** Owner-private CGX Family Set projection, NOT an admission or runtime installer. */
import { escapeHtml } from "./neoExchange";

export interface CgxOperationalObservation {
  resolution: string;
  operational_state: string;
  identifier_state: string;
  representation_count: number;
}
export interface CgxFamilyRow {
  domain: string;
  semantic_object_id: string;
  parent_semantic_object_id: string;
  filespace: string;
  operational: CgxOperationalObservation;
  load_source_reference_count: number;
  native_child_accepted: false;
  scope_owner_acl_verified: false;
  load_alias_admitted: false;
  runtime_capability_installed: false;
}
export interface CgxFamilyOversightSnapshot {
  schema: "CGX-LS-FAMILY-OVERSIGHT/0.1";
  mode: string;
  parent: {
    semantic_object_id: string;
    filespace: string;
    operational: CgxOperationalObservation;
    carrier: { state: string; byte_binding_match: boolean };
    native_parent_admitted: false;
  };
  families: CgxFamilyRow[];
  load_alexandria: {
    state: string; reference_count: number;
    source_registry_count: number; frontier_count: number;
    native_accepted: number;
    selector_source_route_counts?: Record<string, number>;
    selector_routes_are_installed?: false;
  };
  effects: {
    canonical_db_writes: number; object_ids_minted: number;
    source_bytes_copied: number; public_release: false;
  };
  owner_session_verified_by_bridge?: boolean;
}

const esc = (x: unknown): string => escapeHtml(String(x ?? "unknown"));
const number = (value: unknown): number =>
  typeof value === "number" && Number.isSafeInteger(value) && value >= 0 ? value : 0;

export function renderCgxFamilyOversight(value: CgxFamilyOversightSnapshot): string {
  if (value?.schema !== "CGX-LS-FAMILY-OVERSIGHT/0.1"
      || value.effects?.canonical_db_writes !== 0
      || value.effects?.object_ids_minted !== 0
      || value.effects?.source_bytes_copied !== 0
      || value.effects?.public_release !== false
      || value.parent?.native_parent_admitted !== false
      || !Array.isArray(value.families)) {
    return '<p class="muted">Family evidence contract invalid; hold oversight view.</p>';
  }
  const selectorRoutes = Object.entries(
    value.load_alexandria?.selector_source_route_counts ?? {},
  ).filter(([name, count]) =>
    name.length < 65 && Number.isSafeInteger(count) && count >= 0,
  ).sort(([a], [b]) => a.localeCompare(b));
  const selectorSummary = selectorRoutes.length
    ? `<details><summary>Declared agent selector coverage (source-only)</summary>
      <p class="muted">${selectorRoutes.map(([name, count]) =>
        `${esc(name)}: ${number(count)}`).join(" · ")}</p>
      <p class="muted">Route declarations are not installed tools,
      authenticated providers, or executable capabilities.</p></details>`
    : "";
  const rows = value.families.map(family => {
    if (family.native_child_accepted !== false || family.scope_owner_acl_verified !== false
      || family.load_alias_admitted !== false || family.runtime_capability_installed !== false) {
      return '<article class="panel"><strong>Unverified authority claim — held</strong></article>';
    }
    return `<article class="task-card">
      <div><strong>${esc(family.filespace)}</strong>
      <small>${esc(family.domain)} · ${esc(family.semantic_object_id)}</small>
      <span>Parent ${esc(family.parent_semantic_object_id)}</span>
      <span>Native row: ${esc(family.operational?.operational_state)} ·
      ${number(family.load_source_reference_count)} LOAD source references</span></div>
    </article>`;
  }).join("");
  return `<div class="panel-head">
    <div><p class="eyebrow">Single Cognigrex parent</p>
    <h2>${esc(value.parent.filespace)}</h2></div>
    <span class="badge">Not natively admitted by this view</span>
  </div>
  <p class="muted">Operational state: ${esc(value.parent.operational?.operational_state)};
  S92 byte check: ${esc(value.parent.carrier?.state)}. These are observations,
  not an owner signature, DBR acceptance or permission to execute.</p>
  <div class="graph-stack">${rows}</div>
  <p class="muted">Alexandria: ${number(value.load_alexandria?.reference_count)} source
  references across ${number(value.load_alexandria?.source_registry_count)} registries,
  ${number(value.load_alexandria?.frontier_count)} Frontier cases.
  Source mode: ${esc(value.load_alexandria?.state)}. Native LOAD admission: none.</p>
  ${selectorSummary}
  <p class="muted">UniSpace remains a private, non-authoritative oversight lens.
  Source bytes, remote fetch, installer actions, and canonical writes are excluded.</p>`;
}
