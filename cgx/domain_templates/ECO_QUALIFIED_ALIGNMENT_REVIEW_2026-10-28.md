# Eco.cgx qualified ecological alignment — additive review guard

**State:** GIT SOURCE ONLY / R1–R2 CANDIDATE. This file is an Eco-specific qualification adapter for the existing Cognigrex.cgx Family Set, not a replacement for the shared LOAD.cgx aligner, source registry, CCC router or native Resolve/DBR path.

## Evidence sources reviewed

- Existing `cgx/domain_templates/eco_semantic_library.json` (main Git blob `d4eac3fd93f8c85f0385718355b47d59556aa1ec`) distinguishes taxon, species, population, sample, observation, place, experiment and ecological state.
- Draft LOAD PR #205 `cgx/load_minimum/loadQualifiedKnowledge.mjs` (blob `7aa2d77ad026303ce28491e421ff1f836a309c2a`) checks type, dimensions, units, frame, configuration and epoch but has no ecological-specific taxon/specimen/observation context comparisons.
- Current Type 1 Eco-Grex Drive source manifest lists distinct Embedded Bio Blocks and Second Cycle originals. The field-data schema provides example device, site, observation, method, unit and temporal fields; its examples **are not observed ecological measurements**.
- The original EcoX control index retains a pending raw canonical workbook publication, uncompleted gates and no overarching-suite activation. This code does not depend on the missing workbook.
- Exact original GPT export shards 000–011 are not verified. A separate accessible `Conversations` folder has six large plain-text files (69–186 MB each) but no source-qualified equivalence to the requested shards; do not ingest these in this bounded run. The two folders `manual` and `manual-additions` inside `CGX Domain Skeletons 2026-09-21` are empty and are not evidence of an authoritative CGX MANUAL INTAKE.

## Contract

`planEcoAlignment` accepts explicitly permitted source and known-object IDs, rejects duplicate authorised IDs, discriminates subject/taxon/specimen/population/site/station identity, geospatial CRS and point, time, evidence class, method, units, measurement and environmental context. It marks missing mandatory observation metadata, including impossible calendar dates and unzoned timestamps. Geometry is a source-declared point only; no interpolation, CRS transform, inferred 3D, map reconstruction or environmental impact simulation.

Source-lineage review now distinguishes **overlapping permitted references**, **disjoint permitted references**, and **partially authorised reference sets**. Disjoint lineages produce `SOURCE_LINEAGE_DISJOINT_REVIEW`; filtered-out source references produce `NOVEL_SOURCE_SCOPE_PARTIAL` or `KNOWN_SOURCE_SCOPE_PARTIAL`. These are review warnings, not a prohibition on independently corroborated cross-source alignment. No unpermitted source ID or private source body is emitted. Provider ACL visibility does not by itself establish copyright, data reuse, or cultural stewardship rights.

All outputs are source-only. A typed alignment candidate never means the objects are identical, rights-cleared, measured, accepted or safe to release. Integration with the shared LOAD plan must remain a *review gate*, not a parallel source of canonical authority. No original source is copied into this repository.

## Reproduce

~~~sh
node --test cgx/domain_templates/eco_qualified_alignment.test.mjs
~~~

Forty declared Node regression cases cover distinct taxon/specimen/coordinates/evidence/time/method/environment/units, missing observation metadata, invalid coordinates, 3D vertical datum, permissions, duplicate IDs and no automatic native promotion. All 40 committed primary regression test bodies passed in an isolated V8 compatibility harness against the exact read-back module; this is **not a Node CI run or host acceptance**. A same-ID proof-priority regression was detected and corrected before the final passing run. These are **source-level negative tests**, not host, DBR, field or two-node tests.

## Native integration holds

Source rights/ACL and exact original byte hashes; GPT shard and manual-intake reconciliation; accepted current root and child; source-specific R1 reversible parse and loss report; scoped R2/Frontier/Overlay; independent DBR/root readback; issue #158 public static privacy; issue #161 two-node transfer if requested; ecological measurement and counterevidence before impact claims. No canonical write, installer, live solver or release.

## 2026-10-28 additional review gate

A declared observation timestamp such as `2026-02-29T12:00:00Z` (invalid calendar date), `2026-10-01T12:00:00` (no timezone) or an impossible UTC offset now yields `OBSERVATION_TIMESTAMP_INVALID_OR_UNZONED`. Valid leap dates with explicit offsets remain candidates. This is a conservative R1/R2 timestamp qualification, not a conversion or native timestamp resolver. The 40 primary fixtures passed in an isolated V8 compatibility harness; Node CI and host/DBR acceptance must be checked separately.

