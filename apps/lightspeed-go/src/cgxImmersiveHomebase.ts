/**
 * AR-first (screen overlay) and top-down/OS/VR-style spatial CGX workbench.
 * Functional local layout editing + existing workspace navigation only.
 * WebXR hardware/passthrough and host FileSpace persistence NOT claimed.
 */
import type { CgxGeneratedGuiPlan, CgxShellWorkspace } from "./cgxGeneratedGui";
import {
  addSpatialObject, compileSpatialHomebase, createSpatialHomebase,
  linkSpatialObjects, placeSpatialNode, spatialSnapshot, styleSpatialRoom,
  type SpatialHomebase, type SpatialNode, type SpatialRoom,
  type SpatialNodeKind, type SpatialTheme, type SpatialLight, SpatialHold,
  CGX_SPATIAL_COLUMNS, CGX_SPATIAL_ROWS
} from "./cgxSpatialHomebase";

export type ImmersiveMode="ar"|"plan"|"os"|"vr";
const MODES:readonly ImmersiveMode[]=["ar","plan","os","vr"];
const THEMES:readonly SpatialTheme[]=["neutral","forest","industrial","cosmos","arcade"];
const LIGHTS:readonly SpatialLight[]=["day","dusk","night"];
const DRAFT_KEY="cgx.unispace.spatial-homebase.review-v1";
const MAX_IMPORT_BYTES=65536;
const element=(tag:string,cls?:string,value?:string):HTMLElement=>{
  const item=document.createElement(tag);
  if(cls)item.className=cls;
  if(value!==undefined)item.textContent=value;
  return item;
};
const action=(value:string,handler:()=>void,cls?:string):HTMLButtonElement=>{
  const b=document.createElement("button");b.type="button";b.textContent=value;
  if(cls)b.className=cls;b.addEventListener("click",handler);return b;
};
const select=<T extends string>(items:readonly T[],current:T):HTMLSelectElement=>{
  const s=document.createElement("select");
  for(const value of items){const o=document.createElement("option");o.value=value;
    o.textContent=value;if(value===current)o.selected=true;s.append(o);}
  return s;
};
const numeric=(name:string,value:number,min:number,max:number):HTMLInputElement=>{
  const input=document.createElement("input");input.type="number";input.step="1";
  input.min=String(min);input.max=String(max);input.value=String(value);
  input.setAttribute("aria-label",name);return input;
};
const statusError=(error:unknown):string=>
  error instanceof SpatialHold ? error.code :
  error instanceof Error ? error.message.slice(0,130) : "LOCAL_LAYOUT_HOLD";
const snapshot=(x:SpatialHomebase):SpatialHomebase=>compileSpatialHomebase(x);
const sameRoom=(a:SpatialNode,b:SpatialNode)=>a.room===b.room;
const ymid=(n:SpatialNode)=>((n.y+n.h/2)/CGX_SPATIAL_ROWS)*100;
const xmid=(n:SpatialNode)=>((n.x+n.w/2)/CGX_SPATIAL_COLUMNS)*100;

