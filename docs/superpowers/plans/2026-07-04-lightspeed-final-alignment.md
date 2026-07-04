# LightSpeed Final Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate LightSpeed Desktop into one tested Trinity IT shell, stop runaway generated-file growth, establish compact Neo/floor persistence in Drive, preserve the approved C-root runtime, and publish source-only Desktop/GO/Web integration through the canonical GitHub repository.

**Architecture:** `C:\LightSpeed_Consolidated` remains the local runtime authority and `D:\LightSpeed_Consolidated` remains compatibility junctions only. SQLite holds machine state, bounded weekly JSONL holds recovery evidence, Raphael-styled workbooks provide human review, Drive holds approved inter-platform knowledge, and Git holds source, schemas, manifests, and public-safe queue summaries. Runtime Desktop never invokes Git; Neo reconciles Drive/local state through explicit manifests.

**Tech Stack:** Python 3.11, Tkinter, SQLite, openpyxl, pytest, TypeScript, Vite, Google Drive/Sheets, GitHub, PyInstaller, Windows Task Scheduler.

---

## Authority And Safety Invariants

- Canonical local root: `C:\LightSpeed_Consolidated`.
- Compatibility root: `D:\LightSpeed_Consolidated`, junctions only.
- Canonical Desktop entry: `Desktop_Hooks\LightSpeed\launcher_exe.py -> __main__.py -> N.py`.
- Canonical Git remote: `https://github.com/achillesromer-coder/LightSpeed.git`.
- Historical Git remote: `https://github.com/NCNBOUWER/LightSpeed.git`, reference only.
- Empirical source files, model weights, SQLite databases, virtual environments, generated logs, and secrets never enter Git.
- The Construct remains Desktop-bound and does not receive a Drive memory workbook.
- Neo uses `N. LightSpeed`; persistent floor workbooks are Trinity, Architect, Morpheus, Oracle, Smith, and Merovingian.
- Achilles and Athene remain under LS GO; Athene receives public-approved material only.
- Restricted material never enters public Git or Athene.
- Generated-file cleanup quarantines first and requires a manifest, checksum, classification, and second recoverable copy.

## Task 1: Source Boundary And Synchronization Contract

**Files:**
- Create: `tools/sync_desktop_source.py`
- Create: `tools/source_allowlist.json`
- Create: `tests/test_sync_desktop_source.py`
- Create: `desktop/README.md`
- Create: `docs/architecture/LIGHTSPEED_AUTHORITY_MAP.md`
- Modify: `.gitignore`

- [ ] **Step 1: Write the failing source-boundary tests**

```python
def test_manifest_rejects_runtime_data(tmp_path):
    from sync_desktop_source import validate_relative_path

    assert validate_relative_path("Desktop_Hooks/LightSpeed/N.py")
    assert not validate_relative_path("Desktop_Hooks/LightSpeed/data/runtime.db")
    assert not validate_relative_path("Desktop_Hooks/LightSpeed/Z Axis/Z-2_Oracle/Data/source.fits")


def test_sync_uses_hashes_and_does_not_copy_unchanged_files(tmp_path):
    from sync_desktop_source import sync_sources

    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "N.py").write_text("print('ok')\n", encoding="utf-8")
    first = sync_sources(source, target, ["N.py"])
    second = sync_sources(source, target, ["N.py"])
    assert first["copied"] == 1
    assert second["copied"] == 0
    assert second["unchanged"] == 1
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe -m pytest tests\test_sync_desktop_source.py -q
```

Expected: import failure because `sync_desktop_source` does not exist.

- [ ] **Step 3: Implement the allowlisted synchronizer**

```python
BLOCKED_PARTS = {
    "data", "archive", "ai_logs", "__pycache__", ".pytest_cache",
    "node_modules", "reservoirs", "vault", "venv",
}


def validate_relative_path(value: str) -> bool:
    path = PurePosixPath(value.replace("\\", "/"))
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and not any(part.lower() in BLOCKED_PARTS for part in path.parts)
    )


def sync_sources(source_root: Path, target_root: Path, paths: list[str]) -> dict[str, object]:
    copied = unchanged = 0
    records = []
    for relative in paths:
        if not validate_relative_path(relative):
            raise ValueError(f"blocked source path: {relative}")
        source = source_root / relative
        target = target_root / relative
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == digest:
            unchanged += 1
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied += 1
        records.append({"path": relative, "sha256": digest, "bytes": source.stat().st_size})
    return {"copied": copied, "unchanged": unchanged, "records": records}
```

