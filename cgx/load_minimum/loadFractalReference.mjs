/** Reversible R0 source-reference shorthand for existing LOAD/Alexandria.
 * This is an exact metadata descriptor, NOT source-byte compression, native
 * CGX minting, a geometry operator, a DOOM/WASM codec or an ACL decision.
 */
export const SCHEMA="CGX-LOAD-R0-REFERENCE-SHORTHAND/0.1";
const MAX_WORK=60*1024*1024;
const RIGHTS=new Set(["OWNER_PRIVATE","PUBLIC_SAFE","LICENSE_RESTRICTED","UNKNOWN"]);
const DOMAINS=Object.freeze({
  romer:["Romer.cgx","Cognigrex.cgx"],
  eco:["Eco.cgx","Cognigrex.cgx"],
  emassc:["EMASSC.cgx","Cognigrex.cgx"],
  ls:["LS.cgx","EMASSC.cgx"]
});
const FIELDS=Object.freeze([
  "candidate_key","owner_domain","file_space","parent_file_space",
  "source_ref","source_sha256","source_version","source_byte_length",
  "rights","operator_ref","operator_version","children",
  "residual_ref","geometry_profile"
]);
const txt=x=>typeof x==="string"&&x.length>0&&x.length<=256&&
  x===x.normalize("NFC")&&!/[\u0000-\u001f\u007f-\u009f]/.test(x)&&
  !/[\p{Cf}\p{Zl}\p{Zp}\p{Cs}]/u.test(x);
