# CGX Component Geometry Atlas — Current Technology Baseline

**Date:** 2026-10-08  
**Authority:** Drive-owned engineering/evidence canon; Git is an implementation and validation mirror.  
**Owning workbook:** Type 1 Romer Cognigrex

## Scope

This package establishes a parameterized physical-component atlas beneath the existing PT catalogue. It does not attempt to enumerate every commercial SKU. Each commercial or project-specific part is an **instance** of an archetype and must bind its exact datasheet/package geometry, material/process information, revision, measured state and evidence ceiling.

Drive owner tabs:

- `27_CGX_Component_Geometry_Atlas_v0_1`: 411 parameterized current-technology component archetypes across 15 domains and 22 family labels.
- `28_CGX_4D_Field_Slice_Model_v0_1`: 64 volumetric field/slice/operator records.
- `29_Raphael_Component_Geometry_Search_v0_1`: 61 bounded geometry-search families.
- `30_CGX_Component_Interaction_Map_v0_1`: 75 pair/coupling/parasitic/process/common-cause interaction records.
- `26_CGX_Portfolio_Delivery_v0_1`: UTP-101..104 register the four layers in the existing delivery catalogue.

## Gap-closure population — v0.3

The first-pass 266-archetype primitive library was expanded by 120 archetypes in v0.2 specifically where flat schematics hide important physical structure. v0.3 adds 21 explicit current control/interface archetypes that were previously only implicit combinations of lower-level primitives: CPU/SoC/DSP/ASIC packages, watchdog/supervisor, gate/current-sense/isolation interfaces, CAN/RS-485/USB/Ethernet physical interfaces, motor-control ICs, electromechanical contactor, thermal cutoff, solid-state relay, and BLDC/stepper/servo drive stages. The atlas now carries 411 archetypes while retaining exact commercial SKUs as instances rather than canonical rows.

## UTP universal-function gap closure — v0.4

v0.4 adds four first-class archetypes required by the Printer-μ dependency graph rather than forcing them through neighbouring component classes: machine frame/datum network (CGA-M-029), printable dielectric/insulation layer (CGA-DIEL-001), visible semiconductor LED/RGB emitter package (CGA-O-023), and service bay/removable access interface (CGA-M-030). These close MU-001, MU-006, MU-011 and MU-020 at the archetype-ontology level only. Exact parts, materials, process windows, tolerances and physical qualification remain instance-level evidence.

The dielectric archetype explicitly exposes the geometry-derived ideal relations C≈ε0εrA/d and E≈V/d only when εr, area and thickness are source-bound. These are engineering estimates, not substitutes for measured capacitance, leakage, loss tangent, breakdown, edge/fringing effects or process defects.

### v0.3 coverage rule

A commercial part or assembly is considered covered only when it can bind to an atlas archetype with exact geometry/material/rating/interface data, or when a new archetype is added. Composite functions may map to multiple archetypes, but common current assemblies such as receivers, transponders, compute packages and motor drives are kept explicit when their packaging, coupling or safety geometry materially affects the 4D twin.

A specific component instance is represented as:

`archetype + dimensions + materials + ratings + interfaces + process route + calibration/evidence + revision`.

This keeps the atlas finite and reusable while preserving enough geometric/material information to instantiate an exact commercial part, printed coupon, hybrid module or mission build without creating one canonical row per manufacturer SKU.

The 4D layer also closes spatial-netlist, interface/contact, return-current-loop, energy-conservation, control-state, tribology, EMC, process-exposure-history, aging and evidence-lineage fields. This is the minimum set needed to turn a logical schematic into a build-order-aware volumetric twin rather than merely extruding a 2D board layout.

## Engineering model

A conventional schematic is retained as the network/function view, but every component instance can now resolve to:

`identity + geometry + materials + ports + process + fields + environment + evidence + uncertainty + history`.

The volumetric twin is **x-y-z plus time**. Frequency, modal and phase/coherence maps are derived views of time-varying state, not additional physical dimensions. Longitudinal, transverse, arbitrary-plane, cylindrical and interface-normal slices support the requested MRI-like inspection model.

## Raphael boundary

Raphael does not replace Maxwell, semiconductor carrier transport, continuum mechanics, thermodynamics, fluid mechanics, heat transfer, electrochemistry, acoustics or optical models. The search sequence is:

`conventional baseline → bounded geometry candidates → standard physics solver → Raphael comparison/residual analysis → hard gates/Pareto → coupon/device/system test → DBR`.

A candidate is not an improvement until it is compared against the same-material/same-environment baseline on declared metrics and survives uncertainty, manufacturability and empirical validation.

## Current manufacturing boundary

The atlas distinguishes direct-printable, printable-with-inserts, hybrid and seed-only components. Conductors, passive geometries, antennas, coils, channels, housings, heaters, many sensors and transmission structures may be printable or hybrid depending on process resolution/material qualification. Advanced silicon, MEMS, quartz/SAW/BAW resonators, precision semiconductor optoelectronics and certified high-consequence protection remain explicit seed components unless their local process chain is independently qualified.

## Ambient-energy boundary

Ambient RF / electromagnetic harvesting and Solar-Hull/New-Neutral collector geometry are represented as measured-energy problems:

`measured incident spectrum/flux → collector effective aperture/coupling → impedance match → rectifier/converter → storage → load duty cycle`.

Energy conservation, actual site spectra, conversion/standby/storage loss and component thresholds remain hard gates. No free-energy assumption is encoded.

## Human / natural-frequency boundary

Mechanical, acoustic, RF/EM, thermal and chemical interactions with occupants or environments are mapped where they are measurable. Geometry may be optimized for defined exposure, noise, vibration, heat, sensing or electromagnetic compatibility targets. The atlas does not infer biological benefit or health effects from frequency coincidence or “resonance” without a separate empirical protocol.

## Convergence path

1. Instantiate exact current parts/builds against CGA archetypes.
2. Register geometry/material/ports in the MRI4D twin.
3. Extract intentional and parasitic couplings through CIM.
4. Run conventional baseline physics.
5. Apply bounded Raphael geometry search.
6. Reject non-manufacturable candidates using calibrated printer/tool capability.
7. Coupon/device test surviving candidates.
8. Promote only through DBR/readback and existing evidence gates.
9. Use validated overlaps to propose frontier functions while keeping them hypothesis-labeled until tested.

The result is the bridge from a flat schematic to a geometry-aware, material-aware, time/frequency-aware integrated printable system without conflating architecture with physical proof.
