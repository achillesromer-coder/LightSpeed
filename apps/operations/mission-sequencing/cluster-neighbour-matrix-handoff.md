# Cluster Neighbour Matrix Handoff

## Input surfaces

```text
Asteroid workbook
- Cluster Neighbour Matrix!A1:Y21
- Cluster Source Capture
- Cluster Enrichment Queue

Operations workbook
- Cluster Sequence!A14:AB33

Data repository
- docs/cluster_neighbour_matrix.md
- docs/cluster_neighbour_source_reconciliation_2026-07-14.md
- schemas/cluster_neighbour_matrix_fields.json
- data/jpl/neighbours/sbdb/latest/
- data/jpl/neighbours/horizons/latest/
```

## Canonical source state

The default-branch JPL workflow is complete and authoritative:

```text
Data commit: db1ec4064ffe4b800a897cec251001f8380ede0b
16 / 16 SBDB candidates current
16 / 16 orbit invariants PASS
16 / 16 Horizons objects current
48 / 48 comparison-window rows
0 manifest errors
```

The provisional bootstrap is superseded. Its previously recorded Drive archive identifier is unavailable and must not be used by LightSpeed, Cognigrex, Desktop, Go or Web.

## Cognigrex interpretation

The neighbour matrix is an orbital-element analogue graph. It is not a transfer graph and must not be displayed or consumed as present-day spatial proximity.

Cognigrex should treat each row as a candidate edge with independent evidence states:

- analogue distance;
- physical-source completeness;
- PHA state;
- three-window Earth-relative context;
- interface-allocation readiness;
- unresolved source conflicts.

## Canonical PHA corrections

```text
Vishnu: No  -> Yes
Minos:  No  -> Yes
Lugh:   No  -> Yes
Pan:    No  -> Yes
Ptah:   No  -> Yes
Toro:   Yes -> No
```

These states are already returned to the asteroid and operations workbooks.

## Active candidate holds

```text
Ninkasi: taxonomy A versus JPL Sq
Vishnu: taxonomy Q versus JPL O
Cerberus: taxonomy Q versus JPL S/S
Golevka: diameter 0.34 versus JPL 0.53 km
Toro: diameter 3.6 versus JPL 3.4 km
Pocahontas / Minos: workbook physical values uncorroborated by JPL
```

Cognigrex must preserve these as independent evidence holds and must not infer resolution from orbital distance or range order.

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

## Current operational lane

The neighbour source/window layer is complete. The next LS/Cognigrex lane is conflict-resolution routing and branch-combination analysis while preserving:

- Toutatis anchor physical conflict hold;
- Apollo/Apl anchor physical conflict hold;
- candidate-level taxonomy and diameter holds;
- strategic Apophis tag/support posture;
- Eros baseline/control role;
- no final branch selection from descriptive evidence alone.
