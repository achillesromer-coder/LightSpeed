'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {route, list} = require('./unispace_mobile_routes.cjs');
const web = {chatgpt:'https://chatgpt.com/',drive:'https://drive.google.com/',docs:'https://docs.google.com/',sheets:'https://sheets.google.com/',github:'https://github.com/',gmail:'https://mail.google.com/',calendar:'https://calendar.google.com/',canva:'https://www.canva.com/',maps:'https://maps.google.com/'};
const internal = ['filespace','dataspace','printspace','socialspace','profilespace','intelligencespace','earth','orbital','mol','raphael','universe','lightspeed'];
test('all 21 route IDs are unique and retain their presentation-only authority', () => {
  const all = list(internal);
  assert.equal(all.length, 21);
  assert.equal(new Set(all.map(x=>x.id)).size, 21);
  assert.ok(all.every(x=>x.nativeAuthority === false));
  assert.equal(all.filter(x=>x.state === 'HTTPS_LINK').length, 9);
  assert.equal(all.filter(x=>x.state === 'INTERNAL_VIEW').length, 12);
});
test('fixed HTTPS destinations cannot carry private IDs, credentials or custom intents', () => {
  for (const [id,url] of Object.entries(web)) {
    const x = route(id, ['https://invalid.example/?private=1']);
    assert.equal(x.url, url);
    assert.equal(x.target, '_blank');
    assert.equal(x.rel, 'noopener noreferrer');
    assert.equal(x.installed, 'UNKNOWN');
    assert.equal(x.nativeAuthority, false);
    const u = new URL(x.url);
    assert.equal(u.protocol, 'https:');
    assert.equal(u.username + u.password + u.search + u.hash, '');
  }
});
test('internal contexts require explicit registration and never imply native authority', () => {
  for (const id of internal) {
    assert.equal(route(id).state, 'HOLD');
    const x = route(id, [id]);
    assert.equal(x.state, 'INTERNAL_VIEW');
    assert.equal(x.nativeAuthority, false);
    assert.equal(Object.hasOwn(x, 'url'), false);
  }
});
test('unknown, malformed and prototype route IDs fail closed without echo', () => {
  for (const id of [null,undefined,{},[],1,'','__proto__','constructor','toString','javascript:alert(1)','intent://native','https://example.com/','FILESPACE','filespace?secret=1','filespace\u0000']) {
    assert.deepEqual(route(id, [id]), {state:'HOLD',nativeAuthority:false});
  }
});
test('malformed availability fails closed even for web destinations', () => {
  for (const available of [null,{},true,1,'filespace']) {
    assert.deepEqual(route('filespace', available), {state:'HOLD',nativeAuthority:false});
    assert.deepEqual(route('drive', available), {state:'HOLD',nativeAuthority:false});
  }
});
test('registration of a different context cannot promote the selected route', () => {
  assert.equal(route('filespace',['dataspace','FILESPACE','__proto__']).state,'HOLD');
  assert.equal(route('dataspace',['filespace']).state,'HOLD');
  assert.equal(route('universe',['earth']).state,'HOLD');
});
