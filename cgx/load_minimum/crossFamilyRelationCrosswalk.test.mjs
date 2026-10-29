// Source-only cross-family lexical overlap regression; never mints, admits, or resolves Object_IDs.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';

const sourceFiles = {
  romer: '../domain_templates/romer_relation_registry.json',
  eco: '../domain_templates/eco_relation_registry.json',
  emassc_ls: '../domain_templates/emassc_ls_relation_registry.json',
  shared: '../domain_templates/relation_qualifier_contract.json'
};
const read = relative => readFileSync(new URL(relative, import.meta.url));
const json = relative => JSON.parse(read(relative).toString('utf8'));
const delta = json('./cross_family_relation_overlap_delta_2026-10-29.json');
const prior = json('./eco_shared_relation_crosswalk_candidates_2026-10-29.json');
const sources = Object.fromEntries(Object.entries(sourceFiles).map(([key,path]) => [key,json(path)]));
const gitBlob = bytes => createHash('sha1').update(Buffer.concat([
  Buffer.from('blob ' + bytes.length + '\0'), bytes
])).digest('hex');
const same = (a,b) => assert.deepEqual(a,b);
const sorted = arr => [...arr].sort();

function declarations(source) {
  const registry = sources[source];
  const groups = source === 'shared' ? registry.shared_relation_types
    : source === 'emassc_ls' ? Object.fromEntries(
      ['emassc','lightspeed','bridge'].map(key => [key,registry[key]])
    ) : registry.families;
  return Object.entries(groups).flatMap(([family,items]) => items.map(item => ({
    source, family, source_declaration: item
  })));
}
const all = Object.keys(sourceFiles).flatMap(declarations);
const byId = new Map();
for (const row of all) {
  const entries = byId.get(row.source_declaration.id) ?? [];
  entries.push(row);
  byId.set(row.source_declaration.id, entries);
}
const overlapIds = sorted([...byId].filter(([,rows]) => new Set(rows.map(r => r.source)).size > 1).map(([id]) => id));
const priorIds = sorted(prior.candidates.map(c => c.relation_id));
const newIds = sorted(delta.new_overlap_candidates.map(c => c.relation_id));

function assertReviewOnly(document) {
  assert.equal(document.stage,'SOURCE_REVIEW_ONLY');
  assert.equal(document.status,'HOLD');
  assert.equal(document.new_qualified_object_ids,0);
  assert.equal(document.authority_transferred,false);
  assert.equal(document.readback_verified,false);
  same(sorted(document.new_overlap_candidates.map(c => c.relation_id)),newIds);
  assert.equal(new Set(newIds).size,newIds.length);
  for (const item of document.new_overlap_candidates) {
    assert.equal(item.semantic_equivalence,'UNDETERMINED');
    assert.equal(item.candidate_owner_qualified,false);
    assert.equal(item.source_rights_qualified,false);
    assert.equal(item.source_acl_qualified,false);
    assert.equal(item.canonical_object_id,null);
    assert.equal(item.native_dbr_readback,null);
    assert.equal(item.disposition,'HOLD');
    const expected = byId.get(item.relation_id);
    same(sorted(item.declarations.map(JSON.stringify)),sorted(expected.map(JSON.stringify)));
  }
}

test('original relation source Git blob bytes and qualifier versions are pinned', () => {
  for (const snapshot of delta.source_snapshots) {
    const actual = read(sourceFiles[snapshot.source]);
    assert.equal(gitBlob(actual),snapshot.git_blob,snapshot.source);
    assert.equal(sources[snapshot.source].schema,snapshot.schema);
    assert.equal(sources[snapshot.source].extends ?? null,snapshot.extends);
  }
  assert.equal(gitBlob(read('./eco_shared_relation_crosswalk_candidates_2026-10-29.json')),delta.prior_crosswalk.git_blob);
  assert.equal(sources.shared.schema,'CGX-RELATION-QUALIFIER/0.2');
  for (const source of ['romer','eco','emassc_ls']) assert.equal(sources[source].extends,'CGX-RELATION-QUALIFIER/0.1');
});

test('17 original cross-source lexical overlaps partition into six prior and eleven new candidates', () => {
  assert.equal(overlapIds.length,17);
  assert.equal(priorIds.length,6);
  assert.equal(newIds.length,11);
  same(sorted([...priorIds,...newIds]),overlapIds);
  same(sorted(delta.prior_crosswalk.previous_overlap_ids),priorIds);
  assert.equal(delta.findings.distinct_lexical_overlaps_all_sources,overlapIds.length);
  assert.equal(delta.findings.previously_recorded_eco_shared_ids,priorIds.length);
  assert.equal(delta.findings.new_distinct_lexical_overlap_ids,newIds.length);
});

test('all eleven source declarations are exact, reversible and explicitly noncanonical', () => {
  assertReviewOnly(delta);
});

test('negative mutations fail: missing relation, invented declaration, forged authority, and source drift', () => {
  const clone = () => structuredClone(delta);
  const omitted = clone(); omitted.new_overlap_candidates.pop();
  assert.throws(() => assertReviewOnly(omitted));
  const invented = clone(); invented.new_overlap_candidates[0].declarations[0].family = 'fabricated';
  assert.throws(() => assertReviewOnly(invented));
  const promoted = clone(); promoted.new_overlap_candidates[0].canonical_object_id = 'cgx:forged';
  assert.throws(() => assertReviewOnly(promoted));
  const owner = clone(); owner.new_overlap_candidates[0].candidate_owner_qualified = true;
  assert.throws(() => assertReviewOnly(owner));
  const forgedSource = clone(); forgedSource.source_snapshots[0].git_blob = '0'.repeat(40);
  assert.notEqual(gitBlob(read(sourceFiles.romer)),forgedSource.source_snapshots[0].git_blob);
});
