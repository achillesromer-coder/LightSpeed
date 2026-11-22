(function(){let e=document.createElement(`link`).relList;if(e&&e.supports&&e.supports(`modulepreload`))return;for(let e of document.querySelectorAll(`link[rel="modulepreload"]`))n(e);new MutationObserver(e=>{for(let t of e)if(t.type===`childList`)for(let e of t.addedNodes)e.tagName===`LINK`&&e.rel===`modulepreload`&&n(e)}).observe(document,{childList:!0,subtree:!0});function t(e){let t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),t.credentials=e.crossOrigin===`use-credentials`?`include`:e.crossOrigin===`anonymous`?`omit`:`same-origin`,t}function n(e){if(e.ep)return;e.ep=!0;let n=t(e);fetch(e.href,n)}})();var e=`lightspeed-go-command-v2`,t=`http://127.0.0.1:8765`,n=(e=>t)(void 0),r=[`Achilles`,`Neo`,`Architect`,`TheConstruct`,`Morpheus`,`Oracle`,`Smith`,`Merovingian`,`Trinity`],i=e=>e?.state===`ready_for_private_relay_verification`?{label:`Verify off-device`,detail:`Private HTTPS origin configured; remote owner flow still needs readback.`}:e?.state===`credential_gate`?{label:`Credential held`,detail:`Complete the owner password change before remote verification.`}:{label:`Local only`,detail:`No private HTTPS relay origin is configured.`},a=e=>{let t=e?.transport?.verified_carriers?.length||0,n=e?.compute?.peer_nodes?.length||0;return{transfer:e?.transport?.peer_transport_verified?`Peer transport verified · ${n} peer node${n===1?``:`s`}`:t?`Carrier readback verified · ${t} carrier${t===1?``:`s`} · peer transport unproven`:`No verified carrier or peer transport`,compute:e?.compute?.peer_compute_verified?`Peer compute verified · ${n} peer node${n===1?``:`s`}`:e?.compute?.local_ready?`Local compute ready · peer compute unproven`:`Compute unavailable or held`,boundary:e?.claim_boundary||`Node-exchange status is unavailable.`}},o=(e,t)=>e.replace(/\s+/g,` `).trim().slice(0,t),s=e=>{let t=e.toLowerCase();return/\b(ui|site|web|design|visual|layout|canva|accessibility)\b/.test(t)?`Trinity`:/\b(git|github|code|build|commit|branch|deploy|schema|api|runtime)\b/.test(t)?`Smith`:/\b(source|evidence|research|data|document|drive|sheet|workbook|citation)\b/.test(t)?`Oracle`:/\b(proof|claim|verify|conflict|confidence|audit)\b/.test(t)?`Morpheus`:/\b(simulate|simulation|model|gmat|trajectory|twin|physics)\b/.test(t)?`TheConstruct`:/\b(plan|mission|architecture|dependency|roadmap|system|project)\b/.test(t)?`Architect`:/\b(health|status|diagnostic|failure|error|monitor|storage|cleanup|archive)\b/.test(t)?`Merovingian`:/\b(coordinate|queue|handoff|agent|task|execute|run)\b/.test(t)?`Neo`:`Achilles`},c=t=>{let n=o(t.instruction,4e3);if(!n)throw TypeError(`instruction is required`);let r=new Date().toISOString(),i=Math.random().toString(36).slice(2,8).toUpperCase(),a=t.targetFloor??s(n),c=t.authorityContract;if(!c)throw TypeError(`Desktop authority contract is not available`);let l=o(c.canonical_gate_id,160),u=o(c.owner_decision_ref,160),d=o(c.core_acceptance_ref,160),f=o(c.approval_or_hold_state,40).toLowerCase(),p=o(c.authorised_scope,1e3),m=o(c.prohibited_scope,1e3);if(!l||!u||!d||!p||!m)throw TypeError(`Desktop authority contract is incomplete`);if(![`approve`,`approved`,`operator_approved`,`operator_authorized`,`operator_authorised`].includes(f))throw TypeError(`Desktop authority contract is held`);let h=t.executionMode??`review`;return{schema_version:e,command_id:`LSGO-${r.replace(/\D/g,``).slice(0,14)}-${i}`,created_utc:r,source:`LS GO`,title:o(t.title||n,160),instruction:n,target_floor:a,oversight_floor:`Achilles`,priority:t.priority??`normal`,execution_mode:h,action_type:t.actionType??`cognigrex_workflow`,proof_required:!0,public_safe:!0,canonical_gate_id:l,owner_decision_ref:u,core_acceptance_ref:d,approval_or_hold_state:f,authorised_scope:p,prohibited_scope:m,requested_scope:`${a} private local ${h} queue`}},l=class extends Error{status;constructor(e,t){super(t),this.name=`DesktopRequestError`,this.status=e}},u=async(e,t,n=3500)=>{let r=new AbortController,i=window.setTimeout(()=>r.abort(),n);try{let n=await fetch(e,{...t,signal:r.signal,cache:`no-store`});if(!n.ok){let e=`Desktop returned HTTP ${n.status}`;try{let t=await n.json();t.detail&&(e=t.detail)}catch{}throw new l(n.status,e)}return await n.json()}finally{window.clearTimeout(i)}},d=(e=n)=>u(`${e}/api/v1/status`,{method:`GET`},1e4),f=(e,t,r=n)=>u(`${r}/api/v1/auth/login`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify({username:o(e,64),password:t.slice(0,1024)})},15e3),p=(e,t,r,i,a,s=n)=>u(`${s}/api/v1/auth/change-password`,{method:`POST`,headers:{"Content-Type":`application/json`,[a?`X-LightSpeed-Password-Change`:`X-LightSpeed-Session`]:i.slice(0,256)},body:JSON.stringify({username:o(e,64),current_password:t.slice(0,1024),new_password:r.slice(0,1024)})},2e4),m=(e,t=n)=>u(`${t}/api/v1/auth/logout`,{method:`POST`,headers:{"X-LightSpeed-Session":e.slice(0,256)}},7e3),h=(e,t,r=n)=>u(`${r}/api/v1/node-exchange/transfer/plan`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":t.slice(0,256)},body:JSON.stringify(e)},1e4),g=(e,t,r=n)=>u(`${r}/api/v1/node-exchange/compute/plan`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":t.slice(0,256)},body:JSON.stringify(e)},1e4),_=(e,t=n)=>u(`${t}/api/v1/ls-go/commands`,{method:`POST`,headers:{"Content-Type":`application/json`},body:JSON.stringify(e)},7e3),v=async(e=n)=>{let t=await u(`${e}/api/v1/tasks?limit=12`,{method:`GET`});return Array.isArray(t.tasks)?t.tasks:[]},ee=async(e=n)=>{let t=await u(`${e}/api/v1/projects`,{method:`GET`},15e3);return{projects:Array.isArray(t.projects)?t.projects:[],summary:t.summary||{},duplicateNames:Array.isArray(t.duplicate_names)?t.duplicate_names:[],cleanupSummary:t.cleanup_summary||{}}},te=(e,t,n)=>{if(n!==void 0&&(t===void 0||!/^[a-f0-9]{64}$/.test(n)))throw Error(`Exact file metadata revision required.`);let r=encodeURIComponent(e);if(t===void 0)return`/api/v1/projects/${r}/files`;let i=`/api/v1/projects/${r}/files/${t.split(`/`).map(e=>encodeURIComponent(e)).join(`/`)}`;return n===void 0?i:`${i}?expected_metadata_revision=${n}`},ne=async(e,t=n)=>u(`${t}${te(e)}?limit=200`,{method:`GET`},15e3),re=async(e,t,r,i=n,a)=>u(`${i}${te(e,t,a)}`,{method:`GET`,cache:`no-store`,headers:{"X-LightSpeed-Session":r.slice(0,256)}},1e4),ie=(e,t)=>{if(t!==void 0&&(e===void 0||!/^[a-f0-9]{64}$/.test(t)))throw Error(`Exact receipt revision required.`);if(e===void 0)return`/api/v1/results`;let n=`/api/v1/results/${encodeURIComponent(e)}`;return t===void 0?n:`${n}?expected_sha256=${t}`},ae=async(e=n,t=50)=>u(`${e}${ie()}?limit=${Math.max(1,Math.min(t,200))}`,{method:`GET`},1e4),oe=async(e,t,r=n,i)=>u(`${r}${ie(e,i)}`,{method:`GET`,cache:`no-store`,headers:{"X-LightSpeed-Session":t.slice(0,256)}},1e4),se=async(e=n,t=50)=>{let r=await u(`${e}/api/v1/reviews?limit=${Math.max(1,Math.min(t,200))}`,{method:`GET`},1e4);return Array.isArray(r.reviews)?r.reviews:[]},ce=async(e,t,r=``,i=``,a=n)=>u(`${a}/api/v1/reviews/${encodeURIComponent(e)}/decision`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":i.slice(0,256)},body:JSON.stringify({decision:t,note:o(r,1e3)})},7e3),le=(e,t=n)=>u(`${t}/api/v1/cgx/surface?selector=LightSpeed`,{method:`GET`,headers:{"X-LightSpeed-Session":e.slice(0,256)}},1e4),ue=(e,t=n)=>u(`${t}/api/v1/cgx/family/topology`,{method:`GET`,headers:{"X-LightSpeed-Session":e.slice(0,256)}},12e3),de=e=>({roles:e.roles.filter(e=>!e.execution_enabled),routes:e.routes.filter(e=>e.state===`available`&&e.read_only&&!e.execution_enabled)}),fe=(e,t,r=n)=>u(`${r}/api/v1/cgx/persistence/checkpoint`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":t.slice(0,256)},body:JSON.stringify(e)},12e3),pe=(e,t,r,i,a=n)=>u(`${a}/api/v1/cgx/persistence/revoke/${encodeURIComponent(e)}/${encodeURIComponent(t)}`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":i.slice(0,256)},body:JSON.stringify({expected_candidate_sha256:r})},12e3),me=(e,t,n)=>{let r=n.receipt?.drive_writeback_mode;return r===`owner_approved_exact_drive_target`?`${e} marked ${t}. Owner-approved Drive decision receipt written by Desktop.`:r===`local_outbox_pending_drive_sync`?`${e} marked ${t}. Local outbox receipt staged; Drive sync remains pending.`:`${e} marked ${t}. Decision receipt recorded; destination requires verification.`},he=async(e=n)=>{let t=await u(`${e}/api/v1/representation-graphs`,{method:`GET`},15e3);return Array.isArray(t.graphs)?t.graphs:[]},ge=async(e,t,r,i=[],a=``,s=``,c=n)=>u(`${c}/api/v1/representation-reviews/${encodeURIComponent(e)}/decision`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-LightSpeed-Session":s.slice(0,256)},body:JSON.stringify({decision:t,scope:r,edge_ids:i.slice(0,100),note:o(a,1e3)})},1e4),_e=`lightspeed-go-pending-commands-v1`,ve=()=>{try{let e=JSON.parse(localStorage.getItem(_e)||`[]`);return Array.isArray(e)?e:[]}catch{return[]}},ye=e=>{let t=[e,...ve().filter(t=>t.command_id!==e.command_id)].slice(0,30);return localStorage.setItem(_e,JSON.stringify(t)),t},be=e=>{let t=ve().filter(t=>t.command_id!==e);return localStorage.setItem(_e,JSON.stringify(t)),t},xe=e=>{let t=new Blob([JSON.stringify(e,null,2)],{type:`application/json`}),n=URL.createObjectURL(t),r=document.createElement(`a`);r.href=n,r.download=`${e.command_id}.json`,r.click(),URL.revokeObjectURL(n)},Se=`lightspeed-neo-exchange-v1`,Ce=[`critical`,`high`,`normal`,`low`],we=[`queued`,`active`,`review`,`blocked`,`complete`],Te=[`icon`,`age_label`],Ee=e=>typeof e==`object`&&!!e&&!Array.isArray(e),y=(e,t,n)=>{if(typeof e!=`string`)return t;let r=e.replace(/\s+/g,` `).trim();return r?r.slice(0,n):t},De=(e,t,n)=>{let r=y(e,``,n);if(!r)throw TypeError(`queue record ${t} is required`);return r},Oe=(e,t,n)=>typeof e==`string`&&t.includes(e)?e:n,ke=e=>Ee(e)?Object.fromEntries(Te.flatMap(t=>{let n=y(e[t],``,48);return n?[[t,n]]:[]})):{},Ae=e=>{if(!Ee(e))throw TypeError(`queue record must be an object`);return{id:De(e.id,`id`,80),title:De(e.title,`title`,160),priority:Oe(e.priority,Ce,`normal`),status:Oe(e.status,we,`queued`),source:y(e.source,`GO Gate`,48),target:y(e.target,`Neo`,48),created_utc:y(e.created_utc,``,32),extensions:ke(e.extensions),notes:y(e.notes,``,240)}},je=e=>{if(!Ee(e))throw TypeError(`Neo exchange must be an object`);let t=Array.isArray(e.queue)?e.queue.map(Ae):[];return{schema_version:Se,generated_at_utc:y(e.generated_at_utc,``,32),queue:t}},Me=e=>({total:e.queue.length,critical:e.queue.filter(e=>e.priority===`critical`).length,active:e.queue.filter(e=>e.status!==`complete`).length,complete:e.queue.filter(e=>e.status===`complete`).length}),b=e=>e.replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#039;`})[e]??e),Ne=async e=>{try{return je(await e())}catch{return je({})}},Pe=e=>e.status===`blocked`?`blocked`:e.status===`complete`?`pass`:e.priority===`critical`||e.priority===`high`?`warn`:`ready`,Fe=e=>{let t=Me(e),n=e.queue.length?e.queue.map(e=>`
            <li class="status-row ${Pe(e)}">
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
  `},Ie=e=>{let t=de(e);return{revision:e.source_view_sha256,roles:t.roles.map(({id:e,floor:t})=>({id:e,label:t})),routes:t.routes.map(({id:e})=>({id:e,label:e})),canStage:t.roles.length>0&&t.routes.length>0&&e.native_mint_authorized===!1&&e.execution_authorized===!1,permission:`owner_session_private_review_only`}};function Le(e,t,n,r){let i=Ie(t),a=i.roles.map(e=>`<option value="`+b(e.id)+`">`+b(e.label)+`</option>`).join(``),o=i.routes.map(e=>`<option value="`+b(e.id)+`">`+b(e.label)+`</option>`).join(``),s=document.createElement(`details`);s.innerHTML=`<summary>Canonical Cognigrex persistence · review checkpoint</summary><p class="muted">Task-bound metadata only in the existing FileSpace/DataSpace operational ledger. This does not dispatch an agent, train weights, mint CGX, or grant source access.</p><form class="form-grid" id="cgx-native-checkpoint-form"><label class="field"><span>Existing task ID</span><input name="task" required maxlength="128" pattern="[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}" placeholder="task-001"></label><label class="field"><span>Run ID</span><input name="run" required maxlength="128" pattern="[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}" placeholder="run-001"></label><label class="field"><span>Specialist lane</span><select name="role" required>`+a+`</select></label><label class="field"><span>Read-only capability</span><select name="route" required>`+o+`</select></label><label class="field"><span>CPU planning ceiling</span><input name="cpu" type="number" min="1" max="4" value="1" required></label><label class="field"><span>Memory planning ceiling (MiB)</span><input name="memory" type="number" min="64" max="1024" value="128" required></label><label class="field"><span>Maximum jobs</span><input name="jobs" type="number" min="1" max="16" value="2" required></label><label class="field"><span>TTL (seconds)</span><input name="ttl" type="number" min="60" max="3600" value="900" required></label><button type="submit"`+(i.canStage?``:` disabled`)+`>Record private checkpoint</button><button type="button" id="cgx-native-revoke" hidden>Revoke checkpoint</button></form><p id="cgx-native-result" class="muted" role="status">No checkpoint recorded.</p>`,e.appendChild(s);let c=s.querySelector(`form`),l=s.querySelector(`#cgx-native-result`),u=s.querySelector(`#cgx-native-revoke`);if(!c||!l||!u)return;let d=e=>c.elements.namedItem(e);c.addEventListener(`submit`,async e=>{if(e.preventDefault(),!r()||!i.canStage)return;let t=d(`task`)?.value.trim()||``,a=d(`run`)?.value.trim()||``,o=d(`role`)?.value||``,s=d(`route`)?.value||``;if(t&&a&&o&&s){l.textContent=`Validating owner authority and canonical source revision…`;try{let e=await fe({selector:`LightSpeed`,task_id:t,run_id:a,expected_view_sha256:i.revision,role_ids:[o],route_ids:[s],cpu_threads:Number(d(`cpu`)?.value),memory_mib:Number(d(`memory`)?.value),max_jobs:Number(d(`jobs`)?.value),ttl_seconds:Number(d(`ttl`)?.value)},n);if(!r()||!l.isConnected)return;l.textContent=e.state+` · readback `+String(e.exact_readback_verified)+` · expires `+e.expires_utc+` · execution/mint held`,u.hidden=e.state!==`REVIEW_ONLY`,u.onclick=async()=>{if(r()){l.textContent=`Submitting bounded revocation…`;try{let i=await pe(t,a,e.candidate_sha256,n);if(!r()||!l.isConnected)return;l.textContent=i.state+` · readback `+String(i.exact_readback_verified),u.hidden=!0}catch(e){r()&&l.isConnected&&(l.textContent=e instanceof Error?e.message:`Revocation held`)}}}}catch(e){r()&&l.isConnected&&(l.textContent=e instanceof Error?e.message:`Native persistence deployment or authority is held`)}}})}var Re=e=>{let t=Number(e||0);return t<1024?`${t} B`:t<1024**2?`${(t/1024).toFixed(1)} KB`:t<1024**3?`${(t/1024**2).toFixed(1)} MB`:`${(t/1024**3).toFixed(1)} GB`},ze=e=>e.length?e.slice(0,30).map(e=>{let t=e.file_browser?.state??(e.authority===`external_reference`?`restricted`:void 0),n=!t||t===`available`,r=t&&t!==`available`?` · ${b(e.file_browser?.reason||`External references remain metadata-only until the bridge confirms bounded access.`)}`:``,i=n?`<button type="button" data-project-files="${b(e.project_id)}" aria-expanded="false">Files</button>`:`<small class="project-file-access">Files ${t===`restricted`?`held`:`unavailable`}</small>`;return`
    <article class="task-card project-card" data-project-card="${b(e.project_id)}">
      <div class="project-summary">
        <strong>${b(e.name)}</strong>
        <span>${b(e.condition||`unknown`)} · ${b(e.authority||`reference`)} · ${e.file_count||0} files</span>
        <small>${Re(e.size_bytes)}${e.scan_truncated?` · bounded scan`:``}${r}</small>
      </div>
      <div class="task-actions">
        ${i}
      </div>
      <div class="project-files" aria-live="polite" hidden></div>
    </article>
  `}).join(``):`<p class="muted">No project folders were found in the configured roots.</p>`,Be=e=>{let t=e.summary,n=`<p class="project-file-boundary">${b(e.boundary)}</p>`;if(!e.files.length){let t=e.state===`restricted`?`No files are visible; credential-like or excluded runtime files are withheld.`:`This registered project currently has no visible files.`;return`<div class="project-files-head"><strong>Files</strong><small>${b(e.project.authority||`reference`)} authority</small></div><p class="muted">${t}</p>${n}`}let r=e.files.map(t=>`
    <article class="project-file-row">
      <div><strong>${b(t.relative_path)}</strong><small>${b(t.mime_type)} · ${Re(t.size_bytes)}</small></div>
      <button type="button" data-project-file="${b(t.relative_path)}" data-project-id="${b(e.project.project_id)}">Open</button>
    </article>
  `).join(``),i=t.scan_truncated?` · bounded result`:``;return`
    <div class="project-files-head"><strong>Files</strong><small>${t.visible_file_count} visible · ${t.blocked_file_count} withheld${i}</small></div>
    <div class="project-file-list">${r}</div>
    <div class="project-file-result" aria-live="polite"></div>
    ${n}
  `},Ve=e=>`
  <div class="project-files-head"><strong>Files unavailable</strong></div>
  <p class="result" data-tone="bad">${b(e)}</p>
