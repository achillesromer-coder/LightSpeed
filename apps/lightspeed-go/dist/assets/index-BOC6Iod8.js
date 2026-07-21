(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),e.crossOrigin===`use-credentials`?t.credentials=`include`:e.crossOrigin===`anonymous`?t.credentials=`omit`:t.credentials=`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var e=`lightspeed-go-command-v1`,t=`http://127.0.0.1:8765`,n=[`Achilles`,`Neo`,`Architect`,`TheConstruct`,`Morpheus`,`Oracle`,`Smith`,`Merovingian`,`Trinity`],r=(e,t)=>e.replace(/\s+/g,` `).trim().slice(0,t),i=e=>{let t=e.toLowerCase();return/\b(ui|site|web|design|visual|layout|canva|accessibility)\b/.test(t)?`Trinity`:/\b(git|github|code|build|commit|branch|deploy|schema|api|runtime)\b/.test(t)?`Smith`:/\b(source|evidence|research|data|document|drive|sheet|workbook|citation)\b/.test(t)?`Oracle`:/\b(proof|claim|verify|conflict|confidence|audit)\b/.test(t)?`Morpheus`:/\b(simulate|simulation|model|gmat|trajectory|twin|physics)\b/.test(t)?`TheConstruct`:/\b(plan|mission|architecture|dependency|roadmap|system|project)\b/.test(t)?`Architect`:/\b(health|status|diagnostic|failure|error|monitor|storage|cleanup|archive)\b/.test(t)?`Merovingian`:/\b(coordinate|queue|handoff|agent|task|execute|run)\b/.test(t)?`Neo`:`Achilles`},a=t=>{let n=r(t.instruction,4e3);if(!n)throw TypeError(`instruction is required`);let a=new Date().toISOString(),o=Math.random().toString(36).slice(2,8).toUpperCase(),s=t.targetFloor??i(n);return{schema_version:e,command_id:`LSGO-${a.replace(/\D/g,``).slice(0,14)}-${o}`,created_utc:a,source:`LS GO`,title:r(t.title||n,160),instruction:n,target_floor:s,oversight_floor:`Achilles`,priority:t.priority??`normal`,execution_mode:t.executionMode??`review`,proof_required:!0,public_safe:!0}},o=async(e,t,n=3500)=>{let r=new AbortController,i=window.setTimeout(()=>r.abort(),n);try{let n=await fetch(e,{...t,signal:r.signal,cache:`no-store`});if(!n.ok){let e=`Desktop returned HTTP ${n.status}`;try{let t=await n.json();t.detail&&(e=t.detail)}catch{}throw Error(e)}return await n.json()}finally{window.clearTimeout(i)}},s=(e=t)=>o(`${e}/api/v1/status`,{method:`GET`},1e4),c=(e,n=t)=>o(`${n}/api/v1/ls-go/commands`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify(e)},7e3),ee=async(e=t)=>{let n=await o(`${e}/api/v1/tasks?limit=12`,{method:`GET`});return Array.isArray(n.tasks)?n.tasks:[]},l=async(e=t)=>{let n=await o(`${e}/api/v1/projects`,{method:`GET`},15e3);return{projects:Array.isArray(n.projects)?n.projects:[],summary:n.summary||{},duplicateNames:Array.isArray(n.duplicate_names)?n.duplicate_names:[],cleanupSummary:n.cleanup_summary||{}}},u=async(e=t,n=50)=>{let r=await o(`${e}/api/v1/reviews?limit=${Math.max(1,Math.min(n,200))}`,{method:`GET`},1e4);return Array.isArray(r.reviews)?r.reviews:[]},d=async(e,n,i=``,a=t)=>o(`${a}/api/v1/reviews/${encodeURIComponent(e)}/decision`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({decision:n,note:r(i,1e3)})},7e3),f=`lightspeed-go-pending-commands-v1`,p=()=>{try{let e=JSON.parse(localStorage.getItem(f)||`[]`);return Array.isArray(e)?e:[]}catch{return[]}},m=e=>{let t=[e,...p().filter(t=>t.command_id!==e.command_id)].slice(0,30);return localStorage.setItem(f,JSON.stringify(t)),t},h=e=>{let t=p().filter(t=>t.command_id!==e);return localStorage.setItem(f,JSON.stringify(t)),t},g=e=>{let t=new Blob([JSON.stringify(e,null,2)],{type:`application/json`}),n=URL.createObjectURL(t),r=document.createElement(`a`);r.href=n,r.download=`${e.command_id}.json`,r.click(),URL.revokeObjectURL(n)},_=`lightspeed-neo-exchange-v1`,v=[`critical`,`high`,`normal`,`low`],te=[`queued`,`active`,`review`,`blocked`,`complete`],y=[`icon`,`age_label`],b=e=>typeof e==`object`&&!!e&&!Array.isArray(e),x=(e,t,n)=>{if(typeof e!=`string`)return t;let r=e.replace(/\s+/g,` `).trim();return r?r.slice(0,n):t},S=(e,t,n)=>{let r=x(e,``,n);if(!r)throw TypeError(`queue record ${t} is required`);return r},C=(e,t,n)=>typeof e==`string`&&t.includes(e)?e:n,w=e=>b(e)?Object.fromEntries(y.flatMap(t=>{let n=x(e[t],``,48);return n?[[t,n]]:[]})):{},T=e=>{if(!b(e))throw TypeError(`queue record must be an object`);return{id:S(e.id,`id`,80),title:S(e.title,`title`,160),priority:C(e.priority,v,`normal`),status:C(e.status,te,`queued`),source:x(e.source,`GO Gate`,48),target:x(e.target,`Neo`,48),created_utc:x(e.created_utc,``,32),extensions:w(e.extensions),notes:x(e.notes,``,240)}},E=e=>{if(!b(e))throw TypeError(`Neo exchange must be an object`);let t=Array.isArray(e.queue)?e.queue.map(T):[];return{schema_version:_,generated_at_utc:x(e.generated_at_utc,``,32),queue:t}},D=e=>({total:e.queue.length,critical:e.queue.filter(e=>e.priority===`critical`).length,active:e.queue.filter(e=>e.status!==`complete`).length,complete:e.queue.filter(e=>e.status===`complete`).length}),O=e=>e.replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#039;`})[e]??e),k=async e=>{try{return E(await e())}catch{return E({})}},A=e=>e.status===`blocked`?`blocked`:e.status===`complete`?`pass`:e.priority===`critical`||e.priority===`high`?`warn`:`ready`,j=e=>{let t=D(e),n=e.queue.length?e.queue.map(e=>`
            <li class="status-row ${A(e)}">
              <div>
                <strong>${O(e.title)}</strong>
                <span>${O(e.source)} to ${O(e.target)} · ${O(e.id)}</span>
                ${e.notes?`<small>${O(e.notes)}</small>`:``}
              </div>
              <em>${O(e.status)}</em>
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
  `},M=[{name:`Central Facility Boundary`,radiusM:2500,description:`All facilities and buildings remain inside this radius.`},{name:`Active Eco-Restoration`,radiusM:3500,description:`1 km active band for managed biome, native rehabilitation, and functional climate pockets.`},{name:`Passive Eco-Restoration`,radiusM:11e3,description:`Outer passive restoration reserve securing the full radial print.`}],ne=[{id:`integration-hall`,name:`Integration Hall`,footprint:`40 m x 75 m, 22 m clear`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Starship-compatible roller doors both ends; single bridge crane spans the hall.`},{id:`chainhill`,name:`ChainHill Relay`,footprint:`~225-250 m relay length`,elevation:`flat raised concrete, approximately 3 m above water table`,releaseStatus:`bounded-assumption`,notes:`Incoming and outgoing tracks oppose each other with two anti-parallel internal lines.`},{id:`x-pads`,name:`X-Layout Pads`,footprint:`solid pads, no beveled building base`,elevation:`pad-specific hardstand`,releaseStatus:`canonical`,notes:`Flame/exhaust outlets orient away from central node and buildings.`},{id:`mission-control`,name:`Mission Control / ATC`,footprint:`pentagon base, level 1 at 80%, four-storey tower`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Foyer, cafeteria, meeting, offices, emergency access, elevator, and top operating floor.`},{id:`living-rd`,name:`R&D + Living Quarters`,footprint:`room-level workbook detail pending`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`known-unknown`,notes:`FIFO and FIFO+family support with ground community and rooftop lifestyle zones.`}],re=[`site_zones`,`facilities`,`rooms_spaces`,`roads_tracks`,`pads_exhaust`,`eco_restoration`,`standards_evidence`,`viewer_toggles`,`known_unknowns`],N=document.getElementById(`app`);if(!N)throw Error(`LightSpeed Go mount node #app not found.`);N.innerHTML=`
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

    <section class="view" id="view-system">
      <article class="panel definition">
        <div><p class="eyebrow">cognigrex</p><h2>Common goal, distinct agents</h2></div>
        <p>The system coordinates GO, Desktop, Git, Drive, agents and human oversight while retaining separate authority, resource limits and reviewable receipts.</p>
      </article>
      <div class="agent-grid">${[[`Achilles`,`governance, proof and release`],[`Neo`,`task routing and handoff`],[`Architect`,`projects, plans and dependencies`],[`TheConstruct`,`simulation and digital twins`],[`Morpheus`,`claim proof and conflict resolution`],[`Oracle`,`sources, evidence and knowns`],[`Smith`,`Git, code, schemas and execution`],[`Merovingian`,`health, storage, projects and recovery`],[`Trinity`,`interface and visual implementation`]].map(([e,t])=>`<article class="agent"><strong>${e}</strong><span>${t}</span></article>`).join(``)}</div>
      <div class="two-column">
        <article class="panel"><p class="eyebrow">Execution path</p><h2>One project, one receipt chain</h2><div class="flow"><span>LS GO</span><i>→</i><span>Achilles</span><i>→</i><span>Neo + floor</span><i>→</i><span>Desktop project</span><i>→</i><span>Drive receipt</span><i>→</i><span>GO decision</span></div></article>
        <article class="panel"><p class="eyebrow">Existing twin context</p><h2>Spaceport contract retained</h2><p class="muted">${M.length} zones · ${ne.length} facility records · ${re.length} workbook tabs. The twin remains bounded context, not the command-centre homepage.</p></article>
      </div>
    </section>

    <section class="view" id="view-sources">
      <div class="source-grid">${[[`LightSpeed Git`,`https://github.com/achillesromer-coder/LightSpeed`,`Versioned implementation and receipts`],[`LS GO Queue`,`https://docs.google.com/spreadsheets/d/1f5i4V3FshYHkztv3_HAg0ZofUl0sdcJZcwrlesUlCfM/edit`,`Phone tasks, approvals, commands, results and sync health`],[`Portfolio Handoff`,`https://docs.google.com/document/d/1tsDkb79UVX_SqS2-oBgc5DHb89QIlH3DcmKMN77hdOo/edit`,`Cross-chat portfolio continuity`],[`Römer Industries`,`https://romer.industries`,`Reviewed public portfolio surface`]].map(([e,t,n])=>`<a class="source-card" href="${t}" target="_blank" rel="noreferrer"><strong>${e}</strong><span>${n}</span><em>Open ↗</em></a>`).join(``)}</div>
      <article class="panel"><p class="eyebrow">Authority order</p><h2>Where each truth lives</h2><div class="authority-grid"><div><strong>Drive</strong><span>evidence, workbooks and review receipts</span></div><div><strong>Git</strong><span>code, schemas, tests and implementation receipts</span></div><div><strong>Desktop</strong><span>projects, local execution, state and jobs</span></div><div><strong>LS GO</strong><span>owner commands, review and bounded decisions</span></div></div></article>
    </section>
  </main>
`;var P=e=>{let t=document.getElementById(e);if(!t)throw Error(`Missing #${e}`);return t},F=P(`instruction`),I=P(`target-floor`),L=P(`priority`),R=P(`execution-mode`),z=P(`route-preview`),B=P(`command-result`),V=null,H=[],U=()=>{let e=i(F.value||`governance`);I.value=e,z.innerHTML=`<strong>Achilles route:</strong> ${e} is primary. Neo coordinates and proof returns to this gate.`};F.addEventListener(`input`,U),U();var W=()=>a({instruction:F.value,targetFloor:I.value,priority:L.value,executionMode:R.value}),G=(e,t)=>{B.dataset.tone=e,B.textContent=t},K=()=>{let e=p();P(`pending-count`).textContent=String(e.length);let t=P(`pending-commands`);if(!e.length){t.innerHTML=`<p class="muted">No locally saved commands.</p>`;return}t.innerHTML=e.map(e=>`<article class="task-card"><div><strong>${O(e.title)}</strong><span>${O(e.target_floor)} · ${O(e.priority)} · ${O(e.execution_mode)}</span><small>${O(e.command_id)}</small></div><div class="task-actions"><button data-send="${O(e.command_id)}">Send</button><button data-download="${O(e.command_id)}">Download</button></div></article>`).join(``),t.querySelectorAll(`[data-send]`).forEach(t=>t.addEventListener(`click`,async()=>{let n=e.find(e=>e.command_id===t.dataset.send);if(n)try{let e=await c(n);h(n.command_id),K(),G(`good`,`Desktop accepted ${e.command_id||n.command_id}. Task ${e.task_id??`created`}.`),await X()}catch(e){G(`bad`,e instanceof Error?e.message:`Desktop command failed.`)}})),t.querySelectorAll(`[data-download]`).forEach(t=>t.addEventListener(`click`,()=>{let n=e.find(e=>e.command_id===t.dataset.download);n&&g(n)}))},q=e=>{let t=Number(e||0);return t<1024?`${t} B`:t<1024**2?`${(t/1024).toFixed(1)} KB`:t<1024**3?`${(t/1024**2).toFixed(1)} MB`:`${(t/1024**3).toFixed(1)} GB`},J=e=>{let t=P(`desktop-projects`);if(P(`project-count`).textContent=String(e.length),!e.length){t.innerHTML=`<p class="muted">No project folders were found in the configured roots.</p>`;return}t.innerHTML=e.slice(0,30).map(e=>`<article class="task-card"><div><strong>${O(e.name)}</strong><span>${O(e.condition||`unknown`)} · ${O(e.authority||`reference`)} · ${e.file_count||0} files</span><small>${q(e.size_bytes)}${e.scan_truncated?` · bounded scan`:``}</small></div></article>`).join(``)},Y=e=>{H=e;let t=P(`desktop-reviews`);if(!e.length){t.innerHTML=`<p class="muted">No project receipts are awaiting review.</p>`;return}t.innerHTML=e.slice(0,30).map(e=>{let t=e.state||`pending_review`,n=t===`pending_review`?`<div class="task-actions"><button data-review="${O(e.review_id)}" data-decision="approve">Approve</button><button data-review="${O(e.review_id)}" data-decision="hold">Hold</button><button data-review="${O(e.review_id)}" data-decision="reject">Reject</button></div>`:``;return`<article class="task-card"><div><strong>${O(e.title||`Project receipt`)}</strong><span>${O(t)} · ${O(e.event_type||`receipt`)}</span><small>${O(e.summary||e.review_id)}</small></div>${n}</article>`}).join(``),t.querySelectorAll(`[data-review]`).forEach(e=>e.addEventListener(`click`,async()=>{let t=e.dataset.review||``,n=e.dataset.decision,r=H.find(e=>e.review_id===t);if(!r||!t)return;let i=window.prompt(`${n.toUpperCase()}: ${r.title||t}\nOptional decision note:`,``)??``;try{await d(t,n,i),G(`good`,`${t} marked ${n}. Drive decision receipt written by Desktop.`),await X()}catch(e){G(`bad`,e instanceof Error?e.message:`Review decision failed.`)}}))};P(`command-form`).addEventListener(`submit`,async e=>{e.preventDefault();try{V=W(),G(`warn`,`Sending ${V.command_id} to Desktop…`);let e=await c(V);h(V.command_id),K(),G(`good`,`Accepted by Desktop. Task ${e.task_id??`created`}; ${e.state||`queued for governed processing`}.`),await X()}catch(e){V&&m(V),K(),G(`bad`,`${e instanceof Error?e.message:`Desktop unavailable`} The command envelope was saved locally.`)}}),P(`save-command`).addEventListener(`click`,()=>{try{V=W(),m(V),K(),G(`good`,`${V.command_id} saved locally.`)}catch(e){G(`bad`,e instanceof Error?e.message:`Command could not be saved.`)}}),P(`copy-command`).addEventListener(`click`,async()=>{try{V=W(),await navigator.clipboard.writeText(JSON.stringify(V,null,2)),G(`good`,`${V.command_id} copied as JSON.`)}catch(e){G(`bad`,e instanceof Error?e.message:`Command could not be copied.`)}});var X=async()=>{let e=P(`desktop-pill`),t=P(`desktop-state`),n=P(`merovingian-state`),r=P(`desktop-pill-text`),i=P(`desktop-tasks`);e.dataset.state=`checking`,r.textContent=`checking local runtime`,t.textContent=`Checking`,n.textContent=`Checking`;try{let a=await s();e.dataset.state=a.ok?`online`:`degraded`,r.textContent=a.ok?`local runtime connected`:`runtime connected; health needs review`,t.textContent=`Online`,n.textContent=a.merovingian?.status===`pass`?`Healthy`:`Degraded`;try{let e=await ee();i.innerHTML=e.length?e.map(e=>`<article class="task-card"><div><strong>${O(String(e.title||`Untitled task`))}</strong><span>${O(String(e.status||`unknown`))} · ${O(String(e.priority||`normal`))}</span><small>Task ${O(String(e.id||``))}</small></div></article>`).join(``):`<p class="muted">Desktop queue is clear.</p>`}catch{i.innerHTML=`<p class="muted">Desktop is online, but task listing is unavailable.</p>`}try{J((await l()).projects)}catch{J([])}try{Y(await u())}catch{Y([])}}catch{e.dataset.state=`offline`,r.textContent=`start LightSpeed Desktop and the local bridge`,t.textContent=`Offline`,n.textContent=`Offline`,P(`project-count`).textContent=`0`,i.innerHTML=`<p class="muted">Desktop is offline. Commands can still be saved, copied or downloaded.</p>`,P(`desktop-projects`).innerHTML=`<p class="muted">Project registry unavailable while Desktop is offline.</p>`,P(`desktop-reviews`).innerHTML=`<p class="muted">Review queue unavailable while Desktop is offline.</p>`}};P(`refresh-desktop`).addEventListener(`click`,()=>void X()),K(),X();var Z=P(`neo-exchange`),ie=new URL(`./data/neo_exchange.json`,document.baseURI).toString();k(async()=>{let e=await fetch(ie,{cache:`no-store`});if(!e.ok)throw Error(`Neo exchange returned HTTP ${e.status}`);return e.json()}).then(e=>{Z.innerHTML=j(e)}),document.querySelectorAll(`.tab`).forEach(e=>e.addEventListener(`click`,()=>{document.querySelectorAll(`.tab`).forEach(e=>e.classList.remove(`active`)),document.querySelectorAll(`.view`).forEach(e=>e.classList.remove(`active`)),e.classList.add(`active`),P(`view-${e.dataset.view}`).classList.add(`active`)}));var ae=new URL(`./data/site_integration.json`,document.baseURI).toString(),oe=async()=>{try{let e=await fetch(ae,{cache:`no-store`});return e.ok?await e.json():null}catch{return null}},se=()=>{if(document.getElementById(`lsgo-sites-side-edit-styles`))return;let e=document.createElement(`style`);e.id=`lsgo-sites-side-edit-styles`,e.textContent=`
    .site-context-strip { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
    .site-context-strip span { border:1px solid var(--line); border-radius:999px; padding:7px 10px; color:var(--muted); font-size:12px; background:rgba(255,255,255,.025); }
    .site-context-strip strong { color:var(--text); }
    .site-parity-card { border:1px solid var(--line); border-radius:14px; padding:14px; background:rgba(255,255,255,.025); display:grid; gap:8px; }
    .site-parity-card p { margin:0; color:var(--muted); line-height:1.5; }
    .site-parity-card .site-chain { display:flex; flex-wrap:wrap; gap:7px; align-items:center; }
    .site-parity-card .site-chain span { border:1px solid var(--line); border-radius:999px; padding:6px 9px; font-size:12px; }
    .site-parity-card .site-chain i { color:var(--teal); font-style:normal; }
  `,document.head.appendChild(e)},ce=async()=>{let e=document.querySelector(`.topbar > div:first-child`),t=document.querySelector(`#view-sources`);if(!e||!t)return!1;se();let n=await oe(),r=n?.authority_chain??[`Nathaniel Bouwer`,`Achilles / GO gate`,`agent floor`,`LightSpeed Desktop`,`Git and Drive receipts`];if(!document.getElementById(`site-context-strip`)){let t=document.createElement(`div`);t.id=`site-context-strip`,t.className=`site-context-strip`,t.innerHTML=`
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
    `,t.prepend(e)}return!0},Q=0,$=()=>{ce().then(e=>{e||Q>=40||(Q+=1,window.requestAnimationFrame($))})};$();