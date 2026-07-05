# LightSpeed 3x50 Execution Matrix

Canonical source: `C:\Users\acc\Desktop\LightSpeed Consolidated\LightSpeed`

Snapshot target: `D:\LightSpeed_Consolidated`

Status:
- Completed: `2026-04-10`
- Progress: `150/150` tasks exhausted
- Validation:
  - `python -m pytest tests/test_config_contracts.py tests/test_path_ownership_contracts.py tests/test_oracle_data_contracts.py tests/test_runtime_package.py -q` -> `100/100`
  - `python N.py --smoke` -> passed, `8/8` floors initialized
  - `python __main__.py --verify` -> passed, root hygiene OK
- Closure note: restored the zero-byte `Z Axis/Z-1_Morpheus/components/morpheus_portal_glass.py` file as a compact runtime-backed review panel during final proof.

Policy:
- C-root is the source of truth.
- D-root is publish/snapshot output only.
- Tasks are grouped into 3 disjoint execution tracks.
- Workers must not revert each other.

## Track A: UI / Operator OS

1. Audit shell header duplicates.
2. Collapse redundant shell actions into grouped rows.
3. Remove blank or placeholder page surfaces.
4. Move page-local settings into menus or pop-ups.
5. Reduce long flat button rows in `N.py`.
6. Normalize primary and secondary action wording.
7. Standardize `Workspace / Operator / Holospace` language.
8. Restrict WASD messaging to immersive surfaces.
9. Standardize page headers to `title / status / actions / menu`.
10. Standardize compact status cards in runtime adapters.
11. Ensure Oracle opens curated cards before raw JSON.
12. Ensure Morpheus defaults to review cards before inspectors.
13. Reduce raw source visibility in default UI states.
14. Standardize provenance and source actions into compact menus.
15. Tighten Neo wording around Achilles and Cognigrex.
16. Reduce duplicated Neo assistant panels.
17. Fold generic assistant surfaces into one bounded Neo console.
18. Collapse Trinity setup sprawl into modal and toggle flows.
19. Remove duplicate Trinity settings affordances.
20. Consolidate Trinity theme actions into one route.
21. Consolidate Trinity template controls into one route.
22. Ensure IT portal tabs map cleanly to owner floors.
23. Make Architect, Neo, and Trinity handoff copy consistent.
24. Tighten Morpheus review actions into grouped workflow bars.
25. Ensure Oracle and Morpheus proofing language is definition-first.
26. Make status labels readable and non-migration-oriented.
27. Simplify tool-runner wording to operator OS language.
28. Replace raw JSON panes with summaries where easy.
29. Make drawer and modal behavior consistent.
30. Simplify shell help text for shortcuts and settings.
31. Keep `Ctrl+,` as settings entrypoint.
32. Remove stale tab-centric language where operator OS menus are current.
33. Ensure Trinity labels settings and setup as master surface.
34. Tighten Neo lab and project planning actions into bounded proposals.
35. Tighten Morpheus import/export review phrasing.
36. Make Oracle action names reflect proof, promotion, and catalog work.
37. Reduce noisy migration wording in user-facing surfaces.
38. Standardize footer, help, and status hints.
39. Make popup and panel labels consistent with the curved bento wall.
40. Keep bento stack terminology consistent.
41. Remove isolated one-off buttons where grouped actions suffice.
42. Improve menu density without adding pages.
43. Keep disabled actions explicit rather than hidden.
44. Surface missing dependencies gracefully in the shell.
45. Reduce launcher-level feature sprawl by routing to hosted actions.
46. Keep floor launch affordances aligned with owner responsibilities.
47. Tighten visual hierarchy in touched glass components.
48. Update inline docs/comments only where grouping is non-obvious.
49. Run targeted tests for touched surfaces.
50. Summarize changed files, tests, blockers, and completed task numbers.

## Track B: Framework / Runtime Contracts

