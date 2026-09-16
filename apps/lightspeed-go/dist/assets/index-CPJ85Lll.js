(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),e.crossOrigin===`use-credentials`?t.credentials=`include`:e.crossOrigin===`anonymous`?t.credentials=`omit`:t.credentials=`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var e=`lightspeed-go-command-v2`,t=`http://127.0.0.1:8765`,n=(e=>{let n=e?.trim();if(!n)return t;let r;try{r=new URL(n)}catch{throw TypeError(`VITE_LIGHTSPEED_DESKTOP_ORIGIN must be an absolute URL`)}let i=new Set([`127.0.0.1`,`localhost`,`::1`,`[::1]`]).has(r.hostname.toLowerCase());if(r.protocol!==`https:`&&!(r.protocol===`http:`&&i))throw TypeError(`Remote LightSpeed Desktop origins must use HTTPS`);if(r.username||r.password)throw TypeError(`LightSpeed Desktop origins must not contain credentials`);if(r.pathname!==`/`||r.search||r.hash)throw TypeError(`LightSpeed Desktop origins must not contain a path, query or fragment`);return r.origin})(void 0),r=[`Achilles`,`Neo`,`Architect`,`TheConstruct`,`Morpheus`,`Oracle`,`Smith`,`Merovingian`,`Trinity`],i=e=>e?.state===`ready_for_private_relay_verification`?{label:`Verify off-device`,detail:`Private HTTPS origin configured; remote owner flow still needs readback.`}:e?.state===`credential_gate`?{label:`Credential held`,detail:`Complete the owner password change before remote verification.`}:{label:`Local only`,detail:`No private HTTPS relay origin is configured.`},a=(e,t)=>e.replace(/\s+/g,` `).trim().slice(0,t),o=e=>{let t=e.toLowerCase();return/\b(ui|site|web|design|visual|layout|canva|accessibility)\b/.test(t)?`Trinity`:/\b(git|github|code|build|commit|branch|deploy|schema|api|runtime)\b/.test(t)?`Smith`:/\b(source|evidence|research|data|document|drive|sheet|workbook|citation)\b/.test(t)?`Oracle`:/\b(proof|claim|verify|conflict|confidence|audit)\b/.test(t)?`Morpheus`:/\b(simulate|simulation|model|gmat|trajectory|twin|physics)\b/.test(t)?`TheConstruct`:/\b(plan|mission|architecture|dependency|roadmap|system|project)\b/.test(t)?`Architect`:/\b(health|status|diagnostic|failure|error|monitor|storage|cleanup|archive)\b/.test(t)?`Merovingian`:/\b(coordinate|queue|handoff|agent|task|execute|run)\b/.test(t)?`Neo`:`Achilles`},s=t=>{let n=a(t.instruction,4e3);if(!n)throw TypeError(`instruction is required`);let r=new Date().toISOString(),i=Math.random().toString(36).slice(2,8).toUpperCase(),s=t.targetFloor??o(n),c=t.authorityContract;if(!c)throw TypeError(`Desktop authority contract is not available`);let l=a(c.canonical_gate_id,160),u=a(c.owner_decision_ref,160),d=a(c.core_acceptance_ref,160),f=a(c.approval_or_hold_state,40).toLowerCase(),p=a(c.authorised_scope,1e3),m=a(c.prohibited_scope,1e3);if(!l||!u||!d||!p||!m)throw TypeError(`Desktop authority contract is incomplete`);if(![`approve`,`approved`,`operator_approved`,`operator_authorized`,`operator_authorised`].includes(f))throw TypeError(`Desktop authority contract is held`);let h=t.executionMode??`review`;return{schema_version:e,command_id:`LSGO-${r.replace(/\D/g,``).slice(0,14)}-${i}`,created_utc:r,source:`LS GO`,title:a(t.title||n,160),instruction:n,target_floor:s,oversight_floor:`Achilles`,priority:t.priority??`normal`,execution_mode:h,action_type:t.actionType??`cognigrex_workflow`,proof_required:!0,public_safe:!0,canonical_gate_id:l,owner_decision_ref:u,core_acceptance_ref:d,approval_or_hold_state:f,authorised_scope:p,prohibited_scope:m,requested_scope:`${s} private local ${h} queue`}},c=class extends Error{status;constructor(e,t){super(t),this.name=`DesktopRequestError`,this.status=e}},l=async(e,t,n=3500)=>{let r=new AbortController,i=window.setTimeout(()=>r.abort(),n);try{let n=await fetch(e,{...t,signal:r.signal,cache:`no-store`});if(!n.ok){let e=`Desktop returned HTTP ${n.status}`;try{let t=await n.json();t.detail&&(e=t.detail)}catch{}throw new c(n.status,e)}return await n.json()}finally{window.clearTimeout(i)}},u=(e=n)=>l(`${e}/api/v1/status`,{method:`GET`},1e4),d=(e,t,r=n)=>l(`${r}/api/v1/auth/login`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({username:a(e,64),password:t.slice(0,1024)})},15e3),f=(e,t,r,i,o,s=n)=>l(`${s}/api/v1/auth/change-password`,{method:`POST`,headers:{"Content-Type":`application/json`,[o?`X-LightSpeed-Password-Change`:`X-LightSpeed-Session`]:i.slice(0,256)},body:JSON.stringify({username:a(e,64),current_password:t.slice(0,1024),new_password:r.slice(0,1024)})},2e4),p=(e,t=n)=>l(`${t}/api/v1/auth/logout`,{method:`POST`,headers:{"X-LightSpeed-Session":e.slice(0,256)}},7e3),m=(e,t=n)=>l(`${t}/api/v1/ls-go/commands`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify(e)},7e3),h=async(e=n)=>{let t=await l(`${e}/api/v1/tasks?limit=12`,{method:`GET`});return Array.isArray(t.tasks)?t.tasks:[]},ee=async(e=n)=>{let t=await l(`${e}/api/v1/projects`,{method:`GET`},15e3);return{projects:Array.isArray(t.projects)?t.projects:[],summary:t.summary||{},duplicateNames:Array.isArray(t.duplicate_names)?t.duplicate_names:[],cleanupSummary:t.cleanup_summary||{}}},te=(e,t)=>{let n=encodeURIComponent(e);return t===void 0?`/api/v1/projects/${n}/files`:`/api/v1/projects/${n}/files/${t.split(`/`).map(e=>encodeURIComponent(e)).join(`/`)}`},ne=async(e,t=n)=>l(`${t}${te(e)}?limit=200`,{method:`GET`},15e3),re=async(e,t,r,i=n)=>l(`${i}${te(e,t)}`,{method:`GET`,headers:{"X-LightSpeed-Session":r.slice(0,256)}},1e4),ie=e=>e===void 0?`/api/v1/results`:`/api/v1/results/${encodeURIComponent(e)}`,ae=async(e=n,t=50)=>l(`${e}${ie()}?limit=${Math.max(1,Math.min(t,200))}`,{method:`GET`},1e4),oe=async(e,t,r=n)=>l(`${r}${ie(e)}`,{method:`GET`,headers:{"X-LightSpeed-Session":t.slice(0,256)}},1e4),se=async(e=n,t=50)=>{let r=await l(`${e}/api/v1/reviews?limit=${Math.max(1,Math.min(t,200))}`,{method:`GET`},1e4);return Array.isArray(r.reviews)?r.reviews:[]},ce=async(e,t,r=``,i=``,o=n)=>l(`${o}/api/v1/reviews/${encodeURIComponent(e)}/decision`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":i.slice(0,256)},body:JSON.stringify({decision:t,note:a(r,1e3)})},7e3),le=(e,t,n)=>{let r=n.receipt?.drive_writeback_mode;return r===`owner_approved_exact_drive_target`?`${e} marked ${t}. Owner-approved Drive decision receipt written by Desktop.`:r===`local_outbox_pending_drive_sync`?`${e} marked ${t}. Local outbox receipt staged; Drive sync remains pending.`:`${e} marked ${t}. Decision receipt recorded; destination requires verification.`},ue=async(e=n)=>{let t=await l(`${e}/api/v1/representation-graphs`,{method:`GET`},15e3);return Array.isArray(t.graphs)?t.graphs:[]},de=async(e,t,r,i=[],o=``,s=``,c=n)=>l(`${c}/api/v1/representation-reviews/${encodeURIComponent(e)}/decision`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":s.slice(0,256)},body:JSON.stringify({decision:t,scope:r,edge_ids:i.slice(0,100),note:a(o,1e3)})},1e4),g=`lightspeed-go-pending-commands-v1`,_=()=>{try{let e=JSON.parse(localStorage.getItem(g)||`[]`);return Array.isArray(e)?e:[]}catch{return[]}},fe=e=>{let t=[e,..._().filter(t=>t.command_id!==e.command_id)].slice(0,30);return localStorage.setItem(g,JSON.stringify(t)),t},pe=e=>{let t=_().filter(t=>t.command_id!==e);return localStorage.setItem(g,JSON.stringify(t)),t},me=e=>{let t=new Blob([JSON.stringify(e,null,2)],{type:`application/json`}),n=URL.createObjectURL(t),r=document.createElement(`a`);r.href=n,r.download=`${e.command_id}.json`,r.click(),URL.revokeObjectURL(n)},he=`lightspeed-neo-exchange-v1`,ge=[`critical`,`high`,`normal`,`low`],_e=[`queued`,`active`,`review`,`blocked`,`complete`],ve=[`icon`,`age_label`],v=e=>typeof e==`object`&&!!e&&!Array.isArray(e),y=(e,t,n)=>{if(typeof e!=`string`)return t;let r=e.replace(/\s+/g,` `).trim();return r?r.slice(0,n):t},ye=(e,t,n)=>{let r=y(e,``,n);if(!r)throw TypeError(`queue record ${t} is required`);return r},be=(e,t,n)=>typeof e==`string`&&t.includes(e)?e:n,xe=e=>v(e)?Object.fromEntries(ve.flatMap(t=>{let n=y(e[t],``,48);return n?[[t,n]]:[]})):{},Se=e=>{if(!v(e))throw TypeError(`queue record must be an object`);return{id:ye(e.id,`id`,80),title:ye(e.title,`title`,160),priority:be(e.priority,ge,`normal`),status:be(e.status,_e,`queued`),source:y(e.source,`GO Gate`,48),target:y(e.target,`Neo`,48),created_utc:y(e.created_utc,``,32),extensions:xe(e.extensions),notes:y(e.notes,``,240)}},Ce=e=>{if(!v(e))throw TypeError(`Neo exchange must be an object`);let t=Array.isArray(e.queue)?e.queue.map(Se):[];return{schema_version:he,generated_at_utc:y(e.generated_at_utc,``,32),queue:t}},we=e=>({total:e.queue.length,critical:e.queue.filter(e=>e.priority===`critical`).length,active:e.queue.filter(e=>e.status!==`complete`).length,complete:e.queue.filter(e=>e.status===`complete`).length}),b=e=>e.replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#039;`})[e]??e),Te=async e=>{try{return Ce(await e())}catch{return Ce({})}},Ee=e=>e.status===`blocked`?`blocked`:e.status===`complete`?`pass`:e.priority===`critical`||e.priority===`high`?`warn`:`ready`,De=e=>{let t=we(e),n=e.queue.length?e.queue.map(e=>`
            <li class="status-row ${Ee(e)}">
              <div>
                <strong>${b(e.title)}</strong>
                <span>${b(e.source)} to ${b(e.target)} · ${b(e.id)}</span>
                ${e.notes?`<small>${b(e.notes)}</small>`:``}
              </div>
              <em>${b(e.status)}</em>
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
  `},x=e=>{let t=Number(e||0);return t<1024?`${t} B`:t<1024**2?`${(t/1024).toFixed(1)} KB`:t<1024**3?`${(t/1024**2).toFixed(1)} MB`:`${(t/1024**3).toFixed(1)} GB`},Oe=e=>e.length?e.slice(0,30).map(e=>{let t=e.file_browser?.state??(e.authority===`external_reference`?`restricted`:void 0),n=!t||t===`available`,r=t&&t!==`available`?` · ${b(e.file_browser?.reason||`External references remain metadata-only until the bridge confirms bounded access.`)}`:``,i=n?`<button type="button" data-project-files="${b(e.project_id)}" aria-expanded="false">Files</button>`:`<small class="project-file-access">Files ${t===`restricted`?`held`:`unavailable`}</small>`;return`
    <article class="task-card project-card" data-project-card="${b(e.project_id)}">
      <div class="project-summary">
        <strong>${b(e.name)}</strong>
        <span>${b(e.condition||`unknown`)} · ${b(e.authority||`reference`)} · ${e.file_count||0} files</span>
        <small>${x(e.size_bytes)}${e.scan_truncated?` · bounded scan`:``}${r}</small>
      </div>
      <div class="task-actions">
        ${i}
      </div>
      <div class="project-files" aria-live="polite" hidden></div>
    </article>
  `}).join(``):`<p class="muted">No project folders were found in the configured roots.</p>`,ke=e=>{let t=e.summary,n=`<p class="project-file-boundary">${b(e.boundary)}</p>`;if(!e.files.length){let t=e.state===`restricted`?`No files are visible; credential-like or excluded runtime files are withheld.`:`This registered project currently has no visible files.`;return`<div class="project-files-head"><strong>Files</strong><small>${b(e.project.authority||`reference`)} authority</small></div><p class="muted">${t}</p>${n}`}let r=e.files.map(t=>`
    <article class="project-file-row">
      <div><strong>${b(t.relative_path)}</strong><small>${b(t.mime_type)} · ${x(t.size_bytes)}</small></div>
      <button type="button" data-project-file="${b(t.relative_path)}" data-project-id="${b(e.project.project_id)}">Open</button>
    </article>
  `).join(``),i=t.scan_truncated?` · bounded result`:``;return`
    <div class="project-files-head"><strong>Files</strong><small>${t.visible_file_count} visible · ${t.blocked_file_count} withheld${i}</small></div>
    <div class="project-file-list">${r}</div>
    <div class="project-file-result" aria-live="polite"></div>
    ${n}
  `},S=e=>`
  <div class="project-files-head"><strong>Files unavailable</strong></div>
  <p class="result" data-tone="bad">${b(e)}</p>