const hex=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
function normalize(d){
  if(!obj(d)||!Object.keys(d).every(k=>FIELDS.includes(k))||
     !FIELDS.every(k=>Object.hasOwn(d,k)))throw Error("LOSSLESS_FIELD_SET_REQUIRED");
  const scope=Object.hasOwn(DOMAINS,d.owner_domain)?DOMAINS[d.owner_domain]:null;
  if(!scope||d.file_space!==scope[0]||d.parent_file_space!==scope[1])
    throw Error("FAMILY_SCOPE_CONFLICT");
  for(const key of ["candidate_key","source_ref","source_version","operator_ref","operator_version"])
    if(!txt(d[key]))throw Error("INVALID_REFERENCE");
  if(!d.candidate_key.startsWith("candidate:"))throw Error("NATIVE_ID_NOT_MINTED");
  if(!hex(d.source_sha256))throw Error("UNQUALIFIED_SOURCE_SHA");
  if(!Number.isSafeInteger(d.source_byte_length)||d.source_byte_length<0)
    throw Error("INVALID_SOURCE_SIZE");
  if(!RIGHTS.has(d.rights))throw Error("RIGHTS_UNQUALIFIED");
  if(!Array.isArray(d.children)||d.children.length>32||
     !d.children.every(v=>txt(v)&&v.startsWith("candidate:"))||
     new Set(d.children).size!==d.children.length||
     d.children.includes(d.candidate_key))throw Error("INVALID_CHILD_REFS");
  if(d.residual_ref!==null&&!txt(d.residual_ref))throw Error("UNQUALIFIED_RESIDUAL");
  if(d.geometry_profile!==null&&!txt(d.geometry_profile))throw Error("INVALID_GEOMETRY_PROFILE");
  return Object.fromEntries(FIELDS.map(k=>[k,k==="children"?[...d[k]]:d[k]]));
}
/** Tuple schema is a reversible, deterministic shorthand for the exact R0 reference METADATA. */
export function packR0Reference(descriptor){
  const d=normalize(descriptor);
  return Object.freeze([SCHEMA,...FIELDS.map(k=>k==="children"?Object.freeze(d[k]):d[k])]);
}
export function unpackR0Reference(tuple){
  if(!Array.isArray(tuple)||tuple.length!==FIELDS.length+1||tuple[0]!==SCHEMA)
    throw Error("INVALID_R0_SHORTHAND");
  const d=normalize(Object.fromEntries(FIELDS.map((k,i)=>[k,tuple[i+1]])));
  if(JSON.stringify(packR0Reference(d))!==JSON.stringify(tuple))
    throw Error("NONCANONICAL_SHORTHAND");
  return d;
}
/** Selectively plan H0-H2 metadata projection. Actual source bytes remain with R0 providers. */
export function planR0ReferenceHydration({
  tuple, authorized_keys, authorized_source_refs,
  source_sha256, surface="private", level=0, requested_work_bytes=0
}={}){
  const deny=reason=>({schema:SCHEMA,state:"DENIED",reason,source_bytes_read:0,
    canonical_writes:0,native_admission:false,public_release:false});
  if(!Array.isArray(authorized_keys)||!Array.isArray(authorized_source_refs)||
     !authorized_keys.every(txt)||!authorized_source_refs.every(txt)||
     !["private","public"].includes(surface)||![0,1,2].includes(level)||
     !Number.isSafeInteger(requested_work_bytes)||requested_work_bytes<0||
     requested_work_bytes>MAX_WORK)return deny("INVALID_HYDRATION_SCOPE");
  let d;
  try{d=unpackR0Reference(tuple);}catch{return deny("INVALID_SOURCE_DESCRIPTOR");}
  if(!authorized_keys.includes(d.candidate_key)||!authorized_source_refs.includes(d.source_ref))
    return deny("SOURCE_SCOPE_NOT_AUTHORIZED");
  if(d.source_sha256!==source_sha256)return deny("SOURCE_BYTES_IDENTITY_MISMATCH");
  if(surface==="public"&&d.rights!=="PUBLIC_SAFE")return deny("SOURCE_PUBLIC_RIGHTS_HOLD");
  const result={schema:SCHEMA,state:"SOURCE_REFERENCE_ONLY",
    candidate_key:d.candidate_key,owner_domain:d.owner_domain,
    file_space:d.file_space,parent_file_space:d.parent_file_space,
    level,rights:d.rights,source_bytes_read:0,source_byte_length:d.source_byte_length,
    source_ref:null,source_sha256:null,source_version:null,
    children:[],operator_ref:null,operator_version:null,residual_ref:null,geometry_profile:null,
    source_body_hydrated:false,source_compression_verified:false,
    operator_executed:false,object_id_minted:null,canonical_writes:0,
    native_admission:false,public_release:false,
    requires:["provider R0 byte readback","actual owner rights and ACL","codec/geometry proof where applicable",
              "signed current Object_ID/lease/DBR before accepted R3 or F"]};
  if(level>=1)result.children=d.children.filter(k=>authorized_keys.includes(k));
  if(level>=2){
    result.source_ref=d.source_ref;
    result.source_sha256=d.source_sha256;
    result.source_version=d.source_version;
    result.operator_ref=d.operator_ref;
    result.operator_version=d.operator_version;
    result.residual_ref=d.residual_ref;
    result.geometry_profile=d.geometry_profile;
  }
  return result;
}

/** Non-issuing skeletal/leaf transfer proposal, reusing canonical R0 reference metadata.
 * This is NOT a compressor or a transport executor. Every leaf has its own
 * source, permissions and hash proof to acquire before a byte may be hydrated.
 */
