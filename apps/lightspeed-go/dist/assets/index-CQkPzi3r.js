(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),t.credentials=e.crossOrigin===`use-credentials`?`include`:e.crossOrigin===`anonymous`?`omit`:`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var e=`lightspeed-go-command-v2`,t=`http://127.0.0.1:8765`,n=(e=>t)(void 0),r=[`Achilles`,`Neo`,`Architect`,`TheConstruct`,`Morpheus`,`Oracle`,`Smith`,`Merovingian`,`Trinity`],i=e=>e?.state===`ready_for_private_relay_verification`?{label:`Verify off-device`,detail:`Private HTTPS origin configured; remote owner flow still needs readback.`}:e?.state===`credential_gate`?{label:`Credential held`,detail:`Complete the owner password change before remote verification.`}:{label:`Local only`,detail:`No private HTTPS relay origin is configured.`},a=e=>{let t=e?.transport?.verified_carriers?.length||0,n=e?.compute?.peer_nodes?.length||0;return{transfer:e?.transport?.peer_transport_verified?`Peer transport verified · ${n} peer node${n===1?``:`s`}`:t?`Carrier readback verified · ${t} carrier${t===1?``:`s`} · peer transport unproven`:`No verified carrier or peer transport`,compute:e?.compute?.peer_compute_verified?`Peer compute verified · ${n} peer node${n===1?``:`s`}`:e?.compute?.local_ready?`Local compute ready · peer compute unproven`:`Compute unavailable or held`,boundary:e?.claim_boundary||`Node-exchange status is unavailable.`}},o=(e,t)=>e.replace(/\s+/g,` `).trim().slice(0,t),s=e=>{let t=e.toLowerCase();return/\b(ui|site|web|design|visual|layout|canva|accessibility)\b/.test(t)?`Trinity`:/\b(git|github|code|build|commit|branch|deploy|schema|api|runtime)\b/.test(t)?`Smith`:/\b(source|evidence|research|data|document|drive|sheet|workbook|citation)\b/.test(t)?`Oracle`:/\b(proof|claim|verify|conflict|confidence|audit)\b/.test(t)?`Morpheus`:/\b(simulate|simulation|model|gmat|trajectory|twin|physics)\b/.test(t)?`TheConstruct`:/\b(plan|mission|architecture|dependency|roadmap|system|project)\b/.test(t)?`Architect`:/\b(health|status|diagnostic|failure|error|monitor|storage|cleanup|archive)\b/.test(t)?`Merovingian`:/\b(coordinate|queue|handoff|agent|task|execute|run)\b/.test(t)?`Neo`:`Achilles`},c=t=>{let n=o(t.instruction,4e3);if(!n)throw TypeError(`instruction is required`);let r=new Date().toISOString(),i=Math.random().toString(36).slice(2,8).toUpperCase(),a=t.targetFloor??s(n),c=t.authorityContract;if(!c)throw TypeError(`Desktop authority contract is not available`);let l=o(c.canonical_gate_id,160),u=o(c.owner_decision_ref,160),d=o(c.core_acceptance_ref,160),f=o(c.approval_or_hold_state,40).toLowerCase(),p=o(c.authorised_scope,1e3),m=o(c.prohibited_scope,1e3);if(!l||!u||!d||!p||!m)throw TypeError(`Desktop authority contract is incomplete`);if(![`approve`,`approved`,`operator_approved`,`operator_authorized`,`operator_authorised`].includes(f))throw TypeError(`Desktop authority contract is held`);let h=t.executionMode??`review`;return{schema_version:e,command_id:`LSGO-${r.replace(/\D/g,``).slice(0,14)}-${i}`,created_utc:r,source:`LS GO`,title:o(t.title||n,160),instruction:n,target_floor:a,oversight_floor:`Achilles`,priority:t.priority??`normal`,execution_mode:h,action_type:t.actionType??`cognigrex_workflow`,proof_required:!0,public_safe:!0,canonical_gate_id:l,owner_decision_ref:u,core_acceptance_ref:d,approval_or_hold_state:f,authorised_scope:p,prohibited_scope:m,requested_scope:`${a} private local ${h} queue`}},l=class extends Error{status;constructor(e,t){super(t),this.name=`DesktopRequestError`,this.status=e}},u=async(e,t,n=3500)=>{let r=new AbortController,i=window.setTimeout(()=>r.abort(),n);try{let n=await fetch(e,{...t,signal:r.signal,cache:`no-store`});if(!n.ok){let e=`Desktop returned HTTP ${n.status}`;try{let t=await n.json();t.detail&&(e=t.detail)}catch{}throw new l(n.status,e)}return await n.json()}finally{window.clearTimeout(i)}},d=(e=n)=>u(`${e}/api/v1/status`,{method:`GET`},1e4),f=(e,t,r=n)=>u(`${r}/api/v1/auth/login`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({username:o(e,64),password:t.slice(0,1024)})},15e3),p=(e,t,r,i,a,s=n)=>u(`${s}/api/v1/auth/change-password`,{method:`POST`,headers:{"Content-Type":`application/json`,[a?`X-LightSpeed-Password-Change`:`X-LightSpeed-Session`]:i.slice(0,256)},body:JSON.stringify({username:o(e,64),current_password:t.slice(0,1024),new_password:r.slice(0,1024)})},2e4),m=(e,t=n)=>u(`${t}/api/v1/auth/logout`,{method:`POST`,headers:{"X-LightSpeed-Session":e.slice(0,256)}},7e3),h=(e,t,r=n)=>u(`${r}/api/v1/node-exchange/transfer/plan`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":t.slice(0,256)},body:JSON.stringify(e)},1e4),g=(e,t,r=n)=>u(`${r}/api/v1/node-exchange/compute/plan`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":t.slice(0,256)},body:JSON.stringify(e)},1e4),_=(e,t=n)=>u(`${t}/api/v1/ls-go/commands`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify(e)},7e3),v=async(e=n)=>{let t=await u(`${e}/api/v1/tasks?limit=12`,{method:`GET`});return Array.isArray(t.tasks)?t.tasks:[]},ee=async(e=n)=>{let t=await u(`${e}/api/v1/projects`,{method:`GET`},15e3);return{projects:Array.isArray(t.projects)?t.projects:[],summary:t.summary||{},duplicateNames:Array.isArray(t.duplicate_names)?t.duplicate_names:[],cleanupSummary:t.cleanup_summary||{}}},te=(e,t,n)=>{if(n!==void 0&&(t===void 0||!/^[a-f0-9]{64}$/.test(n)))throw Error(`Exact file metadata revision required.`);let r=encodeURIComponent(e);if(t===void 0)return`/api/v1/projects/${r}/files`;let i=`/api/v1/projects/${r}/files/${t.split(`/`).map(e=>encodeURIComponent(e)).join(`/`)}`;return n===void 0?i:`${i}?expected_metadata_revision=${n}`},ne=async(e,t=n)=>u(`${t}${te(e)}?limit=200`,{method:`GET`},15e3),re=async(e,t,r,i=n,a)=>u(`${i}${te(e,t,a)}`,{method:`GET`,cache:`no-store`,headers:{"X-LightSpeed-Session":r.slice(0,256)}},1e4),y=(e,t)=>{if(t!==void 0&&(e===void 0||!/^[a-f0-9]{64}$/.test(t)))throw Error(`Exact receipt revision required.`);if(e===void 0)return`/api/v1/results`;let n=`/api/v1/results/${encodeURIComponent(e)}`;return t===void 0?n:`${n}?expected_sha256=${t}`},ie=async(e=n,t=50)=>u(`${e}${y()}?limit=${Math.max(1,Math.min(t,200))}`,{method:`GET`},1e4),ae=async(e,t,r=n,i)=>u(`${r}${y(e,i)}`,{method:`GET`,cache:`no-store`,headers:{"X-LightSpeed-Session":t.slice(0,256)}},1e4),oe=async(e=n,t=50)=>{let r=await u(`${e}/api/v1/reviews?limit=${Math.max(1,Math.min(t,200))}`,{method:`GET`},1e4);return Array.isArray(r.reviews)?r.reviews:[]},se=async(e,t,r=``,i=``,a=n)=>u(`${a}/api/v1/reviews/${encodeURIComponent(e)}/decision`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":i.slice(0,256)},body:JSON.stringify({decision:t,note:o(r,1e3)})},7e3),ce=(e,t=n)=>u(`${t}/api/v1/cgx/surface?selector=LightSpeed`,{method:`GET`,headers:{"X-LightSpeed-Session":e.slice(0,256)}},1e4),le=(e,t=n)=>u(`${t}/api/v1/cgx/family/topology`,{method:`GET`,headers:{"X-LightSpeed-Session":e.slice(0,256)}},12e3),ue=e=>({roles:e.roles.filter(e=>!e.execution_enabled),routes:e.routes.filter(e=>e.state===`available`&&e.read_only&&!e.execution_enabled)}),de=(e,t,r=n)=>u(`${r}/api/v1/cgx/persistence/checkpoint`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":t.slice(0,256)},body:JSON.stringify(e)},12e3),fe=(e,t,r,i,a=n)=>u(`${a}/api/v1/cgx/persistence/revoke/${encodeURIComponent(e)}/${encodeURIComponent(t)}`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":i.slice(0,256)},body:JSON.stringify({expected_candidate_sha256:r})},12e3),pe=(e,t,n)=>{let r=n.receipt?.drive_writeback_mode;return r===`owner_approved_exact_drive_target`?`${e} marked ${t}. Owner-approved Drive decision receipt written by Desktop.`:r===`local_outbox_pending_drive_sync`?`${e} marked ${t}. Local outbox receipt staged; Drive sync remains pending.`:`${e} marked ${t}. Decision receipt recorded; destination requires verification.`},me=async(e=n)=>{let t=await u(`${e}/api/v1/representation-graphs`,{method:`GET`},15e3);return Array.isArray(t.graphs)?t.graphs:[]},he=async(e,t,r,i=[],a=``,s=``,c=n)=>u(`${c}/api/v1/representation-reviews/${encodeURIComponent(e)}/decision`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":s.slice(0,256)},body:JSON.stringify({decision:t,scope:r,edge_ids:i.slice(0,100),note:o(a,1e3)})},1e4),ge=`lightspeed-go-pending-commands-v1`,_e=()=>{try{let e=JSON.parse(localStorage.getItem(ge)||`[]`);return Array.isArray(e)?e:[]}catch{return[]}},ve=e=>{let t=[e,..._e().filter(t=>t.command_id!==e.command_id)].slice(0,30);return localStorage.setItem(ge,JSON.stringify(t)),t},ye=e=>{let t=_e().filter(t=>t.command_id!==e);return localStorage.setItem(ge,JSON.stringify(t)),t},be=e=>{let t=new Blob([JSON.stringify(e,null,2)],{type:`application/json`}),n=URL.createObjectURL(t),r=document.createElement(`a`);r.href=n,r.download=`${e.command_id}.json`,r.click(),URL.revokeObjectURL(n)},xe=`lightspeed-neo-exchange-v1`,Se=[`critical`,`high`,`normal`,`low`],Ce=[`queued`,`active`,`review`,`blocked`,`complete`],we=[`icon`,`age_label`],Te=e=>typeof e==`object`&&!!e&&!Array.isArray(e),b=(e,t,n)=>{if(typeof e!=`string`)return t;let r=e.replace(/\s+/g,` `).trim();return r?r.slice(0,n):t},Ee=(e,t,n)=>{let r=b(e,``,n);if(!r)throw TypeError(`queue record ${t} is required`);return r},De=(e,t,n)=>typeof e==`string`&&t.includes(e)?e:n,Oe=e=>Te(e)?Object.fromEntries(we.flatMap(t=>{let n=b(e[t],``,48);return n?[[t,n]]:[]})):{},ke=e=>{if(!Te(e))throw TypeError(`queue record must be an object`);return{id:Ee(e.id,`id`,80),title:Ee(e.title,`title`,160),priority:De(e.priority,Se,`normal`),status:De(e.status,Ce,`queued`),source:b(e.source,`GO Gate`,48),target:b(e.target,`Neo`,48),created_utc:b(e.created_utc,``,32),extensions:Oe(e.extensions),notes:b(e.notes,``,240)}},Ae=e=>{if(!Te(e))throw TypeError(`Neo exchange must be an object`);let t=Array.isArray(e.queue)?e.queue.map(ke):[];return{schema_version:xe,generated_at_utc:b(e.generated_at_utc,``,32),queue:t}},je=e=>({total:e.queue.length,critical:e.queue.filter(e=>e.priority===`critical`).length,active:e.queue.filter(e=>e.status!==`complete`).length,complete:e.queue.filter(e=>e.status===`complete`).length}),x=e=>e.replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#039;`})[e]??e),Me=async e=>{try{return Ae(await e())}catch{return Ae({})}},Ne=e=>e.status===`blocked`?`blocked`:e.status===`complete`?`pass`:e.priority===`critical`||e.priority===`high`?`warn`:`ready`,Pe=e=>{let t=je(e),n=e.queue.length?e.queue.map(e=>`
            <li class="status-row ${Ne(e)}">
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
  `},Fe=e=>{let t=ue(e);return{revision:e.source_view_sha256,roles:t.roles.map(({id:e,floor:t})=>({id:e,label:t})),routes:t.routes.map(({id:e})=>({id:e,label:e})),canStage:t.roles.length>0&&t.routes.length>0&&e.native_mint_authorized===!1&&e.execution_authorized===!1,permission:`owner_session_private_review_only`}};function Ie(e,t,n,r){let i=Fe(t),a=i.roles.map(e=>`<option value="`+x(e.id)+`">`+x(e.label)+`</option>`).join(``),o=i.routes.map(e=>`<option value="`+x(e.id)+`">`+x(e.label)+`</option>`).join(``),s=document.createElement(`details`);s.innerHTML=`<summary>Canonical Cognigrex persistence · review checkpoint</summary><p class="muted">Task-bound metadata only in the existing FileSpace/DataSpace operational ledger. This does not dispatch an agent, train weights, mint CGX, or grant source access.</p><form class="form-grid" id="cgx-native-checkpoint-form"><label class="field"><span>Existing task ID</span><input name="task" required maxlength="128" pattern="[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}" placeholder="task-001"></label><label class="field"><span>Run ID</span><input name="run" required maxlength="128" pattern="[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}" placeholder="run-001"></label><label class="field"><span>Specialist lane</span><select name="role" required>`+a+`</select></label><label class="field"><span>Read-only capability</span><select name="route" required>`+o+`</select></label><label class="field"><span>CPU planning ceiling</span><input name="cpu" type="number" min="1" max="4" value="1" required></label><label class="field"><span>Memory planning ceiling (MiB)</span><input name="memory" type="number" min="64" max="1024" value="128" required></label><label class="field"><span>Maximum jobs</span><input name="jobs" type="number" min="1" max="16" value="2" required></label><label class="field"><span>TTL (seconds)</span><input name="ttl" type="number" min="60" max="3600" value="900" required></label><button type="submit"`+(i.canStage?``:` disabled`)+`>Record private checkpoint</button><button type="button" id="cgx-native-revoke" hidden>Revoke checkpoint</button></form><p id="cgx-native-result" class="muted" role="status">No checkpoint recorded.</p>`,e.appendChild(s);let c=s.querySelector(`form`),l=s.querySelector(`#cgx-native-result`),u=s.querySelector(`#cgx-native-revoke`);if(!c||!l||!u)return;let d=e=>c.elements.namedItem(e);c.addEventListener(`submit`,async e=>{if(e.preventDefault(),!r()||!i.canStage)return;let t=d(`task`)?.value.trim()||``,a=d(`run`)?.value.trim()||``,o=d(`role`)?.value||``,s=d(`route`)?.value||``;if(t&&a&&o&&s){l.textContent=`Validating owner authority and canonical source revision…`;try{let e=await de({selector:`LightSpeed`,task_id:t,run_id:a,expected_view_sha256:i.revision,role_ids:[o],route_ids:[s],cpu_threads:Number(d(`cpu`)?.value),memory_mib:Number(d(`memory`)?.value),max_jobs:Number(d(`jobs`)?.value),ttl_seconds:Number(d(`ttl`)?.value)},n);if(!r()||!l.isConnected)return;l.textContent=e.state+` · readback `+String(e.exact_readback_verified)+` · expires `+e.expires_utc+` · execution/mint held`,u.hidden=e.state!==`REVIEW_ONLY`,u.onclick=async()=>{if(r()){l.textContent=`Submitting bounded revocation…`;try{let i=await fe(t,a,e.candidate_sha256,n);if(!r()||!l.isConnected)return;l.textContent=i.state+` · readback `+String(i.exact_readback_verified),u.hidden=!0}catch(e){r()&&l.isConnected&&(l.textContent=e instanceof Error?e.message:`Revocation held`)}}}}catch(e){r()&&l.isConnected&&(l.textContent=e instanceof Error?e.message:`Native persistence deployment or authority is held`)}}})}var Le=e=>{let t=Number(e||0);return t<1024?`${t} B`:t<1024**2?`${(t/1024).toFixed(1)} KB`:t<1024**3?`${(t/1024**2).toFixed(1)} MB`:`${(t/1024**3).toFixed(1)} GB`},Re=e=>e.length?e.slice(0,30).map(e=>{let t=e.file_browser?.state??(e.authority===`external_reference`?`restricted`:void 0),n=!t||t===`available`,r=t&&t!==`available`?` · ${x(e.file_browser?.reason||`External references remain metadata-only until the bridge confirms bounded access.`)}`:``,i=n?`<button type="button" data-project-files="${x(e.project_id)}" aria-expanded="false">Files</button>`:`<small class="project-file-access">Files ${t===`restricted`?`held`:`unavailable`}</small>`;return`
    <article class="task-card project-card" data-project-card="${x(e.project_id)}">
      <div class="project-summary">
        <strong>${x(e.name)}</strong>
        <span>${x(e.condition||`unknown`)} · ${x(e.authority||`reference`)} · ${e.file_count||0} files</span>
        <small>${Le(e.size_bytes)}${e.scan_truncated?` · bounded scan`:``}${r}</small>
      </div>
      <div class="task-actions">
        ${i}
      </div>
      <div class="project-files" aria-live="polite" hidden></div>
    </article>
  `}).join(``):`<p class="muted">No project folders were found in the configured roots.</p>`,ze=e=>{let t=e.summary,n=`<p class="project-file-boundary">${x(e.boundary)}</p>`;if(!e.files.length){let t=e.state===`restricted`?`No files are visible; credential-like or excluded runtime files are withheld.`:`This registered project currently has no visible files.`;return`<div class="project-files-head"><strong>Files</strong><small>${x(e.project.authority||`reference`)} authority</small></div><p class="muted">${t}</p>${n}`}let r=e.files.map(t=>`
    <article class="project-file-row">
      <div><strong>${x(t.relative_path)}</strong><small>${x(t.mime_type)} · ${Le(t.size_bytes)}</small></div>
      <button type="button" data-project-file="${x(t.relative_path)}" data-project-id="${x(e.project.project_id)}">Open</button>
    </article>
  `).join(``),i=t.scan_truncated?` · bounded result`:``;return`
    <div class="project-files-head"><strong>Files</strong><small>${t.visible_file_count} visible · ${t.blocked_file_count} withheld${i}</small></div>
    <div class="project-file-list">${r}</div>
    <div class="project-file-result" aria-live="polite"></div>
    ${n}
  `},Be=e=>`
  <div class="project-files-head"><strong>Files unavailable</strong></div>
  <p class="result" data-tone="bad">${x(e)}</p>
