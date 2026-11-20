# UniSpace / UOS T173 Geometry Reuse & One-of-One Handoff

## Governing decision

- A Raphael shape is a **mathematical reference**, never a unique assignment to any one physical substance, taxon, file, user, agent or device.
- One canonical shape reference may be used by many distinct CGX objects; one CGX object may use several geometries.
- Distinguish source digest, geometry identity, immutable definition digest, canonical Object_ID, instance ID, capability, mutable state and possible on-chain NFT token ID. Never infer one from another.
- `T173` remains an offline non-CGX resolver/interpreter; `LOAD.Lite` remains a deeper native CGX facet; `LOAD` remains Alexandria. Do not duplicate their database or authority.
- Only active source/capability requirements should be hydrated: L1-L2 qualified dictionary summaries, L3 connections, L4 approved operations, L5 temporary state.

## Resolve, reconstruct and fold

1. R0 source bytes or qualified external reference, hashed and rights-scoped.
2. R1 typed structure, geometry/relations/unit/coordinates and loss map, source-located.
3. R2 sparse T173 1..173 paths of depth <=4; content-addressed definitions, shared references, typed edges; no materialisation of empty slots and no role 174.
4. R3 multiple views (3D/render, scientific calculator, map, graph, document and machine surface) derived from the same definitions; separate rendering tessellation from computational precision.
5. F approved kernel/capability only. Missing geometry or physical parameters remains unknown/frontier; never invent a molecule or physical effect from shape alone.
6. Overlay L5 observation/session; updates expressed as versioned, scoped deltas; cache invalidation by exact dependencies; source/rights gates unaffected.

## One-of-one agent and library sequence

### Candidate agent

- Resolve **existing** agent identity and root/child scope via the native signed CGX resolver, rather than minting a duplicate agent if already accepted.
- Require source, actor, rights, immutable operational profile, approved capabilities, lease/ACL/revocation and signed DBR receipt.
- Until independent issuer and host readback, status `CANDIDATE_NOT_MINTED`; no synthetic Object_ID.

### Candidate T173/CCC library

- Bind to the accepted agent only when native source and registry confirm exact parent/dependency identities.
- Register a distinct **library object** referring to many qualified definitions; do not mint 173 shapes or force 1:1 relationships.
- Record signed manifest root, source/geometry/operator identifiers, dependency/rights receipts, version, revocation/upgrade path.
- Support standalone export, UOS package, native CGX FileSpace, and permitted DataSpace exchange with exact transfer and recipient readback.
- Keep external blockchain NFT/token issue separate and optional. Not performed by this packet.

## Required existing contracts

- `UniSpace/product.json` — S91 product reference only; host-local S92 not embedded.
- `cgx/domain_templates/file_conversion_contract.json` — R0/R1/R2/R3 invariants.
- `cgx/domain_templates/file_type_conversion_registry.json` — reuse adapters.
- `cgx/domain_templates/semantic_view_lens_registry.json` — reuse projections.
- `apps/lightspeed-go/src/filespaceProjectionGuard.ts` — display only, no auth.
- `apps/lightspeed-go/src/cgxObjectHydrationView.mjs` — review-only data-hydration planning.
- Issue #158 private/static asset boundary; issue #161 authenticated 2-node FileSpace/DataSpace/DBR acceptance.
- Raphael 173 role catalogue and position 174 null remain immutable until separately qualified.

## Acceptance and release stages

1. Local tests demonstrate shared geometry, multiple independent instances, nested references, 173 trit roundtrip, collision/cycle rejection and untrusted-op refusal.
2. Integrate via existing typed registry; test exported HTML offline, numerical equivalence of render/calculator projections and source provenance.
3. Verify exact live host CGX Object_ID and signed DBR/lease/ACL; real two-node DataSpace transfer with replay and revocation negative tests.
4. Owner approves source rights, issuer agent identity, library one-of-one admission and rollout.
5. Distribute only rights-cleared packages and only then consider optional public/decentralised replicated content with verified pin/availability/receipts. No secrets, private source or effectful lease in public artifacts.

## Local reference proof

Review bundle `T173_UOS_OneOfOne_Review_v0_1.zip` is a standalone local reference prototype, not integrated into the repository or native CGX authority. It has Node.js tests, JSON synthetic manifests and offline interactive HTML. Validate that separately before any source integration.