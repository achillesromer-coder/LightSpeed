/**
 * UniSpace 2D home-base / spatial Grex layout.
 * A reversible *view projection* on the existing Cognigrex root; no native
 * FileSpace import, game engine, model, simulation, scheduler or DB is created.
 */
import type { CgxGeneratedGuiPlan, CgxShellWorkspace } from "./cgxGeneratedGui";

export const CGX_SPATIAL_SCHEMA = "cgx.spatial.homebase/1" as const;
export const CGX_SPATIAL_ROOT = "cgx:root:cognigrex" as const;
export const CGX_SPATIAL_COLUMNS = 20;
export const CGX_SPATIAL_ROWS = 14;
export const CGX_SPATIAL_MAX_ROOMS = 24;
export const CGX_SPATIAL_MAX_NODES = 96;

export type SpatialNodeKind = "facet" | "grex" | "game" | "profile" | "object";
export type SpatialNodeLayer = "ground" | "overlay";
export type SpatialTheme = "neutral" | "forest" | "industrial" | "cosmos" | "arcade";
export type SpatialLight = "day" | "dusk" | "night";
export type SpatialRelation = "related" | "depends_on" | "gateway";
export interface SpatialRoom {
  id: string;
  title: string;
  parent: string | null;
  theme: SpatialTheme;
  light: SpatialLight;
  /** Non-physical presentation preset; no measured temperature or weather. */
  climate: "VISUAL_PRESET_ONLY";
}
export interface SpatialNode {
  id: string;
  label: string;
  room: string;
  kind: SpatialNodeKind;
  layer: SpatialNodeLayer;
  x: number; y: number; w: number; h: number;
  facet: string | null;
  workspace: CgxShellWorkspace | null;
  /** Original source identifier for review only; not a hydration capability. */
  sourceRef: string | null;
  targetRoom: string | null;
}
export interface SpatialLink {
  id: string;
  from: string;
  to: string;
  kind: SpatialRelation;
}
export interface SpatialHomebase {
  schema: typeof CGX_SPATIAL_SCHEMA;
  parent: typeof CGX_SPATIAL_ROOT;
  home: "home";
  rooms: SpatialRoom[];
  nodes: SpatialNode[];
  links: SpatialLink[];
  authority: "LOCAL_PRESENTATION_ONLY";
}
export class SpatialHold extends Error {
  constructor(readonly code: string) {super(code);this.name="SpatialHold";}
}
const fail=(code:string):never=>{throw new SpatialHold(code);};
const isObj=(o:unknown):o is Record<string,unknown>=>!!o&&typeof o==="object"&&!Array.isArray(o);
const keys=(o:Record<string,unknown>,expected:string[]):boolean=>
  Object.keys(o).length===expected.length&&Object.keys(o).every(x=>expected.includes(x));
const ID=/^[a-z][a-z0-9_-]{0,63}$/;
const SOURCE=/^(?:cgx|ui):[a-z0-9_./:-]{1,119}$/;
const safe=(s:unknown,max=112):s is string=>typeof s==="string"&&s.length>0&&s.length<=max
  &&s.trim().length>0&&!/[\u0000-\u001f\u007f<>]/.test(s)
  &&!/(?:javascript:|data:|https?:\/\/|file:\/\/|token=|password=)/i.test(s);
const themes:SpatialTheme[]=["neutral","forest","industrial","cosmos","arcade"];
const lights:SpatialLight[]=["day","dusk","night"];
const kinds:SpatialNodeKind[]=["facet","grex","game","profile","object"];
const workspaces:CgxShellWorkspace[]=["command","activity","objects","sources","filespace"];
const layers:SpatialNodeLayer[]=["ground","overlay"];
const relations:SpatialRelation[]=["related","depends_on","gateway"];

