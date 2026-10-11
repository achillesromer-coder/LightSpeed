import "./visitorWorkspace.css";
import {LENSES,THEMES,setVisitorSession,visitorRequest,type CgxLens} from "./visitorBridge";
const root=document.getElementById("visitor-app")!;
const escapeText=(s:string)=>s.replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]||c));
const banner='<header><small>LIGHTSPEED GO / CGX</small><h1>External review</h1><a href="https://romer.industries/cgx">Public orientation ↗</a></header>';
const invite=new URLSearchParams(location.hash.slice(1)).get("invite");
let lens:CgxLens="achilles",busy=false;
function workspace(name:string){
 root.innerHTML=banner+`<div class="v-grid"><aside><h2>${escapeText(name)}</h2><p>Select a lens</p><button id="v-logout" class="v-muted">End session</button>${Object.entries(LENSES).map(([id,n])=>`<button data-lens="${id}">${escapeText(n)}</button>`).join("")}</aside>
 <section><h2 id="v-lens">${escapeText(LENSES[lens])}</h2><div id="v-log" role="log">Ask about CGX, challenge a claim or request a source-backed 3D model.</div>
 <form id="v-talk"><textarea maxlength="2000" required aria-label="Your question"></textarea><select aria-label="Request type"><option value="question">Question</option><option value="model_request">3D model</option><option value="feedback">Feedback</option></select><button>Submit</button></form><p id="v-result" role="status"></p></section>
 <aside><h2>Source and evidence</h2><p>Concept → Source-backed → Simulated → Measured → Independently accepted → Publicly released.</p><p>Unadmitted models are not generated. Visitor requests cannot mutate sources or execute commands.</p></aside></div>`;
 document.getElementById("v-logout")!.addEventListener("click",async()=>{
   try{await visitorRequest("/api/v1/visitor/logout",{});}
   finally{
      setVisitorSession("");root.innerHTML=banner+"<main><h2>Signed out</h2><p>Review receipts remain available to the authorised owner. A fresh invitation is needed for a new session.</p></main>";
   }
 });
 document.querySelectorAll<HTMLButtonElement>("[data-lens]").forEach(b=>b.onclick=async()=>{
   lens=b.dataset.lens as CgxLens;document.getElementById("v-lens")!.textContent=LENSES[lens];
   try{await visitorRequest("/api/v1/visitor/interaction",{kind:"selection",lens,text:"Selected lens"});}
   catch{document.getElementById("v-result")!.textContent="Lens selection unavailable to server.";}
 });
 const form=document.getElementById("v-talk") as HTMLFormElement;
 form.onsubmit=async e=>{
  e.preventDefault();if(busy)return;busy=true;
  const q=form.querySelector("textarea")!,kind=form.querySelector("select")!.value,text=q.value.trim();
  try{
   const r=await visitorRequest<{status:string;receipt:{event_id:string}}>("/api/v1/visitor/interaction",{kind,lens,text});
   const p=document.createElement("p");p.textContent=`${text} → ${r.status} · Receipt ${r.receipt.event_id}`;
   document.getElementById("v-log")!.append(p);q.value="";
  }catch(err){document.getElementById("v-result")!.textContent=String(err);}
  finally{busy=false;}
 };
}
if(!invite)root.innerHTML=banner+"<main><h2>Invitation required</h2><p>Request a private LS GO reviewer link from the owner.</p></main>";
else{
 root.innerHTML=banner+`<main><h2>Welcome to CGX</h2><p>Invitation-scoped review · choose a background and lens.</p>
 <form id="v-enroll"><label>Name <input name="name" maxlength="72" required></label>
 <label>Background (optional) <input name="background" maxlength="500"></label>
 <label>Research interest (optional) <input name="intent" maxlength="500"></label>
 <fieldset><legend>Theme</legend>${THEMES.map(t=>`<label><input type="radio" name="theme" value="${t}" ${t==="orbit"?"checked":""}>${t}</label>`).join("")}</fieldset>
 <fieldset><legend>Lens</legend>${Object.entries(LENSES).map(([id,n])=>`<label><input type="radio" name="lens" value="${id}" ${id==="achilles"?"checked":""}>${escapeText(n)}</label>`).join("")}</fieldset>
 <label><input type="checkbox" name="consent" required> Consent to recording your review and selected profile preferences.</label>
 <button>Enter LS GO</button><p id="v-result" role="status"></p></form></main>`;
 const form=document.getElementById("v-enroll") as HTMLFormElement;
 form.onsubmit=async e=>{
  e.preventDefault();if(busy)return;busy=true;
  const fields=Object.fromEntries(new FormData(form));
  try{
    const r=await visitorRequest<{visitor_session:string;profile:{name:string;lens:CgxLens}}>("/api/v1/visitor/enroll",{
      ...fields,invite_token:invite,consent:fields.consent==="on"});
    setVisitorSession(r.visitor_session);lens=r.profile.lens;
    document.body.dataset.vTheme=String(fields.theme||"orbit");
    history.replaceState(null,"",location.pathname);workspace(r.profile.name);
  }catch(err){document.getElementById("v-result")!.textContent=String(err);}
  finally{busy=false;}
 };
}
