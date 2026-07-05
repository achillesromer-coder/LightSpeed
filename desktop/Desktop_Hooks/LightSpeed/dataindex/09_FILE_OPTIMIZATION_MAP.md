# File Optimization Map

Date: 2026-04-08

Purpose: track the systematic file-series reduction pass for files last modified before April 1, 2026. The rule is to keep one canonical runtime path, move generated state into Z-axis ownership, and reduce compatibility files into thin wrappers instead of maintaining parallel systems.

## Current Rules

- `N.py` is the canonical desktop shell.
- `__main__.py` is a compatibility wrapper for `python -m LightSpeed` and legacy flags.
- `LAUNCH_GUI.bat` is a thin Windows launcher and delegates to `__main__.py`.
- Merovingian owns compact cross-floor activity state: `Z Axis/Z-4_Merovingian/data/audit/activity_tables.json` and `Z Axis/Z-4_Merovingian/data/db/lightspeed_activity.db`.
- JSONL logs and ledgers remain append-only evidence; the activity table is the operator-facing surface.
- `data/generated/` must stay absent.
- Root `w6/`, root `operations/w6/`, root `canonical_runtime/`, and outer library folders stay declassified after rehome unless an explicit reference check proves otherwise.

## Pass 01 - Root Files Modified Before 2026-04-01

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `.gitattributes` | Minimal LF autodetect only. | Expanded text/binary policy for Python, docs, JSON/JSONL, batch/PowerShell, database, media, PDF, and Parquet files. | Keeps future versioned file behavior aligned with mixed source/data assets. |
| `__main__.py` | Large legacy launcher with duplicated setup, spatial, backend, and floor logic. | Replaced with a small compatibility wrapper delegating to `N.py`. | Prevents launcher drift and preserves common legacy flags by mapping them to `N.py`. |
| `LAUNCH_GUI.bat` | Large parallel Windows launcher with old setup and dependency logic. | Replaced with a small launcher that sets runtime env vars and calls `__main__.py`. | Reduces duplicate launch framework and keeps Windows startup aligned to the canonical shell. |
| `VERSION` | `5.1.1`. | Updated to `5.1.2`. | Marks the file optimization baseline. |
| `README.md` | `5.1.1`, runtime tests `63/63`. | Updated version heading. | README remains the operator baseline document. |

## Next File-Series Targets

- Review stale `ai_logs/` files as mounted/reference material, not runtime source.
- Review stale `data/` files for template-only status.
- Continue stale `config/runtime` checks only if a later pass finds pre-April drift.
- Continue folder-by-folder through `Z Axis`, prioritizing launcher/wizard/settings surfaces before large archived reservoirs.

## Pass 02 - Stale Dataindex Files Modified Before 2026-04-01

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `00_DIRECTORY_MAP.md` | Generated February directory map with old root `w6`, root generated, and stale file counts. | Deleted. | Superseded by Merovingian reports and current root classification docs. |
| `01_AI_LOGS_DOCUMENT_TABLE.md` | Generated AI-log table from February with stale document/task counts. | Deleted. | Superseded by Oracle knowns, proofing queue, definition library, and activity table. |
| `02_MASTER_BUILD_SPEC_SHEET.md` | Large intended-state document from January/February with outdated `__main__.py` role and supporting index references. | Rewritten as compact current master spec. | Keeps one intended-state document aligned to N.py, Z-axis ownership, and current validation state. |
| `03_Z_AXIS_FILESYSTEM_MAP.md` | Generated February Z-axis file count map with old sizes and archive state. | Deleted. | Superseded by runtime finalization overview and smart-floor assimilation reports. |
| `05_Z_DIRECT_AUDIT.md` | One-off scaffold audit from January. | Deleted. | Z Direct ownership now covered by canonical map and runtime reports. |
| `scenario_catalog.json` | Thin pointer to Merovingian operations registry. | Deleted. | It was not an active runtime contract; canonical scenario state belongs under Merovingian/Construct runtime data. |

## Pass 03 - Stale Config Files Modified Before 2026-04-01

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `config/examples/floor_communication_examples.py` | Standalone example script with no active bounded references. | Deleted and removed empty `config/examples/`. | Prevents example code from looking like an executable floor contract. |
| `config/tests/test_integration.py` | Stale local test under `config/` with non-canonical import assumptions. | Deleted and removed empty `config/tests/`. | Canonical tests remain under `tests/`. |
| `config/layout_config.json` | Tiny bento layout shell with no active bounded references. | Deleted. | Bento layout now belongs in `config/unified_config.json` and Trinity UI contracts. |
| `config/library_registry.json` | Snapshot of installed Python libraries with absolute local paths and stale availability data. | Deleted. | Live library status is regenerated through Merovingian `function_registry.py`. |
| `config/z_stack_manifest.json` | January consolidation manifest duplicating dataindex and finalization reports. | Deleted. | Current Z-axis ownership is covered by `02`, `04`, `07`, `08`, and runtime reports. |
| `config/function_registry.json` | Stale component list using old module names and a shape the service cache did not read correctly. | Hardened the Merovingian cache reader and regenerated the cache. | Now contains `22` libraries and `46` live functions in the canonical `libraries/functions` shape. |
| `config/lightspeed_config.json` | Active health-check config with version `2.0.0` and older hook names. | Updated to `5.1.2` and aligned hooks to Morpheus/Oracle/Construct wording. | Preserved required health-check sections while reducing stale vocabulary. |
| `config/unified_config.json` | Active runtime config at `5.1.1` with old product name and root `logs/` path. | Updated to `5.1.2`, operator OS naming, and Merovingian log/activity paths. | Keeps N.py/Trinity runtime config aligned with compact activity-table ownership. |
| `config/z_direct_template.json` | Active health-check template at `5.1.0` with old floor responsibility text. | Updated to `5.1.2` and current smart-floor responsibilities. | Z Direct now describes floor ownership in the same terms used by the UI and runtime. |
| `config/premium_theme_config.json` | Active Trinity theme file at `1.0.0` with pre-bento wording. | Updated to `5.1.2` and added the 1.5m curved bento panel-wall interaction contract. | Theme config now carries the current glass/bento UI direction. |

