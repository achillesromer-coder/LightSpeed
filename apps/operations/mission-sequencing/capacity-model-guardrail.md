# Capacity Model Guardrail

## Corrected operating rule

Mission capacity must be calculated from active Mark III / capture-capable units, not the mission number.

```text
capacity_m3 = active_capture_units * 1 m3
```

Mission 1 currently carries a 3 m3 active capture cap. Later mission rows increase by active unit count, not by a single m3 per mission.

## Current first-loop values

```text
M1 = 3 m3
M2 = 7 m3
M3 = 11 m3
```

## Current expansion values

```text
M4 = 15 m3
M5 = 19 m3
M16 = 63 m3
```

## Current hardware canon

Current / to-date mission hardware:

```text
Mark III + Mark V only
```

Mark IV:

```text
post-mission successor / next model of Mark III
not current hardware
not current capacity input
```

Luke IV:

```text
facility / logistics / terrestrial receiver layer
not a Mark-series extraction/capture unit
```

## Separate source layer

Phase II's 3/5/7-unit batch envelope is retained as a source-backed deployment/configuration reference. It is not the same as the cumulative serial/fleet capacity value.

## LS/Cognigrex use

When ranking clusters, neighbours, or branch sequences, LS and Cognigrex must consume:

- `Active_Capture_Units`
- `Capacity_m3`
- `Tag_Capacity_Asteroids`
- source-backed batch envelope fields
- current hardware canon: Mark III + Mark V only

Do not infer capacity from mission number.

## Drift guards

- Do not use Mark IV in branch ranking before a post-mission successor-model surface is intentionally opened.
- Do not conflate Luke IV with Mark IV.
- Do not promote historical/OCR Mark I-IV fragments as current canon without reconciliation.
- Do not write planned/post-mission/future states as current.

## Continuation lane

Run M1-M3 branch and cluster ranking from the corrected model, then continue source/Horizons payload expansion.
