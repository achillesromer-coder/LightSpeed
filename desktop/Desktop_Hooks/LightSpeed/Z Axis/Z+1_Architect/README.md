# Architect Floor

**Z-Level:** +1
**Version:** 5.1.2
**Status:** Operational

Architect owns governance, approvals, project planning, publish bundles, Romer reference paths, and finalization queue state.

## Active Entry

- Root coordinator: `Z Axis/Architect.py`
- Floor manifest: `Z Axis/Z+1_Architect/_FLOOR_MANIFEST.json`
- Floor data: `Z Axis/Z+1_Architect/data`
- Primary UI: `components/architect_portal_glass.py`

## Ownership

- Governed publish bundles and package snapshots.
- Execution queues and finalization controls.
- Project planning and approval state.
- Dev/tooling surfaces only where they support governed project work.

Historical floor-local entry code was removed because the live floor loader uses the root coordinator and component files directly.
