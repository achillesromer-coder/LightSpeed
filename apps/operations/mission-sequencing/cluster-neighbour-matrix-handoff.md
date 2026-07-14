# Cluster Neighbour Matrix Handoff

## Input surfaces

```text
Asteroid workbook
- Cluster Neighbour Matrix!A1:Y21
- Cluster Source Capture
- Cluster Enrichment Queue

Data repository
- docs/cluster_neighbour_matrix.md
- schemas/cluster_neighbour_matrix_fields.json
- data/jpl/neighbours/sbdb/latest/
- data/jpl/neighbours/horizons/latest/
```

## Cognigrex interpretation

The neighbour matrix is an orbital-element analogue graph. It is not a transfer graph and must not be displayed or consumed as present-day spatial proximity.

Cognigrex should treat each row as a candidate edge with independent evidence states:

- analogue distance;
- physical-source completeness;
- PHA state;
- three-window Earth-relative context;
- interface-allocation readiness;
- unresolved source conflicts.

## Capacity consumption

Current first-loop capacity:

```text
M1 = 3 m³
M2 = 7 m³
M3 = 11 m³
```

These values describe active Mark III/capture-capable interface allocation. They are not asteroid whole-body size limits.

## Current hardware canon

```text
Current/to-date: Mark III + Mark V only
Mark IV: post-mission successor / next model of Mark III
```

## Selection guardrail

No branch should be selected from analogue distance or Earth-relative range ordering alone. Sequence comparison requires:

1. source and conflict state;
2. three-window context;
3. candidate neighbour set;
4. 3/7/11 m³ allocation context;
5. branch role and PHA posture;
6. explicit review state.

## Shared graph edges

Likho and Ninkasi appear under both Eros and Anteros. LS should preserve these as shared candidate edges rather than deduplicating one anchor relationship.
