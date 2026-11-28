import {test} from 'vitest';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('./main.ts',import.meta.url),'utf8');
const preview=readFileSync(new URL('./tir173PublicPreview.ts',import.meta.url),'utf8');
test('single GUIOS workbench has no separate TIR/173 tab or second mount',()=>{
 assert.match(source,/class="shell guios-workbench"/);
 assert.doesNotMatch(source,/data-view="language"|id="view-language"/);
 assert.equal((source.match(/id="tir173-public-preview"/g)||[]).length,1);
 assert.match(source,/<details class="guios-facet" id="guios-objects" open>/);
 assert.match(source,/language: "objects"/);
});
test('existing commands, reviews, system, sources are contextual components of the same shell',()=>{
 for(const id of ['activity','objects','system','sources']) {
  assert.match(source,new RegExp('id="guios-'+id+'"'));
  assert.match(source,new RegExp('id="view-'+id+'"'));
 }
 assert.match(source,/id="view-command"/);
 assert.match(source,/id="command-form"/);
 assert.match(source,/id="owner-login-form"/);
 assert.match(source,/id="node-exchange-panel"/);
});
test('object component exposes context, independent voices, reversible TIR and LOAD review only',()=>{
 for(const t of ['tir-environment','tir-spatial','tir-perspective','tir-scale','tir-intuitive','tir-deliberative','tir-state','tir-hydration']) assert.ok(preview.includes('id="'+t+'"'),t);
 assert.match(preview,/projectGuiosContext/);
 assert.match(preview,/packThreeLines/);
 assert.match(preview,/planExistingLoadTIR/);
 assert.match(preview,/state:'PLAN_ONLY_NOT_HYDRATED'/);
 assert.match(preview,/native_admitted:false/);
});
