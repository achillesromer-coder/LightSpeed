# CGX Type-I Evidence Maturity Graph — UTP-148

## Purpose

This artifact joins the existing **411 × 60 Type-I archetype matrix**, component-instance binding states, equation and volumetric kernels, directional stack compiler, seed topologies, and P0–P10 physical proof ladder into one deterministic maturation model.

It is deliberately **not** a readiness score. A component, stack, Printer-family member, or infrastructure object matures as a vector of independently proven dimensions. A high digital state cannot compensate for missing physical evidence, safety authority, an unbound material lot, or an unresolved interface.

## Core state machine

The existing instance contract already defines the authoritative sequence:

`UNBOUND → SOURCE_BOUND → GEOMETRY_BOUND → MATERIAL_BOUND → PROCESS_BOUND → TEST_DEFINED → BUILD_READY → BUILT → MEASURED → REVIEWED_PROMOTION`.

UTP-148 maps those states to M0–M9 for projection and analysis only. It does not replace the source contract.

The maturity vector is:

`M = [identity, source, geometry, material, process, model, test/metrology, physical, integration/coupling, authority]`.

For a requested claim, CGX resolves the axes and coupling edges required by that claim and applies the **lowest supported ceiling**. No averaging is permitted.

## Ingestion and maturation

Every new file, CAD revision, datasheet, material certificate, process record, measurement, calibration record, field solve, image, or operator decision enters through:

1. intake;
2. hash + timestamp + source owner;
3. object/revision resolution;
4. evidence/authority classification;
5. append/bind without silent overwrite;
6. affected dependency-subgraph calculation;
7. stale-derived-result invalidation;
8. directional-stack and 4D recompilation;
9. scoped tests/falsifiers;
10. maturity-vector update only for proven axes;
11. next witness selection;
12. DBR/readback receipt;
13. review or hold.

This gives CGX a concrete way to “ingest and mature”: new evidence can improve a model, but changed evidence can also **lower or invalidate** derived state.

## 2D → 3D → 4D

A schematic is a graph of intended connectivity and function. The manufacturing compiler maps that graph into 3D regions, interfaces, field paths, cavities, seeds, thermal routes, fluidic paths, service boundaries and metrology references.

The runtime state then evolves as:

`X_v(t) = {geometry, material_state, environment, electrical, thermal, mechanical, magnetic, optical, fluidic, chemical/electrochemical, logic, calibration, health, uncertainty, history}`.

Frequency, phase, modes and field slices are derived views. Unsupported couplings remain HOLD.

## Seed graphs

- **SG-0:** seedless function. Every required active/passive mechanism must be locally qualified.
- **SG-1:** one specialist seed island. Printed surroundings remain separately qualified.
- **SG-N:** multiple seeds. Every consequential coupling edge is explicit and the system ceiling is bounded by the weakest required node/edge.

This supports functionally dense structures without pretending that printed geometry locally fabricates advanced silicon, certified protection, precision optics or electrochemical chemistry where those process chains are not qualified.

## Radiative and field understanding

The maturity graph distinguishes electrostatic, magnetostatic, lumped RLC, distributed transmission-line, reactive near-field, radiative far-field, conduction, convection, thermal radiation, acoustic/elastic, optical and full-wave regimes.

Closed-form equations are used only where topology and assumptions are attributable. Arbitrary 3D electrostatics uses a Maxwell capacitance matrix / field solve; arbitrary magnetic or RF structures use the appropriate field/network model. Geometry can redistribute, store, couple or dissipate available energy but cannot create an absent source.

## Invalidation is first-class

A geometry revision invalidates topology-specific field matrices and as-built equivalence. A material-lot change invalidates lot-dependent process and witness equivalence. A process/tool/environment change can invalidate prior-layer preservation and build readiness. Calibration expiry affects the measurements that depended on it. A seed or firmware revision reopens system-level timing, power, thermal and EMC evidence.

The old evidence is retained as lineage; it is never silently overwritten.

## Type-I composition

Maturation composes from functional voxel → component → subassembly → machine/process cell → facility/microfactory → infrastructure node → regional/distributed capability.

The rule is not “most components passed.” Every critical node, coupling edge, safe-state path and resource dependency must meet the maturity floor of the declared service. Degraded operation is valid only when the reduced safe function is explicit and tested.

## Immediate engineering effect

UTP-148 converts the current corpus from a large engineering catalogue into a **living evidence graph** that can accept future measured evidence without confusing source facts, inference, simulation, render quality, physical tests, certification or release authority.

The next physical evidence remains P0–P3: identity/provenance, conductor/interconnect, separate R/C/L witnesses, then resonator/loop behavior derived only from measured P2 values.
