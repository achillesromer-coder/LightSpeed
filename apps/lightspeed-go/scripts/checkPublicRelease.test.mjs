import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { scanPublicRelease } from "./checkPublicRelease.mjs";

function fixture(fn) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(),"cgx-release-test-"));
  try { fn(root); } finally { fs.rmSync(root,{recursive:true,force:true}); }
}
function put(root,phase,relative){
  const f=path.join(root,phase==="source"?"public":"dist",relative);
  fs.mkdirSync(path.dirname(f),{recursive:true});
  fs.writeFileSync(f,"fixture only");
}
test("catalogue sources block public distribution",()=>{
  fixture(root=>{
    put(root,"source","data/cgx_object_review_catalogue.json");
    put(root,"source","data/component_geometry_atlas_public_review.json");
    const actual=scanPublicRelease({siteRoot:root,phase:"source"});
    assert.equal(actual.held_count,2);
    assert.equal(actual.state,"HOLD_KNOWN_STATIC_DISCLOSURE");
    assert.equal(actual.public_release_authorised,false);
  });
});
test("mesh and render paths block static output",()=>{
  fixture(root=>{
    put(root,"dist","review/mesh/test.json");
    put(root,"dist","review/renders/test.svg");
    const actual=scanPublicRelease({siteRoot:root,phase:"dist"});
    assert.equal(actual.held_count,2);
    assert.equal(actual.build_authorised,false);
  });
});
test("clean checked paths do not imply release approval",()=>{
  fixture(root=>{
    put(root,"source","cgx/index.html");
    const actual=scanPublicRelease({siteRoot:root,phase:"source"});
    assert.equal(actual.held_count,0);
    assert.equal(actual.public_release_authorised,false);
    assert.equal(actual.complete_privacy_audit,false);
  });
});
test("missing distribution tree always holds",()=>{
  fixture(root=>{
    const actual=scanPublicRelease({siteRoot:root,phase:"dist"});
    assert.equal(actual.state,"HOLD_MISSING_DISTRIBUTION_ROOT");
    assert.equal(actual.build_authorised,false);
  });
});
test("source and destination scans remain distinct",()=>{
  fixture(root=>{
    put(root,"source","cgx/index.html");
    put(root,"dist","review/renders/test.svg");
    assert.equal(scanPublicRelease({siteRoot:root,phase:"source"}).held_count,0);
    assert.equal(scanPublicRelease({siteRoot:root,phase:"dist"}).held_count,1);
  });
});
