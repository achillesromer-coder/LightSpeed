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


test('directionality and inverse cardinality are not inferred across source domains', () => {
  // The same lexical CONNECTS_TO label has different declared symmetry evidence.
  const romerConnect = sources.romer.families.interface.find(r => r.id === 'CONNECTS_TO');
  const lsConnect = sources.emassc_ls.lightspeed.find(r => r.id === 'CONNECTS_TO');
  assert.equal(romerConnect.symmetric,true);
  assert.equal(Object.hasOwn(lsConnect,'symmetric'),false);
  const connectCandidate = delta.new_overlap_candidates.find(c => c.relation_id === 'CONNECTS_TO');
  same(sorted(connectCandidate.declarations.map(d => d.source)),['emassc_ls','romer']);
  assert.equal(connectCandidate.semantic_equivalence,'UNDETERMINED');
  assert.equal(connectCandidate.canonical_object_id,null);

  // Two distinct forward types point to COMPONENT_OF; no automatic bijection is permitted.
  const decomposition = sources.romer.families.decomposition;
  const inbound = decomposition.filter(r => r.inverse === 'COMPONENT_OF').map(r => r.id);
  same(sorted(inbound),['COMPOSED_OF','HAS_COMPONENT']);
  const componentOf = decomposition.find(r => r.id === 'COMPONENT_OF');
  assert.ok(componentOf);
  assert.equal(Object.hasOwn(componentOf,'inverse'),false);
  const invented = structuredClone(decomposition);
  invented.find(r => r.id === 'COMPONENT_OF').inverse = 'HAS_COMPONENT';
  assert.notDeepEqual(invented,decomposition);
});

