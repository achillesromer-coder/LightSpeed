import {test} from 'vitest';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
const ui=readFileSync(new URL('./tir173PublicPreview.ts',import.meta.url),'utf8');
test('one GUIOS object workbench uses existing physics map in the T173 context, not new tab',()=>{
 assert.match(ui,/component_interaction_map_v0_1\.json/);
 assert.match(ui,/tir173_interaction\.mjs/);
 assert.match(ui,/id="tir-interaction-rule"/);
 assert.match(ui,/id="tir-interaction-review"/);
 assert.match(ui,/planAtlasInteraction\(componentAtlas,cap,lens\.context/);
 assert.match(ui,/source_sha256:atlasDigest/);
 assert.match(ui,/physical_interaction_review:physical/);
 assert.doesNotMatch(ui,/id="view-physics"|data-view="physics"/);
});
test('owner-selected Neo triad stays inside existing GUIOS object inspector without native authority',()=>{
 assert.match(ui,/tir173_neo_review_import\\.mjs/);
 assert.match(ui,/id="tir-neo-file"/);
 assert.match(ui,/id="tir-neo-case"/);
 assert.match(ui,/id="tir-neo-human"/);
 assert.match(ui,/id="tir-neo-machine"/);
 assert.match(ui,/reviewLocalNeoBatch\\(JSON\\.parse\\(raw\\)\\)/);
 assert.match(ui,/file\\.size>200_000/);
 assert.match(ui,/file\\.text\\(\\)/);
 assert.match(ui,/localReview=validated/);
 assert.match(ui,/UNTRUSTED_LOCAL_PREVIEW_ONLY/);
 assert.match(ui,/model_weights_verified_by_browser:false/);
 assert.match(ui,/neoCase\\.addEventListener\\('change',showLocalReview\\)/);
 assert.doesNotMatch(ui,/id="view-neo-model"|data-view="neo-model"/);
});