/** Incremental static SVG relationship projection: never an actuation map. */
export function drawSpatialRelations(layout:SpatialHomebase,roomId:string):SVGSVGElement{
  const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
  svg.setAttribute("class","ls-spatial-relations");
  svg.setAttribute("viewBox","0 0 100 100");svg.setAttribute("preserveAspectRatio","none");
  svg.setAttribute("aria-hidden","true");
  const byId=new Map(layout.nodes.map(n=>[n.id,n]));
  for(const relation of layout.links){
    const a=byId.get(relation.from),b=byId.get(relation.to);
    if(!a||!b||!sameRoom(a,b)||a.room!==roomId)continue;
    const line=document.createElementNS("http://www.w3.org/2000/svg","line");
    line.setAttribute("x1",String(xmid(a)));line.setAttribute("y1",String(ymid(a)));
    line.setAttribute("x2",String(xmid(b)));line.setAttribute("y2",String(ymid(b)));
    line.setAttribute("data-relationship",relation.kind);
    line.setAttribute("vector-effect","non-scaling-stroke");
    svg.append(line);
  }
  return svg;
}
export function immersiveModeTitle(mode:ImmersiveMode):string{
  return {
    ar:"AR-style HUD · screen preview",
    plan:"2D editor · top-down",
    os:"OS deck · spatial windows",
    vr:"VR-style stage · screen preview"
  }[mode];
}
export function mountCgxImmersiveHomebase(
  host:HTMLElement,sourcePlan:CgxGeneratedGuiPlan,
  openWorkspace:(workspace:CgxShellWorkspace)=>void
):void{
  if(host.dataset.cgxSpatialMounted==="cgx.spatial.homebase/1")return;
  let layout=createSpatialHomebase(sourcePlan);
  let roomId="home",selected:string|null=null,mode:ImmersiveMode="ar";
  let editing=true;
  let history:SpatialHomebase[]=[];
  let redo:SpatialHomebase[]=[];
  let baseline=spatialSnapshot(layout);
  const panel=element("section","ls-spatial-immersive");
  panel.dataset.viewMode=mode;
  const header=element("header","ls-spatial-header");
  const name=element("div","ls-spatial-title");
  name.append(element("p","ls-spatial-kicker","COGNIGREX · UNIVERSATILE HOME BASE"),
    element("h2",undefined,"Spatial UniSpace"),
    element("p","ls-spatial-subtitle","Move between Grex realities, systems, game worlds and existing data facets without leaving your home-base interface."));
  const state=element("span","ls-spatial-hold","LOCAL PREVIEW · native gate held");
  header.append(name,state);
  const toolbar=element("div","ls-spatial-toolbar");
  const info=element("p","ls-spatial-status","AR-style presentation is 2D screen composition; immersive hardware is not connected.");
  info.setAttribute("role","status");info.setAttribute("aria-live","polite");
  const breadcrumb=element("nav","ls-spatial-breadcrumb");
  breadcrumb.setAttribute("aria-label","Spatial location");
  const layoutFrame=element("div","ls-spatial-frame");
  const stage=element("div","ls-spatial-stage");
  stage.tabIndex=0;stage.setAttribute("role","group");
  stage.setAttribute("aria-label","Top-down spatial Grex home-base arrangement");
  const inspector=element("aside","ls-spatial-inspector");
  const bottom=element("div","ls-spatial-footer");
  layoutFrame.append(stage,inspector);
  panel.append(header,toolbar,breadcrumb,layoutFrame,bottom,info);
  host.replaceChildren(panel);host.dataset.cgxSpatialMounted="cgx.spatial.homebase/1";

  const setNote=(value:string):void=>{info.textContent=value;};
  const present=(next:SpatialHomebase,actionLabel:string):void=>{
    const valid=compileSpatialHomebase(next);
    history.push(snapshot(layout));if(history.length>40)history=history.slice(-40);
    redo=[];layout=valid;setNote(actionLabel+" · local draft only, no native write");
    render();
  };
  const attempt=(compute:()=>SpatialHomebase,label:string):void=>{
    try{present(compute(),label);}catch(error){setNote("Change held: "+statusError(error));}
  };
  const currentRoom=():SpatialRoom=>layout.rooms.find(x=>x.id===roomId)||layout.rooms[0];
  const currentSelection=():SpatialNode|undefined=>layout.nodes.find(n=>n.id===selected&&n.room===roomId);
  const enter=(room:string):void=>{
    if(!layout.rooms.some(r=>r.id===room)){setNote("Room not present in this review layout");return;}
    roomId=room;selected=null;render();
  };
  const move=(node:SpatialNode,x:number,y:number,w=node.w,h=node.h):void=>
    attempt(()=>placeSpatialNode(layout,node.id,x,y,w,h),"Node repositioned");
  const add=(kind:SpatialNodeKind):void=>{
    const labelInput=host.querySelector<HTMLInputElement>("[data-spatial-label]");
    const name=labelInput?.value.trim()||({"grex":"New Grex","game":"New world","profile":"Profile","object":"Object","facet":"Facet"}[kind]);
    attempt(()=>addSpatialObject(layout,roomId,name,kind),"Component added");
  };
  const undo=():void=>{
    const previous=history.pop();if(!previous){setNote("No earlier local version");return;}
    redo.push(snapshot(layout));layout=previous;
    if(!layout.rooms.some(x=>x.id===roomId))roomId="home";
    selected=null;setNote("Undid one local layout operation");render();
  };
  const redoOp=():void=>{
    const next=redo.pop();if(!next){setNote("No redo version");return;}
    history.push(snapshot(layout));layout=next;
    if(!layout.rooms.some(x=>x.id===roomId))roomId="home";
    selected=null;setNote("Redid one local layout operation");render();
  };
  const saveDraft=():void=>{
    try{
      localStorage.setItem(DRAFT_KEY,spatialSnapshot(layout));
      baseline=spatialSnapshot(layout);
      setNote("Local browser draft saved. NOT a FileSpace/DBR commit or cross-device sync.");
    }catch{setNote("Browser storage unavailable; use explicit JSON export.");}
  };
  const restoreDraft=():void=>{
    try{
      const value=localStorage.getItem(DRAFT_KEY);
      if(!value){setNote("No local draft found; original seed retained");return;}
      present(compileSpatialHomebase(value),"Local browser draft restored");
      roomId="home";selected=null;render();
    }catch(error){setNote("Local draft rejected: "+statusError(error));}
  };
  const exportDraft=():void=>{
    const blob=new Blob([spatialSnapshot(layout)],{type:"application/json"});
    const url=URL.createObjectURL(blob),a=document.createElement("a");
    a.href=url;a.download="UniSpace.homebase.cgx.layout.json";
    a.rel="noopener";a.click();URL.revokeObjectURL(url);
    setNote("Portable layout exported; no private file content included");
  };
  const importInput=document.createElement("input");
  importInput.type="file";importInput.accept=".json,application/json";
  importInput.setAttribute("aria-label","Import local spatial CGX layout JSON");
  importInput.hidden=true;
  importInput.addEventListener("change",async()=>{
    const file=importInput.files?.[0];
    if(!file)return;
    if(file.size<1||file.size>MAX_IMPORT_BYTES){setNote("Import held: 64 KiB layout limit");importInput.value="";return;}
    try{
      const parsed=compileSpatialHomebase(await file.text());
      present(parsed,"Portable layout imported for browser preview");
      roomId="home";selected=null;render();
    }catch(error){setNote("Import rejected: "+statusError(error));}
    importInput.value="";
  });
  const collapse=action("Hide map",()=>{
    const hidden=layoutFrame.hidden;layoutFrame.hidden=!hidden;
    collapse.textContent=hidden?"Hide map":"Show map";
  });
  const modes=element("div","ls-spatial-modes");
  for(const candidate of MODES){
    const b=action(immersiveModeTitle(candidate),()=>{
      mode=candidate;panel.dataset.viewMode=mode;render();setNote(
        candidate==="ar"||candidate==="vr"
          ?"Screen-only "+candidate.toUpperCase()+"-style UI: camera/headset tracking not connected."
          :"Local "+candidate.toUpperCase()+" spatial layout active.");
    });
    b.dataset.spatialMode=candidate;modes.append(b);
  }
  const editToggle=action("Editing: on",()=>{
    editing=!editing;editToggle.textContent=editing?"Editing: on":"Editing: off";render();
  });
  toolbar.append(modes,editToggle,action("Undo",undo),action("Redo",redoOp),
    action("Save local",saveDraft),action("Load local",restoreDraft),
    action("Export .cgx layout",exportDraft),action("Import layout",()=>importInput.click()),
    action("Restore original",()=>attempt(()=>compileSpatialHomebase(baseline),"Saved local baseline restored")),
    collapse,importInput);
  const addControls=element("div","ls-spatial-add");
  const labelInput=document.createElement("input");
  labelInput.type="text";labelInput.maxLength=112;labelInput.placeholder="Name new Grex, room or object";
  labelInput.dataset.spatialLabel="";
  labelInput.setAttribute("aria-label","New component name");
  addControls.append(labelInput);
  for(const kind of ["grex","game","profile","object"] as const)
    addControls.append(action("Add "+kind,()=>add(kind)));
  bottom.append(addControls,element("p","ls-spatial-disclaimer",
    "AR/VR are display styles, not camera passthrough or WebXR sessions. Geometry, room themes and relations are local visual projections; real files, wallets, games, identity and De Sporte remain under their existing separate authenticated host contracts."));

  const renderBreadcrumb=():void=>{
    breadcrumb.replaceChildren();
    let node:SpatialRoom|undefined=currentRoom();
    const path:SpatialRoom[]=[];
    while(node){path.unshift(node);node=node.parent?layout.rooms.find(x=>x.id===node!.parent):undefined;}
    path.forEach((room,i)=>{
      if(i)breadcrumb.append(element("span",undefined," / "));
      const link=action(room.title,()=>enter(room.id));if(room.id===roomId)link.setAttribute("aria-current","location");
      breadcrumb.append(link);
    });
  };
  const renderInspector=():void=>{
    inspector.replaceChildren();
    const room=currentRoom();
    inspector.append(element("p","ls-spatial-kicker","Selected environment"),
      element("h3",undefined,room.title));
    const climate=element("p","ls-spatial-caption",
      "Microclimate: visual scene preset only; no sensor/weather/temperature claim.");
    inspector.append(climate);
    const themeSelect=select(THEMES,room.theme);
    const lightSelect=select(LIGHTS,room.light);
    const themeLabel=element("label",undefined,"Environment theme");
    const lightLabel=element("label",undefined,"Lighting preset");
    themeLabel.append(themeSelect);lightLabel.append(lightSelect);
    themeSelect.disabled=!editing;lightSelect.disabled=!editing;
    inspector.append(themeLabel,lightLabel);
    const applyTheme=action("Apply scene",()=>{
      attempt(()=>styleSpatialRoom(layout,roomId,themeSelect.value as SpatialTheme,lightSelect.value as SpatialLight),
        "Microclimate presentation preset updated");
    });applyTheme.disabled=!editing;inspector.append(applyTheme);
    const selectedNode=currentSelection();
    if(!selectedNode){
      inspector.append(element("p","ls-spatial-caption",
        "Choose an object to inspect, move, resize, enter its room or follow its existing UniSpace workspace. Drag objects on the 2D plane or use keyboard arrows."));
      const legend=element("div","ls-spatial-legend");
      for(const label of ["Grex room","Game/world gateway","Data facet","Profile","Object"])
        legend.append(element("span",undefined,label));
      inspector.append(legend);
      return;
    }
    inspector.append(element("h3",undefined,selectedNode.label),
      element("p","ls-spatial-caption","Object "+selectedNode.id+" · "+selectedNode.kind+
      " · "+selectedNode.layer+" layer. Preview identity only; no source hydration."));
    const actions=element("div","ls-spatial-inspector-actions");
    if(selectedNode.targetRoom)actions.append(action("Enter room",()=>enter(selectedNode.targetRoom!)));
    if(selectedNode.workspace)actions.append(action("Open connected "+selectedNode.workspace,
      ()=>openWorkspace(selectedNode.workspace!)));
    inspector.append(actions);
    const editors=element("div","ls-spatial-coordinate-edit");
    const props=["x","y","w","h"] as const;
    const inputs=props.map(k=>{
      const i=numeric(k,selectedNode[k],k==="w"||k==="h"?1:0,
        k==="x"||k==="w"?CGX_SPATIAL_COLUMNS:CGX_SPATIAL_ROWS);
      i.disabled=!editing;const label=element("label",undefined,k.toUpperCase());
      label.append(i);editors.append(label);return i;
    });
    const apply=action("Apply bounds",()=>{
      const [x,y,w,h]=inputs.map(i=>Number(i.value));
      if(![x,y,w,h].every(Number.isSafeInteger)){setNote("Only integer cell coordinates are allowed");return;}
      move(selectedNode,x,y,w,h);
    });apply.disabled=!editing;
    inspector.append(editors,apply);
    const options=layout.nodes.filter(n=>n.id!==selectedNode.id);
    if(options.length){
      const relationSelect=document.createElement("select");
      relationSelect.setAttribute("aria-label","Connect selected object to");
      for(const candidate of options){
        const op=document.createElement("option");op.value=candidate.id;
        op.textContent=candidate.label+" · "+candidate.room;relationSelect.append(op);
      }
      const link=action("Connect related object",()=>{
        attempt(()=>linkSpatialObjects(layout,selectedNode.id,relationSelect.value,"related"),
          "Semantic view-edge added");
      });link.disabled=!editing;
      inspector.append(element("p","ls-spatial-kicker","Nonlinear relations"),relationSelect,link);
    }
  };
  const renderStage=():void=>{
    stage.replaceChildren();
    const room=currentRoom();
    stage.dataset.spatialTheme=room.theme;stage.dataset.spatialLight=room.light;
    stage.append(drawSpatialRelations(layout,roomId));
    const current=layout.nodes.filter(n=>n.room===roomId);
    const createNode=(node:SpatialNode):void=>{
      const button=document.createElement("button");
      button.type="button";button.className="ls-spatial-object";
      button.dataset.spatialKind=node.kind;
      button.dataset.spatialLayer=node.layer;
      button.dataset.selected=String(selected===node.id);
      button.style.left=(node.x/CGX_SPATIAL_COLUMNS*100)+"%";
      button.style.top=(node.y/CGX_SPATIAL_ROWS*100)+"%";
      button.style.width=(node.w/CGX_SPATIAL_COLUMNS*100)+"%";
      button.style.height=(node.h/CGX_SPATIAL_ROWS*100)+"%";
      button.setAttribute("aria-label",node.label+"; "+node.kind+
        (node.targetRoom?"; enter room available":"")+
        (node.workspace?"; connected workspace "+node.workspace:""));
      button.append(element("strong",undefined,node.label),
        element("small",undefined,node.kind==="grex"?"GREX / ROOM":
          node.kind==="game"?"WORLD GATE":node.kind.toUpperCase()));
      button.addEventListener("click",()=>{selected=node.id;render();});
      button.addEventListener("dblclick",()=>{
        if(node.targetRoom)enter(node.targetRoom);
        else if(node.workspace)openWorkspace(node.workspace);
      });
      button.addEventListener("keydown",(event)=>{
        if(event.key==="Enter"&&event.shiftKey){
          event.preventDefault();
          if(node.targetRoom)enter(node.targetRoom);
          else if(node.workspace)openWorkspace(node.workspace);
          return;
        }
        if(!editing||!["ArrowLeft","ArrowRight","ArrowUp","ArrowDown"].includes(event.key))return;
        event.preventDefault();
        const dx=event.key==="ArrowLeft"?-1:event.key==="ArrowRight"?1:0;
        const dy=event.key==="ArrowUp"?-1:event.key==="ArrowDown"?1:0;
        move(node,node.x+dx,node.y+dy);
      });
      // Pointer-based 2D move; all placements validated on pointer-up. A
      // collision rejects and preserves the prior layout. No host write.
      button.addEventListener("pointerdown",(event)=>{
        if(!editing||event.button!==0)return;
        selected=node.id;
        const startX=event.clientX,startY=event.clientY;
        const rect=stage.getBoundingClientRect();
        if(!rect.width||!rect.height)return;
        const origin={x:node.x,y:node.y};let moved=false;
        button.setPointerCapture(event.pointerId);
        const onMove=(e:PointerEvent)=>{
          const dx=Math.round((e.clientX-startX)/rect.width*CGX_SPATIAL_COLUMNS);
          const dy=Math.round((e.clientY-startY)/rect.height*CGX_SPATIAL_ROWS);
          if(dx===0&&dy===0)return;
          moved=true;button.style.left=((origin.x+dx)/CGX_SPATIAL_COLUMNS*100)+"%";
          button.style.top=((origin.y+dy)/CGX_SPATIAL_ROWS*100)+"%";
        };
        const onEnd=(e:PointerEvent)=>{
          button.removeEventListener("pointermove",onMove);
          button.removeEventListener("pointerup",onEnd);
          button.removeEventListener("pointercancel",onCancel);
          if(!moved){render();return;}
          const dx=Math.round((e.clientX-startX)/rect.width*CGX_SPATIAL_COLUMNS);
          const dy=Math.round((e.clientY-startY)/rect.height*CGX_SPATIAL_ROWS);
          move(node,origin.x+dx,origin.y+dy);
        };
        const onCancel=()=>{
          button.removeEventListener("pointermove",onMove);
          button.removeEventListener("pointerup",onEnd);
          button.removeEventListener("pointercancel",onCancel);
          render();
        };
        button.addEventListener("pointermove",onMove);
        button.addEventListener("pointerup",onEnd);
        button.addEventListener("pointercancel",onCancel);
      });
      stage.append(button);
    };
    for(const node of current)createNode(node);
    stage.append(element("div","ls-spatial-compass","N ↑  ·  GRID "+CGX_SPATIAL_COLUMNS+"×"+CGX_SPATIAL_ROWS));
  };
  const render=():void=>{
    panel.dataset.viewMode=mode;
    panel.dataset.editing=String(editing);
    for(const node of modes.querySelectorAll<HTMLButtonElement>("button")){
      const active=node.dataset.spatialMode===mode;
      node.setAttribute("aria-pressed",String(active));
    }
    if(!layout.rooms.some(x=>x.id===roomId))roomId="home";
    renderBreadcrumb();renderStage();renderInspector();
  };
  render();
}
