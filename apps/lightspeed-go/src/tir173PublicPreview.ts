/** Reusable public-safe GUIOS object lens; shares the existing CGX TIR/173 core. */
import { makeCapsule,pack173,packThreeLines,hex,reconcileThreeVoices,validateDictionary, type ShapeDictionary,type Trit } from '../../../cgx/runtime/tir173/tir173_core.mjs';
import { projectSynchronized } from '../../../cgx/runtime/tir173/tir173_composition.mjs';
import { projectGuiosContext } from '../../../cgx/runtime/tir173/tir173_context.mjs';
import { bindTirIntentToExistingPlans } from '../../../cgx/runtime/tir173/tir173_intent_binding.mjs';
import { reviewTirComponentArchetype } from '../../../cgx/runtime/tir173/tir173_archetype_evidence.mjs';
import { planExistingLoadTIR } from '../../../cgx/runtime/tir173/tir173_load_bridge.mjs';
import { listAtlasInteractions, planAtlasInteraction } from '../../../cgx/runtime/tir173/tir173_interaction.mjs';
import { reviewLocalNeoBatch } from '../../../cgx/runtime/tir173/tir173_neo_review_import.mjs';
import componentAtlasRaw from '../../../cgx/component_atlas/component_interaction_map_v0_1.json?raw';
const componentAtlas=JSON.parse(componentAtlasRaw);
import geometryAtlasRaw from '../../../cgx/component_atlas/component_geometry_atlas_v0_1.json?raw';
import physicalProofRaw from '../../../cgx/component_atlas/component_physical_proof_ladder_v0_1.json?raw';
import instanceContractRaw from '../../../cgx/component_atlas/component_instance_build_packet_contract_v0_1.json?raw';
const geometryAtlas=JSON.parse(geometryAtlasRaw);
const physicalProof=JSON.parse(physicalProofRaw);
const instanceContract=JSON.parse(instanceContractRaw);
import neoProjection from '../../../docs/agent-ingestion/local-agent-homes/Z+2_Neo/pilots/raphael_temporal/geometry_language/T173_NEO_ROLE_PROJECTION.review.json';

