# Merovingian Floor

**Z-Level:** -4
**Version:** 5.1.2
**Status:** Active smart floor

Merovingian owns core services, databases, storage, logs, compact activity tables,
telemetry, audit evidence, finalization reports, and closure readiness state. The
active UI coordinator is the root floor module `Z Axis/Merovingian.py`; this folder
holds the core service package, diagnostics components, and governed runtime state.

## Canonical Ownership

- `core/services/`: database, event bus, storage, logging, cache, metrics, and Z Direct services.
- `data/db/`: SQLite runtime databases including the compact activity database.
- `data/audit/`: action ledger and compact activity table.
- `data/telemetry/`: OpenTelemetry-compatible span stream.
- `data/runtime_exports/`: finalization, closure, cleanup, and execution reports.
- `data/quality/`: test and quality-report outputs.
- `components/`: system metrics, DB browser, backup, profiling, and recovery surfaces.

## Current Runtime Flow

Other floors perform domain work. Merovingian records proof, activity, telemetry,
quality, and closure state so finalization is queryable without spreading single-use
logs across the app. Trinity owns user/profile setup state; Merovingian owns system
state.

## Reduction Policy

Do not place profile, wizard, or raw archive state in this floor root. Keep root files
to loader metadata, core-service exports, and floor documentation. Store generated
evidence under the relevant `data/` subdirectory.
