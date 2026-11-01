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
  const scope=DOMAINS[d.owner_domain];
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