`,He=e=>{let t=e.preview,n=`<p class="muted">Metadata only. Binary or non-UTF-8 content is not transferred into UniSpace.</p>`;return t.state===`empty`?n=`<p class="muted">The file is empty.</p>`:t.state===`available`&&(n=`<pre>${b(t.text||``)}</pre>${t.truncated?`<small class="muted">Preview truncated at the governed byte limit.</small>`:``}`),`
    <section class="project-file-preview">
      <div class="project-files-head"><strong>${b(e.file.relative_path)}</strong><small>${b(e.file.mime_type)} · ${Re(e.file.size_bytes)}</small></div>
      ${n}
      <p class="project-file-boundary">${b(e.boundary)}</p>
    </section>
  `},Ue=(e,t)=>{e.querySelectorAll(`[data-project-files]`).forEach(e=>{e.addEventListener(`click`,()=>{let n=e.dataset.projectFiles||``;n&&t(n,e)})})},We=(e,t)=>{e.querySelectorAll(`[data-project-file][data-project-id]`).forEach(e=>{e.addEventListener(`click`,()=>{let n=e.dataset.projectId||``,r=e.dataset.projectFile||``;n&&r&&t(n,r,e)})})},Ge=e=>{let t=Number(e||0);return t<1024?`${t} B`:t<1024**2?`${(t/1024).toFixed(1)} KB`:`${(t/1024**2).toFixed(1)} MB`},Ke=e=>{let t=String(e.status||`unknown`).toLowerCase();return[`complete`,`completed`,`pass`,`passed`].includes(t)?`good`:[`blocked`,`failed`,`error`].includes(t)?`bad`:`warn`},qe=(e,t)=>{let n=e.summary,r=`<p class="result-receipt-boundary">${b(e.boundary)}</p>`,i=t?`Exact receipt content requires the local owner-confirmation token.`:`Content inspection is held because the local owner-confirmation token is not configured.`;if(!e.results.length)return`<p class="muted">${e.state===`restricted`?`No eligible fixed receipts are visible; invalid receipt objects remain withheld.`:`No fixed local result receipts have been written yet.`}</p><p class="result-receipt-auth">${i}</p>${r}`;let a=e.results.map(e=>{let n=e.action_type||`untyped`,r=e.target_floor||`floor unknown`,i=e.completed_utc||e.created_utc||e.modified_utc,a=[e.task_id==null?null:`Task ${e.task_id}`,e.job_id==null?null:`Job ${e.job_id}`,e.command_id||null].filter(Boolean).join(` · `),o=t?``:` disabled aria-disabled="true"`;return`
      <article class="task-card result-receipt-card" data-result-state="${Ke(e)}">
        <div>
          <strong>${b(e.result_id)}</strong>
          <span>${b(e.status)} · ${b(n)} · ${b(r)}</span>
          <small>${b(a||`No task/job identity`)} · ${b(i||`time unavailable`)} · ${Ge(e.size_bytes)}</small>
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
  `},Je=e=>{let t=JSON.stringify(e.result,null,2);return`
    <section class="result-receipt-preview">
      <div class="result-receipt-preview-head">
        <strong>${b(e.identity.result_id)}</strong>
        <small>${Ge(e.identity.size_bytes)} · SHA-256 ${b(e.identity.sha256)}</small>
      </div>
      <pre>${b(t)}</pre>
      <p class="result-receipt-boundary">${b(e.boundary)}</p>
    </section>
  `},x=e=>`
  <p class="result" data-tone="bad">${b(e)}</p>
