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
