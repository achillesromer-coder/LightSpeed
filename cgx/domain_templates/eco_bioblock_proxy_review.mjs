/**
 * Eco.cgx source-only review of Bio-Blocks biomass/carbon arithmetic.
 * Generic physical accounting; no protected workbook rows, field measurements,
 * native Object_ID, carbon credit, ecological efficacy or release permission.
 */
export const BIOBLOCK_PROXY_SCHEMA="CGX-ECO-BIOBLOCK-CARBON-REVIEW/0.1";
const bounded=(x,max=1)=>typeof x==="number"&&Number.isFinite(x)&&x>=0&&x<=max;
const reference=x=>typeof x==="string"&&x.length>0&&x.length<=256&&!/[\u0000-\u001f]/.test(x);
export function reviewBioBlockProxy({
 dry_biomass_kg,usable_fraction,organic_matter_fraction,carbon_fraction_of_om,
 evidence_class="simulated",claim="composition_proxy",field_release_requested=false,
 seed_or_spore_material=false,source_ref=null,baseline_ref=null,
 measurement_ref=null,independent_validation_ref=null,site_review_ref=null,
 biosecurity_review_ref=null,custodial_review_ref=null,rights_review_ref=null
}={}){
 if(!bounded(dry_biomass_kg,1e12)||!bounded(usable_fraction)||
  !bounded(organic_matter_fraction)||!bounded(carbon_fraction_of_om)||
  !["observed","simulated","source_asserted","hypothesised","inferred"].includes(evidence_class)||
  !["composition_proxy","carbon_sequestration","avoided_emissions","carbon_credit","biodiversity_gain"].includes(claim)||
  typeof field_release_requested!=="boolean"||typeof seed_or_spore_material!=="boolean")
  throw Error("INVALID_BIOBLOCK_PROXY_INPUT");
 for(const x of [source_ref,baseline_ref,measurement_ref,independent_validation_ref,
  site_review_ref,biosecurity_review_ref,custodial_review_ref,rights_review_ref])
  if(x!==null&&!reference(x))throw Error("INVALID_BIOBLOCK_REVIEW_REFERENCE");
 const usable_kg=dry_biomass_kg*usable_fraction;
 const carbon_kg_proxy=usable_kg*organic_matter_fraction*carbon_fraction_of_om;
 const stoichiometric_co2_kg_proxy=carbon_kg_proxy*(44/12);
 const flags=["STOICHIOMETRIC_CO2_IS_NOT_SEQUESTRATION_OR_AVOIDED_EMISSIONS"];
 if(evidence_class==="observed")flags.push("INDEPENDENT_FIELD_EVIDENCE_REVIEW_REQUIRED");
 if(!reference(source_ref))flags.push("SOURCE_PROVENANCE_REQUIRED");
 if(!reference(baseline_ref))flags.push("COMPARABLE_BASELINE_REQUIRED_FOR_IMPACT_CLAIM");
 if(claim!=="composition_proxy"){
  flags.push("ECOLOGICAL_OR_CLIMATE_IMPACT_NOT_VERIFIED");
  if(!reference(measurement_ref))flags.push("MEASURED_OUTCOME_REQUIRED");
  if(!reference(independent_validation_ref))flags.push("INDEPENDENT_VALIDATION_REQUIRED");
 }
 if(field_release_requested){
  flags.push("FIELD_RELEASE_NOT_AUTHORISED_BY_SOURCE_ONLY_REVIEW");
  if(!reference(site_review_ref))flags.push("LOCAL_SITE_ECOLOGY_REVIEW_REQUIRED");
  if(!reference(rights_review_ref))flags.push("SOURCE_AND_DEPLOYMENT_RIGHTS_REVIEW_REQUIRED");
  if(!reference(custodial_review_ref))flags.push("CUSTODIAL_STEWARDSHIP_REVIEW_REQUIRED");
  if(seed_or_spore_material&&!reference(biosecurity_review_ref))
   flags.push("SEED_SPORE_BIOSECURITY_REVIEW_REQUIRED");
 }
 return {schema:BIOBLOCK_PROXY_SCHEMA,parent:"Cognigrex.cgx",owner_family:"Eco.cgx",
  evidence_class,claim,units:{usable_kg:"kg dry mass",carbon_kg_proxy:"kg C",
   stoichiometric_co2_kg_proxy:"kg CO2 mass-equivalent"},
  proxies:{usable_kg,carbon_kg_proxy,stoichiometric_co2_kg_proxy},
  flags,native_object_id:null,db_readback:false,rights_verified:false,
  measured_impact_verified:false,carbon_credit_verified:false,
  field_release_authorised:false,source_only:true};
}


