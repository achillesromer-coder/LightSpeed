import "./styles.css";
import {
  createCommandEnvelope,
  decideDesktopReview,
  DEFAULT_DESKTOP_ORIGIN,
  downloadCommand,
  FLOORS,
  listDesktopProjects,
  listDesktopReviews,
  listDesktopTasks,
  readDesktopStatus,
  readPendingCommands,
  removePendingCommand,
  routeInstruction,
  storePendingCommand,
  submitDesktopCommand,
  type CommandEnvelope,
  type ExecutionMode,
  type Floor,
  type Priority,
  type ProjectRecord,
  type ReviewDecision,
  type ReviewRecord,
} from "./desktopBridge";
import { escapeHtml, loadNeoExchange, renderExchangePanel } from "./neoExchange";
import { facilityRecords, twinZones, workbookTabs } from "./spaceportTwin";

const app = document.getElementById("app");
if (!app) throw new Error("LightSpeed Go mount node #app not found.");

const sourceLinks = [
  ["LightSpeed Git", "https://github.com/achillesromer-coder/LightSpeed", "Versioned implementation and receipts"],
  ["LS GO Queue", "https://docs.google.com/spreadsheets/d/1f5i4V3FshYHkztv3_HAg0ZofUl0sdcJZcwrlesUlCfM/edit", "Phone tasks, approvals, commands, results and sync health"],
  ["Portfolio Handoff", "https://docs.google.com/document/d/1tsDkb79UVX_SqS2-oBgc5DHb89QIlH3DcmKMN77hdOo/edit", "Cross-chat portfolio continuity"],
  ["Römer Industries", "https://romer.industries", "Reviewed public portfolio surface"],
] as const;

const agentRows = [
  ["Achilles", "governance, proof and release"],
  ["Neo", "task routing and handoff"],
  ["Architect", "projects, plans and dependencies"],
  ["TheConstruct", "simulation and digital twins"],
  ["Morpheus", "claim proof and conflict resolution"],
  ["Oracle", "sources, evidence and knowns"],
  ["Smith", "Git, code, schemas and execution"],
  ["Merovingian", "health, storage, projects and recovery"],
  ["Trinity", "interface and visual implementation"],
] as const;

