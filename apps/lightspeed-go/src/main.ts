import "./styles.css";
import { loadNeoExchange, renderExchangePanel } from "./neoExchange";
import { facilityRecords, twinZones, workbookTabs } from "./spaceportTwin";

const app = document.getElementById("app");
if (!app) throw new Error("LightSpeed Go mount node #app not found.");

type StatusTone = "pass" | "warn" | "blocked" | "ready";

const controlGateRows = [
  ["Nathaniel Bower", "Owner orientation", "Sets intent, priorities, approvals, holds and final operating direction", "pass"],
  ["Achilles", "Governance and control gate", "Validates authority, evidence, risk, rationale and release boundaries", "pass"],
  ["DBL", "Inform and direct through GO", "May analyse and recommend direction to Neo only after Achilles/owner gate acceptance", "ready"],
  ["Neo", "Subordinate routing and execution", "Routes one accepted bounded action; cannot redefine owner intent or orient the system", "ready"],
] satisfies [string, string, string, StatusTone][];

const connectorRows = [
  ["GitHub", "Authenticated", "Connected account verified; write and merge remain GO/Achilles gated", "pass"],
  ["Google Drive", "Authenticated", "Connected account verified; canonical writeback remains approval-gated", "pass"],
  ["Gmail", "Authenticated", "Connected account verified; outbound send remains owner-gated", "pass"],
] satisfies [string, string, string, StatusTone][];

const routeRows = [
  ["/ls-go", "Observed HTTP 200", "Owner-control route observed; access and publication state remain separate", "pass"],
  ["/ls-go/status", "Observed HTTP 200", "Status route observed; claims require current evidence", "pass"],
  ["/ls-go/handoff", "Observed HTTP 200", "Handoff route observed; action remains GO-gated", "pass"],
  ["/ls-go/review", "Observed HTTP 200", "Review route observed; Athene remains training/review-only", "pass"],
  ["/ls-go/agents", "Observed HTTP 404", "Agent route is not proven available; keep it out of primary navigation", "warn"],
] satisfies [string, string, string, StatusTone][];

const agentRows = [
  ["Achilles Core", "Owner governance and source-of-truth gate", "Daily owner brief / control decision", "ready"],
  ["DBL", "Evidence, analysis and direction input", "Feeds GO; no direct execution authority", "ready"],
  ["Neo", "Accepted-action router", "One bounded envelope after GO acceptance", "ready"],
  ["Co-Runner", "Drive review and workbook reconciliation", "Evidence and canonical sync", "ready"],
  ["Desktop Codex", "Repo build, branch and app evidence", "Execution beneath accepted Neo routing", "ready"],
  ["Terminal Codex", "Shell validation and command receipts", "Execution proof only", "ready"],
  ["Claude/UI", "Console and agent-lane artifact pass", "Presentation consumes accepted state", "ready"],
  ["Local Runners", "One-session De Sporte/Ollama gate", "No autonomous authority", "warn"],
] satisfies [string, string, string, StatusTone][];

const appRows = [
  ["LightSpeed Go", "Owner/Achilles control gate", "Private review and approval surface; not canonical data authority or public publication surface", "pass"],
  ["De Sporte", "Desktop/runtime world shell", "Runs accepted work beneath GO and Neo routing", "ready"],
  ["Cognigrex", "Bounded analysis host", "May compare and recommend; cannot select, approve, publish or deploy independently", "warn"],
] satisfies [string, string, string, StatusTone][];

const memoryRows = [
  ["Short-term", "RAM/current run only", "Keep run deltas compact; do not accumulate raw logs in prompt memory"],
  ["Long-term", "CORE/Drive/repo review records", "Persist owner decisions, evidence paths, hashes, route states and blockers"],
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
        <p class="kicker">LightSpeed Go / Achilles Control Gate</p>
        <h1>Nathaniel Bower · Römer Industries</h1>
        <p class="lede">Private owner and Achilles control-gate surface for intent, approvals, holds, evidence, rationale and the next authorised actions. DBL may inform and direct Neo through this gate; Neo remains subordinate routing and execution.</p>
      </div>
      <div class="hero-actions">
        <span class="badge pass">Owner-oriented</span>
        <span class="badge pass">Achilles governed</span>
        <span class="badge ready">Neo subordinate</span>
      </div>
    </section>

    <section class="grid">
      <article class="panel wide">
        <div class="panel-head">
          <p class="kicker">Authority Chain</p>
          <h2>GO Control Gate</h2>
        </div>
        <ul class="status-list">${renderRows(controlGateRows)}</ul>
      </article>

      <article class="panel">
        <div class="panel-head">
          <p class="kicker">Tool State</p>
          <h2>Connectors</h2>
        </div>
        <ul class="status-list">${renderRows(connectorRows)}</ul>
      </article>

      <article class="panel">
        <div class="panel-head">
          <p class="kicker">Route Evidence</p>
          <h2>Observed Gates</h2>
        </div>
        <ul class="status-list">${renderRows(routeRows)}</ul>
      </article>

      <article class="panel">
        <div class="panel-head">
          <p class="kicker">Applications</p>
          <h2>Control / Run State</h2>
        </div>
        <ul class="status-list">${renderRows(appRows)}</ul>
      </article>

      <article class="panel">
        <div class="panel-head">
          <p class="kicker">Authority and Execution</p>
          <h2>Bounded Lanes</h2>
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
            <p class="workbook-link">Workbook-backed review contract: ${workbookSummary}</p>
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
        <div class="panel-head exchange-head">
          <div>
            <p class="kicker">GO-Gated Neo Routing</p>
            <h2>Accepted Queue Projection</h2>
          </div>
          <span class="badge ready">Requires owner/Achilles acceptance</span>
        </div>
        <div id="neo-exchange" aria-live="polite">
          <p class="exchange-loading">Reading the bounded routed-action projection...</p>
        </div>
      </article>

      <article class="panel wide">
        <div class="panel-head">
          <p class="kicker">Next Authorised Actions</p>
          <h2>GO-Gated Queue</h2>
        </div>
        <ol class="queue">
          <li>Read the current CORE and GO owner-decision state before selecting work.</li>
          <li>Consolidate duplicate knowledge, draft and site records through the unified Appendix &amp; Log while retaining provenance.</li>
          <li>Route one DBL-informed, Achilles-accepted bounded action to Neo for execution and receipt capture.</li>
          <li>Verify route, claim and data-state evidence before any publication or deployment decision.</li>
        </ol>
      </article>
    </section>
  </main>
`;

const exchangeMount = document.getElementById("neo-exchange");
if (exchangeMount) {
  const projectionUrl = new URL("./data/neo_exchange.json", document.baseURI).toString();
  void loadNeoExchange(async () => {
    const response = await fetch(projectionUrl, { cache: "no-store" });
    if (!response.ok) throw new Error(`Neo exchange returned HTTP ${response.status}`);
    return response.json();
  }).then((exchange) => {
    exchangeMount.innerHTML = renderExchangePanel(exchange);
  });
}