## Pass 04 - Test Harness Fixes Discovered During Config Validation

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `tests/test_health.py` | Imported `conftest` as a top-level module and recursively walked every file under each floor. | Switched to `tests.conftest` import and bounded the floor Python-file check to active floor/component/core directories. | Health tests now run from the application root and no longer hang on absorbed Oracle archives. |
| `tests/test_scenarios.py` | Imported `conftest` as a top-level module. | Switched to `tests.conftest`. | Aligns stale test imports with package execution from the app root. |
| `tests/test_simulations.py` | Imported `conftest` as a top-level module. | Switched to `tests.conftest`. | Aligns stale test imports with package execution from the app root. |
| `tests/test_z_axis_floors.py` | Imported `conftest` as a top-level module. | Switched to `tests.conftest`. | Aligns stale test imports with package execution from the app root. |
| `tests/test_z_direct.py` | Imported `conftest` as a top-level module. | Switched to `tests.conftest`. | Aligns stale test imports with package execution from the app root. |
| `tests/__init__.py` and `tests/conftest.py` | Version text still reported `5.1.1`; `tests/__init__.py` exported removed `test_integration`. | Updated version text to `5.1.2` and removed the stale export. | Test metadata now matches the active file series. |

## Pass 05 - Root AI Logs

| File Set | Previous State | Action | Result |
| --- | --- | --- | --- |
| `ai_logs/` | Root reference bundle containing January/February handoffs, release notes, alignment notes, and dialogue archives. | Moved to `Z Axis/Z-2_Oracle/data/legacy/ai_logs`. | Removes a root-level reference folder and keeps the raw evidence under Oracle ownership. |
| `config/runtime/runtime_reservoirs.json` | Mounted `lightspeed_ai_logs` from the root `ai_logs/` path. | Updated the reservoir path to Oracle legacy storage. | Knowns ingestion still has the source available without keeping a root log bundle. |
| `verify_launch_ready.py` and `tests/test_health.py` | Treated root `ai_logs/` as required structure. | Updated readiness/health checks to use the Oracle-owned path. | Launch checks now match smart-floor ownership. |
| `N.py` root hygiene | Allowed root `ai_logs/`. | Removed `ai_logs` from the canonical root allowlist and updated the archive comment. | Future root AI-log sprawl is treated as a hygiene regression. |
| `Z Axis/Z-2_Oracle/data/knowns/ai_logs_compaction_manifest.json` | Did not exist. | Generated a compact manifest for the moved archive. | Oracle now records the move, file count, byte count, and top-level source list. |

## Pass 06 - Stale Z Axis Root Files Modified Before 2026-04-01

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/__init__.py` | Large stale tower framework with incorrect floor levels and unused package-style scanning. | Rewritten as a compact floor ownership map. | Keeps inspection helpers without duplicating runtime floor loading. |
| `Z Axis/icon_manifest.json` | Root-level icon manifest unused by the active Trinity icon library path. | Moved to `Z Axis/Z+3_Trinity/assets/icons/icon_manifest.json` and updated to `5.1.2`. | Trinity now owns the glass/bento icon manifest where the loader expects it. |
| `Z Axis/romer-mission-control-v5.1.jsx` | January standalone JSX artifact with no active bounded references. | Deleted. | Removes stale root UI artifact after bento/operator UI alignment. |
| `Z Axis/romer-mission-control-v5.1-artifact.jsx` | January standalone JSX artifact with no active bounded references. | Deleted. | Removes stale root UI artifact after bento/operator UI alignment. |
| `Z Axis/Merovingian.py` | Active coordinator with older diagnostics-only wording. | Updated docstring to include compact activity tables, runtime exports, finalization, telemetry, and audit evidence. | Floor description now matches the implemented Merovingian role. |
| `Z Axis/Smith.py` | Active coordinator with older task/SOP-only wording. | Updated docstring to include Smith router, bounded execution, and resumable workflow state. | Floor description now matches the implemented Smith role. |

## Pass 07 - Architect Floor Root Files

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z+1_Architect/Architect.py` | Floor-local January entrypoint duplicate; active manifest uses root `Z Axis/Architect.py`. | Deleted. | Removes duplicate Architect execution surface. |
| `Z Axis/Z+1_Architect/.gitignore` | Per-floor gitignore in a non-git floor folder. | Deleted. | Root policy now handles file behavior. |
| `Z Axis/Z+1_Architect/__init__.py` | Imported the deleted floor-local `Architect.py`. | Rewritten as compact metadata only. | Prevents stale package import assumptions. |
| `Z Axis/Z+1_Architect/README.md` | January README with mojibake tree and invalid `from Z+1_Architect import` usage. | Rewritten as compact current ownership note. | Documents root coordinator, data root, and governance role. |
| `Z Axis/Z+1_Architect/z+1_config.json` | `1.0.0` planning/dev-tools config with legacy Tank wording. | Rewritten as compact `5.1.2` governance/publish/finalization config. | Keeps floor-local config aligned to current Architect ownership. |
| `Z Axis/Z+1_Architect/_FLOOR_MANIFEST.json` | Active manifest with `1.0.0` version and old mission-planning-only descriptions. | Updated version, descriptions, capabilities, and timestamp. | Floor loader contract remains intact while reflecting current responsibility. |

