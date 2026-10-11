import {DEFAULT_DESKTOP_ORIGIN} from "./desktopBridge";
const safe=(s:string)=>s.replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]||c));
type RecordRow={reviewer_id:string;name:string;theme:string;lens:string;handshake_json:string;consent_utc:string};
type EventRow={event_id:string;reviewer_id:string;event_type:string;recorded_utc:string;event_hash:string;previous_hash:string;payload_json:string};
type Snapshot={schema:string;profiles:RecordRow[];events:EventRow[];canonical_cgx_ingestion:false;chain_verified:boolean;proof_scope:string};
async function ownerFetch<T>(path:string,token:string,data?:unknown):Promise<T>{
 if(!token)throw Error("Owner sign-in required. Use the Activity workspace.");
 const r=await fetch(DEFAULT_DESKTOP_ORIGIN+path,{
  method:data===undefined?"GET":"POST",
  headers:{"X-LightSpeed-Session":token,"Content-Type":"application/json"},
  body:data===undefined?undefined:JSON.stringify(data),
  credentials:"omit",cache:"no-store",
 });
 const result=await r.json().catch(()=>({detail:"Unreadable owner response"}));
 if(!r.ok)throw Error(String(result.detail||"Owner review unavailable"));
 return result as T;
}
export function installOwnerVisitorReview(getToken:()=>string):void{
 const mount=document.getElementById("visitor-owner-review");
 if(!mount)return;
 mount.innerHTML=`<div class="panel-head"><div><p class="eyebrow">Cognigrex · LS GO</p><h2>External reviewer receipts</h2></div><span class="badge">Owner only</span></div>
 <p class="muted">Four visitor seats, stored handshake preferences and scoped review events. No automatic CGX DBR promotion.</p>
 <div class="actions"><button type="button" id="visitor-owner-refresh">Read receipts</button><button type="button" id="visitor-owner-invite">Issue one private invitation</button></div>
 <p id="visitor-owner-status" role="status"></p><div id="visitor-owner-list"></div>`;
 const status=document.getElementById("visitor-owner-status")!;
 const list=document.getElementById("visitor-owner-list")!;
 const refresh=async()=>{
   try{
     const data=await ownerFetch<Snapshot>("/api/v1/visitor/owner-review",getToken());
     status.textContent=`${data.profiles.length} reviewer profiles · ${data.events.length} receipts · Chain ${data.chain_verified ? "VERIFIED" : "FAILED"} · ${data.proof_scope} · not canonical CGX DBR`;
     list.innerHTML=data.profiles.map(p=>{
      const events=data.events.filter(e=>e.reviewer_id===p.reviewer_id);
      return `<article class="task-card"><div><strong>${safe(p.name)}</strong><span>${safe(p.reviewer_id)} · ${safe(p.theme)} · ${safe(p.lens)}</span><small>Consent: ${safe(p.consent_utc)} · ${events.length} events</small><div class="task-actions"><button data-owner-revoke="${safe(p.reviewer_id)}">Revoke sessions</button><button data-owner-renew="${safe(p.reviewer_id)}">Renew invite</button></div><details><summary>Inspect receipt lineage</summary>${events.map(e=>"<p>"+safe(e.event_type)+" · "+safe(e.recorded_utc)+" · "+safe(e.event_hash.slice(0,20))+"…<br/><small>"+safe(e.payload_json.slice(0,400))+"</small></p>").join("")}</details></div></article>`;
     }).join("")||"<p class='muted'>No reviewer profiles enrolled.</p>";
     list.querySelectorAll<HTMLButtonElement>("[data-owner-revoke]").forEach(b=>b.onclick=async()=>{
       if(!window.confirm("Revoke all active sessions for this reviewer?"))return;
       try{
         await ownerFetch("/api/v1/visitor/revoke",getToken(),{reviewer_id:b.dataset.ownerRevoke});
         await refresh();
       }catch(err){status.textContent=String(err);}
     });
     list.querySelectorAll<HTMLButtonElement>("[data-owner-renew]").forEach(b=>b.onclick=async()=>{
       try{
         const host=String(import.meta.env.VITE_LIGHTSPEED_REVIEW_ORIGIN||"").trim();
         const uri=new URL(host);
         if(uri.protocol!=="https:"||uri.username||uri.password||uri.pathname!=="/"||uri.search||uri.hash)throw Error("Verified HTTPS reviewer origin required");
         const next=await ownerFetch<{invite_token:string;reviewer_id:string}>("/api/v1/visitor/invites",getToken(),{reviewer_id:b.dataset.ownerRenew});
         const link=new URL("review.html",uri.origin+"/");link.hash="invite="+encodeURIComponent(next.invite_token);
         const field=document.createElement("textarea");field.readOnly=true;field.value=link.href;field.style.width="100%";
         list.prepend(field);status.textContent="Reissued one-time invite for "+next.reviewer_id+". Deliver privately after off-device verification.";
       }catch(err){status.textContent=String(err);}
     });
   }catch(e){status.textContent=e instanceof Error?e.message:"Review readback unavailable";}
 };
 document.getElementById("visitor-owner-refresh")!.addEventListener("click",()=>void refresh());
 document.getElementById("visitor-owner-invite")!.addEventListener("click",async()=>{
  try{
   const configured=String(import.meta.env.VITE_LIGHTSPEED_REVIEW_ORIGIN || "").trim();
   const uri=new URL(configured);
   if(uri.protocol!=="https:" || uri.username || uri.password || uri.pathname!=="/" || uri.search || uri.hash)
     throw new Error("Verified HTTPS reviewer host must be configured before private links are issued.");
   const r=await ownerFetch<{reviewer_id:string;invite_token:string;expires_utc:string}>("/api/v1/visitor/invites",getToken(),{});
   const link=new URL("review.html",uri.origin+"/");
   link.hash="invite="+encodeURIComponent(r.invite_token);
   list.textContent="";
   const code=document.createElement("textarea");code.readOnly=true;code.value=link.href;code.style.width="100%";
   list.append(code);
   status.textContent=`Private one-time link issued for ${r.reviewer_id}. Not verified for off-device delivery; test TLS and backend first. Never paste into public /cgx.`;
  }catch(e){status.textContent=e instanceof Error?e.message:"Invitation issue held";}
 });
}
