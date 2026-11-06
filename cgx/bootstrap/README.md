# CGX-enabled LightSpeed — one smart startup wizard (source review)

**Status:** review-only. **No local install, host start, deployment, CGX root write, LS GO activation, email, public release or archival deletion.**

This consolidates the owner-facing entry point into the existing CGX and LightSpeed managed-runtime architecture, not a new root or parallel queue. Keep Cognigrex.cgx and its accepted children authoritative. Romer.cgx, Eco.cgx, EMASSC.cgx and LS.cgx remain family members; LOAD.cgx is the Alexandria minimal-library alias whose exact accepted Object_ID must be read back. **UniSpace is a distinct product; LS GO is a Grex-scoped operator surface.**

## Read-only setup preview

Requires Node 20+ on a developer/operator checkout:

~~~sh
node cgx/bootstrap/cgxSetupCli.mjs --family Romer.cgx --mode first-run --device desktop --profile core --ls-go=true
node --test cgx/bootstrap/unifiedBootstrap.test.mjs
~~~

This returns a review plan with missing native proofs. It deliberately does not trust CLI flags as real RootAuthority or DBR receipts. Use the existing authorized host's lightspeed_runtime.startup_options for startup settings and lightspeed_runtime.runtime_productization for managed-runtime status/configure/install/update/rollback. That runtime manager already requires confirmed=true for mutations and delegates to the existing install PowerShell script. Do **not** execute those actions as a consequence of this plan alone.

The one-wizard flow has 11 staged steps: discover, resume, identity, sources, LOAD, CCC tools, runtime, Grex LS GO, node/agent handshake, verify and handoff. smart_setup_surface_contract.json describes accessible newcomer/returning/expert/operator interfaces, targeted repair, offline-first mode, permission/receipt rechecks and per-Grex source-halo preferences. Client-side simulations are not two independent node proofs.

Source reconciliation: the speech-derived text **GOT** is a nonblocking transcription ambiguity for *Git*, *GPT*, or possibly *LightSpeed GO*, depending on context. No independent GOT tool or FileSpace was identified. The Smart Setup UI and CLI no longer expose a GOT option or gate; see the source-only correction record.

## Duplicate decisions

Review startup_overlap_register.json. The original first-run and Trinity wizards are candidate predecessor UI sources, not a reason to auto-delete source files. The common runtime manager and the installer are deliberately distinct layers. Legacy ERC/CCC contracts are source inputs, not a parallel financial engine. Public LS GO static assets and UniSpace product pages have different privacy/release requirements.

## Integration and release gates

1. Verify live parent RootAuthority, state/DBR root and every child Object_ID; source-only S92 and draft review carriers are not live native admission.
2. Preserve original R0 data, verify rights, use bounded typed R1/R2 semantic adapters and source-quality/Frontier before Resolve. GPT original JSON shards and actual manual-intake folder are not proven complete.
3. Bind approved LOAD and CCC source-only code from draft PR #205, not by copying its reference catalogue into a second master. Confirm exact accepted LOAD alias.
4. Reconnect BouwerBase, check Python 3.11 runtime, slot and existing installer; collect real negative/positive receipts.
5. Private Grex LS GO: resolve issue #158 unauthenticated asset exposure, #161 genuine distinct-node FS/DS acceptance, host auth/lease and session revocation. Enable child toggles separately with verified readback.
6. Only after private CGX/LS GO acceptance pursue independent UniSpace product/free trial and website release. Source/IP privacy licences, actual HTTPS deployment and external outreach remain separate owner approvals.

See release_train_and_website_review.json for five successive release phases and public page candidates. No public site copy, download/trial link or release claim is validated by the presence of these files.

## Tests

~~~sh
node --test cgx/bootstrap/unifiedBootstrap.test.mjs
~~~

The tests are deterministic source-only regressions; they cannot certify a host install, a signed node handshake, full corpus ingestion, a live LS GO toggle, or an accepted web release.

## Browser Smart Setup preview

