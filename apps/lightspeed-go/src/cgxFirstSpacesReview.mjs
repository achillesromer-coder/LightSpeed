import {presentationStyle} from './cgxPresentationPreferences.mjs';
/**
 * Additive preview on the existing UniSpace Objects tab, not another OS shell.
 * No host API, mint issuer, remote effects, source access or persistent approval.
 */
import {planFirstSpacesReview,makeFirstSpacesDesignExport} from './cgxFirstSpacesReviewModel.mjs';
const layouts=['lattice','family-tree','space-grid'];
export function mountFirstSpacesReview(root){
 if(!root||typeof root.replaceChildren!=='function'||!root.ownerDocument)
  return {state:'HOLD',reason:'INVALID_MOUNT'};
 const doc=root.ownerDocument;
 const state={layout:'lattice',focus:'facet.load',order:null,decisions:{},presentation:{}};
 const el=(tag,text='',cls='')=>{
  const node=doc.createElement(tag);node.textContent=text;
  if(cls)node.className=cls;
  return node;
 };
 const button=(label,attr,value,pressed=false)=>{
  const b=el('button',label);b.type='button';b.setAttribute(attr,value);
  if(pressed!==null)b.setAttribute('aria-pressed',String(pressed));
  return b;
 };
 const render=()=>{
  const plan=planFirstSpacesReview(state);
  root.replaceChildren();
  if(plan.state!=='SOURCE_REVIEW_ONLY')return;
  const section=el('article','','panel');
  section.setAttribute('data-cgx-press','SOURCE_REVIEW_ONLY');
  const palette=presentationStyle(plan.presentation);
  section.setAttribute('style','background:'+palette.background+';color:'+palette.foreground+';border-color:'+palette.accent+';padding:18px');
  section.append(el('p','LOAD startup / first spaces','eyebrow'));
  section.append(el('h2','CGX first-spaces lattice — design review only'));
  section.append(el('p','Mint, signing and deployment are held. Rearrangement affects the visual order only. No saved approvals.','muted'));
  const modes=el('div');modes.setAttribute('role','group');
  modes.setAttribute('aria-label','Choose first-spaces view');
  for(const mode of layouts)modes.append(button(mode,'data-cgx-layout',mode,mode===plan.layout));
  section.append(modes);
  const prefs=el('fieldset');prefs.append(el('legend','Appearance and display region'));
  const fields=[['background',['midnight','slate','paper']],['hue',[205,145,35,285]],['density',['comfortable','compact']],['motion',['reduced','system']],['locale',['en','en-AU','en-GB','en-US','de','fr','ar']],['region',['unspecified','AU','NZ','GB','US','ZA','DE']]];
  for(const [key,values] of fields){
   const label=el('label',key+' ');const select=el('select');
   select.setAttribute('data-cgx-preference',key);select.setAttribute('aria-label',key);
   for(const value of values){const option=el('option',String(value));option.value=String(value);option.selected=value===plan.presentation[key];select.append(option);}
   label.append(select);prefs.append(label);
  }
  prefs.append(el('p','Region is optional display context. Preferences apply to this preview and export; they grant no location, legal or SocialSpace permissions.','muted'));
  section.append(prefs);
  const cards=el('div','','graph-stack');cards.setAttribute('style','display:grid;gap:'+palette.gap);cards.setAttribute('role','list');
  cards.setAttribute('aria-label','Provisional families and first spaces');
  for(const node of plan.nodes){
   const row=el('div','','panel');row.setAttribute('role','listitem');
   row.append(button(node.label,'data-cgx-select',node.key,node.key===plan.focus));
   row.append(el('span',node.kind+' · '+node.review_stage,'muted'));
   const earlier=button('↑','data-cgx-move',node.key,null);
   earlier.setAttribute('data-cgx-step','-1');
   earlier.setAttribute('aria-label','Move '+node.label+' earlier in visual order');
   const later=button('↓','data-cgx-move',node.key,null);
   later.setAttribute('data-cgx-step','1');
   later.setAttribute('aria-label','Move '+node.label+' later in visual order');
   row.append(earlier,later);cards.append(row);
  }
  section.append(cards);
  const selected=plan.nodes.find(x=>x.key===plan.focus);
  const status=el('div');status.setAttribute('role','status');
  status.setAttribute('aria-live','polite');
  status.append(el('h3',selected.label));
  status.append(el('p','Kind: '+selected.kind+' · Parent: '+(selected.parent??'single Cognigrex root')+
    ' · Dependencies: '+(selected.requires.join(', ')||'none')));
  status.append(el('p','Unminted candidate. Source rights, issuer, asset proof and DBR are unverified.'));
  status.append(el('p','The Press dependency order is pinned; moving cards cannot rewrite it.'));
  section.append(status);
  const review=el('div');review.setAttribute('role','group');
  review.setAttribute('aria-label','Local concept-only review');
  review.append(button('Mark concept ready (local only)','data-cgx-design','approve',null));
  review.append(button('Defer concept (local only)','data-cgx-design','defer',null));
  review.append(button('Reject concept (local only)','data-cgx-design','deny',null));
  section.append(review);
  section.append(button('Export concept review JSON (no mint)','data-cgx-export','design',null));
  section.append(el('p','Export is a local design receipt only. No authority, signed approval or native mint is created.','muted'));
  root.append(section);
 };
 const onClick=event=>{
  const target=event.target?.closest?.('button');
  if(!target||!root.contains(target))return;
  const layout=target.getAttribute('data-cgx-layout');
  const select=target.getAttribute('data-cgx-select');
  const move=target.getAttribute('data-cgx-move');
  const decision=target.getAttribute('data-cgx-design');
  const exportRequest=target.getAttribute('data-cgx-export');
  if(exportRequest==='design'){
   const receipt=makeFirstSpacesDesignExport(state);
   if(receipt.state!=='LOCAL_DESIGN_REVIEW_FOR_FOUNDER_RECONCILIATION')return;
   const url=URL.createObjectURL(new Blob([JSON.stringify(receipt,null,2)],{type:'application/json'}));
   const a=doc.createElement('a');a.href=url;a.download='CGX_FirstSpaces_DesignReview.json';
   root.append(a);a.click();a.remove();URL.revokeObjectURL(url);return;
  }
  if(layout!==null&&layouts.includes(layout))state.layout=layout;
  else if(select!==null){
   if(planFirstSpacesReview({...state,focus:select}).state==='SOURCE_REVIEW_ONLY')state.focus=select;
  }else if(move!==null){
   const step=Number(target.getAttribute('data-cgx-step'));
   const order=state.order??planFirstSpacesReview(state).order;
   const i=order.indexOf(move),j=i+step;
   if([-1,1].includes(step)&&i>=0&&j>=0&&j<order.length){
    const next=[...order];[next[i],next[j]]=[next[j],next[i]];
    if(planFirstSpacesReview({...state,order:next}).state==='SOURCE_REVIEW_ONLY')state.order=next;
   }
  }else if(decision!==null&&['approve','defer','deny'].includes(decision)){
   const next={...state.decisions,[state.focus]:decision};
   if(planFirstSpacesReview({...state,decisions:next}).state==='SOURCE_REVIEW_ONLY')state.decisions=next;
  }else return;
  render();
 };
 const onChange=event=>{
  const target=event.target;
  if(!target||!root.contains(target))return;
  const key=target.getAttribute('data-cgx-preference');
  if(!['background','hue','density','motion','locale','region'].includes(key))return;
  const value=key==='hue'?Number(target.value):target.value;
  const next={...state.presentation,[key]:value};
  if(planFirstSpacesReview({...state,presentation:next}).state!=='SOURCE_REVIEW_ONLY')return;
  state.presentation=next;render();
 };
 root.addEventListener('change',onChange);
 root.addEventListener('click',onClick);
 render();
 return {state:'SOURCE_REVIEW_ONLY',dispose:()=>{root.removeEventListener('click',onClick);root.removeEventListener('change',onChange);}};
}