`,Ae=e=>{let t=e.preview,n=`<p class="muted">Metadata only. Binary or non-UTF-8 content is not transferred into LS GO.</p>`;return t.state===`empty`?n=`<p class="muted">The file is empty.</p>`:t.state===`available`&&(n=`<pre>${b(t.text||``)}</pre>${t.truncated?`<small class="muted">Preview truncated at the governed byte limit.</small>`:``}`),`
    <section class="project-file-preview">
      <div class="project-files-head"><strong>${b(e.file.relative_path)}</strong><small>${b(e.file.mime_type)} · ${x(e.file.size_bytes)}</small></div>
      ${n}
      <p class="project-file-boundary">${b(e.boundary)}</p>
    </section>
  `},je=(e,t)=>{e.querySelectorAll(`[data-project-files]`).forEach(e=>{e.addEventListener(`click`,()=>{let n=e.dataset.projectFiles||``;n&&t(n,e)})})},Me=(e,t)=>{e.querySelectorAll(`[data-project-file][data-project-id]`).forEach(e=>{e.addEventListener(`click`,()=>{let n=e.dataset.projectId||``,r=e.dataset.projectFile||``;n&&r&&t(n,r,e)})})},Ne=e=>{let t=Number(e||0);return t<1024?`${t} B`:t<1024**2?`${(t/1024).toFixed(1)} KB`:`${(t/1024**2).toFixed(1)} MB`},Pe=e=>{let t=String(e.status||`unknown`).toLowerCase();return[`complete`,`completed`,`pass`,`passed`].includes(t)?`good`:[`blocked`,`failed`,`error`].includes(t)?`bad`:`warn`},Fe=(e,t)=>{let n=e.summary,r=`<p class="result-receipt-boundary">${b(e.boundary)}</p>`,i=t?`Exact receipt content requires the local owner-confirmation token.`:`Content inspection is held because the local owner-confirmation token is not configured.`;if(!e.results.length)return`<p class="muted">${e.state===`restricted`?`No eligible fixed receipts are visible; invalid receipt objects remain withheld.`:`No fixed local result receipts have been written yet.`}</p><p class="result-receipt-auth">${i}</p>${r}`;let a=e.results.map(e=>{let n=e.action_type||`untyped`,r=e.target_floor||`floor unknown`,i=e.completed_utc||e.created_utc||e.modified_utc,a=[e.task_id==null?null:`Task ${e.task_id}`,e.job_id==null?null:`Job ${e.job_id}`,e.command_id||null].filter(Boolean).join(` · `),o=t?``:` disabled aria-disabled="true"`;return`
      <article class="task-card result-receipt-card" data-result-state="${Pe(e)}">
        <div>
          <strong>${b(e.result_id)}</strong>
          <span>${b(e.status)} · ${b(n)} · ${b(r)}</span>
          <small>${b(a||`No task/job identity`)} · ${b(i||`time unavailable`)} · ${Ne(e.size_bytes)}</small>
        </div>
        <div class="task-actions">
          <button type="button" data-result-receipt="${b(e.result_id)}"${o}>Inspect receipt</button>
        </div>
      </article>
    `}).join(``),o=n.truncated?` · bounded index`:``;return`
    <div class="result-receipt-summary"><span>${n.visible_result_count} visible${o}</span><span>${n.invalid_file_count} invalid withheld</span></div>
    <div class="result-receipt-list">${a}</div>
    <div class="result-receipt-detail" aria-live="polite"></div>
    <p class="result-receipt-auth">${b(i)}</p>
    ${r}
  `},Ie=e=>{let t=JSON.stringify(e.result,null,2);return`
    <section class="result-receipt-preview">
      <div class="result-receipt-preview-head">
        <strong>${b(e.identity.result_id)}</strong>
        <small>${Ne(e.identity.size_bytes)} · SHA-256 ${b(e.identity.sha256)}</small>
      </div>
      <pre>${b(t)}</pre>
      <p class="result-receipt-boundary">${b(e.boundary)}</p>
    </section>
  `},C=e=>`
  <p class="result" data-tone="bad">${b(e)}</p>
