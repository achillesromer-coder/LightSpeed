# UniSpace / CGX — Modular physical product and five-container synthesis handoff
**20 Oct 2026 · DRAFT · SOURCE-ONLY · NOT an engineering release, quote or owner-approved site design**

## Source-first reconciliation
- Physical component/catalogue authority: Type 1 Romer Cognigrex tabs `27_CGX_Component_Geometry_Atlas_v0_1` (411 archetypes), `28_CGX_4D_Field_Slice_Model_v0_1` (64), `29_Raphael_Component_Geometry_Search_v0_1` (61), `30_CGX_Component_Interaction_Map_v0_1` (75), and `25_CGX_Node_Horizon_v0_1`. Git source mirror: `docs/engineering/CGX_COMPONENT_GEOMETRY_ATLAS_2026-10-08.md`.
- Modular function-to-stack precedent: `docs/engineering/CGX_PRINTABLE_SOLID_STATE_PORTFOLIO_2026-10-07.md` CGX-COMPILER-001, ASM-PERMISSION-001 and BOOTSTRAP-CLOSURE-001.
- Source-attested facility methodology: InterSol planned facility twin; `docs/digital-twin/DIGITAL_TWIN_ATRIUM_2026-09-11.md`, `data/digital-twin/twin_showcase_manifest_2026-09-11.json`, `assets/models/intersol.obj` and derived internal review `apps/lightspeed-go/public/review/mesh/intersol.json`. InterSol defines site→room→assembly→component→service and service adjacency/hazards/commissioning. **Mesh coordinate units are not physically accepted metres or shipping-container dimensions.** Do not reuse numeric bounds as container sizes.
- Source-attested technical projections: `docs/digital-twin/type1-svg/T1_SVG_STANDARD.md` T1-00 to T1-07; native CAD/structured workbook/telemetry remain different authorities.
- Existing CGX FileSpace/DataSpace/LightSpeed/CCC rules remain the only authority for object identity, rights, runtime, verified node exchange and billing; public #158, native #161 and prior draft PRs remain independent gates.

## A single composable product, not five independent construction designs

Conceptual parent Object_ID `CGX_PRODUCT_CANDIDATE_5UNIT_RELIEF` is **unbound**, not canonical.
Each compound site references five role instances, whose equipment, utilities and open space remain independently revisioned:
1. Power + communications
2. Water + sanitation
3. Shelter + logistics
4. First response/clinical handover
5. Fabrication + education/repair

The five functional roles are an informed **proposed partition**, not a verified instruction that all five shipping containers have exactly these contents. Number, orientation, size, area, co-location and service routing must derive from site and service constraints; many smaller/alternative variants may be preferable.

Each unit record comprises:
- local enclosure coordinate frame and authority-bound internal geometry;
- 0..N component instances referring to the existing CCC/component atlas *types* (no duplicate catalogue);
- AABB occupancy as a *first test only*; rotations, oblique surfaces, piping and human clearance need native CAD/geometry;
- reserved volumes explicitly typed **expansion, circulation, service access, safety buffers and connection bays**;
- ports with medium, direction, interface/standard, local position and link to another unit/host/network;
- mass and COG, equipment loads, supporting beams/clearances, material hazards, lifting and shipping dimensions, always UNKNOWN unless supplied;
- temporal life cycle: packed → transported → sited → interconnected → tested → operated → repaired → reassigned → demobilised/reused.

Packed and deployed geometry are **different configuration states** sharing typed assets. A vacant deployment room may be occupied by shipped equipment while in transit only if an explicit packing state records its pose, restraints, weight and accessibility. Do not reuse an internal box as verified freight exterior/door envelope.

## Implemented source candidate

`cgx/manufacturing/modular_facility_packing.py` accepts a bounded explicit-SI input graph; computes:
- assets as [x,y,z,dx,dy,dz] AABB placements with no intersecting reservations;
- candidate occupied/reserved/unallocated volume; overflow, intersections and missing geometry;
- component source identity/types distinct from placed asset instances;
- dependency cycles/missing upstream assemblies;
- potential utility-port compatibility (service medium/family, direction, connector standard, face, position and explicit alignment tolerance), without claiming service routing or pressure/electrical tests;
- declared component masses, tare, max gross, freight envelope if present; UNKNOWN/HOLD otherwise;
- site and independent safety/transport/clinical/commissioning hold matrix;
- service-edge candidates and list of required physical evidence.

