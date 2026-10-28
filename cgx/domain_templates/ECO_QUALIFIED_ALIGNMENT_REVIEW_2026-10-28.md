# Eco.cgx qualified ecological alignment — additive review guard

**State:** GIT SOURCE ONLY / R1–R2 CANDIDATE. This file is an Eco-specific qualification adapter for the existing Cognigrex.cgx Family Set, not a replacement for the shared LOAD.cgx aligner, source registry, CCC router or native Resolve/DBR path.

## Evidence sources reviewed

- Existing `cgx/domain_templates/eco_semantic_library.json` (main Git blob `d4eac3fd93f8c85f0385718355b47d59556aa1ec`) distinguishes taxon, species, population, sample, observation, place, experiment and ecological state.
- Draft LOAD PR #205 `cgx/load_minimum/loadQualifiedKnowledge.mjs` (blob `7aa2d77ad026303ce28491e421ff1f836a309c2a`) checks type, dimensions, units, frame, configuration and epoch but has no ecological-specific taxon/specimen/observation context comparisons.
- Current Type 1 Eco-Grex Drive source manifest lists distinct Embedded Bio Blocks and Second Cycle originals. The field-data schema provides example device, site, observation, method, unit and temporal fields; its examples **are not observed ecological measurements**.
- The original EcoX control index retains a pending raw canonical workbook publication, uncompleted gates and no overarching-suite activation. This code does not depend on the missing workbook.
- Exact original GPT export shards 000–011 are not verified. A separate accessible `Conversations` folder has six large plain-text files (69–186 MB each) but no source-qualified equivalence to the requested shards; do not ingest these in this bounded run. The two folders `manual` and `manual-additions` inside `CGX Domain Skeletons 2026-09-21` are empty and are not evidence of an authoritative CGX MANUAL INTAKE.

## Contract

`planEcoAlignment` accepts explicitly permitted source and known-object IDs, rejects duplicate authorised IDs, discriminates subject/taxon/specimen/population/site/station identity, geospatial CRS and point, time, evidence class, method, units, measurement and environmental context. It marks missing mandatory observation metadata. Geometry is a source-declared point only; no interpolation, CRS transform, inferred 3D, map reconstruction or environmental impact simulation.

All outputs are source-only. A typed alignment candidate never means the objects are identical, rights-cleared, measured, accepted or safe to release. Integration with the shared LOAD plan must remain a *review gate*, not a parallel source of canonical authority. No original source is copied into this repository.

## Reproduce

~~~sh
node --test cgx/domain_templates/eco_qualified_alignment.test.mjs
~~~

Twenty synthetic cases cover distinct taxon/specimen/coordinates/evidence/time/method/environment/units, missing observation metadata, invalid coordinates, 3D vertical datum, permissions, duplicate IDs and no automatic native promotion. These are **source-level negative tests**, not host, DBR, field or two-node tests.

## Native integration holds

Source rights/ACL and exact original byte hashes; GPT shard and manual-intake reconciliation; accepted current root and child; source-specific R1 reversible parse and loss report; scoped R2/Frontier/Overlay; independent DBR/root readback; issue #158 public static privacy; issue #161 two-node transfer if requested; ecological measurement and counterevidence before impact claims. No canonical write, installer, live solver or release.
