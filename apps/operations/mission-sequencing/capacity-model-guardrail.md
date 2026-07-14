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

## Separate source layer

Phase II's 3/5/7-unit batch envelope is retained as a source-backed deployment/configuration reference. It is not the same as the cumulative serial/fleet capacity value.

## LS/Cognigrex use

When ranking clusters, neighbours, or branch sequences, LS and Cognigrex must consume:

- `Active_Capture_Units`
- `Capacity_m3`
- `Tag_Capacity_Asteroids`
- source-backed batch envelope fields

Do not infer capacity from mission number.

## Mark IV note

Attached and retrieved source material in this correction pass evidences Mark III and Mark V repeatedly. Direct capacity-bearing Mark IV evidence was not found. Preserve user/project Mark IV references as source-pending rather than deleting them or using them as capacity inputs.