## Pass 08 - Neo Floor Root Files

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z+2_Neo/Neo.py` | Floor-local February entrypoint duplicate; active manifest uses root `Z Axis/Neo.py`. | Deleted. | Removes duplicate Neo execution surface. |
| `Z Axis/Z+2_Neo/.gitignore` | Per-floor gitignore in a non-git floor folder. | Deleted. | Root policy now handles file behavior. |
| `Z Axis/Z+2_Neo/__init__.py` | Imported the deleted floor-local `Neo.py`. | Rewritten as compact metadata only. | Prevents stale package import assumptions. |
| `Z Axis/Z+2_Neo/README.md` | January README with mojibake tree and invalid `from Z+2_Neo import` usage. | Rewritten as compact current ownership note. | Documents root coordinator, data root, Achilles/Cognigrex role, and governed handoffs. |
| `Z Axis/Z+2_Neo/z+2_config.json` | `1.0.0` AI integration config with generic assistant wording. | Rewritten as compact `5.1.2` operator-AI/action-proposal config. | Keeps floor-local config aligned to current Neo ownership. |
| `Z Axis/Z+2_Neo/_FLOOR_MANIFEST.json` | Active manifest with `1.0.0` version and old assistant/Ollama descriptions. | Updated version, descriptions, capabilities, and timestamp. | Floor loader contract remains intact while reflecting Achilles/Cognigrex ownership. |

## Pass 09 - Trinity Floor Root Files

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z+3_Trinity/Trinity.py` | Floor-local February entrypoint duplicate; active manifest uses root `Z Axis/Trinity.py`. | Deleted. | Removes duplicate Trinity execution surface. |
| `Z Axis/Z+3_Trinity/.gitignore` | Per-floor gitignore in a non-git floor folder. | Deleted. | Root policy now handles file behavior. |
| `Z Axis/Z+3_Trinity/__init__.py` | Imported the deleted floor-local `Trinity.py`. | Rewritten as compact metadata only. | Prevents stale package import assumptions. |
| `Z Axis/Z+3_Trinity/README.md` | January README with mojibake tree and invalid `from Z+3_Trinity import` usage. | Rewritten as compact current ownership note. | Documents root coordinator, UI contracts, icon assets, and settings role. |
| `Z Axis/Z+3_Trinity/z+3_config.json` | `1.0.0` generic UI/dashboard config. | Rewritten as compact `5.1.2` operator-portal/UI-contract config. | Keeps floor-local config aligned to current Trinity ownership. |
| `Z Axis/Z+3_Trinity/_FLOOR_MANIFEST.json` | Active manifest with old customization/dashboard descriptions and a `stub` status tag. | Updated version, descriptions, capabilities, status tag, and timestamp. | Floor loader contract remains intact while reflecting current operator portal role. |
| `Z Axis/Z+3_Trinity/smart_bento_hub.py` | Active, test-covered settings surface with old phone-shade language. | Updated header wording to the current glass/bento operator-shell model. | Keeps the feature while reducing stale UX assumptions. |

## Pass 10 - TheConstruct Floor Root Files

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z0_TheConstruct/TheConstruct.py` | Floor-local February entrypoint duplicate; active manifest uses root `Z Axis/TheConstruct.py`. | Deleted. | Removes duplicate Construct execution surface. |
| `Z Axis/Z0_TheConstruct/.gitignore` | Per-floor gitignore in a non-git floor folder. | Deleted. | Root policy now handles file behavior. |
| `Z Axis/Z0_TheConstruct/bento_config.py` | Unreferenced stale `Z-0_Foundation` bento shell. | Deleted. | Avoids a misleading alternate bento configuration. |
| `Z Axis/Z0_TheConstruct/__init__.py` | Imported the deleted floor-local `TheConstruct.py`. | Rewritten as compact metadata only. | Prevents stale package import assumptions. |
| `Z Axis/Z0_TheConstruct/README.md` | January README with mojibake tree and invalid package-entrypoint usage. | Rewritten as compact current ownership note. | Documents root coordinator, holospace, scenario labs, physics calculators, and GMAT batch role. |
| `Z Axis/Z0_TheConstruct/z0_config.json` | Large `1.0.0` central-command config with outdated floor names and pre-finalization portal wording. | Rewritten as compact `5.1.2` holospace/scenario-lab config. | Keeps floor-local config aligned to current Construct ownership. |
| `Z Axis/Z0_TheConstruct/_FLOOR_MANIFEST.json` | Active manifest with `1.0.0` training-ground wording. | Updated version, descriptions, capabilities, and timestamp. | Floor loader contract remains intact while reflecting current Construct responsibility. |
| `Z Axis/Z0_TheConstruct/physics_calculators.py` and `dimensions_library.py` | Active scientific libraries with stale generated headers. | Preserved and updated headers only. | Keeps active calculators/reference data while clarifying that orchestration belongs in runtime/root coordinator code. |

## Pass 11 - Morpheus Floor Root Files

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z-1_Morpheus/Morpheus.py` | Floor-local February entrypoint duplicate; active manifest uses root `Z Axis/Morpheus.py`. | Deleted. | Removes duplicate Morpheus execution surface. |
| `Z Axis/Z-1_Morpheus/.gitignore` | Per-floor gitignore in a non-git floor folder. | Deleted. | Root policy now handles file behavior. |
| `Z Axis/Z-1_Morpheus/__init__.py` | Imported the deleted floor-local `Morpheus.py`. | Rewritten as compact metadata only. | Prevents stale package import assumptions. |
| `Z Axis/Z-1_Morpheus/README.md` | January README with mojibake tree and invalid package-entrypoint usage. | Rewritten as compact current ownership note. | Documents root coordinator, review/proofing role, editor surfaces, and proofing data ownership. |
| `Z Axis/Z-1_Morpheus/z-1_config.json` | `1.0.0` knowledge/indexing config with older generic role wording. | Rewritten as compact `5.1.2` review/proofing config. | Keeps floor-local config aligned to current Morpheus ownership. |
| `Z Axis/Z-1_Morpheus/_FLOOR_MANIFEST.json` | Active manifest with `1.0.0` documentation/search wording. | Updated version, descriptions, capabilities, and timestamp. | Floor loader contract remains intact while reflecting current review/proofing responsibility. |