## Coordinate-frame and unexecuted-QA qualification

A source-declared point geometry CRS and separately declared coordinate frame that disagree require `FRAME_CRS_RECONCILIATION_REQUIRED` until an explicit, source-backed transform relationship is reviewed; this adapter does not transform coordinates. An observation marked `Not run`, `untested` or `pending` cannot pass observation QA simply because values and identifiers are present. One pre-existing measurement-scope fixture incorrectly expected no differences despite deliberately disjoint source references; its positive fixture now uses an overlapping authorised source while separate disjoint-lineage tests remain intact. The complete proposed source-only suite contains **49 synthetic tests** (40 primary + 9 measurement scope). These are compatibility checks, not field evidence or native admission.


## Ecological variable and temporal-support gate — 2026-10-29
The Type 1 Eco-Grex Second Cycle source field schema separately declares `observed_variable`, `native_interval` and conditional `aggregation_period` (source: Drive spreadsheet ID `1kWKbAfHH7ox5Wr8pK0eLXSzlEWdZ8SVqaHvZ-UXuXQU`, sheet `SECON0E3E_19_Field_DataSchema`, rows 21–27). These are schema examples, **not measured data**. Its water-quality schema distinguishes dissolved oxygen, nutrients and other parameters with different method and reporting requirements. The Eco-only review adapter now holds a sensor reading without a declared variable/native interval, requires an aggregation period when average/sum reporting is declared, and distinguishes source-declared variables, native sampling intervals and aggregation periods even if numeric values and units coincide. It does not validate controlled-vocabulary membership, resolve instrument calibration, perform conversions, infer causal effects or promote ecological results. Seven additional synthetic negative/invariant cases are included. No original workbook content was copied into Git.


## Measurement correction and uncertainty qualification — 2026-10-29
The original Type 1 Eco-Grex workbook (Drive ID `1kWKbAfHH7ox5Wr8pK0eLXSzlEWdZ8SVqaHvZ-UXuXQU`, revision metadata `2026-09-28T00:15:14.256Z`) distinguishes DO salinity correction, conductivity/salinity reporting scales, turbidity optical methods and open calibration/QA registers (tabs `SECON0E3E_20_WQ_DataSchema` and `SECON0E3E_21_QA_Calibration`). These are method specifications, **not calibrated field data**. The Eco-only adapter now compares optional source-declared `measurement_basis` (raw/corrected/derived/reference), `correction_method_id`, `measurement_uncertainty` (nonnegative value plus unit) and `uncertainty_basis`. Corrected values lacking a method, uncertainty lacking a basis, and uncertainty/measurement unit contradictions require review. A typed candidate never establishes sensor calibration, correction validity, measurement uncertainty metrology, native admission, ecological efficacy or legal permission. Eight synthetic negative/invariant cases added. Existing originals and shared LOAD PR #205 are unchanged.


## Censored water-quality evidence boundary — 2026-10-29

Original Type 1 Eco-Grex workbook (Drive `1kWKbAfHH7ox5Wr8pK0eLXSzlEWdZ8SVqaHvZ-UXuXQU`, modified 2026-09-28) lists conditional nutrient lab/sample observations in `SECON0E3E_20_WQ_DataSchema` and `uncertainty_or_method_limit` in `SECON0E3E_19_Field_DataSchema`. Neither supplies measured nutrient results or numerical LOD/LOQ. This proposed Eco-only R1/R2 guard distinguishes quantified values from below-LOD, below-LOQ and above-range reports; censored reports need a declared bound type, positive value, unit and method reference. Censored data cannot silently become measured numeric points, including zero; different bounds remain separate variants. Eight synthetic tests added. No rights, ecological efficacy, native admission or installed capability is asserted.

## Validated sensor QA provenance gate — 2026-10-29
The original Type 1 Eco-Grex `SECON0E3E_21_QA_Calibration` tab (Drive ID `1kWKbAfHH7ox5Wr8pK0eLXSzlEWdZ8SVqaHvZ-UXuXQU`, modified `2026-09-28T00:15:14.256Z`) leaves water-quality probe QA `Open` and requires instrument identity, pre-use calibration/verification and traceable checks. The review adapter now flags source-declared `validated`, `verified`, `calibrated`, `qa_pass` or `passed` sensor QA without both an instrument ID and calibration-verification reference. Presence of references does **not** prove that checks passed; original source records, method applicability, rights, and independent review remain required. Two synthetic tests added. No source workbook data, live measurements or native identities were published.
