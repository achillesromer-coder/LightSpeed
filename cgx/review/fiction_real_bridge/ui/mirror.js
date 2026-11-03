"use strict";
/* CGX cross-world review projection: no network except same-origin graph.json, no writes. */
const $=id=>document.getElementById(id);
const state={graph:null,selected:"film-red",lens:"both",lookup:null};
const mapping=[
 ["film-green","mention:hackers-books-green","Green Book","Exact edition unresolved"],
 ["film-orange","mention:hackers-books-orange","Orange Book","A real DoD standard"],
 ["film-pink","mention:hackers-books-pink","Pink-Shirt Book","A real IBM PC guide"],
 ["film-devil","mention:hackers-books-devil","Devil Book","A real BSD systems book"],
 ["film-dragon","mention:hackers-books-dragon","Dragon Book","A real compiler textbook"],
 ["film-red","mention:hackers-books-red","Red Book","Two real references conflated"]
];
const norm=s=>String(s||"").toLowerCase().normalize("NFKC").replace(/[^a-z0-9]+/g," ").trim().replace(/\s+/g," ");
const make=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=String(text);return n};
const add=(parent,tag,cls,text)=>{const n=make(tag,cls,text);parent.appendChild(n);return n};
const set=(id,value)=>$(id).textContent=String(value??"—");
const allNodes=()=>state.graph?.nodes||[];
const findNode=id=>allNodes().find(n=>n.id===id);
const findMention=key=>state.graph?.mentions.find(x=>x.identity_key===key);
const sources=()=>Object.fromEntries((state.graph?.sources||[]).map(s=>[s.id,s]));
const qualifiedStatus=r=>r.status||"unverified";
const title=n=>n?.title||"Unknown referent";
const description=n=>{
 if(n?.kind==="constructed_language")return "Created for a fictional world, with documented grammar and real human use. Speaking it does not make the fictional species real.";
 if(n?.kind==="fictional_entity")return "Exists as a narrative object; related published works are distinct empirical artifacts.";
 if(n?.kind==="documented_standard")return "Real historical technical standard. Historic existence does not imply current operational applicability.";
 if(n?.kind==="creative_work")return "Real creative work representing a fictional setting.";
 if(n?.kind==="real_work")return "Published material with independent bibliographic evidence; textual reproduction requires separate rights.";
 return "Proposed candidate, not an accepted native CGX referent.";
};
const allowLens=n=>{
 if(state.lens==="both")return true;
 if(state.lens==="empirical")return n.kind!=="fictional_entity";
 return n.kind==="fictional_entity"||n.kind==="constructed_language"||(n.kind==="creative_work"&&n.facets.fictional_setting===true);
};
function resolveMention(m){
 const by=Object.fromEntries(allNodes().map(n=>[n.id,n]));
 const candidates=m.candidate_ids.map(id=>by[id]).filter(Boolean);
 const status=m.status==="unresolved"?"frontier":m.status==="ambiguous"||candidates.length>1?"ambiguous":"review-supported";
 return {title:m.label,status,candidates,mentions:[m],sourceIds:m.source_ids,
         reason:status==="frontier"?"The reference is confirmed in the scene, but its precise real-world work or edition has not been independently identified. This is not proof that the book is fictional.":
                status==="ambiguous"?"Multiple distinct real-world references fit the scene language. Preserve both and request stronger edition/prop evidence.":"The story references a source-qualified real-world work. The fictional scene and the published document remain different kinds of objects."};
}
function resolveTitle(query,{preferContext=false}={}){
 const q=norm(query);
 if(!q)return {title:"Empty query",status:"frontier",candidates:[],mentions:[],sourceIds:[],reason:"Enter a title or alias."};
 const direct=allNodes().filter(n=>[n.title,...n.aliases].some(a=>norm(a)===q));
 const mentions=state.graph.mentions.filter(m=>[m.label,...m.aliases].some(a=>norm(a)===q));
 if(direct.length && !preferContext){
  return {title:query,status:direct.length===1?"review-supported":"ambiguous",candidates:direct,mentions:[],
         sourceIds:[...new Set(direct.flatMap(n=>n.source_ids))],
         reason:direct.length>1?"The same name is shared by distinct real and fictional referents. They must not be merged by alias.":
         "A source-qualified candidate identity was found. All other narrative uses remain independently scoped."};
 }
 if(mentions.length){
  const unique=[...new Set(mentions.flatMap(x=>x.candidate_ids))].map(findNode).filter(Boolean);
  const frontier=mentions.some(m=>m.status==="unresolved");
  return {title:query,status:frontier&&unique.length===0?"frontier":unique.length>1?"ambiguous":"review-supported",
          candidates:unique,mentions,sourceIds:[...new Set(mentions.flatMap(m=>m.source_ids))],
          reason:frontier&&unique.length===0?"No exact referent established. Retain as an unresolved frontier.":unique.length>1?"Competing referents and scene contexts require an explicit decision.":"A scene reference is supported by one or more external evidence records."};
 }
 return {title:query,status:"frontier",candidates:[],mentions:[],sourceIds:[],reason:"Not found in this bounded corpus. Neither fictional status nor nonexistence is inferred; request further source discovery."};
}
function choose(scenario){
 if(!state.graph)return;
 state.selected=scenario;state.lookup=null;
 if(scenario.startsWith("film-")){
  const row=mapping.find(x=>x[0]===scenario);
  state.lookup=resolveMention(findMention(row[1]));
 }else if(scenario==="hitchhikers")state.lookup=resolveTitle("The Hitchhiker's Guide to the Galaxy");
 else if(scenario==="klingon")state.lookup=resolveTitle("Klingon language");
 else if(scenario==="unknown")state.lookup=resolveTitle("Imaginary Theorem Manual No. 3");
 else if(scenario.startsWith("entity:")){
  const n=findNode(scenario.slice(7));
  state.lookup=n?{title:n.title,status:"review-supported",candidates:[n],mentions:[],sourceIds:n.source_ids,
    reason:"One stable referent, with reusable domain-specific projections. Following it does not create a duplicate object."}:resolveTitle("missing");
 }
 document.querySelectorAll("[data-case]").forEach(b=>b.classList.toggle("active",b.dataset.case===scenario));
 render();history.replaceState(null,"","?case="+encodeURIComponent(scenario));
}
function render(){
 const r=state.lookup;
 if(!r)return;
 set("active-title",r.title);set("resolve-explainer",r.reason);
 const st=$("resolve-status");st.className="tag "+(r.status==="ambiguous"?"ambiguous":r.status==="frontier"?"frontier":"");st.textContent=r.status.toUpperCase();
 set("origin-text",r.mentions.length?r.mentions.map(m=>m.label).join(" · "):state.selected.startsWith("entity:")?"Resolved object":"Name / alias query");
 set("origin-sub",r.mentions.length?"Narrative occurrence · story context":"Contextual semantic lookup");
 set("relation-text",r.status==="frontier"?"UNRESOLVED":r.status==="ambiguous"?"CANDIDATE LINKS":"SOURCED RELATION");
 set("target-text",r.candidates.length?r.candidates.length+" referent"+(r.candidates.length===1?"":"s"):"No confirmed referent");
 const visible=r.candidates.filter(allowLens);
 set("candidate-count",visible.length+" visible / "+r.candidates.length+" total");
 const parent=$("candidates");parent.replaceChildren();
 for(const n of visible){
  const card=add(parent,"article","candidate"),d=add(card,"div");
  add(d,"h4","",title(n));add(d,"p","",description(n));add(d,"code","candidate-id",n.id);
  const fields=add(d,"div","candidate-meta");
  add(fields,"span","",n.kind.replaceAll("_"," "));
  add(fields,"span","",n.owner_domain+" domain");
  if(n.facets.published_year)add(fields,"span","",n.facets.published_year);
  if(n.facets.fictional_origin)add(fields,"span","","Fictional origin");
  if(n.facets.real_world_usage)add(fields,"span","","Real-world use");
  const btn=add(card,"button","","Follow identity");btn.type="button";btn.addEventListener("click",()=>choose("entity:"+n.id));
 }
 if(!visible.length){
  add(parent,"p","empty",r.candidates.length?"This lens hides the resolved referents. Switch to All referents to inspect them; nothing was deleted.":"No confirmed object can be linked. Maintain the frontier and seek independent evidence before assuming a fictional placeholder.");
 }
 renderEdges(r);renderEvidence(r);
}
function renderEdges(r){
 const container=$("edges");container.replaceChildren();
 const starts=new Set([...r.mentions.map(x=>x.id),...r.candidates.map(x=>x.id)]);
 let list=state.graph.edges.filter(e=>starts.has(e.from)||starts.has(e.to));
 if(!list.length){add(container,"p","muted","No outgoing qualified bridge for this selection.");return}
 for(const edge of list.slice(0,18)){
  const row=add(container,"div","edge-row");
  const body=add(row,"div");
  add(body,"strong","",edge.type.replaceAll("_"," "));
  const target=findNode(edge.to),from=findNode(edge.from);
  const descr=target?.title||(from?.title||"Narrative reference");
  add(body,"p","",descr+" · "+edge.epistemic_state+" · "+edge.claim_scope+" · "+edge.source_ids.length+" sources");
  if(target){const btn=add(row,"button","","Follow ↗");btn.addEventListener("click",()=>choose("entity:"+target.id));}
 }
}
function renderEvidence(r){
 const ids=new Set(r.sourceIds);
 for(const n of r.candidates)for(const id of n.source_ids)ids.add(id);
 for(const e of state.graph.edges){
  if(r.mentions.some(m=>m.id===e.from)||r.candidates.some(n=>n.id===e.from||n.id===e.to))
   for(const id of e.source_ids)ids.add(id);
 }
 const container=$("evidence");container.replaceChildren();const sourceIndex=sources();
 if(!ids.size){add(container,"p","empty","No available source locators yet. Source discovery required.");return}
 for(const id of [...ids].sort()){
  const s=sourceIndex[id];if(!s)continue;
  const card=add(container,"div","evidence-card");
  add(card,"strong","",id);add(card,"small","",s.role);
  add(card,"small","",s.sha256===null?"Source content not hydrated · locator only":"Source bytes available");
  const a=add(card,"a","",s.url);a.href=s.url;a.rel="noopener noreferrer";a.target="_blank";
 }
}
function addFilmScenarios(){
 const parent=$("film-list");parent.replaceChildren();
 for(const [id,,label,description] of mapping){
  const button=add(parent,"button","scenario");button.type="button";button.dataset.case=id;
  add(button,"strong","",label);add(button,"small","",description);
  button.addEventListener("click",()=>choose(id));
 }
}
async function init(){
 const r=await fetch("./graph.json",{cache:"no-store"});
 if(!r.ok)throw Error("Graph endpoint HTTP "+r.status);
 const g=await r.json();
 if(g.schema!=="CGX-FICTION-REAL-MIRROR/0.1"||g.parent!=="cgx:root:cognigrex"||g.native_admission!==false||
    !Array.isArray(g.nodes)||g.nodes.length!==13||g.mentions.length!==7||g.edges.length!==12)
   throw Error("Unexpected mirror graph structure; fail closed");
 state.graph=g;set("stat-nodes",g.nodes.length);set("stat-mentions",g.mentions.length);
 set("stat-edges",g.edges.length);set("stat-sources",g.sources.length);
 set("graph-hash","SHA-256 "+g.graph_sha256.slice(0,24)+"…");
 set("load-state","LOCAL REVIEW · NO NATIVE CGX WRITES");
 addFilmScenarios();
 const want=new URLSearchParams(location.search).get("case");
 choose(want&&(mapping.some(x=>x[0]===want)||["hitchhikers","klingon","unknown"].includes(want)||want.startsWith("entity:"))?want:"film-red");
}
$("lookup-form").addEventListener("submit",e=>{
 e.preventDefault();if(!state.graph)return;
 const q=$("lookup").value.trim();if(!q)return;
 state.selected="manual";state.lookup=resolveTitle(q);
 document.querySelectorAll("[data-case]").forEach(b=>b.classList.remove("active"));render();
 history.replaceState(null,"","?query="+encodeURIComponent(q));
});
$("lens").addEventListener("change",e=>{state.lens=e.target.value;if(state.lookup)render()});
document.querySelectorAll("[data-case]").forEach(b=>b.addEventListener("click",()=>choose(b.dataset.case)));
const requestedQuery=new URLSearchParams(location.search).get("query");
init().then(()=>{
 if(requestedQuery!==null && requestedQuery.trim()){
  $("lookup").value=requestedQuery;
  state.selected="manual";state.lookup=resolveTitle(requestedQuery);render();
  history.replaceState(null,"","?query="+encodeURIComponent(requestedQuery));
 }
}).catch(e=>{set("load-state","SOURCE GRAPH HOLD · "+e.message);$("candidates").replaceChildren(add(document.createElement("div"),"p","empty",e.message))});