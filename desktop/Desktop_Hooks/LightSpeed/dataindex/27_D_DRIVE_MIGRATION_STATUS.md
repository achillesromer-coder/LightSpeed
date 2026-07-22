# Canonical C/D Storage Topology

Status: active soft-launch topology

## Current Authority

- Operator and launch namespace: `D:\LightSpeed_Consolidated`
- Physical backing store: `C:\LightSpeed_Consolidated`
- Active launcher: `D:\LightSpeed_Consolidated\tools\launch_lightspeed.ps1`
- Runtime namespace: `D:\LightSpeed_Consolidated\LightSpeed_Runtime`
- Desktop namespace: `D:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed`
- Exported operator-home state: `D:\LightSpeed_Consolidated\LightSpeed_Runtime\exports\agent_home`

The D runtime, shell, agents, applications, logs, sources and environment paths
are junctioned to C. They are one installation and must never be counted as two
recoverable copies.

## Consolidated Source Surfaces

- root launch surfaces from C: `__main__.py`, `verify_launch_ready.py`, `LAUNCH_GUI.bat`, `VERSION`
- root source/config/test/doc roots from C: `config`, `data`, `tests`, `tools`, `dataindex`
- active smart-floor packages from C: `Z+1_Architect`, `Z+2_Neo`, `Z+3_Trinity`, `Z-1_Morpheus`, `Z-2_Oracle`, `Z-3_Smith`, `Z-4_Merovingian`, `Z0_TheConstruct`
- runtime compatibility/modules from C into `D:\LightSpeed_Consolidated\LightSpeed_Runtime\lightspeed_runtime`
- Oracle AI log archive copied into `Z Axis/Z-2_Oracle/data/legacy/ai_logs`
- Merovingian unified DB copied into `Z Axis/Z-4_Merovingian/data/db/lightspeed_unified.db`

## Preserved Runtime Authority

- `LightSpeed_Runtime\lightspeed_runtime\operator_home.py`
- `LightSpeed_Runtime\lightspeed_runtime\agent_home_bridge.py`
- D-side updates in `runtime.py`, `domain_registry.py`, `desktop_adapters.py`, and `__init__.py`
- D-side Trinity/Smith operator-home and queue-router panels

## Validation

- `python verify_launch_ready.py --quick` -> `21/21` passed on D
- `python __main__.py --smoke` -> completed on D with `8/8` canonical floors initialized
- `LightSpeed_Runtime` targeted tests -> `18 passed`

## Historical Residues

Treat these as reference or evidence-gated cleanup candidates, not active
authority:

- `C:\Users\acc\Desktop\LightSpeed Consolidated\LightSpeed\ai_logs`
- `C:\Users\acc\Desktop\LightSpeed Consolidated\LightSpeed\w6`
- archive/legacy roots under `C:\Users\acc\Desktop\LightSpeed Consolidated\LightSpeed\Z Axis`
- outer project clutter under `C:\Users\acc\Desktop\LightSpeed Consolidated`

## Current Rule

Operators and shortcuts target D. Services resolve through the D junctions to C
physical backing. Git changes originate in `_worktrees`, pass validation and
review, then promote into the live runtime. Historical roots may be archived or
removed only after exact-path, checksum, reference and independent-recovery
proof; a C/D junction pair never satisfies the two-copy rule.
