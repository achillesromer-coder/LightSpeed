import test from 'node:test';
import assert from 'node:assert/strict';
import {reviewUniSpaceBuildProvenance as review} from './cgxUniSpaceBuildProvenanceReview.mjs';
const fixture=()=>({selection:{parent_filespace:'Cognigrex.cgx',object_id:'WT-001',filespace:'Romer.cgx',identity_status:'SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED',evidence_class:'scientific'},
client_permissions:{mode:'review_only',revoked:false,allowed_object_ids:['WT-001'],allowed_filespaces:['Romer.cgx']},
source_review:{schema:'UNISPACE-STATIC-ASSET-BOUNDARY-REVIEW/0.1',state:'SOURCE_REVIEW_ONLY',parent_filespace:'Cognigrex.cgx',filespace:'Romer.cgx',candidate_object_id:'WT-001',evidence_class:'scientific',source_scan_verified:false,host_http_verified:false,dist_verified:false,release_accepted:false,canonical_mutation:false,assets:[{asset_id:'catalogue',source_blob_sha:'a'.repeat(40),static_source_path:true,review_result:'SOURCE_RISK_HOLD',risk_codes:['INTERNAL_SOURCE_IN_STATIC_TREE']}]},
entries:[{asset_id:'catalogue',source_blob_sha:'a'.repeat(40),build_sha256:'b'.repeat(64),distribution_class:'PUBLIC_STATIC',source_class:'INTERNAL_REVIEW',scope:'MULTI_OBJECT',rights:'UNRESOLVED',owner_clearance:false,object_id:'WT-001',filespace:'Romer.cgx'}]});
test('source-only never certifies dist or host',()=>{const x=review(fixture());assert.equal(x.state,'SOURCE_REVIEW_ONLY');assert.equal(x.dist_verified,false);assert.equal(x.host_http_verified,false);assert.equal(x.release_accepted,false);});
test('internal source held',()=>{assert.ok(review(fixture()).assets[0].risk_codes.includes('NONPUBLIC_SOURCE_IN_STATIC_BUILD'));});
test('rights hold',()=>{assert.ok(review(fixture()).assets[0].risk_codes.includes('PUBLIC_RIGHTS_OR_CLEARANCE_HOLD'));});
test('multi-object hold',()=>{assert.ok(review(fixture()).assets[0].risk_codes.includes('NOT_SINGLE_OBJECT'));});
test('source risk carried forward',()=>{assert.ok(review(fixture()).assets[0].risk_codes.includes('UNRESOLVED_SOURCE_REVIEW_RISK'));});
test('source hash mismatch flagged',()=>{const f=fixture();f.entries[0].source_blob_sha='c'.repeat(40);assert.ok(review(f).assets[0].risk_codes.includes('SOURCE_BLOB_MISMATCH'));});
test('public safe metadata not release proof',()=>{const f=fixture();f.source_review.assets[0].risk_codes=[];Object.assign(f.entries[0],{source_class:'PUBLIC_CANDIDATE',scope:'ONE_OBJECT',rights:'CLEARED_PUBLIC',owner_clearance:true});const x=review(f);assert.equal(x.risk_count,0);assert.equal(x.release_accepted,false);});
test('private build remains host-unverified',()=>{const f=fixture();f.source_review.assets[0].risk_codes=[];f.entries[0].distribution_class='AUTHENTICATED_PRIVATE';assert.ok(review(f).assets[0].risk_codes.includes('PRIVATE_ROUTE_HOST_DENIAL_NOT_VERIFIED'));});
test('wrong object rejected',()=>{const f=fixture();f.entries[0].object_id='WT-002';assert.equal(review(f).hold_code,'CROSS_OBJECT_OR_FILESPACE_BUILD');});
test('wrong child rejected',()=>{const f=fixture();f.entries[0].filespace='Eco.cgx';assert.equal(review(f).state,'HOLD');});
test('revoked scope rejected',()=>{const f=fixture();f.client_permissions.revoked=true;assert.equal(review(f).hold_code,'CLIENT_SCOPE_MISMATCH');});
test('family object rejected',()=>{const f=fixture();f.selection.object_id='cgx:domain:romer';assert.equal(review(f).state,'HOLD');});
test('duplicate entry rejected',()=>{const f=fixture();f.entries.push({...f.entries[0]});assert.equal(review(f).state,'HOLD');});
test('missing entry rejected',()=>{const f=fixture();f.entries=[];assert.equal(review(f).state,'HOLD');});
test('unknown source rejected',()=>{const f=fixture();f.entries[0].asset_id='unknown';assert.equal(review(f).state,'HOLD');});
test('invalid hash rejected',()=>{const f=fixture();f.entries[0].build_sha256='bad';assert.equal(review(f).state,'HOLD');});
test('private locator suppressed',()=>{const f=fixture();f.entries[0].source_url='SECRET_LOCATOR_88';const x=review(f);assert.equal(x.state,'HOLD');assert.ok(!JSON.stringify(x).includes('SECRET_LOCATOR_88'));});
test('raw path suppressed',()=>{const f=fixture();f.entries[0].path='/private/SECRET_PATH_77';const x=review(f);assert.equal(x.state,'HOLD');assert.ok(!JSON.stringify(x).includes('SECRET_PATH_77'));});
test('source identity mismatch rejected',()=>{const f=fixture();f.source_review.candidate_object_id='OTHER';assert.equal(review(f).state,'HOLD');});
test('untrusted source HTTP claim rejected',()=>{const f=fixture();f.source_review.host_http_verified=true;assert.equal(review(f).state,'HOLD');});
test('offline H0 and LOAD alias only',()=>{const x=review(fixture());assert.equal(x.offline_hydration,'H0_METADATA_ONLY');assert.equal(x.alias_role,'ALEXANDRIA_ENTRY_NOT_PARENT');});
test('circular input fails closed',()=>{const f=fixture();f.loop=f;assert.equal(review(f).state,'HOLD');});
