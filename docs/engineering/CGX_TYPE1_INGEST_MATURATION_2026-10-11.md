# CGX Type-I Ingest-to-Maturity Operational Contract (UTP-150)

## Purpose

UTP-150 operationalizes UTP-148 evidence maturity/invalidation and UTP-149 2D→3D→4D composition. It is the mutation/orchestration contract for new evidence; it does not replace owner engineering records or create a new master.

Every incoming source, CAD revision, material lot, process record, calibration, measurement, seed revision, solver result, anomaly or owner decision is converted into an attributable evidence envelope, dependency closure, scoped invalidation, recompilation, maturity-axis delta, next-witness decision and DBR/readback receipt.

## Core invariant

Evidence is appended, not silently overwritten.

A changed parent may lower or hold dependent claims. Historical raw evidence remains retained. Contradictions remain explicit until resolved by scope, measurement, source authority or owner review.

## Ingest classes

- source documents and datasheets
- CAD/BREP/mesh/geometry revisions
- material lots, passports and assays
- process recipes, tooling and environment records
- calibration certificates and traceability records
- raw measurements
- seed part, firmware or model revisions
- field-solver and numeric results
- failures, anomalies and contradictions
- historical comparators
- owner decisions and authority events

## Evidence envelope

Each mutation must bind a stable event ID, object/revision, source owner, ingest class, locator/hash, observation time, evidence class, authority ceiling, affected claims, parent references, raw/derived status, validity domain/environment, uncertainty/unknowns and contradiction state.

## Mutation chain

1. capture bytes or observation
2. hash, timestamp and bind source owner
3. resolve stable object and revision
4. classify evidence and authority
5. append immutably
6. calculate affected dependency closure
7. invalidate only dependent derived results
8. recompile UTP-149 2D→3D→4D composition
9. recompile UTP-147 normal form where affected
10. run scoped tests and falsifiers
11. apply UTP-148 maturity-axis delta
12. select next witness or HOLD
13. write DBR/readback receipt
14. queue reviewed promotion or HOLD

## No readiness percentage

The maturity vector remains ten-dimensional:

identity/provenance; source authority; geometry; material; process; model; test/metrology; physical evidence; integration/coupling; authority/release.

The claim ceiling is bounded by the lowest required axis or any hard stop. Digital evidence cannot advance physical evidence beyond BUILD_READY/M6.

## Seed graphs

### SG-0

No imported specialist seed supplies the declared function. Every required mechanism must be supported by local material/process/test evidence. Seed absence is not capability evidence.

### SG-1

One exact seed/revision supplies a bounded mechanism. Printed structure, interconnect, thermal paths, shielding, interfaces and service geometry retain independent evidence ceilings.

### SG-N

Every seed and consequential directed coupling/failure edge is explicit. System maturity is bounded by the weakest required node/edge.

## Numeric inference

Every calculation is routed NUMERIC, SYMBOLIC or HOLD.

NUMERIC requires attributable inputs, a valid model/regime, revision-bound geometry/material/environment and declared uncertainty/validity. Closed-form capacitance is used only for valid attributable topologies; arbitrary 3D/multiconductor structures require a Maxwell capacitance matrix or field solve. Radiative/harvesting claims remain bounded by available source power, losses, coupling/aperture and environment.

## Proof fixtures

- dielectric source/lot change invalidates dielectric-dependent capacitance/field/loss inference while preserving unrelated geometry and prior raw evidence
- seed firmware/revision change invalidates timing/power/thermal/EMC/system-equivalence dependents while preserving unrelated printed mechanical evidence
- calibration expiry invalidates affected acceptance/uncertainty claims while preserving raw observations with superseded-calibration state

## Operational surfaces

Filespace stores source bytes, hashes, object/revision, geometry/process/material/calibration and evidence lineage.

Dataspace stores state transitions, invalidations, numeric/symbolic/HOLD outputs, measurements, uncertainty and receipts.

Printspace stores region/interface/process sequence, seed topology, as-built/configuration and physical witness state.

LS GO should surface the maturity vector, contradiction state/count, invalidated dependents, next witness and evidence ceiling. It must not show a universal readiness percentage.

## Authority boundary

UTP-150 authorizes no physical execution, durable carrier/root mutation, certification, public release, procurement, legal/financial action or high-consequence deployment. Reviewed promotion remains separate.
