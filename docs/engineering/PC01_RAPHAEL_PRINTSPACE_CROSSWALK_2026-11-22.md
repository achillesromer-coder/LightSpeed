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

## 411-row owner-matrix source reconciliation — observed 22 November 2026

A read-only connector traversal of the **actual Drive owner workbook** `Type 1 Romer Cognigrex`, tab `32_CGX_Universal_Type1_Tech_Matrix_v0_1`, was completed in four bounded batches for `A2:B412` and `AK2:BH412`. Exactly **411 unique matrix IDs** (`T1M-0001` through `T1M-0411`) were observed, with **411 populated 16-field directional records and 8-field compiler-factorisation sets**. All rows contained a directional non-reversal rule and explicit exact-instance evidence precedence. These are **architectural planning strings**, not observed material compatibility, geometry admission, or 4D performance proof.

A bounded metadata-only implementation mirror is at `cgx/manufacturing/printspace_owner_matrix_projection_v0_1.json`. It records the canonical row locations, matrix/archetype IDs, primitive/operation selectors, a SHA-256 fingerprint per complete set of 24 source fields, aggregate digest and coverage statistics. Full material recipes and sensitive process text are **not** duplicated into this index. It is a point-in-time projection and does not automatically track changes to Drive; any source modification requires an authenticated re-read and reconciliation.

The cross-check tests at `tests/test_printspace_owner_matrix_projection.py` validate exactly 411 rows and matching identities against `cgx/component_atlas/component_geometry_atlas_v0_1.json`, digest consistency, completeness and the no-evidence-promotion policy. This check is included as a stage in the same bounded sequential regression runner. Passing these tests is digital source-index consistency only and cannot replace empirical material/geometry/process/tool verification.

**Reserve:** 25% remaining is the normal RDC stop line, and 24% is a separately controlled emergency floor; no RDC tools were used for this matrix reconciliation, implementation or cloud regression.


## Pre-DBR supersession and Achilles archive-review handoff — 22 November 2026

**No archive move, deletion, DBR promotion, merge, mint, hardware execution or source overwrite has been performed.** This is a pre-DBR **candidate review** under existing `Cognigrex.cgx:/archive-dbr` and ACR3/Type 1 Operations/Achilles P.A governance, not a new archive database or agent queue. The owner-declared Remote Desktop Commander 25% normal stop line / 24% emergency floor is preserved; this change uses no RDC calls.

The typed, read-only candidate register is [`cgx/manufacturing/printspace_pre_dbr_archive_register_v0_1.json`](../../cgx/manufacturing/printspace_pre_dbr_archive_register_v0_1.json). The fail-closed parser [`scripts/validate_printspace_pre_dbr.py`](../../scripts/validate_printspace_pre_dbr.py) and [`tests/test_printspace_pre_dbr_archive_register.py`](../../tests/test_printspace_pre_dbr_archive_register.py) reject attempts to set archive/deletion/DBR permissions, omit protected sources, remove review gates or invent receipt equivalence. Those are schema checks only; the human archive owner must independently re-read source and restoration evidence.

| Candidate | Precisely observed source | Disposition | Independent Achilles action |
| --- | --- | --- | --- |
| `PC01-ARCH-001` | Historical standalone `tools/compile_printspace_review.py` blob `306cad8b...` retained under Git commit `0d8f2c1...` | Ready for **archive review**, not movement | Confirm that active `cgx/manufacturing/review_gate.py` covers unique code; scan active imports, retain Git history, issue parent DBR supersession receipt |
| `PC01-ARCH-002` | Historical standalone `tests/test_printspace_review.py` blob `e686b4c...` under commit `e301f072...` | Ready for **archive review**, not movement | Compare test semantics and negative coverage, preserve historical result lineage, issue supersession receipt |
| `PC01-ARCH-003` | Earlier 12-stage GitHub Actions artifact `14732115075`; ZIP digest `3027f5ed...`, expires 22 Dec 2026 | **HOLD until archived evidence captured** | Copy artifact immutably with checksum, bind exact old-run receipts and chronological provenance; newer 13-stage result is *not* byte-identical or an excuse to delete the older evidence |

**Protected (15 current source and evidence pointers, with exact Git or artifact hash bindings):** the October PC01 convergence note, 81-item printable catalogue, original solid-state portfolio, PC01 operational contract, current 411-row owner index and active review compiler are retained as source/reference or active implementation; latest 13-stage CI evidence is retained. Older source content and the 411-row index must not be conflated with completed canonical absorption. `T173` remains a candidate geometry catalogue; no physical PrintCeptor exists yet.

