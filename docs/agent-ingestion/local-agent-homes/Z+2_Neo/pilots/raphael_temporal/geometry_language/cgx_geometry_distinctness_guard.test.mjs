import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {classifyGeometryClaim,planCapGyration,GeometryEvidenceError} from './cgx_geometry_distinctness_guard.mjs';
const d=JSON.parse(readFileSync(new URL('./T173_NEO_ROLE_PROJECTION.review.json',import.meta.url)));
test('original 131..136 overlays cannot be promoted as polygon boundary faces or proven solids',()=>{
 for(let i=131;i<=136;i++) {
  const role=`T173:${i}`;
  const channels=classifyGeometryClaim(role,d,'functional_channels');
  const faces=classifyGeometryClaim(role,d,'boundary_faces');
  const solid=classifyGeometryClaim(role,d,'distinct_solid');
  assert.equal(channels.verdict,'SOURCE_ROLE_LABEL_ONLY');
  assert.equal(faces.verdict,'NOT_ESTABLISHED');
  assert.equal(solid.assertion_allowed,false);
  assert.equal(faces.native_admitted,false);
 }
});
test('137 is source-bound candidate J72 cap transform, not already a second admitted solid',()=>{
 for(const angle of [-36,36]) {
  const x=planCapGyration('T173:137',angle,d);
  assert.equal(x.base_mesh_ref,'93');assert.equal(x.transform.angle_degrees,angle);
  assert.equal(x.distinctness_proven,false);assert.equal(x.effects_performed,false);
 }
 for(const x of [0,30,72,360])assert.throws(()=>planCapGyration('T173:137',x,d),GeometryEvidenceError);
 for(const x of ['T173:093','T173:174','T173:131'])assert.throws(()=>planCapGyration(x,36,d),GeometryEvidenceError);
});
test('type and authority tampering fail closed',()=>{
 assert.throws(()=>classifyGeometryClaim('T173:137',d,'native_mint'),GeometryEvidenceError);
 let copy=structuredClone(d);copy.slots[136].native_admitted=true;
 assert.throws(()=>classifyGeometryClaim('T173:137',copy,'distinct_solid'),GeometryEvidenceError);
 copy=structuredClone(d);copy.slots[136].slot='T173:136';
 assert.throws(()=>classifyGeometryClaim('T173:137',copy,'distinct_solid'),GeometryEvidenceError);
});
