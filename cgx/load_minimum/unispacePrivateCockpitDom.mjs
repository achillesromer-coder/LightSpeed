/**
 * UniSpace private operator cockpit: accessible, inert DOM binding.
 * Source review only. It does NOT authenticate the browser or grant an ACL.
 * Keep this module outside Vite public/static paths until #158/#161 acceptance.
 * All untrusted labels are inserted as textContent, never as HTML.
 */
import {planUniSpaceOperatorCockpit} from './unispaceSourceInspector.mjs';

export const PRIVATE_STATUS_DOM_SCHEMA='UNISPACE-PRIVATE-STATUS-DOM/0.1';
const denied=reason=>({schema:PRIVATE_STATUS_DOM_SCHEMA,status:'DENIED',reason,
  host_authenticated:false,rendered_live:false,public_release:false,may_execute:false});
const element=(doc,tag,text)=>{
 const node=doc.createElement(tag);
 node.textContent=String(text);
 return node;
};
const line=(doc,label,value)=>{
 const item=doc.createElement('div');
 const dt=element(doc,'dt',label);
 const dd=element(doc,'dd',value);
 item.append(dt,dd);
 return item;
};

/**
 * Mount a review-only status for one exact child Object_ID.
 * No source claims, hashes, private edges, host receipts or credentials are
 * serialized. There are deliberately no links, buttons or execution handlers.
 * The caller MUST independently provide a private authenticated host boundary;
 * passing surface='private' alone is not a security check.
 */
export function renderUniSpacePrivateStatus({
 mount=null,surface=null,selection=null,inspector=null,offline=false,hostReceipt=null
}={}){
 if(!mount||typeof mount.replaceChildren!=='function'||
    !mount.ownerDocument||typeof mount.ownerDocument.createElement!=='function')
  return denied('INVALID_MOUNT');
 // Clear any previous private projection BEFORE checking a new surface.
 // A public-route transition must not leave stale private DOM behind.
 mount.replaceChildren();
 const status=planUniSpaceOperatorCockpit({surface,selection,inspector,offline,hostReceipt});
 if(status.state!=='SOURCE_REVIEW_ONLY')
  return denied(status.reason||'REVIEW_PLAN_NOT_ACCEPTED');
 const doc=mount.ownerDocument;
 const section=doc.createElement('section');
 section.setAttribute('role','status');
 section.setAttribute('aria-live','polite');
 section.setAttribute('aria-atomic','true');
 section.setAttribute('aria-label','UniSpace private source-review status');
 section.setAttribute('data-cgx-authority','SOURCE_REVIEW_ONLY');
 section.append(element(doc,'h2','UniSpace — private source review only'));
 section.append(element(doc,'p',status.accessibility.announcement));
 const details=doc.createElement('dl');
 details.append(
  line(doc,'Selected Object_ID',status.identity),
  line(doc,'Child FileSpace',status.file_space),
  line(doc,'Parent FileSpace',status.parent_file_space),
  line(doc,'View',status.view),
  line(doc,'Presentation stage',status.presentation_stage),
  line(doc,'Source evidence',status.source_evidence),
  line(doc,'Host authentication',status.host_connection),
  line(doc,'Native admission','HOLD — not verified'),
  line(doc,'Live deployment','HOLD — not verified'),
  line(doc,'Next bounded action',status.next_step)
 );
 section.append(details);
 section.append(element(doc,'h3','Workflow proof gates'));
 const workflow=doc.createElement('ol');
 for(const step of status.workflow)
  workflow.append(element(doc,'li',step.stage+' — '+step.status));
 section.append(workflow);
 section.append(element(doc,'h3','Outstanding gates'));
 const blockers=doc.createElement('ul');
 for(const gate of status.blockers)
  blockers.append(element(doc,'li',gate));
 section.append(blockers);
 section.append(element(doc,'p','No host command, hydration, source upload, native mint or public release is available in this view.'));
 mount.replaceChildren(section);
 return {schema:PRIVATE_STATUS_DOM_SCHEMA,status:'RENDERED_SOURCE_REVIEW',
  presentation_stage:status.presentation_stage,host_authenticated:false,
  rendered_live:false,public_release:false,may_execute:false};
}