`,Le=(e,t)=>{e.querySelectorAll(`[data-result-receipt]`).forEach(e=>{e.addEventListener(`click`,()=>{let n=e.dataset.resultReceipt||``;n&&!e.disabled&&t(n,e)})})},w=e=>String(e??``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),T=e=>e?`${e.slice(0,12)}…${e.slice(-8)}`:`not available`,Re=e=>e.path_exposed===!1?String(e.label||`private local evidence`):[e.repository,e.commit_sha?`commit ${String(e.commit_sha).slice(0,12)}`:null,e.path,e.drive_file_id?`Drive ${e.drive_file_id}`:null,e.sheet_name,e.stable_key||e.content_key,e.missing_state].filter(Boolean).map(w).join(` · `)||w(e.locator_type||`logical`),ze=e=>w(JSON.stringify(e,null,2)),Be=e=>{let t=e.representations.filter(e=>e.state===`active`).length,n=e.missing.length;return!t&&n?`unable to determine`:n>t?`smaller bowl`:t>n?`larger bowl`:`unchanged bowl`},Ve=e=>{let t=e.review,n=t?.review_stage||`identity`,r=e.edges.map(e=>e.edge_id).join(`|`),i=t?`
    <div class="graph-actions" data-review-stage="${w(n)}">
      <strong>${n===`identity`?`Review identity first`:`Review ${e.edges.length} bounded edges`}</strong>
      <div class="task-actions">
        <button data-representation-review="${w(t.review_id)}" data-scope="${n}" data-edge-ids="${w(r)}" data-decision="approve">Approve</button>
        <button data-representation-review="${w(t.review_id)}" data-scope="${n}" data-edge-ids="${w(r)}" data-decision="provisional_approve">Provisional</button>
        <button data-representation-review="${w(t.review_id)}" data-scope="${n}" data-edge-ids="${w(r)}" data-decision="hold">Hold</button>
        <button data-representation-review="${w(t.review_id)}" data-scope="${n}" data-edge-ids="${w(r)}" data-decision="request_evidence">Request evidence</button>
        <button data-representation-review="${w(t.review_id)}" data-scope="${n}" data-edge-ids="${w(r)}" data-decision="reject">Reject</button>
        <button data-representation-review="${w(t.review_id)}" data-scope="${n}" data-edge-ids="${w(r)}" data-decision="supersede">Supersede</button>
      </div>
      <small>${w(t.state)} · graph ${T(t.graph_sha256)}</small>
    </div>`:`<p class="muted">Review packet has not been staged.</p>`,a=e.representations.map(e=>`
    <tr>
      <td><strong>${w(e.representation_type)}</strong><small>${w(e.representation_id)}</small></td>
      <td>${Re(e.locator)}</td>
      <td>${w(e.source_authority)}</td>
      <td>${T(e.content_sha256)}</td>
      <td>${w(e.confidence_class)} (${Math.round(e.confidence_numeric*100)}%)</td>
      <td><span class="state-chip" data-state="${w(e.state)}">${w(e.state)}</span></td>
      <td>${w(e.claim_boundary)}</td>
    </tr>`).join(``),o=e.edges.map(e=>`
    <tr>
      <td>${w(e.from_representation_id)}</td>
      <td><strong>${w(e.relation)}</strong></td>
      <td>${w(e.to_representation_id)}</td>
      <td>${w(e.evidence_bundle_id||`not required`)}</td>
      <td>${w(e.review_state)}</td>
      <td>${w(e.claim_boundary)}</td>
    </tr>`).join(``),s=e.missing.length?e.missing.map(e=>`
      <article class="missing-card">
        <strong>${w(e.type)} · ${w(e.missing_state)}</strong>
        <span><b>Why:</b> ${w(e.reason)}</span>
        <span><b>Next:</b> ${w(e.next_evidence_action)}</span>
        <small>Last search: ${w(e.last_search||`not recorded`)} · Floor: ${w(e.assigned_floor)} · Effect: ${w(e.dependency_effect)}</small>
      </article>`).join(``):`<p class="muted">No required representation is currently missing.</p>`,c=e.conflicts.length?e.conflicts.map(e=>`<article class="missing-card conflict"><strong>${w(e.edge_id)}</strong><span>${w(e.claim_boundary)}</span></article>`).join(``):`<p class="muted">No representation conflict is recorded.</p>`,l=e.horizons.length?e.horizons.map(e=>`
      <article class="horizon-card">
        <div><strong>${w(e.name)}</strong><span>${w(e.state)} · ${w(e.horizon_type)}</span></div>
        <p>${w(e.objective)}</p>
        <details><summary>Assumptions and constraints</summary><pre>${ze({assumptions:e.assumptions,constraints:e.constraints})}</pre></details>
        <small>Input ${T(e.input_set_sha256)}</small>
      </article>`).join(``):`<p class="muted">No horizon is assigned.</p>`,u=e.representations.find(e=>e.representation_type===`recommendation`)?.locator.next_highest_value_question,d=(e.linked_objects||[]).length?(e.linked_objects||[]).map(t=>{let n=(e.linked_identifiers||[]).filter(e=>e.object_id===t.object_id).map(e=>`${e.namespace}: ${e.identifier_value}`).join(` | `);return`<article class="missing-card">
        <strong>${w(t.display_name)} · ${w(t.state)}</strong>
        <span><b>Object:</b> ${w(t.object_id)}</span>
        <span><b>Identifiers:</b> ${w(n||`none recorded`)}</span>
      </article>`}).join(``):`<p class="muted">No linked object identity is included.</p>`,f=(e.evidence_bundles||[]).length?(e.evidence_bundles||[]).map(e=>`
      <article class="horizon-card">
        <div><strong>${w(e.title)}</strong><span>${w(e.state)}</span></div>
        <p>${w(e.claim_boundary)}</p>
        <small>${e.independence_group_count} independence groups · ${e.duplicate_reference_count} duplicate references · confidence effect ${e.confidence_effect}</small>
        <details><summary>Source weight summary</summary><pre>${ze(e.source_weight_summary)}</pre></details>
      </article>`).join(``):`<p class="muted">No evidence bundle is linked.</p>`;return`
    <article class="panel graph-panel" data-object-id="${w(e.object.object_id)}">
      <div class="panel-head">
        <div>
          <p class="eyebrow">${w(e.object.object_type)}</p>
          <h2>${w(e.object.display_name)}</h2>
          <p>${w(e.object.description)}</p>
        </div>
        <span class="badge">${w(e.canonical_state)}</span>
      </div>
      <div class="graph-summary">
        <div><span>Object ID</span><strong>${w(e.object.object_id)}</strong></div>
        <div><span>Authority</span><strong>${w(e.object.authority)}</strong></div>
        <div><span>Identity</span><strong>${w(e.object.identity_confidence_class)} · ${Math.round(e.object.identity_confidence_numeric*100)}%</strong></div>
        <div><span>Current horizon</span><strong>${w(e.horizons[0]?.name||`not assigned`)}</strong></div>
        <div><span>Judgment</span><strong>${Be(e)}</strong></div>
      </div>
      <details open><summary>Identifiers (${e.identifiers.length})</summary><div class="identifier-list">${e.identifiers.map(e=>`<span><strong>${w(e.namespace)}</strong>${w(e.identifier_value)} · ${w(e.authority)}</span>`).join(``)}</div></details>
      <details open><summary>Linked identities (${(e.linked_objects||[]).length})</summary><div class="graph-grid">${d}</div></details>
      <details open><summary>Representations (${e.representations.length})</summary><div class="table-scroll"><table class="graph-table"><thead><tr><th>Type</th><th>Locator</th><th>Authority</th><th>Hash/revision</th><th>Confidence</th><th>State</th><th>Claim boundary</th></tr></thead><tbody>${a}</tbody></table></div></details>
      <details open><summary>Edges (${e.edges.length})</summary><div class="table-scroll"><table class="graph-table"><thead><tr><th>Source</th><th>Relation</th><th>Destination</th><th>Evidence</th><th>Review</th><th>Boundary</th></tr></thead><tbody>${o}</tbody></table></div></details>
      <details open><summary>Evidence bundles (${(e.evidence_bundles||[]).length})</summary>${f}</details>
      <div class="graph-grid">
        <section><h3>Missing</h3>${s}</section>
        <section><h3>Conflicts</h3>${c}</section>
      </div>
      <section><h3>Horizon</h3>${l}</section>
      <div class="next-question"><strong>Next highest-value question</strong><span>${w(u||`Owner review determines the next bounded question.`)}</span></div>
      ${i}
    </article>`},He=e=>e.length?e.map(Ve).join(``):`<article class="panel"><p class="muted">The feature-gated representation edge is disabled or unavailable.</p></article>`,Ue=[[`LightSpeed Git`,`https://github.com/achillesromer-coder/LightSpeed`,`Versioned implementation and receipts`],[`Type 1 Digital Review`,`https://github.com/achillesromer-coder/LightSpeed/pull/46`,`Draft 3D, six-view and T1-00..07 review packages`],[`Type 1 Römer Canon`,`https://docs.google.com/spreadsheets/d/1refNFmebTcmPVojCuZsyILJEWaKz-sVzYLfZtqMl8k8/edit`,`Living programme, evidence, handoff and release gates`],[`ACR3 Handoffs`,`https://docs.google.com/spreadsheets/d/1AgAhLPNtrO91C_-ea7EdOkOsyXrCCYvFVvmDSGq8uls/edit`,`Append-only cross-corpus reconciliation receipts`],[`LS GO Queue`,`https://docs.google.com/spreadsheets/d/1f5i4V3FshYHkztv3_HAg0ZofUl0sdcJZcwrlesUlCfM/edit`,`Phone tasks, approvals, commands, results and sync health`],[`Portfolio Handoff`,`https://docs.google.com/document/d/1tsDkb79UVX_SqS2-oBgc5DHb89QIlH3DcmKMN77hdOo/edit`,`Cross-chat portfolio continuity`],[`Römer Industries`,`https://romer.industries`,`Reviewed public portfolio surface`]],We=[{name:`Central Facility Boundary`,radiusM:2500,description:`All facilities and buildings remain inside this radius.`},{name:`Active Eco-Restoration`,radiusM:3500,description:`1 km active band for managed biome, native rehabilitation, and functional climate pockets.`},{name:`Passive Eco-Restoration`,radiusM:11e3,description:`Outer passive restoration reserve securing the full radial print.`}],Ge=[{id:`integration-hall`,name:`Integration Hall`,footprint:`40 m x 75 m, 22 m clear`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Starship-compatible roller doors both ends; single bridge crane spans the hall.`},{id:`chainhill`,name:`ChainHill Relay`,footprint:`~225-250 m relay length`,elevation:`flat raised concrete, approximately 3 m above water table`,releaseStatus:`bounded-assumption`,notes:`Incoming and outgoing tracks oppose each other with two anti-parallel internal lines.`},{id:`x-pads`,name:`X-Layout Pads`,footprint:`solid pads, no beveled building base`,elevation:`pad-specific hardstand`,releaseStatus:`canonical`,notes:`Flame/exhaust outlets orient away from central node and buildings.`},{id:`mission-control`,name:`Mission Control / ATC`,footprint:`pentagon base, level 1 at 80%, four-storey tower`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Foyer, cafeteria, meeting, offices, emergency access, elevator, and top operating floor.`},{id:`living-rd`,name:`R&D + Living Quarters`,footprint:`room-level workbook detail pending`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`known-unknown`,notes:`FIFO and FIFO+family support with ground community and rooftop lifestyle zones.`}],Ke=[`site_zones`,`facilities`,`rooms_spaces`,`roads_tracks`,`pads_exhaust`,`eco_restoration`,`standards_evidence`,`viewer_toggles`,`known_unknowns`],qe=document.getElementById(`app`);if(!qe)throw Error(`LightSpeed Go mount node #app not found.`);qe.innerHTML=`
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
              <label class="field"><span>Route</span><select id="target-floor">${r.map(e=>`<option value="${e}">${e}</option>`).join(``)}</select></label>
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
        <article class="metric"><span>Desktop API</span><strong id="desktop-state">Checking</strong><small>${n}</small></article>
        <article class="metric"><span>Merovingian</span><strong id="merovingian-state">Checking</strong><small>database · storage · health</small></article>
        <article class="metric"><span>Projects</span><strong id="project-count">0</strong><small>Desktop-visible project roots</small></article>
        <article class="metric"><span>Remote review</span><strong id="remote-access-state">Checking</strong><small id="remote-access-detail">private relay gate</small></article>
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
        <article class="panel"><p class="eyebrow">Existing twin context</p><h2>Spaceport contract retained</h2><p class="muted">${We.length} zones · ${Ge.length} facility records · ${Ke.length} workbook tabs. The twin remains bounded context, not the command-centre homepage.</p></article>
      </div>
    </section>

    <section class="view" id="view-sources">
      <div class="source-grid">${Ue.map(([e,t,n])=>`<a class="source-card" href="${t}" target="_blank" rel="noreferrer"><strong>${e}</strong><span>${n}</span><em>Open ↗</em></a>`).join(``)}</div>
      <article class="panel"><p class="eyebrow">Authority order</p><h2>Where each truth lives</h2><div class="authority-grid"><div><strong>Drive</strong><span>evidence, workbooks and review receipts</span></div><div><strong>Git</strong><span>code, schemas, tests and implementation receipts</span></div><div><strong>Desktop</strong><span>projects, local execution, state and jobs</span></div><div><strong>LS GO</strong><span>owner commands, review and bounded decisions</span></div></div></article>
    </section>
  </main>
