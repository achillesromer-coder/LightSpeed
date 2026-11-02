import test from "node:test";
import assert from "node:assert/strict";
import { projectReadOnlyOperatorState as project } from "./unispace_operator_readonly_state.mjs";

const base = () => ({
  authority: { issuer_verified: true, session_valid: true, scope_allows: true,
    lease_valid: true, revocation_checked: true, root_acl_verified: true, server_signed_attestation_verified: true, dbr_readback_verified: true },
  binding: { object_id: "fixture:synthetic-object-1", child_filespace: "Romer.cgx",
    authorised_child_filespace: "Romer.cgx", source_version: "rev1", source_sha256: "a".repeat(64),
    rights: "QUALIFIED", resolver_receipt_verified: true, owner_binding_verified: true, admission: "NATIVE_ADMITTED" },
  runtime: { bridge_http_ok: true, consumer_state: "PID_REUSED_AFTER_HEARTBEAT_HOLD",
    consumer_lease_verified: false },
  progress: { latest_run_state: "FAIL_CLOSED", latest_attempted: 3216,
    last_committed: 3204, committed_target: 11568, committed_receipt_verified: true,
    error_code: "SQLITE_LOCKED" },
});

test("unverified issuer denies all private payloads", () => {
  const x = base(); x.authority.issuer_verified = false;
  assert.deepEqual(project(x).progress, null);
  assert.equal(project(x).view, "ACCESS_DENIED");
});
test("revocation check unavailable fails closed", () => {
  const x = base(); x.authority.revocation_checked = false;
  assert.equal(project(x).hydration, "H0_NONE");
});
test("exact child scope prevents cross-Grex hydration", () => {
  const x = base(); x.binding.authorised_child_filespace = "Eco.cgx";
  assert.equal(project(x).object_id, null);
  assert.equal(project(x).view, "OWNER_SOURCE_REVIEW_ONLY");
});
test("cross-child source cannot leak runtime checkpoint metadata", () => {
  const x = base();
  x.binding.authorised_child_filespace = "Eco.cgx";
  const out = project(x);
  assert.equal(out.progress, null);
  assert.equal(out.bridge, "BRIDGE_UNVERIFIED");
  assert.equal(out.consumer, "CONSUMER_HELD");
  assert.equal(out.dispatch_ready, false);
});
test("unqualified rights cannot leak a verified owner checkpoint", () => {
  const x = base();
  x.binding.rights = "UNREVIEWED";
  const out = project(x);
  assert.equal(out.progress, null);
  assert.equal(out.bridge, "BRIDGE_UNVERIFIED");
  assert.equal(out.object_id, null);
});
test("source-only candidate cannot become R3 by UI choice", () => {
  const x = base(); x.binding.admission = "SANDBOX_STAGED";
  assert.equal(project(x).view, "OWNER_SOURCE_REVIEW_ONLY");
  assert.equal(project(x).hydration, "H0_REVIEW_METADATA_ONLY");
});
test("missing source hash or rights blocks hydration", () => {
  for (const field of ["source_sha256", "rights"]) {
    const x = base(); x.binding[field] = "";
    assert.equal(project(x).object_id, null);
  }
});
test("HTTP 200 cannot grant consumer execution readiness", () => {
  const out = project(base());
  assert.equal(out.bridge, "BRIDGE_REACHABLE");
  assert.equal(out.consumer, "CONSUMER_HELD");
  assert.equal(out.dispatch_ready, false);
});
test("fail-closed progress retains verified checkpoint separately", () => {
  const out = project(base()).progress;
  assert.equal(out.latest_run_state, "FAIL_CLOSED");
  assert.equal(out.latest_attempted, 3216);
  assert.equal(out.last_committed, 3204);
  assert.equal(out.error_code, "SQLITE_LOCKED");
});
test("unverified checkpoint never displays an invented durable count", () => {
  const x = base(); x.progress.committed_receipt_verified = false;
  assert.equal(project(x).progress.last_committed, null);
  assert.equal(project(x).progress.checkpoint_state, "UNVERIFIED");
});
test("missing geometry never creates a fabricated twin", () => {
  assert.equal(project(base()).geometry, "FRONTIER_UNVERIFIED");
});
test("read-only projection never reflects private source paths or raw errors", () => {
  const x = base(); x.binding.source_ref = "C:\\private\\conversations-008.json";
  x.progress.error_code = "C:\\private\\sqlite.db is locked";
  const out = project(x);
  assert.equal(out.progress.error_code, null);
  assert.equal(JSON.stringify(out).includes("private"), false);
  assert.equal(out.release_authorised, false);
});

test("client-like flags without trusted attestation never qualify R3", () => {
  const x = base(); x.authority.server_signed_attestation_verified = false;
  assert.equal(project(x).view, "ACCESS_DENIED");
});
test("even a fully qualified synthetic fixture produces eligibility, not live hydration", () => {
  const out = project(base());
  assert.equal(out.view, "R3_ELIGIBILITY_CANDIDATE_NOT_HYDRATED");
  assert.equal(out.hydration, "H0_H2_ELIGIBILITY_ONLY_NO_FETCH");
});
