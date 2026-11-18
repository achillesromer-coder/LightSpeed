# UniSpace · CGX Native Operational Link and Launch Gate
**18 November 2026 — Source integration and private acceptance plan**

This record links the single existing UniSpace frontend, CGX selector catalogue,
host operational database, and installed .cgx carrier inventory. It does not
create a second registry, one-file clone of the operating system, new machine
daemon, distributed identity, signer, model trainer, or native CGX mint.

## Present machine observations

- BouwerBase local host: Desktop bridge HTTP 200; eight registered agent floors
  operational; database/storage and Merovingian supervisor healthy on last readback.
- Live Desktop bridge source is loaded from `D:\LightSpeed\Core`. The reviewed
  checkout is `D:\LightSpeed\Repositories\LightSpeed_Canonical`. These are
  not byte-identical. Deployed bridge does **not** expose the new checkpoint
  endpoint (HTTP 404), even though source tests pass.
- Existing `tools/reconcile_live_runtime.py plan` read-only audit:
  730 tracked target mappings, 12 changed Core mappings at initial audit,
  and live service ports 4173, 8080 and 8765.
- Its **apply** command is intentionally forbidden until clean `main` exactly
  matches `origin/main` and all managed service ports are stopped. Current
  checkout remains on `ops/canonical-queue-index-20261115` with unrelated
  outstanding source edits, so do not bypass the install gate.
- Existing `C:\UniSpace` installation: seven top-level `.cgx` filenames,
  six unique SHA-256 digests, with `LS.cgx` and `LightSpeed.cgx` an identical
  content-hash alias pair. Presence/hashes do not imply current native admission.
- Nine selector profiles are resolved directly from existing
  `plugins/source/selector_shortcalls.json` and
  `cgx/domain_templates/plugin_capability_routes.json`:
  Achilles, Neo, Athene, Raphael, Cognigrex, Romer-Grex, Eco-Grex,
  EMASSC and LightSpeed. No separate agent registry is created.

## Integrated source functions

1. **Canonical task checkpoint** — owner-authenticated task/run metadata,
   SHA-pinned composition, bounded CPU/RAM/jobs/TTL *planning*, exact
   readback and append-only revocation in `operational_events` in the
   existing `lightspeed_unified.db`. There are no model weights or file
   bytes in these records, and no independent `family.sqlite3`.
2. **System-panel checkpoint interface** — one dynamic adjunct to the
   existing UniSpace System view. Role and read-only capability choices
   come from the backend registry; owner session and current selector
   view revision are required. Creating a checkpoint is an owner action,
   not native minting or execution.
3. **Family topology endpoint** — current nine selector profiles and
   installed carrier hashes, with hash-equal aliases identified. A source
   profile, installed carrier and independently qualified runtime are
   deliberately different conditions.
4. **CGX ternary review reference** — reuse the currently implemented
   composition_ternary_root and SHA-256 identity. These are not a verified
   native T173 codec, geometry-based reasoning engine or T174 mint.
5. **Existing FileSpace/DataSpace** — the operational database is reused;
   node-root registry and independent peer transport are not activated
   by this integration. No content hydration permissions are inferred.
6. **PrintSpace and domain Grexes** — source selectors and installed
   carrier metadata are linked, while physical actuation, proposed science
   and release qualification remain separate technical acceptance steps.

## Release gate sequence

1. Finish review and merge through the normal owner-controlled source
   acceptance flow; never merge this branch implicitly or delete the three
   unrelated pending source files. Reconcile draft PR #227's role-grant
   semantics independently; do not install its second review database.
2. Before live rollout, verify singleton ownership, parent process, host
   authority, memory/disk guard, pending jobs, queue-drain and recovery
   window. Create an exact backup of every changed deployed runtime file
   and record its SHA-256 and a tested rollback command.
3. Run the existing reconciliation tool's **plan** and ensure the source
   checkout is clean main equal to origin/main. Stop managed services
   through an owner-authorized maintenance procedure; never overwrite
   loaded Core under an active bridge. Apply only the tool's authorized,
   hash-verified transaction and preserve its receipt.
4. Restart via the existing `Tools/run_ls_go_bridge.py` singleton
   supervisor, not a new daemon or alternate port. Confirm health HTTP 200,
   eight floors, unchanged DB root, zero duplicate listeners and unchanged
   existing command consumer semantics.
