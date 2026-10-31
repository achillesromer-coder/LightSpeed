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


## Windows host connection, debug, boot and mint review

**Integration source:** [cgxWindowsBootEvidence.py](./cgxWindowsBootEvidence.py) and
[tools/cgx_setup_windows.ps1](../../tools/cgx_setup_windows.ps1).
These are additive to the existing setup planner and `tools/launch_lightspeed.ps1`.
They do **not** install or update a managed runtime; `runtime_productization` and
the canonical LightSpeed stack remain the sole environment owners.

The default command inventories the exact existing Windows environment and writes a
redacted, owner-private JSON receipt into Windows Downloads (exclusive-create, no
existing file overwritten):

~~~powershell
$repo = 'C:\LightSpeed_Consolidated\_analysis_remote\LightSpeed_Canonical'
& "$repo\tools\cgx_setup_windows.ps1" -Repo $repo -Mode resume -PrepareMintReview
~~~

For optional source-only LOAD catalogue metrics, supply an existing local
`online_registry_projection_2026-10-28.json` from the **reviewed #205 source**
with `-LoadSourceRegistry 'C:\path\to\review\online_registry_projection_2026-10-28.json'`.
This does not download sources, register LOAD, ingest source bodies, or accept a new Object_ID.

Only after the probe demonstrates that the **existing** stack prerequisites are
present, an owner-controlled Windows terminal can explicitly request the original
launcher and subsequent loopback readback:

~~~powershell
& "$repo\tools\cgx_setup_windows.ps1" -Repo $repo -Mode resume -BootExistingStack -ApproveNativeStackRestart
~~~

**Caution:** the original launcher may restart Ollama and start local services.
No PowerShell execution-policy override or privilege escalation is applied. Respect
managed script-signing restrictions. The boot action starts **only** the existing
LightSpeed stack, not a CGX mint workflow. The diagnostic report is computed
**before and after** boot and distinguishes the Desktop bridge from the UniSpace/LS GO page.

Host checks include: single Cognigrex semantic parent and domain children; exact S92
carrier SHA-256 and root registry; existing operational SQLite via `mode=ro` and
`query_only=ON`; original R0 hash; native parent state (which may remain `candidate`);
declared LOAD source-index identity; current managed Python, LS GO distribution and
canonical runner; existing owner setup planner and #214 family-ingestion source;
local loopback HTTP identity. Source Git HEAD and local results are **observations**,
not promotion authority.

The `-PrepareMintReview` option creates a **non-authorising review proposal** listing
source-reference candidates and holds; it neither mints nor commits native objects.
A verified historical S92 carrier is not enough to promote the operational parent.
Never infer signed issuer/revocation authority, owner ACL/rights, native DBR
readback or independent receiver from a status flag or an online registry projection.

The setup wizard is ready for source review; **full host setup is NOT certified**
until the host has an actually installed, reviewed integration of #213 (root
preflight), #214 (native family read-only ingestion and owner-private UniSpace view),
#205 (LOAD source metadata) and #206 (this existing unified startup lane), followed
by separately verified native acceptance. Remote Desktop Commander may be paired
while its command allowance is exhausted; do not retry a quota-blocked provider.

Fixture-only validation:

~~~sh
python3 cgx/bootstrap/test_cgx_windows_boot_evidence.py
node --test cgx/bootstrap/unifiedBootstrap.test.mjs cgx/bootstrap/cgxWindowsHostPreflightReview.test.mjs
~~~
