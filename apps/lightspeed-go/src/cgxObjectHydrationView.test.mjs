import {test} from 'vitest';
import assert from 'node:assert/strict';
import {projectCgxOneObjectView as plan} from './cgxObjectHydrationView.mjs';
// Object_ID, FileSpace and Git blob SHA are real registry metadata; receipt
// hashes, sessions and rights in this fixture are synthetic, NOT live proof.
const make=()=>({requested_object_id:'cgx:domain:eco',binding:{semantic_object_id:'cgx:domain:eco',filespace:'Eco.cgx'},source:{provider:'github',repository:'achillesromer-coder/LightSpeed',registry_path:'cgx/domain_templates/domain_child_identity_registry.json',registry_git_blob_sha:'c2e03b1137ba844209e6c80e94c9fc7532f0db11',binding_readback_verified:true,rights:'cleared',visibility:'owner_private',source_sha256:'a'.repeat(64),source_bytes_readback_verified:true},access:{state:'verified_owner',allowed_object_ids:['cgx:domain:eco']},evidence:{r1_parse_receipt_sha256:'b'.repeat(64),r2_overlay_receipt_sha256:'c'.repeat(64),r3_view_receipt_sha256:'d'.repeat(64),owner_private_route_verified:true,dbr_readback_verified:true},requested_layer:'R0',max_bytes:4_000_000});
const check=(p,code)=>assert.equal(plan(p).hold_code,code);
test('exact Eco view remains one metadata-only bounded plan',()=>{const v=plan(make());assert.equal(v.object_id,'cgx:domain:eco');assert.equal(v.filespace,'Eco.cgx');assert.equal(v.hydration.max_bytes,1000000);assert.equal(v.state,'PLAN_ONLY_NOT_HYDRATED');assert.equal(v.native_admitted,false);assert.equal(v.source_bytes_included,false);});
test('fuzzy or adjacent identity rejected',()=>{const p=make();p.requested_object_id='cgx:domain:romer';check(p,'EXACT_ID_OR_FILESPACE_MISMATCH');});
test('invalid child FileSpace rejected',()=>{const p=make();p.binding.filespace='../../Eco.cgx';check(p,'EXACT_ID_OR_FILESPACE_MISMATCH');});
test('missing source readback rejected',()=>{const p=make();p.source.binding_readback_verified=false;check(p,'SOURCE_BINDING_UNVERIFIED');});
test('anonymous revoked or mismatched owner scope denied',()=>{for(const state of ['anonymous','revoked','unknown']){const p=make();p.access.state=state;check(p,'ACCESS_NOT_VERIFIED');}const p=make();p.access.allowed_object_ids=['cgx:domain:romer'];check(p,'ACCESS_NOT_VERIFIED');});
test('unresolved rights or visibility denied',()=>{const p=make();p.source.rights='unknown';check(p,'RIGHTS_OR_VISIBILITY_UNRESOLVED');const q=make();q.source.visibility='public';check(q,'RIGHTS_OR_VISIBILITY_UNRESOLVED');});
test('unverified source hash/bytes denied',()=>{const p=make();p.source.source_sha256='bad';check(p,'SOURCE_BYTES_UNVERIFIED');const q=make();q.source.source_bytes_readback_verified=false;check(q,'SOURCE_BYTES_UNVERIFIED');});
test('R1 parser receipt required',()=>{const p=make();p.requested_layer='R1';p.evidence.r1_parse_receipt_sha256='';check(p,'R1_PARSE_UNVERIFIED');});
test('R2 overlay receipt required',()=>{const p=make();p.requested_layer='R2';p.evidence.r2_overlay_receipt_sha256='';check(p,'R2_OVERLAY_UNVERIFIED');});
test('R3 private route and DBR readback required',()=>{const p=make();p.requested_layer='R3';p.evidence.owner_private_route_verified=false;check(p,'R3_PRIVATE_ROUTE_OR_DBR_UNVERIFIED');const q=make();q.requested_layer='R3';q.evidence.dbr_readback_verified=false;check(q,'R3_PRIVATE_ROUTE_OR_DBR_UNVERIFIED');});
test('inline source, URL and tokens forbidden',()=>{for(const key of ['source_bytes','view_url','token']){const p=make();p[key]='SECRET';check(p,'UNSAFE_INLINE_PAYLOAD');}});
test('all layers are plans, never admission or publication',()=>{for(const layer of ['R0','R1','R2','R3']){const p=make();p.requested_layer=layer;const v=plan(p);assert.equal(v.state,'PLAN_ONLY_NOT_HYDRATED');assert.equal(v.public_publish_authorized,false);assert.equal(v.execution_performed,false);}});
test('invalid layer fails closed',()=>{const p=make();p.requested_layer='F';check(p,'UNSUPPORTED_LAYER');});
