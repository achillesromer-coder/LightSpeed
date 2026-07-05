# LightSpeed

LightSpeed is the local Cognigrex desktop control plane and its approved
inter-platform contracts. The canonical runtime is
`C:\LightSpeed_Consolidated`; `D:\LightSpeed_Consolidated` is compatibility
only and must not become an independent source of truth.

## Operate

- Launch from `C:\Users\acc\Desktop\LightSpeed.lnk` or
  `C:\LightSpeed_Consolidated\LightSpeed.exe`.
- Use Trinity as the single human operator shell. The floor agents remain
  backend workspaces, not separate competing application surfaces.
- Use Neo for reviewed handoffs between Desktop, LS GO, LS Web, and Drive.
- Keep Ollama models on the local endpoint at `http://localhost:11434`.
- Keep The Construct local. It has no Drive memory workbook.

## Authority

| Surface | Authority |
| --- | --- |
| Desktop | Executable runtime, SQLite state, local models, empirical inputs, and active work |
| Drive | Approved long-term agent memory, review workbooks, handoffs, and receipts |
| Git | Source, tests, stable contracts, schemas, and public-safe summaries |
| LS GO / LS Web | Approved queue exchange and front-facing interaction |

Desktop does not invoke Git. Git does not read Desktop runtime state. Approved
records cross boundaries through explicit manifests and receipts. Secrets,
model weights, databases, logs, archives, empirical payloads, and virtual
environments never enter Git.

The complete boundary and classification rules are in
`docs/architecture/LIGHTSPEED_AUTHORITY_MAP.md`.

## Verify

Run the Desktop suite:

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe -m pytest C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed\tests -q -W error
```

Run launch readiness:

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe C:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed\verify_launch_ready.py --quick
```

Run LS GO checks:

```powershell
Set-Location apps\lightspeed-go
npm.cmd test
npm.cmd run check
```

Weekly generated-artifact maintenance is registered for Friday at 19:00 local
time. It quarantines before removal and never treats a junction as a second
copy. Registration source is `scripts/register_weekly_maintenance.ps1`.

## Release

The canonical Git remote is
`https://github.com/achillesromer-coder/LightSpeed.git`. A web deployment is
valid only after the workspace is bound to an explicit Vercel project and the
resulting deployment is verified. Do not deploy the repository root to an
inferred or newly created project.