## Pass 12 - Oracle Floor Root Files

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z-2_Oracle/Oracle.py` | Floor-local January entrypoint duplicate; active manifest uses root `Z Axis/Oracle.py`. | Deleted. | Removes duplicate Oracle execution surface. |
| `Z Axis/Z-2_Oracle/.gitignore` | Per-floor gitignore in a non-git floor folder. | Deleted. | Root policy now handles file behavior. |
| `Z Axis/Z-2_Oracle/__init__.py` | Imported the deleted floor-local `Oracle.py`. | Rewritten as compact metadata only. | Prevents stale package import assumptions. |
| `Z Axis/Z-2_Oracle/README.md` | January README with mojibake tree and invalid package-entrypoint usage. | Rewritten as compact current ownership note. | Documents root coordinator, knowns, empirical catalog, datatables, catalog shell, and legacy provenance role. |
| `Z Axis/Z-2_Oracle/z-2_config.json` | Large `1.0.0` generic data-intelligence config with stale insight widgets. | Rewritten as compact `5.1.2` catalog/proofed-knowns config. | Keeps floor-local config aligned to current Oracle ownership. |
| `Z Axis/Z-2_Oracle/_FLOOR_MANIFEST.json` | Active manifest with IP-vault/archive-only wording. | Updated version, descriptions, endpoints, capabilities, and timestamp. | Floor loader contract remains intact while reflecting current catalog/proofing responsibility. |

## Pass 13 - Smith Floor Root Files

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z-3_Smith/Smith.py` | Floor-local January entrypoint duplicate; active manifest uses root `Z Axis/Smith.py`. | Deleted. | Removes duplicate Smith execution surface. |
| `Z Axis/Z-3_Smith/.gitignore` | Per-floor gitignore in a non-git floor folder. | Deleted. | Root policy now handles file behavior. |
| `Z Axis/Z-3_Smith/__init__.py` | Imported the deleted floor-local `Smith.py`. | Rewritten as compact metadata only. | Prevents stale package import assumptions. |
| `Z Axis/Z-3_Smith/README.md` | January README with mojibake tree and stale security-scanner role. | Rewritten as compact current ownership note. | Documents root coordinator, Smith router, workflow state, queue, and bounded execution ownership. |
| `Z Axis/Z-3_Smith/z-3_config.json` | Large `1.0.0` framework-management config with old hooks/tools inventory. | Rewritten as compact `5.1.2` router/execution-gateway config. | Keeps floor-local config aligned to current Smith ownership. |
| `Z Axis/Z-3_Smith/_FLOOR_MANIFEST.json` | Active manifest with generic background-job wording. | Updated version, descriptions, endpoints, capabilities, and timestamp. | Floor loader contract remains intact while reflecting current router/workflow responsibility. |

## Pass 14 - Merovingian Floor Root Files

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z-4_Merovingian/.gitignore` | Per-floor gitignore in a non-git floor folder. | Deleted. | Root policy now handles file behavior. |
| `Z Axis/Z-4_Merovingian/user_profile.json` | Stale setup profile in the core/evidence floor root. | Rehomed to `Z Axis/Z+3_Trinity/data/profiles/user_profile.json`. | Trinity owns user/profile setup state; Merovingian stays focused on system evidence. |
| `Z Axis/Z-4_Merovingian/__init__.py` | Valid core-service exports with `1.2.0` metadata and older foundation-only wording. | Updated header and version while preserving core-service exports. | Keeps compatibility for any package-level core-service imports. |
| `Z Axis/Z-4_Merovingian/README.md` | January README with mojibake tree and invalid package-entrypoint usage. | Rewritten as compact current ownership note. | Documents root coordinator, core services, activity DB, audit, telemetry, runtime exports, and quality outputs. |
| `Z Axis/Z-4_Merovingian/z-4_config.json` | Large `1.0.0` diagnostics config with stale widget layout and separate log-analyzer framing. | Rewritten as compact `5.1.2` core-services/evidence config. | Keeps floor-local config aligned to current Merovingian ownership. |
| `Z Axis/Z-4_Merovingian/_FLOOR_MANIFEST.json` | Active manifest with health/diagnostics-only wording. | Updated version, descriptions, endpoints, capabilities, and timestamp. | Floor loader contract remains intact while reflecting current activity/audit/finalization responsibility. |

## Pass 15 - Merovingian Component-Level Cull

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z-4_Merovingian/components/bulk_file_ops.py` | Pre-April utility not loaded by the manifest and only exported by the generated component package. | Deleted after bounded reference check. | Removes inactive bulk-file operation surface from the core floor. |
| `Z Axis/Z-4_Merovingian/components/data_sync.py` | Pre-April utility not loaded by the manifest and only exported by the generated component package. | Deleted after bounded reference check. | Removes inactive sync surface from the core floor. |
| `Z Axis/Z-4_Merovingian/components/db_optimizer.py` | Pre-April utility not loaded by the manifest and only exported by the generated component package. | Deleted after bounded reference check. | Removes inactive optimizer surface from the core floor. |
| `Z Axis/Z-4_Merovingian/components/TemplateDeployment.py` | Pre-April service not loaded by the manifest and only exported by the generated component package. | Deleted after bounded reference check. | Removes stale template-deployment service surface from Merovingian. |
| `Z Axis/Z-4_Merovingian/components/__init__.py` | Auto-generated export list referenced deleted inactive utilities. | Rewritten to export active manifest-backed components only. | Component package now matches the active Merovingian loader contract. |

