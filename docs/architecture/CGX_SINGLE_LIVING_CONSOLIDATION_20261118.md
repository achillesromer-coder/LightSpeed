# CGX / UniSpace — one living catalogue and conservative empty cleanup

**BouwerBase review, 18 November 2026.** This change is isolated from the
desktop Work session's active worktree and makes no deployed-host mutation.

## Existing single-root facts

- `C:\UniSpace` is a Windows directory junction to `C:\CGX`. These are
  existing namespace aliases, **not two independent FileSpace databases**.
- The seven observed top-level `.cgx` carrier filenames produce six distinct
  SHA-256 content digests. `LS.cgx` and `LightSpeed.cgx` are byte-identical.
- A matching hash may collapse **one display card**, but does not confer
  semantic identity, permission to delete a filename, signing, ownership,
  canonical promotion or evidence of a native mint.
- All nine existing selector profiles still resolve through the
  `plugin_capability_routes.json` and `selector_shortcalls.json` sources.
  This increment creates no new registry or running daemon.
- The legacy installed bridge remains healthy but is running earlier source.
  Source integration does not imply newly available endpoints until the
  existing controlled deployment/restart and owner readback.

## Implemented

The existing `build_cgx_family_topology` now emits:
- `content_groups`: one read-only UI representative for each exact digest,
  including *all* reference filenames, size and admission qualifiers;
- `collapsed_alias_card_count`: saved duplicate **presentation** cards;
- `retained_empty_carrier_names`: held, non-admitted empty top-level .cgx;
- `storage_root_is_alias`: whether the requested entry root resolves to
  a different physical backing path;
- `safe_delete_candidates=[]` and `deletion_performed=false`:
  explicitly no file removal authority from a content hash.

The existing UniSpace family panel consumes these backend fields instead of
rendering a duplicate card for every filename. It remains the *same* owner
session-scoped host panel; no extra application or surface is created.

The source-only `tools/cgx_living_consolidation_review.py` uses Git's tracked
file list and the existing family topology. It emits a stable JSON review
receipt and SHA-256; it does not walk all manual-intake environments or
modify any file, commit, database, service, carrier, mint or source permission.

## Source empty-file findings

Against the parent source snapshot `1d10fc09` before this review commit:
- 1,832 tracked files examined;
- 28 tracked zero-byte files found;
- 19 Python `__init__.py` namespace/package markers (preserve);
- 9 unfinished Raphael/research `.py` scaffolds (preserve pending exact
  references, source contract review and independent research disposition);
- **zero approved deletion candidates**.

Empty wheels, `py.typed` markers and third-party `__init__.py` under the
historical, untracked `CGX_Manual_Intake/.../.venv` are *not* considered safe
garbage merely by file length. An empty shell may still convey identity,
packaging purpose or a reserved T174/zero sentinel; never automatically
delete based on byte length alone.

## Closure and promotion

1. Desktop Work session retains native service deployment/rollback authority;
   this branch is a review-only source candidate.
2. Complete source review and frontend/backend regression.
3. Reconcile exact roots, signed DBR authority, owner session and source
   rights before any actual carrier replacement or data pruning.
4. For each eventual delete candidate, prove its references have been
   rewritten, a byte-exact verified archive exists, independent readback
   passes, and an authorized rollback and owner decision are recorded.
5. Keep T174 reserved nonmintable. Do not confuse byte equal files with
   equivalent objects, theoretical geometry with empirical results, or a
   UI collapse with physical disk-space reduction.
6. DataSpace node mint, peer transport, PrintSpace hardware, Raphael/T173
   proof and public launch retain separate release gates.

## Repeatable audit (no writes)

```powershell
$repo = 'D:\LightSpeed\Repositories\CGX_Mobile_Review'
D:\LightSpeed\Environment\Scripts\python.exe "$repo\tools\cgx_living_consolidation_review.py" --repo $repo --carriers C:\UniSpace
```

The review can also run against a future accepted main checkout; the root
identity and source zero-file disposition must be re-audited at that time.

**Current classification:** content-alias presentation consolidation built;
physical deletion = 0; no FileSpace/DataSpace/mint state mutated.

## Linked digital-twin assets — observed source audit

The existing digital-twin catalogue is referenced directly from
`data/digital-twin/complete_digital_asset_manifest_2026-09-12.json`,
rather than being ingested again or copied into a second store.

Read-only scan against the current review worktree:

- 16 registered twin object families;
- for each: one tracked OBJ, one tracked six-view PNG, eight tracked T1
  SVG layers (`T1-00` through `T1-07`);
- 160 of 160 referenced layer files observed with nonzero bytes and SHA-256;
- zero missing/empty/untracked referenced layers;
- zero cross-layer identical-byte groups in this manifest's verified inputs;
- representation classes: 13 `INTERACTION_PROXY`,
  2 `SOURCE_DERIVED_GEOMETRY`, 1 `SOURCE_DERIVED_PARTIAL`.

