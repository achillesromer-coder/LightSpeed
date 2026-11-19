# Universal CGX / UOS Endpoint — Squarespace and Independent Nodes
Date: 2026-11-19
State: SOURCE-ONLY REVIEW. No live Squarespace edit, native mint, peer deployment, or authenticated execution.

Canonical implementation: docs/romer-web-hooks/uos_universal_gateway_embed.html

## Principle
One compact URL-aware Squarespace code block resolves current page context to
a public semantic facet. Existing UniSpace, FileSpace, DataSpace, PrintSpace,
ProfileSpace and the singleton LightSpeed operational database retain authority.
A URL is not an identity, lease, source right, network node or proof of liveness.
The same mechanism can be embedded on multiple approved pages without deploying
a new JS application, daemon, model, registry, database or task consumer.

## Route / page type map
| Path family | Page type | Bound facet | State |
| --- | --- | --- | --- |
| /, /home | Portfolio | Romer | Public web |
| /aus, /inter-sol, /emassc, /green-initiative | Research and programmes | Romer / EMASSC / Eco | Public or historically seen |
| /team, /contact-us, /take-action | People / collaboration | ProfileSpace / Romer | Public or historical |
| /operations, /operations/w2, /operations/w3, /operations/w4, /operations/w7 | Study/operations projection | LightSpeed / EMASSC / Romer / DataSpace | Public or historical |
| /lightspeedhome, /ls-go, /ls-go/status, /ls-go/handoff, /ls-go/review, /ls-go/agents | Command and operator shell | LightSpeed | Public/historical; agents requires verification |
| /uos, /uos/{facet} | Universal UOS and virtual facet | UOS / selected facet | Proposed route; no browser privilege |
| /cgx, /cgx/LOAD, /cgx/lightspeed | CGX product catalogue | Cognigrex / LOAD / LightSpeed | Candidate, release-held |
| /cgx/fs, /cgx/ds, /cgx/ps, /cgx/profile | Space portals | FileSpace / DataSpace / PrintSpace / ProfileSpace | Candidate |
| /cgx/ccc, /cgx/cyc, /cgx/doom | Workflow/demo | CCC / CYC / game | Candidate |
| /cgx/achilles, /cgx/neo, /cgx/athene, /cgx/raphael, /cgx/eco, /cgx/romer | Grex / research | Existing selectors | Candidate |
| /docs | Existing public document listing | Cognigrex | Publicly indexed; individual rights review required |

Exact lower-case path match precedes a bounded virtual /uos/{facet} match.
Unknown, cross-origin, encoded, traversal or oversized URL cases fail closed
to the unmapped public view. Rendering a route never creates a Squarespace page.

## Filetype endpoint policy
| Filetype | Public treatment | Independent acceptance |
| --- | --- | --- |
| .cgx | Metadata and approved carrier links | Native parser, signature, licences, rights |
| .cgx.html or HTML | Reviewed portable viewer projection | CSP, script QA, rights |
| .cgxpack.zip / ZIP | Size/hash/manifests; never automatic execution | Reproducible release and signed assets |
| JSON / JSON-LD | Public machine-readable route and source provenance | Schema and signature if authoritative |
| TXT, llms.txt, Markdown | Public index, documentation, AI discovery | Published claims and citations |
| CSV / XLSX | Approved public data preview or file | Data classification and per-occurrence ACL |
| PDF | Approved public paper and evidence | Rights and accessibility |
| SVG, PNG, GLB, OBJ, STL | Preview or download approved assets | Licence and validated geometry |
| EXE, scripts, print actuation | No browser execution | Native owner/host/physical safety gates |

These are handling policies, not a claim the embed parses each format.

## Execution and persistence path
1. The static embed reads window.location origin/path and consults its
   bounded route table, without fetch, remote script, or browser storage.
2. It emits a DOM-only public-route-discovered event and can copy a
   public descriptor on explicit user click. No automatic peer connection.
3. Native UniSpace may accept such a descriptor only after independent
   host/session verification, selector revision binding, file SHA/source
   identity, per-occurrence FileSpace ACL, rights, issuer and lease proof.
4. The draft PR #228 checkpoints, if approved and installed, write bounded
   metadata to existing operational_events in lightspeed_unified.db, not
   to a second registry. They do not train models or grant execution.
5. DataSpace nodes are free to run without Squarespace. A future node
   advertises a verifiable, signed public manifest, then admits peers
   via authenticated challenge/response with explicit role and permission.
6. Peer heartbeat is an authenticated, TTL-bounded lease observation.
   It cannot be inferred from page refresh, JS activity or public status.
   Automation scheduling continues through an authorised local supervisor
   with owner stop/revoke authority, not through a browser timer.
7. Native mint, T173 geometric compression, physics claims and PrintSpace
   actuation remain separately gated. T174 remains a non-mintable sentinel.
   The shell sets ternary_shape to unresolved and does not imply
   lossless data reconstruction.