`,Ye=(e,t)=>{e.querySelectorAll(`[data-result-receipt]`).forEach(e=>{e.addEventListener(`click`,()=>{let n=e.dataset.resultReceipt||``;n&&!e.disabled&&t(n,e)})})},S=e=>String(e??``).replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),Xe=e=>e?`${e.slice(0,12)}…${e.slice(-8)}`:`not available`,Ze=e=>e.path_exposed===!1?String(e.label||`private local evidence`):[e.repository,e.commit_sha?`commit ${String(e.commit_sha).slice(0,12)}`:null,e.path,e.drive_file_id?`Drive ${e.drive_file_id}`:null,e.sheet_name,e.stable_key||e.content_key,e.missing_state].filter(Boolean).map(S).join(` · `)||S(e.locator_type||`logical`),Qe=e=>S(JSON.stringify(e,null,2)),$e=e=>{let t=e.representations.filter(e=>e.state===`active`).length,n=e.missing.length;return!t&&n?`unable to determine`:n>t?`smaller bowl`:t>n?`larger bowl`:`unchanged bowl`},et=e=>{let t=e.review,n=t?.review_stage||`identity`,r=e.edges.map(e=>e.edge_id).join(`|`),i=t?`
    <div class="graph-actions" data-review-stage="${S(n)}">
      <strong>${n===`identity`?`Review identity first`:`Review ${e.edges.length} bounded edges`}</strong>
      <div class="task-actions">
        <button data-representation-review="${S(t.review_id)}" data-scope="${n}" data-edge-ids="${S(r)}" data-decision="approve">Approve</button>
        <button data-representation-review="${S(t.review_id)}" data-scope="${n}" data-edge-ids="${S(r)}" data-decision="provisional_approve">Provisional</button>
        <button data-representation-review="${S(t.review_id)}" data-scope="${n}" data-edge-ids="${S(r)}" data-decision="hold">Hold</button>
        <button data-representation-review="${S(t.review_id)}" data-scope="${n}" data-edge-ids="${S(r)}" data-decision="request_evidence">Request evidence</button>
        <button data-representation-review="${S(t.review_id)}" data-scope="${n}" data-edge-ids="${S(r)}" data-decision="reject">Reject</button>
        <button data-representation-review="${S(t.review_id)}" data-scope="${n}" data-edge-ids="${S(r)}" data-decision="supersede">Supersede</button>
      </div>
      <small>${S(t.state)} · graph ${Xe(t.graph_sha256)}</small>
    </div>`:`<p class="muted">Review packet has not been staged.</p>`,a=e.representations.map(e=>`
    <tr>
      <td><strong>${S(e.representation_type)}</strong><small>${S(e.representation_id)}</small></td>
      <td>${Ze(e.locator)}</td>
      <td>${S(e.source_authority)}</td>
      <td>${Xe(e.content_sha256)}</td>
      <td>${S(e.confidence_class)} (${Math.round(e.confidence_numeric*100)}%)</td>
      <td><span class="state-chip" data-state="${S(e.state)}">${S(e.state)}</span></td>
      <td>${S(e.claim_boundary)}</td>
    </tr>`).join(``),o=e.edges.map(e=>`
    <tr>
      <td>${S(e.from_representation_id)}</td>
      <td><strong>${S(e.relation)}</strong></td>
      <td>${S(e.to_representation_id)}</td>
      <td>${S(e.evidence_bundle_id||`not required`)}</td>
      <td>${S(e.review_state)}</td>
      <td>${S(e.claim_boundary)}</td>
    </tr>`).join(``),s=e.missing.length?e.missing.map(e=>`
      <article class="missing-card">
        <strong>${S(e.type)} · ${S(e.missing_state)}</strong>
        <span><b>Why:</b> ${S(e.reason)}</span>
        <span><b>Next:</b> ${S(e.next_evidence_action)}</span>
        <small>Last search: ${S(e.last_search||`not recorded`)} · Floor: ${S(e.assigned_floor)} · Effect: ${S(e.dependency_effect)}</small>
      </article>`).join(``):`<p class="muted">No required representation is currently missing.</p>`,c=e.conflicts.length?e.conflicts.map(e=>`<article class="missing-card conflict"><strong>${S(e.edge_id)}</strong><span>${S(e.claim_boundary)}</span></article>`).join(``):`<p class="muted">No representation conflict is recorded.</p>`,l=e.horizons.length?e.horizons.map(e=>`
      <article class="horizon-card">
        <div><strong>${S(e.name)}</strong><span>${S(e.state)} · ${S(e.horizon_type)}</span></div>
        <p>${S(e.objective)}</p>
        <details><summary>Assumptions and constraints</summary><pre>${Qe({assumptions:e.assumptions,constraints:e.constraints})}</pre></details>
        <small>Input ${Xe(e.input_set_sha256)}</small>
      </article>`).join(``):`<p class="muted">No horizon is assigned.</p>`,u=e.representations.find(e=>e.representation_type===`recommendation`)?.locator.next_highest_value_question,d=(e.linked_objects||[]).length?(e.linked_objects||[]).map(t=>{let n=(e.linked_identifiers||[]).filter(e=>e.object_id===t.object_id).map(e=>`${e.namespace}: ${e.identifier_value}`).join(` | `);return`<article class="missing-card">
        <strong>${S(t.display_name)} · ${S(t.state)}</strong>
        <span><b>Object:</b> ${S(t.object_id)}</span>
        <span><b>Identifiers:</b> ${S(n||`none recorded`)}</span>
      </article>`}).join(``):`<p class="muted">No linked object identity is included.</p>`,f=(e.evidence_bundles||[]).length?(e.evidence_bundles||[]).map(e=>`
      <article class="horizon-card">
        <div><strong>${S(e.title)}</strong><span>${S(e.state)}</span></div>
        <p>${S(e.claim_boundary)}</p>
        <small>${e.independence_group_count} independence groups · ${e.duplicate_reference_count} duplicate references · confidence effect ${e.confidence_effect}</small>
        <details><summary>Source weight summary</summary><pre>${Qe(e.source_weight_summary)}</pre></details>
      </article>`).join(``):`<p class="muted">No evidence bundle is linked.</p>`;return`
    <article class="panel graph-panel" data-object-id="${S(e.object.object_id)}">
      <div class="panel-head">
        <div>
          <p class="eyebrow">${S(e.object.object_type)}</p>
          <h2>${S(e.object.display_name)}</h2>
          <p>${S(e.object.description)}</p>
        </div>
        <span class="badge">${S(e.canonical_state)}</span>
      </div>
      <div class="graph-summary">
        <div><span>Object ID</span><strong>${S(e.object.object_id)}</strong></div>
        <div><span>Authority</span><strong>${S(e.object.authority)}</strong></div>
        <div><span>Identity</span><strong>${S(e.object.identity_confidence_class)} · ${Math.round(e.object.identity_confidence_numeric*100)}%</strong></div>
        <div><span>Current horizon</span><strong>${S(e.horizons[0]?.name||`not assigned`)}</strong></div>
        <div><span>Judgment</span><strong>${$e(e)}</strong></div>
      </div>
      <details open><summary>Identifiers (${e.identifiers.length})</summary><div class="identifier-list">${e.identifiers.map(e=>`<span><strong>${S(e.namespace)}</strong>${S(e.identifier_value)} · ${S(e.authority)}</span>`).join(``)}</div></details>
      <details open><summary>Linked identities (${(e.linked_objects||[]).length})</summary><div class="graph-grid">${d}</div></details>
      <details open><summary>Representations (${e.representations.length})</summary><div class="table-scroll"><table class="graph-table"><thead><tr><th>Type</th><th>Locator</th><th>Authority</th><th>Hash/revision</th><th>Confidence</th><th>State</th><th>Claim boundary</th></tr></thead><tbody>${a}</tbody></table></div></details>
      <details open><summary>Edges (${e.edges.length})</summary><div class="table-scroll"><table class="graph-table"><thead><tr><th>Source</th><th>Relation</th><th>Destination</th><th>Evidence</th><th>Review</th><th>Boundary</th></tr></thead><tbody>${o}</tbody></table></div></details>
      <details open><summary>Evidence bundles (${(e.evidence_bundles||[]).length})</summary>${f}</details>
      <div class="graph-grid">
        <section><h3>Missing</h3>${s}</section>
        <section><h3>Conflicts</h3>${c}</section>
      </div>
      <section><h3>Horizon</h3>${l}</section>
      <div class="next-question"><strong>Next highest-value question</strong><span>${S(u||`Owner review determines the next bounded question.`)}</span></div>
      ${i}
    </article>`},tt=e=>e.length?e.map(et).join(``):`<article class="panel"><p class="muted">The feature-gated representation edge is disabled or unavailable.</p></article>`,C=e=>e.replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),nt=e=>`
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
      ${e.surfaces.map(e=>`<tr><td><strong>${C(e.id)} · ${C(e.name)}</strong></td><td>${C(e.role)}</td></tr>`).join(``)}
    </tbody></table></div>
    <div class="boundary"><strong>${C(e.inference_example.label)}</strong><span>${C(e.inference_example.equation)} · ${C(e.inference_example.inputs)} → ${C(e.inference_example.result)}. ${C(e.inference_example.evidence)}</span></div>
    <p class="muted"><strong>Active contracts:</strong> ${e.contracts.map(C).join(` · `)}</p>
    <p class="muted">${C(e.boundary)}</p>
  </article>`,rt=async e=>nt(await e()),w=e=>e.replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),T=(e,t)=>`<div><strong>${w(String(e))}</strong><span>${w(t)}</span></div>`,it=e=>`
  <section class="cgx-lens-panel active" data-cgx-lens-panel="overview">
    <div class="graph-summary">
      ${T(e.metrics.archetypes,`archetypes`)}
      ${T(e.metrics.matrix_fields,`matrix fields`)}
      ${T(e.metrics.equation_kernels,`equation kernels`)}
      ${T(e.metrics.volumetric_kernels,`volumetric kernels`)}
      ${T(e.metrics.printable_4d_templates,`printable 4D templates`)}
      ${T(e.metrics.quantitative_invariants,`quantitative invariants`)}
      ${T(e.metrics.smart_stack_regions,`smart-stack regions`)}
      ${T(e.metrics.compound_decomposition_templates,`compound decompositions`)}
      ${T(e.metrics.initial_instances,`proof instances`)}
      ${T(e.metrics.requirement_targets_open,`open target gates`)}
      ${T(e.metrics.physical_tests_run,`physical tests complete`)}
    </div>
    <div class="flow cgx-pipeline">
      ${e.pipeline.map(e=>`<span title="${w(e.contract)}">${w(e.label)} · ${w(e.state)}</span>`).join(`<i>→</i>`)}
    </div>
    <div class="boundary"><strong>${w(e.headline.state)}</strong><span>${w(e.headline.note)}</span></div>
  </section>`,at=e=>`
  <section class="cgx-lens-panel" data-cgx-lens-panel="instances" hidden>
    <div class="graph-summary">
      ${Object.entries(e.gate_counts).map(([e,t])=>T(t,e.replace(/_/g,` `).toLowerCase())).join(``)}
    </div>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>CGXI</th><th>Stage</th><th>Current gate</th><th>Target</th><th>Next evidence</th></tr></thead>
        <tbody>
          ${e.instances.map(e=>`<tr>
            <td><strong>${w(e.instance_id)}</strong><small class="cgx-uri">${w(e.binding_uri)}</small><small>${w(e.binding_progress)} · ${w(e.physical_state)}</small></td>
            <td>${w(e.proof_stage)}<br><small>${w(e.archetype)}</small></td>
            <td><span class="badge">${w(e.first_open_gate)}</span></td>
            <td>${w(e.target)}</td>
            <td>${w(e.next)}</td>
          </tr>`).join(``)}
        </tbody>
      </table>
    </div>
  </section>`,ot=e=>`
  <section class="cgx-lens-panel" data-cgx-lens-panel="kernels" hidden>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>Kernel</th><th>Primitive</th><th>Model family</th><th>Inference gate</th></tr></thead>
        <tbody>
          ${e.kernels.map(e=>`<tr><td><strong>${w(e.kernel_id)}</strong></td><td>${w(e.primitive)}</td><td>${w(e.model)}</td><td>${w(e.gate)}</td></tr>`).join(``)}
        </tbody>
      </table>
    </div>
  </section>`,st=e=>`
  <section class="cgx-lens-panel" data-cgx-lens-panel="volumetric" hidden>
    <div class="graph-summary">
      ${T(e.metrics.volumetric_kernels,`volumetric kernels`)}
      ${T(e.topology_coverage.specific_or_multi,`specific / explicit multi-kernel archetypes`)}
      ${T(e.topology_coverage.final_generic_only,`intentional generic-coupled archetypes`)}
      ${T(`${e.topology_coverage.baseline_generic_only} → ${e.topology_coverage.final_generic_only}`,`generic fallback refinement`)}
    </div>
    <div class="boundary"><strong>UTP-140 coverage closure</strong><span>${w(e.topology_coverage.rule)} Residual: ${e.topology_coverage.residual.map(w).join(` · `)}</span></div>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>Kernel</th><th>Primitive</th><th>Topology / geometry</th><th>Compiler token</th><th>Numeric gate</th></tr></thead>
        <tbody>
          ${e.volumetric_kernels.map(e=>`<tr><td><strong>${w(e.kernel_id)}</strong></td><td>${w(e.primitive)}</td><td>${w(e.topology)}</td><td><small class="cgx-uri">${w(e.token)}</small></td><td>${w(e.gate)}</td></tr>`).join(``)}
        </tbody>
      </table>
    </div>
  </section>`,ct=e=>`
  <section class="cgx-lens-panel" data-cgx-lens-panel="printable" hidden>
    <div class="panel-head">
      <div><p class="eyebrow">UTP-138 · BUILD-070</p><h3>Printable 4D component + stack packets</h3></div>
      <span class="badge">${w(e.printable_4d.state)}</span>
    </div>
    <div class="graph-summary">
      ${T(e.printable_4d.template_count,`derived catalogue templates`)}
      ${T(e.printable_4d.exact_instance_inputs,`current exact-instance inputs`)}
      ${T(e.printable_4d.coupled_stack_kernel,`coupled stack kernel`)}
      ${T(`READ ONLY`,`no machine authority`)}
    </div>
    <p class="muted">Schemas: ${w(e.printable_4d.packet_schema)} · ${w(e.printable_4d.stack_schema)} · ${w(e.printable_4d.catalogue_schema)}</p>
    <div class="two-column">
      <div>
        <strong>Print paths</strong>
        <div class="stack-list">
          ${e.printable_4d.print_paths.map(e=>`<article class="task-card"><div><strong>${w(e.id)}</strong><small>${w(e.role)}</small></div></article>`).join(``)}
        </div>
      </div>
      <div>
        <strong>Exact packet examples</strong>
        <div class="stack-list">
          ${e.printable_4d.exact_examples.map(e=>`<article class="task-card"><div><strong>${w(e.instance_id)}</strong><span>${w(e.state)}</span><small>${w(e.topology)} · next: ${w(e.next_gate)}</small></div></article>`).join(``)}
        </div>
      </div>
    </div>
    <div class="boundary"><strong>Compiler invariants</strong><span>${e.printable_4d.invariants.map(w).join(` · `)}</span></div>
    <div class="boundary"><strong>${String(e.printable_4d.compound_decomposition.count)} compound-parent grammars</strong><span>${w(e.printable_4d.compound_decomposition.state)} · ${e.printable_4d.compound_decomposition.parents.map(w).join(` · `)}</span></div>
    <p class="muted">${w(e.printable_4d.compound_decomposition.rule)}</p>
  </section>`,lt=e=>`
  <section class="cgx-lens-panel" data-cgx-lens-panel="smartstack" hidden>
    <div class="panel-head">
      <div><p class="eyebrow">UTP-139 · BUILD-071</p><h3>Quantitative invariants + dense 4D smart stack</h3></div>
      <span class="badge">${w(e.quantitative_invariants.state)}</span>
    </div>
    <div class="graph-summary">
      ${T(e.metrics.quantitative_invariants,`reusable invariants`)}
      ${T(e.metrics.smart_stack_regions,`smart-stack regions`)}
      ${T(e.dense_smart_stack.coupled_kernel,`coupled assembly kernel`)}
      ${T(`NUMERIC_IF`,`evidence/regime conditional`)}
    </div>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>Invariant</th><th>Role</th><th>Equation</th><th>Current bounded example</th><th>Gate</th></tr></thead>
        <tbody>
          ${e.quantitative_invariants.records.map(e=>`<tr><td><strong>${w(e.id)}</strong></td><td>${w(e.role)}</td><td><small class="cgx-uri">${w(e.equation)}</small></td><td>${w(e.example)}</td><td>${w(e.gate)}</td></tr>`).join(``)}
        </tbody>
      </table>
    </div>
    <div class="boundary"><strong>Invariant rule</strong><span>${w(e.quantitative_invariants.rule)}</span></div>
    <p class="muted"><strong>Smart-stack:</strong> <span class="cgx-uri">${w(e.dense_smart_stack.cgx_uri)}</span> · ${w(e.dense_smart_stack.state)}</p>
    <div class="table-scroll">
      <table class="graph-table">
        <thead><tr><th>Region</th><th>Functional role</th><th>Topology kernels</th><th>State</th></tr></thead>
        <tbody>
          ${e.dense_smart_stack.regions.map(e=>`<tr><td><strong>${w(e.id)}</strong></td><td>${w(e.role)}</td><td><small class="cgx-uri">${w(e.kernels)}</small></td><td><span class="badge">${w(e.state)}</span></td></tr>`).join(``)}
        </tbody>
      </table>
    </div>
    <div class="boundary"><strong>Stack rule</strong><span>${w(e.dense_smart_stack.rule)}</span></div>
  </section>`,ut=e=>`
  <section class="cgx-lens-panel" data-cgx-lens-panel="showcase" hidden>
    <div class="panel-head">
      <div><p class="eyebrow">Public-safe candidate</p><h3>${w(e.showcase.title)}</h3></div>
      <span class="badge">${w(e.showcase.publication_state)}</span>
    </div>
    <p>${w(e.showcase.summary)}</p>
    <div class="graph-summary">${e.showcase.metrics.map(({value:e,label:t})=>T(e,t)).join(``)}</div>
    <div class="two-column">
      <div><strong>Safe showcase points</strong><ul class="compact-list">${e.showcase.safe_points.map(e=>`<li>${w(e)}</li>`).join(``)}</ul></div>
      <div><strong>Excluded from publication</strong><ul class="compact-list">${e.showcase.excludes.map(e=>`<li>${w(e)}</li>`).join(``)}</ul></div>
    </div>
  </section>`,dt=e=>`
  <article class="panel cgx-review-lens">
    <div class="panel-head">
      <div><p class="eyebrow">.cgx interactive review lens</p><h2>${w(e.headline.title)}</h2></div>
      <span class="badge">${w(e.authority.queue_id)} · ${w(e.authority.physical_state)}</span>
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
    ${it(e)}
    ${at(e)}
    ${ot(e)}
    ${st(e)}
    ${ct(e)}
    ${lt(e)}
    ${ut(e)}
    <p class="muted">${w(e.boundary)}</p>
  </article>`,ft=e=>{let t=[...e.querySelectorAll(`[data-cgx-lens]`)],n=[...e.querySelectorAll(`[data-cgx-lens-panel]`)],r=e=>{t.forEach(t=>{let n=t.dataset.cgxLens===e;t.classList.toggle(`active`,n),t.setAttribute(`aria-selected`,String(n))}),n.forEach(t=>{let n=t.dataset.cgxLensPanel===e;t.classList.toggle(`active`,n),t.hidden=!n})};t.forEach(e=>e.addEventListener(`click`,()=>r(e.dataset.cgxLens||`overview`))),r(`overview`)},pt=async e=>{let t=await e();return{data:t,html:dt(t)}},E=e=>e.replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),mt=(e,t)=>[e[1]*t[2]-e[2]*t[1],e[2]*t[0]-e[0]*t[2],e[0]*t[1]-e[1]*t[0]],ht=(e,t)=>[e[0]-t[0],e[1]-t[1],e[2]-t[2]],gt=e=>Math.hypot(e[0],e[1],e[2])||1,_t=e=>{let t=gt(e);return[e[0]/t,e[1]/t,e[2]/t]},vt=(e,t)=>e[0]*t[0]+e[1]*t[1]+e[2]*t[2],yt=(e,t=0,n=1)=>Math.max(t,Math.min(n,e)),bt=(e,t,n)=>{let r=t*Math.PI/180,i=n*Math.PI/180,a=e[0]*Math.cos(i)-e[1]*Math.sin(i),o=e[0]*Math.sin(i)+e[1]*Math.cos(i),s=e[2];return[a,o*Math.cos(r)-s*Math.sin(r),o*Math.sin(r)+s*Math.cos(r)]},xt=(e,t,n)=>e.map((e,r)=>Math.round(e+(t[r]-e)*n)),St=e=>`rgb(${e[0]},${e[1]},${e[2]})`,Ct=(e,t,n)=>{let r=e.getContext(`2d`);if(!r)return;let i=Math.min(window.devicePixelRatio||1,2),a=Math.max(e.clientWidth,320),o=Math.max(e.clientHeight,320),s=Math.round(a*i),c=Math.round(o*i);(e.width!==s||e.height!==c)&&(e.width=s,e.height=c),r.setTransform(i,0,0,i,0,0);let l=a,u=o;r.clearRect(0,0,l,u);let d=r.createRadialGradient(l*.58,u*.42,20,l*.55,u*.45,Math.max(l,u)*.75);d.addColorStop(0,`#173033`),d.addColorStop(.55,`#0c191b`),d.addColorStop(1,`#050a0b`),r.fillStyle=d,r.fillRect(0,0,l,u),r.strokeStyle=`rgba(41,64,67,.25)`,r.lineWidth=1;for(let e=0;e<l;e+=48)r.beginPath(),r.moveTo(e,0),r.lineTo(e,u),r.stroke();for(let e=0;e<u;e+=48)r.beginPath(),r.moveTo(0,e),r.lineTo(l,e),r.stroke();let f=t.vertices.map(e=>bt(e,n.elev,n.azim)),p=1/0,m=-1/0,h=1/0,g=-1/0,_=1/0,v=-1/0;for(let e of f)p=Math.min(p,e[0]),m=Math.max(m,e[0]),h=Math.min(h,e[1]),g=Math.max(g,e[1]),_=Math.min(_,e[2]),v=Math.max(v,e[2]);let ee=Math.max(m-p,1e-9),te=Math.max(g-h,1e-9),ne=Math.max(v-_,1e-9),re=Math.min(l*.78/ee,u*.72/te)*n.zoom,ie=l*.53,ae=u*.53,oe=Math.max(ee,te,ne)*7.5,se=f.map(e=>{let t=e[2]-(_+v)/2,n=oe/(oe-t);return[ie+(e[0]-(p+m)/2)*re*n,ae-(e[1]-(h+g)/2)*re*n,e[2]]}),ce=_t([-.45,-.35,.82]),le=_t([.6,-.2,.5]),ue=_t([.25,.8,.5]),de=t.faces.map(e=>{let t=f[e[0]],n=f[e[1]],r=f[e[2]],i=_t(mt(ht(n,t),ht(r,t)));return{t:e,z:(t[2]+n[2]+r[2])/3,intensity:yt(.16+.58*Math.abs(vt(i,ce))+.16*Math.abs(vt(i,le))+.1*Math.abs(vt(i,ue)),.12,1)}}).sort((e,t)=>e.z-t.z);r.save(),r.shadowColor=`rgba(0,0,0,.4)`,r.shadowBlur=24,r.fillStyle=`rgba(0,0,0,.3)`,r.beginPath(),r.ellipse(ie,u*.82,Math.min(l*.27,380)*n.zoom,Math.max(20,u*.035)*n.zoom,0,0,Math.PI*2),r.fill(),r.restore();let fe=[17,38,41],pe=[92,222,214],me=[200,164,88],he=Math.max(1,Math.ceil(de.length/9e3));for(let e=0;e<de.length;e+=he){let{t,intensity:n}=de[e],i=se[t[0]],a=se[t[1]],o=se[t[2]],s=xt(fe,pe,n);n>.82&&(s=xt(s,me,.12)),r.beginPath(),r.moveTo(i[0],i[1]),r.lineTo(a[0],a[1]),r.lineTo(o[0],o[1]),r.closePath(),r.fillStyle=St(s),r.fill(),r.strokeStyle=`rgba(120,227,221,.15)`,r.lineWidth=.55,r.stroke()}r.fillStyle=`#aab9b8`,r.font=`12px ui-monospace, SFMono-Regular, Consolas, monospace`,r.fillText(`az ${n.azim.toFixed(0)}° · el ${n.elev.toFixed(0)}° · zoom ${n.zoom.toFixed(2)}×`,16,u-18)},wt=()=>`
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
  </div>`,D=null,O=null,Tt=()=>{if(D)return D;D=document.createElement(`div`),D.className=`mesh-viewer-modal`,D.hidden=!0,D.innerHTML=wt(),document.body.append(D);let e=()=>{D&&(D.hidden=!0,O?.abort(),O=null,document.body.classList.remove(`mesh-viewer-open`))};return D.querySelector(`.mesh-viewer-close`)?.addEventListener(`click`,e),D.addEventListener(`click`,t=>{t.target===D&&e()}),window.addEventListener(`keydown`,t=>{t.key===`Escape`&&D&&!D.hidden&&e()}),D},Et=async e=>{let t=Tt();O?.abort(),O=new AbortController,t.hidden=!1,document.body.classList.add(`mesh-viewer-open`);let n=t.querySelector(`[data-mesh-title]`),r=t.querySelector(`[data-mesh-state]`),i=t.querySelector(`[data-mesh-source]`),a=t.querySelector(`[data-mesh-hash]`),o=t.querySelector(`.mesh-viewer-canvas`);if(!o)return;n&&(n.textContent=e.label),r&&(r.textContent=e.physicalState),i&&(i.textContent=e.source),a&&(a.textContent=e.sourceHash?`source SHA-256 ${e.sourceHash}`:`source hash in mesh payload`);let s=o.getContext(`2d`);s&&(s.fillStyle=`#071011`,s.fillRect(0,0,o.width,o.height));let c;try{let t=await fetch(e.url,{cache:`no-store`,signal:O.signal});if(!t.ok)throw Error(`mesh payload HTTP ${t.status}`);c=await t.json()}catch(e){if(e.name===`AbortError`)return;s&&(s.fillStyle=`#e27e7e`,s.font=`16px sans-serif`,s.fillText(`Interactive mesh unavailable.`,20,36));return}let l={elev:22,azim:-38,zoom:1},u=!1,d=0,f=0,p=0,m=()=>{cancelAnimationFrame(p),p=requestAnimationFrame(()=>Ct(o,c,l))},h=()=>{l.elev=22,l.azim=-38,l.zoom=1,m()},g=e=>{u=!0,d=e.clientX,f=e.clientY,o.setPointerCapture(e.pointerId)},_=e=>{if(!u)return;let t=e.clientX-d,n=e.clientY-f;d=e.clientX,f=e.clientY,l.azim+=t*.35,l.elev=Math.max(-85,Math.min(85,l.elev+n*.28)),m()},v=()=>{u=!1};o.onpointerdown=g,o.onpointermove=_,o.onpointerup=v,o.onpointercancel=v,o.onwheel=e=>{e.preventDefault(),l.zoom=Math.max(.35,Math.min(4,l.zoom*Math.exp(-e.deltaY*.001))),m()},o.ondblclick=h,new ResizeObserver(m).observe(o),m()},Dt=e=>`
  <button type="button" class="button-secondary mesh-viewer-trigger"
    data-mesh-url="${E(e.url)}"
    data-mesh-label="${E(e.label)}"
    data-mesh-source="${E(e.source)}"
    data-mesh-hash="${E(e.sourceHash||``)}"
    data-mesh-state="${E(e.physicalState)}">Interactive 3D</button>`,Ot=e=>{e.querySelectorAll(`.mesh-viewer-trigger`).forEach(e=>{e.addEventListener(`click`,()=>void Et({url:e.dataset.meshUrl||``,label:e.dataset.meshLabel||`Object`,source:e.dataset.meshSource||``,sourceHash:e.dataset.meshHash||``,physicalState:e.dataset.meshState||`REVIEW ONLY`}))})},k=e=>e.replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&apos;`),kt=(e,t=58,n=5)=>{let r=(e||`UNRESOLVED`).replace(/\s+/g,` `).trim().split(` `),i=[],a=``;for(let e of r){let r=(a+` `+e).trim();if(r.length>t&&a?(i.push(a),a=e):a=r,i.length>=n)break}return i.length<n&&a&&i.push(a),i.slice(0,n)},A=(e,t,n,r,i=58)=>{let a=kt(r,i,4);return`<g transform="translate(${e} ${t})"><text class="kicker" x="0" y="0">${k(n)}</text>${a.map((e,t)=>`<text class="body" x="0" y="${54+t*44}">${k(e)}</text>`).join(``)}</g>`},At=e=>{let t=[e.Domain,e.Family,e[`Component Archetype`],e[`Primary Physics`]].filter(Boolean).join(` `).toLowerCase();return t.includes(`diode`)||t.includes(`semiconductor`)?`<g class="motif"><rect x="1330" y="650" width="1180" height="700" rx="80" class="shell"/><path d="M1550 1000h310l220-180v360l-220-180h-310M2080 820v360M2080 1000h290" class="active"/><circle cx="1550" cy="1000" r="34" class="port"/><circle cx="2370" cy="1000" r="34" class="port"/></g>`:t.includes(`resistor`)||t.includes(`resistive`)?`<g class="motif"><path d="M1450 1000h180l90-150 130 300 130-300 130 300 130-300 130 300 90-150h180" class="active"/><rect x="1330" y="710" width="1180" height="580" rx="80" class="shell"/></g>`:t.includes(`capacitor`)||t.includes(`capacitive`)||t.includes(`dielectric`)?`<g class="motif"><rect x="1540" y="720" width="180" height="560" rx="25" class="active fill"/><rect x="2120" y="720" width="180" height="560" rx="25" class="active fill"/><rect x="1780" y="760" width="280" height="480" rx="35" class="dielectric"/><path d="M1380 1000h160M2300 1000h160" class="active"/></g>`:t.includes(`inductor`)||t.includes(`coil`)||t.includes(`solenoid`)||t.includes(`magnetic`)?`<g class="motif"><path d="M1370 1000h170c0-170 230-170 230 0s230 170 230 0 230-170 230 0 230 170 230 0h160" class="active"/><rect x="1500" y="690" width="850" height="620" rx="150" class="shell"/></g>`:t.includes(`rf`)||t.includes(`antenna`)||t.includes(`resonator`)?`<g class="motif"><ellipse cx="1920" cy="1000" rx="650" ry="390" class="active"/><ellipse cx="1920" cy="1000" rx="450" ry="250" class="shell"/><path d="M1920 1390v210M1920 1600h430" class="active"/><path d="M1550 1000c180-180 560-180 740 0M1610 1110c150-120 470-120 620 0" class="field"/></g>`:t.includes(`fluid`)||t.includes(`channel`)||t.includes(`valve`)||t.includes(`pump`)?`<g class="motif"><rect x="1350" y="730" width="1140" height="540" rx="160" class="shell"/><path d="M1450 1000h330c90 0 120-170 210-170s120 340 210 340 120-170 210-170h160" class="fluid"/><circle cx="1920" cy="1000" r="120" class="active"/></g>`:t.includes(`optical`)||t.includes(`photon`)||t.includes(`laser`)||t.includes(`led`)?`<g class="motif"><rect x="1400" y="800" width="1040" height="400" rx="80" class="shell"/><path d="M1470 1000c220-260 420 260 640 0s420 260 640 0" class="optical"/><path d="M1560 780l-90-170M1710 800l-20-190M2280 800l100-170" class="field"/></g>`:t.includes(`mechanical`)||t.includes(`structure`)||t.includes(`frame`)||t.includes(`lattice`)?`<g class="motif"><rect x="1390" y="720" width="1060" height="560" rx="50" class="shell"/><path d="M1390 720l1060 560M2450 720L1390 1280M1390 1000h1060M1920 720v560" class="active"/></g>`:t.includes(`energy`)||t.includes(`battery`)||t.includes(`electrochemical`)?`<g class="motif"><rect x="1460" y="720" width="920" height="560" rx="70" class="shell"/><rect x="1550" y="810" width="180" height="380" class="active fill"/><rect x="1810" y="810" width="220" height="380" class="dielectric"/><rect x="2110" y="810" width="180" height="380" class="active fill"/><path d="M2290 880h180v240h-180" class="active"/></g>`:`<g class="motif"><rect x="1390" y="720" width="1060" height="560" rx="90" class="shell"/><circle cx="1920" cy="1000" r="250" class="active"/><path d="M1390 1000h280M2170 1000h280M1920 720v180M1920 1100v180" class="field"/></g>`},jt=e=>`<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160" viewBox="0 0 3840 2160">
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
<text x="180" y="305" class="title">${k(e[`Component Archetype`]||e.ID)}</text>
<text x="180" y="380" class="sub">${k(e.ID)} · ${k(e.Domain||`UNRESOLVED DOMAIN`)} · ${k(e.Family||`UNRESOLVED FAMILY`)}</text>
<text x="3660" y="180" text-anchor="end" class="warn">SYMBOLIC 4K PLATE · NOT RELEASED GEOMETRY</text>
${At(e)}
<g transform="translate(180 540)">
  ${A(0,0,`PRIMARY FUNCTION`,e[`Primary Function`],50)}
  ${A(0,330,`BUILD CLASS / ROUTE`,`${e[`Current CGX Build Class`]||``} · ${e[`Current Manufacturing Route`]||``}`,50)}
  ${A(0,660,`BASELINE GEOMETRY`,e[`Baseline Geometry`],50)}
  ${A(0,990,`GEOMETRIC PARAMETERS`,e[`Geometric Parameters`],50)}
</g>
<g transform="translate(2720 540)">
  ${A(0,0,`PHYSICS / MODEL`,`${e[`Primary Physics`]||``} · ${e[`Baseline Model / Equation`]||``}`,47)}
  ${A(0,330,`MATERIAL STACK`,e[`Typical Material Stack`],47)}
  ${A(0,660,`INTERFACES / 4D`,`${e[`Ports / Interfaces`]||``} · ${e[`4D Fields`]||``}`,47)}
  ${A(0,990,`TEST / FAILURE`,`${e[`Acceptance Tests`]||``} · ${e[`Failure Modes`]||``}`,47)}
</g>
<rect x="180" y="1960" width="3480" height="90" rx="24" fill="#0f1b1c" stroke="#294043" stroke-width="4"/>
<text x="225" y="2018" class="mono">EVIDENCE: ${k(e[`Evidence State`]||`UNRESOLVED`)} · AUTHORITY: ${k(e[`Source Authority Class`]||`UNRESOLVED`)} · SCALE: ${k(e[`Scale Band`]||`UNRESOLVED`)}</text>
<text x="225" y="2085" class="mono">Visual form is corpus-derived symbolic topology. Exact CGXI/source/lot/geometry/process/tool/calibration/test evidence governs realization.</text>
</svg>`,Mt=e=>{let t=jt(e),n=new Blob([t],{type:`image/svg+xml`}),r=URL.createObjectURL(n);window.open(r,`_blank`,`noopener,noreferrer`)?window.setTimeout(()=>URL.revokeObjectURL(r),6e4):URL.revokeObjectURL(r)},Nt=e=>`<button type="button" class="button-secondary component-plate-trigger" data-component-id="${k(e)}">4K symbolic</button>`,Pt=(e,t)=>{let n=new Map(t.map(e=>[e.ID,e]));e.querySelectorAll(`.component-plate-trigger`).forEach(e=>{e.addEventListener(`click`,()=>{let t=n.get(e.dataset.componentId||``);t&&Mt(t)})})},j=e=>e.replace(/&/g,`&amp;`).replace(/</g,`&lt;`).replace(/>/g,`&gt;`).replace(/"/g,`&quot;`).replace(/'/g,`&#39;`),M=(e,t)=>`<div><strong>${j(String(e))}</strong><span>${j(t)}</span></div>`,Ft=e=>{let t=e.hero_render||e.render,n=[e.hero_render?`<a class="button-secondary" href="${j(e.hero_render)}" target="_blank" rel="noreferrer">4K hero</a>`:``,`<a class="button-secondary" href="${j(e.render)}" target="_blank" rel="noreferrer">Engineering plate</a>`,e.mesh_data?Dt({url:e.mesh_data,label:e.label,source:e.source,sourceHash:e.source_sha256,physicalState:e.physical_state}):``].filter(Boolean).join(``);return`
  <article class="object-review-card" data-review-object data-search="${j([e.id,e.label,e.role,e.level,e.geometry_state,e.physical_state].join(` `).toLowerCase())}">
    <a href="${j(t)}" target="_blank" rel="noreferrer">
      <img src="${j(t)}" loading="lazy" alt="${j(e.label)} source-faithful review render" />
    </a>
    <div class="object-review-copy">
      <div class="panel-head">
        <div><p class="eyebrow">${j(e.level)}</p><h3>${j(e.label)}</h3></div>
        <span class="badge">${j(e.physical_state)}</span>
      </div>
      <p>${j(e.role)}</p>
      <small class="cgx-uri">${j(e.source)}</small>
      <div class="object-review-state"><strong>${j(e.geometry_state)}</strong></div>
      ${e.render_state?`<small>${j(e.render_state)}</small>`:``}
      ${e.stats?`<small>${e.stats.vertices.toLocaleString()} vertices · ${e.stats.faces.toLocaleString()} triangles</small>`:``}
      ${e.source_sha256?`<small class="cgx-uri">source SHA-256 ${j(e.source_sha256.slice(0,24))}…</small>`:``}
      <div class="object-review-actions">${n}</div>
      <ul class="compact-list">${e.review_rules.map(e=>`<li>${j(e)}</li>`).join(``)}</ul>
    </div>
  </article>`},It=e=>`
  <div class="object-catalogue-controls">
    <input id="object-catalogue-filter" type="search" placeholder="Filter 411 components by ID, family, geometry, route, physics…" />
    <span class="badge" id="object-catalogue-count">${e.records.length} / ${e.records.length}</span>
  </div>
  <div class="table-scroll">
    <table class="graph-table object-catalogue-table">
      <thead><tr><th>ID</th><th>Component</th><th>Build / route</th><th>Geometry</th><th>4D / physics</th><th>Evidence</th></tr></thead>
      <tbody>
        ${e.records.map(e=>`<tr data-printable-row data-search="${j([e.ID,e.Domain,e.Family,e[`Component Archetype`],e[`Current CGX Build Class`],e[`Current Manufacturing Route`],e[`Baseline Geometry`],e[`Primary Physics`],e[`4D Fields`]].filter(Boolean).join(` `).toLowerCase())}">
          <td><strong>${j(e.ID)}</strong><small>${j(e.Domain||``)}</small>${Nt(e.ID)}</td>
          <td>${j(e[`Component Archetype`]||``)}<small>${j(e.Family||``)} · ${j(e[`Primary Function`]||``)}</small></td>
          <td><span class="badge">${j(e[`Current CGX Build Class`]||``)}</span><small>${j(e[`Current Manufacturing Route`]||``)}</small></td>
          <td>${j(e[`Baseline Geometry`]||``)}<small>${j(e[`Geometric Parameters`]||``)}</small></td>
          <td>${j(e[`Primary Physics`]||``)}<small>${j(e[`4D Fields`]||``)}</small></td>
          <td>${j(e[`Evidence State`]||``)}<small>${j(e[`Source Authority Class`]||``)}</small></td>
        </tr>`).join(``)}
      </tbody>
    </table>
  </div>`,Lt=(e,t)=>`
  <article class="panel object-review-panel">
    <div class="panel-head">
      <div><p class="eyebrow">CGX object review catalogue</p><h2>Component → stack → Luke / Mark / InterSol</h2></div>
      <span class="badge">${j(e.status)}</span>
    </div>
    <p class="muted">${j(e.authority)}</p>
    <div class="graph-summary">
      ${M(e.coverage.printable_4d_archetypes,`component archetypes`)}
      ${M(e.coverage.symbolic_core_component_stack_plates,`CGX symbolic plates`)}
      ${M(e.coverage.source_mesh_4k_hero_views??e.coverage.macro_source_meshes,`4K source-mesh heroes`)}
      ${M(e.coverage.source_mesh_interactive_views??e.coverage.macro_source_meshes,`interactive source meshes`)}
      ${M(e.coverage.symbolic_system_lineage_plates??0,`system lineage plates`)}
      ${M(e.coverage.physical_tests_complete,`physical tests complete`)}
    </div>
    <div class="flow">${e.tiers.map(e=>`<span title="${j(e.description)}">${j(e.id)} · ${j(e.label)}</span>`).join(`<i>→</i>`)}</div>
    <div class="boundary"><strong>Visual rule</strong><span>${j(e.visual_system.rule)}</span></div>

    <div class="cgx-lens-tabs object-review-tabs" role="tablist" aria-label="Object review catalogue">
      <button class="active" type="button" data-object-review-tab="gallery">Review plates</button>
      <button type="button" data-object-review-tab="catalogue">411 component catalogue</button>
      <button type="button" data-object-review-tab="frontier">Current frontier</button>
    </div>

    <section data-object-review-panel="gallery">
      <div class="object-review-search"><input id="object-review-filter" type="search" placeholder="Filter review plates…" /></div>
      <h3>CGX-derived component / stack plates</h3>
      <div class="object-review-grid">${e.micro_review_objects.map(Ft).join(``)}</div>
      <h3>System lineage / bridge plates</h3>
      <div class="object-review-grid">${(e.bridge_review_objects||[]).map(Ft).join(``)}</div>
      <h3>Corpus source meshes</h3>
      <div class="object-review-grid">${e.macro_review_objects.map(Ft).join(``)}</div>
    </section>

    <section data-object-review-panel="catalogue" hidden>
      <div class="boundary"><strong>${j(t.schema)}</strong><span>Canonical component atlas exposed as a read-only UniSpace projection. Printable-4D packet, topology and invariant semantics remain in the adjacent CGX lens rather than being duplicated here.</span></div>
      ${It(t)}
    </section>

    <section data-object-review-panel="frontier" hidden>
      <div class="stack-list">
        ${e.pending_owner_layers.map(e=>`<article class="task-card"><div><strong>Current owner frontier</strong><small>${j(e)}</small></div></article>`).join(``)}
      </div>
      <div class="boundary"><strong>Evidence boundary</strong><span>${j(e.boundary)}</span></div>
    </section>
  </article>`,Rt=(e,t)=>{let n=[...e.querySelectorAll(`[data-object-review-tab]`)],r=[...e.querySelectorAll(`[data-object-review-panel]`)],i=e=>{n.forEach(t=>t.classList.toggle(`active`,t.dataset.objectReviewTab===e)),r.forEach(t=>t.hidden=t.dataset.objectReviewPanel!==e)};n.forEach(e=>e.addEventListener(`click`,()=>i(e.dataset.objectReviewTab||`gallery`))),i(`gallery`);let a=e.querySelector(`#object-review-filter`),o=[...e.querySelectorAll(`[data-review-object]`)];a?.addEventListener(`input`,()=>{let e=(a.value||``).trim().toLowerCase();o.forEach(t=>t.hidden=!!e&&!(t.dataset.search||``).includes(e))});let s=e.querySelector(`#object-catalogue-filter`),c=[...e.querySelectorAll(`[data-printable-row]`)],l=e.querySelector(`#object-catalogue-count`);s?.addEventListener(`input`,()=>{let e=(s.value||``).trim().toLowerCase(),t=0;c.forEach(n=>{let r=!e||(n.dataset.search||``).includes(e);n.hidden=!r,r&&(t+=1)}),l&&(l.textContent=`${t} / ${c.length}`)}),Ot(e),Pt(e,t.records)},zt=async(e,t)=>{let[n,r]=await Promise.all([e(),t()]);return{manifest:n,atlas:r,html:Lt(n,r)}},Bt=[[`LightSpeed Git`,`https://github.com/achillesromer-coder/LightSpeed`,`Versioned implementation and receipts`],[`Type 1 Digital Review`,`https://github.com/achillesromer-coder/LightSpeed/pull/46`,`Draft 3D, six-view and T1-00..07 review packages`],[`Type 1 Römer Canon`,`https://docs.google.com/spreadsheets/d/1refNFmebTcmPVojCuZsyILJEWaKz-sVzYLfZtqMl8k8/edit`,`Living programme, evidence, handoff and release gates`],[`ACR3 Handoffs`,`https://docs.google.com/spreadsheets/d/1AgAhLPNtrO91C_-ea7EdOkOsyXrCCYvFVvmDSGq8uls/edit`,`Append-only cross-corpus reconciliation receipts`],[`LS GO Queue`,`https://docs.google.com/spreadsheets/d/1f5i4V3FshYHkztv3_HAg0ZofUl0sdcJZcwrlesUlCfM/edit`,`Phone tasks, approvals, commands, results and sync health`],[`Portfolio Handoff`,`https://docs.google.com/document/d/1tsDkb79UVX_SqS2-oBgc5DHb89QIlH3DcmKMN77hdOo/edit`,`Cross-chat portfolio continuity`],[`Römer Industries`,`https://romer.industries`,`Reviewed public portfolio surface`]],Vt=[{name:`Central Facility Boundary`,radiusM:2500,description:`All facilities and buildings remain inside this radius.`},{name:`Active Eco-Restoration`,radiusM:3500,description:`1 km active band for managed biome, native rehabilitation, and functional climate pockets.`},{name:`Passive Eco-Restoration`,radiusM:11e3,description:`Outer passive restoration reserve securing the full radial print.`}],Ht=[{id:`integration-hall`,name:`Integration Hall`,footprint:`40 m x 75 m, 22 m clear`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Starship-compatible roller doors both ends; single bridge crane spans the hall.`},{id:`chainhill`,name:`ChainHill Relay`,footprint:`~225-250 m relay length`,elevation:`flat raised concrete, approximately 3 m above water table`,releaseStatus:`bounded-assumption`,notes:`Incoming and outgoing tracks oppose each other with two anti-parallel internal lines.`},{id:`x-pads`,name:`X-Layout Pads`,footprint:`solid pads, no beveled building base`,elevation:`pad-specific hardstand`,releaseStatus:`canonical`,notes:`Flame/exhaust outlets orient away from central node and buildings.`},{id:`mission-control`,name:`Mission Control / ATC`,footprint:`pentagon base, level 1 at 80%, four-storey tower`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`canonical`,notes:`Foyer, cafeteria, meeting, offices, emergency access, elevator, and top operating floor.`},{id:`living-rd`,name:`R&D + Living Quarters`,footprint:`room-level workbook detail pending`,elevation:`+1.5 m floor, +8% beveled foundation`,releaseStatus:`known-unknown`,notes:`FIFO and FIFO+family support with ground community and rooftop lifestyle zones.`}],Ut=[`site_zones`,`facilities`,`rooms_spaces`,`roads_tracks`,`pads_exhaust`,`eco_restoration`,`standards_evidence`,`viewer_toggles`,`known_unknowns`],Wt=`modulepreload`,Gt=function(e){return`/`+e},Kt={},qt=function(e){return e.pathname.endsWith(`.css`)},Jt=function(e,t,n){if(t in e)return e[t];let r=n();if(!r){e[t]=void 0;return}let i=r.then(()=>{e[t]=void 0},n=>{throw e[t]=void 0,n});return e[t]=i,i},Yt=function(e,t,n){let r=Promise.resolve();if(t&&t.length>0){let e,i=document.querySelector(`meta[property=csp-nonce]`),a=i?.nonce||i?.getAttribute(`nonce`);function o(e){return Promise.all(e.map(e=>Promise.resolve(e).then(e=>({status:`fulfilled`,value:e}),e=>({status:`rejected`,reason:e}))))}function s(e){return import.meta.resolve?new URL(import.meta.resolve(e)):new URL(e,import.meta.url)}r=o(t.map(t=>{t=Gt(t,n);let r=s(t),i=qt(r);return Jt(Kt,r.href,()=>{if(e===void 0){e={all:new Set,styles:new Set};let t=document.getElementsByTagName(`link`);for(let n=t.length-1;n>=0;n--){let r=t[n];e.all.add(r.href),r.rel===`stylesheet`&&e.styles.add(r.href)}}if((i?e.styles:e.all).has(r.href))return;let t=document.createElement(`link`);if(t.rel=i?`stylesheet`:Wt,i||(t.as=`script`),t.crossOrigin=``,t.href=r.href,a&&t.setAttribute(`nonce`,a),document.head.appendChild(t),i)return new Promise((e,n)=>{let i=a=>{t.removeEventListener(`load`,i),t.removeEventListener(`error`,i),a.type===`error`?n(Error(`Unable to preload CSS for ${r}`)):e(a)};t.addEventListener(`load`,i),t.addEventListener(`error`,i)})})}).filter(e=>e!==void 0))}function i(e){let t=new Event(`vite:preloadError`,{cancelable:!0});if(t.payload=e,window.dispatchEvent(t),!t.defaultPrevented)throw e}return r.then(t=>{for(let e of t||[])e.status===`rejected`&&i(e.reason);return e().catch(i)})},Xt=document.getElementById(`app`);if(!Xt)throw Error(`UniSpace mount node #app not found.`);Xt.innerHTML=`
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
        <article class="panel"><p class="eyebrow">Existing twin context</p><h2>Spaceport contract retained</h2><p class="muted">${Vt.length} zones · ${Ht.length} facility records · ${Ut.length} workbook tabs. The twin remains bounded context, not the command-centre homepage.</p></article>
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
      <div class="source-grid">${Bt.map(([e,t,n])=>`<a class="source-card" href="${t}" target="_blank" rel="noreferrer"><strong>${e}</strong><span>${n}</span><em>Open ↗</em></a>`).join(``)}</div>
      <article class="panel"><p class="eyebrow">Authority order</p><h2>Where each truth lives</h2><div class="authority-grid"><div><strong>Drive</strong><span>evidence, workbooks and review receipts</span></div><div><strong>Git</strong><span>code, schemas, tests and implementation receipts</span></div><div><strong>Desktop</strong><span>projects, local execution, state and jobs</span></div><div><strong>UniSpace</strong><span>owner commands, review and bounded decisions</span></div></div></article>
    </section>
  </main>
`;var N=e=>{let t=document.getElementById(e);if(!t)throw Error(`Missing #${e}`);return t},Zt=N(`instruction`),Qt=N(`target-floor`),$t=N(`priority`),en=N(`execution-mode`),tn=N(`route-preview`),nn=N(`command-result`),P=null,rn=null,an=[],on=[],F=``,sn=0,I=0,cn=()=>{sn++,I++,document.querySelectorAll(`.result-receipt-detail, .project-file-result`).forEach(e=>{e.textContent=``})},ln=``,L=`NCNB`,R=(e,t)=>{let n=N(`owner-auth-result`);n.dataset.tone=e,n.textContent=t},un=e=>{let t=N(`owner-login-form`),n=N(`owner-change-form`),r=N(`owner-logout`);L=e.credential?.username||L,cn(),F=e.session_token||``,ln=e.password_change_token||``,N(`owner-password`).value=``,e.authenticated&&F?(n.hidden=!0,r.hidden=!1,N(`owner-auth-state`).textContent=`${L} signed in`,R(`good`,`Owner session active until ${e.expires_utc||`page close`}.`)):(r.hidden=!0,n.hidden=!e.change_required,t.hidden=!1,N(`owner-auth-state`).textContent=e.change_required?`Password change required`:`Sign-in required`,R(`warn`,e.change_required?`The bootstrap password was verified. Enter it again with a new password to complete first login.`:`Owner sign-in is required for unredacted files, receipts, and decisions.`))},z=()=>F||(R(`warn`,`Sign in as NCNB before performing this owner-gated action.`),``);N(`owner-login-form`).addEventListener(`submit`,async e=>{e.preventDefault();let t=N(`owner-username`).value.trim(),n=N(`owner-password`);try{un(await f(t,n.value)),F&&U()}catch(e){n.value=``,R(`bad`,e instanceof Error?e.message:`Owner sign-in failed.`)}}),N(`owner-change-form`).addEventListener(`submit`,async e=>{e.preventDefault();let t=N(`owner-current-password`),n=N(`owner-new-password`),r=N(`owner-confirm-password`);if(n.value!==r.value){R(`bad`,`The new passwords do not match.`);return}let i=ln||F;if(!i)R(`bad`,`Sign in before changing the password.`);else try{let e=await p(L,t.value,n.value,i,!!ln);t.value=``,n.value=``,r.value=``,un(e)}catch(e){t.value=``,n.value=``,r.value=``,R(`bad`,e instanceof Error?e.message:`Password change failed.`)}}),N(`owner-logout`).addEventListener(`click`,async()=>{let e=F;if(F=``,cn(),ln=``,e)try{await m(e)}catch{}N(`owner-logout`).hidden=!0,N(`owner-auth-state`).textContent=`Signed out`,R(`warn`,`Owner session cleared from this page.`),N(`cgx-capability-surface`).textContent=`Owner session cleared; capability projection hidden.`});var B=(e,t,n)=>{let r=N(e);r.dataset.tone=t,r.textContent=n};N(`node-transfer-form`).addEventListener(`submit`,async e=>{e.preventDefault();let t=z();if(!t){B(`node-transfer-result`,`warn`,`Owner sign-in is required to plan private transfer.`);return}let n=Number(N(`node-transfer-bytes`).value);try{let e=await h({source_ref:N(`node-transfer-source-ref`).value.trim(),source_sha256:N(`node-transfer-sha`).value.trim(),size_bytes:n,file_name:N(`node-transfer-file`).value.trim(),source_node_id:N(`node-transfer-source-node`).value.trim(),target_node_id:N(`node-transfer-target-node`).value.trim(),source_root_id:N(`node-transfer-source-root`).value.trim(),target_root_id:N(`node-transfer-target-root`).value.trim()},t);B(`node-transfer-result`,`good`,`${String(e.plan?.transfer_id||`planned`)} planned. DIGITAL_WRITE lease required; no bytes moved and no authority transferred.`)}catch(e){B(`node-transfer-result`,`bad`,e instanceof Error?e.message:`Transfer plan failed.`)}}),N(`node-compute-form`).addEventListener(`submit`,async e=>{e.preventDefault();let t=z();if(!t)B(`node-compute-result`,`warn`,`Owner sign-in is required to plan private compute.`);else try{let e=await g({instruction:N(`node-compute-instruction`).value.trim(),task_id:N(`node-compute-task`).value.trim(),run_id:N(`node-compute-run`).value.trim(),target_node_id:N(`node-compute-target`).value.trim(),capability_id:N(`node-compute-capability`).value.trim(),lease_ref:N(`node-compute-lease`).value.trim(),input_receipts:[],resource_budget:{allow_heavy:!1}},t);B(`node-compute-result`,`good`,`${String(e.request?.request_id||`planned`)} planned. COMPUTE_ONLY lease must validate before the existing runtime executes anything.`)}catch(e){B(`node-compute-result`,`bad`,e instanceof Error?e.message:`Compute plan failed.`)}});var dn=()=>{let e=s(Zt.value||`governance`);Qt.value=e;let t=rn?.canonical_gate_id;tn.innerHTML=`<strong>Achilles route:</strong> ${e} is primary. Neo coordinates and proof returns to this gate.${t?` <small>Authority: ${b(t)}</small>`:` <small>Waiting for the Desktop authority contract.</small>`}`};Zt.addEventListener(`input`,dn),dn();var fn=()=>c({instruction:Zt.value,targetFloor:Qt.value,priority:$t.value,executionMode:en.value,authorityContract:rn}),V=(e,t)=>{nn.dataset.tone=e,nn.textContent=t},H=()=>{let e=ve();N(`pending-count`).textContent=String(e.length);let t=N(`pending-commands`);e.length?(t.innerHTML=e.map(e=>`<article class="task-card"><div><strong>${b(e.title)}</strong><span>${b(e.target_floor)} · ${b(e.priority)} · ${b(e.execution_mode)}</span><small>${b(e.command_id)}</small></div><div class="task-actions"><button data-send="${b(e.command_id)}">Send</button><button data-download="${b(e.command_id)}">Download</button></div></article>`).join(``),t.querySelectorAll(`[data-send]`).forEach(t=>t.addEventListener(`click`,async()=>{let n=e.find(e=>e.command_id===t.dataset.send);if(n)try{let e=await _(n);be(n.command_id),H(),V(`good`,`Desktop accepted ${e.command_id||n.command_id}. Task ${e.task_id??`created`}.`),await U()}catch(e){V(`bad`,e instanceof Error?e.message:`Desktop command failed.`)}})),t.querySelectorAll(`[data-download]`).forEach(t=>t.addEventListener(`click`,()=>{let n=e.find(e=>e.command_id===t.dataset.download);n&&xe(n)}))):t.innerHTML=`<p class="muted">No locally saved commands.</p>`},pn=e=>{I++;let t=N(`desktop-projects`);N(`project-count`).textContent=String(e.length),t.innerHTML=ze(e),Ue(t,async(e,t)=>{let n=t.closest(`[data-project-card]`)?.querySelector(`.project-files`);if(n){if(t.getAttribute(`aria-expanded`)===`true`){t.setAttribute(`aria-expanded`,`false`),t.textContent=`Files`,I++;let e=n.querySelector(`.project-file-result`);e&&(e.textContent=``),n.hidden=!0}else{t.disabled=!0,t.textContent=`Loading…`,n.hidden=!1,n.innerHTML=`<p class="muted">Reading bounded project metadata…</p>`;try{let r=await ne(e);n.innerHTML=Be(r),We(n,async(e,t,i)=>{let a=n.querySelector(`.project-file-result`);if(!a)return;let o=++I,s=z();if(!s)a.innerHTML=Ve(`File preview held: sign in through the NCNB owner gate first.`);else{i.disabled=!0,a.innerHTML=`<p class="muted">Opening read-only result…</p>`;try{let n=r.files.find(e=>e.relative_path===t);if(e!==r.project.project_id||!n?.metadata_revision||!/^[a-f0-9]{64}$/.test(n.metadata_revision))throw Error(`File revision unavailable; refresh the list.`);let i=await re(e,t,s,void 0,n.metadata_revision);if(o!==I||s!==F||!a.isConnected)return;if(i.project.project_id!==e||i.file.relative_path!==t||i.file.metadata_revision!==n.metadata_revision)throw Error(`File identity or metadata revision changed; refresh the list.`);a.innerHTML=He(i)}catch(e){if(o!==I||s!==F||!a.isConnected)return;a.innerHTML=Ve(e instanceof Error?e.message:`Project file result is unavailable.`)}finally{i.disabled=!1}}}),t.setAttribute(`aria-expanded`,`true`),t.textContent=`Hide files`}catch(e){n.innerHTML=Ve(e instanceof Error?e.message:`Project files are unavailable.`),t.textContent=`Retry files`}finally{t.disabled=!1}}}})},mn=(e,t)=>{cn();let n=N(`desktop-results`),r=N(`result-auth-state`);r.textContent=t?`Owner gate configured`:`Content gate held`,n.innerHTML=qe(e,t),Ye(n,async(r,i)=>{let a=n.querySelector(`.result-receipt-detail`);if(!a)return;let o=++sn;if(!t){a.innerHTML=x(`Receipt content is held because owner confirmation is not configured on the local bridge.`);return}let s=z();if(!s)a.innerHTML=x(`Receipt inspection held: sign in through the NCNB owner gate first.`);else{i.disabled=!0,a.innerHTML=`<p class="muted">Opening owner-confirmed read-only receipt…</p>`;try{let t=e.results.find(e=>e.result_id===r);if(!t||!/^[a-f0-9]{64}$/.test(t.sha256))throw Error(`Exact receipt revision unavailable; refresh the list.`);let n=await oe(r,s,void 0,t.sha256);if(o!==sn||s!==F||!a.isConnected)return;if(n.identity.result_id!==r||n.identity.sha256!==t.sha256)throw Error(`Receipt identity or revision changed; refresh the list.`);a.innerHTML=Je(n)}catch(e){if(o!==sn||s!==F||!a.isConnected)return;a.innerHTML=x(e instanceof Error?e.message:`Local result receipt is unavailable.`)}finally{i.disabled=!1}}})},hn=e=>{an=e;let t=N(`desktop-reviews`);e.length?(t.innerHTML=e.slice(0,30).map(e=>{let t=e.state||`pending_review`,n=t===`pending_review`?`<div class="task-actions"><button data-review="${b(e.review_id)}" data-decision="approve">Approve</button><button data-review="${b(e.review_id)}" data-decision="hold">Hold</button><button data-review="${b(e.review_id)}" data-decision="reject">Reject</button></div>`:``;return`<article class="task-card"><div><strong>${b(e.title||`Project receipt`)}</strong><span>${b(t)} · ${b(e.event_type||`receipt`)}</span><small>${b(e.summary||e.review_id)}</small></div>${n}</article>`}).join(``),t.querySelectorAll(`[data-review]`).forEach(e=>e.addEventListener(`click`,async()=>{let t=e.dataset.review||``,n=e.dataset.decision,r=an.find(e=>e.review_id===t);if(!r||!t)return;let i=window.prompt(`${n.toUpperCase()}: ${r.title||t}\nOptional decision note:`,``)??``,a=z();if(!a)V(`bad`,`Review decision held: sign in through the NCNB owner gate first.`);else try{V(`good`,me(t,n,await ce(t,n,i,a))),await U()}catch(e){V(`bad`,e instanceof Error?e.message:`Review decision failed.`)}}))):t.innerHTML=`<p class="muted">No project receipts are awaiting review.</p>`},gn=e=>{on=e;let t=N(`representation-graphs`);t.innerHTML=tt(e),t.querySelectorAll(`[data-representation-review]`).forEach(e=>{e.addEventListener(`click`,async()=>{let t=e.dataset.representationReview||``,n=e.dataset.decision,r=e.dataset.scope||`identity`,i=r===`edges`?(e.dataset.edgeIds||``).split(`|`).filter(Boolean).slice(0,100):[],a=on.find(e=>e.review?.review_id===t);if(!t||!a)return;let o=window.prompt(`${n.replace(/_/g,` `).toUpperCase()}: ${a.object.display_name}\n${r===`identity`?`Identity is reviewed before edges.`:`${i.length} bounded edges selected.`}\nOptional decision note:`,``)??``,s=z();if(!s)V(`bad`,`Representation decision held: sign in through the NCNB owner gate first.`);else try{await ge(t,n,r,i,o,s),V(`good`,`${t} recorded ${n}; local staging remains noncanonical until Drive readback.`),await U()}catch(e){V(`bad`,e instanceof Error?e.message:`Representation review decision failed.`)}})})};N(`command-form`).addEventListener(`submit`,async e=>{e.preventDefault(),P=null;try{P=fn(),V(`warn`,`Sending ${P.command_id} to Desktop…`);let e=await _(P);be(P.command_id),H(),V(`good`,`Accepted by Desktop. Task ${e.task_id??`created`}; ${e.state||`queued for governed processing`}.`),await U()}catch(e){let t=e instanceof l;P&&!t&&ye(P),H();let n=e instanceof Error?e.message:`Desktop unavailable`;V(`bad`,t?`${n} Desktop rejected the command; it was not mislabeled as an offline save.`:`${n}${P?` The command envelope was saved locally.`:``}`)}}),N(`save-command`).addEventListener(`click`,()=>{try{P=fn(),ye(P),H(),V(`good`,`${P.command_id} saved locally.`)}catch(e){V(`bad`,e instanceof Error?e.message:`Command could not be saved.`)}}),N(`copy-command`).addEventListener(`click`,async()=>{try{P=fn(),await navigator.clipboard.writeText(JSON.stringify(P,null,2)),V(`good`,`${P.command_id} copied as JSON.`)}catch(e){V(`bad`,e instanceof Error?e.message:`Command could not be copied.`)}});var U=async()=>{let e=N(`desktop-pill`),t=N(`desktop-state`),n=N(`merovingian-state`),r=N(`remote-access-state`),o=N(`remote-access-detail`),s=N(`desktop-pill-text`),c=N(`desktop-tasks`);e.dataset.state=`checking`,s.textContent=`checking local runtime`,t.textContent=`Checking`,n.textContent=`Checking`,r.textContent=`Checking`,o.textContent=`private relay gate`;try{let l=await d();rn=l.authority_contract||null,L=l.auth?.username||L,N(`owner-username`).value=L,F||(N(`owner-auth-state`).textContent=l.auth?.configured?l.auth.must_change?`First change required`:`Sign-in required`:`Credential setup held`,l.auth?.configured?l.auth.must_change&&R(`warn`,`Sign in with the bootstrap password, then complete the required change.`):R(`bad`,`The dedicated owner credential is not configured on Desktop.`)),dn(),e.dataset.state=l.ok?`online`:`degraded`,s.textContent=l.ok?`local runtime connected`:`runtime connected; health needs review`,t.textContent=`Online`,n.textContent=l.merovingian?.status===`pass`?`Healthy`:`Degraded`;let u=i(l.remote_access);r.textContent=u.label,o.textContent=u.detail;let f=l.test_cascade;N(`cascade-mode`).textContent=f?.mode===`corpus_bound`?`Corpus-bound planning`:`Cascade unavailable`,N(`cascade-activation`).textContent=f?.activation_state===`active`?`Active`:f?.activation_state===`held`?`Held`:`Prepared · activation gated`,N(`cascade-boundary`).textContent=f?.dependency_gate?`Results unknown until execution · downstream gate: ${f.dependency_gate}.`:`Corpus inputs and dependency receipts remain required before governed execution.`;let p=l.node_exchange,m=a(p);N(`node-exchange-node`).textContent=p?.node_id?`Node ${p.node_id}`:`Node identity unavailable`,N(`node-exchange-transfer`).textContent=m.transfer,N(`node-exchange-compute`).textContent=m.compute,N(`node-exchange-boundary`).textContent=m.boundary,N(`node-exchange-peer`).textContent=p?.compute?.peer_compute_verified?`Peer compute verified`:p?.activation?.host_root_registry_ready?`Local root registry ready`:`Root registry pending`,p?.node_id&&(N(`node-transfer-source-node`).value=p.node_id,N(`node-compute-target`).value=p.node_id);let h=N(`cgx-capability-surface`);if(F){let e=F;try{let t=await le(e);if(e===F){let n=t.roles.map(e=>`<span class="badge">${b(e.floor)}</span>`).join(` `),r=t.routes.map(e=>`<span class="badge" title="${b(e.gate)}">${b(e.id)} · ${b(e.state)}</span>`).join(` `);h.innerHTML=`<p class="eyebrow">Backend-derived CGX capabilities</p><h2>${t.route_count} scoped routes · review-only</h2><p class="muted">Revision ${b(t.source_view_sha256.slice(0,12))} · no execution or mint authorization inferred.</p><div class="flow">${n}</div><details><summary>Registered capability catalogue</summary><div class="flow" style="flex-wrap:wrap">${r}</div></details>`,Le(h,t,e,()=>e===F);try{let t=await ue(e);if(e===F&&h.isConnected){let e=document.createElement(`details`),n=t.selectors.map(e=>`<li><strong>`+b(e.selector)+`</strong> · `+e.available_routes+` available / `+e.gated_routes+` gated · native admission pending</li>`).join(``),r=t.content_groups.map(e=>`<li><strong>`+b(e.display_name)+`</strong> · `+e.bytes+` bytes · `+b(e.sha256.slice(0,12))+(e.reference_names.length>1?` · same-byte names: `+e.reference_names.map(b).join(` ≡ `):``)+` · observation only, not native object admission</li>`).join(``),i=t.retained_empty_carrier_names.length;e.innerHTML=`<summary>CGX family · `+t.selector_count+` registered selectors</summary><p class="muted">`+t.installed_carrier_count+` observed .cgx filenames consolidated into `+t.content_groups.length+` content groups (`+t.collapsed_alias_card_count+` duplicate display card(s) suppressed). Identical bytes do not prove semantic identity or native mint.</p><ul>`+n+`</ul><details><summary>One content card per unique hash</summary><ul>`+r+`</ul></details><p class="muted">Storage namespace `+(t.storage_root_is_alias?`resolves through an existing alias/junction`:`is a direct root`)+`. Zero-byte carrier holds: `+i+`. Deleted: `+(t.deletion_performed?`yes`:`no`)+`. No carrier aliases are deletion-authorised by this presentation.</p>`,h.appendChild(e)}}catch{if(e===F&&h.isConnected){let e=document.createElement(`p`);e.className=`muted`,e.textContent=`Family topology pending deployment or source admission.`,h.appendChild(e)}}}}catch{h.textContent=`CGX capability projection unavailable; registry or owner session held.`}}else h.textContent=`Sign in as owner to hydrate the read-only CGX capability projection.`;try{let e=await v();c.innerHTML=e.length?e.map(e=>`<article class="task-card"><div><strong>${b(String(e.title||`Untitled task`))}</strong><span>${b(String(e.status||`unknown`))} · ${b(String(e.priority||`normal`))}</span><small>Task ${b(String(e.id||``))}</small></div></article>`).join(``):`<p class="muted">Desktop queue is clear.</p>`}catch{c.innerHTML=`<p class="muted">Desktop is online, but task listing is unavailable.</p>`}try{pn((await ee()).projects)}catch{pn([])}try{hn(await se())}catch{hn([])}try{mn(await ae(),l.auth?.configured===!0)}catch(e){N(`result-auth-state`).textContent=l.auth?.configured===!0?`Owner gate configured`:`Content gate held`,N(`desktop-results`).innerHTML=x(e instanceof Error?e.message:`Local result metadata is unavailable.`)}try{gn(await he())}catch(e){on=[];let t=l.representation_edge?.enabled===!1?`Canonical representation objects are intentionally disabled by the current launch gate.`:e instanceof Error?e.message:`Representation objects are unavailable.`;N(`representation-graphs`).innerHTML=`<article class="panel"><p class="eyebrow">Objects unavailable</p><h2>Feature-gated, not empty</h2><p class="muted">${b(t)}</p></article>`}}catch{rn=null,dn(),e.dataset.state=`offline`,s.textContent=`start LightSpeed Desktop and the local bridge`,t.textContent=`Offline`,n.textContent=`Offline`,r.textContent=`Unavailable`,o.textContent=`Desktop bridge is offline.`,N(`cascade-mode`).textContent=`Desktop offline`,N(`cascade-activation`).textContent=`Unavailable`,N(`cascade-boundary`).textContent=`Start the local Desktop bridge to read the corpus-cascade contract.`,N(`node-exchange-node`).textContent=`Node exchange unavailable`,N(`node-exchange-peer`).textContent=`Peer state unknown`,N(`node-exchange-transfer`).textContent=`Desktop bridge is offline.`,N(`node-exchange-compute`).textContent=`Desktop bridge is offline.`,N(`node-exchange-boundary`).textContent=`Start the local Desktop bridge before planning transfer or compute.`,N(`cgx-capability-surface`).textContent=`Desktop offline; CGX capability projection unavailable.`,N(`project-count`).textContent=`0`,c.innerHTML=`<p class="muted">Desktop is offline. Commands can still be saved, copied or downloaded.</p>`,N(`desktop-projects`).innerHTML=`<p class="muted">Project registry unavailable while Desktop is offline.</p>`,N(`desktop-reviews`).innerHTML=`<p class="muted">Review queue unavailable while Desktop is offline.</p>`,N(`owner-auth-state`).textContent=`Desktop offline`,R(`bad`,`Start the local Desktop bridge before signing in.`),N(`result-auth-state`).textContent=`Desktop offline`,N(`desktop-results`).innerHTML=`<p class="muted">Fixed local result metadata is unavailable while Desktop is offline.</p>`,gn([])}};N(`refresh-desktop`).addEventListener(`click`,()=>void U()),H(),U();var _n=N(`object-review-catalogue`),vn=new URL(`./data/cgx_object_review_catalogue.json`,document.baseURI).toString(),yn=new URL(`./data/component_geometry_atlas_public_review.json`,document.baseURI).toString();zt(async()=>{let e=await fetch(vn,{cache:`no-store`});if(!e.ok)throw Error(`Object review catalogue returned HTTP ${e.status}`);return await e.json()},async()=>{let e=await fetch(yn,{cache:`no-store`});if(!e.ok)throw Error(`Component atlas review projection returned HTTP ${e.status}`);return await e.json()}).then(({html:e,atlas:t})=>{_n.innerHTML=e,Rt(_n,t)}).catch(e=>{_n.innerHTML=`<article class="panel"><p class="eyebrow">CGX object review</p><h2>Catalogue unavailable</h2><p class="muted">${b(e instanceof Error?e.message:`CGX object review catalogue unavailable.`)}</p></article>`});var bn=N(`cgx-review-lens`),xn=new URL(`./data/cgx_internal_review_projection.json`,document.baseURI).toString();pt(async()=>{let e=await fetch(xn,{cache:`no-store`});if(!e.ok)throw Error(`CGX review projection returned HTTP ${e.status}`);return await e.json()}).then(({html:e})=>{bn.innerHTML=e,ft(bn)}).catch(e=>{bn.innerHTML=`<article class="panel"><p class="eyebrow">.cgx review lens</p><h2>Projection unavailable</h2><p class="muted">${b(e instanceof Error?e.message:`CGX review projection unavailable.`)}</p></article>`});var Sn=N(`type1-catalogue-projection`),Cn=new URL(`./data/type1_catalogue_projection.json`,document.baseURI).toString();rt(async()=>{let e=await fetch(Cn,{cache:`no-store`});if(!e.ok)throw Error(`Type-I catalogue projection returned HTTP ${e.status}`);return await e.json()}).then(e=>{Sn.innerHTML=e}).catch(e=>{Sn.innerHTML=`<article class="panel"><p class="eyebrow">Type-I PrintSpace</p><h2>Projection unavailable</h2><p class="muted">${b(e instanceof Error?e.message:`Type-I catalogue projection unavailable.`)}</p></article>`});var wn=N(`neo-exchange`),Tn=new URL(`./data/neo_exchange.json`,document.baseURI).toString();Ne(async()=>{let e=await fetch(Tn,{cache:`no-store`});if(!e.ok)throw Error(`Neo exchange returned HTTP ${e.status}`);return e.json()}).then(e=>{wn.innerHTML=Fe(e)});var En=e=>{let t=Array.from(document.querySelectorAll(`.tab`)).find(t=>t.dataset.view===e)?.dataset.view||`command`;if(t===`filespace`){let e=document.querySelector(`#filespace-reader`);e.srcdoc||Yt(async()=>{let{readerDocument:e}=await import(`./filespaceReader-ynzKLNaM.js`);return{readerDocument:e}},[]).then(({readerDocument:t})=>{e.srcdoc||=t()}).catch(()=>{document.querySelector(`#filespace-load`).textContent=`The FileSpace reader could not load. Reopen this view to retry.`})}document.querySelectorAll(`.tab`).forEach(e=>e.classList.remove(`active`)),document.querySelectorAll(`.view`).forEach(e=>e.classList.remove(`active`)),document.querySelector(`.tab[data-view="${t}"]`)?.classList.add(`active`),N(`view-${t}`).classList.add(`active`)};document.querySelectorAll(`.tab`).forEach(e=>e.addEventListener(`click`,()=>{let t=e.dataset.view||`command`;En(t);let n=t===`command`?``:`#${t}`;window.location.hash!==n&&window.history.replaceState(null,``,n||window.location.pathname+window.location.search)})),window.addEventListener(`hashchange`,()=>En(window.location.hash.replace(/^#/,``)||`command`)),En(window.location.hash.replace(/^#/,``)||`command`);var Dn=`CGX-LSGO-SITE-INTEGRATION-PRESENTATION/0.1`,On=96,kn=Object.freeze([`Owner review`,`Achilles / GO gate`,`Existing LightSpeed runtime`,`Git source review`,`Drive provenance review`]),An=Object.freeze([`owner_credential_ready`,`private_relay_configured`,`off_device_verified`,`accepted_head_installed`,`drive_successor_readback`,`public_deployment_verified`,`public_direct_execution`]),jn=e=>typeof e==`object`&&!!e&&!Array.isArray(e),Mn=e=>typeof e!=`string`||e.length<1||e.length>On||/[\u0000-\u001f\u007f]/.test(e)?null:e.trim()||null,Nn=e=>e.replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#39;`})[e]??e),Pn=e=>{let t=jn(e)&&e.schema_version===`lightspeed-go-sites-integration-v2`&&e.site_name===`LightSpeed GO`&&e.edit_mode===`existing-site-side-edit`&&e.create_new_site===!1&&e.publish_state===`review_source_verified_deployment_held`&&e.source_commit===null&&jn(e.release_gates)&&An.every(t=>e.release_gates&&jn(e.release_gates)&&e.release_gates[t]===!1)&&Array.isArray(e.authority_chain)&&e.authority_chain.length>=1&&e.authority_chain.length<=8&&e.authority_chain.every(e=>Mn(e)!==null),n=t?Object.freeze(e.authority_chain.map(e=>Mn(e))):kn;return Object.freeze({schema:Dn,sourceStatus:t?`Source review only · exact current Git and Drive readback pending`:`Unqualified site manifest · source review required`,launchStatus:`Public deployment, native acceptance and DBR proof held`,authority:n,manifestEvidence:t?`REVIEW_SOURCE_ONLY`:`INVALID_SOURCE_HELD`,nativeVerified:!1,publicDeployed:!1,dbrVerified:!1})},Fn=new URL(`./data/site_integration.json`,document.baseURI).toString(),In=async()=>{try{let e=await fetch(Fn,{cache:`no-store`});return e.ok?await e.json():null}catch{return null}},Ln=()=>{if(document.getElementById(`lsgo-sites-side-edit-styles`))return;let e=document.createElement(`style`);e.id=`lsgo-sites-side-edit-styles`,e.textContent=`
    .site-context-strip { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
    .site-context-strip span { border:1px solid var(--line); border-radius:999px; padding:7px 10px; color:var(--muted); font-size:12px; background:rgba(255,255,255,.025); }
    .site-context-strip strong { color:var(--text); }
    .site-parity-card { border:1px solid var(--line); border-radius:14px; padding:14px; background:rgba(255,255,255,.025); display:grid; gap:8px; }
    .site-parity-card p { margin:0; color:var(--muted); line-height:1.5; }
    .site-parity-card .site-chain { display:flex; flex-wrap:wrap; gap:7px; align-items:center; }
    .site-parity-card .site-chain span { border:1px solid var(--line); border-radius:999px; padding:6px 9px; font-size:12px; }
    .site-parity-card .site-chain i { color:var(--teal); font-style:normal; }
  `,document.head.appendChild(e)},Rn=async()=>{let e=document.querySelector(`.topbar > div:first-child`),t=document.querySelector(`#view-sources`);if(!e||!t)return!1;Ln();let n=Pn(await In()),r=n.authority,i=Nn(n.sourceStatus),a=Nn(n.launchStatus);if(!document.getElementById(`site-context-strip`)){let t=document.createElement(`div`);t.id=`site-context-strip`,t.dataset.cgxEvidence=n.manifestEvidence,t.className=`site-context-strip`,t.innerHTML=`
      <span><strong>Owner:</strong> Nathaniel Bouwer</span>
      <span><strong>Mode:</strong> private soft launch</span>
      <span><strong>Source:</strong> ${i}</span>
    `,e.appendChild(t)}if(!document.getElementById(`site-parity-card`)){let e=document.createElement(`article`);e.id=`site-parity-card`,e.dataset.cgxPublicRelease=`held`,e.className=`panel site-parity-card`,e.innerHTML=`
      <p class="eyebrow">Canonical source chain</p>
      <h2>One operator surface, durable receipts</h2>
      <p>Desktop executes locally, Git carries implementation, Drive carries evidence and review records, and UniSpace remains the operator decision surface, powered by LightSpeed. Alignment is shown only after current evidence validates.</p>
      <div class="site-chain">
        ${r.map((e,t)=>`${t?`<i>→</i>`:``}<span>${Nn(e)}</span>`).join(``)}
      </div>
      <p><strong>Launch state:</strong> ${a}</p>
    `,t.prepend(e)}return!0},zn=0,Bn=()=>{Rn().then(e=>{e||zn>=40||(zn+=1,window.requestAnimationFrame(Bn))})};Bn();var Vn=`{
  "design": {
    "schema": "cgx.unispace.interface/1",
    "parent": "cgx:root:cognigrex",
    "title": "UniSpace: one-root five-facet operator review",
    "body": {
      "id": "root",
      "type": "group",
      "title": "UniSpace: one-root five-facet operator review",
      "layout": "tabs",
      "children": [
        {
          "id": "view-0",
          "type": "collection",
          "title": "FileSpace",
          "dataset": "files",
          "facet": "file_space",
          "kind": "",
          "status": "",
          "query": "",
          "layout": "cards",
          "limit": 18
        },
        {
          "id": "view-1",
          "type": "collection",
          "title": "DataSpace",
          "dataset": "records",
          "facet": "data_space",
          "kind": "",
          "status": "",
          "query": "",
          "layout": "cards",
          "limit": 18
        },
        {
          "id": "view-2",
          "type": "collection",
          "title": "SocialSpace",
          "dataset": "handoffs",
          "facet": "social_space",
          "kind": "Handoff",
          "status": "",
          "query": "",
          "layout": "cards",
          "limit": 18
        },
        {
          "id": "view-3",
          "type": "collection",
          "title": "PrintSpace",
          "dataset": "workspace",
          "facet": "print_space",
          "kind": "",
          "status": "",
          "query": "",
          "layout": "cards",
          "limit": 18
        },
        {
          "id": "view-4",
          "type": "collection",
          "title": "IntelligenceSpace",
          "dataset": "workspace",
          "facet": "intelligence_space",
          "kind": "",
          "status": "",
          "query": "",
          "layout": "cards",
          "limit": 18
        }
      ]
    }
  }
}
`,Hn=`cgx.unispace.interface/1`,Un=`cgx:root:cognigrex`,Wn=class extends Error{code;constructor(e){super(e),this.code=e,this.name=`CgxInterfaceHold`}},W=e=>{throw new Wn(e)},Gn=e=>typeof e==`object`&&!!e&&!Array.isArray(e),G=(e,t)=>Object.keys(e).length===t.length&&Object.keys(e).every(e=>t.includes(e)),K=(e,t=112,n=!1)=>typeof e==`string`&&e.length<=t&&(n||e.trim().length>0)&&!/[\u0000-\u001f\u007f<>]/.test(e)&&!/(?:https?:\/\/|javascript:|data:|file:|token=|password=)/i.test(e),Kn=/^[a-z][a-z0-9_-]{0,63}$/,qn={file_space:new Set([`files`,`workspace`]),data_space:new Set([`records`,`workspace`]),social_space:new Set([`handoffs`,`workspace`]),print_space:new Set([`workspace`]),intelligence_space:new Set([`workspace`])},Jn={file_space:`filespace`,data_space:`sources`,social_space:`activity`,print_space:`objects`,intelligence_space:`command`},Yn=Object.keys(Jn),Xn=[`workspace`,`files`,`records`,`handoffs`,`stacks`],Zn=[`id`,`type`,`title`,`layout`,`children`],Qn=[`id`,`type`,`title`,`dataset`,`facet`,`kind`,`status`,`query`,`layout`,`limit`];function $n(e){let t=e;if(typeof t==`string`){if(t.length===0||t.length>32768)return W(`CGX_GUI_SOURCE_SIZE_HOLD`);try{t=JSON.parse(t)}catch{return W(`CGX_GUI_INVALID_JSON`)}}if(!Gn(t)||!G(t,[`design`])||!Gn(t.design))return W(`CGX_GUI_WRAPPER_HOLD`);let n=t.design;if(!G(n,[`schema`,`parent`,`title`,`body`])||n.schema!==`cgx.unispace.interface/1`||n.parent!==`cgx:root:cognigrex`||!K(n.title))return W(`CGX_GUI_CANONICAL_IDENTITY_HOLD`);let r=new Set,i=[],a=0,o=(e,t,n)=>{if(++a>32||n>4||!Gn(e)||typeof e.type!=`string`)return W(`CGX_GUI_DEPTH_OR_NODE_HOLD`);if(!K(e.id,64)||!Kn.test(e.id)||r.has(e.id)||!K(e.title))return W(`CGX_GUI_NODE_ID_OR_LABEL_HOLD`);if(r.add(e.id),e.type===`group`){if(!G(e,Zn)||![`tabs`,`stack`,`grid`].includes(String(e.layout))||!Array.isArray(e.children)||e.children.length<1||e.children.length>16)return W(`CGX_GUI_GROUP_SHAPE_HOLD`);for(let r of e.children)o(r,[...t,e.title],n+1);return}if(e.type!==`collection`||!G(e,Qn))return W(`CGX_GUI_UNSUPPORTED_CONTROL_HOLD`);if(!Xn.includes(e.dataset)||e.facet!==``&&!Yn.includes(e.facet)||!K(e.kind,64,!0)||!K(e.status,64,!0)||!K(e.query,110,!0)||![`cards`,`rows`].includes(String(e.layout))||!Number.isSafeInteger(e.limit)||Number(e.limit)<1||Number(e.limit)>24)return W(`CGX_GUI_COLLECTION_SHAPE_HOLD`);let s=e.facet;if(s){if(!qn[s].has(e.dataset))return W(`CGX_GUI_FACET_DATASET_MISMATCH`)}else if(e.dataset!==`workspace`&&e.dataset!==`stacks`)return W(`CGX_GUI_UNSCOPED_PRIVATE_DATASET_HOLD`);i.push(Object.freeze({id:e.id,title:e.title,path:Object.freeze(t),type:`collection`,dataset:e.dataset,facet:s,kind:e.kind,status:e.status,query:e.query,layout:e.layout,limit:e.limit,workspace:s?Jn[s]:null}))},s=n.body;return!Gn(s)||s.type!==`group`||s.id!==`root`||!G(s,Zn)||![`tabs`,`stack`,`grid`].includes(String(s.layout))?W(`CGX_GUI_ROOT_GROUP_HOLD`):(o(s,[],0),i.length<1||i.length>16?W(`CGX_GUI_NO_BOUNDED_COLLECTIONS`):Object.freeze({schema:Hn,parent:Un,title:n.title,layout:s.layout,panels:Object.freeze(i),state:`SOURCE_PROJECTION_ONLY`,nativeAdmitted:!1,hostAuthenticated:!1,publicPublished:!1,handlersBound:!1,privateBytesIncluded:!1}))}var q=e=>e.replace(/[&<>"']/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#39;`})[e]||e);function er(e,t=e.panels[0]?.id){let n=e.panels.find(e=>e.id===t)||e.panels[0],r=e.panels.map(e=>`<button type="button" role="tab" data-cgx-gui-tab="`+e.id+`" aria-selected="`+String(n?.id===e.id)+`" tabindex="`+String(n?.id===e.id?0:-1)+`">`+q(e.title)+`</button>`).join(``),i=n.path.slice(1).map(q).join(` / `),a=n.workspace?`<button type="button" data-cgx-gui-open="`+n.workspace+`">Open existing `+q(n.workspace)+` workspace</button>`:`<p class="ls-cgx-gui-muted">Unscoped catalogue preview; no private objects loaded</p>`;return`<div class="ls-cgx-gui-layout" data-layout="`+e.layout+`"><nav class="ls-cgx-gui-tabs" role="tablist" aria-label="Generated CGX views">`+r+`</nav><article class="ls-cgx-gui-panel" role="tabpanel" aria-label="`+q(n.title)+`"><p class="ls-cgx-gui-kicker">`+(i?i+` / `:``)+q(n.facet||`workspace`)+`</p><h3>`+q(n.title)+`</h3><div class="ls-cgx-gui-metadata"><span>Dataset: `+q(n.dataset)+`</span><span>Projection: `+q(n.layout)+`</span><span>Max rows: `+n.limit+`</span></div><p>View generated from a source-qualified Interface Studio schema. No private entries, peer DBR evidence or privileged controls are loaded in this preview.</p><div class="ls-cgx-gui-card-stack" data-layout="`+n.layout+`"><div class="ls-cgx-gui-preview-card"><strong>Object references</strong><small>Awaiting authenticated FileSpace/DataSpace readback</small></div><div class="ls-cgx-gui-preview-card"><strong>Evidence and rights</strong><small>Source-review only · no native admission</small></div><div class="ls-cgx-gui-preview-card"><strong>Generated controls</strong><small>Preview-only navigation · write actions remain held</small></div></div><div class="ls-cgx-gui-actions">`+a+`</div></article></div>`}function tr(e,t,n){let r=t,i=$n(r),a=i,o=a.panels[0]?.id;e.innerHTML=`<div class="ls-cgx-gui-head"><div><p class="ls-cgx-gui-kicker">Cognigrex.cgx / generated GUI</p><h2>Interface Studio · FileSpace engine</h2><p>Five-facet source layout; existing LightSpeed workspaces remain the only navigation targets.</p></div><span class="ls-cgx-gui-hold">Source review · native held</span></div><div class="ls-cgx-gui-live" id="ls-cgx-gui-preview"></div><details class="ls-cgx-gui-schema"><summary>Review or paste an Interface Studio layout (local preview only)</summary><label for="ls-cgx-gui-json">Portable .cgx interface JSON</label><textarea id="ls-cgx-gui-json" rows="8" spellcheck="false" maxlength="32768"></textarea><div class="ls-cgx-gui-actions"><button type="button" id="ls-cgx-gui-apply">Preview schema</button><button type="button" id="ls-cgx-gui-reset">Restore source layout</button></div></details><p class="ls-cgx-gui-note" id="ls-cgx-gui-note" role="status" aria-live="polite">Source-qualified layout loaded locally; no private data or published site updates.</p>`;let s=e.querySelector(`#ls-cgx-gui-preview`),c=e.querySelector(`#ls-cgx-gui-json`),l=e.querySelector(`#ls-cgx-gui-note`);c.value=t;let u=()=>{s.innerHTML=er(a,o),s.querySelectorAll(`[data-cgx-gui-tab]`).forEach(e=>{e.addEventListener(`click`,()=>{o=e.dataset.cgxGuiTab||a.panels[0]?.id,u()})}),s.querySelectorAll(`[data-cgx-gui-open]`).forEach(e=>{e.addEventListener(`click`,()=>{let t=e.dataset.cgxGuiOpen;[`command`,`activity`,`objects`,`sources`,`filespace`].includes(t)&&n(t)})})};e.querySelector(`#ls-cgx-gui-apply`)?.addEventListener(`click`,()=>{try{a=$n(c.value),o=a.panels[0]?.id,l.textContent=`Valid portable layout; browser preview updated. Host import not performed.`,u()}catch(e){l.textContent=e instanceof Wn?`Import held: `+e.code+`. Existing layout preserved.`:`Import held: invalid or unsupported Interface Studio payload.`}}),e.querySelector(`#ls-cgx-gui-reset`)?.addEventListener(`click`,()=>{c.value=r,a=i,o=a.panels[0]?.id,l.textContent=`Original source-qualified layout restored; no remote mutation.`,u()}),u()}var nr=`lightspeed-cognigrex-os-shell-v0.1`,rr=[`command`,`activity`,`objects`,`system`,`sources`,`filespace`],ir=[{id:`profilespace`,label:`ProfileSpace`,view:`activity`,description:`Owner session and activity review; not a portable identity service.`,status:`projection-only`},{id:`filespace`,label:`FileSpace`,view:`filespace`,description:`Bounded FileSpace reader; private hydration requires approved scope.`,status:`projection-only`},{id:`dataspace`,label:`DataSpace`,view:`sources`,description:`Source and evidence review; no distributed persistence claim.`,status:`projection-only`},{id:`socialspace`,label:`SocialSpace`,view:`activity`,description:`Event and review evidence; no external social publication.`,status:`projection-only`},{id:`printspace`,label:`PrintSpace`,view:`objects`,description:`Object and CAD references; no physical machine commands.`,status:`projection-only`},{id:`intelligencespace`,label:`IntelligenceSpace`,view:`command`,description:`Neo-routed command intake; execution remains separately authorised.`,status:`projection-only`},{id:`systemspace`,label:`SystemSpace`,view:`system`,description:`Runtime status; selecting does not admit a node or root.`,status:`projection-only`}],ar=e=>ir.find(t=>t.id===e),or=[{id:`intake`,label:`Intake`,owner:`Neo`,receipt:`source envelope`,description:`Capture the request, source pointers, project identity, constraints and expected output without inventing missing authority.`},{id:`analyse`,label:`Analyse`,owner:`Neo + Oracle`,receipt:`scope / evidence map`,description:`Resolve knowns, source authority, evidence class, conflicts, privacy and the minimum useful execution path.`},{id:`route`,label:`Commit`,owner:`Neo`,receipt:`stable task / agent route`,description:`Commit one bounded job to the correct specialist floor while retaining stable identity and exact-once transport semantics.`},{id:`workshop`,label:`Workshop`,owner:`specialist floor`,receipt:`artifact / data / result`,description:`Execute the bounded specialist work: code, modelling, evidence extraction, interface work, planning or runtime recovery.`},{id:`proof`,label:`Proof`,owner:`Smith + Morpheus + Oracle`,receipt:`tests / provenance / contradiction`,description:`Test implementation, verify provenance, resolve conflicts and keep hypothesis, inference and empirical evidence distinct.`},{id:`consolidate`,label:`Consolidate`,owner:`Neo + Achilles`,receipt:`canonical delta / supersession`,description:`Return accepted results to the living canonical library as compact deltas, pointers and receipts rather than duplicate masters.`},{id:`release`,label:`Publish-ready`,owner:`Achilles`,receipt:`claim / security / release gate`,description:`Package approved digital artifacts, data and objects for a bounded release candidate. Publish-ready is not automatically published.`}],sr=[{floor:`Neo`,short:`N`,role:`Cognigrex operational head: intake, decomposition, routing, cycle control and result aggregation.`,boundary:`May coordinate and reason operationally; cannot self-promote evidence, canon or public claims past Achilles/owner gates.`},{floor:`Oracle`,short:`O`,role:`Sources, evidence retrieval, indexing, known-state and data lineage.`,boundary:`Preserves source authority and uncertainty; duplicate references do not become independent evidence.`},{floor:`Morpheus`,short:`M`,role:`Contradiction, provenance, claim proof, confidence and supersession review.`,boundary:`Reviews and recommends; does not fabricate empirical validation.`},{floor:`Smith`,short:`S`,role:`Code, schemas, deterministic transforms, tests, build and execution receipts.`,boundary:`Changes remain branch/review gated until the applicable execution and release receipts exist.`},{floor:`Architect`,short:`A`,role:`Projects, dependency topology, plans, interfaces and system decomposition.`,boundary:`Uses canonical project identity and pointers rather than spawning competing masters.`},{floor:`TheConstruct`,short:`TC`,role:`Simulation, CAD, meshes, digital twins, derived views and manufacturing-reference artifacts.`,boundary:`Derived models remain labelled and cannot imply physical performance without evidence.`},{floor:`Trinity`,short:`T`,role:`Interface, interaction, visual language, accessibility and communication surfaces.`,boundary:`Presentation cannot elevate claim state or bypass evidence/security classification.`},{floor:`Merovingian`,short:`R`,role:`Runtime health, storage, recovery, resource control, persistence and operational receipts.`,boundary:`Recovery and cleanup are reversible/evidence-gated; no silent deletion or second runtime.`},{floor:`Achilles`,short:`Ω`,role:`Meta-governance, proof thresholds, safety, canonical promotion and release oversight.`,boundary:`Audits and gates the collective; it is not the routine task router inside Cognigrex.`}],cr=e=>rr.includes(e)?e:`command`,lr=(e,t=`command`)=>cr(new URLSearchParams(e.startsWith(`?`)?e.slice(1):e).get(`view`)||t),ur=e=>{let t=e.trim().toLowerCase();return t?/\b(publish|release|public[- ]?ready|export|mint|deploy)\b/.test(t)?`release`:/\b(consolidat|canon|supersed|assimil|promot|living library|handoff)\b/.test(t)?`consolidate`:/\b(test|proof|verify|validat|audit|conflict|provenance|claim|confidence)\b/.test(t)?`proof`:/\b(build|code|model|simulate|render|mesh|cad|analyse data|analyze data|workshop|execute|run)\b/.test(t)?`workshop`:/\b(route|delegate|commit|queue|assign|agent|floor)\b/.test(t)?`route`:/\b(source|evidence|research|analyse|analyze|classif|scope|compare|reconcile)\b/.test(t)?`analyse`:`intake`:`intake`},dr=e=>{let t=e.trim().toLowerCase();if(!t)return`Neo`;if(/\b(proof|claim|verify|verification|conflict|confidence|audit|contradiction|supersession)\b/.test(t))return`Morpheus`;if(/\b(achilles|governance|canonical promotion|release gate|safety gate)\b/.test(t))return`Achilles`;let n=s(e);return n===`Achilles`?`Neo`:n},fr=e=>or.find(t=>t.id===e)??or[0],pr=`lightspeed-cognigrex-os-shell-state-v1`,mr={activeView:`command`,activeAgent:`Neo`,focusMode:!1},J=(()=>{try{let e=JSON.parse(localStorage.getItem(pr)||`{}`),t=sr.some(t=>t.floor===e.activeAgent)?e.activeAgent:mr.activeAgent;return{activeView:lr(window.location.search,window.location.hash.slice(1)||e.activeView),activeAgent:t,focusMode:!!e.focusMode}}catch{return{...mr}}})(),hr=e=>{J={...J,...e},localStorage.setItem(pr,JSON.stringify(J))},Y=e=>e.replace(/[&<>'"]/g,e=>({"&":`&amp;`,"<":`&lt;`,">":`&gt;`,"'":`&#39;`,'"':`&quot;`})[e]||e),X=e=>{let t=document.querySelector(`.tab[data-view="${e}"]`);t&&!t.classList.contains(`active`)&&t.click(),hr({activeView:e}),document.body.dataset.lsWorkspace=e,document.body.dataset.lsSpace=`unispace`;let n=document.getElementById(`ls-os-space-context`);n&&(n.textContent=`UniSpace · one canonical workspace`)},Z=(e,t=!1)=>{hr({activeAgent:e}),document.body.dataset.lsAgent=e,document.querySelectorAll(`[data-ls-agent]`).forEach(t=>{t.dataset.active=t.dataset.lsAgent===e?`true`:`false`});let n=document.getElementById(`target-floor`);n&&(n.value=e),t&&(X(`command`),document.getElementById(`instruction`)?.focus())},Q=e=>{let t=fr(e);document.body.dataset.lsWorkflow=t.id,document.querySelectorAll(`[data-ls-stage]`).forEach(e=>{e.dataset.active=e.dataset.lsStage===t.id?`true`:`false`});let n=document.getElementById(`ls-os-stage-detail`);n&&(n.innerHTML=`<strong>${Y(t.label)}</strong><span>${Y(t.description)}</span><small>${Y(t.owner)} · receipt: ${Y(t.receipt)}</small>`)},gr=()=>{let e=document.createElement(`aside`);return e.className=`ls-os-rail`,e.setAttribute(`aria-label`,`Cognigrex agent rail`),e.innerHTML=`
    <button class="ls-os-mark" type="button" data-ls-home title="UniSpace · Cognigrex" aria-label="UniSpace home">U</button>
    <div class="ls-os-agent-stack">
      ${sr.map(e=>`
        <button class="ls-os-agent" type="button" data-ls-agent="${e.floor}" title="${Y(e.floor)} — ${Y(e.role)}">
          <span>${Y(e.short)}</span><small>${Y(e.floor)}</small>
        </button>
      `).join(``)}
    </div>
    <button class="ls-os-focus" type="button" data-ls-focus title="Toggle focus mode">◫</button>
  `,e.querySelectorAll(`[data-ls-agent]`).forEach(e=>{e.addEventListener(`click`,()=>Z(e.dataset.lsAgent,!0))}),e.querySelector(`[data-ls-home]`)?.addEventListener(`click`,()=>X(`command`)),e.querySelector(`[data-ls-focus]`)?.addEventListener(`click`,()=>{let e=!J.focusMode;hr({focusMode:e}),document.body.dataset.lsFocus=e?`true`:`false`}),e},_r=()=>{let e=document.createElement(`section`);return e.className=`ls-os-status-strip`,e.setAttribute(`aria-label`,`UniSpace operating state`),e.innerHTML=`
    <div><span class="ls-os-status-dot" id="ls-os-runtime-dot"></span><strong id="ls-os-runtime">Desktop checking</strong><small>${n}</small></div>
    <div><span class="ls-os-status-dot stable"></span><strong>Neo operational head</strong><small>specialist-agent orchestration</small></div>
    <div><span class="ls-os-status-dot guarded"></span><strong>Achilles oversight</strong><small>evidence · canon · release gate</small></div>
    <div><span class="ls-os-status-dot private"></span><strong>De Sporte</strong><small>private persistence sidecar · metadata only</small></div>
    <button type="button" id="ls-os-palette-open" aria-controls="ls-os-palette" aria-expanded="false" title="Open command palette (Ctrl/Cmd+K)">⌘K</button>
  `,e},vr=()=>{let e=document.createElement(`section`);return e.className=`ls-os-workflow`,e.setAttribute(`aria-label`,`ACR3 operating workflow`),e.innerHTML=`
    <div class="ls-os-workflow-track">
      ${or.map((e,t)=>`
        <button type="button" data-ls-stage="${e.id}" title="${Y(e.description)}">
          <span>${String(t+1).padStart(2,`0`)}</span><strong>${Y(e.label)}</strong><small>${Y(e.owner)}</small>
        </button>
      `).join(``)}
    </div>
    <div class="ls-os-stage-detail" id="ls-os-stage-detail"></div>
  `,e.querySelectorAll(`[data-ls-stage]`).forEach(e=>{e.addEventListener(`click`,()=>Q(e.dataset.lsStage))}),e},yr=()=>{let e=document.createElement(`div`);return e.className=`ls-os-palette`,e.id=`ls-os-palette`,e.hidden=!0,e.innerHTML=`
    <div class="ls-os-palette-card" role="dialog" aria-modal="true" aria-label="UniSpace command palette">
      <div class="ls-os-palette-head"><strong>UniSpace</strong><span>LightSpeed toolkit</span><button type="button" data-ls-close aria-label="Close">×</button></div>
      <input id="ls-os-palette-input" type="search" autocomplete="off" placeholder="Find a space, workspace, agent, or route an outcome…" />
      <div id="ls-os-palette-results" class="ls-os-palette-results"></div>
    </div>
  `,e.addEventListener(`click`,t=>{t.target===e&&$()}),e.querySelector(`[data-ls-close]`)?.addEventListener(`click`,()=>$()),e.querySelector(`#ls-os-palette-input`)?.addEventListener(`input`,()=>Sr()),e.addEventListener(`keydown`,t=>{if(t.key===`Escape`){t.preventDefault(),t.stopPropagation(),$();return}if(t.key!==`Tab`)return;let n=Array.from(e.querySelectorAll(`button:not([disabled]), input:not([disabled])`)).filter(e=>e.getClientRects().length>0),r=n[0],i=n[n.length-1];!r||!i?t.preventDefault():t.shiftKey&&document.activeElement===r?(t.preventDefault(),i.focus()):!t.shiftKey&&document.activeElement===i&&(t.preventDefault(),r.focus())}),e},br=null,xr=()=>{let e=document.getElementById(`ls-os-palette`);e&&(e.hidden&&(br=document.activeElement instanceof HTMLElement?document.activeElement:null),e.hidden=!1,document.getElementById(`ls-os-palette-open`)?.setAttribute(`aria-expanded`,`true`),Sr(),window.setTimeout(()=>{e.hidden||document.getElementById(`ls-os-palette-input`)?.focus()},0))},$=(e=!0)=>{let t=document.getElementById(`ls-os-palette`);t&&(t.hidden=!0),document.getElementById(`ls-os-palette-open`)?.setAttribute(`aria-expanded`,`false`),e&&br?.focus(),br=null},Sr=()=>{let e=document.getElementById(`ls-os-palette-input`),t=document.getElementById(`ls-os-palette-results`);if(!e||!t)return;let n=e.value.trim().toLowerCase(),r=ir.filter(e=>!n||`${e.label} ${e.description}`.toLowerCase().includes(n)).map(e=>`<button type="button" data-palette-facet="${e.id}"><span>Space</span><strong>${Y(e.label)}</strong><small>${Y(e.description)}</small></button>`),i=rr.filter(e=>!n||e.includes(n)).map(e=>`<button type="button" data-palette-view="${e}"><span>Workspace</span><strong>${e}</strong><small>Open ${e} workspace</small></button>`),a=sr.filter(e=>!n||`${e.floor} ${e.role}`.toLowerCase().includes(n)).map(e=>`<button type="button" data-palette-agent="${e.floor}"><span>Agent</span><strong>${Y(e.floor)}</strong><small>${Y(e.role)}</small></button>`),o=n?[`<button type="button" data-palette-route="true"><span>Neo route</span><strong>${Y(dr(e.value))}</strong><small>Use this text as the command outcome and route it through Cognigrex.</small></button>`]:[];t.innerHTML=[...r,...o,...i,...a].slice(0,18).join(``),t.querySelectorAll(`[data-palette-view]`).forEach(e=>e.addEventListener(`click`,()=>{X(cr(e.dataset.paletteView)),$()})),t.querySelectorAll(`[data-palette-facet]`).forEach(e=>{let t=ar(e.dataset.paletteFacet);t&&e.addEventListener(`click`,()=>{X(t.view);let e=document.getElementById(`ls-os-space-context`);e&&(e.textContent=`${t.label} · projection-only · ${t.description}`),document.body.dataset.lsSpace=t.id,$()})}),t.querySelectorAll(`[data-palette-agent]`).forEach(e=>e.addEventListener(`click`,()=>{Z(e.dataset.paletteAgent,!0),$(!1)})),t.querySelector(`[data-palette-route]`)?.addEventListener(`click`,()=>{let t=e.value.trim(),n=document.getElementById(`instruction`);n&&t&&(n.value=t,n.dispatchEvent(new Event(`input`,{bubbles:!0})),Z(dr(t)),Q(ur(t)),n.focus()),X(`command`),$(!1)})},Cr=e=>{let t=e.querySelector(`#view-command .command-panel .panel-head .eyebrow`);t&&(t.textContent=`Neo intake`);let n=e.querySelector(`#view-command .command-panel .panel-head h2`);n&&(n.textContent=`State the outcome`);let r=e.querySelector(`#command-form button.primary[type=submit]`);r&&(r.textContent=`Send to runtime`);let i=e.querySelector(`#view-command .guardrail-panel .eyebrow`);i&&(i.textContent=`Cognigrex operating contract`);let a=e.querySelector(`#view-command .guardrail-panel h2`);a&&(a.textContent=`Neo-led work, durable proof`);let o=e.querySelectorAll(`#view-command .guardrail-panel .compact-list li`),s=[`Neo owns intake, decomposition, routing and aggregate workflow identity.`,`Specialist floors execute only their bounded purpose and return receipts.`,`Oracle, Smith and Morpheus preserve source, implementation and proof boundaries.`,`Achilles governs evidence class, canonical promotion, safety and release.`,`Accepted results return as compact canonical deltas rather than duplicate masters.`];o.forEach((e,t)=>{s[t]&&(e.textContent=s[t])});let c=e.querySelector(`#view-system .flow`);c&&(c.innerHTML=`<span>UniSpace</span><i>→</i><span>Neo</span><i>→</i><span>specialist floors</span><i>→</i><span>Morpheus proof</span><i>→</i><span>Achilles gate</span><i>→</i><span>canon / release</span>`);let l=e.querySelector(`#view-system .agent-grid`);if(l){let e=new Map;l.querySelectorAll(`.agent`).forEach(t=>{let n=t.querySelector(`strong`)?.textContent?.trim();n&&e.set(n,t)}),sr.forEach(t=>{let n=e.get(t.floor);n&&l.append(n)})}e.querySelectorAll(`.panel-head`).forEach(e=>{if(e.querySelector(`h2`)?.textContent?.trim()!==`Review queue`)return;let t=e.querySelector(`.eyebrow`);t&&(t.textContent=`Achilles / owner gate`)})},wr=()=>{document.querySelectorAll(`.tab[data-view]`).forEach(e=>{e.addEventListener(`click`,()=>{let t=cr(e.dataset.view);hr({activeView:t}),document.body.dataset.lsWorkspace=t,document.body.dataset.lsSpace=`unispace`;let n=document.getElementById(`ls-os-space-context`);n&&(n.textContent=`UniSpace · one canonical workspace`)})});let e=document.getElementById(`instruction`),t=document.getElementById(`route-preview`);e?.addEventListener(`input`,()=>{let n=dr(e.value);Z(n),Q(ur(e.value)),t&&(t.innerHTML=`<strong>Neo route:</strong> ${Y(n)} is the primary specialist. Achilles remains the evidence, canonical-promotion and release oversight gate.`)}),document.getElementById(`ls-os-palette-open`)?.addEventListener(`click`,()=>xr())},Tr=async()=>{let e=document.getElementById(`ls-os-runtime`),t=document.getElementById(`ls-os-runtime-dot`);if(e&&t)try{let n=await d(),r=!!(n.ok&&n.services?.merovingian!==!1);e.textContent=r?`Desktop online`:`Desktop degraded`,t.dataset.state=r?`online`:`degraded`,t.title=n.time_utc?`Last read ${n.time_utc}`:`Local status read`}catch{e.textContent=`Desktop offline / unproved`,t.dataset.state=`offline`,t.title=`No current localhost receipt from this browser.`}};queueMicrotask(()=>{if(document.documentElement.dataset.lsOsShell===`lightspeed-cognigrex-os-shell-v0.1`)return;let e=document.querySelector(`.shell`);if(!e)return;document.documentElement.dataset.lsOsShell=nr,document.body.classList.add(`ls-os-enabled`),document.body.dataset.lsFocus=J.focusMode?`true`:`false`,document.title=`UniSpace · Cognigrex`,document.body.prepend(gr()),e.prepend(vr()),e.prepend(_r()),document.body.append(yr());let t=e.querySelector(`.tabs`);if(t){let e=document.createElement(`section`);e.id=`ls-cgx-generated-gui`,e.className=`ls-cgx-generated-gui`,e.setAttribute(`aria-label`,`Generated Cognigrex FileSpace operator interface`),t.after(e);try{tr(e,Vn,e=>X(e))}catch{e.textContent=`Generated .cgx layout held: review the source schema. Existing UniSpace views remain available.`,e.dataset.sourceState=`held`}}let n=e.querySelector(`.topbar h1`);n&&(n.textContent=`UniSpace`);let r=e.querySelector(`.topbar .eyebrow`);r&&(r.textContent=`Cognigrex · powered by LightSpeed`);let i=e.querySelector(`.topbar .lede`);i&&(i.textContent=`Your Cognigrex workspace for .cgx objects, local tools and evidence. Neo coordinates specialist agents through LightSpeed; Achilles governs evidence and release.`);let a=document.createElement(`p`);a.id=`ls-os-space-context`,a.setAttribute(`role`,`status`),a.textContent=`UniSpace · one canonical workspace`,a.style.cssText=`font-size:12px;color:var(--muted);margin-top:6px;line-height:1.4`,e.querySelector(`.topbar .lede`)?.after(a),Cr(e),wr(),X(J.activeView),Z(J.activeAgent);let o=document.getElementById(`instruction`);o?o.dispatchEvent(new Event(`input`,{bubbles:!0})):(Q(`intake`),Z(`Neo`)),Tr().catch(()=>void 0),window.setInterval(()=>Tr().catch(()=>void 0),3e4),window.addEventListener(`keydown`,e=>{(e.ctrlKey||e.metaKey)&&e.key.toLowerCase()===`k`?(e.preventDefault(),xr()):(e.key===`Escape`&&$(),(e.ctrlKey||e.metaKey)&&/^[1-6]$/.test(e.key)&&(e.preventDefault(),X(rr[Number(e.key)-1]||`command`)))})});