export const LEAF_PACKET_SCHEMA="CGX-LOAD-R0-LEAF-PACKET-PLAN/0.1";
export function planR0LeafPacket({
 tuple,authorized_keys,authorized_source_refs,source_sha256,
 surface="private",requested_leaf_keys=[],max_packet_bytes=65536
}={}){
 const deny=reason=>({schema:LEAF_PACKET_SCHEMA,state:"DENIED",reason,
   source_bytes_read:0,payload_bytes_transferred:0,canonical_writes:0,
   native_mint:false,public_release:false});
 if(!Array.isArray(requested_leaf_keys)||requested_leaf_keys.length>32||
    !requested_leaf_keys.every(k=>txt(k)&&k.startsWith("candidate:")&&!k.includes("\\"))||
    new Set(requested_leaf_keys).size!==requested_leaf_keys.length||
    !Number.isSafeInteger(max_packet_bytes)||max_packet_bytes<512||
    max_packet_bytes>MAX_WORK)return deny("INVALID_PACKET_REQUEST");
 const proof=planR0ReferenceHydration({tuple,authorized_keys,authorized_source_refs,
   source_sha256,surface,level:2,requested_work_bytes:0});
 if(proof.state!=="SOURCE_REFERENCE_ONLY")return deny(proof.reason||"SOURCE_NOT_AUTHORIZED");
 const d=unpackR0Reference(tuple);
 if(requested_leaf_keys.some(k=>!d.children.includes(k)||!authorized_keys.includes(k)))
   return deny("LEAF_NOT_AUTHORIZED");
 // Canonical child order is independent of request order, so plan replay is stable.
 const requested=new Set(requested_leaf_keys);
 const leaves=d.children.filter(k=>requested.has(k)).map(candidate_key=>({
   candidate_key,stage:"REFERENCE_ONLY",source_hash:null,rights_verified:false
 }));
 const packet={
   schema:LEAF_PACKET_SCHEMA,state:"UNSIGNED_METADATA_PLAN_ONLY",
   candidate_key:d.candidate_key,file_space:d.file_space,parent_file_space:d.parent_file_space,
   source_ref:d.source_ref,source_sha256:d.source_sha256,source_version:d.source_version,
   source_byte_length:d.source_byte_length,rights:d.rights,
   operator_ref:d.operator_ref,operator_version:d.operator_version,
   residual_ref:d.residual_ref,geometry_profile:d.geometry_profile,leaves,
   raw_source_included:false,payload_bytes_transferred:0,source_bytes_read:0,
   leaf_byte_integrity_verified:false,child_rights_verified:false,
   codec_compression_verified:false,network_executed:false,canonical_writes:0,
   native_mint:false,public_release:false,
   requires:["per-leaf independent source hash and rights","actual payload retrieval and byte verification",
     "authenticated current issuer and DBR for native admission"]
 };
 const metadata_utf8_bytes=new TextEncoder().encode(JSON.stringify(packet)).length;
 if(metadata_utf8_bytes>max_packet_bytes)return deny("PACKET_BUDGET_EXCEEDED");
 return {...packet,metadata_utf8_bytes,max_packet_bytes};
}


/** Nested, source-reference-only assembly crosswalk.
 * One R0 descriptor per candidate identity; shared child occurrences are edges,
 * never extra native objects. H2 carries exact reversible metadata, not bytes.
 * FileSpace retains custody; DataSpace transport and F80 execution require host
 * authorization independently of this F70/F90 review descriptor.
 */
export const NESTED_FACET_SCHEMA="CGX-LOAD-R0-NESTED-FACET-PLAN/0.1";
const FACET_KINDS=new Set(["assembly","document","dataset","geometry","simulation","model","tool","smart_contract","state","receipt"]);
const exactFields=(v,keys)=>obj(v)&&Object.keys(v).length===keys.length&&keys.every(k=>Object.hasOwn(v,k));
const evmFields=["standard","chain_ref","contract_address","interface_sha256","runtime_code_sha256","method_selector","operation"];
function contractBinding(b,d){
 if(!exactFields(b,evmFields)||b.standard!=="evm-abi/1"||
    typeof b.chain_ref!=="string"||!/^eip155:[1-9][0-9]{0,31}$/.test(b.chain_ref)||
    (b.contract_address!==null&&(typeof b.contract_address!=="string"||!/^0x[0-9a-f]{40}$/.test(b.contract_address)))||
    b.interface_sha256!==d.source_sha256||
    (b.runtime_code_sha256!==null&&!hex(b.runtime_code_sha256))||
    (b.contract_address===null&&b.runtime_code_sha256!==null)||
    (b.method_selector!==null&&(typeof b.method_selector!=="string"||!/^0x[0-9a-f]{8}$/.test(b.method_selector)))||
    !["inspect","simulate","submit"].includes(b.operation))throw Error("SMART_CONTRACT_BINDING_INVALID");
 return Object.fromEntries(evmFields.map(k=>[k,b[k]]));
}
const nestedDeny=reason=>({schema:NESTED_FACET_SCHEMA,state:"DENIED",reason,source_bytes_read:0,
 payload_bytes_transferred:0,canonical_writes:0,native_admission:false,public_release:false});
