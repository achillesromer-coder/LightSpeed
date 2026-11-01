# UniSpace / CGX — Authenticated Objects viewer wiring

**21 October 2026; draft, source-only; stacked on PR #191.**

## Implemented
- The LightSpeed GO Objects lens no longer requests the known internal catalogues using public Vite `/data/` URLs. The signed-in owner session, not a page URL or GUI title, initiates the read.
- The newly integrated `privateObjectReview.ts` accepts only exact allowlisted legacy *references*, translating them to the existing authenticated Desktop bridge `/api/v1/private-object-review/{category}/{asset_name}`.
- Requests use the in-memory `X-LightSpeed-Session` owner token in a header, with `credentials: omit`, `cache: no-store`, no redirect and revocable `AbortController` instances. The file body is rejected on HTTP denial, missing/excessive size, unexpected MIME or missing/mismatched SHA-256 header. Browser WebCrypto is required; no insecure fallback.
- The bridge now explicitly exposes `X-CGX-Source-SHA256` to allowlisted browser origins via CORS, leaving CORS and owner session checks separate.
- Private gallery HTML emits no direct `img src` or `a href` pointing to the internal Vite static paths. Source-bound references are used only to request private bytes after authentication; lazy visible SVG thumbnails become in-memory Blob URLs. Engineering plate expansion uses an in-page dialog rather than opening potentially active SVG documents in new tabs.
- The existing interactive mesh viewer accepts the authenticated JSON media loader, and the original drawing/canvas logic is retained. It does not fetch a public mesh URL in private mode.
- On logout, failed login/password rotation or cancelled loading, all in-flight private requests are aborted, active modal closed, private gallery cleared and Blob URLs revoked. A delayed response from a previous session is ignored.
- Private data from a server response is not persisted to localStorage/IndexedDB, stored in a public manifest or published to any server.

## Evidence and limits
- Current CI validates source isolation, exact external-path allowlist, digest matching, denied/revoked responses, abort-on-logout, existing Objects rendering and whole-site build/typechecks.
- The existing PR #191 bridge and owner credential verification remain the only authentication authority. The browser does not trust merely seeing a sign-in button, an owner label or a URL fragment.
- User-facing catalogues can now render through the guarded endpoint **once the real local host has the private root configured and rights-cleared source bytes installed**; this change does not move or remove any of the known 61 static files.
- A valid owner session is not a permanent permission to download/save private assets. Per-object ACLs, source/custodian rights and future multi-user grants require their own server-side checks.
- Revoking a browser Blob URL limits reuse in this page; it cannot erase copies, screenshots, caches elsewhere or media users already saved. Proper logout and server-side session invalidation are both needed.
- No production build is authorised: issue #158 continues to block all public release until the original static assets are removed from public/, the built dist and caches scanned, actual private HTTP access verified across independent devices and roles, and the owner has reviewed source rights.
- Issue #161 separately requires signed independent peer FileSpace/DataSpace handshake and accepted receipts; no peer or host mutation occurs through this client-side integration.

## Source lineage
The branch is based on PR #191; prior #182 → #184 → #185 → #186 → #187 → #189 → #190 remain in review. The desktop source manifest retains 736 entries, with only the bridge CORS header digest refreshed. The existing CGX Object_ID/source authority, CCC capability family and Alexandria registered libraries are not duplicated.

## Next controlled acceptance
Owner-approved private source migration with 61-file SHA-256 parity; a real browser and host authenticated review after credentials and CORS are configured; unauthenticated/expired/revoked/cross-tenant endpoint denial and no fallback; built HTML/JS/CSS/private CDN cache scan; catalogue data governance and licensing. Only then lift the public-site HOLD.
