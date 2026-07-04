# D-Drive Migration Status

Date: 2026-05-21
Status: D-drive shell/runtme alignment completed to non-GUI launch parity

## D Is Now Authoritative

- Active launcher: `D:\LightSpeed_Consolidated\Desktop_Hooks\LightSpeed\N.py`
- Runtime authority: `D:\LightSpeed_Consolidated\LightSpeed_Runtime`
- Exported operator-home state: `D:\LightSpeed_Consolidated\LightSpeed_Runtime\exports\agent_home`

## Imported Canonical Source Surfaces

- root launch surfaces from C: `__main__.py`, `verify_launch_ready.py`, `LAUNCH_GUI.bat`, `VERSION`
- root source/config/test/doc roots from C: `config`, `data`, `tests`, `tools`, `dataindex`
- active smart-floor packages from C: `Z+1_Architect`, `Z+2_Neo`, `Z+3_Trinity`, `Z-1_Morpheus`, `Z-2_Oracle`, `Z-3_Smith`, `Z-4_Merovingian`, `Z0_TheConstruct`
- runtime compatibility/modules from C into `D:\LightSpeed_Consolidated\LightSpeed_Runtime\lightspeed_runtime`
- Oracle AI log archive copied into `Z Axis/Z-2_Oracle/data/legacy/ai_logs`
- Merovingian unified DB copied into `Z Axis/Z-4_Merovingian/data/db/lightspeed_unified.db`

## Preserved D-Only Authority

- `LightSpeed_Runtime\lightspeed_runtime\operator_home.py`
- `LightSpeed_Runtime\lightspeed_runtime\agent_home_bridge.py`
- D-side updates in `runtime.py`, `domain_registry.py`, `desktop_adapters.py`, and `__init__.py`
- D-side Trinity/Smith operator-home and queue-router panels

## Validation

- `python verify_launch_ready.py --quick` -> `21/21` passed on D
- `python __main__.py --smoke` -> completed on D with `8/8` canonical floors initialized
- `LightSpeed_Runtime` targeted tests -> `18 passed`

## C-Side Residues

Treat these as reference or deletion candidates, not active authority:

- `C:\Users\acc\Desktop\LightSpeed Consolidated\LightSpeed\ai_logs`
- `C:\Users\acc\Desktop\LightSpeed Consolidated\LightSpeed\w6`
- archive/legacy roots under `C:\Users\acc\Desktop\LightSpeed Consolidated\LightSpeed\Z Axis`
- outer project clutter under `C:\Users\acc\Desktop\LightSpeed Consolidated`

## Current Rule

No new active work should target the C-drive LightSpeed root. Use the D-drive shell/runtime split as the live system and treat the C-drive tree as reference-only until final manual residue deletion.
