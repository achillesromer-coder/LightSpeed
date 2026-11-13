# CGX / UniSpace — Private Objects Migration Plan (61 held static assets)

**2026-10-21 · Stack over PR #192 · source-only reviewer artifact.**

## Reason / existing authority
The published static tree is currently unsafe for CGX internal engineering review. The previous #189/#190 source audits found 61 known internal Vite assets, and #191/#192 now provide a session-only Desktop bridge and Objects viewer without static fallback. This stage creates the **exact source-byte migration plan** and a separately opt-in, no-overwrite local staging primitive; it does not move the real user's files or modify any deployment. The existing Cognigrex.cgx source owner, Asset/Object_ID identities, source manifests and ACL remain authoritative. Issue #158 stays OPEN.

## Source paths and limits
The planner reads only the two known `public/data` CGX review catalogues plus regular top-level `.svg` files in `public/review/renders` and `.json` files in `public/review/mesh`. It rejects symlinks, nested/unregistered files, bad filenames, file replacements during read, missing roots, and assets exceeding the current gateway's 4 MiB per-file limit. It refuses more than 256 review files. Any exceptions are a qualification HOLD, not silent deletion.

The default command is **read-only**:
```sh
python cgx/review/private_object_asset_migration.py --root .
```
The output includes ordered file-relative paths, individual SHA-256 and byte counts, and a deterministic `plan_sha256` receipt binding the selected set. It contains **no asset bytes, credentials, source owner approval or admission grant**. Do not copy this plan to public/static sites without owner classification and approval, because private filenames and inventory can themselves be sensitive.

## Explicit private staging (owner action, not executed by this change)
When the owner has independently reviewed/approved the 61-file source set, provision a private directory **outside the repository and outside every `public`/`dist` directory**, verify permissions, then explicitly run:
```sh
python cgx/review/private_object_asset_migration.py --root /path/to/LightSpeed \
  --stage --private-root /existing/owner-approved/private-review \
  --approved-plan-sha256 <reviewed-plan-sha256> --expected-count 61
```
This is not a command automatically executed by automation. It requires a matching plan digest and count, pre-existing absolute target root, non-static/non-repo placement and no existing target file. Exact sources are copied with a temporary file then non-overwriting atomic hardlink, re-read and SHA-256 verified; source originals are retained. Any new source mutation changes the plan digest and requires reapproval. If hardlinks are unsupported on the destination volume, staging fails instead of falling back to a possibly unsafe overwrite.

**Rollback:** no source delete is part of staging. On mismatch/error, stop and retain the source. Any newly staged target files require independent owner inspection before cleanup; this script does not delete those copies or automatically reattempt a partial stage.

## Release progression and evidence
1. Confirm CI source scan lists expected 61 assets and the plan checksum. Compare each owner source attribution, licence/IP boundary, expected private class, and exact byte count against the current CGX source authorities. Approval is manual.
2. Stage into an approved private root with SHA parity, then configure only the existing `CGX_PRIVATE_REVIEW_ROOT` on the approved LS GO host. Do not embed this path or owner credentials into static HTML.
3. Exercise a real owner-session login and the authenticated 411-component atlas, renders/hero and JSON mesh loader over the existing Desktop bridge. Confirm failed and revoked sessions cannot retrieve bytes, even after cached browser links are cleared.
4. **Separately, after owner readback:** make a guarded source commit removing public/static copies; scan built `dist/`, compiled JS/CSS and CDN caches for exact private bytes, and test unauthenticated / revoked / cross-tenant / offline request denial on real target deployment.
5. Only after independent acceptance and rights sign-off resolve #158. Issue #161 remains independently held until signed two-node FileSpace/DataSpace source/State_Root/DBR exchange.

## CI scope
`tests/test_cgx_private_review_asset_migration.py` proves dry-run has no writes, deterministic manifest, deliberate owner/count/hash requirements, exact independent staged readback on **synthetic temporary files only**, no source deletion/overwrite, refusal of symlinks, arbitrary extensions, >4 MiB files and disallowed target roots. Workflow checks actual source-tree inventory and static gate but does NOT upload its per-file hashes or execute staging. No live BouwerBase, Google Drive, public site, GitHub main merge or physical operation is claimed.
