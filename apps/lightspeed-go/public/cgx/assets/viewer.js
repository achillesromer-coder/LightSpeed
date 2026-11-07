import {PUBLIC_OBJECT,DOOM_PROOF,SYNTHETIC_CUBE,sectionConvexMesh,selectRoute,walkSlice,handshake,applySparseDelta,evaluatePrint,numericSlice,PUBLIC_SCHEMA,PUBLIC_CGX_ATLAS,projectCgxOrbit} from "./core.js";
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

function orbitPanel(){
  const options=PUBLIC_CGX_ATLAS.nodes.map(n=>'<option value="'+esc(n.id)+'">'+esc(n.label)+'</option>').join("");
  return panel("FamilySpace · 360° orbit atlas",
    '<p>Rotate the source-bound family illustration to explore depth and hierarchy. Amber denotes fractal family mass; blue is a sealed dedicated space; green denotes an open synthetic example. These colours do not grant rights.</p>'+
    '<div class="orbit-layout"><div class="orbit-stage"><svg id="orbit-view" viewBox="0 0 760 370" tabindex="0" role="img" aria-label="Interactive perspective view of synthetic CGX family nodes. Use arrow keys to rotate, plus and minus to zoom."></svg>'+
    '<p class="orbit-hint">Drag / swipe to orbit · arrow keys to rotate · + / − to zoom</p></div>'+
    '<div class="orbit-controls"><label for="orbit-focus">Focus node</label><select id="orbit-focus">'+options+'</select>'+
    '<div class="orbit-actions">'+button("orbit-left","↶ Left")+button("orbit-right","Right ↷")+button("orbit-up","Up")+button("orbit-down","Down")+button("orbit-in","Zoom +")+button("orbit-out","Zoom −")+button("orbit-reset","Reset")+'</div>'+
    '<pre class="output orbit-readout" id="orbit-readout" aria-live="polite"></pre>'+
    '<div class="orbit-legend"><span><i class="orbit-key fractal"></i>Fractal mass</span><span><i class="orbit-key dedicated"></i>Dedicated / sealed</span><span><i class="orbit-key open"></i>Open demo</span></div></div></div>'+
    '<p class="small">Synthetic geometry only · PUBLIC SURFACE viewpoint. Private governance height/depth, original content, precise geospatial coordinates, live access grants and native minted identities are not projected. The authorised owner workspace is a separate security boundary.</p>',
    "PUBLIC R3 DEMONSTRATION · NOT NATIVE ADMISSION");
}
function bindOrbit(){
  const svg=$("orbit-view"),focus=$("orbit-focus"),out=$("orbit-readout");
  if(!svg||!focus||!out)return;
  let yaw=.65,pitch=.3,zoom=1,down=null;
  const render=()=>{
    const result=projectCgxOrbit({yaw,pitch,zoom});
    if(result.status!=="SYNTHETIC_ORBIT_PROJECTION_ONLY"){
      out.textContent="Orbit frame unavailable · unverified";return;
    }
    const f=focus.value;
    const node=PUBLIC_CGX_ATLAS.nodes.find(x=>x.id===f);
    const segments=result.edges.map(e=>'<line x1="'+e.x1.toFixed(2)+'" y1="'+e.y1.toFixed(2)+'" x2="'+e.x2.toFixed(2)+'" y2="'+e.y2.toFixed(2)+'" stroke="#ed9c45" stroke-opacity="'+e.opacity.toFixed(2)+'" stroke-width="2.2" class="orbit-edge"/>').join("");
    const dots=result.nodes.map(n=>'<g class="orbit-node'+(n.id===f?' orbit-selected':'')+'" data-orbit-node="'+esc(n.id)+'">'+
      '<circle cx="'+n.x.toFixed(2)+'" cy="'+n.y.toFixed(2)+'" r="'+(n.radius*2.25).toFixed(2)+'" fill="'+n.color+'" opacity=".095"/>'+
      '<circle cx="'+n.x.toFixed(2)+'" cy="'+n.y.toFixed(2)+'" r="'+n.radius.toFixed(2)+'" fill="'+n.color+'" fill-opacity="'+n.opacity.toFixed(2)+'" stroke="'+n.color+'" stroke-width="'+(n.id===f?3:1.2)+'"/>'+
      '<text x="'+n.x.toFixed(2)+'" y="'+(n.y-n.radius-14).toFixed(2)+'" text-anchor="middle">'+esc(n.label)+'</text></g>').join("");
    svg.innerHTML='<g class="orbit-background"><circle cx="380" cy="185" r="159" fill="none" stroke="#385b71" stroke-dasharray="3 10"/><ellipse cx="380" cy="185" rx="230" ry="93" fill="none" stroke="#335262" stroke-dasharray="3 10"/></g>'+segments+dots;
    const kind=node?.layer==="dedicated"?"SEALED · ACCESS NOT CONFERRED":node?.layer==="open"?"OPEN SYNTHETIC DEMO":"FRACTAL FAMILY · SOURCE REVIEW";
    out.textContent="Focus: "+(node?.label||"Unknown")+"\nClass: "+kind+
      "\nAzimuth: "+Math.round(((result.yaw%(2*Math.PI)+2*Math.PI)%(2*Math.PI))*180/Math.PI)+"° · Zoom: "+zoom.toFixed(2)+"×"+
      "\nOriginal source: NOT HYDRATED\nNative Object_ID: NOT MINTED";
  };
  const rotate=(x,y)=>{yaw+=x;pitch=Math.max(-1.4,Math.min(1.4,pitch+y));render();};
  const scale=n=>{zoom=Math.max(.55,Math.min(2.5,Math.round((zoom+n)*100)/100));render();};
  const actions={
    "orbit-left":()=>rotate(-.18,0),"orbit-right":()=>rotate(.18,0),
    "orbit-up":()=>rotate(0,-.14),"orbit-down":()=>rotate(0,.14),
    "orbit-in":()=>scale(.15),"orbit-out":()=>scale(-.15),
    "orbit-reset":()=>{yaw=.65;pitch=.3;zoom=1;focus.value="root";render();}
  };
  Object.entries(actions).forEach(([id,cb])=>$(id).addEventListener("click",cb));
  focus.addEventListener("change",render);
  svg.addEventListener("keydown",e=>{
    const map={ArrowLeft:actions["orbit-left"],ArrowRight:actions["orbit-right"],
      ArrowUp:actions["orbit-up"],ArrowDown:actions["orbit-down"],
      "+":actions["orbit-in"],"=":actions["orbit-in"],"-":actions["orbit-out"],Home:actions["orbit-reset"]};
    if(map[e.key]){e.preventDefault();map[e.key]();}
  });
  svg.addEventListener("pointerdown",e=>{
    down={x:e.clientX,y:e.clientY,id:e.pointerId};
    if(svg.setPointerCapture)svg.setPointerCapture(e.pointerId);
  });
  svg.addEventListener("pointermove",e=>{
    if(!down||down.id!==e.pointerId)return;
    const dx=e.clientX-down.x,dy=e.clientY-down.y;
    down={x:e.clientX,y:e.clientY,id:e.pointerId};rotate(dx*.009,dy*.009);
  });
  const stop=()=>{down=null;};
  svg.addEventListener("pointerup",stop);svg.addEventListener("pointercancel",stop);
  svg.addEventListener("wheel",e=>{e.preventDefault();scale(e.deltaY>0?-.1:.1);},{passive:false});
  render();
}

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
$("surface").innerHTML=orbitPanel()+'<div class="cards">'+[
["fs","FileSpace","Objects · provenance · reversible source and frontier"],
["ds","DataSpace","Scoped context · sparse deltas · device lens negotiation"],
["ps","PrintSpace","Conditional fabrication · metrology · safe-state evidence"],
["doom","DOOM","Full offline executable · genuine 15-layer reconstruction"]
].map(x=>'<a class="tile" href="/cgx/'+x[0]+'/"><span class="eyebrow">'+x[0].toUpperCase()+'</span><h2>'+x[1]+'</h2><p>'+x[2]+'</p><strong>Explore →</strong></a>').join("")+'</div>'+prism()+panel("Current proof boundary",'<p>In-browser demonstrations are local simulations. DOOM has separate real-engine test evidence, but a public CGX handshake, signed transport and physical printing are not established by this page.</p>');
bindPrism();bindOrbit();
}
function planeSectionPanel(){
return panel("Exact 2D cut of a synthetic 3D vertex mesh",'<p>Finite indexed vertices and edges; this is a geometric derivation, not compression, source evidence, or a licensed Archimedean template.</p><label for="cut-axis">Plane normal</label><select id="cut-axis"><option value="z">XY (z constant)</option><option value="x">YZ (x constant)</option><option value="y">XZ (y constant)</option></select><label for="cut-offset">Plane offset (m)</label><input id="cut-offset" type="number" value="0" step="0.25"><pre class="output" id="cut-result"></pre>');
}
function bindPlaneSection(){
 const render=()=>{
  const axis=$("cut-axis").value,normal=axis==="z"?[0,0,1]:axis==="x"?[1,0,0]:[0,1,0];
  const offset=Number($("cut-offset").value);
  const result=sectionConvexMesh(SYNTHETIC_CUBE,{normal,offset});
  $("cut-result").textContent=JSON.stringify(result,null,2);
 };
 $("cut-axis").addEventListener("change",render);
 $("cut-offset").addEventListener("input",render);
 render();
}
function fs(){
$("surface").innerHTML=orbitPanel()+prism()+planeSectionPanel()+panel("Native FileSpace object view",'<p>The same canonical identity is exposed as a folder-like tree, geometry slice or provenance lens. No secondary database or owner is created.</p><div class="tree">'+PUBLIC_OBJECT.slices.map(x=>'<button type="button" data-slice="'+x.id+'">'+(x.parent?"└ ":"▣ ")+esc(x.label)+'</button>').join("")+'</div><pre class="output" id="filesrc"></pre>'+button("copy","Copy public fixture JSON"));
bindPrism();
bindOrbit();
bindPlaneSection();
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
$("surface").innerHTML='<div class="twocol">'+panel("A complete offline game",'<p>A genuine Chocolate Doom WebAssembly engine and Freedoom Phase 1 asset set were packaged as a playable single file. In CI, the 15-layer variant reassembled the WAD and changed rendered gameplay in response to input.</p><div class="metrics"><div><strong>28.80 MB</strong><small>WAD only</small></div><div><strong>22.02 MB</strong><small>Full one-file game</small></div><div><strong>22.46 MB</strong><small>15-layer full game</small></div></div><a class="button primary" href="https://romer-cgx-doom.vercel.app/" target="_blank" rel="noopener noreferrer">Open separately hosted DOOM project ↗</a><p class="small">The linked site&#39;s precise deployed artefact is not certified by this page; use the recorded CI run for benchmark verification.</p>')+panel("Inspect the N=15 decode profile",'<p>Every slice contains actual original bytes, not information generated by a short geometric locator.</p><label for="layer">Selected WAD byte range</label><input id="layer" type="range" min="1" max="15" value="1" step="1"><pre class="output" id="doom-out"></pre><p>The engine currently hydrates the whole reconstructed WAD. True selective level loading is a separate frontier.</p>')+'</div>'+panel("Independent proof record",'<p>First-install overhead is paid once; minimal input updates can be smaller only after matching static definitions are present.</p><a href="https://github.com/achillesromer-coder/LightSpeed/actions/runs/38193600179" target="_blank" rel="noreferrer">Open actual 15-layer test evidence ↗</a>');
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
