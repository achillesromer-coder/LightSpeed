# CGX / Raphael — Viscosity and Fluid Transport Shared Operator Review
Date: 21 October 2026 · Source-only draft stacked on PR #198 · Cognigrex.cgx remains sole parent

## Existing source owners reused (no new solver)

- `cgx/component_atlas/type1_equation_kernel_v0_1.json`, UTP-136 / **T1K-012**: original fluidic environment source, continuity, pressure-flow and hydraulic regime.
- `cgx/component_atlas/type1_volumetric_kernel_v0_1.json`, UTP-137 / **VGK-019**: laminar circular channel; **VGK-020**: porous-media Darcy relationship, NOT equivalent to a pipe.
- `cgx/component_atlas/component_interaction_map_v0_1.json`, **CIM-024/026/027**: pressure/structure, convection/heat and flow/species coupling.
- The associated source-envelope/owner/rights and status are retained. The new `cgx/review/fluid_transport_regime_adapter.py` is a *synthetic screening and regression unit*, not another CFD numerical engine, physical operating control, trained model, or scientific proof.

## Typed shared source family

Viscosity `μ` is a constitutive property for fluid stress, not a separate domain solver. For Newtonian scalar shear (only), `τ = μ γ̇`; SI: `[μ] = Pa·s`, `[γ̇] = 1/s`, `[τ] = Pa`. Newtonian isotropic tensor stress requires an appropriate strain-rate tensor, bulk-viscosity treatment if compressible, geometry and boundary conditions; the scalar calculator does not imply those cases.

For a **steady, single-phase, incompressible, fully developed, Newtonian, no-slip flow in a straight, rigid circular pipe** under the stated screen, `Δp = 8 μ L Q/(π r⁴)`; `Re = 2 ρ Q/(π μ r)`. The source owner is VGK-019/T1K-012, not a novel invented model. Input values must explicitly specify `m`, `Pa*s`, `m^3/s`, `kg/m^3`, and one synthetic case identifier. Computed `Δp`, resistance, shear and Re remain **model candidates**.

This prototype refuses a different geometry, material law, phase/compressibility, time regime, inlet or wall assumption. `Re<2000` and `L>=20r` are deliberately conservative **synthetic screening rules, not proof** of laminar development, negligible entrance/exit losses, roughness effects or absence of instability. The required `FULLY_DEVELOPED` flag is user-declared; no experimental evidence is inferred. Large/small numbers and underflow/overflow are refused. All source family JSONs are checked at read time with recorded SHA-256; if original source IDs or equations drift, fail rather than silently mint a substitute.

## Fractal reuse / non-equivalence across domains

| Existing family lens | Reusable operator | Invalid extrapolation / distinct proof |
|---|---|---|
| PrintSpace resin | Constitutive μ, channel pressure/flow, temperature dependence | Shear-thinning, cure/gel kinetics, wetting, air inclusion, directional print X→Y ≠ Y→X need rheometer/process evidence |
| M1 highway misting | Laminar liquid feed **if** exact enclosed geometry + measured inputs | Dispersed droplets, air entrainment, wind, spray deposition require multiphase modelling, environmental/safety tests |
| Eco-Grex soil/porous medium | Conservation, viscosity and permeability constitutive input | Pipe Poiseuille must be rejected in favour of VGK-020 Darcy model with measured tensor, saturation and heterogeneity |
| Aerodynamics | Shared fluid momentum/viscosity family, dimensional similarities | External geometry, compressibility, turbulence, boundary layer/drag, Mach/Knudsen/regime and wind-tunnel/CFD validation |
| Römer/EMASSC space liquid line | Same liquid channel law if sealed and all assumptions actually apply | Slosh, capillary/wetting, partial filling, phase/gas and microgravity interface dynamics are not circular-pipe results |

Five case-specific expected refusals are encoded in `cgx_fluid_constitutive_operator_reuse_20261021.json`. The tests include bad SI units, negative/nonfinite μ, missing source evidence, non-Newtonian, air/water mist, compressible and external flow, poor channel aspect ratio, high Re, source-owner drift, r^-4 pressure scaling and signed shear stress. The tests are **synthetic mathematical falsifiers**, not hardware validation.

## Adapter evaluation and UI boundary

This is the smallest deterministic reusable adapter. A future existing Alexandria/LightSpeed/UniSpace/Raphael Generative UI lens may show source family, exact original SHA, SI units, qualified regime, failed falsifier and rights status; do not duplicate pages or turn source text into live sensor claims. Appropriate future external fluid-solver providers (e.g. OpenFOAM, SU2) require separately verified provider source, licences, binary/ABI, model applicability, isolated tests and owner permission. Do not infer availability or runtime installation from registry entries.

Folding rule: original R0 unchanged → source-ID and physical dimension link → scoped R1 numeric candidate → falsification / independent readback → possible owner DBR review. Preserve every original domain record and evidence grade. Raphael/fractal high-dimensional map describes shared semantics/topology; it does not qualify higher-dimensional physics or lossless inferential truth.

## Owner decisions / release status

No live printing, misting, fluid test, aircraft, propulsion, or physical actuator was controlled. Physical qualification and device calibration remain HOLD. The same public review issue #158 (61 assets) and two-node signed native acceptance #161 remain HOLD. The selected evidence-map 21/45 = 47% is **unchanged**: this work adds proof detail to a review source contract, not product readiness.

Next bounded steps: B validates another constitutive-property cross-domain similarity and counterexample; A consumes typed SI schema and tests one native format conversion without claiming physical results; C can project an ACL-safe source-only UI; D checks exact licence/version if a CFD provider is later selected; E remains responsible for independent signed peer, not this synthetic regression. Handoff via existing issue #40 and private Achilles P.A owner decision note. No new CGX architecture, scheduler, production merger or deployment.
