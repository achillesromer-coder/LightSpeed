/**
 * Verify one source-only cross-surface review entry IN the existing CGX open-thread register.
 * No network, file read/write, deletion, branch operation, issuer or new source registry.
 */
export const SCHEMA='CGX-CROSS-SURFACE-FOLD-AUDIT/0.1';
export const REVIEW_SCHEMA='CGX-CROSS-SURFACE-FOLD-REVIEW/0.1';
const ROOT='cgx:root:cognigrex';
const SHA40=/^[0-9a-f]{40}$/;
const EXPECTED=Object.freeze([
 'NCNBOUWER/Raphael',
 'achillesromer-coder/Romer-MPL',
 'achillesromer-coder/LightSpeed',
 'achillesromer-coder/Operations',
 'achillesromer-coder/Data'
]);
const GATES=Object.freeze(['G01','G02','G03','G04','G05','G06','G07']);
const BLOBS=Object.freeze([
 '67b737d466a4ef225857fde70061d4f9686ee4c5',
 '72ceb61ae624e48bd6c7ae8f670a10595ceb17be',
 '8b137891791fe96927ad78e64b0aad7bded08bdc',
 'df26a8d6805c030481a02a304977232676b2e0ec'
]);
const object=v=>v!==null && typeof v==='object' && !Array.isArray(v);
const no=(reason)=>({
 schema:SCHEMA,status:'HOLD_INVALID_REVIEW_EVIDENCE',reason,
 native_admitted:false,may_mint:false,may_sign:false,may_publish:false,
 may_delete:false,may_merge:false
});
export function auditCrossSurfaceFold(registry){
 if(!object(registry)||registry.schema!=='CGX-OPEN-THREAD-EXECUTION-REGISTER/0.2'||
 registry.state!=='SOURCE_REVIEW_ONLY'||registry.release_ready!==false||
 registry.deletion_ready_count!==0)return no('CANONICAL_REGISTRY_AUTHORITY_HOLD');
 const a=registry.cross_surface_fold_review_20261111;
 if(!object(a)||a.schema!==REVIEW_SCHEMA||
 a.status!=='SOURCE_ONLY_NO_NATIVE_AUTHORITY'||a.parent!==ROOT||
 a.sole_resolver!=='LOAD.cgx'||a.integration_pr!==206||
 a.integration_branch!=='review/cgx-ls-unified-bootstrap-20261028'||
 !SHA40.test(a.as_of_integration_head??''))return no('SOURCE_IDENTITY_OR_OWNER_HOLD');
 if(!Array.isArray(a.public_repositories)||a.public_repositories.length!==EXPECTED.length||
 new Set(a.public_repositories.map(r=>r?.name)).size!==EXPECTED.length||
 a.public_repositories.some(r=>!object(r)||!EXPECTED.includes(r.name)||
 r.default_branch!=='main'||!SHA40.test(r.tree_sha??'')||
 !Number.isSafeInteger(r.source_file_count)||r.source_file_count<1||
 r.disposition!=='RETAIN_DISTINCT_ORIGINAL_SOURCE'||
 r.snapshot_is_live!==false))return no('REPOSITORY_PROVENANCE_HOLD');
 if(!Array.isArray(a.exact_blob_overlap_groups)||a.exact_blob_overlap_groups.length!==4||
 new Set(a.exact_blob_overlap_groups.map(x=>x?.git_blob_sha)).size!==4||
 BLOBS.some(sha=>!a.exact_blob_overlap_groups.some(x=>x.git_blob_sha===sha))||
 a.exact_blob_overlap_groups.some(x=>!object(x)||!SHA40.test(x.git_blob_sha??'')||
 !Array.isArray(x.repositories)||new Set(x.repositories).size<2||
 x.repositories.some(r=>!EXPECTED.includes(r))||
 x.deletion_authorized!==false))return no('CROSS_REPO_SOURCE_EQUIVALENCE_HOLD');
 const l=a.local_worktree_review;
 if(!object(l)||!Number.isSafeInteger(l.registered)||l.registered<1||
 !Number.isSafeInteger(l.tracked_clean)||!Number.isSafeInteger(l.tracked_dirty)||
 !Number.isSafeInteger(l.missing)||l.tracked_clean<0||l.tracked_dirty<0||l.missing<0||
 l.tracked_clean+l.tracked_dirty+l.missing!==l.registered||
 l.untracked_not_scanned!==true||l.stale_prune_candidates!==0||
 l.worktrees_deleted!==0||l.branches_deleted!==0||
 l.junction_is_independent_source!==false||
 l.closeout_ready!==false)return no('LOCAL_WORKTREE_PROOF_OR_LIFECYCLE_HOLD');
 if(!object(a.cleanup)||a.cleanup.original_source_deletions!==0||
 a.cleanup.repos_archived!==0||a.cleanup.closure_ready!==false||
 a.cleanup.unqualified_delete_candidates!==0||
 a.cleanup.unapproved_archive_moves!==0||
 a.cleanup.independent_recovery_verified!==false)return no('DESTRUCTIVE_RETIREMENT_HOLD');
 if(!object(a.release)||a.release.native_mint_authorized!==false||
 a.release.independent_dbr_verified!==false||
 a.release.production_merge_completed!==false||
 a.release.public_launch_verified!==false||
 !object(a.release.gates)||GATES.some(k=>a.release.gates[k]!=='HOLD'))return no('LAUNCH_GATE_ESCALATION_HOLD');
 const providers=a.connected_surfaces;
 if(!object(providers)||providers.drive!=='PRIVATE_METADATA_POINTERS_ONLY'||
 providers.canva!=='CONCURRENT_OWNER_LANE_NO_WRITE'||
 providers.live_source_acl_verified!==false||
 providers.individual_private_assets_exported!==false)return no('EXTERNAL_PROVIDER_SCOPE_HOLD');
 const expectedSurfaces=[
  'cognigrex_parent','load_resolver','file_space','data_space',
  'unispace_product','ls_go_operator','public_viewer','local_devnet'
 ];
 if(!Array.isArray(a.functional_surfaces)||
 a.functional_surfaces.length!==expectedSurfaces.length||
 new Set(a.functional_surfaces.map(s=>s?.id)).size!==expectedSurfaces.length||
 expectedSurfaces.some(id=>!a.functional_surfaces.some(s=>s.id===id))||
 a.functional_surfaces.some(s=>!object(s)||
 typeof s.contract!=='string'||!s.contract.startsWith('cgx/')&&
 !s.contract.startsWith('apps/lightspeed-go/scripts/')||
 typeof s.owner!=='string'||!s.owner||
 typeof s.state!=='string'||!(s.state.endsWith('HOLD')||s.state.endsWith('ONLY')||
 s.state==='SOURCE_ONLY')))return no('FUNCTIONAL_SURFACE_CONVERGENCE_HOLD');
 if(!object(a.owner_automations)||a.owner_automations.enabled!==3||
 a.owner_automations.disabled!==2||
 a.owner_automations.auto_restart_disabled!==false)return no('AUTOMATION_OWNER_STATE_HOLD');
 return {
  schema:SCHEMA,status:'SOURCE_REFERENCES_RECONCILED_REVIEW_ONLY',
  parent:ROOT,resolver:'LOAD.cgx',
  source_repositories:a.public_repositories.length,
  source_file_refs:a.public_repositories.reduce((sum,x)=>sum+x.source_file_count,0),
  exact_cross_repo_blob_groups:a.exact_blob_overlap_groups.length,
  worktrees_reviewed:l.registered,
  worktree_tracked_clean:l.tracked_clean,
  worktree_tracked_dirty:l.tracked_dirty,
  no_stale_prune_candidates:l.stale_prune_candidates===0,
  cleanup_eligible:0,authority_holds:GATES,
  native_admitted:false,may_mint:false,may_sign:false,
  may_publish:false,may_delete:false,may_merge:false,
  source_current_after_snapshot:false,
  note:'Pointers only; provider heads, rights, worktree untracked state and consumer rollback must be reverified before any promotion'
 };
}