/** Full supplied closure, deterministic top-down occurrence projection and
 * bottom-up unique-node order. Expected source digests and scopes are claims,
 * not authenticated ACLs. No provider, chain, codec or simulation is executed.
 * LOAD.Lite can still use planR0ReferenceHydration for the root-only bootstrap.
 */
export function planR0NestedFacets(request){
 if(!obj(request))return nestedDeny("INVALID_NESTED_REQUEST");
 const allowed=["root_key","facets","authorized_keys","authorized_source_refs","expected_source_hashes","surface","level","max_nodes","max_depth","max_metadata_bytes"];
 if(!Object.keys(request).every(k=>allowed.includes(k)))return nestedDeny("UNEXPECTED_NESTED_FIELD");
 const {root_key,facets,authorized_keys,authorized_source_refs,expected_source_hashes,
  surface="private",level=2,max_nodes=128,max_depth=16,max_metadata_bytes=65536}=request;
 if(!txt(root_key)||!root_key.startsWith("candidate:")||!Array.isArray(facets)||!facets.length||
    !Number.isSafeInteger(max_nodes)||max_nodes<1||max_nodes>256||facets.length>max_nodes||
    !Number.isSafeInteger(max_depth)||max_depth<0||max_depth>32||
    !Number.isSafeInteger(max_metadata_bytes)||max_metadata_bytes<512||max_metadata_bytes>1048576||
    !["private","public"].includes(surface)||![0,1,2].includes(level)||
    !Array.isArray(authorized_keys)||authorized_keys.length>512||!authorized_keys.every(txt)||
    !Array.isArray(authorized_source_refs)||authorized_source_refs.length>512||!authorized_source_refs.every(txt)||
    !obj(expected_source_hashes)||Object.keys(expected_source_hashes).length>512)
  return nestedDeny("INVALID_NESTED_SCOPE");
 // Never publish nested R0 source locations or smart-contract bindings from
 // caller-supplied rights. Public review here is root identity only.
 if(surface==="public"&&level!==0)return nestedDeny("PUBLIC_NESTED_METADATA_HOLD");
 const nodes=new Map();
 try{
  for(const f of facets){
   if(!exactFields(f,["tuple","kind","binding"])||!FACET_KINDS.has(f.kind))throw Error("INVALID_FACET");
   const d=unpackR0Reference(f.tuple), key=d.candidate_key;
   if(nodes.has(key))throw Error("DUPLICATE_CANDIDATE_IDENTITY");
   if(!Object.hasOwn(expected_source_hashes,key))throw Error("SOURCE_DIGEST_REQUIRED");
   const projection=planR0ReferenceHydration({tuple:f.tuple,authorized_keys,authorized_source_refs,
    source_sha256:expected_source_hashes[key],surface,level:0});
   if(projection.state!=="SOURCE_REFERENCE_ONLY")throw Error(projection.reason||"FACET_SOURCE_DENIED");
   let binding=null;
   if(f.kind==="smart_contract")binding=contractBinding(f.binding,d);
   else if(f.binding!==null)throw Error("UNEXPECTED_ADAPTER_BINDING");
   nodes.set(key,{d,tuple:packR0Reference(d),kind:f.kind,binding});
  }
  if(!nodes.has(root_key))throw Error("ROOT_REFERENCE_MISSING");
  const visiting=new Set(),heights=new Map(),ordered=[];
  const visit=(key,depth)=>{
   if(depth>max_depth)throw Error("NESTED_DEPTH_EXCEEDED");
   if(visiting.has(key))throw Error("NESTED_CYCLE");
   if(heights.has(key)){
    if(depth+heights.get(key)>max_depth)throw Error("NESTED_DEPTH_EXCEEDED");
    return heights.get(key);
   }
   const n=nodes.get(key);if(!n)throw Error("CHILD_REFERENCE_MISSING");
   visiting.add(key);let height=0;
   for(const child of n.d.children)height=Math.max(height,1+visit(child,depth+1));
   visiting.delete(key);heights.set(key,height);ordered.push(key);return height;
  };
  visit(root_key,0);
  if(ordered.length!==nodes.size)throw Error("UNREACHABLE_FACET");
  const expanded=new Set();
  const human=(key)=>{
   const n=nodes.get(key);
   if(expanded.has(key))return {ref:key,occurrence:"SHARED_REFERENCE"};
   expanded.add(key);
   const item={ref:key,occurrence:"EXPANDED",kind:n.kind};
   if(level>=1)item.children=n.d.children.map(human);
   return item;
  };
  const visible=level===0?[root_key]:ordered;
  const bottom=visible.map(key=>{
   const n=nodes.get(key),out={ref:key,kind:n.kind};
   if(level>=1)out.children=[...n.d.children];
   if(level===2){
    out.tuple=n.tuple;out.binding=n.binding;
    out.adapter={operator_ref:n.d.operator_ref,operator_version:n.d.operator_version,
     source_ref:n.d.source_ref,source_sha256:n.d.source_sha256,
     function_facets:["F70","F80","F90"],operator_executed:false};
    if(n.binding)out.contract_review={operation:n.binding.operation,
     state:n.binding.operation==="submit"?"HOLD_SIGNED_LEASE_AND_TRANSACTION_CONSENT":
      n.binding.operation==="simulate"?"HOLD_QUALIFIED_SIMULATION_PROVIDER":"REFERENCE_INSPECTION_ONLY",
     chain_identity_verified:false,abi_selector_verified:false,runtime_code_verified:false,
     proxy_resolution_verified:false,finality_verified:false,transaction_constructed:false};
   }
   return out;
  });
  const plan={schema:NESTED_FACET_SCHEMA,state:"NESTED_REFERENCE_PLAN_ONLY",parent:"Cognigrex.cgx",
   resolver_alias:"LOAD.cgx",root:root_key,level,surface,
   human_top_down:human(root_key),machine_bottom_up:bottom,
   unique_facets:visible.length,closure_checked:true,identity_model:"ONE_CANDIDATE_PER_KEY_SHARED_OCCURRENCES",
   source_custody:"FileSpace_R0",exchange:"DataSpace_REFERENCE_PLAN_ONLY",
   source_bytes_read:0,payload_bytes_transferred:0,canonical_writes:0,
   source_digests_independently_verified:false,scope_independently_verified:false,
   rights_independently_verified:false,semantic_equivalence_verified:false,geometry_verified:false,
   source_body_hydrated:false,native_admission:false,public_release:false,
   operator_executed:false,transaction_constructed:false,chain_transaction_submitted:false,
   requires:["independent provider R0 digest and rights readback","existing scoped DataSpace peer and signed lease",
    "adapter-specific proof and signed DBR before execution","transaction-specific consent before effectful chain operation"]};
  const bytes=new TextEncoder().encode(JSON.stringify(plan)).length;
  if(bytes>max_metadata_bytes)return nestedDeny("NESTED_METADATA_BUDGET_EXCEEDED");
  return plan;
 }catch(e){
  // Never echo source metadata, paths, credentials or arbitrary exception text.
  const known=new Set(["INVALID_FACET","DUPLICATE_CANDIDATE_IDENTITY","SOURCE_DIGEST_REQUIRED","SOURCE_SCOPE_NOT_AUTHORIZED",
   "SOURCE_BYTES_IDENTITY_MISMATCH","SOURCE_PUBLIC_RIGHTS_HOLD","INVALID_HYDRATION_SCOPE","INVALID_SOURCE_DESCRIPTOR",
   "SMART_CONTRACT_BINDING_INVALID","UNEXPECTED_ADAPTER_BINDING","ROOT_REFERENCE_MISSING",
   "NESTED_DEPTH_EXCEEDED","NESTED_CYCLE","CHILD_REFERENCE_MISSING","UNREACHABLE_FACET"]);
  return nestedDeny(known.has(e?.message)?e.message:"INVALID_NESTED_DESCRIPTOR");
 }
}
