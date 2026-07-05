# LightSpeed Clean-Slate Activation Plan

**Goal:** Reset generated desktop state without losing canonical configuration, floor contracts, workbooks, datasets, models, or unresolved historical evidence, then create a compact Neo handoff and wake each configured Ollama floor sequentially.

**Authority:** `C:\LightSpeed_Consolidated` is the live desktop authority. The Git source mirror is `achillesromer-coder/LightSpeed`. Google Drive remains the canonical inter-platform document authority. `D:\.ollama\models` remains the local model store.

**Safety contract:** Historical source roots are not deletion-ready. Project work is quarantined, not deleted. The active SQLite database is copied and checksummed before a transaction clears approved generated tables. Every mutation is recorded in one JSON manifest.

---

## Task 1: Make release-clean paths junction-safe

**Files:**
- Modify: `desktop/LightSpeed_Runtime/lightspeed_runtime/release_clean.py`
- Test: `desktop/Desktop_Hooks/LightSpeed/tests/test_release_clean.py`

1. Add a failing test where `lightspeed_runtime` resolves to the split runtime sibling.
2. Permit only the exact split-runtime cache roots as external cleanup candidates.
3. Keep arbitrary external and reparse-point targets rejected.
4. Run `python -m pytest desktop/Desktop_Hooks/LightSpeed/tests/test_release_clean.py -q`.

## Task 2: Implement the governed clean-slate transaction

**Files:**
- Modify: `desktop/LightSpeed_Runtime/lightspeed_runtime/release_clean.py`
- Test: `desktop/Desktop_Hooks/LightSpeed/tests/test_release_clean.py`

1. Add tests for dry-run, database backup/checksum, approved-table clearing, protected-table retention, project quarantine, cache cleanup, and manifest output.
2. Add `execute_clean_slate(...)` with dry-run as the default.
3. Clear generated content/activity tables, but retain identity/configuration and Z-floor contracts.
4. Quarantine project workspace entries below `_migration/clean_slate/<timestamp>/projects`.
5. Delete only enumerated cache/temp roots after containment validation.
6. Write a single manifest with row counts, paths, byte totals, checksums, and before/after state.

## Task 3: Apply the reset to the live authority

**Files:**
- Create: `_migration/clean_slate/<timestamp>/clean_slate_manifest.json`
- Create: `_migration/clean_slate/<timestamp>/database/lightspeed_unified.db`

1. Stop only the LightSpeed Desktop wrapper and child processes.
2. Run a dry-run and inspect every candidate.
3. Run the guarded mutation once.
4. Verify the backup hash, zeroed operational rows, retained configuration, empty project workspace, and absent approved caches.

## Task 4: Rebuild compact Neo and floor state

**Files:**
- Modify generated runtime exports only through the existing export/build commands.
- Create one activation receipt under the existing Neo handoff location.

1. Regenerate agent-home exports from canonical contracts.
2. Record Git branch/SHA, Drive authority identifiers, database reset manifest, and installed Ollama models in one compact handoff.
3. Create at most two active tasks per floor and preserve existing gates.
4. Do not ingest bulk historical roots or duplicate canonical Drive workbooks.

## Task 5: Wake local floors sequentially

1. Confirm the Ollama endpoint and installed models.
2. Run the existing local floor runner one floor at a time with low output limits and `keep_alive=0`.
3. Skip unavailable/heavy/manual-only floors according to the host policy.
4. Store compact receipts through the existing receipt mechanism; do not create per-token or per-log files.

## Task 6: Verify and publish

1. Run focused release-clean and local-runner tests.
2. Run the full canonical Desktop test suite and launch-readiness checks.
3. Sync source changes into the clean worktree, review the diff, and scan for secrets.
4. Commit and push the bounded source change.
5. Relaunch LightSpeed Desktop and verify the UI, Ollama status, floor contracts, and clean-state counts.
