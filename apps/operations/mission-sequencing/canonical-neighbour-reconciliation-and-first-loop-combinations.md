# Canonical Neighbour Reconciliation and First-Loop Combinations

Date: 2026-07-15

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
- Cluster Enrichment Queue
- Task Roadmap

Operations workbook
- Mission 1 Detail
- Mission 2 Detail
- Mission 3 Detail
- Cluster Sequence!A14:AB43   canonical edge and branch-summary layer
- Cluster Sequence!A45:S55    first-loop combination layer
- Cluster Sequence!A57:S67    non-scoring evidence-sensitivity layer
- Cluster Sequence!A69:R79    qualitative perturbation-test results
- Readiness Gates
- LS Cognigrex Handoff
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

Legacy values remain in workbook/Git reconciliation logs. Density and composition gaps remain visible where primary sources do not provide values.

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

The operations workbook contains `ES-001` through `ES-008`, one row for each first-loop arrangement. The sensitivity layer is categorical and non-scoring.

It exposes sensitivity to:

- missing physical and density evidence;
- PHA classification and review burden;
- shared-edge assumptions;
- Apophis strategic-role assumptions;
- M1/M2/M3 interface allocation at 3/7/11 m3;
- cross-mission data continuity;
- failure modes that could distort interpretation.

`HIGH` or `VERY HIGH` means that the comparative interpretation is sensitive to that assumption or evidence gap. It does not mean that the arrangement is better, worse, preferred or more feasible.

## Completed perturbation pass

`ETR-001` through `ETR-008` record the completed qualitative tests:

```text
- shared-edge operational benefit set to zero;
- assumed strategic utility removed from Apophis comparisons;
- unresolved density/composition assumptions stressed;
- branch role order perturbed while evidence remained fixed;
- Earth-relative range ordering removed from interpretation;
- governance/review burden separated from technical evidence depth.
```

Cross-combination results:

1. Removing Earth-relative range order caused no material change in any comparator because range was never permitted as selection logic.
2. Removing shared-edge benefit materially changed FLC-001, FLC-004 and FLC-006, but each retained a narrower data-reuse or directionality comparison function.
3. Removing assumed Apophis strategic utility materially changed FLC-002, FLC-003 and FLC-007. FLC-007 remained useful only as a governance stress comparator.
4. Density/composition uncertainty remained high-impact across all eight arrangements and is the main outstanding technical evidence sensitivity.
5. Separating review burden from technical evidence confirmed that PHA concentration and governance complexity are burdens, not comparative advantages.
6. FLC-008 remained robust as a negative-control comparator after all candidate and anchor physical holds were resolved.
7. No perturbation produced a preferred, feasible or selected sequence.

## Cognigrex stable-freeze state

The workbooks are now stable for deferred Cognigrex continuation under freeze ID:

```text
CGX-FREEZE-001
Freeze date: 2026-07-15
Selection state: none
Operations readiness: stable complete
Scientific evidence state: complete where sourced; remaining gaps explicitly deferred
```

Stable completion means:

- canonical source and window manifests are registered;
- candidate and anchor source conflicts are resolved and logged;
- neighbour, branch, combination, sensitivity and perturbation surfaces are complete;
- M1, M2 and M3 detail pages are structurally complete and selection-deferred;
- dashboard, task registers, readiness gates and review queues are current;
- missing physical evidence is explicit and non-blocking;
- no public release, runtime activation, target selection or autonomous action is implied.

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
- a numeric ranking from categorical sensitivity states or qualitative test outcomes;
- a final preferred branch without an explicit later review decision.

## Approved future restart protocol

A future Cognigrex continuation must:

1. cite `CGX-FREEZE-001`;
2. verify the current Data and LightSpeed commits and canonical manifests;
3. run the workbook assumption-drift and formula-error checks;
4. identify material source, rule or workbook changes since the freeze;
5. rerun only the affected sensitivity and perturbation tests;
6. read canonical surfaces without inheriting a preferred order;
7. return suggestions only to `Open Build Tasks`, `Readiness Gates`, `Cluster Sequence`, `Publish Review Queue`, or `Appendix & Log`;
8. preserve the distinction between evidence, sensitivity, test outcome and recommendation.

## Current canon

```text
Current hardware: Mark III + Mark V only
Mark IV: post-mission successor / next model of Mark III
Apophis: strategic tag/support posture, not mine-first
Apollo shorthand: Apl
M1/M2/M3 interface allocation: 3/7/11 m3
Selection state: none
```

## Deferred, non-blocking work

1. Enrich remaining density, composition, albedo, diameter and taxonomy gaps from primary sources when later analysis needs them.
2. Reopen curated Asteroid Master promotion only under a separate reviewed catalogue objective.
3. Repeat perturbation tests after material evidence or rule changes rather than reusing stale results.
4. Make a separate reviewed decision before any public release or selected-sequence activation.
