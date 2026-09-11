# ACHILLES Digital Asset Contract — 2026-09-12

Status: **review / prepublish / evidence-gated**

## Definition of a complete digital asset

A Römer / ACHILLES digital asset is not only a mesh. The minimum complete bundle is:

1. **Native geometry authority** — FCStd / STEP / BREP / source mesh where positively recovered.
2. **Viewer geometry** — OBJ now; GLB/GLTF target for web delivery; proxy geometry is separately classed.
3. **Object / assembly identity** — stable asset, assembly, component, interface and service IDs.
4. **Parametric state** — dimensions, equations, tolerances, scenario ranges and known/unknown classification.
5. **Materials / surface slots** — materials, coatings, textures and layer stack references, with evidence status.
6. **Simulation bindings** — structural, thermal, electrical, field, acoustic, traffic, hydrodynamic or ecological models as applicable.
7. **Telemetry / evidence bindings** — sensor/config IDs, raw-data URI/hash, calibration, uncertainty, environmental state and review.
8. **Coordinate frame + units** — SI/metric master, origin/axes/handedness and transforms declared.
9. **Lifecycle state** — design, simulation, test, qualification, fabrication, commissioning, operations, maintenance and upgrade states.
10. **Claim / release gate** — explicit ceiling preventing digital state being confused with physical validation, certification or approval.

## Representation classes

- `SOURCE_NATIVE_MESH` — provider-native mesh bytes embedded unchanged with source/hash provenance.
- `SOURCE_DERIVED_GEOMETRY` — geometry reproduced from source-locked CAD/BREP-derived dimensions or object bounds.
- `SOURCE_DERIVED_PARTIAL` — some dimensions/forms are source-derived but the digital object is not a complete engineering solid.
- `INTERACTION_PROXY` — manipulable 3D object for chat/viewer interaction only; never manufacturing/engineering authority.
- `SOURCE_LINK_ONLY` — native source exists or is referenced but has not been copied into the current package.

## Current embedded geometry

The Atrium review bundle contains one OBJ viewer asset and one asset metadata object per showcased twin. Two currently have stronger source authority:

- **WatchTower** — source-locked BREP-derived bounding/object geometry from `107_WATCHTOWER_FCSTD_EXTRACT_v0_1`; source SHA-256 `c476f9f2f9946ab8e99e58dd399aa7b02bac630c5d9336b80ef66f5f2a397321`.
- **M1 Elevated Bypass** — source-extracted Stage-0 FreeCAD massing from `SEQLD Pilot Builds.FCStd`, including 1 km road bodies, 23.5 m directional road widths and current underlay/barrier host massing. Structural depth remains open.

The Römer Spaceport asset is `SOURCE_DERIVED_PARTIAL` from the current application-twin data contract. All remaining current objects are `INTERACTION_PROXY` until native/current CAD or qualified exchange geometry is recovered and bound.

## Mission/reference mesh library

Drive contains an `Asteroids (obj)` collection. A native OBJ sample can be retained byte-for-byte with Drive ID/hash provenance for viewer validation; source-mesh availability must not be conflated with Mission-1 target selection or physical/mission qualification.

## Exchange targets

Engineering authority should preserve `FCStd` / `STEP` / `BREP` and native source formats while web/runtime distribution should converge on `GLB/GLTF`. OBJ remains a transparent interchange/review format. USDZ can be generated for AR once geometry and material state are release-qualified.

## Non-promotion rule

A viewer mesh, manifold mesh, render, CI pass, digital equation closure or simulation result is not evidence of physical manufacture, structural capacity, safety, empirical performance, site approval, commissioning or deployment unless the required external evidence and competent review are separately bound.
