// Static first-party UniSpace programme view. NO backend calls or private content.
import {describeDomain} from "./domain-overviews.js";
const root = document.getElementById("cgx-public-domain");
const name = document.body.dataset.domain;
const data = describeDomain(name);
if (!root || data.status === "UNKNOWN_DOMAIN") {
  document.body.textContent = "Unknown public UniSpace programme";
} else {
  const add = (parent,tag,text,cls) => {
    const node=document.createElement(tag);
    node.textContent=text;
    if(cls)node.className=cls;
    parent.appendChild(node);
    return node;
  };
  const wrap=add(root,"div","","container");
  const head=add(wrap,"header","","mast");
  const home=add(head,"a","","brand");
  home.href="/cgx/";
  add(home,"strong","U","glyph");
  const brand=add(home,"span","");
  add(brand,"strong","UniSpace");
  add(brand,"small","Powered by CGX");
  add(head,"span","PUBLIC DESCRIPTIVE VIEW · NOT RELEASE PROOF","publictag");
  const nav=add(wrap,"nav","","nav");
  nav.setAttribute("aria-label","UniSpace public sections");
  for (const [url,label] of [
    ["/cgx/","UniSpace"],["/cgx/fs/","FileSpace"],["/cgx/ds/","DataSpace"],
    ["/cgx/ps/","PrintSpace"],["/cgx/romer/","Römer-Grex"],["/cgx/eco/","Eco-Grex"]
  ]) {
    const a=add(nav,"a",label);
    a.href=url;
    if(url==="/cgx/"+name+"/")a.setAttribute("aria-current","page");
  }
  const hero=add(wrap,"section","","hero");
  add(hero,"p","CGX / UniSpace / domain orientation","eyebrow");
  add(hero,"h1",data.label);
  add(hero,"p",data.description);
  const area=add(wrap,"main","");
  area.id="cgx-domain-main";
  const intro=add(area,"section","","panel");
  add(intro,"p","PROGRAMME FRAMEWORK","eyebrow");
  add(intro,"h2",data.heading);
  add(intro,"p","The same Cognigrex FileSpace identity supports separate, rights-scoped domain views. LightSpeed is an execution extension, not a replacement source of authority.");
  const cards=add(area,"div","","cards");
  for(const item of data.families) {
    const card=add(cards,"section","","tile");
    add(card,"p","DESCRIPTIVE · EVIDENCE GATED","eyebrow");
    add(card,"h2",item.title);
    add(card,"p",item.description);
  }
  const gate=add(area,"section","","panel");
  add(gate,"p","EVIDENCE AND ACCESS","eyebrow");
  add(gate,"h2","Interpretation is not qualification");
  add(gate,"p","These labels are public programme descriptions only, not an export from an internal CGX catalogue, approved engineering claim, authenticated node connection, physical result or release receipt.");
  const pre=add(gate,"pre",JSON.stringify(data,null,2),"output");
  pre.setAttribute("aria-label","Machine-readable public programme orientation");
  const foot=add(wrap,"footer","");
  add(foot,"strong",data.label+" / CGX");
  add(foot,"p","Public orientation · Owner publication and source evidence verified independently");
  const back=add(foot,"a","Back to UniSpace ↗");
  back.href="/cgx/";
  document.title="UniSpace · "+data.label;
}
