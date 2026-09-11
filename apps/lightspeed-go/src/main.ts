import "./styles.css";
import "./mobile.css";
import "./projectFiles.css";
import "./resultReceipts.css";
import "./ownerAuth.css";
import {
  createCommandEnvelope,
  changeDesktopOwnerPassword,
  decideDesktopReview,
  decideRepresentationReview,
  DEFAULT_DESKTOP_ORIGIN,
  DesktopRequestError,
  downloadCommand,
  FLOORS,
  listDesktopProjects,
  listDesktopProjectFiles,
  listDesktopReviews,
  listDesktopResults,
  listDesktopTasks,
  listRepresentationGraphs,
  loginDesktopOwner,
  logoutDesktopOwner,
  openDesktopProjectFile,
  openDesktopResult,
  readDesktopStatus,
  readPendingCommands,
  removePendingCommand,
  routeInstruction,
  reviewDecisionOutcomeMessage,
  storePendingCommand,
  submitDesktopCommand,
  type AuthorityContract,
  type CommandEnvelope,
  type ExecutionMode,
  type Floor,
  type LocalResultsResponse,
  type OwnerAuthResponse,
  type Priority,
  type ProjectRecord,
  type RepresentationDecision,
  type RepresentationGraph,
  type ReviewDecision,
  type ReviewRecord,
} from "./desktopBridge";
import { escapeHtml, loadNeoExchange, renderExchangePanel } from "./neoExchange";
import {
  bindProjectBrowseButtons,
  bindProjectFileOpenButtons,
  renderProjectCards,
  renderProjectFileOpenResult,
  renderProjectFiles,
  renderProjectFilesError,
} from "./projectFiles";
import {
  bindResultReceiptButtons,
  renderResultReceiptOpen,
  renderResultReceipts,
  renderResultReceiptsError,
} from "./resultReceipts";
import { renderRepresentationGraphs } from "./representationGraphs";
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
      <button class="tab" data-view="objects">Objects</button>
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
      <article class="panel owner-auth-panel">
        <div class="panel-head">
          <div><p class="eyebrow">NCNB owner access</p><h2>Local credential gate</h2></div>
          <span class="badge" id="owner-auth-state">Checking credential</span>
        </div>
        <form id="owner-login-form" class="owner-auth-form">
          <label class="field"><span>Username</span><input id="owner-username" autocomplete="username" value="NCNB" maxlength="64"></label>
          <label class="field"><span>Password</span><input id="owner-password" type="password" autocomplete="current-password" maxlength="1024"></label>
          <button class="primary" type="submit">Sign in</button>
          <button id="owner-logout" type="button" hidden>Sign out</button>
        </form>
        <form id="owner-change-form" class="owner-auth-form" hidden>
          <label class="field"><span>Current password</span><input id="owner-current-password" type="password" autocomplete="current-password" maxlength="1024"></label>
          <label class="field"><span>New password</span><input id="owner-new-password" type="password" autocomplete="new-password" maxlength="1024"></label>
          <label class="field"><span>Confirm new password</span><input id="owner-confirm-password" type="password" autocomplete="new-password" maxlength="1024"></label>
          <button class="primary" type="submit">Change password</button>
        </form>
        <div id="owner-auth-result" class="result" aria-live="polite"></div>
        <p class="muted">Sessions remain in memory and expire when this page closes. The Achilles reference stores only the non-secret rotation ID and due dates.</p>
      </article>
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
      <article class="panel result-receipts-panel"><div class="panel-head"><div><p class="eyebrow">Neo + Smith durable proof</p><h2>Local results</h2></div><span class="badge" id="result-auth-state">Checking owner gate</span></div><div id="desktop-results"><p class="muted">Reading fixed local result metadata…</p></div></article>
      <article class="panel"><div class="panel-head"><div><p class="eyebrow">Neo exchange</p><h2>Public-safe projection</h2></div></div><div id="neo-exchange"><p class="muted">Reading bounded exchange projection…</p></div></article>
    </section>

    <section class="view" id="view-objects">
      <article class="panel definition">
        <div><p class="eyebrow">Canonical representation edge</p><h2>Identity, evidence, horizon, review</h2></div>
        <p>Three bounded local candidates prove the complete intake route. Drive becomes canonical only after owner decision, promotion, and exact readback.</p>
      </article>
      <div id="representation-graphs" class="graph-stack">
        <article class="panel"><p class="muted">Reading feature-gated object graphs from Desktop…</p></article>
      </div>
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
let currentAuthorityContract: AuthorityContract | null = null;
let currentReviews: ReviewRecord[] = [];
let currentRepresentationGraphs: RepresentationGraph[] = [];
let ownerSessionToken = "";
let ownerPasswordChangeToken = "";
let ownerUsername = "NCNB";

