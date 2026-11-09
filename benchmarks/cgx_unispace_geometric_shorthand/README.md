# CGX / UniSpace — fuel-for-fuel engineering decision record

**12 October 2026 · Candidate software proof, not canonical production release.**

## Decided from measured software tests

1. **R0 universal byte preservation is the irreducible base.** An unknown file remains reconstructable, even if its type/meaning is unknown. The `CGXS` envelope is not required when raw/ZIP is cheaper.
2. **Geometry is indexing, not a source of entropy.** The prototype uses 3D Morton mapping for chunks, `index % N` layers, independent time/state reference. Existing CGX semantic `XY/Z/T` and rights remain the owning schema. Geometry faces are derived references only.
3. **Read variation is typed and evidence-gated.** JSON, WAD, PNG, JPEG, ZIP, PDF and executables may be recognised by bounded signatures. Actual semantic parsing requires a registered adapter and source/licence verification. Unsupported format remains `OPAQUE / UNKNOWN`.
4. **Adaptive delivery has at least three modes.** (a) Cold source: raw/ZIP/CGXS measured selection; (b) cached chunks: exact digest reference; (c) same entire source root: sparse patch (one root plus edit ranges). Never decode a reference without locally verified bytes.
5. **Do not mutate the existing CGX object family or create a new runtime.** The carrier is a candidate function under source-native FileSpace and the LightSpeed CGX Node Exchange; real rights, cryptography and DBR sign-off remain external.
6. **No unpriced computation.** Conversion is only worthwhile if the expected bytes saved, CPU cost, energy, latency and risk fit a measured local budget. Model weights are environment-specific; this prototype measured bytes and one-run wall-clock, not joules.

## Reversible source benchmark

See `benchmark_results.json` for machine-readable inputs, hashes and exact bytes. Ordinary ZIP/DEFLATE is a fairer cold comparison than uncompressed file size.

| Fixture | Original bytes | CGXS bytes | ZIP bytes | Cold preferred (bytes only) |
|---|---:|---:|---:|---|
| Structured JSON | 39,210 | 2,795 | 2,100 | ZIP |
| CGX Prism HTML | 12,126 | 6,068 | 5,315 | ZIP |
| Freedoom Phase-1 WAD | 28,795,076 | 11,575,325 | 10,305,057 | ZIP |
| Complete playable Freedoom HTML | 22,018,509 | 16,881,865 | 16,588,054 | ZIP |

A one-byte byte-for-byte change produced 544 bytes (WAD) and 547 bytes (complete HTML) using **exact original root already cached**. Both pass SHA readback; without cache they fail. A previously implemented chunk-hash mode used 36,505 and 65,134 bytes respectively for the same controlled edits. The single-root version is more economical in this particularly sparse scenario. Neither result validates modified-game playability.

## Required semantic/reading variations, in source order

- **Opaque native:** exact bytes, size, source identity, ACL, provenance, hash and expiry; only hex/native open supported.
- **Typed structural:** registered JSON/CSV/XML/PDF/OpenXML/ZIP/media/app/CAD parser; capability and verified original input. Read-only default.
- **Geometric:** 3D Morton or domain-native coordinate system; coordinate basis, SI units, tolerances, transforms, parent/child, geometry owner and version.
- **Semantic/equation:** language dictionary version, typed kernel, explicit inputs/outputs and uncertainty; no untrusted code evaluation.
- **State/DataSpace:** root handshake, index of known/cached/unknown, minimal delta with integrity, optional distributed compute under lease.
- **Operational/PrintSpace:** tool-specific adapter and independently accepted process safety; physical qualification never inferred from bytes.
- **Presentation:** device/role/task-selected lens; accessibility and permission policy takes precedence over preferences.

A single CGX object can expose one or N faces. N is determined by required information, not a mandated geometry. Logical layers, byte chunks, application libraries, distributed nodes and hardware devices are distinct concepts; do not equate their counts by default.

## Next acceptance gates

1. Attach decoder as a **read-only opt-in native adapter** in the existing CGX owner flow, without replacing CGX-IR, owner DBR or existing source providers.
2. Verify native application round trips (read, preserve, export, reopen) for `.txt`, `.json`, `.pdf`, `.xlsx`, `.docx`, `.png`, `.html`, `.wad`, `.zip` and one CAD source under permission and revision checks.
3. Add signed root negotiation and two independently authenticated devices; compare against rsync, xdelta and content-addressed storage rather than only ZIP.
4. Measure decode CPU, peak RAM, storage churn and **actual device joules** on BouwerBase and an energy-constrained device. Work out the break-even threshold for each transport medium and task.
5. Prototype lazy/selective hydration and one source-bound registered semantic lens with inverse conversion proof, separating reversible from inferred output.
6. Complete owner release, licence, private/public and source DBR gates before hosting converters on UniSpace public pages.

## Source context

LightSpeed `cgx/domain_templates/universal_object_extension_contract.json`, `node_exchange_contract.json`, `view_selection_policy.json`, `semantic_view_lens_registry.json`; GitHub LightSpeed issue #161 and #158; Raphael PrintSpace draft PR #6. This file adds no alternate canon.
