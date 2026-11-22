# PrintSpace CGX FileSpace/LOAD.Lite digital facets — 22 November 2026

**Integration lane:** `achillesromer-coder/LightSpeed`, draft PR #236, `cgx.manufacturing` under the pre-existing PrintSpace and UniSpace source-governance stack. No parallel manufacturing compiler, private source warehouse, new persistent agent, network protocol, actual machine or native mint created.

## Canonical scope and limits

This increment expresses the already-implemented **three-level diode → board → phone** virtual-factory catalogue as a deterministic **content-addressed DAG of reusable CGX faceted JSON objects**. Its canonical `printspace_cgx.py` derives exactly from the existing source catalogue and retains every original source pointer and explicit verification ceiling. Product dimensions and machine envelopes in the viewer remain *synthetic*; an entire phone is not manufactured or validated simply because its conceptual components share a graph.

The bundle is `CGX-PRINTSPACE-FILESPACE-BUNDLE/0.1`, a **digital interoperability projection**, not certified native CGX/ternary fractal encoding. Its content hashes are byte-level internal consistency checks—not digital signatures, rights grants, third-party CAD authentication, model calibration, material lot passports or DBR receipts. It contains **opaque paths only** to owner PC01, Raphael geometry, equation kernels, material matrix, simulation module, manufacturing IR and LOAD lens. No source bodies or secrets are copied. The source of authority remains the original owner-controlled library, Git code and independent evidence per relevant domain.

## Object identity and deduplicated dependencies

Every object is exactly one `sha256:<64 hex>` of canonical JSON UTF-8: sorted keys, ASCII JSON, no non-finite numerics. Each object records a facet `kind`, typed `payload`, *sorted and unique* hash dependencies, and false native/device permission flags. Stable aliases are treated as pointers—not independent copies of source information—and the bundle root binds all objects, catalogue revision and release holds. The integrity validator verifies every hash, alias, parent/child dependency, acyclic closure, bounds and complete root manifest. Any missing objects, unexpected source bodies or authority-escalating fields fail closed.

Facet families include opaque source reference, illustrative geometry primitive, printer-family role, synthetic operating environment, individual part instance and external-part provenance, non-actuating process stage, nested product assembly and root FileSpace control reference. A given nominal box primitive appears once and is reused across part placements; **canonical equivalent geometry is asserted only for identical nominal box payloads**, not all T173, chirality classes, real CAD revisions or material formulations.

The existing catalogue covers seven named printer roles and three environments: terrestrial, controlled enclosure and illustrative in-situ low gravity/vacuum. Environment entries remain assumptions with independent C0, atmospheric physics and equipment qualifications pending. Product hierarchy references diode in board and board in phone; source-required battery, SoC, RF, display, camera and other external devices remain flagged as unqualified/sourced components.

## Selective hydration and reversible transport

`h0_handshake`/`LOAD.Lite` returns **only** root and product alias keys with zero bodies. `hydrate(..., product_id='diode'|'board'|'phone', mode='SUBTREE_DIGITAL')` traverses the selected product and only its required geometry, parts, stages, printer roles and child assemblies. `ALL_DIGITAL` expands the complete internal *symbolic* graph, but still retrieves **zero external material bodies, CAD files or DBR/private source bytes**. `NATIVE_LOAD`, device-side operations, unsupported high-depth requests and budget overflows are rejected. The copy is bounded (512 maximum canonical objects, 1 MB JSON, 24 dependency-depth steps, caller-defined node/byte limits).

`pack_lite` is a deterministic standard zlib-9 compression and base64 JSON transport wrapper with original-byte length and SHA-256 revalidation, decompression cap and canonical JSON re-encoding check. It is **not** the promised native ternary or theoretically optimal CGX compression; size reduction applies only to this particular digital payload and must be benchmarked per content type. It can be unpacked offline with Python standard library only.

`verify_back_down` requires the *original* source catalogue, regenerates the full DAG and checks every object/alias/root against the received bundle. A self-consistent substitute is not accepted as owner-authentic without an independently trusted source hash. Those semantics extend the previously validated 12-service manufacturing stack and its 216-case electrothermal and 756-case printer/product/environment/scale sweeps **by reference**, not by silently generalising these narrow surrogates to all real science.

## Delivered files and build contract

- `cgx/manufacturing/printspace_cgx.py`: deterministic content-addressed facet graph, integrity validation, non-hydrating H0, selective digital hydration, source replay, compact transport.
- `cgx/manufacturing/printspace_cgx_bundle_v0_1.json`: full inspected conceptual CGX FileSpace graph.
- `cgx/manufacturing/printspace_cgx_h0_v0_1.json`: source-only LOAD.Lite handshake.
- `cgx/manufacturing/printspace_cgx_lite_v0_1.json`: compressed digital transport for byte-preserving offline exchange.
- `scripts/build_printspace_cgx_bundle.py`: reproducible build and `--check` drift safeguard.
- `scripts/build_printspace_studio.py` and `cgx/manufacturing/printspace_studio_v0_1.html`: same offline studio, extended with **CGX H0** and **CGX Package** export controls and embedded source-matched hashes.
- `tests/test_printspace_cgx_bundle.py`: negative, reproducible, source-replay and immutable hydration regression; included as an additional stage of the pre-existing sequential CI.

Build order: `python scripts/build_printspace_cgx_bundle.py` → `python scripts/build_printspace_studio.py`; validation: both tools `--check`, followed by `python -m pytest -q tests/test_printspace_cgx_bundle.py` and full `scripts/run_cgx_printspace_batch.py --profile comprehensive`. All copies and build steps refer to the **existing canonical** catalogue—none can independently qualify an owner-provided material or physical printer.

## Remaining empirical and platform-native gates

**Before native CGX/UniSpace admission:** verify production FileSpace/DataSpace schema, signed owner rights and provenance, exact T173 geometry as mesh/incidence if used, licence conditions, host Load.lite/private hydration access controls, semantic-equivalence versioning and content-address resolver interoperability. These require owner approval and native platform readbacks; JSON hashes alone are not admission receipts.

**Before physical PrintCeptor operations:** obtain source-verified PC01 CAD, printer travel/work envelope, real toolhead and kinematics, verified feature resolution and processing material systems; measured lot-level forward and reverse interface adhesion/conductivity; atmosphere, purge, heating, pressure, humidity and 4D activation histories; calibrated metrology, environmental safety, independent C0 and separate parent DBR approval. 3D rendering and factor sweeps are not performance guarantees.

**Before a complete commercially printable phone:** separately qualify the board, semiconductor processes, encapsulation, power storage, RF/EMC, antenna integration, display, camera, mechanical reliability, thermal safety and all externally sourced/licensed parts. Choose a hybrid multi-process network when warranted. A user-facing product claim must be narrower than the actual independent measurements and standards verification.

**Retention and reserves:** pre-DBR register protects current canonical sources and evidence; historical candidates are proposals only. No deletions, archive moves, signed mint/DBR or machine operations are authorised by this module. No RDC calls required; preserve the user-declared 25% normal reserve and 24% emergency floor.
