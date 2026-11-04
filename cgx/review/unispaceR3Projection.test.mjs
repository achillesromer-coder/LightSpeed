import { strict as assert } from "node:assert";
import { planR3Projection } from "./unispaceR3Projection.mjs";
const good = {verified:true,issuerVerified:true,sessionActive:true,revoked:false,rootAclVerified:true,dbrVerified:true,leaseActive:true,objectId:"cgx:test:one",childFileSpace:"cgx:fs:eco",rightsQualified:true,sourceRevisionVerified:true,allowedHydration:["H0","H1","H2"],bridgeReachable:true,consumerReady:false};
const req={objectId:good.objectId,childFileSpace:good.childFileSpace,view:"graph"};
assert.equal(planR3Projection(req,good).status,"SOURCE_ONLY_PLAN");
for(const field of ["verified","issuerVerified","sessionActive","rootAclVerified","dbrVerified","leaseActive","rightsQualified","sourceRevisionVerified"]) {
  assert.equal(planR3Projection(req,{...good,[field]:false}).status,"DENY",field);
}
assert.equal(planR3Projection(req,{...good,revoked:true}).status,"DENY");
assert.equal(planR3Projection({...req,objectId:"cgx:test:other"},good).status,"DENY");
assert.equal(planR3Projection({...req,childFileSpace:"cgx:fs:romer"},good).status,"DENY");
assert.equal(planR3Projection({...req,view:"3d"},good).view,"FRONTIER");
assert.equal(planR3Projection(req,good).consumer,"CONSUMER_HELD");
assert.equal(planR3Projection(req,{...good,allowedHydration:["H0","H4"]}).hydration.includes("H4"),false);
assert.equal(planR3Projection(req,good).execute,false);
console.log("UniSpace R3 source-only gate: 15 assertions passed");
