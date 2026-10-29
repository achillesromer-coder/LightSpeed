import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import assert from 'node:assert/strict';

// Review-only source assertions. These do not authenticate underlying R0 bytes,
// establish a host session, verify a signed DBR, or grant native CGX admission.
const app = readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8');
const manifest = JSON.parse(readFileSync(new URL('../../../desktop/source-manifest.json', import.meta.url), 'utf8'));

function validateManifest(input) {
  assert.equal(input?.schema_version, 1);
  assert.ok(Array.isArray(input.records));
  const paths = new Set();
  for (const record of input.records) {
    assert.equal(typeof record.path, 'string');
    assert.ok(record.path.length > 0 && !record.path.startsWith('/') &&
      !record.path.includes('\\') && !/^[A-Za-z]:/.test(record.path) &&
      !record.path.split('/').some(part => part === '..' || part === '.' || part === ''),
      'manifest path must be relative and normalized');
    assert.ok(!paths.has(record.path), 'duplicate manifest path');
    paths.add(record.path);
    assert.match(record.sha256, /^[a-f0-9]{64}$/);
    assert.ok(Number.isSafeInteger(record.bytes) && record.bytes >= 0);
  }
  return paths;
}

const fixture = () => ({
  schema_version: 1,
  records: [{path:'safe/source.py',sha256:'a'.repeat(64),bytes:10}],
});

test('reconciled source manifest preserves 739 unique qualified references', () => {
  const paths = validateManifest(manifest);
  assert.equal(paths.size, 739);
  const site = manifest.records.find(r => r.path === 'LightSpeed_Runtime/lightspeed_runtime/site_link.py');
  assert.deepEqual(site, {
    path: 'LightSpeed_Runtime/lightspeed_runtime/site_link.py',
    bytes: 3684,
    sha256: 'ae38d576a41334fc513cc7ffb12b8e12edc726979fa64fc4d326489468aa1c0e',
  });
});

test('duplicate source paths fail closed', () => {
  const x = fixture();
  x.records.push({...x.records[0]});
  assert.throws(() => validateManifest(x), /duplicate manifest path/);
});

test('malformed source hash fails closed', () => {
  const x = fixture();
  x.records[0].sha256 = 'unverified';
  assert.throws(() => validateManifest(x));
});

test('traversal, absolute, and Windows paths fail closed', () => {
  for (const path of ['../private.txt', '/absolute/file', 'C:/local/file', 'safe\\unsafe', 'safe//file']) {
    const x = fixture();
    x.records[0].path = path;
    assert.throws(() => validateManifest(x), path);
  }
});

test('negative or non-integral byte counts fail closed', () => {
  for (const bytes of [-1, 1.25, '10', Number.MAX_SAFE_INTEGER + 1]) {
    const x = fixture();
    x.records[0].bytes = bytes;
    assert.throws(() => validateManifest(x), String(bytes));
  }
});

test('UniSpace identity and product navigation survive Neo integration', () => {
  for (const text of ['<h1>UniSpace</h1>', 'aria-label="UniSpace views"',
    'UniSpace on LightSpeed', 'Connections and capabilities are reported below']) {
    assert.ok(app.includes(text), text);
  }
});

test('Neo connection controls and event handlers remain explicit', () => {
  for (const text of ['id="mobile-connect-form"', 'id="mobile-disconnect"',
    'id="mobile-carrier"', 'id="mobile-signin"',
    'byId<HTMLFormElement>("mobile-connect-form").addEventListener("submit"',
    'byId("mobile-disconnect").addEventListener("click"']) {
    assert.ok(app.includes(text), text);
  }
});

test('bridge status never masquerades as host or DBR authority in the review UI', () => {
  for (const text of ['bridge responds; consumer proof separate',
    'Device identity: enrollment not verified.',
    'Execution and phone DBR verification require separate receipts.',
    'Reconnect never resubmits pending commands.']) {
    assert.ok(app.includes(text), text);
  }
});
