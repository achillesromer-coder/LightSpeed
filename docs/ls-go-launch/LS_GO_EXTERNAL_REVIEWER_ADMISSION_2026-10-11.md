# LS GO CGX — external reviewer deployment and admission packet
Date: 2026-10-11 · Execution status: SOURCE ONLY / NOT DEPLOYED / OWNER SIGN-OFF REQUIRED

## No second LS GO application

The same LS GO repository builds two explicitly bounded web projections:

- **Private operator artifact** `apps/lightspeed-go/dist`: all existing desktop/owner visualisation paths, including internal review assets. NEVER point an unauthenticated web host at this directory.
- **Visitor-only artifact** `apps/lightspeed-go/dist-review`: `npm run build:visitor` from existing authoritative `vite.config.js`. No copy of `public/` allowed. CI runs `node scripts/check_public_reviewer_artifact.mjs`; failures are release-blocking.
- Same FastAPI `ls_go_bridge.create_app`, existing Merovingian database, existing CGX parent identity and DBR root. No new second store/host/runtime.
- `https://romer.industries/cgx` remains the static public CGX orientation, not an authentication or private-asset mount.

## Public reverse proxy / route permit-list

The public reviewer HTTPS ingress MUST expose only these endpoints, never unrestricted `/api/v1/*`:

| Route | Method | Scope |
| --- | --- | --- |
| `/api/v1/visitor/capabilities` | GET | Orientation/readiness, no secrets |
| `/api/v1/visitor/enroll` | POST | One-time invite, consent and bounded profile |
| `/api/v1/visitor/me` | GET | Own profile, valid visitor bearer |
| `/api/v1/visitor/interaction` | POST | Attributable bounded review event, NO PRIVATE RESOLVER |
| `/api/v1/visitor/surface` | POST | Read exact Object_ID/lens/view from strictly preapproved Public projection, visitor bearer required; no source enumeration |
| `/api/v1/visitor/privacy-request` | POST | Own export/erasure/withdrawal request |
| `/api/v1/visitor/logout` | POST | Revoke own bearer |

Public 404/403 for `/api/v1/visitor/invites`, `/api/v1/visitor/revoke`, `/api/v1/visitor/owner-review`, `/api/v1/command*`, `/api/v1/projects*`, `/api/v1/results*`, `/api/v1/node*`, `/api/v1/representation*`, and ALL internal source, media and Desktop endpoints. These owner routes stay reachable only through the existing authenticated private operator path.

**Deployment template (not a command to deploy):** serve `dist-review` on an owner-controlled HTTPS origin. Configure explicit exact-path proxy rules for the seven approved visitor endpoints, and deny all other /api paths; reverse proxy to the already authenticated LS GO bridge over a protected host connection, never expose local port 8765 directly. Preserve origin allowlists, enforce small request bodies, 403/404 on forbidden paths, per-IP rate limiting, TLS, no-store responses and `Referrer-Policy: no-referrer`. Browser CSP should restrict script/style/connect sources to the intended first party. Do not generate a site-wide `proxy_pass` for `/api/v1/visitor/` because that prefix includes privileged owner endpoints.

## Privacy and identity acceptance

- Session tokens: 12-hour server expiry, hash-only database storage, current-tab sessionStorage for reload recovery; logout and owner revoke are implemented. Threat-model XSS and session theft before release.
- Invitation: 14-day expiry, single redemption, four allocated seat IDs, reissue revokes prior unused invites. Initial identity assurance is **INVITATION_POSSESSION_ONLY**, not verified legal/real-world identity.
- Submitted HTTPS profile URLs: structural checks only, NO remote fetch and NO external authentication. Mark **LINK_SUBMITTED_UNVERIFIED**. Later OAuth/OIDC requires trusted issuer, nonce/state/PKCE, audience, verifier/JWKS and owner-approved callback host. Never treat mere URL possession as a verified account.
- Captured with consent: name, theme, selected lens, voluntarily supplied background/intent, questions/model prompts, optional profile URL, timestamp and HMAC-chain. It may contain personal data. No silent device fingerprints.
- Privacy actions: data-copy, erasure and withdrawal request captured; withdrawal revokes active sessions. Automated export/erasure and legal retention schedule are NOT IMPLEMENTED. Owner must approve retention period, respond to requests and define deletion/archival that preserves necessary minimal audit without retaining unneeded personal content. Do not invite people until this policy is accepted.
- Review receipt HMAC confirms integrity under a current key, not independent CGX DBR authority. Provision and rotate key through owner secrets; long-term key-history/archival handling remains a documented acceptance gap.
- Single process/write lane until an atomic database append/lock/unique predecessor constraint is proven across multiple writers.

## CGX frontier and evidence

Every question, proposal, hypothetical geometry change and profile link remains review evidence and/or `PENDING_PUBLIC_SAFE_RESOLVER`. Do NOT return fabricated 3D or LLM output, operational claims, CAD, restricted roots, or private source contents. Future reviewer LLM may only receive explicitly approved PUBLIC_SAFE manifest projections carrying exact source hash/revision, rights/licence, Object_ID, evidential stage and readback, and must never execute commands via visitor authority.

