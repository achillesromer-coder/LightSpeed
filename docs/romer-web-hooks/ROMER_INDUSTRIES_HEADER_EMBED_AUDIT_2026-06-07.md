# Romer Industries Header / Embed Hook Audit — 2026-06-07

Result label: ROMER_WEB_HEADERS_AUDITED__HOOK_BLOCK_READY__SHEET_REAUTH_REQUIRED

## Source state

- Live source audited: https://romer.industries
- Sheet source requested: https://docs.google.com/spreadsheets/d/1wLNW2cC-vQ1ZTzNmgGQiSFE0wGp_dvupCW1ZGBtT_yw/edit?usp=sharing
- Sheet read status: blocked by expired Drive connector token / not public-fetchable in this environment.
- Live publish status: not attempted; Squarespace/manual operator paste remains required.

## Outputs

- romer_route_header_embed_map.csv
- romer_route_hook_manifest.json
- romer_achilles_route_header_hook_embed.html

## Route findings

- `/` — FETCHED — H2: Green Sollutions for a Space Fairing Type 1 Civilisation & Nation — badges: PUBLIC, ROUTE HUB, REVIEW — risk: HIGH
- `/home` — FETCHED — H2: Green Sollutions for a Space Fairing Type 1 Civilisation & Nation — badges: PUBLIC, ROUTE HUB, REVIEW — risk: HIGH
- `/aus` — FETCHED — H1: Securing Australia’s Sovereign Capabilities in Public & National Interest — badges: AUS, PUBLIC-SAFE, EVIDENCE GATE — risk: HIGH
- `/emassc` — FETCHED — H2: E = MASS . C^2 — badges: EMASSC, CLAIMS REVIEW, NO TOKEN — risk: HIGH
- `/green-initiative` — FETCHED — H3: Embedded — badges: ECO, PUBLIC-SAFE, REVIEW — risk: LOW
- `/green-innitiative/embedded` — SEARCH_CONFIRMED_DIRECT_FETCH_404 — H1: Embedded — badges: ECO, EMBEDDED, REVIEW — risk: MEDIUM
- `/inter-sol` — FETCHED — H1: InterSol, proposed to be Australia’s first space port for re-usable rocketing technologies. — badges: INTERSOL, CONCEPT, REVIEW — risk: HIGH
- `/contact-us` — FETCHED — H2: Contact Us — badges: CONTACT, PUBLIC, SAFE — risk: LOW
- `/take-action` — FETCHED — H2: Inter Sol — badges: CONTACT, INTEREST, REVIEW — risk: MEDIUM
- `/operations` — FETCHED — H3: Inter-planetary Supply Chain Network — badges: OPERATIONS, INTERNAL-FIRST, REVIEW — risk: MEDIUM
- `/operations/w2` — FETCHED — H2: OPS TRACKER: W2 · LUKE II CATCH/HOLD — badges: W2, RFS/EMFF, CLAIMS BLOCKED — risk: HIGH
- `/operations/w3` — FETCHED — H2: OPS TRACKER: W3 · RFS & EMFF — badges: W3, FIELD PROJECTIONS, CLAIMS BLOCKED — risk: HIGH
- `/operations/w4` — FETCHED — H1: Market Opportunities & Growth Projections — badges: W4, SUPPLY CHAIN, MARKET REVIEW — risk: HIGH
- `/operations/w7` — FETCHED — H1: DECENTRALISED PUBLIC BENEFIT CONTRACT & LEDGER ARCHITECTURE — badges: W7, REGISTRY, WALLET/TOKEN LOCKED — risk: MEDIUM
- `/emassc-log-in` — FETCHED — H3: Technological Innovations — badges: LOGIN, PRIVATE, NO LIVE AUTH — risk: MEDIUM

## Recommended execution

1. Re-auth Google Drive connector and read the source sheet tabs.
2. Compare sheet rows against `romer_route_header_embed_map.csv`.
3. Paste `romer_achilles_route_header_hook_embed.html` into a test Squarespace code block on one low-risk test route first.
4. Confirm desktop/mobile render, visible badges, and blocked-action panel.
5. Only then roll the same static hook block to the selected Romer route headers.