/**
 * Public-safe topology and private/operator visual REVIEW model.
 * This is not a native Object_ID registry, signer, resolver, DBR or mint API.
 * The deterministic lattice is view metadata only; changing it never changes
 * family containment, dependency pins or evidence/rights authority.
 */
export const SCHEMA='CGX-FIRST-SPACES-REVIEW-LATTICE/0.1';
const raw=[
 ['family.cognigrex','Cognigrex Family Set','canonical-parent',null,[],'root'],
 ['facet.load','LOAD / Alexandria','resolver-facet','family.cognigrex',['family.cognigrex'],'resolver'],
 ['family.romer','Römer-Grex','grex-family','family.cognigrex',['facet.load'],'engineering'],
 ['family.eco','Eco-Grex','grex-family','family.cognigrex',['facet.load'],'ecology'],
 ['family.emassc','EMASSC-Grex','grex-family','family.cognigrex',['facet.load'],'engineering'],
 ['family.ls','LightSpeed / LS','nested-grex','family.emassc',['family.emassc','facet.load'],'execution'],
 ['space.filespace','FileSpace','functional-space','family.cognigrex',['facet.load'],'evidence'],
 ['space.unispace-control','UniSpace FileSpace control','product-facet','space.filespace',['space.filespace'],'presentation'],
 ['space.dataspace','DataSpace','functional-space','space.filespace',['space.filespace','space.unispace-control'],'evidence'],
 ['space.printspace','PrintSpace','functional-space','space.dataspace',['space.dataspace'],'creative'],
 ['facet.ccc','CCC / skill routing','orchestration-facet','facet.load',['facet.load','family.ls'],'execution'],
];
const NODES=Object.freeze(raw.map(([key,label,kind,parent,requires,role])=>Object.freeze({
 key,label,kind,parent,requires:Object.freeze(requires),role,
 candidate_object_id:null,source_rights:'UNVERIFIED',
 native_issuer:'UNVERIFIED',native_minted:false
})));
const KEYS=new Set(NODES.map(n=>n.key));
const validOrder=order=>Array.isArray(order)&&order.length===NODES.length&&
 order.every(x=>typeof x==='string'&&KEYS.has(x))&&new Set(order).size===NODES.length;
const validDecisions=decisions=>decisions!==null&&typeof decisions==='object'&&
 !Array.isArray(decisions)&&Object.keys(decisions).every(k=>KEYS.has(k)&&
 ['approve','deny','defer'].includes(decisions[k]));
const hold=reason=>Object.freeze({schema:SCHEMA,state:'HOLD',reason,
 native_minted:false,canonical_mutation:false,may_sign:false,may_publish:false});
export function planFirstSpacesReview({order=null,layout='lattice',focus='facet.load',decisions={}}={}){
 if(!['lattice','family-tree','space-grid'].includes(layout)||!KEYS.has(focus)||
   (order!==null&&!validOrder(order))||!validDecisions(decisions))return hold('INVALID_VISUAL_REVIEW_INPUT');
 const ordering=order??NODES.map(n=>n.key);
 const nodes=ordering.map((key,i)=>{
  const n=NODES.find(x=>x.key===key);
  const stage=decisions[key]==='approve'?'DESIGN_APPROVED_ONLY':
   decisions[key]==='deny'?'DESIGN_DENIED_ONLY':
   decisions[key]==='defer'?'DESIGN_DEFERRED':'AWAITING_DESIGN_REVIEW';
  return {...n,requires:[...n.requires],display_order:i,
   review_stage:stage,recorded_founder_approval:false,
   mint_eligible:false,can_execute:false};
 });
 const edges=NODES.flatMap(n=>[
  ...(n.parent?[{from:n.parent,to:n.key,kind:'containment'}]:[]),
  ...n.requires.map(x=>({from:x,to:n.key,kind:'dependency'}))
 ]);
 return {schema:SCHEMA,state:'SOURCE_REVIEW_ONLY',canonical_parent:'cgx:root:cognigrex',
  library:'LOAD.cgx',product:'UniSpace',layout,focus,order:[...ordering],nodes,edges,
  mint_sequence:['family.cognigrex','facet.load','family.romer','family.eco',
    'family.emassc','family.ls','space.filespace','space.unispace-control',
    'space.dataspace','space.printspace','facet.ccc'],
  semantic_views:['document','3d','chat','graph','matrix','interactive'],
  review_interaction:'LOCAL_EPHEMERAL_VISUAL_ONLY',
  parent_identity_status:'SOURCE_DESIGN_NOT_NATIVE_ROOT',
  rights_qualified:false,independent_dbr:false,
  signed_issuer:false,native_minted:false,canonical_mutation:false,
  may_sign:false,may_publish:false,may_deploy:false,
  source_bytes_transferred:0,network_transfer:false};
}