`cgx/manufacturing/modular_deployment_logistics.py` consumes the same graph and provides:
- type-deduplicated bill of materials with counts and unit pick lists;
- tentative topological installation sequence, unresolved cycles retained;
- per-unit shipping readiness packet with UNKNOWN for gross, center of gravity, handling/WLL, vehicle/route, dangerous goods, lashing, customs, offload and environment;
- engineering drawing schedule T1-00 to T1-07;
- phased trace: acquire→inspect→dry-fit→qualify→pack→transport→site→interconnect→commission→handover.

Both functions are **read-only planners**; no CAD generation, construction authorization, route certification, inventory mutation, purchase order, instrument command or public release.

## Five-unit synthetic regression fixture

`cgx/manufacturing/fixtures/five_unit_relief_synthetic_v0_1.json` uses entirely invented review-only internal boxes `[6.0,2.4,2.5]` m, arbitrary placements, no real ISO shipping container authority. Per unit:
- synthetic internal envelope 36.0 m³;
- 2 placeholder installed asset instances, 1.6 m³ cumulative AABB occupancy;
- 1.485 m³ marked expansion, 14.25 m³ circulation, 2.64 m³ overhead service-access, giving 18.375 m³ reserved;
- 16.025 m³ *geometrically unallocated*, not automatically operationally usable;
- all equipment masses, tare, gross, real shipping envelope, supplier SKU and verified service capabilities UNKNOWN;
- 4 geometrically coincident candidate data-port connections, all uncommissioned.

This fixture proves only program logic for a deliberately simple axis-aligned example. Even passing geometry checks leaves every physical release gate at HOLD.

## Inter-industry derived lens and capability connections

| Lens | Existing capability owner | Composition |
|---|---|---|
| Spatial enclosure, assembly, hardware | CGX component atlas + Type1 SVG + native CAD/FreeCAD | Dimensional authority, datums, attachment and tolerances |
| Functional compound assembly | CGX-COMPILER-001 / ASM-PERMISSION-001 | Function→component→process→equipment→evidence |
| Facility adjacency/services | InterSol planned twin / Römer-Grex | Compartments, utility paths, hazardous segregation, occupancy |
| Supply, procurement, logistics | Römer programme + LS + CCC | Vendor/source provenance, common BOM, storage, dangerous goods, lead times |
| Site and environment | Eco-Grex + map/catchment/monitoring | Ground conditions, climate/flood/fire, water/waste, ecology |
| PrintSpace and local repair | Raphael/PrintSpace + qualified manufacturing recipes | Conditional fabrication; physical coupons and safety gates |
| Knowledge/field training | Alexandria + UniSpace Creator | Offline source references, local procedures, revisions, accessible use |
| Runtime / remote data nodes | CGX FileSpace/DataSpace + LS | Signed/authenticated source and telemetry exchange, not automatic actuation |
| Assurance / custodial | Achilles/EMASSC/FMEA/MPL | Independent hazard, evidence, rights, regulatory and qualification gates |

One common Object_ID graph can hydrate all these lenses, *but source authority still belongs to each original domain/owner*. No CGX semantic inference substitutes for physical regulation, electrical approval, potable water testing, clinical governance, structural certification or freight compliance.

## Compilation steps for an actual product

1. Bind a real candidate/site/project, topography and deployment role using an authorised source, not sample assumptions.
2. Acquire native enclosure and component CAD/BREP/SI dimensions with supplier revision and datum frame; verify credible gross/tare and weights.
3. Bind all candidate embedded systems to actual CCC/source component type, exact supplier material/part and rights.
4. Declare both *packed* and *deployed* poses/volumes; doors, movement arcs, service areas, loading, ventilation, repairability and future spare room.
5. Route inter-container utility links with rated connectors and explicit pressure/voltage/current/diameter/throughput/water quality/data/security contracts. Include fault separation and isolation.
6. Solve 3D interference and support loads, lifting/lashing and COG, environmental/thermal/fire risk, logistics/route/permits, schedule and cost uncertainties.
7. Emit re-openable engineering views T1-00..07 plus exact source-enveloped BOM, cargo manifest, installation schedule, procurement and risk ledger.
8. Independently verify target site, source licensing, supplier fulfilment, safety and service commissioning. Only then an authorised owner may promote a build-ready configuration.

## Claim and UI status

This PR does not change public UniSpace Creator v0.6, official authority, CAD owners, real hardware, PowerShell/host, Git main, Drive or deployed products. It is an additive typed manufacturing/facility planning engine intended to be invoked by existing Creator/Press and CGX capability router **after review**, with no new application master.

Cross-branch review: PR #181 must not be auto-merged with draft PR #174 / #179 / #180; consume their selected source contracts and independently test exact identity, rights, local/offline behavior and physical release holds. #158/#161 remain open.
