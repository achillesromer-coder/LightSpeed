import test from 'node:test';
import assert from 'node:assert/strict';
import {planDeviceRolePreflight as plan} from './cgxHouseholdHandshakeReview.mjs';
const candidates=[
 {key:'home-computer',kind:'computer',relationship:'owner_claim',proximity:'local'},
 {key:'home-phone',kind:'phone',relationship:'owner_claim',proximity:'unknown'},
 {key:'home-watch',kind:'watch',relationship:'owner_claim',proximity:'unknown'},
 {key:'home-switch',kind:'console',relationship:'owner_claim',proximity:'unknown'},
 {key:'home-tv',kind:'television',relationship:'owner_claim',proximity:'unknown'},
 {key:'excluded-laptop',kind:'laptop',relationship:'excluded',proximity:'local'},
 {key:'other-user-secondary-phone',kind:'phone',relationship:'other_user',proximity:'out_of_range'}
];
test('seven roles remain review-only, five held, two denied and no scanned device',()=>{
 const p=plan({candidates});
 assert.equal(p.role_count,7);assert.equal(p.pending_count,5);assert.equal(p.denied_count,2);
 assert.equal(p.native_admitted,false);assert.equal(p.network_scan_performed,false);
 for(const x of p.devices){assert.equal(x.may_pair,false);assert.equal(x.may_scan,false);
  assert.equal(x.may_mint,false);assert.equal(x.owner_os_consent_verified,false);}
});
test('non-owned laptop denied on local network even if in proximity',()=>{
 const p=plan({candidates});const x=p.devices.find(y=>y.key==='excluded-laptop');
 assert.equal(x.status,'DENY_NOT_OWNED');assert.equal(x.may_pair,false);
});
test('separate-user phone out of range cannot bind or hydrate',()=>{
 const x=plan({candidates}).devices.find(y=>y.key==='other-user-secondary-phone');
 assert.equal(x.status,'DENY_OTHER_USER_OUT_OF_RANGE');assert.equal(x.may_hydrate,false);
});
test('untrusted "consent true", secret, duplicates and spoofed Unicode identifiers denied',()=>{
 for(const list of [
  [...candidates,{...candidates[0]}],
  [{...candidates[0],consent:true}],
  [{...candidates[0],token:'hidden'}],
  [{...candidates[0],key:'hоme-computer'}],
  [{...candidates[0],kind:'arbitrary'}],
 ])assert.equal(plan({candidates:list}).state,'DENIED');
});