/**
 * Source-only Bio-Blocks germination/establishment expectation review.
 * The site-suitability factor is an uncalibrated synthetic modifier, not an
 * independently measured probability. Fractional expectations are not plants.
 * This adapter cannot verify a field observation, outcome or release permission.
 */
export function reviewBioBlockEstablishmentProxy({
 seed_count,viability_fraction,germination_fraction,site_suitability_factor,survival_fraction,
 evidence_class="simulated",claim="establishment_proxy",source_ref=null,seed_batch_ref=null,
 taxon_ref=null,recipe_ref=null,site_ref=null,sampling_date=null,method_ref=null,
 raw_data_ref=null,baseline_ref=null,control_ref=null,replicate_count=null,
 germinated_count=null,surviving_count=null
}={}){
 const frac=x=>typeof x==="number"&&Number.isFinite(x)&&x>=0&&x<=1;
 const refs=[source_ref,seed_batch_ref,taxon_ref,recipe_ref,site_ref,sampling_date,
  method_ref,raw_data_ref,baseline_ref,control_ref];
 if(!Number.isSafeInteger(seed_count)||seed_count<0||seed_count>1e9||
  ![viability_fraction,germination_fraction,site_suitability_factor,survival_fraction].every(frac)||
  !["observed","simulated","source_asserted","hypothesised","inferred"].includes(evidence_class)||
  !["establishment_proxy","germination_rate","survival_rate","biodiversity_gain"].includes(claim)||
  refs.some(x=>x!==null&&!reference(x))||
  (replicate_count!==null&&(!Number.isSafeInteger(replicate_count)||replicate_count<1))||
  [germinated_count,surviving_count].some(x=>x!==null&&(!Number.isSafeInteger(x)||x<0))||
  (germinated_count!==null&&germinated_count>seed_count)||
  (surviving_count!==null&&(germinated_count===null||surviving_count>germinated_count)))
  throw Error("INVALID_BIOBLOCK_ESTABLISHMENT_INPUT");
 const expected_viable_seeds=seed_count*viability_fraction;
 const expected_germinated=expected_viable_seeds*germination_fraction;
 const expected_established_plants=expected_germinated*site_suitability_factor*survival_fraction;
 const flags=["EXPECTED_COUNT_NOT_OBSERVED","SITE_SUITABILITY_MODIFIER_UNCALIBRATED",
  "MULTIPLICATIVE_ESTABLISHMENT_ASSUMPTIONS_UNVALIDATED"];
 if(!reference(source_ref))flags.push("SOURCE_PROVENANCE_REQUIRED");
 if(evidence_class==="observed"){
  flags.push("FIELD_EVIDENCE_NOT_INDEPENDENTLY_VERIFIED");
  if(germinated_count===null||surviving_count===null)flags.push("OBSERVED_COUNTS_REQUIRED");
  for(const [key,value] of Object.entries({seed_batch_ref,taxon_ref,recipe_ref,site_ref,
   sampling_date,method_ref,raw_data_ref,baseline_ref,control_ref}))
   if(!reference(value))flags.push("MISSING_"+key.toUpperCase());
  if(replicate_count===null||replicate_count<2)flags.push("REPLICATED_TRIAL_EVIDENCE_REQUIRED");
 }else if(germinated_count!==null||surviving_count!==null){
  flags.push("COUNTS_NOT_VERIFIED_AS_FIELD_OBSERVATIONS");
 }
 if(claim!=="establishment_proxy")flags.push("RATE_OR_IMPACT_CLAIM_REQUIRES_METHOD_REVIEW");
 if(claim==="biodiversity_gain")flags.push("BIODIVERSITY_GAIN_NOT_VERIFIED");
 return {schema:"CGX-ECO-BIOBLOCK-ESTABLISHMENT-REVIEW/0.1",
  parent:"Cognigrex.cgx",owner_family:"Eco.cgx",evidence_class,claim,
  units:{seed_count:"seeds",expected_viable_seeds:"seeds (expectation)",
   expected_germinated:"seedlings (expectation)",
   expected_established_plants:"plants (expectation)"},
  proxies:{expected_viable_seeds,expected_germinated,expected_established_plants},
  flags,native_object_id:null,db_readback:false,field_observation_verified:false,
  biodiversity_gain_verified:false,field_release_authorised:false,source_only:true};
}
