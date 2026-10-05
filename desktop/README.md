# LightSpeed Desktop Source Mirror

This directory is the Git boundary for approved LightSpeed Desktop source. The
runtime authority is `D:\LightSpeed_Consolidated`; the retained C-drive tree is
a migration and recovery source, not a competing runtime authority.

The synchronizer preserves allowlisted paths below this directory and writes
`source-manifest.json` with the SHA-256 digest and byte size of every included
file. It copies only approved source, test, and documentation extensions plus
explicitly named stable configuration contracts. Mandatory deny patterns
exclude personal, setup, runtime-state, secret, credential, token, receipt, and
generated-state names even when their extensions are approved. Runtime data,
archives, logs, caches, dependencies, reservoirs, vaults, virtual environments,
legacy trees, and reparse points are excluded.

Every changed source file and the manifest are written to unique, exclusively
created temporary files under verified target parents. Target containment and
reparse status are checked again immediately before atomic replacement.

From the repository root, preview the synchronization without writing:

```powershell
D:\LightSpeed_Consolidated\venv\Scripts\python.exe tools\sync_desktop_source.py --dry-run
```

Apply the synchronization:

```powershell
D:\LightSpeed_Consolidated\venv\Scripts\python.exe tools\sync_desktop_source.py --sync
```

The source root is fixed by the CLI. `--target-root` exists for isolated
verification; production synchronization uses this directory. The tool does
not delete stale output. Review the manifest and Git diff before commit.

Z-floor source may be added only as explicit files after secret and restricted
classification. Never allowlist a complete `Data`, `archive`, `legacy`,
`reservoirs`, or `vault` tree.

## Desktop dependency environment

From the repository root, use `tools/install_lightspeed_runtime.ps1 -Profile desktop`
to prepare a Python 3.11 environment with the API, data and desktop launch
dependencies. Supply `-VenvPath` and `-ReceiptPath` to keep a verification
environment and its receipt separate from an installed runtime. Python must
include Tcl/Tk; it is not installed through pip.

The desktop profile imports the modules in `LAUNCH_CORE_MODULES`, checks
Pillow's Tk bridge and creates a headless Tcl interpreter. It does not open the
desktop, start services or run queued work. A successful receipt proves these
dependency checks only. The environment links to this repository; it is not a
standalone distributable, installer acceptance or proof of working UI flows.
