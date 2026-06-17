import "./styles.css";

const app = document.getElementById("app");
if (!app) throw new Error("LightSpeed Go mount node #app not found.");

type StatusTone = "pass" | "warn" | "blocked" | "ready";

const connectorRows = [
  ["GitHub", "Authenticated", "Connected account verified; private identity held in gated handoff", "pass"],
  ["Google Drive", "Authenticated", "Connected account verified; writeback remains approval-gated", "pass"],
  ["Gmail", "Authenticated", "Connected account verified; outbound send remains approval-gated", "pass"],
] satisfies [string, string, string, StatusTone][];

const routeRows = [
  ["/ls-go", "HTTP 200", "Public route is live", "pass"],
  ["/ls-go/status", "HTTP 200", "Status route is live", "pass"],
  ["/ls-go/handoff", "HTTP 200", "Handoff route is live", "pass"],
  ["/ls-go/review", "HTTP 200", "Review route is live", "pass"],
  ["/ls-go/agents", "Verify after publish", "Agent route remains a post-publish route check", "warn"],
] satisfies [string, string, string, StatusTone][];

const agentRows = [
  ["Achilles Core", "Governance/source-of-truth", ":00 / :48", "ready"],
  ["Co-Runner", "Drive review and workbook reconciliation", ":12", "ready"],
  ["Desktop Codex", "Repo build, branch, app evidence", ":24", "ready"],
  ["Terminal Codex", "Shell validation and command receipts", ":24", "ready"],
  ["Claude/UI", "Console and agent-lane artifact pass", ":36", "ready"],
  ["Local Runners", "One-session De Sporte/Ollama gate", ":48", "warn"],
] satisfies [string, string, string, StatusTone][];

const appRows = [
  ["LightSpeed Go", "Vite 8 build green", "C-drive staging is the build lane while D: remains space constrained", "pass"],
  ["De Sporte", "Desktop/runtime world shell", "Packaged Cognigrex shortcut uses explicit data-root and stays resident", "ready"],
  ["Cognigrex", "Operator shell + Smith queue proof", "Desktop launch lane is active; capture UI proof after public route update", "warn"],
] satisfies [string, string, string, StatusTone][];

const memoryRows = [
  ["Short-term", "RAM/current run only", "Keep run deltas compact; do not accumulate raw logs in prompt memory"],
  ["Long-term", "Drive/repo/local review records", "Persist evidence paths, hashes, route statuses, and blockers only"],
  ["Safety", "No secret persistence", "Never store credential values, OAuth secrets, wallet/token/payment/custody/IPFS data"],
];

const renderRows = (rows: [string, string, string, StatusTone][]) =>
  rows
    .map(
      ([name, state, detail, tone]) => `
        <li class="status-row ${tone}">
          <div>
            <strong>${name}</strong>
            <span>${detail}</span>
          </div>
          <em>${state}</em>
        </li>
      `,
    )
    .join("");

app.innerHTML = `
  <main class="lsgo-shell">
    <section class="hero panel">
      <div>
        <p class="kicker">LightSpeed Go / De Sporte Launch Console</p>
        <h1>Römer Industries Operations</h1>
        <p class="lede">Static, public-safe operator surface for launch evidence, agent lanes, route gates, app state, and compact co-runner handoff.</p>
      </div>
      <div class="hero-actions">
        <span class="badge pass">Connectors authenticated</span>
        <span class="badge pass">Vite audit clear</span>
        <span class="badge warn">Public route verification next</span>
      </div>
    </section>

    <section class="grid">
      <article class="panel">
        <div class="panel-head">
          <p class="kicker">Tool State</p>
          <h2>Connectors</h2>
        </div>
        <ul class="status-list">${renderRows(connectorRows)}</ul>
      </article>

      <article class="panel">
        <div class="panel-head">
          <p class="kicker">Public Web</p>
          <h2>Route Gates</h2>
        </div>
        <ul class="status-list">${renderRows(routeRows)}</ul>
      </article>

      <article class="panel">
        <div class="panel-head">
          <p class="kicker">Applications</p>
          <h2>Build / Run State</h2>
        </div>
        <ul class="status-list">${renderRows(appRows)}</ul>
      </article>

      <article class="panel">
        <div class="panel-head">
          <p class="kicker">Agent Rotation</p>
          <h2>Oversight Lanes</h2>
        </div>
        <ul class="status-list">${renderRows(agentRows)}</ul>
      </article>

      <article class="panel wide">
        <div class="panel-head">
          <p class="kicker">Compact Memory</p>
          <h2>RAM + Persistence Policy</h2>
        </div>
        <div class="memory-grid">
          ${memoryRows
            .map(
              ([name, mode, detail]) => `
                <div>
                  <strong>${name}</strong>
                  <em>${mode}</em>
                  <span>${detail}</span>
                </div>
              `,
            )
            .join("")}
        </div>
      </article>

      <article class="panel wide">
        <div class="panel-head">
          <p class="kicker">Next Safe Actions</p>
          <h2>Launch Queue</h2>
        </div>
        <ol class="queue">
          <li>Commit and push the LS Go source, route, and handoff packet.</li>
          <li>Merge the approved branch with <code>origin/Main</code> static-route package files.</li>
          <li>Publish the static route packet and verify public route status.</li>
          <li>Capture manual UX evidence for LightSpeed, De Sporte, and LS Go.</li>
        </ol>
      </article>
    </section>
  </main>
`;
