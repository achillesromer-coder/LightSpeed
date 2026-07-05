# Master Build Spec Sheet

Date: 2026-04-08
Status: Current compact architecture baseline

This file is the intended-state summary for LightSpeed after the Z-axis consolidation pass. Generated directory maps, stale AI-log tables, and old root-layout audits were removed from `dataindex/` because their content is now represented by runtime reports under Merovingian and the current maps in this folder.

## Canonical Launch Model

- `N.py` is the canonical desktop shell.
- `__main__.py` is only a thin compatibility wrapper for `python -m LightSpeed` and legacy flags.
- `LAUNCH_GUI.bat` is only a thin Windows launcher delegating to `__main__.py`.
- `verify_launch_ready.py` remains the explicit launch-readiness verifier.

## Z-Axis Ownership

- Trinity owns the workspace shell, portal settings, UI polish contracts, and operator-facing bento experience.
- Neo owns the Achilles/Cognigrex operator bridge and approval-aware AI action proposals.
- Architect owns governance, execution queues, approvals, Romer publishing, and package control.
- TheConstruct owns simulation, holospace, heliocentric zoning, and lab presets.
- Morpheus owns review/proofing surfaces and knowledge inspection.
- Oracle owns knowns, definition library, catalog, datatables, ingestion, empirical sources, and provenance.
- Smith owns routing, workflows, background jobs, and floor coordination.
- Merovingian owns database, storage, runtime exports, logs, telemetry, activity tables, quality reports, and finalization state.

## Data And Log Policy

- `data/generated/` must remain absent.
- Raw archives and absorbed external sources are not primary UI surfaces; they are mounted/reference/provenance material.
- Compact operator state lives in Z-axis-owned tables and reports:
  - `Z Axis/Z-4_Merovingian/data/audit/activity_tables.json`
  - `Z Axis/Z-4_Merovingian/data/db/lightspeed_activity.db`
  - `Z Axis/Z-4_Merovingian/data/runtime_exports/finalization_overview.json`
  - `Z Axis/Z+1_Architect/data/finalization/execution_control.json`
  - `Z Axis/Z+1_Architect/data/finalization/execution_queues.json`
- Append-only JSONL ledgers remain audit evidence, not primary browsing surfaces.

## Scientific Workflow

- Oracle catalogs and validates empirical datasets.
- TheConstruct consumes curated/clusterable inputs for heliocentric zoning and scenario presets.
- Architect packages validated runs and publishable artifacts.
- Neo proposes bounded actions through Achilles; write, execute, and publish actions remain approval-gated.
- Merovingian records the runtime evidence and cross-floor activity table.

## Active Reference Files

- `README.md`: operator baseline and launch status.
- `dataindex/04_Z_AXIS_CANONICAL_MAP.md`: current Z-axis map.
- `dataindex/07_ROOT_CLASSIFICATION_MAP.md`: root classification policy.
- `dataindex/08_SMART_FLOOR_ASSIMILATION.md`: assimilation policy.
- `dataindex/09_FILE_OPTIMIZATION_MAP.md`: file-by-file optimization log for the finalization pass.

## Validation Baseline

- `tests/test_runtime_package.py`: 64/64 passing.
- `python N.py --smoke`: 8/8 canonical floors initialized.
- Architect execution queue: 81/81 complete.