`,Ve=e=>{let t=e.preview,n=`<p class="muted">Metadata only. Binary or non-UTF-8 content is not transferred into UniSpace.</p>`;return t.state===`empty`?n=`<p class="muted">The file is empty.</p>`:t.state===`available`&&(n=`<pre>${x(t.text||``)}</pre>${t.truncated?`<small class="muted">Preview truncated at the governed byte limit.</small>`:``}`),`
    <section class="project-file-preview">
      <div class="project-files-head"><strong>${x(e.file.relative_path)}</strong><small>${x(e.file.mime_type)} · ${Le(e.file.size_bytes)}</small></div>
      ${n}
      <p class="project-file-boundary">${x(e.boundary)}</p>
    </section>
  `},He=(e,t)=>{e.querySelectorAll(`[data-project-files]`).forEach(e=>{e.addEventListener(`click`,()=>{let n=e.dataset.projectFiles||``;n&&t(n,e)})})},Ue=(e,t)=>{e.querySelectorAll(`[data-project-file][data-project-id]`).forEach(e=>{e.addEventListener(`click`,()=>{let n=e.dataset.projectId||``,r=e.dataset.projectFile||``;n&&r&&t(n,r,e)})})},We=e=>{let t=Number(e||0);return t<1024?`${t} B`:t<1024**2?`${(t/1024).toFixed(1)} KB`:`${(t/1024**2).toFixed(1)} MB`},Ge=e=>{let t=String(e.status||`unknown`).toLowerCase();return[`complete`,`completed`,`pass`,`passed`].includes(t)?`good`:[`blocked`,`failed`,`error`].includes(t)?`bad`:`warn`},Ke=(e,t)=>{let n=e.summary,r=`<p class="result-receipt-boundary">${x(e.boundary)}</p>`,i=t?`Exact receipt content requires the local owner-confirmation token.`:`Content inspection is held because the local owner-confirmation token is not configured.`;if(!e.results.length)return`<p class="muted">${e.state===`restricted`?`No eligible fixed receipts are visible; invalid receipt objects remain withheld.`:`No fixed local result receipts have been written yet.`}</p><p class="result-receipt-auth">${i}</p>${r}`;let a=e.results.map(e=>{let n=e.action_type||`untyped`,r=e.target_floor||`floor unknown`,i=e.completed_utc||e.created_utc||e.modified_utc,a=[e.task_id==null?null:`Task ${e.task_id}`,e.job_id==null?null:`Job ${e.job_id}`,e.command_id||null].filter(Boolean).join(` · `),o=t?``:` disabled aria-disabled="true"`;return`
      <article class="task-card result-receipt-card" data-result-state="${Ge(e)}">
        <div>
          <strong>${x(e.result_id)}</strong>
          <span>${x(e.status)} · ${x(n)} · ${x(r)}</span>
          <small>${x(a||`No task/job identity`)} · ${x(i||`time unavailable`)} · ${We(e.size_bytes)}</small>
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
  `},qe=e=>{let t=JSON.stringify(e.result,null,2);return`
    <section class="result-receipt-preview">
      <div class="result-receipt-preview-head">
        <strong>${x(e.identity.result_id)}</strong>
        <small>${We(e.identity.size_bytes)} · SHA-256 ${x(e.identity.sha256)}</small>
      </div>
      <pre>${x(t)}</pre>
      <p class="result-receipt-boundary">${x(e.boundary)}</p>
    </section>
  `},S=e=>`
  <p class="result" data-tone="bad">${x(e)}</p>
