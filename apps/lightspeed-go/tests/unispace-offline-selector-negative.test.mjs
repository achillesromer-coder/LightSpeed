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
