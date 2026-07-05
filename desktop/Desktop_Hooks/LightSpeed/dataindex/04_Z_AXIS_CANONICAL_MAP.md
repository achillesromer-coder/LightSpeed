# Z Axis Canonical Map (Spec vs Disk)

Generated: 2026-04-04
Root: C:\Users\acc\Desktop\LightSpeed Consolidated\LightSpeed

## Primary Floors (Cognigrex, Z+3..Z-4)
| Floor ID | Folder present | Key files present (spot-check) |
|---|---|---|
| `Z+3_Trinity` | yes | `Z Axis/Z+3_Trinity/wizards/cognigrex_setup_wizard.py`, `Z Axis/Z+3_Trinity/components/cognigrex_login.py`, `Z Axis/Z+3_Trinity/ui/it_portal.py` |
| `Z+2_Neo` | yes | `Z Axis/Z+2_Neo/Neo.py`, `Z Axis/Z+2_Neo/components/neo_lab_assistant_glass.py` |
| `Z+1_Architect` | yes | `Z Axis/Z+1_Architect/Architect.py`, `Z Axis/Z+1_Architect/components/dev_tools_portal_glass.py` |
| `Z0_TheConstruct` | yes | `Z Axis/Z0_TheConstruct/ui/immersive_3d_engine.py`, `Z Axis/Z0_TheConstruct/ui/cognigrex_3d_environment.py`, `Z Axis/Z0_TheConstruct/tools/ComponentLinker.py` |
| `Z-1_Morpheus` | yes | `Z Axis/Z-1_Morpheus/documentation` |
| `Z-2_Oracle` | yes | `Z Axis/Z-2_Oracle/components/oracle_smart_floor_integrator.py` |
| `Z-3_Smith` | yes | `Z Axis/Z-3_Smith/tools/scan_docs_to_tasks.py`, `Z Axis/Z-3_Smith/tools/generate_dataindex.py`, `Z Axis/Z-3_Smith/tools/sync_open_dialogue_to_db.py` |
| `Z-4_Merovingian` | yes | `Z Axis/Z-4_Merovingian/core/services/event_bus.py`, `Z Axis/Z-4_Merovingian/core/services/settings_hub.py`, `Z Axis/Z-4_Merovingian/core/services/database.py`, `Z Axis/Z-4_Merovingian/core/services/floor_manager.py` |

## Historical Capability Floors
| Folder | Disk state | Current treatment |
|---|---|---|
| `Z Axis/Z-0_Foundation` | not present | Reference only |
| `Z Axis/Z-1_DataFlow` | not present | Reference only |
| `Z Axis/Z-2_Intelligence` | not present | Reference only |
| `Z Axis/Z-3_Interface` | not present | Reference only |
| `Z Axis/Z-5_Experience` | archived under `Z Axis/archive/legacy_packs/Z-5_Experience` | Reference only |
| `Z Axis/Z-6_Command` | not present | Reference only |

## Notes
- Older docs may still mention Z-0..Z-6 floors, but the canonical runtime stack is the 8-floor Z+3..Z-4 stack.
- `Z Axis/*.py` files are legacy/root wrappers; floor-native packages live in `Z Axis/Z*/` folders.
- Use `dataindex/02_MASTER_BUILD_SPEC_SHEET.md` as the intended-state baseline and this file as the reconciliation layer.
