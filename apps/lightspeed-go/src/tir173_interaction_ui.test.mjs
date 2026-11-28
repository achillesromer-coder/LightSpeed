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
 assert.ok(ui.includes('tir173_neo_review_import.mjs'));
 for(const id of ['tir-neo-file','tir-neo-case','tir-neo-human','tir-neo-machine'])
   assert.ok(ui.includes('id="'+id+'"'),id);
 assert.ok(ui.includes('reviewLocalNeoBatch(JSON.parse(raw))'));
 assert.ok(ui.includes('file.size>200_000'));
 assert.ok(ui.includes('file.text()'));
 assert.ok(ui.includes('localReview=validated'));
 assert.ok(ui.includes('UNTRUSTED_LOCAL_PREVIEW_ONLY'));
 assert.ok(ui.includes('model_weights_verified_by_browser:false'));
 assert.ok(ui.includes("neoCase.addEventListener('change',showLocalReview)"));
 assert.doesNotMatch(ui,/id="view-neo-model"|data-view="neo-model"/);
});