export function compileSpatialHomebase(input: unknown): SpatialHomebase {
  let data=input;
  if(typeof data==="string"){
    if(!data.length||data.length>65536)return fail("SPATIAL_IMPORT_SIZE_HOLD");
    try{data=JSON.parse(data);}catch{return fail("SPATIAL_IMPORT_JSON_HOLD");}
  }
  if(!isObj(data)||!keys(data,["schema","parent","home","rooms","nodes","links","authority"])
    ||data.schema!==CGX_SPATIAL_SCHEMA||data.parent!==CGX_SPATIAL_ROOT
    ||data.home!=="home"||data.authority!=="LOCAL_PRESENTATION_ONLY")
    return fail("SPATIAL_CANONICAL_ROOT_HOLD");
  if(!Array.isArray(data.rooms)||data.rooms.length<1||data.rooms.length>CGX_SPATIAL_MAX_ROOMS
    ||!Array.isArray(data.nodes)||data.nodes.length>CGX_SPATIAL_MAX_NODES
    ||!Array.isArray(data.links)||data.links.length>CGX_SPATIAL_MAX_NODES*2)
    return fail("SPATIAL_FANOUT_HOLD");
  const rooms:SpatialRoom[]=[];const roomIds=new Set<string>();
  for(const raw of data.rooms){
    if(!isObj(raw)||!keys(raw,["id","title","parent","theme","light","climate"])
      ||!safe(raw.id,64)||!ID.test(raw.id)||roomIds.has(raw.id)||!safe(raw.title)
      ||(raw.parent!==null&&(!safe(raw.parent,64)||!ID.test(raw.parent)))
      ||!themes.includes(raw.theme as SpatialTheme)||!lights.includes(raw.light as SpatialLight)
      ||raw.climate!=="VISUAL_PRESET_ONLY")return fail("SPATIAL_ROOM_SHAPE_HOLD");
    roomIds.add(raw.id);rooms.push(raw as unknown as SpatialRoom);
  }
  const roomMap=new Map(rooms.map(r=>[r.id,r]));
  if(!roomMap.has("home")||roomMap.get("home")!.parent!==null
    ||rooms.filter(r=>r.parent===null).length!==1)return fail("SPATIAL_HOME_HOLD");
  for(const room of rooms){
    const path=new Set<string>();let node:SpatialRoom|undefined=room;
    while(node&&node.parent!==null){
      if(path.has(node.id)||path.size>5)return fail("SPATIAL_ROOM_CYCLE_HOLD");
      path.add(node.id);node=roomMap.get(node.parent);
      if(!node)return fail("SPATIAL_ORPHAN_ROOM_HOLD");
    }
    if(node?.id!=="home")return fail("SPATIAL_ROOT_ROOM_HOLD");
  }
  const nodes:SpatialNode[]=[];const nodeIds=new Set<string>();
  const allowedFacets=new Set(["file_space","data_space","social_space","print_space","intelligence_space"]);
  for(const raw of data.nodes){
    if(!isObj(raw)||!keys(raw,["id","label","room","kind","layer","x","y","w","h","facet","workspace","sourceRef","targetRoom"])
      ||!safe(raw.id,64)||!ID.test(raw.id)||nodeIds.has(raw.id)
      ||!safe(raw.label)||!roomMap.has(String(raw.room))||!kinds.includes(raw.kind as SpatialNodeKind)
      ||!layers.includes(raw.layer as SpatialNodeLayer)
      ||![raw.x,raw.y,raw.w,raw.h].every(Number.isInteger)
      ||Number(raw.x)<0||Number(raw.y)<0||Number(raw.w)<1||Number(raw.h)<1
      ||Number(raw.x)+Number(raw.w)>CGX_SPATIAL_COLUMNS||Number(raw.y)+Number(raw.h)>CGX_SPATIAL_ROWS
      ||(raw.facet!==null&&!allowedFacets.has(String(raw.facet)))
      ||(raw.workspace!==null&&!workspaces.includes(raw.workspace as CgxShellWorkspace))
      ||(raw.sourceRef!==null&&(!safe(raw.sourceRef,128)||!SOURCE.test(raw.sourceRef)))
      ||(raw.targetRoom!==null&&(!safe(raw.targetRoom,64)||!roomMap.has(raw.targetRoom as string)))
      ||(raw.targetRoom!==null&&roomMap.get(raw.targetRoom as string)?.parent!==raw.room)
    )return fail("SPATIAL_NODE_SHAPE_OR_SCOPE_HOLD");
    if(raw.kind==="facet"&&(!raw.facet||!raw.workspace))
      return fail("SPATIAL_FACET_WORKSPACE_HOLD");
    nodeIds.add(raw.id);nodes.push(raw as unknown as SpatialNode);
  }
  for(const room of rooms.slice(1)){
    if(!nodes.some(n=>n.room===room.parent&&n.targetRoom===room.id))
      return fail("SPATIAL_ROOM_UNREACHABLE_HOLD");
  }
  const intersects=(a:SpatialNode,b:SpatialNode):boolean=>
    a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h;
  // Same-layer overlap is forbidden. A decorative overlay may intentionally
  // overlap the ground without inheriting its privileges or hit target.
  for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++)
    if(nodes[i].room===nodes[j].room&&nodes[i].layer===nodes[j].layer
      &&intersects(nodes[i],nodes[j]))return fail("SPATIAL_COLLISION_HOLD");
  const links:SpatialLink[]=[];const linkIds=new Set<string>();
  for(const raw of data.links){
    if(!isObj(raw)||!keys(raw,["id","from","to","kind"])
      ||!safe(raw.id,64)||!ID.test(raw.id)||linkIds.has(raw.id)
      ||!nodeIds.has(String(raw.from))||!nodeIds.has(String(raw.to))||raw.from===raw.to
      ||!relations.includes(raw.kind as SpatialRelation))return fail("SPATIAL_LINK_HOLD");
    linkIds.add(raw.id);links.push(raw as unknown as SpatialLink);
  }
  return {
    schema:CGX_SPATIAL_SCHEMA,parent:CGX_SPATIAL_ROOT,home:"home",
    rooms:rooms.map(r=>({...r})),nodes:nodes.map(n=>({...n})),
    links:links.map(l=>({...l})),authority:"LOCAL_PRESENTATION_ONLY"
  };
}
export function spatialSnapshot(layout:SpatialHomebase):string{
  return JSON.stringify(compileSpatialHomebase(layout),null,2);
}
export function placeSpatialNode(layout:SpatialHomebase,id:string,x:number,y:number,w?:number,h?:number):SpatialHomebase{
  const found=layout.nodes.some(n=>n.id===id);if(!found)return fail("SPATIAL_NODE_NOT_FOUND");
  return compileSpatialHomebase({...layout,nodes:layout.nodes.map(n=>n.id===id
    ?{...n,x,y,w:w??n.w,h:h??n.h}:n)});
}
export function styleSpatialRoom(layout:SpatialHomebase,id:string,theme:SpatialTheme,light:SpatialLight):SpatialHomebase{
  if(!layout.rooms.some(r=>r.id===id))return fail("SPATIAL_ROOM_NOT_FOUND");
  return compileSpatialHomebase({...layout,rooms:layout.rooms.map(r=>r.id===id?{...r,theme,light}:r)});
}
function uniqueId(layout:SpatialHomebase,prefix:string):string{
  const ids=new Set([...layout.nodes.map(n=>n.id),...layout.rooms.map(r=>r.id),...layout.links.map(l=>l.id)]);
  for(let i=1;i<=9999;i++){const id=prefix+"-"+i;if(!ids.has(id))return id;}
  return fail("SPATIAL_ID_EXHAUSTED");
}
function firstSpace(layout:SpatialHomebase,room:string,w=3,h=2):{x:number,y:number}{
  for(let y=0;y<=CGX_SPATIAL_ROWS-h;y++)for(let x=0;x<=CGX_SPATIAL_COLUMNS-w;x++){
    if(!layout.nodes.some(n=>n.room===room&&n.layer==="ground"&&x<n.x+n.w&&n.x<x+w&&y<n.y+n.h&&n.y<y+h))return {x,y};
  }
  return fail("SPATIAL_ROOM_FULL_HOLD");
}
/** Creates only a local interface component or navigable child room. */
export function addSpatialObject(layout:SpatialHomebase,room:string,label:string,kind:SpatialNodeKind):SpatialHomebase{
  if(!layout.rooms.some(r=>r.id===room)||!safe(label)||!kinds.includes(kind))return fail("SPATIAL_ADD_SCOPE_HOLD");
  const id=uniqueId(layout,kind);const rect=firstSpace(layout,room);
  if(kind==="grex"||kind==="game"){
    const child=uniqueId(layout,"room");
    const next:SpatialHomebase={...layout,rooms:[...layout.rooms,{
      id:child,title:label,parent:room,theme:kind==="game"?"arcade":"neutral",
      light:"day",climate:"VISUAL_PRESET_ONLY"}],
      nodes:[...layout.nodes,{id,label,room,kind,layer:"ground",...rect,w:3,h:2,
      facet:null,workspace:null,sourceRef:null,targetRoom:child}]};
    return compileSpatialHomebase(next);
  }
  return compileSpatialHomebase({...layout,nodes:[...layout.nodes,{
    id,label,room,kind,layer:"ground",...rect,w:3,h:2,
    facet:null,workspace:kind==="profile"?"activity":null,sourceRef:null,targetRoom:null
  }]});
}
export function linkSpatialObjects(layout:SpatialHomebase,from:string,to:string,kind:SpatialRelation="related"):SpatialHomebase{
  if(!relations.includes(kind))return fail("SPATIAL_LINK_TYPE_HOLD");
  return compileSpatialHomebase({...layout,links:[...layout.links,{id:uniqueId(layout,"link"),from,to,kind}]});
}
/**
 * Seed a home-base representation from the EXISTING five-facet Studio plan.
 * These are UI references, never claims that files or Grex bodies were read.
 */
