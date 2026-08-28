# Root Classification Map

Status date: 2026-08-28
Purpose: guide mass file movement, reduction, and finalization without mixing source, generated state, archive material, mounted external reservoirs, migration/intake corpora, or canonical owner surfaces.

## Canonical classes

### `source`

Owns live application code, operator docs, and maintained config.

- [lightspeed_runtime](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/lightspeed_runtime)
- [Z Axis](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/Z%20Axis)
- [config](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/config)
- [tests](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/tests)
- [README.md](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/README.md)
- [N.py](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/N.py)
- [__main__.py](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/__main__.py)
- [verify_launch_ready.py](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/verify_launch_ready.py)
- [dataindex](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/dataindex)

### `generated`

Owns runtime outputs, package exports, reports, indexes, and archive execution receipts.

- [Z Axis/Z-2_Oracle/data](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/Z%20Axis/Z-2_Oracle/data)
- [Z Axis/Z0_TheConstruct/data](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/Z%20Axis/Z0_TheConstruct/data)
- [Z Axis/Z+1_Architect/data](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/Z%20Axis/Z+1_Architect/data)
- [Z Axis/Z-3_Smith/data](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/Z%20Axis/Z-3_Smith/data)
- [Z Axis/Z-4_Merovingian/data](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/Z%20Axis/Z-4_Merovingian/data)

Policy:
- Generated files may be replaced or compacted by canonical runtime processes.
- Generated files must not become the source of truth for runtime imports.

### `archive_reference`

Historical, duplicated, or migration-only material kept for comparison until declassified.

- [Z Axis/Z-4_Merovingian/data/legacy_runtime_bundle/canonical_runtime](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/Z%20Axis/Z-4_Merovingian/data/legacy_runtime_bundle/canonical_runtime)
- [ai_logs](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/ai_logs)

Policy:
- May remain mounted/readable.
- Must not be expanded as active runtime ownership.
- Removal only after replacement, diffing, and verification.

### `legacy_support`

Small compatibility paths retained temporarily for loader stability.

- Legacy-runtime dependency alias in [N.py](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/N.py)

Policy:
- Reduce progressively.
- Keep only where live loader compatibility still depends on them.

### `external_migration_intake`

External/cloud source reservoirs used for extraction, reconciliation, package staging and migration. They are not a substitute for the owning Type-1/ACR3/Achilles canon.

- Google Drive `Temporary Drives` ID `1nma8t8pNW7YD8FttBCnoc_0IVsifYMjM`.
- Existing control roots: `CYC/`, `Agents/`, `Logs/`, `Library/`, `ZIP Check/`.

Policy:
- Sweep comprehensively, extraction-first.
- Route unique substantive content into the existing canonical owner and preserve source identity.
- Treat already-assimilated/superseded material as lineage, not current authority.
- Archive/delete only after exact-content/reference/recovery gates.
- Do not describe Temporary Drives as the sole canonical home; it is a migration/intake/finalisation corpus within the federated canon.

## Move policy

1. Move only when the target class and owning canonical destination are already defined and verified.
2. Prefer moving generated outputs into the owning smart-floor data root, not into root legacy shells.
3. Prefer reducing the Merovingian-hosted legacy runtime bundle by diff/reconciliation, not by direct deletion.
4. Do not move mounted external reservoirs into the app root.
5. Keep operator docs in [dataindex](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/dataindex), not mixed into generated output folders.
6. Cloud migration/intake sources are cross-analysed against Drive Type-1 owners, ACR3 and Git lineage before disposition.

## Current blocking items before broader shuffle

1. `oracle_ingest_file` still has `455,345` raw manifests and requires archive execution before deeper pruning.
2. Compatibility aliases around the legacy runtime bundle still exist in the live shell for safety.
3. Provider-held Drive parent mutations remain explicit permission holds; do not create duplicate copies solely to manufacture a clean tree.
4. LightSpeed local installed-shell promotion remains receipt-gated independently of cloud canonical consolidation.

## Safe next move classes

1. Generated report consolidation inside [Z Axis/Z-4_Merovingian/data/runtime_exports](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/Z%20Axis/Z-4_Merovingian/data/runtime_exports)
2. Legacy bundle declassification once the rehomed bundle diff is fully clean
3. Temporary Drives extraction/classification into canonical-owner, source-only, assimilated, superseded, archive and delete-candidate classes
4. Empty/cache cleanup after final reference scans

## 2026-08-28 GST-058 canonical consolidation receipt

Authority: ACR3 GST-058 and LightSpeed PR #38.

- Canonical authority is federated: Achilles P.A + ACR3 + owning Type-1/specialist workbooks; Git is executable/provenance authority within its domain.
- Google Drive `Temporary Drives` ID `1nma8t8pNW7YD8FttBCnoc_0IVsifYMjM` is the comprehensive migration/intake/finalisation corpus, not the sole canon.
- `Achilles.romer@gmail.com` is the owner-supplied Achilles canonical email identity; the connected `hotdogg3211@gmail.com` Nathaniel Bouwer Drive session is an authorised working surface.
- Canonical naming is Römer/Romer. `Roma` is not a Römer Industries/workbook/agent/email alias.
- Existing package-classification destination in Temporary Drives: `ZIP Check` ID `1NwiFmDDKkxBWQV047G7c2A7aM_ANmyz_`.
- Existing archive destination: `Logs/99_Archive` ID `1gilzVeOsBXMBvWcAbOLYd8UZ0zpVriqL`.
- `ACR3_Hotdogg3211_Drive_Alignment_Map_TEMP_TO_ACHILLES_2026_06_24` (`Drive:1XI9VEu5sN72dv2dUHLVXALA02VD2DUOiPyQe8Dnef3E`) was moved in-place to `Logs/99_Archive`; provider readback returned parent `1gilzVeOsBXMBvWcAbOLYd8UZ0zpVriqL`.
- Both `LightSpeed_CL3_Final_Handoff_Set_2026_06_02.zip` objects remain intact and held because Google Drive returned `appNotAuthorizedToFile` for the first move attempt; IDs `1gtUQ39dnZ6nCjxiJ6dqxxdqrTUgXnTXL` and `1O_jQtRfN2o4LPcSAItHMQ5zPkOQ41vGY`.
- Byte-duplicate status does not authorize deletion; retained-copy authority, member-level canonical destination/readback, recovery path, and steward closure remain required.
- GitHub installed identities are `NCNBOUWER` and `achillesromer-coder`; five accessible repositories are Raphael, LightSpeed, Operations, Data and Romer-MPL.

Independent proof: Drive root/Temporary Drives listing, ACR3 current registers and GitHub installation/repository reads were reconciled on 2026-08-28. This receipt records cloud/source topology and does not assert installed-shell execution, empirical validation, publication or deployment.
