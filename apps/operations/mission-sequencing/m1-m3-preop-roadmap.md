# M1-M3 Pre-Operational Roadmap

## Purpose

This file records the LightSpeed/Cognigrex handoff for the operations workbook's first detailed mission loop.

## Workbook source

- Operations workbook: `Type1_Asteroid_Operating_Workbook`
- Asteroid workbook: `Asteroid_Strategic_Mapping_Base_withRocks`

## Read surfaces

LightSpeed and Cognigrex should read:

- `Asteroid Workbook Interface`
- `Pre-Operational Expansion`
- `Mission 1 Detail`
- `Mission 2 Detail`
- `Mission 3 Detail`
- `Cluster Sequence`
- `Open Build Tasks`
- `Readiness Gates`
- `Publish Review Queue`
- `LS Cognigrex Handoff`

## Write/queue surfaces

Suggested outputs should be written or queued into:

- `Open Build Tasks`
- `Readiness Gates`
- `Cluster Sequence`
- `Publish Review Queue`
- `Appendix & Log`

## First-loop branch logic

M1 is the primary case-study/manual seed and uses 3 m3 planning capacity.
M2 is the follow-on reinforcement/extension branch and uses 4 m3 planning capacity.
M3 is the consolidation and first-loop review/export branch and uses 5 m3 planning capacity.

The current candidate branches include:

- Eros as first source-backed orbit baseline
- Apophis as strategic tag-case branch
- Castalia as top candidate branch
- Toutatis as PHA comparison branch
- Anteros as Amor-class candidate branch
- Apollo/Apl as Apollo-class candidate branch

## Required next automation/runner tasks

1. Capture SBDB payloads for Apophis and top candidate rows where available.
2. Run Jan 2028 Horizons checks first, then June 2027 and August 2028 comparisons.
3. Build neighbour/cluster candidate lists from asteroid workbook rows.
4. Return ranked branch suggestions to `Cluster Sequence`.
5. Return unresolved or missing values to `Open Build Tasks` and `Readiness Gates`.
6. Keep public output in `Publish Review Queue` until reviewed.

## Guardrails

- Do not store secrets in workbook or Git.
- Do not publish externally from runner state alone.
- Do not treat source route URLs as payload evidence.
- Do not infer final target, trajectory, delta-v, window suitability or operational execution from source identity alone.
- Do not duplicate asteroid database logic into the operations workbook.
