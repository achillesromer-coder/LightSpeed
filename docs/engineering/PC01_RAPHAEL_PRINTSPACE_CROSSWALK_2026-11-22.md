# PC01 / Raphael / PrintSpace — geometry-to-process crosswalk (22 November 2026)

**Status:** DIGITAL REVIEW ONLY. Typed handoff to the existing PC01 contract. **Not** a second canonical engineering workbook, a validated geometry admission, a hardware commissioning result, or permission to manufacture. The binding source of engineering decisions and evidence remains [Type 1 Romer Cognigrex](https://docs.google.com/spreadsheets/d/1refNFmebTcmPVojCuZsyILJEWaKz-sVzYLfZtqMl8k8/edit), in particular `32_CGX_Universal_Type1_Tech_Matrix_v0_1!AK:BH` and `33_PC01_CGX_Operational_Matrix_v0_1!A:AD`.

## Existing checked implementations to reuse

- [PC01 typed operational contract](../../cgx/component_atlas/pc01_printceptor_operational_contract_v0_1.json): `PC01-NODE-001`, `CGX-PHYSOBJ-001`, `UTP-117` / 411 archetypes, 16 route profiles, C0–C2 separation, and the first-article hold.
- [UniSpace product verifier](../../tools/verify_unispace_product.py): deterministic archive identity, bounded nested hydrate, T173 parent/previous/next transition grammar, exact *convex integer* mesh review, and canonical fixed-axis translation identity. Its explicit limitations mean the 173 numbered catalogue entries are not 173 validated printer meshes.
- [Raphael Fascicle II code](https://github.com/NCNBOUWER/Raphael/blob/main/N%5E3/RUN/code/fascicle_ii_geomatrices.py): finite normalisation, barycentric map and closure-preserving interpolation. These are mathematical modelling utilities, not material or physical-force validation.
- [Raphael falsification crosswalk](https://github.com/NCNBOUWER/Raphael/blob/main/N%5E3/RUN/proofs/Fascicle%20III/Raphael%20claim%20crosswalk.md): separates internal proof from external empirical tests.

## Minimal interoperable object chain

`source/rights -> geometry construct or validated mesh -> exact instance + scale/units -> interface and gradient zones -> materials and lots -> directed process DAG -> qualified tool & environment -> witness/inspection -> frozen build packet -> C0-authorised execution -> readback -> DBR/evidence`

Represent each source/reference once, resolved by stable content hash plus revision. Composition is a typed tree/DAG of instances, not copying physical property evidence from parent to child. T174 is a reserved non-mintable sentinel. Geometry identity and geometrical equivalence have explicit frames, precision and chirality; no universal deduplication without proof.

### Geometry and physical manufacturing have separate domains

| Geometry projection | Required manufacturing interpretation | Failure/hold condition |
| --- | --- | --- |
| Closed primitive or compound solid | Units, topology, nozzle/tool clearance, stock/feed and production orientation | No coordinates/incidence or constructive proof |
| Transition between two shapes | Explicit geometry correspondence, tolerances, local process and test coupon | Non-manifold or unbounded transition |
| Boundary/offset/interlock | Surface finish, differential contraction, adhesion and collision envelope | Unqualified deposition direction |
| Functionally graded zone | Spatial composition law, mixing/diffusion window, rheology and gradient coupon | Unsupported cross-material interface |
| 4D dynamic state | Initial/reference state, stimulus, constitutive response, hysteresis, repeat-cycle target | Unmeasured transfer function |
| Embedded field/EM function | Conductivity/permittivity/permeability, geometry, measured frequency/power/bandwidth/exposure, EMC and temperature | Field parameter exceeds approved tool envelope |
| Scale/repetition/packing | Dimensionful rescale, minimum feature, process-specific resolution, thermal diffusion, mechanical stability and metrology | Scale crosses qualified envelope |

Representing a geometry compactly does **not** imply constant-time slicing, FEM, collision checking, field simulation or all printer control. Cost savings must be benchmarked against conventional CAD/CAM using end-to-end CPU time, memory, byte size and measured part quality.

## Directed material compatibility and process-DAG contract

Existing authoritative matrix `AK:BH` already declares predecessor and successor classes, interface, atmosphere, cleaning, damage checks, activation, encapsulation, 4D state and verification. Compile these fields into **directed edges keyed by exact material lots and process revisions**. **A deposited onto B is not equivalent to B onto A**. Architecture-level class `ALLOW_IF` is only a proposed planning edge; acceptance requires source-bound evidence.

Each transition node must carry predecessor state, tool, preconditions, measurements, postconditions, irreversible exposure budget and an explicit failed-branch outcome. Typical process vocabulary: `PREPARE / DEPOSIT / CLEAN / PURGE / DRY / CURE / INSPECT / INSERT / ENCAPSULATE / ACTIVATE / VERIFY / READBACK`. Pressure, vacuum, gas flow, laser/UV/EM exposures, moisture and heat are measured machine states where applicable, never merely textual settings.

The scheduler may propose lowest-cost qualified sequences and alternate hybrid or outsource routes but **cannot overrule independent machine-local C0 safety**.

## Near-term digital implementation lane

1. Parse and validate the existing 411-row class-level directional matrix, preserving its source cells and revisions; do not independently rewrite technical content in Git.
2. Add `GeometryInstance`, `InterfaceZone`, `GradedZone`, `ProcessOperation`, `WitnessReceipt`, `MachineEnvelope` and `RightsGrant` type contracts, each with its own source, hash, time and evidence state.
3. Admit *only independently validated* geometry records with exact units/incidence, geometry checks, canonical equivalence policy and rights; keep 173 positions visible as a catalogue even when geometry is unresolved.
4. Compile the simplest closed route to a read-only review packet; create negative tests for reverse-order incompatibility, missing interlayer, atmosphere handoff, collision/thermal damage, field-dose exceedance and untested encapsulation.
5. Benchmark geometric identity/composition versus conventional geometry generation and slices. Report CPU time, RAM, storage and geometry equivalence with instrumentation, not estimated performance.
6. Release reference build kits only after exact source rights and capability gates: (a) directional interface coupon; (b) responsive strip; (c) encapsulated conductor/sensor.
7. Retain the existing root/queue and append outcomes/readbacks there. No new root scheduler, agents, DB service or alternative canonical master.

## FreeSpace / commercial library boundaries

UniSpace is the first-party user brand and voice; FileSpace is identity/provenance/rights, DataSpace is permitted state/events, PrintSpace is physical planning/manufacturing. Offer four rights-aware library projections: **open rights-cleared source**, **community licensed**, **paid qualified reusable recipes**, **private/restricted engineering**. A possible **AUD 5 per authorised print use** is a commercial hypothesis, not an implemented payment product. Each recipe needs licensing scope, revocation/version terms, tax/payment reconciliation, vendor shares where relevant, rights checks, support boundaries and evidence of physical compatibility.

A source-licensed digital design may be publishable before PC01 hardware is built. Claims about 4D actuation, safety, hermeticity, atmospheric modes, hardware throughput or production suitability require their respective experimental evidence before commercial marketing.

## Closeout versus outstanding

**Completed in this handoff:** surveyed and cross-linked existing contracts and verified geometry utilities; defined a proposed typed bridge, directed transition rule, geometry/scaling policy, catalogue rights lanes and eight negative acceptance cases. This is a reviewed *specification*, not an integrated compiler.

**Still open:** authoritative 173-row mesh+rights admission audit; true CAD with units; exact machine envelope/calibration; physical coupon matrix and service-life tests; pressure-rated process hardware evidence; implemented billing and licence enforcement; end-to-end integration tests; public privacy/security regression gates. No offline machine, printer or cloud runner was operated by this change.

**Research alignment:** see the contemporaneous PrintSpace literature review for 2026 PLA/TPU orientation, DLP multivat carryover, graded resin interfaces, sequential LCD/Xolography and polymer/copper encapsulation. Translate each relevant paper into *bounded hypotheses* and coupon designs, never automatic acceptance.

## Handoff destination and approvals

- **Engineering/evidence owner:** existing Drive workbook/ranges above. This review does not elevate authority.
- **Git implementation:** [LightSpeed](https://github.com/achillesromer-coder/LightSpeed) existing `cgx/component_atlas`, `tools/verify_unispace_product.py`, `tests/test_unispace_product.py`; this branch provides a crosswalk only.
- **Raphael geometry evidence:** [NCNBOUWER/Raphael](https://github.com/NCNBOUWER/Raphael) and the existing 173/174 audit. Falsification and empirical validation remain independent.
- **Approval gates:** (A) lock exact source coordinates/units and material-rights references, (B) choose first physical coupon route and host safety owner, (C) separately approve public licensing/product terms. These are gates, not requests to approve unsafe hardware execution.


## 22 November continuation — actual tested integration

**No competing engine.** Repo discovery confirmed the existing canonical manufacturing IR at `cgx/manufacturing/compiler.py`, the 4D stack adapter at `cgx/manufacturing/printstack.py`, the exact-binding gate at `cgx/manufacturing/binding.py`, and the volumetric kernel at `cgx/manufacturing/volumetric.py`. The isolated prototype was consequently refactored into a **pure review gate**, `cgx/manufacturing/review_gate.py`, exported as `cgx.manufacturing.review_printspace_sequence`. The review input **must reference** an existing `cgx://manufacturing/build/<id>` URI; it does not compile a rival manufacturing IR or grant downstream authority.

It validates candidate geometry identity/units/source, the reserved T174 sentinel, exact directed material lot edges, typed DAG ordering, active atmosphere across sequential or parallel branches, calibrated transition metadata, gradient composition and resolution, encapsulation requiring a dependent post-seal test, EM field exposure parameters, machine-local C0 declaration, and rights before any candidate is projected.

**Review result contract:** `HOLD` or `REVIEW_ONLY`; both have `physical_machine_authorised=false`, `mint_authorised=false` and `commercial_release_authorised=false`. The review result says `DECLARED_NOT_INDEPENDENTLY_VERIFIED` because arbitrary receipt identifiers cannot establish physical evidence or provenance. Interoperability with the canonical IR is currently a **referenced review overlay**, not automatic assembly of a fully source-bound PC01 build packet.

**Test evidence:** 22 standalone synthetic regression cases passed locally on 22 Nov 2026, plus a separate 400-input malformed-data investigation with no unhandled exceptions after hardening. The shared CGX component-atlas CI includes `tests/test_printspace_review_gate.py`; consult the corresponding GitHub Actions result for branch validation. No printer or local machine tests were run.

**Still open:** exact 411-row owner-matrix ingestion and per-row revision crosswalk, verified geometry/rights admission, machine and material source lots, measured coupon experiments, link from actual `compile_component` output to the per-operation review envelope, public library entitlement/billing, and actual C0 integration only following commissioning.


## 22 November operational batching and RDC reserve policy

**Owner-supplied current budget:** treat **25% RDC calls remaining** as the protected normal reserve and **24% remaining** as the emergency floor. Do not spend routine Remote Desktop Commander calls at or below 25%. Any emergency draw requires an explicit consequence and approval; never run unknown, restart or destructive local commands simply to consume budget. This is a policy declaration, not an independent connector-usage readback. The review work below used **no RDC calls**.

The bounded runner lives at `scripts/run_cgx_printspace_batch.py` and uses the existing canonical LightSpeed repository and tests. It is not an additional root scheduler, agent, database, or print execution service. Its CLI exposes only named allowlisted test profiles, a fixed local repo root, bounded step/total timeout and an inter-stage rest. Each stage serially exits before the next begins; it writes a checkpoint JSON atomically after completion, plus each stage's log, length and SHA-256. A timeout/failure stops the remaining sequence and returns a nonzero exit code. Test-only PASS cannot promote physical evidence or permissions.

For an **already verified local checkout of this branch** (after installing `pytest`), operators may choose a single explicit execution:

```powershell
python scripts/run_cgx_printspace_batch.py --profile comprehensive --step-limit-seconds 240 --total-limit-seconds 1200 --rest-seconds 2 --output-dir "$env:TEMP\cgx-printspace-batches"
```

The CI path runs the same allowed comprehensive profile inside a GitHub-hosted checkout, uses the CI temporary directory for receipts, and uploads an artifact named `pc01-printspace-sequential-regression` irrespective of test outcome. Review those checkpoints and GitHub Actions outcome before attempting any next phase. CI does not need local network access, RDC, or machine control. This script does not fetch remote assets, change hardware, restart local services, make commits, mint or publish.

**Backpressure:** only one child test command runs at a time; the short pause is a configurable cooling interval, not a measured CPU/thermal safety monitor. Do not claim it protects an overloaded local workstation without independent telemetry. Full local run was not performed during this GitHub-only commit.
