# CGX Type-I 2D→3D→4D Composition Matrix

**Artifacts:** UTP-149 / BUILD-082  
**Parent contracts:** UTP-124, UTP-136, UTP-137, UTP-146, UTP-147, UTP-148  
**State:** digital engineering composition; physical execution not run.

## 1. Purpose

UTP-149 is the derived composition view over the existing Type-I technology ontology. It does not replace the 411×60 archetype matrix, exact component-instance records, equation or volumetric kernels, radiative/transport owner, stack normal form, maturity graph, or physical proof ladder.

Its job is to answer one engineering question consistently:

> Given a desired 2D functional intent, what 3D material/geometry/interface/seed regions must exist, how may they be manufactured in directional sequence, which field/transport model applies, which states evolve in time, and what evidence is still required before the result may be used?

## 2. 2D, 3D and 4D are distinct contracts

**2D intent** is a schematic or net-level statement such as conductor, capacitor, heat path, sensor, actuator, optical path, safety interlock or logic block. A symbol does not specify dimensions, interfaces, process compatibility, ratings or manufacturability.

**3D realization** is a directed region/interface graph. Regions may be non-planar solids, films, traces, vias, cavities, dielectric layers, shields, thermal paths, fluid channels, optical structures, barriers, service volumes and seed packages. Interfaces and interlayers are first-class because X→Y is not equivalent to Y→X.

**4D state** is the time/history evolution of that 3D article: electrical, thermal, mechanical, magnetic, optical, fluidic, chemical/electrochemical, logic, calibration, health and uncertainty state. Frequency, phase and modal views are derived representations of the same evolving object rather than additional spatial dimensions.

## 3. Seed cardinality

UTP-149 uses three seed graphs.

- **SG-0 — seedless:** no imported specialist component supplies the declared function. Every active/passive mechanism must therefore be supported by locally qualified material, process and witness evidence.
- **SG-1 — single seed:** one exact specialist component supplies a bounded mechanism. Printed structure, interconnect, thermal management, sensing, service or protection surrounding it retains its own evidence ceiling.
- **SG-N — multi seed:** multiple seeds are connected by explicit directed coupling edges. Electrical, thermal, optical, RF, fluidic, timing, mechanical and failure-propagation edges are not collapsed into a single readiness claim.

A seed can contribute capability; it cannot transfer its certification or source rating to untested printed surroundings.

## 4. Universal primitive basis

The matrix covers the same 20 primitive basis classes used by the Type-I stack compiler:

1. structure/datum
2. conductor/interconnect
3. dielectric/isolation
4. resistive/heater
5. capacitive/electrostatic
6. inductive/magnetic
7. RF/wave
8. energy storage
9. optical/photonic
10. sensor/metrology
11. actuator/motion
12. fluidic/environment
13. thermal control
14. active logic seed
15. power conversion
16. safe-state/protection
17. barrier/hermetic/compliance
18. service/access
19. identity/state/DBR
20. chemical/electrochemical

Each primitive carries a bounded 2D intent, candidate 3D region families, 4D state variables, SG-0/1/N routes, engineering model route, verification route and explicit fail-closed conditions.

## 5. Capacitance is topology-selected, not one equation

Capacitance is a useful example of the matrix discipline because the same schematic capacitor symbol can map to radically different internal geometry.

- Uniform parallel plate: **C ≈ ε0 εr A / d** only when the field/material assumptions are valid.
- Layered dielectrics along the field direction: **C/A ≈ ε0 / Σ(di/εri)**, with each layer and interface state bound.
- Long concentric cylindrical pair: **C' ≈ 2π ε / ln(b/a)** when the coaxial approximation is valid.
- Concentric spherical pair: **C ≈ 4π εab/(b-a)** for that exact boundary condition.
- Arbitrary multi-conductor 3D geometry: use a **Maxwell capacitance matrix**, **Q = C_M V**, from an attributable field solve or measurement.
- Distributed/high-frequency structures: capacitance becomes part of the per-unit-length **R'L'G'C'** description or a full-wave solve.
- Moving geometry or nonlinear/stateful dielectric: use **C = C(x,state,t)** only inside a validated constitutive/state model.

