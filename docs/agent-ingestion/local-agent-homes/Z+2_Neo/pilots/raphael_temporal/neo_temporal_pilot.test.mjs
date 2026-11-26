import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { NeoTemporalPilot } from "./neo_temporal_pilot.mjs";
const hash = text => createHash("sha256").update(text).digest("hex");
test("only Neo can occupy the pilot", () => {
  assert.throws(() => new NeoTemporalPilot({hash,agentId:"Achilles"}));
});
test("full lifecycle yields valid hash-linked provisional receipts", () => {
  const p=new NeoTemporalPilot({hash});
  const phases=["retrieve","interpret","document","receipt","close"];
  const values=[{source_ref:"local://evidence"},{claim:"inference"},{text:"draft"},{note:"provisional"},{reason:"done"}];
  phases.forEach((phase,i)=>p.advance({taskId:"T1",phase,payload:values[i],expectedSeq:i}));
  assert.equal(p.history().length,5);
  assert.equal(p.verify(),true);
  assert.equal(p.rehydrate().stages.T1,4);
  assert.equal(p.history().at(-1).epistemic,"workflow-complete-not-fact-validation");
});
test("source, order and stale sequence fail closed", () => {
  const p=new NeoTemporalPilot({hash});
  assert.throws(()=>p.advance({taskId:"T",phase:"interpret",expectedSeq:0}));
  assert.throws(()=>p.advance({taskId:"T",phase:"retrieve",expectedSeq:0}));
  p.advance({taskId:"T",phase:"retrieve",payload:{source_ref:"x"},expectedSeq:0});
  assert.throws(()=>p.advance({taskId:"T",phase:"interpret",payload:{claim_status:"verified"},expectedSeq:1}));
  assert.throws(()=>p.advance({taskId:"T",phase:"interpret",expectedSeq:0}));
});
test("retrospective fork cannot rewrite main and conflicting proposal preserves both tips",()=>{
  const p=new NeoTemporalPilot({hash});
  p.advance({taskId:"T",phase:"retrieve",payload:{source_ref:"x"},expectedSeq:0});
  p.advance({taskId:"T",phase:"interpret",payload:{meaning:"x"},expectedSeq:1});
  p.advance({taskId:"T",phase:"document",payload:{text:"main"},expectedSeq:2});
  const mainTip=p.history().at(-1).receipt_hash;
  p.fork({from:"main",branchId:"past-offset",atSeq:2});
  p.advance({branchId:"past-offset",taskId:"T",phase:"document",payload:{text:"alternative"},expectedSeq:3});
  const proposal=p.proposeMerge({source:"past-offset",target:"main"});
  assert.equal(p.history().at(-1).receipt_hash,mainTip);
  assert.deepEqual(proposal.conflict_task_ids,["T"]);
  assert.equal(proposal.state,"PROPOSAL_ONLY");
  assert.equal(proposal.dual_parent_receipts.length,2);
  assert.equal(p.verify("past-offset"),true);
});
test("independent changes remain proposal, and quiet monitoring is nonmutating",()=>{
  const p=new NeoTemporalPilot({hash});
  p.fork({from:"main",branchId:"side",atSeq:0});
  p.advance({taskId:"A",phase:"retrieve",payload:{source_ref:"A"},expectedSeq:0});
  p.advance({branchId:"side",taskId:"B",phase:"retrieve",payload:{source_ref:"B"},expectedSeq:1});
  assert.deepEqual(p.proposeMerge({source:"side",target:"main"}).conflict_task_ids,[]);
  const n=p.history().length;
  assert.equal(p.idleTick().mode,"STILL_MONITORING");
  assert.equal(p.idleTick({signals:["frontier-change"]}).mode,"WAKE_REVIEW");
  assert.equal(p.history().length,n);
});
test("rehydrated views cannot mutate receipt state",()=>{
  const p=new NeoTemporalPilot({hash});
  p.advance({taskId:"T",phase:"retrieve",payload:{source_ref:"x"},expectedSeq:0});
  const view=p.rehydrate();view.events[0].payload.source_ref="tampered";
  assert.equal(p.history()[0].payload.source_ref,"x");
  assert.equal(p.verify(),true);
});