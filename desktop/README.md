# LightSpeed Desktop Source Mirror

This directory is the Git boundary for approved LightSpeed Desktop source. The
runtime authority remains `C:\LightSpeed_Consolidated`; the compatibility
`D:\LightSpeed_Consolidated` tree is never a synchronization input.

The synchronizer preserves allowlisted paths below this directory and writes
`source-manifest.json` with the SHA-256 digest and byte size of every included
file. It copies only approved source, configuration, test, and documentation
extensions. Runtime data, archives, logs, caches, dependencies, reservoirs,
vaults, virtual environments, legacy trees, and reparse points are excluded.

From the repository root, preview the synchronization without writing:

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe tools\sync_desktop_source.py --dry-run
```

Apply the synchronization:

```powershell
C:\LightSpeed_Consolidated\venv\Scripts\python.exe tools\sync_desktop_source.py --sync
```

The source root is fixed by the CLI. `--target-root` exists for isolated
verification; production synchronization uses this directory. The tool does
not delete stale output. Review the manifest and Git diff before commit.

Z-floor source may be added only as explicit files after secret and restricted
classification. Never allowlist a complete `Data`, `archive`, `legacy`,
`reservoirs`, or `vault` tree.
