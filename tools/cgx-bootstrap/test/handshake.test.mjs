import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  LOCAL_STATUS_URL, LOCAL_BOOTSTRAP_URL, MAX_STATUS_BYTES,
  classifyStatus, discoverLocal, discoverCgx, observeLocal, publicSkeleton,
} from "../src/handshake.mjs";

const cli = fileURLToPath(new URL("../bin/cgx.mjs", import.meta.url));
const healthy = {
  bridge: "ls-go", root: "D:\\LightSpeed\\App", ok: true,
  services: { db: true, storage: true, merovingian: true },
  auth: { configured: true, username: "DO_NOT_SHOW" },
};

test("Alexandria empty frame remains typed and never claims authority or secrets", () => {
  const s = publicSkeleton();
  assert.equal(s.schema_version, "cgx-public-bootstrap-v1");
  assert.equal(s.geometry.face_count, 12);
  assert.equal(s.geometry.edge_count, 30);
  assert.equal(s.geometry.vertex_count, 20);
  assert.equal(s.geometry.euler_characteristic, 2);
  assert.equal(s.geometry.cells.length, 12);
  assert.ok(s.geometry.cells.every(c => c.state === "NEUTRAL_UNBOUND" && c.source_ref === null));
  assert.equal(s.geometry.physical_volume_m3, null);
  assert.equal(s.network.gps, false);
  assert.equal(s.network.backscatter, false);
  assert.equal(s.network.network_scan, false);
  assert.equal(s.safety.device_identity_verified, false);
  assert.equal(s.safety.script_execution, false);
  assert.equal(s.root_authority, "UNASSIGNED");
  assert.ok(!JSON.stringify(s).includes("DO_NOT_SHOW"));
});

test("healthy HTTP bridge is NOT mistaken for consumer/job execution", async () => {
  const result = await discoverLocal({
    fetchImpl: async (url, options) => {
      assert.equal(url, LOCAL_STATUS_URL);
      assert.equal(options.method, "GET");
      assert.equal(options.redirect, "error");
      assert.equal(options.signal.aborted, false);
      return {
        ok: true, headers: { get: () => null }, body: null,
        text: async () => JSON.stringify(healthy),
      };
    },
  });
  assert.equal(result.state, "BRIDGE_RESPONSIVE_ONLY");
  assert.equal(result.services_candidate.database, true);
  assert.equal(result.consumer_state, "UNVERIFIED_NO_SIGNED_RECEIPT");
  assert.equal(result.queue_execution_state, "UNVERIFIED");
  assert.equal(result.authenticated, false);
  assert.equal(result.device_identity_verified, false);
  assert.ok(!JSON.stringify(result).includes("DO_NOT_SHOW"));
  assert.ok(!JSON.stringify(result).includes("LightSpeed\\App"));
});

test("unhealthy source is candidate not proof", () => {
  const s = classifyStatus({ ...healthy, ok: false });
  assert.equal(s.state, "BRIDGE_PRESENT_DEGRADED");
  assert.equal(s.authenticated, false);
});

test("spurious service and malformed JSON never produce a session", async () => {
  assert.equal(classifyStatus({ bridge: "not-cgx" }).state, "UNRECOGNISED_LOCAL_SERVICE");
  const r = await discoverLocal({ fetchImpl: async () => ({
    ok: true, headers: { get: () => null }, body: null,
    text: async () => "{broken",
  }) });
  assert.equal(r.state, "UNRECOGNISED_LOCAL_SERVICE");
  assert.equal(r.authenticated, false);
});

test("unreachable loopback does not imply the PC is offline", async () => {
  const result = await discoverLocal({ fetchImpl: async () => { throw new Error("ECONNREFUSED"); } });
  assert.equal(result.state, "LOCAL_BRIDGE_UNREACHABLE_OR_UNTRUSTED");
  assert.equal(result.local_host_offline_inferred, false);
  assert.equal(result.fallback, "PUBLIC_SKELETON_AVAILABLE");
});

test("discovery rejects redirects, non-200 and large responses", async () => {
  const redirect = await discoverLocal({ fetchImpl: async (_url, options) => {
    assert.equal(options.redirect, "error");
    throw new Error("unexpected redirect");
  } });
  assert.equal(redirect.state, "LOCAL_BRIDGE_UNREACHABLE_OR_UNTRUSTED");
  const notFound = await discoverLocal({ fetchImpl: async () => ({ ok: false, status: 404 }) });
  assert.equal(notFound.state, "LOCAL_BRIDGE_HTTP_ERROR");
  const tooLarge = await discoverLocal({ fetchImpl: async () => ({
    ok: true, headers: { get: () => String(MAX_STATUS_BYTES + 1) },
    text: async () => JSON.stringify(healthy),
  }) });
  assert.equal(tooLarge.state, "LOCAL_BRIDGE_UNREACHABLE_OR_UNTRUSTED");
});

test("bounded periodic sampling is read-only and never restores authentication", async () => {
  let calls = 0;
  let sleeps = 0;
  const result = await observeLocal({
    samples: 3, intervalMs: 20,
    discover: async () => { calls++; return { state: "BRIDGE_RESPONSIVE_ONLY" }; },
    sleep: async ms => { assert.equal(ms, 20); sleeps++; },
    now: () => "2026-10-12T00:00:00.000Z",
  });
  assert.equal(calls, 3);
  assert.equal(sleeps, 2);
  assert.deepEqual(result.observations.map(o => o.phase), [0, 1, 2]);
  assert.equal(result.session_restored, false);
  assert.equal(result.device_pairing_performed, false);
  await assert.rejects(() => observeLocal({ samples: 100 }), /samples/);
  await assert.rejects(() => observeLocal({ intervalMs: -1 }), /intervalMs/);
});

