# Root Classification Map

Status date: 2026-04-04
Purpose: guide mass file movement, reduction, and finalization without mixing source, generated state, archive material, and mounted external reservoirs.

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

## Move policy

1. Move only when the target class is already defined and verified.
2. Prefer moving generated outputs into the owning smart-floor data root, not into root legacy shells.
3. Prefer reducing the Merovingian-hosted legacy runtime bundle by diff/reconciliation, not by direct deletion.
4. Do not move mounted external reservoirs into the app root.
5. Keep operator docs in [dataindex](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/dataindex), not mixed into generated output folders.

## Current blocking items before broader shuffle

1. `oracle_ingest_file` still has `455,345` raw manifests and requires archive execution before deeper pruning.
2. Compatibility aliases around the legacy runtime bundle still exist in the live shell for safety.

## Safe next move classes

1. Generated report consolidation inside [Z Axis/Z-4_Merovingian/data/runtime_exports](/C:/Users/acc/Desktop/LightSpeed%20Consolidated/LightSpeed/Z%20Axis/Z-4_Merovingian/data/runtime_exports)
2. Legacy bundle declassification once the rehomed bundle diff is fully clean
3. Empty/cache cleanup after final reference scans
