import { test } from 'node:test';
import assert from 'node:assert/strict';
import { reviewUniSpaceStaticRouteReferences as review } from './cgxUniSpaceStaticRouteReferenceReview.mjs';
const fixture=()=>({
 selection:{parent_filespace:'Cognigrex.cgx',object_id:'WT-001',filespace:'Romer.cgx',identity_status:'SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED',evidence_class:'scientific'},
 client_permissions:{mode:'review_only',revoked:false,allowed_object_ids:['WT-001'],allowed_filespaces:['Romer.cgx']},
 entry_source:'const internalUrl = new URL("./data/internal_review.json", document.baseURI).toString(); void fetch(internalUrl);',
 assets:[{asset_id:'review_catalogue',public_relative_path:'data/internal_review.json',source_class:'INTERNAL_REVIEW',scope:'MULTI_OBJECT',rights:'UNRESOLVED',owner_clearance:false,object_id:null,filespace:null}]
});
test('detects direct fetch of held public asset',()=>{const r=review(fixture());assert.equal(r.referenced_held_asset_count,1);assert.ok(r.assets[0].risk_codes.includes('SOURCE_CODE_FETCHES_HELD_PUBLIC_ASSET'));});
test('source review never grants release',()=>{const r=review(fixture());assert.equal(r.release_accepted,false);assert.equal(r.host_http_verified,false);assert.equal(r.native_admitted,false);});
test('source bytes hashed',()=>assert.match(review(fixture()).source_sha256,/^[a-f0-9]{64}$/));
test('no private paths returned',()=>{const r=JSON.stringify(review(fixture()));assert.ok(!r.includes('internal_review.json'));assert.ok(!r.includes('data/'));});
test('revoked client denied',()=>{const x=fixture();x.client_permissions.revoked=true;assert.equal(review(x).hold_code,'CLIENT_SCOPE_MISMATCH');});
test('cross child denied',()=>{const x=fixture();x.client_permissions.allowed_filespaces=['Eco.cgx'];assert.equal(review(x).state,'HOLD');});
test('wrong Object_ID denied',()=>{const x=fixture();x.selection.object_id='WT-002';assert.equal(review(x).state,'HOLD');});
test('domain parent not object',()=>{const x=fixture();x.selection.object_id='cgx:domain:romer';assert.equal(review(x).state,'HOLD');});
test('unexpected key denied',()=>{const x=fixture();x.token='bad';assert.equal(review(x).state,'HOLD');});
test('asset path traversal denied',()=>{const x=fixture();x.assets[0].public_relative_path='../private.json';assert.equal(review(x).state,'HOLD');});
test('duplicate asset rejected',()=>{const x=fixture();x.assets.push({...x.assets[0]});assert.equal(review(x).state,'HOLD');});
test('duplicate path rejected',()=>{const x=fixture();x.assets.push({...x.assets[0],asset_id:'other'});assert.equal(review(x).state,'HOLD');});
test('unresolved dynamic fetch reported',()=>{const x=fixture();x.entry_source+=' fetch(getDynamicUrl());';assert.equal(review(x).unresolved_fetch_count,1);});
test('unmatched literal fetch reported',()=>{const x=fixture();x.entry_source+=' fetch("./data/unknown.json");';assert.equal(review(x).unmatched_literal_fetch_count,1);});
test('public candidate still not release authority',()=>{const x=fixture();x.assets[0]={...x.assets[0],source_class:'PUBLIC_CANDIDATE',scope:'ONE_OBJECT',rights:'CLEARED_PUBLIC',owner_clearance:true,object_id:'WT-001',filespace:'Romer.cgx'};const r=review(x);assert.equal(r.held_public_asset_count,0);assert.equal(r.release_accepted,false);});
test('unreferenced private public asset still held',()=>{const x=fixture();x.entry_source='const greeting="hello"';const r=review(x);assert.equal(r.referenced_held_asset_count,0);assert.equal(r.held_public_asset_count,1);});
test('creative proof class preserved',()=>{const x=fixture();x.selection.evidence_class='creative';assert.equal(review(x).evidence_class,'creative');});
test('oversized source rejected',()=>{const x=fixture();x.entry_source='x'.repeat(524289);assert.equal(review(x).state,'HOLD');});
test('multiple fetches counted',()=>{const x=fixture();x.entry_source+=' void fetch(internalUrl);';assert.equal(review(x).assets[0].fetch_count,2);});
test('exact source review deterministic',()=>assert.deepEqual(review(fixture()),review(fixture())));
