/** #158 source-review regression: no host, browser, network or release proof. */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const main = readFileSync(join(here, 'main.ts'), 'utf8');
const source = readFileSync(join(here, 'objectReview.ts'), 'utf8');
const publicRoot = join(here, '..', 'public', 'data');

test('object-review panel explicitly remains on security hold', () => {
  assert.match(main, /data-cgx-private-review-hold="issue-158"/);
  assert.match(main, /No private catalogue has been hydrated/);
});
test('object-review public catalogue is no longer automatically fetched', () => {
  assert.doesNotMatch(main, /cgx_object_review_catalogue\.json/);
  assert.doesNotMatch(main, /loadObjectReview\s*\(/);
});
test('component atlas public review is no longer automatically fetched by entry', () => {
  assert.doesNotMatch(main, /component_geometry_atlas_public_review\.json/);
  assert.doesNotMatch(main, /bindObjectReview\s*\(/);
});
test('H0-only offline boundary and exact child identity requirement are visible', () => {
  assert.match(main, /Offline view: H0 identity only/);
  assert.match(main, /exact Object_ID and child FileSpace/);
});
test('original object review implementation is preserved for authorised future host binding', () => {
  assert.match(source, /export const renderObjectReview/);
  assert.match(source, /export const loadObjectReview/);
});
test('existing public source assets remain: static exposure is NOT fixed by this patch', () => {
  assert.equal(existsSync(join(publicRoot, 'cgx_object_review_catalogue.json')), true);
  assert.equal(existsSync(join(publicRoot, 'component_geometry_atlas_public_review.json')), true);
});
test('internal CGX projection is held without public-static browser fetch', () => {
  assert.match(main, /data-cgx-private-projection-hold="issue-158"/);
  assert.match(main, /No private projection has been hydrated/);
  assert.doesNotMatch(main, /cgx_internal_review_projection\\.json/);
  assert.doesNotMatch(main, /fetch\\(cgxReviewUrl/);
  assert.doesNotMatch(main, /loadCgxReviewProjection\\s*\\(/);
});
test('CGX projection renderer is preserved and public static asset still requires isolation', () => {
  const renderer = readFileSync(join(here, 'cgxReview.ts'), 'utf8');
  assert.match(renderer, /export const loadCgxReviewProjection/);
  assert.equal(existsSync(join(publicRoot, 'cgx_internal_review_projection.json')), true);
});
test('CGX projection hold cannot assert host or release acceptance', () => {
  const segment = main.slice(main.indexOf('data-cgx-private-projection-hold'), main.indexOf('const type1CatalogueMount'));
  assert.match(segment, /root\\/DBR permission checks/);
  assert.match(segment, /Offline view: H0 identity only/);
  assert.doesNotMatch(segment, /host_http_verified:\\s*true|release_accepted:\\s*true|native_admitted:\\s*true/);
});
test('no claims of host or release acceptance in hold message', () => {
  const segment = main.slice(main.indexOf('data-cgx-private-review-hold'), main.indexOf('const cgxReviewMount'));
  assert.doesNotMatch(segment, /host_http_verified:\s*true|release_accepted:\s*true|native_admitted:\s*true/);
});
