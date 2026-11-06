import {importLoadIndex,buildBatchDraft,restoreBatchDraft,DRAFT_SCHEMA,LIMIT} from './cgxLoadBatchDraft.mjs';
/** Local file interaction inside Objects. Never uploads or contacts a provider. */
export function mountLoadBatchReview(root){
 if(!root?.ownerDocument||typeof root.replaceChildren!=='function')return {state:'HOLD'};
 const doc=root.ownerDocument;
 const state={index:null,selected:new Set(),query:'',page:0,size:25,draft:null,detail:null,busy:false,
  message:'Choose your existing private LOAD index to begin. Nothing is uploaded.'};
 let disposed=false,generation=0,downloadUrl=null;
 const el=(tag,text='')=>{const e=doc.createElement(tag);e.textContent=text;return e;};
 const button=(text,action)=>{const e=el('button',text);e.type='button';e.setAttribute('data-load-action',action);return e;};
 const renderList=()=>{
  const list=root.querySelector('[data-load-list]');if(!list||!state.index)return;
  list.replaceChildren();
  const found=state.index.records.filter(r=>(r.name+' '+r.review_ref+' '+r.routes.join(' ')).toLowerCase().includes(state.query.toLowerCase()));
  const maxPage=Math.max(0,Math.ceil(found.length/25)-1);state.page=Math.min(state.page,maxPage);
  list.append(el('p',found.length+' matches · page '+(state.page+1)+' of '+(maxPage+1)));
  for(const r of found.slice(state.page*25,state.page*25+25)){
   const row=el('div');const label=el('label');const box=el('input');box.type='checkbox';box.checked=state.selected.has(r.review_ref);
   box.setAttribute('data-load-ref',r.review_ref);box.setAttribute('aria-label','Select '+r.name);
   label.append(box,doc.createTextNode(r.name));row.append(label);
   const inspect=button('Inspect source: '+r.name,'inspect');inspect.setAttribute('data-load-inspect',r.review_ref);
   row.append(inspect);list.append(row);
  }
  const prev=button('Previous sources','previous');prev.disabled=state.page===0;
  const next=button('Next sources','next');next.disabled=state.page===maxPage;list.append(prev,next);
 };
 const render=()=>{
  if(disposed)return;
  root.replaceChildren();const panel=el('article');panel.className='panel';
  panel.setAttribute('data-load-batch','LOCAL_UNSIGNED_REVIEW');
  panel.append(el('p','FileSpace / LOAD preparation'),el('h2','Prepare LOAD launch batches'));
  panel.append(el('p','Import a local index, inspect source references, select a batch and save a draft. Source rights and native admission are reviewed separately.'));
  const label=el('label','LOAD index or saved batch draft ');const file=el('input');file.type='file';file.accept='.json,application/json';
  file.setAttribute('aria-label','LOAD index or saved batch draft');file.setAttribute('data-load-import','true');file.disabled=state.busy;label.append(file);panel.append(label);
  const paste=el('details');paste.append(el('summary','Paste local JSON instead'));
  const area=el('textarea');area.rows=4;area.setAttribute('aria-label','Local LOAD index or draft JSON');area.setAttribute('data-load-paste','true');
  paste.append(area,button('Load pasted JSON','paste'));panel.append(paste);
  const status=el('p',state.message);status.setAttribute('role','status');status.setAttribute('data-load-status','true');panel.append(status);
  if(state.index){
   panel.append(el('p',state.index.records.length+' imported references · '+state.selected.size+' selected · 0 mint-ready records'));
   panel.append(el('p','Imported file SHA-256: '+state.index.raw_index_sha256));
   const search=el('input');search.type='search';search.value=state.query;search.setAttribute('aria-label','Search LOAD sources');search.setAttribute('data-load-search','true');panel.append(search);
   panel.append(button('Select all LOAD references','all'),button('Clear source selection','clear'));
   const sizeLabel=el('label','Batch size ');const size=el('select');size.setAttribute('aria-label','Batch size');size.setAttribute('data-load-size','true');
   for(const n of [10,25,50,100]){const opt=el('option',String(n));opt.value=String(n);opt.selected=state.size===n;size.append(opt);}sizeLabel.append(size);panel.append(sizeLabel);
   const list=el('div');list.setAttribute('data-load-list','true');list.setAttribute('style','max-height:360px;overflow:auto;overflow-wrap:anywhere');panel.append(list);
   if(state.detail){const details=el('pre',JSON.stringify(state.detail,null,2));details.setAttribute('aria-label','Selected source metadata');details.setAttribute('style','white-space:pre-wrap;overflow-wrap:anywhere');panel.append(details);}
   const prepare=button('Prepare unsigned LOAD batch','prepare');prepare.disabled=state.busy||state.selected.size===0;panel.append(prepare);
  }
  if(state.draft){
   panel.append(el('h3','Unsigned batch prepared'));
   panel.append(el('p',state.draft.summary.selected_records+' references · '+state.draft.summary.batches+' sequential batches · '+state.draft.summary.source_digest_present+' source digests present'));
   panel.append(el('p','Plan SHA-256: '+state.draft.plan_sha256));
   panel.append(button('Export unsigned batch draft','export'));
  }
  panel.append(el('p','Chain, contract, issuer and signatures are unset. No signing, broadcast, automatic launch execution or source-body hydration.'));
  root.append(panel);renderList();
 };
 const acceptBytes=async bytes=>{
  if(bytes.length>LIMIT)throw new Error('INDEX_SIZE_LIMIT');
  const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);const parsed=JSON.parse(text);
  const restored=parsed.schema===DRAFT_SCHEMA?await restoreBatchDraft(text):{index:await importLoadIndex(bytes),draft:null};
  if(disposed)return;
  state.index=restored.index;state.draft=restored.draft;state.size=restored.draft?.batch_size??25;
  state.selected=new Set(restored.draft?.selected_refs??[]);state.detail=null;state.query='';state.page=0;
  state.message=restored.draft?'Saved draft verified and restored; signing remains disabled.':'Local LOAD index imported. Review and select references.';
 };
 const change=async event=>{
  const target=event.target;if(!root.contains(target)||state.busy)return;
  try{
   if(target.hasAttribute('data-load-import')){
    const file=target.files?.[0];if(!file)return;
    if(file.size>LIMIT)throw new Error('INDEX_SIZE_LIMIT');
    state.busy=true;state.message='Reading local file…';const run=++generation;render();
    const bytes=new Uint8Array(await file.arrayBuffer());
    if(disposed||run!==generation)return;
    await acceptBytes(bytes);
   }else if(target.hasAttribute('data-load-ref')){
    const ref=target.getAttribute('data-load-ref');if(!state.index?.records.some(r=>r.review_ref===ref))return;
    target.checked?state.selected.add(ref):state.selected.delete(ref);state.draft=null;
   }else if(target.hasAttribute('data-load-size')){state.size=Number(target.value);state.draft=null;}
  }catch(error){state.message='Import held: '+error.message;state.draft=null;}
  finally{state.busy=false;render();}
 };
 const input=event=>{if(event.target.hasAttribute('data-load-search')){state.query=event.target.value;state.page=0;renderList();}};
 const click=async event=>{
  const b=event.target.closest?.('button');if(!b||!root.contains(b)||state.busy)return;
  const action=b.getAttribute('data-load-action');if(!action)return;
  try{
   if(action==='paste'){
    const text=root.querySelector('[data-load-paste]').value;
    state.busy=true;state.message='Validating pasted JSON locally…';render();
    await acceptBytes(new TextEncoder().encode(text));
   }
   else if(action==='all'){state.selected=new Set(state.index.records.map(r=>r.review_ref));state.draft=null;}
   else if(action==='clear'){state.selected.clear();state.draft=null;}
   else if(action==='inspect')state.detail=state.index.records.find(r=>r.review_ref===b.getAttribute('data-load-inspect'));
   else if(action==='previous'){state.page--;renderList();return;}
   else if(action==='next'){state.page++;renderList();return;}
   else if(action==='prepare'){
    state.busy=true;state.message='Hashing the selected references locally…';render();
    state.draft=await buildBatchDraft(state.index,{selectedRefs:[...state.selected],batchSize:state.size});
    state.message='Unsigned metadata batch prepared. Native and chain readiness remain held.';
   }else if(action==='export'&&state.draft){
    if(downloadUrl)URL.revokeObjectURL(downloadUrl);
    downloadUrl=URL.createObjectURL(new Blob([JSON.stringify(state.draft,null,2)+'\n'],{type:'application/json'}));
    const a=el('a','Save LOAD batch draft');a.href=downloadUrl;a.download='LOAD_unsigned_batch_'+state.draft.plan_sha256.slice(0,16)+'.json';
    root.append(a);a.click();a.remove();
    state.message='Draft download requested. Re-import the saved file to verify its exact plan.';
   }
  }catch(error){state.message='Preparation held: '+error.message;state.draft=null;}
  finally{state.busy=false;render();}
 };
 root.addEventListener('change',change);root.addEventListener('input',input);root.addEventListener('click',click);render();
 return {state:'LOCAL_UNSIGNED_REVIEW',dispose:()=>{disposed=true;generation++;if(downloadUrl)URL.revokeObjectURL(downloadUrl);root.removeEventListener('change',change);root.removeEventListener('input',input);root.removeEventListener('click',click);}};
}
