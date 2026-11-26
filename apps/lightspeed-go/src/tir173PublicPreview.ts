/** Reusable public-safe GUIOS object lens; shares the existing CGX TIR/173 core. */
import { makeCapsule,pack173,packThreeLines,hex,reconcileThreeVoices,validateDictionary, type ShapeDictionary,type Trit } from '../../../cgx/runtime/tir173/tir173_core.mjs';
import { projectSynchronized } from '../../../cgx/runtime/tir173/tir173_composition.mjs';
import { projectGuiosContext } from '../../../cgx/runtime/tir173/tir173_context.mjs';
import { planExistingLoadTIR } from '../../../cgx/runtime/tir173/tir173_load_bridge.mjs';
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
 root.innerHTML=`<article class="panel"><p class="eyebrow">Cognigrex / Raphael shape language</p><h2>TIR/173 — contextual geometry component</h2>
 <p class="muted">Public metadata-only review. The existing Raphael catalogue has 173 named research roles and 157 numeric payload references. Private coordinates and source meanings are never loaded on this public surface.</p>
 <div class="form-grid"><label class="field"><span>Geometry role</span><select id="tir-role"></select></label>
 <label class="field"><span>Second shape</span><select id="tir-second"></select></label>
 <label class="field"><span>Assurance line</span><select id="tir-state"><option value="-1">−1</option><option value="0" selected>0</option><option value="1">+1</option></select></label></div>
 <div class="form-grid"><label class="field"><span>Intuitive line</span><select id="tir-intuitive"><option value="-1">−1</option><option value="0" selected>0</option><option value="1">+1</option></select></label>
 <label class="field"><span>Deliberative line</span><select id="tir-deliberative"><option value="-1">−1</option><option value="0" selected>0</option><option value="1">+1</option></select></label>
 <label class="field"><span>LOAD planning depth</span><select id="tir-hydration"><option value="H0">H0 · reference</option><option value="H1">H1 · metadata</option><option value="H2">H2 · selected content</option><option value="H3">H3 · requested detail</option></select></label></div>
 <div class="form-grid">
   <label class="field"><span>Environment</span><select id="tir-environment"><option value="digital">Digital</option><option value="physical">Physical</option><option value="simulated">Simulated</option><option value="hybrid">Hybrid</option></select></label>
   <label class="field"><span>Spatial operation</span><select id="tir-spatial"><option value="in">In</option><option value="on">On</option><option value="through">Through</option><option value="across">Across</option><option value="around">Around</option><option value="between">Between</option></select></label>
   <label class="field"><span>Observer</span><select id="tir-perspective"><option value="intersection">Intersection</option><option value="top_down">Top-down</option><option value="bottom_up">Bottom-up</option><option value="side">Side</option><option value="void">Negative space</option></select></label>
 </div>
 <div class="form-grid"><label class="field"><span>View scale (ratio)</span><select id="tir-scale"><option value="0.001">0.001× micro</option><option value="1" selected>1× native</option><option value="1000">1000× macro</option></select></label></div>
 <p class="muted">The shape remains identical across lenses. The three state lines can disagree without being collapsed to neutral. LOAD and LOAD.Lite share the existing resolver; this surface produces a plan only, never hydration or admission.</p>
 <div class="route-preview" id="tir-context" aria-live="polite"></div>
 <div class="route-preview" id="tir-display"></div><div class="actions"><button type="button" id="tir-export">Export typed capsule</button></div>
 <pre id="tir-machine" style="white-space:pre-wrap;overflow-wrap:anywhere;max-height:300px;overflow:auto;border:1px solid #33435c;border-radius:8px;padding:12px"></pre>
 <p class="boundary">No public source access, minting, model execution, signed DBR, or canonical mutation is performed.</p></article>`;
 const choose=el<HTMLSelectElement>(root,'tir-role'),other=el<HTMLSelectElement>(root,'tir-second'),states=el<HTMLSelectElement>(root,'tir-state');
 const environment=el<HTMLSelectElement>(root,'tir-environment'),spatial=el<HTMLSelectElement>(root,'tir-spatial'),perspective=el<HTMLSelectElement>(root,'tir-perspective'),scale=el<HTMLSelectElement>(root,'tir-scale');
 const intuitive=el<HTMLSelectElement>(root,'tir-intuitive'),deliberative=el<HTMLSelectElement>(root,'tir-deliberative'),hydration=el<HTMLSelectElement>(root,'tir-hydration');
 const opts=d.roles.map((s,i)=>`<option value="${i+1}">${s.role} • ${s.name}</option>`).join('');
 choose.innerHTML=opts;other.innerHTML=opts;other.value='2';let last=null as {capsule:ReturnType<typeof makeCapsule>;lens:ReturnType<typeof projectGuiosContext>}|null;
 const display=():void=>{
  try{
   active=Number(choose.value);const b=Number(other.value),value=Number(states.value) as Trit;
   const voices=reconcileThreeVoices([
    {voice:'intuitive',trit:Number(intuitive.value) as Trit,validity:'UNRESOLVED',source_ref:'review:neo:public'},
    {voice:'deliberative',trit:Number(deliberative.value) as Trit,validity:'UNRESOLVED',source_ref:'review:neo:public'},
    {voice:'assurance',trit:value,validity:'UNRESOLVED',source_ref:'review:neo:public'}]);
   const cap=makeCapsule(d,{shape:active,path:[1,active],label:d.roles[active-1].name,
    object_ref:'review:public:shape',source_ref:'review:neo:public',
    coarse:{level:0,status:'REFERENCE_ONLY',source_ref:'review:neo:public',value:'shape role'},
    fine:{level:3,status:'UNRESOLVED'},state:{basis:'review:entered-symbolic',trit:value,validity:'UNRESOLVED'},
    relations:[{predicate:'interacts_with',target:`review:public:shape:${b}`,evidence:'UNRESOLVED'}]});
   const p=projectSynchronized(d,cap);
   const lens=projectGuiosContext(d,cap,{environment:environment.value as 'digital'|'physical'|'simulated'|'hybrid',
    spatial:spatial.value as 'in'|'on'|'through'|'across'|'around'|'between',
    perspective:perspective.value as 'top_down'|'bottom_up'|'intersection'|'side'|'void',
    scale_ratio:Number(scale.value),environment_ref:'review:declared-environment',source_ref:'review:neo:public'});
   last={capsule:cap,lens};
   const line=(v:Trit):Trit[]=>{const st=Array(173).fill(0) as Trit[];st[active-1]=v;return st;};
   const st=line(value);
   const packedTriad=packThreeLines({
    intuitive:line(Number(intuitive.value) as Trit),deliberative:line(Number(deliberative.value) as Trit),assurance:st});
   const h=hydration.value as 'H0'|'H1'|'H2'|'H3';
   const load=planExistingLoadTIR(d,cap,{schema:'UNISPACE-CGX-LOAD-LENS-PLAN/0.1',
    state:'PLAN_ONLY_NOT_HYDRATED',alias:'LOAD.cgx',parent_filespace:'Cognigrex.cgx',
    object_id:cap.object_ref,native_admitted:false,hydrated:false,execution_performed:false,
    public_publish_authorized:false,canonical_mutation:false,host_context_readback_authenticated:false,
    source_rights_independently_verified:false,client_scope_independently_authenticated:false,
    requested_hydration:h,planned_hydration:h});
   el(root,'tir-display').textContent=`Selected ${cap.shape_role} | reference mesh ${String(cap.geometry_ref)} | binary state ${hex(pack173(st)).slice(0,18)}… | three lanes ${packedTriad.length}B | ${voices.conflict?'VOICE CONFLICT':'voices compatible'} | ${voices.epistemic} | LOAD ${h} PLAN ONLY`;
   el(root,'tir-context').textContent=`${lens.human.description} Apparent scale ${lens.human.view_scale}. Identity unchanged; relation not established. Void/fine detail remain explicit.`;
   el(root,'tir-machine').textContent=JSON.stringify({capsule:cap,environment_lens:lens.context,human:lens.human,machine:p.machine,triad:voices,load_review_plan:load,negative_space:p.negative_space,binary_transport:p.transport},null,2);
  }catch(error){el(root,'tir-display').textContent=error instanceof Error?error.message:'Invalid TIR input';}
 };
 for(const x of [choose,other,states,environment,spatial,perspective,scale,intuitive,deliberative,hydration])x.addEventListener('change',display);
 el(root,'tir-export').addEventListener('click',()=>{if(!last)return;const blob=new Blob([JSON.stringify(last,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='tir173-guios-review-context.json';a.click();URL.revokeObjectURL(url);});
 display();
}