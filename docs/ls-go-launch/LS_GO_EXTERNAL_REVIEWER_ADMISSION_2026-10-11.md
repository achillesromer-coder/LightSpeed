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
| `/api/v1/visitor/privacy-request` | POST | Own export/erasure/withdrawal request |
| `/api/v1/visitor/logout` | POST | Revoke own bearer |

Public 404/403 for `/api/v1/visitor/invites`, `/api/v1/visitor/revoke`, `/api/v1/visitor/owner-review`, `/api/v1/command*`, `/api/v1/projects*`, `/api/v1/results*`, `/api/v1/node*`, `/api/v1/representation*`, and ALL internal source, media and Desktop endpoints. These owner routes stay reachable only through the existing authenticated private operator path.

**Deployment template (not a command to deploy):** serve `dist-review` on an owner-controlled HTTPS origin. Configure explicit exact-path proxy rules for the six approved visitor endpoints, and deny all other /api paths; reverse proxy to the already authenticated LS GO bridge over a protected host connection, never expose local port 8765 directly. Preserve origin allowlists, enforce small request bodies, 403/404 on forbidden paths, per-IP rate limiting, TLS, no-store responses and `Referrer-Policy: no-referrer`. Browser CSP should restrict script/style/connect sources to the intended first party. Do not generate a site-wide `proxy_pass` for `/api/v1/visitor/` because that prefix includes privileged owner endpoints.

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
