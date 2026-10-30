import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { reviewWindowsCGXHost, classifyInstallerPolicySource } from './cgxWindowsHostPreflightReview.mjs';
const base = {connection:'ONLINE', fileAccess:'VERIFIED_READ_ONLY', policies:{CurrentUser:'RemoteSigned'},signature:'VALID',zone:'LOCAL'};
test('online and read-only does not certify native root or execution',()=>{
 const x=reviewWindowsCGXHost(base);
 assert.equal(x.state,'REVIEW_ONLY');assert.equal(x.authority_verified,false);
 assert.equal(x.dbr_verified,false);assert.equal(x.may_execute,false);
});
test('paired but quota-blocked host is held and cannot be retried by advice',()=>{
 const x=reviewWindowsCGXHost({...base,fileAccess:'QUOTA_BLOCKED'});
 assert.ok(x.holds.includes('PROVIDER_MONTHLY_QUOTA_HOLD_DO_NOT_RETRY'));
 assert.match(x.next_read_only_step,/do not retry/);
});
test('offline host does not imply filesystem access even if file claims exist',()=>{
 const x=reviewWindowsCGXHost({...base,connection:'OFFLINE'});
 assert.ok(x.holds.includes('HOST_CONNECTION_UNVERIFIED'));
});
test('unsigned script under AllSigned is a distinct signing hold',()=>{
 const x=reviewWindowsCGXHost({...base, policies:{LocalMachine:'Unrestricted',MachinePolicy:'AllSigned'},signature:'NOT_SIGNED',startupError:'UNSIGNED_SCRIPT'});
 assert.equal(x.effective_policy_scope,'MachinePolicy');
 assert.ok(x.holds.includes('SCRIPT_SIGNING_POLICY_HOLD'));
});
test('RemoteSigned downloaded unsigned script cannot silently run',()=>{
 const x=reviewWindowsCGXHost({...base,signature:'NOT_SIGNED',zone:'INTERNET'});
 assert.ok(x.holds.includes('SCRIPT_SIGNING_POLICY_HOLD'));assert.equal(x.may_change_execution_policy,false);
});
test('a signature observed valid is not CGX authority',()=>{
 const x=reviewWindowsCGXHost({...base,policies:{MachinePolicy:'AllSigned'}});
 assert.equal(x.state,'REVIEW_ONLY');assert.equal(x.signed_lease_verified,false);
});
test('PowerShell 5.1 parse issue is not a native-kernel fault',()=>{
 const x=reviewWindowsCGXHost({...base,startupError:'PARSE_ERROR',psVersion:'5.1.19041'});
 assert.ok(x.holds.includes('POWERSHELL_SCRIPT_PARSE_HOLD'));
 assert.equal(x.runtime_installed,false);
});
test('workspace action exception is separate from console startup',()=>{
 const x=reviewWindowsCGXHost({...base,startupError:'ARGUMENT_TYPES_DO_NOT_MATCH'});
 assert.ok(x.holds.includes('WIZARD_RUNTIME_ARGUMENT_HOLD'));
});
test('managed policy outranks process Bypass; never recommends policy bypass',()=>{
 const x=reviewWindowsCGXHost({...base,policies:{MachinePolicy:'AllSigned',Process:'Bypass'},signature:'NOT_SIGNED'});
 assert.equal(x.effective_policy,'AllSigned');assert.equal(x.may_change_execution_policy,false);
});
test('invalid observations deny input without manufacturing a receipt',()=>{
 for(const input of [null,[],{...base,signature:'BROKEN'},{...base,policies:{Random:'Bypass'}},{...base,psVersion:'A\nB'}]){
  assert.equal(reviewWindowsCGXHost(input).state,'DENIED');
 }
});
test('all declared input error classes remain non-executing',()=>{
 for(const status of ['NONE','UNSIGNED_SCRIPT','PARSE_ERROR','ARGUMENT_TYPES_DO_NOT_MATCH','OTHER']){
  const x=reviewWindowsCGXHost({...base,startupError:status});
  assert.equal(x.may_execute,false);assert.equal(x.may_publish,false);
 }
});

test('existing Python installer policy is classified from source without running it',()=>{
 const source=readFileSync(new URL('../../desktop/LightSpeed_Runtime/lightspeed_runtime/runtime_productization.py',import.meta.url),'utf8');
 const explicitBypass=classifyInstallerPolicySource(source)==='EXPLICIT_BYPASS';
 const classification=explicitBypass?'EXPLICIT_BYPASS':'NO_EXPLICIT_OVERRIDE';
 const x=reviewWindowsCGXHost({...base,installerInvocationPolicy:classification});
 assert.equal(x.installer_invocation_policy_observation,classification);
 assert.equal(classification,'NO_EXPLICIT_OVERRIDE');
 assert.equal(x.state,'REVIEW_ONLY');
 assert.equal(x.runtime_installed,false);
 assert.equal(x.may_execute,false);assert.equal(x.may_change_execution_policy,false);
 if(explicitBypass)assert.ok(x.holds.includes('NATIVE_INSTALLER_POLICY_BYPASS_SOURCE_HOLD'));
});
test('explicit source-level execution-policy bypass remains HOLD even if host policy appears permissive',()=>{
 for(const policy of ['RemoteSigned','AllSigned','Unrestricted','Bypass']){
  const x=reviewWindowsCGXHost({...base,policies:{CurrentUser:policy},installerInvocationPolicy:'EXPLICIT_BYPASS'});
  assert.equal(x.state,'HOLD');
  assert.ok(x.holds.includes('NATIVE_INSTALLER_POLICY_BYPASS_SOURCE_HOLD'));
  assert.equal(x.may_execute,false);
 }
});
test('installer invocation observation is closed-schema and never host proof',()=>{
 const x=reviewWindowsCGXHost({...base,installerInvocationPolicy:'NO_EXPLICIT_OVERRIDE'});
 assert.equal(x.state,'REVIEW_ONLY');assert.equal(x.authority_verified,false);
 assert.equal(reviewWindowsCGXHost({...base,installerInvocationPolicy:'OWNER_APPROVED'}).state,'DENIED');
});

test('source classifier detects quoted PowerShell argv bypass with whitespace and newline',()=>{
 for(const source of [
  'args = ["-ExecutionPolicy", "Bypass", "-File", script]',
  "args = ['-ExecutionPolicy',\\n  'Bypass']".replace('\\n','\n'),
  'powershell.exe -ExecutionPolicy Bypass -File script.ps1'
 ]){
  assert.equal(classifyInstallerPolicySource(source),'EXPLICIT_BYPASS');
  const x=reviewWindowsCGXHost({...base,installerInvocationPolicy:classifyInstallerPolicySource(source)});
  assert.equal(x.state,'HOLD');assert.equal(x.may_execute,false);
 }
});
test('source classifier does not promote ordinary or unknown policy observations',()=>{
 for(const source of ['["-ExecutionPolicy", "RemoteSigned"]','powershell.exe -NoProfile -File script.ps1','']){
  assert.equal(classifyInstallerPolicySource(source),'NO_EXPLICIT_OVERRIDE');
 }
 for(const source of [null,{},'x'.repeat(2*1024*1024+1)]){
  assert.equal(classifyInstallerPolicySource(source),'UNKNOWN');
  assert.equal(reviewWindowsCGXHost({...base,installerInvocationPolicy:classifyInstallerPolicySource(source)}).state,'REVIEW_ONLY');
 }
});
