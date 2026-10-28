/** #158 real repository-source negative review.
 * Reads only this checkout's Vite public/dist trees; never contacts a host,
 * serves private files, verifies licences, or grants release.
 * This test must not be represented as a deployed distribution/ACL check.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { scanUniSpaceViteStaticReview } from './cgxUniSpaceViteStaticScan.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const publicRoot = resolve(here, '../public');
const distRoot = resolve(here, '../dist');
const MAX_TRANSFER = 60 * 1024 * 1024;
const selection = () => ({
  parent_filespace: 'Cognigrex.cgx',
  object_id: 'WT-001',
  filespace: 'Romer.cgx',
  identity_status: 'SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED',
  evidence_class: 'scientific'
});
const permissions = () => ({
  mode: 'review_only', revoked: false,
  allowed_object_ids: ['WT-001'], allowed_filespaces: ['Romer.cgx']
});
const input = () => ({
  selection: selection(), client_permissions: permissions(),
  public_root: publicRoot,
  // A tracked dist snapshot is not an independently verified deployed build.
  dist_root: existsSync(distRoot) ? distRoot : null,
  limits: { max_files: 256, max_total_bytes: 16 * 1024 * 1024, max_file_bytes: 2 * 1024 * 1024 }
});

test('actual Vite public-source tree has a fail-closed internal-review finding', async () => {
  const r = await scanUniSpaceViteStaticReview(input());
  assert.equal(r.state, 'SOURCE_SCAN_REVIEW_ONLY');
  assert.equal(r.parent_filespace, 'Cognigrex.cgx');
  assert.equal(r.candidate_object_id, 'WT-001');
  assert.equal(r.filespace, 'Romer.cgx');
  assert.ok(r.file_entries > 0);
  assert.ok(r.bytes_inspected > 0 && r.bytes_inspected <= MAX_TRANSFER);
  assert.ok(r.findings.some(x => x.reason_codes.includes('PRIVATE_REVIEW_MARKER_IN_STATIC_TREE')));
  assert.ok(r.findings.some(x => x.reason_codes.includes('INTERNAL_STATUS_IN_STATIC_JSON')));
});

test('one source original is byte-identical to its reviewed Git blob, without publishing its bytes', async () => {
  const bytes = await readFile(join(publicRoot, 'data', 'cgx_object_review_catalogue.json'));
  assert.ok(bytes.length > 0 && bytes.length < MAX_TRANSFER);
  const gitBlob = createHash('sha1')
    .update(Buffer.from('blob ' + bytes.length + '\0'))
    .update(bytes).digest('hex');
  assert.equal(gitBlob, 'e05b728562fc5c67a3fe5b283d03e28b8a375ca6');
  assert.match(bytes.toString('utf8'), /INTERNAL_REVIEW/);
});

test('source scan and optional tracked dist cannot establish deployed or HTTP acceptance', async () => {
  const r = await scanUniSpaceViteStaticReview(input());
  assert.equal(r.state, 'SOURCE_SCAN_REVIEW_ONLY');
  assert.equal(r.dist_source_scanned, existsSync(distRoot));
  for (const key of ['dist_verified','host_http_verified','release_accepted','native_admitted','canonical_mutation'])
    assert.equal(r[key], false, key);
  assert.equal(r.offline_hydration, 'H0_METADATA_ONLY');
  assert.equal(r.alias_role, 'ALEXANDRIA_ENTRY_NOT_PARENT');
});

test('report contains neither source bytes nor original asset paths', async () => {
  const r = await scanUniSpaceViteStaticReview(input());
  const serialized = JSON.stringify(r);
  assert.doesNotMatch(serialized, /cgx_object_review_catalogue\.json|component_geometry_atlas_public_review\.json|cgx_internal_review_projection\.json/);
  assert.equal(serialized.includes(publicRoot), false);
  assert.equal(serialized.includes(distRoot), false);
  assert.doesNotMatch(serialized, /PHYSICAL_NOT_RUN/);
});

test('revoked and cross-Grex review clients cannot inspect the real tree', async () => {
  const revoked = input(); revoked.client_permissions.revoked = true;
  assert.equal((await scanUniSpaceViteStaticReview(revoked)).hold_code, 'CLIENT_SCOPE_MISMATCH');
  const cross = input(); cross.client_permissions.allowed_filespaces = ['Eco.cgx'];
  assert.equal((await scanUniSpaceViteStaticReview(cross)).hold_code, 'CLIENT_SCOPE_MISMATCH');
});