`;var E=e=>{let t=document.getElementById(e);if(!t)throw Error(`Missing #${e}`);return t},D=E(`instruction`),Je=E(`target-floor`),Ye=E(`priority`),Xe=E(`execution-mode`),Ze=E(`route-preview`),Qe=E(`command-result`),O=null,k=null,$e=[],A=[],j=``,M=``,N=`NCNB`,P=(e,t)=>{let n=E(`owner-auth-result`);n.dataset.tone=e,n.textContent=t},et=e=>{let t=E(`owner-login-form`),n=E(`owner-change-form`),r=E(`owner-logout`);if(N=e.credential?.username||N,j=e.session_token||``,M=e.password_change_token||``,E(`owner-password`).value=``,e.authenticated&&j){n.hidden=!0,r.hidden=!1,E(`owner-auth-state`).textContent=`${N} signed in`,P(`good`,`Owner session active until ${e.expires_utc||`page close`}.`);return}r.hidden=!0,n.hidden=!e.change_required,t.hidden=!1,E(`owner-auth-state`).textContent=e.change_required?`Password change required`:`Sign-in required`,P(`warn`,e.change_required?`The bootstrap password was verified. Enter it again with a new password to complete first login.`:`Owner sign-in is required for unredacted files, receipts, and decisions.`)},F=()=>j||(P(`warn`,`Sign in as NCNB before performing this owner-gated action.`),``);E(`owner-login-form`).addEventListener(`submit`,async e=>{e.preventDefault();let t=E(`owner-username`).value.trim(),n=E(`owner-password`);try{et(await d(t,n.value))}catch(e){n.value=``,P(`bad`,e instanceof Error?e.message:`Owner sign-in failed.`)}}),E(`owner-change-form`).addEventListener(`submit`,async e=>{e.preventDefault();let t=E(`owner-current-password`),n=E(`owner-new-password`),r=E(`owner-confirm-password`);if(n.value!==r.value){P(`bad`,`The new passwords do not match.`);return}let i=M||j;if(!i){P(`bad`,`Sign in before changing the password.`);return}try{let e=await f(N,t.value,n.value,i,!!M);t.value=``,n.value=``,r.value=``,et(e)}catch(e){t.value=``,n.value=``,r.value=``,P(`bad`,e instanceof Error?e.message:`Password change failed.`)}}),E(`owner-logout`).addEventListener(`click`,async()=>{let e=j;if(j=``,M=``,e)try{await p(e)}catch{}E(`owner-logout`).hidden=!0,E(`owner-auth-state`).textContent=`Signed out`,P(`warn`,`Owner session cleared from this page.`)});var I=()=>{let e=o(D.value||`governance`);Je.value=e;let t=k?.canonical_gate_id;Ze.innerHTML=`<strong>Achilles route:</strong> ${e} is primary. Neo coordinates and proof returns to this gate.${t?` <small>Authority: ${b(t)}</small>`:` <small>Waiting for the Desktop authority contract.</small>`}`};D.addEventListener(`input`,I),I();var L=()=>s({instruction:D.value,targetFloor:Je.value,priority:Ye.value,executionMode:Xe.value,authorityContract:k}),R=(e,t)=>{Qe.dataset.tone=e,Qe.textContent=t},z=()=>{let e=_();E(`pending-count`).textContent=String(e.length);let t=E(`pending-commands`);if(!e.length){t.innerHTML=`<p class="muted">No locally saved commands.</p>`;return}t.innerHTML=e.map(e=>`<article class="task-card"><div><strong>${b(e.title)}</strong><span>${b(e.target_floor)} · ${b(e.priority)} · ${b(e.execution_mode)}</span><small>${b(e.command_id)}</small></div><div class="task-actions"><button data-send="${b(e.command_id)}">Send</button><button data-download="${b(e.command_id)}">Download</button></div></article>`).join(``),t.querySelectorAll(`[data-send]`).forEach(t=>t.addEventListener(`click`,async()=>{let n=e.find(e=>e.command_id===t.dataset.send);if(n)try{let e=await m(n);pe(n.command_id),z(),R(`good`,`Desktop accepted ${e.command_id||n.command_id}. Task ${e.task_id??`created`}.`),await V()}catch(e){R(`bad`,e instanceof Error?e.message:`Desktop command failed.`)}})),t.querySelectorAll(`[data-download]`).forEach(t=>t.addEventListener(`click`,()=>{let n=e.find(e=>e.command_id===t.dataset.download);n&&me(n)}))},tt=e=>{let t=E(`desktop-projects`);E(`project-count`).textContent=String(e.length),t.innerHTML=Oe(e),je(t,async(e,t)=>{let n=t.closest(`[data-project-card]`)?.querySelector(`.project-files`);if(n){if(t.getAttribute(`aria-expanded`)===`true`){t.setAttribute(`aria-expanded`,`false`),t.textContent=`Files`,n.hidden=!0;return}t.disabled=!0,t.textContent=`Loading…`,n.hidden=!1,n.innerHTML=`<p class="muted">Reading bounded project metadata…</p>`;try{n.innerHTML=ke(await ne(e)),Me(n,async(e,t,r)=>{let i=n.querySelector(`.project-file-result`);if(!i)return;let a=F();if(!a){i.innerHTML=S(`File preview held: sign in through the NCNB owner gate first.`);return}r.disabled=!0,i.innerHTML=`<p class="muted">Opening read-only result…</p>`;try{i.innerHTML=Ae(await re(e,t,a))}catch(e){i.innerHTML=S(e instanceof Error?e.message:`Project file result is unavailable.`)}finally{r.disabled=!1}}),t.setAttribute(`aria-expanded`,`true`),t.textContent=`Hide files`}catch(e){n.innerHTML=S(e instanceof Error?e.message:`Project files are unavailable.`),t.textContent=`Retry files`}finally{t.disabled=!1}}})},nt=(e,t)=>{let n=E(`desktop-results`),r=E(`result-auth-state`);r.textContent=t?`Owner gate configured`:`Content gate held`,n.innerHTML=Fe(e,t),Le(n,async(e,r)=>{let i=n.querySelector(`.result-receipt-detail`);if(!i)return;if(!t){i.innerHTML=C(`Receipt content is held because owner confirmation is not configured on the local bridge.`);return}let a=F();if(!a){i.innerHTML=C(`Receipt inspection held: sign in through the NCNB owner gate first.`);return}r.disabled=!0,i.innerHTML=`<p class="muted">Opening owner-confirmed read-only receipt…</p>`;try{i.innerHTML=Ie(await oe(e,a))}catch(e){i.innerHTML=C(e instanceof Error?e.message:`Local result receipt is unavailable.`)}finally{r.disabled=!1}})},B=e=>{$e=e;let t=E(`desktop-reviews`);if(!e.length){t.innerHTML=`<p class="muted">No project receipts are awaiting review.</p>`;return}t.innerHTML=e.slice(0,30).map(e=>{let t=e.state||`pending_review`,n=t===`pending_review`?`<div class="task-actions"><button data-review="${b(e.review_id)}" data-decision="approve">Approve</button><button data-review="${b(e.review_id)}" data-decision="hold">Hold</button><button data-review="${b(e.review_id)}" data-decision="reject">Reject</button></div>`:``;return`<article class="task-card"><div><strong>${b(e.title||`Project receipt`)}</strong><span>${b(t)} · ${b(e.event_type||`receipt`)}</span><small>${b(e.summary||e.review_id)}</small></div>${n}</article>`}).join(``),t.querySelectorAll(`[data-review]`).forEach(e=>e.addEventListener(`click`,async()=>{let t=e.dataset.review||``,n=e.dataset.decision,r=$e.find(e=>e.review_id===t);if(!r||!t)return;let i=window.prompt(`${n.toUpperCase()}: ${r.title||t}\nOptional decision note:`,``)??``,a=F();if(!a){R(`bad`,`Review decision held: sign in through the NCNB owner gate first.`);return}try{R(`good`,le(t,n,await ce(t,n,i,a))),await V()}catch(e){R(`bad`,e instanceof Error?e.message:`Review decision failed.`)}}))},rt=e=>{A=e;let t=E(`representation-graphs`);t.innerHTML=He(e),t.querySelectorAll(`[data-representation-review]`).forEach(e=>{e.addEventListener(`click`,async()=>{let t=e.dataset.representationReview||``,n=e.dataset.decision,r=e.dataset.scope||`identity`,i=r===`edges`?(e.dataset.edgeIds||``).split(`|`).filter(Boolean).slice(0,100):[],a=A.find(e=>e.review?.review_id===t);if(!t||!a)return;let o=window.prompt(`${n.replace(/_/g,` `).toUpperCase()}: ${a.object.display_name}\n${r===`identity`?`Identity is reviewed before edges.`:`${i.length} bounded edges selected.`}\nOptional decision note:`,``)??``,s=F();if(!s){R(`bad`,`Representation decision held: sign in through the NCNB owner gate first.`);return}try{await de(t,n,r,i,o,s),R(`good`,`${t} recorded ${n}; local staging remains noncanonical until Drive readback.`),await V()}catch(e){R(`bad`,e instanceof Error?e.message:`Representation review decision failed.`)}})})};E(`command-form`).addEventListener(`submit`,async e=>{e.preventDefault(),O=null;try{O=L(),R(`warn`,`Sending ${O.command_id} to Desktop…`);let e=await m(O);pe(O.command_id),z(),R(`good`,`Accepted by Desktop. Task ${e.task_id??`created`}; ${e.state||`queued for governed processing`}.`),await V()}catch(e){let t=e instanceof c;O&&!t&&fe(O),z();let n=e instanceof Error?e.message:`Desktop unavailable`;R(`bad`,t?`${n} Desktop rejected the command; it was not mislabeled as an offline save.`:`${n}${O?` The command envelope was saved locally.`:``}`)}}),E(`save-command`).addEventListener(`click`,()=>{try{O=L(),fe(O),z(),R(`good`,`${O.command_id} saved locally.`)}catch(e){R(`bad`,e instanceof Error?e.message:`Command could not be saved.`)}}),E(`copy-command`).addEventListener(`click`,async()=>{try{O=L(),await navigator.clipboard.writeText(JSON.stringify(O,null,2)),R(`good`,`${O.command_id} copied as JSON.`)}catch(e){R(`bad`,e instanceof Error?e.message:`Command could not be copied.`)}});var V=async()=>{let e=E(`desktop-pill`),t=E(`desktop-state`),n=E(`merovingian-state`),r=E(`remote-access-state`),a=E(`remote-access-detail`),o=E(`desktop-pill-text`),s=E(`desktop-tasks`);e.dataset.state=`checking`,o.textContent=`checking local runtime`,t.textContent=`Checking`,n.textContent=`Checking`,r.textContent=`Checking`,a.textContent=`private relay gate`;try{let c=await u();k=c.authority_contract||null,N=c.auth?.username||N,E(`owner-username`).value=N,j||(E(`owner-auth-state`).textContent=c.auth?.configured?c.auth.must_change?`First change required`:`Sign-in required`:`Credential setup held`,c.auth?.configured?c.auth.must_change&&P(`warn`,`Sign in with the bootstrap password, then complete the required change.`):P(`bad`,`The dedicated owner credential is not configured on Desktop.`)),I(),e.dataset.state=c.ok?`online`:`degraded`,o.textContent=c.ok?`local runtime connected`:`runtime connected; health needs review`,t.textContent=`Online`,n.textContent=c.merovingian?.status===`pass`?`Healthy`:`Degraded`;let l=i(c.remote_access);r.textContent=l.label,a.textContent=l.detail;try{let e=await h();s.innerHTML=e.length?e.map(e=>`<article class="task-card"><div><strong>${b(String(e.title||`Untitled task`))}</strong><span>${b(String(e.status||`unknown`))} · ${b(String(e.priority||`normal`))}</span><small>Task ${b(String(e.id||``))}</small></div></article>`).join(``):`<p class="muted">Desktop queue is clear.</p>`}catch{s.innerHTML=`<p class="muted">Desktop is online, but task listing is unavailable.</p>`}try{tt((await ee()).projects)}catch{tt([])}try{B(await se())}catch{B([])}try{nt(await ae(),c.auth?.configured===!0)}catch(e){E(`result-auth-state`).textContent=c.auth?.configured===!0?`Owner gate configured`:`Content gate held`,E(`desktop-results`).innerHTML=C(e instanceof Error?e.message:`Local result metadata is unavailable.`)}try{rt(await ue())}catch(e){A=[];let t=c.representation_edge?.enabled===!1?`Canonical representation objects are intentionally disabled by the current launch gate.`:e instanceof Error?e.message:`Representation objects are unavailable.`;E(`representation-graphs`).innerHTML=`<article class="panel"><p class="eyebrow">Objects unavailable</p><h2>Feature-gated, not empty</h2><p class="muted">${b(t)}</p></article>`}}catch{k=null,I(),e.dataset.state=`offline`,o.textContent=`start LightSpeed Desktop and the local bridge`,t.textContent=`Offline`,n.textContent=`Offline`,r.textContent=`Unavailable`,a.textContent=`Desktop bridge is offline.`,E(`project-count`).textContent=`0`,s.innerHTML=`<p class="muted">Desktop is offline. Commands can still be saved, copied or downloaded.</p>`,E(`desktop-projects`).innerHTML=`<p class="muted">Project registry unavailable while Desktop is offline.</p>`,E(`desktop-reviews`).innerHTML=`<p class="muted">Review queue unavailable while Desktop is offline.</p>`,E(`owner-auth-state`).textContent=`Desktop offline`,P(`bad`,`Start the local Desktop bridge before signing in.`),E(`result-auth-state`).textContent=`Desktop offline`,E(`desktop-results`).innerHTML=`<p class="muted">Fixed local result metadata is unavailable while Desktop is offline.</p>`,rt([])}};E(`refresh-desktop`).addEventListener(`click`,()=>void V()),z(),V();var it=E(`neo-exchange`),at=new URL(`./data/neo_exchange.json`,document.baseURI).toString();Te(async()=>{let e=await fetch(at,{cache:`no-store`});if(!e.ok)throw Error(`Neo exchange returned HTTP ${e.status}`);return e.json()}).then(e=>{it.innerHTML=De(e)}),document.querySelectorAll(`.tab`).forEach(e=>e.addEventListener(`click`,()=>{document.querySelectorAll(`.tab`).forEach(e=>e.classList.remove(`active`)),document.querySelectorAll(`.view`).forEach(e=>e.classList.remove(`active`)),e.classList.add(`active`),E(`view-${e.dataset.view}`).classList.add(`active`)}));var ot=new URL(`./data/site_integration.json`,document.baseURI).toString(),st=async()=>{try{let e=await fetch(ot,{cache:`no-store`});return e.ok?await e.json():null}catch{return null}},ct=()=>{if(document.getElementById(`lsgo-sites-side-edit-styles`))return;let e=document.createElement(`style`);e.id=`lsgo-sites-side-edit-styles`,e.textContent=`
    .site-context-strip { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
    .site-context-strip span { border:1px solid var(--line); border-radius:999px; padding:7px 10px; color:var(--muted); font-size:12px; background:rgba(255,255,255,.025); }
    .site-context-strip strong { color:var(--text); }
    .site-parity-card { border:1px solid var(--line); border-radius:14px; padding:14px; background:rgba(255,255,255,.025); display:grid; gap:8px; }
    .site-parity-card p { margin:0; color:var(--muted); line-height:1.5; }
    .site-parity-card .site-chain { display:flex; flex-wrap:wrap; gap:7px; align-items:center; }
    .site-parity-card .site-chain span { border:1px solid var(--line); border-radius:999px; padding:6px 9px; font-size:12px; }
    .site-parity-card .site-chain i { color:var(--teal); font-style:normal; }
  `,document.head.appendChild(e)},lt=async()=>{let e=document.querySelector(`.topbar > div:first-child`),t=document.querySelector(`#view-sources`);if(!e||!t)return!1;ct();let n=(await st())?.authority_chain??[`Nathaniel Bouwer`,`Achilles / GO gate`,`agent floor`,`LightSpeed Desktop`,`Git and Drive receipts`];if(!document.getElementById(`site-context-strip`)){let t=document.createElement(`div`);t.id=`site-context-strip`,t.className=`site-context-strip`,t.innerHTML=`
      <span><strong>Owner:</strong> Nathaniel Bouwer</span>
      <span><strong>Mode:</strong> private soft launch</span>
      <span><strong>Source:</strong> Git + Drive linked · public update held</span>
    `,e.appendChild(t)}if(!document.getElementById(`site-parity-card`)){let e=document.createElement(`article`);e.id=`site-parity-card`,e.className=`panel site-parity-card`,e.innerHTML=`
      <p class="eyebrow">Canonical source chain</p>
      <h2>One operator surface, durable receipts</h2>
      <p>Desktop executes locally, Git carries implementation, Drive carries evidence and review records, and LS GO remains the operator decision surface. Alignment is shown only after current evidence validates.</p>
      <div class="site-chain">
        ${n.map((e,t)=>`${t?`<i>→</i>`:``}<span>${e}</span>`).join(``)}
      </div>
      <p><strong>Launch state:</strong> private local operation. Public Web work remains deferred.</p>
    `,t.prepend(e)}return!0},ut=0,dt=()=>{lt().then(e=>{e||ut>=40||(ut+=1,window.requestAnimationFrame(dt))})};dt();var ft=`lightspeed-cognigrex-os-shell-v0.1`,H=[`command`,`activity`,`objects`,`system`,`sources`],U=[{id:`intake`,label:`Intake`,owner:`Neo`,receipt:`source envelope`,description:`Capture the request, source pointers, project identity, constraints and expected output without inventing missing authority.`},{id:`analyse`,label:`Analyse`,owner:`Neo + Oracle`,receipt:`scope / evidence map`,description:`Resolve knowns, source authority, evidence class, conflicts, privacy and the minimum useful execution path.`},{id:`route`,label:`Commit`,owner:`Neo`,receipt:`stable task / agent route`,description:`Commit one bounded job to the correct specialist floor while retaining stable identity and exact-once transport semantics.`},{id:`workshop`,label:`Workshop`,owner:`specialist floor`,receipt:`artifact / data / result`,description:`Execute the bounded specialist work: code, modelling, evidence extraction, interface work, planning or runtime recovery.`},{id:`proof`,label:`Proof`,owner:`Smith + Morpheus + Oracle`,receipt:`tests / provenance / contradiction`,description:`Test implementation, verify provenance, resolve conflicts and keep hypothesis, inference and empirical evidence distinct.`},{id:`consolidate`,label:`Consolidate`,owner:`Neo + Achilles`,receipt:`canonical delta / supersession`,description:`Return accepted results to the living canonical library as compact deltas, pointers and receipts rather than duplicate masters.`},{id:`release`,label:`Publish-ready`,owner:`Achilles`,receipt:`claim / security / release gate`,description:`Package approved digital artifacts, data and objects for a bounded release candidate. Publish-ready is not automatically published.`}],W=[{floor:`Neo`,short:`N`,role:`Cognigrex operational head: intake, decomposition, routing, cycle control and result aggregation.`,boundary:`May coordinate and reason operationally; cannot self-promote evidence, canon or public claims past Achilles/owner gates.`},{floor:`Oracle`,short:`O`,role:`Sources, evidence retrieval, indexing, known-state and data lineage.`,boundary:`Preserves source authority and uncertainty; duplicate references do not become independent evidence.`},{floor:`Morpheus`,short:`M`,role:`Contradiction, provenance, claim proof, confidence and supersession review.`,boundary:`Reviews and recommends; does not fabricate empirical validation.`},{floor:`Smith`,short:`S`,role:`Code, schemas, deterministic transforms, tests, build and execution receipts.`,boundary:`Changes remain branch/review gated until the applicable execution and release receipts exist.`},{floor:`Architect`,short:`A`,role:`Projects, dependency topology, plans, interfaces and system decomposition.`,boundary:`Uses canonical project identity and pointers rather than spawning competing masters.`},{floor:`TheConstruct`,short:`TC`,role:`Simulation, CAD, meshes, digital twins, derived views and manufacturing-reference artifacts.`,boundary:`Derived models remain labelled and cannot imply physical performance without evidence.`},{floor:`Trinity`,short:`T`,role:`Interface, interaction, visual language, accessibility and communication surfaces.`,boundary:`Presentation cannot elevate claim state or bypass evidence/security classification.`},{floor:`Merovingian`,short:`R`,role:`Runtime health, storage, recovery, resource control, persistence and operational receipts.`,boundary:`Recovery and cleanup are reversible/evidence-gated; no silent deletion or second runtime.`},{floor:`Achilles`,short:`Ω`,role:`Meta-governance, proof thresholds, safety, canonical promotion and release oversight.`,boundary:`Audits and gates the collective; it is not the routine task router inside Cognigrex.`}],G=e=>H.includes(e)?e:`command`,pt=(e,t=`command`)=>G(new URLSearchParams(e.startsWith(`?`)?e.slice(1):e).get(`view`)||t),mt=e=>{let t=e.trim().toLowerCase();return t?/\b(publish|release|public[- ]?ready|export|mint|deploy)\b/.test(t)?`release`:/\b(consolidat|canon|supersed|assimil|promot|living library|handoff)\b/.test(t)?`consolidate`:/\b(test|proof|verify|validat|audit|conflict|provenance|claim|confidence)\b/.test(t)?`proof`:/\b(build|code|model|simulate|render|mesh|cad|analyse data|analyze data|workshop|execute|run)\b/.test(t)?`workshop`:/\b(route|delegate|commit|queue|assign|agent|floor)\b/.test(t)?`route`:/\b(source|evidence|research|analyse|analyze|classif|scope|compare|reconcile)\b/.test(t)?`analyse`:`intake`:`intake`},K=e=>{let t=e.trim().toLowerCase();if(!t)return`Neo`;if(/\b(proof|claim|verify|verification|conflict|confidence|audit|contradiction|supersession)\b/.test(t))return`Morpheus`;if(/\b(achilles|governance|canonical promotion|release gate|safety gate)\b/.test(t))return`Achilles`;let n=o(e);return n===`Achilles`?`Neo`:n},ht=e=>U.find(t=>t.id===e)??U[0],gt=`lightspeed-cognigrex-os-shell-state-v1`,_t={activeView:`command`,activeAgent:`Neo`,focusMode:!1},q=(()=>{try{let e=JSON.parse(localStorage.getItem(gt)||`{}`),t=W.some(t=>t.floor===e.activeAgent)?e.activeAgent:_t.activeAgent;return{activeView:pt(window.location.search,e.activeView),activeAgent:t,focusMode:!!e.focusMode}}catch{return{..._t}}})(),J=e=>{q={...q,...e},localStorage.setItem(gt,JSON.stringify(q))},Y=e=>e.replace(/[&<>'"]/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,"'":`&#39;`,'"':`&quot;`})[e]||e),X=e=>{let t=document.querySelector(`.tab[data-view="${e}"]`);t&&!t.classList.contains(`active`)&&t.click(),J({activeView:e}),document.body.dataset.lsWorkspace=e},Z=(e,t=!1)=>{J({activeAgent:e}),document.body.dataset.lsAgent=e,document.querySelectorAll(`[data-ls-agent]`).forEach(t=>{t.dataset.active=t.dataset.lsAgent===e?`true`:`false`});let n=document.getElementById(`target-floor`);n&&(n.value=e),t&&(X(`command`),document.getElementById(`instruction`)?.focus())},Q=e=>{let t=ht(e);document.body.dataset.lsWorkflow=t.id,document.querySelectorAll(`[data-ls-stage]`).forEach(e=>{e.dataset.active=e.dataset.lsStage===t.id?`true`:`false`});let n=document.getElementById(`ls-os-stage-detail`);n&&(n.innerHTML=`<strong>${Y(t.label)}</strong><span>${Y(t.description)}</span><small>${Y(t.owner)} · receipt: ${Y(t.receipt)}</small>`)},vt=()=>{let e=document.createElement(`aside`);return e.className=`ls-os-rail`,e.setAttribute(`aria-label`,`Cognigrex agent rail`),e.innerHTML=`
    <button class="ls-os-mark" type="button" data-ls-home title="LightSpeed Cognigrex">LS</button>
    <div class="ls-os-agent-stack">
      ${W.map(e=>`
        <button class="ls-os-agent" type="button" data-ls-agent="${e.floor}" title="${Y(e.floor)} — ${Y(e.role)}">
          <span>${Y(e.short)}</span><small>${Y(e.floor)}</small>
        </button>
      `).join(``)}
    </div>
    <button class="ls-os-focus" type="button" data-ls-focus title="Toggle focus mode">◫</button>
  `,e.querySelectorAll(`[data-ls-agent]`).forEach(e=>{e.addEventListener(`click`,()=>Z(e.dataset.lsAgent,!0))}),e.querySelector(`[data-ls-home]`)?.addEventListener(`click`,()=>X(`command`)),e.querySelector(`[data-ls-focus]`)?.addEventListener(`click`,()=>{let e=!q.focusMode;J({focusMode:e}),document.body.dataset.lsFocus=e?`true`:`false`}),e},yt=()=>{let e=document.createElement(`section`);return e.className=`ls-os-status-strip`,e.setAttribute(`aria-label`,`LightSpeed operating state`),e.innerHTML=`
    <div><span class="ls-os-status-dot" id="ls-os-runtime-dot"></span><strong id="ls-os-runtime">Desktop checking</strong><small>${n}</small></div>
    <div><span class="ls-os-status-dot stable"></span><strong>Neo operational head</strong><small>specialist-agent orchestration</small></div>
    <div><span class="ls-os-status-dot guarded"></span><strong>Achilles oversight</strong><small>evidence · canon · release gate</small></div>
    <div><span class="ls-os-status-dot private"></span><strong>De Sporte</strong><small>private persistence sidecar · metadata only</small></div>
    <button type="button" id="ls-os-palette-open" title="Open command palette (Ctrl/Cmd+K)">⌘K</button>
  `,e},bt=()=>{let e=document.createElement(`section`);return e.className=`ls-os-workflow`,e.setAttribute(`aria-label`,`ACR3 operating workflow`),e.innerHTML=`
    <div class="ls-os-workflow-track">
      ${U.map((e,t)=>`
        <button type="button" data-ls-stage="${e.id}" title="${Y(e.description)}">
          <span>${String(t+1).padStart(2,`0`)}</span><strong>${Y(e.label)}</strong><small>${Y(e.owner)}</small>
        </button>
      `).join(``)}
    </div>
    <div class="ls-os-stage-detail" id="ls-os-stage-detail"></div>
  `,e.querySelectorAll(`[data-ls-stage]`).forEach(e=>{e.addEventListener(`click`,()=>Q(e.dataset.lsStage))}),e},xt=()=>{let e=document.createElement(`div`);return e.className=`ls-os-palette`,e.id=`ls-os-palette`,e.hidden=!0,e.innerHTML=`
    <div class="ls-os-palette-card" role="dialog" aria-modal="true" aria-label="LightSpeed command palette">
      <div class="ls-os-palette-head"><strong>LightSpeed</strong><span>${ft}</span><button type="button" data-ls-close aria-label="Close">×</button></div>
      <input id="ls-os-palette-input" type="search" autocomplete="off" placeholder="Open workspace, select agent, or route an outcome…" />
      <div id="ls-os-palette-results" class="ls-os-palette-results"></div>
    </div>
  `,e.addEventListener(`click`,t=>{t.target===e&&$()}),e.querySelector(`[data-ls-close]`)?.addEventListener(`click`,()=>$()),e.querySelector(`#ls-os-palette-input`)?.addEventListener(`input`,()=>Ct()),e},St=()=>{let e=document.getElementById(`ls-os-palette`);e&&(e.hidden=!1,Ct(),window.setTimeout(()=>document.getElementById(`ls-os-palette-input`)?.focus(),0))},$=()=>{let e=document.getElementById(`ls-os-palette`);e&&(e.hidden=!0)},Ct=()=>{let e=document.getElementById(`ls-os-palette-input`),t=document.getElementById(`ls-os-palette-results`);if(!e||!t)return;let n=e.value.trim().toLowerCase(),r=H.filter(e=>!n||e.includes(n)).map(e=>`<button type="button" data-palette-view="${e}"><span>Workspace</span><strong>${e}</strong><small>Open ${e} workspace</small></button>`),i=W.filter(e=>!n||`${e.floor} ${e.role}`.toLowerCase().includes(n)).map(e=>`<button type="button" data-palette-agent="${e.floor}"><span>Agent</span><strong>${Y(e.floor)}</strong><small>${Y(e.role)}</small></button>`);t.innerHTML=[...n?[`<button type="button" data-palette-route="true"><span>Neo route</span><strong>${Y(K(e.value))}</strong><small>Use this text as the command outcome and route it through Cognigrex.</small></button>`]:[],...r,...i].slice(0,14).join(``),t.querySelectorAll(`[data-palette-view]`).forEach(e=>e.addEventListener(`click`,()=>{X(G(e.dataset.paletteView)),$()})),t.querySelectorAll(`[data-palette-agent]`).forEach(e=>e.addEventListener(`click`,()=>{Z(e.dataset.paletteAgent,!0),$()})),t.querySelector(`[data-palette-route]`)?.addEventListener(`click`,()=>{let t=e.value.trim(),n=document.getElementById(`instruction`);n&&t&&(n.value=t,n.dispatchEvent(new Event(`input`,{bubbles:!0})),Z(K(t)),Q(mt(t)),n.focus()),X(`command`),$()})},wt=e=>{let t=e.querySelector(`#view-command .command-panel .panel-head .eyebrow`);t&&(t.textContent=`Neo intake`);let n=e.querySelector(`#view-command .command-panel .panel-head h2`);n&&(n.textContent=`State the outcome`);let r=e.querySelector(`#command-form button.primary[type=submit]`);r&&(r.textContent=`Send to runtime`);let i=e.querySelector(`#view-command .guardrail-panel .eyebrow`);i&&(i.textContent=`Cognigrex operating contract`);let a=e.querySelector(`#view-command .guardrail-panel h2`);a&&(a.textContent=`Neo-led work, durable proof`);let o=e.querySelectorAll(`#view-command .guardrail-panel .compact-list li`),s=[`Neo owns intake, decomposition, routing and aggregate workflow identity.`,`Specialist floors execute only their bounded purpose and return receipts.`,`Oracle, Smith and Morpheus preserve source, implementation and proof boundaries.`,`Achilles governs evidence class, canonical promotion, safety and release.`,`Accepted results return as compact canonical deltas rather than duplicate masters.`];o.forEach((e,t)=>{s[t]&&(e.textContent=s[t])});let c=e.querySelector(`#view-system .flow`);c&&(c.innerHTML=`<span>LS GO</span><i>→</i><span>Neo</span><i>→</i><span>specialist floors</span><i>→</i><span>Morpheus proof</span><i>→</i><span>Achilles gate</span><i>→</i><span>canon / release</span>`);let l=e.querySelector(`#view-system .agent-grid`);if(l){let e=new Map;l.querySelectorAll(`.agent`).forEach(t=>{let n=t.querySelector(`strong`)?.textContent?.trim();n&&e.set(n,t)}),W.forEach(t=>{let n=e.get(t.floor);n&&l.append(n)})}e.querySelectorAll(`.panel-head`).forEach(e=>{if(e.querySelector(`h2`)?.textContent?.trim()!==`Review queue`)return;let t=e.querySelector(`.eyebrow`);t&&(t.textContent=`Achilles / owner gate`)})},Tt=()=>{document.querySelectorAll(`.tab[data-view]`).forEach(e=>{e.addEventListener(`click`,()=>{let t=G(e.dataset.view);J({activeView:t}),document.body.dataset.lsWorkspace=t})});let e=document.getElementById(`instruction`),t=document.getElementById(`route-preview`);e?.addEventListener(`input`,()=>{let n=K(e.value);Z(n),Q(mt(e.value)),t&&(t.innerHTML=`<strong>Neo route:</strong> ${Y(n)} is the primary specialist. Achilles remains the evidence, canonical-promotion and release oversight gate.`)}),document.getElementById(`ls-os-palette-open`)?.addEventListener(`click`,()=>St())},Et=async()=>{let e=document.getElementById(`ls-os-runtime`),t=document.getElementById(`ls-os-runtime-dot`);if(!(!e||!t))try{let n=await u(),r=!!(n.ok&&n.services?.merovingian!==!1);e.textContent=r?`Desktop online`:`Desktop degraded`,t.dataset.state=r?`online`:`degraded`,t.title=n.time_utc?`Last read ${n.time_utc}`:`Local status read`}catch{e.textContent=`Desktop offline / unproved`,t.dataset.state=`offline`,t.title=`No current localhost receipt from this browser.`}};queueMicrotask(()=>{if(document.documentElement.dataset.lsOsShell===`lightspeed-cognigrex-os-shell-v0.1`)return;let e=document.querySelector(`.shell`);if(!e)return;document.documentElement.dataset.lsOsShell=ft,document.body.classList.add(`ls-os-enabled`),document.body.dataset.lsFocus=q.focusMode?`true`:`false`,document.title=`LightSpeed · Cognigrex`,document.body.prepend(vt()),e.prepend(bt()),e.prepend(yt()),document.body.append(xt());let t=e.querySelector(`.topbar h1`);t&&(t.textContent=`Cognigrex`);let n=e.querySelector(`.topbar .eyebrow`);n&&(n.textContent=`LightSpeed operating system`);let r=e.querySelector(`.topbar .lede`);r&&(r.textContent=`Neo coordinates specialised purpose agents across intake, workshop execution, proof, canonical consolidation and publish-ready digital artifacts; Achilles governs evidence and release.`),wt(e),Tt(),X(q.activeView),Z(q.activeAgent);let i=document.getElementById(`instruction`);i?i.dispatchEvent(new Event(`input`,{bubbles:!0})):(Q(`intake`),Z(`Neo`)),Et().catch(()=>void 0),window.setInterval(()=>Et().catch(()=>void 0),3e4),window.addEventListener(`keydown`,e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()===`k`){e.preventDefault(),St();return}e.key===`Escape`&&$(),(e.ctrlKey||e.metaKey)&&/^[1-5]$/.test(e.key)&&(e.preventDefault(),X(H[Number(e.key)-1]||`command`))})});