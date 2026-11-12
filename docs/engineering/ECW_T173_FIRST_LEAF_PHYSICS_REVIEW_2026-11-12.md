# ECW.cgx.html — T173 physical-interface and first-leaf catalogue (source review)

**Date:** 12 November 2026 AEST  
**Disposition:** REVIEW ONLY / NO CGX NATIVE ADMISSION / NO MINT / NO PUBLIC RELEASE  
**Source HEAD:** LightSpeed main `e46ca5e888dac9035f41f4b52a1cdd297b4c8cac`  
**Raphael Nov 8 source SHA-256:** `328ab7d117f9906d85608a40cc1e6d9e278f49570431078e14a0d91df553bc9c`

## Architecture
- Preserve the **173 numbered Raphael research positions** exactly as source-bound reference roles, not physical molecules, atomic numbers, usable opcodes, or automatically distinct 3D solids.
- The **174th position is null and non-addressable**: no leaf, geometry, state, Object_ID, founder reference, or mintable item.
- Each role declares **173 possible child addresses** but initially instantiates a common 18-leaf *typed contract*. Leaf positions 019..173 remain uninstantiated. Shared definitions are content-addressed rather than repeated.
- 173-way recursive addressing and balanced ternary `{-1,0,+1}` are **different** mathematical schemes. A trit applies only to a declared typed basis, tolerance and validity mask. Zero is a defined neutral, never an unknown.
- Distinguish `RAPHAEL/ROLE/*`, `MAT/*`, `INTERACTION/*`, `MODEL/*`, `SOURCE/*`, `INSTANCE/*` and native CGX Object_ID namespaces. No automatic physical material binding from Raphael slot index.
- The Nov 8 independent audit reports 159 issues across 72 positions, 0 then-validated coordinate meshes; Nov 9 RaphaelVisualStudio v0.7 reports 131 numeric payloads covering 140 roles and 33 unresolved mesh positions. The later numerical claims require independently accepted coordinate/incidence checks before physics use. Leave the 33-mesh work to its existing separate proof lane.
- Known alias conflict: Nov 8 audit `005↔058` (rhombicuboctahedron) and `014↔059` (J37); draft Raphael PR #7 reports a different J37/058 mapping. Hold all four references in review and do not merge identities silently.

## First-leaf contract 001–018
`001 role_identity; 002 source_label; 003 source_family; 004 topology_fingerprint; 005 canonical_equivalence; 006 geometry_payload; 007 geometric_interface; 008 spatial_chart_and_scale; 009 material_binding; 010 phase_and_state; 011 interaction_edges; 012 governing_equations; 013 boundary_conditions; 014 data_and_validity; 015 semantic_view; 016 evidence_and_rights; 017 ternary_relation; 018 children_and_references.`

Initial material bindings, physical solver declarations and trits are **UNBOUND** for all roles until sourced and qualified. This is deliberate. The first-leaf semantic contract and the complete derived 173-record review set have been generated separately as machine-readable JSON and a human-review spreadsheet; avoid claiming those full datasets are already merged into this branch.

## Ten inherited Raphael reference families
13 Archimedean; 1 Miller/torsion; 7 prisms; 92 Johnson-labelled; 4 Kepler–Poinsot; 13 Catalan duals; 6 proposed chiral frames; 1 pseudo-great proposal; 35 uniform-star-labelled; 1 U75 reference.

Family-dependent geometry **candidate** interfaces: bounded polyhedral occupancy, parametric extrusion, facet normals/dual relations, orientation frames or research-only visualisation. No existing catalogue polyhedron is automatically a chemically valid `H2O` shape or a CFD-ready watertight boundary.

## Material and interaction dedication
Separate physical medium identities for moist/dry air, water vapor, liquid/droplets, clouds, ice, rain/snow, aerosols, oceans/freshwater, sand/clay/loam, rock/bare soil, trees/shrubs/grass/crops, urban surfaces, wetlands, snowpack and sea ice. A medium's geometry representation changes with scale and application; the physical state/equations/data remain typed and source qualified.

Initial interaction pairs (review-only): air–air transport; vapor–cloud phase changes; cloud–rain/ice; orographic air–terrain; air–soil/vegetation/urban/snow/ocean energy and momentum; rainfall–soil/canopy/urban runoff; aerosols–cloud CCN; freshwater/ice/ocean interfaces; droplet surface tension. Require real fields, units, boundary parameters and a qualified solver, including conservation and grid-resolution limits.

**Moles**: `n=m/M` counts amount of substance. Surface tension concerns interface free energy, temperature/composition and curvature, not a mole-to-weather law. A spherical droplet's Laplace jump `Δp=2γ/r` is a scale-specific approximation. Atmospheric-grid cells must follow physically admissible conservation and state equations.

**Forecast probability**: combine qualified NWP and available ensembles (ECMWF IFS/AIFS ENS, NOAA GFS) with historical ERA5 and independent observed verification. Machine learning may calibrate/downscale residuals using terrain, land cover and soil predictors with strict time/space holdouts; it may not fabricate unobserved subgrid conditions or convert a geometrical analogue frequency directly into future probability.

## Source candidates & restrictions
- ECMWF Open IFS/AIFS: https://www.ecmwf.int/en/forecasts/datasets/open-data (CC BY 4.0, applicable terms)
- ERA5: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-pressure-levels
- ERA5-Land: https://climate.copernicus.eu/climate-reanalysis
- ESA WorldCover: https://esa-worldcover.org/en/data-access (10 m, years 2020/2021; class ≠ physical parameters; CC BY 4.0)
- NASA MODIS MCD12Q1: https://data.nasa.gov/dataset/modis-terraaqua-land-cover-type-yearly-l3-global-500m-sin-grid-v061-fac3a
- NOAA ETOPO 2022: https://www.ncei.noaa.gov/products/etopo-global-relief-model (CC0)
- ISRIC SoilGrids: https://docs.isric.org/globaldata/soilgrids/index.html (REST API currently reports paused; use published alternative access)
- Existing source conversion contract: `cgx/domain_templates/file_conversion_contract.json`
- Existing source/view registry: `cgx/domain_templates/semantic_view_lens_registry.json`

## Acceptance and operational status
1. Source/hash/173-role/18-first-leaf/empty-174 exact parity; alias conflicts held.
2. Typed medium physical properties and scale-specific governing equations.
3. Exact frame/time, mass/energy/water conservation and missing-value tests.
4. Temporal/spatial out-of-sample hindcast, ensemble calibration and independent observation comparison.
5. Offline `ECW.cgx.html` with empty globe; optional local `WXPACK1`; optional source-qualified online adapter; existing CGX bridge only after accepted authority.
6. No CCC mint, source-rights waiver, root signing, automatic deployment, or public scientific promotion.

**BouwerBase:** founder reports external power interruption on 12 November 2026; mark host-dependent checks `BLOCKED_EXTERNAL_POWER_REPORTED / NOT_RUN`, **not** a software failure. No remote host calls or polling during outage. Resume only after founder-reported restoration, then one authenticated availability check and a bounded read-only inventory. Existing automations remain scheduled as configured. Handoff: https://github.com/achillesromer-coder/LightSpeed/issues/40#issuecomment-6812273839

This document is an additive cloud source-review note only. It does not replace Raphael master workbooks, other owner branches, or the active Cognigrex.cgx parent.
