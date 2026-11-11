import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {auditCrossSurfaceFold,SCHEMA} from './cgxCrossSurfaceFoldAudit.mjs';

const data=JSON.parse(readFileSync(new URL('./open_threads_execution_register.json',import.meta.url),'utf8'));
const fresh=()=>structuredClone(data);
const outcome=(mod)=>{const a=fresh();mod(a.cross_surface_fold_review_20261111);return auditCrossSurfaceFold(a);};

test('all five distinct GitHub public sources point at original trees without creating a sixth CGX root',()=>{
 const result=auditCrossSurfaceFold(fresh());
 assert.equal(result.schema,SCHEMA);
 assert.equal(result.status,'SOURCE_REFERENCES_RECONCILED_REVIEW_ONLY');
 assert.equal(result.source_repositories,5);
 assert.equal(result.source_file_refs,2194);
 assert.equal(result.exact_cross_repo_blob_groups,4);
 assert.equal(result.parent,'cgx:root:cognigrex');
 assert.equal(result.resolver,'LOAD.cgx');
 assert.equal(result.cleanup_eligible,0);
 for(const key of ['native_admitted','may_mint','may_sign','may_publish','may_delete','may_merge'])assert.equal(result[key],false,key);
 assert.equal(result.source_current_after_snapshot,false);
});
test('a changed root, secondary resolver or made-up repository is denied',()=>{
 for(const mutation of [
  a=>a.parent='cgx:root:second',
  a=>a.sole_resolver='OTHER_LOAD.cgx',
  a=>a.public_repositories[0].name='NEW_PUBLIC_ROOT',
  a=>a.public_repositories[1].name=a.public_repositories[0].name,
  a=>a.public_repositories[0].tree_sha='not-a-source-hash',
  a=>a.public_repositories[0].disposition='DELETE_REPO',
  a=>a.public_repositories[0].snapshot_is_live=true
 ]){
  const res=outcome(mutation);
  assert.equal(res.status,'HOLD_INVALID_REVIEW_EVIDENCE');
  assert.equal(res.may_delete,false);
 }
});
test('byte-identical cross repository blobs never entitle deletion, migration or source ownership',()=>{
 for(const mutation of [
  a=>a.exact_blob_overlap_groups[0].deletion_authorized=true,
  a=>a.exact_blob_overlap_groups[0].git_blob_sha='invalid',
  a=>a.exact_blob_overlap_groups[0].repositories=['NCNBOUWER/Raphael'],
  a=>a.cleanup.original_source_deletions=1,
  a=>a.cleanup.repos_archived=1,
  a=>a.cleanup.unapproved_archive_moves=1,
  a=>a.cleanup.independent_recovery_verified=true,
  a=>a.cleanup.closure_ready=true
 ]){
  const res=outcome(mutation);
  assert.equal(res.status,'HOLD_INVALID_REVIEW_EVIDENCE');
  assert.equal(res.cleanup_eligible,undefined);
 }
});
test('worktree status is evidence-limited: untracked content and alias consumers are held',()=>{
 for(const mutation of [
  a=>a.local_worktree_review.untracked_not_scanned=false,
  a=>a.local_worktree_review.worktrees_deleted=1,
  a=>a.local_worktree_review.branches_deleted=1,
  a=>a.local_worktree_review.junction_is_independent_source=true,
  a=>a.local_worktree_review.closeout_ready=true,
  a=>a.local_worktree_review.stale_prune_candidates=4
 ]){
  const res=outcome(mutation);
  assert.equal(res.status,'HOLD_INVALID_REVIEW_EVIDENCE');
 }
});
test('offline Git review never grants native mint, merge, publication, DBR or connector authority',()=>{
 for(const mutation of [
  a=>a.release.gates.G01='ACCEPTED',
  a=>a.release.gates.G04='PASS',
  a=>a.release.gates.G05='READY',
  a=>a.release.native_mint_authorized=true,
  a=>a.release.public_launch_verified=true,
  a=>a.release.production_merge_completed=true,
  a=>a.release.independent_dbr_verified=true
 ]){
  const res=outcome(mutation);
  assert.equal(res.status,'HOLD_INVALID_REVIEW_EVIDENCE');
  assert.equal(res.native_admitted,false);
 }
});
test('no raw Drive/Canva private metadata, provider ACL or disabled owner automation can be silently promoted',()=>{
 const text=JSON.stringify(fresh().cross_surface_fold_review_20261111);
 assert.doesNotMatch(text,/docs\.google\.com\/document\/d\/|hotdogg3211|achilles\.romer@gmail|private_key|client_secret|C:\\\\Users\\\\acc/i);
 for(const mutation of [
  a=>a.connected_surfaces.individual_private_assets_exported=true,
  a=>a.connected_surfaces.drive='PUBLIC_ASSETS',
  a=>a.connected_surfaces.live_source_acl_verified=true,
  a=>a.owner_automations.enabled=5,
  a=>a.owner_automations.auto_restart_disabled=true
 ]){
  const res=outcome(mutation);
  assert.equal(res.status,'HOLD_INVALID_REVIEW_EVIDENCE');
 }
});

test('every fold surface points to a real existing implementation contract',()=>{
 const surfaces=fresh().cross_surface_fold_review_20261111.functional_surfaces;
 assert.equal(surfaces.length,8);
 for(const s of surfaces)assert.ok(existsSync(new URL('../../'+s.contract,import.meta.url)),s.contract);
 for(const mutation of [
  a=>a.functional_surfaces[0].id='secondary_root',
  a=>a.functional_surfaces[1].state='NATIVE_ADMITTED',
  a=>a.functional_surfaces.pop(),
  a=>a.exact_blob_overlap_groups[0].git_blob_sha='0'.repeat(40)
 ])assert.equal(outcome(mutation).status,'HOLD_INVALID_REVIEW_EVIDENCE');
});