## Reproducible source checks

From `apps/lightspeed-go`:
```bash
npm ci
npm run check
npm test
npm run build
npm run build:visitor
node scripts/check_public_reviewer_artifact.mjs
```

From repository root:
```bash
python -m pytest desktop/LightSpeed_Runtime/tests/test_ls_go_visitor.py -q
python scripts/validate_desktop_source_manifest.py
```

The exact manifest validator invocation must be checked against repository usage; any mismatched invocation should be treated as hold, not skipped.

## Production acceptance MUST include

1. Founder/owner approves explicit migration `ls_go_visitor_schema.sql` with verified existing-database backup/restore and exact installed-runtime/source parity.
2. Secret provisioned; app fails closed without valid key and migration; owner credential is healthy; no duplicate bridge/worker or unapproved port.
3. HTTPS and exact route allowlist from TWO independent off-device networks, plus intentionally unauthenticated GET of every prohibited private asset and endpoint.
4. Four invitations delivered privately only after the real host readback; selected themes/lenses, reload, expiry, reissue, revocation, logout, accessibility/mobile and privacy responses tested.
5. Separate license/source manifest and owner release gate for any portfolio image, CAD, simulation or model. #158 remains open until off-device negative GET tests and #161 until actual verified FileSpace/DataSpace end-to-end exchange.
6. Production artifact SHA-256, runtime/canonical source root, owner decision, rollback, TLS origin, proxy config digest and DBR readback persisted in the existing owner log.
7. No external reviewers sent a link until the above has independent PASS receipts. Dates are planning checkpoints, not release authority.

Related owner source: PR #172; security #158; FileSpace/DataSpace #161.

## Provider HTTPS acceptance probe

Source-only preparation now includes `scripts/verify_ls_go_visitor_https_release.py`. It performs **read-only** HTTPS checks against an explicitly supplied public origin and emits a JSON receipt; it does not deploy, issue invites, mutate CGX/DBR state, or persist session secrets. CI validates only Python compilation and `--help`; CI does **not** contact a deployment target.

Use only after an owner-controlled provider origin exists:

```bash
python scripts/verify_ls_go_visitor_https_release.py \
  --origin https://REVIEWER-HOST.example \
  --expected-review-sha256 EXPECTED_DIST_REVIEW_HTML_SHA256 \
  --output provider-review-acceptance.json
```

The probe verifies public `/review.html` and visitor capabilities, required no-store/referrer/CSP headers, exact reviewer HTML hash binding, fail-closed authority flags, invitation-possession identity wording, and 403/404 non-disclosure for owner/private API and known internal static paths. Optional valid/revoked-session proofs are read from `LIGHTSPEED_VISITOR_PROBE_VALID_SESSION` and `LIGHTSPEED_VISITOR_PROBE_REVOKED_SESSION`; token values are never written to the receipt. Absence of either session proof or of the expected artifact hash yields PARTIAL rather than PASS. Any private-route disclosure, unsafe capability state, header failure or hash mismatch yields FAIL.

This probe advances only deployment **readiness**. Until executed against the real provider-managed HTTPS ingress with owner-controlled sessions, issue #158 remains open and PR #172 remains DRAFT / NO PUBLIC DEPLOY.


## 15 October 2026 — reusable CGX / UniSpace object window

**SOURCE REVIEW ONLY; no public deployment or release authority.**

An existing reviewer `review.html` now contains a reusable dialog-based object lens backed by the same FastAPI LS GO bridge at `POST /api/v1/visitor/surface`. It uses only the existing owner-admitted Public manifest. Exact object ID and lens binding, approved payload hash, source revision, rights class and release receipt remain mandatory. Unknown/malformed/duplicated/unreleased sources fail closed. Map and historical modes remain held until independently verified public spatial and bitemporal projections exist; a requested valid-at or recorded-at date yields 409, never silently resolves to current.

Copy-ready compact Squarespace block: `docs/romer-web-hooks/CGX_UNISPACE_REUSABLE_SURFACE_EMBED_2026-10-15.html`. Its `CGX-SURFACE/UNISPACE-REVIEW` attribute is a non-secret UI selector, not an API key or authentication. Only set `data-review-origin` to a verified HTTPS reviewer host after separate acceptance. Never embed a private invitation fragment, browser session bearer, signing key, owner token or local bridge endpoint in page HTML.

The seventh external route requires an **exact POST reverse-proxy allowlist**, not an `/api/v1/*` wildcard. Enforce visitor bearer admission; no-store, no-referrer, CSP and origin allowlists. Verify CSP `frame-ancestors` permits the intended `https://romer.industries` embedding origin, and keep the standalone opening option if third-party browser storage is blocked.

Current `/cgx`, legacy `/operations/w1..w6`, `/gmat` and other Squarespace pages are optional **hosts** of this compact iframe, not copies of the backend or canonical files. They are not updated by this Git source change. PR #173 spatial/temporal and PR #175 UniSpace shorthand remain separate draft source candidates, not assumed merged. Security issue #158, native source/runtime issue #161 and owner privacy/public approval remain blocking.
