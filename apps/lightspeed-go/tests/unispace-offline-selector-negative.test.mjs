import { test } from "vitest";
import assert from "node:assert/strict";
import { projectOwnerProgress } from "../src/ownerProgressProjection.ts";

// #158: an offline snapshot or a browser-supplied gateway claim is not an ACL grant.
const envelope = (object_id) => ({
  gateway: { session_verified:true, host_handshake_verified:true, root_acl_verified:true,
    object_acl_verified:true, source_rights_verified:true },
  source: { object_id, filespace:"Cognigrex.cgx/FileSpace", revision:"a".repeat(64) },
  bridge: { reachable:false },
  consumer: { heartbeat_fresh:true, pid_identity_verified:true, lock_verified:true,
    lease_verified:true, dispatch_ready:true },
  checkpoint: { object_id, filespace:"Cognigrex.cgx/FileSpace",
    source_revision:"a".repeat(64), reported_completed:12 },
  latest: { object_id, filespace:"Cognigrex.cgx/FileSpace",
    source_revision:"a".repeat(64), state:"RUNNING", completed:12, target:20 },
});

test("encoded, Unicode and delimiter-ambiguous selectors disclose no private R3", () => {
  const bad = ["%2e%2e", "%2F", "child%5csecret", "child?token=x",
    "child#fragment", "child\\secret", "сhild", "child\u0000secret"];
  for (const tail of bad) {
    const view = projectOwnerProgress(envelope("Cognigrex.cgx:/FileSpace/" + tail));
    assert.equal(view.access, "HOLD_SOURCE_IDENTITY", JSON.stringify(tail));
    assert.equal(view.object_id, null);
    assert.equal(view.progress, null);
    assert.equal(view.dispatch_authorized, false);
  }
});

test("offline bridge never converts claimed consumer readiness into execution authority", () => {
  const view = projectOwnerProgress(envelope("Cognigrex.cgx:/FileSpace/qualified-candidate-1"));
  assert.equal(view.bridge, "BRIDGE_OFFLINE");
  assert.equal(view.consumer, "CONSUMER_HELD");
  assert.equal(view.native_admitted, false);
  assert.equal(view.dispatch_authorized, false);
  assert.equal(view.public_publish_authorized, false);
});


test("foreign child and cross-source progress are denied without source hydration", () => {
  const id = "Cognigrex.cgx:/FileSpace/qualified-candidate-1";
  const foreign = envelope(id);
  foreign.source.filespace = "Cognigrex.cgx/Eco.cgx/FileSpace";
  const denied = projectOwnerProgress(foreign);
  assert.equal(denied.access, "HOLD_SOURCE_IDENTITY");
  assert.equal(denied.object_id, null);
  assert.equal(denied.progress, null);

  const mixed = envelope(id);
  mixed.latest.object_id = "Cognigrex.cgx:/FileSpace/another-source";
  const held = projectOwnerProgress(mixed);
  assert.equal(held.progress_binding, "HOLD_UNBOUND_PROGRESS");
  assert.equal(held.progress, null);
  assert.equal(held.dispatch_authorized, false);
  assert.equal(held.public_publish_authorized, false);
});


test("offline snapshot cannot borrow a different child checkpoint or a claimed session", () => {
  const id = "Cognigrex.cgx:/FileSpace/qualified-candidate-1";
  const crossed = envelope(id);
  crossed.checkpoint.filespace = "Cognigrex.cgx/Eco.cgx/FileSpace";
  const view = projectOwnerProgress(crossed);
  assert.equal(view.progress, null);
  assert.equal(view.dispatch_authorized, false);
  assert.equal(view.public_publish_authorized, false);

  const unverified = envelope(id);
  unverified.gateway.session_verified = false;
  const denied = projectOwnerProgress(unverified);
  assert.equal(denied.dispatch_authorized, false);
  assert.equal(denied.public_publish_authorized, false);
  assert.equal(denied.progress, null);
});


test("offline progress cannot hydrate a stale source revision or bypass rights", () => {
  const id = "Cognigrex.cgx:/FileSpace/qualified-candidate-1";
  const stale = envelope(id);
  stale.latest.source_revision = "b".repeat(64);
  const view = projectOwnerProgress(stale);
  assert.equal(view.progress_binding, "HOLD_UNBOUND_PROGRESS");
  assert.equal(view.progress, null);
  assert.equal(view.dispatch_authorized, false);

  const rights = envelope(id);
  rights.gateway.source_rights_verified = false;
  const denied = projectOwnerProgress(rights);
  assert.equal(denied.access, "HOLD_PRIVATE_SCOPE");
  assert.equal(denied.object_id, null);
  assert.equal(denied.progress, null);
});