1. Remove stale D-root assumptions from C-root runtime logic.
2. Make C-root canonical and D-root snapshot-only in touched code.
3. Centralize path resolution for publish, snapshot, and export outputs.
4. Add an explicit publish snapshot contract for D-root overwrite flow.
5. Normalize runtime config resolution with canonical and legacy fallback order.
6. Ensure AI settings loader handles hardened schema cleanly.
7. Ensure intermediary targets are owner-floor aware.
8. Ensure runtime reservoirs accept proofed source fields.
9. Reduce any flat `data/generated` assumptions that remain.
10. Confirm Merovingian log and activity ownership everywhere touched.
11. Confirm Architect publish ownership everywhere touched.
12. Confirm Trinity settings ownership everywhere touched.
13. Confirm Smith router ownership everywhere touched.
14. Add compact runtime summaries for new config contracts where useful.
15. Tighten execution queue loading to canonical Architect roots only.
16. Tighten closure and finalization summaries.
17. Improve activity table summarization without duplicating raw event noise.
18. Standardize snapshot and publish terminology.
19. Ensure runtime exports are generated on demand.
20. Tighten bootstrap outputs to show canonical vs snapshot destinations.
21. Tighten Smith router contracts for bounded jobs and proofing actions.
22. Improve governance ledger action classes where touched.
23. Improve missing canonical config field handling.
24. Preserve compatibility for older fields where still referenced.
25. Remove clearly dead compatibility code.
26. Standardize floor terminology across touched runtime modules.
27. Tighten function-first comments and docs in touched modules.
28. Ensure helper paths prefer Z-axis owner roots.
29. Ensure runtime modules do not recreate flat compatibility roots.
30. Make snapshot publishing explicit rather than accidental.
31. Add/update tests for config contract loading.
32. Add/update tests for path ownership.
33. Add/update tests for runtime summaries.
34. Add/update tests for closure/finalization status.
35. Add/update tests for activity table contract.
36. Keep tests targeted and fast.
37. Avoid adding new generated artifacts.
38. Remove obsolete helper code only when safe.
39. Simplify duplicated normalizers.
40. Standardize field names in touched runtime payloads.
41. Improve docstrings for canonical vs snapshot behavior.
42. Ensure bootstrap and runtime degrade cleanly if snapshot target is absent.
43. Avoid breaking smoke and verify flows.
44. Validate changed Python files compile.
45. Run targeted pytest for touched runtime areas.
46. Run `__main__.py --smoke` if warranted.
47. Note blockers requiring UI or data follow-up.
48. Summarize completed task numbers.
49. List exact changed files.
50. Report tests run and residual risks.

## Track C: Oracle / Data / Provenance / Simulation

1. Tighten proofed definition usage so Oracle summaries rely on definitions.
2. Improve source label, definition, and operator note propagation.
3. Ensure dataset catalog shells expose owner floor and usage role.
4. Tighten source-type definitions and fallback descriptions.
5. Reduce raw-source-first behavior in data payloads.
6. Ensure knowns promotion records carry confidence and basis consistently.
7. Tighten proofing queue object schema.
8. Improve knowns registry summaries for operator use.
9. Improve empirical catalog summaries around clusterable inputs.
10. Ensure empirical layer flows cleanly into proofing and simulation.
11. Tighten dataset roles: raw, reference, curated, derived, simulation, publish.
12. Improve scientific query templates toward curated table access.
13. Tighten query payload summaries for operator readability.
14. Strengthen unit validation metadata.
15. Tighten entity registry coverage for datasets, tables, artifacts, and runs.
16. Ensure Oracle definition library and knowns stay aligned.
17. Reduce duplicated theme and term definition logic.
18. Improve provenance payloads to favor compact evidence summaries.
19. Keep raw file paths behind provenance links.
20. Improve GMAT target batch or zoning output metadata.
21. Tighten simulation preset summaries for Romer-first usage.
22. Ensure TheConstruct presets draw from empirical and proofed sources.
23. Improve shortlist metadata for publishability and handoff.
24. Ensure Architect-facing artifacts have concise metadata where touched.
25. Improve knowns declassification audit summaries where touched.
26. Ensure AI logs remain corroboration-only in payload wording.
27. Standardize floor owner naming in data payloads.
28. Standardize confidence labels.
29. Standardize `generated_at` and `report_path` fields.
30. Remove stale or noisy payload fields when redundant.
31. Avoid writing unnecessary generated artifacts.
32. Add/update tests for definition proofing.
33. Add/update tests for dataset catalog or runtime reservoirs use.
34. Add/update tests for scientific query layer.
35. Add/update tests for knowns promotion and proofing.
36. Add/update tests for zoning metadata.
37. Keep tests targeted and fast.
38. Validate changed Python files compile.
39. Run targeted pytest for touched data/runtime areas.
40. Note source roots that still need assimilation.
41. Identify payloads still too raw or mention-driven.
42. Reduce duplicate metadata between Oracle and TheConstruct.
43. Improve comments/docs in non-obvious data-contract code only.
44. Preserve current smoke compatibility.
45. Keep changes C-root canonical only.
46. Do not introduce D-root coupling.
47. Summarize completed task numbers.
48. List exact changed files.
49. Report tests run.
50. Report blockers and next best follow-ups.