The `digital_twin_asset_linkage` field is computed by the existing living
consolidation review command, with per-layer SHA-256 identities, stable
relative paths, missing-layer holds and non-authority flags. Nonexistent,
symlinked, escaping or untracked paths are not silently accepted. The tool
does not extract unqualified source bytes or assert geometrical equivalence,
watertight precision, fabrication tolerances, source licensing, native
CGX mint or independent scientific verification.

Completeness of these 160 **files** is not product completeness. Upstream
source meshes, engineering CAD, unit validation, derivative provenance,
rights and physical quality controls remain separate acceptance gates.

## Shared cross-Grex contracts — source-qualified parent graph

The same read-only consolidation receipt now resolves the existing
`cgx/domain_templates/domains.json`,
`domain_child_identity_registry.json` and
`cognigrex_parent_topology.json` as a single graph. It checks every
child against its original domain namespace, parent identity, physical
carrier filename and principal agent, with per-file SHA-256 for all
required source registries and shared contracts.

Observed source qualification:
- Parent semantic root: `cgx:root:cognigrex` / `Cognigrex.cgx`.
- Three direct domains: Römer / `Romer.cgx` (Neo);
  Eco / `Eco.cgx` (Athene); EMASSC / `EMASSC.cgx` (Achilles).
- Each direct domain retains its own semantic library, type registry and
  relation registry: nine existing source files, all tracked and readable.
- Forty-eight existing parent shared contracts resolved by exact file
  reference and SHA-256, with no missing source references.
- LightSpeed remains nested under EMASSC as
  `cgx:domain:lightspeed` / `LS.cgx`; alternate
  `LightSpeed.cgx` is an observed exact-byte alias, not a new domain.
- Negative tests fail closed on missing lease contract and tampered
  child-parent identity. The related regression passes 18 backend tests.

This checks **source linkage**, not authenticated runtime admission.
No cross-Grex semantic authority, source rights, release signature,
training permission, DataSpace network identity, native mint, or
filesystem deletion follows from a successful source-only hash match.
The next gate remains host owner/lease/source provenance and DBR
readback during reviewed native acceptance; do not install a duplicate
Cognigrex or flatten independently governed child-domain meanings.

## Narrow local destructive cleanup receipt — 18 November 2026

The owner explicitly authorized a local destructive cleanup, but the
delete boundary remained **regenerable Python bytecode generated inside
the isolated review worktree only**. No canonical source, signed/minted
carrier, reserved Raphael/T174 scaffold, referenced alias, model weight,
native service, database, untracked owner data or desktop Work checkout
was eligible for this operation.

**Executed and independently read back:**
- Tool: `tools/cgx_review_bytecode_cleanup.py`, review commit
  `bc7dc758099fbb2a42f1e88abb948788df9aee7a`.
- Scope: four allowlisted `__pycache__` directories under
  `D:\LightSpeed\Repositories\CGX_Mobile_Review`, on
  `review/cgx-living-consolidation-20261118`.
- 73 bytecode files deleted, 2,274,702 bytes; held files = zero.
- No remaining target cache directory after deletion; Git worktree clean.
- Before unlinking any file, the tool saved a byte-exact ZIP with
  73 entries plus one content manifest, verified ZIP readback and SHA-256,
  and checked each file had not changed.
- Archive:
  `D:\LightSpeed\State\Review\CGX_CacheCleanup_20261118\cgx-review-bytecode-8984f105e84418b8.zip`
- Scan digest:
  `8984f105e84418b8782a922cce51d79d3e8c0ac3404f3c394d2308c958ca11d9`
- Independent archive SHA-256:
  `39a124f5d7f2a6e3e04bc8b86d1ca080da9ba9c77d7b7956721c998c708097c8`
- A companion `.receipt.json` exists beside the ZIP, containing exact
  removed counts, state, commit, hash and isolated rollback instructions.
- BouwerBase bridge remained healthy (HTTP 200), and canonical `.cgx`
  carrier hash prefixes matched their pre-cleanup values. Source Git
  files were not modified by the cleanup.

This archive is only for optional bytecode restoration: source-level
execution remains reproducible from the corresponding Git commit. This
is not a release archive, minted DataSpace receipt or new persistent
Cognigrex database. The precise cleanup can be rerun as a dry-run without
authorization; actual deletion requires the narrow explicit confirmation
`PURGE_REGENERABLE_REVIEW_BYTECODE_ONLY`. Deletion of semantic or
scientific artifacts remains **HOLD** pending a verified reference
graph, rights, independent source preservation and rollback.

The `node_modules` junction, source manifests, existing `dist` build,
`LS.cgx` / `LightSpeed.cgx` reference aliases, and empty Python package
markers remain intact. The cache savings may be transient because later
test runs can safely regenerate Python bytecode.
