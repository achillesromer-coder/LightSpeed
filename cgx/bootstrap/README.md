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
