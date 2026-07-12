# Mission 1 Workbook Integration Map

## Purpose

This note records the LightSpeed-facing integration path for the Mission 1 asteroid workbook surfaces. It is documentation only and does not activate runtime systems, deployment paths, launch actions, procurement, autonomous operations, or external publication.

## Workbook

Live workbook:
https://docs.google.com/spreadsheets/d/148UObDgK_YsqHDbIkJo89yDvyDcgySTE4wQMEVGwga8/edit

## Canon workbook inputs for LightSpeed

| LightSpeed Surface | Workbook Input | Primary Use |
|---|---|---|
| LS Web | `Mission 1 Control`, `Mission 1 Flight Windows`, `Mission Planning Toolkit` | Dashboard cards, mission-window summaries, status panels |
| LS Desktop | `Mission 1 Target Library`, `Asteroid Master`, `Index & Log` | Review table, filtering, enrichment queue, source-gate workflow |
| LS Go | `Mission 1 Control`, `Mission 1 Flight Windows` | Compact review status and window cards |
| LS Drive | Canon workbook sheets | Authoritative working state and traceability layer |
| LS Git | `docs/`, `schemas/`, future reviewed exports | Documentation/schema handoff only |
| Cognigrex | `Index & Log`, `Mission 1 Target Library` | Retrieval anchor, missing-field indexing, report queue |
| RSOC planning | `Mission 1 Operations Path`, future Horizons enrichment | Simulation and review packet preparation |

## Mission windows

Current workbook windows:

- June 2027: scout / simulation / pre-clearance review.
- January 2028: primary launch-readiness review.
- August 2028: buffer / secondary review.

These are review windows only. They are not a launch command or commitment.

## Mission 27 continuity

Mission 1 target rows are tagged for future Mission 27 near-Lagrange central hub relevance. The workbook keeps this dependency visible so Mission 1 target selection and operational learning remain reusable for cislunar, lunar, Mars, and Earth supply pathways.

## Next LightSpeed-safe work

1. Surface the `Mission 1 Control` metrics in a Web dashboard mock route.
2. Create a Desktop review table wired to `Mission 1 Target Library` exports after source-gate review.
3. Create a Go compact status view using only reviewed control/window rows.
4. Keep Git changes documentation/schema-only until explicitly authorised for runtime work.
