# UniSpace / CGX — Squarespace, SAI and transport-readiness fold
**Date:** 20 October 2026 (Australia/Brisbane)  
**Status:** SOURCE-ONLY REVIEW; no native or web release authority

## Canonical alignment, not a second system
This is a routing/installation readiness note for the existing `Cognigrex.cgx` parent, CCC, FileSpace/identity, DataSpace node exchange, LightSpeed runtime, and existing LS GO/UniSpace presentation surfaces. No alternate FS/DS/PS manager, agent, root, database, scheduler, or execution service is created.

References verified against current Git source (not a deployed-page audit):
- `cgx/domain_templates/cognigrex_parent_topology.json`: Cognigrex.cgx parent, `/ccc`, `/identity`, `/graph`, `/lenses`, `/archive-dbr`; Römer, Eco, EMASSC and LS as scoped child domains.
- `cgx/domain_templates/node_exchange_contract.json`: distinct signed node identities, content-addressed transfer, leases, receiver readback, no authority transfer from copying data.
- PR #179: `cgx/domain_templates/passive_edge_profile_registry.json` and `cgx/portable_node/passive_node_plan.py` for T0–T3 / WEB_OFFLINE, WEB_CONNECTED, ANDROID_RELAY, WEARABLE_VIA_PHONE and DESKTOP_VERIFIED.
- PR #174: public-only static UniSpace viewer and `apps/lightspeed-go/public/cgx/deployment/SQUARESPACE_CGX_EMBED.html`; public `/cgx`, `/cgx/fs`, `/cgx/ds`, `/cgx/ps`, `/cgx/doom` are independent of the authenticated operator surface.
- PR #180: source-proven, noncanonical Alexandria catalogue/rights/byte-range hydratable candidate; no source ownership or permissions transferred.
- PR #183: latest-current-main exact Object_ID fix, still draft.
- #158: public/internal static asset boundary OPEN; #161: actual independently authenticated two-node FS/DS verification OPEN.

## Squarespace shell composition
**Squarespace is the public page and navigation container.** Supported custom-code/iframe features depend on the Squarespace site plan. Use the existing isolated public `SQUARESPACE_CGX_EMBED.html` snippet and static Vercel source tree from PR #174, not a copy of LS GO's private application bundle or a source/credentials database. A Squarespace Code Block or Code Injection is **not a server-side runtime**. A content-only iframe from an explicitly allowlisted production origin is a reasonable proposed installation surface; check framing policy, Content-Security-Policy, sandbox, mobile sizing, custom domain and keyboard access in a genuine browser. Avoid putting a URL containing private credentials into iframe attributes or query parameters.

Keep routes within the single UniSpace product: `/cgx` public orientation, linked public domain lenses and DOOM; private user/workspace/owner actions stay behind the **existing authenticated UniSpace/LS GO application**, not the Squarespace code block. No new source manager. An anonymous visitor must see only approved public assets. Public static/served files are considered accessible without a session regardless of UI navigation hiding them.

The PR #174 README states a Vercel candidate at `https://romer-unispace-public.vercel.app/cgx/`, but this note does NOT independently verify that URL or `https://romer.industries/cgx` is presently reachable, framed, up to date or safe. Verify externally on desktop/mobile before claiming publication.

## One CGX, three presentation contexts
| Context | How selected | Proof required | Status |
|---|---|---|---|
| CGX base | default in any local/online surface | standard per-object ACL and source root for actual content | source-only projection |
| UniSpace | requested creator/portable workspace | existing authenticated app if data/private capabilities are used | existing candidate UI |
| SAI (Shared Australian Intelligence) | separate explicit regional opt-in on eligible authenticated UniSpace/CGX session | independent Australian-jurisdiction/eligibility verification, consent, session ACL and capability registration | **HOLD**; never inferred from IP/geolocation or language alone |

Geographic context may inform a **suggestion** to request eligible SAI services only; it cannot activate an agent, grant access to government systems or change repository authority. Public Squarespace pages do not expose SAI private capabilities.

## Current transports and future natural-network candidate
The `CURRENT_HTTPS` profile is a planning label for explicitly selected HTTPS endpoints and existing signed sessions; `OFFLINE` uses only user-provided/local cached sources and does not fabricate peer acknowledgements; `NATURAL_CANDIDATE` is a prospective transport implementation, not an established physical communications network or alternate governance authority. No assumptions about RF, Schumann resonance throughput, ecological/sensory channels, peer encryption, connection range or transfer capacity may be made without actual hardware/protocol definition, measured tests and independent proof.

`plan_unispace_surface` is a **pure plan** extending the existing passive-node planner. Every output maintains `connected=false`, `authenticated=false`, `sai_activated=false`, `canonical_promotion=false`. For natural transport, even asserted proof leaves `HOLD_NATURAL_PEER_READBACK`. Handoff into the existing DataSpace node-exchange is only allowed later after signed independent device identity, lease, source and target exact-byte SHA-256/size and DBR-compatible receiver readback, and owner decision. Fallback is LOCAL_OFFLINE or explicit HTTPS, not automatic public-LAN scanning.

## Durability across devices and networks
- **R0**: original owner/Drive/Git/official-public-dump source unchanged, version+SHA+rights retained; never imply semantic projection reconstructs missing bytes.
- **R1–R3**: typed provenance-carrying source structures, qualified semantics and view candidates; source-free fragments are only complete for declared fields.
- **DBR**: append-only provenance/receipts and explicit root/delta comparison; no timestamp-wins conflict erasure.
- **Offline**: user-explicit local source/cache, manifest hashes, no fabricated server/peer verification.
- **Recovery**: both branch HEAD and signed owner root/DBR proof required before native acceptance; sparse state and unique historical claims preserved.
- **Library**: consolidate only approved public source bibliography/licence entries in public UI; all private S92/physics JSON R0 remain owner-only under Drive's previously created private UniSpace Alexandria Intake workspace.

## Release checklist (do not mark accepted from source code alone)
1. Review/fix issue #158: unauthenticated GET, static `dist/`, leaked catalogue/API URLs/paths, revoked sessions, CSP/frame ancestors, and explicit public-safe asset inventory.
2. Review/fix issue #161: signed identity, current node registry, HTTPS/TLS origin, leases, two distinct nodes, interrupted/resumed transfer and exact receiver SHA/size+root readback.
3. Test actual Squarespace plan/code execution, Vercel route HTTP responses, mobile iframe, keyboard/accessibility, framing and isolated origin; compare current builds with exact Git digest and expected viewer data.
4. Provide access-controlled owner workspace and server-enforced permission when binding Alexandria source-backed hydration to LS GO Objects, not to `public/` or guest routes.
5. Register SAI only as a conditional owner-approved capability with independent, consented regional verification, audit and licence; natural network only after protocol+real physical tests.
6. Merge only exact-head approved PRs in owner-reviewed dependency order. Never auto-fold legacy manifest overwrites, merge drafts because CI is green, deploy private data, delete archives or copy owner-only source to public Squarespace.
7. Verify Google Drive receipt plan/rights under an unshared owner intake folder; preserve original files and avoid automatic moves into existing broadly link-shared CGX/Recovery.

**Next independently executable slice:** produce and browser-test the public-safe Squarespace embed against the exact approved static viewer artifact, plus a server-authenticated source-hydration inspector in the existing UniSpace/LS GO Objects view. Both remain blocked on #158; never use the pure source-lens caller flag as authentication.
