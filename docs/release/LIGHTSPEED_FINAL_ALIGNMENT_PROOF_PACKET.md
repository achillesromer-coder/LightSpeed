# LightSpeed Final Alignment Proof Packet

Evidence captured on 2026-07-05 for the LightSpeed Desktop release candidate.

## Release Authority

- Canonical local runtime: `C:\LightSpeed_Consolidated`
- Compatibility root: `D:\LightSpeed_Consolidated`
- Canonical repository:
  `https://github.com/achillesromer-coder/LightSpeed.git`
- Release branch: `codex/lightspeed-final-alignment`
- Pull request:
  `https://github.com/achillesromer-coder/LightSpeed/pull/2`
- Base `main`: `714feeb792dabe9ab7784ccda75f7b20870f918f`
- Proof-packet parent commit:
  `cf21096d662b51d9acc37d798f4ee67a4a80a965`
- Application version: `5.1.2`

The three pre-existing generated LS GO `dist` modifications were not staged,
committed, reverted, or included in this release branch.

## Desktop Runtime

- Executable: `C:\LightSpeed_Consolidated\LightSpeed.exe`
- Executable bytes: `7,900,775`
- Executable SHA-256:
  `2990D45886E8AD25993E616CDEFF379A3D6C614FA38FCFADB5D0282EAB0BB534`
- Desktop shortcut: `C:\Users\acc\Desktop\LightSpeed.lnk`
- Shortcut target: `C:\LightSpeed_Consolidated\LightSpeed.exe`
- Verified live title: `LightSpeed Unified Orchestrator v5.1.2`
- Launch-to-window time: 22.97 seconds
- Live process topology: one wrapper and one runtime child
- Live child working set: 160.9 MB
- Passive active-view CPU duty: 10.2% of one core
- Previous passive active-view CPU duty: 75.9% of one core
- Renderer duty reduction: approximately 86%

The passive Cognigrex host now renders at 4 FPS. An explicitly launched
standalone visualizer retains 30 FPS. Startup reservoir indexing stops source
iteration at the configured limit before sorting.

## Validation

| Gate | Result |
| --- | --- |
| Canonical Desktop pytest suite | 453 passed in 163.01 seconds |
| Warnings policy | `-W error`, clean |
| Launch readiness | 22/22, 100%, 0 warnings |
| Repository/source tests | Passed |
| LS GO Vitest | 7/7 passed |
| LS GO TypeScript | Passed |
| LS GO isolated Vite build | Passed |
| npm audit | 0 vulnerabilities |
| Python `pip check` | No broken requirements |
| Tracked runtime/model/database boundary | Clean |
| Credential scan | Clean except intentional `test_secret` fixture |

## Ollama

- Endpoint: `http://127.0.0.1:11434`
- Ollama version: `0.23.1`
- Default verified model: `qwen3:8b`
- Installed models: `deepseek-r1:8b`, `gemma3:27b`, `qwen3:8b`,
  `deepseek-v3.1:671b-cloud`, and `gpt-oss:120b`
- Bounded inference response: `LIGHTSPEED_OK`
- Cold load time: 47.58 seconds
- End-to-end request time: 55.22 seconds
- Model unloaded after validation

Heavy and cloud models remain manual-only. Floor contracts allow at most one
job per floor and do not grant direct CPU, firmware, or operating-system
control.

## Drive Persistence

- Receipt: `drive/manifest/drive_upload_receipts.json`
- Receipt verification time: `2026-07-05T00:00:03Z`
- Verified targets: 10
- Verified artifacts: 20
- Landing documents: 10
- Native Google Sheets workbooks: 10
- Unexpected duplicates: 0

Targets are N. LightSpeed, Trinity, Architect, Morpheous, Oracle, Smith,
Merovingian, LS Neo, LS Web, and LS GO. The Construct remains Desktop-only.

## Historical Consolidation

- Physical files inventoried: 620,474
- Bytes inventoried: 151,262,329,743
- Generated/archive files compacted into aggregates: 601,314
- Aggregate records: 274
- Review candidates reconciled: 203
- Newly copied candidates: 60
- Long-path exceptions: 249

Exact root and classification counts are recorded in
`docs/migration/LIGHTSPEED_SOURCE_EXTRACTION_REGISTER.md` and
`data/migration/source_roots.json`. Historical roots remain deletion-blocked
until the long-path and independent-second-copy gates pass.

## Maintenance

- Scheduled task: `LightSpeed Friday Maintenance`
- Schedule: Friday 19:00 Australia/Brisbane local time
- Next run at verification: 2026-07-10 19:00
- Start when available: enabled
- Wake computer: disabled
- Concurrent instance policy: ignore new
- First governed quarantine: 43 artifacts
- Deleted artifacts: 0
- Verified second copies in quarantine: 0

The maintenance implementation quarantines and hashes generated candidates.
It does not delete entries without a verified independent second copy.

## External Deployment Boundary

The connected Vercel team contains no project and this checkout has no
`.vercel/project.json`; the Vercel CLI is also absent. The connector can deploy
only an already bound current project and cannot create or bind the intended
project. No Vercel deployment was attempted because doing so could create or
target the wrong public surface.

Web deployment remains blocked on one explicit external action: bind the
approved Vercel project to the intended repository and application root. This
does not block the verified Desktop release candidate.
