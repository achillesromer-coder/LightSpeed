/**
 * CGX / UniSpace generated interface compiler and read-only operator preview.
 * Consumes the existing LightSpeed GO Interface Studio "cgx.unispace.interface/1"
 * shape. GUI projection is not an Object_ID mint, native ACL/lease, hydration,
 * public launch or trusted execution plan. Source data is never fetched here.
 */
export const CGX_GENERATED_GUI_SCHEMA = "cgx.unispace.interface/1" as const;
export const CGX_GENERATED_GUI_ROOT = "cgx:root:cognigrex" as const;
export type CgxFacetId =
  | "file_space" | "data_space" | "social_space" | "print_space" | "intelligence_space";
export type CgxShellWorkspace =
  | "command" | "activity" | "objects" | "sources" | "filespace";

export interface CgxCollectionPanel {
  readonly id: string;
  readonly title: string;
  readonly path: readonly string[];
  readonly type: "collection";
  readonly dataset: "workspace" | "files" | "records" | "handoffs" | "stacks";
  readonly facet: CgxFacetId | "";
  readonly kind: string;
  readonly status: string;
  readonly query: string;
  readonly layout: "cards" | "rows";
  readonly limit: number;
  readonly workspace: CgxShellWorkspace | null;
}
export interface CgxGeneratedGuiPlan {
  readonly schema: typeof CGX_GENERATED_GUI_SCHEMA;
  readonly parent: typeof CGX_GENERATED_GUI_ROOT;
  readonly title: string;
  readonly layout: "tabs" | "stack" | "grid";
  readonly panels: readonly CgxCollectionPanel[];
  readonly state: "SOURCE_PROJECTION_ONLY";
  readonly nativeAdmitted: false;
  readonly hostAuthenticated: false;
  readonly publicPublished: false;
  readonly handlersBound: false;
  readonly privateBytesIncluded: false;
}

export class CgxInterfaceHold extends Error {
  constructor(readonly code: string) { super(code); this.name = "CgxInterfaceHold"; }
}
const hold = (code: string): never => { throw new CgxInterfaceHold(code); };
const object = (v: unknown): v is Record<string, unknown> =>
  v !== null && typeof v === "object" && !Array.isArray(v);
const hasKeys = (v: Record<string, unknown>, keys: readonly string[]): boolean =>
  Object.keys(v).length === keys.length && Object.keys(v).every((key) => keys.includes(key));
const label = (v: unknown, max = 112, empty = false): v is string =>
  typeof v === "string" && v.length <= max && (empty || v.trim().length > 0)
  && !/[\u0000-\u001f\u007f<>]/.test(v) && !/(?:https?:\/\/|javascript:|data:|file:|token=|password=)/i.test(v);
const ID = /^[a-z][a-z0-9_-]{0,63}$/;
const SCOPED_DATASETS = {
  file_space: new Set(["files", "workspace"]),
  data_space: new Set(["records", "workspace"]),
  social_space: new Set(["handoffs", "workspace"]),
  print_space: new Set(["workspace"]),
  intelligence_space: new Set(["workspace"]),
} as const;
const WORKSPACE: Readonly<Record<CgxFacetId, CgxShellWorkspace>> = {
  file_space: "filespace",
  data_space: "sources",
  social_space: "activity",
  print_space: "objects",
  intelligence_space: "command",
};
const FACETS = Object.keys(WORKSPACE) as CgxFacetId[];
const DATASETS = ["workspace", "files", "records", "handoffs", "stacks"] as const;
const GROUP_KEYS = ["id", "type", "title", "layout", "children"];
const COLLECTION_KEYS = ["id", "type", "title", "dataset", "facet",
  "kind", "status", "query", "layout", "limit"];

/**
 * Strict, capped JSON-to-GUI compilation; no eval, network, template interpolation
 * of executable HTML, prototype expansion, opaque data or executable controls.
 */
