/** UniSpace private semantic inspector: H0-only source-review adapter.
 * Reuses existing LOAD semantic budget names and the private R3 card.
 * No network, source acquisition, native admission, host proof, execution or Vite import.
 */
export const SCHEMA = "UNISPACE-PRIVATE-VIEWPORT-INSPECTOR/0.1";
const VIEWS = new Set(["document","3d","chat","graph","interactive","matrix"]);
const CHILDREN = new Set(["Romer.cgx","Eco.cgx","EMASSC.cgx","LS.cgx"]);
const DEPTHS = new Set(["glance","standard","deep","audit","raw"]);
const ID = /^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/;
const SHA1 = /^[0-9a-f]{40}$/i;
const CAPS = Object.freeze({max_nodes:512,max_hops:6,max_cross_domains:8,max_cross_edges:256,max_evidence_refs:256,max_compute_ms:120000,max_ops_per_second:1000,max_transfer_bytes:60*1024*1024});
const DEFAULTS = Object.freeze({max_nodes:16,max_hops:2,max_cross_domains:0,max_cross_edges:0,max_evidence_refs:0,max_compute_ms:2000,max_ops_per_second:50,max_transfer_bytes:0,reasoning_depth:"standard"});
const record = x => x !== null && typeof x === "object" && !Array.isArray(x);
const hold = code => Object.freeze({schema:SCHEMA,state:"HOLD",code,hydration:"NONE",native_admitted:false,host_verified:false,release_accepted:false,network_fetch:false,canonical_mutation:false});
function budget(x) {
 if (x === undefined) x = {};
 if (!record(x) || Object.keys(x).some(k => !(k in DEFAULTS))) return null;
 const b = {...DEFAULTS,...x};
 if (!DEPTHS.has(b.reasoning_depth)) return null;
 for (const [k,cap] of Object.entries(CAPS))
   if (!Number.isSafeInteger(b[k]) || b[k] < (k==="max_nodes"||k==="max_ops_per_second"?1:0) || b[k]>cap) return null;
 return Object.freeze(b);
}
function controlsHtml(b) {
 const names = [["max_nodes","Knowledge breadth"],["max_hops","Hop radius"],["max_cross_domains","Cross-domains"],["max_cross_edges","Cross-edges"],["max_evidence_refs","Evidence references"],["max_compute_ms","Compute milliseconds"],["max_ops_per_second","Operations per second"],["max_transfer_bytes","Transfer bytes"]];
 return names.map(([key,label]) => '<label>'+label+' <input type="range" aria-label="'+label+'" min="0" max="'+CAPS[key]+'" value="'+b[key]+'" disabled><output>'+b[key]+'</output></label>').join("");
}
/** All inputs are review claims, never an authenticated session or DBR receipt. */
export function planPrivateViewportInspector({card,selection,client,request,source}={}) {
 if (!record(card)||card.schema!=="UNISPACE-PRIVATE-R3-CARD/0.1"||card.state!=="R3_PRIVATE_VIEW_CANDIDATE"||
     card.native_admitted!==false||card.host_verified!==false||card.release_accepted!==false||
     card.display_hydration!=="H0_REFERENCE_ONLY") return hold("UNTRUSTED_R3_CARD");
 if (!record(selection)||selection.parent_filespace!=="Cognigrex.cgx"||
     !ID.test(selection.object_id||"")||!CHILDREN.has(selection.filespace)||
     selection.object_id!==card.candidate_object_id||selection.filespace!==card.child_filespace||
     selection.identity_status!=="SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED") return hold("EXACT_OBJECT_CHILD_REQUIRED");
 if (!record(client)||client.mode!=="review_only"||client.revoked!==false||
     !Array.isArray(client.allowed_object_ids)||client.allowed_object_ids.length!==1||
     client.allowed_object_ids[0]!==selection.object_id||
     !Array.isArray(client.allowed_filespaces)||client.allowed_filespaces.length!==1||
     client.allowed_filespaces[0]!==selection.filespace) return hold("CLIENT_SCOPE_MISMATCH");
 if (!record(source)||source.object_id!==selection.object_id||source.filespace!==selection.filespace||
     source.mapping_id!==card.source_mapping_id||source.mapping_blob_sha!==card.source_mapping_blob_sha||
     !SHA1.test(source.mapping_blob_sha||"")||source.evidence_class!==card.evidence_class||
     !["UNRESOLVED","PRIVATE_SCOPED","PUBLIC_SAFE"].includes(source.rights)) return hold("SOURCE_PROVENANCE_MISMATCH");
 if (!record(request)||!VIEWS.has(request.view)||!["H0","H1","H2","H3","H4"].includes(request.requested_hydration)) return hold("INVALID_VIEW");
 const b = budget(request.controls);
 if (!b) return hold("INVALID_BUDGET");
 const frontier = ["INDEPENDENT_ROOT_DBR_HOST_READBACK_REQUIRED","ISSUE_158_PUBLIC_STATIC_ISOLATION_HOLD","ISSUE_161_TWO_NODE_READBACK_HOLD","SEMANTIC_HALO_NOT_HYDRATED","SOURCE_RIGHTS_NOT_INDEPENDENTLY_VERIFIED"];
 if (request.requested_hydration!=="H0") frontier.push("HIGHER_HYDRATION_DENIED");
 if (request.view==="3d" && (!source.geometry_frame||!source.geometry_units||source.geometry_state!=="SOURCE_DERIVED_GEOMETRY")) frontier.push("GEOMETRY_FRAME_UNITS_OR_RIGHTS_FRONTIER");
 if (request.view==="chat") frontier.push("MODEL_CAPABILITY_NOT_VERIFIED");
 if (request.view==="interactive") frontier.push("INTERACTION_NOT_AUTHORISED");
 if (b.max_cross_domains||b.max_cross_edges) frontier.push("CROSS_DOMAIN_EDGES_NOT_HYDRATED");
 if (b.max_transfer_bytes||b.max_compute_ms||b.max_ops_per_second) frontier.push("BUDGET_IS_REQUEST_NOT_COMPUTE_OR_TRANSFER");
 const html = '<section role="region" aria-label="Private semantic viewport inspector" data-cgx-inspector="review-hold"><h2>Private viewport · source review</h2><p role="status">View: '+request.view+'. Offline H0 reference only. No source evidence or geometry loaded.</p><p>Semantic halo and novel-to-known matching: Frontier pending authorised source readback.</p><fieldset disabled><legend>Requested context ceilings · inactive</legend>'+controlsHtml(b)+'</fieldset><p>Reasoning depth: '+b.reasoning_depth+'. Host and permission checks required.</p></section>';
 return Object.freeze({
   schema:SCHEMA,state:"R3_PRIVATE_INSPECTOR_CANDIDATE",parent_filespace:"Cognigrex.cgx",
   candidate_object_id:selection.object_id,child_filespace:selection.filespace,
   source_mapping_id:source.mapping_id,source_mapping_blob_sha:source.mapping_blob_sha,
   evidence_class:source.evidence_class,evidence_ceiling:"SOURCE_REFERENCE_UNVERIFIED",
   selected_view:request.view,requested_hydration:request.requested_hydration,display_hydration:"H0_REFERENCE_ONLY",
   semantic_halo:Object.freeze({requested_max_nodes:b.max_nodes,actual_nodes:null,edges:null,status:"FRONTIER_NOT_HYDRATED"}),
   permitted_evidence_refs:null,novel_to_known:"FRONTIER_NO_TYPED_SOURCE_COMPARISON",
   geometry_status:request.view==="3d"?"FRONTIER_NO_AUTHORISED_RENDER":"NOT_REQUESTED",
   requested_controls:b,actual_compute_ms:null,actual_ops_per_second:null,actual_transfer_bytes:0,
   frontier:Object.freeze(frontier),html,
   capability_mode:"DECLARATIVE_PREFLIGHT_ONLY",executable:false,installable:false,
   source_bytes_embedded:false,public_vite_asset:false,network_fetch:false,
   native_admitted:false,host_verified:false,dist_verified:false,release_accepted:false,canonical_mutation:false
 });
}