The additive [smartSetup.html](./smartSetup.html) offers an accessible progressive flow for selecting one recognised Grex, first-run/resume/repair/upgrade, runtime profile, offline LOAD, and a requested Grex LS GO toggle. It displays the wizard and explicit missing proof, **not an install success screen**. It imports the read-only setup planner. No permissions, DBR writes, network scans, local storage, credentials or external scripts are created by the preview.

The page is not wired to a live UniSpace product or LS GO server. Do not move this private review page or internal static assets into a public server or download bundle without #158 and source-rights approval.

## Latest context archive and continuation queue (2026-10-30)

**No new GPT export is expected soon.** Begin all future CGX/LightSpeed continuation from [chat-context closeout](./chat_context_closeout_2026-10-30.md), then the same [open-thread execution register](./open_threads_execution_register.json) already owned by this bootstrap lane. The checkpoint records current source/geometry/rights/function decisions and verified five-lane progress, with manual source handoff through the chat. It is not a full raw chat transcript or a native CGX admission. Preserve all originals and hold deletion and publication pending independent acceptance.

## Canonical continuation index — 2026-11-06 (read first)

The **existing** [open-thread execution register](./open_threads_execution_register.json) now contains `git_crosslane_inventory_20261106`: an authenticated GitHub snapshot of **64 open pull requests and 224 named branches** in the connected `achillesromer-coder/LightSpeed` source repository, each with immutable source head, base branch, retention and review disposition. Its earlier October `reviewed_pull_requests` entries are historical; **do not use them as the current PR heads or infer implementation from titles**. The register is a review source locator, not a new registry or a license to delete branches.

The source-only Windows startup diagnostics from dependent PR #215 are now exactly folded (three Git blob IDs preserved) into this review branch, with a fixture-only CI test. Two PR #215 paths overlap newer bootstrap README/workflow changes and **must not overwrite them**. Other branches — including Eco #207, scientific assurance #210, external LOAD adapters #211, Grex family ingestion #214 and fiction bridge #223 — remain provenance-linked for owner qualification; overlapping *paths* do not prove byte equality or canonical admission.

**Authority identity conflict:** accepted historical source projections name `Cognigrex.cgx` / `cgx:root:cognigrex` as one parent. Later owner-directed `CGX.cgx` universal root + `Build.cgx` is a *target migration proposal*, not permission to silently reparent Object_IDs or mint a second live root. Source R0/provider rights, current lease/issuer/revocation, independent two-node DBR #161, public/private routing #158, scientific assurance #209 and live product release remain HOLD until independently proven.

If another Codex/owner lane has locally edited or unpushed files, reconcile its exact blobs and consumer dependencies **before Git reset/merge/archive**. Preserve original repository branches, Drive files, FileSpace R0 and audit receipts until verified successor IDs and rollback are established. Remote Desktop Commander user reserve: **at least 5,205 monthly calls; avoid exploratory remote use**. No source-only CI or review ledger grants live mint/deploy authority.

## Windows owner-host diagnostics — source fold of PR #215

The original source-only Windows diagnostics are preserved in
[cgxWindowsBootEvidence.py](./cgxWindowsBootEvidence.py),
[test_cgx_windows_boot_evidence.py](./test_cgx_windows_boot_evidence.py) and
[cgx_setup_windows.ps1](../../tools/cgx_setup_windows.ps1). Their **Git blobs match
PR #215 exactly**. The unified bootstrap CI runs the original fixture-only
negative tests; no Windows service is started by CI.

The tool reads the existing S92 carrier/registry, family identity, **read-only**
operational SQLite, managed runtime prerequisites, bounded LOAD reference source
and local HTTP identity; it does not create an Object_ID, ingest source bodies,
accept a DBR, install a runtime or grant an issuer. Optional
`-PrepareMintReview` creates a new, owner-private **review-only** receipt and
is not a native mint or Git commit. Historical machine-specific checkout paths
in PR #215 are *source history*, not a supported universal installer path.

The optional `-BootExistingStack -ApproveNativeStackRestart` path **still
unconditionally throws `NATIVE_RESTART_HOLD`** before invoking the existing
launcher. Do not enable it until signed host lease, ACL, revocation and
independent two-node DBR evidence have passed live host acceptance. Source
presence and green Linux CI do not certify a working local Windows launch.

