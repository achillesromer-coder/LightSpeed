import "./styles.css";
import { facilityRecords, twinZones, workbookTabs } from "./spaceportTwin";

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

const zoneSummary = twinZones
  .map(
    (zone) => `
      <div class="zone-chip">
        <strong>${(zone.radiusM / 1000).toFixed(zone.radiusM % 1000 === 0 ? 0 : 1)} km</strong>
        <span>${zone.name}</span>
        <em>${zone.description}</em>
      </div>
    `,
  )
  .join("");

const facilitySummary = facilityRecords
  .map(
    (facility) => `
      <li class="facility-row ${facility.releaseStatus}">
        <div>
          <strong>${facility.name}</strong>
          <span>${facility.footprint}</span>
          <small>${facility.elevation}</small>
          <small>${facility.notes}</small>
        </div>
        <em>${facility.releaseStatus.replace("-", " ")}</em>
      </li>
    `,
  )
  .join("");

const workbookSummary = workbookTabs.map((tab) => `<code>${tab}</code>`).join("");

app.innerHTML = `
  <main class="lsgo-shell">
    <section class="hero panel">
      <div>
        <p class="kicker">LightSpeed Go / De Sporte Launch Console</p>
        <h1>Römer Industries Operations</h1>
        <p class="lede">Static, public-safe operator surface for launch evidence, site-twin gates, agent lanes, route state, and compact co-runner handoff.</p>
      </div>
      <div class="hero-actions">
        <span class="badge pass">Connectors authenticated</span>
        <span class="badge pass">Desktop launch ready 22/22</span>
        <span class="badge warn">Agent route verification next</span>
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
        <div class="panel-head twin-head">
          <div>
            <p class="kicker">Cognigrex Site Twin</p>
            <h2>11 km Radial Spaceport Contract</h2>
          </div>
          <div class="twin-toggles" aria-label="Viewer controls staged for workbook-backed embed">
            <span>Römer blueprint</span>
            <span>Daylight architecture</span>
            <span>Labels: none / light / descriptive</span>
            <span>Grid toggle</span>
          </div>
        </div>
        <div class="twin-grid">
          <figure class="site-map" aria-label="Top-down schematic of central facility, X pad layout, roads, and restoration bands">
            <svg viewBox="0 0 640 640" role="img">
              <title>Römer spaceport radial plan</title>
              <circle class="passive-band" cx="320" cy="320" r="300" />
              <circle class="active-band" cx="320" cy="320" r="126" />
              <circle class="facility-band" cx="320" cy="320" r="90" />
              <line class="road" x1="165" y1="165" x2="475" y2="475" />
              <line class="road" x1="475" y1="165" x2="165" y2="475" />
              <line class="road-dash" x1="165" y1="165" x2="475" y2="475" />
              <line class="road-dash" x1="475" y1="165" x2="165" y2="475" />
              <rect class="hall" x="282" y="250" width="76" height="140" rx="8" />
              <polygon class="control" points="320,210 350,232 338,268 302,268 290,232" />
              <circle class="pad starship" cx="190" cy="190" r="34" />
              <circle class="pad starship" cx="450" cy="190" r="34" />
              <circle class="pad falcon" cx="190" cy="450" r="28" />
              <circle class="pad falcon-heavy" cx="450" cy="450" r="30" />
              <path class="flame" d="M180 204 L122 232" />
              <path class="flame" d="M178 437 L125 411" />
              <text x="320" y="60">11 km passive reserve</text>
              <text x="320" y="166">3.5 km active band</text>
              <text x="320" y="306">2.5 km facility limit</text>
            </svg>
          </figure>
          <div class="twin-details">
            <div class="zone-grid">${zoneSummary}</div>
            <ul class="facility-list">${facilitySummary}</ul>
            <p class="workbook-link">Workbook-backed embed contract: ${workbookSummary}</p>
          </div>
        </div>
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
          <li>Promote the workbook contract and site-twin data shape into the Drive/repo truth lane.</li>
          <li>Replace the static schematic with the existing 3D viewer once the artifact is identified and bounded.</li>
          <li>Publish the static route packet and verify public route status, including <code>/ls-go/agents</code>.</li>
          <li>Capture manual UX evidence for LightSpeed, De Sporte, and LS Go.</li>
        </ol>
      </article>
    </section>
  </main>
`;