## Pass 16 - Trinity Component-Level Cull

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z+3_Trinity/components/chart_widget.py` | Pre-April widget module not loaded by the active manifest and only exported by the generated component package. | Deleted after bounded reference check. | Removes inactive chart widget surface; current analytics use `analytics_dashboard.py`. |
| `Z Axis/Z+3_Trinity/components/notification_center.py` | Pre-April notification/demo widget module not loaded by the active manifest and only exported by the generated component package. | Deleted after bounded reference check. | Removes inactive notification-center surface from Trinity. |
| `Z Axis/Z+3_Trinity/components/service_integrations.py` | Pre-April service-integration panel not loaded by the active manifest and only exported by the generated component package. | Deleted after bounded reference check. | Removes inactive settings-side integration surface; current settings are managed through `settings_dialog.py` and runtime contracts. |
| `Z Axis/Z+3_Trinity/components/collaboration_todo_panel.py` | Pre-April collaboration todo panel not loaded by the manifest and not referenced by current portal flow. | Deleted after bounded reference check. | Removes an isolated collaboration side panel from the publishable operator shell. |
| `Z Axis/Z+3_Trinity/components/__init__.py` | Auto-generated export list pulled in inactive widgets and old service panels. | Rewritten to export active and still-referenced Trinity components only. | Component package now matches current operator portal, settings, context menu, analytics, and collaboration surfaces. |

## Pass 17 - Trinity UI Low-Risk Cull

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z+3_Trinity/ui/data_integration.py` | Pre-bento optional UI helper with zero bounded external references. | Deleted after bounded reference check. | Removes an unused data-integration side surface. |
| `Z Axis/Z+3_Trinity/ui/data_objectifier_ui.py` | Pre-bento optional data-objectifier UI with zero bounded external references. | Deleted after bounded reference check. | Removes an unused objectifier side panel from Trinity UI. |
| `Z Axis/Z+3_Trinity/ui/spatial_integration.py` | Pre-bento spatial integration helper with zero bounded external references. | Deleted after bounded reference check. | Removes an unused spatial integration side surface while preserving active holospace modules. |
| `Z Axis/Z+3_Trinity/ui/smart_theme.py`, `spherical_ui.py`, `widget_registry.py`, and immersive modules | Still referenced directly or indirectly by settings/UI wrapper modules. | Preserved for now. | Avoids breaking active UI/settings paths while narrowing only proven-unused files. |

## Pass 18 - Trinity UI Bridge Cull

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z+3_Trinity/ui/floor_widgets.py` | Legacy `Widget3D` helper with no exact external references. | Deleted after exact reference check. | Removes a pre-bento widget bridge no longer used by the active shell. |
| `Z Axis/Z+3_Trinity/ui/visualization.py` | Dependency-free ASCII visualization helper with no exact external references. | Deleted after exact reference check. | Removes an unused fallback visualization module. |
| `Z Axis/Z+3_Trinity/ui/immersive_engine.py` | Legacy immersive engine referenced only by deleted `floor_widgets.py`. | Deleted after dependency reference check. | Removes the unused terminal/Widget3D immersive layer. |
| `Z Axis/Z+3_Trinity/ui/immersive_bento_ui.py` | Old standalone curved bento UI shell with no exact external references. | Deleted after exact reference check. | Removes a duplicate bento implementation. |
| `Z Axis/Z+3_Trinity/ui/n_bento_overlay.py` | Old N overlay bridge with no exact external references. | Deleted after exact reference check. | Removes an unused overlay implementation. |
| `Z Axis/Z+3_Trinity/ui/dome_projection_engine.py` | Old dome projection helper with no exact external references after bento-system declassification. | Deleted after exact reference check. | Removes an unused projection bridge. |
| `Z Axis/Z+3_Trinity/ui/immersive_bento_system.py` | Old 3-step bento manager with no exact external references. | Deleted after exact reference check. | Removes a duplicate bento manager now superseded by active operator shell flows. |
| `Z Axis/Z+3_Trinity/ui/floor_ui_wrapper.py` and `spherical_ui.py` | Legacy spherical wrapper pair with no external references outside the pair. | Deleted after exact reference check. | Removes an unused spherical wrapper layer while preserving `immersive_interface.py` and its active dependencies. |
| `Z Axis/Z+3_Trinity/ui/interface_orchestrator.py` and `immersive_interface.py` | Still loaded by `N.py`. | Preserved. | Keeps active shell launch paths intact. |

## Next Consolidation Execution List

## Pass 19 - Core UI Compatibility and Neo Tool Cull

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z-4_Merovingian/core/ui/__init__.py` | Still imported deleted pre-bento UI modules directly, causing `core.ui` to degrade during smoke. | Rewritten as a compact compatibility namespace that extends to Trinity/Construct UI roots and only optional-imports live surfaces. | Restores `core.ui` as a stable import path without reviving old full UI modules. |
| `Z Axis/Z-4_Merovingian/core/ui/spherical_ui.py` | Deleted pre-bento implementation left one active Construct workspace import unresolved. | Added a thin compatibility bridge backed by `EnhancedSphericalGlassUI`. | Active workspace layout code now loads while preserving the smaller UI stack. |
| `tests/test_health.py` | Event bus latency test measured async thread startup against a 10 ms synchronous bus budget. | Switched the test to direct `Event` dispatch with `async_mode=False` and explicit delivery assertion. | Removes a noisy single-sample timing false negative while still proving dispatch health. |
| `Z Axis/Z+2_Neo/components/ai_tool_integration.py` | Generic pre-April tool-integration GUI not loaded by Neo manifest or root coordinator, only package-exported. | Deleted after bounded reference check. | Removes an isolated assistant/tool panel in favor of the current Achilles/Cognigrex governed action runtime. |
| `Z Axis/Z+2_Neo/components/__init__.py` | Exported the deleted generic tool-integration symbols. | Removed stale exports/imports. | Neo component package now reflects active Achilles/Cognigrex components more closely. |

