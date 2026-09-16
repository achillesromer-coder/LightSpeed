# LightSpeed

LightSpeed is the local Cognigrex desktop control plane and its approved
inter-platform contracts. `D:\LightSpeed` is the stable operator and launch
namespace. Its `App`, `Core` and `Apps` surfaces resolve to the established
`C:\LightSpeed_Consolidated` backing stores; `Environment`, `Automation`,
`Tools`, `Data`, `State` and `Worktrees` remain under the D-drive namespace.
These paths form one controlled system rather than competing C- and D-drive
copies. Reviewed Git worktrees stay separate under `D:\LightSpeed\Worktrees`
and promote code into the live runtime only through the maintenance/launch
workflow.

## Operate

- Launch from `C:\Users\acc\Desktop\LightSpeed.lnk`; its canonical target is
  the D-drive LightSpeed launcher.
- Use Trinity as the single human operator shell. The floor agents remain
  backend workspaces, not separate competing application surfaces.
- Use Neo for reviewed handoffs between Desktop, LS GO, LS Web, and Drive.
- Keep Ollama models on the local endpoint at `http://localhost:11434`.
- Keep The Construct local. It has no Drive memory workbook.

## Authority

| Surface | Authority |
| --- | --- |
| Desktop | Executable runtime, SQLite state, local models, empirical inputs, and active work under the D operator namespace with C physical backing |
| Drive | Approved long-term agent memory, review workbooks, handoffs, and receipts |
| Git | Source, tests, stable contracts, schemas, and public-safe summaries |
| LS GO / LS Web | Approved queue exchange and front-facing interaction |

The interactive Desktop runtime does not run Git commands. Reviewed Git source
is promoted into Desktop through the maintenance/launch workflow, while Neo
routes approved Drive knowledge and receipts. Git never reads unrestricted
Desktop runtime state. Approved records cross boundaries through explicit
manifests and receipts. Secrets,
model weights, databases, logs, archives, empirical payloads, and virtual
environments never enter Git.

The complete boundary and classification rules are in
`docs/architecture/LIGHTSPEED_AUTHORITY_MAP.md`.

## Verify

Run the Desktop suite:

```powershell
D:\LightSpeed\Environment\Scripts\python.exe -m pytest D:\LightSpeed\App\tests -q -W error
```

Run launch readiness:

```powershell
D:\LightSpeed\Environment\Scripts\python.exe D:\LightSpeed\App\verify_launch_ready.py --quick
```

Run LS GO checks:

```powershell
Set-Location apps\lightspeed-go
npm.cmd test
npm.cmd run check
```

### Private remote review

LS GO uses the same-machine Desktop bridge at `http://127.0.0.1:8765` by
default. A reviewed web build can instead use an authenticated private relay by
setting `VITE_LIGHTSPEED_DESKTOP_ORIGIN` to the relay's credential-free HTTPS
origin before building. Paths, query strings, embedded credentials and remote
plain-HTTP origins fail closed. The relay must terminate TLS, forward only to
the local bridge, and its exact LS GO origin must also be present in
`LIGHTSPEED_GO_ALLOWED_ORIGINS`.

This setting changes transport only. Owner authentication, first-login password
change, session expiry, review gates and the prohibition on public direct
execution remain enforced by Desktop.

Weekly generated-artifact maintenance is registered for Friday at 19:00 local
time. It quarantines before removal and never treats a junction as a second
copy. Registration source is `scripts/register_weekly_maintenance.ps1`.

## Release

The canonical Git remote is
`https://github.com/achillesromer-coder/LightSpeed.git`. A web deployment is
valid only after the workspace is bound to an explicit Vercel project and the
resulting deployment is verified. Do not deploy the repository root to an
inferred or newly created project.
