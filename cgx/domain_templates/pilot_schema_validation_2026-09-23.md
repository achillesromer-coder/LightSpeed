# CGX Pilot Schema Validation — Mark III / Embedded Bio Blocks / RFS-EMFF — 2026-09-23

Status: review evidence. No source workbook or carrier mutation.

## Purpose

Use the three first-file pilots to test whether the semantic contracts can absorb real current corpus structures without copying workbook tab layouts into CGX.

## 1. Mark III → Romer.cgx

Observed source families:
- claims/requirements;
- architecture and component/BOM;
- module geometry/parameters;
- RFS/EMFF/Free Flow/Solar Hull interfaces;
- sample process/control flow;
- environment/load cases;
- tests, calibration and validation gates;
- FMEA;
- source/provenance and publication view.

Natural CGX mapping:
- sheet rows become typed objects/cells, not permanent sheets;
- components → `component`;
- architecture rows → components/functions/interfaces/relations;
- geometry rows → `parameter` Universal Cells with units + formula/method + epistemic state;
- claims → `claim` linked to required evidence/gates;
- tests → `test` / `test-run`;
- FMEA rows → `failure-mode` + risk/mitigation;
- mission/environment rows → `environment` / `load-case`;
- process flow → `process-step` graph.

Useful new common relations exposed by pilot:
`PRECEDES`, `USES_INPUT`, `PRODUCES_OUTPUT`, `USES_CONTROL`, `GATED_BY`, `HAS_CRITERION`, `MITIGATED_BY`, `CAUSES`, `AFFECTS`.

Recommended default projection:
**Twin/Configuration + Claims/Gates + Components/Interfaces + Test Evidence + FMEA**, with dashboard cell as entry and inspector as detail.

## 2. Embedded Bio Blocks → Eco.cgx

Observed source families:
- intervention/block composition;
- candidate species and functional roles;
- seed/spore placement;
- process/production batches;
- germination, soil/microbiome, nutrient processes;
- site assessment/deployment zones;
- monitoring/field schema;
- biosecurity/regulatory risks;
- validation gates.

Natural CGX mapping:
- block composition → `recipe` + composition component/layer objects and parameter cells;
- each deployed block → intervention instance, not the recipe itself;
- species register → taxon/species + functional-group + site suitability review;
- batch/process → production-batch/process-step;
- site assessment → site-assessment + assessment-criterion values;
- field rows → immutable observations tied to block/recipe/site/time/method;
- biosecurity register → risk/control/gate relations.

Critical rule confirmed:
a later ecological state estimate must never overwrite the underlying observation.

Recommended default projection:
**Site Map + Intervention Recipe + Taxa/Functional/Food-Web + Process + Monitoring Time Series + Biosecurity/Gates**.

## 3. RFS/EMFF → EMASSC.cgx + LS.cgx

Observed source families:
- claims and controlled wording;
- apparatus/system architecture;
- design variables;
- synthetic RFS/EMFF model scenarios;
- integrated hypotheses;
- material/control matrix;
- test protocols;
- sensor/data schema;
- run log;
- calibration and validation gates.

Natural CGX mapping:
- variables → parameter Universal Cells with unit/min/max/method;
- synthetic rows → scenario + simulation-run + model/result cells, permanently marked synthetic/modelled;
- material rows → material-sample/control roles;
- tests → protocol/test/test-run;
- sensor table → data-schema + measurement-field semantics;
- actual execution route → LS host/device/tool/provider/job;
- execution receipt returns evidence input to EMASSC; EMASSC controls validation interpretation.

Numeric-sanity finding:
the current synthetic RFS workbook contains extremely large finite model results in some detuned/control scenarios. This is useful proof that **finite numeric output is not sufficient evidence**. Model/scenario provenance, sanity review, uncertainty and epistemic state must be visible before any result can inform a claim.

Recommended default projection:
**Protocol/Apparatus + Parameters/Model Scenario + Sensor Schema + Run/Evidence + Uncertainty/Validation Gates**, with LS runtime/job receipt available as a secondary view.

## Cross-pilot conclusion

The semantic libraries are adequate if the next registry revision includes:
- explicit domain Type Registries;
- a small shared process/risk relation family;
- configuration/time/site qualifiers;
- claim/evidence/gate linkage;
- model/simulation epistemic handling;
- deterministic domain view profiles.

No new top-level filespace is required by these pilots.