5. Authenticate using existing owner session, read the two owner-scoped
   endpoints `/api/v1/cgx/surface` and `/api/v1/cgx/family/topology`.
   Check a benign pinned task/run checkpoint, exact persisted readback
   after supervised restart, expiry/revocation and denial with forged,
   stale or absent owner session. Verify no source bytes or external
   action appeared in events.
6. Only then mark **local metadata persistence** as live. Broader
   subagent task execution still requires real host lease verification,
   per-occurrence rights, source-path ACL, enforced CPU/RAM quotas,
   stop authority, task receipts and independent regression tests.
7. Mint/promote native CGX, issue DataSpace network identity, and publish
   outside the private host only under their respective issuer,
   revocation, peer proof, signing, safety and release acceptance gates.

## Research and continuity ledger

Raphael/T173, theoretical geometry, compact model packaging, Grex research,
PrintSpace manufacturing and edge/network bridging remain governed R&D and
product lanes. They may cite canonical sources and submitted review receipts,
but source presence does not become proof of geometric claims, improved CPU
capacity, completed AGI or physical manufacturing readiness.

**Current disposition:** Reviewed source integration ready for independent
code/QA acceptance. The running deployed Core remains unchanged. Native
metadata execution is not yet loaded on port 8765; DataSpace decentralized
mint and actual subagent scheduler activation remain HOLD.


## Offline CGX catalogue portability correction

The existing `cgx_capability_registry.py` assumed repository-relative files
would still exist after installation into `D:\LightSpeed\Core`. In the
installed layout this resolves incorrectly to `D:` and the registered
capability surface cannot hydrate. The reviewed code now uses
`cgx_catalogue_root.resolve_cgx_catalogue_root` to select either:

- authoring root: the existing Git repository during development; or
- installed root: `D:\LightSpeed\Core\cgx_catalogue` containing the
  read-only, hash-verified snapshot of the **same** source manifests.

The existing `reconcile_live_runtime.py` installer now derives **25**
allowed catalogue paths from eight fixed CGX source descriptors, nine shared
skill IDs in `selector_packages.json`, and eight role manifests resolved
through the selector profiles. Nothing under live `data`, credentials,
queues or secret stores is copied. This is packaged source metadata, not a
mutable second catalogue; the normal installer still requires clean main,
stopped services, backup and hash/readback verification. A new isolated
deployment test proves the installed snapshot resolves `LightSpeed`,
`role:neo` and `route:cgx.plan_query` without a Git checkout.

The source UI was built with Vite into the existing tracked
`apps/lightspeed-go/dist` output. The superseded hashed JavaScript asset is
removed and replaced by one current build asset; this does not create another
application or change the public release authorization.

**These are source/release-package changes only** until a normal,
owner-authorized deployment applies them to the live host.


## Subsequent read-only deployment gate — 18 November 2026

The existing `tools/reconcile_live_runtime.py plan` now returns
`deployment_readiness` with explicit machine-readable blockers. This is
a presentation/decision aid: it does not stop services, copy bytes, issue
owner approval or mint anything. An apparently eligible state continues to
require the operator's confirmed apply, checked backups and rollback plan.

Observed later this day (no installed file copied):
- 757 tracked mappings, 60 changed installed targets.
- Source branch `ops/canonical-queue-index-20261115`, 11 commits ahead of
  `origin/main`, with three pre-existing unrelated working-tree paths.
- Active managed TCP ports: 4173, 8080 and 8765.
- Current deterministic deployment blockers:
  `REVIEW_BRANCH_NOT_ACCEPTED_MAIN`,
  `MAIN_NOT_ALIGNED_WITH_ORIGIN`,
  `UNCOMMITTED_OR_UNTRACKED_SOURCE`,
  `MANAGED_SERVICES_ACTIVE`.
- Verified nine selector profiles; seven observed installed .cgx carrier
  filenames, six unique content hashes, one alias set:
  `LS.cgx` and `LightSpeed.cgx`.
- Read-only host status: DB, storage, supervisor and eight floors operational;
  canonical command identity held, representation edge off and no verified
  independent DataSpace peer.

The current review branch has a draft PR #228, not an approved production
merge. Keep existing `D:\LightSpeed\Core` live code intact; do not
install under active service ports or silently promote proposed research
as native, signed CGX functionality. The reusable manifest and tests remain
the owner-scoped release candidate.
