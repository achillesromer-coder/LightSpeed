# UniSpace — one-root cross-space gate reconciliation (22 November 2026)

**Status:** `SOURCE_REVIEW_ONLY_51_TASKS_OPEN`; private review, **not** native admission, an approved public launch, automated branch merging or an archive/delete authority.

## Scope and source provenance

This is an additive reconciliation layer for the *existing* five-facet mesh in `tools/cgx_unispace_facet_mesh.py`, not a second root, scheduler, database or UI. It consumes the original cross-conversation handoff ZIP SHA-256 `634695accc767f7a25e41e10335cc8b7a6c7f988cbaf4b024e700c92e1d522fa` and exposes the 51 curated task groups in `cgx/review/unispace_crossspace_gate_register_v0_1.json`.

The source checkpoint remains an **observed historical snapshot**. Its 16 PrintSpace tasks retain `OPEN_SOURCE_VERIFIED` provenance (meaning registered and *open*, not completed); the 35 cross-space groups retain `PROPOSED_NEEDS_CURRENT_SOURCE_RECONCILIATION`. Proposed review dependencies are advisory, not native task/agent allocations, and have no execution capability. PrintSpace's 16 labels are restored from its canonical `cgx/manufacturing/printspace_product_handoff_v0_1.json` instead of treating empty handoff labels as real missing tasks.

| Work domain | Open groups | Review class |
| --- | ---: | --- |
| PrintSpace | 16 | Registered source-open gates |
| FileSpace | 6 | Source-reconciliation candidates |
| DataSpace | 6 | Source-reconciliation candidates |
| SocialSpace | 6 | Source-reconciliation candidates |
| IntelligenceSpace | 6 | Source-reconciliation candidates |
| UniSpace operations / launch | 7 | Source-reconciliation candidates |
| Legacy / archive | 4 | Source-reconciliation candidates |
| **Total** | **51** | All still open |

## One canonical dependency plane

`cgx:root:cognigrex` remains the sole semantic root. The five facets are `file_space`, `data_space`, `social_space`, `print_space`, and `intelligence_space`; `ProfileSpace` and `SystemSpace` are only GUI projections. The review reads the **existing** `CGX-UNISPACE-SINGLE-ROOT-FACET-MESH/0.1` output for its real source parent identity, five exact facets, 12 unique source contracts and seven shared parent services. No model, printhead, private file or native agent is loaded or acted upon.

The small deterministic validator (`tools/cgx_unispace_crossspace_review.py`) requires an exact source SHA-256 for the register, verifies all 51 IDs, count boundaries, source evidence classes, proposed acyclic dependency graph, parent namespace and all-deny permission flags. It requires the existing facet mesh to report SOURCE_CONTRACTS_PRESENT with no native authority. Errors produce `HOLD` and a nonzero exit status. A success produces **only** a read-only source receipt.

Eight proposed review roots have no predecessors in the **proposed** graph: `SW-01`, `SW-02`, `FS-01`, `DS-02`, `SS-01`, `IM-01`, `US-01` and `AR-01`. These are starting points for evidence gathering, **not automatic authorisations to execute, close or publish them**.

## Source anchors verified for this handoff

- PrintSpace [PR #236](https://github.com/achillesromer-coder/LightSpeed/pull/236), observed head `399b0c8721225bc82c0fa275d46e3b175fd5b9eb`, private `0.1.0-rc.2` and 29-stage review; 16 source-registered open gates; 89 protected source and evidence references and three distinct unexecuted archive candidates.
- UniSpace [PR #232](https://github.com/achillesromer-coder/LightSpeed/pull/232), previous head `b61519d09e009a223e6c0c2bec1b3414c3f1d5c0`; draft five-facet source contracts, native hold.
- Parent catalogue [PR #230](https://github.com/achillesromer-coder/LightSpeed/pull/230), native [PR #228](https://github.com/achillesromer-coder/LightSpeed/pull/228), LOAD [PR #205](https://github.com/achillesromer-coder/LightSpeed/pull/205), mobile [PR #229](https://github.com/achillesromer-coder/LightSpeed/pull/229), all remain review candidates and cannot be automatically merged or deployed.
- Historical single-shell [PR #235](https://github.com/achillesromer-coder/LightSpeed/pull/235) is closed **without merge**, not proof its assets are deletable.
- SocialSpace source: Achilles Drive document `UniSpace SocialSpace Integration Handoff 2026-11-01`, with explicit opt-in, independent two-principal identity/consent, AI-free and no-AI-contact server-side enforcement. Not a native social-network endpoint.

The registry's observed PR heads are **historical source pins**, not an authenticated live GitHub/host readback. The exact current GitHub CI for this PR establishes only the review branch state and cannot accept an external owner-rights or native DBR assertion.

## Recommended batches and holds

**Batch A — reconcile source and rights:** FS-01 canonical source envelope/licence/ID; SW-02 PrintSpace product rights; US-01 existing PR ancestry and source identity. Require exact Git/Drive evidence plus independent source rights.

**Batch B — security and persistence:** DS-02 trust and nonce ledger; FS-03 private hydration/ACL negative test; US-03 private/public release boundaries; SocialSpace bilateral opt-in and AI contact denial. Source-only tests may proceed; live acceptance needs authenticated host authority.

**Batch C — reproducible software UAT:** PrintSpace SW-03/04, FileSpace FS-02/06 and DataSpace DS-06, then UniSpace UI regression. Independent UAT and owner acceptance still required.

**Batch D — gated integration:** reconcile PR #230/#232/#228/#205/#236 only after parent/source/rights/lease acceptance; stage UniSpace offline build, release signing and rollback for independent review. Never assume that a passing CI constitutes native admission.

**Batch E — archival review only:** AR-01..04 require exact source path and SHA-256, rights, dependent imports/consumers, restore proof, immutable history custody and owner approval *per target*. The three original PrintSpace archival candidates remain unexecuted; automated deletion is refused. Do not purge conversation sources, Google Drive, Git history, disabled legacy tasks or private host data based on their names.

## Reproducible validation

```bash
python -m pytest -q tests/test_cgx_unispace_crossspace_review.py
python tools/cgx_unispace_facet_mesh.py --repo . > facet-source-review.json
python tools/cgx_unispace_crossspace_review.py --repo . \
  --mesh-json facet-source-review.json --out crossspace-source-review.json
```

The read-only regression checks wrong root, altered checkpoint bytes, privilege escalation, changes to source class, duplicated or missing task IDs, cycles, unknown dependencies, unobserved contracts, and falsified native facet permissions. Outputs are source-only receipts; no private source was ingested, no owner DBR changed and no automated promotion occurred.

**Coordinator routing:** reuse the existing five hourly lanes unchanged: Achilles (governance), Neo (host/engineering), Athene (science/ethics), Cognigrex (identity/rights), UniSpace (product UX). Do not create a new root/daemon or promise work outside those established schedules. Remote Desktop Commander normal reserve 25%, emergency floor 24%; no RDC use in this increment.
