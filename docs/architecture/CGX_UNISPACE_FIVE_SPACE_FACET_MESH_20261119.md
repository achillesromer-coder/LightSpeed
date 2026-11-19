# UniSpace: five spaces, one Cognigrex root — source-level facet mesh

**Review candidate:** `CGX-UNISPACE-SINGLE-ROOT-FACET-MESH/0.1`
**Semantic parent:** `cgx:root:cognigrex` / `Cognigrex.cgx`
**Separate physical/install alias:** `C:\UniSpace` may resolve to `C:\CGX` on the owner host; path aliases are not semantic identity or additional stores.

## Implemented

`tools/cgx_unispace_facet_mesh.py` builds a deterministic **read-only source-contract graph** over the existing domain configuration (`domains.json`) and existing Cognigrex parent services (`cognigrex_parent_topology.json`). The five workspace facets are `file_space`, `data_space`, `social_space`, `print_space`, and `intelligence_space`.

Each facet links exact existing parent services and contract files by reference. Shared dependencies resolve **once per unique contract ID** in an immutable source projection; individual Grex semantic owners and agent/model identities are retained. The `plan_facet_projection` API accepts a bounded selection of spaces and only `inspect` or `propose`; it never dispatches, writes, trains, signs, mints, creates databases, or hydrates private source.

The existing read-only `cgx_living_consolidation_review` includes `unispace_space_facets` in its **same existing consolidation receipt**. This is not a new owner shell, native Task_ID scheduler, model supervisor, permanent database, or deployed app.

| Workspace facet | Existing shared services | Existing source contracts | Native action status |
|---|---|---|---|
| FileSpace | identity, CCC | source envelope, conversion, child-domain identity | Hold |
| DataSpace | cross-domain graph | node exchange, execution lease | Hold |
| SocialSpace | agents, representations | notification evidence, source envelope | Hold |
| PrintSpace | representations, technology stack | file conversion, file-type conversion, format adapters | Hold |
| IntelligenceSpace | agents, assurance | agent runtime, corpus simulation and capability, assurance roles | Hold |

## Explicit boundaries

- A present contract **is not** a functioning connector, deployed model, physical printer, social network, agent, or signed peer.
- Models remain independent capabilities behind stable agent IDs and scoped leases. The five *spaces* are not five model weights or five proven resident engines.
- The output does not infer permissions, licences, semantic equivalence or peer custody. `SOURCE_CONTRACTS_PRESENT` means source files exist with checked hashes, not that engines are available.
- A missing, unsafe or untracked required contract holds its facet; invalid parent identity, duplicate services, traversal references, unknown operations, unbounded fanout and inconsistent shared contracts fail closed.
- T173/T174 research, signed two-device exchange, print hardware, smart contracts and national-grid integration, science, safety, independent operator review and public marketing claims retain separate acceptance gates.

## Reproducibility

```bash
python -m pytest tests/test_cgx_unispace_facet_mesh.py -q
python tools/cgx_unispace_facet_mesh.py --repo . --spaces file_space data_space intelligence_space
python tools/cgx_living_consolidation_review.py --repo . --carriers /path/to/observed/carriers
```

The synthetic Git-index tests cover five facets, exact dependency deduplication, deterministic output, missing and untracked contracts, invalid canonical parents, escaped source paths, duplicate services, conflicting shared definitions and prohibited operations.

**Next gate:** Desktop Work reviews the candidate against [native ABI source PR #228](https://github.com/achillesromer-coder/LightSpeed/pull/228), [consolidation PR #230](https://github.com/achillesromer-coder/LightSpeed/pull/230), and [manifest fix PR #231](https://github.com/achillesromer-coder/LightSpeed/pull/231). Only its existing owner-supervised host path may deploy, validate signer/leases or promote product claims.

## Closeout reconciliation — 19 November 2026

- The separate [manifest repair PR #231](https://github.com/achillesromer-coder/LightSpeed/pull/231) is **closed without merge as superseded**. Native [PR #228](https://github.com/achillesromer-coder/LightSpeed/pull/228) now contains the same complete 748-entry `desktop/source-manifest.json` source set and its newer `local_floor_runner.py` hash, as confirmed by independent record-path comparison.
- Current native source head for this reconciliation: `60baabc94d43291187ef1382f18a6a02fc506fa6`. GitHub Actions reported four green native PR workflows at that head. A native CI pass does not constitute live Core installation, licence review or security/lease acceptance.
- Dependency order for this source-only five-space capability mesh remains: owner review of existing consolidation [PR #230](https://github.com/achillesromer-coder/LightSpeed/pull/230), this draft PR #232, and reconciliation with the continuously evolving native #228 (not the now-retired #231). No merge/deployment was performed by this note.