const ownerAuthMessage = (tone: "good" | "warn" | "bad", message: string): void => {
  const mount = byId("owner-auth-result");
  mount.dataset.tone = tone;
  mount.textContent = message;
};

const applyOwnerAuth = (response: OwnerAuthResponse): void => {
  const loginForm = byId<HTMLFormElement>("owner-login-form");
  const changeForm = byId<HTMLFormElement>("owner-change-form");
  const logoutButton = byId<HTMLButtonElement>("owner-logout");
  ownerUsername = response.credential?.username || ownerUsername;
  ownerSessionToken = response.session_token || "";
  ownerPasswordChangeToken = response.password_change_token || "";
  byId<HTMLInputElement>("owner-password").value = "";
  if (response.authenticated && ownerSessionToken) {
    changeForm.hidden = true;
    logoutButton.hidden = false;
    byId("owner-auth-state").textContent = `${ownerUsername} signed in`;
    ownerAuthMessage("good", `Owner session active until ${response.expires_utc || "page close"}.`);
    return;
  }
  logoutButton.hidden = true;
  changeForm.hidden = !response.change_required;
  loginForm.hidden = false;
  byId("owner-auth-state").textContent = response.change_required
    ? "Password change required"
    : "Sign-in required";
  ownerAuthMessage(
    "warn",
    response.change_required
      ? "The bootstrap password was verified. Enter it again with a new password to complete first login."
      : "Owner sign-in is required for unredacted files, receipts, and decisions.",
  );
};

const requireOwnerSession = (): string => {
  if (ownerSessionToken) return ownerSessionToken;
  ownerAuthMessage("warn", "Sign in as NCNB before performing this owner-gated action.");
  return "";
};

byId<HTMLFormElement>("owner-login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = byId<HTMLInputElement>("owner-username").value.trim();
  const passwordInput = byId<HTMLInputElement>("owner-password");
  try {
    applyOwnerAuth(await loginDesktopOwner(username, passwordInput.value));
  } catch (error) {
    passwordInput.value = "";
    ownerAuthMessage("bad", error instanceof Error ? error.message : "Owner sign-in failed.");
  }
});

byId<HTMLFormElement>("owner-change-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const current = byId<HTMLInputElement>("owner-current-password");
  const next = byId<HTMLInputElement>("owner-new-password");
  const confirmation = byId<HTMLInputElement>("owner-confirm-password");
  if (next.value !== confirmation.value) {
    ownerAuthMessage("bad", "The new passwords do not match.");
    return;
  }
  const token = ownerPasswordChangeToken || ownerSessionToken;
  if (!token) {
    ownerAuthMessage("bad", "Sign in before changing the password.");
    return;
  }
  try {
    const response = await changeDesktopOwnerPassword(
      ownerUsername,
      current.value,
      next.value,
      token,
      Boolean(ownerPasswordChangeToken),
    );
    current.value = "";
    next.value = "";
    confirmation.value = "";
    applyOwnerAuth(response);
  } catch (error) {
    current.value = "";
    next.value = "";
    confirmation.value = "";
    ownerAuthMessage("bad", error instanceof Error ? error.message : "Password change failed.");
  }
});

byId<HTMLButtonElement>("owner-logout").addEventListener("click", async () => {
  const token = ownerSessionToken;
  ownerSessionToken = "";
  ownerPasswordChangeToken = "";
  if (token) {
    try { await logoutDesktopOwner(token); } catch { /* The local session is already cleared. */ }
  }
  byId<HTMLButtonElement>("owner-logout").hidden = true;
  byId("owner-auth-state").textContent = "Signed out";
  ownerAuthMessage("warn", "Owner session cleared from this page.");
});

const renderRoute = (): void => {
  const routed = routeInstruction(instruction.value || "governance");
  targetFloor.value = routed;
  const gate = currentAuthorityContract?.canonical_gate_id;
  routePreview.innerHTML = `<strong>Achilles route:</strong> ${routed} is primary. Neo coordinates and proof returns to this gate.${gate ? ` <small>Authority: ${escapeHtml(gate)}</small>` : " <small>Waiting for the Desktop authority contract.</small>"}`;
};
instruction.addEventListener("input", renderRoute);
renderRoute();

