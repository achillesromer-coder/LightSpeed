# Mission 1 Source-Gate LightSpeed Integration

## Purpose

This note maps the new Mission 1 source-gate workbook surfaces into LightSpeed-facing review operations. It is documentation only and does not activate runtime systems, deployments, autonomous operations, procurement, launch actions, or external publication.

## Workbook

Live workbook:
https://docs.google.com/spreadsheets/d/148UObDgK_YsqHDbIkJo89yDvyDcgySTE4wQMEVGwga8/edit

## New workbook surfaces

| Workbook Surface | LightSpeed Use |
|---|---|
| `Mission 1 Source Gate` | Desktop/Web source-route review table with SBDB, Horizons, MPC, and ESA links |
| `Mission 1 Review Pack` | Compact review pack for top-ranked Mission 1 source-gate candidates |
| `Mission 1 Enrichment Queue` | Task source for Cognigrex/RSOC enrichment workflows after review |

## Candidate review flow

1. Review `Mission 1 Review Pack` row.
2. Open SBDB object route.
3. Capture object/orbit/physical/source signature fields into a future reviewed capture surface.
4. Open Horizons January 2028 route after identity confirmation.
5. Record Horizons ELEMENTS output and signature.
6. Compare against workbook values.
7. Only then consider promotion/export into LS data products.

## UI implications

Recommended LS surfaces remain documentation/schema only until explicit runtime authorisation:

- Web: source-gate dashboard cards and review-pack list.
- Desktop: sortable review table and enrichment queue.
- Go: compact window/gate status cards.
- Cognigrex: retrieval and report queue from `Index & Log` plus `Mission 1 Enrichment Queue`.

## Guardrails

- No source payloads are treated as captured until reviewed.
- No launch, delta-v, accessibility, mining, safety, procurement, legal, or operational claim is created by the workbook route links.
- Mission 27 remains a future architecture dependency carried through Mission 1 planning.
