#!/usr/bin/env node
/**
 * Offline, read-only R0/LOAD family source probe. Writes no files and
 * never communicates with remote services. Output is a redacted review receipt.
 */
import {lstatSync,readFileSync,statSync} from 'node:fs';
import {buildReviewEnvelope,verifyReconstruction,MAX_WORK_UNIT_BYTES} from './cgxLeafEnvelopeReview.mjs';
import {stageFamilyPacket,projectUniSpace} from './cgxPremintFamilyProjection.mjs';
import {makePrivateLoadBinding} from './cgxPrivateLoadBindingReview.mjs';
import {planUniSpaceSourceInspector} from '../load_minimum/unispaceSourceInspector.mjs';
import {planUniSpaceFacetConvergence} from '../load_minimum/unispaceFacetConvergence.mjs';
const ALLOWED=new Set(['--source','--object-id','--version','--family','--owner','--semantic-key']);
const forbidden=reason=>{process.stderr.write('CGX_OFFLINE_PROBE_DENIED '+reason+'\n');process.exitCode=2;};
function run(argv){
 if(argv.length!==ALLOWED.size*2)return forbidden('ARGS_INCOMPLETE');
 const o={};
 for(let i=0;i<argv.length;i+=2){
  const k=argv[i],v=argv[i+1];
  if(!ALLOWED.has(k)||Object.hasOwn(o,k)||typeof v!=='string'||v.length===0)
   return forbidden('ARGS_INVALID');
  o[k]=v;
 }
 if(Object.keys(o).length!==ALLOWED.size)return forbidden('ARGS_INCOMPLETE');
 let buffer,statBefore,statAfter;
 try{
  statBefore=lstatSync(o['--source']);
  if(!statBefore.isFile()||statBefore.size>MAX_WORK_UNIT_BYTES)return forbidden('SOURCE_NOT_REGULAR_OR_OVERSIZE');
  buffer=readFileSync(o['--source']);
  statAfter=statSync(o['--source']);
 }catch{
  return forbidden('SOURCE_READ_FAILED');
 }
 if(buffer.length!==statBefore.size||statAfter.size!==statBefore.size||
   statAfter.mtimeMs!==statBefore.mtimeMs)return forbidden('SOURCE_CHANGED_DURING_READ');
 const leaves=[];
 for(let i=0;i<buffer.length;i+=1024*1024)leaves.push(buffer.subarray(i,Math.min(i+1024*1024,buffer.length)));
 if(leaves.length===0)leaves.push(Buffer.alloc(0));
 const packet=stageFamilyPacket({
  objectId:o['--object-id'],version:o['--version'],family:o['--family'],
  owner:o['--owner'],semanticKey:o['--semantic-key'],originalLeaves:leaves,
  rights:'unknown',acl:'unknown'
 });
 if(packet.state==='DENIED')return forbidden(packet.reason);
 if(!verifyReconstruction(packet.envelope,leaves))return forbidden('R0_RECONSTRUCTION_FAILED');
 const v=projectUniSpace(packet,{audience:'owner'});
 // Exercise the existing LOAD -> private UniSpace boundary with actual R0
 // bytes, without treating this machine's filesystem access as host authority.
 // A parent library is not a Grex child FileSpace and is intentionally held.
 const family=o['--family'];
 let privateFlow={state:'HOLD',reason:'PARENT_NOT_CHILD_FILESPACE',
  identity_match:false,leaf_count:0,source_qualified:false,
  native_admitted:false,may_execute:false,public_release:false};
 if(family!=='Cognigrex.cgx'){
  const objectId=v.h0.object_id;
  const domain=family.slice(0,-4).toLowerCase();
  const binding=makePrivateLoadBinding(packet,{objectId,fileSpace:family});
  const inspector=planUniSpaceSourceInspector({
   surface:'private',file_space:family,focus_id:objectId,view:'document',
   nodes:[{object_id:objectId,domain,file_space:family,owner:o['--owner'],
     kind:'source_artifact',source_refs:[objectId],edges:[]}],
   access:{authorized_object_ids:[objectId],authorized_source_ids:[objectId]},
   source_envelopes:[]
  });
  const facet=planUniSpaceFacetConvergence({
   surface:'private',route:'/operator/objects',
   selection:{object_id:objectId,file_space:family,domain,
    parent_file_space:family==='LS.cgx'?'EMASSC.cgx':'Cognigrex.cgx'},
   inspector,sourcePacket:binding
  });
  const privatePlan=facet.status==='SOURCE_REVIEW_ONLY'&&
   facet.source_review?.hydration==='HOLD';
  const rightsHeld=privatePlan&&facet.source_review?.state==='SOURCE_RIGHTS_HOLD';
  privateFlow={state:rightsHeld?'PRIVATE_H0_RIGHTS_HOLD':
    privatePlan?'PRIVATE_H0_H2_REVIEW_ONLY':'HOLD',
   reason:rightsHeld?'UNCLASSIFIED_RIGHTS_OR_ACL':
    privatePlan?null:(facet.reason||'REVIEW_UNQUALIFIED'),
   identity_match:facet.selected_object_id===objectId,
   leaf_count:facet.source_review?.leaf_count??0,
   source_qualified:false,native_admitted:false,may_execute:false,
   public_release:false};
 }
 process.stdout.write(JSON.stringify({
  schema:'CGX-R0-OFFLINE-SOURCE-RECEIPT/0.1',
  state:'SOURCE_HASHED_REVIEW_ONLY',object_id:v.h0.object_id,version:v.h0.version,
  parent:packet.canonical_parent,sha256:v.h0.source_sha256,
  manifest_digest:v.h0.manifest_digest,leaf_count:v.h1.leaf_count,
  byte_count:buffer.length,reconstructed:true,private_review:privateFlow,
  rights:'UNKNOWN_HOLD',acl:'UNKNOWN_HOLD',native_admitted:false,
  committed:false,network_transfer:false,public_release:false,
  note:'No original bytes, source paths or permission proof included in this receipt'
 })+'\n');
}
run(process.argv.slice(2));