`,Je=(e,t)=>{e.querySelectorAll(`[data-result-receipt]`).forEach(e=>{e.addEventListener(`click`,()=>{let n=e.dataset.resultReceipt||``;n&&!e.disabled&&t(n,e)})})},C=e=>String(e??``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),Ye=e=>e?`${e.slice(0,12)}…${e.slice(-8)}`:`not available`,Xe=e=>e.path_exposed===!1?String(e.label||`private local evidence`):[e.repository,e.commit_sha?`commit ${String(e.commit_sha).slice(0,12)}`:null,e.path,e.drive_file_id?`Drive ${e.drive_file_id}`:null,e.sheet_name,e.stable_key||e.content_key,e.missing_state].filter(Boolean).map(C).join(` · `)||C(e.locator_type||`logical`),Ze=e=>C(JSON.stringify(e,null,2)),Qe=e=>{let t=e.representations.filter(e=>e.state===`active`).length,n=e.missing.length;return!t&&n?`unable to determine`:n>t?`smaller bowl`:t>n?`larger bowl`:`unchanged bowl`},$e=e=>{let t=e.review,n=t?.review_stage||`identity`,r=e.edges.map(e=>e.edge_id).join(`|`),i=t?`
    <div class="graph-actions" data-review-stage="${C(n)}">
      <strong>${n===`identity`?`Review identity first`:`Review ${e.edges.length} bounded edges`}</strong>
      <div class="task-actions">
        <button data-representation-review="${C(t.review_id)}" data-scope="${n}" data-edge-ids="${C(r)}" data-decision="approve">Approve</button>
        <button data-representation-review="${C(t.review_id)}" data-scope="${n}" data-edge-ids="${C(r)}" data-decision="provisional_approve">Provisional</button>
        <button data-representation-review="${C(t.review_id)}" data-scope="${n}" data-edge-ids="${C(r)}" data-decision="hold">Hold</button>
        <button data-representation-review="${C(t.review_id)}" data-scope="${n}" data-edge-ids="${C(r)}" data-decision="request_evidence">Request evidence</button>
        <button data-representation-review="${C(t.review_id)}" data-scope="${n}" data-edge-ids="${C(r)}" data-decision="reject">Reject</button>
        <button data-representation-review="${C(t.review_id)}" data-scope="${n}" data-edge-ids="${C(r)}" data-decision="supersede">Supersede</button>
      </div>
      <small>${C(t.state)} · graph ${Ye(t.graph_sha256)}</small>
    </div>`:`<p class="muted">Review packet has not been staged.</p>`,a=e.representations.map(e=>`
    <tr>
      <td><strong>${C(e.representation_type)}</strong><small>${C(e.representation_id)}</small></td>
      <td>${Xe(e.locator)}</td>
      <td>${C(e.source_authority)}</td>
      <td>${Ye(e.content_sha256)}</td>
      <td>${C(e.confidence_class)} (${Math.round(e.confidence_numeric*100)}%)</td>
      <td><span class="state-chip" data-state="${C(e.state)}">${C(e.state)}</span></td>
      <td>${C(e.claim_boundary)}</td>
    </tr>`).join(``),o=e.edges.map(e=>`
    <tr>
      <td>${C(e.from_representation_id)}</td>
      <td><strong>${C(e.relation)}</strong></td>
      <td>${C(e.to_representation_id)}</td>
      <td>${C(e.evidence_bundle_id||`not required`)}</td>
      <td>${C(e.review_state)}</td>
      <td>${C(e.claim_boundary)}</td>
    </tr>`).join(``),s=e.missing.length?e.missing.map(e=>`
      <article class="missing-card">
        <strong>${C(e.type)} · ${C(e.missing_state)}</strong>
        <span><b>Why:</b> ${C(e.reason)}</span>
        <span><b>Next:</b> ${C(e.next_evidence_action)}</span>
        <small>Last search: ${C(e.last_search||`not recorded`)} · Floor: ${C(e.assigned_floor)} · Effect: ${C(e.dependency_effect)}</small>
      </article>`).join(``):`<p class="muted">No required representation is currently missing.</p>`,c=e.conflicts.length?e.conflicts.map(e=>`<article class="missing-card conflict"><strong>${C(e.edge_id)}</strong><span>${C(e.claim_boundary)}</span></article>`).join(``):`<p class="muted">No representation conflict is recorded.</p>`,l=e.horizons.length?e.horizons.map(e=>`
      <article class="horizon-card">
        <div><strong>${C(e.name)}</strong><span>${C(e.state)} · ${C(e.horizon_type)}</span></div>
        <p>${C(e.objective)}</p>
        <details><summary>Assumptions and constraints</summary><pre>${Ze({assumptions:e.assumptions,constraints:e.constraints})}</pre></details>
        <small>Input ${Ye(e.input_set_sha256)}</small>
      </article>`).join(``):`<p class="muted">No horizon is assigned.</p>`,u=e.representations.find(e=>e.representation_type===`recommendation`)?.locator.next_highest_value_question,d=(e.linked_objects||[]).length?(e.linked_objects||[]).map(t=>{let n=(e.linked_identifiers||[]).filter(e=>e.object_id===t.object_id).map(e=>`${e.namespace}: ${e.identifier_value}`).join(` | `);return`<article class="missing-card">
        <strong>${C(t.display_name)} · ${C(t.state)}</strong>
        <span><b>Object:</b> ${C(t.object_id)}</span>
        <span><b>Identifiers:</b> ${C(n||`none recorded`)}</span>
      </article>`}).join(``):`<p class="muted">No linked object identity is included.</p>`,f=(e.evidence_bundles||[]).length?(e.evidence_bundles||[]).map(e=>`
      <article class="horizon-card">
        <div><strong>${C(e.title)}</strong><span>${C(e.state)}</span></div>
        <p>${C(e.claim_boundary)}</p>
        <small>${e.independence_group_count} independence groups · ${e.duplicate_reference_count} duplicate references · confidence effect ${e.confidence_effect}</small>
        <details><summary>Source weight summary</summary><pre>${Ze(e.source_weight_summary)}</pre></details>
      </article>`).join(``):`<p class="muted">No evidence bundle is linked.</p>`;return`
    <article class="panel graph-panel" data-object-id="${C(e.object.object_id)}">
      <div class="panel-head">
        <div>
          <p class="eyebrow">${C(e.object.object_type)}</p>
          <h2>${C(e.object.display_name)}</h2>
          <p>${C(e.object.description)}</p>
        </div>
        <span class="badge">${C(e.canonical_state)}</span>
      </div>
      <div class="graph-summary">
        <div><span>Object ID</span><strong>${C(e.object.object_id)}</strong></div>
        <div><span>Authority</span><strong>${C(e.object.authority)}</strong></div>
        <div><span>Identity</span><strong>${C(e.object.identity_confidence_class)} · ${Math.round(e.object.identity_confidence_numeric*100)}%</strong></div>
        <div><span>Current horizon</span><strong>${C(e.horizons[0]?.name||`not assigned`)}</strong></div>
        <div><span>Judgment</span><strong>${Qe(e)}</strong></div>
      </div>
      <details open><summary>Identifiers (${e.identifiers.length})</summary><div class="identifier-list">${e.identifiers.map(e=>`<span><strong>${C(e.namespace)}</strong>${C(e.identifier_value)} · ${C(e.authority)}</span>`).join(``)}</div></details>
      <details open><summary>Linked identities (${(e.linked_objects||[]).length})</summary><div class="graph-grid">${d}</div></details>
      <details open><summary>Representations (${e.representations.length})</summary><div class="table-scroll"><table class="graph-table"><thead><tr><th>Type</th><th>Locator</th><th>Authority</th><th>Hash/revision</th><th>Confidence</th><th>State</th><th>Claim boundary</th></tr></thead><tbody>${a}</tbody></table></div></details>
      <details open><summary>Edges (${e.edges.length})</summary><div class="table-scroll"><table class="graph-table"><thead><tr><th>Source</th><th>Relation</th><th>Destination</th><th>Evidence</th><th>Review</th><th>Boundary</th></tr></thead><tbody>${o}</tbody></table></div></details>
      <details open><summary>Evidence bundles (${(e.evidence_bundles||[]).length})</summary>${f}</details>
      <div class="graph-grid">
        <section><h3>Missing</h3>${s}</section>
        <section><h3>Conflicts</h3>${c}</section>
      </div>
      <section><h3>Horizon</h3>${l}</section>
      <div class="next-question"><strong>Next highest-value question</strong><span>${C(u||`Owner review determines the next bounded question.`)}</span></div>
      ${i}
    </article>`},et=e=>e.length?e.map($e).join(``):`<article class="panel"><p class="muted">The feature-gated representation edge is disabled or unavailable.</p></article>`,w=e=>e.replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),tt=e=>`
  <article class="panel">
    <div class="panel-head">
      <div><p class="eyebrow">Type-I PrintSpace</p><h2>Universal 4D technology matrix</h2></div>
      <span class="badge">${e.metrics.archetypes} archetypes · ${e.metrics.universal_matrix_fields} fields</span>
    </div>
    <p class="muted">One Drive-owned evidence graph projected into volumetric build order, primitive/equivalent-network models, source-bound component instances and PC01 manufacturing packets. No duplicate catalogue is created here.</p>
    <div class="graph-summary">
      <div><strong>${e.metrics.archetypes}</strong><span>component archetypes</span></div>
      <div><strong>${e.metrics.directional_4d_fields}</strong><span>directional / 4D fields</span></div>
      <div><strong>${e.metrics.quantitative_factorization_fields}</strong><span>quantitative compiler fields</span></div>
      <div><strong>${e.metrics.primitive_basis_classes}</strong><span>primitive basis classes</span></div>\n      <div><strong>${e.metrics.equation_kernel_records}</strong><span>equation / constitutive kernels</span></div>
      <div><strong>${e.metrics.volumetric_topology_kernels}</strong><span>volumetric topology kernels</span></div>
      <div><strong>${e.metrics.topology_generic_fallback}</strong><span>intentional generic-coupled archetypes</span></div>
      <div><strong>${e.metrics.printable_4d_templates}</strong><span>derived printable 4D templates</span></div>
      <div><strong>${e.metrics.quantitative_invariants}</strong><span>quantitative invariants</span></div>
      <div><strong>${e.metrics.smart_stack_regions}</strong><span>dense smart-stack regions</span></div>
      <div><strong>${e.metrics.compound_decomposition_templates}</strong><span>compound-parent decomposition grammars</span></div>
      <div><strong>UTP-124/125/138/139</strong><span>stack + manufacturing + print-packet compiler</span></div>
      <div><strong>READ ONLY</strong><span>owner matrix remains Drive</span></div>
    </div>
    <div class="table-scroll"><table class="graph-table"><thead><tr><th>Surface</th><th>Role</th></tr></thead><tbody>
      ${e.surfaces.map(e=>`<tr><td><strong>${w(e.id)} · ${w(e.name)}</strong></td><td>${w(e.role)}</td></tr>`).join(``)}
    </tbody></table></div>
    <div class="boundary"><strong>${w(e.inference_example.label)}</strong><span>${w(e.inference_example.equation)} · ${w(e.inference_example.inputs)} → ${w(e.inference_example.result)}. ${w(e.inference_example.evidence)}</span></div>
    <p class="muted"><strong>Active contracts:</strong> ${e.contracts.map(w).join(` · `)}</p>
    <p class="muted">${w(e.boundary)}</p>
  </article>`,nt=async e=>tt(await e()),T=e=>e.replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),E=(e,t)=>`<div><strong>${T(String(e))}</strong><span>${T(t)}</span></div>`,rt=e=>`
  <section class="cgx-lens-panel active" data-cgx-lens-panel="overview">
    <div class="graph-summary">
      ${E(e.metrics.archetypes,`archetypes`)}
      ${E(e.metrics.matrix_fields,`matrix fields`)}
      ${E(e.metrics.equation_kernels,`equation kernels`)}
      ${E(e.metrics.volumetric_kernels,`volumetric kernels`)}
      ${E(e.metrics.printable_4d_templates,`printable 4D templates`)}
      ${E(e.metrics.quantitative_invariants,`quantitative invariants`)}
      ${E(e.metrics.smart_stack_regions,`smart-stack regions`)}
      ${E(e.metrics.compound_decomposition_templates,`compound decompositions`)}
      ${E(e.metrics.initial_instances,`proof instances`)}
      ${E(e.metrics.requirement_targets_open,`open target gates`)}
      ${E(e.metrics.physical_tests_run,`physical tests complete`)}
    </div>
    <div class="flow cgx-pipeline">
      ${e.pipeline.map(e=>`<span title="${T(e.contract)}">${T(e.label)} · ${T(e.state)}</span>`).join(`<i>→</i>`)}
    </div>
    <div class="boundary"><strong>${T(e.headline.state)}</strong><span>${T(e.headline.note)}</span></div>
  </section>`,it=e=>`
  <section class="cgx-lens-panel" data-cgx-lens-panel="instances" hidden>
    <div class="graph-summary">
      ${Object.entries(e.gate_counts).map(([e,t])=>E(t,e.replace(/_/g,` `).toLowerCase())).join(``)}
    </div>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>CGXI</th><th>Stage</th><th>Current gate</th><th>Target</th><th>Next evidence</th></tr></thead>
        <tbody>
          ${e.instances.map(e=>`<tr>
            <td><strong>${T(e.instance_id)}</strong><small class="cgx-uri">${T(e.binding_uri)}</small><small>${T(e.binding_progress)} · ${T(e.physical_state)}</small></td>
            <td>${T(e.proof_stage)}<br><small>${T(e.archetype)}</small></td>
            <td><span class="badge">${T(e.first_open_gate)}</span></td>
            <td>${T(e.target)}</td>
            <td>${T(e.next)}</td>
          </tr>`).join(``)}
        </tbody>
      </table>
    </div>
  </section>`,at=e=>`
  <section class="cgx-lens-panel" data-cgx-lens-panel="kernels" hidden>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>Kernel</th><th>Primitive</th><th>Model family</th><th>Inference gate</th></tr></thead>
        <tbody>
          ${e.kernels.map(e=>`<tr><td><strong>${T(e.kernel_id)}</strong></td><td>${T(e.primitive)}</td><td>${T(e.model)}</td><td>${T(e.gate)}</td></tr>`).join(``)}
        </tbody>
      </table>
    </div>
  </section>`,ot=e=>`
  <section class="cgx-lens-panel" data-cgx-lens-panel="volumetric" hidden>
    <div class="graph-summary">
      ${E(e.metrics.volumetric_kernels,`volumetric kernels`)}
      ${E(e.topology_coverage.specific_or_multi,`specific / explicit multi-kernel archetypes`)}
      ${E(e.topology_coverage.final_generic_only,`intentional generic-coupled archetypes`)}
      ${E(`${e.topology_coverage.baseline_generic_only} → ${e.topology_coverage.final_generic_only}`,`generic fallback refinement`)}
    </div>
    <div class="boundary"><strong>UTP-140 coverage closure</strong><span>${T(e.topology_coverage.rule)} Residual: ${e.topology_coverage.residual.map(T).join(` · `)}</span></div>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>Kernel</th><th>Primitive</th><th>Topology / geometry</th><th>Compiler token</th><th>Numeric gate</th></tr></thead>
        <tbody>
          ${e.volumetric_kernels.map(e=>`<tr><td><strong>${T(e.kernel_id)}</strong></td><td>${T(e.primitive)}</td><td>${T(e.topology)}</td><td><small class="cgx-uri">${T(e.token)}</small></td><td>${T(e.gate)}</td></tr>`).join(``)}
        </tbody>
      </table>
    </div>
  </section>`,st=e=>`
  <section class="cgx-lens-panel" data-cgx-lens-panel="printable" hidden>
    <div class="panel-head">
      <div><p class="eyebrow">UTP-138 · BUILD-070</p><h3>Printable 4D component + stack packets</h3></div>
      <span class="badge">${T(e.printable_4d.state)}</span>
    </div>
    <div class="graph-summary">
      ${E(e.printable_4d.template_count,`derived catalogue templates`)}
      ${E(e.printable_4d.exact_instance_inputs,`current exact-instance inputs`)}
      ${E(e.printable_4d.coupled_stack_kernel,`coupled stack kernel`)}
      ${E(`READ ONLY`,`no machine authority`)}
    </div>
    <p class="muted">Schemas: ${T(e.printable_4d.packet_schema)} · ${T(e.printable_4d.stack_schema)} · ${T(e.printable_4d.catalogue_schema)}</p>
    <div class="two-column">
      <div>
        <strong>Print paths</strong>
        <div class="stack-list">
          ${e.printable_4d.print_paths.map(e=>`<article class="task-card"><div><strong>${T(e.id)}</strong><small>${T(e.role)}</small></div></article>`).join(``)}
        </div>
      </div>
      <div>
        <strong>Exact packet examples</strong>
        <div class="stack-list">
          ${e.printable_4d.exact_examples.map(e=>`<article class="task-card"><div><strong>${T(e.instance_id)}</strong><span>${T(e.state)}</span><small>${T(e.topology)} · next: ${T(e.next_gate)}</small></div></article>`).join(``)}
        </div>
      </div>
    </div>
    <div class="boundary"><strong>Compiler invariants</strong><span>${e.printable_4d.invariants.map(T).join(` · `)}</span></div>
    <div class="boundary"><strong>${String(e.printable_4d.compound_decomposition.count)} compound-parent grammars</strong><span>${T(e.printable_4d.compound_decomposition.state)} · ${e.printable_4d.compound_decomposition.parents.map(T).join(` · `)}</span></div>
    <p class="muted">${T(e.printable_4d.compound_decomposition.rule)}</p>
  </section>`,ct=e=>`
  <section class="cgx-lens-panel" data-cgx-lens-panel="smartstack" hidden>
    <div class="panel-head">
      <div><p class="eyebrow">UTP-139 · BUILD-071</p><h3>Quantitative invariants + dense 4D smart stack</h3></div>
      <span class="badge">${T(e.quantitative_invariants.state)}</span>
    </div>
    <div class="graph-summary">
      ${E(e.metrics.quantitative_invariants,`reusable invariants`)}
      ${E(e.metrics.smart_stack_regions,`smart-stack regions`)}
      ${E(e.dense_smart_stack.coupled_kernel,`coupled assembly kernel`)}
      ${E(`NUMERIC_IF`,`evidence/regime conditional`)}
    </div>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>Invariant</th><th>Role</th><th>Equation</th><th>Current bounded example</th><th>Gate</th></tr></thead>
        <tbody>
          ${e.quantitative_invariants.records.map(e=>`<tr><td><strong>${T(e.id)}</strong></td><td>${T(e.role)}</td><td><small class="cgx-uri">${T(e.equation)}</small></td><td>${T(e.example)}</td><td>${T(e.gate)}</td></tr>`).join(``)}
        </tbody>
      </table>
    </div>
    <div class="boundary"><strong>Invariant rule</strong><span>${T(e.quantitative_invariants.rule)}</span></div>
    <p class="muted"><strong>Smart-stack:</strong> <span class="cgx-uri">${T(e.dense_smart_stack.cgx_uri)}</span> · ${T(e.dense_smart_stack.state)}</p>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>Region</th><th>Functional role</th><th>Topology kernels</th><th>State</th></tr></thead>
        <tbody>
          ${e.dense_smart_stack.regions.map(e=>`<tr><td><strong>${T(e.id)}</strong></td><td>${T(e.role)}</td><td><small class="cgx-uri">${T(e.kernels)}</small></td><td><span class="badge">${T(e.state)}</span></td></tr>`).join(``)}
        </tbody>
      </table>
    </div>
    <div class="boundary"><strong>Stack rule</strong><span>${T(e.dense_smart_stack.rule)}</span></div>
  </section>`,lt=e=>`
  <section class="cgx-lens-panel" data-cgx-lens-panel="showcase" hidden>
    <div class="panel-head">
      <div><p class="eyebrow">Public-safe candidate</p><h3>${T(e.showcase.title)}</h3></div>
      <span class="badge">${T(e.showcase.publication_state)}</span>
    </div>
    <p>${T(e.showcase.summary)}</p>
    <div class="graph-summary">${e.showcase.metrics.map(({value:e,label:t})=>E(e,t)).join(``)}</div>
    <div class="two-column">
      <div><strong>Safe showcase points</strong><ul class="compact-list">${e.showcase.safe_points.map(e=>`<li>${T(e)}</li>`).join(``)}</ul></div>
      <div><strong>Excluded from publication</strong><ul class="compact-list">${e.showcase.excludes.map(e=>`<li>${T(e)}</li>`).join(``)}</ul></div>
    </div>
  </section>`,ut=e=>`
  <article class="panel cgx-review-lens">
    <div class="panel-head">
      <div><p class="eyebrow">.cgx interactive review lens</p><h2>${T(e.headline.title)}</h2></div>
      <span class="badge">${T(e.authority.queue_id)} · ${T(e.authority.physical_state)}</span>
    </div>
    <p class="muted">Drive remains engineering/evidence authority. This local UI is a read-only projection over existing CGXI, UTP and manufacturing contracts.</p>
    <div class="cgx-lens-tabs" role="tablist" aria-label="CGX review lens">
      <button class="active" type="button" data-cgx-lens="overview">Overview</button>
      <button type="button" data-cgx-lens="instances">CGXI queue</button>
      <button type="button" data-cgx-lens="kernels">Equation kernels</button>
      <button type="button" data-cgx-lens="volumetric">Volumetric kernels</button>
      <button type="button" data-cgx-lens="printable">Printable 4D</button>
      <button type="button" data-cgx-lens="smartstack">Invariants + Smart Stack</button>
      <button type="button" data-cgx-lens="showcase">Showcase-safe</button>
    </div>
    ${rt(e)}
    ${it(e)}
    ${at(e)}
    ${ot(e)}
    ${st(e)}
    ${ct(e)}
    ${lt(e)}
    <p class="muted">${T(e.boundary)}</p>
  </article>`,dt=e=>{let t=[...e.querySelectorAll(`[data-cgx-lens]`)],n=[...e.querySelectorAll(`[data-cgx-lens-panel]`)],r=e=>{t.forEach(t=>{let n=t.dataset.cgxLens===e;t.classList.toggle(`active`,n),t.setAttribute(`aria-selected`,String(n))}),n.forEach(t=>{let n=t.dataset.cgxLensPanel===e;t.classList.toggle(`active`,n),t.hidden=!n})};t.forEach(e=>e.addEventListener(`click`,()=>r(e.dataset.cgxLens||`overview`))),r(`overview`)},ft=async e=>{let t=await e();return{data:t,html:ut(t)}},D=e=>e.replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),pt=(e,t)=>[e[1]*t[2]-e[2]*t[1],e[2]*t[0]-e[0]*t[2],e[0]*t[1]-e[1]*t[0]],mt=(e,t)=>[e[0]-t[0],e[1]-t[1],e[2]-t[2]],ht=e=>Math.hypot(e[0],e[1],e[2])||1,gt=e=>{let t=ht(e);return[e[0]/t,e[1]/t,e[2]/t]},_t=(e,t)=>e[0]*t[0]+e[1]*t[1]+e[2]*t[2],vt=(e,t=0,n=1)=>Math.max(t,Math.min(n,e)),yt=(e,t,n)=>{let r=t*Math.PI/180,i=n*Math.PI/180,a=e[0]*Math.cos(i)-e[1]*Math.sin(i),o=e[0]*Math.sin(i)+e[1]*Math.cos(i),s=e[2];return[a,o*Math.cos(r)-s*Math.sin(r),o*Math.sin(r)+s*Math.cos(r)]},bt=(e,t,n)=>e.map((e,r)=>Math.round(e+(t[r]-e)*n)),xt=e=>`rgb(${e[0]},${e[1]},${e[2]})`,St=(e,t,n)=>{let r=e.getContext(`2d`);if(!r)return;let i=Math.min(window.devicePixelRatio||1,2),a=Math.max(e.clientWidth,320),o=Math.max(e.clientHeight,320),s=Math.round(a*i),c=Math.round(o*i);(e.width!==s||e.height!==c)&&(e.width=s,e.height=c),r.setTransform(i,0,0,i,0,0);let l=a,u=o;r.clearRect(0,0,l,u);let d=r.createRadialGradient(l*.58,u*.42,20,l*.55,u*.45,Math.max(l,u)*.75);d.addColorStop(0,`#173033`),d.addColorStop(.55,`#0c191b`),d.addColorStop(1,`#050a0b`),r.fillStyle=d,r.fillRect(0,0,l,u),r.strokeStyle=`rgba(41,64,67,.25)`,r.lineWidth=1;for(let e=0;e<l;e+=48)r.beginPath(),r.moveTo(e,0),r.lineTo(e,u),r.stroke();for(let e=0;e<u;e+=48)r.beginPath(),r.moveTo(0,e),r.lineTo(l,e),r.stroke();let f=t.vertices.map(e=>yt(e,n.elev,n.azim)),p=1/0,m=-1/0,h=1/0,g=-1/0,_=1/0,v=-1/0;for(let e of f)p=Math.min(p,e[0]),m=Math.max(m,e[0]),h=Math.min(h,e[1]),g=Math.max(g,e[1]),_=Math.min(_,e[2]),v=Math.max(v,e[2]);let ee=Math.max(m-p,1e-9),te=Math.max(g-h,1e-9),ne=Math.max(v-_,1e-9),re=Math.min(l*.78/ee,u*.72/te)*n.zoom,y=l*.53,ie=u*.53,ae=Math.max(ee,te,ne)*7.5,oe=f.map(e=>{let t=e[2]-(_+v)/2,n=ae/(ae-t);return[y+(e[0]-(p+m)/2)*re*n,ie-(e[1]-(h+g)/2)*re*n,e[2]]}),se=gt([-.45,-.35,.82]),ce=gt([.6,-.2,.5]),le=gt([.25,.8,.5]),ue=t.faces.map(e=>{let t=f[e[0]],n=f[e[1]],r=f[e[2]],i=gt(pt(mt(n,t),mt(r,t)));return{t:e,z:(t[2]+n[2]+r[2])/3,intensity:vt(.16+.58*Math.abs(_t(i,se))+.16*Math.abs(_t(i,ce))+.1*Math.abs(_t(i,le)),.12,1)}}).sort((e,t)=>e.z-t.z);r.save(),r.shadowColor=`rgba(0,0,0,.4)`,r.shadowBlur=24,r.fillStyle=`rgba(0,0,0,.3)`,r.beginPath(),r.ellipse(y,u*.82,Math.min(l*.27,380)*n.zoom,Math.max(20,u*.035)*n.zoom,0,0,Math.PI*2),r.fill(),r.restore();let de=[17,38,41],fe=[92,222,214],pe=[200,164,88],me=Math.max(1,Math.ceil(ue.length/9e3));for(let e=0;e<ue.length;e+=me){let{t,intensity:n}=ue[e],i=oe[t[0]],a=oe[t[1]],o=oe[t[2]],s=bt(de,fe,n);n>.82&&(s=bt(s,pe,.12)),r.beginPath(),r.moveTo(i[0],i[1]),r.lineTo(a[0],a[1]),r.lineTo(o[0],o[1]),r.closePath(),r.fillStyle=xt(s),r.fill(),r.strokeStyle=`rgba(120,227,221,.15)`,r.lineWidth=.55,r.stroke()}r.fillStyle=`#aab9b8`,r.font=`12px ui-monospace, SFMono-Regular, Consolas, monospace`,r.fillText(`az ${n.azim.toFixed(0)}° · el ${n.elev.toFixed(0)}° · zoom ${n.zoom.toFixed(2)}×`,16,u-18)},Ct=()=>`
  <div class="mesh-viewer-dialog" role="dialog" aria-modal="true" aria-label="Interactive source mesh review">
    <div class="mesh-viewer-head">
      <div><p class="eyebrow">source-hashed interactive geometry</p><h3 data-mesh-title>Object</h3></div>
      <button type="button" class="mesh-viewer-close" aria-label="Close interactive mesh">×</button>
    </div>
    <div class="mesh-viewer-canvas-wrap"><canvas class="mesh-viewer-canvas"></canvas></div>
    <div class="mesh-viewer-foot">
      <div><strong data-mesh-state>REVIEW ONLY</strong><small data-mesh-source></small><small data-mesh-hash></small></div>
      <div class="mesh-viewer-help">Drag to orbit · wheel to zoom · double-click to reset</div>
    </div>
  </div>`,O=null,k=null,wt=()=>{if(O)return O;O=document.createElement(`div`),O.className=`mesh-viewer-modal`,O.hidden=!0,O.innerHTML=Ct(),document.body.append(O);let e=()=>{O&&(O.hidden=!0,k?.abort(),k=null,document.body.classList.remove(`mesh-viewer-open`))};return O.querySelector(`.mesh-viewer-close`)?.addEventListener(`click`,e),O.addEventListener(`click`,t=>{t.target===O&&e()}),window.addEventListener(`keydown`,t=>{t.key===`Escape`&&O&&!O.hidden&&e()}),O},Tt=async e=>{let t=wt();k?.abort(),k=new AbortController,t.hidden=!1,document.body.classList.add(`mesh-viewer-open`);let n=t.querySelector(`[data-mesh-title]`),r=t.querySelector(`[data-mesh-state]`),i=t.querySelector(`[data-mesh-source]`),a=t.querySelector(`[data-mesh-hash]`),o=t.querySelector(`.mesh-viewer-canvas`);if(!o)return;n&&(n.textContent=e.label),r&&(r.textContent=e.physicalState),i&&(i.textContent=e.source),a&&(a.textContent=e.sourceHash?`source SHA-256 ${e.sourceHash}`:`source hash in mesh payload`);let s=o.getContext(`2d`);s&&(s.fillStyle=`#071011`,s.fillRect(0,0,o.width,o.height));let c;try{let t=await fetch(e.url,{cache:`no-store`,signal:k.signal});if(!t.ok)throw Error(`mesh payload HTTP ${t.status}`);c=await t.json()}catch(e){if(e.name===`AbortError`)return;s&&(s.fillStyle=`#e27e7e`,s.font=`16px sans-serif`,s.fillText(`Interactive mesh unavailable.`,20,36));return}let l={elev:22,azim:-38,zoom:1},u=!1,d=0,f=0,p=0,m=()=>{cancelAnimationFrame(p),p=requestAnimationFrame(()=>St(o,c,l))},h=()=>{l.elev=22,l.azim=-38,l.zoom=1,m()},g=e=>{u=!0,d=e.clientX,f=e.clientY,o.setPointerCapture(e.pointerId)},_=e=>{if(!u)return;let t=e.clientX-d,n=e.clientY-f;d=e.clientX,f=e.clientY,l.azim+=t*.35,l.elev=Math.max(-85,Math.min(85,l.elev+n*.28)),m()},v=()=>{u=!1};o.onpointerdown=g,o.onpointermove=_,o.onpointerup=v,o.onpointercancel=v,o.onwheel=e=>{e.preventDefault(),l.zoom=Math.max(.35,Math.min(4,l.zoom*Math.exp(-e.deltaY*.001))),m()},o.ondblclick=h,new ResizeObserver(m).observe(o),m()},Et=e=>`
  <button type="button" class="button-secondary mesh-viewer-trigger"
    data-mesh-url="${D(e.url)}"
    data-mesh-label="${D(e.label)}"
    data-mesh-source="${D(e.source)}"
    data-mesh-hash="${D(e.sourceHash||``)}"
    data-mesh-state="${D(e.physicalState)}">Interactive 3D</button>`,Dt=e=>{e.querySelectorAll(`.mesh-viewer-trigger`).forEach(e=>{e.addEventListener(`click`,()=>void Tt({url:e.dataset.meshUrl||``,label:e.dataset.meshLabel||`Object`,source:e.dataset.meshSource||``,sourceHash:e.dataset.meshHash||``,physicalState:e.dataset.meshState||`REVIEW ONLY`}))})},A=e=>e.replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&apos;`),Ot=(e,t=58,n=5)=>{let r=(e||`UNRESOLVED`).replace(/\s+/g,` `).trim().split(` `),i=[],a=``;for(let e of r){let r=(a+` `+e).trim();if(r.length>t&&a?(i.push(a),a=e):a=r,i.length>=n)break}return i.length<n&&a&&i.push(a),i.slice(0,n)},j=(e,t,n,r,i=58)=>{let a=Ot(r,i,4);return`<g transform="translate(${e} ${t})"><text class="kicker" x="0" y="0">${A(n)}</text>${a.map((e,t)=>`<text class="body" x="0" y="${54+t*44}">${A(e)}</text>`).join(``)}</g>`},kt=e=>{let t=[e.Domain,e.Family,e[`Component Archetype`],e[`Primary Physics`]].filter(Boolean).join(` `).toLowerCase();return t.includes(`diode`)||t.includes(`semiconductor`)?`<g class="motif"><rect x="1330" y="650" width="1180" height="700" rx="80" class="shell"/><path d="M1550 1000h310l220-180v360l-220-180h-310M2080 820v360M2080 1000h290" class="active"/><circle cx="1550" cy="1000" r="34" class="port"/><circle cx="2370" cy="1000" r="34" class="port"/></g>`:t.includes(`resistor`)||t.includes(`resistive`)?`<g class="motif"><path d="M1450 1000h180l90-150 130 300 130-300 130 300 130-300 130 300 90-150h180" class="active"/><rect x="1330" y="710" width="1180" height="580" rx="80" class="shell"/></g>`:t.includes(`capacitor`)||t.includes(`capacitive`)||t.includes(`dielectric`)?`<g class="motif"><rect x="1540" y="720" width="180" height="560" rx="25" class="active fill"/><rect x="2120" y="720" width="180" height="560" rx="25" class="active fill"/><rect x="1780" y="760" width="280" height="480" rx="35" class="dielectric"/><path d="M1380 1000h160M2300 1000h160" class="active"/></g>`:t.includes(`inductor`)||t.includes(`coil`)||t.includes(`solenoid`)||t.includes(`magnetic`)?`<g class="motif"><path d="M1370 1000h170c0-170 230-170 230 0s230 170 230 0 230-170 230 0 230 170 230 0h160" class="active"/><rect x="1500" y="690" width="850" height="620" rx="150" class="shell"/></g>`:t.includes(`rf`)||t.includes(`antenna`)||t.includes(`resonator`)?`<g class="motif"><ellipse cx="1920" cy="1000" rx="650" ry="390" class="active"/><ellipse cx="1920" cy="1000" rx="450" ry="250" class="shell"/><path d="M1920 1390v210M1920 1600h430" class="active"/><path d="M1550 1000c180-180 560-180 740 0M1610 1110c150-120 470-120 620 0" class="field"/></g>`:t.includes(`fluid`)||t.includes(`channel`)||t.includes(`valve`)||t.includes(`pump`)?`<g class="motif"><rect x="1350" y="730" width="1140" height="540" rx="160" class="shell"/><path d="M1450 1000h330c90 0 120-170 210-170s120 340 210 340 120-170 210-170h160" class="fluid"/><circle cx="1920" cy="1000" r="120" class="active"/></g>`:t.includes(`optical`)||t.includes(`photon`)||t.includes(`laser`)||t.includes(`led`)?`<g class="motif"><rect x="1400" y="800" width="1040" height="400" rx="80" class="shell"/><path d="M1470 1000c220-260 420 260 640 0s420 260 640 0" class="optical"/><path d="M1560 780l-90-170M1710 800l-20-190M2280 800l100-170" class="field"/></g>`:t.includes(`mechanical`)||t.includes(`structure`)||t.includes(`frame`)||t.includes(`lattice`)?`<g class="motif"><rect x="1390" y="720" width="1060" height="560" rx="50" class="shell"/><path d="M1390 720l1060 560M2450 720L1390 1280M1390 1000h1060M1920 720v560" class="active"/></g>`:t.includes(`energy`)||t.includes(`battery`)||t.includes(`electrochemical`)?`<g class="motif"><rect x="1460" y="720" width="920" height="560" rx="70" class="shell"/><rect x="1550" y="810" width="180" height="380" class="active fill"/><rect x="1810" y="810" width="220" height="380" class="dielectric"/><rect x="2110" y="810" width="180" height="380" class="active fill"/><path d="M2290 880h180v240h-180" class="active"/></g>`:`<g class="motif"><rect x="1390" y="720" width="1060" height="560" rx="90" class="shell"/><circle cx="1920" cy="1000" r="250" class="active"/><path d="M1390 1000h280M2170 1000h280M1920 720v180M1920 1100v180" class="field"/></g>`},At=e=>`<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160" viewBox="0 0 3840 2160">
<defs>
  <radialGradient id="bg" cx="56%" cy="43%" r="80%"><stop offset="0" stop-color="#173033"/><stop offset=".55" stop-color="#0c191b"/><stop offset="1" stop-color="#050a0b"/></radialGradient>
  <filter id="glow"><feGaussianBlur stdDeviation="12" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<style>
  .title{font:700 92px Inter,Segoe UI,sans-serif;fill:#f2ede7;letter-spacing:-2px}.sub{font:500 36px Inter,Segoe UI,sans-serif;fill:#aab9b8}.kicker{font:700 24px Inter,Segoe UI,sans-serif;fill:#55d6cf;letter-spacing:3px}.body{font:500 30px Inter,Segoe UI,sans-serif;fill:#f2ede7}.mono{font:500 27px ui-monospace,SFMono-Regular,Consolas,monospace;fill:#aab9b8}.active{fill:none;stroke:#55d6cf;stroke-width:26;stroke-linecap:round;stroke-linejoin:round}.fill{fill:#123a3b;stroke:#55d6cf}.shell{fill:#0f1b1c;stroke:#294043;stroke-width:12}.dielectric{fill:#c8a45822;stroke:#c8a458;stroke-width:16}.field{fill:none;stroke:#c8a458;stroke-width:13;stroke-dasharray:26 22}.fluid{fill:none;stroke:#76d39b;stroke-width:30;stroke-linecap:round}.optical{fill:none;stroke:#e9d28d;stroke-width:22;filter:url(#glow)}.port{fill:#071011;stroke:#c8a458;stroke-width:16}.warn{font:700 24px Inter,Segoe UI,sans-serif;fill:#e27e7e;letter-spacing:2px}
</style>
<rect width="3840" height="2160" fill="url(#bg)"/>
<g opacity=".22" stroke="#294043" stroke-width="2">${Array.from({length:25},(e,t)=>`<path d="M${t*160} 0v2160"/>`).join(``)}${Array.from({length:15},(e,t)=>`<path d="M0 ${t*160}h3840"/>`).join(``)}</g>
<text x="180" y="180" class="kicker">RÖMER / COGNIGREX · CGX COMPONENT REVIEW</text>
<text x="180" y="305" class="title">${A(e[`Component Archetype`]||e.ID)}</text>
<text x="180" y="380" class="sub">${A(e.ID)} · ${A(e.Domain||`UNRESOLVED DOMAIN`)} · ${A(e.Family||`UNRESOLVED FAMILY`)}</text>
<text x="3660" y="180" text-anchor="end" class="warn">SYMBOLIC 4K PLATE · NOT RELEASED GEOMETRY</text>
${kt(e)}
<g transform="translate(180 540)">
  ${j(0,0,`PRIMARY FUNCTION`,e[`Primary Function`],50)}
  ${j(0,330,`BUILD CLASS / ROUTE`,`${e[`Current CGX Build Class`]||``} · ${e[`Current Manufacturing Route`]||``}`,50)}
  ${j(0,660,`BASELINE GEOMETRY`,e[`Baseline Geometry`],50)}
  ${j(0,990,`GEOMETRIC PARAMETERS`,e[`Geometric Parameters`],50)}
</g>
<g transform="translate(2720 540)">
  ${j(0,0,`PHYSICS / MODEL`,`${e[`Primary Physics`]||``} · ${e[`Baseline Model / Equation`]||``}`,47)}
  ${j(0,330,`MATERIAL STACK`,e[`Typical Material Stack`],47)}
  ${j(0,660,`INTERFACES / 4D`,`${e[`Ports / Interfaces`]||``} · ${e[`4D Fields`]||``}`,47)}
  ${j(0,990,`TEST / FAILURE`,`${e[`Acceptance Tests`]||``} · ${e[`Failure Modes`]||``}`,47)}
</g>
<rect x="180" y="1960" width="3480" height="90" rx="24" fill="#0f1b1c" stroke="#294043" stroke-width="4"/>
<text x="225" y="2018" class="mono">EVIDENCE: ${A(e[`Evidence State`]||`UNRESOLVED`)} · AUTHORITY: ${A(e[`Source Authority Class`]||`UNRESOLVED`)} · SCALE: ${A(e[`Scale Band`]||`UNRESOLVED`)}</text>
<text x="225" y="2085" class="mono">Visual form is corpus-derived symbolic topology. Exact CGXI/source/lot/geometry/process/tool/calibration/test evidence governs realization.</text>
</svg>`,jt=e=>{let t=At(e),n=new Blob([t],{type:`image/svg+xml`}),r=URL.createObjectURL(n);window.open(r,`_blank`,`noopener,noreferrer`)?window.setTimeout(()=>URL.revokeObjectURL(r),6e4):URL.revokeObjectURL(r)},Mt=e=>`<button type="button" class="button-secondary component-plate-trigger" data-component-id="${A(e)}">4K symbolic</button>`,Nt=(e,t)=>{let n=new Map(t.map(e=>[e.ID,e]));e.querySelectorAll(`.component-plate-trigger`).forEach(e=>{e.addEventListener(`click`,()=>{let t=n.get(e.dataset.componentId||``);t&&jt(t)})})},M=e=>e.replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),N=(e,t)=>`<div><strong>${M(String(e))}</strong><span>${M(t)}</span></div>`,Pt=e=>{let t=e.hero_render||e.render,n=[e.hero_render?`<a class="button-secondary" href="${M(e.hero_render)}" target="_blank" rel="noreferrer">4K hero</a>`:``,`<a class="button-secondary" href="${M(e.render)}" target="_blank" rel="noreferrer">Engineering plate</a>`,e.mesh_data?Et({url:e.mesh_data,label:e.label,source:e.source,sourceHash:e.source_sha256,physicalState:e.physical_state}):``].filter(Boolean).join(``);return`
  <article class="object-review-card" data-review-object data-search="${M([e.id,e.label,e.role,e.level,e.geometry_state,e.physical_state].join(` `).toLowerCase())}">
    <a href="${M(t)}" target="_blank" rel="noreferrer">
      <img src="${M(t)}" loading="lazy" alt="${M(e.label)} source-faithful review render" />
    </a>
    <div class="object-review-copy">
      <div class="panel-head">
        <div><p class="eyebrow">${M(e.level)}</p><h3>${M(e.label)}</h3></div>
        <span class="badge">${M(e.physical_state)}</span>
      </div>
      <p>${M(e.role)}</p>
      <small class="cgx-uri">${M(e.source)}</small>
      <div class="object-review-state"><strong>${M(e.geometry_state)}</strong></div>
      ${e.render_state?`<small>${M(e.render_state)}</small>`:``}
      ${e.stats?`<small>${e.stats.vertices.toLocaleString()} vertices · ${e.stats.faces.toLocaleString()} triangles</small>`:``}
      ${e.source_sha256?`<small class="cgx-uri">source SHA-256 ${M(e.source_sha256.slice(0,24))}…</small>`:``}
      <div class="object-review-actions">${n}</div>
      <ul class="compact-list">${e.review_rules.map(e=>`<li>${M(e)}</li>`).join(``)}</ul>
    </div>
  </article>`},Ft=e=>`
  <div class="object-catalogue-controls">
    <input id="object-catalogue-filter" type="search" placeholder="Filter 411 components by ID, family, geometry, route, physics…" />
    <span class="badge" id="object-catalogue-count">${e.records.length} / ${e.records.length}</span>
  </div>
  <div class="table-scroll">
    <table class="graph-table object-catalogue-table">
      <thead><tr><th>ID</th><th>Component</th><th>Build / route</th><th>Geometry</th><th>4D / physics</th><th>Evidence</th></tr></thead>
      <tbody>
        ${e.records.map(e=>`<tr data-printable-row data-search="${M([e.ID,e.Domain,e.Family,e[`Component Archetype`],e[`Current CGX Build Class`],e[`Current Manufacturing Route`],e[`Baseline Geometry`],e[`Primary Physics`],e[`4D Fields`]].filter(Boolean).join(` `).toLowerCase())}">
          <td><strong>${M(e.ID)}</strong><small>${M(e.Domain||``)}</small>${Mt(e.ID)}</td>
          <td>${M(e[`Component Archetype`]||``)}<small>${M(e.Family||``)} · ${M(e[`Primary Function`]||``)}</small></td>
          <td><span class="badge">${M(e[`Current CGX Build Class`]||``)}</span><small>${M(e[`Current Manufacturing Route`]||``)}</small></td>
          <td>${M(e[`Baseline Geometry`]||``)}<small>${M(e[`Geometric Parameters`]||``)}</small></td>
          <td>${M(e[`Primary Physics`]||``)}<small>${M(e[`4D Fields`]||``)}</small></td>
          <td>${M(e[`Evidence State`]||``)}<small>${M(e[`Source Authority Class`]||``)}</small></td>
        </tr>`).join(``)}
      </tbody>
    </table>
  </div>`,It=(e,t)=>`
  <article class="panel object-review-panel">
    <div class="panel-head">
      <div><p class="eyebrow">CGX object review catalogue</p><h2>Component → stack → Luke / Mark / InterSol</h2></div>
      <span class="badge">${M(e.status)}</span>
    </div>
    <p class="muted">${M(e.authority)}</p>
    <div class="graph-summary">
      ${N(e.coverage.printable_4d_archetypes,`component archetypes`)}
      ${N(e.coverage.symbolic_core_component_stack_plates,`CGX symbolic plates`)}
      ${N(e.coverage.source_mesh_4k_hero_views??e.coverage.macro_source_meshes,`4K source-mesh heroes`)}
      ${N(e.coverage.source_mesh_interactive_views??e.coverage.macro_source_meshes,`interactive source meshes`)}
      ${N(e.coverage.symbolic_system_lineage_plates??0,`system lineage plates`)}
      ${N(e.coverage.physical_tests_complete,`physical tests complete`)}
    </div>
    <div class="flow">${e.tiers.map(e=>`<span title="${M(e.description)}">${M(e.id)} · ${M(e.label)}</span>`).join(`<i>→</i>`)}</div>
    <div class="boundary"><strong>Visual rule</strong><span>${M(e.visual_system.rule)}</span></div>

    <div class="cgx-lens-tabs object-review-tabs" role="tablist" aria-label="Object review catalogue">
      <button class="active" type="button" data-object-review-tab="gallery">Review plates</button>
      <button type="button" data-object-review-tab="catalogue">411 component catalogue</button>
      <button type="button" data-object-review-tab="frontier">Current frontier</button>
    </div>

    <section data-object-review-panel="gallery">
      <div class="object-review-search"><input id="object-review-filter" type="search" placeholder="Filter review plates…" /></div>
      <h3>CGX-derived component / stack plates</h3>
      <div class="object-review-grid">${e.micro_review_objects.map(Pt).join(``)}</div>
      <h3>System lineage / bridge plates</h3>
      <div class="object-review-grid">${(e.bridge_review_objects||[]).map(Pt).join(``)}</div>
      <h3>Corpus source meshes</h3>
      <div class="object-review-grid">${e.macro_review_objects.map(Pt).join(``)}</div>
    </section>

    <section data-object-review-panel="catalogue" hidden>
      <div class="boundary"><strong>${M(t.schema)}</strong><span>Canonical component atlas exposed as a read-only UniSpace projection. Printable-4D packet, topology and invariant semantics remain in the adjacent CGX lens rather than being duplicated here.</span></div>
      ${Ft(t)}
    </section>

    <section data-object-review-panel="frontier" hidden>
      <div class="stack-list">
        ${e.pending_owner_layers.map(e=>`<article class="task-card"><div><strong>Current owner frontier</strong><small>${M(e)}</small></div></article>`).join(``)}
      </div>
      <div class="boundary"><strong>Evidence boundary</strong><span>${M(e.boundary)}</span></div>
    </section>
  </article>`,Lt=(e,t)=>{let n=[...e.querySelectorAll(`[data-object-review-tab]`)],r=[...e.querySelectorAll(`[data-object-review-panel]`)],i=e=>{n.forEach(t=>t.classList.toggle(`active`,t.dataset.objectReviewTab===e)),r.forEach(t=>t.hidden=t.dataset.objectReviewPanel!==e)};n.forEach(e=>e.addEventListener(`click`,()=>i(e.dataset.objectReviewTab||`gallery`))),i(`gallery`);let a=e.querySelector(`#object-review-filter`),o=[...e.querySelectorAll(`[data-review-object]`)];a?.addEventListener(`input`,()=>{let e=(a.value||``).trim().toLowerCase();o.forEach(t=>t.hidden=!!e&&!(t.dataset.search||``).includes(e))});let s=e.querySelector(`#object-catalogue-filter`),c=[...e.querySelectorAll(`[data-printable-row]`)],l=e.querySelector(`#object-catalogue-count`);s?.addEventListener(`input`,()=>{let e=(s.value||``).trim().toLowerCase(),t=0;c.forEach(n=>{let r=!e||(n.dataset.search||``).includes(e);n.hidden=!r,r&&(t+=1)}),l&&(l.textContent=`${t} / ${c.length}`)}),Dt(e),Nt(e,t.records)},Rt=async(e,t)=>{let[n,r]=await Promise.all([e(),t()]);return{manifest:n,atlas:r,html:It(n,r)}},zt=[[`LightSpeed Git`,`https://github.com/achillesromer-coder/LightSpeed`,`Versioned implementation and receipts`],[`Type 1 Digital Review`,`https://github.com/achillesromer-coder/LightSpeed/pull/46`,`Draft 3D, six-view and T1-00..07 review packages`],[`Type 1 Römer Canon`,`https://docs.google.com/spreadsheets/d/1refNFmebTcmPVojCuZsyILJEWaKz-sVzYLfZtqMl8k8/edit`,`Living programme, evidence, handoff and release gates`],[`ACR3 Handoffs`,`https://docs.google.com/spreadsheets/d/1AgAhLPNtrO91C_-ea7EdOkOsyXrCCYvFVvmDSGq8uls/edit`,`Append-only cross-corpus reconciliation receipts`],[`LS GO Queue`,`https://docs.google.com/spreadsheets/d/1f5i4V3FshYHkztv3_HAg0ZofUl0sdcJZcwrlesUlCfM/edit`,`Phone tasks, approvals, commands, results and sync health`],[`Portfolio Handoff`,`https://docs.google.com/document/d/1tsDkb79UVX_SqS2-oBgc5DHb89QIlH3DcmKMN77hdOo/edit`,`Cross-chat portfolio continuity`],[`Römer Industries`,`https://romer.industries`,`Reviewed public portfolio surface`]],Bt=[{name:`Central Facility Boundary`,radiusM:2500,description:`All facilities and buildings remain inside this radius.`},{name:`Active Eco-Restoration`,radiusM:3500,description:`1 km active band for managed biome, native rehabilitation, and functional climate pockets.`},{name:`Passive Eco-Restoration`,radiusM:11e3,description:`Outer passive restoration reserve securing the full radial print.`}],Vt=[{id:`integration-hall`,name:`Integration Hall`,footprint:`40 m x 75 m, 22 m clear`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Starship-compatible roller doors both ends; single bridge crane spans the hall.`},{id:`chainhill`,name:`ChainHill Relay`,footprint:`~225-250 m relay length`,elevation:`flat raised concrete, approximately 3 m above water table`,releaseStatus:`bounded-assumption`,notes:`Incoming and outgoing tracks oppose each other with two anti-parallel internal lines.`},{id:`x-pads`,name:`X-Layout Pads`,footprint:`solid pads, no beveled building base`,elevation:`pad-specific hardstand`,releaseStatus:`canonical`,notes:`Flame/exhaust outlets orient away from central node and buildings.`},{id:`mission-control`,name:`Mission Control / ATC`,footprint:`pentagon base, level 1 at 80%, four-storey tower`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Foyer, cafeteria, meeting, offices, emergency access, elevator, and top operating floor.`},{id:`living-rd`,name:`R&D + Living Quarters`,footprint:`room-level workbook detail pending`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`known-unknown`,notes:`FIFO and FIFO+family support with ground community and rooftop lifestyle zones.`}],Ht=[`site_zones`,`facilities`,`rooms_spaces`,`roads_tracks`,`pads_exhaust`,`eco_restoration`,`standards_evidence`,`viewer_toggles`,`known_unknowns`],Ut=`modulepreload`,Wt=function(e){return`/`+e},Gt={},Kt=function(e){return e.pathname.endsWith(`.css`)},qt=function(e,t,n){if(t in e)return e[t];let r=n();if(!r){e[t]=void 0;return}let i=r.then(()=>{e[t]=void 0},n=>{throw e[t]=void 0,n});return e[t]=i,i},Jt=function(e,t,n){let r=Promise.resolve();if(t&&t.length>0){let e,i=document.querySelector(`meta[property=csp-nonce]`),a=i?.nonce||i?.getAttribute(`nonce`);function o(e){return Promise.all(e.map(e=>Promise.resolve(e).then(e=>({status:`fulfilled`,value:e}),e=>({status:`rejected`,reason:e}))))}function s(e){return import.meta.resolve?new URL(import.meta.resolve(e)):new URL(e,import.meta.url)}r=o(t.map(t=>{t=Wt(t,n);let r=s(t),i=Kt(r);return qt(Gt,r.href,()=>{if(e===void 0){e={all:new Set,styles:new Set};let t=document.getElementsByTagName(`link`);for(let n=t.length-1;n>=0;n--){let r=t[n];e.all.add(r.href),r.rel===`stylesheet`&&e.styles.add(r.href)}}if((i?e.styles:e.all).has(r.href))return;let t=document.createElement(`link`);if(t.rel=i?`stylesheet`:Ut,i||(t.as=`script`),t.crossOrigin=``,t.href=r.href,a&&t.setAttribute(`nonce`,a),document.head.appendChild(t),i)return new Promise((e,n)=>{let i=a=>{t.removeEventListener(`load`,i),t.removeEventListener(`error`,i),a.type===`error`?n(Error(`Unable to preload CSS for ${r}`)):e(a)};t.addEventListener(`load`,i),t.addEventListener(`error`,i)})})}).filter(e=>e!==void 0))}function i(e){let t=new Event(`vite:preloadError`,{cancelable:!0});if(t.payload=e,window.dispatchEvent(t),!t.defaultPrevented)throw e}return r.then(t=>{for(let e of t||[])e.status===`rejected`&&i(e.reason);return e().catch(i)})},Yt=document.getElementById(`app`);if(!Yt)throw Error(`UniSpace mount node #app not found.`);Yt.innerHTML=`
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Cognigrex · powered by LightSpeed</p>
        <h1>UniSpace</h1>
        <p class="lede">Achilles-governed commands, Desktop execution, project visibility, review receipts and source continuity.</p>
      </div>
      <div class="connection-pill" id="desktop-pill" data-state="checking">
        <span class="status-dot"></span>
        <div><strong>Desktop</strong><small id="desktop-pill-text">checking local runtime</small></div>
      </div>
    </header>

    <nav class="tabs" aria-label="UniSpace views">
      <button class="tab active" data-view="command">Command</button>
      <button class="tab" data-view="activity">Activity</button>
      <button class="tab" data-view="objects">Objects</button>
      <button class="tab" data-view="filespace">FileSpace</button>
      <button class="tab" data-view="system">System</button>
      <button class="tab" data-view="sources">Sources</button>
    </nav>

    <section class="view" id="view-filespace"><p role="status" id="filespace-load"></p><iframe id="filespace-reader" title="CGX FileSpace reader" sandbox="allow-scripts allow-downloads" style="width:100%;height:76vh;border:0"></iframe></section>
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
      <div id="object-review-catalogue" class="graph-stack">
        <article class="panel"><p class="muted">Reading the CGX object review catalogue…</p></article>
      </div>
      <div id="cgx-review-lens" class="graph-stack">
        <article class="panel"><p class="muted">Reading the internal .cgx review projection…</p></article>
      </div>
      <div id="type1-catalogue-projection" class="graph-stack">
        <article class="panel"><p class="muted">Reading the bounded Type-I catalogue projection…</p></article>
      </div>
      <div id="representation-graphs" class="graph-stack">
        <article class="panel"><p class="muted">Reading feature-gated object graphs from Desktop…</p></article>
      </div>
    </section>

    <section class="view" id="view-system">
      <article class="panel"><p class="eyebrow">Application and toolkit</p><h2>UniSpace on LightSpeed</h2><p>UniSpace brings your Cognigrex workspace together. LightSpeed provides the local tools, agent routing and runtime services; .cgx carries object identity, provenance and evidence.</p><p class="muted">Connections and capabilities are reported below from the active runtime. A listed tool or plugin is usable only when its connection and permissions are ready.</p></article>
      <article class="panel definition">
        <div><p class="eyebrow">cognigrex</p><h2>Common goal, distinct agents</h2></div>
        <p>The system coordinates GO, Desktop, Git, Drive, agents and human oversight while retaining separate authority, resource limits and reviewable receipts.</p>
      </article>
      <div class="agent-grid">${[[`Achilles`,`governance, proof and release`],[`Neo`,`task routing and handoff`],[`Architect`,`projects, plans and dependencies`],[`TheConstruct`,`simulation and digital twins`],[`Morpheus`,`claim proof and conflict resolution`],[`Oracle`,`sources, evidence and knowns`],[`Smith`,`Git, code, schemas and execution`],[`Merovingian`,`health, storage, projects and recovery`],[`Trinity`,`interface and visual implementation`]].map(([e,t])=>`<article class="agent"><strong>${e}</strong><span>${t}</span></article>`).join(``)}</div>
      <article class="panel" id="cgx-capability-surface"><p class="eyebrow">Backend-derived CGX capabilities</p><h2>Owner sign-in required</h2><p class="muted">Route and role metadata are read from the current authenticated Desktop registry, not a separate UI catalogue.</p></article>
      <div class="two-column">
        <article class="panel"><p class="eyebrow">Execution path</p><h2>One project, one receipt chain</h2><div class="flow"><span>UniSpace</span><i>→</i><span>Achilles</span><i>→</i><span>Neo + floor</span><i>→</i><span>Desktop project</span><i>→</i><span>Drive receipt</span><i>→</i><span>GO decision</span></div></article>
        <article class="panel"><p class="eyebrow">Existing twin context</p><h2>Spaceport contract retained</h2><p class="muted">${Bt.length} zones · ${Vt.length} facility records · ${Ht.length} workbook tabs. The twin remains bounded context, not the command-centre homepage.</p></article>
      </div>
      <article class="panel">
        <div class="panel-head"><div><p class="eyebrow">Corpus test cascade</p><h2 id="cascade-mode">Checking Desktop contract</h2></div><span class="badge" id="cascade-activation">Activation gated</span></div>
        <div class="flow"><span>Blocked</span><i>→</i><span>Ready</span><i>→</i><span>Underway</span><i>→</i><span>Partial</span><i>→</i><span>Complete</span></div>
        <p class="muted" id="cascade-boundary">Corpus supplies verified inputs and dependency lineage. Results remain unknown until receipted execution; downstream propagation waits for proof, verified readback and commit.</p>
      </article>

      <article class="panel" id="node-exchange-panel">
        <div class="panel-head">
          <div><p class="eyebrow">CGX node exchange</p><h2 id="node-exchange-node">Checking node identity</h2></div>
          <span class="badge" id="node-exchange-peer">Peer compute unproven</span>
        </div>
        <div class="two-column">
          <div><strong>Transfer</strong><p class="muted" id="node-exchange-transfer">Checking content-addressed transport.</p></div>
          <div><strong>Compute</strong><p class="muted" id="node-exchange-compute">Checking leased compute capability.</p></div>
        </div>
        <p class="muted" id="node-exchange-boundary">Carrier readback and compute capability are verified independently. Copying data never transfers authority.</p>

        <div class="two-column">
          <details>
            <summary>Plan content transfer</summary>
            <form id="node-transfer-form">
              <label class="field field-wide"><span>Source reference</span><input id="node-transfer-source-ref" placeholder="cgx://… or provider reference" required></label>
              <label class="field field-wide"><span>SHA-256</span><input id="node-transfer-sha" minlength="64" maxlength="64" required></label>
              <div class="form-grid">
                <label class="field"><span>Bytes</span><input id="node-transfer-bytes" type="number" min="0" required></label>
                <label class="field"><span>File name</span><input id="node-transfer-file" required></label>
                <label class="field"><span>Source node</span><input id="node-transfer-source-node" value="bouwerbase" required></label>
                <label class="field"><span>Target node</span><input id="node-transfer-target-node" required></label>
                <label class="field"><span>Source root</span><input id="node-transfer-source-root" value="local-source" required></label>
                <label class="field"><span>Target root</span><input id="node-transfer-target-root" value="node-staging" required></label>
              </div>
              <button class="primary" type="submit">Plan transfer</button>
              <div id="node-transfer-result" class="result" aria-live="polite"></div>
            </form>
          </details>

          <details>
            <summary>Plan delegated compute</summary>
            <form id="node-compute-form">
              <label class="field field-wide"><span>Instruction</span><textarea id="node-compute-instruction" rows="4" required></textarea></label>
              <div class="form-grid">
                <label class="field"><span>Task ID</span><input id="node-compute-task" required></label>
                <label class="field"><span>Run ID</span><input id="node-compute-run" required></label>
                <label class="field"><span>Target node</span><input id="node-compute-target" value="bouwerbase" required></label>
                <label class="field"><span>Capability</span><input id="node-compute-capability" value="cognigrex-supervised-workflow" required></label>
                <label class="field field-wide"><span>Execution lease</span><input id="node-compute-lease" required></label>
              </div>
              <button class="primary" type="submit">Plan compute</button>
              <div id="node-compute-result" class="result" aria-live="polite"></div>
            </form>
          </details>
        </div>
      </article>
    </section>

    <section class="view" id="view-sources">
      <div class="source-grid">${zt.map(([e,t,n])=>`<a class="source-card" href="${t}" target="_blank" rel="noreferrer"><strong>${e}</strong><span>${n}</span><em>Open ↗</em></a>`).join(``)}</div>
      <article class="panel"><p class="eyebrow">Authority order</p><h2>Where each truth lives</h2><div class="authority-grid"><div><strong>Drive</strong><span>evidence, workbooks and review receipts</span></div><div><strong>Git</strong><span>code, schemas, tests and implementation receipts</span></div><div><strong>Desktop</strong><span>projects, local execution, state and jobs</span></div><div><strong>UniSpace</strong><span>owner commands, review and bounded decisions</span></div></div></article>
    </section>
  </main>
`;var P=e=>{let t=document.getElementById(e);if(!t)throw Error(`Missing #${e}`);return t},Xt=P(`instruction`),Zt=P(`target-floor`),Qt=P(`priority`),$t=P(`execution-mode`),en=P(`route-preview`),tn=P(`command-result`),F=null,I=null,nn=[],rn=[],L=``,R=0,z=0,an=()=>{R++,z++,document.querySelectorAll(`.result-receipt-detail, .project-file-result`).forEach(e=>{e.textContent=``})},B=``,V=`NCNB`,H=(e,t)=>{let n=P(`owner-auth-result`);n.dataset.tone=e,n.textContent=t},on=e=>{let t=P(`owner-login-form`),n=P(`owner-change-form`),r=P(`owner-logout`);V=e.credential?.username||V,an(),L=e.session_token||``,B=e.password_change_token||``,P(`owner-password`).value=``,e.authenticated&&L?(n.hidden=!0,r.hidden=!1,P(`owner-auth-state`).textContent=`${V} signed in`,H(`good`,`Owner session active until ${e.expires_utc||`page close`}.`)):(r.hidden=!0,n.hidden=!e.change_required,t.hidden=!1,P(`owner-auth-state`).textContent=e.change_required?`Password change required`:`Sign-in required`,H(`warn`,e.change_required?`The bootstrap password was verified. Enter it again with a new password to complete first login.`:`Owner sign-in is required for unredacted files, receipts, and decisions.`))},U=()=>L||(H(`warn`,`Sign in as NCNB before performing this owner-gated action.`),``);P(`owner-login-form`).addEventListener(`submit`,async e=>{e.preventDefault();let t=P(`owner-username`).value.trim(),n=P(`owner-password`);try{on(await f(t,n.value)),L&&q()}catch(e){n.value=``,H(`bad`,e instanceof Error?e.message:`Owner sign-in failed.`)}}),P(`owner-change-form`).addEventListener(`submit`,async e=>{e.preventDefault();let t=P(`owner-current-password`),n=P(`owner-new-password`),r=P(`owner-confirm-password`);if(n.value!==r.value){H(`bad`,`The new passwords do not match.`);return}let i=B||L;if(!i)H(`bad`,`Sign in before changing the password.`);else try{let e=await p(V,t.value,n.value,i,!!B);t.value=``,n.value=``,r.value=``,on(e)}catch(e){t.value=``,n.value=``,r.value=``,H(`bad`,e instanceof Error?e.message:`Password change failed.`)}}),P(`owner-logout`).addEventListener(`click`,async()=>{let e=L;if(L=``,an(),B=``,e)try{await m(e)}catch{}P(`owner-logout`).hidden=!0,P(`owner-auth-state`).textContent=`Signed out`,H(`warn`,`Owner session cleared from this page.`),P(`cgx-capability-surface`).textContent=`Owner session cleared; capability projection hidden.`});var W=(e,t,n)=>{let r=P(e);r.dataset.tone=t,r.textContent=n};P(`node-transfer-form`).addEventListener(`submit`,async e=>{e.preventDefault();let t=U();if(!t){W(`node-transfer-result`,`warn`,`Owner sign-in is required to plan private transfer.`);return}let n=Number(P(`node-transfer-bytes`).value);try{let e=await h({source_ref:P(`node-transfer-source-ref`).value.trim(),source_sha256:P(`node-transfer-sha`).value.trim(),size_bytes:n,file_name:P(`node-transfer-file`).value.trim(),source_node_id:P(`node-transfer-source-node`).value.trim(),target_node_id:P(`node-transfer-target-node`).value.trim(),source_root_id:P(`node-transfer-source-root`).value.trim(),target_root_id:P(`node-transfer-target-root`).value.trim()},t);W(`node-transfer-result`,`good`,`${String(e.plan?.transfer_id||`planned`)} planned. DIGITAL_WRITE lease required; no bytes moved and no authority transferred.`)}catch(e){W(`node-transfer-result`,`bad`,e instanceof Error?e.message:`Transfer plan failed.`)}}),P(`node-compute-form`).addEventListener(`submit`,async e=>{e.preventDefault();let t=U();if(!t)W(`node-compute-result`,`warn`,`Owner sign-in is required to plan private compute.`);else try{let e=await g({instruction:P(`node-compute-instruction`).value.trim(),task_id:P(`node-compute-task`).value.trim(),run_id:P(`node-compute-run`).value.trim(),target_node_id:P(`node-compute-target`).value.trim(),capability_id:P(`node-compute-capability`).value.trim(),lease_ref:P(`node-compute-lease`).value.trim(),input_receipts:[],resource_budget:{allow_heavy:!1}},t);W(`node-compute-result`,`good`,`${String(e.request?.request_id||`planned`)} planned. COMPUTE_ONLY lease must validate before the existing runtime executes anything.`)}catch(e){W(`node-compute-result`,`bad`,e instanceof Error?e.message:`Compute plan failed.`)}});var sn=()=>{let e=s(Xt.value||`governance`);Zt.value=e;let t=I?.canonical_gate_id;en.innerHTML=`<strong>Achilles route:</strong> ${e} is primary. Neo coordinates and proof returns to this gate.${t?` <small>Authority: ${x(t)}</small>`:` <small>Waiting for the Desktop authority contract.</small>`}`};Xt.addEventListener(`input`,sn),sn();var cn=()=>c({instruction:Xt.value,targetFloor:Zt.value,priority:Qt.value,executionMode:$t.value,authorityContract:I}),G=(e,t)=>{tn.dataset.tone=e,tn.textContent=t},K=()=>{let e=_e();P(`pending-count`).textContent=String(e.length);let t=P(`pending-commands`);e.length?(t.innerHTML=e.map(e=>`<article class="task-card"><div><strong>${x(e.title)}</strong><span>${x(e.target_floor)} · ${x(e.priority)} · ${x(e.execution_mode)}</span><small>${x(e.command_id)}</small></div><div class="task-actions"><button data-send="${x(e.command_id)}">Send</button><button data-download="${x(e.command_id)}">Download</button></div></article>`).join(``),t.querySelectorAll(`[data-send]`).forEach(t=>t.addEventListener(`click`,async()=>{let n=e.find(e=>e.command_id===t.dataset.send);if(n)try{let e=await _(n);ye(n.command_id),K(),G(`good`,`Desktop accepted ${e.command_id||n.command_id}. Task ${e.task_id??`created`}.`),await q()}catch(e){G(`bad`,e instanceof Error?e.message:`Desktop command failed.`)}})),t.querySelectorAll(`[data-download]`).forEach(t=>t.addEventListener(`click`,()=>{let n=e.find(e=>e.command_id===t.dataset.download);n&&be(n)}))):t.innerHTML=`<p class="muted">No locally saved commands.</p>`},ln=e=>{z++;let t=P(`desktop-projects`);P(`project-count`).textContent=String(e.length),t.innerHTML=Re(e),He(t,async(e,t)=>{let n=t.closest(`[data-project-card]`)?.querySelector(`.project-files`);if(n){if(t.getAttribute(`aria-expanded`)===`true`){t.setAttribute(`aria-expanded`,`false`),t.textContent=`Files`,z++;let e=n.querySelector(`.project-file-result`);e&&(e.textContent=``),n.hidden=!0}else{t.disabled=!0,t.textContent=`Loading…`,n.hidden=!1,n.innerHTML=`<p class="muted">Reading bounded project metadata…</p>`;try{let r=await ne(e);n.innerHTML=ze(r),Ue(n,async(e,t,i)=>{let a=n.querySelector(`.project-file-result`);if(!a)return;let o=++z,s=U();if(!s)a.innerHTML=Be(`File preview held: sign in through the NCNB owner gate first.`);else{i.disabled=!0,a.innerHTML=`<p class="muted">Opening read-only result…</p>`;try{let n=r.files.find(e=>e.relative_path===t);if(e!==r.project.project_id||!n?.metadata_revision||!/^[a-f0-9]{64}$/.test(n.metadata_revision))throw Error(`File revision unavailable; refresh the list.`);let i=await re(e,t,s,void 0,n.metadata_revision);if(o!==z||s!==L||!a.isConnected)return;if(i.project.project_id!==e||i.file.relative_path!==t||i.file.metadata_revision!==n.metadata_revision)throw Error(`File identity or metadata revision changed; refresh the list.`);a.innerHTML=Ve(i)}catch(e){if(o!==z||s!==L||!a.isConnected)return;a.innerHTML=Be(e instanceof Error?e.message:`Project file result is unavailable.`)}finally{i.disabled=!1}}}),t.setAttribute(`aria-expanded`,`true`),t.textContent=`Hide files`}catch(e){n.innerHTML=Be(e instanceof Error?e.message:`Project files are unavailable.`),t.textContent=`Retry files`}finally{t.disabled=!1}}}})},un=(e,t)=>{an();let n=P(`desktop-results`),r=P(`result-auth-state`);r.textContent=t?`Owner gate configured`:`Content gate held`,n.innerHTML=Ke(e,t),Je(n,async(r,i)=>{let a=n.querySelector(`.result-receipt-detail`);if(!a)return;let o=++R;if(!t){a.innerHTML=S(`Receipt content is held because owner confirmation is not configured on the local bridge.`);return}let s=U();if(!s)a.innerHTML=S(`Receipt inspection held: sign in through the NCNB owner gate first.`);else{i.disabled=!0,a.innerHTML=`<p class="muted">Opening owner-confirmed read-only receipt…</p>`;try{let t=e.results.find(e=>e.result_id===r);if(!t||!/^[a-f0-9]{64}$/.test(t.sha256))throw Error(`Exact receipt revision unavailable; refresh the list.`);let n=await ae(r,s,void 0,t.sha256);if(o!==R||s!==L||!a.isConnected)return;if(n.identity.result_id!==r||n.identity.sha256!==t.sha256)throw Error(`Receipt identity or revision changed; refresh the list.`);a.innerHTML=qe(n)}catch(e){if(o!==R||s!==L||!a.isConnected)return;a.innerHTML=S(e instanceof Error?e.message:`Local result receipt is unavailable.`)}finally{i.disabled=!1}}})},dn=e=>{nn=e;let t=P(`desktop-reviews`);e.length?(t.innerHTML=e.slice(0,30).map(e=>{let t=e.state||`pending_review`,n=t===`pending_review`?`<div class="task-actions"><button data-review="${x(e.review_id)}" data-decision="approve">Approve</button><button data-review="${x(e.review_id)}" data-decision="hold">Hold</button><button data-review="${x(e.review_id)}" data-decision="reject">Reject</button></div>`:``;return`<article class="task-card"><div><strong>${x(e.title||`Project receipt`)}</strong><span>${x(t)} · ${x(e.event_type||`receipt`)}</span><small>${x(e.summary||e.review_id)}</small></div>${n}</article>`}).join(``),t.querySelectorAll(`[data-review]`).forEach(e=>e.addEventListener(`click`,async()=>{let t=e.dataset.review||``,n=e.dataset.decision,r=nn.find(e=>e.review_id===t);if(!r||!t)return;let i=window.prompt(`${n.toUpperCase()}: ${r.title||t}\nOptional decision note:`,``)??``,a=U();if(!a)G(`bad`,`Review decision held: sign in through the NCNB owner gate first.`);else try{G(`good`,pe(t,n,await se(t,n,i,a))),await q()}catch(e){G(`bad`,e instanceof Error?e.message:`Review decision failed.`)}}))):t.innerHTML=`<p class="muted">No project receipts are awaiting review.</p>`},fn=e=>{rn=e;let t=P(`representation-graphs`);t.innerHTML=et(e),t.querySelectorAll(`[data-representation-review]`).forEach(e=>{e.addEventListener(`click`,async()=>{let t=e.dataset.representationReview||``,n=e.dataset.decision,r=e.dataset.scope||`identity`,i=r===`edges`?(e.dataset.edgeIds||``).split(`|`).filter(Boolean).slice(0,100):[],a=rn.find(e=>e.review?.review_id===t);if(!t||!a)return;let o=window.prompt(`${n.replace(/_/g,` `).toUpperCase()}: ${a.object.display_name}\n${r===`identity`?`Identity is reviewed before edges.`:`${i.length} bounded edges selected.`}\nOptional decision note:`,``)??``,s=U();if(!s)G(`bad`,`Representation decision held: sign in through the NCNB owner gate first.`);else try{await he(t,n,r,i,o,s),G(`good`,`${t} recorded ${n}; local staging remains noncanonical until Drive readback.`),await q()}catch(e){G(`bad`,e instanceof Error?e.message:`Representation review decision failed.`)}})})};P(`command-form`).addEventListener(`submit`,async e=>{e.preventDefault(),F=null;try{F=cn(),G(`warn`,`Sending ${F.command_id} to Desktop…`);let e=await _(F);ye(F.command_id),K(),G(`good`,`Accepted by Desktop. Task ${e.task_id??`created`}; ${e.state||`queued for governed processing`}.`),await q()}catch(e){let t=e instanceof l;F&&!t&&ve(F),K();let n=e instanceof Error?e.message:`Desktop unavailable`;G(`bad`,t?`${n} Desktop rejected the command; it was not mislabeled as an offline save.`:`${n}${F?` The command envelope was saved locally.`:``}`)}}),P(`save-command`).addEventListener(`click`,()=>{try{F=cn(),ve(F),K(),G(`good`,`${F.command_id} saved locally.`)}catch(e){G(`bad`,e instanceof Error?e.message:`Command could not be saved.`)}}),P(`copy-command`).addEventListener(`click`,async()=>{try{F=cn(),await navigator.clipboard.writeText(JSON.stringify(F,null,2)),G(`good`,`${F.command_id} copied as JSON.`)}catch(e){G(`bad`,e instanceof Error?e.message:`Command could not be copied.`)}});var q=async()=>{let e=P(`desktop-pill`),t=P(`desktop-state`),n=P(`merovingian-state`),r=P(`remote-access-state`),o=P(`remote-access-detail`),s=P(`desktop-pill-text`),c=P(`desktop-tasks`);e.dataset.state=`checking`,s.textContent=`checking local runtime`,t.textContent=`Checking`,n.textContent=`Checking`,r.textContent=`Checking`,o.textContent=`private relay gate`;try{let l=await d();I=l.authority_contract||null,V=l.auth?.username||V,P(`owner-username`).value=V,L||(P(`owner-auth-state`).textContent=l.auth?.configured?l.auth.must_change?`First change required`:`Sign-in required`:`Credential setup held`,l.auth?.configured?l.auth.must_change&&H(`warn`,`Sign in with the bootstrap password, then complete the required change.`):H(`bad`,`The dedicated owner credential is not configured on Desktop.`)),sn(),e.dataset.state=l.ok?`online`:`degraded`,s.textContent=l.ok?`local runtime connected`:`runtime connected; health needs review`,t.textContent=`Online`,n.textContent=l.merovingian?.status===`pass`?`Healthy`:`Degraded`;let u=i(l.remote_access);r.textContent=u.label,o.textContent=u.detail;let f=l.test_cascade;P(`cascade-mode`).textContent=f?.mode===`corpus_bound`?`Corpus-bound planning`:`Cascade unavailable`,P(`cascade-activation`).textContent=f?.activation_state===`active`?`Active`:f?.activation_state===`held`?`Held`:`Prepared · activation gated`,P(`cascade-boundary`).textContent=f?.dependency_gate?`Results unknown until execution · downstream gate: ${f.dependency_gate}.`:`Corpus inputs and dependency receipts remain required before governed execution.`;let p=l.node_exchange,m=a(p);P(`node-exchange-node`).textContent=p?.node_id?`Node ${p.node_id}`:`Node identity unavailable`,P(`node-exchange-transfer`).textContent=m.transfer,P(`node-exchange-compute`).textContent=m.compute,P(`node-exchange-boundary`).textContent=m.boundary,P(`node-exchange-peer`).textContent=p?.compute?.peer_compute_verified?`Peer compute verified`:p?.activation?.host_root_registry_ready?`Local root registry ready`:`Root registry pending`,p?.node_id&&(P(`node-transfer-source-node`).value=p.node_id,P(`node-compute-target`).value=p.node_id);let h=P(`cgx-capability-surface`);if(L){let e=L;try{let t=await ce(e);if(e===L){let n=t.roles.map(e=>`<span class="badge">${x(e.floor)}</span>`).join(` `),r=t.routes.map(e=>`<span class="badge" title="${x(e.gate)}">${x(e.id)} · ${x(e.state)}</span>`).join(` `);h.innerHTML=`<p class="eyebrow">Backend-derived CGX capabilities</p><h2>${t.route_count} scoped routes · review-only</h2><p class="muted">Revision ${x(t.source_view_sha256.slice(0,12))} · no execution or mint authorization inferred.</p><div class="flow">${n}</div><details><summary>Registered capability catalogue</summary><div class="flow" style="flex-wrap:wrap">${r}</div></details>`,Ie(h,t,e,()=>e===L);try{let t=await le(e);if(e===L&&h.isConnected){let e=document.createElement(`details`),n=t.selectors.map(e=>`<li><strong>`+x(e.selector)+`</strong> · `+e.available_routes+` available / `+e.gated_routes+` gated · native admission pending</li>`).join(``),r=t.content_groups.map(e=>`<li><strong>`+x(e.display_name)+`</strong> · `+e.bytes+` bytes · `+x(e.sha256.slice(0,12))+(e.reference_names.length>1?` · same-byte names: `+e.reference_names.map(x).join(` ≡ `):``)+` · observation only, not native object admission</li>`).join(``),i=t.retained_empty_carrier_names.length;e.innerHTML=`<summary>CGX family · `+t.selector_count+` registered selectors</summary><p class="muted">`+t.installed_carrier_count+` observed .cgx filenames consolidated into `+t.content_groups.length+` content groups (`+t.collapsed_alias_card_count+` duplicate display card(s) suppressed). Identical bytes do not prove semantic identity or native mint.</p><ul>`+n+`</ul><details><summary>One content card per unique hash</summary><ul>`+r+`</ul></details><p class="muted">Storage namespace `+(t.storage_root_is_alias?`resolves through an existing alias/junction`:`is a direct root`)+`. Zero-byte carrier holds: `+i+`. Deleted: `+(t.deletion_performed?`yes`:`no`)+`. No carrier aliases are deletion-authorised by this presentation.</p>`,h.appendChild(e)}}catch{if(e===L&&h.isConnected){let e=document.createElement(`p`);e.className=`muted`,e.textContent=`Family topology pending deployment or source admission.`,h.appendChild(e)}}}}catch{h.textContent=`CGX capability projection unavailable; registry or owner session held.`}}else h.textContent=`Sign in as owner to hydrate the read-only CGX capability projection.`;try{let e=await v();c.innerHTML=e.length?e.map(e=>`<article class="task-card"><div><strong>${x(String(e.title||`Untitled task`))}</strong><span>${x(String(e.status||`unknown`))} · ${x(String(e.priority||`normal`))}</span><small>Task ${x(String(e.id||``))}</small></div></article>`).join(``):`<p class="muted">Desktop queue is clear.</p>`}catch{c.innerHTML=`<p class="muted">Desktop is online, but task listing is unavailable.</p>`}try{ln((await ee()).projects)}catch{ln([])}try{dn(await oe())}catch{dn([])}try{un(await ie(),l.auth?.configured===!0)}catch(e){P(`result-auth-state`).textContent=l.auth?.configured===!0?`Owner gate configured`:`Content gate held`,P(`desktop-results`).innerHTML=S(e instanceof Error?e.message:`Local result metadata is unavailable.`)}try{fn(await me())}catch(e){rn=[];let t=l.representation_edge?.enabled===!1?`Canonical representation objects are intentionally disabled by the current launch gate.`:e instanceof Error?e.message:`Representation objects are unavailable.`;P(`representation-graphs`).innerHTML=`<article class="panel"><p class="eyebrow">Objects unavailable</p><h2>Feature-gated, not empty</h2><p class="muted">${x(t)}</p></article>`}}catch{I=null,sn(),e.dataset.state=`offline`,s.textContent=`start LightSpeed Desktop and the local bridge`,t.textContent=`Offline`,n.textContent=`Offline`,r.textContent=`Unavailable`,o.textContent=`Desktop bridge is offline.`,P(`cascade-mode`).textContent=`Desktop offline`,P(`cascade-activation`).textContent=`Unavailable`,P(`cascade-boundary`).textContent=`Start the local Desktop bridge to read the corpus-cascade contract.`,P(`node-exchange-node`).textContent=`Node exchange unavailable`,P(`node-exchange-peer`).textContent=`Peer state unknown`,P(`node-exchange-transfer`).textContent=`Desktop bridge is offline.`,P(`node-exchange-compute`).textContent=`Desktop bridge is offline.`,P(`node-exchange-boundary`).textContent=`Start the local Desktop bridge before planning transfer or compute.`,P(`cgx-capability-surface`).textContent=`Desktop offline; CGX capability projection unavailable.`,P(`project-count`).textContent=`0`,c.innerHTML=`<p class="muted">Desktop is offline. Commands can still be saved, copied or downloaded.</p>`,P(`desktop-projects`).innerHTML=`<p class="muted">Project registry unavailable while Desktop is offline.</p>`,P(`desktop-reviews`).innerHTML=`<p class="muted">Review queue unavailable while Desktop is offline.</p>`,P(`owner-auth-state`).textContent=`Desktop offline`,H(`bad`,`Start the local Desktop bridge before signing in.`),P(`result-auth-state`).textContent=`Desktop offline`,P(`desktop-results`).innerHTML=`<p class="muted">Fixed local result metadata is unavailable while Desktop is offline.</p>`,fn([])}};P(`refresh-desktop`).addEventListener(`click`,()=>void q()),K(),q();var pn=P(`object-review-catalogue`),mn=new URL(`./data/cgx_object_review_catalogue.json`,document.baseURI).toString(),hn=new URL(`./data/component_geometry_atlas_public_review.json`,document.baseURI).toString();Rt(async()=>{let e=await fetch(mn,{cache:`no-store`});if(!e.ok)throw Error(`Object review catalogue returned HTTP ${e.status}`);return await e.json()},async()=>{let e=await fetch(hn,{cache:`no-store`});if(!e.ok)throw Error(`Component atlas review projection returned HTTP ${e.status}`);return await e.json()}).then(({html:e,atlas:t})=>{pn.innerHTML=e,Lt(pn,t)}).catch(e=>{pn.innerHTML=`<article class="panel"><p class="eyebrow">CGX object review</p><h2>Catalogue unavailable</h2><p class="muted">${x(e instanceof Error?e.message:`CGX object review catalogue unavailable.`)}</p></article>`});var gn=P(`cgx-review-lens`),_n=new URL(`./data/cgx_internal_review_projection.json`,document.baseURI).toString();ft(async()=>{let e=await fetch(_n,{cache:`no-store`});if(!e.ok)throw Error(`CGX review projection returned HTTP ${e.status}`);return await e.json()}).then(({html:e})=>{gn.innerHTML=e,dt(gn)}).catch(e=>{gn.innerHTML=`<article class="panel"><p class="eyebrow">.cgx review lens</p><h2>Projection unavailable</h2><p class="muted">${x(e instanceof Error?e.message:`CGX review projection unavailable.`)}</p></article>`});var vn=P(`type1-catalogue-projection`),yn=new URL(`./data/type1_catalogue_projection.json`,document.baseURI).toString();nt(async()=>{let e=await fetch(yn,{cache:`no-store`});if(!e.ok)throw Error(`Type-I catalogue projection returned HTTP ${e.status}`);return await e.json()}).then(e=>{vn.innerHTML=e}).catch(e=>{vn.innerHTML=`<article class="panel"><p class="eyebrow">Type-I PrintSpace</p><h2>Projection unavailable</h2><p class="muted">${x(e instanceof Error?e.message:`Type-I catalogue projection unavailable.`)}</p></article>`});var bn=P(`neo-exchange`),xn=new URL(`./data/neo_exchange.json`,document.baseURI).toString();Me(async()=>{let e=await fetch(xn,{cache:`no-store`});if(!e.ok)throw Error(`Neo exchange returned HTTP ${e.status}`);return e.json()}).then(e=>{bn.innerHTML=Pe(e)});var Sn=e=>{let t=Array.from(document.querySelectorAll(`.tab`)).find(t=>t.dataset.view===e)?.dataset.view||`command`;if(t===`filespace`){let e=document.querySelector(`#filespace-reader`);e.srcdoc||Jt(async()=>{let{readerDocument:e}=await import(`./filespaceReader-ynzKLNaM.js`);return{readerDocument:e}},[]).then(({readerDocument:t})=>{e.srcdoc||=t()}).catch(()=>{document.querySelector(`#filespace-load`).textContent=`The FileSpace reader could not load. Reopen this view to retry.`})}document.querySelectorAll(`.tab`).forEach(e=>e.classList.remove(`active`)),document.querySelectorAll(`.view`).forEach(e=>e.classList.remove(`active`)),document.querySelector(`.tab[data-view="${t}"]`)?.classList.add(`active`),P(`view-${t}`).classList.add(`active`)};document.querySelectorAll(`.tab`).forEach(e=>e.addEventListener(`click`,()=>{let t=e.dataset.view||`command`;Sn(t);let n=t===`command`?``:`#${t}`;window.location.hash!==n&&window.history.replaceState(null,``,n||window.location.pathname+window.location.search)})),window.addEventListener(`hashchange`,()=>Sn(window.location.hash.replace(/^#/,``)||`command`)),Sn(window.location.hash.replace(/^#/,``)||`command`);var Cn=new URL(`./data/site_integration.json`,document.baseURI).toString(),wn=async()=>{try{let e=await fetch(Cn,{cache:`no-store`});return e.ok?await e.json():null}catch{return null}},Tn=()=>{if(document.getElementById(`lsgo-sites-side-edit-styles`))return;let e=document.createElement(`style`);e.id=`lsgo-sites-side-edit-styles`,e.textContent=`
    .site-context-strip { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
    .site-context-strip span { border:1px solid var(--line); border-radius:999px; padding:7px 10px; color:var(--muted); font-size:12px; background:rgba(255,255,255,.025); }
    .site-context-strip strong { color:var(--text); }
    .site-parity-card { border:1px solid var(--line); border-radius:14px; padding:14px; background:rgba(255,255,255,.025); display:grid; gap:8px; }
    .site-parity-card p { margin:0; color:var(--muted); line-height:1.5; }
    .site-parity-card .site-chain { display:flex; flex-wrap:wrap; gap:7px; align-items:center; }
    .site-parity-card .site-chain span { border:1px solid var(--line); border-radius:999px; padding:6px 9px; font-size:12px; }
    .site-parity-card .site-chain i { color:var(--teal); font-style:normal; }
  `,document.head.appendChild(e)},En=async()=>{let e=document.querySelector(`.topbar > div:first-child`),t=document.querySelector(`#view-sources`);if(!e||!t)return!1;Tn();let n=await wn(),r=n?.authority_chain??[`Nathaniel Bouwer`,`Achilles / GO gate`,`agent floor`,`LightSpeed Desktop`,`Git and Drive receipts`],i=n?.source_state_label??`Git review source current · Drive successor pending · public update held`,a=n?.launch_state_label??`Private local operation; remote verification and public deployment held`;if(!document.getElementById(`site-context-strip`)){let t=document.createElement(`div`);t.id=`site-context-strip`,t.className=`site-context-strip`,t.innerHTML=`
      <span><strong>Owner:</strong> Nathaniel Bouwer</span>
      <span><strong>Mode:</strong> private soft launch</span>
      <span><strong>Source:</strong> ${i}</span>
    `,e.appendChild(t)}if(!document.getElementById(`site-parity-card`)){let e=document.createElement(`article`);e.id=`site-parity-card`,e.className=`panel site-parity-card`,e.innerHTML=`
      <p class="eyebrow">Canonical source chain</p>
      <h2>One operator surface, durable receipts</h2>
      <p>Desktop executes locally, Git carries implementation, Drive carries evidence and review records, and UniSpace remains the operator decision surface, powered by LightSpeed. Alignment is shown only after current evidence validates.</p>
      <div class="site-chain">
        ${r.map((e,t)=>`${t?`<i>→</i>`:``}<span>${e}</span>`).join(``)}
      </div>
      <p><strong>Launch state:</strong> ${a}</p>
    `,t.prepend(e)}return!0},Dn=0,On=()=>{En().then(e=>{e||Dn>=40||(Dn+=1,window.requestAnimationFrame(On))})};On();var kn=`lightspeed-cognigrex-os-shell-v0.1`,An=[`command`,`activity`,`objects`,`system`,`sources`,`filespace`],jn=[{id:`intake`,label:`Intake`,owner:`Neo`,receipt:`source envelope`,description:`Capture the request, source pointers, project identity, constraints and expected output without inventing missing authority.`},{id:`analyse`,label:`Analyse`,owner:`Neo + Oracle`,receipt:`scope / evidence map`,description:`Resolve knowns, source authority, evidence class, conflicts, privacy and the minimum useful execution path.`},{id:`route`,label:`Commit`,owner:`Neo`,receipt:`stable task / agent route`,description:`Commit one bounded job to the correct specialist floor while retaining stable identity and exact-once transport semantics.`},{id:`workshop`,label:`Workshop`,owner:`specialist floor`,receipt:`artifact / data / result`,description:`Execute the bounded specialist work: code, modelling, evidence extraction, interface work, planning or runtime recovery.`},{id:`proof`,label:`Proof`,owner:`Smith + Morpheus + Oracle`,receipt:`tests / provenance / contradiction`,description:`Test implementation, verify provenance, resolve conflicts and keep hypothesis, inference and empirical evidence distinct.`},{id:`consolidate`,label:`Consolidate`,owner:`Neo + Achilles`,receipt:`canonical delta / supersession`,description:`Return accepted results to the living canonical library as compact deltas, pointers and receipts rather than duplicate masters.`},{id:`release`,label:`Publish-ready`,owner:`Achilles`,receipt:`claim / security / release gate`,description:`Package approved digital artifacts, data and objects for a bounded release candidate. Publish-ready is not automatically published.`}],Mn=[{floor:`Neo`,short:`N`,role:`Cognigrex operational head: intake, decomposition, routing, cycle control and result aggregation.`,boundary:`May coordinate and reason operationally; cannot self-promote evidence, canon or public claims past Achilles/owner gates.`},{floor:`Oracle`,short:`O`,role:`Sources, evidence retrieval, indexing, known-state and data lineage.`,boundary:`Preserves source authority and uncertainty; duplicate references do not become independent evidence.`},{floor:`Morpheus`,short:`M`,role:`Contradiction, provenance, claim proof, confidence and supersession review.`,boundary:`Reviews and recommends; does not fabricate empirical validation.`},{floor:`Smith`,short:`S`,role:`Code, schemas, deterministic transforms, tests, build and execution receipts.`,boundary:`Changes remain branch/review gated until the applicable execution and release receipts exist.`},{floor:`Architect`,short:`A`,role:`Projects, dependency topology, plans, interfaces and system decomposition.`,boundary:`Uses canonical project identity and pointers rather than spawning competing masters.`},{floor:`TheConstruct`,short:`TC`,role:`Simulation, CAD, meshes, digital twins, derived views and manufacturing-reference artifacts.`,boundary:`Derived models remain labelled and cannot imply physical performance without evidence.`},{floor:`Trinity`,short:`T`,role:`Interface, interaction, visual language, accessibility and communication surfaces.`,boundary:`Presentation cannot elevate claim state or bypass evidence/security classification.`},{floor:`Merovingian`,short:`R`,role:`Runtime health, storage, recovery, resource control, persistence and operational receipts.`,boundary:`Recovery and cleanup are reversible/evidence-gated; no silent deletion or second runtime.`},{floor:`Achilles`,short:`Ω`,role:`Meta-governance, proof thresholds, safety, canonical promotion and release oversight.`,boundary:`Audits and gates the collective; it is not the routine task router inside Cognigrex.`}],Nn=e=>An.includes(e)?e:`command`,Pn=(e,t=`command`)=>Nn(new URLSearchParams(e.startsWith(`?`)?e.slice(1):e).get(`view`)||t),Fn=e=>{let t=e.trim().toLowerCase();return t?/\b(publish|release|public[- ]?ready|export|mint|deploy)\b/.test(t)?`release`:/\b(consolidat|canon|supersed|assimil|promot|living library|handoff)\b/.test(t)?`consolidate`:/\b(test|proof|verify|validat|audit|conflict|provenance|claim|confidence)\b/.test(t)?`proof`:/\b(build|code|model|simulate|render|mesh|cad|analyse data|analyze data|workshop|execute|run)\b/.test(t)?`workshop`:/\b(route|delegate|commit|queue|assign|agent|floor)\b/.test(t)?`route`:/\b(source|evidence|research|analyse|analyze|classif|scope|compare|reconcile)\b/.test(t)?`analyse`:`intake`:`intake`},In=e=>{let t=e.trim().toLowerCase();if(!t)return`Neo`;if(/\b(proof|claim|verify|verification|conflict|confidence|audit|contradiction|supersession)\b/.test(t))return`Morpheus`;if(/\b(achilles|governance|canonical promotion|release gate|safety gate)\b/.test(t))return`Achilles`;let n=s(e);return n===`Achilles`?`Neo`:n},Ln=e=>jn.find(t=>t.id===e)??jn[0],Rn=`lightspeed-cognigrex-os-shell-state-v1`,zn={activeView:`command`,activeAgent:`Neo`,focusMode:!1},J=(()=>{try{let e=JSON.parse(localStorage.getItem(Rn)||`{}`),t=Mn.some(t=>t.floor===e.activeAgent)?e.activeAgent:zn.activeAgent;return{activeView:Pn(window.location.search,window.location.hash.slice(1)||e.activeView),activeAgent:t,focusMode:!!e.focusMode}}catch{return{...zn}}})(),Y=e=>{J={...J,...e},localStorage.setItem(Rn,JSON.stringify(J))},X=e=>e.replace(/[&<>'"]/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,"'":`&#39;`,'"':`&quot;`})[e]||e),Z=e=>{let t=document.querySelector(`.tab[data-view="${e}"]`);t&&!t.classList.contains(`active`)&&t.click(),Y({activeView:e}),document.body.dataset.lsWorkspace=e},Q=(e,t=!1)=>{Y({activeAgent:e}),document.body.dataset.lsAgent=e,document.querySelectorAll(`[data-ls-agent]`).forEach(t=>{t.dataset.active=t.dataset.lsAgent===e?`true`:`false`});let n=document.getElementById(`target-floor`);n&&(n.value=e),t&&(Z(`command`),document.getElementById(`instruction`)?.focus())},Bn=e=>{let t=Ln(e);document.body.dataset.lsWorkflow=t.id,document.querySelectorAll(`[data-ls-stage]`).forEach(e=>{e.dataset.active=e.dataset.lsStage===t.id?`true`:`false`});let n=document.getElementById(`ls-os-stage-detail`);n&&(n.innerHTML=`<strong>${X(t.label)}</strong><span>${X(t.description)}</span><small>${X(t.owner)} · receipt: ${X(t.receipt)}</small>`)},Vn=()=>{let e=document.createElement(`aside`);return e.className=`ls-os-rail`,e.setAttribute(`aria-label`,`Cognigrex agent rail`),e.innerHTML=`
    <button class="ls-os-mark" type="button" data-ls-home title="UniSpace · Cognigrex" aria-label="UniSpace home">U</button>
    <div class="ls-os-agent-stack">
      ${Mn.map(e=>`
        <button class="ls-os-agent" type="button" data-ls-agent="${e.floor}" title="${X(e.floor)} — ${X(e.role)}">
          <span>${X(e.short)}</span><small>${X(e.floor)}</small>
        </button>
      `).join(``)}
    </div>
    <button class="ls-os-focus" type="button" data-ls-focus title="Toggle focus mode">◫</button>
  `,e.querySelectorAll(`[data-ls-agent]`).forEach(e=>{e.addEventListener(`click`,()=>Q(e.dataset.lsAgent,!0))}),e.querySelector(`[data-ls-home]`)?.addEventListener(`click`,()=>Z(`command`)),e.querySelector(`[data-ls-focus]`)?.addEventListener(`click`,()=>{let e=!J.focusMode;Y({focusMode:e}),document.body.dataset.lsFocus=e?`true`:`false`}),e},Hn=()=>{let e=document.createElement(`section`);return e.className=`ls-os-status-strip`,e.setAttribute(`aria-label`,`UniSpace operating state`),e.innerHTML=`
    <div><span class="ls-os-status-dot" id="ls-os-runtime-dot"></span><strong id="ls-os-runtime">Desktop checking</strong><small>${n}</small></div>
    <div><span class="ls-os-status-dot stable"></span><strong>Neo operational head</strong><small>specialist-agent orchestration</small></div>
    <div><span class="ls-os-status-dot guarded"></span><strong>Achilles oversight</strong><small>evidence · canon · release gate</small></div>
    <div><span class="ls-os-status-dot private"></span><strong>De Sporte</strong><small>private persistence sidecar · metadata only</small></div>
    <button type="button" id="ls-os-palette-open" title="Open command palette (Ctrl/Cmd+K)">⌘K</button>
  `,e},Un=()=>{let e=document.createElement(`section`);return e.className=`ls-os-workflow`,e.setAttribute(`aria-label`,`ACR3 operating workflow`),e.innerHTML=`
    <div class="ls-os-workflow-track">
      ${jn.map((e,t)=>`
        <button type="button" data-ls-stage="${e.id}" title="${X(e.description)}">
          <span>${String(t+1).padStart(2,`0`)}</span><strong>${X(e.label)}</strong><small>${X(e.owner)}</small>
        </button>
      `).join(``)}
    </div>
    <div class="ls-os-stage-detail" id="ls-os-stage-detail"></div>
  `,e.querySelectorAll(`[data-ls-stage]`).forEach(e=>{e.addEventListener(`click`,()=>Bn(e.dataset.lsStage))}),e},Wn=()=>{let e=document.createElement(`div`);return e.className=`ls-os-palette`,e.id=`ls-os-palette`,e.hidden=!0,e.innerHTML=`
    <div class="ls-os-palette-card" role="dialog" aria-modal="true" aria-label="UniSpace command palette">
      <div class="ls-os-palette-head"><strong>UniSpace</strong><span>LightSpeed toolkit</span><button type="button" data-ls-close aria-label="Close">×</button></div>
      <input id="ls-os-palette-input" type="search" autocomplete="off" placeholder="Open workspace, select agent, or route an outcome…" />
      <div id="ls-os-palette-results" class="ls-os-palette-results"></div>
    </div>
  `,e.addEventListener(`click`,t=>{t.target===e&&$()}),e.querySelector(`[data-ls-close]`)?.addEventListener(`click`,()=>$()),e.querySelector(`#ls-os-palette-input`)?.addEventListener(`input`,()=>Kn()),e},Gn=()=>{let e=document.getElementById(`ls-os-palette`);e&&(e.hidden=!1,Kn(),window.setTimeout(()=>document.getElementById(`ls-os-palette-input`)?.focus(),0))},$=()=>{let e=document.getElementById(`ls-os-palette`);e&&(e.hidden=!0)},Kn=()=>{let e=document.getElementById(`ls-os-palette-input`),t=document.getElementById(`ls-os-palette-results`);if(!e||!t)return;let n=e.value.trim().toLowerCase(),r=An.filter(e=>!n||e.includes(n)).map(e=>`<button type="button" data-palette-view="${e}"><span>Workspace</span><strong>${e}</strong><small>Open ${e} workspace</small></button>`),i=Mn.filter(e=>!n||`${e.floor} ${e.role}`.toLowerCase().includes(n)).map(e=>`<button type="button" data-palette-agent="${e.floor}"><span>Agent</span><strong>${X(e.floor)}</strong><small>${X(e.role)}</small></button>`);t.innerHTML=[...n?[`<button type="button" data-palette-route="true"><span>Neo route</span><strong>${X(In(e.value))}</strong><small>Use this text as the command outcome and route it through Cognigrex.</small></button>`]:[],...r,...i].slice(0,14).join(``),t.querySelectorAll(`[data-palette-view]`).forEach(e=>e.addEventListener(`click`,()=>{Z(Nn(e.dataset.paletteView)),$()})),t.querySelectorAll(`[data-palette-agent]`).forEach(e=>e.addEventListener(`click`,()=>{Q(e.dataset.paletteAgent,!0),$()})),t.querySelector(`[data-palette-route]`)?.addEventListener(`click`,()=>{let t=e.value.trim(),n=document.getElementById(`instruction`);n&&t&&(n.value=t,n.dispatchEvent(new Event(`input`,{bubbles:!0})),Q(In(t)),Bn(Fn(t)),n.focus()),Z(`command`),$()})},qn=e=>{let t=e.querySelector(`#view-command .command-panel .panel-head .eyebrow`);t&&(t.textContent=`Neo intake`);let n=e.querySelector(`#view-command .command-panel .panel-head h2`);n&&(n.textContent=`State the outcome`);let r=e.querySelector(`#command-form button.primary[type=submit]`);r&&(r.textContent=`Send to runtime`);let i=e.querySelector(`#view-command .guardrail-panel .eyebrow`);i&&(i.textContent=`Cognigrex operating contract`);let a=e.querySelector(`#view-command .guardrail-panel h2`);a&&(a.textContent=`Neo-led work, durable proof`);let o=e.querySelectorAll(`#view-command .guardrail-panel .compact-list li`),s=[`Neo owns intake, decomposition, routing and aggregate workflow identity.`,`Specialist floors execute only their bounded purpose and return receipts.`,`Oracle, Smith and Morpheus preserve source, implementation and proof boundaries.`,`Achilles governs evidence class, canonical promotion, safety and release.`,`Accepted results return as compact canonical deltas rather than duplicate masters.`];o.forEach((e,t)=>{s[t]&&(e.textContent=s[t])});let c=e.querySelector(`#view-system .flow`);c&&(c.innerHTML=`<span>UniSpace</span><i>→</i><span>Neo</span><i>→</i><span>specialist floors</span><i>→</i><span>Morpheus proof</span><i>→</i><span>Achilles gate</span><i>→</i><span>canon / release</span>`);let l=e.querySelector(`#view-system .agent-grid`);if(l){let e=new Map;l.querySelectorAll(`.agent`).forEach(t=>{let n=t.querySelector(`strong`)?.textContent?.trim();n&&e.set(n,t)}),Mn.forEach(t=>{let n=e.get(t.floor);n&&l.append(n)})}e.querySelectorAll(`.panel-head`).forEach(e=>{if(e.querySelector(`h2`)?.textContent?.trim()!==`Review queue`)return;let t=e.querySelector(`.eyebrow`);t&&(t.textContent=`Achilles / owner gate`)})},Jn=()=>{document.querySelectorAll(`.tab[data-view]`).forEach(e=>{e.addEventListener(`click`,()=>{let t=Nn(e.dataset.view);Y({activeView:t}),document.body.dataset.lsWorkspace=t})});let e=document.getElementById(`instruction`),t=document.getElementById(`route-preview`);e?.addEventListener(`input`,()=>{let n=In(e.value);Q(n),Bn(Fn(e.value)),t&&(t.innerHTML=`<strong>Neo route:</strong> ${X(n)} is the primary specialist. Achilles remains the evidence, canonical-promotion and release oversight gate.`)}),document.getElementById(`ls-os-palette-open`)?.addEventListener(`click`,()=>Gn())},Yn=async()=>{let e=document.getElementById(`ls-os-runtime`),t=document.getElementById(`ls-os-runtime-dot`);if(e&&t)try{let n=await d(),r=!!(n.ok&&n.services?.merovingian!==!1);e.textContent=r?`Desktop online`:`Desktop degraded`,t.dataset.state=r?`online`:`degraded`,t.title=n.time_utc?`Last read ${n.time_utc}`:`Local status read`}catch{e.textContent=`Desktop offline / unproved`,t.dataset.state=`offline`,t.title=`No current localhost receipt from this browser.`}};queueMicrotask(()=>{if(document.documentElement.dataset.lsOsShell===`lightspeed-cognigrex-os-shell-v0.1`)return;let e=document.querySelector(`.shell`);if(!e)return;document.documentElement.dataset.lsOsShell=kn,document.body.classList.add(`ls-os-enabled`),document.body.dataset.lsFocus=J.focusMode?`true`:`false`,document.title=`UniSpace · Cognigrex`,document.body.prepend(Vn()),e.prepend(Un()),e.prepend(Hn()),document.body.append(Wn());let t=e.querySelector(`.topbar h1`);t&&(t.textContent=`UniSpace`);let n=e.querySelector(`.topbar .eyebrow`);n&&(n.textContent=`Cognigrex · powered by LightSpeed`);let r=e.querySelector(`.topbar .lede`);r&&(r.textContent=`Your Cognigrex workspace for .cgx objects, local tools and evidence. Neo coordinates specialist agents through LightSpeed; Achilles governs evidence and release.`),qn(e),Jn(),Z(J.activeView),Q(J.activeAgent);let i=document.getElementById(`instruction`);i?i.dispatchEvent(new Event(`input`,{bubbles:!0})):(Bn(`intake`),Q(`Neo`)),Yn().catch(()=>void 0),window.setInterval(()=>Yn().catch(()=>void 0),3e4),window.addEventListener(`keydown`,e=>{(e.ctrlKey||e.metaKey)&&e.key.toLowerCase()===`k`?(e.preventDefault(),Gn()):(e.key===`Escape`&&$(),(e.ctrlKey||e.metaKey)&&/^[1-6]$/.test(e.key)&&(e.preventDefault(),Z(An[Number(e.key)-1]||`command`)))})});