const buildCommand = (): CommandEnvelope => createCommandEnvelope({
  instruction: instruction.value,
  targetFloor: targetFloor.value as Floor,
  priority: priority.value as Priority,
  executionMode: executionMode.value as ExecutionMode,
  authorityContract: currentAuthorityContract,
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

const renderProjects = (projects: ProjectRecord[]): void => {
  const mount = byId("desktop-projects");
  byId("project-count").textContent = String(projects.length);
  mount.innerHTML = renderProjectCards(projects);
  bindProjectBrowseButtons(mount, async (projectId, button) => {
    const card = button.closest<HTMLElement>("[data-project-card]");
    const filesMount = card?.querySelector<HTMLElement>(".project-files");
    if (!filesMount) return;
    if (button.getAttribute("aria-expanded") === "true") {
      button.setAttribute("aria-expanded", "false");
      button.textContent = "Files";
      filesMount.hidden = true;
      return;
    }
    button.disabled = true;
    button.textContent = "Loading…";
    filesMount.hidden = false;
    filesMount.innerHTML = `<p class="muted">Reading bounded project metadata…</p>`;
    try {
      const response = await listDesktopProjectFiles(projectId);
      filesMount.innerHTML = renderProjectFiles(response);
      bindProjectFileOpenButtons(filesMount, async (selectedProjectId, relativePath, openButton) => {
        const resultMount = filesMount.querySelector<HTMLElement>(".project-file-result");
        if (!resultMount) return;
        const ownerSession = requireOwnerSession();
        if (!ownerSession) {
          resultMount.innerHTML = renderProjectFilesError(
            "File preview held: sign in through the NCNB owner gate first.",
          );
          return;
        }
        openButton.disabled = true;
        resultMount.innerHTML = `<p class="muted">Opening read-only result…</p>`;
        try {
          resultMount.innerHTML = renderProjectFileOpenResult(
            await openDesktopProjectFile(selectedProjectId, relativePath, ownerSession),
          );
        } catch (error) {
          resultMount.innerHTML = renderProjectFilesError(
            error instanceof Error ? error.message : "Project file result is unavailable.",
          );
        } finally {
          openButton.disabled = false;
        }
      });
      button.setAttribute("aria-expanded", "true");
      button.textContent = "Hide files";
    } catch (error) {
      filesMount.innerHTML = renderProjectFilesError(
        error instanceof Error ? error.message : "Project files are unavailable.",
      );
      button.textContent = "Retry files";
    } finally {
      button.disabled = false;
    }
  });
};

const renderResults = (
  response: LocalResultsResponse,
  ownerConfirmationConfigured: boolean,
): void => {
  const mount = byId("desktop-results");
  const authState = byId("result-auth-state");
  authState.textContent = ownerConfirmationConfigured ? "Owner gate configured" : "Content gate held";
  mount.innerHTML = renderResultReceipts(response, ownerConfirmationConfigured);
  bindResultReceiptButtons(mount, async (resultId, button) => {
    const detailMount = mount.querySelector<HTMLElement>(".result-receipt-detail");
    if (!detailMount) return;
    if (!ownerConfirmationConfigured) {
      detailMount.innerHTML = renderResultReceiptsError(
        "Receipt content is held because owner confirmation is not configured on the local bridge.",
      );
      return;
    }
    const ownerSession = requireOwnerSession();
    if (!ownerSession) {
      detailMount.innerHTML = renderResultReceiptsError(
        "Receipt inspection held: sign in through the NCNB owner gate first.",
      );
      return;
    }
    button.disabled = true;
    detailMount.innerHTML = `<p class="muted">Opening owner-confirmed read-only receipt…</p>`;
    try {
      detailMount.innerHTML = renderResultReceiptOpen(
        await openDesktopResult(resultId, ownerSession),
      );
    } catch (error) {
      detailMount.innerHTML = renderResultReceiptsError(
        error instanceof Error ? error.message : "Local result receipt is unavailable.",
      );
    } finally {
      button.disabled = false;
    }
  });
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
    const ownerSession = requireOwnerSession();
    if (!ownerSession) {
      setResult("bad", "Review decision held: sign in through the NCNB owner gate first.");
      return;
    }
    try {
      const response = await decideDesktopReview(reviewId, decision, note, ownerSession);
      setResult("good", reviewDecisionOutcomeMessage(reviewId, decision, response));
      await refreshDesktop();
    } catch (error) {
      setResult("bad", error instanceof Error ? error.message : "Review decision failed.");
    }
  }));
};

