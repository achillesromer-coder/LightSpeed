# Canonical Neighbour Reconciliation and First-Loop Combinations

Date: 2026-07-14

## Canonical inputs

```text
Data main
- data/jpl/neighbours/sbdb/latest/manifest.json
- data/jpl/neighbours/sbdb/latest/summary.csv
- data/jpl/neighbours/horizons/latest/manifest.json
- data/jpl/neighbours/horizons/latest/summary.csv
- docs/jpl_neighbour_canonical_reconciliation.md

Asteroid workbook
- Cluster Neighbour Matrix!A1:Y21
- Cluster Review Pack
- Cluster Source Capture

Operations workbook
- Cluster Sequence!A14:AB43   canonical edge and branch-summary layer
- Cluster Sequence!A45:S55    first-loop combination layer
- Cluster Sequence!A57:S67    non-scoring evidence-sensitivity layer
```

## Reconciliation state

Canonical neighbour capture is complete:

```text
16 / 16 source objects current
16 / 16 orbit-invariant checks pass
48 / 48 month-window summaries complete
459 daily samples per candidate
Manifest errors = 0
```

Classification corrections propagated:

```text
Vishnu, Minos, Lugh, Pan, Ptah -> PHA
Toro -> non-PHA
```

SBDB-first candidate resolutions:

```text
Ninkasi taxonomy: legacy A -> Sq (Bus)
Vishnu taxonomy: legacy Q -> O (Bus)
Cerberus taxonomy: legacy Q -> S (Bus/Tholen)
Golevka diameter: legacy 0.34 km -> 0.53 km
Toro diameter: legacy 3.6 km -> 3.4 km
```

SBDB-first anchor resolutions:

```text
Toutatis: 5.4 km, albedo 0.405, Sk (Bus)
Apollo/Apl: 1.5 km, albedo 0.25, Q (Bus/Tholen)
```

Legacy values remain in workbook/Git reconciliation logs. Density gaps remain visible where JPL does not supply a value.

## First-loop comparison set

Eight arrangements are available in the operations workbook:

```text
FLC-001 control/shared-edge/expansion
FLC-002 strategic-support/expansion/non-PHA context
FLC-003 control/strategic-support/expansion
FLC-004 shared-edge/control/expansion
FLC-005 control/expansion/high-PHA comparison
FLC-006 control/shared-edge/mixed-PHA comparison
FLC-007 strategic/high-PHA governance stress comparison
FLC-008 high-PHA negative-control comparator
```

These are branch arrangements, not trajectories or recommendations.

## Evidence-sensitivity layer

The operations workbook also contains `ES-001` through `ES-008`, one row for each first-loop arrangement. The sensitivity layer is categorical and non-scoring.

It exposes sensitivity to:

- missing physical and density evidence;
- PHA classification and review burden;
- shared-edge assumptions;
- Apophis strategic-role assumptions;
- M1/M2/M3 interface allocation at 3/7/11 m3;
- cross-mission data continuity;
- failure modes that could distort interpretation.

`HIGH` or `VERY HIGH` means that the comparative interpretation is sensitive to that assumption or evidence gap. It does not mean that the arrangement is better, worse, preferred or more feasible.

Required evidence tests include:

```text
- set shared-edge operational benefit to zero;
- remove assumed strategic utility from Apophis comparisons;
- vary unresolved density/composition assumptions;
- hold evidence constant while changing role order;
- remove Earth-relative range ordering from comparative interpretation;
- separate governance/review burden from technical evidence depth.
```

## Cognigrex consumption rules

Cognigrex may compare:

- source completeness;
- physical evidence gaps;
- PHA concentration;
- shared graph edges;
- branch role;
- M1/M2/M3 interface allocation at 3/7/11 m3;
- review burden;
- sensitivity to unresolved density/composition fields;
- stability of an arrangement when the listed evidence tests are applied.

Cognigrex must not infer:

- present spatial proximity from orbital analogue distance;
- transfer cost or route continuity from shared edges;
- launch suitability from Earth-relative range;
- mining feasibility from candidate diameter;
- whole-body fit from 3/7/11 m3 interface allocation;
- a numeric ranking from categorical sensitivity states;
- a final preferred branch without an explicit later review decision.

## Current canon

```text
Current hardware: Mark III + Mark V only
Mark IV: post-mission successor / next model of Mark III
Apophis: strategic tag/support posture, not mine-first
Apollo shorthand: Apl
Selection state: none
```

## Next computation lane

1. Enrich remaining candidate density, albedo, diameter and taxonomy gaps from primary sources.
2. Run the specified evidence tests against ES-001 to ES-008 and record interpretation changes without producing a final rank.
3. Prepare reviewed internal exports that distinguish evidence posture, sensitivity and recommendation.
4. Do not publish or activate a selected sequence without explicit release authority.
