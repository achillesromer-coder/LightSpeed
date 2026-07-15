(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),e.crossOrigin===`use-credentials`?t.credentials=`include`:e.crossOrigin===`anonymous`?t.credentials=`omit`:t.credentials=`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var e=`lightspeed-neo-exchange-v1`,t=[`critical`,`high`,`normal`,`low`],n=[`queued`,`active`,`review`,`blocked`,`complete`],r=[`icon`,`age_label`],i=e=>typeof e==`object`&&!!e&&!Array.isArray(e),a=(e,t,n)=>{if(typeof e!=`string`)return t;let r=e.replace(/\s+/g,` `).trim();return r?r.slice(0,n):t},o=(e,t,n)=>{let r=a(e,``,n);if(!r)throw TypeError(`queue record ${t} is required`);return r},s=(e,t,n)=>typeof e==`string`&&t.includes(e)?e:n,c=e=>i(e)?Object.fromEntries(r.flatMap(t=>{let n=a(e[t],``,48);return n?[[t,n]]:[]})):{},l=e=>{if(!i(e))throw TypeError(`queue record must be an object`);return{id:o(e.id,`id`,80),title:o(e.title,`title`,160),priority:s(e.priority,t,`normal`),status:s(e.status,n,`queued`),source:a(e.source,`Neo`,48),target:a(e.target,`Review`,48),created_utc:a(e.created_utc,``,32),extensions:c(e.extensions),notes:a(e.notes,``,240)}},u=t=>{if(!i(t))throw TypeError(`Neo exchange must be an object`);let n=Array.isArray(t.queue)?t.queue.map(l):[];return{schema_version:e,generated_at_utc:a(t.generated_at_utc,``,32),queue:n}},d=e=>({total:e.queue.length,critical:e.queue.filter(e=>e.priority===`critical`).length,active:e.queue.filter(e=>e.status!==`complete`).length,complete:e.queue.filter(e=>e.status===`complete`).length}),f=e=>e.replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#039;`})[e]??e),p=async e=>{try{return u(await e())}catch{return u({})}},m=e=>e.status===`blocked`?`blocked`:e.status===`complete`?`pass`:e.priority===`critical`||e.priority===`high`?`warn`:`ready`,h=e=>{let t=d(e),n=e.queue.length?e.queue.map(e=>`
            <li class="status-row ${m(e)}">
              <div>
                <strong>${f(e.title)}</strong>
                <span>${f(e.source)} to ${f(e.target)} · ${f(e.id)}</span>
                ${e.notes?`<small>${f(e.notes)}</small>`:``}
              </div>
              <em>${f(e.status)}</em>
            </li>
          `).join(``):`
      <li class="status-row ready">
        <div>
          <strong>Queue clear</strong>
          <span>No public-safe Neo exchange tasks are waiting.</span>
        </div>
        <em>ready</em>
      </li>
    `;return`
    <div class="exchange-summary" aria-label="Neo exchange summary">
      <span><strong>${t.total}</strong> total</span>
      <span aria-label="${t.active} active"><strong>${t.active}</strong> active</span>
      <span><strong>${t.critical}</strong> critical</span>
      <span><strong>${t.complete}</strong> complete</span>
    </div>
    <ul class="status-list exchange-list">${n}</ul>
  `},g=[{name:`Central Facility Boundary`,radiusM:2500,description:`All facilities and buildings remain inside this radius.`},{name:`Active Eco-Restoration`,radiusM:3500,description:`1 km active band for managed biome, native rehabilitation, and functional climate pockets.`},{name:`Passive Eco-Restoration`,radiusM:11e3,description:`Outer passive restoration reserve securing the full radial print.`}],_=[{id:`integration-hall`,name:`Integration Hall`,footprint:`40 m x 75 m, 22 m clear`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Starship-compatible roller doors both ends; single bridge crane spans the hall.`},{id:`chainhill`,name:`ChainHill Relay`,footprint:`~225-250 m relay length`,elevation:`flat raised concrete, approximately 3 m above water table`,releaseStatus:`bounded-assumption`,notes:`Incoming and outgoing tracks oppose each other with two anti-parallel internal lines.`},{id:`x-pads`,name:`X-Layout Pads`,footprint:`solid pads, no beveled building base`,elevation:`pad-specific hardstand`,releaseStatus:`canonical`,notes:`Flame/exhaust outlets orient away from central node and buildings.`},{id:`mission-control`,name:`Mission Control / ATC`,footprint:`pentagon base, level 1 at 80%, four-storey tower`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Foyer, cafeteria, meeting, offices, emergency access, elevator, and top operating floor.`},{id:`living-rd`,name:`R&D + Living Quarters`,footprint:`room-level workbook detail pending`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`known-unknown`,notes:`FIFO and FIFO+family support with ground community and rooftop lifestyle zones.`}],v=[`site_zones`,`facilities`,`rooms_spaces`,`roads_tracks`,`pads_exhaust`,`eco_restoration`,`standards_evidence`,`viewer_toggles`,`known_unknowns`],y=document.getElementById(`app`);if(!y)throw Error(`LightSpeed Go mount node #app not found.`);var b=[[`GitHub`,`Authenticated`,`Connected account verified; private identity held in gated handoff`,`pass`],[`Google Drive`,`Authenticated`,`Connected account verified; writeback remains approval-gated`,`pass`],[`Gmail`,`Authenticated`,`Connected account verified; outbound send remains approval-gated`,`pass`]],x=[[`/ls-go`,`HTTP 200`,`Public route is live`,`pass`],[`/ls-go/status`,`HTTP 200`,`Status route is live`,`pass`],[`/ls-go/handoff`,`HTTP 200`,`Handoff route is live`,`pass`],[`/ls-go/review`,`HTTP 200`,`Review route is live`,`pass`],[`/ls-go/agents`,`HTTP 404`,`Agent route is not published yet; keep it out of primary navigation until live`,`warn`]],S=[[`Achilles Core`,`Governance/source-of-truth`,`:00 / :48`,`ready`],[`Co-Runner`,`Drive review and workbook reconciliation`,`:12`,`ready`],[`Desktop Codex`,`Repo build, branch, app evidence`,`:24`,`ready`],[`Terminal Codex`,`Shell validation and command receipts`,`:24`,`ready`],[`Claude/UI`,`Console and agent-lane artifact pass`,`:36`,`ready`],[`Local Runners`,`One-session De Sporte/Ollama gate`,`:48`,`warn`]],C=[[`LightSpeed Go`,`Vite 8 build green`,`C-drive staging is the build lane while D: remains space constrained`,`pass`],[`De Sporte`,`Desktop/runtime world shell`,`Packaged Cognigrex shortcut uses explicit data-root and stays resident`,`ready`],[`Cognigrex`,`Operator shell + Smith queue proof`,`Desktop launch lane is active; capture UI proof after public route update`,`warn`]],w=[[`Short-term`,`RAM/current run only`,`Keep run deltas compact; do not accumulate raw logs in prompt memory`],[`Long-term`,`Drive/repo/local review records`,`Persist evidence paths, hashes, route statuses, and blockers only`],[`Safety`,`No secret persistence`,`Never store credential values, OAuth secrets, wallet/token/payment/custody/IPFS data`]],T=e=>e.map(([e,t,n,r])=>`
        <li class="status-row ${r}">
          <div>
            <strong>${e}</strong>
            <span>${n}</span>
          </div>
          <em>${t}</em>
        </li>
      `).join(``),E=g.map(e=>`
      <div class="zone-chip">
        <strong>${(e.radiusM/1e3).toFixed(e.radiusM%1e3==0?0:1)} km</strong>
        <span>${e.name}</span>
        <em>${e.description}</em>
      </div>
    `).join(``),D=_.map(e=>`
      <li class="facility-row ${e.releaseStatus}">
        <div>
          <strong>${e.name}</strong>
          <span>${e.footprint}</span>
          <small>${e.elevation}</small>
          <small>${e.notes}</small>
        </div>
        <em>${e.releaseStatus.replace(`-`,` `)}</em>
      </li>
    `).join(``),O=v.map(e=>`<code>${e}</code>`).join(``);y.innerHTML=`
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
        <span class="badge warn">Agent route pending</span>
      </div>
    </section>

    <section class="grid">
      <article class="panel">
        <div class="panel-head">
          <p class="kicker">Tool State</p>
          <h2>Connectors</h2>
        </div>
        <ul class="status-list">${T(b)}</ul>
      </article>

      <article class="panel">
        <div class="panel-head">
          <p class="kicker">Public Web</p>
          <h2>Route Gates</h2>
        </div>
        <ul class="status-list">${T(x)}</ul>
      </article>

      <article class="panel">
        <div class="panel-head">
          <p class="kicker">Applications</p>
          <h2>Build / Run State</h2>
        </div>
        <ul class="status-list">${T(C)}</ul>
      </article>

      <article class="panel">
        <div class="panel-head">
          <p class="kicker">Agent Rotation</p>
          <h2>Oversight Lanes</h2>
        </div>
        <ul class="status-list">${T(S)}</ul>
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
            <div class="zone-grid">${E}</div>
            <ul class="facility-list">${D}</ul>
            <p class="workbook-link">Workbook-backed embed contract: ${O}</p>
          </div>
        </div>
      </article>

      <article class="panel wide">
        <div class="panel-head">
          <p class="kicker">Compact Memory</p>
          <h2>RAM + Persistence Policy</h2>
        </div>
        <div class="memory-grid">
          ${w.map(([e,t,n])=>`
                <div>
                  <strong>${e}</strong>
                  <em>${t}</em>
                  <span>${n}</span>
                </div>
              `).join(``)}
        </div>
      </article>

      <article class="panel wide">
        <div class="panel-head exchange-head">
          <div>
            <p class="kicker">Neo Exchange</p>
            <h2>Public-Safe Queue Projection</h2>
          </div>
          <span class="badge ready">Execution remains Desktop-only</span>
        </div>
        <div id="neo-exchange" aria-live="polite">
          <p class="exchange-loading">Reading the bounded exchange projection...</p>
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
`;var k=document.getElementById(`neo-exchange`);if(k){let e=new URL(`./data/neo_exchange.json`,document.baseURI).toString();p(async()=>{let t=await fetch(e,{cache:`no-store`});if(!t.ok)throw Error(`Neo exchange returned HTTP ${t.status}`);return t.json()}).then(e=>{k.innerHTML=h(e)})}