// Source-only contract regression. Run: node --test cgx/domain_templates/unispace_adaptive_surface_acceptance.test.mjs
// This is NOT a browser ACL, DBR, native mint, or deployment acceptance test.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const dir = dirname(fileURLToPath(import.meta.url));
const load = (name) => JSON.parse(readFileSync(join(dir, name), "utf8"));
const acceptance = load("unispace_adaptive_surface_acceptance_20261102.json");
const policy = load("view_selection_policy.json");
const cases = new Map(acceptance.negative_acceptance_cases.map((item) => [item.id, item]));

test("only one primary view and policy precedence unchanged", () => {
  assert.equal(acceptance.projection.primary_view_count, 1);
  assert.equal(policy.hybridisation_policy.max_primary_views, 1);
  assert.deepEqual(acceptance.projection.policy_priority, policy.inputs_in_priority_order);
  assert.equal(acceptance.projection.secondary_inspector, "OPT_IN_ONLY");
});

test("all acceptance IDs unique and expected fail-closed cases present", () => {
  assert.equal(cases.size, 11);
  for (let n = 1; n <= 11; n++) {
    const id = `U-A${String(n).padStart(2, "0")}`;
    assert.ok(cases.has(id), id);
    assert.ok(cases.get(id).expected, id);
  }
});

test("offline fallback cannot become a stale private cache", () => {
  const c = acceptance.projection.offline_cache_policy;
  assert.equal(c.default, "NO_PRIVATE_OBJECT_OR_SOURCE_METADATA_CACHE");
  assert.equal(c.allowed, "OWNER_APPROVED_PUBLIC_SAFE_REDACTED_METADATA_ONLY");
  assert.equal(c.revoked_or_unverifiable, "DENY_PRIVATE_R3_AND_CLEAR_PRIVATE_CACHE");
  assert.match(c.private_r3_revalidation, /REVOCATION/);
  assert.match(cases.get("U-A10").expected, /^DENY_PRIVATE_OFFLINE_HYDRATION/);
});

test("HTTP 200 or bridge liveness cannot grant dispatch", () => {
  assert.equal(cases.get("U-A03").expected, "BRIDGE_REACHABLE_CONSUMER_HELD_NO_EXECUTION");
  assert.equal(cases.get("U-A11").expected, "BRIDGE_STATUS_ONLY_NO_EXECUTION_AUTHORITY");
  assert.match(acceptance.canonical_bindings.session, /SERVER_VERIFIED/);
});

test("missing geometry, rights, and source identity stay held", () => {
  assert.equal(cases.get("U-A01").expected, "NO_OBJECT_HYDRATION_FRONTIER");
  assert.equal(cases.get("U-A02").expected, "DENY_CROSS_CHILD_HYDRATION");
  assert.equal(cases.get("U-A05").expected, "FRONTIER_NOT_FAKE_GEOMETRY");
  assert.match(acceptance.canonical_bindings.object_id, /REQUIRED_FROM_ACCEPTED_RESOLVER/);
  assert.match(acceptance.canonical_bindings.source_rights, /REQUIRED/);
});

test("review source cannot claim installed, admitted, or public release", () => {
  assert.equal(acceptance.status, "SOURCE_ONLY_REVIEW_NOT_DEPLOYED");
  assert.equal(acceptance.release_authorised, false);
  assert.equal(acceptance.canonical_bindings.canonical_mutation, false);
  assert.ok(acceptance.pending_source_paths.every((p) => p.startsWith("apps/lightspeed-go/src/")));
  for (const gate of ["#158", "#161", "#209"]) assert.ok(acceptance.gates.includes(gate));
});
