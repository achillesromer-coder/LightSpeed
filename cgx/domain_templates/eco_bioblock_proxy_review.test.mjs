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


import {reviewBioBlockEstablishmentProxy} from "./eco_bioblock_proxy_review.mjs";
const establishment={seed_count:220,viability_fraction:0.75,germination_fraction:0.55,
 site_suitability_factor:0.65,survival_fraction:0.45,source_ref:"synthetic-workbook-scenario"};
test("Bio-Blocks workbook synthetic baseline is an expectation not observed plants",()=>{
 const r=reviewBioBlockEstablishmentProxy(establishment);
 assert.ok(Math.abs(r.proxies.expected_established_plants-26.544375)<1e-9);
 assert.ok(r.flags.includes("EXPECTED_COUNT_NOT_OBSERVED"));
 assert.equal(r.field_observation_verified,false);
});
test("zero seeds yields zero expectation, not evidence of a failed field trial",()=>{
 const r=reviewBioBlockEstablishmentProxy({...establishment,seed_count:0});
 assert.equal(r.proxies.expected_established_plants,0);
 assert.equal(r.field_observation_verified,false);
});
test("invalid probabilities, fractional seed count and contradictory observed counts fail closed",()=>{
 for(const bad of [{viability_fraction:1.1},{survival_fraction:-0.1},{seed_count:1.5},
  {germinated_count:3,surviving_count:4},{germinated_count:221},{site_suitability_factor:NaN}])
  assert.throws(()=>reviewBioBlockEstablishmentProxy({...establishment,...bad}),/INVALID_BIOBLOCK_ESTABLISHMENT_INPUT/);
});
test("observed label without counts, provenance, method, controls or replicates remains blocked",()=>{
 const r=reviewBioBlockEstablishmentProxy({...establishment,evidence_class:"observed"});
 for(const f of ["FIELD_EVIDENCE_NOT_INDEPENDENTLY_VERIFIED","OBSERVED_COUNTS_REQUIRED",
  "MISSING_TAXON_REF","MISSING_SITE_REF","MISSING_SAMPLING_DATE",
  "MISSING_CONTROL_REF","REPLICATED_TRIAL_EVIDENCE_REQUIRED"])
  assert.ok(r.flags.includes(f));
});
test("complete-looking field references never self-verify an ecological claim",()=>{
 const r=reviewBioBlockEstablishmentProxy({...establishment,evidence_class:"observed",
  claim:"biodiversity_gain",germinated_count:12,surviving_count:8,replicate_count:3,
  seed_batch_ref:"seed",taxon_ref:"taxon",recipe_ref:"recipe",site_ref:"restricted-site",
  sampling_date:"2026-10-01",method_ref:"method",raw_data_ref:"data",
  baseline_ref:"baseline",control_ref:"control"});
 assert.equal(r.biodiversity_gain_verified,false);
 assert.equal(r.field_release_authorised,false);
 assert.ok(r.flags.includes("BIODIVERSITY_GAIN_NOT_VERIFIED"));
});
test("synthetic counts are not promoted to field observations",()=>{
 const r=reviewBioBlockEstablishmentProxy({...establishment,germinated_count:12,surviving_count:8});
 assert.ok(r.flags.includes("COUNTS_NOT_VERIFIED_AS_FIELD_OBSERVATIONS"));
 assert.equal(r.field_observation_verified,false);
});

import {reviewBioBlockGateLineage as gateLineage} from "./eco_bioblock_proxy_review.mjs";
const gates={original_source_ref:"synthetic-original",translated_source_ref:"synthetic-translation",
 original_gate_ids:["VG-001","VG-002","VG-004"],
 translated_gate_ids:["VG-001","VG-002","VG-008"],
 translated_risk_gate_refs:[{cell_ref:"Synthetic_Risk!F12",gate_ids:["VG-004"]}]};
test("missing original gate and orphan translated reference remain explicit R1 HOLD",()=>{
 const r=gateLineage(gates);
 assert.deepEqual(r.missing_original_gate_ids,["VG-004"]);
 assert.deepEqual(r.orphan_translated_risk_references,
  [{cell_ref:"Synthetic_Risk!F12",gate_id:"VG-004"}]);
 assert.deepEqual(r.translation_only_gate_ids,["VG-008"]);
 assert.equal(r.r2_equivalence_verified,false);
 assert.equal(r.production_qa_verified,false);
 assert.equal(r.native_object_id,null);
});
test("preserved gate identifiers never self-attest source rights or gate closure",()=>{
 const r=gateLineage({...gates,translated_gate_ids:["VG-001","VG-002","VG-004"]});
 assert.deepEqual(r.missing_original_gate_ids,[]);
 assert.deepEqual(r.orphan_translated_risk_references,[]);
 assert.equal(r.source_owner_disposition_verified,false);
 assert.equal(r.rights_verified,false);
 assert.equal(r.db_readback,false);
});
test("unqualified translation-only gate is not silently treated as original",()=>{
 const r=gateLineage({...gates,translated_gate_ids:["VG-001","VG-002","VG-004","VG-008"]});
 assert.deepEqual(r.translation_only_gate_ids,["VG-008"]);
 assert.ok(r.flags.includes("TRANSLATION_ONLY_GATES_REQUIRE_SOURCE_ATTRIBUTION"));
});
test("duplicate IDs, raw fields and malformed risk anchors fail closed",()=>{
 for(const bad of [
  {original_gate_ids:["VG-001","VG-001"]},
  {translated_gate_ids:["VG-001","VG-001"]},
  {raw_source_rows:[{site:"private"}]},
  {translated_risk_gate_refs:[{cell_ref:"gps:-27,153",gate_ids:["VG-004"]}]},
  {translated_risk_gate_refs:[{cell_ref:"Synthetic_Risk!F12",gate_ids:["VG-004","VG-004"]}]},
  {original_source_ref:"synthetic-translation"}
 ])assert.throws(()=>gateLineage({...gates,...bad}),/INVALID_BIOBLOCK_GATE_LINEAGE/);
});
