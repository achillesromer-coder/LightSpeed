import {test} from "vitest";
import assert from "node:assert/strict";
import {PUBLIC_OBJECT,DOOM_PROOF,SYNTHETIC_CUBE,sectionConvexMesh,selectRoute,walkSlice,handshake,applySparseDelta,evaluatePrint,numericSlice} from "../public/cgx/assets/core.js";
test("five public routes resolve without internal fallback",()=>{
  assert.equal(selectRoute("/cgx/"),"overview");
  for(const x of ["fs","ds","ps","doom"])assert.equal(selectRoute("/cgx/"+x+"/"),x);
  assert.equal(selectRoute("/private/owner"),"overview");
});
test("single source identity is public synthetic, no secret",()=>{
  assert.equal(PUBLIC_OBJECT.authority,"PUBLIC_SAFE_SYNTHETIC");
  assert.ok(PUBLIC_OBJECT.object_id.startsWith("PUBLIC-DEMO/"));
  assert.equal(PUBLIC_OBJECT.slices.length,4);
  assert.deepEqual(walkSlice(PUBLIC_OBJECT,"geometry"),["root","geometry"]);
});
test("device never grants execution authority",()=>{
  for(const device of ["desktop_browser","mobile_touch","machine"])
    assert.equal(handshake({device,requested:"metric"}).authorised,false);
  assert.equal(handshake({device:"machine",requested:"graph"}).status,"UNSUPPORTED_RENDERER");
  assert.equal(handshake({device:"mobile_touch",requested:"process"}).status,"REVIEW_ONLY");
  assert.equal(handshake({device:"mobile_touch",requested:"metric",cached:false}).status,"NOT_CACHED");
});
test("sparse replay and context errors preserve state",()=>{
  const old={sequence:0,root:"demo-state-0",value:"idle"};
  const next=applySparseDelta(old,{sequence:1,prior_root:"demo-state-0",value:"moving"});
  assert.equal(next.status,"LOCAL_RECONSTRUCTED_UNTRUSTED_CANDIDATE");
  assert.equal(next.applied,1);
  assert.equal(next.authenticated,false);
  assert.equal(applySparseDelta(old,{sequence:1,prior_root:"WRONG",value:"moving"}).status,"CONTEXT_MISMATCH");
  assert.equal(applySparseDelta(old,{sequence:3,prior_root:"demo-state-0",value:"moving"}).status,"REPLAY_OR_SEQUENCE_MISMATCH");
});
test("PrintSpace direction is distinct and physical qualification false",()=>{
  const a=evaluatePrint({direction:"polymer-to-metal",inert:true,interfaceQualified:true});
  const b=evaluatePrint({direction:"metal-to-polymer",inert:true,interfaceQualified:true});
  assert.equal(a.status,"CAN_IF_SIMULATED_CONDITIONS");
  assert.equal(b.status,a.status);
  assert.notDeepEqual(a.requirements,b.requirements);
  assert.equal(a.qualified_machine,false);
  assert.equal(evaluatePrint({direction:"metal-to-polymer",interfaceQualified:false}).status,"HOLD_CONDITIONS_UNVERIFIED");
});
test("unknown is not zero",()=>{
  assert.equal(numericSlice("geometry",null).status,"UNKNOWN_INPUT");
  assert.equal(numericSlice("absent").status,"UNKNOWN_SLICE");
  assert.equal(numericSlice("geometry").value,12);
});
test("historical DOOM sizes exactly preserved in public fixture",()=>{
  assert.equal(DOOM_PROOF.raw_wad_bytes,28795076);
  assert.equal(DOOM_PROOF.monolithic_html_bytes,22018509);
  assert.equal(DOOM_PROOF.sharded_html_bytes,22462117);
  assert.equal(DOOM_PROOF.n_layers,15);
});

test("synthetic cube plane cuts derive square area and preserve object identity",()=>{
  const original=JSON.stringify(SYNTHETIC_CUBE);
  for(const normal of [[0,0,1],[1,0,0],[0,1,0]]){
    const x=sectionConvexMesh(SYNTHETIC_CUBE,{normal,offset:0});
    assert.equal(x.status,"DERIVED_PLANE_SECTION");
    assert.equal(x.vertices_2d.length,4);
    assert.ok(Math.abs(x.area-4)<1e-8);
    assert.equal(x.object_id,PUBLIC_OBJECT.object_id);
    assert.equal(x.geometry_root,"synthetic-unit-cube-r1");
    assert.equal(x.physical_proof,false);
  }
  assert.equal(JSON.stringify(SYNTHETIC_CUBE),original);
});
test("2D cut preserves distinct NO_INTERSECTION and DEGENERATE states",()=>{
  assert.equal(sectionConvexMesh(SYNTHETIC_CUBE,{normal:[0,0,1],offset:3}).status,"NO_INTERSECTION");
  const touch=sectionConvexMesh(SYNTHETIC_CUBE,{normal:[1,1,1],offset:Math.sqrt(3)});
  assert.equal(touch.status,"DEGENERATE_SECTION");
  assert.equal(touch.area,null);
});
test("2D cut rejects invalid vertices, edges, normals and missing source units",()=>{
  const clone=()=>JSON.parse(JSON.stringify(SYNTHETIC_CUBE));
  assert.equal(sectionConvexMesh(clone(),{normal:[0,0,0],offset:0}).status,"HOLD_DEGENERATE_NORMAL");
  assert.equal(sectionConvexMesh(clone(),{normal:[NaN,0,1],offset:0}).status,"HOLD_INVALID_PLANE");
  const v=clone();v.vertices[0][0]=Infinity;
  assert.equal(sectionConvexMesh(v,{normal:[0,0,1],offset:0}).status,"HOLD_INVALID_VERTEX");
  const e=clone();e.edges[0]=[0,99];
  assert.equal(sectionConvexMesh(e,{normal:[0,0,1],offset:0}).status,"HOLD_INVALID_EDGE");
  const u=clone();delete u.unit;
  assert.equal(sectionConvexMesh(u,{normal:[0,0,1],offset:0}).status,"HOLD_SOURCE_FRAME_OR_UNITS");
  const c=clone();c.convex=false;
  assert.equal(sectionConvexMesh(c,{normal:[0,0,1],offset:0}).status,"HOLD_INVALID_GEOMETRY");
  assert.equal(sectionConvexMesh(clone(),{normal:[0,0,1],offset:Infinity}).status,"HOLD_INVALID_PLANE");
});
