import {test} from 'vitest';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const ui=readFileSync(new URL('./tir173PublicPreview.ts',import.meta.url),'utf8');
test('TIR173 exact command review belongs to the existing GUIOS object, not a new tab',()=>{
 assert.match(ui,/tir173_intent_guard\.mjs/);
 assert.match(ui,/id="tir-intent-command"/);
 assert.match(ui,/id="tir-intent-human"/);
 assert.match(ui,/inspectTir173Intent\(d,intentInput\.value,\{expected_role:cap\.shape_role\}\)/);
 assert.match(ui,/intent_review:intentReview/);
 assert.doesNotMatch(ui,/id="view-shorthand"|data-view="shorthand"/);
});
test('human and machine command reviews derive from the same state and never execute',()=>{
 assert.match(ui,/intentReview\.human\.summary/);
 assert.match(ui,/intentReview\.human\.status/);
 assert.match(ui,/intent_review:intentReview,negative_space/);
 assert.match(ui,/intentInput\.addEventListener\('input',display\)/);
 assert.match(ui,/choose\.addEventListener\('change'/);
 assert.doesNotMatch(ui,/eval\(|new Function\(/);
});