export function compileCgxGeneratedGui(input: unknown): CgxGeneratedGuiPlan {
  let value = input;
  if (typeof value === "string") {
    if (value.length === 0 || value.length > 32768) return hold("CGX_GUI_SOURCE_SIZE_HOLD");
    try { value = JSON.parse(value); } catch { return hold("CGX_GUI_INVALID_JSON"); }
  }
  if (!object(value) || !hasKeys(value, ["design"]) || !object(value.design))
    return hold("CGX_GUI_WRAPPER_HOLD");
  const design = value.design;
  if (!hasKeys(design, ["schema", "parent", "title", "body"])
      || design.schema !== CGX_GENERATED_GUI_SCHEMA
      || design.parent !== CGX_GENERATED_GUI_ROOT
      || !label(design.title))
    return hold("CGX_GUI_CANONICAL_IDENTITY_HOLD");

  const ids = new Set<string>();
  const panels: CgxCollectionPanel[] = [];
  let nodeCount = 0;
  const visit = (node: unknown, path: string[], depth: number): void => {
    if (++nodeCount > 32 || depth > 4 || !object(node) || typeof node.type !== "string")
      return hold("CGX_GUI_DEPTH_OR_NODE_HOLD");
    if (!label(node.id, 64) || !ID.test(node.id) || ids.has(node.id)
        || !label(node.title))
      return hold("CGX_GUI_NODE_ID_OR_LABEL_HOLD");
    ids.add(node.id);

    if (node.type === "group") {
      if (!hasKeys(node, GROUP_KEYS)
          || !["tabs", "stack", "grid"].includes(String(node.layout))
          || !Array.isArray(node.children) || node.children.length < 1
          || node.children.length > 16)
        return hold("CGX_GUI_GROUP_SHAPE_HOLD");
      for (const child of node.children) visit(child, [...path, node.title], depth + 1);
      return;
    }
    if (node.type !== "collection" || !hasKeys(node, COLLECTION_KEYS))
      return hold("CGX_GUI_UNSUPPORTED_CONTROL_HOLD");
    if (!DATASETS.includes(node.dataset as typeof DATASETS[number])
        || (node.facet !== "" && !FACETS.includes(node.facet as CgxFacetId))
        || !label(node.kind, 64, true) || !label(node.status, 64, true)
        || !label(node.query, 110, true)
        || !["cards", "rows"].includes(String(node.layout))
        || !Number.isSafeInteger(node.limit) || Number(node.limit) < 1
        || Number(node.limit) > 24)
      return hold("CGX_GUI_COLLECTION_SHAPE_HOLD");
    const facet = node.facet as CgxFacetId | "";
    if (facet) {
      if (!(SCOPED_DATASETS[facet] as ReadonlySet<string>).has(node.dataset as string))
        return hold("CGX_GUI_FACET_DATASET_MISMATCH");
    } else if (node.dataset !== "workspace" && node.dataset !== "stacks") {
      return hold("CGX_GUI_UNSCOPED_PRIVATE_DATASET_HOLD");
    }
    panels.push(Object.freeze({
      id: node.id, title: node.title as string, path: Object.freeze(path),
      type: "collection", dataset: node.dataset as CgxCollectionPanel["dataset"],
      facet, kind: node.kind as string, status: node.status as string,
      query: node.query as string, layout: node.layout as "cards" | "rows",
      limit: node.limit as number, workspace: facet ? WORKSPACE[facet] : null,
    }));
  };
  const root = design.body;
  if (!object(root) || root.type !== "group" || root.id !== "root"
      || !hasKeys(root, GROUP_KEYS) || !["tabs", "stack", "grid"].includes(String(root.layout)))
    return hold("CGX_GUI_ROOT_GROUP_HOLD");
  visit(root, [], 0);
  if (panels.length < 1 || panels.length > 16)
    return hold("CGX_GUI_NO_BOUNDED_COLLECTIONS");

  return Object.freeze({
    schema: CGX_GENERATED_GUI_SCHEMA, parent: CGX_GENERATED_GUI_ROOT,
    title: design.title as string, layout: root.layout as "tabs" | "stack" | "grid",
    panels: Object.freeze(panels),
    state: "SOURCE_PROJECTION_ONLY" as const,
    nativeAdmitted: false as const, hostAuthenticated: false as const,
    publicPublished: false as const, handlersBound: false as const,
    privateBytesIncluded: false as const,
  });
}

const escapeHtml = (value: string): string => value.replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[char] || char));

/** Pure safe markup projection; no private data or privileged controls. */
export function renderCgxGeneratedGuiMarkup(plan: CgxGeneratedGuiPlan, selected = plan.panels[0]?.id): string {
  const active = plan.panels.find((x) => x.id === selected) || plan.panels[0];
  const tabs = plan.panels.map((panel) =>
    '<button type="button" role="tab" data-cgx-gui-tab="' + panel.id
    + '" aria-selected="' + String(active?.id === panel.id)
    + '" tabindex="' + String(active?.id === panel.id ? 0 : -1)
    + '">' + escapeHtml(panel.title) + '</button>').join("");
  const crumbs = active.path.slice(1).map(escapeHtml).join(" / ");
  const workspace = active.workspace
    ? '<button type="button" data-cgx-gui-open="' + active.workspace
      + '">Open existing ' + escapeHtml(active.workspace) + ' workspace</button>'
    : '<p class="ls-cgx-gui-muted">Unscoped catalogue preview; no private objects loaded</p>';
  return '<div class="ls-cgx-gui-layout" data-layout="' + plan.layout + '">'
    + '<nav class="ls-cgx-gui-tabs" role="tablist" aria-label="Generated CGX views">' + tabs + '</nav>'
    + '<article class="ls-cgx-gui-panel" role="tabpanel" aria-label="' + escapeHtml(active.title) + '">'
    + '<p class="ls-cgx-gui-kicker">' + (crumbs ? crumbs + ' / ' : '') + escapeHtml(active.facet || "workspace")
    + '</p><h3>' + escapeHtml(active.title) + '</h3>'
    + '<div class="ls-cgx-gui-metadata">'
    + '<span>Dataset: ' + escapeHtml(active.dataset) + '</span>'
    + '<span>Projection: ' + escapeHtml(active.layout) + '</span>'
    + '<span>Max rows: ' + active.limit + '</span></div>'
    + '<p>View generated from a source-qualified Interface Studio schema. '
    + 'No private entries, peer DBR evidence or privileged controls are loaded in this preview.</p>'
    + '<div class="ls-cgx-gui-card-stack" data-layout="' + active.layout + '">'
    + '<div class="ls-cgx-gui-preview-card"><strong>Object references</strong>'
    + '<small>Awaiting authenticated FileSpace/DataSpace readback</small></div>'
    + '<div class="ls-cgx-gui-preview-card"><strong>Evidence and rights</strong>'
    + '<small>Source-review only · no native admission</small></div>'
    + '<div class="ls-cgx-gui-preview-card"><strong>Generated controls</strong>'
    + '<small>Preview-only navigation · write actions remain held</small></div></div>'
    + '<div class="ls-cgx-gui-actions">' + workspace + '</div>'
    + '</article></div>';
}

