/** CGX source-only batch convergence. No I/O, mint, dispatch, privileges or release. */
export const SCHEMA = 'CGX-BATCH-CONVERGENCE-REVIEW/0.1';
const ROOT = 'cgx:root:cognigrex';
// Source-only gate names never establish a signed/accepted fact. See cgxPhaseAcceptance_v01.json.
export const PHASE_GATE_STATES=Object.freeze(['SOURCE_LANDED','R1_VERIFIED','R2_QUALIFIED','NATIVE_ADMITTED','LIVE_VERIFIED','OWNER_ACCEPTED','R3_VIEW_VERIFIED']);
export const NATIVE_ACTIVATION_DEPENDENCIES=Object.freeze({
  file_space:Object.freeze([]),
  unispace_file_space_control:Object.freeze(['file_space:OWNER_ACCEPTED']),
  data_space:Object.freeze(['file_space:OWNER_ACCEPTED','unispace_file_space_control:OWNER_ACCEPTED']),
  print_space:Object.freeze(['file_space:OWNER_ACCEPTED','data_space:OWNER_ACCEPTED'])
});
const VALID_GATES=new Set(PHASE_GATE_STATES);
const FAMILIES = new Set(['Cognigrex.cgx','Romer.cgx','Eco.cgx','EMASSC.cgx','LS.cgx']);
const RIGHTS = new Set(['public_clear','internal_only','restricted','unknown']);
const ACLS = new Set(['public','internal','owner_only','unknown']);
const ACTION_KINDS = new Set(['adapter','tool','widget','skillset','view','resolver']);
const ID = /^[a-z][a-z0-9:_./-]{0,127}$/;
const SHA = /^[0-9a-f]{64}$/;
const VERSION = /^(0|[1-9][0-9]{0,17})$/;
const validId = x=>typeof x==='string'&&ID.test(x)&&!/(^|[/:])\.\.($|[/:])/.test(x)&&!x.includes('://');
const object = x=>x!==null && typeof x==='object' && !Array.isArray(x);
const validString = x=>typeof x==='string' && x.length>0 && x.length<=256 && !/[\u0000-\u001f\u007f\u2028\u2029]/.test(x);
const sorted = xs => [...xs].sort((a,b)=>a<b?-1:a>b?1:0);
const uniq = xs => sorted([...new Set(xs)]);
const cmp = (a,b) => a<b?-1:a>b?1:0;
const bySource = (a,b)=>cmp(a.source_id,b.source_id)||cmp(BigInt(a.revision),BigInt(b.revision))||cmp(a.sha256,b.sha256)||cmp(a.family,b.family);
const blocked = (reason)=>({schema:SCHEMA,state:'DENIED_INVALID_REVIEW_INPUT',reason,source_records:[],capabilities:[],overlaps:[],blockers:[reason],native_admitted:false,may_mint:false,may_dispatch:false,may_publish:false,may_print:false,may_transact:false});
export function convergeCGXBatch(input={}) {
  if(!object(input)||input.parent!==ROOT) return blocked('INVALID_PARENT');
  const sources=input.sources??[], capabilities=input.capabilities??[], phases=input.phases??[], aliases=input.aliases??[];
  if(!Array.isArray(sources)||!Array.isArray(capabilities)||!Array.isArray(phases)||!Array.isArray(aliases)||sources.length>2500||capabilities.length>2500||phases.length>40||aliases.length>2500) return blocked('INVALID_BATCH_BOUNDS');
  if(!Number.isSafeInteger(input.transferred_bytes??0)||(input.transferred_bytes??0)<0||(input.transferred_bytes??0)>60*1024*1024) return blocked('TRANSFER_BUDGET_EXCEEDED');
  for(const x of sources){
    if(!object(x)||!validId(x.source_id)||!VERSION.test(x.revision??'')||!SHA.test(x.sha256??'')||!FAMILIES.has(x.family)||!validId(x.owner)||!validString(x.abi)||!validString(x.semantic_key)||!RIGHTS.has(x.rights)||!ACLS.has(x.acl)) return blocked('INVALID_SOURCE_IDENTITY_OR_CUSTODY');
  }
  for(const x of capabilities){
    if(!object(x)||!validId(x.capability_id)||!validId(x.source_id)||!validId(x.owner)||!ACTION_KINDS.has(x.kind)||!validString(x.abi))return blocked('INVALID_CAPABILITY_BINDING');
  }
  for(const x of aliases){if(!object(x)||!validId(x.alias)||!validId(x.target)||x.alias===x.target)return blocked('INVALID_ALIAS');}
  for(const x of phases){
    if(!object(x)||!validId(x.id)||!Number.isSafeInteger(x.ordinal)||x.ordinal<1||!Array.isArray(x.dependency)||x.dependency.length>40||x.dependency.some(d=>!validString(d)||!/^([a-z][a-z0-9_./-]*):([A-Z][A-Z0-9_]+)$/.test(d))||x.may_self_mint!==false)return blocked('INVALID_PHASE_CONTRACT');
  }
  const sourceRecords=[...sources].sort(bySource);
  const blockers=[]; const overlaps=[]; const aliasReport=[];
  const identityGroup=new Map(), semanticGroup=new Map(), sourceIds=new Set();
  for(const s of sourceRecords){
    sourceIds.add(s.source_id);
    const key=s.source_id+'@'+s.revision;
    if(!identityGroup.has(key)) identityGroup.set(key,[]);
    identityGroup.get(key).push(s);
    if(!semanticGroup.has(s.semantic_key))semanticGroup.set(s.semantic_key,[]);
    semanticGroup.get(s.semantic_key).push(s);
    if(s.rights==='unknown'||s.acl==='unknown')blockers.push('UNCLASSIFIED_RIGHTS_OR_ACL:'+key);
    if(s.rights==='restricted'&&s.acl==='public')blockers.push('RIGHTS_ACL_CONFLICT:'+key);
  }
  for(const [key, group] of [...identityGroup].sort((a,b)=>cmp(a[0],b[0]))){
    const distinct=uniq(group.map(x=>[x.sha256,x.family,x.owner,x.rights,x.acl,x.abi,x.semantic_key].join('|')));
    if(distinct.length>1){blockers.push('IDENTITY_VERSION_COLLISION:'+key);overlaps.push({kind:'CONFLICT_HOLD',key,variants:group.length});}
    else if(group.length>1)overlaps.push({kind:'SAME_VERSION_REPEATED_REFERENCE',key,count:group.length});
  }
  for(const [key,group] of [...semanticGroup].sort((a,b)=>cmp(a[0],b[0]))){
    const ids=uniq(group.map(x=>x.source_id));
    if(ids.length>1)overlaps.push({kind:'SEMANTIC_OVERLAP_REVIEW_ONLY',key,source_ids:ids,abi_variants:uniq(group.map(x=>x.abi)).length});
  }
  const aliasMap=new Map();
  for(const x of [...aliases].sort((a,b)=>cmp(a.alias,b.alias)||cmp(a.target,b.target))){
    if(aliasMap.has(x.alias)&&aliasMap.get(x.alias)!==x.target)blockers.push('ALIAS_COLLISION:'+x.alias);
    else aliasMap.set(x.alias,x.target);
    if(sourceIds.has(x.alias))blockers.push('ALIAS_SHADOWS_SOURCE_ID:'+x.alias);
    aliasReport.push({alias:x.alias,target:x.target,status:'REVIEW_ONLY_NOT_RESOLVED'});
  }
  for(const alias of aliasMap.keys()){
    let current=alias;const seen=new Set();
    while(aliasMap.has(current)){
      if(seen.has(current)){blockers.push('ALIAS_CYCLE:'+alias);break;}
      seen.add(current);current=aliasMap.get(current);
    }
    if(!sourceIds.has(current))blockers.push('ALIAS_TARGET_UNQUALIFIED:'+alias);
  }
  const ids=new Set();const phaseOrdinals=new Set();
  for(const p of phases){
    if(ids.has(p.id)||phaseOrdinals.has(p.ordinal)) blockers.push('PHASE_ID_OR_ORDINAL_COLLISION:'+p.id);
    ids.add(p.id);phaseOrdinals.add(p.ordinal);
  }
  const gates=new Map();
  for(const p of phases){
    for(const d of p.dependency){
      const pos=d.lastIndexOf(':');const id=d.slice(0,pos),gate=d.slice(pos+1);
      if(!ids.has(id))blockers.push('UNKNOWN_PHASE_DEPENDENCY:'+p.id+':'+id);
      if(!VALID_GATES.has(gate))blockers.push('AMBIGUOUS_OR_UNKNOWN_PHASE_GATE:'+p.id+':'+d);
      if(!gates.has(id))gates.set(id,new Set());gates.get(id).add(gate);
      const target=phases.find(x=>x.id===id);
      if(target&&target.ordinal>=p.ordinal)blockers.push('PHASE_BACKEDGE:'+p.id+':'+id);
    }
  }
  // Review dependency contracts are fixed by the existing phase owners; no unreviewed weaker gate substitutions.
  for(const p of phases){
    const expected=NATIVE_ACTIVATION_DEPENDENCIES[p.id];
    if(expected&&!Array.isArray(expected))throw new TypeError('INVALID_STATIC_DEPENDENCY_CONTRACT');
    if(expected&&JSON.stringify(uniq(p.dependency))!==JSON.stringify(uniq(expected)))blockers.push('PHASE_DEPENDENCY_CONTRACT_DRIFT:'+p.id);
  }
  // Distinct evidence stages are not synonyms, but can be separately required by consumers.
  // The contract-drift comparison above decides if the requirement is exact.
  const capIds=new Map();
  const capReport=[...capabilities].sort((a,b)=>cmp(a.capability_id,b.capability_id)||cmp(a.source_id,b.source_id)).map(c=>{
    if(capIds.has(c.capability_id))blockers.push('DUPLICATE_CAPABILITY_ID:'+c.capability_id);capIds.set(c.capability_id,true);
    if(!sourceIds.has(c.source_id))blockers.push('CAPABILITY_SOURCE_UNRESOLVED:'+c.capability_id);
    const owners=uniq(sourceRecords.filter(s=>s.source_id===c.source_id).map(s=>s.owner));
    if(owners.length&&(!owners.includes(c.owner)||owners.length>1))blockers.push('CAPABILITY_OWNER_MISMATCH:'+c.capability_id);
    const sourceBindings=sourceRecords.filter(s=>s.source_id===c.source_id);
    if(sourceBindings.length&&sourceBindings.some(s=>s.abi!==c.abi))blockers.push('CAPABILITY_ABI_NOT_SOURCE_QUALIFIED:'+c.capability_id);
    if(sourceBindings.some(s=>s.rights==='unknown'||s.acl==='unknown'||s.rights==='restricted'&&s.acl==='public'))blockers.push('CAPABILITY_SOURCE_RIGHTS_HOLD:'+c.capability_id);
    return {capability_id:c.capability_id,source_id:c.source_id,kind:c.kind,owner:c.owner,abi:c.abi,state:'QUALIFICATION_ONLY_NO_RUNTIME_BIND'};
  });
  return {schema:SCHEMA,state:blockers.length?'BATCH_REVIEW_WITH_HOLDS':'BATCH_REVIEW_ASSEMBLED',parent:ROOT,
    source_records:sourceRecords.map(x=>({source_id:x.source_id,revision:x.revision,sha256:x.sha256,family:x.family,owner:x.owner,rights:x.rights,acl:x.acl,abi:x.abi,semantic_key:x.semantic_key,stage:'R1_R2_REVIEW_ONLY'})),
    overlaps,aliases:aliasReport,capabilities:capReport,
    phases:[...phases].sort((a,b)=>cmp(a.ordinal,b.ordinal)||cmp(a.id,b.id)).map(p=>({id:p.id,ordinal:p.ordinal,dependency:[...p.dependency],status:'REVIEW_ONLY_NOT_NATIVE_ACCEPTED',signed_dependency_readback:'NOT_PRESENT_IN_SOURCE_REVIEW'})),
    blockers:uniq(blockers),metrics:{source_instances:sourceRecords.length,unique_source_ids:sourceIds.size,qualified_capability_refs:capReport.length,semantic_overlap_groups:overlaps.filter(x=>x.kind==='SEMANTIC_OVERLAP_REVIEW_ONLY').length,source_version_conflicts:overlaps.filter(x=>x.kind==='CONFLICT_HOLD').length,declared_transfer_bytes:input.transferred_bytes??0},
    hold_authority:['SIGNED_ROOT_ISSUER_REVOCATION_DBR','SOURCE_RIGHTS_AND_PRIVATE_ACL','ISSUE_158_PUBLIC_STATIC','ISSUE_161_TWO_NODE','ISSUE_209_SCIENCE','SMITH_SINGLETON','OWNER_PUBLICATION_AND_PHYSICAL'],
    native_admitted:false,may_mint:false,may_dispatch:false,may_publish:false,may_print:false,may_transact:false};
}
const escapeHTML=x=>String(x).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
/** Static print-to-PDF preview of actual provided source-only batch review; no scripts or external fetch. */
export function renderBatchReviewHTML(report){
  if(!object(report)||report.schema!==SCHEMA)throw new TypeError('UNVERIFIED_REVIEW_REPORT');
  const section=(title,items)=>`<section><h2>${escapeHTML(title)}</h2><ol>${items.map(x=>`<li>${escapeHTML(x)}</li>`).join('')}</ol></section>`;
  const phases=report.phases??[];
  const rows=phases.map(p=>`<tr><td>${escapeHTML(p.ordinal)}</td><td>${escapeHTML(p.id)}</td><td>${escapeHTML(p.status)}</td><td>${escapeHTML(p.dependency.join(', ')||'none')}</td></tr>`).join('');
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CGX batch alignment — source review only</title><style>body{font:15px/1.5 system-ui,sans-serif;max-width:1050px;margin:2rem auto;padding:0 1rem;color:#222}h1{font-size:1.6rem}h2{font-size:1.15rem}table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:.4rem;text-align:left}section{margin:1.4rem 0}small{color:#555}@media print{body{margin:0;max-width:none}section{break-inside:avoid}table{font-size:11px}}</style><h1>CGX — Batch Convergence / Print & Mint Review</h1><p><strong>${escapeHTML(report.state)}</strong> — ${escapeHTML(report.parent??'not verified')}</p><p>Source references: ${escapeHTML(report.metrics?.source_instances??0)}. Capabilities: ${escapeHTML(report.metrics?.qualified_capability_refs??0)}. Native admitted: NO. Release: HOLD.</p><table><thead><tr><th>Order</th><th>Phase</th><th>Evidence stage</th><th>Declared prerequisites</th></tr></thead><tbody>${rows}</tbody></table>${section('Alignment holds',report.blockers??[])}${section('Authority holds',report.hold_authority??[])}<small>Source-only, non-operational; no tokens, DBR, FileSpace objects, physical prints or active services minted.</small></html>`;
}