## Next Consolidation Execution List

## Pass 20 - Construct Component Export Cull

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z0_TheConstruct/components/TheConstruct_portal_glass.py` | Standalone old Construct portal surface, only self-referenced and package-exported; active root coordinator uses `construct_dashboard_glass.py`. | Deleted after bounded reference check. | Removes a duplicate Construct portal implementation without touching the active dashboard or manifest components. |
| `Z Axis/Z0_TheConstruct/components/__init__.py` | Exported the standalone portal alongside active dashboard/workspace/visualization/service surfaces. | Removed `PortalTheme` and `TheConstructPortalGlass` exports/imports. | Construct component package now exposes active dashboard, workspace portal, core service provider, and visualization objects only. |
| `Z Axis/Z0_TheConstruct/components/construct_dashboard_glass.py` | Unmanifested but actively loaded by root `Z Axis/TheConstruct.py`. | Preserved. | Kept as the active holospace dashboard surface. |
| `Z Axis/Z0_TheConstruct/components/TheConstructCoreComponent.py` | Not in `components[]` but declared as manifest service provider. | Preserved. | Kept as active service-provider contract. |

## Next Consolidation Execution List

## Pass 21 - Trinity UI Standalone Surface Cull

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z+3_Trinity/ui/calculator_inventory.py` | Standalone calculator inventory panel with no bounded external references. | Deleted. | Removes a detached inventory view; calculator knowledge remains under Oracle/Construct catalogs. |
| `Z Axis/Z+3_Trinity/ui/enhanced_settings_manager.py` | Alternate settings manager shell with no bounded external references. | Deleted. | Keeps settings ownership on the active settings dialog, smart settings hub, and runtime contracts. |
| `Z Axis/Z+3_Trinity/ui/oasis_aesthetic_system.py` | Demo/reference aesthetic module with no active imports; current UI contract is held by Trinity runtime artifacts. | Deleted. | Removes a parallel visual language while retaining current glass/bento surfaces. |
| `Z Axis/Z+3_Trinity/ui/floor_widgets_system.py` | Large pre-bento universal floor widget registry with no bounded external references. | Deleted. | Removes a duplicate widget-builder stack; current surfaces use manifest/floor-owned components. |
| `Z Axis/Z+3_Trinity/ui/it_portal_integration_guide.py` | Python-form integration guide with only self-references. | Deleted. | Removes executable documentation that is not part of the active portal path. |
| `Z Axis/Z+3_Trinity/ui/template_manager.py`, `dashboard_widgets.py`, `premium_theme_engine.py`, and `operations_manager_panel.py` | Active root/portal imports. | Preserved. | Avoids breaking current shell and portal workflows. |

## Next Consolidation Execution List

## Pass 22 - Neo Duplicate Portal Cull

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z+2_Neo/components/Neo_portal_glass.py` | Standalone Neo portal surface, only self-referenced and package-exported; active coordinator uses `neo_lab_assistant_glass.py`. | Deleted after bounded reference check. | Removes a duplicate Neo UI shell while keeping the Achilles/Cognigrex operator console. |
| `Z Axis/Z+2_Neo/components/__init__.py` | Exported the standalone portal symbols. | Removed `PortalTheme` and `NeoPortalGlass` exports/imports. | Neo component package now exposes active assistant/context/training/orchestrator/Cognigrex/Romer surfaces plus the service provider. |
| `Z Axis/Z+2_Neo/components/NeoCoreComponent.py` | Service-provider contract from manifest `services[].provider`. | Preserved. | Keeps the explicit floor service-provider object available for later loader/service work. |

## Next Consolidation Execution List

## Pass 23 - Merovingian Project Workspace Contract Refresh

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z-4_Merovingian/core/project_workspace/__init__.py` | Stale `0.9.5` package metadata only exported workspace creator/type helpers while active Construct code still reached into module-specific imports for component pulling, layout, and validation. | Updated the package contract to `5.1.2` and exported active component-puller, spherical-layout, and schema-validator factories/classes. | Keeps the Merovingian project-workspace surface current without restoring old standalone UI shells. |
| `Z Axis/Z0_TheConstruct/components/project_workspace_portal.py` | Imported workspace helper factories through deeper module-specific paths. | Switched the portal to consume the package-level contract. | TheConstruct now depends on one Merovingian project-workspace API surface. |
| `tests/test_runtime_package.py` | No regression coverage for the package-level Construct workspace exports. | Added a focused export-contract test. | Future cleanup cannot silently remove the active workspace factories from `core.project_workspace`. |

## Next Consolidation Execution List

