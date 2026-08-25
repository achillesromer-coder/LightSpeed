(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),e.crossOrigin===`use-credentials`?t.credentials=`include`:e.crossOrigin===`anonymous`?t.credentials=`omit`:t.credentials=`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var e=`lightspeed-go-command-v2`,t=`http://127.0.0.1:8765`,n=[`Achilles`,`Neo`,`Architect`,`TheConstruct`,`Morpheus`,`Oracle`,`Smith`,`Merovingian`,`Trinity`],r=(e,t)=>e.replace(/\s+/g,` `).trim().slice(0,t),i=e=>{let t=e.toLowerCase();return/\b(ui|site|web|design|visual|layout|canva|accessibility)\b/.test(t)?`Trinity`:/\b(git|github|code|build|commit|branch|deploy|schema|api|runtime)\b/.test(t)?`Smith`:/\b(source|evidence|research|data|document|drive|sheet|workbook|citation)\b/.test(t)?`Oracle`:/\b(proof|claim|verify|conflict|confidence|audit)\b/.test(t)?`Morpheus`:/\b(simulate|simulation|model|gmat|trajectory|twin|physics)\b/.test(t)?`TheConstruct`:/\b(plan|mission|architecture|dependency|roadmap|system|project)\b/.test(t)?`Architect`:/\b(health|status|diagnostic|failure|error|monitor|storage|cleanup|archive)\b/.test(t)?`Merovingian`:/\b(coordinate|queue|handoff|agent|task|execute|run)\b/.test(t)?`Neo`:`Achilles`},a=t=>{let n=r(t.instruction,4e3);if(!n)throw TypeError(`instruction is required`);let a=new Date().toISOString(),o=Math.random().toString(36).slice(2,8).toUpperCase(),s=t.targetFloor??i(n),c=t.authorityContract;if(!c)throw TypeError(`Desktop authority contract is not available`);let l=r(c.canonical_gate_id,160),u=r(c.owner_decision_ref,160),d=r(c.core_acceptance_ref,160),f=r(c.approval_or_hold_state,40).toLowerCase(),p=r(c.authorised_scope,1e3),m=r(c.prohibited_scope,1e3);if(!l||!u||!d||!p||!m)throw TypeError(`Desktop authority contract is incomplete`);if(![`approve`,`approved`,`operator_approved`,`operator_authorized`,`operator_authorised`].includes(f))throw TypeError(`Desktop authority contract is held`);let h=t.executionMode??`review`;return{schema_version:e,command_id:`LSGO-${a.replace(/\D/g,``).slice(0,14)}-${o}`,created_utc:a,source:`LS GO`,title:r(t.title||n,160),instruction:n,target_floor:s,oversight_floor:`Achilles`,priority:t.priority??`normal`,execution_mode:h,action_type:t.actionType??`cognigrex_workflow`,proof_required:!0,public_safe:!0,canonical_gate_id:l,owner_decision_ref:u,core_acceptance_ref:d,approval_or_hold_state:f,authorised_scope:p,prohibited_scope:m,requested_scope:`${s} private local ${h} queue`}},o=class extends Error{status;constructor(e,t){super(t),this.name=`DesktopRequestError`,this.status=e}},s=async(e,t,n=3500)=>{let r=new AbortController,i=window.setTimeout(()=>r.abort(),n);try{let n=await fetch(e,{...t,signal:r.signal,cache:`no-store`});if(!n.ok){let e=`Desktop returned HTTP ${n.status}`;try{let t=await n.json();t.detail&&(e=t.detail)}catch{}throw new o(n.status,e)}return await n.json()}finally{window.clearTimeout(i)}},c=(e=t)=>s(`${e}/api/v1/status`,{method:`GET`},1e4),l=(e,n=t)=>s(`${n}/api/v1/ls-go/commands`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify(e)},7e3),u=async(e=t)=>{let n=await s(`${e}/api/v1/tasks?limit=12`,{method:`GET`});return Array.isArray(n.tasks)?n.tasks:[]},d=async(e=t)=>{let n=await s(`${e}/api/v1/projects`,{method:`GET`},15e3);return{projects:Array.isArray(n.projects)?n.projects:[],summary:n.summary||{},duplicateNames:Array.isArray(n.duplicate_names)?n.duplicate_names:[],cleanupSummary:n.cleanup_summary||{}}},f=(e,t)=>{let n=encodeURIComponent(e);return t===void 0?`/api/v1/projects/${n}/files`:`/api/v1/projects/${n}/files/${t.split(`/`).map(e=>encodeURIComponent(e)).join(`/`)}`},p=async(e,n=t)=>s(`${n}${f(e)}?limit=200`,{method:`GET`},15e3),m=async(e,n,r,i=t)=>s(`${i}${f(e,n)}`,{method:`GET`,headers:{"X-LightSpeed-Owner-Confirmation":r.slice(0,256)}},1e4),h=e=>e===void 0?`/api/v1/results`:`/api/v1/results/${encodeURIComponent(e)}`,ee=async(e=t,n=50)=>s(`${e}${h()}?limit=${Math.max(1,Math.min(n,200))}`,{method:`GET`},1e4),te=async(e,n,r=t)=>s(`${r}${h(e)}`,{method:`GET`,headers:{"X-LightSpeed-Owner-Confirmation":n.slice(0,256)}},1e4),ne=async(e=t,n=50)=>{let r=await s(`${e}/api/v1/reviews?limit=${Math.max(1,Math.min(n,200))}`,{method:`GET`},1e4);return Array.isArray(r.reviews)?r.reviews:[]},re=async(e,n,i=``,a=``,o=t)=>s(`${o}/api/v1/reviews/${encodeURIComponent(e)}/decision`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Owner-Confirmation":a},body:JSON.stringify({decision:n,note:r(i,1e3)})},7e3),ie=(e,t,n)=>{let r=n.receipt?.drive_writeback_mode;return r===`owner_approved_exact_drive_target`?`${e} marked ${t}. Owner-approved Drive decision receipt written by Desktop.`:r===`local_outbox_pending_drive_sync`?`${e} marked ${t}. Local outbox receipt staged; Drive sync remains pending.`:`${e} marked ${t}. Decision receipt recorded; destination requires verification.`},ae=async(e=t)=>{let n=await s(`${e}/api/v1/representation-graphs`,{method:`GET`},15e3);return Array.isArray(n.graphs)?n.graphs:[]},oe=async(e,n,i,a=[],o=``,c=``,l=t)=>s(`${l}/api/v1/representation-reviews/${encodeURIComponent(e)}/decision`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Owner-Confirmation":c.slice(0,256)},body:JSON.stringify({decision:n,scope:i,edge_ids:a.slice(0,100),note:r(o,1e3)})},1e4),g=`lightspeed-go-pending-commands-v1`,_=()=>{try{let e=JSON.parse(localStorage.getItem(g)||`[]`);return Array.isArray(e)?e:[]}catch{return[]}},v=e=>{let t=[e,..._().filter(t=>t.command_id!==e.command_id)].slice(0,30);return localStorage.setItem(g,JSON.stringify(t)),t},se=e=>{let t=_().filter(t=>t.command_id!==e);return localStorage.setItem(g,JSON.stringify(t)),t},ce=e=>{let t=new Blob([JSON.stringify(e,null,2)],{type:`application/json`}),n=URL.createObjectURL(t),r=document.createElement(`a`);r.href=n,r.download=`${e.command_id}.json`,r.click(),URL.revokeObjectURL(n)},le=`lightspeed-neo-exchange-v1`,ue=[`critical`,`high`,`normal`,`low`],de=[`queued`,`active`,`review`,`blocked`,`complete`],fe=[`icon`,`age_label`],y=e=>typeof e==`object`&&!!e&&!Array.isArray(e),b=(e,t,n)=>{if(typeof e!=`string`)return t;let r=e.replace(/\s+/g,` `).trim();return r?r.slice(0,n):t},pe=(e,t,n)=>{let r=b(e,``,n);if(!r)throw TypeError(`queue record ${t} is required`);return r},me=(e,t,n)=>typeof e==`string`&&t.includes(e)?e:n,he=e=>y(e)?Object.fromEntries(fe.flatMap(t=>{let n=b(e[t],``,48);return n?[[t,n]]:[]})):{},ge=e=>{if(!y(e))throw TypeError(`queue record must be an object`);return{id:pe(e.id,`id`,80),title:pe(e.title,`title`,160),priority:me(e.priority,ue,`normal`),status:me(e.status,de,`queued`),source:b(e.source,`GO Gate`,48),target:b(e.target,`Neo`,48),created_utc:b(e.created_utc,``,32),extensions:he(e.extensions),notes:b(e.notes,``,240)}},_e=e=>{if(!y(e))throw TypeError(`Neo exchange must be an object`);let t=Array.isArray(e.queue)?e.queue.map(ge):[];return{schema_version:le,generated_at_utc:b(e.generated_at_utc,``,32),queue:t}},ve=e=>({total:e.queue.length,critical:e.queue.filter(e=>e.priority===`critical`).length,active:e.queue.filter(e=>e.status!==`complete`).length,complete:e.queue.filter(e=>e.status===`complete`).length}),x=e=>e.replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#039;`})[e]??e),ye=async e=>{try{return _e(await e())}catch{return _e({})}},be=e=>e.status===`blocked`?`blocked`:e.status===`complete`?`pass`:e.priority===`critical`||e.priority===`high`?`warn`:`ready`,xe=e=>{let t=ve(e),n=e.queue.length?e.queue.map(e=>`
            <li class="status-row ${be(e)}">
              <div>
                <strong>${x(e.title)}</strong>
                <span>${x(e.source)} to ${x(e.target)} · ${x(e.id)}</span>
                ${e.notes?`<small>${x(e.notes)}</small>`:``}
              </div>
              <em>${x(e.status)}</em>
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
  `},S=e=>{let t=Number(e||0);return t<1024?`${t} B`:t<1024**2?`${(t/1024).toFixed(1)} KB`:t<1024**3?`${(t/1024**2).toFixed(1)} MB`:`${(t/1024**3).toFixed(1)} GB`},Se=e=>e.length?e.slice(0,30).map(e=>`
    <article class="task-card project-card" data-project-card="${x(e.project_id)}">
      <div class="project-summary">
        <strong>${x(e.name)}</strong>
        <span>${x(e.condition||`unknown`)} · ${x(e.authority||`reference`)} · ${e.file_count||0} files</span>
        <small>${S(e.size_bytes)}${e.scan_truncated?` · bounded scan`:``}</small>
      </div>
      <div class="task-actions">
        <button type="button" data-project-files="${x(e.project_id)}" aria-expanded="false">Files</button>
      </div>
      <div class="project-files" aria-live="polite" hidden></div>
    </article>
  `).join(``):`<p class="muted">No project folders were found in the configured roots.</p>`,Ce=e=>{let t=e.summary,n=`<p class="project-file-boundary">${x(e.boundary)}</p>`;if(!e.files.length){let t=e.state===`restricted`?`No files are visible; credential-like or excluded runtime files are withheld.`:`This registered project currently has no visible files.`;return`<div class="project-files-head"><strong>Files</strong><small>${x(e.project.authority||`reference`)} authority</small></div><p class="muted">${t}</p>${n}`}let r=e.files.map(t=>`
    <article class="project-file-row">
      <div><strong>${x(t.relative_path)}</strong><small>${x(t.mime_type)} · ${S(t.size_bytes)}</small></div>
      <button type="button" data-project-file="${x(t.relative_path)}" data-project-id="${x(e.project.project_id)}">Open</button>
    </article>
  `).join(``),i=t.scan_truncated?` · bounded result`:``;return`
    <div class="project-files-head"><strong>Files</strong><small>${t.visible_file_count} visible · ${t.blocked_file_count} withheld${i}</small></div>
    <div class="project-file-list">${r}</div>
    <div class="project-file-result" aria-live="polite"></div>
    ${n}
  `},C=e=>`
  <div class="project-files-head"><strong>Files unavailable</strong></div>
  <p class="result" data-tone="bad">${x(e)}</p>
