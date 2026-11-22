# UniSpace / CGX — Batch Convergence and Regression Handoff (22 Nov 2026)

**Disposition:** SOURCE-ONLY INTEGRATION COMMITTED / CI PASS / NO MERGE / NO NATIVE ADMISSION / NO PUBLIC RELEASE.

## Parent and product invariants

One existing `cgx:root:cognigrex` authority, child classes `Romer.cgx`, `Eco.cgx`, `EMASSC.cgx` with nested `LS.cgx`. LOAD/Alexandria is a source/activation alias; FileSpace, DataSpace, SocialSpace, PrintSpace and IntelligenceSpace are workspace facets, not independent DBs, models or schedulers. UniSpace is the common R3/GUI projection. Original source rights, provider ACLs, bytes, hashes, versions, issuer/leases and native signed DBR remain separate, independently tested authorities.

## Implemented in the existing LightSpeed PR #230 review branch

| Component | Source | Function |
|---|---|---|
| Historical automation reviewer | `tools/cgx_automation_archive_review.py` | Bounded provider task/run source IDs, digest observation, idempotent deduplication and fail-closed incomplete histories |
| PR source snapshot | `cgx/review/unispace_git_pr_source_snapshot_20261122.json` | All 74 *public LightSpeed* PR heads/base branches at source observation; not a current mergeability claim |
| Dependency planner | `tools/cgx_unispace_branch_convergence.py` | Deterministic base-branch DAG, cycle/authority rejection, optional existing 51-gate validation |
| Competing-source footprints | `cgx/review/unispace_source_path_overlap_20261122.json` | Exact revision-aware changed-path lists for PR #205, #228, #230, #232, #233, closed #235 and #236 |
| Overlap reviewer | `tools/cgx_unispace_overlap_review.py` | Five shared-path collision pairs, risk classification without assuming byte or semantic equivalence |
| Hybrid source projection | `tools/cgx_unispace_hybrid_source_review.py` | Composes the above independent source reviews into one root/five-facet reference result, flags moved heads, unresolved bases and missing provider evidence |
| Regression | `tests/test_cgx_*archive_review.py`, `tests/test_cgx_unispace_*review.py`, `tests/test_cgx_unispace_branch_convergence.py` | 65 deterministic positive/negative source-bound cases in one read-only GitHub workflow |

The parent branch is `ops/canonical-queue-index-20261115` (PR #228). The dependent five-facet source candidate is PR #232. This set of commits is **only** on PR #230 and does not modify PR #228, #232 or `main`.

## Independently observed source comparisons

- Priority branch samples: **7**, path collision pairs: **5**.
- #228 ↔ #230: **6** shared changed paths, including LS GO runtime/UI and family topology.
- #228 ↔ #232: **19** shared changed paths, including UniSpace surface files.
- #228 ↔ closed #235: **3** shared shell implementation paths.
- #230 ↔ #232: **5** shared changed paths, including `tools/cgx_living_consolidation_review.py`, tests, `main.ts`, manifest and generated dist.
- #232 ↔ closed #235: **3** shared shell implementation paths. Source SHA and code differ. #232 includes later bounded FileSpace view and accessibility changes, so do not restore #235 wholesale.
- #205 LOAD and #236 PrintSpace are independent source candidates in this seven-branch footprint comparison. An absence of intersecting paths in this sample is not proof of domain compatibility or complete source independence.
- PR #230 was behind its moving parent by six commits at the comparison checkpoint. #232 was behind the updated PR #230 head and must be reconciled before promotion.
- The 51 source-review gate groups are owned in PR #232, *not recopied* into this PR. Source-only hybrid code can accept that original register as a separate pinned input; without it the gate-readback field remains zero and an explicit source hold is emitted.

## CI and regression acceptance

The consolidated `CGX Living Convergence Source Review` checks:
1. historical/provider intake: 17 cases;
2. PR dependency and source gate rules: 22 cases;
3. source path collision and non-equivalence: 15 cases;
4. one-root hybrid composition: 11 cases.

**65 test cases** (subject to exact-head CI recheck after this documentation commit), plus deterministic PR review-plan generation. The last validated combined run before this documentation update was https://github.com/achillesromer-coder/LightSpeed/actions/runs/45013148578 at `ffb3578047304b2b3e5f35a5af9d707fe1d76e0f`.

Do not confuse these source-only synthetic tests with real current branch mergeability, installed native readback, two-node DBR, physical PrintCeptor, full historical corpus ingestion, model weight training or customer release.

## Practical integration sequence

1. Resolve exact PR #228 / #230 / #232 branch ancestry using independent current-head comparisons. Preserve all branches until source parity and CI succeed. Do not use a bulk squash/merge on diverged source.
2. Review the five overlapping changed-path groups, prefer tracked source over built `dist` artefacts, and regenerate compiled assets from independently accepted source. Do not silently choose a winner for conflicting TypeScript, Python, manifests or tests.
3. Reconcile closed #231 source-manifest repair and closed #235 GUI changes against their actual accepted successor code; maintain predecessor provenance and prevent loss of unique functionality.
4. Check #205 LOAD and #206 bootstrap contracts against the admitted Cognigrex parent identity before selective code reuse. Keep auth, rights and source-envelope controls.
5. Keep #236 PrintSpace and Raphael/T173 experimental dependencies in their engineering evidence track. Software CI is not physical material/geometry proof.
6. Validate original 51 cross-space source gates from PR #232. Build independent FileSpace/DataSpace peer and DBR readback prior to native phase transition; five-facet R3 GUI must not grant lease or publish from navigation.
7. Test offline/web/Windows/mobile packaging and A11y, security, rights, rollback and real user workflows before separate release approval. SocialSpace/outreach, funding, institutional and public sites come after claim and consent review.
8. Old task outputs, closed PRs and archives remain original-source references. Conditionally archive only after complete original-byte and semantic crosswalk proof, independent signed DBR and restoration test, exact target owner approval and post-archive receipt. Deletion is not part of this batch.

## Automation boundaries

Reuse the five existing CGX hourly coordinators. Historical paused/completed task metadata does not mean the complete original run bodies are accessible. Do not introduce a new scheduler, operating store or resident agent; treat incremental source-review output as proposals for the existing lanes.

**No file deletion. No merge to main. No native DBR admission. No model training. No outreach or publication. No Remote Desktop Commander usage in this batch.**
