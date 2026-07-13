# Mission Scenario Matrix LS Handoff

## Workbook

Live workbook:
https://docs.google.com/spreadsheets/d/148UObDgK_YsqHDbIkJo89yDvyDcgySTE4wQMEVGwga8/edit

## LS-facing workbook surfaces

| Surface | Workbook Input | LS Use |
|---|---|---|
| LS Web | `Mission 1 Scenario Matrix`, `Mission 1 Control`, `Publish Review Queue` | Scenario dashboard, branch cards, publish-state panels |
| LS Desktop | `Mission 1 Source Capture`, `Mission Sequence Planner`, `Appendix & Log` | Source capture table, conflict review, branch planning workspace |
| LS Go | `Mission 1 Control`, `Mission 1 Scenario Matrix` | Compact status and branch comparison summaries |
| LS Git | `docs/`, future schemas, reviewed exports | Versioned handoff and file-review queue |
| Cognigrex | `Mission 1 Source Capture`, `Appendix & Log`, `Mission Sequence Planner` | Automated source pulls, field comparison, branch analysis tasks |

## Operational interpretation

The workbook now treats June 2027, January 2028, and August 2028 as comparative start-state branches. Each branch carries its own M1, M2, and M3 follow-on planning path. The shorthand pattern is:

- `1.6.27.<target>`
- `2.6.27.<target>`
- `3.6.27.<target>`

and equivalently for January and August branches.

## Source capture integration

`Mission 1 Source Capture` is the next LS/Cognigrex data handoff surface. It provides:

- Capture IDs.
- Object IDs and names.
- Source route URLs.
- 30-minute capture-window notes.
- Payload status.
- Conflicting values column.
- Workbook and candidate ranges.
- Cognigrex action column.
- Publish queue link.

## Publish queue integration

`Publish Review Queue` is the handoff surface for Drive/Git/LS artefact generation. It is intended to support reviewed exports, schema generation, front/back document production, and LS surface planning.

## Current safe boundary

This note is an LS planning and data-surface handoff. It does not create external physical actions. Source-payload capture and branch comparisons remain data operations routed through workbook and Git surfaces.
