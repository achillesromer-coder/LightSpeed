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
 assert.match(ui,/intent_binding_review:intentBinding,negative_space/);
 assert.match(ui,/intentInput\.addEventListener\('input',display\)/);
 assert.match(ui,/choose\.addEventListener\('change'/);
 assert.doesNotMatch(ui,/eval\(|new Function\(/);
});