## Pass 24 - Merovingian Project Workspace Header Alignment

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z-4_Merovingian/core/project_workspace/component_puller.py` | Stale v1 header and old `Z-stack` wording. | Updated to v5.1.2 active Z-axis smart-floor wording. | Component-puller metadata now matches current floor-owned architecture. |
| `Z Axis/Z-4_Merovingian/core/project_workspace/spherical_layout.py` | Described itself as extending the old `core/ui/spherical_ui.py` implementation. | Reframed as a bridge over the compact Merovingian compatibility UI. | Documents the actual reduced UI dependency instead of implying the full legacy spherical stack exists. |
| `Z Axis/Z-4_Merovingian/core/project_workspace/schema_validator.py` | Stale v1 header and date. | Updated to v5.1.2 governed-workspace wording. | Keeps validation module metadata current without changing validation behavior. |
| `Z Axis/Z-4_Merovingian/core/project_workspace/workspace_creator.py` | Stale v1 header and old `Z-stack` wording. | Updated to current Z-axis smart-floor language. | Workspace creator now reflects the active architecture while preserving runtime schema definitions. |
| `Z Axis/Z-4_Merovingian/core/project_workspace/workspace_types.py` | Stale v1 header and date. | Updated to v5.1.2 Construct scenario/project-shell wording. | Workspace type contracts are now current at the package metadata level. |

## Next Consolidation Execution List

## Pass 25 - Trinity Active UI Metadata Alignment

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z+3_Trinity/ui/glass_theme_manager.py`, `glass_ui.py`, and `icon_library_glass.py` | Active glass/theme modules carried pre-finalization version/date headers. | Updated headers to the current `5.1.2` baseline. | Active glass UI surfaces no longer advertise old build metadata. |
| `Z Axis/Z+3_Trinity/ui/immersive_interface.py` and `spherical_projection.py` | Active immersive launcher/projection modules carried old `0.9.5` metadata and a stale standalone window title. | Updated metadata and standalone title to `LightSpeed 5.1.2`. | Holospace/immersive paths align with the current application baseline. |
| `Z Axis/Z+3_Trinity/ui/settings_manager.py`, `smart_settings_hub.py`, `smart_theme.py`, and `template_manager.py` | Active settings/template/theme modules carried old `0.9.x` metadata and Smart Settings still displayed the old build date. | Updated metadata and visible Smart Settings about fields to `5.1.2` / `April 8, 2026`. | Trinity setup/settings surfaces now present one current baseline. |
| `Z Axis/Z+3_Trinity/ui/interface_orchestrator.py`, `universal_bento_system.py`, and `widget_registry.py` | Active shell/orchestrator/widget modules carried v1 or `0.9.5` headers. | Updated module headers to current bento/operator-shell wording. | The remaining active Trinity UI core now reads as one current OS layer. |

## Next Consolidation Execution List

1. Run the targeted runtime/health/Z-axis proof loop after Pass 25.
2. Run `python __main__.py --smoke` and `python __main__.py --verify`.
3. Run compact report/cache refresh and confirm `data/generated` remains absent.
4. Continue Trinity UI review by checking for active-runtime output paths that still write outside Z-axis floor-owned roots.
5. Then start the next Merovingian `core/project_workspace` semantic cleanup only where explicit contracts/tests can back the change.

## Pass 26 - Trinity Settings Root Ownership and Shell Shortcut Cleanup

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z+3_Trinity/ui/settings_manager.py` | Defaulted to older root-relative config/log/project paths. | Moved defaults to Trinity-owned settings and Merovingian/Architect floor-owned roots. | Trinity settings now persist under floor ownership instead of root compatibility paths. |
| `Z Axis/Z+3_Trinity/components/settings_dialog.py` | Fell back to a root-relative settings file with a schema separate from the active settings manager. | Redirected the default dialog state into Trinity-owned settings storage. | The dialog keeps its legacy schema without colliding with the unified settings file. |
| `Z Axis/Z+3_Trinity/components/theme_switcher.py` | Wrote custom themes and active-theme state into older generic roots. | Moved custom themes to Trinity-owned theme storage and active theme state into Trinity settings. | Theme persistence now stays under Trinity-owned roots. |
| `N.py` | Still exposed a root `projects` fallback and a duplicate `Ctrl+S` settings shortcut. | Switched project fallbacks to Architect-owned projects, removed `Ctrl+S`, and clarified settings/help text. | The shell now follows the Z-axis ownership model and standard desktop settings shortcut. |
| `Z Axis/Z+3_Trinity/ui/it_portal.py` | Exposed duplicate settings/themes/templates launchers and a legacy settings-window fallback. | Reduced the shortcut strip, routed settings to page-local controls, and gated the legacy settings window behind an explicit compatibility env var. | Trinity’s operator portal is leaner and less likely to drift into old standalone settings surfaces. |

## Pass 27 - Merovingian Project Workspace Contract Hardening

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z-4_Merovingian/core/project_workspace/workspace_creator.py` | Failed template copies because `shutil` was only imported in delete flow; also emitted non-ASCII workspace summary arrows and repeated schema version literals. | Hoisted `shutil`, normalized summary output to ASCII, centralized schema template versioning, and tightened path typing/load normalization. | Workspace creation and template application are safer on Windows consoles and easier to maintain. |
| `Z Axis/Z-4_Merovingian/core/project_workspace/category_positions.py` | Category defaults were duplicated and drifting between the registry and spherical layout. | Added one shared non-UI category-position source with detached position copies. | Registry auto-placement and spherical layout now share one category map. |
| `Z Axis/Z-4_Merovingian/core/project_workspace/component_puller.py` | Compatible workspace sets drifted from active workspace recommendations and maintained its own category-position map. | Extended the targeted compatibility sets and switched auto-placement to the shared category-position helper. | The live registry better reflects current workspace contracts without restoring deleted components. |
| `Z Axis/Z-4_Merovingian/core/project_workspace/workspace_types.py` and `__init__.py` | Documentation workspace referenced an undiscoverable `help_browser`, and package exports re-exported `WorkspaceType`/`WorkspaceStatus` via the creator module. | Replaced `help_browser` with `documentation_browser` and anchored type exports to `workspace_types.py`. | Package contract now points at live workspace definitions instead of stale aliases. |
| `tests/test_runtime_package.py`, `README.md` | No focused proof for the workspace-creator/template/category-position changes; README still advertised the old runtime baseline. | Added six focused project-workspace regressions and refreshed the validation baselines. | The new contract is covered and the top-level status reflects the current `74/74` and `116/116` proofs. |

