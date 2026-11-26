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