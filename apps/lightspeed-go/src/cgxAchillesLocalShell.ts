/**
 * Existing Achilles local control shell: source-qualified, non-authoritative
 * SystemSpace navigation. Port 8772 is NOT the Desktop bridge (8765).
 * No proxy, runtime status inference, execution call, iframe or private relay.
 */
export const ACHILLES_LOCAL_SHELL_SCHEMA = "CGX-ACHILLES-LOCAL-SHELL-PRESENTATION/0.1" as const;
export const ACHILLES_LOCAL_ROOT = "cgx:root:cognigrex" as const;
export const ACHILLES_LOCAL_SHELL_URL = "http://127.0.0.1:8772/" as const;
export const ACHILLES_DESKTOP_BRIDGE_BASELINE = "http://127.0.0.1:8765" as const;
export const ACHILLES_LOCAL_OBSERVATION_DATE = "2026-11-23" as const;

export type AchillesLocalFacet = Readonly<{
  id: "agent_runtime" | "cpu_policy" | "failure_policy" |
      "llm_sorter" | "loaded_models" | "operator_notes";
  label: string;
  observed: string;
  boundary: string;
  state: "OBSERVED_UI_CONTROL_NOT_CONNECTED";
}>;
const ACHILLES_LOCAL_FACET_ROWS: AchillesLocalFacet[] = [
  { id: "agent_runtime", label: "Agent runtime", observed: "Pause, start and stop agent actions are present in the local shell.", boundary: "Actual run state and mutations are not exposed by this UniSpace projection.", state: "OBSERVED_UI_CONTROL_NOT_CONNECTED" },
  { id: "cpu_policy", label: "Resource policy", observed: "CPU ceiling slider spans 10–100 in steps of 5; displayed presets are 40, 70 and 95.", boundary: "No CPU setting is read or changed from this page.", state: "OBSERVED_UI_CONTROL_NOT_CONNECTED" },
  { id: "failure_policy", label: "Reliability", observed: "An auto-disable-failing-agents option is present.", boundary: "Option state and agent failures are unknown until authenticated local readback.", state: "OBSERVED_UI_CONTROL_NOT_CONNECTED" },
  { id: "llm_sorter", label: "Sorting", observed: "A generic LLM sorter pass is offered as a local option.", boundary: "No model-selection or inference invocation is made here.", state: "OBSERVED_UI_CONTROL_NOT_CONNECTED" },
  { id: "loaded_models", label: "Model inventory", observed: "The shell exposes a loaded-models information region.", boundary: "No weights, model identities or active count were verified by the HTTP snapshot.", state: "OBSERVED_UI_CONTROL_NOT_CONNECTED" },
  { id: "operator_notes", label: "Operational notes", observed: "The shell exposes an operational notes region.", boundary: "No notes or private content are copied into UniSpace.", state: "OBSERVED_UI_CONTROL_NOT_CONNECTED" },
];
export const ACHILLES_LOCAL_FACETS: readonly AchillesLocalFacet[] =
  Object.freeze(ACHILLES_LOCAL_FACET_ROWS.map((f) => Object.freeze(f)));

export function resolveAchillesLocalShellUrl(input: unknown): typeof ACHILLES_LOCAL_SHELL_URL {
  if (typeof input !== "string" || input.length > 64) throw new TypeError("ACHILLES_LOCAL_EXACT_ORIGIN_REQUIRED");
  let url: URL;
  try { url = new URL(input); } catch { throw new TypeError("ACHILLES_LOCAL_EXACT_ORIGIN_REQUIRED"); }
  if (url.protocol !== "http:" || url.hostname !== "127.0.0.1" ||
      url.port !== "8772" || url.pathname !== "/" || url.search !== "" ||
      url.hash !== "" || url.username !== "" || url.password !== "") {
    throw new TypeError("ACHILLES_LOCAL_EXACT_ORIGIN_REQUIRED");
  }
  return ACHILLES_LOCAL_SHELL_URL;
}
export type AchillesLocalShellPlan = Readonly<{
  schema: typeof ACHILLES_LOCAL_SHELL_SCHEMA;
  parent: typeof ACHILLES_LOCAL_ROOT;
  endpoint: typeof ACHILLES_LOCAL_SHELL_URL;
  desktopBridgeBaseline: typeof ACHILLES_DESKTOP_BRIDGE_BASELINE;
  observation: Readonly<{
    date: typeof ACHILLES_LOCAL_OBSERVATION_DATE;
    method: "READ_ONLY_GET";
    rootHttp: 200;
    rootTitle: "Achilles shell";
    healthRouteHttp: 404;
    currentBrowserStatus: "NOT_VERIFIED";
  }>;
  localOnly: true;
  privateHydration: false;
  hostAuthVerified: false;
  peerDbrVerified: false;
  nativeAdmitted: false;
  publicReleased: false;
  controlsBound: false;
  networkRequestsFromPage: false;
  facets: readonly AchillesLocalFacet[];
}>;

