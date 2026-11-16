import test from "node:test";
import assert from "node:assert/strict";
import {reviewEcoRegenerationBalance as review} from "./eco_regeneration_balance_review.mjs";
// All numbers are synthetic dimensionless arithmetic fixtures, never ecology observations.
const ones={Br:1,Qh:1,Gr:1,Ds:1,Cf:1,Bl:1,Fr:1};
test("missing calibration and component indices never create an EV measurement",()=>{
 const r=review();assert.equal(r.conditional_arithmetic_ratio,null);
 assert.ok(r.flags.includes("COMPONENT_INDICES_NOT_SUPPLIED"));
 assert.ok(r.flags.includes("INDEX_NORMALISATION_REQUIRED"));
 assert.equal(r.ecological_effect_verified,false);
});
test("neutral synthetic indices produce arithmetic identity only",()=>{
 const r=review({indices:ones});
 assert.equal(r.conditional_arithmetic_ratio,1);
 assert.equal(r.arithmetic_ratio_gt_one,false);
 assert.equal(r.harvest_or_scale_up_authorised,false);
 assert.equal(r.native_object_id,null);
});
test("lower synthetic fragmentation denominator changes arithmetic not ecology proof",()=>{
 const r=review({indices:{...ones,Fr:0.8}});
 assert.equal(r.conditional_arithmetic_ratio,1.25);
 assert.equal(r.ecological_effect_verified,false);
});
test("zero denominator is undefined, not infinite ecological success",()=>{
 const r=review({indices:{...ones,Bl:0}});
 assert.equal(r.conditional_arithmetic_ratio,null);
 assert.ok(r.flags.includes("ZERO_LOSS_FRAGMENTATION_DENOMINATOR_UNDEFINED"));
});
test("reserve and maturity controls cannot change EV without response functions",()=>{
 const a=review({indices:ones,reserve_fraction:0.4,maturity_fraction:0.6});
 const b=review({indices:ones,reserve_fraction:0.8,maturity_fraction:0.9});
 assert.equal(a.conditional_arithmetic_ratio,b.conditional_arithmetic_ratio);
 assert.equal(a.controls_entered_formula_directly,false);
 assert.ok(a.flags.includes("CONTROLS_NOT_DIRECT_EV_MULTIPLIERS"));
});
test("even complete-looking refs and observed label never self-certify outcomes",()=>{
 const x={indices:ones,evidence_class:"observed",source_ref:"fixture:source",
 source_revision_ref:"fixture:revision",normalisation_ref:"fixture:norm",
 baseline_ref:"fixture:baseline",site_ref:"fixture:site",time_frame_ref:"fixture:year",
 response_calibration_ref:"fixture:calibration",redline_review_ref:"fixture:redline",
 independent_qa_ref:"fixture:qa",original_lineage_ref:"fixture:original"};
 const r=review(x);assert.equal(r.ecological_effect_verified,false);
 assert.equal(r.redline_veto_cleared,false);
 assert.equal(r.source_rights_verified,false);
 assert.ok(r.flags.includes("OBSERVED_LABEL_DOES_NOT_VALIDATE_COMPOSITE_INDICES"));
});
test("reject nonfinite, negative, partial, extra and raw coordinate fields",()=>{
 for(const x of [{indices:{...ones,Br:Infinity}},
  {indices:{...ones,Qh:-0.1}},{indices:{Br:1}},
  {indices:{...ones,extra:2}},{coordinates:[-27,153]},
  {reserve_fraction:1.1},{evidence_class:"measured_verified"}])
 assert.throws(()=>review(x),/INVALID_ECO_EV_/);
});
test("extreme but finite values cannot overflow an unqualified ratio",()=>{
 const r=review({indices:{...ones,Br:1e6,Qh:1e6,Gr:1e6,Ds:1e6,Cf:1e6,Bl:1e-6,Fr:1e-6}});
 assert.equal(r.conditional_arithmetic_ratio,null);
 assert.ok(r.flags.includes("ARITHMETIC_OUT_OF_BOUNDS"));
});
