/** Owner-proposed 173+1 review addressing. References only; no registry or mint authority. */
export const FAMILY_OBJECT_CAPACITY=173;
export const FAMILY_FOUNDER_SLOT=174;
export function planFamilyAddresses(sourceRefs,{rootRef='Cognigrex.cgx'}={}){
 if(typeof rootRef!=='string'||!rootRef.trim())throw Error('ROOT_REFERENCE_REQUIRED');
 if(!Array.isArray(sourceRefs)||sourceRefs.some(r=>typeof r!=='string'||!r.trim()))throw Error('EXISTING_SOURCE_REFERENCE_REQUIRED');
 const unique=[...new Set(sourceRefs)],groups=[];
 function fold(refs,path){
  const node={path,founder:{slot:FAMILY_FOUNDER_SLOT,kind:'self-reference',target:rootRef,target_path:[...path],mintable:false},slots:[]};
  groups.push(node);
  if(refs.length<=FAMILY_OBJECT_CAPACITY){
   node.slots=refs.map((source_ref,i)=>({slot:i+1,kind:'object-reference',source_ref,native_mint_ready:false}));
  }else{
   let span=FAMILY_OBJECT_CAPACITY;
   while(Math.ceil(refs.length/span)>FAMILY_OBJECT_CAPACITY)span*=FAMILY_OBJECT_CAPACITY;
   for(let i=0;i<refs.length;i+=span){
    const slot=node.slots.length+1,child=[...path,slot];
    node.slots.push({slot,kind:'umbrella-reference',child_path:child,mintable:false});
    fold(refs.slice(i,i+span),child);
   }
  }
 }
 fold(unique,[]);
 return {schema:'CGX-173-PLUS-REFERENCE-ADDRESS-REVIEW/0.1',parent:rootRef,evidence_class:'OWNER_PROPOSED_ADDRESSING',
  object_slots_per_group:173,reference_slot:174,source_reference_count:sourceRefs.length,unique_reference_count:unique.length,
  duplicate_references:sourceRefs.length-unique.length,ordering:'input order; no inferred semantic class',groups,
  ternary_state_encoding:'UNRESOLVED',physical_completeness_verified:false,geometry_catalogue_verified:false,
  founder_is_object:false,new_database:false,native_mint:false,canonical_write:false};
}
