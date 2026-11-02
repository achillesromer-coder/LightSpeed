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


/**
 * Source-safe orbit atlas for the public UniSpace demonstration.
 * This is a 3D -> 2D perspective projection of a FIXED synthetic family
 * example, not a private object resolver, graph proof or native .cgx mint.
 * Colour semantics: amber=fractal, blue=dedicated/sealed, green=open demo.
 */
export const PUBLIC_CGX_ATLAS=Object.freeze({
  schema:"cgx-public-family-orbit/0.1",
  source:"STATIC_SYNTHETIC_FIXTURE",
  viewpoint:"PUBLIC_SURFACE_LOOKING_INWARD",
  nodes:Object.freeze([
    {id:"root",label:"Cognigrex",layer:"fractal",access:"SYNTHETIC",xyz:[0,0,0]},
    {id:"romer",label:"Römer",layer:"fractal",access:"SYNTHETIC",xyz:[-1.38,.56,-.48]},
    {id:"eco",label:"Eco",layer:"fractal",access:"SYNTHETIC",xyz:[1.32,.67,-.58]},
    {id:"emassc",label:"EMASSC",layer:"fractal",access:"SYNTHETIC",xyz:[-.52,-.94,.85]},
    {id:"ls",label:"LS / local",layer:"dedicated",access:"SEALED_NO_PUBLIC_OBJECT",xyz:[.72,-.82,.71]},
    {id:"unisp",label:"UniSpace",layer:"dedicated",access:"SEALED_NO_PUBLIC_OBJECT",xyz:[.05,1.17,1.15]},
    {id:"load",label:"LOAD · demo",layer:"open",access:"PUBLIC_SYNTHETIC_ONLY",xyz:[1.53,-.18,-.86]},
    {id:"ccc",label:"CCC / CYC",layer:"dedicated",access:"SEALED_NO_PUBLIC_OBJECT",xyz:[-1.40,-.42,-1.14]},
    {id:"open",label:"Open example",layer:"open",access:"PUBLIC_SYNTHETIC_ONLY",xyz:[.25,.11,-1.45]}
  ]),
  edges:Object.freeze([
    ["root","romer"],["root","eco"],["root","emassc"],
    ["root","ls"],["root","unisp"],["root","load"],["root","ccc"],
    ["root","open"],["romer","emassc"],["eco","load"]
  ])
});
const ORBIT_COLOURS=Object.freeze({fractal:"#ed9c45",dedicated:"#5daaff",open:"#45d994"});
export function projectCgxOrbit({yaw=0,pitch=0.18,zoom=1,width=760,height=370}={}){
  const hold=reason=>({status:reason,native_admitted:false,public_release_verified:false,nodes:[],edges:[]});
  if (![yaw,pitch,zoom,width,height].every(v=>typeof v==="number"&&Number.isFinite(v)) ||
      Math.abs(yaw)>1e7 || Math.abs(pitch)>1e7 || zoom<0.55 || zoom>2.5 ||
      width<320 || width>4096 || height<200 || height>4096)
    return hold("HOLD_INVALID_ORBIT_FRAME");
  const a=yaw%(2*Math.PI),b=Math.max(-1.4,Math.min(1.4,pitch));
  const ca=Math.cos(a),sa=Math.sin(a),cb=Math.cos(b),sb=Math.sin(b);
  const nodes=PUBLIC_CGX_ATLAS.nodes.map(n=>{
    const [x,y,z]=n.xyz;
    const xx=x*ca-z*sa,zz=x*sa+z*ca,yy=y*cb-zz*sb,depth=y*sb+zz*cb;
    const scale=5.5/(5.5-depth*zoom);
    return {
      id:n.id,label:n.label,layer:n.layer,access:n.access,color:ORBIT_COLOURS[n.layer],
      x:width/2+xx*83*zoom*scale,
      y:height/2-yy*83*zoom*scale,
      radius:(n.id==="root"?21:12)*scale,
      depth,opacity:Math.max(.55,Math.min(.98,.75+depth*.11)),
      clickable_source_body:false
    };
  });
  const lookup=new Map(nodes.map(n=>[n.id,n]));
  const edges=PUBLIC_CGX_ATLAS.edges.map(([from,to])=>{
    const a=lookup.get(from),b=lookup.get(to);
    return {from,to,x1:a.x,y1:a.y,x2:b.x,y2:b.y,
      opacity:Math.max(.24,Math.min(.8,(a.opacity+b.opacity)/2-.15))};
  });
  return {
    status:"SYNTHETIC_ORBIT_PROJECTION_ONLY",schema:PUBLIC_CGX_ATLAS.schema,
    viewpoint:PUBLIC_CGX_ATLAS.viewpoint,yaw:a,pitch:b,zoom,
    nodes:nodes.sort((x,y)=>x.depth-y.depth),edges,
    selectable_public_source:false,native_admitted:false,
    governance_access:false,private_source_included:false,
    public_release_verified:false,geospatial_frame_verified:false,
    calculations:"PERSPECTIVE_PROJECTION_OF_SYNTHETIC_COORDINATES_ONLY"
  };
}
