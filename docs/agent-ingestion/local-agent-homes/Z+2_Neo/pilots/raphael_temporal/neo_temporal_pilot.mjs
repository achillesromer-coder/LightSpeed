// Neo-only Raphael temporal pilot. No network, side effects, or canonical DBR mutation.

function canonical(value){
  if(value===null||typeof value==="string"||typeof value==="boolean") return value;
  if(typeof value==="number"&&Number.isFinite(value)) return value;
  if(Array.isArray(value)) return value.map(canonical);
  if(value&&typeof value==="object"&&Object.getPrototypeOf(value)===Object.prototype){
    const out={}; for(const k of Object.keys(value).sort()){if(value[k]!==undefined)out[k]=canonical(value[k]);}return out;
  }
  throw new Error("unsupported-json-value");
}

function sealHash(hash,payload){
  const digest=hash(JSON.stringify(canonical(payload)));
  if(typeof digest!=="string"||!/^[0-9a-f]{64}$/.test(digest))throw new Error("hash-must-be-sha256-hex");
  return digest;
}

class NeoTemporalPilot{
  constructor({hash,agentId="neo",maxEventsPerBranch=128,maxPayloadBytes=8192}={}){
    if(agentId!=="neo")throw new Error("pilot-agent-must-be-neo");
    if(typeof hash!=="function")throw new Error("trusted-hash-function-required");
    this.hash=hash;this.maxEventsPerBranch=maxEventsPerBranch;this.maxPayloadBytes=maxPayloadBytes;
    this.branches=new Map([["main",{id:"main",origin:null,baseEvents:[],events:[],stages:{}}]]);
    this.idleTicks=0;
  }
  branch(id){const b=this.branches.get(id);if(!b)throw new Error("unknown-branch");return b;}
  _history(b){return [...b.baseEvents,...b.events];}
  _append(b,kind,taskId,phase,payload,epistemic,expectedSeq){
    const events=this._history(b);
    if(expectedSeq!==events.length)throw new Error("stale-expected-sequence");
    if(b.events.length>=this.maxEventsPerBranch)throw new Error("bounded-branch-capacity");
    const clean=canonical(payload);
    if(JSON.stringify(clean).length>this.maxPayloadBytes)throw new Error("bounded-payload-capacity");
    const receipt={schema:"CGX-NEO-TEMPORAL-RECEIPT/0.1",agent_id:"neo",branch_id:b.id,seq:events.length,prev_hash:events.at(-1)?.receipt_hash||"GENESIS",kind,task_id:taskId,phase,payload:clean,epistemic};
    receipt.receipt_hash=sealHash(this.hash,receipt);b.events.push(receipt);
    return JSON.parse(JSON.stringify(receipt));
  }
  advance({branchId="main",taskId,phase,payload={},expectedSeq}={}){
    if(typeof taskId!=="string"||!taskId||taskId.length>128)throw new Error("task-id-required");
    const order=["retrieve","interpret","document","receipt","close"],step=order.indexOf(phase);
    if(step===-1)throw new Error("invalid-phase");
    const b=this.branch(branchId),previous=b.stages[taskId]??-1;
    if(step!==previous+1)throw new Error("invalid-temporal-transition");
    if(phase==="retrieve"&&(typeof payload.source_ref!=="string"||!payload.source_ref))throw new Error("source-reference-required");
    if(phase==="interpret"&&payload.claim_status==="verified")throw new Error("no-automatic-epistemic-promotion");
    const epistemic=({retrieve:"source-referenced",interpret:"inferred",document:"draft",receipt:"unsigned-provisional",close:"workflow-complete-not-fact-validation"})[phase];
    const out=this._append(b,"LIFECYCLE",taskId,phase,payload,epistemic,expectedSeq);
    b.stages[taskId]=step;return out;
  }
  fork({from="main",branchId,atSeq}={}){
    const parent=this.branch(from),parentEvents=this._history(parent);
    if(typeof branchId!=="string"||!/^[a-zA-Z0-9_-]{1,64}$/.test(branchId)||this.branches.has(branchId))throw new Error("invalid-or-existing-branch-id");
    if(!Number.isInteger(atSeq)||atSeq<0||atSeq>parentEvents.length)throw new Error("invalid-temporal-offset");
    const baseEvents=parentEvents.slice(0,atSeq),stages={};
    for(const e of baseEvents){if(e.kind==="LIFECYCLE")stages[e.task_id]=["retrieve","interpret","document","receipt","close"].indexOf(e.phase);}
    const b={id:branchId,origin:{branch:from,at_seq:atSeq,ancestor_hash:baseEvents.at(-1)?.receipt_hash||"GENESIS"},baseEvents,events:[],stages};
    this.branches.set(branchId,b);
    return this._append(b,"FORK",null,null,b.origin,"simulated-branch-only",atSeq);
  }
  history(branchId="main"){return JSON.parse(JSON.stringify(this._history(this.branch(branchId))));}
  rehydrate(branchId="main"){const b=this.branch(branchId);return {branch:branchId,origin:JSON.parse(JSON.stringify(b.origin)),stages:JSON.parse(JSON.stringify(b.stages)),events:this.history(branchId)};}
  verify(branchId="main"){
    const events=this._history(this.branch(branchId));let prev="GENESIS";
    for(let i=0;i<events.length;i++){const e=events[i],{receipt_hash,...withoutHash}=e;if(e.seq!==i||e.prev_hash!==prev||receipt_hash!==sealHash(this.hash,withoutHash))return false;prev=receipt_hash;}return true;
  }
  proposeMerge({source,target}={}){
    if(source===target)throw new Error("different-branches-required");
    const a=this._history(this.branch(source)),b=this._history(this.branch(target));
    let common=0;while(common<a.length&&common<b.length&&a[common].receipt_hash===b[common].receipt_hash)common++;
    const ca=new Set(a.slice(common).filter(e=>e.task_id).map(e=>e.task_id));
    const cb=new Set(b.slice(common).filter(e=>e.task_id).map(e=>e.task_id));
    const conflicts=[...ca].filter(t=>cb.has(t)).sort();
    const proposal={schema:"CGX-NEO-MERGE-PROPOSAL/0.1",source,target,common_prefix_count:common,source_tip:a.at(-1)?.receipt_hash||"GENESIS",target_tip:b.at(-1)?.receipt_hash||"GENESIS",conflict_task_ids:conflicts,dual_parent_receipts:[a.at(-1)?.receipt_hash||"GENESIS",b.at(-1)?.receipt_hash||"GENESIS"],state:"PROPOSAL_ONLY",admission:"REQUIRES_EXISTING_DBR_AUTHORITY_AND_CONFLICT_REVIEW"};
    return {...proposal,proposal_hash:sealHash(this.hash,proposal)};
  }
  idleTick({signals=[]}={}){if(!Array.isArray(signals))throw new Error("signals-array-required");this.idleTicks++;return {agent_id:"neo",mode:signals.length?"WAKE_REVIEW":"STILL_MONITORING",tick:this.idleTicks,persisted_event:false,signals:canonical(signals)};}
}

export { NeoTemporalPilot };

