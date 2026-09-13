# Type 1 SVG — Canonical Technical Projection Contract

Status: **ACTIVE / EVIDENCE-GATED / REVIEW BRANCH**  
Canonical data authority: **Type 1 Romer Cognigrex → `Type1_SVG_Standard`**  
Date: 2026-09-13

## Purpose

Type 1 SVG is the persistent, source-traceable, object-addressable, print-stable **2D technical projection layer** for a living digital twin. It binds native CAD/mesh, structured twin records, simulations, telemetry, evidence and known-unknowns without replacing their owning authority.

Native CAD/BREP/mesh remains geometry authority. Canonical workbook/database records remain structured-data authority. Calibrated observations/raw receipts remain empirical authority.

## Evidence classes

- **A — SOURCE_AUTHORITY**: direct controlled-source geometry/data.
- **B — SOURCE_DERIVED**: deterministic projection/calculation from authority.
- **C — BOUNDED_ASSUMPTION**: constrained provisional state.
- **D — TARGET**: design objective, not validated.
- **E — INTERACTION_PROXY**: UI/viewer geometry only.
- **U — UNKNOWN**: unresolved and explicitly gated.

Evidence state applies at feature/object level, not only to the whole drawing.

## Required data contract

Every Type 1 SVG package binds stable IDs for Twin, Asset, Drawing, Object and Parent; source model/revision/hash; coordinate frame; SI units; view scale; dimension/datums; material/layer records; interface/network records; sensor/telemetry bindings where applicable; simulation provenance; evidence receipts; unknowns; claim gates; revision and release state.

Object hierarchy is:

`System → Subsystem → Assembly → Subassembly → Component → Part → Feature → Interface`

## Required drawing package

Complex assets use a multi-sheet series rather than compressing information into one drawing:

- `T1-00` — cover / general arrangement
- `T1-01` — geometry / orthographic / sections
- `T1-02` — assembly / exploded / parts
- `T1-03` — interfaces / services / functional networks
- `T1-04` — materials / layer stacks
- `T1-05` — simulation / operating envelope
- `T1-06` — telemetry / instrumentation / living-state bindings
- `T1-07` — evidence / verification / unknowns / claim boundary

## Canonical SVG layer tree

`L00-SHEET`, `L10-CONTEXT`, `L20-AUTH-GEOMETRY`, `L21-DERIVED-GEOMETRY`, `L22-PROVISIONAL-GEOMETRY`, `L30-HIDDEN`, `L31-CENTRE-DATUM`, `L40-SECTIONS`, `L50-DIMENSIONS`, `L60-MATERIALS`, `L70-INTERFACES`, `L75-SENSORS`, `L80-SIMULATION`, `L90-EVIDENCE`, `L91-UNKNOWNS`, `L95-ANNOTATIONS`, `L99-CLAIM-GATE`.

Meaningful SVG elements require stable IDs/data attributes so the drawing remains machine-addressable. Flattened SVG artwork is non-compliant.

## Validation

A Type 1 SVG is validated by source-hash binding, native-geometry/topology comparison, dimensional recomputation, coordinate-frame round trip, object/interface graph checks, simulation reproducibility, telemetry calibration state, evidence/contradiction sweep, stable-ID/schema lint, cross-sheet link integrity, monochrome/print readability and exact export/provider receipt.

## Release score

Weighted completeness:

- geometry authority 20%
- assemblies/components 10%
- dimensions/datums/tolerances 10%
- materials/layers 10%
- interfaces 10%
- simulation/physics 10%
- telemetry/physical binding 10%
- evidence/provenance 10%
- unknowns/claim gates 5%
- drawing/print/machine quality 5%

`TYPE1 COMPLETE` requires **≥95% and no critical-domain failure**. A high aggregate score never overrides missing geometry authority, provenance or a critical unresolved interface.

## Current migration order

1. **WT-001 WatchTower** — F3 / SOURCE_DERIVED_GEOMETRY; source FCStd/BREP and source GLB derivative exist; semantic A/C + discipline evidence remain gated.
2. **M1 Elevated Bypass** — F3 / SOURCE_DERIVED_GEOMETRY; extracted `SEQLD Pilot Builds.FCStd` Stage-0 bodies exist; native-source topology/site/engineering gates remain.
3. **Römer Spaceport** — F2/F3 / SOURCE_DERIVED_PARTIAL; current data contract/facility dimensions exist; complete accepted site/facility geometry remains partial.
4. **Mark III** — F2 with source subobjects; exact current three-appendage/interlock/Mark V mating CAD/ICD remains open.
5. Remaining formal/living twins — retain F1/F2 lineage/proxy state until attributable current whole-object geometry and evidence close their promotion gate.

## Claim boundary

Drawing completeness does **not** by itself prove structural adequacy, manufacturing release, material performance, safety, site approval, regulatory compliance, deployment, commissioning, ecological outcome or mission readiness. Those remain separately evidenced states in the owning canon.
