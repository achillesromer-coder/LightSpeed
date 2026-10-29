/**
 * Eco.cgx Second Cycle passive-flow proxy review, source-only.
 * Original source locator: Drive workbook 1TWpEaBMRdIBBryyoVhERQ1LQv3dFhbeg
 * R0 SHA-256 (raw XLSX): 0e3e7e878cca173f3799117f5f03cee8fbe924fd1051642d1d66202d0e35108d
 * No workbook rows, protected geometry or field records are embedded here.
 * This is NOT a hydrodynamic solver, deployment design, live operator or DBR writer.
 */
export const SECOND_CYCLE_PROXY_SCHEMA = "CGX-ECO-SECOND-CYCLE-PROXY-REVIEW/0.1";
const isObject = x => x !== null && typeof x === "object" && !Array.isArray(x);
const isRef = x => typeof x === "string" && x.length > 0 && x.length <= 256 && !/[\u0000-\u001f]/.test(x);
const isFiniteNumber = x => typeof x === "number" && Number.isFinite(x);
const requiredUnits = Object.freeze({
 current_speed: "m/s", intake_area: "m2", flow_coefficient: "1",
 mist_fraction: "1", water_density: "kg/m3"
});
const outputs = Object.freeze({
 volumetric_flow_lps: "L/s", mist_output_lps: "L/s",
 dynamic_pressure_pa: "Pa", hydraulic_power_w: "W"
});
function approx(a,b){ return Math.abs(a-b) <= Math.max(1e-9,1e-6*Math.max(Math.abs(a),Math.abs(b))); }
export function qualifySecondCycleProxy(candidate){
 if(!isObject(candidate) || !isObject(candidate.source) || !isObject(candidate.inputs))
  throw new TypeError("INVALID_SECOND_CYCLE_CANDIDATE");
 const {source,inputs}=candidate;
 if(!isRef(source.id) || !isRef(source.revision) || !/^[a-f0-9]{64}$/i.test(source.sha256||""))
  throw new TypeError("SOURCE_ID_REVISION_HASH_REQUIRED");
 const p={};
 for(const [name,unit] of Object.entries(requiredUnits)){
  const q=inputs[name];
  if(!isObject(q) || !isFiniteNumber(q.value) || q.unit!==unit)
   throw new TypeError("INVALID_PHYSICAL_QUANTITY_"+name.toUpperCase());
  p[name]=q.value;
 }
 if(p.current_speed<0 || p.intake_area<=0 || p.water_density<=0 ||
    p.flow_coefficient<0 || p.flow_coefficient>1 || p.mist_fraction<0 || p.mist_fraction>1)
  throw new RangeError("PHYSICAL_PROXY_DOMAIN_ERROR");
 const q_m3s=p.current_speed*p.intake_area*p.flow_coefficient;
 const calculated={
  volumetric_flow_lps:q_m3s*1000,
  mist_output_lps:q_m3s*1000*p.mist_fraction,
  dynamic_pressure_pa:0.5*p.water_density*p.current_speed*p.current_speed,
  hydraulic_power_w:0.5*p.water_density*p.current_speed*p.current_speed*q_m3s
 };
 const flags=["FLOW_PROXY_NOT_OBSERVED","MIST_FRACTION_SYNTHETIC_UNTIL_MEASURED",
  "NOZZLE_ATOMISATION_UNVERIFIED","NO_ECOLOGICAL_OR_ATMOSPHERIC_EFFECT_PROVEN",
  "PHYSICAL_SITE_FRAME_NOT_VERIFIED","INDEPENDENT_REVIEW_REQUIRED"];
 if(!isRef(source.rights_review_ref))flags.push("SOURCE_REUSE_RIGHTS_UNVERIFIED");
 const evidence=isObject(candidate.evidence)?candidate.evidence:{};
 if(!isRef(evidence.flume_calibration_ref))flags.push("FLUME_CALIBRATION_REQUIRED");
 if(!isRef(evidence.nozzle_characterisation_ref))flags.push("NOZZLE_CHARACTERISATION_REQUIRED");
 if(!isRef(evidence.mist_measurement_ref))flags.push("MIST_MEASUREMENT_REQUIRED");
 if(candidate.claimed_observed_mist===true)flags.push("OBSERVED_MIST_CLAIM_REQUIRES_INDEPENDENT_VALIDATION");
 if(candidate.claimed_ecological_benefit===true)flags.push("ECOLOGICAL_BENEFIT_CLAIM_BLOCKED");
 if(candidate.residence_index_claimed_as_time===true)flags.push("RESIDENCE_INDEX_NOT_A_VALIDATED_TIME");
 if(candidate.required_atomisation_power_w!==undefined){
  if(!isFiniteNumber(candidate.required_atomisation_power_w) || candidate.required_atomisation_power_w<0)
   throw new TypeError("INVALID_ATOMISATION_POWER");
  if(candidate.required_atomisation_power_w>calculated.hydraulic_power_w)
   flags.push("ATOMISATION_ENERGY_EXCEEDS_IDEALISED_PROXY");
 }
 if(candidate.reported!==undefined){
  if(!isObject(candidate.reported))throw new TypeError("INVALID_REPORTED_OUTPUTS");
  for(const [name,unit] of Object.entries(outputs)){
   if(candidate.reported[name]===undefined)continue;
   const v=candidate.reported[name];
   if(!isObject(v) || !isFiniteNumber(v.value) || v.unit!==unit)
    throw new TypeError("INVALID_REPORTED_UNIT_"+name.toUpperCase());
   if(!approx(v.value,calculated[name]))flags.push("REPORTED_PROXY_MISMATCH_"+name.toUpperCase());
  }
 }
 return {
  schema:SECOND_CYCLE_PROXY_SCHEMA,
  candidate_filespace:"Eco.cgx/second-cycle/passive-flow-mist-proxy",
  source:{id:source.id,revision:source.revision,sha256:source.sha256},
  calculated,calculated_units:outputs,
  evidence_class:"simulated",stage:"R2_REVIEW_CANDIDATE",
  review_flags:[...new Set(flags)].sort(),
  native_admitted:false,live_installed:false,public_release_authorised:false,
  observed_mist_verified:false,ecological_effect_verified:false
 };
}