- [ ] **Step 4: Sync only active source/config/tests/docs**

The allowlist must include:

```json
{
  "roots": [
    "Desktop_Hooks/LightSpeed/N.py",
    "Desktop_Hooks/LightSpeed/__main__.py",
    "Desktop_Hooks/LightSpeed/launcher_exe.py",
    "Desktop_Hooks/LightSpeed/verify_launch_ready.py",
    "Desktop_Hooks/LightSpeed/config",
    "Desktop_Hooks/LightSpeed/tests",
    "Desktop_Hooks/LightSpeed/dataindex",
    "LightSpeed_Runtime/lightspeed_runtime"
  ],
  "extensions": [".py", ".json", ".yaml", ".yml", ".toml", ".md", ".ini", ".cfg"]
}
```

Z-floor source is added by explicit file list after secret/restricted classification; no recursive `Data`, `archive`, `legacy`, `reservoirs`, or `vault` copy is permitted.

- [ ] **Step 5: Verify GREEN and commit**

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe -m pytest tests\test_sync_desktop_source.py -q
git add .gitignore desktop docs/architecture tools tests
git commit -m "Define Desktop source boundary"
```

## Task 2: Compact Operational Persistence

**Files:**
- Create: `LightSpeed_Runtime/lightspeed_runtime/operational_store.py`
- Create: `LightSpeed_Runtime/lightspeed_runtime/maintenance.py`
- Create: `Desktop_Hooks/LightSpeed/tests/test_operational_store.py`
- Create: `Desktop_Hooks/LightSpeed/tests/test_weekly_maintenance.py`
- Modify: `LightSpeed_Runtime/lightspeed_runtime/governance_ledgers.py`
- Modify: `LightSpeed_Runtime/lightspeed_runtime/telemetry.py`
- Modify: `LightSpeed_Runtime/lightspeed_runtime/log_ledger_export.py`
- Modify: `Desktop_Hooks/LightSpeed/Z Axis/Z-4_Merovingian/core/services/dataspace.py`
- Modify: `Desktop_Hooks/LightSpeed/config/archives_policy.yaml`

- [ ] **Step 1: Write failing SQLite ledger tests**

```python
def test_store_deduplicates_idempotent_events(tmp_path):
    store = OperationalStore(tmp_path / "runtime.db")
    event = {"event_id": "evt-1", "kind": "handoff", "payload": {"task": "T-1"}}
    assert store.record_event(event)["inserted"] is True
    assert store.record_event(event)["inserted"] is False
    assert store.count("operational_events") == 1


