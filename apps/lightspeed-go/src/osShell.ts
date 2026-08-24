import "./osShell.css";
import { DEFAULT_DESKTOP_ORIGIN, readDesktopStatus, type Floor } from "./desktopBridge";
import {
  AGENT_ROLES,
  inferWorkflowStage,
  normalizeShellView,
  routeOperationalFloor,
  SHELL_SCHEMA,
  SHELL_VIEWS,
  workflowStage,
  WORKFLOW_STAGES,
  type ShellView,
  type WorkflowStageId,
} from "./osShellModel";

const STORAGE_KEY = "lightspeed-cognigrex-os-shell-state-v1";

interface ShellState {
  activeView: ShellView;
  activeAgent: Floor;
  focusMode: boolean;
}

const defaultState: ShellState = {
  activeView: "command",
  activeAgent: "Neo",
  focusMode: false,
};

const readState = (): ShellState => {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") as Partial<ShellState>;
    const floor = AGENT_ROLES.some((agent) => agent.floor === parsed.activeAgent)
      ? parsed.activeAgent as Floor
      : defaultState.activeAgent;
    return {
      activeView: normalizeShellView(parsed.activeView),
      activeAgent: floor,
      focusMode: Boolean(parsed.focusMode),
    };
  } catch {
    return { ...defaultState };
  }
};

let state = readState();

const writeState = (patch: Partial<ShellState>): void => {
  state = { ...state, ...patch };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
};

const escapeText = (value: string): string =>
  value.replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  }[character] || character));

const setActiveView = (view: ShellView): void => {
  const button = document.querySelector<HTMLButtonElement>(`.tab[data-view="${view}"]`);
  if (button && !button.classList.contains("active")) button.click();
  writeState({ activeView: view });
  document.body.dataset.lsWorkspace = view;
};

const setActiveAgent = (floor: Floor, focusInstruction = false): void => {
  writeState({ activeAgent: floor });
  document.body.dataset.lsAgent = floor;
  document.querySelectorAll<HTMLElement>("[data-ls-agent]").forEach((element) => {
    element.dataset.active = element.dataset.lsAgent === floor ? "true" : "false";
  });
  const target = document.getElementById("target-floor") as HTMLSelectElement | null;
  if (target) target.value = floor;
  if (focusInstruction) {
    setActiveView("command");
    (document.getElementById("instruction") as HTMLTextAreaElement | null)?.focus();
  }
};

const setWorkflowStage = (id: WorkflowStageId): void => {
  const selected = workflowStage(id);
  document.body.dataset.lsWorkflow = selected.id;
  document.querySelectorAll<HTMLElement>("[data-ls-stage]").forEach((element) => {
    element.dataset.active = element.dataset.lsStage === selected.id ? "true" : "false";
  });
  const detail = document.getElementById("ls-os-stage-detail");
  if (detail) {
    detail.innerHTML = `<strong>${escapeText(selected.label)}</strong><span>${escapeText(selected.description)}</span><small>${escapeText(selected.owner)} · receipt: ${escapeText(selected.receipt)}</small>`;
  }
};

const makeAgentRail = (): HTMLElement => {
  const rail = document.createElement("aside");
  rail.className = "ls-os-rail";
  rail.setAttribute("aria-label", "Cognigrex agent rail");
  rail.innerHTML = `
    <button class="ls-os-mark" type="button" data-ls-home title="LightSpeed Cognigrex">LS</button>
    <div class="ls-os-agent-stack">
      ${AGENT_ROLES.map((agent) => `
        <button class="ls-os-agent" type="button" data-ls-agent="${agent.floor}" title="${escapeText(agent.floor)} — ${escapeText(agent.role)}">
          <span>${escapeText(agent.short)}</span><small>${escapeText(agent.floor)}</small>
        </button>
      `).join("")}
    </div>
    <button class="ls-os-focus" type="button" data-ls-focus title="Toggle focus mode">◫</button>
  `;
  rail.querySelectorAll<HTMLButtonElement>("[data-ls-agent]").forEach((button) => {
    button.addEventListener("click", () => setActiveAgent(button.dataset.lsAgent as Floor, true));
  });
  rail.querySelector<HTMLButtonElement>("[data-ls-home]")?.addEventListener("click", () => setActiveView("command"));
  rail.querySelector<HTMLButtonElement>("[data-ls-focus]")?.addEventListener("click", () => {
    const next = !state.focusMode;
    writeState({ focusMode: next });
    document.body.dataset.lsFocus = next ? "true" : "false";
  });
  return rail;
};