## Offline LOAD-to-UniSpace pre-mint review (2026-11-06)

The existing bootstrap review branch also carries source-only `cgxLeafEnvelopeReview.mjs`, `cgxPremintFamilyProjection.mjs`, and `cgxOfflineSourceProbe.mjs`. These reuse `cgxBatchConvergence.mjs` to form one Object_ID/version source candidate, deterministic SHA-256 source/leaf manifest and dependency pins, and an owner-only H0–H4 UniSpace view. A review `REQUEST_PLAN_ONLY` does not transfer or hydrate network bytes, authenticate rights, activate CCC or issue any token.

~~~sh
node --test cgx/bootstrap/*.test.mjs
node cgx/bootstrap/cgxOfflineSourceProbe.mjs --source cgx/bootstrap/unified_bootstrap_contract.json --object-id cgx:load:bootstrap-contract --version 1 --family Cognigrex.cgx --owner achilles --semantic-key load:bootstrap-contract
~~~

The probe reads a bounded 60 MiB-or-smaller regular source file, verifies exact byte reconstruction and prints a redacted JSON receipt (source digest, byte/leaf counts, immutable manifest digest; no source paths or original text). Rights/ACL remain unknown and all public/private native authority checks remain held until an authenticated independent proof is supplied. It never writes a source copy or calls a network service. Public preview is denied even for a caller-labelled `public_clear` source until separately authorised release.

The CI workflow now runs **all** bootstrap `*.test.mjs` files rather than only the three original suites. Actual host tests and signed independent DBR/issuer confirmation remain separate. The initial reviewed test suite passed locally on BouwerBase under Node 22 and Python 3.11, but source-only tests are not a proof of product deployment.

**Mainline reconciliation:** The review branch retains both the pre-existing Smith receipt/CPU-admission regressions from `main` and the scoped Neo singleton PID-reuse negative from this review lane. `cgxManifestIntegrityReview.py` checks exact newline-normalised SHA-256 and byte length of all 118 declared LightSpeed Runtime source records. Its output is source-integrity evidence, not a native execution approval. No original source or historical worktree should be deleted from this merge.

**LOAD source-branch integration review:** The bootstrap review worktree now combines the existing LOAD/Alexandria source-review branch without creating another LOAD root, catalogue or DBR. Windows CRLF checkout bytes may differ from the canonical Git blob: the declared JSON source snapshots are checked against their original LF Git-blob fingerprints; none of the 14 pinned source-register SHA-1 IDs was silently rebaselined. The source-only leaf request planner also rejects Windows separator strings in candidate keys before permission checks. `cgxLoadCrossLaneReview.test.mjs` verifies the integrated existing LOAD catalogue (131 indexed refs; 45 CCC routes), source hash/reconstruction and disabled UniSpace H0–H4 execution. All native rights/signing/DBR/mint/publication holds remain in force.

## UniSpace isolated public release verification (issue #158)

The historical PR #188 public-viewer source and its blob-identity ledger remain immutable.
The ordinary `apps/lightspeed-go/dist` output must **never** be treated as the
CGX public-only deployment: the general Vite build can include LS GO `public/data`,
`public/review` and operator seed files. This is a pre-mint HOLD, not proof that
a deployed private endpoint is exposed.

A nonpublishing synthetic viewer candidate may be built into a fresh directory
outside the operator application, then independently re-read:

```bash
python apps/lightspeed-go/scripts/cgx_public_bundle_guard.py --output /tmp/unispace-cgx-review
python apps/lightspeed-go/scripts/cgx_public_bundle_guard.py --verify-output /tmp/unispace-cgx-review
```

The second command verifies the 12-file allowlist, immutable source bytes,
receipt, source-policy equivalence and isolation. It denies changed files,
extra private assets, altered host/rights claims, changed CSP and a generic operator `dist`.
It cannot approve actual publication, provider rights, signed issuer or two-node DBR.
The remaining acceptance work requires authenticated private-asset routing,
negative anonymous/revoked-session HTTP readback, source rights and founder release approval.
