/** Reusable permission-scoped CGX visitor object window. Not a second store. */
import { LENSES, visitorRequest, type CgxLens } from "./visitorBridge";

type CgxView = "overview" | "evidence" | "model" | "map" | "timeline";
type Projection = {
  status: string; public_safe: boolean; projection_id?: string; projection_sha256?: string;
  release_receipt_ref?: string;
  payload?: { title: string; summary: string; evidence_stage: string; limitations: string[];
    citations?: { label: string; url: string; revision: string }[];
    model?: { url: string; sha256: string; kind: string } } | null;
};
const validId = (value: string): boolean => value.length > 0 && value.length <= 120 &&
  /^[A-Za-z0-9._:-]+$/.test(value);
const safeUrl = (value: string): string | null => {
  try {
    const u = new URL(value);
    if (u.protocol !== "https:" || u.username || u.password || u.search || u.hash ||
        !u.hostname.includes(".") || u.hostname.endsWith(".local")) return null;
    return u.href;
  } catch { return null; }
};
const write = (root: HTMLElement, tag: "p" | "h3" | "small" | "strong", message: string): void => {
  const el = document.createElement(tag);
  el.textContent = message; root.append(el);
};
const link = (root: HTMLElement, label: string, href: string): void => {
  const safe = safeUrl(href); if (!safe) return;
  const a = document.createElement("a");
  a.textContent = label; a.href = safe; a.target = "_blank"; a.rel = "noopener noreferrer";
  root.append(a);
};
export function installCgxSurfaceWindow(mount: HTMLElement, currentLens: () => CgxLens,
                                        onObjectSelected: (id: string) => void): void {
  const query = new URLSearchParams(window.location.search);
  const queryId = query.get("object_id") || "";
  const queryLens = query.get("lens") || "";
  const queryView = query.get("view") || "";
  mount.innerHTML = [
    '<div class="cgx-surface-launch"><button type="button" data-cgx-open>Open CGX object window</button>',
    '<small data-cgx-selection>Object not selected · read-only visitor lens</small></div>',
    '<dialog class="cgx-surface-dialog" aria-label="CGX object workspace">',
    '<div class="cgx-surface-header"><div><small>UNISPACE / CGX · FILESPACE PROJECTION</small>',
    '<h2>Object workspace</h2></div><button type="button" data-cgx-close>Close</button></div>',
    '<form class="cgx-surface-form" data-cgx-form>',
    '<label>Exact object ID <input name="object_id" maxlength="120" autocomplete="off" required',
    ' placeholder="cgx:approved:object-id" aria-label="Exact CGX object ID"></label>',
    '<label>Review lens <select name="lens" aria-label="CGX review lens"></select></label>',
    '<label>Surface <select name="view_id" aria-label="CGX surface">',
    '<option value="overview">Object</option><option value="evidence">Evidence</option>',
    '<option value="model">3D / representation</option><option value="map">Map / spatial</option>',
    '<option value="timeline">Historical / DBR</option></select></label>',
    '<button type="submit">Inspect approved projection</button></form>',
    '<p class="cgx-surface-notice">Read-only. Exact release receipt required. Map and historic',
    ' snapshots remain held until admitted source/time/geometry evidence exists.</p>',
    '<div class="cgx-surface-result" data-cgx-result role="status" aria-live="polite"></div>',
    '</dialog>'
  ].join("");
  const dialog = mount.querySelector<HTMLDialogElement>("dialog")!;
  const form = mount.querySelector<HTMLFormElement>("[data-cgx-form]")!;
  const idInput = form.elements.namedItem("object_id") as HTMLInputElement;
  const lensInput = form.elements.namedItem("lens") as HTMLSelectElement;
  const viewInput = form.elements.namedItem("view_id") as HTMLSelectElement;
  const result = mount.querySelector<HTMLElement>("[data-cgx-result]")!;
  const selected = mount.querySelector<HTMLElement>("[data-cgx-selection]")!;
  if (queryView && ["overview", "evidence", "model", "map", "timeline"].includes(queryView))
    viewInput.value = queryView;
  for (const [id, name] of Object.entries(LENSES)) {
    const option = document.createElement("option");
    option.value = id; option.textContent = name; lensInput.add(option);
  }
  if (Object.prototype.hasOwnProperty.call(LENSES, queryLens)) lensInput.value = queryLens;
  if (validId(queryId)) {
    idInput.value = queryId; selected.textContent = queryId + " · visitor read-only";
    onObjectSelected(queryId);
  }
  mount.querySelector<HTMLButtonElement>("[data-cgx-open]")!.onclick = () => {
    lensInput.value = (Object.prototype.hasOwnProperty.call(LENSES, queryLens) ? queryLens : currentLens());
    dialog.showModal(); idInput.focus();
  };
  mount.querySelector<HTMLButtonElement>("[data-cgx-close]")!.onclick = () => dialog.close();
  let busy = false;
  form.onsubmit = async e => {
    e.preventDefault(); if (busy) return;
    const object_id = idInput.value.trim(), lens = lensInput.value as CgxLens;
    const view_id = viewInput.value as CgxView;
    result.replaceChildren();
    if (!validId(object_id) || !Object.prototype.hasOwnProperty.call(LENSES, lens)) {
      write(result, "p", "Use an exact CGX object ID and a permitted lens."); return;
    }
    selected.textContent = object_id + " · visitor read-only";
    onObjectSelected(object_id);
    busy = true;
    try {
      const response = await visitorRequest<Projection>("/api/v1/visitor/surface", {object_id, lens, view_id});
      if (response.status !== "PUBLIC_SAFE_PROJECTION" || !response.public_safe || !response.payload) {
        write(result, "p", response.status === "SURFACE_NOT_RELEASED"
          ? "This surface has not been released for public inspection."
          : "No owner-approved public projection is available for the selected object and lens.");
        return;
      }
      const p = response.payload;
      write(result, "h3", p.title);
      write(result, "small", "Evidence: " + p.evidence_stage + " · View: " + view_id);
      write(result, "p", p.summary);
      for (const item of p.limitations || []) write(result, "p", "Limit: " + item);
      for (const citation of p.citations || []) {
        const line = document.createElement("p"); result.append(line);
        link(line, citation.label + " · " + citation.revision, citation.url);
      }
      if (view_id === "model" && p.model) {
        write(result, "p", "Approved model metadata only; no automatic geometry fetch.");
        const row = document.createElement("p"); result.append(row);
        link(row, "Open approved representation ↗", p.model.url);
      }
      write(result, "small", "Projection: " + (response.projection_id || "unknown") +
        " · SHA-256: " + (response.projection_sha256 || "missing") +
        " · Release: " + (response.release_receipt_ref || "unavailable"));
    } catch (error) {
      write(result, "p", error instanceof Error ? error.message : "Surface unavailable.");
    } finally { busy = false; }
  };
}
