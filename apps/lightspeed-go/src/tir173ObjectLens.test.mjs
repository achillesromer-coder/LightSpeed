import {test} from 'vitest';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {publicTirDictionary,requestPublicTirLoad} from './tir173PublicPreview';
const source=readFileSync(new URL('../../../docs/agent-ingestion/local-agent-homes/Z+2_Neo/pilots/raphael_temporal/geometry_language/T173_NEO_ROLE_PROJECTION.review.json',import.meta.url));
test('public dictionary binds exact source bytes, not reserialized JSON',async()=>{
 const d=await publicTirDictionary();assert.equal(d.source_sha256,createHash('sha256').update(source).digest('hex'));
 assert.equal(d.roles.length,173);assert.equal(d.sentinel,null);
});
test('public roles cannot fabricate a LOAD context or escalate to hydration',()=>{
 for(const h of ['H0','H1','H2','H3'])for(const offline of [true,false]){
  const out=requestPublicTirLoad('review:public:shape:1',h,offline);
  assert.equal(out.requested_hydration,h);assert.equal(out.planner_result.state,'HOLD');
  assert.equal(out.planner_result.hold_code,'EXACT_OBJECT_CHILD_CONTEXT_UNVERIFIED');
  assert.equal(out.source_hydrated,false);assert.equal(out.native_admitted,false);assert.equal(out.execution_performed,false);
 }
});
test('single lazy Objects inspector, no replacement app or standalone tab',()=>{
 const main=readFileSync(new URL('./main.ts',import.meta.url),'utf8');
 const ui=readFileSync(new URL('./tir173PublicPreview.ts',import.meta.url),'utf8');
 assert.match(main,/<details class="panel" id="tir173-object-inspector">/);
 assert.equal((main.match(/id="tir173-object-mount"/g)||[]).length,1);
 assert.match(main,/import\("\.\/tir173PublicPreview"\)/);
 assert.doesNotMatch(main,/data-view="(?:tir173|geometry|language|physics)"/);
 assert.match(ui,/planAtlasInteraction\(componentAtlas,cap,lens\.context/);
 assert.doesNotMatch(ui,/planned_hydration:h|client_scope_independently_authenticated:false/);
});
