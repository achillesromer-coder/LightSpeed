# APOPHIS / Type I digital asset — Public CGX projection

Object identity: `JPL:SBDB:99942` / `candidate:asteroid:apophis`.

## Scope and authority
This directory is a read-only public educational projection from existing Römer/EMASSC/Cognigrex systems. The parent CGX/UniSpace, FileSpace, DataSpace, LightSpeed, operations workbooks, GMAT receipts and Römer-MPL remain authoritative in their own scopes. No duplicate canonical database, private credentials, agency mission control, live telemetry, mining permissions, ore locations or spacecraft readiness is published.

## Implementation
- `index.html`, `style.css`, `app.js`: visual exhibit, schematic flyby, shape-reference and conditional-material lenses.
- `type1-console.css`, `type1-console.js`: five-lens research console (dynamics/materials/mission/risk/provenance).
- `data/ephemeris-2029-30s.json`: 21 real, source-sampled Horizons geocentric state vectors, 2029-04-13 21:40–21:50 TDB at 30-second cadence, AU and AU/day in J2000 ecliptic axes. Frontend converts AU→km using 149597870.7 km. Time scrubbing never extrapolates or integrates.
- `data/object-public-contract.json`: selected safe source-projected physical data, object identity, engineering/mission guards, source roots, historical capture/branch states. Not a sync API.
- NASA image is external and not itself a high-resolution 3D mesh. PDS radar shape data exists but model bytes, orientation, mesh frame/normal, rights and local materialisation remain unverified.

## Canonical source roots
1. NASA JPL Horizons/SBDB event source: `achillesromer-coder/Data/data/jpl/horizons/events/apophis-2029`, manifest captured 2026-10-18, raw file receipts and source checksums.
2. [Asteroid Master](https://docs.google.com/spreadsheets/d/148UObDgK_YsqHDbIkJo89yDvyDcgySTE4wQMEVGwga8/edit#gid=2101927502) `Asteroid Master!A3:Z3`: orbit, approximate 340m diameter, albedo 0.3838, taxonomic S; density blank.
3. [Taxonomy Map](https://docs.google.com/spreadsheets/d/148UObDgK_YsqHDbIkJo89yDvyDcgySTE4wQMEVGwga8/edit#gid=883089090): S-type density proxy 2700 kg/m³ and metal fraction proxy 0.45. These are screening assumptions, not measured material fraction, grade or location.
4. [Asteroid Evidence Register](https://docs.google.com/spreadsheets/d/1Uy04F5gtf2mXf9tDmAyIvNrsCn1kn4Csa2oc-skSZxY/edit#gid=301000025): Apophis shape model, strategic tag/support, 2029 encounter timing; H1, H2 held.
5. [MPL GMAT Windows](https://docs.google.com/spreadsheets/d/1M3nBDHw85S0YV2U3r97GwJ9YyH8w4P42HA-HvpOMhKg/edit#gid=302000001), [Contract](https://docs.google.com/spreadsheets/d/1M3nBDHw85S0YV2U3r97GwJ9YyH8w4P42HA-HvpOMhKg/edit#gid=302000002): candidate windows and field constraints; no triggered GMAT or MPL run receipts. M1/M2/M3 allocation 3/7/11 m³ is an interface planning slot, not proven payload capacity.
6. [NASA PDS shape bundle](https://sbn.psi.edu/pds/resource/doi/apophis_shape_1.0.html): Lawrence & Benner (2026), DOI 10.26033/ydyq-5756, radar-derived preliminary three-dimensional external shape and spin state from historical observations, not subsurface.
7. [NASA Apophis facts](https://science.nasa.gov/solar-system/asteroids/apophis-facts/) and [NASA OSIRIS-APEX](https://science.nasa.gov/mission/osiris-apex/): context, not Römer programme approvals.

## Release gates
- Public educational deployment allowed for clearly qualified figures and source links.
- No verified internal deposits, density measurement, in-situ inventory or survey coordinate file; conceptual cutaways must carry permanent claim boundaries.
- No numerical GMAT mission/launch feasibility result unless signed receipt and authority chain are present.
- Full PDS mesh ingestion requires byte/hash, units, frame, spin, normals, licensing and geometry-sanity validation before representing the actual scientific surface.
- Consumer/browser interaction and mobile design still require end-to-end independent browser acceptance; successful Vercel HTTP responses are transport tests, not UI-certification.
- No changes to upstream master/child workbooks from this release.

## Object data invariants
`ephemeris.object_id===contract.object_id==="JPL:SBDB:99942"`; sample count exactly 21; cadence 30s; frame Earth-centred J2000 ecliptic; no time-system relabelling of TDB as UTC; no numeric extrapolation beyond 2029-04-13 21:40–21:50 TDB.

## Publishing
Project: existing `romer-unispace-apophis` Vercel; serves `https://romer-unispace-apophis.vercel.app/`. Parent UniSpace remains `https://romer-unispace-public.vercel.app/cgx/`. Public child link goes to parent; parent navigation insertion is separate publisher work.
