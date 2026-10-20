// PUBLIC DEMONSTRATION ONLY. No internal LS GO bridge, secrets, privileged assets, or private object IDs.
export const PUBLIC_SCHEMA = "unispace-cgx-public-demonstration/1";
export const ROUTES = Object.freeze(["overview","fs","ds","ps","doom"]);
export const PUBLIC_OBJECT = Object.freeze({
  object_id: "PUBLIC-DEMO/UNISPACE/PRISM-01",
  licence: "Original synthetic demonstration; not an exported internal CGX object",
  authority: "PUBLIC_SAFE_SYNTHETIC",
  evidence: "SIMULATED",
  owner_ref: "UniSpace example publisher",
  roots: { source:"demo-source-r1", geometry:"demo-geometry-r1", semantic:"demo-semantics-r1", model:"demo-model-r1" },
  slices: [
    {id:"root",parent:null,label:"One source object",ref:"demo-source-r1",unit:"none",value:1},
    {id:"geometry",parent:"root",label:"Spatial section",ref:"demo-geometry-r1",unit:"m",value:12},
    {id:"material",parent:"root",label:"Material section",ref:"demo-material-r1",unit:"kg",value:4},
    {id:"state",parent:"root",label:"Mutable observation",ref:"demo-state-r1",unit:"index",value:0}
  ],
  render_views:["filespace-tree","topology-graph","evidence-claim","metric","process-route"],
});
export const DOOM_PROOF = Object.freeze({
  title:"Freedoom Phase 1 · Chocolate Doom WASM",
  raw_wad_bytes:28795076,
  monolithic_html_bytes:22018509,
  sharded_html_bytes:22462117,
  n_layers:15,
  evidence:"ACTUAL_ENGINE_AUTOMATED / USER-REPORTED_MONOLITHIC_RUN",
  note:"First-download compression is conventional; 15 slices are real byte ranges, not source-free reconstruction."
});
export const DEVICE_KINDS = Object.freeze(["desktop_browser","mobile_touch","machine"]);
export const VIEW_KINDS = Object.freeze(["tree","metric","graph","process"]);

export function selectRoute(raw) {
  const x=String(raw||"").toLowerCase().replace(/\/+$/,"").split("/").pop();
  return ROUTES.includes(x) ? x : "overview";
}
export function walkSlice(model,id) {
  if(!model || !Array.isArray(model.slices)) return null;
  const seen=new Set(),byId=new Map(model.slices.map(x=>[x.id,x])),chain=[];
  let node=byId.get(id);
  if(!node)return null;
  while(node){if(seen.has(node.id))return null;seen.add(node.id);chain.unshift(node.id);node=node.parent?byId.get(node.parent):null;}
  return chain;
}
export function handshake({requested="metric",device="desktop_browser",cached=true,authorized=false}={}) {
  if(!DEVICE_KINDS.includes(device))return {status:"UNKNOWN_DEVICE",authorised:false};
  if(!VIEW_KINDS.includes(requested))return {status:"UNKNOWN_VIEW",authorised:false};
  if(!cached)return {status:"NOT_CACHED",authorised:false};
  if(requested==="process"&&!authorized)return {status:"REVIEW_ONLY",authorised:false};
  if(device==="machine"&&requested==="graph")return {status:"UNSUPPORTED_RENDERER",authorised:false};
  // An automatic device hint NEVER confers security identity or an operational lease.
  return {status:"LOCAL_VIEW_CANDIDATE",authorised:false,view:requested,device,origin:PUBLIC_OBJECT.object_id};
}
export function applySparseDelta(prior,change) {
  if(!prior || !change || !Number.isInteger(change.sequence) || change.sequence!==prior.sequence+1)
    return {status:"REPLAY_OR_SEQUENCE_MISMATCH"};
  if(change.prior_root!==prior.root)return {status:"CONTEXT_MISMATCH"};
  if(!["idle","moving","unknown"].includes(change.value))return {status:"INVALID_STATE"};
  const next={sequence:change.sequence,root:"demo-state-"+change.sequence,value:change.value};
  return {status:"LOCAL_RECONSTRUCTED_UNTRUSTED_CANDIDATE",next,applied:prior.value!==next.value?1:0,authenticated:false};
}
export function evaluatePrint({direction="polymer-to-metal",inert=false,interfaceQualified=false}={}) {
  if(!["polymer-to-metal","metal-to-polymer"].includes(direction))return {status:"UNKNOWN_ROUTE"};
  const needed=direction==="polymer-to-metal"
    ? ["verified compatible interlayer","temperature-controlled deposition"]
    : ["temperature-compatible pre-existing metal surface","polymer cure and adhesion"];
  return {
    status:inert&&interfaceQualified ? "CAN_IF_SIMULATED_CONDITIONS":"HOLD_CONDITIONS_UNVERIFIED",
    requirements:needed,environment:inert?"inert selected":"environment unverified",
    evidence:"SYNTHETIC_PROCESS_MODEL",qualified_machine:false,command_authorised:false
  };
}
export function numericSlice(id,override) {
  const item=PUBLIC_OBJECT.slices.find(x=>x.id===id);
  if(!item)return {status:"UNKNOWN_SLICE"};
  if(override===null||override==="")return {status:"UNKNOWN_INPUT"};
  const value=override===undefined?item.value:Number(override);
  if(!Number.isFinite(value))return {status:"UNKNOWN_INPUT"};
  return {status:"DERIVED_LOCAL_CANDIDATE",value,unit:item.unit,geometry_ref:item.ref,evidence:"SYNTHETIC"};
}

