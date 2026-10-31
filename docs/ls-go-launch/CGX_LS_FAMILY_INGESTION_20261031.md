# CGX / LightSpeed family ingestion and UniSpace oversight — private integration

**Status:** Review-branch implementation. No host installation, native admission, signed lease, DBR promotion, or public release is implied by repository CI.

## One architecture, not another runtime

- `Cognigrex.cgx` is the single parent. The stable semantic ID is `cgx:root:cognigrex`; S92 carrier instance ID is `cgx:phase-a:42d99b46c0d322f08b59b7b7`.
- `Romer.cgx`, `Eco.cgx`, and `EMASSC.cgx` remain children of Cognigrex; `LS.cgx` remains scoped beneath EMASSC.
- `LOAD.cgx` / Alexandria is the existing source-reference/library alias under Cognigrex, not a separate canonical root. Draft #205 owns its source registry and activation contract.
- LightSpeed/Desktop and its existing eight-floor orchestration execute the host work. Achilles is the private governance/assurance lane; CCC retains its permission policy; domain owners retain acceptance authority.
- UniSpace is the user-facing, non-authoritative workspace/oversight lens. No new database, scheduler, customer-facing product, login system, or provider mirror is created here.

## Implemented (source)

1. `lightspeed_runtime.cgx_family_ingestion` parses the canonical `domain_child_identity_registry.json` and (if configured) the existing Alexandria `online_registry_projection_2026-10-28.json`.
2. It queries the **existing** `lightspeed_unified.db` via SQLite `mode=ro` and `query_only=ON`; it resolves semantic Object_IDs, observes candidate/active operational rows, and reports identity collisions as HOLD. It does not equate any state with native DBR admission.
3. It checks source-only catalogue provenance/invariants and reports the 131 reference declarations, 14 source registries and three Frontier items when given the original review projection. It does **not** fetch original source bodies or promote candidate Object_IDs.
4. Existing LS GO Desktop bridge: `GET /api/v1/cgx/family-oversight`, accessible only with the existing in-memory owner session via `X-LightSpeed-Session`. No password/confirmation value is read from a source document; no request-supplied file paths.
5. Existing LS GO **System** view gains a private, owner-clicked CGX Family Set panel. It renders only aggregate source references and native operational states. It clears displayed evidence on sign-out.
6. `tools/cgx_ls_family_oversight.ps1` is an additive process-scoped probe for BouwerBase, not a second setup wizard or a replacement runtime manager. It does not start or stop existing services.

## BouwerBase non-mutating smoke test

Prerequisites: the review code is present locally in the **existing** managed LightSpeed repository/runtime; do not change the running canonical checkout or live service just to run a source test.

```powershell
$repo = 'C:\LightSpeed_Consolidated\_analysis_remote\LightSpeed_Canonical'
& "$repo\tools\cgx_ls_family_oversight.ps1" -Repo $repo
```

Expected: JSON schema `CGX-LS-FAMILY-OVERSIGHT/0.1`, one semantic root, four registered children with LS nested under EMASSC, candidate/unknown native states, zero writes. If the review code is not in the local checkout, the probe must fail rather than create or modify an environment.

For the optional Alexandria source projection, supply the **existing** owner-private source-review JSON from #205, preserving its Git identity and rights boundary:

```powershell
& "$repo\tools\cgx_ls_family_oversight.ps1" -Repo $repo `
  -LoadSourceRegistry 'C:\path\to\existing\online_registry_projection_2026-10-28.json'
```

Do **not** treat that review projection as an installed LOAD carrier. The source registry contains reference metadata only. Do not copy private R0 source bodies into public app assets.

To set **current-process-only** variables for an owner-controlled future bridge launch, add `-BindCurrentProcess`. This does not change the already-running bridge and does not create a persistent Windows configuration or an owner session.

## Live bridge route after separately approved deployment

Existing LS GO source provides owner login at `POST /api/v1/auth/login`. Keep the session token private and in memory. The family endpoint is `GET /api/v1/cgx/family-oversight`, requiring `X-LightSpeed-Session`.

The bridge process must be started by the **existing authenticated runtime manager** with trusted environment paths:

- `CGX_FAMILY_IDENTITY_REGISTRY`: the existing canonical domain-child identity registry.
- `CGX_LOAD_SOURCE_REGISTRY`: optional source-only Alexandria projection from review #205.
- `LIGHTSPEED_CANONICAL_DB`: the existing operational `D:\LightSpeed\Data\db\lightspeed_unified.db`.
- `CGX_ROOT_REGISTRY` and `CGX_ROOT_CARRIER`: optional **pair** of the existing S92 root registry and carrier for byte-binding observation; a hash match is not a signature or owner approval.

The endpoint fails closed if its required family-registry path is not configured or its input invariants fail. It does not itself enable the representation-edge feature flag.

## Unresolved admission and release controls

- Operational parent `candidate` remains distinct from historically verified S92 Recovery; no automatic `candidate → active` transition.
- Parent review creation requires the separately reviewed #213 owner path **and** trusted signed-lease issuer, revocation, exact graph hash, transaction/rollback, and DBR readback. This branch does not add a native review writer.
- Child Object_IDs and LOAD alias collision/owner ACL/rights require independent native resolution and acceptance.
- Unverified provider, plugin, and CCC route declarations remain `SOURCE_REGISTRY_ONLY`. The 131 items are references, not 131 executed capabilities.
- Stop ships: #158 private/static asset boundary, #161 distinct-node FileSpace/DataSpace receiver readback, and #209 scientific provenance/scale constraints.
- #206 owns existing first-run/Grex toggle smart setup; #208 runtime acceptance and managed package lanes remain independent. Do not merge them by copying their installers into this branch.
- Remote Desktop Commander is presently connected but command execution is unavailable due usage allowance. No BouwerBase live install, service restart, or DBR acceptance was performed from this change.

## Acceptance evidence

Run CI Python tests for `test_cgx_family_ingestion.py` and the LS GO bridge. Frontend `cgxFamilyOversight.test.ts`, TypeScript type-check, and Vite build must pass. Source-manifest SHA-256 records must match current tracked bytes. On BouwerBase, the local owner should separately execute the smoke-test command, validate actual bridge session readback, and retain a source/DBR receipt before production feature enablement.