const makeStatusStrip = (): HTMLElement => {
  const strip = document.createElement("section");
  strip.className = "ls-os-status-strip";
  strip.setAttribute("aria-label", "LightSpeed operating state");
  strip.innerHTML = `
    <div><span class="ls-os-status-dot" id="ls-os-runtime-dot"></span><strong id="ls-os-runtime">Desktop checking</strong><small>${DEFAULT_DESKTOP_ORIGIN}</small></div>
    <div><span class="ls-os-status-dot stable"></span><strong>Neo operational head</strong><small>specialist-agent orchestration</small></div>
    <div><span class="ls-os-status-dot guarded"></span><strong>Achilles oversight</strong><small>evidence · canon · release gate</small></div>
    <div><span class="ls-os-status-dot private"></span><strong>De Sporte</strong><small>private persistence sidecar · metadata only</small></div>
    <button type="button" id="ls-os-palette-open" title="Open command palette (Ctrl/Cmd+K)">⌘K</button>
  `;
  return strip;
};

const makeWorkflow = (): HTMLElement => {
  const workflow = document.createElement("section");
  workflow.className = "ls-os-workflow";
  workflow.setAttribute("aria-label", "ACR3 operating workflow");
  workflow.innerHTML = `
    <div class="ls-os-workflow-track">
      ${WORKFLOW_STAGES.map((stage, index) => `
        <button type="button" data-ls-stage="${stage.id}" title="${escapeText(stage.description)}">
          <span>${String(index + 1).padStart(2, "0")}</span><strong>${escapeText(stage.label)}</strong><small>${escapeText(stage.owner)}</small>
        </button>
      `).join("")}
    </div>
    <div class="ls-os-stage-detail" id="ls-os-stage-detail"></div>
  `;
  workflow.querySelectorAll<HTMLButtonElement>("[data-ls-stage]").forEach((button) => {
    button.addEventListener("click", () => setWorkflowStage(button.dataset.lsStage as WorkflowStageId));
  });
  return workflow;
};

const makePalette = (): HTMLElement => {
  const palette = document.createElement("div");
  palette.className = "ls-os-palette";
  palette.id = "ls-os-palette";
  palette.hidden = true;
  palette.innerHTML = `
    <div class="ls-os-palette-card" role="dialog" aria-modal="true" aria-label="LightSpeed command palette">
      <div class="ls-os-palette-head"><strong>LightSpeed</strong><span>${SHELL_SCHEMA}</span><button type="button" data-ls-close aria-label="Close">×</button></div>
      <input id="ls-os-palette-input" type="search" autocomplete="off" placeholder="Open workspace, select agent, or route an outcome…" />
      <div id="ls-os-palette-results" class="ls-os-palette-results"></div>
    </div>
  `;
  palette.addEventListener("click", (event) => {
    if (event.target === palette) closePalette();
  });
  palette.querySelector<HTMLButtonElement>("[data-ls-close]")?.addEventListener("click", () => closePalette());
  palette.querySelector<HTMLInputElement>("#ls-os-palette-input")?.addEventListener("input", () => renderPaletteResults());
  return palette;
};

const openPalette = (): void => {
  const palette = document.getElementById("ls-os-palette");
  if (!palette) return;
  palette.hidden = false;
  renderPaletteResults();
  window.setTimeout(() => (document.getElementById("ls-os-palette-input") as HTMLInputElement | null)?.focus(), 0);
};

const closePalette = (): void => {
  const palette = document.getElementById("ls-os-palette");
  if (palette) palette.hidden = true;
};

const renderPaletteResults = (): void => {
  const input = document.getElementById("ls-os-palette-input") as HTMLInputElement | null;
  const mount = document.getElementById("ls-os-palette-results");
  if (!input || !mount) return;
  const query = input.value.trim().toLowerCase();
  const viewItems = SHELL_VIEWS
    .filter((view) => !query || view.includes(query))
    .map((view) => `<button type="button" data-palette-view="${view}"><span>Workspace</span><strong>${view}</strong><small>Open ${view} workspace</small></button>`);
  const agentItems = AGENT_ROLES
    .filter((agent) => !query || `${agent.floor} ${agent.role}`.toLowerCase().includes(query))
    .map((agent) => `<button type="button" data-palette-agent="${agent.floor}"><span>Agent</span><strong>${escapeText(agent.floor)}</strong><small>${escapeText(agent.role)}</small></button>`);
  const routeItem = query
    ? [`<button type="button" data-palette-route="true"><span>Neo route</span><strong>${escapeText(routeOperationalFloor(input.value))}</strong><small>Use this text as the command outcome and route it through Cognigrex.</small></button>`]
    : [];
  mount.innerHTML = [...routeItem, ...viewItems, ...agentItems].slice(0, 14).join("");
  mount.querySelectorAll<HTMLButtonElement>("[data-palette-view]").forEach((button) => button.addEventListener("click", () => {
    setActiveView(normalizeShellView(button.dataset.paletteView));
    closePalette();
  }));
  mount.querySelectorAll<HTMLButtonElement>("[data-palette-agent]").forEach((button) => button.addEventListener("click", () => {
    setActiveAgent(button.dataset.paletteAgent as Floor, true);
    closePalette();
  }));
  mount.querySelector<HTMLButtonElement>("[data-palette-route]")?.addEventListener("click", () => {
    const text = input.value.trim();
    const instruction = document.getElementById("instruction") as HTMLTextAreaElement | null;
    if (instruction && text) {
      instruction.value = text;
      instruction.dispatchEvent(new Event("input", { bubbles: true }));
      setActiveAgent(routeOperationalFloor(text));
      setWorkflowStage(inferWorkflowStage(text));
      instruction.focus();
    }
    setActiveView("command");
    closePalette();
  });
};

