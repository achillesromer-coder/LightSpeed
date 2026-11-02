import { test } from "vitest";
import assert from "node:assert/strict";
import { projectOwnerProgress } from "../src/ownerProgressProjection.ts";

const full = () => ({
  gateway: { session_verified:true, host_handshake_verified:true, root_acl_verified:true, object_acl_verified:true, source_rights_verified:true },
  source: { object_id:"Cognigrex.cgx:/FileSpace/qualified-candidate-1", filespace:"Cognigrex.cgx/FileSpace", revision:"a".repeat(64) },
  bridge: { reachable:true },
  consumer: { heartbeat_fresh:false, pid_identity_verified:false, lock_verified:false, lease_verified:false, dispatch_ready:false },
  checkpoint: { reported_completed:3200, independently_verified_committed:3200, database_integrity_verified:false },
  latest: { state:"FAIL_CLOSED", completed:0, target:0, observed_attempted:3216, error:"sqlite3.OperationalError: database is locked" },
});

test("no session/ACL/handshake yields no private metadata", () => {
  for (const key of Object.keys(full().gateway)) {
    const x=full(); x.gateway[key]=false;
    const view=projectOwnerProgress(x);
    assert.equal(view.access,"HOLD_PRIVATE_SCOPE");
    assert.equal(view.progress,null);
    assert.equal(view.object_id,null);
  }
  assert.equal(projectOwnerProgress(null).access,"HOLD_PRIVATE_SCOPE");
});

test("failed latest run zero does not erase reported checkpoint", () => {
  const v=projectOwnerProgress(full());
  assert.equal(v.access,"PRIVATE_SOURCE_REVIEW");
  assert.equal(v.bridge,"BRIDGE_REACHABLE");
  assert.equal(v.consumer,"CONSUMER_HELD");
  assert.equal(v.progress.latest_state,"FAIL_CLOSED");
  assert.equal(v.progress.latest_completed,0);
  assert.equal(v.progress.latest_target,0);
  assert.equal(v.progress.reported_checkpoint,3200);
  assert.equal(v.progress.independently_verified_committed,null);
  assert.equal(v.progress.observed_attempted,3216);
  assert.equal(v.progress.error_class,"SQLITE_DATABASE_LOCKED");
  assert.equal(v.native_admitted,false);
  assert.equal(v.dispatch_authorized,false);
});

test("verified DB integrity alone does not grant execution or native admission", () => {
  const x=full(); x.checkpoint.database_integrity_verified=true;
  const v=projectOwnerProgress(x);
  assert.equal(v.progress.independently_verified_committed,3200);
  assert.equal(v.dispatch_authorized,false);
  assert.equal(v.native_admitted,false);
});

test("bridge reachability cannot override stale PID/lease", () => {
  const x=full(); x.consumer.dispatch_ready=true;
  assert.equal(projectOwnerProgress(x).consumer,"CONSUMER_HELD");
  x.consumer.heartbeat_fresh=true;
  x.consumer.pid_identity_verified=true;
  x.consumer.lock_verified=true;
  x.consumer.lease_verified=true;
  const v=projectOwnerProgress(x);
  assert.equal(v.consumer,"CONSUMER_READY_CLAIM_NOT_AUTHORITY");
  assert.equal(v.dispatch_authorized,false);
});

test("wrong child FileSpace, missing ID or revision fails source identity", () => {
  for (const source of [
    {...full().source, filespace:"Eco.cgx/FileSpace"},
    {...full().source, object_id:"Eco.cgx:/FileSpace/foreign-object"},
    {...full().source, object_id:null},
    {...full().source, revision:"unsigned"},
  ]) {
    const x=full(); x.source=source;
    const v=projectOwnerProgress(x);
    assert.equal(v.access,"HOLD_SOURCE_IDENTITY");
    assert.equal(v.object_id,null);
    assert.equal(v.progress,null);
    assert.equal(v.bridge,"BRIDGE_WITHHELD");
    assert.equal(v.consumer,"CONSUMER_HELD");
    assert.equal(v.source_revision,null);
  }
});

test("private paths, tokens, raw prompts and arbitrary error text never project", () => {
  const x=full();
  x.private_path="C:\\Secret\\source.json";
  x.session_token="token-123";
  x.raw_prompts=["private text"];
  x.latest.error="C:\\Secret\\source.json token-123 internal error";
  const rendered=JSON.stringify(projectOwnerProgress(x));
  for (const secret of ["Secret","source.json","token-123","private text"]) assert.ok(!rendered.includes(secret));
  assert.ok(rendered.includes("REDACTED_FAILURE"));
});

test("malformed counts never masquerade as verified progress", () => {
  const x=full(); x.checkpoint.reported_completed=-1;
  x.checkpoint.independently_verified_committed=Number.NaN;
  x.checkpoint.database_integrity_verified=true;
  x.latest.observed_attempted=Infinity;
  const v=projectOwnerProgress(x);
  assert.equal(v.progress.reported_checkpoint,null);
  assert.equal(v.progress.independently_verified_committed,null);
  assert.equal(v.progress.observed_attempted,null);
});

test("Object_ID selector rejects traversal, ambiguous and empty path segments (#158)", () => {
  const rejected = [
    "Cognigrex.cgx:/FileSpace/../Eco.cgx/secret",
    "Cognigrex.cgx:/FileSpace/./qualified-candidate-1",
    "Cognigrex.cgx:/FileSpace/qualified-candidate-1/..",
    "Cognigrex.cgx:/FileSpace//qualified-candidate-1",
    "Cognigrex.cgx:/FileSpace/qualified-candidate-1/",
    "Cognigrex.cgx:/FileSpace/qualified-candidate-1:other",
    "Cognigrex.cgx:/FileSpace/",
    "Cognigrex.cgx:/FileSpace/" + "x".repeat(161),
  ];
  for (const object_id of rejected) {
    const x=full(); x.source.object_id=object_id;
    const view=projectOwnerProgress(x);
    assert.equal(view.access,"HOLD_SOURCE_IDENTITY",object_id);
    assert.equal(view.object_id,null);
    assert.equal(view.progress,null);
    assert.equal(view.bridge,"BRIDGE_WITHHELD");
  }
  const nested=full();
  nested.source.object_id="Cognigrex.cgx:/FileSpace/owner-reviewed/qualified-candidate-1";
  const view=projectOwnerProgress(nested);
  assert.equal(view.access,"PRIVATE_SOURCE_REVIEW");
  assert.equal(view.object_id,nested.source.object_id);
  assert.equal(view.native_admitted,false);
  assert.equal(view.dispatch_authorized,false);
});
