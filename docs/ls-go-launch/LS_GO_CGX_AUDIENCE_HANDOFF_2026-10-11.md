# LS GO / CGX — audience-scoped visitor integration handoff
Date: 2026-10-11 (Australia/Brisbane)
Status: FEATURE BRANCH / OWNER REVIEW / PUBLIC RELEASE HELD

## Single-stack reconciliation

- `/cgx` on romer.industries remains the bounded public CGX orientation surface. It is neither the LS GO authenticated interface nor the canonical DBR ledger.
- LS GO remains ONE application: its existing Vite web build now contains `review.html` as an additional audience-scoped entry, and the existing Command Centre adds `Review`.
- LS GO remains ONE bridge: `lightspeed_runtime.ls_go_bridge.create_app` installs `ls_go_visitor.register_visitor_routes`. No new HTTP listener, scheduler, filesystem master or agent runtime is introduced.
- CGX = FileSpace; parent `Cognigrex.cgx`. DataSpace is authorised sparse exchange; PrintSpace and Digital Twins are evidence-bound projections/operations, not independent canonical stores.
- Existing owner login, Desktop command/receipt path, object identity and owner review workflows are retained. Visitor API cannot address those command or private-file paths.

## Access tiers and present implementation

| Audience | Frontend | Current server admission | Functional privileges |
| --- | --- | --- | --- |
| Public | Römer /cgx | public page only | orientation; no workspace or backend proof |
| Visitor (4 seats) | LS GO /review.html | one-time invite redemption + 12-hour bearer session; human/legal identity not independently verified | consented preferences, four lenses, interactions queued/receipted; source and model hydration held |
| Collaborator | LS GO role contract | NOT IMPLEMENTED (requires federated identity and ACL grant) | no inherited visitor/owner privilege |
| Operator | Existing LS GO workspaces | existing runtime authority lease and owner/canonical gates | unchanged |
| Owner | Existing LS GO Activity login and Review panel | existing credential + owner session | issue/reissue 4 reviewer seats, inspect reviews; canonical promotion still independent |

## Handshake and retention semantics

Explicitly persisted in the **existing database**: assigned reviewer ID, provided display name, consent timestamp, selected theme/lens, voluntarily entered background/interest, interactions, request type and evidence-status receipts. Never infer demographic/psychological traits or silently construct a person profile from a question. Keep receipt profile scope clearly stated to reviewer.

No raw invitation secret, plaintext credential, model key or visitor bearer token is stored: only SHA-256 token digests. Session bearer is kept in browser memory, **not localStorage**. Reload/sign-out requires a new owner-issued link; original preferences can be used again after a renewed enrollment. This is a deliberate first-boundary limitation, not full cross-device account persistence.

Contact verification (email/phone/OIDC) is NOT IMPLEMENTED; invitation possession must not be labelled independently verified identity. Privacy notice, retention/deletion workflow, opt-out and regional legal/privacy review require owner acceptance before distributing links.

## DBR / audit meaning

- `LS-GO-CGX-VISITOR/0.1` is a bounded, HMAC-chained *review* receipt stream stored in the existing Merovingian/LS GO DB, with per-reviewer predecessor hash and owner-side verification.
- It is not a CGX root change, signed canonical carrier release, independent engineering proof, or permission grant.
- Canonical reconciliation requires owner-approved resolve/DBR ingestion with original Object_ID, source/rights, evidence ceiling, parent root and readback. Do not auto-import interactions as truth.

## Installation and gates

1. Review this branch against current `main` and the current live owner state; preserve all other lane branches and credentials.
2. Explicitly apply the reviewed additive SQL in `desktop/LightSpeed_Runtime/lightspeed_runtime/ls_go_visitor_schema.sql` to the verified **existing** database with an immutable backup/rollback. It is never automatically applied by a web request. Do not attempt migration on an unknown path or read-only connection.
3. Provision `LIGHTSPEED_VISITOR_RECEIPT_KEY` (at least 32 characters) through the existing secret manager; set `LIGHTSPEED_VISITOR_REVIEW_ENABLED=1` only after the schema, connection and owner gates pass. Default disabled.
4. Configure an approved HTTPS same-origin reverse proxy for `/api/v1/visitor/*` or `VITE_LIGHTSPEED_VISITOR_API_ORIGIN`; preserve exact CORS origins. No direct exposure of localhost bridge or arbitrary tunnelling.
5. Confirm the owner credential and session gate; use LS GO Activity sign-in, then Review to issue **at most four** distinct links. Each `review.html#invite=...` URL is sensitive. It MUST NOT be placed on public /cgx, GitHub or logs.
6. Before host publication, close LightSpeed#158: private static `public/data`, `public/review/renders` and `dist` contents require allowlist/redaction and negative unauthenticated GET tests; source storage location alone does not enforce ACL.
7. Before substantive AI/model replies, close related LightSpeed#161 and admit a verified public-safe resolver with source rights, object state, geometry hash, licence, uncertainty, evidence and publication receipts. The present UI *correctly returns pending* for model generation and AI responses.
8. Verify off-device mobile/desktop flows, duplicate invite denial, session expiry/revocation, 401/403 for private route attempts, owner readback and hash-chain integrity. Run tests and record exact provider/artifact hashes.
9. Owner-specific security/legal/publication sign-off and rollback receipt are required before invitations are sent.

## Verification that can be claimed

A passing source CI test proves the Python contract and TypeScript/build checks under that run's checkout, NOT live network capability, actual owner login, real LLM/model generation, deployed static path isolation, or human identity verification.

## Files introduced / adjusted

- `apps/lightspeed-go/review.html`, `src/visitorMain.ts`, `src/visitorBridge.ts`, `src/visitorWorkspace.css`, `vite.config.ts`
- `apps/lightspeed-go/src/ownerVisitorReview.ts`, `src/main.ts`, `src/osShellModel.ts`
- `desktop/LightSpeed_Runtime/lightspeed_runtime/ls_go_visitor.py`, `ls_go_visitor_schema.sql`; bridge registration and CORS header
- `cgx/domain_templates/ls_go_visitor_workspace_contract.json`
- visitor unit and UI regression workflow

No production deployment, canonical write, local Windows host mutation, paid service activation, mail/SMS send, or new automation is part of this branch.
