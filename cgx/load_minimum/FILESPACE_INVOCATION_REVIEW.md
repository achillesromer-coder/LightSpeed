# CGX FileSpace feature invocation — LOAD and related functions

**Date:** 28 October 2026 · **Status:** source-reviewed candidate; no native admission or deployment · **Scope:** additive CGX / UniSpace / CCC invocation layer, not another system or authoritative Object_ID registry.

## Existing source authority

- `Cognigrex.cgx` = parent; shared `ccc`, `identity`, cross-domain graph and representations. `Romer.cgx`, `Eco.cgx`, `EMASSC.cgx > LS.cgx` retain their respective scoped authority. Existing parent topology is **review-blueprint**, not an accepted new LOAD child.
- `cgx/domain_templates/toolkit_registry.json` already names CCC `discover`, `plan`, `verify`, `apply`, `unapply`, `receipts`; LightSpeed computation and provider adapters. `workflow_registry.json` already names `intake-to-canonical`, `analysis`, `publish`, `remote-small-edit`, etc. Do not reimplement these.
- `depth_profiles.json` identifies orthogonal reasoning/execution/device-hydration dimensions; don't treat `H0-H4` LOAD shortcut labels as replacement for existing independently named H0–H9 or device profile contracts.
- `surface_registry.json` defines desktop, web, mobile, CLI, chat, API, node with distinct rights. Right-click, touch long-press, command palette, slash command and CCC discovery should invoke the *same* action ID and host preflight.
- Existing legacy Trinity right-click code (`.../Z+3_Trinity/components/context_menu.py`, `ui/universal_context_menu.py`) handles file/folder operations and inter-floor actions. It is a reusable UI precedent, **not** proof of a native CGX FileSpace/CCC installation menu.
- Alexandria `LOAD.cgx` isolated local review carrier is about 27 KB; contains source-linked reference records, not resolved full corpus. Its demonstration can search/inspect/walk/hydrate metadata offline, but cannot authoritatively install itself.
- Existing F00–F90 **source-reviewed labels** are taken from `Alexandria_Engine_Upcycle_Source_Bound_Manifest.json` (23 October 2026). Its listed upstream game/engine projects are mostly references only; an F ID is not a verified active plugin. Names remain unchanged; optional short commands are *proposals*, not newly minted `.cgx` files.

## User entry points (one action model)

| Surface | Invocation | Initial result |
|---|---|---|
| FileSpace tree / UniSpace desktop | Right-click child FileSpace → **Alexandria** → `Explore`, `Resolve`, `Equip with LOAD…`, `Hydrate…` | Metadata-only catalogue, optional guided preflight |
| Mobile / tablet | Long-press selected FileSpace → **Alexandria** | Same action IDs, limited hydration |
| Keyboard / Command palette | `LOAD`, `Alexandria`, or `Explore Library` | Existing-object lookup, low-hydration chooser |
| CCC selector | Find Alexandria / `LOAD` → `Inspect`, `Verify`, `Equip` | Existing current package/capability resolution before any apply |
| Object right-click | `Resolve with Alexandria`, `Inspect sources` | Source and contradiction projection; no child installation |
| File right-click | `Compare source with Alexandria` | Bounded, permissioned R0/R1 proposal, not automatic ingestion |

A user can enable LOAD for multiple children by adding capability links to the same authorised library; do **not** replicate source forests or create a second Alexandria master for each child. Composition choices use existing CGX semantics: **TRACK** by default, REFERENCE, PIN or EMBED if current policy/source licence and device profile permit. Selection is not a commit.

## Wizard sequence

1. Choose a target FileSpace (exact accepted Object_ID and child owner, not its display label).
2. Resolve `Alexandria`, `LOAD` and alternative aliases against the *current authoritative parent identity registry*. If an identity already exists, **reuse**, do not mint.
3. Decide TRACK/REFERENCE/PIN/EMBED and scoped views; define offline minimum and optional network hydration levels.
4. Show source rights/ACL, dependencies, expected storage/cache/bandwidth and evidence ceiling; prefer references to originals.
5. Produce a diff, check source collisions, owner capability, admission/security, public/private boundaries and undo path.
6. Native host performs independent licence/lease/preflight, an explicit authorised apply, and DBR readback; only then show **Installed/Enabled**. On any unverified condition show **Review/Hold**.

The planner supplied here stops at **READY_FOR_AUTHENTICATED_HOST_PREFLIGHT**. It does not install, execute or reach a network. `LOAD` is a founder-directed functional mnemonic, **not yet a source-verified globally unique accepted Object_ID**.

## Next short-function candidates (review names only)

`CALC` → existing LightSpeed/EMASSC compute; `SIM` → qualified simulation; `SHAPE` → typed geometry/twins; `TRACE` → Alexandria source/evidence; `SYNC` → signed DataSpace exchange (issue #161 HOLD); `PRESS` → existing UniSpace/CGX Press review. All are **CCC action aliases**, not new sibling FileSpaces by default. Avoid collision with existing user labels before final naming; never overtake validated functional names or actuation/financial/legal releases.

The established F00–F90 function decomposition remains distinct and reusable. Specialist domain functions (GMAT, FreeCAD, PrintSpace, Eco assess, Raphael numerical operators) attach to these **via qualified versioned adapters** and never have their scientific/physical performance inferred from a catalogue link.

## Validation and gates

Run `node --test cgxLoadFeaturePlanner.test.mjs` (12 tests). Pure ESM code has no network or file permissions. It returns a proposal with explicit blockers, does not claim live installed capability, and prohibits traversal strings and >60 MiB single work units. The 60 MiB limit is a processing boundary, not an Alexandria storage ceiling.

This proposal should be added on the existing **LOAD.cgx draft PR #205**, not merged to main or embedded into canonical `Cognigrex.cgx` until current host RootAuthority/DBR, accepted alias lookup and independent security tests permit it. Currently BouwerBase/host acceptance and independent node evidence are unverified. Keep issue #158 (web static visibility) and #161 (signed two-node exchange) separate; no auto-archive/delete.
