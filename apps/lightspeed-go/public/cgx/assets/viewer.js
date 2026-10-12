import {PUBLIC_OBJECT,DOOM_PROOF,selectRoute,walkSlice,handshake,applySparseDelta,evaluatePrint,numericSlice,PUBLIC_SCHEMA} from "./core.js";
const route=selectRoute(document.body.dataset.space||location.pathname);
const labels={overview:"Universal Operating Model",fs:"FileSpace",ds:"DataSpace",ps:"PrintSpace",doom:"DOOM benchmark"};
const $=id=>document.getElementById(id);
let state={sequence:0,root:"demo-state-0",value:"idle"};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const link=(id,name)=>'<a href="/cgx/'+(id==="overview"?"":id+"/")+'"'+(route===id?' aria-current="page"':'')+'>'+name+'</a>';
const button=(id,text,cls="")=>'<button type="button" class="button '+cls+'" id="'+id+'">'+text+'</button>';
const panel=(title,body,eyebrow="PUBLIC SAFE / SOURCE BOUND")=>'<section class="panel"><p class="eyebrow">'+eyebrow+'</p><h2>'+title+'</h2>'+body+'</section>';
const receipt=entry=>{const x=$("receipt");if(x)x.textContent=JSON.stringify({schema:PUBLIC_SCHEMA,object_id:PUBLIC_OBJECT.object_id,evidence:"SYNTHETIC",authenticated:false,canonical_promotion_authorized:false,...entry},null,2);};
document.title="UniSpace | "+labels[route]+" · CGX";
document.body.innerHTML='<div class="aura"></div><div class="container"><header class="mast"><a class="brand" href="/cgx/"><strong class="glyph">U</strong><span><strong>UniSpace</strong><small>Powered by CGX</small></span></a><span class="publictag">PUBLIC · INTERACTIVE DEMONSTRATION</span></header><nav class="nav" aria-label="UniSpace sections">'+link("overview","Overview")+link("fs","FileSpace")+link("ds","DataSpace")+link("ps","PrintSpace")+link("doom","DOOM")+'</nav><section class="hero"><p class="eyebrow">RÖMER INDUSTRIES · UNIVERSAL</p><h1>'+labels[route]+'</h1><p>One source-bound CGX object. Configurable interpretations. Local-first, evidence-aware interaction.</p><div class="pillrow"><span>Identity</span><span>Geometry</span><span>Semantic views</span><span>State + DBR</span><span>Frontier</span></div></section><main id="surface"></main><footer><strong>UniSpace / CGX</strong><p>Public synthetic examples only. Not a private LS GO operator session, source registry, live peer, or qualified physical control.</p><a href="https://romer.industries/" target="_top" rel="noreferrer">Römer Industries ↗</a></footer></div>';
function prism(){
const palettes=["#648ed9","#42bba5","#a28ad8","#d6a262"];
const planes=PUBLIC_OBJECT.slices.map((x,i)=>'<g><polygon points="60,'+(30+i*53)+' 238,'+(6+i*53)+' 348,'+(49+i*53)+' 168,'+(74+i*53)+'" fill="'+palettes[i]+'" fill-opacity=".36" stroke="'+palettes[i]+'" stroke-width="2" data-plane="'+x.id+'"></polygon><text x="201" y="'+(44+i*53)+'" class="svgtxt">'+esc(x.label)+'</text></g>').join("");
return panel("Source prism · one object, many lenses",'<div class="prismgrid"><svg viewBox="0 0 400 285" role="img" aria-label="Four stacked interpretations of the same object">'+planes+'</svg><div class="controls"><label for="slice">Object slice</label><select id="slice">'+PUBLIC_OBJECT.slices.map(x=>'<option value="'+x.id+'">'+esc(x.label)+'</option>').join("")+'</select><label for="lens">Interpretation</label><select id="lens"><option value="geometry">Geometry</option><option value="identity">Identity</option><option value="evidence">Evidence</option><option value="frontier">Unresolved frontier</option></select><pre class="output" id="prism-out"></pre></div></div>');
}
function bindPrism(){
const update=()=>{const id=$("slice").value,lens=$("lens").value,row=PUBLIC_OBJECT.slices.find(x=>x.id===id),chain=walkSlice(PUBLIC_OBJECT,id),num=numericSlice(id);
document.querySelectorAll("[data-plane]").forEach(x=>x.classList.toggle("selected",x.dataset.plane===id));
$("prism-out").textContent=lens==="frontier"?"UNKNOWN: there is no verified interpretation dictionary for this frontier.":lens==="identity"?"Object_ID: "+PUBLIC_OBJECT.object_id+"\nPath: "+chain.join(" → "):lens==="evidence"?"Source class: "+PUBLIC_OBJECT.authority+"\nEvidence: "+PUBLIC_OBJECT.evidence+"\nOwner: "+PUBLIC_OBJECT.owner_ref:"Value: "+num.value+" "+num.unit+"\nModel reference: "+row.ref;};
$("slice").addEventListener("change",update);$("lens").addEventListener("change",update);update();
}
function overview(){
$("surface").innerHTML='<div class="cards">'+[
["fs","FileSpace","Objects · provenance · reversible source and frontier"],
["ds","DataSpace","Scoped context · sparse deltas · device lens negotiation"],
["ps","PrintSpace","Conditional fabrication · metrology · safe-state evidence"],
["doom","DOOM","Full offline executable · genuine 15-layer reconstruction"]
].map(x=>'<a class="tile" href="/cgx/'+x[0]+'/"><span class="eyebrow">'+x[0].toUpperCase()+'</span><h2>'+x[1]+'</h2><p>'+x[2]+'</p><strong>Explore →</strong></a>').join("")+'</div>'+prism()+panel("Current proof boundary",'<p>In-browser demonstrations are local simulations. DOOM has separate real-engine test evidence, but a public CGX handshake, signed transport and physical printing are not established by this page.</p>');
bindPrism();
}
function fs(){
$("surface").innerHTML=prism()+panel("Native FileSpace object view",'<p>The same canonical identity is exposed as a folder-like tree, geometry slice or provenance lens. No secondary database or owner is created.</p><div class="tree">'+PUBLIC_OBJECT.slices.map(x=>'<button type="button" data-slice="'+x.id+'">'+(x.parent?"└ ":"▣ ")+esc(x.label)+'</button>').join("")+'</div><pre class="output" id="filesrc"></pre>'+button("copy","Copy public fixture JSON"));
bindPrism();
$("filesrc").textContent=JSON.stringify({object_id:PUBLIC_OBJECT.object_id,source_root:PUBLIC_OBJECT.roots.source,licence:PUBLIC_OBJECT.licence,evidence:PUBLIC_OBJECT.evidence},null,2);
document.querySelectorAll("[data-slice]").forEach(x=>x.addEventListener("click",()=>{$("slice").value=x.dataset.slice;$("slice").dispatchEvent(new Event("change"))}));
$("copy").addEventListener("click",async()=>{try{await navigator.clipboard.writeText($("filesrc").textContent);$("copy").textContent="Copied"}catch{$("copy").textContent="Select text manually"}});
}
function ds(){
$("surface").innerHTML='<div class="twocol">'+panel("Automatic local handshake",'<p>Negotiate a renderer against available cached definitions. Device type cannot grant access.</p><label for="device">Simulated device</label><select id="device"><option value="desktop_browser">Desktop browser</option><option value="mobile_touch">Touch / mobile</option><option value="machine">Limited machine</option></select><label for="view">Required view</label><select id="view"><option value="metric">Metric</option><option value="tree">Tree</option><option value="graph">Graph</option><option value="process">Process (review only)</option></select><label class="check"><input id="cached" type="checkbox" checked> Static source locally cached (simulated)</label>'+button("resolve","Resolve", "primary")+'<pre class="output" id="handshake"></pre>')+panel("Local sparse state model",'<p>Compare known context, preserve unknowns, and replay changed states locally. No actual network transfer occurs.</p><label for="value">Next state</label><select id="value"><option value="idle">Idle</option><option value="moving">Moving</option><option value="unknown">Unknown</option></select>'+button("step","Apply simulated delta")+button("reset","Reset simulation","ghost")+'<pre class="output" id="delta"></pre>')+'</div>'+panel("Untrusted local receipt",'<pre class="output" id="receipt"></pre>');
const resolve=()=>{const r=handshake({device:$("device").value,requested:$("view").value,cached:$("cached").checked});$("handshake").textContent=r.status+"\nAuthority / identity: UNVERIFIED\nNetwork transfer: NONE";receipt({status:r.status,device:r.device||$("device").value});};
const step=()=>{const r=applySparseDelta(state,{sequence:state.sequence+1,prior_root:state.root,value:$("value").value});if(r.next)state=r.next;$("delta").textContent=r.status+"\nSequence: "+state.sequence+"\nState: "+state.value+"\nChanged fields: "+(r.applied??0);receipt({status:r.status,simulation_state:state});};
$("resolve").addEventListener("click",resolve);$("device").addEventListener("change",resolve);$("view").addEventListener("change",resolve);
$("step").addEventListener("click",step);$("reset").addEventListener("click",()=>{state={sequence:0,root:"demo-state-0",value:"idle"};$("delta").textContent="Sequence 0 · idle";receipt({status:"RESET_LOCAL_ONLY"});});resolve();$("delta").textContent="Sequence 0 · idle";
}
function ps(){
$("surface").innerHTML='<div class="twocol">'+panel("Conditional interface evaluator",'<p>The direction matters: X → Y does not imply Y → X. These are illustrative, not qualified material properties.</p><label for="direction">Material sequence</label><select id="direction"><option value="polymer-to-metal">Polymer → metal</option><option value="metal-to-polymer">Metal → polymer</option></select><label class="check"><input id="inert" type="checkbox"> Controlled atmosphere assumed (simulation)</label><label class="check"><input id="verified" type="checkbox"> Interface compatibility assumed (simulation)</label>'+button("evaluate","Evaluate CAN IF","primary")+'<pre class="output" id="process"></pre>')+panel("Independent physical proof",'<p>Digital geometry, exact model calculations and visual representations cannot qualify a manufacturing result. Actual machine identity, calibration, environmental control, materials evidence and measured coupons are still required.</p><div class="ladder"><span>CONCEPT</span><span>COMPUTED</span><span>BENCH</span><span>FIELD</span><span>REVIEWED</span><span>RELEASED</span></div><p class="warn">PHYSICAL TEST: NOT RUN<br>ACTUATION: DISABLED</p>')+'</div>'+panel("Untrusted local receipt",'<pre class="output" id="receipt"></pre>');
const evaluate=()=>{const r=evaluatePrint({direction:$("direction").value,inert:$("inert").checked,interfaceQualified:$("verified").checked});$("process").textContent=r.status+"\nRequired: "+r.requirements.join("; ")+"\n"+r.environment+"\nPhysical acceptance: NOT RUN";receipt({status:r.status,route:r});};
$("evaluate").addEventListener("click",evaluate);$("direction").addEventListener("change",evaluate);evaluate();
}
function doom(){
$("surface").innerHTML='<div class="twocol">'+panel("A complete offline game",'<p>A genuine Chocolate Doom WebAssembly engine and Freedoom Phase 1 asset set were packaged as a playable single file. In CI, the 15-layer variant reassembled the WAD and changed rendered gameplay in response to input.</p><div class="metrics"><div><strong>28.80 MB</strong><small>WAD only</small></div><div><strong>22.02 MB</strong><small>Full one-file game</small></div><div><strong>22.46 MB</strong><small>15-layer full game</small></div></div><a class="button primary" href="https://romer-cgx-doom.vercel.app/" target="_blank" rel="noopener noreferrer">Open separately hosted DOOM project ↗</a><p class="small">The linked site's precise deployed artefact is not certified by this page; use the recorded CI run for benchmark verification.</p>')+panel("Inspect the N=15 decode profile",'<p>Every slice contains actual original bytes, not information generated by a short geometric locator.</p><label for="layer">Selected WAD byte range</label><input id="layer" type="range" min="1" max="15" value="1" step="1"><pre class="output" id="doom-out"></pre><p>The engine currently hydrates the whole reconstructed WAD. True selective level loading is a separate frontier.</p>')+'</div>'+panel("Independent proof record",'<p>First-install overhead is paid once; minimal input updates can be smaller only after matching static definitions are present.</p><a href="https://github.com/achillesromer-coder/LightSpeed/actions/runs/38193600179" target="_blank" rel="noreferrer">Open actual 15-layer test evidence ↗</a>');
const render=()=>{const i=Number($("layer").value),n=Math.ceil(DOOM_PROOF.raw_wad_bytes/15),a=(i-1)*n,b=Math.min(DOOM_PROOF.raw_wad_bytes,i*n);
$("doom-out").textContent="Layer "+i+"/15\nOriginal offsets: "+a.toLocaleString()+"–"+(b-1).toLocaleString()+"\nBytes: "+(b-a).toLocaleString()+"\nWhole source IWAD still required.";};
$("layer").addEventListener("input",render);render();
}
({overview,fs,ds,ps,doom}[route]||overview)();
function height(){
if(parent===window)return;let o;try{o=new URL(document.referrer).origin}catch{return}
if(!["https://romer.industries","https://www.romer.industries"].includes(o))return;
parent.postMessage({type:"unispace:height",height:Math.max(document.documentElement.scrollHeight,650)},o);
}
if(typeof ResizeObserver!=="undefined")new ResizeObserver(height).observe(document.body);
addEventListener("load",height);
