import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';

// The one existing CGX open-thread register carries review-source lineage;
// it is not a native authority, a release permission, or a deletion permit.
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const registry=JSON.parse(readFileSync(resolve(ROOT,'cgx/bootstrap/open_threads_execution_register.json'),'utf8'));
const audit=registry.git_crosslane_inventory_20261106;
const sha40=/^[0-9a-f]{40}$/;

test('cross-lane audit is in the canonical open-thread register, never a second root',()=>{
 assert.equal(registry.schema,'CGX-OPEN-THREAD-EXECUTION-REGISTER/0.2');
 assert.equal(audit.schema,'CGX-CANONICAL-GIT-CROSSLANE-SWEEP/0.1');
 assert.equal(audit.repository,'achillesromer-coder/LightSpeed');
 assert.equal(audit.integration_pr,206);
 assert.equal(audit.integration_native_authority,false);
 assert.equal(audit.semantic_authority_conflict.status,'VERSIONED_MIGRATION_PROPOSAL_NOT_NATIVE_REPARENTING');
 assert.equal(audit.counts.branch_deletions,0);
 assert.equal(audit.counts.original_source_deletions,0);
 assert.equal(audit.counts.production_merges,0);
 assert.equal(registry.release_ready,false);
});

test('every open PR is one uniquely identified original source ref, including dependent-base PRs',()=>{
 const prs=audit.open_prs;
 assert.equal(prs.length,audit.counts.open_prs);
 assert.equal(new Set(prs.map(x=>x.number)).size,prs.length);
 for(const p of prs){
  assert.match(p.head_sha,sha40);
  assert.ok(typeof p.base_branch==='string'&&p.base_branch.length);
  assert.ok(p.source_url.endsWith('/pull/'+p.number));
  // Different evidence lanes legitimately use different dispositions.
  // Enforce explicit, nonblank classification and deny automatic disposition
  // rather than restricting to a brittle vocabulary.
  assert.ok(typeof p.disposition==='string'&&p.disposition.length>=12);
  assert.ok(!p.disposition.includes('AUTO_DELETE'));
  assert.ok(!p.disposition.includes('NATIVE_MINTED'));
 }
 assert.ok(prs.some(x=>x.number===206&&x.disposition==='CANONICAL_SOURCE_REVIEW_BRANCH_UNMERGED'));
 assert.ok(prs.some(x=>x.base_branch!=='main'));
});

test('all branch refs remain individually retained, including those without open PRs',()=>{
 const branches=audit.branch_refs;
 assert.equal(branches.length,audit.counts.branches);
 assert.equal(new Set(branches.map(x=>x.ref)).size,branches.length);
 assert.ok(branches.some(b=>b.ref==='main'));
 assert.ok(branches.some(b=>b.open_pr===null));
 for(const b of branches){
  assert.match(b.sha,sha40);
  assert.equal(b.retention,'RETAIN_ORIGINAL_REF_PENDING_EXACT_OBJECT_AND_CONSUMER_PROOF');
 }
});

test('PR215 three implemented paths remain exact original Git blobs, and other two differ',()=>{
 const folded=audit.pr215_exact_source_fold;
 assert.equal(folded.source_pr,215);
 assert.equal(folded.integrated_files.length,3);
 assert.equal(folded.other_two_paths_not_identical.length,2);
 assert.equal(folded.closure_approved,false);
 for(const f of folded.integrated_files){
  // SHA is Git's original indexed blob, not Windows checkout CRLF content.
  const output=execFileSync('git',['rev-parse','HEAD:'+f.path],{
    cwd:ROOT,encoding:'utf8',timeout:3000
  }).trim();
  assert.equal(output,f.sha,'PR215 exact source drift: '+f.path);
 }
});

test('rights, native mint, local worktrees, and production release remain independent holds',()=>{
 assert.match(audit.repository_coverage,/LOCAL_REPOS_NOT_AUDITED/);
 assert.equal(audit.counts.unreviewed_local_worktrees,'UNKNOWN_CONCURRENT_CODEX_WORK');
 assert.ok(audit.next_gaps.some(x=>x.includes('#158')));
 assert.ok(audit.next_gaps.some(x=>x.includes('#161')));
 assert.ok(audit.next_gaps.some(x=>x.includes('original GPT')||x.includes('Original GPT')));
 assert.match(audit.deduplication_contract.retention,/No branch, repository/);
});