app.innerHTML = `
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">LightSpeed GO</p>
        <h1>Command Centre</h1>
        <p class="lede">Achilles-governed commands, Desktop execution, project visibility, review receipts and source continuity.</p>
      </div>
      <div class="connection-pill" id="desktop-pill" data-state="checking">
        <span class="status-dot"></span>
        <div><strong>Desktop</strong><small id="desktop-pill-text">checking local runtime</small></div>
      </div>
    </header>

    <nav class="tabs" aria-label="LS GO views">
      <button class="tab active" data-view="command">Command</button>
      <button class="tab" data-view="activity">Activity</button>
      <button class="tab" data-view="system">System</button>
      <button class="tab" data-view="sources">Sources</button>
    </nav>

    <section class="view active" id="view-command">
      <div class="command-layout">
        <article class="panel command-panel">
          <div class="panel-head">
            <div><p class="eyebrow">Achilles assistant</p><h2>State the outcome</h2></div>
            <span class="badge">review-gated</span>
          </div>
          <form id="command-form">
            <label class="field field-wide"><span>Command</span><textarea id="instruction" rows="7" placeholder="Example: Reconcile a project, run bounded checks, write its receipt to Drive and return it here for approval." required></textarea></label>
            <div class="form-grid">
              <label class="field"><span>Route</span><select id="target-floor">${FLOORS.map((floor) => `<option value="${floor}">${floor}</option>`).join("")}</select></label>
              <label class="field"><span>Priority</span><select id="priority"><option value="normal">Normal</option><option value="high">High</option><option value="critical">Critical</option><option value="low">Low</option></select></label>
              <label class="field"><span>Mode</span><select id="execution-mode"><option value="review">Prepare for review</option><option value="queue">Queue on Desktop</option></select></label>
            </div>
            <div class="route-preview" id="route-preview"></div>
            <div class="actions">
              <button class="primary" type="submit">Send to Desktop</button>
              <button type="button" id="save-command">Save envelope</button>
              <button type="button" id="copy-command">Copy JSON</button>
            </div>
          </form>
          <div id="command-result" class="result" aria-live="polite"></div>
        </article>

        <aside class="panel guardrail-panel">
          <p class="eyebrow">Operating contract</p>
          <h2>Local work, durable proof</h2>
          <ol class="compact-list">
            <li>Achilles remains the oversight floor.</li>
            <li>Neo routes one primary floor at a time.</li>
            <li>Architect exposes the canonical project registry.</li>
            <li>Merovingian records health, storage and receipts.</li>
            <li>Project work returns here for approve, hold or reject.</li>
          </ol>
          <div class="boundary"><strong>No destructive autonomy.</strong><span>Cleanup is evidence-gated; Web, publication, payments and direct public execution remain outside this loop.</span></div>
        </aside>
      </div>
    </section>

    <section class="view" id="view-activity">
      <div class="metric-grid">
        <article class="metric"><span>Desktop API</span><strong id="desktop-state">Checking</strong><small>${DEFAULT_DESKTOP_ORIGIN}</small></article>
        <article class="metric"><span>Merovingian</span><strong id="merovingian-state">Checking</strong><small>database · storage · health</small></article>
        <article class="metric"><span>Projects</span><strong id="project-count">0</strong><small>Desktop-visible project roots</small></article>
        <article class="metric"><span>Pending fallback</span><strong id="pending-count">0</strong><small>saved command envelopes</small></article>
      </div>
      <div class="two-column">
        <article class="panel"><div class="panel-head"><div><p class="eyebrow">Desktop</p><h2>Latest tasks</h2></div><button id="refresh-desktop">Refresh</button></div><div id="desktop-tasks" class="stack-list"><p class="muted">Desktop tasks appear when the local runtime is available.</p></div></article>
        <article class="panel"><div class="panel-head"><div><p class="eyebrow">Fallback</p><h2>Saved commands</h2></div></div><div id="pending-commands" class="stack-list"></div></article>
      </div>
      <div class="two-column">
        <article class="panel"><div class="panel-head"><div><p class="eyebrow">Architect + Merovingian</p><h2>Available projects</h2></div></div><div id="desktop-projects" class="stack-list"><p class="muted">Project registry appears when Desktop is online.</p></div></article>
        <article class="panel"><div class="panel-head"><div><p class="eyebrow">Nathaniel / Achilles gate</p><h2>Review queue</h2></div></div><div id="desktop-reviews" class="stack-list"><p class="muted">Project receipts appear here for approval.</p></div></article>
      </div>
      <article class="panel"><div class="panel-head"><div><p class="eyebrow">Neo exchange</p><h2>Public-safe projection</h2></div></div><div id="neo-exchange"><p class="muted">Reading bounded exchange projection…</p></div></article>
    </section>

    <section class="view" id="view-system">
      <article class="panel definition">
        <div><p class="eyebrow">cognigrex</p><h2>Common goal, distinct agents</h2></div>
        <p>The system coordinates GO, Desktop, Git, Drive, agents and human oversight while retaining separate authority, resource limits and reviewable receipts.</p>
      </article>
      <div class="agent-grid">${agentRows.map(([name, role]) => `<article class="agent"><strong>${name}</strong><span>${role}</span></article>`).join("")}</div>
      <div class="two-column">
        <article class="panel"><p class="eyebrow">Execution path</p><h2>One project, one receipt chain</h2><div class="flow"><span>LS GO</span><i>→</i><span>Achilles</span><i>→</i><span>Neo + floor</span><i>→</i><span>Desktop project</span><i>→</i><span>Drive receipt</span><i>→</i><span>GO decision</span></div></article>
        <article class="panel"><p class="eyebrow">Existing twin context</p><h2>Spaceport contract retained</h2><p class="muted">${twinZones.length} zones · ${facilityRecords.length} facility records · ${workbookTabs.length} workbook tabs. The twin remains bounded context, not the command-centre homepage.</p></article>
      </div>
    </section>

    <section class="view" id="view-sources">
      <div class="source-grid">${sourceLinks.map(([name, url, role]) => `<a class="source-card" href="${url}" target="_blank" rel="noreferrer"><strong>${name}</strong><span>${role}</span><em>Open ↗</em></a>`).join("")}</div>
      <article class="panel"><p class="eyebrow">Authority order</p><h2>Where each truth lives</h2><div class="authority-grid"><div><strong>Drive</strong><span>evidence, workbooks and review receipts</span></div><div><strong>Git</strong><span>code, schemas, tests and implementation receipts</span></div><div><strong>Desktop</strong><span>projects, local execution, state and jobs</span></div><div><strong>LS GO</strong><span>owner commands, review and bounded decisions</span></div></div></article>
    </section>
  </main>
`;

const byId = <T extends HTMLElement>(id: string): T => {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Missing #${id}`);
  return element as T;
};

const instruction = byId<HTMLTextAreaElement>("instruction");
const targetFloor = byId<HTMLSelectElement>("target-floor");
const priority = byId<HTMLSelectElement>("priority");
const executionMode = byId<HTMLSelectElement>("execution-mode");
const routePreview = byId<HTMLDivElement>("route-preview");
const resultBox = byId<HTMLDivElement>("command-result");
let currentCommand: CommandEnvelope | null = null;
let currentReviews: ReviewRecord[] = [];

