# Completed Release and Publish Cull Pass

Worker completed the following 5 release/finalization tasks:

1. Added launch-state and setup-state cleanup planning for blank release prep, dry-run only.
2. Added overwrite-only publish snapshot planning that preserves the live C-root source and rejects unsafe destinations.
3. Added stale user, project, company, and preference runtime row cleanup planning after proof runs, dry-run only.
4. Added generated cache and temp cleanup planning after validation cycles, dry-run only and path-guarded.
5. Added duplicate surface audit descriptors for remaining settings, theme, wizard, and popup entrypoints to cull later.

## Verification

- `python -m py_compile lightspeed_runtime\\release_clean.py lightspeed_runtime\\publish_snapshot.py tests\\test_release_clean.py tests\\test_publish_snapshot.py`
- `python -m pytest tests\\test_release_clean.py tests\\test_publish_snapshot.py -q`
- `python -m pytest tests -q`
- `python verify_launch_ready.py`

## Notes

- All cleanup and publish routines remain dry-run or planning only.
- No protected live source paths are mutated by the new publish snapshot planner.
- The duplicate surface audit is descriptive only and intended for later cull work.
