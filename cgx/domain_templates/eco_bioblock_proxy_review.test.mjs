import test from "node:test";
import assert from "node:assert/strict";
import {reviewBioBlockProxy} from "./eco_bioblock_proxy_review.mjs";
const base={dry_biomass_kg:100,usable_fraction:0.5,
 organic_matter_fraction:0.8,carbon_fraction_of_om:0.5,source_ref:"synthetic-fixture"};
test("dry mass and stoichiometric proxy retain physical units without climate benefit",()=>{
 const r=reviewBioBlockProxy(base);
 assert.equal(r.proxies.usable_kg,50);
 assert.equal(r.proxies.carbon_kg_proxy,20);
 assert.ok(Math.abs(r.proxies.stoichiometric_co2_kg_proxy-73.33333333333333)<1e-10);
 assert.equal(r.measured_impact_verified,false);
 assert.ok(r.flags.includes("STOICHIOMETRIC_CO2_IS_NOT_SEQUESTRATION_OR_AVOIDED_EMISSIONS"));
});
test("carbon credit language cannot be justified by stoichiometric proxy",()=>{
 const r=reviewBioBlockProxy({...base,claim:"carbon_credit",evidence_class:"observed"});
 assert.ok(r.flags.includes("ECOLOGICAL_OR_CLIMATE_IMPACT_NOT_VERIFIED"));
 assert.ok(r.flags.includes("INDEPENDENT_FIELD_EVIDENCE_REVIEW_REQUIRED"));
 assert.equal(r.carbon_credit_verified,false);
});
test("local seed or spore release remains blocked without ecological and custodial reviews",()=>{
 const r=reviewBioBlockProxy({...base,field_release_requested:true,seed_or_spore_material:true});
 for(const f of ["FIELD_RELEASE_NOT_AUTHORISED_BY_SOURCE_ONLY_REVIEW",
 "LOCAL_SITE_ECOLOGY_REVIEW_REQUIRED","CUSTODIAL_STEWARDSHIP_REVIEW_REQUIRED",
 "SEED_SPORE_BIOSECURITY_REVIEW_REQUIRED"])
 assert.ok(r.flags.includes(f));
 assert.equal(r.field_release_authorised,false);
});
test("references do not self-approve field release or climate outcomes",()=>{
 const r=reviewBioBlockProxy({...base,field_release_requested:true,
  site_review_ref:"review",rights_review_ref:"review",custodial_review_ref:"review",
  biosecurity_review_ref:"review",claim:"carbon_sequestration",
  baseline_ref:"baseline",measurement_ref:"measurement",independent_validation_ref:"review"});
 assert.equal(r.field_release_authorised,false);
 assert.equal(r.measured_impact_verified,false);
 assert.ok(r.flags.includes("ECOLOGICAL_OR_CLIMATE_IMPACT_NOT_VERIFIED"));
});
test("invalid physical inputs fail closed",()=>{
 for(const bad of [{usable_fraction:1.2},{carbon_fraction_of_om:-0.1},
  {dry_biomass_kg:NaN},{organic_matter_fraction:Infinity}])
 assert.throws(()=>reviewBioBlockProxy({...base,...bad}),/INVALID_BIOBLOCK_PROXY_INPUT/);
});
