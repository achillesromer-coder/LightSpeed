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
