import {emptyComposition,sourceAsset,addAsset,addLayer,updateLayer,moveLayer,parseCsv,exportComposition,restoreComposition,KINDS} from './cgxPressComposition.mjs';
import {planFirstSpacesReview} from './cgxFirstSpacesReviewModel.mjs';
import {restoreBatchDraft} from './cgxLoadBatchDraft.mjs';
import {resolveKnownFacets} from './cgxKnownFacets.mjs';
/** The Objects composition facet, not a second FileSpace, registry or execution shell. */
export function mountPressSurface(root){
 const doc=root.ownerDocument;let composition=emptyComposition(),selected=null,busy=false,stack='all',editing=false,pressedJson='',resolvedFacets=null,showSources=true,showInspector=true;
 const families=planFirstSpacesReview().nodes;
 const urls=new Map();let message='Drop local files to inspect and layer them. Save a draft before closing this page.';
 const el=(tag,text='',className='')=>{const e=doc.createElement(tag);e.textContent=text;e.className=className;return e;};
 const button=(text,fn)=>{const b=el('button',text);b.type='button';b.addEventListener('click',fn);return b;};
 const field=(title,input)=>{const label=el('label',title);label.append(input);return label;};
 const input=(label,value,fn,type='text')=>{const e=el('input');e.type=type;e.value=String(value);e.setAttribute('aria-label',label);e.addEventListener('input',()=>{editing=true;try{fn(type==='number'?Number(e.value):e.value);}finally{editing=false;}});e.addEventListener('change',()=>render());return e;};
 const run=async fn=>{const repaint=!editing;try{await fn();}catch(e){message=e.message;}if(repaint)render();};
 const update=patch=>run(()=>{composition=updateLayer(composition,selected,patch);});
 const pick=async files=>{
  if(busy)return;busy=true;render();let added=0,duplicates=0,held=0;
  try{for(const f of Array.from(files).slice(0,32)){
   try{if(f.size>(/\.json$/i.test(f.name)?16:3)*1024*1024)throw Error('File exceeds local intake limit.');
    const bytes=new Uint8Array(await f.arrayBuffer());
    if(/\.json$/i.test(f.name)&&bytes.length<=16*1024*1024){const text=new TextDecoder().decode(bytes);let j;try{j=JSON.parse(text);}catch{}
     if(j?.schema==='CGX-PRESS-COMPOSITION-REVIEW/0.1'){
      if(composition.layers.length&&!doc.defaultView.confirm('Replace this page’s current composition with the saved draft?'))continue;
      composition=await restoreComposition(text);selected=composition.layers.at(-1)?.id||null;message='Composition restored; source bytes and digest verified.';continue;}
     if(j?.schema==='CGX-LOAD-UNSIGNED-BATCH-DRAFT/0.1'){await bindLoad(j);continue;}}
    const a=await sourceAsset(f.name,f.type,bytes);const result=addAsset(composition,a);composition=result.composition;
    if(result.duplicate){duplicates++;continue;}
    const kind=a.mime.startsWith('image/')?'image':a.handler==='table-preview'?'table':a.handler==='contract-inspection'?'contract':a.text?'information':'object';
    composition=addLayer(composition,kind,a.id);selected=composition.layers.at(-1).id;added++;
   }catch{held++;}
  }
  if(added||duplicates||held)message=`${added} sources added · ${duplicates} exact duplicates reused · ${held} files held. Nothing uploaded.`;
  }finally{busy=false;render();}
 };
 const imageUrl=a=>{if(!urls.has(a.id)){const bytes=Uint8Array.from(atob(a.base64),c=>c.charCodeAt(0));urls.set(a.id,URL.createObjectURL(new Blob([bytes],{type:a.mime})));}return urls.get(a.id);};
 const visible=l=>l.visible&&(!l.parent_id||composition.layers.find(p=>p.id===l.parent_id)&&visible(composition.layers.find(p=>p.id===l.parent_id)));
 function render(){
  root.replaceChildren();const panel=el('article','','panel cgx-composer'+(!showSources&&!showInspector?' press-focused':''));panel.append(el('p','UniSpace · FileSpace / visual Press','eyebrow'),el('h2','Layer your object'));
  panel.append(el('p','Arrange source facets on one surface. Image, information and contract views follow the selected layer. Original bytes remain unchanged.'));
  const meta=el('div','','press-toolbar');meta.append(field('Composition title',input('Composition title',composition.title,v=>{composition.title=v.slice(0,180);})),field('Existing object / family reference',input('Existing object or family reference',composition.object_ref,v=>{composition.object_ref=v.slice(0,500);})));panel.append(meta);
  const family=el('select');family.setAttribute('aria-label','Existing review family');const unset=el('option','Choose existing review family / space');unset.value='';family.append(unset);for(const node of families){const o=el('option',node.label);o.value=node.key;family.append(o);}family.value=composition.object_ref;family.addEventListener('change',()=>{composition.object_ref=family.value;message='Existing review reference selected; native identity remains unverified.';render();});panel.append(field('Family / space (existing review hierarchy)',family));
  const toolbar=el('div','','press-toolbar');const file=el('input');file.type='file';file.multiple=true;file.setAttribute('aria-label','Add local files or saved composition');file.disabled=busy;file.addEventListener('change',()=>pick(file.files));toolbar.append(file);
  toolbar.append(button(showSources?'Close sources panel':'Open sources panel',()=>{showSources=!showSources;render();}),button(showInspector?'Close inspector panel':'Open inspector panel',()=>{showInspector=!showInspector;render();}),button('Focus composition',()=>{showSources=false;showInspector=false;render();}));
  for(const kind of KINDS)toolbar.append(button('Add '+kind,()=>run(()=>{composition=addLayer(composition,kind);selected=composition.layers.at(kind==='background'?0:-1).id;})));
  toolbar.append(button('Press · save premint composition',()=>run(async()=>{
   const draft=await exportComposition(composition);pressedJson=JSON.stringify(draft,null,2);const url=URL.createObjectURL(new Blob([pressedJson],{type:'application/json'}));const a=el('a');a.href=url;a.download='CGX_Press_'+draft.composition_sha256.slice(0,16)+'.review.json';doc.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);message='Preparation download requested · SHA-256 '+draft.composition_sha256;
  })));panel.append(toolbar);
  toolbar.append(button('Resolve known facets',()=>run(async()=>{resolvedFacets=await resolveKnownFacets(composition);message='Known facets resolved from verified local bytes. Unknown facets remain unavailable; source bodies are referenced once.';})));
  if(resolvedFacets){const known=el('details');known.append(el('summary','Last resolved source objects / known facets'));known.append(el('pre',JSON.stringify({composition_sha256:resolvedFacets.composition_sha256,source_objects:resolvedFacets.objects.map(o=>({source_ref:o.source_ref,known_fields:Object.keys(o.known),byte_size:o.known.byte_size,presentation_facets:o.presentation_facets,unresolved:o.unresolved})),display_only_layers:resolvedFacets.display_only_layers,new_database:false},null,2)));panel.append(known);}
  if(pressedJson){const saved=el('details');saved.append(el('summary','Last pressed snapshot · JSON save fallback'));const output=el('textarea');output.readOnly=true;output.rows=4;output.value=pressedJson;output.setAttribute('aria-label','Last pressed composition JSON');saved.append(output,button('Copy pressed JSON',()=>run(async()=>{await doc.defaultView.navigator.clipboard.writeText(pressedJson);message='Pressed JSON copied. Save it as a local .review.json file.';})),el('p','This is the last pressed snapshot. Press again after changing the composition.'));panel.append(saved);}
  const launch=el('div','','press-launch');launch.append(el('strong','Launch order: LOAD library → accepted LOAD completion → Grex families'),el('p',composition.load_plan?`${composition.load_plan.references} LOAD references · ${composition.load_plan.batches} sequential batches · 0 mint-ready · plan ${composition.load_plan.plan_sha256}`:'Prepare or restore the existing LOAD batch below to link its exact plan to this composition.'));
  launch.append(button('Prepare / inspect LOAD sequence',()=>{doc.dispatchEvent(new doc.defaultView.CustomEvent('cgx-open-object-tool',{detail:{id:'load'}}));}),el('span','Mint held · signed launch adapter, source rights, native identities and DBR not accepted'));panel.append(launch);
  const status=el('p',message);status.setAttribute('role','status');status.setAttribute('data-press-status','');panel.append(status);
  const grid=el('div','','press-grid'+(!showSources?' sources-closed':'')+(!showInspector?' inspector-closed':''));const library=el('aside','','press-library');library.append(el('h3','Sources & layer stack'),el('p','Top of this list is the foreground. Move layers with arrows or drag a row onto another.'));
  const stackTabs=el('div','','press-stack-tabs');for(const [key,label] of [['all','All'],['visual','Visual layers'],['data','Data layers'],['contract','Contract layers']]){const b=button(label,()=>{stack=key;render();});b.setAttribute('aria-pressed',String(stack===key));stackTabs.append(b);}library.append(stackTabs);
  for(const layer of [...composition.layers].reverse()){
   const category=['image','object','background'].includes(layer.kind)?'visual':layer.kind==='contract'?'contract':'data';if(stack!=='all'&&stack!==category)continue;
   const row=el('div','','press-layer-row');row.draggable=true;row.dataset.layer=layer.id;
   row.addEventListener('dragstart',e=>{e.dataTransfer.setData('application/x-cgx-layer',layer.id);e.dataTransfer.effectAllowed='move';});
   row.addEventListener('dragover',e=>{if(e.dataTransfer.types.includes('application/x-cgx-layer'))e.preventDefault();});
   row.addEventListener('drop',e=>{const id=e.dataTransfer.getData('application/x-cgx-layer');if(!id)return;e.preventDefault();e.stopPropagation();const from=composition.layers.findIndex(l=>l.id===id),to=composition.layers.findIndex(l=>l.id===layer.id);composition=moveLayer(composition,id,to-from);render();});
   const choose=button((layer.parent_id?'↳ ':'')+layer.name,()=>{selected=layer.id;render();});choose.setAttribute('aria-pressed',String(selected===layer.id));
   const thumbnailAsset=composition.assets.find(a=>a.id===layer.asset_id);if(thumbnailAsset?.mime.startsWith('image/')){const thumb=el('img');thumb.src=imageUrl(thumbnailAsset);thumb.alt='';thumb.draggable=false;choose.prepend(thumb);}else choose.prepend(doc.createTextNode(category==='visual'?'▧ ':category==='data'?'▤ ':'◇ '));
   row.append(choose,button('↑',()=>{composition=moveLayer(composition,layer.id,1);render();}),button('↓',()=>{composition=moveLayer(composition,layer.id,-1);render();}));library.append(row);
  }
  library.append(el('h3','Source library'));
  for(const a of composition.assets){const card=el('div','','press-source');card.append(el('strong',a.name),el('small',`${a.size} bytes · ${a.handler}\nSHA-256 ${a.id}`));card.append(button('Use source again',()=>run(()=>{composition=addLayer(composition,a.mime.startsWith('image/')?'image':'object',a.id);selected=composition.layers.at(-1).id;})));library.append(card);}
  const center=el('div');const previews=el('div','','press-previews');const layerPreview=el('div','','press-single-preview');layerPreview.append(el('h3','Layer preview'));const chosen=composition.layers.find(l=>l.id===selected);const selectedAsset=composition.assets.find(a=>a.id===chosen?.asset_id);
  if(chosen){if(selectedAsset?.mime.startsWith('image/')){const img=el('img');img.src=imageUrl(selectedAsset);img.alt='Selected layer '+chosen.name;layerPreview.append(img);}else layerPreview.append(el('pre',chosen.text||chosen.name));}else layerPreview.append(el('p','Choose a layer'));
  const fullPreview=el('div');fullPreview.append(el('h3','Full preview'));const surface=el('div','','press-surface');surface.setAttribute('aria-label','Layer composition surface');surface.tabIndex=0;
  surface.addEventListener('dragover',e=>{if(e.dataTransfer.types.includes('Files')){e.preventDefault();e.dataTransfer.dropEffect='copy';}});
  surface.addEventListener('drop',e=>{if(e.dataTransfer.files.length){e.preventDefault();pick(e.dataTransfer.files);}});
  if(!composition.layers.length)surface.append(el('p','Drop images, source objects, CSV tables or contract JSON here.','press-empty'));
  for(const [z,l] of composition.layers.entries()){
   if(!visible(l))continue;const item=el('div','','press-item'+(selected===l.id?' selected':''));item.tabIndex=0;item.dataset.pressLayer=l.id;item.setAttribute('aria-label','Layer '+l.name);
   Object.assign(item.style,{left:l.x+'%',top:l.y+'%',width:l.width+'%',height:l.height+'%',opacity:l.opacity/100,zIndex:String(z),color:l.color,background:l.kind==='background'?l.color:'transparent'});
   const a=composition.assets.find(a=>a.id===l.asset_id);
   if(a?.mime.startsWith('image/')&&['image','background','object'].includes(l.kind)){const img=el('img');img.src=imageUrl(a);img.alt=l.name;img.draggable=false;item.append(img);}
   else if(l.kind==='table'){
    try{const table=el('table');for(const cells of parseCsv(l.text).slice(0,15)){const tr=el('tr');for(const cell of cells.slice(0,10))tr.append(el('td',cell));table.append(tr);}item.append(table);}catch{item.append(el('p','Table format needs review.'));}
   }else if(l.kind!=='background')item.append(el(l.kind==='contract'?'pre':'div',l.text||l.name));
   item.addEventListener('click',()=>{if(selected!==l.id){selected=l.id;render();}});
   item.addEventListener('keydown',e=>{const map={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};if(!map[e.key])return;e.preventDefault();selected=l.id;const [dx,dy]=map[e.key];run(()=>{composition=updateLayer(composition,l.id,{x:Math.max(0,Math.min(100-l.width,l.x+dx)),y:Math.max(0,Math.min(100-l.height,l.y+dy))});});});
   item.addEventListener('pointerdown',e=>{
    if(e.button!==0)return;const rect=surface.getBoundingClientRect(),sx=e.clientX,sy=e.clientY;let moved=false;item.setPointerCapture(e.pointerId);
    const move=ev=>{const x=Math.max(0,Math.min(100-l.width,l.x+(ev.clientX-sx)/rect.width*100)),y=Math.max(0,Math.min(100-l.height,l.y+(ev.clientY-sy)/rect.height*100));item.style.left=x+'%';item.style.top=y+'%';moved=true;};
    const end=()=>{item.removeEventListener('pointermove',move);item.removeEventListener('pointerup',end);item.removeEventListener('pointercancel',end);if(moved){composition=updateLayer(composition,l.id,{x:parseFloat(item.style.left),y:parseFloat(item.style.top)});selected=l.id;render();}};
    item.addEventListener('pointermove',move);item.addEventListener('pointerup',end);item.addEventListener('pointercancel',end);
   });surface.append(item);
  }
  fullPreview.append(surface);previews.append(layerPreview,fullPreview);center.append(previews,el('p','Drag to place · arrow keys to nudge · inspector for exact position. Parent links group visibility; positions remain relative to the surface.','muted'));
  const details=el('div','','press-catalogue');details.append(el('h3','Premint catalogue details'));for(const [key,label] of [['catalogue','Catalogue / library'],['contract_type','Contract type (unbound)'],['notes','Preparation notes']])details.append(field(label,input(label,composition[key],v=>{composition[key]=v.slice(0,key==='notes'?4000:180);})));center.append(details);
  const inspector=el('aside','','press-inspector');inspector.append(el('h3','Selected facet'));
  const l=composition.layers.find(l=>l.id===selected);
  if(l){
   inspector.append(field('Layer name',input('Layer name',l.name,v=>update({name:v}))));
   const kind=el('select');kind.setAttribute('aria-label','Layer kind');for(const k of KINDS){const o=el('option',k);o.value=k;kind.append(o);}kind.value=l.kind;kind.addEventListener('change',()=>update({kind:kind.value}));inspector.append(field('Handler / facet',kind));
   const parent=el('select');parent.setAttribute('aria-label','Layer parent');const none=el('option','No layer parent');none.value='';parent.append(none);for(const p of composition.layers.filter(p=>p.id!==l.id)){const o=el('option',p.name);o.value=p.id;parent.append(o);}parent.value=l.parent_id||'';parent.addEventListener('change',()=>update({parent_id:parent.value||null}));inspector.append(field('Hierarchy',parent));
   for(const key of ['x','y','width','height','opacity']){const n=input('Layer '+key,l[key],v=>update({[key]:v}),'number');n.min='0';n.max='100';n.step='1';inspector.append(field(key+' %',n));}
   inspector.append(field('Colour',input('Layer colour',l.color,v=>update({color:v}),'color')));
   const text=el('textarea');text.rows=7;text.value=l.text;text.setAttribute('aria-label','Layer content');text.addEventListener('input',()=>{editing=true;update({text:text.value});editing=false;});text.addEventListener('change',()=>render());inspector.append(field(l.kind==='table'?'CSV table':l.kind==='contract'?'Contract data (inert)':'Information',text));
   inspector.append(field('Source / shorthand reference',input('Layer source reference',l.source_ref,v=>update({source_ref:v}))));
   inspector.append(button(l.visible?'Hide layer':'Show layer',()=>update({visible:!l.visible})),button('Remove from composition',()=>{composition={...composition,layers:composition.layers.filter(x=>x.id!==l.id).map(x=>x.parent_id===l.id?{...x,parent_id:null}:x)};selected=null;render();}));
   const a=composition.assets.find(a=>a.id===l.asset_id);inspector.append(el('small',a?`${a.handler} · original SHA-256 ${a.id} · rights unverified`:'Display facet · no source identity bound'));
  }else inspector.append(el('p','Select a layer to inspect its content, placement, source or contract data.'));
  grid.append(library,center,inspector);panel.append(grid);
  const restore=el('details');restore.append(el('summary','Restore a saved composition from JSON'));const pasted=el('textarea');pasted.rows=3;pasted.setAttribute('aria-label','Saved composition JSON');restore.append(pasted,button('Restore composition JSON',()=>run(async()=>{const next=await restoreComposition(pasted.value);if(composition.layers.length&&!doc.defaultView.confirm('Replace this page’s composition with the saved draft?'))return;composition=next;selected=next.layers.at(-1)?.id||null;message='Restored and verified source bytes, layers and preparation digest.';})));panel.append(restore);
  panel.append(el('p','Private local preparation · changes stay in this page until saved · source rights unverified · contracts are inspected as data · native mint, publication and execution remain unset.','muted'));root.append(panel);
 }
 const onFocus=e=>{if(families.some(n=>n.key===e.detail?.key)){composition.object_ref=e.detail.key;message='Selected existing family / space; your composition layers are retained.';render();}};
 const bindLoad=async draft=>{const verified=await restoreBatchDraft(JSON.stringify(draft));const d=verified.draft;composition.load_plan={plan_sha256:d.plan_sha256,references:d.summary.selected_records,batches:d.summary.batches,mint_ready:0};composition.object_ref='facet.load';message='Linked the existing verified unsigned LOAD plan. No launch execution enabled.';};
 const onLoad=e=>run(()=>bindLoad(e.detail));
 doc.addEventListener('cgx-review-focus',onFocus);
 doc.addEventListener('cgx-load-batch-prepared',onLoad);
 render();return {dispose(){doc.removeEventListener('cgx-review-focus',onFocus);doc.removeEventListener('cgx-load-batch-prepared',onLoad);for(const u of urls.values())URL.revokeObjectURL(u);root.replaceChildren();}};
}
