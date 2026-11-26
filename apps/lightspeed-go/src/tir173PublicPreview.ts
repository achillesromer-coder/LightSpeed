/** Public-safe, read-only UniSpace tab: imports the shared CGX TIR/173 core. */
import { makeCapsule,pack173,packThreeLines,hex,reconcileThreeVoices,validateDictionary, type ShapeDictionary,type Trit } from '../../../cgx/runtime/tir173/tir173_core.mjs';
import { projectSynchronized } from '../../../cgx/runtime/tir173/tir173_composition.mjs';
import neoProjection from '../../../docs/agent-ingestion/local-agent-homes/Z+2_Neo/pilots/raphael_temporal/geometry_language/T173_NEO_ROLE_PROJECTION.review.json';

type PreviewRoot=HTMLElement;
const el=<T extends HTMLElement=HTMLElement>(root:HTMLElement,id:string):T=>{
 const e=root.querySelector<T>(`#${id}`);if(!e)throw new Error(`TIR/173 mounting element ${id} missing`);return e;
};
async function sourceDigest(value:unknown):Promise<string>{
 const serialized=JSON.stringify(value), bytes=new TextEncoder().encode(serialized);
 if(!crypto.subtle)throw new Error('Source digest unavailable in this browser context');
 const digest=await crypto.subtle.digest('SHA-256',bytes);
 return Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
}
export const publicTirDictionary=async():Promise<ShapeDictionary>=>{
 if(neoProjection.schema!=='cgx.neo.t173.reference-review/0.1'||neoProjection.slots.length!==173)throw new Error('Public geometry source mismatch');
 const digest=await sourceDigest(neoProjection);
 const roles=neoProjection.slots.map((s,i)=>({slot:i+1,role:`T173:${String(i+1).padStart(3,'0')}`,
    name:`Raphael research role ${String(i+1).padStart(3,'0')}`,family:s.class,mesh_ref:String(s.mesh_ref),evidence:s.qualifier,lexical_tokens:[s.class.toLowerCase()]}));
 const d:ShapeDictionary={schema:'cgx.t173.shape_dictionary/0.2',roles,source_sha256:digest,sentinel:null};validateDictionary(d);return d;
};
export async function mountTir173PublicPreview(root:PreviewRoot):Promise<void>{
 const d=await publicTirDictionary();let active=1;
 root.innerHTML=`<article class="panel"><p class="eyebrow">Cognigrex / Raphael shape language</p><h2>TIR/173 — shared computational alphabet</h2>
 <p class="muted">Public metadata-only review. The existing Raphael catalogue has 173 named research roles and 157 numeric payload references. Private coordinates and source meanings are never loaded on this public surface.</p>
 <div class="form-grid"><label class="field"><span>Geometry role</span><select id="tir-role"></select></label>
 <label class="field"><span>Second shape</span><select id="tir-second"></select></label>
 <label class="field"><span>Symbolic state</span><select id="tir-state"><option value="-1">−1</option><option value="0" selected>0</option><option value="1">+1</option></select></label></div>
 <p class="muted">Symbolic triad is not a deployed three-model intelligence. The fine-scale lens remains unresolved until existing LOAD / FileSpace permissioned hydration succeeds.</p>
 <div class="route-preview" id="tir-display"></div><div class="actions"><button type="button" id="tir-export">Export typed capsule</button></div>
 <pre id="tir-machine" style="white-space:pre-wrap;overflow-wrap:anywhere;max-height:300px;overflow:auto;border:1px solid #33435c;border-radius:8px;padding:12px"></pre>
 <p class="boundary">No public source access, minting, model execution, signed DBR, or canonical mutation is performed.</p></article>`;
 const choose=el<HTMLSelectElement>(root,'tir-role'),other=el<HTMLSelectElement>(root,'tir-second'),states=el<HTMLSelectElement>(root,'tir-state');
 const opts=d.roles.map((s,i)=>`<option value="${i+1}">${s.role} • ${s.name}</option>`).join('');
 choose.innerHTML=opts;other.innerHTML=opts;other.value='2';let last=null as ReturnType<typeof makeCapsule>|null;
 const display=():void=>{
  try{
   active=Number(choose.value);const b=Number(other.value),value=Number(states.value) as Trit;
   const cap=makeCapsule(d,{shape:active,path:[1,active],label:d.roles[active-1].name,
    object_ref:'review:public:shape',source_ref:'review:neo:public',
    coarse:{level:0,status:'REFERENCE_ONLY',source_ref:'review:neo:public',value:'shape role'},
    fine:{level:3,status:'UNRESOLVED'},state:{basis:'review:entered-symbolic',trit:value,validity:'UNRESOLVED'},
    relations:[{predicate:'interacts_with',target:`review:public:shape:${b}`,evidence:'UNRESOLVED'}]});
   last=cap;const p=projectSynchronized(d,cap);
   const triad=reconcileThreeVoices(['intuitive','deliberative','assurance'].map(voice=>({voice,trit:value,validity:'UNRESOLVED' as const,source_ref:'review:neo:public'})));
   const st=Array(173).fill(0) as Trit[];st[active-1]=value;const packedTriad=packThreeLines({intuitive:st,deliberative:st,assurance:st});
   el(root,'tir-display').textContent=`Selected ${cap.shape_role} | reference mesh ${String(cap.geometry_ref)} | binary state ${hex(pack173(st)).slice(0,18)}… | three lanes ${packedTriad.length}B | ${triad.epistemic} | source-qualified hydration HOLD`;
   el(root,'tir-machine').textContent=JSON.stringify({capsule:cap,projection:p.machine,negative_space:p.negative_space,binary_transport:p.transport},null,2);
  }catch(error){el(root,'tir-display').textContent=error instanceof Error?error.message:'Invalid TIR input';}
 };
 for(const x of [choose,other,states])x.addEventListener('change',display);
 el(root,'tir-export').addEventListener('click',()=>{if(!last)return;const blob=new Blob([JSON.stringify(last,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='tir173-review-capsule.json';a.click();URL.revokeObjectURL(url);});
 display();
}