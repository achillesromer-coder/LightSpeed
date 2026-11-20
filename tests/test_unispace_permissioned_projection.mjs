import test from 'node:test';
import assert from 'node:assert/strict';
import { projectPermissionedObject as project, VIEWPORT_SCHEMA } from '../cgx/review/unispace_permissioned_projection.mjs';
const id = 'cgx:synthetic:object:001';
const child = 'Cognigrex.cgx:/unispace';
const sha = 'a'.repeat(64);
const valid = () => ({
  request: { object_id: id, child_filespace: child, view: 'graph' },
  grant: { issuer_verified: true, session_active: true, revocation_checked: true, root_acl_verified: true, dbr_scope_verified: true, lease_active: true, source_rights_approved: true, object_id: id, child_filespace: child },
  record: { object_id: id, child_filespace: child, source_sha256: sha, source_rights_approved: true, release_class: 'OWNER_PRIVATE', admission_stage: 'SANDBOX_STAGED', evidence_class: 'R2_CANDIDATE', permitted_edge_count: 12, permitted_source_count: 3, qualified_capability_count: 2, raw_original: 'SECRET_SOURCE', source_locator: 'C:\\Private\\secret' },
});
test('schema and exact selected object', () => { const x=project(valid()); assert.equal(x.schema,VIEWPORT_SCHEMA); assert.equal(x.object_id,id); assert.equal(x.primary_view,'graph'); });
test('no session / issuer / ACL / DBR / lease / revocation denies', () => { for(const key of ['issuer_verified','session_active','revocation_checked','root_acl_verified','dbr_scope_verified','lease_active']) { const a=valid(); a.grant[key]=false; assert.equal(project(a).state,'HOLD',key); } });
test('revoked/unknown grant does not reveal object identity', () => { const a=valid(); a.grant.session_active=false; assert.equal(JSON.stringify(project(a)).includes(id),false); });
test('exact Object_ID mismatch denies', () => { const a=valid(); a.request.object_id='cgx:synthetic:other:002'; assert.equal(project(a).reason,'EXACT_SCOPE_MISMATCH'); });
test('cross-child FileSpace mismatch denies', () => { const a=valid(); a.request.child_filespace='Cognigrex.cgx:/eco'; assert.equal(project(a).reason,'EXACT_SCOPE_MISMATCH'); });
test('unqualified source SHA denies', () => { const a=valid(); a.record.source_sha256='not-a-hash'; assert.equal(project(a).reason,'SOURCE_IDENTITY_OR_STAGE_UNQUALIFIED'); });
test('unknown admission stage denies', () => { const a=valid(); a.record.admission_stage='RELEASED'; assert.equal(project(a).state,'HOLD'); });
test('source rights and public class deny private projection', () => { const a=valid(); a.record.release_class='PUBLIC_SAFE'; assert.equal(project(a).state,'HOLD'); });
test('missing geometry falls back with explicit Frontier', () => { const a=valid(); a.request.view='3d'; const x=project(a); assert.equal(x.primary_view,'document'); assert.match(x.frontier,/GEOMETRY/); });
test('source-verified metric geometry permits only a 3d view intent', () => { const a=valid(); a.request.view='3d'; a.record.geometry={source_verified:true,frame:'EPSG:4978',units:'m',metric_validated:true}; const x=project(a); assert.equal(x.primary_view,'3d'); assert.equal(x.live_host_verified,false); });
test('no original, locator, credential, authority or arbitrary fields leak', () => { const x=JSON.stringify(project(valid())); for(const word of ['SECRET_SOURCE','Private','source_sha256','issuer_verified','raw_original','source_locator']) assert.equal(x.includes(word),false,word); });
test('H0-H4 only, bounded counts, never executable', () => { const a=valid(); a.record.permitted_edge_count=1e9; const x=project(a); assert.deepEqual(x.layers.map(l=>l.id),['H0','H1','H2','H3','H4']); assert.equal(x.layers[1].count,10000); assert.equal(x.execution_available,false); assert.equal(x.canonical_mutation,false); });
test('invalid view falls back without semantic mutation', () => { const a=valid(); a.request.view='execute'; assert.equal(project(a).primary_view,'document'); });
test('empty input is opaque hold', () => { assert.equal(project().state,'HOLD'); });