/** Convex polyhedron plane-section DEMO. Original geometry/identity are never mutated.
 * A caller must independently certify topology, provider rights and source-root.
 */
export const SYNTHETIC_CUBE = Object.freeze({
  object_id:PUBLIC_OBJECT.object_id,
  geometry_root:"synthetic-unit-cube-r1",frame:"synthetic-cartesian-XYZ",
  epoch:"synthetic-static",unit:"m",convex:true,
  vertices:[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
            [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],
  edges:[[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],
         [0,4],[1,5],[2,6],[3,7]],
});
export function sectionConvexMesh(mesh,plane){
  const hold=(status)=>({status,published:false,authoritative:false,physical_proof:false});
  if(!mesh || mesh.convex!==true || !Array.isArray(mesh.vertices) ||
     !Array.isArray(mesh.edges) || !mesh.vertices.length ||
     mesh.vertices.length>4096 || mesh.edges.length>8192 ||
     mesh.edges.length===0) return hold("HOLD_INVALID_GEOMETRY");
  if(![mesh.object_id,mesh.geometry_root,mesh.frame,mesh.epoch,mesh.unit].every(
    x=>typeof x==="string" && !!x.trim())) return hold("HOLD_SOURCE_FRAME_OR_UNITS");
  if(mesh.vertices.some(p=>!Array.isArray(p)||p.length!==3||
     p.some(v=>typeof v!=="number"||!Number.isFinite(v))))return hold("HOLD_INVALID_VERTEX");
  if(mesh.edges.some(e=>!Array.isArray(e)||e.length!==2||
     e.some(i=>!Number.isInteger(i)||i<0||i>=mesh.vertices.length)||
     e[0]===e[1]))return hold("HOLD_INVALID_EDGE");
  if(!plane || !Array.isArray(plane.normal) || plane.normal.length!==3 ||
     plane.normal.some(x=>typeof x!=="number"||!Number.isFinite(x)) ||
     typeof plane.offset!=="number"||!Number.isFinite(plane.offset))
     return hold("HOLD_INVALID_PLANE");
  const len=Math.hypot(...plane.normal);
  if(!Number.isFinite(len)||len<1e-12)return hold("HOLD_DEGENERATE_NORMAL");
  const n=plane.normal.map(v=>v/len), tolerance=1e-9;
  const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
  const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const points=[];
  const add=p=>{if(!points.some(q=>Math.hypot(...p.map((v,i)=>v-q[i]))<=tolerance))points.push(p);};
  for(const [ia,ib] of mesh.edges){
    const a=mesh.vertices[ia],b=mesh.vertices[ib],da=dot(a,n)-plane.offset,db=dot(b,n)-plane.offset;
    if(Math.abs(da)<=tolerance)add([...a]);
    if(Math.abs(db)<=tolerance)add([...b]);
    if((da>tolerance&&db< -tolerance)||(db>tolerance&&da< -tolerance)){
      const t=da/(da-db);add(a.map((v,i)=>v+t*(b[i]-v)));
    }
  }
  const basisSeed=Math.abs(n[0])<0.85?[1,0,0]:[0,1,0];
  let u=cross(basisSeed,n);const uLen=Math.hypot(...u);
  u=u.map(v=>v/uLen);const v=cross(n,u);
  const center=[0,0,0];for(const p of points)for(let i=0;i<3;i++)center[i]+=p[i];
  if(points.length)for(let i=0;i<3;i++)center[i]/=points.length;
  const ordered=points.map(p=>{
    const delta=p.map((x,i)=>x-center[i]);
    return {xy:[dot(delta,u),dot(delta,v)],point:p};
  }).sort((a,b)=>Math.atan2(a.xy[1],a.xy[0])-Math.atan2(b.xy[1],b.xy[0]));
  let twiceArea=0;
  for(let i=0;i<ordered.length;i++){
    const a=ordered[i].xy,b=ordered[(i+1)%ordered.length].xy;
    twiceArea+=a[0]*b[1]-a[1]*b[0];
  }
  const area=Math.abs(twiceArea)/2;
  const status=points.length===0?"NO_INTERSECTION":points.length<3||area<=tolerance?"DEGENERATE_SECTION":"DERIVED_PLANE_SECTION";
  return {status,object_id:mesh.object_id,geometry_root:mesh.geometry_root,
          frame:mesh.frame,epoch:mesh.epoch,unit:mesh.unit,
          plane:{normal:n,offset:plane.offset},vertices_2d:status==="DERIVED_PLANE_SECTION"?ordered.map(p=>p.xy):[],
          area:status==="DERIVED_PLANE_SECTION"?area:null,area_unit:mesh.unit+"^2",
          evidence:"SYNTHETIC_GEOMETRY_ONLY",published:false,authoritative:false,physical_proof:false};
}
