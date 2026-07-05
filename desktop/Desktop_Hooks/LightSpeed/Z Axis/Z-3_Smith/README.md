# Smith Floor

**Z-Level:** -3
**Version:** 5.1.2
**Status:** Active smart floor

Smith owns job routing, bounded tool execution, background work, resumable workflow
state, and cross-floor coordination. The active UI coordinator is the root floor
module `Z Axis/Smith.py`; this folder holds Smith components and operations state.

## Canonical Ownership

- `data/operations/smith_router.json`: routed job/action queue state.
- `data/operations/workflow_state.json`: resumable workflow state.
- `components/smith_task_queue.py`: queue and quota surface.
- `components/smith_interfloor_coordinator.py`: cross-floor routing surface.
- `components/workflow_scheduler.py`: scheduled workflow surface.
- `components/workflow_debugger.py`: workflow inspection surface.
- `components/workflow_versioning.py`: workflow history and diff surface.

## Current Runtime Flow

Neo and TheConstruct propose bounded work. Oracle and Morpheus supply proofed
context. Smith stages and routes jobs, then Merovingian records audit/activity
evidence and Architect governs write/execute/publish approval where required.

## Reduction Policy

Do not add floor-local duplicate launchers here. Keep orchestration in the runtime
and root coordinator, and keep floor-local files focused on queueing, scheduling,
workflow state, and bounded execution.