`,we=e=>{let t=e.preview,n=`<p class="muted">Metadata only. Binary or non-UTF-8 content is not transferred into LS GO.</p>`;return t.state===`empty`?n=`<p class="muted">The file is empty.</p>`:t.state===`available`&&(n=`<pre>${x(t.text||``)}</pre>${t.truncated?`<small class="muted">Preview truncated at the governed byte limit.</small>`:``}`),`
    <section class="project-file-preview">
      <div class="project-files-head"><strong>${x(e.file.relative_path)}</strong><small>${x(e.file.mime_type)} · ${S(e.file.size_bytes)}</small></div>
      ${n}
      <p class="project-file-boundary">${x(e.boundary)}</p>
    </section>
  `},Te=(e,t)=>{e.querySelectorAll(`[data-project-files]`).forEach(e=>{e.addEventListener(`click`,()=>{let n=e.dataset.projectFiles||``;n&&t(n,e)})})},Ee=(e,t)=>{e.querySelectorAll(`[data-project-file][data-project-id]`).forEach(e=>{e.addEventListener(`click`,()=>{let n=e.dataset.projectId||``,r=e.dataset.projectFile||``;n&&r&&t(n,r,e)})})},w=e=>{let t=Number(e||0);return t<1024?`${t} B`:t<1024**2?`${(t/1024).toFixed(1)} KB`:`${(t/1024**2).toFixed(1)} MB`},De=e=>{let t=String(e.status||`unknown`).toLowerCase();return[`complete`,`completed`,`pass`,`passed`].includes(t)?`good`:[`blocked`,`failed`,`error`].includes(t)?`bad`:`warn`},Oe=(e,t)=>{let n=e.summary,r=`<p class="result-receipt-boundary">${x(e.boundary)}</p>`,i=t?`Exact receipt content requires the local owner-confirmation token.`:`Content inspection is held because the local owner-confirmation token is not configured.`;if(!e.results.length)return`<p class="muted">${e.state===`restricted`?`No eligible fixed receipts are visible; invalid receipt objects remain withheld.`:`No fixed local result receipts have been written yet.`}</p><p class="result-receipt-auth">${i}</p>${r}`;let a=e.results.map(e=>{let n=e.action_type||`untyped`,r=e.target_floor||`floor unknown`,i=e.completed_utc||e.created_utc||e.modified_utc,a=[e.task_id==null?null:`Task ${e.task_id}`,e.job_id==null?null:`Job ${e.job_id}`,e.command_id||null].filter(Boolean).join(` · `),o=t?``:` disabled aria-disabled="true"`;return`
      <article class="task-card result-receipt-card" data-result-state="${De(e)}">
        <div>
          <strong>${x(e.result_id)}</strong>
          <span>${x(e.status)} · ${x(n)} · ${x(r)}</span>
          <small>${x(a||`No task/job identity`)} · ${x(i||`time unavailable`)} · ${w(e.size_bytes)}</small>
        </div>
        <div class="task-actions">
          <button type="button" data-result-receipt="${x(e.result_id)}"${o}>Inspect receipt</button>
        </div>
      </article>
    `}).join(``),o=n.truncated?` · bounded index`:``;return`
    <div class="result-receipt-summary"><span>${n.visible_result_count} visible${o}</span><span>${n.invalid_file_count} invalid withheld</span></div>
    <div class="result-receipt-list">${a}</div>
    <div class="result-receipt-detail" aria-live="polite"></div>
    <p class="result-receipt-auth">${x(i)}</p>
    ${r}
  `},ke=e=>{let t=JSON.stringify(e.result,null,2);return`
    <section class="result-receipt-preview">
      <div class="result-receipt-preview-head">
        <strong>${x(e.identity.result_id)}</strong>
        <small>${w(e.identity.size_bytes)} · SHA-256 ${x(e.identity.sha256)}</small>
      </div>
      <pre>${x(t)}</pre>
      <p class="result-receipt-boundary">${x(e.boundary)}</p>
    </section>
  `},T=e=>`
  <p class="result" data-tone="bad">${x(e)}</p>