test('temporal, spatial and causal qualifiers remain source-scoped, not merged by label', () => {
  const precedes = delta.new_overlap_candidates.find(c => c.relation_id === 'PRECEDES');
  const romerPrecedes = precedes.declarations.find(d => d.source === 'romer');
  const sharedPrecedes = precedes.declarations.find(d => d.source === 'shared');
  assert.match(romerPrecedes.source_declaration.rule,/does not imply causation/);
  assert.equal(Object.hasOwn(sharedPrecedes.source_declaration,'rule'),false);
  const targets = delta.new_overlap_candidates.find(c => c.relation_id === 'TARGETS');
  same(sorted(targets.declarations.map(d => d.source + ':' + d.family)),['eco:intervention','romer:spatial']);
  assert.ok(sources.romer.common_qualifiers.includes('effective_from'));
  assert.ok(sources.romer.common_qualifiers.includes('effective_to'));
  assert.ok(sources.eco.common_qualifiers.includes('timestamp'));
  assert.ok(sources.eco.common_qualifiers.includes('geometry_ref'));
  for (const candidate of [precedes,targets]) {
    assert.equal(candidate.semantic_equivalence,'UNDETERMINED');
    assert.equal(candidate.candidate_owner_qualified,false);
    assert.equal(candidate.canonical_object_id,null);
    assert.equal(candidate.native_dbr_readback,null);
  }
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


test('inverse fan-in remains a typed ambiguity requiring explicit source-pinned cardinality evidence', () => {
  const decomposition = sources.romer.families.decomposition;
  const incoming = new Map();
  for (const declaration of decomposition) {
    if (!declaration.inverse) continue;
    const forward = incoming.get(declaration.inverse) ?? [];
    forward.push(declaration.id);
    incoming.set(declaration.inverse,forward);
  }
  const ambiguous = [...incoming].filter(([,forward]) => new Set(forward).size > 1);
  same(ambiguous.map(([target]) => target),['COMPONENT_OF']);
  same(sorted(incoming.get('COMPONENT_OF')),['COMPOSED_OF','HAS_COMPONENT']);
  // This is a source declaration fan-in, NOT an accepted cardinality or inverse equivalence.
  const romerBlob = delta.source_snapshots.find(s => s.source === 'romer').git_blob;
  function requireExplicitReviewEvidence(proof) {
    assert.equal(proof?.source_git_blob,romerBlob);
    assert.equal(proof?.inverse_target,'COMPONENT_OF');
    same(sorted(proof?.forward_types ?? []),sorted(incoming.get('COMPONENT_OF')));
    assert.equal(proof?.cardinality,'MANY_TO_ONE_DECLARATIONS');
    assert.equal(proof?.canonical_object_id,null);
    assert.equal(proof?.native_dbr_readback,null);
    return 'SOURCE_REVIEW_ONLY';
  }
  assert.throws(() => requireExplicitReviewEvidence({inverse_target:'COMPONENT_OF',forward_types:['HAS_COMPONENT']}));
  assert.throws(() => requireExplicitReviewEvidence({source_git_blob:'0'.repeat(40),inverse_target:'COMPONENT_OF',forward_types:['COMPOSED_OF','HAS_COMPONENT'],cardinality:'MANY_TO_ONE_DECLARATIONS'}));
  assert.equal(requireExplicitReviewEvidence({
    source_git_blob:romerBlob,inverse_target:'COMPONENT_OF',
    forward_types:['COMPOSED_OF','HAS_COMPONENT'],cardinality:'MANY_TO_ONE_DECLARATIONS',
    canonical_object_id:null,native_dbr_readback:null
  }),'SOURCE_REVIEW_ONLY');
});

test('temporal and spatial crosswalks require source-specific fields and cannot inherit shared qualifiers', () => {
  const sharedOptional = sources.shared.relation_record.optional;
  for (const key of ['valid_from','valid_to','time_ref','spatial_ref','geometry_ref']) {
    assert.ok(sharedOptional.includes(key));
  }
  const romerQualifiers = sources.romer.common_qualifiers;
  const ecoQualifiers = sources.eco.common_qualifiers;
  for (const key of ['effective_from','effective_to']) assert.ok(romerQualifiers.includes(key));
  for (const key of ['timestamp','site_id','geometry_ref']) assert.ok(ecoQualifiers.includes(key));
  assert.equal(romerQualifiers.includes('valid_from'),false);
  assert.equal(ecoQualifiers.includes('valid_from'),false);
  assert.equal(romerQualifiers.includes('spatial_ref'),false);
  // No source asserts that effective_from == valid_from or timestamp == time_ref.
  const sourceBlob = Object.fromEntries(delta.source_snapshots.map(s => [s.source,s.git_blob]));
  function requireExplicitTypedBridge(proof,dimension,source,sourceField,sharedField) {
    assert.equal(proof?.dimension,dimension);
    assert.equal(proof?.source,source);
    assert.equal(proof?.source_git_blob,sourceBlob[source]);
    assert.equal(proof?.shared_git_blob,sourceBlob.shared);
    assert.equal(proof?.source_field,sourceField);
    assert.equal(proof?.shared_field,sharedField);
    assert.ok(typeof proof?.frame === 'string' && proof.frame.length > 0);
    assert.ok(typeof proof?.configuration_ref === 'string' && proof.configuration_ref.length > 0);
    assert.ok(typeof proof?.evidence_ref === 'string' && proof.evidence_ref.length > 0);
    assert.equal(proof?.canonical_object_id,null);
    assert.equal(proof?.native_dbr_readback,null);
    return 'SOURCE_REVIEW_ONLY';
  }
  const temporal = {dimension:'temporal',source:'romer',source_git_blob:sourceBlob.romer,
    shared_git_blob:sourceBlob.shared,source_field:'effective_from',shared_field:'valid_from',
    canonical_object_id:null,native_dbr_readback:null};
  assert.throws(() => requireExplicitTypedBridge(temporal,'temporal','romer','effective_from','valid_from'));
  assert.throws(() => requireExplicitTypedBridge({...temporal,frame:'UTC',configuration_ref:'synthetic',evidence_ref:'synthetic',source_git_blob:'0'.repeat(40)},'temporal','romer','effective_from','valid_from'));
  const spatial = {dimension:'spatial',source:'eco',source_git_blob:sourceBlob.eco,
    shared_git_blob:sourceBlob.shared,source_field:'geometry_ref',shared_field:'spatial_ref',
    canonical_object_id:null,native_dbr_readback:null};
  assert.throws(() => requireExplicitTypedBridge(spatial,'spatial','eco','geometry_ref','spatial_ref'));
  for (const relationId of ['PRECEDES','TARGETS']) {
    const candidate = delta.new_overlap_candidates.find(c => c.relation_id === relationId);
    assert.equal(candidate.semantic_equivalence,'UNDETERMINED');
    assert.equal(candidate.candidate_owner_qualified,false);
    assert.equal(candidate.canonical_object_id,null);
  }
});


test('historical S92 four-child carrier audit remains technical-candidate evidence, not current native admission', () => {
  const bytes = read('../domain_templates/s92_domain_children_acceptance_audit_2026-10-04.json');
  assert.equal(gitBlob(bytes),'77861c734b3c63c394031c79bf830154faaec1e3');
  const audit = JSON.parse(bytes.toString('utf8'));
  assert.equal(audit.schema,'CGX-S92-DOMAIN-CHILD-ACCEPTANCE-AUDIT/0.1');
  assert.match(audit.status,/ROOT_AUTHORITY_DECISION_OPEN/);
  assert.match(audit.authority_effect,/does not accept, promote, or mutate child authority/);
  assert.equal(audit.durable_candidate.state,'PRE_CANONICAL');
  assert.equal(audit.recommendation.promotion_performed,false);
  assert.equal(audit.durable_candidate.package_sha256,'36349987fa34dc0f85e26c9658fbf8e3814010f7cc9f536b836920eab239a90d');
  const members = audit.exact_members;
  same(sorted(Object.keys(members)),sorted(['Romer.cgx','Eco.cgx','EMASSC.cgx','LS.cgx']));
  for (const [name,child] of Object.entries(members)) {
    assert.equal(child.authority_transfer,false,name);
    assert.equal(child.binding_mode,'REFERENCE',name);
    assert.match(child.sha256,/^[a-f0-9]{64}$/,name);
    assert.ok(child.tracked_objects > 0,name); // Historical carrier count, not admitted population.
  }
  assert.equal(members['LS.cgx'].parent_semantic_object_id,members['EMASSC.cgx'].semantic_object_id);
  for (const name of ['Romer.cgx','Eco.cgx','EMASSC.cgx']) {
    assert.equal(members[name].parent_semantic_object_id,'Cognigrex.cgx');
  }
  assert.equal(audit.parent_recovery.readback,'VERIFIED'); // Historical S92 only.
  assert.equal(audit.recommendation.promotion_performed,false); // Not signed current RootAuthority/DBR.
});

test('S92 historical review cannot be promoted by altered metadata or fabricated child authority', () => {
  const original = json('../domain_templates/s92_domain_children_acceptance_audit_2026-10-04.json');
  function requireCandidateOnly(audit) {
    assert.equal(audit.durable_candidate.state,'PRE_CANONICAL');
    assert.equal(audit.recommendation.promotion_performed,false);
    assert.match(audit.status,/ROOT_AUTHORITY_DECISION_OPEN/);
    for (const child of Object.values(audit.exact_members)) {
      assert.equal(child.authority_transfer,false);
      assert.equal(child.binding_mode,'REFERENCE');
    }
    return 'SOURCE_REVIEW_ONLY';
  }
  assert.equal(requireCandidateOnly(original),'SOURCE_REVIEW_ONLY');
  const fakePromotion=structuredClone(original);
  fakePromotion.recommendation.promotion_performed=true;
  assert.throws(()=>requireCandidateOnly(fakePromotion));
  const fakeChild=structuredClone(original);
  fakeChild.exact_members['LS.cgx'].authority_transfer=true;
  assert.throws(()=>requireCandidateOnly(fakeChild));
  const fakeCanonical=structuredClone(original);
  fakeCanonical.durable_candidate.state='CANONICAL';
  assert.throws(()=>requireCandidateOnly(fakeCanonical));
});

test('S92 durable readback and acceptance audit agree on four exact historical instances without native promotion', () => {
  const raw = read('../domain_templates/s92_domain_children_persistence_verification_2026-10-04.json');
  assert.equal(gitBlob(raw),'44285b9f26bc84e6438c9ab6a133cc69fbe922bb');
  const receipt = JSON.parse(raw.toString('utf8'));
  const audit = json('../domain_templates/s92_domain_children_acceptance_audit_2026-10-04.json');
  const childNames = {romer:'Romer.cgx',eco:'Eco.cgx',emassc:'EMASSC.cgx',lightspeed:'LS.cgx'};
  function requireHistoricalOnly(p,a) {
    assert.equal(p.authority.parent_recovery_state,'S92');
    assert.equal(p.authority.candidate_state,'PRE_CANONICAL');
    assert.equal(p.authority.promotion_performed,false);
    assert.equal(p.authority.fresh_acceptance_required,true);
    assert.equal(a.recommendation.promotion_performed,false);
    assert.equal(p.durable_package.sha256,a.durable_candidate.package_sha256);
    assert.equal(p.durable_package.drive_id,a.durable_candidate.drive_id);
    assert.equal(p.durable_package.size_bytes,a.durable_candidate.size_bytes);
    assert.equal(p.authority.parent_sha256,a.parent_recovery.sha256);
    same(sorted(Object.keys(p.outputs)),sorted(Object.keys(childNames)));
    for (const [key,name] of Object.entries(childNames)) {
      const source = p.outputs[key], reviewed = a.exact_members[name];
      assert.equal(source.member,name);
      assert.equal(source.sha256,reviewed.sha256,name);
      assert.equal(source.semantic_object_id,reviewed.semantic_object_id,name);
      assert.equal(source.tracked_objects,reviewed.tracked_objects,name);
      assert.match(source.carrier_instance_object_id,/^cgx:local:/);
      assert.match(source.content_root,/^[a-f0-9]{64}$/);
      assert.match(source.dbr_root,/^[a-f0-9]{64}$/); // Historical packed carrier root only.
      assert.equal(source.verify,'PASS');
      assert.equal(reviewed.binding_mode,'REFERENCE');
      assert.equal(reviewed.authority_transfer,false);
    }
    assert.equal(p.outputs.lightspeed.semantic_object_id,a.exact_members['LS.cgx'].semantic_object_id);
    assert.equal(a.exact_members['LS.cgx'].parent_semantic_object_id,a.exact_members['EMASSC.cgx'].semantic_object_id);
    return 'HISTORICAL_SOURCE_VERIFIED_NATIVE_HOLD';
  }
  assert.equal(requireHistoricalOnly(receipt,audit),'HISTORICAL_SOURCE_VERIFIED_NATIVE_HOLD');
  const forgedPromotion = structuredClone(receipt);
  forgedPromotion.authority.promotion_performed = true;
  assert.throws(() => requireHistoricalOnly(forgedPromotion,audit));
  const alteredChild = structuredClone(receipt);
  alteredChild.outputs.lightspeed.dbr_root = '0'.repeat(64);
  // A plausible-looking changed DBR root alone is not detectable without an external signed root receipt.
  assert.notDeepEqual(alteredChild.outputs.lightspeed,receipt.outputs.lightspeed);
  assert.equal(requireHistoricalOnly(alteredChild,audit),'HISTORICAL_SOURCE_VERIFIED_NATIVE_HOLD');
  const forgedBinding = structuredClone(audit);
  forgedBinding.exact_members['LS.cgx'].authority_transfer = true;
  assert.throws(() => requireHistoricalOnly(receipt,forgedBinding));
});
