# UniSpace private CGX Objects gateway — source acceptance candidate

Date: 20 October 2026. **Stacked review-only after PR #190.** No live route deployment, no public release and no owner-data relocation performed.

## Source-first reason
The LS GO Objects lens currently fetches `/data/cgx_object_review_catalogue.json` and `/data/component_geometry_atlas_public_review.json` from Vite's `public/` directory and links to `/review/renders` and `/review/mesh`. In the earlier #189/#190 static audit there were **61 known internal-review files at these paths**. The public site build is blocked. This new code adds a permissioned read surface for those same *classes* of assets; it does not reclassify the existing static files as releasable.

## Implemented
- `lightspeed_runtime/private_review_assets.py` reads from the **explicit** `CGX_PRIVATE_REVIEW_ROOT` absolute path, not from the Vite asset root, GitHub, Drive, source names or UI inputs.
- Private root must exist, must not point inside any `public` or `dist` component, and rejects symlink and parent escapes. No default root or public fallback is provided.
- Allowlisted routes only: `catalogue/cgx_object_review_catalogue.json`, `atlas/component_geometry_atlas_public_review.json`, `renders/<filename>.svg`, `mesh/<filename>.json`. Dynamic filename is restricted and no traversal, dot files, arbitrary extensions or directory listing is allowed.
- Response size capped at 4 MiB per file, exact bytes SHA-256 calculated and returned as owner-only header.
- Existing `ls_go_bridge.create_app` gets **GET** `/api/v1/private-object-review/{category}/{asset_name}`: every request must include `X-LightSpeed-Session` and pass existing `_verified_owner_actor` with `confirmation=None`. The old confirmation-header mechanism deliberately cannot read these private assets. No token in URL, cookies, static HTML or artifacts.
- Responses include `Cache-Control: no-store, private`, `nosniff`, frame denial and sandboxed CSP. File read changes no local state.
- Existing desktop source-manifest gains a private reader record and one new hash for the bridge, preserving original 734 entries and #177, #186 and #187 identity/source-readback contracts.

## Deliberate non-activation
- No `CGX_PRIVATE_REVIEW_ROOT` is configured on actual host by this PR.
- Existing 61 public paths are unchanged and may still be served by a development/static web server. The #190 default build gate remains FAIL-CLOSED.
- Objects UI is not yet rebound to the new owner-only endpoint. Browser loading must use header-based requests and create short-lived in-memory blob URLs for SVG/mesh thumbnails only after authenticated readback. Do **not** put tokens in query parameters or expose raw server paths. Revoke and clear Blob URLs at logout and project/ACL switch.
- Do not bypass gate by using `build:internal` for public hosting; it is local development only.
- No actual second-device sign-in, credential database operation, HTML browser flow, remote relay or live no-auth HTTP test was performed; tests include only isolated server route checks with the real session-validation hook mocked for selected positive cases. Authentication correctness still depends on the separately tested existing OwnerSessionStore.

## Owner source placement sequence
1. Obtain explicit owner approval on each of the 61 original static files, its classification, source digest and rights. Establish a local private root outside any static Vite directory.
2. Copy files with identical hashes, preserving `data/`, `review/renders/`, `review/mesh/` layout. Verify expected 61 files, digest parity, ownership and access controls; retain original source authority.
3. Update `objectReview.ts`/the LS GO client to load catalogues via `desktopBridge` owner-header calls and gallery media through owner-authenticated, bounded Blob URLs. Session failure must show unavailable and not fall back to public URLs.
4. Only after source readback, delete/move public copies in a separately reviewable source commit. Confirm `public/`, built `dist/`, JS/CSS bundles and CDN cache contain no held bytes or URLs.
5. Run unauthenticated, expired/revoked, changed-owner/cross-tenant and remote HTTP negative tests against the *actual deployment*. Explicitly verify no old cached public asset survives.
6. Close issue #158 only after independent owner security acceptance. Issue #161 remains a separate authenticated two-node FileSpace/DataSpace gate.

This is an additive capability within the same Cognigrex/LightSpeed runtime and is **not** a separate master library, server, cloud, scheduler or native peer. CGX-CCC refers to the current common capability family and must not be conflated with the older Create Your Collective project.
