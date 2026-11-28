import {test} from 'vitest';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const ui=readFileSync(new URL('./tir173PublicPreview.ts',import.meta.url),'utf8');
test('the existing GUIOS object view reuses TIR173/LOAD/atlas intent binding, not another tab',()=>{
 assert.match(ui,/tir173_intent_binding\.mjs/);
 assert.match(ui,/id="tir-intent-command"/);
 assert.match(ui,/id="tir-intent-human"/);
 assert.match(ui,/bindTirIntentToExistingPlans\(d,cap,lens\.context,/);
 assert.match(ui,/loadPlan,atlas:componentAtlas,atlasSelection:/);
 assert.match(ui,/intent_binding_review:intentBinding/);
 assert.doesNotMatch(ui,/id="view-shorthand"|data-view="shorthand"/);
});
test('human and machine command reviews derive from one source-bound adapter',()=>{
 assert.match(ui,/intentBinding\.human\.summary/);
 assert.match(ui,/intentBinding\.human\.interpretation/);
 assert.match(ui,/intentBinding\.machine\.status/);
 assert.match(ui,/intent_binding_review:intentBinding,archetype_review:archetypeReview,instance_review:instanceReview,negative_space/);
 assert.match(ui,/intentInput\.addEventListener\('input',display\)/);
 assert.match(ui,/choose\.addEventListener\('change'/);
 assert.doesNotMatch(ui,/eval\(|new Function\(/);
});

test('the same GUIOS object view presents the original 411-component archetype evidence boundary',()=>{
 assert.match(ui,/tir173_archetype_evidence\.mjs/);
 assert.match(ui,/component_geometry_atlas_v0_1\.json\?raw/);
 assert.match(ui,/component_physical_proof_ladder_v0_1\.json\?raw/);
 assert.match(ui,/component_instance_build_packet_contract_v0_1\.json\?raw/);
 assert.match(ui,/id="tir-archetype"/);
 assert.match(ui,/id="tir-archetype-review"/);
 assert.match(ui,/archetype_id:archetypeSelect\.value\|\|null/);
 assert.match(ui,/reviewTirComponentArchetype\(d,cap,geometryAtlas,physicalProof,instanceContract/);
 assert.match(ui,/archetype_review:archetypeReview,negative_space/);
 assert.match(ui,/archetypeSelect\.append\(none\)/);
 assert.match(ui,/archetypeSelect\.addEventListener|ruleSelect,archetypeSelect/);
 assert.doesNotMatch(ui,/data-view="geometry-archetypes"|id="view-geometry-archetypes"/);
});
test('unresolved empirical status remains legible beside human and machine identity',()=>{
 assert.match(ui,/archetypeReview\.human\.interpretation/);
 assert.match(ui,/archetypeReview\.human\.physical_state/);
 assert.match(ui,/archetypeReview\.human\.proof_stages/);
 assert.match(ui,/source_claims:\{geometry_atlas_sha256:geometryDigest/);
 assert.match(ui,/intent_binding_review:intentBinding,archetype_review:archetypeReview/);
});

test('existing GUIOS adds exactly matched eight-instance evidence without new tabs or automatic binding',()=>{
 assert.match(ui,/component_instance_population_v0_1\.json\?raw/);
 assert.match(ui,/reviewTirExistingInstance/);
 assert.match(ui,/id="tir-instance"/);
 assert.match(ui,/id="tir-instance-review"/);
 assert.match(ui,/record\.archetype_id!==archetypeSelect\.value/);
 assert.match(ui,/empty\.value=''/);
 assert.match(ui,/archetypeSelect\.addEventListener\('change',\(\)=>\{syncInstanceOptions\(\);display\(\);\}\)/);
 assert.match(ui,/instance_id:instanceSelect\.value\|\|null/);
 assert.match(ui,/instance_register_sha256:populationDigest/);
 assert.match(ui,/instance_review:instanceReview,negative_space/);
 assert.doesNotMatch(ui,/data-view="cgx-instances"|id="view-cgx-instances"/);
});
test('instance review human and machine projections are the same source-scoped result',()=>{
 assert.match(ui,/instanceReview\.human\.summary/);
 assert.match(ui,/instanceReview\.human\.interpretation/);
 assert.match(ui,/instanceReview\.human\.next_binding/);
 assert.match(ui,/instance_review:ReturnType<typeof reviewTirExistingInstance>/);
 assert.match(ui,/instanceSelect\]\)x\.addEventListener\('change',display\)/);
 assert.match(ui,/syncInstanceOptions\(\);\s*display\(\);\s*\}/);
});