type PreviewRoot=HTMLElement;
const el=<T extends HTMLElement=HTMLElement>(root:HTMLElement,id:string):T=>{
 const e=root.querySelector<T>(`#${id}`);if(!e)throw new Error(`TIR/173 mounting element ${id} missing`);return e;
};
async function sourceDigest(value:unknown):Promise<string>{
 const serialized=typeof value==='string'?value:JSON.stringify(value), bytes=new TextEncoder().encode(serialized);
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
 const d=await publicTirDictionary();
 const [atlasDigest,geometryDigest,proofDigest,packetDigest]=await Promise.all([
  sourceDigest(componentAtlasRaw),sourceDigest(geometryAtlasRaw),
  sourceDigest(physicalProofRaw),sourceDigest(instanceContractRaw)]);
 let active=1;
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
 <div class="form-grid"><label class="field"><span>Existing CGX interaction rule · review only</span><select id="tir-interaction-rule"></select></label></div>
 <div class="route-preview" id="tir-interaction-review" aria-live="polite"></div>
 <div class="form-grid"><label class="field"><span>Existing CGX component archetype · optional evidence comparison</span><select id="tir-archetype"></select></label></div>
 <div class="route-preview" id="tir-archetype-review" aria-live="polite"></div>
 <div class="form-grid"><label class="field"><span>T173 shorthand · exact review command</span>
 <input type="text" id="tir-intent-command" value="SELECT T173:001" maxlength="240" spellcheck="false" autocomplete="off" aria-describedby="tir-intent-help"/></label></div>
 <p class="muted" id="tir-intent-help">Exact syntax: SELECT T173:001 or another registered operation. Unknown, multi-role, privileged and incomplete natural-language instructions abstain; no commands execute.</p>
 <div class="route-preview" id="tir-intent-human" aria-live="polite"></div>
 <div class="form-grid"><label class="field"><span>Neo / Achilles local triadic review · optional user-selected JSON</span>
 <input id="tir-neo-file" type="file" accept=".json,application/json" aria-describedby="tir-neo-help"/></label>
 <label class="field"><span>Local review case</span><select id="tir-neo-case" disabled><option value="">Select a local packet first</option></select></label></div>
 <p class="muted" id="tir-neo-help">Local review-only import: browser reads a user-selected file in memory, never automatically uploads, persists or executes it. This display is separate from the selected public shape; source SHA-256 is not proof of model weight validity.</p>
 <div class="route-preview" id="tir-neo-human" aria-live="polite">No local Neo review packet selected.</div>
 <pre id="tir-neo-machine" style="white-space:pre-wrap;overflow-wrap:anywhere;max-height:240px;overflow:auto"></pre>
 <p class="muted">The shape remains identical across lenses. The three state lines can disagree without being collapsed to neutral. LOAD and LOAD.Lite share the existing resolver; this surface produces a plan only, never hydration or admission.</p>
 <div class="route-preview" id="tir-context" aria-live="polite"></div>
 <div class="route-preview" id="tir-display"></div><div class="actions"><button type="button" id="tir-export">Export synchronized review context</button></div>
 <pre id="tir-machine" style="white-space:pre-wrap;overflow-wrap:anywhere;max-height:300px;overflow:auto;border:1px solid #33435c;border-radius:8px;padding:12px"></pre>
 <p class="boundary">No public source access, minting, model execution, signed DBR, or canonical mutation is performed.</p></article>`;
 const choose=el<HTMLSelectElement>(root,'tir-role'),other=el<HTMLSelectElement>(root,'tir-second'),states=el<HTMLSelectElement>(root,'tir-state');
 const environment=el<HTMLSelectElement>(root,'tir-environment'),spatial=el<HTMLSelectElement>(root,'tir-spatial'),perspective=el<HTMLSelectElement>(root,'tir-perspective'),scale=el<HTMLSelectElement>(root,'tir-scale');
 const intuitive=el<HTMLSelectElement>(root,'tir-intuitive'),deliberative=el<HTMLSelectElement>(root,'tir-deliberative'),hydration=el<HTMLSelectElement>(root,'tir-hydration');
 const ruleSelect=el<HTMLSelectElement>(root,'tir-interaction-rule');
 const archetypeSelect=el<HTMLSelectElement>(root,'tir-archetype');
 const intentInput=el<HTMLInputElement>(root,'tir-intent-command');
 const neoFile=el<HTMLInputElement>(root,'tir-neo-file');
 const neoCase=el<HTMLSelectElement>(root,'tir-neo-case');
 for(const rule of listAtlasInteractions(componentAtlas,{limit:75})){const option=document.createElement('option');option.value=rule.id;option.textContent=`${rule.id} • ${rule.source_family} → ${rule.target_family} (${rule.interaction})`;ruleSelect.append(option);}
 const none=document.createElement('option');none.value='';none.textContent='No archetype assigned — do not infer material';archetypeSelect.append(none);
 for(const item of geometryAtlas.records){const option=document.createElement('option');option.value=item.ID;option.textContent=`${item.ID} · ${item.Family} · ${item['Component Archetype']}`;archetypeSelect.append(option);}
 const opts=d.roles.map((s,i)=>`<option value="${i+1}">${s.role} • ${s.name}</option>`).join('');
 choose.innerHTML=opts;other.innerHTML=opts;other.value='2';let last=null as {capsule:ReturnType<typeof makeCapsule>;lens:ReturnType<typeof projectGuiosContext>;triad:ReturnType<typeof reconcileThreeVoices>;load_review_plan:ReturnType<typeof planExistingLoadTIR>;physical_interaction_review:ReturnType<typeof planAtlasInteraction>;intent_binding_review:ReturnType<typeof bindTirIntentToExistingPlans>;archetype_review:ReturnType<typeof reviewTirComponentArchetype>}|null;
 let localReview:ReturnType<typeof reviewLocalNeoBatch>|null=null;
 let localFileSha:string|null=null;
 const showLocalReview=():void=>{
  const human=el(root,'tir-neo-human'),machine=el(root,'tir-neo-machine');
  const caseIndex=Number(neoCase.value);
  const selected=localReview?.items[caseIndex];
  if(!selected){human.textContent='No valid local Neo review case selected.';machine.textContent='';return;}
  human.textContent=`${selected.human_summary} | Guard: ${selected.status} | Learned suggestion: ${selected.model_candidate||'none'} | Assurance: ${selected.assurance} | No native effects.`;
  machine.textContent=JSON.stringify({
   local_selected_file_sha256:localFileSha,
   packet_import_status:'UNTRUSTED_LOCAL_PREVIEW_ONLY',
   checkpoint_sha256_claim:localReview?.checkpoint_sha256_claim,
   model_weights_verified_by_browser:false,
   imported_case:selected,
   native_admitted:false,execution:false,public_publish_authorized:false
  },null,2);
 };
 neoCase.addEventListener('change',showLocalReview);
 neoFile.addEventListener('change',async()=>{
  try{
   const file=neoFile.files?.[0];
   if(!file){localReview=null;localFileSha=null;neoCase.disabled=true;showLocalReview();return;}
   if(file.size>200_000)throw new Error('Local review packet exceeds the 200 kB inspection limit');
   const raw=await file.text();
   const validated=reviewLocalNeoBatch(JSON.parse(raw));
   const hash=await sourceDigest(raw);
   localReview=validated;localFileSha=hash;
   neoCase.replaceChildren();
   for(const item of validated.items){const option=document.createElement('option');
    option.value=String(item.index-1);option.textContent=`${item.index} · ${item.status}`;neoCase.append(option);}
   neoCase.disabled=false;neoCase.value='0';showLocalReview();
  }catch(error){
   localReview=null;localFileSha=null;neoCase.disabled=true;neoCase.replaceChildren();
   el(root,'tir-neo-human').textContent='Local review packet refused: '+(error instanceof Error?error.message:'invalid file');
   el(root,'tir-neo-machine').textContent='';
  }
 });
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

   const line=(v:Trit):Trit[]=>{const st=Array(173).fill(0) as Trit[];st[active-1]=v;return st;};
   const st=line(value);
   const packedTriad=packThreeLines({
    intuitive:line(Number(intuitive.value) as Trit),deliberative:line(Number(deliberative.value) as Trit),assurance:st});
   const h=hydration.value as 'H0'|'H1'|'H2'|'H3';
   const loadPlan:Parameters<typeof planExistingLoadTIR>[2]={schema:'UNISPACE-CGX-LOAD-LENS-PLAN/0.1',
    state:'PLAN_ONLY_NOT_HYDRATED',alias:'LOAD.cgx',parent_filespace:'Cognigrex.cgx',
    object_id:cap.object_ref,native_admitted:false,hydrated:false,execution_performed:false,
    public_publish_authorized:false,canonical_mutation:false,host_context_readback_authenticated:false,
    source_rights_independently_verified:false,client_scope_independently_authenticated:false,
    requested_hydration:h,planned_hydration:h};
   const load=planExistingLoadTIR(d,cap,loadPlan);
   const physical=planAtlasInteraction(componentAtlas,cap,lens.context,{rule_id:ruleSelect.value,source_sha256:atlasDigest});
   const intentBinding=bindTirIntentToExistingPlans(d,cap,lens.context,{command:intentInput.value,
    loadPlan,atlas:componentAtlas,atlasSelection:{rule_id:ruleSelect.value,source_sha256:atlasDigest}});
   const archetypeReview=reviewTirComponentArchetype(d,cap,geometryAtlas,physicalProof,instanceContract,{
    archetype_id:archetypeSelect.value||null,
    source_claims:{geometry_atlas_sha256:geometryDigest,proof_ladder_sha256:proofDigest,
     instance_contract_sha256:packetDigest}});
   last={capsule:cap,lens,triad:voices,load_review_plan:load,physical_interaction_review:physical,intent_binding_review:intentBinding,archetype_review:archetypeReview};
   el(root,'tir-display').textContent=`Selected ${cap.shape_role} | reference mesh ${String(cap.geometry_ref)} | binary state ${hex(pack173(st)).slice(0,18)}… | three lanes ${packedTriad.length}B | ${voices.conflict?'VOICE CONFLICT':'voices compatible'} | ${voices.epistemic} | LOAD ${h} PLAN ONLY`;
   el(root,'tir-intent-human').textContent=`${intentBinding.human.summary} | ${intentBinding.human.interpretation} | Requires: ${intentBinding.human.missing_inputs.join(', ')||'independent evidence and authority'} | ${intentBinding.machine.status}`;
   el(root,'tir-archetype-review').textContent=`${archetypeReview.human.summary} | ${archetypeReview.human.interpretation} | ${archetypeReview.human.physical_state} | ${archetypeReview.human.proof_stages}`;
   el(root,'tir-interaction-review').textContent=`${physical.human.title} | ${physical.human.summary} | ${physical.human.interpretation} | Requires: ${physical.required_variables.geometry.concat(physical.required_variables.state).join(', ')||'defined source parameters'} | Test: ${physical.human.next_test} | ${physical.human.boundary}`;
   el(root,'tir-context').textContent=`${lens.human.description} Apparent scale ${lens.human.view_scale}. Identity unchanged; relation not established. Void/fine detail remain explicit.`;
   el(root,'tir-machine').textContent=JSON.stringify({capsule:cap,environment_lens:lens.context,human:lens.human,machine:p.machine,triad:voices,load_review_plan:load,physical_interaction_review:physical,intent_binding_review:intentBinding,archetype_review:archetypeReview,negative_space:p.negative_space,binary_transport:p.transport},null,2);
  }catch(error){last=null;el(root,'tir-display').textContent=error instanceof Error?error.message:'Invalid TIR input';el(root,'tir-interaction-review').textContent='Interaction plan unavailable';el(root,'tir-archetype-review').textContent='Component archetype review unavailable';el(root,'tir-intent-human').textContent='Shorthand review unavailable';el(root,'tir-machine').textContent='';}
 };
 for(const x of [other,states,environment,spatial,perspective,scale,intuitive,deliberative,hydration,ruleSelect,archetypeSelect])x.addEventListener('change',display);
 choose.addEventListener('change',()=>{intentInput.value='SELECT T173:'+choose.value.padStart(3,'0');display();});
 intentInput.addEventListener('input',display);
 el(root,'tir-export').addEventListener('click',()=>{if(!last)return;const blob=new Blob([JSON.stringify(last,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='tir173-guios-review-context.json';a.click();URL.revokeObjectURL(url);});
 display();
}