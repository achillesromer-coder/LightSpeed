# CGX / UniSpace — private-byte public distribution gate

**21 October 2026 | Stacked source-only after PR #194 | Owner release review, not deployment**

## Exact gap addressed
The existing Vite source/dist release guard (#190) rejects names such as `/data/cgx_object_review_catalogue.json` and `/review/renders/`, but static/private content can leak under *renamed* asset paths or within emitted HTML/JavaScript bundles. The new `cgx/review/private_source_byte_disclosure_gate.py` tests content-level matches against all source-qualified internal CGX assets. The primary authority remains the existing 61-file migration plan (#193/#194), not a second catalogue.

## Implementation
- In pre-migration mode, re-create and verify the current source migration plan, reading and matching each of the 61 original static-review assets with exact bytes, size and SHA-256.
- In post-owner-stage mode, use an explicitly supplied *private*, non-repository `--approved-plan-file` plus `--private-root` directory (source private bytes must already be owner-approved, staged and hash-exact). This continues byte-scan proof after public copies have legitimately been removed.
- Scan a bounded destination tree recursively (at most 50,000 regular files and 256 MiB total, no symlinks) and detect source files copied under different paths, complete raw embedded source bytes, complete base64 encodings, and complete JSON-escaped UTF-8 source text. Exact binary match covers small source files; embedded-source scans require at least 64 original bytes to reduce meaningless false positives.
- Reports use only hashed candidate and source-path identities, match types and counts, not contents or plaintext private paths; source bytes and source manifest are not uploaded as workflow artifacts.
- No automatic release decision is ever granted: `public_release_authorised: false` even when this limited scanner detects no match.

## Source-authorised commands (read-only)

Before owner-approved migration, using known current original source tree:

```sh
python cgx/review/private_source_byte_disclosure_gate.py \
  --root /path/to/LightSpeed \
  --scan-root /path/to/LightSpeed/apps/lightspeed-go/dist
```

After owner-approved private staging and before publishing any new build, requiring a separately retained, owner-approved and source-root-verified manifest outside the repository:

```sh
python cgx/review/private_source_byte_disclosure_gate.py \
  --root /path/to/LightSpeed \
  --private-root /owner-approved/private/review \
  --approved-plan-file /owner-secure-location/review-source-plan.json \
  --scan-root /path/to/LightSpeed/apps/lightspeed-go/dist
```

The binary exit is **2** for found complete private sources, missing/unavailable source evidence or scan errors. A zero exit means ONLY no match of the tested complete source-byte representations. It is never a signed owner or ACL release receipt. Do not put the approved plan, raw private sources, credential material or results under `public/` or publish them in public CI artifacts.

## Scoped CI proof
The dedicated workflow builds the current source tree using `npm run build:internal` **inside an ephemeral GitHub Actions runner only** and then verifies that all 61 private review assets appear in the compiled distributable tree and the scan exits with a HOLD. The compiled tree is not deployed or uploaded. Synthetic negative tests separately check same bytes under a renamed path, copied inside JS, base64 and JSON string escaping, source tampering, manifest tampering, symlinks, and limits. Existing source migration and filename gates are also rerun.

## Completion boundaries
This detects neither arbitrary partial/private field extraction nor minified transformed strings, compressed/cryptographically encoded assets, confidential data newly introduced outside the 61 reviewed sources, screenshots, invisible cache copies or live network disclosure. It is not a complete DLP system, private asset removal, owner sign-in test, source/semantic root promotion or public site permission. An actual release still requires owner rights/ACL review, source removal/rehoming, all static tree and build route inspection, real denied unauthenticated/revoked/cross-tenant HTTP tests and CDN purge validation under #158. Independent signed two-node FileSpace/DataSpace acceptance remains #161 HOLD.

**No production, local host, GitHub main, Drive or owner files modified.**
