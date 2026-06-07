# Squarespace Paste Packet — Romer Industries Header Hook — 2026-06-07

Result label: ROMER_HEADER_HOOK_READY_FOR_MANUAL_TEST_PASTE

## Prepared source

- Paste-ready static block: `romer_achilles_route_header_hook_embed.html`
- Route/header map: `romer_route_header_embed_map.csv`
- Machine manifest: `romer_route_hook_manifest.json`
- Audit report: `ROMER_INDUSTRIES_HEADER_EMBED_AUDIT_2026-06-07.md`

## First safe test route

Use one low-risk test or low-risk route first. Preferred:

```text
/operations
```

Reason: it is already an operations index surface and the hook can be reviewed before placing on higher-risk claim pages such as `/aus`, `/emassc`, `/operations/w2`, `/operations/w3`, `/operations/w4`, or `/operations/w7`.

## Manual paste steps

1. Open Squarespace page editor for the selected route.
2. Add a new Code/Embed block above the current page body.
3. Copy all content from `romer_achilles_route_header_hook_embed.html`.
4. Paste into the Code/Embed block.
5. Preview desktop and mobile.
6. Confirm the header renders with route title, badges, claim gate, embed state, next hook, and blocked-action lock line.
7. Do not publish broadly until the Google Sheet source is re-authenticated and compared against `romer_route_header_embed_map.csv`.

## Required visible locks

The rendered block must show or preserve:

```text
No wallet/token/mint/payment/custody/IPFS actions.
No secrets.
No backend writes.
No public-status claim upgrade.
```

## Hold conditions

Stop and return HOLD if:

- the block breaks mobile layout;
- badges do not render;
- the existing page content is hidden or displaced incorrectly;
- Squarespace strips the script/style;
- route title does not match the current page;
- the Google Sheet source remains unavailable and the operator wants sheet-controlled roll-out.

## Next pass after successful paste

1. Re-auth Google Drive connector.
2. Read the sheet tabs from `1wLNW2cC-vQ1ZTzNmgGQiSFE0wGp_dvupCW1ZGBtT_yw`.
3. Reconcile sheet rows against `romer_route_hook_manifest.json`.
4. Roll the header hook to selected page families in this order:
   - `/operations`
   - `/contact-us`
   - `/green-initiative`
   - `/inter-sol`
   - `/emassc`
   - `/aus`
   - `/operations/w2`, `/operations/w3`, `/operations/w4`, `/operations/w7`

