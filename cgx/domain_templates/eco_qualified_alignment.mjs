/**
 * Eco.cgx source-only ecological identity discrimination for qualified LOAD candidates.
 * An Eco-specific review adapter, NOT a new canonical resolver or a second LOAD registry.
 * No data acquisition, coordinates transformation, inference, merging, Object_ID minting or DBR writes.
 */
export const ECO_ALIGNMENT_SCHEMA="CGX-ECO-QUALIFIED-ALIGNMENT/0.1";
const good=s=>typeof s==="string"&&s.trim().length>0&&s.length<=256&&!/[\u0000-\u001f]/.test(s);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const stringList=x=>Array.isArray(x)&&x.length<=5000&&x.every(good);
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const EVIDENCE=new Set(["observed","simulated","source_asserted","hypothesised","inferred","independently_reviewed"]);
const ECO_TYPES=new Set(["taxon","species","specimen","population","ecological_observation","sensor_reading","site","habitat","intervention","experiment","ecological_state_estimate"]);
const IDENTITY=["taxon_id","specimen_id","population_id","site_id","station_id","subject_kind","subject_id"];
const OBSERVATIONS=new Set(["ecological_observation","sensor_reading"]);
function validateConcept(x){
 if(!obj(x)||!ECO_TYPES.has(x.semantic_type)||!stringList(x.source_refs))throw Error("INVALID_ECO_CONCEPT");
 if(x.object_id!==undefined&&!good(x.object_id))throw Error("INVALID_OBJECT_ID");
 for(const f of [...IDENTITY,"observed_at","method_id","unit","frame","environment_id","configuration","epoch","aggregation_scope","baseline_id"]){
  if(x[f]!==undefined&&x[f]!==null&&!good(x[f]))throw Error("INVALID_ECO_FIELD_"+f);
 }
 if(x.sample_count!==undefined&&(!Number.isSafeInteger(x.sample_count)||x.sample_count<1))throw Error("INVALID_SAMPLE_COUNT");
 if(x.evidence_class!==undefined&&!EVIDENCE.has(x.evidence_class))throw Error("INVALID_EVIDENCE_CLASS");
 if(x.geometry!==undefined){
  const g=x.geometry;
  if(!obj(g)||g.type!=="Point"||!good(g.crs)||!Array.isArray(g.coordinates)||
   ![2,3].includes(g.coordinates.length)||!g.coordinates.every(v=>typeof v==="number"&&Number.isFinite(v)))
    throw Error("INVALID_GEOMETRY");
  if(g.crs==="EPSG:4326"&&(g.coordinates[0]<-180||g.coordinates[0]>180||g.coordinates[1]<-90||g.coordinates[1]>90))
    throw Error("INVALID_WGS84_COORDINATES");
  if(g.vertical_datum!==undefined&&!good(g.vertical_datum))throw Error("INVALID_VERTICAL_DATUM");
 }
 if(x.environment!==undefined&&(!obj(x.environment)||Object.keys(x.environment).length>50))throw Error("INVALID_ENVIRONMENT");
 if(x.measurement!==undefined){
  if(!obj(x.measurement)||typeof x.measurement.value!=="number"||!Number.isFinite(x.measurement.value)||
   !good(x.measurement.unit))throw Error("INVALID_MEASUREMENT");
 }
}
const add=(checks,c)=>{if(!checks.includes(c))checks.push(c)};
function compare(a,b,checks){
 for(const f of IDENTITY){
  if(a[f]!==b[f]){
   add(checks,a[f]===undefined||b[f]===undefined?"IDENTITY_FIELD_MISSING_"+f.toUpperCase():"IDENTITY_DIFFERENCE_"+f.toUpperCase());
  }
 }
 if(a.aggregation_scope!==b.aggregation_scope)add(checks,"AGGREGATION_SCOPE_DIFFERENT_OR_UNDECLARED");
 if(a.sample_count!==b.sample_count)add(checks,"SAMPLE_COUNT_DIFFERENT_OR_UNDECLARED");
 if(a.baseline_id!==b.baseline_id)add(checks,"BASELINE_DIFFERENT_OR_UNDECLARED");
 if(a.evidence_class!==b.evidence_class)add(checks,"EVIDENCE_CLASS_DIFFERENT_OR_UNDECLARED");
 if(a.observed_at!==b.observed_at)add(checks,"OBSERVATION_TIME_DIFFERENT_OR_UNDECLARED");
 if(a.method_id!==b.method_id)add(checks,"METHOD_DIFFERENT_OR_UNDECLARED");
 if(a.frame!==b.frame)add(checks,"FRAME_TRANSFORM_OR_DEFINITION_REQUIRED");
 if(a.configuration!==b.configuration)add(checks,"CONFIGURATION_VARIANT");
 if(a.epoch!==b.epoch)add(checks,"TIME_VARIANT");
 if(a.environment_id!==b.environment_id||!equal(a.environment??null,b.environment??null))
  add(checks,"ENVIRONMENT_CONTEXT_DIFFERENT");
 if(a.unit!==b.unit&&a.unit!==undefined&&b.unit!==undefined)add(checks,"UNIT_CONVERSION_REQUIRED");
 else if((a.unit===undefined)!==(b.unit===undefined))add(checks,"UNIT_UNDECLARED");
 if(!equal(a.measurement??null,b.measurement??null)){
  if(a.measurement&&b.measurement&&a.measurement.unit!==b.measurement.unit)add(checks,"UNIT_CONVERSION_REQUIRED");
  add(checks,"MEASUREMENT_VALUE_OR_METHOD_DIFFERENT");
 }
 if(!equal(a.geometry??null,b.geometry??null)){
  if(a.geometry?.crs!==b.geometry?.crs)add(checks,"GEOMETRY_CRS_DIFFERENT_OR_UNDECLARED");
  add(checks,"GEOMETRY_DIFFERENT_OR_UNDECLARED");
 }
 if(a.geometry?.coordinates.length===3&&!a.geometry.vertical_datum||
    b.geometry?.coordinates.length===3&&!b.geometry.vertical_datum)add(checks,"VERTICAL_DATUM_REQUIRED");
}
function completeness(x,checks){
 if(!good(x.evidence_class))add(checks,"EVIDENCE_CLASS_REQUIRED");
 if(x.semantic_type==="sensor_reading"&&!x.measurement)add(checks,"SENSOR_MEASUREMENT_REQUIRED");
 if(x.measurement&&good(x.unit)&&x.unit!==x.measurement.unit)add(checks,"MEASUREMENT_UNIT_CONFLICT");
 if(OBSERVATIONS.has(x.semantic_type)){
  if(!good(x.observed_at))add(checks,"OBSERVATION_TIME_REQUIRED");
  if(!good(x.method_id))add(checks,"METHOD_REQUIRED");
  if(!good(x.subject_kind)||!good(x.subject_id))add(checks,"SUBJECT_IDENTITY_REQUIRED");
  if(!good(x.site_id)&&!good(x.station_id)&&!x.geometry)add(checks,"SPATIAL_CONTEXT_REQUIRED");
  if(x.measurement&&!good(x.measurement.unit))add(checks,"UNIT_REQUIRED");
  if(x.geometry&&!good(x.geometry.crs))add(checks,"GEOMETRY_CRS_REQUIRED");
 }
 if(x.semantic_type==="specimen"&&!good(x.specimen_id))add(checks,"SPECIMEN_ID_REQUIRED");
 if(["species","taxon"].includes(x.semantic_type)&&!good(x.taxon_id))add(checks,"TAXON_ID_REQUIRED");
 if(x.semantic_type==="population"&&(!good(x.population_id)||!good(x.taxon_id)))add(checks,"POPULATION_TAXON_ID_REQUIRED");
 if(x.geometry?.coordinates.length===3&&!x.geometry.vertical_datum)add(checks,"VERTICAL_DATUM_REQUIRED");
}
export function planEcoAlignment({novel,known_objects=[],authorised_object_ids=[],authorised_source_ids=[],max_candidates=20}={}){
 validateConcept(novel);
 if(!Array.isArray(known_objects)||known_objects.length>5000||!stringList(authorised_object_ids)||
 !stringList(authorised_source_ids)||!Number.isSafeInteger(max_candidates)||max_candidates<1||max_candidates>100)
  throw Error("INVALID_ECO_SCOPE");
 const allowedIds=new Set(authorised_object_ids),allowedSources=new Set(authorised_source_ids);
 const novelRefs=novel.source_refs.filter(s=>allowedSources.has(s));
 const seen=new Set(),out=[];
 for(const k of known_objects){
  validateConcept(k);
  if(!good(k.object_id)||!allowedIds.has(k.object_id))continue;
  if(seen.has(k.object_id))throw Error("DUPLICATE_AUTHORISED_OBJECT_ID");
  seen.add(k.object_id);
  if(k.semantic_type!==novel.semantic_type)continue;
  const checks=[];
  completeness(novel,checks);completeness(k,checks);compare(novel,k,checks);
  const refs=k.source_refs.filter(s=>allowedSources.has(s));
  if(!novelRefs.length||!refs.length)add(checks,"EVIDENCE_SOURCE_GAP");
  else if(!refs.some(s=>novelRefs.includes(s)))add(checks,"SOURCE_LINEAGE_DISJOINT_REVIEW");
  if(novelRefs.length<novel.source_refs.length)add(checks,"NOVEL_SOURCE_SCOPE_PARTIAL");
  if(refs.length<k.source_refs.length)add(checks,"KNOWN_SOURCE_SCOPE_PARTIAL");
  const exactId=novel.object_id===k.object_id;
  out.push({known_object_id:k.object_id,
   state:exactId?"SAME_ID_CLAIM_REQUIRES_PROOF":checks.length?"REVIEW_DIFFERENCE":"TYPED_ALIGNMENT_CANDIDATE",
   checks,permitted_known_source_refs:refs,auto_merge:false,object_id_minted:false,source_rights_verified:false});
 }
 out.sort((a,b)=>a.checks.length-b.checks.length||a.known_object_id.localeCompare(b.known_object_id));
 return {schema:ECO_ALIGNMENT_SCHEMA,state:"SOURCE_ONLY_ECO_REVIEW",file_space:"Eco.cgx",
  parent:"Cognigrex.cgx",semantic_type:novel.semantic_type,
  candidate_count:out.length,candidates:out.slice(0,max_candidates),
  incomplete_coverage:out.length>max_candidates,novel_permitted_source_refs:novelRefs,
  distinct_r0_sources_preserved:true,accepted_native_identity:false,db_readback:false,
  object_ids_minted:0,ecological_effect_verified:false,compute_invoked:false,
  unresolved:["source licence and ownership","current root/ACL and DBR acceptance","independent field evidence and counterevidence","geometry and measurement method validation"]};
}
