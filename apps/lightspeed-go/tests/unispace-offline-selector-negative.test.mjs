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

// A deserialised offline file is untrusted: truthy strings and numeric flags
// must never impersonate host-verified boolean grants (#158).
test("offline forged truthy ACL flags cannot hydrate private owner progress", () => {
  const id = "Cognigrex.cgx:/FileSpace/qualified-candidate-1";
  for (const field of ["session_verified", "host_handshake_verified",
    "root_acl_verified", "object_acl_verified", "source_rights_verified"]) {
    for (const forged of ["true", 1, {}, []]) {
      const x = envelope(id);
      x.bridge.reachable = true;
      x.gateway[field] = forged;
      const view = projectOwnerProgress(x);
      assert.equal(view.access, "HOLD_PRIVATE_SCOPE", field);
      assert.equal(view.object_id, null);
      assert.equal(view.progress, null);
      assert.equal(view.dispatch_authorized, false);
      assert.equal(view.public_publish_authorized, false);
    }
  }
});

// #158: never forward private worker metadata, arbitrary source bodies or
// malformed progress numbers into the owner R3 scalar projection.
test("owner progress projection redacts injected private fields and malformed counters", () => {
  const id = "Cognigrex.cgx:/FileSpace/qualified-candidate-1";
  const x = envelope(id);
  x.bridge.reachable = true;
  x.checkpoint.database_integrity_verified = true;
  x.checkpoint.independently_verified_committed = -1;
  x.latest.completed = Number.POSITIVE_INFINITY;
  x.latest.observed_attempted = 1.5;
  x.latest.error = "secret token at /private/owner/database is locked";
  x.latest.raw_source_text = "PRIVATE_SOURCE_BODY";
  x.latest.access_token = "PRIVATE_TOKEN";
  x.source.private_locator = "C:/private/source";
  const view = projectOwnerProgress(x);
  assert.equal(view.access, "PRIVATE_SOURCE_REVIEW");
  assert.equal(view.progress.latest_state, "FAIL_CLOSED");
  assert.equal(view.progress.error_class, "SQLITE_DATABASE_LOCKED");
  assert.equal(view.progress.independently_verified_committed, null);
  assert.equal(view.progress.latest_completed, null);
  assert.equal(view.progress.observed_attempted, null);
  assert.equal(view.dispatch_authorized, false);
  assert.equal(view.public_publish_authorized, false);
  const serialized = JSON.stringify(view);
  for (const secret of ["PRIVATE_SOURCE_BODY", "PRIVATE_TOKEN", "C:/private/source", "/private/owner/"]) {
    assert.equal(serialized.includes(secret), false, secret);
  }
});
