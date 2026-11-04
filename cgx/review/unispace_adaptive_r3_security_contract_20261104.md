# UniSpace adaptive FileSpace R3 boundary — source-only review (2026-11-04)

Source baseline: `cgx/domain_templates/view_selection_policy.json` blob `27ca0230e75743448c91482f2ea0a454f67bfab6`; `apps/lightspeed-go/src/osShell.ts` default-branch blob `b7a5d1009d2597180502f853ca9caa90fe83dd8a`. This is a proposed interface contract, NOT an installed component.

## One-object hydration contract
Input: authenticated server-side scope decision, exact accepted `Object_ID`, child FileSpace ID, source revision/rights, evidence ceiling, selected subgraph and requested task/device. Reject absent/mismatched identity, expired/revoked session, missing issuer/DBR/lease, wrong child domain, unqualified rights or unverified provenance. Never use display palette or localStorage as an authorization source.

Output: at most one primary view per existing view-selection policy; secondary inspector opt-in. H0 identity, H1 scoped typed edges, H2 permitted provenance, H3 only qualified capabilities, H4 only with independently authorized execution. Missing source/geometry frame/units => explicit FRONTIER, never synthetic map/3D. R0/R1 private source bytes remain server-side. Browser offline mode may show only previously approved redacted snapshot with stale timestamp and no execute controls.

## Acceptance negatives (not yet run on deployed host)
1. Anonymous request for private Object_ID => deny, no private identifier or metadata in HTML, JS, Vite dist, source map or network response.
2. Revoked/expired/forged session => deny even if localhost or X-LightSpeed-Session header is supplied.
3. Valid session for child A requesting child B => deny H0–H4 hydration, including search/context menu.
4. Valid read-only scope => H0–H2 permitted, H3 only qualified discovery, H4 denied.
5. Object_ID substitution after authorization => deny; same Object_ID retained across document/graph/matrix/3D lens switching.
6. Geometry absent or evidence below R2 => FRONTIER; no physical coordinates, simulated measurements or live badges.
7. Smith bridge HTTP 200 with stale PID => BRIDGE_REACHABLE / CONSUMER_HELD, no dispatch-ready indicator.
8. Offline cached snapshot after revocation => no fresh data or execution; explicitly stale, scoped cache policy reviewed.

## Proof required
Pinned code/branch diff, TypeScript tests, keyboard/mobile/a11y tests, built-dist private asset scan, authenticated host negative responses with issuer/ACL/DBR/lease and independent browser readback. Source-only Git CI is not host verification. Issues #158/#161/#209 and S92/S97 remain HOLD. No native mint, public release or token/physical execution authorized.