const bindExistingSurface = (): void => {
  document.querySelectorAll<HTMLButtonElement>(".tab[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      const view = normalizeShellView(button.dataset.view);
      writeState({ activeView: view });
      document.body.dataset.lsWorkspace = view;
    });
  });

  const instruction = document.getElementById("instruction") as HTMLTextAreaElement | null;
  const routePreview = document.getElementById("route-preview");
  instruction?.addEventListener("input", () => {
    const floor = routeOperationalFloor(instruction.value);
    setActiveAgent(floor);
    setWorkflowStage(inferWorkflowStage(instruction.value));
    if (routePreview) {
      routePreview.innerHTML = `<strong>Neo route:</strong> ${escapeText(floor)} is the primary specialist. Achilles remains the evidence, canonical-promotion and release oversight gate.`;
    }
  });

  document.getElementById("ls-os-palette-open")?.addEventListener("click", () => openPalette());
};

const refreshRuntimeStatus = async (): Promise<void> => {
  const label = document.getElementById("ls-os-runtime");
  const dot = document.getElementById("ls-os-runtime-dot");
  if (!label || !dot) return;
  try {
    const status = await readDesktopStatus();
    const healthy = Boolean(status.ok && status.services?.merovingian !== false);
    label.textContent = healthy ? "Desktop online" : "Desktop degraded";
    dot.dataset.state = healthy ? "online" : "degraded";
    dot.title = status.time_utc ? `Last read ${status.time_utc}` : "Local status read";
  } catch {
    label.textContent = "Desktop offline / unproved";
    dot.dataset.state = "offline";
    dot.title = "No current localhost receipt from this browser.";
  }
};

const installShell = (): void => {
  if (document.documentElement.dataset.lsOsShell === SHELL_SCHEMA) return;
  const shell = document.querySelector<HTMLElement>(".shell");
  if (!shell) return;

  document.documentElement.dataset.lsOsShell = SHELL_SCHEMA;
  document.body.classList.add("ls-os-enabled");
  document.body.dataset.lsFocus = state.focusMode ? "true" : "false";
  document.title = "LightSpeed · Cognigrex";

  document.body.prepend(makeAgentRail());
  shell.prepend(makeWorkflow());
  shell.prepend(makeStatusStrip());
  document.body.append(makePalette());

  const heading = shell.querySelector(".topbar h1");
  if (heading) heading.textContent = "Cognigrex";
  const eyebrow = shell.querySelector(".topbar .eyebrow");
  if (eyebrow) eyebrow.textContent = "LightSpeed operating system";
  const lede = shell.querySelector(".topbar .lede");
  if (lede) lede.textContent = "Neo coordinates specialised purpose agents across intake, workshop execution, proof, canonical consolidation and publish-ready digital artifacts; Achilles governs evidence and release.";

  bindExistingSurface();
  setActiveView(state.activeView);
  setActiveAgent(state.activeAgent);

  const instruction = document.getElementById("instruction") as HTMLTextAreaElement | null;
  setWorkflowStage(inferWorkflowStage(instruction?.value || ""));
  refreshRuntimeStatus().catch(() => undefined);
  window.setInterval(() => refreshRuntimeStatus().catch(() => undefined), 30000);

  window.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      openPalette();
      return;
    }
    if (event.key === "Escape") closePalette();
    if ((event.ctrlKey || event.metaKey) && /^[1-5]$/.test(event.key)) {
      event.preventDefault();
      setActiveView(SHELL_VIEWS[Number(event.key) - 1] || "command");
    }
  });
};

queueMicrotask(installShell);