const renderCanonicalGraphs = (graphs: RepresentationGraph[]): void => {
  currentRepresentationGraphs = graphs;
  const mount = byId("representation-graphs");
  mount.innerHTML = renderRepresentationGraphs(graphs);
  mount.querySelectorAll<HTMLButtonElement>("[data-representation-review]").forEach((button) => {
    button.addEventListener("click", async () => {
      const reviewId = button.dataset.representationReview || "";
      const decision = button.dataset.decision as RepresentationDecision;
      const scope = (button.dataset.scope || "identity") as "identity" | "edges";
      const edgeIds = scope === "edges"
        ? (button.dataset.edgeIds || "").split("|").filter(Boolean).slice(0, 100)
        : [];
      const graph = currentRepresentationGraphs.find(
        (item) => item.review?.review_id === reviewId,
      );
      if (!reviewId || !graph) return;
      const note = window.prompt(
        `${decision.replace(/_/g, " ").toUpperCase()}: ${graph.object.display_name}\n` +
        `${scope === "identity"
          ? "Identity is reviewed before edges."
          : `${edgeIds.length} bounded edges selected.`}\n` +
        "Optional decision note:",
        "",
      ) ?? "";
      const ownerSession = requireOwnerSession();
      if (!ownerSession) {
        setResult("bad", "Representation decision held: sign in through the NCNB owner gate first.");
        return;
      }
      try {
        await decideRepresentationReview(
          reviewId,
          decision,
          scope,
          edgeIds,
          note,
          ownerSession,
        );
        setResult(
          "good",
          `${reviewId} recorded ${decision}; local staging remains noncanonical until Drive readback.`,
        );
        await refreshDesktop();
      } catch (error) {
        setResult(
          "bad",
          error instanceof Error ? error.message : "Representation review decision failed.",
        );
      }
    });
  });
};

byId<HTMLFormElement>("command-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  currentCommand = null;
  try {
    currentCommand = buildCommand();
    setResult("warn", `Sending ${currentCommand.command_id} to Desktop…`);
    const receipt = await submitDesktopCommand(currentCommand);
    removePendingCommand(currentCommand.command_id);
    renderPending();
    setResult("good", `Accepted by Desktop. Task ${receipt.task_id ?? "created"}; ${receipt.state || "queued for governed processing"}.`);
    await refreshDesktop();
  } catch (error) {
    const rejected = error instanceof DesktopRequestError;
    if (currentCommand && !rejected) storePendingCommand(currentCommand);
    renderPending();
    const detail = error instanceof Error ? error.message : "Desktop unavailable";
    setResult(
      "bad",
      rejected
        ? `${detail} Desktop rejected the command; it was not mislabeled as an offline save.`
        : `${detail}${currentCommand ? " The command envelope was saved locally." : ""}`,
    );
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
    currentAuthorityContract = status.authority_contract || null;
    ownerUsername = status.auth?.username || ownerUsername;
    byId<HTMLInputElement>("owner-username").value = ownerUsername;
    if (!ownerSessionToken) {
      byId("owner-auth-state").textContent = status.auth?.configured
        ? status.auth.must_change ? "First change required" : "Sign-in required"
        : "Credential setup held";
      if (!status.auth?.configured) {
        ownerAuthMessage("bad", "The dedicated owner credential is not configured on Desktop.");
      } else if (status.auth.must_change) {
        ownerAuthMessage("warn", "Sign in with the bootstrap password, then complete the required change.");
      }
    }
    renderRoute();
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

    try {
      renderResults(await listDesktopResults(), status.auth?.configured === true);
    } catch (error) {
      byId("result-auth-state").textContent = status.auth?.configured === true
        ? "Owner gate configured"
        : "Content gate held";
      byId("desktop-results").innerHTML = renderResultReceiptsError(
        error instanceof Error ? error.message : "Local result metadata is unavailable.",
      );
    }

    try {
      renderCanonicalGraphs(await listRepresentationGraphs());
    } catch (error) {
      currentRepresentationGraphs = [];
      const reason = status.representation_edge?.enabled === false
        ? "Canonical representation objects are intentionally disabled by the current launch gate."
        : error instanceof Error ? error.message : "Representation objects are unavailable.";
      byId("representation-graphs").innerHTML = `<article class="panel"><p class="eyebrow">Objects unavailable</p><h2>Feature-gated, not empty</h2><p class="muted">${escapeHtml(reason)}</p></article>`;
    }
  } catch {
    currentAuthorityContract = null;
    renderRoute();
    pill.dataset.state = "offline";
    pillText.textContent = "start LightSpeed Desktop and the local bridge";
    desktopState.textContent = "Offline";
    merovingianState.textContent = "Offline";
    byId("project-count").textContent = "0";
    tasksMount.innerHTML = `<p class="muted">Desktop is offline. Commands can still be saved, copied or downloaded.</p>`;
    byId("desktop-projects").innerHTML = `<p class="muted">Project registry unavailable while Desktop is offline.</p>`;
    byId("desktop-reviews").innerHTML = `<p class="muted">Review queue unavailable while Desktop is offline.</p>`;
    byId("owner-auth-state").textContent = "Desktop offline";
    ownerAuthMessage("bad", "Start the local Desktop bridge before signing in.");
    byId("result-auth-state").textContent = "Desktop offline";
    byId("desktop-results").innerHTML = `<p class="muted">Fixed local result metadata is unavailable while Desktop is offline.</p>`;
    renderCanonicalGraphs([]);
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
