/** Review-only CGX geometry shorthand planner; no execution, provider calls or native admission. */
const PLAN = 'DRY_RUN_REVIEW_ONLY';
const SLOT_RE = /^T173:(\d{3})$/;
const RELATIONS = new Set(['is_a','part_of','has_mesh','has_role','equivalent_to','mirrors','adjacent_to','depends_on','encapsulates','interacts_with','derived_from','measured_by','validated_by','constrained_by','contradicts','supports']);
const AXES = Object.freeze(['X','E','L','T','P','C','V','R','I','B','U','Q']);
export class CGXLanguageError extends Error {}
export function parseSlot(slot, registry) {
  if (typeof slot !== 'string') throw new CGXLanguageError('Slot must be a string');
  const match = SLOT_RE.exec(slot);
  if (!match) throw new CGXLanguageError('Use literal T173:001..173');
  const n = Number(match[1]);
  if (n === 174) throw new CGXLanguageError('T173:174 is reserved null and nonmintable');
  if (n < 1 || n > 173) throw new CGXLanguageError('Outside T173:001..173');
  if (!registry || registry.schema !== 'cgx.neo.t173.reference-review/0.1' || !Array.isArray(registry.slots) || registry.slots.length !== 173) throw new CGXLanguageError('Review registry missing or incompatible');
  const entry = registry.slots[n-1];
  if (!entry || entry.slot !== slot || entry.native_admitted !== false) throw new CGXLanguageError('Registry order, state or identity mismatch');
  return entry;
}
function planned(kind, details) { return {schema:'cgx.geometry.ast/0.1',kind,status:PLAN,effects_performed:false,authority_transfer:false,...details}; }
export function compileLine(line, registry) {
  if (typeof line !== 'string' || line.length > 256) throw new CGXLanguageError('Shorthand line required, bounded to 256 characters');
  const tok = line.trim().split(/\s+/).filter(Boolean);
  if (tok.length < 2) throw new CGXLanguageError('Missing tokens');
  const action = tok[0];
  if (action === 'SELECT' && tok.length === 2) {
    const e=parseSlot(tok[1],registry);
    return planned('geometry_reference',{slot:e.slot,geometry_role:e.geometry_role,mesh_ref:e.mesh_ref,qualifier:e.qualifier});
  }
  if ((action==='RELATE' || action==='TRIAD') && tok.length===4) {
    const a=parseSlot(tok[1],registry), b=parseSlot(tok[3],registry), relation=tok[2];
    if (!RELATIONS.has(relation)) throw new CGXLanguageError('Unregistered relation token');
    return planned(action==='TRIAD'?'triadic_relation':'relation_proposal',{left:a.slot,right:b.slot,relation,semantic_trit:0,epistemic_status:'UNRESOLVED',requires_evidence:true,x:evidenceFacet(a),e:evidenceFacet(b)});
  }
  if (action==='PLAN_HYDRATE'&&tok.length===2) {
    const e=parseSlot(tok[1],registry);
    return planned('hydrate_plan',{slot:e.slot,mesh_ref:e.mesh_ref,requirements:['authenticated_lease','rights','source_digest','budget','source_readback'],hydrated:false});
  }
  if (action==='PLAN_TRANSFORM'&&tok.length===5) {
    const e=parseSlot(tok[1],registry);
    const p=Object.fromEntries(tok.slice(2).map(t=>t.split('=',2)));
    if (!tok.slice(2).every(t=>/^(scale|unit|frame)=\S+$/.test(t)) || Object.keys(p).sort().join(',')!=='frame,scale,unit') throw new CGXLanguageError('Expected scale, unit, frame');
    const scale=Number(p.scale);
    if(!Number.isFinite(scale)||scale<=0||scale>1000000||!/^[A-Za-z][\w\/-]{0,20}$/.test(p.unit)||!/^[A-Za-z][\w\/-]{0,30}$/.test(p.frame))throw new CGXLanguageError('Invalid geometric transform parameters');
    return planned('transform_plan',{slot:e.slot,transform:'uniform_scale',factor:scale,unit:p.unit,frame:p.frame,geometry_mutated:false,requirements:['geometry_source_hydration','source_and_target_frame_registry','units','rights','tolerance']});
  }
  if (action==='ENCODE_BYTES'&&tok.length===2) {
    if (!/^(?:[0-9a-fA-F]{2})*$/.test(tok[1]) || tok[1].length>128) throw new CGXLanguageError('Hex payload required, maximum 64 bytes');
    const bytes=Uint8Array.from(tok[1].match(/.{2}/g)?.map(s=>parseInt(s,16)) || []);
    return planned('transport_encode',{hex:tok[1].toLowerCase(),trits:encodeBytes(bytes),transport_only:true});
  }
  if (action==='DECODE_BYTES'&&tok.length===2) {
    return planned('transport_decode',{hex:Array.from(decodeBytes(tok[1]),v=>v.toString(16).padStart(2,'0')).join(''),transport_only:true});
  }
  throw new CGXLanguageError('Unknown or invalid operator');
}
function evidenceFacet(e){return {slot:e.slot,mesh_ref:e.mesh_ref,qualifier:e.qualifier};}
export function encodeBytes(bytes) {
  if (!(bytes instanceof Uint8Array)) throw new CGXLanguageError('Uint8Array required');
  let s=''; for(const b of bytes) s+=b.toString(3).padStart(6,'0'); return s;
}
export function decodeBytes(trits) {
  if(typeof trits!=='string'||!/^([012]{6})*$/.test(trits))throw new CGXLanguageError('Invalid transport trits');
  const data=new Uint8Array(trits.length/6);
  for(let i=0;i<data.length;i++){let n=parseInt(trits.slice(i*6,i*6+6),3);if(n>255)throw new CGXLanguageError('Invalid byte value in six trits');data[i]=n;}
  return data;
}
export function validateRegistry(registry) {
  if(!registry||registry.role_count!==173||registry.mesh_payload_count!==157||registry.sentinel!=='T173:174 RESERVED_NULL_NOT_OBJECT') throw new CGXLanguageError('Registry count/sentinel mismatch');
  if(!Array.isArray(registry.slots)||registry.slots.length!==173)throw new CGXLanguageError('Missing slot records');
  const seen=new Set();
  registry.slots.forEach((e,i)=>{const slot=`T173:${String(i+1).padStart(3,'0')}`;if(e.slot!==slot||seen.has(e.slot)||e.native_admitted!==false)throw new CGXLanguageError('Duplicate, reordered or incorrectly admitted slot');seen.add(e.slot);});
  return {status:'BASIC_REVIEW_REGISTRY_VALID',slots:seen.size,axes:AXES.length,geometry_proven:false,rights_verified:false};
}