## Next Consolidation Execution List

1. Continue the Merovingian `core/project_workspace` cleanup by reducing registry/config drift for recommended components that still have no live registry entry.
2. Sweep remaining active-root output and settings fallbacks outside Z-axis floor-owned roots, starting with older compatibility aliases rather than live floor data.
3. Collapse Trinity settings/theme/template affordances further into page-local toggles and modal flows, not extra launcher strips.
4. Run the same bounded proof loop after each slice: targeted pytest, `python __main__.py --smoke`, `python __main__.py --verify`, compact refresh.
5. Keep `verify_launch_ready.py --quick` parked until its stall is fixed; continue using `python __main__.py --verify` as the non-stalling verifier.

## Pass 28 - Compatibility Path Ownership Cleanup

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `lightspeed_runtime/storage_paths.py` | Canonical runtime ownership helpers were still mixed with legacy root-level compatibility reads in ways that obscured the true owner roots. | Kept legacy reads as fallback, but anchored canonical runtime reservoirs, intermediary targets, and AI settings to Oracle/Architect-owned config roots. | Active writes now resolve to Z-axis floor ownership while compatibility reads remain available. |
| `lightspeed_runtime/ai_settings.py` | AI settings save/load behavior depended on compatibility resolution but was not explicitly proofed against the Architect-owned canonical path. | Kept save behavior on the Architect-owned config root and preserved legacy read fallback. | New AI settings writes stay under Architect ownership. |
| `lightspeed_runtime/runtime.py`, `lightspeed_runtime/assimilation.py`, and `Z Axis/Z-4_Merovingian/core/config/paths.py` | Runtime and Merovingian path surfaces needed explicit proof that the canonical config roots were floor-owned. | Aligned the runtime-facing and Merovingian-facing path contracts to the same Oracle/Architect canonical targets. | Floor-owned config paths are now one consistent contract across runtime, assimilation, and core paths. |
| `tests/test_path_ownership_contracts.py` | No dedicated proof file existed for canonical-vs-legacy config ownership rules. | Added focused path-ownership contract tests. | The compatibility cleanup is now regression-covered outside the larger runtime package suite. |

## Pass 29 - Merovingian Project Workspace Registry Alignment

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z-4_Merovingian/core/project_workspace/workspace_types.py` | Workspace defaults still recommended several stale component ids with no live registry entry. | Reduced recommendations/templates to registry-backed live surfaces and kept documentation defaults on `documentation_browser`. | Creator-side workspace defaults now point at active contract surfaces instead of dead ids. |
| `Z Axis/Z-4_Merovingian/core/project_workspace/component_puller.py` | Registry coverage still lagged behind some live workspace defaults. | Added/aligned live entries for performance/task/archive/documentation/model/timeline/milestone/theme/chart surfaces and kept the workspace compatibility extensions in place. | Registry-backed workspace creation is now closer to the actual floor-owned live surface set. |
| `tests/test_project_workspace_contracts.py` | No standalone contract proof existed for registry-backed recommendations/templates and creator floor lookup. | Added focused contract tests for registry coverage, template coverage, creator floor lookup, and active metadata routing. | The project-workspace contract can now be reduced further with tighter proof. |

## Pass 30 - Trinity Settings and Portal Consolidation

| File | Previous State | Action | Result |
| --- | --- | --- | --- |
| `Z Axis/Z+3_Trinity/ui/it_portal.py` | Trinity still exposed duplicate theme/template/wizard jump routes alongside the main Settings Hub. | Collapsed the Trinity jump set to `Portal`, `Bento System`, and `Settings Hub`, with page-local actions for the rest. | Operator-facing Trinity navigation is leaner and less duplicative. |
| `Z Axis/Z+3_Trinity/ui/smart_settings_hub.py` | Wizards still opened as a separate surface, and theme/template actions were scattered. | Moved setup actions inline on the System tab and added a dedicated Trinity section for theme/template entry points. | Settings/setup flows are more consolidated inside the floor-owned hub. |
| `Z Axis/Z+3_Trinity/ui/template_manager.py` | Separate `Create Blank` and `From Template` launcher buttons duplicated one workflow. | Replaced them with a page-local generation mode toggle and one `Generate Output` action. | Template generation is simpler and more consistent with the no-extra-pages rule. |
| `Z Axis/Z+3_Trinity/components/trinity_portal_glass.py` | The Settings tab was still closer to a placeholder than an active control surface. | Replaced it with live refresh controls and page-local actions into settings, theme/templates, and setup tools. | Trinity portal settings now behave like a real in-page operator surface. |
| `tests/test_trinity_ui_contracts.py` | No focused proof existed for the consolidated Trinity operator flows. | Added a dedicated Trinity UI contract test file. | The Trinity consolidation slice is now isolated and regression-covered. |

## Next Consolidation Execution List

1. Continue reducing `workspace_types.py` and `component_puller.py` drift for live workspace defaults that still rely on broad compatibility rather than precise registry-backed contracts.
2. Sweep the remaining runtime/settings compatibility aliases that still fallback to root-level config files and move more of them to explicit floor-owned write/read contracts.
3. Continue Trinity setup/settings consolidation by folding more wizard/profile affordances into the master settings flow instead of separate launchers.
4. Audit floor-root component exports against manifest ownership for Architect, Neo, and Oracle using the same bounded export-vs-live-surface pattern.
5. Keep the proof loop unchanged after each slice: targeted pytest, `python __main__.py --smoke`, `python __main__.py --verify`, compact refresh.