const renderRoute = (): void => {
  const routed = routeInstruction(instruction.value || "governance");
  targetFloor.value = routed;
  routePreview.innerHTML = `<strong>Achilles route:</strong> ${routed} is primary. Neo coordinates and proof returns to this gate.`;
};
instruction.addEventListener("input", renderRoute);
renderRoute();

const buildCommand = (): CommandEnvelope => createCommandEnvelope({
  instruction: instruction.value,
  targetFloor: targetFloor.value as Floor,
  priority: priority.value as Priority,
  executionMode: executionMode.value as ExecutionMode,
});

const setResult = (tone: "good" | "warn" | "bad", text: string): void => {
  resultBox.dataset.tone = tone;
  resultBox.textContent = text;
};

const renderPending = (): void => {
  const commands = readPendingCommands();
  byId("pending-count").textContent = String(commands.length);
  const mount = byId("pending-commands");
  if (!commands.length) {
    mount.innerHTML = `<p class="muted">No locally saved commands.</p>`;
    return;
  }
  mount.innerHTML = commands.map((command) => `<article class="task-card"><div><strong>${escapeHtml(command.title)}</strong><span>${escapeHtml(command.target_floor)} · ${escapeHtml(command.priority)} · ${escapeHtml(command.execution_mode)}</span><small>${escapeHtml(command.command_id)}</small></div><div class="task-actions"><button data-send="${escapeHtml(command.command_id)}">Send</button><button data-download="${escapeHtml(command.command_id)}">Download</button></div></article>`).join("");
  mount.querySelectorAll<HTMLButtonElement>("[data-send]").forEach((button) => button.addEventListener("click", async () => {
    const command = commands.find((item) => item.command_id === button.dataset.send);
    if (!command) return;
    try {
      const receipt = await submitDesktopCommand(command);
      removePendingCommand(command.command_id);
      renderPending();
      setResult("good", `Desktop accepted ${receipt.command_id || command.command_id}. Task ${receipt.task_id ?? "created"}.`);
      await refreshDesktop();
    } catch (error) {
      setResult("bad", error instanceof Error ? error.message : "Desktop command failed.");
    }
  }));
  mount.querySelectorAll<HTMLButtonElement>("[data-download]").forEach((button) => button.addEventListener("click", () => {
    const command = commands.find((item) => item.command_id === button.dataset.download);
    if (command) downloadCommand(command);
  }));
};

const formatBytes = (value?: number): string => {
  const bytes = Number(value || 0);
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
};

const renderProjects = (projects: ProjectRecord[]): void => {
  const mount = byId("desktop-projects");
  byId("project-count").textContent = String(projects.length);
  if (!projects.length) {
    mount.innerHTML = `<p class="muted">No project folders were found in the configured roots.</p>`;
    return;
  }
  mount.innerHTML = projects.slice(0, 30).map((project) => `<article class="task-card"><div><strong>${escapeHtml(project.name)}</strong><span>${escapeHtml(project.condition || "unknown")} · ${escapeHtml(project.authority || "reference")} · ${project.file_count || 0} files</span><small>${formatBytes(project.size_bytes)}${project.scan_truncated ? " · bounded scan" : ""}</small></div></article>`).join("");
};

const renderReviews = (reviews: ReviewRecord[]): void => {
  currentReviews = reviews;
  const mount = byId("desktop-reviews");
  if (!reviews.length) {
    mount.innerHTML = `<p class="muted">No project receipts are awaiting review.</p>`;
    return;
  }
  mount.innerHTML = reviews.slice(0, 30).map((review) => {
    const state = review.state || "pending_review";
    const pending = state === "pending_review";
    const actions = pending ? `<div class="task-actions"><button data-review="${escapeHtml(review.review_id)}" data-decision="approve">Approve</button><button data-review="${escapeHtml(review.review_id)}" data-decision="hold">Hold</button><button data-review="${escapeHtml(review.review_id)}" data-decision="reject">Reject</button></div>` : "";
    return `<article class="task-card"><div><strong>${escapeHtml(review.title || "Project receipt")}</strong><span>${escapeHtml(state)} · ${escapeHtml(review.event_type || "receipt")}</span><small>${escapeHtml(review.summary || review.review_id)}</small></div>${actions}</article>`;
  }).join("");
  mount.querySelectorAll<HTMLButtonElement>("[data-review]").forEach((button) => button.addEventListener("click", async () => {
    const reviewId = button.dataset.review || "";
    const decision = button.dataset.decision as ReviewDecision;
    const review = currentReviews.find((item) => item.review_id === reviewId);
    if (!review || !reviewId) return;
    const note = window.prompt(`${decision.toUpperCase()}: ${review.title || reviewId}\nOptional decision note:`, "") ?? "";
    try {
      await decideDesktopReview(reviewId, decision, note);
      setResult("good", `${reviewId} marked ${decision}. Drive decision receipt written by Desktop.`);
      await refreshDesktop();
    } catch (error) {
      setResult("bad", error instanceof Error ? error.message : "Review decision failed.");
    }
  }));
};