def test_store_counts_duplicate_attempts_without_new_rows(tmp_path):
    store = OperationalStore(tmp_path / "runtime.db")
    store.record_event({"event_id": "evt-1", "kind": "handoff", "payload": {}})
    duplicate = store.record_event({"event_id": "evt-1", "kind": "handoff", "payload": {}})
    assert duplicate["duplicate_count"] == 1
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe -m pytest Desktop_Hooks\LightSpeed\tests\test_operational_store.py -q
```

Expected: import failure because `operational_store` does not exist.

- [ ] **Step 3: Implement the operational tables**

```sql
CREATE TABLE IF NOT EXISTS operational_events (
    event_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    source TEXT,
    target TEXT,
    project_id TEXT,
    priority TEXT,
    risk TEXT,
    status TEXT,
    payload_json TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    created_utc TEXT NOT NULL,
    updated_utc TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_operational_events_status
    ON operational_events(status, priority, updated_utc);
```

Use `INSERT ... ON CONFLICT(event_id) DO UPDATE SET duplicate_count = duplicate_count + 1`.

- [ ] **Step 4: Route producers to SQLite**

- `ZDirectService` records event/object/message transitions once in SQLite.
- `append_channel_inbox` and `append_channel_outbox` return stable receipt paths but do not mirror byte-identical JSONL records.
- Governance and telemetry write SQLite rows.
- Weekly JSONL receives only approval, failure, blocked, publish, maintenance, and recovery events.
- Stable `*_latest.json` files are atomically replaced using a temporary file and `Path.replace`.

- [ ] **Step 5: Write failing Friday-maintenance tests**

```python
def test_maintenance_quarantines_generated_duplicates_only(tmp_path):
    source = tmp_path / "Data" / "empirical.fits"
    generated = tmp_path / "reports" / "run_20260701.json"
    source.parent.mkdir(parents=True)
    generated.parent.mkdir(parents=True)
    source.write_bytes(b"source")
    generated.write_text("{}\n", encoding="utf-8")

    result = run_maintenance(tmp_path, now=datetime(2026, 7, 10, 19, 0))

    assert source.exists()
    assert not generated.exists()
    assert result["quarantined"] == 1
    assert result["manifest_path"].exists()
```

- [ ] **Step 6: Implement governed weekly maintenance**

Maintenance must:

1. Require Friday at or after 19:00 unless `force=True`.
2. Exclude empirical, source, reservoir, vault, workbook, model, and database files.
3. Classify candidates using explicit globs and producer ownership.
4. Hash every candidate.
5. Move candidates into `C:\LightSpeed_Consolidated\_migration\weekly_quarantine\<ISO-week>`.
6. Write one JSON manifest and append one weekly-log summary.
7. Retain four weekly quarantines and delete older quarantines only when their manifest reports a verified second copy.

- [ ] **Step 7: Export one human ledger**

`LightSpeed_Operational_Log_Ledger.xlsx` must contain:

- `Overview`
- `Tasks`
- `Handoffs`
- `Approvals`
- `Receipts`
- `Exceptions`
- `Daily Log`

It is a projection from SQLite and bounded weekly JSONL, never an independent authority.

- [ ] **Step 8: Verify and commit**

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe -m pytest `
  Desktop_Hooks\LightSpeed\tests\test_operational_store.py `
  Desktop_Hooks\LightSpeed\tests\test_weekly_maintenance.py -q
git add LightSpeed_Runtime Desktop_Hooks/LightSpeed
git commit -m "Compact operational persistence"
```

## Task 3: Trinity IT Shell Consolidation

**Files:**
- Create: `Desktop_Hooks/LightSpeed/Z Axis/Z+3_Trinity/ui/shell_routes.py`
- Create: `Desktop_Hooks/LightSpeed/Z Axis/Z+3_Trinity/ui/it_shell.py`
- Create: `Desktop_Hooks/LightSpeed/Z Axis/Z+3_Trinity/ui/floor_selector.py`
- Create: `Desktop_Hooks/LightSpeed/Z Axis/Z+3_Trinity/ui/achilles_dock.py`
- Create: `Desktop_Hooks/LightSpeed/Z Axis/Z-1_Morpheus/components/comparison_workspace.py`
- Create: `Desktop_Hooks/LightSpeed/tests/test_shell_routes.py`
- Create: `Desktop_Hooks/LightSpeed/tests/test_entrypoint_contract.py`
- Modify: `Desktop_Hooks/LightSpeed/N.py`
- Modify: `Desktop_Hooks/LightSpeed/__main__.py`
- Modify: `Desktop_Hooks/LightSpeed/Z Axis/Z+3_Trinity/ui/it_portal.py`
- Modify: `Desktop_Hooks/LightSpeed/Z Axis/Trinity.py`
- Modify: `Desktop_Hooks/LightSpeed/Z Axis/Morpheus.py`
- Modify: `Desktop_Hooks/LightSpeed/tests/test_z_axis_floors.py`

- [ ] **Step 1: Write failing route-state tests**

```python
def test_shell_has_one_mode_floor_context_tuple():
    state = ShellState()
    state.transition(mode="operator", active_floor="Oracle", workspace_context="P-17")
    assert state.snapshot() == {
        "mode": "operator",
        "active_floor": "Oracle",
        "workspace_context": "P-17",
    }


def test_holospace_requires_explicit_route():
    router = ShellRouter(clearance=5)
    assert router.default_route().mode == "workspace"
    assert router.resolve("holospace").mode == "holospace"
```

- [ ] **Step 2: Verify RED**

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe -m pytest Desktop_Hooks\LightSpeed\tests\test_shell_routes.py -q
```

- [ ] **Step 3: Implement the six shell modes**

```python
SHELL_MODES = ("workspace", "operator", "review", "publish", "settings", "holospace")


@dataclass
class ShellState:
    mode: str = "workspace"
    active_floor: str = "Trinity"
    workspace_context: str = ""

    def transition(self, *, mode: str, active_floor: str, workspace_context: str) -> None:
        if mode not in SHELL_MODES:
            raise ValueError(f"unknown shell mode: {mode}")
        self.mode = mode
        self.active_floor = active_floor
        self.workspace_context = workspace_context
```

- [ ] **Step 4: Embed IT Portal**

- `open_it_portal` renders `ITShell` inside the existing `LightSpeedUnified.content_frame`.
- `ITPortal` remains a compatibility facade and must not create a `Toplevel`.
- One floor selector changes `active_floor`; it does not open new windows.
- Dashboard opens the Universal Bento frame.
- Achilles is one persistent dock with current project/artifact/floor context.
- Review mode embeds the Morpheus comparison workspace.
- Holospace is explicit and lazy.

- [ ] **Step 5: Correct readiness and entrypoint contracts**

```python
def _trinity_ui_surface_available() -> bool:
    return (LIGHTSPEED_ROOT / "Z Axis" / "Z+3_Trinity" / "ui" / "it_shell.py").is_file()
```

`test_entrypoint_contract.py` must assert:

```python
assert launcher_target.name == "__main__.py"
assert "__main__" in launcher_source
assert "from N import main" in entrypoint_source
assert "_analysis_remote" not in entrypoint_source
```

- [ ] **Step 6: Verify UI contracts and commit**

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe -m pytest `
  Desktop_Hooks\LightSpeed\tests\test_shell_routes.py `
  Desktop_Hooks\LightSpeed\tests\test_entrypoint_contract.py `
  Desktop_Hooks\LightSpeed\tests\test_z_axis_floors.py -q
git add Desktop_Hooks/LightSpeed
git commit -m "Consolidate Trinity IT shell"
```

## Task 4: Raphael-Style Agent Workbooks And Drive Landing Files

**Files:**
- Create: `tools/build_agent_workbooks.py`
- Create: `tests/test_build_agent_workbooks.py`
- Create: `drive/landings/N_LIGHTSPEED_README.md`
- Create: `drive/landings/TRINITY_README.md`
- Create: `drive/landings/ARCHITECT_README.md`
- Create: `drive/landings/MORPHEUS_README.md`
- Create: `drive/landings/ORACLE_README.md`
- Create: `drive/landings/SMITH_README.md`
- Create: `drive/landings/MEROVINGIAN_README.md`
- Create: `drive/manifest/drive_targets.json`

- [ ] **Step 1: Write failing workbook tests**

```python
def test_neo_workbook_has_approved_tabs(tmp_path):
    path = build_neo_workbook(tmp_path / "N_LightSpeed.xlsx", records=[])
    workbook = load_workbook(path, data_only=False)
    assert workbook.sheetnames == [
        "00 Dashboard", "01 Index", "02 Floor Registry", "03 Projects",
        "04 Quick Knowns", "05 Open Tasks", "06 Handoffs", "07 Approvals",
        "08 Sync Receipts", "09 Exceptions", "10 Human Review",
        "11 Aesthetic Lock", "12 Daily Log", "13 Legend",
    ]


def test_floor_workbook_uses_raphael_classification_palette(tmp_path):
    path = build_floor_workbook(tmp_path / "Oracle.xlsx", floor="Oracle", records=[])
    workbook = load_workbook(path)
    legend = workbook["12 Legend"]
    colors = {legend.cell(row=row, column=2).fill.fgColor.rgb for row in range(5, 10)}
    assert {"FFB7FF59", "FF3FA65B", "FFF2C94C", "FF5A2A4A", "FFD66A6A"} <= colors
```

- [ ] **Step 2: Verify RED**

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe -m pytest tests\test_build_agent_workbooks.py -q
```

- [ ] **Step 3: Implement workbooks**

Use:

- Garamond 18–22 pt titles, 12 pt subtitles, 11 pt headers, 10 pt wrapped body.
- Teal `#156162`, secondary `#235160`, charcoal `#0A0C0B`, cream `#F7F3E8`, gold `#C9A24A`.
- Known `#B7FF59`, Derived `#3FA65B`, Hypothesis `#F2C94C`, Conceptual Model `#5A2A4A`, Requires Validation `#D66A6A`.
- Merged title/subtitle rows 1–2, navigation row 3, headers row 4, data row 5, `A5` freeze, filters, landscape print.
- Hyperlinked index cells, one owning floor per fact, and cross-floor links instead of duplicate rows.

Required flexible columns:

```python
CORE_COLUMNS = [
    "Item_ID", "Workstream", "Artifact", "Input_Source", "Local_Path",
    "Drive_URL", "Release_Class", "Claim_Grade", "Status", "Completion",
    "Owner", "Last_Review_UTC", "Next_Action", "Evidence_Notes",
]
```

Additional columns are allowed; missing optional fields remain blank.

- [ ] **Step 4: Populate from governed sources**

Extract:

- Instruction-kit AGENT files and CORE controls.
- Existing CORE task/register rows.
- Current local floor manifests and contracts.
- Approved/manual-reviewed Raphael classifications.
- Existing Drive links and local anchors.

Do not copy full document bodies into every workbook. Store one owner row plus source link, digest, classification, status, and next action.

- [ ] **Step 5: Upload and verify**

Targets:

- `N. LightSpeed`: Neo landing + Neo workbook.
- `LS Desktop Agents/Trinity`
- `LS Desktop Agents/Architect`
- `LS Desktop Agents/Morpheous` (preserve existing folder spelling)
- `LS Desktop Agents/Oracle`
- `LS Desktop Agents/Smith`
- `LS Desktop Agents/Merovingian`
- `LS Neo`, `LS Web`, and `LS GO`: operational exchange landing/workbook projections only.

Use native Google Sheets conversion for the workbooks and preserve exact target parents. Re-read each target folder after upload.

- [ ] **Step 6: Commit**

```powershell
git add tools tests drive
git commit -m "Build compact agent workbooks"
```

## Task 5: Historical Tree Consolidation

**Files:**
- Create: `tools/inventory_lightspeed_roots.py`
- Create: `tests/test_inventory_lightspeed_roots.py`
- Create: `docs/migration/LIGHTSPEED_SOURCE_EXTRACTION_REGISTER.md`
- Create: `data/migration/source_roots.json`

- [ ] **Step 1: Write failing classification tests**

```python
def test_root_classification_preserves_newer_unique_files(tmp_path):
    result = classify_file(
        path=tmp_path / "N_updated.py",
        canonical_hashes=set(),
        modified_utc="2025-11-14T10:46:19Z",
    )
    assert result.action == "extract_candidate"


def test_identical_file_is_not_copied_again(tmp_path):
    digest = "abc"
    result = classify_file(
        path=tmp_path / "duplicate.md",
        canonical_hashes={digest},
        digest=digest,
    )
    assert result.action == "reference_existing"
```

- [ ] **Step 2: Inventory the physical source roots**

Inventory without following junctions:

- `C:\Cognigrex\LightSpeed Consolidated`
- `C:\Users\acc\Desktop\LightSpeed Consolidated`
- `C:\LightSpeed_Isolated`
- `C:\Users\acc\Desktop\EMC^2; LightSpeed`
- `C:\Users\acc\Desktop\EMC^^2; LightSpeed`

Record path, size, modified time, SHA-256, duplicate group, source classification, proposed owner, and action.

- [ ] **Step 3: Extract unique code/docs**

- Move nothing directly into the runtime.
- Copy unique candidates into `C:\LightSpeed_Consolidated\Sources\Historical LightSpeed`.
- Preserve relative source root and checksum.
- Promote code only through review and tests.
- Replace finalized duplicate source roots with a compact receipt only after verified extraction and two-copy evidence.

- [ ] **Step 4: Verify and commit**

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe -m pytest tests\test_inventory_lightspeed_roots.py -q
git add tools tests docs/migration data/migration
git commit -m "Register historical LightSpeed sources"
```

## Task 6: LS GO/Web Neo Exchange And Publication

**Files:**
- Create: `apps/lightspeed-go/src/neoExchange.ts`
- Create: `apps/lightspeed-go/src/neoExchange.test.ts`
- Create: `apps/lightspeed-go/public/data/neo_exchange.json`
- Modify: `apps/lightspeed-go/src/main.ts`
- Modify: `apps/lightspeed-go/src/styles.css`
- Modify: `apps/lightspeed-go/package.json`
- Create: `docs/integration/NEO_EXCHANGE_CONTRACT.md`

- [ ] **Step 1: Write failing queue-normalization tests**

```typescript
it("accepts minimal and extended queue records", () => {
  expect(normalizeQueueRecord({ id: "T-1", title: "Review" }).id).toBe("T-1");
  expect(
    normalizeQueueRecord({
      id: "T-2",
      title: "Publish",
      priority: "critical",
      extensions: { icon: "warning" },
      notes: "Owner review required",
    }).extensions.icon,
  ).toBe("warning");
});
```

- [ ] **Step 2: Verify RED**

```powershell
npm test -- --run
```

Expected: import failure because `neoExchange.ts` does not exist.

- [ ] **Step 3: Implement public-safe exchange projection**

- LS GO and LS Web read a static, sanitized `neo_exchange.json`.
- Queue details contain no private Drive payload, secret, local path, token, or restricted title.
- GitHub Issues/Projects may carry public-safe task metadata.
- Private payloads remain in Drive and are referenced by opaque IDs.
- Static UI displays counts, criticality, age, source, target, and status icons.
- Task execution remains Desktop-only.

- [ ] **Step 4: Verify and commit**

```powershell
npm ci
npm run test
npm run check
npm run build
git add apps docs/integration
git commit -m "Connect LS Go to Neo exchange"
```

## Task 7: Release Verification, Scheduling, Build, Launch, And Publish

**Files:**
- Create: `scripts/register_weekly_maintenance.ps1`
- Create: `docs/release/LIGHTSPEED_FINAL_ALIGNMENT_PROOF_PACKET.md`
- Modify: `README.md`

- [ ] **Step 1: Register Friday maintenance**

The scheduled task must execute:

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe `
  -m lightspeed_runtime.maintenance `
  --root C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed
```

Schedule: weekly Friday, 19:00 Australia/Brisbane local time. Run only when the machine is available; start when available after a missed schedule; do not wake from sleep by default.

- [ ] **Step 2: Run security and secrets checks**

Scan tracked files and intended deployment output. Fail on:

- API keys or tokens
- private Drive IDs in public payloads
- local absolute paths in Web/GO output
- SQLite databases, model files, virtual environments, archives, or empirical datasets in Git

- [ ] **Step 3: Run complete test matrix**

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe -m pytest `
  C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed\tests -q -W error
C:\LightSpeed_Consolidated\venv\Scripts\python.exe `
  C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed\verify_launch_ready.py --quick
npm ci
npm run test
npm run check
npm run build
```

- [ ] **Step 4: Rebuild and launch Desktop**

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe `
  C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed\launcher_exe.py --build
```

Terminate stale duplicate LightSpeed instances, launch one instance through the Desktop shortcut, and verify:

- one `LightSpeedUnified` root
- dashboard default
- one embedded IT shell
- floor selector works
- Achilles dock responds through Ollama
- no new per-event files appear during smoke flow
- SQLite/weekly ledger receives one governed receipt

- [ ] **Step 5: Push and deploy**

```powershell
git status -sb
git push -u canonical codex/lightspeed-final-alignment
```

Open a pull request into `achillesromer-coder/LightSpeed:main`, verify CI, merge when green, and deploy LS GO/Web through the verified Vercel project. Do not deploy Desktop data or restricted artifacts.

- [ ] **Step 6: Produce proof packet**

Record:

- commit and merge SHAs
- Drive file IDs/URLs
- test counts and durations
- security scan result
- executable hash and shortcut target
- scheduled-task state
- process/RAM baseline
- quarantine manifest
- remaining restricted/manual-review items

Commit:

```powershell
git add README.md scripts docs/release
git commit -m "Record LightSpeed final alignment"
git push
```
