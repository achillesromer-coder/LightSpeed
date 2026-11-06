import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const cli=new URL('./cgxOfflineSourceProbe.mjs',import.meta.url);
function run(file,overrides={}){
 const a={'--source':file,'--object-id':'cgx:load:fixture','--version':'1',
  '--family':'Cognigrex.cgx','--owner':'achilles','--semantic-key':'load:fixture',...overrides};
 return spawnSync(process.execPath,[fileURLToPath(cli),...Object.entries(a).flat()],{encoding:'utf8'});
}
test('offline R0 source probe reconstructs actual on-disk bytes with redacted receipt',()=>{
 const dir=mkdtempSync(join(tmpdir(),'cgx-r0-review-'));
 try{
  const f=join(dir,'source.txt'),content='Original source bytes remain private: A B C';
  writeFileSync(f,content);
  const p=run(f);assert.equal(p.status,0,p.stderr);
  const r=JSON.parse(p.stdout);
  assert.equal(r.state,'SOURCE_HASHED_REVIEW_ONLY');
  assert.equal(r.reconstructed,true);
  assert.equal(r.byte_count,Buffer.byteLength(content));
  assert.equal(r.native_admitted,false);
  assert.equal(r.network_transfer,false);
  assert.equal(r.public_release,false);
  assert.equal(p.stdout.includes(dir),false);
  assert.equal(p.stdout.includes('Original source bytes remain private'),false);
 }finally{rmSync(dir,{recursive:true,force:true});}
});
test('missing or nonregular source fails closed with no receipt',()=>{
 const dir=mkdtempSync(join(tmpdir(),'cgx-source-negative-'));
 try{
  const p=run(join(dir,'absent'));
  assert.notEqual(p.status,0);
  assert.match(p.stderr,/SOURCE_READ_FAILED/);
  assert.equal(p.stdout,'');
  const q=run(dir);
  assert.notEqual(q.status,0);
  assert.match(q.stderr,/SOURCE_NOT_REGULAR_OR_OVERSIZE/);
 }finally{rmSync(dir,{recursive:true,force:true});}
});
test('incorrect family does not create a source receipt',()=>{
 const dir=mkdtempSync(join(tmpdir(),'cgx-family-negative-'));
 try{
  const f=join(dir,'source');writeFileSync(f,'x');
  const p=run(f,{'--family':'UniSpace'});
  assert.equal(p.status,2);
  assert.match(p.stderr,/SOURCE_IDENTITY_SCOPE_INVALID/);
  assert.equal(p.stdout,'');
 }finally{rmSync(dir,{recursive:true,force:true});}
});
