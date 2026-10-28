/** UniSpace private R3 source-view adapter. Review-only; no fetch, host proof or Vite import. */
const PARENT="Cognigrex.cgx", CHILDREN=new Set(["Romer.cgx","Eco.cgx","EMASSC.cgx","LS.cgx"]);
const VIEWS=new Set(["document","3d","chat","graph","interactive","matrix"]);
const ID=/^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/, SHA256=/^[a-f0-9]{64}$/i, SHA1=/^[a-f0-9]{40}$/i;
function esc(x){return String(x).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function hold(code){return Object.freeze({schema:"UNISPACE-PRIVATE-R3-CARD/0.1",state:"HOLD",code,hydration:"NONE",native_admitted:false,host_verified:false,release_accepted:false,network_fetch:false,canonical_mutation:false});}
export function planPrivateR3Card(input){
  if(!input || typeof input!=="object" || Array.isArray(input))return hold("INVALID_INPUT");
  const {selection:s,source:p,client:c,request:r}=input;
  if(!s||s.parent_filespace!==PARENT||!CHILDREN.has(s.filespace)||!ID.test(s.object_id||"")||s.object_id==="cgx:root:cognigrex"||s.object_id.startsWith("cgx:domain:")||s.identity_status!=="SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED")return hold("UNQUALIFIED_SELECTION");
  if(!c||c.mode!=="review_only"||c.revoked!==false||!Array.isArray(c.allowed_object_ids)||c.allowed_object_ids.length!==1||c.allowed_object_ids[0]!==s.object_id||!Array.isArray(c.allowed_filespaces)||c.allowed_filespaces.length!==1||c.allowed_filespaces[0]!==s.filespace)return hold("CLIENT_SCOPE_MISMATCH");
  if(!p||p.object_id!==s.object_id||p.filespace!==s.filespace||typeof p.mapping_id!=="string"||!/^FF-[A-Z0-9-]{4,90}$/.test(p.mapping_id)||!SHA256.test(p.r0_source_sha256||"")||!SHA1.test(p.mapping_blob_sha||"")||!["scientific","creative","mixed","unknown"].includes(p.evidence_class)||!["UNRESOLVED","PRIVATE_SCOPED","PUBLIC_SAFE"].includes(p.rights)||!["R0_R1_R2_REFERENCE","R0_R1_REFERENCE"].includes(p.mapping_stage))return hold("SOURCE_MAPPING_MISMATCH");
  if(!r||!VIEWS.has(r.view)||!["H0","H1","H2","H3","H4"].includes(r.requested_hydration))return hold("INVALID_VIEW_REQUEST");
  // No client-provided boolean, localhost header, or registry document can establish live host proof.
  // This pure adapter deliberately cannot hydrate source bytes or certify any R3/DBR admission.
  const frontier=["INDEPENDENT_ROOT_DBR_HOST_READBACK_REQUIRED","ISSUE_158_STATIC_PRIVATE_BOUNDARY_HOLD","ISSUE_161_TWO_NODE_ACCEPTANCE_HOLD"];
  if(p.rights!=="PRIVATE_SCOPED")frontier.push("PRIVATE_RIGHTS_NOT_CONFIRMED");
  if(r.view==="3d" && (!p.geometry_frame||!p.geometry_units||p.geometry_state!=="SOURCE_DERIVED_GEOMETRY"))frontier.push("GEOMETRY_FRAME_UNITS_OR_AUTHORITY_FRONTIER");
  if(r.requested_hydration!=="H0")frontier.push("HYDRATION_ABOVE_H0_DENIED");
  const html='<article class="panel" data-cgx-r3-private-candidate="held" role="status" aria-live="polite"><p class="eyebrow">UniSpace · private source view</p><h2>Object view awaiting authenticated readback</h2><p class="muted">Selected view: '+esc(r.view)+'. Only H0 reference metadata is planned; no private source, geometry, capability, or execution is loaded.</p><p class="muted">Frontier: source permissions and host authority must be independently verified.</p></article>';
  return Object.freeze({
    schema:"UNISPACE-PRIVATE-R3-CARD/0.1",state:"R3_PRIVATE_VIEW_CANDIDATE",
    parent_filespace:PARENT,candidate_object_id:s.object_id,child_filespace:s.filespace,
    evidence_class:p.evidence_class,source_mapping_id:p.mapping_id,source_mapping_blob_sha:p.mapping_blob_sha,
    r0_hash_status:"REGISTERED_REFERENCE_NOT_BYTES_VERIFIED",mapping_stage:p.mapping_stage,
    selected_view:r.view,requested_hydration:r.requested_hydration,display_hydration:"H0_REFERENCE_ONLY",
    frontier:Object.freeze(frontier),html,
    capability_mode:"DECLARATIVE_PREFLIGHT_ONLY",executable:false,installable:false,
    source_rights_status:"CLAIM_ONLY_INDEPENDENT_CLEARANCE_REQUIRED",
    source_bytes_embedded:false,public_vite_asset:false,network_fetch:false,
    native_admitted:false,host_verified:false,dist_verified:false,release_accepted:false,canonical_mutation:false,
    claim_boundary:"Source-mapped private R3 presentation candidate, not a live R3 view, permission receipt, CAD rendering, installed CCC tool, or public release."
  });
}
