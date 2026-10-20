# Alexandria ↔ UniSpace / CGX — Cross-domain open-source library intake and public-safe training kits
**20 October 2026 · Source-only candidate · parent: draft PR #187 · no public deployment / distribution approval**

## What was consolidated
- Original **207 list entries** from two bobeff game/engine indexes remain in `cgx/review/alexandria_external_reference_intake_20261020.json`, pinned to their original README commit hashes.
- **31 independently discovered source repositories** across 11 domain categories now reside in `cgx/review/alexandria_curated_upstream_tools_20261020.json`. Eight selected GitHub upstream branch-head commits were captured as *observations*, not downloaded/approved builds. One proposed `gmsh/gmsh` repository path returned 404 and was excluded instead of guessed.
- `cgx/review/alexandria_library_projection.py` merges reference identities conservatively: exact GitHub repository homepage match **may** avoid duplicate link registration; code blobs, provider revisions, source Object_ID, engines, assets, model weights, scientific evidence and individual rights remain independent. Extra path/branch URLs are **not** assumed identical full repos.
- Existing 33 file profiles, 34 UI lenses, 12 toolkit families, 49 declared routes, 19 mapping candidates, 40 symbolic volumetric kernels and owner authority still come from the original `cgx/review/library_coverage_projection.py`; no replacement owner registry is created.

## Training and learning maps, not model-weight training or unrestricted content copying

| Knowledge track | Candidate examples | CGX learning artifact and proof |
|---|---|---|
| Native CAD, geometry and interconnect | FreeCAD, OpenSCAD, Blender, glTF | Stable units, frame/tolerance evidence, typed meshes vs parameterized CAD, source-preserving representation and 3D fidelity/loss map |
| GIS, biodiversity and ecological sites | GDAL, QGIS, GeoPandas, pygbif | Geodetic coordinate/projection handling, provider citation, biodiversity terms/data licence and environmental history |
| Aerospace/simulation and science | NASA Open MCT, F Prime, Basilisk, SU2, dolfinx | Solver/model assumption, flight/telemetry architecture, independent numerical tests and decision authority |
| Shared-game runtimes | Godot, ScummVM, OpenTTD, OpenRA, Endless Sky, Freedoom | Game/engine separation, compatible ABI and version, source/binary/game-asset licensing, shared-engine digest and cold/warm tests |
| Local computational/data/AI | NumPy, pandas, xarray, Transformers, ONNX, Ollama | Unit/array/dataframe semantics, model provenance and evaluation, private/local inference isolation |
| Preservation/interchange/licensing | Ruffle, Wayback, OCI, RO-Crate, WASM Component Model, SPDX | Source and provenance metadata, capture history, package digest/rights, conformance and reproducible re-opening |

The listed upstream repositories are **not installed**, **not automatically licensed for Alexandria redistribution**, and **not tested as standalone execution modules** by this catalogue pass. GitHub `license.spdx_id` is *advisory metadata*, especially `NOASSERTION` or `UNKNOWN`. Review actual root and component-specific licences and notices, dataset/model/game asset restrictions, source revisions and export/redistribution requirements before including executable bytes in a kit. Avoid source-code/model-weight ingestion for model training without appropriate authorisation.

### Standards-first interoperability
- Use SPDX licence identifiers, dependency/SBOM declarations and original licence notices, not a custom moral-rights or licence heuristic.
- Existing CGX Source Envelopes and R0 hashes remain authoritative for local original bytes. Where helpful, use OCI descriptors and RO-Crate linked metadata as external compatibility *patterns*; this branch does not claim a standards-conformant OCI or RO-Crate implementation.
- Game-engine sharing works only when both packages can run the same exact versioned runtime with matching ABI/assets/rights. A shorter pointer is not a self-contained offline game unless all required bytes are available locally.
- NASA tools/data and historical Miniclip/Friv capture references remain their respective owners' source records; archive capture is not permission to publish SWF/game assets.

## Public-release gate #158

The existing LS GO site is based on Vite, which copies `public/` files to root static paths. The user-visible Objects UI is **not** an access-control boundary for static resources.

Read-only audit: `python cgx/review/unispace_public_asset_boundary.py`. Its report lists known internal review files without printing their contents. Release-enforcing command: `python cgx/review/unispace_public_asset_boundary.py --strict`, which exits nonzero when those risky paths exist.

Known release holds include:
- `apps/lightspeed-go/public/data/cgx_object_review_catalogue.json`
- `apps/lightspeed-go/public/data/component_geometry_atlas_public_review.json`
- `apps/lightspeed-go/public/review/renders/**`
- `apps/lightspeed-go/public/review/mesh/**`

**Do not whitelist by filename.** Require exact source ownership, licence/IP disclosure clearance, public-safe projection and SHA-256 for each proposed public asset. Internal object/engineering review must be served through the existing permissioned owner backend or omitted from public distribution. Only after removal/migration can the release check pass; it must still be complemented by built `dist/` scanning and unauthenticated/revoked/cross-tenant HTTP 401/403 tests on an actual deployment. A clear static-path scan by itself does NOT close #158.

## Candidate Alexandria kitset packaging
1. **Discovery-only free pack (next first build):** source names/metadata, licences and citations, selected public-safe schemas, text/SVG training modules, static offline search index, source references and local export. No account/network required after the *approved* kit is downloaded. Do not include game binaries or any internal component atlas.
2. **Rights-reviewed functional expansion:** exact source commits and independently verified asset/data licences, bounded pinned dependency graph, repeatable test results and verified offline reopen.
3. **Private UniSpace / lab / field package:** source-owner-authenticated FileSpace and DataSpace with independent rights/scope. Grants, private profiles and keys must not be serialized into public manifests.
4. **Grex specialist:** Eco/Römer/PrintSpace/EMASSC child-domain packages, original physical and scientific evidence and separate jurisdiction/site/regulatory qualifications.

### Acceptance before any public launch
- Current #158 internal static folder blocker removed/rehosted; built output and external no-auth disclosure tests approved.
- #161 real authenticated independent second-node source/State_Root/DBR readback remains separate.
- Public-safe manifest with pinned source and owner-approved SPDX/rights; no private data or external archive/game media without rights.
- Offline kit reopens on supported browsers with zero server requirement and with explicit source provenance.
- Training prompts label explanatory inference and unsolved Frontier separately from reproducible source evidence; no fabricated simulation verification.
- Preservation/rollback: R0 unchanged source data and legacy branches/archives retained.

**This is a staged source review, not a merge to `main`, running paid service, model training, external source download, Vercel deployment, Drive rewrite or local BouwerBase action.**
