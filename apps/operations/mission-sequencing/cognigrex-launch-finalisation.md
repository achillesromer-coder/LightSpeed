# Cognigrex Launch Finalisation Handoff

Date: 2026-07-14
Surface: LightSpeed operations / mission sequencing
Mode: internal launch-control ready, public output gated

## Role

This file is the LightSpeed-facing companion to the Drive/Git launch finalisation packet in `achillesromer-coder/Data`.

LightSpeed should treat Drive workbooks as durable source/backend surfaces and Git as operational RAM for schemas, scaffolds, docs, and guardrails.

## Canonical Inputs

- Operations workbook: `Type1_Asteroid_Operating_Workbook`
  - https://docs.google.com/spreadsheets/d/1Uy04F5gtf2mXf9tDmAyIvNrsCn1kn4Csa2oc-skSZxY/edit
- Asteroid workbook: `Asteroid_Strategic_Mapping_Base_withRocks`
  - https://docs.google.com/spreadsheets/d/148UObDgK_YsqHDbIkJo89yDvyDcgySTE4wQMEVGwga8/edit
- Data launch packet: `docs/cognigrex_launch_drive_git_finalisation_2026-07-14.md`

## LS Surface Behaviour

| Surface | Launch role | Write boundary |
|---|---|---|
| LS Desktop / Neo | Local analysis, source-runner prep, queue review, branch refinement | Writes only to reviewed local DB/workbook queue rows. |
| LS GO | Review/control surface for queues, status, approvals | No private sync or command execution without approval gate. |
| LS Web / Athene | Presentation of reviewed internal/public outputs | No public publication from workbook state alone. |
| Cognigrex | Reads canonical workbooks and returns ranked suggestions, blockers, and proof deltas | Outputs return to Open Build Tasks, Readiness Gates, Cluster Sequence, Publish Review Queue, and Appendix & Log. |
| Git / Smith | Docs, schemas, scaffolds, route memory | No secrets, no unsupported public claims, no deletion-by-default. |

## Current Canon

Capacity is active-unit based:

```text
capacity_m3 = active_capture_units * 1 m3
M1 = 3 m3
M2 = 7 m3
M3 = 11 m3
```

Current hardware is Mark III + Mark V only. Mark IV is post-mission successor / next model of Mark III and is not a current capacity input. Luke IV is facility/logistics/terrestrial receiver layer.

## Launch Gates For LS/Cognigrex

LS/Cognigrex may proceed with internal queue execution for:

1. Apophis and top-candidate source payload capture.
2. Jan 2028 window check preparation, then June 2027 and August 2028 comparisons.
3. M1-M3 detail completion under corrected capacity canon.
4. Non-destructive handoff protocol closure.
5. Internal publish/export queue preparation.

LS/Cognigrex must not proceed with:

- public publish,
- destructive deletes,
- final target selection,
- trajectory/delta-v/window suitability claims,
- extraction/yield/reserve/revenue claims,
- safety or standards-compliance claims,
- secret storage in workbook or Git.

## Required Return Surfaces

Cognigrex outputs should return to these workbook surfaces rather than creating sidecar sprawl:

- `Open Build Tasks`
- `Readiness Gates`
- `Cluster Sequence`
- `Mission 1 Detail`
- `Mission 2 Detail`
- `Mission 3 Detail`
- `Publish Review Queue`
- `Appendix & Log`
- `Cluster Source Capture` in the asteroid workbook for source payload state

## Launch Status

Drive/Git/LS are aligned for internal Cognigrex launch-control operation. Public/web/export/delete lanes remain gate-controlled until the exact proof packet is complete.
