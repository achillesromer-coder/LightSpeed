(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),e.crossOrigin===`use-credentials`?t.credentials=`include`:e.crossOrigin===`anonymous`?t.credentials=`omit`:t.credentials=`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var e=`lightspeed-go-command-v1`,t=`http://127.0.0.1:8765`,n=[`Achilles`,`Neo`,`Architect`,`TheConstruct`,`Morpheus`,`Oracle`,`Smith`,`Merovingian`,`Trinity`],r=(e,t)=>e.replace(/\s+/g,` `).trim().slice(0,t),i=e=>{let t=e.toLowerCase();return/\b(ui|site|web|design|visual|layout|canva|accessibility)\b/.test(t)?`Trinity`:/\b(git|github|code|build|commit|branch|deploy|schema|api|runtime)\b/.test(t)?`Smith`:/\b(source|evidence|research|data|document|drive|sheet|workbook|citation)\b/.test(t)?`Oracle`:/\b(proof|claim|verify|conflict|confidence|audit)\b/.test(t)?`Morpheus`:/\b(simulate|simulation|model|gmat|trajectory|twin|physics)\b/.test(t)?`TheConstruct`:/\b(plan|mission|architecture|dependency|roadmap|system|project)\b/.test(t)?`Architect`:/\b(health|status|diagnostic|failure|error|monitor|storage|cleanup|archive)\b/.test(t)?`Merovingian`:/\b(coordinate|queue|handoff|agent|task|execute|run)\b/.test(t)?`Neo`:`Achilles`},a=t=>{let n=r(t.instruction,4e3);if(!n)throw TypeError(`instruction is required`);let a=new Date().toISOString(),o=Math.random().toString(36).slice(2,8).toUpperCase(),s=t.targetFloor??i(n);return{schema_version:e,command_id:`LSGO-${a.replace(/\D/g,``).slice(0,14)}-${o}`,created_utc:a,source:`LS GO`,title:r(t.title||n,160),instruction:n,target_floor:s,oversight_floor:`Achilles`,priority:t.priority??`normal`,execution_mode:t.executionMode??`review`,proof_required:!0,public_safe:!0}},o=async(e,t,n=3500)=>{let r=new AbortController,i=window.setTimeout(()=>r.abort(),n);try{let n=await fetch(e,{...t,signal:r.signal,cache:`no-store`});if(!n.ok){let e=`Desktop returned HTTP ${n.status}`;try{let t=await n.json();t.detail&&(e=t.detail)}catch{}throw Error(e)}return await n.json()}finally{window.clearTimeout(i)}},s=(e=t)=>o(`${e}/api/v1/status`,{method:`GET`},1e4),c=(e,n=t)=>o(`${n}/api/v1/ls-go/commands`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify(e)},7e3),l=async(e=t)=>{let n=await o(`${e}/api/v1/tasks?limit=12`,{method:`GET`});return Array.isArray(n.tasks)?n.tasks:[]},u=async(e=t)=>{let n=await o(`${e}/api/v1/projects`,{method:`GET`},15e3);return{projects:Array.isArray(n.projects)?n.projects:[],summary:n.summary||{},duplicateNames:Array.isArray(n.duplicate_names)?n.duplicate_names:[],cleanupSummary:n.cleanup_summary||{}}},d=async(e=t,n=50)=>{let r=await o(`${e}/api/v1/reviews?limit=${Math.max(1,Math.min(n,200))}`,{method:`GET`},1e4);return Array.isArray(r.reviews)?r.reviews:[]},f=async(e,n,i=``,a=t)=>o(`${a}/api/v1/reviews/${encodeURIComponent(e)}/decision`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({decision:n,note:r(i,1e3)})},7e3),p=async(e=t)=>{let n=await o(`${e}/api/v1/representation-graphs`,{method:`GET`},15e3);return Array.isArray(n.graphs)?n.graphs:[]},m=async(e,n,i,a=[],s=``,c=t)=>o(`${c}/api/v1/representation-reviews/${encodeURIComponent(e)}/decision`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({decision:n,actor:`Nathaniel`,scope:i,edge_ids:a.slice(0,100),note:r(s,1e3)})},1e4),h=`lightspeed-go-pending-commands-v1`,g=()=>{try{let e=JSON.parse(localStorage.getItem(h)||`[]`);return Array.isArray(e)?e:[]}catch{return[]}},_=e=>{let t=[e,...g().filter(t=>t.command_id!==e.command_id)].slice(0,30);return localStorage.setItem(h,JSON.stringify(t)),t},v=e=>{let t=g().filter(t=>t.command_id!==e);return localStorage.setItem(h,JSON.stringify(t)),t},ee=e=>{let t=new Blob([JSON.stringify(e,null,2)],{type:`application/json`}),n=URL.createObjectURL(t),r=document.createElement(`a`);r.href=n,r.download=`${e.command_id}.json`,r.click(),URL.revokeObjectURL(n)},te=`lightspeed-neo-exchange-v1`,ne=[`critical`,`high`,`normal`,`low`],re=[`queued`,`active`,`review`,`blocked`,`complete`],y=[`icon`,`age_label`],b=e=>typeof e==`object`&&!!e&&!Array.isArray(e),x=(e,t,n)=>{if(typeof e!=`string`)return t;let r=e.replace(/\s+/g,` `).trim();return r?r.slice(0,n):t},S=(e,t,n)=>{let r=x(e,``,n);if(!r)throw TypeError(`queue record ${t} is required`);return r},C=(e,t,n)=>typeof e==`string`&&t.includes(e)?e:n,ie=e=>b(e)?Object.fromEntries(y.flatMap(t=>{let n=x(e[t],``,48);return n?[[t,n]]:[]})):{},ae=e=>{if(!b(e))throw TypeError(`queue record must be an object`);return{id:S(e.id,`id`,80),title:S(e.title,`title`,160),priority:C(e.priority,ne,`normal`),status:C(e.status,re,`queued`),source:x(e.source,`GO Gate`,48),target:x(e.target,`Neo`,48),created_utc:x(e.created_utc,``,32),extensions:ie(e.extensions),notes:x(e.notes,``,240)}},w=e=>{if(!b(e))throw TypeError(`Neo exchange must be an object`);let t=Array.isArray(e.queue)?e.queue.map(ae):[];return{schema_version:te,generated_at_utc:x(e.generated_at_utc,``,32),queue:t}},oe=e=>({total:e.queue.length,critical:e.queue.filter(e=>e.priority===`critical`).length,active:e.queue.filter(e=>e.status!==`complete`).length,complete:e.queue.filter(e=>e.status===`complete`).length}),T=e=>e.replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#039;`})[e]??e),se=async e=>{try{return w(await e())}catch{return w({})}},ce=e=>e.status===`blocked`?`blocked`:e.status===`complete`?`pass`:e.priority===`critical`||e.priority===`high`?`warn`:`ready`,le=e=>{let t=oe(e),n=e.queue.length?e.queue.map(e=>`
            <li class="status-row ${ce(e)}">
              <div>
                <strong>${T(e.title)}</strong>
                <span>${T(e.source)} to ${T(e.target)} · ${T(e.id)}</span>
                ${e.notes?`<small>${T(e.notes)}</small>`:``}
              </div>
              <em>${T(e.status)}</em>
            </li>
          `).join(``):`
      <li class="status-row ready">
        <div>
          <strong>Routed queue clear</strong>
          <span>No GO-accepted Neo actions are waiting.</span>
        </div>
        <em>ready</em>
      </li>
    `;return`
    <div class="exchange-summary" aria-label="GO-gated Neo routing summary">
      <span><strong>${t.total}</strong> total</span>
      <span aria-label="${t.active} active"><strong>${t.active}</strong> active</span>
      <span><strong>${t.critical}</strong> critical</span>
      <span><strong>${t.complete}</strong> complete</span>
    </div>
    <ul class="status-list exchange-list">${n}</ul>
  `},E=e=>String(e??``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),D=e=>e?`${e.slice(0,12)}…${e.slice(-8)}`:`not available`,ue=e=>e.path_exposed===!1?String(e.label||`private local evidence`):[e.repository,e.commit_sha?`commit ${String(e.commit_sha).slice(0,12)}`:null,e.path,e.drive_file_id?`Drive ${e.drive_file_id}`:null,e.sheet_name,e.stable_key||e.content_key,e.missing_state].filter(Boolean).map(E).join(` · `)||E(e.locator_type||`logical`),de=e=>E(JSON.stringify(e,null,2)),fe=e=>{let t=e.representations.filter(e=>e.state===`active`).length,n=e.missing.length;return!t&&n?`unable to determine`:n>t?`smaller bowl`:t>n?`larger bowl`:`unchanged bowl`},pe=e=>{let t=e.review,n=t?.review_stage||`identity`,r=e.edges.map(e=>e.edge_id).join(`|`),i=t?`
    <div class="graph-actions" data-review-stage="${E(n)}">
      <strong>${n===`identity`?`Review identity first`:`Review ${e.edges.length} bounded edges`}</strong>
      <div class="task-actions">
        <button data-representation-review="${E(t.review_id)}" data-scope="${n}" data-edge-ids="${E(r)}" data-decision="approve">Approve</button>
        <button data-representation-review="${E(t.review_id)}" data-scope="${n}" data-edge-ids="${E(r)}" data-decision="provisional_approve">Provisional</button>
        <button data-representation-review="${E(t.review_id)}" data-scope="${n}" data-edge-ids="${E(r)}" data-decision="hold">Hold</button>
        <button data-representation-review="${E(t.review_id)}" data-scope="${n}" data-edge-ids="${E(r)}" data-decision="request_evidence">Request evidence</button>
        <button data-representation-review="${E(t.review_id)}" data-scope="${n}" data-edge-ids="${E(r)}" data-decision="reject">Reject</button>
        <button data-representation-review="${E(t.review_id)}" data-scope="${n}" data-edge-ids="${E(r)}" data-decision="supersede">Supersede</button>
      </div>
      <small>${E(t.state)} · graph ${D(t.graph_sha256)}</small>
    </div>`:`<p class="muted">Review packet has not been staged.</p>`,a=e.representations.map(e=>`
    <tr>
      <td><strong>${E(e.representation_type)}</strong><small>${E(e.representation_id)}</small></td>
      <td>${ue(e.locator)}</td>
      <td>${E(e.source_authority)}</td>
      <td>${D(e.content_sha256)}</td>
      <td>${E(e.confidence_class)} (${Math.round(e.confidence_numeric*100)}%)</td>
      <td><span class="state-chip" data-state="${E(e.state)}">${E(e.state)}</span></td>
      <td>${E(e.claim_boundary)}</td>
    </tr>`).join(``),o=e.edges.map(e=>`
    <tr>
      <td>${E(e.from_representation_id)}</td>
      <td><strong>${E(e.relation)}</strong></td>
      <td>${E(e.to_representation_id)}</td>
      <td>${E(e.evidence_bundle_id||`not required`)}</td>
      <td>${E(e.review_state)}</td>
      <td>${E(e.claim_boundary)}</td>
    </tr>`).join(``),s=e.missing.length?e.missing.map(e=>`
      <article class="missing-card">
        <strong>${E(e.type)} · ${E(e.missing_state)}</strong>
        <span><b>Why:</b> ${E(e.reason)}</span>
        <span><b>Next:</b> ${E(e.next_evidence_action)}</span>
        <small>Last search: ${E(e.last_search||`not recorded`)} · Floor: ${E(e.assigned_floor)} · Effect: ${E(e.dependency_effect)}</small>
      </article>`).join(``):`<p class="muted">No required representation is currently missing.</p>`,c=e.conflicts.length?e.conflicts.map(e=>`<article class="missing-card conflict"><strong>${E(e.edge_id)}</strong><span>${E(e.claim_boundary)}</span></article>`).join(``):`<p class="muted">No representation conflict is recorded.</p>`,l=e.horizons.length?e.horizons.map(e=>`
      <article class="horizon-card">
        <div><strong>${E(e.name)}</strong><span>${E(e.state)} · ${E(e.horizon_type)}</span></div>
        <p>${E(e.objective)}</p>
        <details><summary>Assumptions and constraints</summary><pre>${de({assumptions:e.assumptions,constraints:e.constraints})}</pre></details>
        <small>Input ${D(e.input_set_sha256)}</small>
      </article>`).join(``):`<p class="muted">No horizon is assigned.</p>`,u=e.representations.find(e=>e.representation_type===`recommendation`)?.locator.next_highest_value_question;return`
    <article class="panel graph-panel" data-object-id="${E(e.object.object_id)}">
      <div class="panel-head">
        <div>
          <p class="eyebrow">${E(e.object.object_type)}</p>
          <h2>${E(e.object.display_name)}</h2>
          <p>${E(e.object.description)}</p>
        </div>
        <span class="badge">${E(e.canonical_state)}</span>
      </div>
      <div class="graph-summary">
        <div><span>Object ID</span><strong>${E(e.object.object_id)}</strong></div>
        <div><span>Authority</span><strong>${E(e.object.authority)}</strong></div>
        <div><span>Identity</span><strong>${E(e.object.identity_confidence_class)} · ${Math.round(e.object.identity_confidence_numeric*100)}%</strong></div>
        <div><span>Current horizon</span><strong>${E(e.horizons[0]?.name||`not assigned`)}</strong></div>
        <div><span>Judgment</span><strong>${fe(e)}</strong></div>
      </div>
      <details open><summary>Identifiers (${e.identifiers.length})</summary><div class="identifier-list">${e.identifiers.map(e=>`<span><strong>${E(e.namespace)}</strong>${E(e.identifier_value)} · ${E(e.authority)}</span>`).join(``)}</div></details>
      <details open><summary>Representations (${e.representations.length})</summary><div class="table-scroll"><table class="graph-table"><thead><tr><th>Type</th><th>Locator</th><th>Authority</th><th>Hash/revision</th><th>Confidence</th><th>State</th><th>Claim boundary</th></tr></thead><tbody>${a}</tbody></table></div></details>
      <details open><summary>Edges (${e.edges.length})</summary><div class="table-scroll"><table class="graph-table"><thead><tr><th>Source</th><th>Relation</th><th>Destination</th><th>Evidence</th><th>Review</th><th>Boundary</th></tr></thead><tbody>${o}</tbody></table></div></details>
      <div class="graph-grid">
        <section><h3>Missing</h3>${s}</section>
        <section><h3>Conflicts</h3>${c}</section>
      </div>
      <section><h3>Horizon</h3>${l}</section>
      <div class="next-question"><strong>Next highest-value question</strong><span>${E(u||`Owner review determines the next bounded question.`)}</span></div>
      ${i}
    </article>`},O=e=>e.length?e.map(pe).join(``):`<article class="panel"><p class="muted">The feature-gated representation edge is disabled or unavailable.</p></article>`,k=[{name:`Central Facility Boundary`,radiusM:2500,description:`All facilities and buildings remain inside this radius.`},{name:`Active Eco-Restoration`,radiusM:3500,description:`1 km active band for managed biome, native rehabilitation, and functional climate pockets.`},{name:`Passive Eco-Restoration`,radiusM:11e3,description:`Outer passive restoration reserve securing the full radial print.`}],A=[{id:`integration-hall`,name:`Integration Hall`,footprint:`40 m x 75 m, 22 m clear`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Starship-compatible roller doors both ends; single bridge crane spans the hall.`},{id:`chainhill`,name:`ChainHill Relay`,footprint:`~225-250 m relay length`,elevation:`flat raised concrete, approximately 3 m above water table`,releaseStatus:`bounded-assumption`,notes:`Incoming and outgoing tracks oppose each other with two anti-parallel internal lines.`},{id:`x-pads`,name:`X-Layout Pads`,footprint:`solid pads, no beveled building base`,elevation:`pad-specific hardstand`,releaseStatus:`canonical`,notes:`Flame/exhaust outlets orient away from central node and buildings.`},{id:`mission-control`,name:`Mission Control / ATC`,footprint:`pentagon base, level 1 at 80%, four-storey tower`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Foyer, cafeteria, meeting, offices, emergency access, elevator, and top operating floor.`},{id:`living-rd`,name:`R&D + Living Quarters`,footprint:`room-level workbook detail pending`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`known-unknown`,notes:`FIFO and FIFO+family support with ground community and rooftop lifestyle zones.`}],j=[`site_zones`,`facilities`,`rooms_spaces`,`roads_tracks`,`pads_exhaust`,`eco_restoration`,`standards_evidence`,`viewer_toggles`,`known_unknowns`],M=document.getElementById(`app`);if(!M)throw Error(`LightSpeed Go mount node #app not found.`);M.innerHTML=`
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
              <label class="field"><span>Route</span><select id="target-floor">${n.map(e=>`<option value="${e}">${e}</option>`).join(``)}</select></label>
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
        <article class="metric"><span>Desktop API</span><strong id="desktop-state">Checking</strong><small>${t}</small></article>
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

    <section class="view" id="view-objects">
      <article class="panel definition">
        <div><p class="eyebrow">Canonical representation edge</p><h2>Identity, evidence, horizon, review</h2></div>
        <p>Three bounded local candidates prove the complete intake route. Drive becomes canonical only after owner decision, promotion, and exact readback.</p>
      </article>
      <div id="representation-graphs" class="graph-stack">
        <article class="panel"><p class="muted">Reading feature-gated object graphs from Desktopâ€¦</p></article>
      </div>
    </section>

    <section class="view" id="view-system">
      <article class="panel definition">
        <div><p class="eyebrow">cognigrex</p><h2>Common goal, distinct agents</h2></div>
        <p>The system coordinates GO, Desktop, Git, Drive, agents and human oversight while retaining separate authority, resource limits and reviewable receipts.</p>
      </article>
      <div class="agent-grid">${[[`Achilles`,`governance, proof and release`],[`Neo`,`task routing and handoff`],[`Architect`,`projects, plans and dependencies`],[`TheConstruct`,`simulation and digital twins`],[`Morpheus`,`claim proof and conflict resolution`],[`Oracle`,`sources, evidence and knowns`],[`Smith`,`Git, code, schemas and execution`],[`Merovingian`,`health, storage, projects and recovery`],[`Trinity`,`interface and visual implementation`]].map(([e,t])=>`<article class="agent"><strong>${e}</strong><span>${t}</span></article>`).join(``)}</div>
      <div class="two-column">
        <article class="panel"><p class="eyebrow">Execution path</p><h2>One project, one receipt chain</h2><div class="flow"><span>LS GO</span><i>→</i><span>Achilles</span><i>→</i><span>Neo + floor</span><i>→</i><span>Desktop project</span><i>→</i><span>Drive receipt</span><i>→</i><span>GO decision</span></div></article>
        <article class="panel"><p class="eyebrow">Existing twin context</p><h2>Spaceport contract retained</h2><p class="muted">${k.length} zones · ${A.length} facility records · ${j.length} workbook tabs. The twin remains bounded context, not the command-centre homepage.</p></article>
      </div>
    </section>

    <section class="view" id="view-sources">
      <div class="source-grid">${[[`LightSpeed Git`,`https://github.com/achillesromer-coder/LightSpeed`,`Versioned implementation and receipts`],[`LS GO Queue`,`https://docs.google.com/spreadsheets/d/1f5i4V3FshYHkztv3_HAg0ZofUl0sdcJZcwrlesUlCfM/edit`,`Phone tasks, approvals, commands, results and sync health`],[`Portfolio Handoff`,`https://docs.google.com/document/d/1tsDkb79UVX_SqS2-oBgc5DHb89QIlH3DcmKMN77hdOo/edit`,`Cross-chat portfolio continuity`],[`Römer Industries`,`https://romer.industries`,`Reviewed public portfolio surface`]].map(([e,t,n])=>`<a class="source-card" href="${t}" target="_blank" rel="noreferrer"><strong>${e}</strong><span>${n}</span><em>Open ↗</em></a>`).join(``)}</div>
      <article class="panel"><p class="eyebrow">Authority order</p><h2>Where each truth lives</h2><div class="authority-grid"><div><strong>Drive</strong><span>evidence, workbooks and review receipts</span></div><div><strong>Git</strong><span>code, schemas, tests and implementation receipts</span></div><div><strong>Desktop</strong><span>projects, local execution, state and jobs</span></div><div><strong>LS GO</strong><span>owner commands, review and bounded decisions</span></div></div></article>
    </section>
  </main>
`;var N=e=>{let t=document.getElementById(e);if(!t)throw Error(`Missing #${e}`);return t},P=N(`instruction`),F=N(`target-floor`),I=N(`priority`),L=N(`execution-mode`),R=N(`route-preview`),z=N(`command-result`),B=null,V=[],H=[],U=()=>{let e=i(P.value||`governance`);F.value=e,R.innerHTML=`<strong>Achilles route:</strong> ${e} is primary. Neo coordinates and proof returns to this gate.`};P.addEventListener(`input`,U),U();var W=()=>a({instruction:P.value,targetFloor:F.value,priority:I.value,executionMode:L.value}),G=(e,t)=>{z.dataset.tone=e,z.textContent=t},K=()=>{let e=g();N(`pending-count`).textContent=String(e.length);let t=N(`pending-commands`);if(!e.length){t.innerHTML=`<p class="muted">No locally saved commands.</p>`;return}t.innerHTML=e.map(e=>`<article class="task-card"><div><strong>${T(e.title)}</strong><span>${T(e.target_floor)} · ${T(e.priority)} · ${T(e.execution_mode)}</span><small>${T(e.command_id)}</small></div><div class="task-actions"><button data-send="${T(e.command_id)}">Send</button><button data-download="${T(e.command_id)}">Download</button></div></article>`).join(``),t.querySelectorAll(`[data-send]`).forEach(t=>t.addEventListener(`click`,async()=>{let n=e.find(e=>e.command_id===t.dataset.send);if(n)try{let e=await c(n);v(n.command_id),K(),G(`good`,`Desktop accepted ${e.command_id||n.command_id}. Task ${e.task_id??`created`}.`),await X()}catch(e){G(`bad`,e instanceof Error?e.message:`Desktop command failed.`)}})),t.querySelectorAll(`[data-download]`).forEach(t=>t.addEventListener(`click`,()=>{let n=e.find(e=>e.command_id===t.dataset.download);n&&ee(n)}))},me=e=>{let t=Number(e||0);return t<1024?`${t} B`:t<1024**2?`${(t/1024).toFixed(1)} KB`:t<1024**3?`${(t/1024**2).toFixed(1)} MB`:`${(t/1024**3).toFixed(1)} GB`},q=e=>{let t=N(`desktop-projects`);if(N(`project-count`).textContent=String(e.length),!e.length){t.innerHTML=`<p class="muted">No project folders were found in the configured roots.</p>`;return}t.innerHTML=e.slice(0,30).map(e=>`<article class="task-card"><div><strong>${T(e.name)}</strong><span>${T(e.condition||`unknown`)} · ${T(e.authority||`reference`)} · ${e.file_count||0} files</span><small>${me(e.size_bytes)}${e.scan_truncated?` · bounded scan`:``}</small></div></article>`).join(``)},J=e=>{V=e;let t=N(`desktop-reviews`);if(!e.length){t.innerHTML=`<p class="muted">No project receipts are awaiting review.</p>`;return}t.innerHTML=e.slice(0,30).map(e=>{let t=e.state||`pending_review`,n=t===`pending_review`?`<div class="task-actions"><button data-review="${T(e.review_id)}" data-decision="approve">Approve</button><button data-review="${T(e.review_id)}" data-decision="hold">Hold</button><button data-review="${T(e.review_id)}" data-decision="reject">Reject</button></div>`:``;return`<article class="task-card"><div><strong>${T(e.title||`Project receipt`)}</strong><span>${T(t)} · ${T(e.event_type||`receipt`)}</span><small>${T(e.summary||e.review_id)}</small></div>${n}</article>`}).join(``),t.querySelectorAll(`[data-review]`).forEach(e=>e.addEventListener(`click`,async()=>{let t=e.dataset.review||``,n=e.dataset.decision,r=V.find(e=>e.review_id===t);if(!r||!t)return;let i=window.prompt(`${n.toUpperCase()}: ${r.title||t}\nOptional decision note:`,``)??``;try{await f(t,n,i),G(`good`,`${t} marked ${n}. Drive decision receipt written by Desktop.`),await X()}catch(e){G(`bad`,e instanceof Error?e.message:`Review decision failed.`)}}))},Y=e=>{H=e;let t=N(`representation-graphs`);t.innerHTML=O(e),t.querySelectorAll(`[data-representation-review]`).forEach(e=>{e.addEventListener(`click`,async()=>{let t=e.dataset.representationReview||``,n=e.dataset.decision,r=e.dataset.scope||`identity`,i=r===`edges`?(e.dataset.edgeIds||``).split(`|`).filter(Boolean).slice(0,100):[],a=H.find(e=>e.review?.review_id===t);if(!t||!a)return;let o=window.prompt(`${n.replace(/_/g,` `).toUpperCase()}: ${a.object.display_name}\n${r===`identity`?`Identity is reviewed before edges.`:`${i.length} bounded edges selected.`}\nOptional decision note:`,``)??``;try{await m(t,n,r,i,o),G(`good`,`${t} recorded ${n}; local staging remains noncanonical until Drive readback.`),await X()}catch(e){G(`bad`,e instanceof Error?e.message:`Representation review decision failed.`)}})})};N(`command-form`).addEventListener(`submit`,async e=>{e.preventDefault();try{B=W(),G(`warn`,`Sending ${B.command_id} to Desktop…`);let e=await c(B);v(B.command_id),K(),G(`good`,`Accepted by Desktop. Task ${e.task_id??`created`}; ${e.state||`queued for governed processing`}.`),await X()}catch(e){B&&_(B),K(),G(`bad`,`${e instanceof Error?e.message:`Desktop unavailable`} The command envelope was saved locally.`)}}),N(`save-command`).addEventListener(`click`,()=>{try{B=W(),_(B),K(),G(`good`,`${B.command_id} saved locally.`)}catch(e){G(`bad`,e instanceof Error?e.message:`Command could not be saved.`)}}),N(`copy-command`).addEventListener(`click`,async()=>{try{B=W(),await navigator.clipboard.writeText(JSON.stringify(B,null,2)),G(`good`,`${B.command_id} copied as JSON.`)}catch(e){G(`bad`,e instanceof Error?e.message:`Command could not be copied.`)}});var X=async()=>{let e=N(`desktop-pill`),t=N(`desktop-state`),n=N(`merovingian-state`),r=N(`desktop-pill-text`),i=N(`desktop-tasks`);e.dataset.state=`checking`,r.textContent=`checking local runtime`,t.textContent=`Checking`,n.textContent=`Checking`;try{let a=await s();e.dataset.state=a.ok?`online`:`degraded`,r.textContent=a.ok?`local runtime connected`:`runtime connected; health needs review`,t.textContent=`Online`,n.textContent=a.merovingian?.status===`pass`?`Healthy`:`Degraded`;try{let e=await l();i.innerHTML=e.length?e.map(e=>`<article class="task-card"><div><strong>${T(String(e.title||`Untitled task`))}</strong><span>${T(String(e.status||`unknown`))} · ${T(String(e.priority||`normal`))}</span><small>Task ${T(String(e.id||``))}</small></div></article>`).join(``):`<p class="muted">Desktop queue is clear.</p>`}catch{i.innerHTML=`<p class="muted">Desktop is online, but task listing is unavailable.</p>`}try{q((await u()).projects)}catch{q([])}try{J(await d())}catch{J([])}try{Y(await p())}catch{Y([])}}catch{e.dataset.state=`offline`,r.textContent=`start LightSpeed Desktop and the local bridge`,t.textContent=`Offline`,n.textContent=`Offline`,N(`project-count`).textContent=`0`,i.innerHTML=`<p class="muted">Desktop is offline. Commands can still be saved, copied or downloaded.</p>`,N(`desktop-projects`).innerHTML=`<p class="muted">Project registry unavailable while Desktop is offline.</p>`,N(`desktop-reviews`).innerHTML=`<p class="muted">Review queue unavailable while Desktop is offline.</p>`,Y([])}};N(`refresh-desktop`).addEventListener(`click`,()=>void X()),K(),X();var he=N(`neo-exchange`),ge=new URL(`./data/neo_exchange.json`,document.baseURI).toString();se(async()=>{let e=await fetch(ge,{cache:`no-store`});if(!e.ok)throw Error(`Neo exchange returned HTTP ${e.status}`);return e.json()}).then(e=>{he.innerHTML=le(e)}),document.querySelectorAll(`.tab`).forEach(e=>e.addEventListener(`click`,()=>{document.querySelectorAll(`.tab`).forEach(e=>e.classList.remove(`active`)),document.querySelectorAll(`.view`).forEach(e=>e.classList.remove(`active`)),e.classList.add(`active`),N(`view-${e.dataset.view}`).classList.add(`active`)}));var _e=new URL(`./data/site_integration.json`,document.baseURI).toString(),ve=async()=>{try{let e=await fetch(_e,{cache:`no-store`});return e.ok?await e.json():null}catch{return null}},Z=()=>{if(document.getElementById(`lsgo-sites-side-edit-styles`))return;let e=document.createElement(`style`);e.id=`lsgo-sites-side-edit-styles`,e.textContent=`
    .site-context-strip { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
    .site-context-strip span { border:1px solid var(--line); border-radius:999px; padding:7px 10px; color:var(--muted); font-size:12px; background:rgba(255,255,255,.025); }
    .site-context-strip strong { color:var(--text); }
    .site-parity-card { border:1px solid var(--line); border-radius:14px; padding:14px; background:rgba(255,255,255,.025); display:grid; gap:8px; }
    .site-parity-card p { margin:0; color:var(--muted); line-height:1.5; }
    .site-parity-card .site-chain { display:flex; flex-wrap:wrap; gap:7px; align-items:center; }
    .site-parity-card .site-chain span { border:1px solid var(--line); border-radius:999px; padding:6px 9px; font-size:12px; }
    .site-parity-card .site-chain i { color:var(--teal); font-style:normal; }
  `,document.head.appendChild(e)},ye=async()=>{let e=document.querySelector(`.topbar > div:first-child`),t=document.querySelector(`#view-sources`);if(!e||!t)return!1;Z();let n=await ve(),r=n?.authority_chain??[`Nathaniel Bouwer`,`Achilles / GO gate`,`agent floor`,`LightSpeed Desktop`,`Git and Drive receipts`];if(!document.getElementById(`site-context-strip`)){let t=document.createElement(`div`);t.id=`site-context-strip`,t.className=`site-context-strip`,t.innerHTML=`
      <span><strong>Owner:</strong> Nathaniel Bouwer</span>
      <span><strong>Mode:</strong> existing Site side edit</span>
      <span><strong>Source:</strong> Git + Drive aligned</span>
    `,e.appendChild(t)}if(!document.getElementById(`site-parity-card`)){let e=document.createElement(`article`);e.id=`site-parity-card`,e.className=`panel site-parity-card`,e.innerHTML=`
      <p class="eyebrow">Current Site integration</p>
      <h2>One surface, additive side edit</h2>
      <p>The existing LightSpeed GO Site remains canonical. Git carries implementation, Drive carries evidence and control records, and Sites publishes only the reviewed delta.</p>
      <div class="site-chain">
        ${r.map((e,t)=>`${t?`<i>→</i>`:``}<span>${e}</span>`).join(``)}
      </div>
      <p><strong>Publish state:</strong> ${n?.publish_state??`review-required`}. No replacement Site is created.</p>
    `,t.prepend(e)}return!0},Q=0,$=()=>{ye().then(e=>{e||Q>=40||(Q+=1,window.requestAnimationFrame($))})};$();