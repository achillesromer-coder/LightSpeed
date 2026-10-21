# Achilles / CGX — one source-linked water state, reused without physics conflation

21 October 2026 (Australia/Brisbane) | Candidate review artifact; **not a new kernel/graph/master/solver**.

## Source anchor and fidelity
NIST, *Reference Correlations for Thermophysical Properties of Liquid Water at 0.1 MPa*, 2009, Table 8, sample computer-verification point at **T=298.15 K**, **p=0.1 MPa**. Original publication: https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=832373; NIST abstract: https://www.nist.gov/publications/reference-correlations-thermophysical-properties-liquid-water-01-mpa . The published sample gives **density 997.047013 kg/m³** and **viscosity 889.996774 µPa·s = 0.000889996774 Pa·s** at the same state. The local JSON is a *verbatim-numeric transcription* of only this two-quantity row, not a reproduced original NIST source or independent measurement. Original source PDF bytes and SHA-256 have **not** been obtained/attested. Redistribution rights are **not** claimed. To obtain complete R0 external-source admission, acquire the source from the official original URL, checksum, parse provenance and rights, with owner acceptance.

## Existing owner components reused
- `cgx/domain_templates/cross_domain_bridge_registry.json`, `operator_family_crosswalk`, `METHOD_APPLIES_TO`; `cgx/portable_node/cross_domain_method_lens.py` handles dimensional-only/operator reuse. We **do not** create another cross-domain method resolver.
- Equation `T1K-012` and volumetric `VGK-019` model steady fully developed Newtonian laminar circular tube flow. Existing `VGK-020` is porous Darcy with distinct measured permeability and regime; `VGK-039` is full general CFD and is **not** implemented by this fixture. Existing RFS/EMFF medium sweep uses dynamic viscosity and density for particle Stokes screen with small Reynolds and isolated sphere assumptions.
- Source hashes seen in owner Git at comparison: `type1_equation_kernel_v0_1.json` Git blob `ff65474eb744273d8502d11417321cc35e6fae00`; `type1_volumetric_kernel_v0_1.json` Git blob `c5e92038495a15a66fb6008925a1bb3e92d7bd8b`; `cross_domain_bridge_registry.json` Git blob `1ffbb1ce9a9bf17b9b5d62a4cb5c1da324b0b413`. These are source snapshots, **not current promoted DBR revisions**.

## Three intentionally synthetic quantitative screens
| Existing consumer | Synthetic geometry/process inputs | Analytical output | Assumptions and hold |
|---|---|---|---|
| `T1K-012` / `VGK-019` | radius=0.001 m, length=0.1 m, Q=1e-7 m³/s | pressure drop ~22.66358 Pa | computed Re~71.32; entry length estimate 0.00713 m < L; needs actual geometry/wall/flow proof |
| `VGK-020` | k=1e-12 m², A=0.001 m², L=0.02 m, Δp=100 Pa | Q~5.617998e-9 m³/s | *k is entirely hypothetical*, Darcy regime not independently proven; any 'source-measured' claim rejected |
| RFS/EMFF small particle | 30 µm ideal isolated sphere, relative speed 0.0001 m/s | drag ~2.516407e-11 N | Re~0.00336; real magnetic force/particle material and wall effects unmeasured |

The three output dimensions differ: Pa, m³/s, N. All reuse the same attributable viscosity and density state; none asserts physical or mission validation. Regime/units/temperature/pressure and source property identity are hard checks. General CFD, non-Newtonian resin, turbulent/high-Re and dynamic 3D simulations are explicitly out of scope.

## Tests and owner route
26 focused tests: 25 passing in standalone portable workspace, 1 existing-contract integration test *skips locally*, runs in full LightSpeed GitHub tree. Adversarial cases include forged original SHA, fabricated owner DBR/rights/measurement, viscosity unit mismatch, temperature substitution, Reynolds and entrance-length violations, unqualified porous permeability, wrong particle geometry, NaN, source-state substitution, false canonical release and non-equivalent kernel conflation.

Owner: Alexandria/shared L4-L5 source/evidence joins; Lane B :11 reviews `METHOD_APPLIES_TO` integration; Lane A :00 may reuse source state as typed property fixture but not register a solver or codec; Römer/Eco/PrintSpace/EMASSC keep domain calculations and hardware acceptance independently. Co-running frontier conversation may propose candidate aliases or higher-dimensional/scale views but cannot alter quantity semantics or default rights. Do not recast unresolved RUVR acronym. Link-only source is not fully acquired R0.

**NEXT**: actual measured source-specific input (e.g., signed porous coupon permeability vs temperature, calibrated microchannel dimensions, instrumented fluid test) with owner/permission/uncertainty, plus real NIST source byte hash, then output provenance and negative counterparty tests. Keep #158/#161 and all physical qualification HOLD.