import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';import {createHash} from 'node:crypto';
import {validateDictionary,encodeOrdinal,decodeOrdinal,pack173,unpack173,packThreeLines,unpackThreeLines,makeCapsule,encodeBinaryTransport,decodeBinaryTransport,reconcileThreeVoices,validateCapsule} from './tir173_core.mjs';
import {bridgeNeoPlan,compileShapeRecipe,projectSynchronized} from './tir173_composition.mjs';
import {planExistingLoadTIR} from './tir173_load_bridge.mjs';
const source=readFileSync(new URL('../../../docs/agent-ingestion/local-agent-homes/Z+2_Neo/pilots/raphael_temporal/geometry_language/T173_NEO_ROLE_PROJECTION.review.json',import.meta.url));
const projection=JSON.parse(source.toString('utf8'));
const dict={schema:'cgx.t173.shape_dictionary/0.2',status:'PUBLIC_SAFE_REVIEW',source_sha256:createHash('sha256').update(source).digest('hex'),
 sentinel:null,roles:projection.slots.map((r,i)=>({slot:i+1,role:`T173:${String(i+1).padStart(3,'0')}`,name:`Research role ${i+1}`,family:r.class,mesh_ref:String(r.mesh_ref),evidence:r.qualifier}))};
test('existing Neo public projection crosswalk maintains 173 identity and 157 references',()=>{assert.equal(validateDictionary(dict).roles,173);assert.equal(new Set(dict.roles.map(r=>r.mesh_ref)).size,157);});
test('all local addresses roundtrip under true five-trit positional encoding; 174 denied',()=>{for(let i=1;i<=173;i++)assert.equal(decodeOrdinal(encodeOrdinal(i)),i);assert.throws(()=>encodeOrdinal(174));});
test('dense 173-state 35-byte bridge is exact for extrema and mixed',()=>{for(let k of [-1,0,1]){const x=Array(173).fill(k);assert.deepEqual(unpack173(pack173(x)),x);}const mixed=Array.from({length:173},(_,i)=>i%3-1);assert.deepEqual(unpack173(pack173(mixed)),mixed);});
test('capsule exists once; both human and machine views derive from same value',()=>{const c=makeCapsule(dict,{shape:131,path:[1,173,131],object_ref:'public:review',source_ref:'public:projection',coarse:{level:0,status:'REFERENCE_ONLY'},fine:{level:3,status:'UNRESOLVED'},state:{basis:'public:review',trit:0,validity:'UNRESOLVED'}});
 const r=projectSynchronized(dict,c);assert.equal(r.machine.shape,r.human.geometry_role);assert.equal(r.transport.exact_roundtrip,true);assert.deepEqual(decodeBinaryTransport(encodeBinaryTransport(c)),c);});
test('older Neo geometry syntax is adapted, no hydration/mint escalation',()=>{const p={schema:'cgx.geometry.ast/0.1',kind:'geometry_reference',slot:'T173:131',status:'DRY_RUN_REVIEW_ONLY',effects_performed:false,authority_transfer:false};const v=bridgeNeoPlan(dict,p);assert.equal(v.capsule.geometry_ref,projection.slots[130].mesh_ref);assert.equal(v.promotion_allowed,false);assert.throws(()=>bridgeNeoPlan(dict,{...p,effects_performed:true}));});
test('repeated shape roles are allowed for different instances and triads keep contradiction',()=>{const a=compileShapeRecipe(dict,'compose T173:014 interacts_with T173:014');assert.equal(a.same_role_instances,true);
 const roles=['intuitive','deliberative','assurance'];const r=reconcileThreeVoices(roles.map((v,i)=>({voice:v,trit:i===1?-1:1,validity:'SUPPORTED',source_ref:'public:review'})));assert.equal(r.conflict,true);assert.equal(r.combined_state,null);});

test('3 independent 173-trit lines encode to exact 105-byte carrier',()=>{const x={intuitive:Array(173).fill(0),deliberative:Array(173).fill(1),assurance:Array(173).fill(-1)};assert.deepEqual(unpackThreeLines(packThreeLines(x)),x);assert.equal(packThreeLines(x).length,105);});

