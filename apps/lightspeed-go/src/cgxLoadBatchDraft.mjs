/** Local LOAD reference folding and launch-batch preparation. No wallet, RPC or mint API. */
export const DRAFT_SCHEMA='CGX-LOAD-UNSIGNED-BATCH-DRAFT/0.1';
const INDEX_SCHEMA='CGX-LOAD-LOCAL-INDEX/0.1';
const SHA=/^[0-9a-f]{64}$/;
const REF=/^cgx\.review:\/\/cognigrex\/load\/[0-9a-f]{64}$/;
const LANES=['Cognigrex_Family','Achilles_Romer','Neo_LightSpeed','Athene_Eco','UniSpace_Product'];
export const LIMIT=8*1024*1024;
export const canonical=x=>JSON.stringify(x,(_k,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
export async function digest(value){
 const bytes=typeof value==='string'?new TextEncoder().encode(value):value;
 return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
}
const check=(condition,reason)=>{if(!condition)throw new Error(reason);};
function rows(records){
 check(Array.isArray(records)&&records.length>0&&records.length<=2500,'INDEX_RECORD_BUDGET');
 const seen=new Set();
 const result=records.map(r=>{
  check(r&&REF.test(r.review_ref)&&r.pointer_sha256===r.review_ref.split('/').at(-1),'INVALID_REFERENCE');
  check(!seen.has(r.review_ref),'DUPLICATE_REFERENCE');seen.add(r.review_ref);
  check(r.native_mint===false&&r.rights_approved===false,'INDEX_AUTHORITY_CLAIM');
  check(typeof r.name==='string'&&r.name.length<=2000&&typeof r.rights_status==='string'&&r.rights_status.length<=256,'INVALID_SOURCE_METADATA');
  const unresolved='R0_SHARD_HASH_IN_ORIGINAL_RECEIPT';
  check(r.source_sha256==null||SHA.test(r.source_sha256)||r.source_sha256===unresolved,'INVALID_SOURCE_DIGEST');
  check(r.source_digest_claim==null||r.source_digest_claim===unresolved,'INVALID_DIGEST_CLAIM');
  check(!SHA.test(r.source_sha256??'')||r.source_digest_claim==null,'CONFLICTING_DIGEST_CLAIM');
  check(Array.isArray(r.routes)&&r.routes.length>0&&r.routes.length<=5&&r.routes.every(x=>LANES.includes(x)),'INVALID_OWNER_ROUTE');
  check(r.locator==null||typeof r.locator==='string'&&r.locator.length<=8192,'INVALID_SOURCE_LOCATOR');
  return {review_ref:r.review_ref,pointer_sha256:r.pointer_sha256,name:r.name,locator:r.locator??'',
   source_sha256:SHA.test(r.source_sha256??'')?r.source_sha256:null,
   source_digest_claim:r.source_sha256===unresolved?unresolved:r.source_digest_claim??null,rights_status:r.rights_status,
   routes:[...new Set(r.routes)].sort(),native_mint:false,rights_approved:false};
 });
 return result.sort((a,b)=>a.review_ref<b.review_ref?-1:a.review_ref>b.review_ref?1:0);
}
function validateIndex(index){
 check(index?.schema===INDEX_SCHEMA&&SHA.test(index.raw_index_sha256),'INVALID_LOCAL_INDEX');
 check(index.canonical_parent==='cgx:root:cognigrex'&&index.load_alias==='LOAD.cgx','WRONG_PARENT');
 return rows(index.records);
}
export async function importLoadIndex(input){
 const bytes=typeof input==='string'?new TextEncoder().encode(input):input;
 check(bytes instanceof Uint8Array&&bytes.length<=LIMIT,'INDEX_SIZE_LIMIT');
 const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
 const original=JSON.parse(text.replace(/^\uFEFF/,''));
 check(original.schema==='CGX-ONE-LOAD-INTAKE/0.17'&&original.parent==='Cognigrex.cgx'&&original.child==='LOAD.cgx'&&original.native_mint===false,'UNQUALIFIED_LOAD_INDEX');
 return {schema:INDEX_SCHEMA,canonical_parent:'cgx:root:cognigrex',load_alias:'LOAD.cgx',
  raw_index_sha256:await digest(bytes),records:rows(original.records)};
}
export async function buildBatchDraft(index,{selectedRefs=null,batchSize=25}={}){
 const records=validateIndex(index);
 check(Number.isInteger(batchSize)&&batchSize>=1&&batchSize<=100,'INVALID_BATCH_SIZE');
 const selected=selectedRefs??records.map(r=>r.review_ref);
 check(Array.isArray(selected)&&selected.length>0&&selected.length<=2500&&new Set(selected).size===selected.length,'INVALID_SELECTION');
 const refs=new Set(records.map(r=>r.review_ref));
 check(selected.every(x=>refs.has(x)),'UNKNOWN_SELECTED_REFERENCE');
 const chosen=new Set(selected);
 const leaves=[];
 for(const r of records.filter(r=>chosen.has(r.review_ref))){
  const holds=['SOURCE_VERSION_UNVERIFIED','RIGHTS_ACL_EVIDENCE_UNVERIFIED','NATIVE_OBJECT_ID_UNRESOLVED'];
  if(!r.source_sha256)holds.unshift('R0_BYTES_NOT_HASH_QUALIFIED');
  const leaf={reference:r.review_ref,source_sha256:r.source_sha256,source_digest_claim:r.source_digest_claim,source_version:null,
   owner_routes:r.routes,rights_label:r.rights_status,qualification_holds:holds,
   native_object_id:null,metadata_only:true};
  leaves.push({...leaf,leaf_sha256:await digest(canonical(leaf))});
 }
 const batches=[];
 for(let i=0;i<leaves.length;i+=batchSize){
  const entries=leaves.slice(i,i+batchSize);
  const body={ordinal:batches.length+1,depends_on:batches.length?batches.at(-1).batch_sha256:'LOAD_NATIVE_ADMISSION_REQUIRED',entries};
  batches.push({...body,batch_sha256:await digest(canonical(body))});
 }
 const payload={schema:DRAFT_SCHEMA,state:'PREPARED_UNSIGNED_METADATA_WITH_HOLDS',
  canonical_parent:index.canonical_parent,load_alias:index.load_alias,
  source_index_sha256:index.raw_index_sha256,source_records:records,
  selected_refs:leaves.map(x=>x.reference),batch_size:batchSize,batches,
  summary:{index_records:records.length,selected_records:leaves.length,batches:batches.length,
   source_digest_present:leaves.filter(x=>x.source_sha256).length,mint_ready_records:0},
  launch_binding:{chain_id:null,contract_address:null,contract_abi_sha256:null,issuer:null,
   transaction_data:null,fee_quote:null,nonce:null,signature:null},
  launch_requirements:['EXACT_CHAIN_AND_CONTRACT_ADAPTER','PER_ITEM_SOURCE_VERSION_RIGHTS_ACL',
   'ACCEPTED_OBJECT_IDS','SIGNED_ISSUER_ROOT_AND_SCOPED_LEASE','INDEPENDENT_TWO_NODE_DBR',
   'REPLAY_AND_IDEMPOTENCY_ACCEPTANCE','FRESH_OWNER_TRANSACTION_APPROVAL'],
  execution_policy:{sign:false,broadcast:false,auto_execute_on_chain_launch:false,native_admission:false,
   public_release:false,source_body_included:false},
  provenance:'Locally imported index is review evidence, not authenticated source or issuer acceptance'};
 return {...payload,plan_sha256:await digest(canonical(payload))};
}
export async function restoreBatchDraft(text){
 check(typeof text==='string'&&new TextEncoder().encode(text).length<=LIMIT,'DRAFT_SIZE_LIMIT');
 const draft=JSON.parse(text);
 check(draft?.schema===DRAFT_SCHEMA,'UNKNOWN_DRAFT_SCHEMA');
 const expected=await buildBatchDraft({schema:INDEX_SCHEMA,canonical_parent:draft.canonical_parent,
  load_alias:draft.load_alias,raw_index_sha256:draft.source_index_sha256,records:draft.source_records},
  {selectedRefs:draft.selected_refs,batchSize:draft.batch_size});
 check(canonical(draft)===canonical(expected),'DRAFT_CONTENT_OR_POLICY_MISMATCH');
 return {draft:expected,index:{schema:INDEX_SCHEMA,canonical_parent:expected.canonical_parent,
  load_alias:expected.load_alias,raw_index_sha256:expected.source_index_sha256,records:expected.source_records}};
}