byId<HTMLFormElement>("command-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    currentCommand = buildCommand();
    setResult("warn", `Sending ${currentCommand.command_id} to Desktop…`);
    const receipt = await submitDesktopCommand(currentCommand);
    removePendingCommand(currentCommand.command_id);
    renderPending();
    setResult("good", `Accepted by Desktop. Task ${receipt.task_id ?? "created"}; ${receipt.state || "queued for governed processing"}.`);
    await refreshDesktop();
  } catch (error) {
    if (currentCommand) storePendingCommand(currentCommand);
    renderPending();
    setResult("bad", `${error instanceof Error ? error.message : "Desktop unavailable"} The command envelope was saved locally.`);
  }
});

byId("save-command").addEventListener("click", () => {
  try {
    currentCommand = buildCommand();
    storePendingCommand(currentCommand);
    renderPending();
    setResult("good", `${currentCommand.command_id} saved locally.`);
  } catch (error) {
    setResult("bad", error instanceof Error ? error.message : "Command could not be saved.");
  }
});

byId("copy-command").addEventListener("click", async () => {
  try {
    currentCommand = buildCommand();
    await navigator.clipboard.writeText(JSON.stringify(currentCommand, null, 2));
    setResult("good", `${currentCommand.command_id} copied as JSON.`);
  } catch (error) {
    setResult("bad", error instanceof Error ? error.message : "Command could not be copied.");
  }
});

const refreshDesktop = async (): Promise<void> => {
  const pill = byId("desktop-pill");
  const desktopState = byId("desktop-state");
  const merovingianState = byId("merovingian-state");
  const pillText = byId("desktop-pill-text");
  const tasksMount = byId("desktop-tasks");
  pill.dataset.state = "checking";
  pillText.textContent = "checking local runtime";
  desktopState.textContent = "Checking";
  merovingianState.textContent = "Checking";
  try {
    const status = await readDesktopStatus();
    pill.dataset.state = status.ok ? "online" : "degraded";
    pillText.textContent = status.ok ? "local runtime connected" : "runtime connected; health needs review";
    desktopState.textContent = "Online";
    merovingianState.textContent = status.merovingian?.status === "pass" ? "Healthy" : "Degraded";

    try {
      const tasks = await listDesktopTasks();
      tasksMount.innerHTML = tasks.length ? tasks.map((task) => `<article class="task-card"><div><strong>${escapeHtml(String(task.title || "Untitled task"))}</strong><span>${escapeHtml(String(task.status || "unknown"))} · ${escapeHtml(String(task.priority || "normal"))}</span><small>Task ${escapeHtml(String(task.id || ""))}</small></div></article>`).join("") : `<p class="muted">Desktop queue is clear.</p>`;
    } catch {
      tasksMount.innerHTML = `<p class="muted">Desktop is online, but task listing is unavailable.</p>`;
    }

    try {
      const projectResponse = await listDesktopProjects();
      renderProjects(projectResponse.projects);
    } catch {
      renderProjects([]);
    }

    try {
      renderReviews(await listDesktopReviews());
    } catch {
      renderReviews([]);
    }
  } catch {
    pill.dataset.state = "offline";
    pillText.textContent = "start LightSpeed Desktop and the local bridge";
    desktopState.textContent = "Offline";
    merovingianState.textContent = "Offline";
    byId("project-count").textContent = "0";
    tasksMount.innerHTML = `<p class="muted">Desktop is offline. Commands can still be saved, copied or downloaded.</p>`;
    byId("desktop-projects").innerHTML = `<p class="muted">Project registry unavailable while Desktop is offline.</p>`;
    byId("desktop-reviews").innerHTML = `<p class="muted">Review queue unavailable while Desktop is offline.</p>`;
  }
};

byId("refresh-desktop").addEventListener("click", () => void refreshDesktop());
renderPending();
void refreshDesktop();

const exchangeMount = byId("neo-exchange");
const projectionUrl = new URL("./data/neo_exchange.json", document.baseURI).toString();
void loadNeoExchange(async () => {
  const response = await fetch(projectionUrl, { cache: "no-store" });
  if (!response.ok) throw new Error(`Neo exchange returned HTTP ${response.status}`);
  return response.json();
}).then((exchange) => { exchangeMount.innerHTML = renderExchangePanel(exchange); });

document.querySelectorAll<HTMLButtonElement>(".tab").forEach((button) => button.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
  document.querySelectorAll(".view").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  byId(`view-${button.dataset.view}`).classList.add("active");
}));