test('existing LOAD planning contract maps shape but never authorises hydration',()=>{
 const cap=makeCapsule(dict,{shape:1,path:[1],object_ref:'public:review',source_ref:'public:projection',state:{basis:'public:review',trit:0,validity:'UNRESOLVED'}});
 const lp={schema:'UNISPACE-CGX-LOAD-LENS-PLAN/0.1',state:'PLAN_ONLY_NOT_HYDRATED',alias:'LOAD.cgx',parent_filespace:'Cognigrex.cgx',object_id:'public:review',native_admitted:false,hydrated:false,execution_performed:false,public_publish_authorized:false,canonical_mutation:false,host_context_readback_authenticated:false,source_rights_independently_verified:false,client_scope_independently_authenticated:false,requested_hydration:'H0',planned_hydration:'H0'};
 const out=planExistingLoadTIR(dict,cap,lp);assert.equal(out.source_bytes_transferred,0);assert.equal(out.source_hydrated,false);
 for(const patch of [{hydrated:true},{native_admitted:true},{object_id:'public:different'},{state:'HYDRATED'}])assert.throws(()=>planExistingLoadTIR(dict,cap,{...lp,...patch}));
});

test('capsule evidence cannot be replaced and required fields cannot default on receipt',()=>{
 const c=makeCapsule(dict,{shape:1,path:[1],object_ref:'public:review',source_ref:'public:projection'});
 assert.equal(validateCapsule(dict,c),true);
 assert.throws(()=>validateCapsule(dict,{...c,geometry_evidence:c.geometry_evidence==='SUPPORTED'?'REFUTED':'SUPPORTED'}),/CAPSULE_DICTIONARY_HASH_MISMATCH/);
 for(const field of Object.keys(c)){
   const absent={...c};delete absent[field];
   assert.throws(()=>validateCapsule(dict,absent),undefined,`missing ${field}`);
 }
 for(const field of ['coarse','fine']){
   const lenses={...c.scale_lenses};delete lenses[field];
   assert.throws(()=>validateCapsule(dict,{...c,scale_lenses:lenses}),/CAPSULE_SCALE_LENS_MISSING/);
 }
 assert.throws(()=>validateCapsule(dict,{...c,scale_lenses:null}),/CAPSULE_SCALE_LENS_MISSING/);
 assert.equal(validateCapsule(dict,decodeBinaryTransport(encodeBinaryTransport(c))),true);
});


test('direct LOAD seam rejects unknown and escalating levels; accepts explicit offline H0 only',()=>{
 const cap=makeCapsule(dict,{shape:1,path:[1],object_ref:'public:review',source_ref:'public:projection'});
 const lp={schema:'UNISPACE-CGX-LOAD-LENS-PLAN/0.1',state:'PLAN_ONLY_NOT_HYDRATED',alias:'LOAD.cgx',parent_filespace:'Cognigrex.cgx',object_id:cap.object_ref,native_admitted:false,hydrated:false,execution_performed:false,public_publish_authorized:false,canonical_mutation:false,host_context_readback_authenticated:false,source_rights_independently_verified:false,client_scope_independently_authenticated:false,requested_hydration:'H0',planned_hydration:'H0'};
 for(const requested_hydration of ['H0','H1','H2','H3']){
  const r=planExistingLoadTIR(dict,cap,{...lp,requested_hydration,planned_hydration:requested_hydration,offline_degraded:false});assert.equal(r.requested_level,requested_hydration);assert.equal(r.source_hydrated,false);
  if(requested_hydration!=='H0'){const d=planExistingLoadTIR(dict,cap,{...lp,requested_hydration,offline_degraded:true});assert.equal(d.planned_level,'H0');assert.equal(d.source_bytes_transferred,0);}
 }
 for(const patch of [{requested_hydration:'H4'},{requested_hydration:null},{planned_hydration:'H1'},{planned_hydration:'H1',offline_degraded:true},{requested_hydration:'H2'},{requested_hydration:'H2',planned_hydration:'H1',offline_degraded:true},{offline_degraded:true},{offline_degraded:'true'}])assert.throws(()=>planExistingLoadTIR(dict,cap,{...lp,...patch}),undefined,JSON.stringify(patch));
});
