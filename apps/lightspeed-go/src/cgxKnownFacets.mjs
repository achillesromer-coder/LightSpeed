/** Derived facet view over verified local composition bytes; never another object registry. */
import {exportComposition} from './cgxPressComposition.mjs';
import {restoreBatchDraft} from './cgxLoadBatchDraft.mjs';
import {planFamilyAddresses} from './cgxFamilyAddressModel.mjs';
export async function resolveKnownFacets(composition){
 const verified=await exportComposition(composition);
 const objects=composition.assets.map(a=>({
  source_ref:'sha256:'+a.id,evidence:'LOCAL_BYTES_HASH_VERIFIED',native_object_id:null,
  known:{source_name:a.name,source_sha256:a.id,byte_size:a.size,mime:a.mime,preview_handler:a.handler,
   ...(a.text?{source_text_preview:a.text,source_text_preview_may_be_truncated:true}:{})},
  presentation_facets:composition.layers.filter(l=>l.asset_id===a.id).map(l=>({layer_ref:l.id,kind:l.kind,parent_layer:l.parent_id,source_annotation:l.source_ref})),
  unresolved:['native_identity','source_rights_acceptance','semantic_equivalence','physical_geometry','contract_authority']
 }));
 return {schema:'CGX-KNOWN-FACETS-DERIVED-REVIEW/0.1',parent:'Cognigrex.cgx',composition_sha256:verified.composition_sha256,
  objects,display_only_layers:composition.layers.filter(l=>!l.asset_id).map(l=>l.id),
  source_body_copies:0,new_database:false,native_mint:false,semantic_acceptance:false,
  rule:'Known facts come from verified bytes; annotations and unverified claims do not become database knowledge.'};
}
export function readKnownFacet(resolution,sourceRef,key){
 const object=resolution.objects.find(o=>o.source_ref===sourceRef);
 if(!object)throw Error('SOURCE_OBJECT_UNRESOLVED');
 if(!Object.hasOwn(object.known,key))throw Error('FACET_UNKNOWN_OR_UNVERIFIED');
 return object.known[key];
}
export async function resolveLoadReferenceFacets(text){
 const {draft}=await restoreBatchDraft(text);
 const claimedGroups=new Map();
 for(const source of draft.source_records){
  const key=source.source_sha256?'claimed-sha256:'+source.source_sha256:'pointer:'+source.pointer_sha256;
  if(!claimedGroups.has(key))claimedGroups.set(key,{review_group_ref:key,source_sha256_claim:source.source_sha256,
   source_bytes_verified:false,native_object_id:null,source_pointers:[],known_facets:['source_locator','pointer_identity','declared_owner_routes'],
   unresolved_facets:['original_source_bytes','source_version','rights_acl','native_identity','semantic_equivalence'],native_mint_ready:false});
  claimedGroups.get(key).source_pointers.push({review_ref:source.review_ref,locator:source.locator,name:source.name,owner_routes:source.routes});
 }
 return {schema:'CGX-LOAD-FACET-PRERESOLUTION-REVIEW/0.1',parent:'Cognigrex.cgx',load_plan_sha256:draft.plan_sha256,
  source_reference_count:draft.source_records.length,selected_reference_count:draft.summary.selected_records,batch_count:draft.summary.batches,
  candidate_groups:[...claimedGroups.values()],family_address_review:planFamilyAddresses([...claimedGroups.keys()]),deduplication:'Declared same-digest groups only; no source deletion or semantic/native identity merge.',
  representation_options:['flat-2d','dodecagon','folded-sheet','stacked-sheets','volume-3d'],representation_geometry_verified:false,
  socialspace:{parent:'FileSpace',kind:'constituent',user_domain_ref:null,profile_mint_authorized:false,visibility:'private',searchable:false,networking_enabled:false},
  native_mint_ready_objects:0,canonical_write:false,source_body_copies:0};
}
