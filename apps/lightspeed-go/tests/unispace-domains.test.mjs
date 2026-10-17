import {test} from "vitest";
import assert from "node:assert/strict";
import {PUBLIC_DOMAIN_SCHEMA,selectDomain,describeDomain} from "../public/cgx/assets/domain-overviews.js";

test("one public owner-scoped lens for each domain",()=>{
  for(const d of ["romer","eco"]){
    const row=selectDomain(d),view=describeDomain(d);
    assert.ok(row&&row.entries.length>=4);
    assert.equal(view.schema,PUBLIC_DOMAIN_SCHEMA);
    assert.equal(view.families.length,row.entries.length);
    assert.equal(view.public_release_proven,false);
    assert.equal(view.signed_owner_release_verified,false);
    assert.equal(view.private_catalogue_included,false);
    assert.equal(view.physical_qualification,false);
    assert.equal(view.object_id,null);
  }
  assert.equal(describeDomain("admin").status,"UNKNOWN_DOMAIN");
});
test("Römer and Eco are descriptive-only and cannot leak internal keys",()=>{
  for(const d of ["romer","eco"]){
    const rendered=JSON.stringify(describeDomain(d));
    for(const blocked of [
      "localhost", "127.0.0.1", "C:/Cognigrex", "D:/LightSpeed",
      "Bearer ", "cgx_internal_review_projection", "component_geometry_atlas_public_review",
      "ownerAuth", "desktopBridge", "provider_file_id", "source_sha256", "acl_ref"
    ])assert.equal(rendered.includes(blocked),false,blocked);
  }
});