No capacitance calculation grants a voltage, breakdown, lifetime or safety rating.

## 6. Compile and ingest chain

The deterministic composition path is:

1. receive 2D intent;
2. resolve archetype, exact instance where known, and primitive kernel;
3. expand to a 3D region/interface graph;
4. bind reference nodes and local coordinate frames;
5. assign SG-0, SG-1 or SG-N;
6. order the directional process DAG;
7. resolve interlayers, atmospheres and prior-layer damage/preservation;
8. select the valid field/transport regime;
9. bind equation, volumetric and mutual-coupling models;
10. infer numeric values only from attributable inputs, otherwise retain symbolic or HOLD;
11. compile 4D state/history and safe-state behavior;
12. route evidence through UTP-148 maturity/invalidation;
13. select the next physical witness;
14. freeze the normal-form hash, DBR/readback and review state.

The deterministic helper `scripts/project_type1_4d_composition.py` performs only the bounded projection step. It neither executes a printer nor invents missing physical properties.

## 7. Evidence maturation

UTP-148 remains the evidence owner. UTP-149 is therefore invalidation-aware.

A consequential change to source, geometry, material, process, calibration, seed revision or environment must invalidate only the dependent derived state, then recompile the affected subgraph. Historical/raw evidence is preserved.

The evaluator now fails closed on:
- unknown changed-node IDs;
- dangling dependency references;
- duplicate maturity-node IDs;
- empty mutation sets.

This prevents an unregistered change from producing an empty dependency closure and being accidentally accepted.

## 8. Field and transport regime selection

The composition layer distinguishes electrostatic, magnetostatic, lumped RLC, distributed transmission-line, reactive near-field, radiative far-field, optical, thermal conduction/convection/radiation, acoustic/elastic, fluid, species, ionic/electrochemical and inertial/contact regimes.

No universal radiation equation is assumed. Geometry may guide, couple, store or dissipate energy through an existing mechanism; cavities and voids are not energy sources.

## 9. Printer-family interpretation

A Printer-family machine does not need every function to be produced by one toolhead or one deposition event. The universal claim is instead a qualified process grammar plus interoperable tool/environment stages capable of producing the required region/interface graph.

A child Printer-μ becomes meaningfully recursive only when:
- its required functional basis has physical witnesses;
- its C0 deterministic safety/motion path is independently verified;
- exact parent-made/seed-dependent fractions are measured;
- its metrology is cross-calibrated;
- identity/DBR handshakes pass without authority transfer.

Recursive manufacturing never means unlimited self-replication.

## 10. Physical proof order

UTP-149 does not change the physical owner. The first useful witnesses remain:

- **P0:** passive identity/provenance;
- **P1:** conductor/interconnect;
- **P2:** separate R, C and L witnesses;
- **P3:** resonator/field geometry using measured P2 values.

Dense P10 integration may only combine children and interfaces that remain within their own evidenced envelopes.

## 11. Immediate maturation targets

1. Bind actual P0-P2 lots, tools, process revisions and calibration records.
2. Project UTP-149 into the existing LS GO Objects/review lens rather than creating another runtime.
3. Reconcile source-unique UTP-146/147 deltas from PR155 against current main.
4. Generate one bounded SG-0, SG-1 and SG-N stack packet and compare blockers/readiness deterministically.
5. Feed every measured witness back through UTP-148 before a denser article reuses dependent inference.

## 12. Non-claims

This architecture is not physical readiness, certification, a universal-material compatibility claim, a universal solver, a free-energy model, permission to infer semiconductor or battery mechanisms from geometry, or authority for hazardous/high-consequence execution.
