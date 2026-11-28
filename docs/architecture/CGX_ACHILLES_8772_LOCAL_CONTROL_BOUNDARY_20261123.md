# Achilles localhost 8772 · one-root UniSpace SystemSpace projection

Status: **source-qualified read-only UI bridge**, not host API or native admission. Date of machine observation: 23 November 2026. Reviewed using an authorised, batched, read-only BouwerBase PowerShell probe; no settings, process or lease were changed. Remote Desktop Commander emergency reserve is protected.

## Exact live observation (one point in time)
- GET \`http://127.0.0.1:8772/\` -> HTTP **200**, \`<title>Achilles shell</title>\`, content type \`text/html; charset=utf-8\`. TCP bound to \`127.0.0.1:8772\`; Python 3.14 processes were observed.
- GET \`http://127.0.0.1:8772/health\` -> HTTP **404**. **Do not invent a /health route.**
- Page exposed agent start/stop/pause; CPU ceiling slider 10–100 step 5 with 40/70/95 presets; auto-disable failing agents; generic LLM sorter pass; loaded-model and operational-note regions. Presence was observed; **current values, API semantics, model identities, host ACL and signed authority were not**.

## Integration topology
- Port **8772** = existing Achilles **local oversight** page; local navigation only.
- Port **8765** = existing LightSpeed Desktop bridge baseline from \`desktopBridge.ts\`; its own \`/api/v1/status\` contract is unrelated. Do **not** silently replace or unify ports.
- Existing UniSpace shell mounts a **SystemSpace** read-only capability card with a fixed literal loopback link. No iframe, proxy, automatic cross-origin fetch, cookie, POST, root mutation or scheduled task. The operator link is useful on BouwerBase; on other devices 127.0.0.1 refers to that device, **not** BouwerBase. Unreachable/CORS status cannot be equated to host outage.
- Six observed operator capability **categories** are UI subfacets, not six canonical CGX/Grex roots. Existing \`cgx:root:cognigrex\`, five UniSpace operational facets and ProfileSpace/SystemSpace contexts remain intact.

## Current bound / follow-up acceptance
- Read-only labels and local link require no new login or signing; the local 8772 UI retains sole authority for its existing controls.
- Before interoperable in-page status: inventory actual GET API and CORS/Private Network Access policy on the existing host, validate owner session, signed scope, response schema and denied/revoked test vectors. \`/health\` is **not** an approved probe.
- Before any remote control: obtain separate explicit scope plus authenticated existing native ACL/lease and independent node readback. Do not forward a public site's agent start/stop or CPU controls to 127.0.0.1.
- Existing GitHub issues #158 (static/private asset boundary) and #161 (native FileSpace/DataSpace identity, signed DBR and restart recovery) stay open; all 51 cross-space engineering groups remain OPEN. No public Squarespace edit or mint is implied.

Verification: \`apps/lightspeed-go/src/cgxAchillesLocalShell.test.ts\` synthetic invariants; combined current frontend test suite; strict TypeScript/Vite; exact tracked \`dist\` parity CI. Real local snapshot is independently observed but **not continuous monitoring**.
