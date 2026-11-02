/**
 * Eco.cgx FM-009 lineage-conservation ratio: source-only R1 arithmetic review.
 * The Type-I Eco-Grex translated formula is NOT original R0 equivalence.
 * No vegetation intervention, species permission, field outcome or mint is authorised.
 */
export const ECO_LINEAGE_REVIEW_SCHEMA="CGX-ECO-LINEAGE-CONSERVATION-R1/0.1";
const allowed=new Set(["source_ref","source_revision_ref","formula_id","evidence_class",
  "parent_plants_removed","established_descendants","parent_lineage_ref",
  "descendant_record_ref","establishment_method_ref","observation_time_ref",
  "site_review_ref","taxon_review_ref","removal_authorisation_ref",
  "denominator_basis_ref","counterevidence_ref","independent_qa_ref",
  "original_formula_lineage_ref"]);
const ref=x=>typeof x==="string"&&x.length>0&&x.length<=256&&
  !/[\u0000-\u001f]/.test(x);
const count=x=>x===null||(Number.isSafeInteger(x)&&x>=0);
export function reviewEcoLineageConservation(input={}){
  if(input===null||typeof input!=="object"||Array.isArray(input)||
    Object.keys(input).some(k=>!allowed.has(k)))throw Error("INVALID_ECO_LCR_FIELDS");
  const {source_ref=null,source_revision_ref=null,formula_id="FM-009",
    evidence_class="hypothesised",parent_plants_removed=null,
    established_descendants=null,parent_lineage_ref=null,
    descendant_record_ref=null,establishment_method_ref=null,
    observation_time_ref=null,site_review_ref=null,taxon_review_ref=null,
    removal_authorisation_ref=null,denominator_basis_ref=null,
    counterevidence_ref=null,independent_qa_ref=null,
    original_formula_lineage_ref=null}=input;
  const refs={source_ref,source_revision_ref,parent_lineage_ref,descendant_record_ref,
    establishment_method_ref,observation_time_ref,site_review_ref,taxon_review_ref,
    removal_authorisation_ref,denominator_basis_ref,counterevidence_ref,
    independent_qa_ref,original_formula_lineage_ref};
  if(formula_id!=="FM-009"||
    !["simulated","source_asserted","hypothesised","inferred","observed"].includes(evidence_class)||
    !count(parent_plants_removed)||!count(established_descendants)||
    Object.values(refs).some(x=>x!==null&&!ref(x)))
    throw Error("INVALID_ECO_LCR_INPUT");
  const flags=["TRANSLATED_FM009_ORIGINAL_R0_EQUIVALENCE_UNVERIFIED",
    "ESTABLISHMENT_COUNTS_NOT_INDEPENDENTLY_VERIFIED",
    "SITE_SPECIFIC_LINEAGE_THRESHOLD_UNQUALIFIED",
    "REMOVAL_BIOSECURITY_RIGHTS_AND_REDLINE_GATES_OPEN"];
  const required={
    source_ref:"SOURCE_ID_REQUIRED",
    source_revision_ref:"SOURCE_REVISION_REQUIRED",
    parent_lineage_ref:"PARENT_SOURCE_TRACE_REQUIRED",
    descendant_record_ref:"ESTABLISHED_DESCENDANT_RECORD_REQUIRED",
    establishment_method_ref:"ESTABLISHMENT_METHOD_REQUIRED",
    observation_time_ref:"OBSERVATION_TIME_REQUIRED",
    site_review_ref:"SITE_SENSITIVE_LOCATION_REVIEW_REQUIRED",
    taxon_review_ref:"TAXON_SPECIMEN_DISTINCTION_REQUIRED",
    removal_authorisation_ref:"REMOVAL_PERMISSION_NOT_PROVEN",
    denominator_basis_ref:"PARENT_REMOVAL_COUNT_BASIS_REQUIRED",
    counterevidence_ref:"COUNTEREVIDENCE_REVIEW_REQUIRED",
    independent_qa_ref:"INDEPENDENT_QA_REQUIRED",
    original_formula_lineage_ref:"ORIGINAL_FORMULA_LINEAGE_REQUIRED"
  };
  for(const [key,flag] of Object.entries(required))if(!ref(refs[key]))flags.push(flag);
  let ratio=null;
  if(parent_plants_removed===null||established_descendants===null)
    flags.push("COUNT_INPUTS_NOT_SUPPLIED");
  else if(parent_plants_removed===0)
    flags.push("ZERO_REMOVED_PARENT_DENOMINATOR_UNDEFINED");
  else if(![parent_lineage_ref,descendant_record_ref,establishment_method_ref,
    observation_time_ref].every(ref))
    flags.push("UNTRACED_DESCENDANTS_RATIO_WITHHELD");
  else {
    const value=established_descendants/parent_plants_removed;
    if(!Number.isFinite(value)||value>1e12)
      flags.push("ARITHMETIC_OUT_OF_BOUNDS");
    else ratio=value;
  }
  if(evidence_class==="observed")
    flags.push("OBSERVED_LABEL_NOT_A_FIELD_RECEIPT");
  return {schema:ECO_LINEAGE_REVIEW_SCHEMA,parent:"Cognigrex.cgx",
    owner_family:"Eco.cgx",formula_id,evidence_class,stage:"R1_REVIEW_ONLY",
    numerator_unit:"established descendant plants",denominator_unit:"removed parent plants",
    conditional_arithmetic_ratio:ratio,flags,source_only:true,
    original_formula_equivalence_verified:false,source_record_bytes_verified_by_module:false,
    parent_descendant_linkage_independently_verified:false,
    observed_establishment_verified:false,ecological_effect_verified:false,
    removal_or_propagation_authorised:false,source_rights_verified:false,
    native_object_id:null,db_readback:false,host_verified:false,
    public_release_authorised:false};
}
