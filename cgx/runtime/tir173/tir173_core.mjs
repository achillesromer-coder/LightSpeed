/** TIR/173 bridge. Pure deterministic representation; never performs native CGX actions. */
export const TIR_SCHEMA='cgx.tir173/0.2';
export const ROLE_COUNT=173, SENTINEL=174, STATE_BYTES=35;
export const INTENTS=['geometry','object','interaction','field','state','source_ref','view','operation'];
export const EVIDENCE=['SUPPORTED','REFUTED','UNRESOLVED','CONFLICT','NO_DATA','WITHHELD','NOT_AUTHORISED','INVALID','NOT_CACHED'];
const STATES=new Set([-1,0,1]);
const BAD=new Set(['__proto__','prototype','constructor']);
export class TIRError extends Error {constructor(code){super(code);this.code=code;}}
const must=(c,e)=>{if(!c)throw new TIRError(e);};
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
export function roleIndex(i){must(Number.isInteger(i)&&i>=1&&i<=ROLE_COUNT,'ROLE_OUT_OF_RANGE_174_IS_SENTINEL');return i;}
export function slotName(i){return `T173:${String(roleIndex(i)).padStart(3,'0')}`;}
export function normaliseRole(i){if(typeof i==='string'){const m=/^T173:(\d{3})$/.exec(i);must(m,'BAD_ROLE_FORMAT');return roleIndex(Number(m[1]));}return roleIndex(i);}
export function validateDictionary(d){
 must(d?.schema==='cgx.t173.shape_dictionary/0.2'&&Array.isArray(d.roles)&&d.roles.length===173,'DICTIONARY_CONTRACT');
 must(typeof d.source_sha256==='string'&&/^[a-f0-9]{64}$/.test(d.source_sha256),'SOURCE_HASH_REQUIRED');
 for(let i=0;i<173;i++){
  const e=d.roles[i];must(e&&e.slot===i+1&&e.role===slotName(i+1)&&typeof e.name==='string'&&e.name.length>0,'ROLE_SEQUENCE');
  must(typeof e.mesh_ref==='string'&&e.mesh_ref.length>0,'GEOMETRY_REF_REQUIRED');
  must(typeof e.evidence==='string'&&e.evidence.length>0,'GEOMETRY_EVIDENCE_REQUIRED');
 }
 must(!own(d,'sentinel')||d.sentinel===null,'SENTINEL_MUST_BE_NULL');
 must(d.roles.every(e=>e.slot!==174),'SENTINEL_MINT_DENIED');
 return {roles:173,unique_mesh_refs:new Set(d.roles.map(e=>e.mesh_ref)).size,source:d.source_sha256,status:'SOURCE_REVIEW_ONLY'};
}
/** 5 *transport* trits encode a local ordinal, not a ternary epistemic state. */
export function encodeOrdinal(slot){let n=roleIndex(slot)-1, out='';for(let k=0;k<5;k++){out=String(n%3)+out;n=Math.floor(n/3);}return out;}
export function decodeOrdinal(t){must(typeof t==='string'&&/^[012]{5}$/.test(t),'INVALID_ADDRESS_TRITS');let n=0;for(const k of t)n=n*3+Number(k);return roleIndex(n+1);}
export function encodePath(path){must(Array.isArray(path)&&path.length>0&&path.length<=8,'PATH_DEPTH');return path.map(encodeOrdinal).join('/');}
export function decodePath(t){must(typeof t==='string'&&t.length<=47,'BAD_ADDRESS');return t.split('/').map(decodeOrdinal);}
/** Balanced semantic state vector. Zero is NEUTRAL, never absent. Bigint -> 35-byte binary. */
export function pack173(states){must(Array.isArray(states)&&states.length===173,'STATE_VECTOR_173_REQUIRED');let x=0n,p=1n;for(const s of states){must(STATES.has(s),'BAD_TRIT');x+=BigInt(s+1)*p;p*=3n;}const bytes=new Uint8Array(35);for(let i=0;i<35;i++){bytes[i]=Number(x&255n);x>>=8n;}must(x===0n,'STATE_OVERFLOW');return bytes;}
export function unpack173(bytes){must(bytes instanceof Uint8Array&&bytes.length===35,'STATE_BLOCK_35_BYTES');let x=0n;for(let i=34;i>=0;i--)x=(x<<8n)+BigInt(bytes[i]);const out=[];for(let i=0;i<173;i++){out.push(Number(x%3n)-1);x/=3n;}must(x===0n,'TRIT_BLOCK_OUT_OF_RANGE');return out;}
export function hex(bytes){return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');}
export function unhex(s){must(typeof s==='string'&&/^(?:[a-f0-9]{2})*$/.test(s),'HEX_REQUIRED');return Uint8Array.from(s.match(/../g)?.map(v=>parseInt(v,16))||[]);}
/** Unicode UTF8 bridge. Does not claim compressed payload or native CGX binary. */
export function encodeBinaryTransport(obj){const b=new TextEncoder().encode(JSON.stringify(obj));must(b.length<=1048576,'TRANSPORT_LIMIT');const out=new Uint8Array(b.length+8);out.set([84,73,82,49,55,51,0,2]);out.set(b,8);return out;}
export function decodeBinaryTransport(data){must(data instanceof Uint8Array&&data.length>=8&&data.length<=1048584,'TRANSPORT_BOUND');const h=[84,73,82,49,55,51,0,2];must(h.every((v,i)=>v===data[i]),'BINARY_MAGIC');let value;try{value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(data.slice(8)));}catch{throw new TIRError('BINARY_JSON_INVALID');}return value;}
function safeRef(v){return typeof v==='string'&&v.length<=150&&/^[A-Za-z0-9][A-Za-z0-9:./_#-]*$/.test(v);}
/** Values at two scales refer to the same object; fine details cannot be invented by zoom. */
export function makeCapsule(d,{path=[1],shape=1,label='',object_ref='local:review',frame='local',unit='m',magnitude=1,
 coarse=null,fine=null,relations=[],state={basis:'local:orientation',trit:0,validity:'UNRESOLVED'},source_ref='local:review',kind='object'}={}){
 validateDictionary(d);const role=normaliseRole(shape);
 must(INTENTS.includes(kind),'NODE_KIND');must(Array.isArray(path)&&path.length>=1&&path.length<=8,'PATH_DEPTH');path.forEach(roleIndex);
 must(safeRef(object_ref)&&safeRef(source_ref)&&safeRef(state?.basis),'IDENTITY_SOURCE_REQUIRED');
 must(typeof label==='string'&&label.length<=140,'LABEL_LIMIT');must(typeof frame==='string'&&/^[A-Za-z][\w./-]{0,50}$/.test(frame),'FRAME_REQUIRED');
 must(typeof unit==='string'&&/^[A-Za-z][\w/-]{0,20}$/.test(unit),'UNITS_REQUIRED');
 must(typeof magnitude==='number'&&Number.isFinite(magnitude)&&magnitude>0,'SCALE_POSITIVE');
 must(STATES.has(state.trit)&&EVIDENCE.includes(state.validity),'STATE_AND_VALIDITY');
 const lens=(v)=>{if(v===null)return null;must(v&&Number.isInteger(v.level)&&v.level>=0&&v.level<=8&&['HYDRATED','REFERENCE_ONLY','UNRESOLVED','NOT_AUTHORISED'].includes(v.status),'SCALE_LENS');must(v.status!=='HYDRATED'||safeRef(v.source_ref),'HYDRATED_REQUIRES_SOURCE');return {level:v.level,status:v.status,source_ref:v.source_ref||null,value:v.value??null};};
 must(Array.isArray(relations)&&relations.length<=173,'RELATIONS_BOUND');
 for(const r of relations){must(safeRef(r.predicate)&&safeRef(r.target)&&EVIDENCE.includes(r.evidence),'RELATION_TYPE_EVIDENCE');}
 return {schema:TIR_SCHEMA,authority:'REVIEW_ONLY',object_ref,local_path:path,ordinal_address:encodePath(path),kind,shape_role:slotName(role),geometry_ref:d.roles[role-1].mesh_ref,
  geometry_evidence:d.roles[role-1].evidence,source_ref,frame,unit,magnitude,label,scale_lenses:{coarse:lens(coarse),fine:lens(fine)},relations:structuredClone(relations),state:{basis:state.basis,trit:state.trit,validity:state.validity},dictionary_source_sha256:d.source_sha256,
  native_admitted:false,execution_performed:false};
}
export function validateCapsule(d,c){validateDictionary(d);must(c?.schema===TIR_SCHEMA&&c.authority==='REVIEW_ONLY'&&c.native_admitted===false&&c.execution_performed===false,'CAPSULE_AUTHORITY');
 const check=makeCapsule(d,{path:c.local_path,shape:c.shape_role,label:c.label,object_ref:c.object_ref,frame:c.frame,unit:c.unit,magnitude:c.magnitude,coarse:c.scale_lenses?.coarse,fine:c.scale_lenses?.fine,relations:c.relations,state:c.state,source_ref:c.source_ref,kind:c.kind});
 // Rebuilding applies defaults for absent inputs; a received capsule must instead
 // carry every emitted field and bind its evidence label to the dictionary.
 must(Object.keys(check).every(k=>own(c,k)&&c[k]!==undefined),'CAPSULE_FIELD_MISSING');
 must(c.scale_lenses&&own(c.scale_lenses,'coarse')&&own(c.scale_lenses,'fine')&&c.scale_lenses.coarse!==undefined&&c.scale_lenses.fine!==undefined,'CAPSULE_SCALE_LENS_MISSING');
 must(c.ordinal_address===check.ordinal_address&&c.geometry_ref===check.geometry_ref&&c.geometry_evidence===check.geometry_evidence&&c.dictionary_source_sha256===check.dictionary_source_sha256,'CAPSULE_DICTIONARY_HASH_MISMATCH');return true;
}
export function projectLenses(d,c){validateCapsule(d,c);const r=d.roles[normaliseRole(c.shape_role)-1];return {
 human:{object:c.label||c.object_ref,shape:r.name,geometry_role:c.shape_role,category:r.family,scale:`${c.magnitude} ${c.unit}`,frame:c.frame,available_detail:c.scale_lenses.fine?.status||'NO_DATA',coarse:c.scale_lenses.coarse?.status||'NO_DATA',source_status:r.evidence,voice_status:c.state.validity,meaning:c.state.trit===1?'positive along declared basis':c.state.trit===-1?'negative along declared basis':'neutral along declared basis',relations:c.relations},
 machine:{schema:c.schema,object_ref:c.object_ref,shape:c.shape_role,path:c.ordinal_address,mesh_ref:c.geometry_ref,states:[c.state.trit],source:c.source_ref,dictionary:c.dictionary_source_sha256},
 negative_space:{missing_fine:c.scale_lenses.fine===null||c.scale_lenses.fine.status!=='HYDRATED',not_a_physical_truth:true}
};}
/** Three analytic lanes do not pretend to be independent learned models. */
export function reconcileThreeVoices(voices){must(Array.isArray(voices)&&voices.length===3,'THREE_VOICES_REQUIRED');
 const by={};for(const e of voices){must(['intuitive','deliberative','assurance'].includes(e.voice)&&!own(by,e.voice),'VOICE_ID');must(STATES.has(e.trit)&&EVIDENCE.includes(e.validity)&&safeRef(e.source_ref),'VOICE_EVIDENCE');by[e.voice]={...e};}
 must(Object.keys(by).length===3,'THREE_VOICES_REQUIRED');const vs=Object.values(by),val=vs.map(x=>x.trit),s=new Set(val);
 const missing=vs.some(x=>x.validity!=='SUPPORTED');return {schema:'cgx.ternary.reconcile/0.1',voices:by,conflict:s.size>1,combined_state:!missing&&s.size===1?val[0]:null,epistemic:missing?'UNRESOLVED':s.size>1?'CONFLICT':'SUPPORTED',automatic_promotion:false};
}
export function resolveWords(d,query,{limit=20}={}){validateDictionary(d);must(typeof query==='string'&&query.length<=120,'QUERY_BOUNDS');must(Number.isInteger(limit)&&limit>=1&&limit<=173,'RESULT_LIMIT');const q=query.trim().toLocaleLowerCase();if(!q)return [];return d.roles.map(e=>({role:e.role,name:e.name,family:e.family,terms:e.lexical_tokens||[],evidence:e.evidence,mesh_ref:e.mesh_ref,score:(e.name.toLocaleLowerCase().includes(q)?10:0)+(e.family.toLocaleLowerCase().includes(q)?3:0)+(e.lexical_tokens?.some(t=>t.includes(q))?2:0)})).filter(x=>x.score).sort((a,b)=>b.score-a.score||a.role.localeCompare(b.role)).slice(0,limit);}

/** Three independently typed state lines, 173 positions each = 3 × 35 = 105 bytes.
 * The carrier omits evidence masks, dictionary hash, units, sources and timestamps. */
export const THREE_LINES=Object.freeze(['intuitive','deliberative','assurance']);
export function packThreeLines(lines){
 must(lines&&typeof lines==='object'&&!Array.isArray(lines)&&Object.keys(lines).length===3&&THREE_LINES.every(k=>own(lines,k)),'EXACTLY_THREE_NAMED_LINES');
 const bytes=new Uint8Array(105);THREE_LINES.forEach((name,i)=>bytes.set(pack173(lines[name]),35*i));return bytes;
}
export function unpackThreeLines(bytes){must(bytes instanceof Uint8Array&&bytes.length===105,'THREE_LINES_105_BYTES');
 const out={};for(let i=0;i<3;i++)out[THREE_LINES[i]]=unpack173(bytes.slice(i*35,(i+1)*35));return out;
}
/** Never collapse opposed lanes into 0: 0 is neutral; disagreement is a separate flag. */
export function examineShapeTriad(lines,role){const i=normaliseRole(role)-1;
 must(lines&&THREE_LINES.every(k=>Array.isArray(lines[k])&&lines[k].length===173&&STATES.has(lines[k][i])),'UNQUALIFIED_TRIAD_FRAME');
 const states=THREE_LINES.map(k=>lines[k][i]);const conflict=new Set(states).size>1;
 return {schema:'cgx.tir173.triad_shape_state/0.2',role:slotName(i+1),lines:Object.fromEntries(THREE_LINES.map((k,j)=>[k,states[j]])),conflict,
  combined_state:conflict?null:states[0],epistemic:'EVIDENCE_MASK_NOT_INCLUDED',automatic_execution:false};
}