**Achilles acceptance checklist:** verify the original immutable source SHA and exact locations; traverse current Git references and affected Drive/ACR3 owner records; detect unique content and contradictions; independently test the nominated successor; confirm licence/privacy and immutable recovery destination; obtain scoped review and separate mutation authority; perform exact archive readback *if* authorised; record irreversible operations as distinct final DBR events; issue the explicit reversible closure receipt. Before those gates close, use **HOLD** and do not remove source bytes or close historical lineage.

**Canonical one-version rule:** active implementation remains `cgx.manufacturing` in the existing LightSpeed worktree. Superseded standalone compiler and tests exist **only in Git history** and this register refers to them by exact blob/ref, without reintroducing them in a separate working branch or duplicate corpus. Drive keeps owner engineering/evidence authority and Achilles/A﻿CR3 keeps archival governance.


## 22 November — LOAD/Raphael ground-up composite geometry integration

**Reused committed capabilities, not a competing engine.**

- \`tools/verify_unispace_product.py\` provides **bounded exact convex-integer mesh and fixed-axis translation-canonical identity**. It does not prove arbitrary non-convex CSG, chirality or T173 catalogue admission.
- \`cgx/component_atlas/type1_volumetric_kernel_v0_1.json\` owns the existing **40 VGK topology/boundary records**. Composition references their canonical IDs and hashes; it does not establish another primitive-basis source.
- \`cgx.manufacturing.compiler\` remains the sole manufacturing IR compiler, \`cgx.manufacturing.review_gate\` remains the machine-neutral directional process preflight and \`cgx.manufacturing.composition\` now provides deterministic **geometry references and bounded placements** over those existing components.
- \`apps/lightspeed-go/src/cgxLoadLibraryLensPlan.mjs\` and \`cgxUniSpaceLoadCommandSurface.mjs\` provide the existing non-executing **LOAD.cgx / Alexandria alias and R0/H0 planning conventions**. The new composite carries a minimal \`CGX-PRINTSPACE-LOAD-H0-REFERENCE/0.1\` content-addressed reference **without** a native LOAD activation or private-body hydration.
- Separate [LightSpeed draft PR #205](https://github.com/achillesromer-coder/LightSpeed/pull/205) implements an R0 **source-only** LOAD GPT export-manifest intake; its original source contents, permissions and native DBR remain **outside** PrintSpace. \`LOAD.Lite\` continues as a proposed minimal bootstrap path, not a new agent/root or an authorised private source adapter.

**New digital building unit.** A geometry composite is a bounded immutable description: a source-owned, exactly reviewed convex mesh under explicit millimetre units; an instance placement by integer translation; a VGK topology reference; a material-slot label; a directed candidate interface; and a canonical graph hash. The result maps to \`cgx://manufacturing/composite/<sha256>\` only as a **reference key**, with \`cgx://manufacturing/build/<id>\` remaining the manufacturing IR namespace. The H0 envelope references the canonical mesh hashes and VGK IDs; it never includes private source bytes, executes equipment, installs a model or authorises publishing.

**Ground-up coupon example.** \`cgx/manufacturing/printspace_composite_pilot_v0_1.json\` is a wholly synthetic **three-layer coupon** proposal: a structural region, an interlayer region and a conductive region, formed from **two reusable exact box shapes** and **three placements**, linked by two *untested* directional interface candidates. The bounds may classify a possible touch, separation or overlap; a bounding-box match is *not* exact face contact, mechanical interlocking, adhesion or material compatibility. There is no Boolean union, CAD mesh export, physical build or claimed 4D response.

**Numeric and source limits.** The first release uses exact integer coordinates/translation in millimetres, up to 12 source shapes, 24 instances, 64 interface edges and 256 KiB input; it rejects unverified kernel IDs, malformed/non-convex meshes, disconnected/empty interface graphs, unbound source references, attempted qualified material status and out-of-scope H1–H4 hydration. Changing orientation, scaling, units, shape family, mesh topology, material recipe, stimulus frequency, temperature or response requires explicit new bounded operations and independent validation; they are **not** secretly inferred from the shorthand or ternary representation.

**T173/T174.** A proposed Raphael \`t173_position\` 1–173 on a shape produces a visible **HOLD** pending independently accepted coordinates/incidence/rights/source revision. Position 174 remains reserved and rejected. A generic exact convex mesh can reach \`REVIEW_ONLY\` without thereby becoming a mintable Raphael object. Finiteness of the indexed catalogue does not exhaust manufacturable forms or physical process combinations.

**Test and integration gates.** \`tests/test_printspace_composition.py\` tests deterministic shape-key reuse, order-invariant graph hashing, the three-layer fixture, T173 hold/T174 rejection, directional edge identity, disjoint/ambiguous bounds, invalid mesh/units/transform/kernel/source, unrelated graph nodes, untrusted rights and H1 denial. Included as the **15th stage** of the existing bounded sequential regression batch and the same CGX component-atlas workflow. Exact source-bound CGXI configuration and the PC01 physical build authority remain subject to the existing \`review_existing_manufacturing_ir\` and independently measured coupon/calibrated machine gates.

**Current exact-IR review link.** The existing `review_existing_manufacturing_ir` now accepts an optional geometry-composition input, validates the graph using `cgx.manufacturing`, and requires its exact build URI and the identical frozen IR configuration SHA-256. Unbound CGXI/material/tool/source requirements, malformed geometry, T173 shape candidates and revised hashes remain HOLD. Even matching synthetic review never authorises a machine. **Next justified work:** verify actual contact/Boolean geometry and tool clearance; bind measured directional materials, atmosphere, field-history and encapsulation evidence with calibrated physical tests.

**Archive governance:** existing pre-DBR register now protects the new composite resolver, fixture, canonical VGK library, exact mesh verifier and LOAD source-review lenses in addition to existing PC01 sources. No archive/delete/publication authority is conveyed.

**Regressions:** URI mismatch, configuration-hash drift, malformed shape input and T173 unadmitted candidates are checked on the canonical IR review path. The existing comprehensive batch now contains 15 bounded regression stages. No native LOAD/LOAD.Lite R1–R3 admission or H1–H4 hydration is implied.


## 22 November continuation — exact convex-contact kernel and measured-interface preparation

**Single digital geometry source:** `cgx.manufacturing.exact_contact` now extends the existing `composition` review. It reuses `tools.verify_unispace_product.exact_convex_mesh_review` rather than minting another T173 atlas or changing the manufacturing IR. There is no new LOAD root, host service, archive scheduler or machine executor.

**Mathematical scope:** for two independently validated closed, outward-facing **convex integer meshes** with bounded integer-mm translations, intersect the oriented face half-spaces using **exact rational edge–plane intersections**. Derive the affine dimension of the resulting convex intersection: disjoint, point contact, edge contact, planar face contact or positive-volume overlap. For planar intersections provide **exact rational squared area** (mm⁴); output area in mm² only when its square root is rational. Face direction is carried as an exact outward primitive integer normal from the requested source region toward the target. This is exact **for the supplied geometry and unit assumptions**, not a claim of manufacturing tolerance, physical contact, surface preparation or material state.

The computation fails closed beyond its bounded envelope: up to 64 oriented faces, 192 undirected mesh edges, 12,000 edge–face crossing checks and 2,048 intersection vertices **per pair**. It does not perform a Boolean union/difference, non-convex contact, arbitrary rotation/scale, 4D swept collisions, slicing, tool clearance or physical compatibility analysis. Large or unadmitted meshes must not silently revert to bounding-box clearance evidence.

**Concrete digital pilot:** the two directed interfaces of `pc01-digital-three-layer-coupon` each have **16 mm² geometrically shared planar area** between four-by-four-millimetre regions. This is derived from integer geometry, not measured. An overlap without Boolean resolution blocks ordinary contact/interlayer planning; an interlayer requiring a finite shared face rejects point-only/edge-only contact. Bare `CONTACT_CANDIDATE` remains descriptive even at point contact and cannot assert adhesive capability. A mathematically separated pair may be recognised as separate even if their axis-aligned bounding boxes overlap.

**Qualification, not automatic admission:** each interface carries a deliberately unfulfilled plan: exact lot/tool/pasport identity; deposition of source→target; separately measured reverse target→source; source-atmosphere/surface-preparation/cure record; and a functional/adhesion/damage readback. Every test must bind its own process revision, geometry orientation, real metrology, environment, observed uncertainty, specimen history and rights. Source row metadata under the 411-entry owner matrix can select planning archetypes but never substitutes for the exact UTP-106 material-lot/process coupon.

**First physical comparator proposal (not scheduled or authorised):** choose one verified structurally compatible pair for a 4×4 mm reference geometry, use source-bound material batches, characterise dimensional and surface conditions, fabricate both A→B and B→A with individually controlled deposition and post-cure histories; measure cross-sectional integrity and interface performance under an engineer-approved method appropriate for the feature scale. Compare with unjoined and process-control specimens; predefine reject thresholds and equipment hazards. After successful independent replication, test the interlayer→conductor interface and any later encapsulation or 4D activation separately. Do not assign strength, dose, uncertainty or sample count without a reviewed standard/test protocol.

**Architecture alignment:** the optional `review_existing_manufacturing_ir(..., geometry_composition=...)` still checks *one exact* build URI and configuration SHA-256; the geometry graph hash and LOAD H0 source references are downstream non-authoritative keys. Passing the exact-contact or digital regression cannot override parent rights, native R0→R3 admission, T173 source verification, C0 device safety, witnessed physical receipts, minting or commercial release. The pre-DBR Achilles register protects the new exact-contact kernel and current composite, **22 protected sources**; the three historical archive candidates remain proposed and no bytes are deleted.

**Digital regression:** `tests/test_printspace_exact_contact.py` covers point, edge, planar area, overlap, disjoint, direction, non-convex/invalid input and candidate qualification boundaries; the existing serial cloud regression is extended to **16 test stages**. Use GitHub Actions for full-repository verification and inspect the attached synthetic receipt before approving a merge. No Remote Desktop Commander calls were required.


## 22 November continuation — source-indexed directional witness qualification (digital only)

**Existing sources reused.** Authoritative engineering remains in the Type 1 Romer Cognigrex Drive workbook, tab 32_CGX_Universal_Type1_Tech_Matrix_v0_1, ranges A2:B412 and AK2:BH412. Its fixed 411-row read-only fingerprint projection at cgx/manufacturing/printspace_owner_matrix_projection_v0_1.json retains row identities and observed SHA-256s, not source recipes. The existing cgx.manufacturing.binding owns exact CGXI source/lot/tool/witness evidence semantics, and the canonical compiler owns the build IR. No second material database, manufacturing compiler, LOAD root or private corpus was created.

**Bounded planning integration.** cgx/manufacturing/interface_qualification.py now compiles a deterministic *unmeasured witness requirement plan* from the existing exact convex geometry composition and graph hash, canonical build URI/configuration hash, and owner-row fingerprints. The fixture cgx/manufacturing/pc01_interface_witness_plan_v0_1.json is synthetic planning metadata only; its manufacturing configuration hash is intentionally null until inserted from a real digital compiler output during testing. It is not an authenticated signature or approved configuration.

**Three source-class candidates, not actual material lots:**
- Structure: T1M-0257 / CGA-M-001 / STRUCTURE_DATUM. Not an identified structural polymer or metal lot.
- Interlayer: T1M-0409 / CGA-DIEL-001 / DIELECTRIC_ISOLATION. Not a validated adhesive or sourced dielectric batch.
- Conductive region: T1M-0039 / CGA-I-001 / CONDUCTOR_INTERCONNECT. Not a validated ink/metal formulation.

Each region references the exact observed directional_sha256. Fingerprints bind an observed planning class and one source revision; they must be re-read from authoritative Drive before consequential application. No physical chemical/material compatibility can be inferred from matching source-row identity.

**Four independent directed coupon plans.** The digital three-layer pilot has two geometric interfaces at exactly 16 mm² of *synthetic planned contact area* each. Each interface generates a source-to-target and an independently identified reverse target-to-source coupon, giving FOUR unique candidate coupon keys. A successful test in one direction cannot qualify the other. Each route requires original lot passport, equipment and calibration, independent C0 safety, exact process and pre-treatment revision, atmosphere and cure history, control specimens, method, uncertainty and falsifiers, raw results, independent reviewer, rights and native DBR readback. All physical test evidence fields remain null. State: PLAN_READY_UNQUALIFIED; never BUILD_READY or a licence to print.

**Single canonical IR coupling.** The existing review_existing_manufacturing_ir function accepts the optional interface_selections projection alongside geometry_composition and checks all three against one exact emitted CGX manufacturing build URI and configuration SHA-256. Even a syntactically complete plan yields a MATERIAL_INTERFACE_EVIDENCE_PENDING hold. Modified selection rows, stale geometric source, unbound configuration, claimed qualified measurements, fabricated DBR signatures and mismatched instance IDs cannot promote physical authority.

**Next empirical gate.** Identify or acquire real material lots with observed batch, storage and provider source evidence; choose an engineer-approved machine, process route, deposition orientation and calibrated tools; pre-register both A-to-B and B-to-A comparators and control specimens; independently review oxygen/moisture/pressure/temperature/time exposure, cure and surface-conditioning risks. Specify objective mechanical/electrical readbacks, acceptance thresholds, independent uncertainty and rejection handling *before* any authorised run. No sample counts, mixing recipes, strengths, energy doses or qualification claims are assigned without a signed protocol and native evidence. Non-ambient, chemical, heated and EM steps require independent C0 approval.

**Retained audit.** tests/test_printspace_interface_witness_plan.py tests deterministic four-coupon generation and fail-closed row/identity/authority cases. The existing sequential CI batch increases to 17 stages and emits an unmeasured witness-plan receipt. Achilles's pre-DBR register now protects 24 current/source/evidence references and retains 3 historical candidates pending separate approval. Archive/deletion/native admission are unauthorised. RDC normal reserve 25%; emergency floor 24%. No routine RDC usage.
