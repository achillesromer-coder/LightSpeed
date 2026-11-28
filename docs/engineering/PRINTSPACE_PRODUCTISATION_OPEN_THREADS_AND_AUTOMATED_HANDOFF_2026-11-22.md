# PrintSpace productisation — counted open workstreams and automatic handoff

**Date:** 22 November 2026 (Australia/Brisbane). **Authority:** review-only. Source branch: `review/pc01-raphael-printspace-crosswalk-20261122`, [draft PR #236](https://github.com/achillesromer-coder/LightSpeed/pull/236). This is an additive inventory and deterministic handoff *read model*, not another CGX core, a live FileSpace/DBR writer, or an automation scheduler.

## What is already source-validated

- Private digital demonstrator `PrintSpace Studio 0.1.0-rc.2`: the exact preserved ZIP is **63,404 bytes**, SHA-256 `2f81a22ac0d00e22086d5e3f0d77f3026a4a971f1bb6a4e0267f704efb4911c2`; internal `MANIFEST.json` says `OWNER_PRIVATE_EVALUATION_ONLY` and all public/device/native approval flags false. CI-artifact digest and inner ZIP digest differ because one is an outer GitHub artifact wrapper.
- The last audited PR head before this inventory was `7298fa23f9992e67edffb01ce91edf59367d43c7`. The three associated workflow conclusions were success, including 27/27 serial regression stages. **Historical status, not an attestation of every future commit:** GitHub PR checkouts may use generated merge SHAs, so the runner's checkout SHA may differ from the PR head.
- Single offline Studio, three illustrative diode/board/phone assemblies, seven printer-family roles, three notional environments, 80 symbolic CGX facets and source-bound H0/R0. Existing numerical sweeps (756 hypothetical bed-fit cases, 216 surrogate cases) are NOT physical qualification. T173 mesh admission, genuine digital machine operation, 4D material activation and actual phone manufacturing remain separate evidence gates.
- Existing five hourly staggered CGX coordinator tasks are enabled; Achilles collates results. No sixth scheduler or duplicate agent is authorised. The emergency RDC floor is 24%, normal reserve 25%.

## Exact counted open workstreams — 16 curated release gates

This **is not a claim to have searched every historical workbook or GitHub issue**. The register has 16 *uniquely identified, owner-handoff-relevant gate groups*, split as follows. Each is open pending separately verifiable evidence; none is silently treated as accepted.

| ID | Gate | Responsible existing coordinator | Release dependency |
| --- | --- | --- | --- |
| SW-01 | Owner acceptance of private `rc.2` digital scope | Achilles | Explicit handoff approval |
| SW-02 | Rights, licences, trademark, free/paid reusable asset and recipe grants | Cognigrex | Public software distribution |
| SW-03 | Independent security, privacy and supply-chain threat review | Neo | Public software distribution |
| SW-04 | Accessibility, keyboard/mobile, browser/device and user acceptance | UniSpace | Public software distribution |
| SW-05 | Official publisher signing, installation/download identity and domain | UniSpace | Public software distribution |
| SW-06 | Rollback, support, terms, pricing and operational ownership | Achilles | Public software distribution |
| SW-07 | PR ancestry, #236/#232 source reconciliation and owner merge review | Neo | Final software code-line adoption |
| NATIVE-01 | Native semantic Object_ID, owner rights/ACL and signed DBR | Cognigrex | Native FileSpace admission |
| NATIVE-02 | Owner-authenticated trust roots, revocation and durable one-use nonce ledger | Neo | Real host acceptance |
| NATIVE-03 | Native FileSpace/LOAD resolver and lease-bound private hydration | UniSpace | FileSpace productisation |
| NATIVE-04 | DataSpace and five-facet UniSpace parent topology convergence | Cognigrex | DataSpace/UniSpace productisation |
| PHYS-01 | Source-verified PC01 CAD/kinematics/tool envelope and C0 | Achilles | Physical printer operation |
| PHYS-02 | Material lots and independently witnessed A→B/B→A interface coupons | Athene | Physical compatibility qualification |
| PHYS-03 | Atmospheres, encapsulation and experimentally measured 4D activation | Athene | 4D process qualification |
| PHYS-04 | Semiconductor/electronics, power, RF/EMC and functional phone tests | Neo | Functional printed devices |
| PHYS-05 | Transfer from terrestrial to in-situ scaled environments | Athene | Environmental/space qualification |

**Count:** 7 software + 4 native + 5 physical = **16 open gate groups**. Separately, the Achilles pre-DBR register has **three historical archival-review candidates**, each with zero delete/execute authority, and at least 80 active/protected source/evidence references at the baseline. Those 3 are **not** added to the 16. A broad GitHub issue search returned four related open results (issues #161, #158, #40 and #221); those are overlapping cross-product matters and are **not** four new PrintSpace blockers. The draft PR had zero unresolved inline review threads at inspection; this does not mean there are zero owner decisions.

## Deterministic handoff and read-only autonomous continuation

The single source-of-truth workstream register is `cgx/manufacturing/printspace_product_handoff_v0_1.json`. Every existing coordinator may read it and check its assigned `OPEN_VERIFICATION_OR_APPROVAL` tasks against real source data. It may produce a proposed diff, run bounded tests, compare hashes, create a non-authorising CI receipt, and report to Achilles. **No task can change its status merely because a model, UI, or another agent declared success.** An independently checked owner approval is required to move a gate out of HOLD.

The fixed `scripts/validate_printspace_product_handoff.py` validates the exact 16-group count, original private RC2 digest, canonical product transition sequence, existing coordinator IDs/roles, archive and RDC protections, and the false native/public/hardware authority flags. When provided the exact private RC2 ZIP, it additionally checks byte count, SHA-256, in-archive manifest identity and private-only scope. It emits `PASS_HANDOFF_REGISTER_INVARIANTS_ONLY`: **a source/manifest review receipt, not a signature or DBR authorisation**.

CI usage, after the existing release build:

```bash
python scripts/validate_printspace_product_handoff.py --check \
  --archive "$RUNNER_TEMP/printspace-private-rc/PrintSpace_Software_0.1.0-rc.2_PRIVATE.zip" \
  --emit "$RUNNER_TEMP/cgx-printspace-batch/printspace-product-handoff-review.json"
python -m pytest -q tests/test_printspace_product_handoff.py
```

The bounded 28-stage sequential PrintSpace regression includes the handoff invariant tests. Both the tests and CI hold on changed scope, incorrect counts, fabricated owner acceptance, false public or hardware approval, missing referenced package or archive policy escalation. This remains a source-only artifact.

## Release decision and phases

**Current phase: `PrintSpace PRIVATE_RC_OWNER_EVALUATION`**. The user did not yet explicitly approve `0.1.0-rc.2` for transfer; the prior approval question concerned `rc.1`, now superseded by `rc.2`. Software RC packaging may be considered technically verified when current exact-head CI is green, but **public software release is blocked** by `SW-02`–`SW-06` and owner authorization. Physical claims require the PHYS series independently; they do not block a responsibly labelled digital-only product.

**The next stage is NOT automatically invoked:** after verified owner acceptance of PrintSpace private handoff, FileSpace package preparation may be activated through the existing UniSpace/Cognigrex coordinators. DataSpace follows FileSpace acceptance, UniSpace integrated launch follows both, and Grex outreach follows qualified release evidence. No auto-merge, deployment, mint, native DBR, key creation, signed rights grant, archive move, remote desktop operation, machine command or public promotion occurs from this register.

## Engineering reservations

The test-proven diode/board/phone hierarchy is illustrative. The owner spreadsheet projection contains 411 archetypes with direction-field fingerprints but lacks real material-lot certification. Native T173 geometric mesh/incidence, canonical chirality, atmospheric transitions, electrical functions, energy budgets and true additive/4D print processes must each be validated rather than inferred from synthetic geometry. Protect prior unique versions and external Drive/Git evidence; consolidate references without deleting originals. No new paid/open-use licence is declared here.
