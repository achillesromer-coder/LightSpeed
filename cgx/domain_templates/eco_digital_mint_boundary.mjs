/**
 * Eco.cgx review-only boundary for Git.CGX's synthetic EcoObservation showcase.
 * This is a PROPOSED bridge shape, not a recovered full Digital Mint class ABI,
 * native mint, ecological observation registry, field QA, or publication approval.
 * Do not export source bodies, specimen locations, or raw geometry.
 */
export const ECO_MINT_BOUNDARY_SCHEMA="CGX-ECO-DIGITAL-MINT-BOUNDARY/0.1";
const object=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const ref=x=>typeof x==="string"&&x.length>0&&x.length<=256&&!/[\u0000-\u001f]/.test(x);
const add=(a,s)=>{if(!a.includes(s))a.push(s)};
const classes=new Set(["observed","simulated","source_asserted","hypothesised","inferred"]);
const isoZoned=x=>{
 if(!ref(x))return false;
 const m=/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,9})?(Z|[+-](\d{2}):(\d{2}))$/.exec(x);
 if(!m)return false;
 const [y,mo,d,h,mi,s]=m.slice(1,7).map(Number);
 const leap=y%4===0&&(y%100!==0||y%400===0);
 const days=[31,leap?29:28,31,30,31,30,31,31,30,31,30,31];
 if(y<1||mo<1||mo>12||d<1||d>days[mo-1]||h>23||mi>59||s>59)return false;
 if(m[7]!=="Z"){
  const oh=Number(m[8]),om=Number(m[9]);
  if(oh>14||om>59||(oh===14&&om!==0))return false;
 }
 return true;
};
export function reviewEcoObservationShowcase({record,authorised_source_refs=[],public_release_requested=false}={}){
 if(!object(record)||record.kind!=="EcoObservation"||typeof record.measured!=="boolean"||
    !Array.isArray(authorised_source_refs)||authorised_source_refs.length>5000||
    !authorised_source_refs.every(ref)||typeof public_release_requested!=="boolean")
   throw Error("INVALID_ECO_MINT_BRIDGE");
 if(record.synthetic!==undefined&&typeof record.synthetic!=="boolean")throw Error("INVALID_SYNTHETIC_FLAG");
 if(record.evidence_class!==undefined&&!classes.has(record.evidence_class))throw Error("INVALID_ECO_MINT_EVIDENCE_CLASS");
 if(record.measurement!==undefined&&(!object(record.measurement)||
   typeof record.measurement.value!=="number"||!Number.isFinite(record.measurement.value)||
   !ref(record.measurement.unit)))throw Error("INVALID_ECO_MINT_MEASUREMENT");
 for(const field of ["taxon","place","method","source_provenance","source_revision_ref",
  "source_owner_ref","source_hash_sha256","field_record_ref","observed_at",
  "seasonal_frame_ref","spatial_sensitivity_review_ref","rights_review_ref","acl_review_ref",
  "specimen_id","subject_kind"]){
   if(record[field]!==undefined&&!ref(record[field]))throw Error("INVALID_ECO_MINT_FIELD_"+field.toUpperCase());
 }
 const checks=[];
 for(const [field,flag] of [["taxon","TAXON_REFERENCE_REQUIRED"],["place","PLACE_REFERENCE_REQUIRED"],
  ["method","METHOD_REFERENCE_REQUIRED"],["source_provenance","SOURCE_PROVENANCE_REQUIRED"]])
  if(!ref(record[field]))add(checks,flag);
 if(!ref(record.evidence_class))add(checks,"EVIDENCE_CLASS_REQUIRED");
 if(!ref(record.source_revision_ref))add(checks,"SOURCE_REVISION_REQUIRED");
 if(!ref(record.source_owner_ref))add(checks,"SOURCE_OWNER_REQUIRED");
 if(!ref(record.source_provenance)||!authorised_source_refs.includes(record.source_provenance))
  add(checks,"SOURCE_NOT_IN_AUTHORISED_SCOPE");
 if(record.synthetic===true&&record.evidence_class==="observed")
  add(checks,"SYNTHETIC_FIXTURE_CANNOT_ASSERT_OBSERVED_EVIDENCE");
 if(record.measured&&!record.measurement)add(checks,"MEASURED_FLAG_REQUIRES_QUANTITY_AND_UNIT");
 if(!record.measured&&record.measurement)add(checks,"UNMEASURED_FLAG_CONFLICTS_WITH_NUMERIC_MEASUREMENT");
 if(record.subject_kind==="specimen"&&!ref(record.specimen_id))
  add(checks,"SPECIMEN_IDENTITY_REQUIRED");
 if(record.evidence_class==="observed"){
  if(!ref(record.field_record_ref))add(checks,"ORIGINAL_FIELD_RECEIPT_REQUIRED");
  if(!isoZoned(record.observed_at))add(checks,"ZONED_OBSERVATION_TIMESTAMP_REQUIRED");
  if(!ref(record.seasonal_frame_ref))add(checks,"SEASONAL_CONTEXT_REQUIRED");
  if(!/^[a-f0-9]{64}$/i.test(record.source_hash_sha256??""))add(checks,"ORIGINAL_EVIDENCE_HASH_REQUIRED");
  // Presence of a receipt/hash is not independent evidence of field validity.
  add(checks,"FIELD_EVIDENCE_INDEPENDENT_REVIEW_REQUIRED");
 }
 if(public_release_requested){
  add(checks,"PUBLIC_RELEASE_OWNER_APPROVAL_REQUIRED");
  if(!ref(record.rights_review_ref))add(checks,"PUBLIC_RIGHTS_REVIEW_REQUIRED");
  if(!ref(record.acl_review_ref))add(checks,"PUBLIC_ACL_REVIEW_REQUIRED");
  if(!ref(record.spatial_sensitivity_review_ref))add(checks,"SPATIAL_SENSITIVITY_REVIEW_REQUIRED");
  // A sensitivity-review reference is not proof that precise sites are safe to disclose.
  add(checks,"NO_AUTOMATIC_SPECIMEN_OR_SITE_GEOMETRY_RELEASE");
 }
 return {schema:ECO_MINT_BOUNDARY_SCHEMA,owner_family:"Eco.cgx",parent:"Cognigrex.cgx",
  target_class:"EcoObservation",candidate_semantic_type:"ecological_observation",
  state:checks.length?"REVIEW_REQUIRED":"SCHEMA_BRIDGE_CANDIDATE_ONLY",
  checks,permitted_source_refs:ref(record.source_provenance)&&
    authorised_source_refs.includes(record.source_provenance)?[record.source_provenance]:[],
  synthetic:record.synthetic===true,measured_flag:record.measured,
  native_object_id:null,object_id_minted:false,accepted_native_identity:false,
  db_readback:false,source_rights_verified:false,field_observation_verified:false,
  ecological_benefit_verified:false,public_release_authorised:false,
  geometry_emitted:false,source_body_emitted:false};
}
