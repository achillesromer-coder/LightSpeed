# Asteroid Cluster Sequence — Source Capture Status

## Source workbook

`Asteroid_Strategic_Mapping_Base_withRocks`

https://docs.google.com/spreadsheets/d/148UObDgK_YsqHDbIkJo89yDvyDcgySTE4wQMEVGwga8/edit

## Current operational role

This operations scaffold reads the asteroid workbook as the canonical asteroid-side source. Git is used as routing, schema and implementation memory; Drive remains the durable workbook and portfolio layer.

## Batch status — 2026-07-14

Completed:

- `Mission 1 Source Capture` rows 4–27 converted to static operating rows.
- `Eros` source snapshot captured from the JPL SBDB API where the chat browser could safely access the official example route.
- `Eros` marked as the first source-backed orbit baseline in `Cluster Sequence Optimiser`.
- `Appendix & Log` event `M1SRC-EROS-001` added.

## Eros source-backed baseline

Source URL: `https://ssd-api.jpl.nasa.gov/sbdb.api?sstr=Eros`

Captured object/orbit values include:

- `433 Eros (A898 PA)`
- SPK ID `20000433`
- NEO true
- PHA false
- Orbit class Amor
- e `0.223`
- a `1.46 au`
- q `1.13 au`
- i `10.8 deg`
- Q `1.78 au`
- MOID `0.149 au`

## Runner requirements

The LS/Cognigrex source runner should:

1. Execute arbitrary SBDB object API routes from `Mission 1 Source Capture`.
2. Capture signature/version before parsing payloads.
3. Write payload status back to workbook ranges or a reviewed import surface.
4. Log conflicts into `Appendix & Log`.
5. Avoid promoting physical proxy fields until physical payload sections are captured and reviewed.
6. Run Horizons ELEMENTS checks only after identity/orbit source capture.

## No inference rule

Do not infer trajectory, launch-window suitability, delta-v, operational reach, mining feasibility or cluster sequence viability from object/orbit capture alone. Those states require Horizons, mission-design and operations-workbook analysis.
