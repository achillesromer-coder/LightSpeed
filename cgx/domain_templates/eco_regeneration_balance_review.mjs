/**
 * Eco.cgx R1-only arithmetic guard for translated Type-I FM-008/FM-012.
 * This is not a calibrated ecosystem model, field measurement, or harvest gate.
 * Original formula equivalence, site data, rights and red-line vetoes remain held.
 */
export const ECO_EV_REVIEW_SCHEMA="CGX-ECO-REGENERATION-BALANCE-R1/0.1";
const fields=new Set(["source_ref","source_revision_ref","formula_id","evidence_class",
 "indices","reserve_fraction","maturity_fraction","normalisation_ref",
 "baseline_ref","site_ref","time_frame_ref","response_calibration_ref",
 "redline_review_ref","independent_qa_ref","original_lineage_ref"]);
const indexNames=["Br","Qh","Gr","Ds","Cf","Bl","Fr"];
const ref=x=>typeof x==="string"&&x.length>0&&x.length<=256&&
 !/[\u0000-\u001f]/.test(x);
const fraction=x=>x===null||(typeof x==="number"&&Number.isFinite(x)&&x>=0&&x<=1);
export function reviewEcoRegenerationBalance(input={}){
 if(input===null||typeof input!=="object"||Array.isArray(input)||
  Object.keys(input).some(k=>!fields.has(k)))throw Error("INVALID_ECO_EV_FIELDS");
 const {source_ref=null,source_revision_ref=null,formula_id="FM-008",
  evidence_class="hypothesised",indices=null,reserve_fraction=null,
  maturity_fraction=null,normalisation_ref=null,baseline_ref=null,
  site_ref=null,time_frame_ref=null,response_calibration_ref=null,
  redline_review_ref=null,independent_qa_ref=null,original_lineage_ref=null}=input;
 if(!["FM-008","FM-012"].includes(formula_id)||
  !["simulated","source_asserted","hypothesised","inferred","observed"].includes(evidence_class)||
  !fraction(reserve_fraction)||!fraction(maturity_fraction)||
  [source_ref,source_revision_ref,normalisation_ref,baseline_ref,site_ref,
   time_frame_ref,response_calibration_ref,redline_review_ref,
   independent_qa_ref,original_lineage_ref].some(x=>x!==null&&!ref(x)))
  throw Error("INVALID_ECO_EV_INPUT");
 if(indices!==null&&(typeof indices!=="object"||Array.isArray(indices)||
  Object.keys(indices).length!==indexNames.length||
  indexNames.some(k=>!Object.hasOwn(indices,k)||
   typeof indices[k]!=="number"||!Number.isFinite(indices[k])||
   indices[k]<0||indices[k]>1e6)))
  throw Error("INVALID_ECO_EV_INDICES");
 const flags=["ECOLOGICAL_EFFECT_NOT_VERIFIED",
  "SOURCE_FORMULA_IS_PROVISIONAL_NOT_SITE_CALIBRATED",
  "REDLINE_VETO_AND_SOURCE_RIGHTS_NOT_ATTESTED"];
 for(const [value,flag] of [
  [source_ref,"SOURCE_ID_REQUIRED"],[source_revision_ref,"SOURCE_REVISION_REQUIRED"],
  [normalisation_ref,"INDEX_NORMALISATION_REQUIRED"],
  [baseline_ref,"COMPARABLE_BASELINE_REQUIRED"],
  [site_ref,"SITE_AND_SENSITIVE_LOCATION_REVIEW_REQUIRED"],
  [time_frame_ref,"ECOLOGICAL_TIME_HORIZON_REQUIRED"],
  [response_calibration_ref,"RESERVE_MATURITY_RESPONSE_CALIBRATION_REQUIRED"],
  [redline_review_ref,"SPECIES_HABITAT_REDLINE_REVIEW_REQUIRED"],
  [independent_qa_ref,"INDEPENDENT_QA_REQUIRED"],
  [original_lineage_ref,"ORIGINAL_FORMULA_LINEAGE_REQUIRED"]
 ])if(!ref(value))flags.push(flag);
 let ratio=null;
 if(indices===null)flags.push("COMPONENT_INDICES_NOT_SUPPLIED");
 else{
  const denominator=indices.Bl*indices.Fr;
  const numerator=indices.Br*indices.Qh*indices.Gr*indices.Ds*indices.Cf;
  if(denominator===0)flags.push("ZERO_LOSS_FRAGMENTATION_DENOMINATOR_UNDEFINED");
  else if(!Number.isFinite(denominator)||!Number.isFinite(numerator)||
   !Number.isFinite(numerator/denominator)||numerator/denominator>1e12)
   flags.push("ARITHMETIC_OUT_OF_BOUNDS");
  else ratio=numerator/denominator;
 }
 if(reserve_fraction!==null||maturity_fraction!==null)
  flags.push("CONTROLS_NOT_DIRECT_EV_MULTIPLIERS");
 if(evidence_class==="observed")
  flags.push("OBSERVED_LABEL_DOES_NOT_VALIDATE_COMPOSITE_INDICES");
 return {schema:ECO_EV_REVIEW_SCHEMA,parent:"Cognigrex.cgx",owner_family:"Eco.cgx",
  formula_id,evidence_class,stage:"R1_REVIEW_ONLY",units:"dimensionless indices assumed; basis unverified",
  conditional_arithmetic_ratio:ratio,arithmetic_ratio_gt_one:ratio===null?null:ratio>1,
  controls_entered_formula_directly:false,
  flags,source_only:true,original_formula_equivalence_verified:false,
  indices_independently_calibrated:false,ecological_effect_verified:false,
  harvest_or_scale_up_authorised:false,redline_veto_cleared:false,
  source_rights_verified:false,native_object_id:null,db_readback:false,
  host_verified:false,public_release_authorised:false};
}
