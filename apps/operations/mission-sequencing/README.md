# LightSpeed Operations Mission Sequencing

Date: 2026-07-14

## Role

This scaffold records the LightSpeed-facing handoff from the asteroid database workbook into the operations mission sequencing workbook.

## Workbooks

- Asteroid evidence/database workbook: `Asteroid_Strategic_Mapping_Base_withRocks`
  - URL: https://docs.google.com/spreadsheets/d/148UObDgK_YsqHDbIkJo89yDvyDcgySTE4wQMEVGwga8/edit
- Operations workbook: `Type1_Asteroid_Operating_Workbook`
  - URL: https://docs.google.com/spreadsheets/d/1Uy04F5gtf2mXf9tDmAyIvNrsCn1kn4Csa2oc-skSZxY/edit

## Boundary

Asteroid workbook:

- body catalogue
- inner-system body map
- cluster library
- source gate
- source capture
- enrichment queue
- evidence/conflict log

Operations workbook:

- mission sequencing
- capacity model
- start-window comparison
- route/path planning
- cluster sequence
- LS Desktop/Go and Cognigrex handoff

## Initial operational surfaces

- `Operations Control`
- `Mission Architecture Control`
- `Mining Capacity Model`
- `Mission Scenario Matrix`
- `Mission Sequence Planner`
- `Mission Flight Windows`
- `Mission Operations Path`
- `Cluster Sequence`
- `Asteroid Workbook Interface`
- `LS Cognigrex Handoff`

## Capacity rule

Mission 1 begins with 3 m3 planning capacity. Each added unit adds 1 m3. The operations workbook carries M1-M35, with M1-M3 detailed, M4-M16 scaffolded, and M17-M35 roll-up.

## Current baseline

Eros is the first source-backed orbit baseline from SBDB object/orbit capture. Other branch targets remain route-ready or payload-pending until LS/Cognigrex source runners complete capture and comparison.

## Next implementation tasks

1. Build workbook-pull adapters for the operations surfaces.
2. Add source-state ingestion from the asteroid workbook interface.
3. Add non-destructive branch-ranking views for LS Desktop.
4. Add LS Go review states for queued, active, reviewed, approved internal, and published.
5. Keep public/web outputs behind the publish review queue.

No deployment or live runner activation is included in this scaffold.