/**
 * Mount *inside* the existing UniSpace shell. The schema editor affects this
 * browser preview only; neither Studio nor a desktop/remote host is mutated.
 */
export function mountCgxGeneratedGui(
  target: HTMLElement, initial: string,
  onOpenWorkspace: (view: CgxShellWorkspace) => void,
): void {
  const source = initial;
  const initialPlan = compileCgxGeneratedGui(source);
  let plan = initialPlan;
  let selected = plan.panels[0]?.id;
  target.innerHTML = '<div class="ls-cgx-gui-head">'
    + '<div><p class="ls-cgx-gui-kicker">Cognigrex.cgx / generated GUI</p>'
    + '<h2>Interface Studio · FileSpace engine</h2>'
    + '<p>Five-facet source layout; existing LightSpeed workspaces remain the only navigation targets.</p></div>'
    + '<span class="ls-cgx-gui-hold">Source review · native held</span></div>'
    + '<div class="ls-cgx-gui-live" id="ls-cgx-gui-preview"></div>'
    + '<details class="ls-cgx-gui-schema"><summary>Review or paste an Interface Studio layout (local preview only)</summary>'
    + '<label for="ls-cgx-gui-json">Portable .cgx interface JSON</label>'
    + '<textarea id="ls-cgx-gui-json" rows="8" spellcheck="false" maxlength="32768"></textarea>'
    + '<div class="ls-cgx-gui-actions"><button type="button" id="ls-cgx-gui-apply">Preview schema</button>'
    + '<button type="button" id="ls-cgx-gui-reset">Restore source layout</button></div></details>'
    + '<p class="ls-cgx-gui-note" id="ls-cgx-gui-note" role="status" aria-live="polite">'
    + 'Source-qualified layout loaded locally; no private data or published site updates.</p>';
  const preview = target.querySelector<HTMLElement>("#ls-cgx-gui-preview")!;
  const textarea = target.querySelector<HTMLTextAreaElement>("#ls-cgx-gui-json")!;
  const note = target.querySelector<HTMLElement>("#ls-cgx-gui-note")!;
  textarea.value = initial;
  const paint = (): void => {
    preview.innerHTML = renderCgxGeneratedGuiMarkup(plan, selected);
    preview.querySelectorAll<HTMLButtonElement>("[data-cgx-gui-tab]").forEach((button) => {
      button.addEventListener("click", () => {
        selected = button.dataset.cgxGuiTab || plan.panels[0]?.id;
        paint();
      });
    });
    preview.querySelectorAll<HTMLButtonElement>("[data-cgx-gui-open]").forEach((button) => {
      button.addEventListener("click", () => {
        const view = button.dataset.cgxGuiOpen as CgxShellWorkspace;
        if (["command", "activity", "objects", "sources", "filespace"].includes(view))
          onOpenWorkspace(view);
      });
    });
  };
  target.querySelector<HTMLButtonElement>("#ls-cgx-gui-apply")?.addEventListener("click", () => {
    try {
      plan = compileCgxGeneratedGui(textarea.value);
      selected = plan.panels[0]?.id;
      note.textContent = "Valid portable layout; browser preview updated. Host import not performed.";
      paint();
    } catch (error) {
      note.textContent = error instanceof CgxInterfaceHold
        ? "Import held: " + error.code + ". Existing layout preserved."
        : "Import held: invalid or unsupported Interface Studio payload.";
    }
  });
  target.querySelector<HTMLButtonElement>("#ls-cgx-gui-reset")?.addEventListener("click", () => {
    textarea.value = source;
    plan = initialPlan;
    selected = plan.panels[0]?.id;
    note.textContent = "Original source-qualified layout restored; no remote mutation.";
    paint();
  });
  paint();
}