export function createSpatialHomebase(plan:CgxGeneratedGuiPlan):SpatialHomebase{
  if(plan.parent!==CGX_SPATIAL_ROOT||plan.panels.length<5)
    return fail("SPATIAL_PARENT_OR_FACETS_HOLD");
  const fixed=["file_space","data_space","social_space","print_space","intelligence_space"];
  const used=new Set<string>();
  const nodes:SpatialNode[]=fixed.map((facet,i)=>{
    const p=plan.panels.find(x=>x.facet===facet);
    if(!p||!p.workspace||used.has(p.id))return fail("SPATIAL_SOURCE_FACET_HOLD");
    used.add(p.id);
    return {id:"facet-"+facet,label:p.title,room:"home",kind:"facet",layer:"ground",
      x:1+(i%4)*4,y:1+Math.floor(i/4)*4,w:3,h:2,facet,workspace:p.workspace,
      sourceRef:"ui:"+p.id,targetRoom:null};
  });
  nodes.push(
    {id:"profile-base",label:"ProfileSpace",room:"home",kind:"profile",layer:"ground",x:5,y:5,w:3,h:2,facet:null,workspace:"activity",sourceRef:null,targetRoom:null},
    {id:"grex-eco",label:"Eco Grex",room:"home",kind:"grex",layer:"ground",x:9,y:5,w:3,h:2,facet:null,workspace:null,sourceRef:null,targetRoom:"eco"},
    {id:"grex-romer",label:"Römer Grex",room:"home",kind:"grex",layer:"ground",x:13,y:5,w:3,h:2,facet:null,workspace:null,sourceRef:null,targetRoom:"romer"},
    {id:"game-hub",label:"Game gateways",room:"home",kind:"game",layer:"ground",x:9,y:9,w:3,h:2,facet:null,workspace:null,sourceRef:null,targetRoom:"games"},
    {id:"eco-objects",label:"Ecological objects",room:"eco",kind:"object",layer:"ground",x:2,y:3,w:4,h:2,facet:null,workspace:"objects",sourceRef:null,targetRoom:null},
    {id:"eco-evidence",label:"Environmental evidence",room:"eco",kind:"object",layer:"ground",x:9,y:3,w:4,h:2,facet:null,workspace:"sources",sourceRef:null,targetRoom:null},
    {id:"romer-systems",label:"System architecture",room:"romer",kind:"object",layer:"ground",x:2,y:3,w:4,h:2,facet:null,workspace:"objects",sourceRef:null,targetRoom:null},
    {id:"romer-files",label:"FileSpace references",room:"romer",kind:"object",layer:"ground",x:9,y:3,w:4,h:2,facet:null,workspace:"filespace",sourceRef:null,targetRoom:null},
    {id:"game-worlds",label:"World collection",room:"games",kind:"object",layer:"ground",x:3,y:4,w:4,h:2,facet:null,workspace:null,sourceRef:null,targetRoom:null},
    {id:"game-profiles",label:"Player profiles",room:"games",kind:"profile",layer:"ground",x:10,y:4,w:4,h:2,facet:null,workspace:"activity",sourceRef:null,targetRoom:null},
  );
  return compileSpatialHomebase({schema:CGX_SPATIAL_SCHEMA,parent:CGX_SPATIAL_ROOT,
    home:"home",rooms:[
      {id:"home",title:"My UniSpace home",parent:null,theme:"neutral",light:"day",climate:"VISUAL_PRESET_ONLY"},
      {id:"eco",title:"Eco Grex",parent:"home",theme:"forest",light:"day",climate:"VISUAL_PRESET_ONLY"},
      {id:"romer",title:"Römer Industries",parent:"home",theme:"industrial",light:"dusk",climate:"VISUAL_PRESET_ONLY"},
      {id:"games",title:"Game gateways",parent:"home",theme:"arcade",light:"night",climate:"VISUAL_PRESET_ONLY"}
    ],nodes,links:[
      {id:"relation-files-data",from:"facet-file_space",to:"facet-data_space",kind:"related"},
      {id:"relation-eco-data",from:"grex-eco",to:"facet-data_space",kind:"depends_on"},
      {id:"relation-world-profile",from:"game-hub",to:"profile-base",kind:"related"},
    ],authority:"LOCAL_PRESENTATION_ONLY"});
}