## Proposed future node endpoint contract (NOT implemented here)
| Path | Authorization | Purpose |
| --- | --- | --- |
| GET /.well-known/cgx-node.json | Public signed asset | Independent node discovery hint |
| GET /api/v1/cgx/public/routes | Public sanitised | Approved public route catalogue |
| Existing GET /api/v1/cgx/surface | Owner session | Private capability projection from PR #228 |
| Existing GET /api/v1/cgx/family/topology | Owner session | Private selector/carrier mapping from PR #228 |
| POST /api/v1/cgx/peer/offer | Authenticated future | Challenge, role/capability request |
| POST /api/v1/cgx/peer/confirm | Authenticated future | Verified admission, signed lease |
| GET /api/v1/cgx/peer/lease | Authenticated future | Lease/heartbeat status |
| POST /api/v1/cgx/peer/revoke | Authenticated future | Revocation and receipt |

Protect future endpoints with TLS, restrictive CORS, CSRF where applicable,
identity and signature checks, anti-replay, source classification,
rates/quotas and opt-in consent. Never include personal machine addresses,
API keys, passwords, private profiles or wallets in public code.

## Audit evidence and regression constraints
The June 2026 Squarespace route-hook and LS GO shell source were inspected.
The 11 November offline workbench was reported as 49 editable page tabs,
392 blocks and 21 tests, but its pages were not authenticated against the
Squarespace live editor. The 19 November public fetch confirmed the
Romer website and AUS page; /uos, /cgx/LOAD, /docs, /cgx could not be
independently fetched, and /team and /ls-go were not verifiable on this pass.
Do not promote historical observed status to current HTTP 200 without proof.

Squarespace procedure: backup current blocks; create /uos as Not Linked pilot;
paste the single embed into a Code Block; confirm that Squarespace permits
the script/CSP; verify desktop/mobile, 404 fallbacks, clipboard denial,
a11y, old LS GO coexistence and public rights; then expand to published
product/space/Grex pages. Keep existing page content. Log page IDs, route,
revision, test receipt, owner approval and rollback in existing DBR records.
Never automatically merge PR #228 or deploy the live Core as part of this.

## Sign-off
[x] Source hooks reconciled; review-only gateway implementation created.
[ ] Authenticated Squarespace page ID inventory and actual page creation.
[ ] Live CSP, embed, device and regression QA.
[ ] Public release assets, rights, signatures and owner approval.
[ ] Independent DataSpace peer authentication and heartbeat implementation.
[ ] Native UOS source acceptance and controlled live deployment.

## 2026-11-19 live website delta (public retrieval, not editor verification)

Verified linked routes include /green, /green/future, /green/embedded,
/green/second-cycle, /gmat, /mpl-engine, /raphael, /lightspeedhome and /docs.
The former /green-initiative naming is retained as historical reference, not
a guaranteed active alias. The public command centre's displayed operating
and scientific validation labels are not independent evidence of deployed
services or empirical claims.

The /docs page publicly lists document titles including founders/operating
agreements, IP reports and research files. Do not ingest, mirror or licence
attachments just because their URLs are visible: review each source for
permission, data classification, authorship and public release suitability.

The LightSpeed command centre links six paths that presently return HTTP 404:

| Missing link | Candidate future UOS selector | Confirmed site fallback |
| --- | --- | --- |
| /w1-data | /uos/w1 | /lightspeedhome |
| /w2-data | /uos/w2 | /lightspeedhome |
| /w3-data | /uos/w3 | /lightspeedhome |
| /w4-data | /uos/w4 | /lightspeedhome |
| /w5-data | /uos/w5 | /lightspeedhome |
| /w6-data | /uos/w6 | /lightspeedhome |

The /uos/w1-w6 virtual selectors are NOT real Squarespace routes until an
authorised editor creates and publishes suitable pages. A public source
table cannot repair an HTTP 404 or confer access to a private DataSpace.
Retain /lightspeedhome as the published navigation fallback until the
specific targets have been independently tested at HTTP 200.

### Source-level regression
- Fixed the route extraction regex to include "/" and detect the six
  missing-404 routes; 51 unique source routes are now represented.
- Added VM-executed URL routing tests for home, ecology, uppercase path,
  virtual facet, unknown route and 404 evidence labels.
- Dedicated secret-free and deploy-free GitHub Actions workflow passed:
  run 44450285774, head 730aff768c82426b5561c6f2c4fade6684ccdf18.
- Source tests do not establish Squarespace publishing, browser CSP
  compatibility, native runtime deployment or peer transport.
- Desktop Commander indicated 31% monthly call allowance remaining
  at this check; no remote machine mutations were performed.

### Next release gates
1. Authenticated Squarespace page-ID inventory, backups and preview.
2. Public document rights/claims classification before llms.txt or
   public data indexing.
3. Create Not Linked /uos pilot, then repair six missing W1-W6 routes.
4. Test mobile layout, sandbox/code-block script policy and existing LS GO.
5. Independently authorise signed DataSpace peer identity, heartbeat,
   revocation, local runtime acceptance and publication/mint separately.
