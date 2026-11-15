# UniSpace Public CGX — Source Fold and Static Release Boundary
**2026-10-20 · Source-only review candidate · Not deployed · Owner gate #158 remains OPEN**

## Why this is additive
Base: PR #187 (which stacks on #186/#185/#184/#182). Source: draft PR #174, exact original source head `317156f2b4ad9dddbc9ce5c2137407f726818d5c`.

The public synthetic-only viewer assets and its 2 JS tests + CI/deployment source are folded **unchanged**: 18 original source blobs pinned in `cgx/review/unispace_public_source_fold_20261020.json` and checked by Git blob hashes. There is no second frontend, CGX authority, corpus master, hosted site, user subscription or external archive download.

## Exact public package
`apps/lightspeed-go/scripts/cgx_public_bundle_guard.py` produces an **independent candidate directory** containing only:
- `/cgx/index.html`, seven synthetic route pages in all (overview / fs / ds / ps / doom / romer / eco).
- Five already-approved synthetic `/cgx/assets` JS/CSS source files.
- Public route-only Vercel header/CSP policy at package root.
- A deterministic, unsigned `cgx-package-review.json` containing SHA-256 and byte counts, with `owner_approval_required: true` and `external_host_live_verified: false`.

It explicitly does **NOT** read from, or copy, the rest of `apps/lightspeed-go/public`, including:
`public/data/cgx_object_review_catalogue.json`, `public/data/component_geometry_atlas_public_review.json`, `public/review/mesh/**`, `public/review/renders/**`, credentials, local-operator JS/TS or `dist/`.
The allowlist requires the exact 12 reviewed public source files, rejects unknown paths, symlinks, oversized files, encoded non-UTF8 text, private source/API/credential patterns, unsafe script/module references, and a drifted restrictive CSP. Copies to a newly created directory only, re-verifies source bytes to reduce TOCTOU risk, and rejects replacing existing output. A real deployment still requires owner and hosting approval.

## Important issue #158 distinction
**Separate synthetic public site:** this staged *allowlisted build* is source-isolated and has no intended private server/machine dependencies. Passing CI only demonstrates this particular build candidate excludes operator source files.

**Existing LS GO operator site:** `apps/lightspeed-go/public/data` and `apps/lightspeed-go/public/review` still contain internal source review assets in the original Vite public tree. A **normal LS GO/Vite build or dev server may serve them unauthenticated** unless the operator site is independently remediated. This PR does not remove or reclassify those assets, change `vite.config.js` or `main.ts`, or pretend issue #158 is closed. An operator release must pass its own negative unauthenticated GET/revocation/access tests, private resolver/owner session, and public allowlist/compiled-dist residual scan. Use only the new allowlisted candidate for the public synthetic deployment.

## How to inspect without publishing
Run from repository root:

```bash
python apps/lightspeed-go/scripts/cgx_public_bundle_guard.py
python -m unittest discover -s tests -p 'test_cgx_public_bundle_guard.py' -v
python apps/lightspeed-go/scripts/cgx_public_bundle_guard.py --output /tmp/unispace-cgx-public-review
```

The last command creates a **non-production folder** and does not upload or deploy it. No sandbox location or cloud deployment is assumed. The CI also runs original PR #174 synthetic viewer tests.

## Next release and source sequence
1. Review draft PR #174's original source owner/licence records and its static policy; preserve archived benchmark source claims.
2. Validate this candidate's 7 routes from a local static server *rooted at the newly packaged output*, not all of LS GO `public/`. Test browsers, mobile, scripts, CSP and no leaked private routes.
3. Independently remediate issue #158 for **operator GO** by moving internal assets out of Vite public roots, accessing them only via existing authenticated and scoped owner bridge and validating 401/403, revocation and private metadata tests.
4. Owner-approved separate static hosting of the verified public candidate, if desired. PR #174's former Vercel deployment/alias is not new readback from this branch; this source fold makes no live HTTPS claim.
5. Continue issue #161 native signed FileSpace/DataSpace peer tests and Creator/Press full use of the existing shared CGX registry. Public viewer demos do not authenticate or execute node commands.

Original PR #174, issue #158, and issue #161 remain unchanged. No main merge, LS GO UI mutation, source deletion, provider upload, host C:/D: operation, payment system or real device activation occurred.