export function planAchillesLocalShell(): AchillesLocalShellPlan {
  return Object.freeze({
    schema: ACHILLES_LOCAL_SHELL_SCHEMA,
    parent: ACHILLES_LOCAL_ROOT,
    endpoint: resolveAchillesLocalShellUrl(ACHILLES_LOCAL_SHELL_URL),
    desktopBridgeBaseline: ACHILLES_DESKTOP_BRIDGE_BASELINE,
    observation: Object.freeze({
      date: ACHILLES_LOCAL_OBSERVATION_DATE,
      method: "READ_ONLY_GET" as const,
      rootHttp: 200 as const,
      rootTitle: "Achilles shell" as const,
      healthRouteHttp: 404 as const,
      currentBrowserStatus: "NOT_VERIFIED" as const,
    }),
    localOnly: true as const,
    privateHydration: false as const,
    hostAuthVerified: false as const,
    peerDbrVerified: false as const,
    nativeAdmitted: false as const,
    publicReleased: false as const,
    controlsBound: false as const,
    networkRequestsFromPage: false as const,
    facets: ACHILLES_LOCAL_FACETS,
  });
}

/**
 * Inert local navigation panel; no external response, credentials, frames,
 * post/fetch or device action is handled by the calling site.
 */
export function mountAchillesLocalShell(target: HTMLElement): void {
  if (target.dataset.achillesLocalMounted === ACHILLES_LOCAL_SHELL_SCHEMA) return;
  const plan = planAchillesLocalShell();
  const el = (tag: string, className?: string, value?: string): HTMLElement => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = value;
    return node;
  };
  const heading = el("div", "ls-achilles-local-heading");
  const label = el("div");
  label.append(el("p", "ls-achilles-local-kicker", "SystemSpace / local supervisor"),
               el("h2", undefined, "Achilles shell · BouwerBase"),
               el("p", "ls-achilles-local-muted", "Separate existing localhost agent-oversight service; not a new CGX root or remote management gateway."));
  const badge = el("span", "ls-achilles-local-hold", "Local-only / authority held");
  heading.append(label, badge);

  const observation = el("p", "ls-achilles-local-observation",
    "Read-only diagnostic " + plan.observation.date +
    ": GET / → HTTP 200, title “Achilles shell”; GET /health → HTTP 404. " +
    "This is a dated observation, not live browser status.");
  const context = el("p", "ls-achilles-local-muted",
    "Achilles control: " + plan.endpoint +
    " · UniSpace Desktop baseline: " + plan.desktopBridgeBaseline +
    ". Open the link only from the machine where the service is running.");
  const link = document.createElement("a");
  link.href = plan.endpoint;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.className = "ls-achilles-local-link";
  link.textContent = "Open local Achilles control shell";
  link.setAttribute("aria-label", "Open Achilles control shell on this computer; local port 8772");

  const tabs = el("nav", "ls-achilles-local-facet-tabs");
  tabs.setAttribute("aria-label", "Achilles shell observed capabilities");
  const detail = el("div", "ls-achilles-local-detail");
  detail.setAttribute("role", "region");
  detail.setAttribute("aria-live", "polite");
  const buttons: HTMLButtonElement[] = [];
  const show = (index: number): void => {
    const item = plan.facets[index] || plan.facets[0];
    detail.replaceChildren(
      el("h3", undefined, item.label),
      el("p", undefined, item.observed),
      el("p", "ls-achilles-local-muted", item.boundary),
    );
    buttons.forEach((button, i) => {
      button.setAttribute("aria-pressed", String(i === index));
      button.tabIndex = i === index ? 0 : -1;
    });
  };
  plan.facets.forEach((item, i) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = item.label;
    button.addEventListener("click", () => show(i));
    buttons.push(button);
    tabs.append(button);
  });
  const foot = el("p", "ls-achilles-local-muted",
    "No remote control, automatic CORS probe, credentials, local service mutation, model inference, DBR acceptance or publication is performed by this panel.");
  target.replaceChildren(heading, observation, context, link, tabs, detail, foot);
  target.dataset.achillesLocalMounted = plan.schema;
  show(0);
}