`,Ae=(e,t)=>{e.querySelectorAll(`[data-result-receipt]`).forEach(e=>{e.addEventListener(`click`,()=>{let n=e.dataset.resultReceipt||``;n&&!e.disabled&&t(n,e)})})},E=e=>String(e??``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),D=e=>e?`${e.slice(0,12)}…${e.slice(-8)}`:`not available`,je=e=>e.path_exposed===!1?String(e.label||`private local evidence`):[e.repository,e.commit_sha?`commit ${String(e.commit_sha).slice(0,12)}`:null,e.path,e.drive_file_id?`Drive ${e.drive_file_id}`:null,e.sheet_name,e.stable_key||e.content_key,e.missing_state].filter(Boolean).map(E).join(` · `)||E(e.locator_type||`logical`),O=e=>E(JSON.stringify(e,null,2)),Me=e=>{let t=e.representations.filter(e=>e.state===`active`).length,n=e.missing.length;return!t&&n?`unable to determine`:n>t?`smaller bowl`:t>n?`larger bowl`:`unchanged bowl`},Ne=e=>{let t=e.review,n=t?.review_stage||`identity`,r=e.edges.map(e=>e.edge_id).join(`|`),i=t?`
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
      <td>${je(e.locator)}</td>
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
        <details><summary>Assumptions and constraints</summary><pre>${O({assumptions:e.assumptions,constraints:e.constraints})}</pre></details>
        <small>Input ${D(e.input_set_sha256)}</small>
      </article>`).join(``):`<p class="muted">No horizon is assigned.</p>`,u=e.representations.find(e=>e.representation_type===`recommendation`)?.locator.next_highest_value_question,d=(e.linked_objects||[]).length?(e.linked_objects||[]).map(t=>{let n=(e.linked_identifiers||[]).filter(e=>e.object_id===t.object_id).map(e=>`${e.namespace}: ${e.identifier_value}`).join(` | `);return`<article class="missing-card">
        <strong>${E(t.display_name)} · ${E(t.state)}</strong>
        <span><b>Object:</b> ${E(t.object_id)}</span>
        <span><b>Identifiers:</b> ${E(n||`none recorded`)}</span>
      </article>`}).join(``):`<p class="muted">No linked object identity is included.</p>`,f=(e.evidence_bundles||[]).length?(e.evidence_bundles||[]).map(e=>`
      <article class="horizon-card">
        <div><strong>${E(e.title)}</strong><span>${E(e.state)}</span></div>
        <p>${E(e.claim_boundary)}</p>
        <small>${e.independence_group_count} independence groups · ${e.duplicate_reference_count} duplicate references · confidence effect ${e.confidence_effect}</small>
        <details><summary>Source weight summary</summary><pre>${O(e.source_weight_summary)}</pre></details>
      </article>`).join(``):`<p class="muted">No evidence bundle is linked.</p>`;return`
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
        <div><span>Judgment</span><strong>${Me(e)}</strong></div>
      </div>
      <details open><summary>Identifiers (${e.identifiers.length})</summary><div class="identifier-list">${e.identifiers.map(e=>`<span><strong>${E(e.namespace)}</strong>${E(e.identifier_value)} · ${E(e.authority)}</span>`).join(``)}</div></details>
      <details open><summary>Linked identities (${(e.linked_objects||[]).length})</summary><div class="graph-grid">${d}</div></details>
      <details open><summary>Representations (${e.representations.length})</summary><div class="table-scroll"><table class="graph-table"><thead><tr><th>Type</th><th>Locator</th><th>Authority</th><th>Hash/revision</th><th>Confidence</th><th>State</th><th>Claim boundary</th></tr></thead><tbody>${a}</tbody></table></div></details>
      <details open><summary>Edges (${e.edges.length})</summary><div class="table-scroll"><table class="graph-table"><thead><tr><th>Source</th><th>Relation</th><th>Destination</th><th>Evidence</th><th>Review</th><th>Boundary</th></tr></thead><tbody>${o}</tbody></table></div></details>
      <details open><summary>Evidence bundles (${(e.evidence_bundles||[]).length})</summary>${f}</details>
      <div class="graph-grid">
        <section><h3>Missing</h3>${s}</section>
        <section><h3>Conflicts</h3>${c}</section>
      </div>
      <section><h3>Horizon</h3>${l}</section>
      <div class="next-question"><strong>Next highest-value question</strong><span>${E(u||`Owner review determines the next bounded question.`)}</span></div>
      ${i}
    </article>`},Pe=e=>e.length?e.map(Ne).join(``):`<article class="panel"><p class="muted">The feature-gated representation edge is disabled or unavailable.</p></article>`,Fe=[{name:`Central Facility Boundary`,radiusM:2500,description:`All facilities and buildings remain inside this radius.`},{name:`Active Eco-Restoration`,radiusM:3500,description:`1 km active band for managed biome, native rehabilitation, and functional climate pockets.`},{name:`Passive Eco-Restoration`,radiusM:11e3,description:`Outer passive restoration reserve securing the full radial print.`}],Ie=[{id:`integration-hall`,name:`Integration Hall`,footprint:`40 m x 75 m, 22 m clear`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Starship-compatible roller doors both ends; single bridge crane spans the hall.`},{id:`chainhill`,name:`ChainHill Relay`,footprint:`~225-250 m relay length`,elevation:`flat raised concrete, approximately 3 m above water table`,releaseStatus:`bounded-assumption`,notes:`Incoming and outgoing tracks oppose each other with two anti-parallel internal lines.`},{id:`x-pads`,name:`X-Layout Pads`,footprint:`solid pads, no beveled building base`,elevation:`pad-specific hardstand`,releaseStatus:`canonical`,notes:`Flame/exhaust outlets orient away from central node and buildings.`},{id:`mission-control`,name:`Mission Control / ATC`,footprint:`pentagon base, level 1 at 80%, four-storey tower`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Foyer, cafeteria, meeting, offices, emergency access, elevator, and top operating floor.`},{id:`living-rd`,name:`R&D + Living Quarters`,footprint:`room-level workbook detail pending`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`known-unknown`,notes:`FIFO and FIFO+family support with ground community and rooftop lifestyle zones.`}],Le=[`site_zones`,`facilities`,`rooms_spaces`,`roads_tracks`,`pads_exhaust`,`eco_restoration`,`standards_evidence`,`viewer_toggles`,`known_unknowns`],k=document.getElementById(`app`);if(!k)throw Error(`LightSpeed Go mount node #app not found.`);k.innerHTML=`
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
      <div class="agent-grid">${[[`Achilles`,`governance, proof and release`],[`Neo`,`task routing and handoff`],[`Architect`,`projects, plans and dependencies`],[`TheConstruct`,`simulation and digital twins`],[`Morpheus`,`claim proof and conflict resolution`],[`Oracle`,`sources, evidence and knowns`],[`Smith`,`Git, code, schemas and execution`],[`Merovingian`,`health, storage, projects and recovery`],[`Trinity`,`interface and visual implementation`]].map(([e,t])=>`<article class="agent"><strong>${e}</strong><span>${t}</span></article>`).join(``)}</div>
      <div class="two-column">
        <article class="panel"><p class="eyebrow">Execution path</p><h2>One project, one receipt chain</h2><div class="flow"><span>LS GO</span><i>→</i><span>Achilles</span><i>→</i><span>Neo + floor</span><i>→</i><span>Desktop project</span><i>→</i><span>Drive receipt</span><i>→</i><span>GO decision</span></div></article>
        <article class="panel"><p class="eyebrow">Existing twin context</p><h2>Spaceport contract retained</h2><p class="muted">${Fe.length} zones · ${Ie.length} facility records · ${Le.length} workbook tabs. The twin remains bounded context, not the command-centre homepage.</p></article>
      </div>
    </section>

    <section class="view" id="view-sources">
      <div class="source-grid">${[[`LightSpeed Git`,`https://github.com/achillesromer-coder/LightSpeed`,`Versioned implementation and receipts`],[`LS GO Queue`,`https://docs.google.com/spreadsheets/d/1f5i4V3FshYHkztv3_HAg0ZofUl0sdcJZcwrlesUlCfM/edit`,`Phone tasks, approvals, commands, results and sync health`],[`Portfolio Handoff`,`https://docs.google.com/document/d/1tsDkb79UVX_SqS2-oBgc5DHb89QIlH3DcmKMN77hdOo/edit`,`Cross-chat portfolio continuity`],[`Römer Industries`,`https://romer.industries`,`Reviewed public portfolio surface`]].map(([e,t,n])=>`<a class="source-card" href="${t}" target="_blank" rel="noreferrer"><strong>${e}</strong><span>${n}</span><em>Open ↗</em></a>`).join(``)}</div>
      <article class="panel"><p class="eyebrow">Authority order</p><h2>Where each truth lives</h2><div class="authority-grid"><div><strong>Drive</strong><span>evidence, workbooks and review receipts</span></div><div><strong>Git</strong><span>code, schemas, tests and implementation receipts</span></div><div><strong>Desktop</strong><span>projects, local execution, state and jobs</span></div><div><strong>LS GO</strong><span>owner commands, review and bounded decisions</span></div></div></article>
    </section>
  </main>
`;var A=e=>{let t=document.getElementById(e);if(!t)throw Error(`Missing #${e}`);return t},j=A(`instruction`),Re=A(`target-floor`),ze=A(`priority`),Be=A(`execution-mode`),Ve=A(`route-preview`),He=A(`command-result`),M=null,N=null,Ue=[],P=[],F=()=>{let e=i(j.value||`governance`);Re.value=e;let t=N?.canonical_gate_id;Ve.innerHTML=`<strong>Achilles route:</strong> ${e} is primary. Neo coordinates and proof returns to this gate.${t?` <small>Authority: ${x(t)}</small>`:` <small>Waiting for the Desktop authority contract.</small>`}`};j.addEventListener(`input`,F),F();var I=()=>a({instruction:j.value,targetFloor:Re.value,priority:ze.value,executionMode:Be.value,authorityContract:N}),L=(e,t)=>{He.dataset.tone=e,He.textContent=t},R=()=>{let e=_();A(`pending-count`).textContent=String(e.length);let t=A(`pending-commands`);if(!e.length){t.innerHTML=`<p class="muted">No locally saved commands.</p>`;return}t.innerHTML=e.map(e=>`<article class="task-card"><div><strong>${x(e.title)}</strong><span>${x(e.target_floor)} · ${x(e.priority)} · ${x(e.execution_mode)}</span><small>${x(e.command_id)}</small></div><div class="task-actions"><button data-send="${x(e.command_id)}">Send</button><button data-download="${x(e.command_id)}">Download</button></div></article>`).join(``),t.querySelectorAll(`[data-send]`).forEach(t=>t.addEventListener(`click`,async()=>{let n=e.find(e=>e.command_id===t.dataset.send);if(n)try{let e=await l(n);se(n.command_id),R(),L(`good`,`Desktop accepted ${e.command_id||n.command_id}. Task ${e.task_id??`created`}.`),await z()}catch(e){L(`bad`,e instanceof Error?e.message:`Desktop command failed.`)}})),t.querySelectorAll(`[data-download]`).forEach(t=>t.addEventListener(`click`,()=>{let n=e.find(e=>e.command_id===t.dataset.download);n&&ce(n)}))},We=e=>{let t=A(`desktop-projects`);A(`project-count`).textContent=String(e.length),t.innerHTML=Se(e),Te(t,async(e,t)=>{let n=t.closest(`[data-project-card]`)?.querySelector(`.project-files`);if(n){if(t.getAttribute(`aria-expanded`)===`true`){t.setAttribute(`aria-expanded`,`false`),t.textContent=`Files`,n.hidden=!0;return}t.disabled=!0,t.textContent=`Loading…`,n.hidden=!1,n.innerHTML=`<p class="muted">Reading bounded project metadata…</p>`;try{n.innerHTML=Ce(await p(e)),Ee(n,async(e,t,r)=>{let i=n.querySelector(`.project-file-result`);if(!i)return;let a=window.prompt(`Enter the local owner-confirmation token to open this unredacted read-only preview. It is sent only to the loopback Desktop bridge and is not stored.`,``)??``;if(!a){i.innerHTML=C(`File preview cancelled: owner confirmation is required.`);return}r.disabled=!0,i.innerHTML=`<p class="muted">Opening read-only result…</p>`;try{i.innerHTML=we(await m(e,t,a))}catch(e){i.innerHTML=C(e instanceof Error?e.message:`Project file result is unavailable.`)}finally{r.disabled=!1}}),t.setAttribute(`aria-expanded`,`true`),t.textContent=`Hide files`}catch(e){n.innerHTML=C(e instanceof Error?e.message:`Project files are unavailable.`),t.textContent=`Retry files`}finally{t.disabled=!1}}})},Ge=(e,t)=>{let n=A(`desktop-results`),r=A(`result-auth-state`);r.textContent=t?`Owner gate configured`:`Content gate held`,n.innerHTML=Oe(e,t),Ae(n,async(e,r)=>{let i=n.querySelector(`.result-receipt-detail`);if(!i)return;if(!t){i.innerHTML=T(`Receipt content is held because owner confirmation is not configured on the local bridge.`);return}let a=window.prompt(`Enter the local owner-confirmation token to inspect this unredacted fixed receipt. It is sent only to the loopback Desktop bridge and is not stored.`,``)??``;if(!a){i.innerHTML=T(`Receipt inspection cancelled: owner confirmation is required.`);return}r.disabled=!0,i.innerHTML=`<p class="muted">Opening owner-confirmed read-only receipt…</p>`;try{i.innerHTML=ke(await te(e,a))}catch(e){i.innerHTML=T(e instanceof Error?e.message:`Local result receipt is unavailable.`)}finally{r.disabled=!1}})},Ke=e=>{Ue=e;let t=A(`desktop-reviews`);if(!e.length){t.innerHTML=`<p class="muted">No project receipts are awaiting review.</p>`;return}t.innerHTML=e.slice(0,30).map(e=>{let t=e.state||`pending_review`,n=t===`pending_review`?`<div class="task-actions"><button data-review="${x(e.review_id)}" data-decision="approve">Approve</button><button data-review="${x(e.review_id)}" data-decision="hold">Hold</button><button data-review="${x(e.review_id)}" data-decision="reject">Reject</button></div>`:``;return`<article class="task-card"><div><strong>${x(e.title||`Project receipt`)}</strong><span>${x(t)} · ${x(e.event_type||`receipt`)}</span><small>${x(e.summary||e.review_id)}</small></div>${n}</article>`}).join(``),t.querySelectorAll(`[data-review]`).forEach(e=>e.addEventListener(`click`,async()=>{let t=e.dataset.review||``,n=e.dataset.decision,r=Ue.find(e=>e.review_id===t);if(!r||!t)return;let i=window.prompt(`${n.toUpperCase()}: ${r.title||t}\nOptional decision note:`,``)??``,a=window.prompt(`Enter the local owner-confirmation token. It is sent only to the loopback Desktop bridge and is not stored.`,``)??``;if(!a){L(`bad`,`Review decision cancelled: owner confirmation is required.`);return}try{L(`good`,ie(t,n,await re(t,n,i,a))),await z()}catch(e){L(`bad`,e instanceof Error?e.message:`Review decision failed.`)}}))},qe=e=>{P=e;let t=A(`representation-graphs`);t.innerHTML=Pe(e),t.querySelectorAll(`[data-representation-review]`).forEach(e=>{e.addEventListener(`click`,async()=>{let t=e.dataset.representationReview||``,n=e.dataset.decision,r=e.dataset.scope||`identity`,i=r===`edges`?(e.dataset.edgeIds||``).split(`|`).filter(Boolean).slice(0,100):[],a=P.find(e=>e.review?.review_id===t);if(!t||!a)return;let o=window.prompt(`${n.replace(/_/g,` `).toUpperCase()}: ${a.object.display_name}\n${r===`identity`?`Identity is reviewed before edges.`:`${i.length} bounded edges selected.`}\nOptional decision note:`,``)??``,s=window.prompt(`Enter the local owner-confirmation token. It is sent only to the loopback Desktop bridge and is not stored.`,``)??``;if(!s){L(`bad`,`Representation decision cancelled: owner confirmation is required.`);return}try{await oe(t,n,r,i,o,s),L(`good`,`${t} recorded ${n}; local staging remains noncanonical until Drive readback.`),await z()}catch(e){L(`bad`,e instanceof Error?e.message:`Representation review decision failed.`)}})})};A(`command-form`).addEventListener(`submit`,async e=>{e.preventDefault(),M=null;try{M=I(),L(`warn`,`Sending ${M.command_id} to Desktop…`);let e=await l(M);se(M.command_id),R(),L(`good`,`Accepted by Desktop. Task ${e.task_id??`created`}; ${e.state||`queued for governed processing`}.`),await z()}catch(e){let t=e instanceof o;M&&!t&&v(M),R();let n=e instanceof Error?e.message:`Desktop unavailable`;L(`bad`,t?`${n} Desktop rejected the command; it was not mislabeled as an offline save.`:`${n}${M?` The command envelope was saved locally.`:``}`)}}),A(`save-command`).addEventListener(`click`,()=>{try{M=I(),v(M),R(),L(`good`,`${M.command_id} saved locally.`)}catch(e){L(`bad`,e instanceof Error?e.message:`Command could not be saved.`)}}),A(`copy-command`).addEventListener(`click`,async()=>{try{M=I(),await navigator.clipboard.writeText(JSON.stringify(M,null,2)),L(`good`,`${M.command_id} copied as JSON.`)}catch(e){L(`bad`,e instanceof Error?e.message:`Command could not be copied.`)}});var z=async()=>{let e=A(`desktop-pill`),t=A(`desktop-state`),n=A(`merovingian-state`),r=A(`desktop-pill-text`),i=A(`desktop-tasks`);e.dataset.state=`checking`,r.textContent=`checking local runtime`,t.textContent=`Checking`,n.textContent=`Checking`;try{let a=await c();N=a.authority_contract||null,F(),e.dataset.state=a.ok?`online`:`degraded`,r.textContent=a.ok?`local runtime connected`:`runtime connected; health needs review`,t.textContent=`Online`,n.textContent=a.merovingian?.status===`pass`?`Healthy`:`Degraded`;try{let e=await u();i.innerHTML=e.length?e.map(e=>`<article class="task-card"><div><strong>${x(String(e.title||`Untitled task`))}</strong><span>${x(String(e.status||`unknown`))} · ${x(String(e.priority||`normal`))}</span><small>Task ${x(String(e.id||``))}</small></div></article>`).join(``):`<p class="muted">Desktop queue is clear.</p>`}catch{i.innerHTML=`<p class="muted">Desktop is online, but task listing is unavailable.</p>`}try{We((await d()).projects)}catch{We([])}try{Ke(await ne())}catch{Ke([])}try{Ge(await ee(),a.auth?.configured===!0)}catch(e){A(`result-auth-state`).textContent=a.auth?.configured===!0?`Owner gate configured`:`Content gate held`,A(`desktop-results`).innerHTML=T(e instanceof Error?e.message:`Local result metadata is unavailable.`)}try{qe(await ae())}catch(e){P=[];let t=a.representation_edge?.enabled===!1?`Canonical representation objects are intentionally disabled by the current launch gate.`:e instanceof Error?e.message:`Representation objects are unavailable.`;A(`representation-graphs`).innerHTML=`<article class="panel"><p class="eyebrow">Objects unavailable</p><h2>Feature-gated, not empty</h2><p class="muted">${x(t)}</p></article>`}}catch{N=null,F(),e.dataset.state=`offline`,r.textContent=`start LightSpeed Desktop and the local bridge`,t.textContent=`Offline`,n.textContent=`Offline`,A(`project-count`).textContent=`0`,i.innerHTML=`<p class="muted">Desktop is offline. Commands can still be saved, copied or downloaded.</p>`,A(`desktop-projects`).innerHTML=`<p class="muted">Project registry unavailable while Desktop is offline.</p>`,A(`desktop-reviews`).innerHTML=`<p class="muted">Review queue unavailable while Desktop is offline.</p>`,A(`result-auth-state`).textContent=`Desktop offline`,A(`desktop-results`).innerHTML=`<p class="muted">Fixed local result metadata is unavailable while Desktop is offline.</p>`,qe([])}};A(`refresh-desktop`).addEventListener(`click`,()=>void z()),R(),z();var Je=A(`neo-exchange`),Ye=new URL(`./data/neo_exchange.json`,document.baseURI).toString();ye(async()=>{let e=await fetch(Ye,{cache:`no-store`});if(!e.ok)throw Error(`Neo exchange returned HTTP ${e.status}`);return e.json()}).then(e=>{Je.innerHTML=xe(e)}),document.querySelectorAll(`.tab`).forEach(e=>e.addEventListener(`click`,()=>{document.querySelectorAll(`.tab`).forEach(e=>e.classList.remove(`active`)),document.querySelectorAll(`.view`).forEach(e=>e.classList.remove(`active`)),e.classList.add(`active`),A(`view-${e.dataset.view}`).classList.add(`active`)}));var Xe=new URL(`./data/site_integration.json`,document.baseURI).toString(),Ze=async()=>{try{let e=await fetch(Xe,{cache:`no-store`});return e.ok?await e.json():null}catch{return null}},Qe=()=>{if(document.getElementById(`lsgo-sites-side-edit-styles`))return;let e=document.createElement(`style`);e.id=`lsgo-sites-side-edit-styles`,e.textContent=`
    .site-context-strip { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
    .site-context-strip span { border:1px solid var(--line); border-radius:999px; padding:7px 10px; color:var(--muted); font-size:12px; background:rgba(255,255,255,.025); }
    .site-context-strip strong { color:var(--text); }
    .site-parity-card { border:1px solid var(--line); border-radius:14px; padding:14px; background:rgba(255,255,255,.025); display:grid; gap:8px; }
    .site-parity-card p { margin:0; color:var(--muted); line-height:1.5; }
    .site-parity-card .site-chain { display:flex; flex-wrap:wrap; gap:7px; align-items:center; }
    .site-parity-card .site-chain span { border:1px solid var(--line); border-radius:999px; padding:6px 9px; font-size:12px; }
    .site-parity-card .site-chain i { color:var(--teal); font-style:normal; }
  `,document.head.appendChild(e)},$e=async()=>{let e=document.querySelector(`.topbar > div:first-child`),t=document.querySelector(`#view-sources`);if(!e||!t)return!1;Qe();let n=(await Ze())?.authority_chain??[`Nathaniel Bouwer`,`Achilles / GO gate`,`agent floor`,`LightSpeed Desktop`,`Git and Drive receipts`];if(!document.getElementById(`site-context-strip`)){let t=document.createElement(`div`);t.id=`site-context-strip`,t.className=`site-context-strip`,t.innerHTML=`
      <span><strong>Owner:</strong> Nathaniel Bouwer</span>
      <span><strong>Mode:</strong> private soft launch</span>
      <span><strong>Source:</strong> Git + Drive evidence pending</span>
    `,e.appendChild(t)}if(!document.getElementById(`site-parity-card`)){let e=document.createElement(`article`);e.id=`site-parity-card`,e.className=`panel site-parity-card`,e.innerHTML=`
      <p class="eyebrow">Canonical source chain</p>
      <h2>One operator surface, durable receipts</h2>
      <p>Desktop executes locally, Git carries implementation, Drive carries evidence and review records, and LS GO remains the operator decision surface. Alignment is shown only after current evidence validates.</p>
      <div class="site-chain">
        ${n.map((e,t)=>`${t?`<i>→</i>`:``}<span>${e}</span>`).join(``)}
      </div>
      <p><strong>Launch state:</strong> private local operation. Public Web work remains deferred.</p>
    `,t.prepend(e)}return!0},et=0,tt=()=>{$e().then(e=>{e||et>=40||(et+=1,window.requestAnimationFrame(tt))})};tt();var nt=`lightspeed-cognigrex-os-shell-v0.1`,B=[`command`,`activity`,`objects`,`system`,`sources`],V=[{id:`intake`,label:`Intake`,owner:`Neo`,receipt:`source envelope`,description:`Capture the request, source pointers, project identity, constraints and expected output without inventing missing authority.`},{id:`analyse`,label:`Analyse`,owner:`Neo + Oracle`,receipt:`scope / evidence map`,description:`Resolve knowns, source authority, evidence class, conflicts, privacy and the minimum useful execution path.`},{id:`route`,label:`Commit`,owner:`Neo`,receipt:`stable task / agent route`,description:`Commit one bounded job to the correct specialist floor while retaining stable identity and exact-once transport semantics.`},{id:`workshop`,label:`Workshop`,owner:`specialist floor`,receipt:`artifact / data / result`,description:`Execute the bounded specialist work: code, modelling, evidence extraction, interface work, planning or runtime recovery.`},{id:`proof`,label:`Proof`,owner:`Smith + Morpheus + Oracle`,receipt:`tests / provenance / contradiction`,description:`Test implementation, verify provenance, resolve conflicts and keep hypothesis, inference and empirical evidence distinct.`},{id:`consolidate`,label:`Consolidate`,owner:`Neo + Achilles`,receipt:`canonical delta / supersession`,description:`Return accepted results to the living canonical library as compact deltas, pointers and receipts rather than duplicate masters.`},{id:`release`,label:`Publish-ready`,owner:`Achilles`,receipt:`claim / security / release gate`,description:`Package approved digital artifacts, data and objects for a bounded release candidate. Publish-ready is not automatically published.`}],H=[{floor:`Neo`,short:`N`,role:`Cognigrex operational head: intake, decomposition, routing, cycle control and result aggregation.`,boundary:`May coordinate and reason operationally; cannot self-promote evidence, canon or public claims past Achilles/owner gates.`},{floor:`Oracle`,short:`O`,role:`Sources, evidence retrieval, indexing, known-state and data lineage.`,boundary:`Preserves source authority and uncertainty; duplicate references do not become independent evidence.`},{floor:`Morpheus`,short:`M`,role:`Contradiction, provenance, claim proof, confidence and supersession review.`,boundary:`Reviews and recommends; does not fabricate empirical validation.`},{floor:`Smith`,short:`S`,role:`Code, schemas, deterministic transforms, tests, build and execution receipts.`,boundary:`Changes remain branch/review gated until the applicable execution and release receipts exist.`},{floor:`Architect`,short:`A`,role:`Projects, dependency topology, plans, interfaces and system decomposition.`,boundary:`Uses canonical project identity and pointers rather than spawning competing masters.`},{floor:`TheConstruct`,short:`TC`,role:`Simulation, CAD, meshes, digital twins, derived views and manufacturing-reference artifacts.`,boundary:`Derived models remain labelled and cannot imply physical performance without evidence.`},{floor:`Trinity`,short:`T`,role:`Interface, interaction, visual language, accessibility and communication surfaces.`,boundary:`Presentation cannot elevate claim state or bypass evidence/security classification.`},{floor:`Merovingian`,short:`R`,role:`Runtime health, storage, recovery, resource control, persistence and operational receipts.`,boundary:`Recovery and cleanup are reversible/evidence-gated; no silent deletion or second runtime.`},{floor:`Achilles`,short:`Ω`,role:`Meta-governance, proof thresholds, safety, canonical promotion and release oversight.`,boundary:`Audits and gates the collective; it is not the routine task router inside Cognigrex.`}],U=e=>B.includes(e)?e:`command`,rt=e=>{let t=e.trim().toLowerCase();return t?/\b(publish|release|public[- ]?ready|export|mint|deploy)\b/.test(t)?`release`:/\b(consolidat|canon|supersed|assimil|promot|living library|handoff)\b/.test(t)?`consolidate`:/\b(test|proof|verify|validat|audit|conflict|provenance|claim|confidence)\b/.test(t)?`proof`:/\b(build|code|model|simulate|render|mesh|cad|analyse data|analyze data|workshop|execute|run)\b/.test(t)?`workshop`:/\b(route|delegate|commit|queue|assign|agent|floor)\b/.test(t)?`route`:/\b(source|evidence|research|analyse|analyze|classif|scope|compare|reconcile)\b/.test(t)?`analyse`:`intake`:`intake`},W=e=>{let t=e.trim().toLowerCase();if(!t)return`Neo`;if(/\b(proof|claim|verify|verification|conflict|confidence|audit|contradiction|supersession)\b/.test(t))return`Morpheus`;if(/\b(achilles|governance|canonical promotion|release gate|safety gate)\b/.test(t))return`Achilles`;let n=i(e);return n===`Achilles`?`Neo`:n},it=e=>V.find(t=>t.id===e)??V[0],at=`lightspeed-cognigrex-os-shell-state-v1`,G={activeView:`command`,activeAgent:`Neo`,focusMode:!1},K=(()=>{try{let e=JSON.parse(localStorage.getItem(at)||`{}`),t=H.some(t=>t.floor===e.activeAgent)?e.activeAgent:G.activeAgent;return{activeView:U(e.activeView),activeAgent:t,focusMode:!!e.focusMode}}catch{return{...G}}})(),q=e=>{K={...K,...e},localStorage.setItem(at,JSON.stringify(K))},J=e=>e.replace(/[&<>'"]/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,"'":`&#39;`,'"':`&quot;`})[e]||e),Y=e=>{let t=document.querySelector(`.tab[data-view="${e}"]`);t&&!t.classList.contains(`active`)&&t.click(),q({activeView:e}),document.body.dataset.lsWorkspace=e},X=(e,t=!1)=>{q({activeAgent:e}),document.body.dataset.lsAgent=e,document.querySelectorAll(`[data-ls-agent]`).forEach(t=>{t.dataset.active=t.dataset.lsAgent===e?`true`:`false`});let n=document.getElementById(`target-floor`);n&&(n.value=e),t&&(Y(`command`),document.getElementById(`instruction`)?.focus())},Z=e=>{let t=it(e);document.body.dataset.lsWorkflow=t.id,document.querySelectorAll(`[data-ls-stage]`).forEach(e=>{e.dataset.active=e.dataset.lsStage===t.id?`true`:`false`});let n=document.getElementById(`ls-os-stage-detail`);n&&(n.innerHTML=`<strong>${J(t.label)}</strong><span>${J(t.description)}</span><small>${J(t.owner)} · receipt: ${J(t.receipt)}</small>`)},ot=()=>{let e=document.createElement(`aside`);return e.className=`ls-os-rail`,e.setAttribute(`aria-label`,`Cognigrex agent rail`),e.innerHTML=`
    <button class="ls-os-mark" type="button" data-ls-home title="LightSpeed Cognigrex">LS</button>
    <div class="ls-os-agent-stack">
      ${H.map(e=>`
        <button class="ls-os-agent" type="button" data-ls-agent="${e.floor}" title="${J(e.floor)} — ${J(e.role)}">
          <span>${J(e.short)}</span><small>${J(e.floor)}</small>
        </button>
      `).join(``)}
    </div>
    <button class="ls-os-focus" type="button" data-ls-focus title="Toggle focus mode">◫</button>
  `,e.querySelectorAll(`[data-ls-agent]`).forEach(e=>{e.addEventListener(`click`,()=>X(e.dataset.lsAgent,!0))}),e.querySelector(`[data-ls-home]`)?.addEventListener(`click`,()=>Y(`command`)),e.querySelector(`[data-ls-focus]`)?.addEventListener(`click`,()=>{let e=!K.focusMode;q({focusMode:e}),document.body.dataset.lsFocus=e?`true`:`false`}),e},st=()=>{let e=document.createElement(`section`);return e.className=`ls-os-status-strip`,e.setAttribute(`aria-label`,`LightSpeed operating state`),e.innerHTML=`
    <div><span class="ls-os-status-dot" id="ls-os-runtime-dot"></span><strong id="ls-os-runtime">Desktop checking</strong><small>${t}</small></div>
    <div><span class="ls-os-status-dot stable"></span><strong>Neo operational head</strong><small>specialist-agent orchestration</small></div>
    <div><span class="ls-os-status-dot guarded"></span><strong>Achilles oversight</strong><small>evidence · canon · release gate</small></div>
    <div><span class="ls-os-status-dot private"></span><strong>De Sporte</strong><small>private persistence sidecar · metadata only</small></div>
    <button type="button" id="ls-os-palette-open" title="Open command palette (Ctrl/Cmd+K)">⌘K</button>
  `,e},ct=()=>{let e=document.createElement(`section`);return e.className=`ls-os-workflow`,e.setAttribute(`aria-label`,`ACR3 operating workflow`),e.innerHTML=`
    <div class="ls-os-workflow-track">
      ${V.map((e,t)=>`
        <button type="button" data-ls-stage="${e.id}" title="${J(e.description)}">
          <span>${String(t+1).padStart(2,`0`)}</span><strong>${J(e.label)}</strong><small>${J(e.owner)}</small>
        </button>
      `).join(``)}
    </div>
    <div class="ls-os-stage-detail" id="ls-os-stage-detail"></div>
  `,e.querySelectorAll(`[data-ls-stage]`).forEach(e=>{e.addEventListener(`click`,()=>Z(e.dataset.lsStage))}),e},lt=()=>{let e=document.createElement(`div`);return e.className=`ls-os-palette`,e.id=`ls-os-palette`,e.hidden=!0,e.innerHTML=`
    <div class="ls-os-palette-card" role="dialog" aria-modal="true" aria-label="LightSpeed command palette">
      <div class="ls-os-palette-head"><strong>LightSpeed</strong><span>${nt}</span><button type="button" data-ls-close aria-label="Close">×</button></div>
      <input id="ls-os-palette-input" type="search" autocomplete="off" placeholder="Open workspace, select agent, or route an outcome…" />
      <div id="ls-os-palette-results" class="ls-os-palette-results"></div>
    </div>
  `,e.addEventListener(`click`,t=>{t.target===e&&Q()}),e.querySelector(`[data-ls-close]`)?.addEventListener(`click`,()=>Q()),e.querySelector(`#ls-os-palette-input`)?.addEventListener(`input`,()=>dt()),e},ut=()=>{let e=document.getElementById(`ls-os-palette`);e&&(e.hidden=!1,dt(),window.setTimeout(()=>document.getElementById(`ls-os-palette-input`)?.focus(),0))},Q=()=>{let e=document.getElementById(`ls-os-palette`);e&&(e.hidden=!0)},dt=()=>{let e=document.getElementById(`ls-os-palette-input`),t=document.getElementById(`ls-os-palette-results`);if(!e||!t)return;let n=e.value.trim().toLowerCase(),r=B.filter(e=>!n||e.includes(n)).map(e=>`<button type="button" data-palette-view="${e}"><span>Workspace</span><strong>${e}</strong><small>Open ${e} workspace</small></button>`),i=H.filter(e=>!n||`${e.floor} ${e.role}`.toLowerCase().includes(n)).map(e=>`<button type="button" data-palette-agent="${e.floor}"><span>Agent</span><strong>${J(e.floor)}</strong><small>${J(e.role)}</small></button>`);t.innerHTML=[...n?[`<button type="button" data-palette-route="true"><span>Neo route</span><strong>${J(W(e.value))}</strong><small>Use this text as the command outcome and route it through Cognigrex.</small></button>`]:[],...r,...i].slice(0,14).join(``),t.querySelectorAll(`[data-palette-view]`).forEach(e=>e.addEventListener(`click`,()=>{Y(U(e.dataset.paletteView)),Q()})),t.querySelectorAll(`[data-palette-agent]`).forEach(e=>e.addEventListener(`click`,()=>{X(e.dataset.paletteAgent,!0),Q()})),t.querySelector(`[data-palette-route]`)?.addEventListener(`click`,()=>{let t=e.value.trim(),n=document.getElementById(`instruction`);n&&t&&(n.value=t,n.dispatchEvent(new Event(`input`,{bubbles:!0})),X(W(t)),Z(rt(t)),n.focus()),Y(`command`),Q()})},ft=e=>{let t=e.querySelector(`#view-command .command-panel .panel-head .eyebrow`);t&&(t.textContent=`Neo intake`);let n=e.querySelector(`#view-command .command-panel .panel-head h2`);n&&(n.textContent=`State the outcome`);let r=e.querySelector(`#command-form button.primary[type=submit]`);r&&(r.textContent=`Send to runtime`);let i=e.querySelector(`#view-command .guardrail-panel .eyebrow`);i&&(i.textContent=`Cognigrex operating contract`);let a=e.querySelector(`#view-command .guardrail-panel h2`);a&&(a.textContent=`Neo-led work, durable proof`);let o=e.querySelectorAll(`#view-command .guardrail-panel .compact-list li`),s=[`Neo owns intake, decomposition, routing and aggregate workflow identity.`,`Specialist floors execute only their bounded purpose and return receipts.`,`Oracle, Smith and Morpheus preserve source, implementation and proof boundaries.`,`Achilles governs evidence class, canonical promotion, safety and release.`,`Accepted results return as compact canonical deltas rather than duplicate masters.`];o.forEach((e,t)=>{s[t]&&(e.textContent=s[t])});let c=e.querySelector(`#view-system .flow`);c&&(c.innerHTML=`<span>LS GO</span><i>→</i><span>Neo</span><i>→</i><span>specialist floors</span><i>→</i><span>Morpheus proof</span><i>→</i><span>Achilles gate</span><i>→</i><span>canon / release</span>`);let l=e.querySelector(`#view-system .agent-grid`);if(l){let e=new Map;l.querySelectorAll(`.agent`).forEach(t=>{let n=t.querySelector(`strong`)?.textContent?.trim();n&&e.set(n,t)}),H.forEach(t=>{let n=e.get(t.floor);n&&l.append(n)})}e.querySelectorAll(`.panel-head`).forEach(e=>{if(e.querySelector(`h2`)?.textContent?.trim()!==`Review queue`)return;let t=e.querySelector(`.eyebrow`);t&&(t.textContent=`Achilles / owner gate`)})},pt=()=>{document.querySelectorAll(`.tab[data-view]`).forEach(e=>{e.addEventListener(`click`,()=>{let t=U(e.dataset.view);q({activeView:t}),document.body.dataset.lsWorkspace=t})});let e=document.getElementById(`instruction`),t=document.getElementById(`route-preview`);e?.addEventListener(`input`,()=>{let n=W(e.value);X(n),Z(rt(e.value)),t&&(t.innerHTML=`<strong>Neo route:</strong> ${J(n)} is the primary specialist. Achilles remains the evidence, canonical-promotion and release oversight gate.`)}),document.getElementById(`ls-os-palette-open`)?.addEventListener(`click`,()=>ut())},$=async()=>{let e=document.getElementById(`ls-os-runtime`),t=document.getElementById(`ls-os-runtime-dot`);if(!(!e||!t))try{let n=await c(),r=!!(n.ok&&n.services?.merovingian!==!1);e.textContent=r?`Desktop online`:`Desktop degraded`,t.dataset.state=r?`online`:`degraded`,t.title=n.time_utc?`Last read ${n.time_utc}`:`Local status read`}catch{e.textContent=`Desktop offline / unproved`,t.dataset.state=`offline`,t.title=`No current localhost receipt from this browser.`}};queueMicrotask(()=>{if(document.documentElement.dataset.lsOsShell===`lightspeed-cognigrex-os-shell-v0.1`)return;let e=document.querySelector(`.shell`);if(!e)return;document.documentElement.dataset.lsOsShell=nt,document.body.classList.add(`ls-os-enabled`),document.body.dataset.lsFocus=K.focusMode?`true`:`false`,document.title=`LightSpeed · Cognigrex`,document.body.prepend(ot()),e.prepend(ct()),e.prepend(st()),document.body.append(lt());let t=e.querySelector(`.topbar h1`);t&&(t.textContent=`Cognigrex`);let n=e.querySelector(`.topbar .eyebrow`);n&&(n.textContent=`LightSpeed operating system`);let r=e.querySelector(`.topbar .lede`);r&&(r.textContent=`Neo coordinates specialised purpose agents across intake, workshop execution, proof, canonical consolidation and publish-ready digital artifacts; Achilles governs evidence and release.`),ft(e),pt(),Y(K.activeView),X(K.activeAgent);let i=document.getElementById(`instruction`);i?i.dispatchEvent(new Event(`input`,{bubbles:!0})):(Z(`intake`),X(`Neo`)),$().catch(()=>void 0),window.setInterval(()=>$().catch(()=>void 0),3e4),window.addEventListener(`keydown`,e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()===`k`){e.preventDefault(),ut();return}e.key===`Escape`&&Q(),(e.ctrlKey||e.metaKey)&&/^[1-5]$/.test(e.key)&&(e.preventDefault(),Y(B[Number(e.key)-1]||`command`))})});