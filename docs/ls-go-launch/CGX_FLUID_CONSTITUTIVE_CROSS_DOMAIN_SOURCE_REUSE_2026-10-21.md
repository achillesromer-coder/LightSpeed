# CGX / Raphael / Alexandria — shared fluid regime operator review

**21 October 2026 · Draft-only, stacked after PR #198 · NON-AUTHORITATIVE**

## Consolidation without a new fluid engine

The existing Drive-owned Type-I volumetric kernel `UTP-137` already declares the governing science. Rather than creating separate viscosity, aerodynamics, resin-printing and propellant numerical engines, `cgx/review/fluid_operator_regime_projection.py` provides one **source-bound, read-only selection/proof lens** for these exact unchanged owner kernel records:

- `VGK-019` steady, fully developed circular Newtonian laminar channel
- `VGK-020` effective porous/Darcy permeability and fluid viscosity
- `VGK-036` coupled sparse 4D-state boundary/interface assembly
- `VGK-039` general 3D CFD/fluid equations

The projection refuses any mutation of its original owner source: it pins the existing Git blob `c5e92038495a15a66fb6008925a1bb3e92d7bd8b`, exposes exact source SHA-256 and source size, and fails closed if the original owner file changes or lacks those gated kernels.

It links shared mass/momentum transport and fluid viscosity to six declared profiles (circular channel, porous flow, external aero, PrintSpace resin/inert-gas flow, corridor misting, orbital propellant/microgravity). All application-specific closure remains explicit: equation of state, shear dependence, Reynolds/Mach/Weber, turbulence, thermal/cure/wetting, geometry, walls/ports, multiphase and gravitational/interface conditions. These are **not** six standalone solvers or six measured physical results.

## Narrow deterministic check, not CFD qualification

The only numeric evaluator is a synthetic Hagen–Poiseuille baseline under explicitly provided assumptions. It computes:

```
nu = dynamic_mu / rho                           # [m2/s]
U  = Q/(pi*r*r)                                 # [m/s]
Re = rho*U*(2*r)/dynamic_mu                     # dimensionless
estimated entrance L_e ~= 0.05*Re*(2*r)         # screening only
delta_p = 8*dynamic_mu*L*Q/(pi*r**4)             # [Pa]
```

All eight conditions must be caller-confirmed **without treating such confirmation as empirical evidence**: Newtonian, single-phase, incompressible, steady, fully developed, no-slip, rigid circular walls and isothermal. The conservative `Re < 2000` and entrance length screens must pass. If not, output `HOLD_REGIME_OR_CONDITION` and `pressure_drop_Pa=null`; never fall back to invented CFD output. Even a passing synthetic screen does not prove roughness/entrance correction, material data, leakage, pressure rating, engineered safety or accepted CAD.

## Independent falsifiers in CI

The ten targeted tests verify exact owner-source Git object, unchanged four kernels, M-L-T dimensional identities for nu/Re/pressure, the laminar pressure example, viscosity and radius scaling, high Reynolds rejection, short entrance rejection, all eight failed condition flags, malformed/NaN/underflow/surprise owner-permission attributes, and original-source SHA tamper/deletion rejection. The inherited UTP-137 volumetric tests are run too. Any negative scenario fails closed rather than broadening the model.

## Lens and adapter handoffs

Lane A (:00): reuse the named dimensional/condition schema in existing Creator/Press family adapters. Never claim the profile is an installed OpenFOAM/SU2 or a qualified numerical solver. Convert R0 measurements into R1 SI typed candidates, attach original SHA and source licence, and preserve unmeasured variables as null/HOLD.

Lane B (:11): use the shared operator as a symbolic selection grammar. New cross-domain relationships need independent scenario counterexamples rather than merging owners or physical models. Attach to existing VGK and MRI4D view overlays, not a new master catalogue.

Lane C (:22): if a Generative UI view displays pressure/flow, label it `synthetic conditional baseline`, show assumptions, confidence, source, dimensional frame and no release. Never hydrate private material from Vite public assets; issue #158 remains open.

Lane D (:33): source/rights provenance, PAs, library originals and third-party licences have separate acceptance. Source references and sample code cannot be transformed into installed tool/provider claims.

Lane E (:44): a generated view/pressure calculation is not native authenticated FileSpace/DataSpace evidence. Issue #161 still requires truly separate signed physical peers, source and state-root readback and replay/ACL rejection.

## Status

`SOURCE_BOUND_SYNTHETIC_OPERATOR_REVIEW` only. No owner DBR promotion, Google Drive owner workbook edits, public release, 61-file private migration, 2-node physical peer acceptance, software installation, physical actuation or production merge. The earlier 21/45 checkpoint fraction remains unaffected. Safe next step is one verified R0 measurement source or independent domain dataset only after rights, SI units and provenance validation.
