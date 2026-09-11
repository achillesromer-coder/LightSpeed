# Mark III Multi-Unit Screening Contract

## Authority and purpose

This runner extends the current Mark III owner topology without inventing
missing engineering values. OD-050 controls the three-appendage count and
abstract interlock roles. Exact appendage/interlock geometry, Mark V mating
definition, mass/inertia, mechanism dynamics, propulsion architecture, and
physical test evidence remain external-evidence-gated.

Run:

    python scripts/run_mark3_multi_unit_screening.py input.json receipt.json

Every numeric scenario must explicitly supply:

- one or more uniquely identified Mark III units;
- dry and propellant mass, specific impulse, and conservative bounding radius;
- each traversal leg's supplied delta-v, duration, and active units;
- one static placement per unit;
- any joint moves with appendage ID, angle, torque, and efficiency;
- any interlocks with unique appendage endpoints and an allowed canonical role;
- optional positive delta-v scale factors for a sensitivity sweep.

The runner has no operational default scenario. Missing or invalid fields
return HOLD and exit code 2.

The machine-readable intake shape is
schemas/mark3_multi_unit_screening_input.schema.json.

## Output meaning

The receipt reports rocket-equation propellant bookkeeping, supplied traversal
time/delta-v totals, a lower-bound manipulator work estimate, static
bounding-sphere clearance, and interlock-topology consistency. All outputs are
DERIVED_SCREENING.

screening_pass means only that the supplied bookkeeping case did not exhaust
propellant or overlap the supplied static bounding spheres. It does not
establish a trajectory, optimum, swept-volume clearance, contact stability,
interlock strength, structural safety, Mark V compatibility, mechanism life,
propulsion performance, extraction performance, flight readiness, or target
selection.

## Minimum next evidence

Before a project-specific result can be reviewed beyond screening, bind:

1. exact three-appendage/interlock CAD and revision/hash;
2. Mark V mating ICD and latch/release definition;
3. mass, centre-of-mass, inertia, propellant, tank, thruster and control model;
4. appendage joint axes, limits, rates, torque curves, friction/damping and
   swept-volume envelopes;
5. contact properties, load cases, FMEA and safe-state logic;
6. source-bound body ephemerides and a validated mission-design trajectory;
7. calibrated physical test article, raw evidence, uncertainty and acceptance
   criteria.

Optimization may compare explicitly supplied scenarios, but may not call one
case fuel-optimal or operationally preferred until omitted constraints and
acceptance authority are bound.