test("CLI seed prints JSON and does not contact any network or write by default", () => {
  const run = spawnSync(process.execPath, [cli, "seed"], { encoding: "utf8", timeout: 5000 });
  assert.equal(run.status, 0, run.stderr);
  const body = JSON.parse(run.stdout);
  assert.equal(body.geometry.face_count, 12);
  assert.equal(body.safety.file_system_mutation, false);
});

test("CLI seed write is exclusive and cannot traverse or touch Documents", async () => {
  const dir = await mkdtemp(join(tmpdir(), "cgx-bootstrap-test-"));
  try {
    const run = spawnSync(process.execPath, [cli, "seed", "--write"], {
      cwd: dir, encoding: "utf8", timeout: 5000,
    });
    assert.equal(run.status, 0, run.stderr);
    const file = join(dir, "alexandria.public.cgx");
    assert.equal(JSON.parse(await readFile(file, "utf8")).geometry.face_count, 12);
    assert.ok((await stat(file)).isFile());
    const overwrite = spawnSync(process.execPath, [cli, "seed", "--write"], {
      cwd: dir, encoding: "utf8", timeout: 5000,
    });
    assert.equal(overwrite.status, 2);
    const traversal = spawnSync(process.execPath, [cli, "seed", "--write", "../private.cgx"], {
      cwd: dir, encoding: "utf8", timeout: 5000,
    });
    assert.equal(traversal.status, 2);
    const protectedDir = join(dir, "Documents");
    await mkdir(protectedDir);
    const blocked = spawnSync(process.execPath, [cli, "seed", "--write", "new.cgx"], {
      cwd: protectedDir, encoding: "utf8", timeout: 5000,
    });
    assert.equal(blocked.status, 2);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});


test("CGX-native advertisement is a public, unauthenticated candidate only", async () => {
  const advertised = {
    schema_version: "cgx-bootstrap-advertisement-v1",
    namespace_candidate: "cgx://CGX.cgx",
    geometry: { vertex_count: 20, edge_count: 30, face_count: 12 },
    security: {
      device_authenticated: false,
      consumer_receipt_verified: false,
      commands_allowed: false,
    },
    semantics: { source_root: null },
    secret: "SECRET_MUST_NOT_PRINT",
  };
  let count = 0;
  const actual = await discoverCgx({ fetchImpl: async (url, options) => {
    count++;
    assert.equal(url, LOCAL_BOOTSTRAP_URL);
    assert.equal(options.redirect, "error");
    return {
      ok: true, status: 200, headers: { get: () => null },
      text: async () => JSON.stringify(advertised),
    };
  } });
  assert.equal(count, 1);
  assert.equal(actual.state, "CGX_PUBLIC_BOOTSTRAP_CANDIDATE");
  assert.equal(actual.consumer_verified, false);
  assert.equal(actual.authenticated, false);
  assert.equal(actual.session_restored, false);
  assert.ok(!JSON.stringify(actual).includes("SECRET_MUST_NOT_PRINT"));
});

test("CGX-native discovery falls back only to read-only legacy status", async () => {
  const calls = [];
  const result = await discoverCgx({ fetchImpl: async url => {
    calls.push(url);
    if (url === LOCAL_BOOTSTRAP_URL) return { ok: false, status: 404 };
    return {
      ok: true, status: 200, headers: { get: () => null },
      text: async () => JSON.stringify(healthy),
    };
  } });
  assert.deepEqual(calls, [LOCAL_BOOTSTRAP_URL, LOCAL_STATUS_URL]);
  assert.equal(result.state, "BRIDGE_RESPONSIVE_ONLY");
  assert.equal(result.protocol, "LEGACY_LIGHTSPEED_STATUS_FALLBACK");
  assert.equal(result.consumer_state, "UNVERIFIED_NO_SIGNED_RECEIPT");
});

test("CGX fake advertisement cannot promote source root or authentication", async () => {
  const forged = {
    schema_version: "cgx-bootstrap-advertisement-v1",
    namespace_candidate: "cgx://CGX.cgx",
    geometry: { vertex_count: 20, edge_count: 30, face_count: 12 },
    security: { device_authenticated: true, consumer_receipt_verified: true, commands_allowed: true },
    semantics: { source_root: "fake-private-root" },
  };
  const result = await discoverCgx({ fetchImpl: async () => ({
    ok: true, status: 200, headers: { get: () => null },
    text: async () => JSON.stringify(forged),
  }) });
  assert.equal(result.state, "UNRECOGNISED_CGX_ADVERTISEMENT");
  assert.equal(result.authenticated, false);
  assert.equal(result.consumer_verified, false);
});


test("native CGX bootstrap rejects partial or created HTTP responses even with valid JSON", async () => {
  const advertised = {
    schema_version: "cgx-bootstrap-advertisement-v1",
    namespace_candidate: "cgx://CGX.cgx",
    geometry: { vertex_count: 20, edge_count: 30, face_count: 12 },
    security: { device_authenticated: false, consumer_receipt_verified: false, commands_allowed: false },
    semantics: { source_root: null },
  };
  for (const status of [201, 206]) {
    const result = await discoverCgx({ fetchImpl: async (url, options) => {
      assert.equal(url, LOCAL_BOOTSTRAP_URL);
      assert.equal(options.redirect, "error");
      return {
        ok: true, status, headers: { get: () => null },
        text: async () => JSON.stringify(advertised),
      };
    } });
    assert.equal(result.state, "CGX_BOOTSTRAP_HTTP_ERROR");
    assert.equal(result.http_status, status);
    assert.equal(result.authenticated, false);
    assert.equal(result.consumer_verified, false);
  }
});
