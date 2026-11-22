import { describe, expect, it } from "vitest";
import source from "../../../docs/architecture/CGX_UNISPACE_GO_FIVE_FACET_INTERFACE_20261122.json?raw";
import {compileCgxGeneratedGui} from "./cgxGeneratedGui";
import {
  CGX_SPATIAL_SCHEMA, CGX_SPATIAL_ROOT, CGX_SPATIAL_COLUMNS, CGX_SPATIAL_ROWS,
  compileSpatialHomebase,createSpatialHomebase,spatialSnapshot,
  placeSpatialNode,styleSpatialRoom,addSpatialObject,linkSpatialObjects,
  SpatialHold
} from "./cgxSpatialHomebase";

const seed=()=>createSpatialHomebase(compileCgxGeneratedGui(source));
const clone=()=>JSON.parse(spatialSnapshot(seed()));
const deny=(change:(v:any)=>void,code?:string)=>{
  const v=clone();change(v);
  expect(()=>compileSpatialHomebase(v)).toThrow(SpatialHold);
  if(code)expect(()=>compileSpatialHomebase(v)).toThrow(code);
};
describe("CGX single-root top-down home-base geometry and microclimate views",()=>{
  it("projects only existing five qualified facets into a single home room",()=>{
    const v=seed();expect(v.parent).toBe(CGX_SPATIAL_ROOT);
    expect(v.schema).toBe(CGX_SPATIAL_SCHEMA);
    expect(v.nodes.filter(n=>n.kind==="facet").map(n=>n.facet)).toEqual([
      "file_space","data_space","social_space","print_space","intelligence_space"]);
    expect(v.authority).toBe("LOCAL_PRESENTATION_ONLY");
  });
  it("has home, Eco, Römer, and game-world rooms with valid portal lineage",()=>{
    const v=seed();expect(v.rooms.map(x=>x.id)).toEqual(["home","eco","romer","games","desporte","raphael","achilles","neo"]);
    expect(v.nodes.find(x=>x.id==="game-hub")?.targetRoom).toBe("games");
    expect(v.nodes.find(x=>x.id==="grex-romer")?.targetRoom).toBe("romer");
  });
  it("makes De Sporte, Raphael, Achilles and Neo navigable rooms without host state invention",()=>{
    const p=seed();
    for(const id of ["desporte","raphael","achilles","neo"]){
      expect(p.rooms.find(r=>r.id===id)?.parent).toBe("home");
      expect(p.nodes.some(n=>n.room==="home"&&n.targetRoom===id)).toBe(true);
    }
    expect(p.nodes.find(n=>n.id==="desporte-state")?.workspace).toBe("sources");
    expect(p.nodes.find(n=>n.id==="neo-command")?.workspace).toBe("command");
    expect(p.nodes.find(n=>n.id==="achilles-oversight")?.workspace).toBeNull();
  });
  it("microclimates are visual presets, not measured conditions",()=>{
    const v=seed();expect(v.rooms.every(x=>x.climate==="VISUAL_PRESET_ONLY")).toBe(true);
    expect(JSON.stringify(v)).not.toMatch(/temperature_c|humidity_pct|measured_at|weather_reading/);
  });
  it("bounded source snapshot round trips byte structurally",()=>{
    const v=seed();expect(compileSpatialHomebase(spatialSnapshot(v))).toEqual(v);
  });
  it("does not mutate original when moving or styling",()=>{
    const v=seed(),n=placeSpatialNode(v,"grex-eco",10,6),s=styleSpatialRoom(n,"eco","cosmos","night");
    expect(v.nodes.find(x=>x.id==="grex-eco")?.x).toBe(9);
    expect(n.nodes.find(x=>x.id==="grex-eco")?.x).toBe(10);
    expect(v.rooms.find(x=>x.id==="eco")?.theme).toBe("forest");
    expect(s.rooms.find(x=>x.id==="eco")?.theme).toBe("cosmos");
  });
  it("blocks collision on same layer",()=>{
    expect(()=>placeSpatialNode(seed(),"grex-eco",13,5)).toThrow("SPATIAL_COLLISION_HOLD");
  });
  it("blocks out-of-grid bounds including negative and fractional",()=>{
    for(const x of [-1,21,0.5])expect(()=>placeSpatialNode(seed(),"grex-eco",x,5)).toThrow(SpatialHold);
    expect(()=>placeSpatialNode(seed(),"grex-eco",18,5)).toThrow("SPATIAL_NODE_SHAPE_OR_SCOPE_HOLD");
  });
  it("supports deliberate ground/overlay overlap without native right",()=>{
    const v=clone(),n={...v.nodes[0],id:"annotation-overlay",kind:"object",layer:"overlay",facet:null,workspace:null,sourceRef:null};
    v.nodes.push(n);const p=compileSpatialHomebase(v);
    expect(p.nodes.find(x=>x.id==="annotation-overlay")?.layer).toBe("overlay");
    expect(p.authority).toBe("LOCAL_PRESENTATION_ONLY");
  });
  it("rejects unintended same-overlay overlap",()=>{
    deny(x=>{const n=x.nodes[0];x.nodes.push({...n,id:"overlap",kind:"object",facet:null,workspace:null,sourceRef:null});},"SPATIAL_COLLISION_HOLD");
  });
  it("rejects injected or external URLs in labels and refs",()=>{
    deny(x=>{x.nodes[0].label="<img onerror=alert(1)>";},"SPATIAL_NODE_SHAPE_OR_SCOPE_HOLD");
    deny(x=>{x.nodes[0].sourceRef="https://external.invalid/token";},"SPATIAL_NODE_SHAPE_OR_SCOPE_HOLD");
  });
  it("rejects replacing canonical parent and authority",()=>{
    deny(x=>{x.parent="cgx:root:game-world";},"SPATIAL_CANONICAL_ROOT_HOLD");
    deny(x=>{x.authority="NATIVE_ADMITTED";},"SPATIAL_CANONICAL_ROOT_HOLD");
  });
  it("rejects injected runtime control or object-body property",()=>{
    deny(x=>{x.nodes[0].onClick="publish";},"SPATIAL_NODE_SHAPE_OR_SCOPE_HOLD");
    deny(x=>{x.nodes[0].privateText="source message";},"SPATIAL_NODE_SHAPE_OR_SCOPE_HOLD");
  });
  it("cannot substitute a second home or orphan rooms",()=>{
    deny(x=>{x.rooms.push({...x.rooms[0],id:"home-2",parent:null});},"SPATIAL_HOME_HOLD");
    deny(x=>{x.rooms[1].parent="missing";},"SPATIAL_ORPHAN_ROOM_HOLD");
  });
  it("holds cyclic and unreachable portal topology",()=>{
    deny(x=>{x.rooms[0].parent="eco";},"SPATIAL_HOME_HOLD");
    deny(x=>{x.nodes.find((y:any)=>y.id==="grex-eco").targetRoom=null;},"SPATIAL_ROOM_UNREACHABLE_HOLD");
  });
  it("holds forged link references and duplicate link IDs",()=>{
    deny(x=>{x.links[0].to="phantom";},"SPATIAL_LINK_HOLD");
    deny(x=>{x.links.push({...x.links[0]});},"SPATIAL_LINK_HOLD");
  });
  it("cross-room typed relationships support nonlinear navigation",()=>{
    const v=linkSpatialObjects(seed(),"eco-evidence","romer-systems","related");
    expect(v.links[v.links.length-1]).toMatchObject({from:"eco-evidence",to:"romer-systems"});
  });
  it("adds a new Grex as a traversable child room without new CGX root",()=>{
    const v=addSpatialObject(seed(),"home","Raphael Grex","grex");
    const node=v.nodes.find(x=>x.label==="Raphael Grex");
    expect(node?.targetRoom).toBeTruthy();
    expect(v.rooms.find(r=>r.id===node?.targetRoom)?.parent).toBe("home");
    expect(v.parent).toBe(CGX_SPATIAL_ROOT);
  });
  it("adds game gateways with reversible local layout only",()=>{
    const v=addSpatialObject(seed(),"games","Fictional world","game");
    expect(v.nodes.find(n=>n.label==="Fictional world")?.kind).toBe("game");
    expect(v.rooms.find(r=>r.title==="Fictional world")?.climate).toBe("VISUAL_PRESET_ONLY");
  });
  it("does not silently convert an object into a minted source identity",()=>{
    const v=addSpatialObject(seed(),"home","My 2D component","object");
    const n=v.nodes.find(x=>x.label==="My 2D component");
    expect(n?.sourceRef).toBeNull();
    expect(n?.workspace).toBeNull();
  });
  it("keeps semantic reference moves separate from source mutation",()=>{
    const v=seed(),m=placeSpatialNode(v,"facet-file_space",2,1);
    expect(m.nodes.find(n=>n.id==="facet-file_space")?.sourceRef).toBe("ui:view-0");
    expect(m.nodes.find(n=>n.id==="facet-file_space")?.facet).toBe("file_space");
    expect(v.nodes.find(n=>n.id==="facet-file_space")?.x).toBe(1);
  });
  it("resizing respects grid bounds and same-layer collisions",()=>{
    expect(()=>placeSpatialNode(seed(),"facet-file_space",1,1,20,2)).toThrow(SpatialHold);
    expect(placeSpatialNode(seed(),"facet-file_space",1,1,2,2).nodes[0].w).toBe(2);
  });
  it("strictly limits imported data and arrays",()=>{
    expect(()=>compileSpatialHomebase("x".repeat(65537))).toThrow("SPATIAL_IMPORT_SIZE_HOLD");
    expect(()=>compileSpatialHomebase("{broken")).toThrow("SPATIAL_IMPORT_JSON_HOLD");
    deny(x=>{x.nodes.push(...Array.from({length:101},()=>x.nodes[0]));},"SPATIAL_FANOUT_HOLD");
  });
  it("rejects fake calibration and physical climate fields",()=>{
    deny(x=>{x.rooms[1].temperature_c=18;},"SPATIAL_ROOM_SHAPE_HOLD");
    deny(x=>{x.rooms[1].climate="MEASURED";},"SPATIAL_ROOM_SHAPE_HOLD");
  });
  it("only allows in-grid nodes and all objects are bounded",()=>{
    const v=seed();
    expect(v.nodes.every(n=>n.x>=0&&n.y>=0&&n.x+n.w<=CGX_SPATIAL_COLUMNS&&n.y+n.h<=CGX_SPATIAL_ROWS)).toBe(true);
  });
  it("remains interoperable with existing generated facet workspace names",()=>{
    const v=seed();
    expect(v.nodes.filter(n=>n.kind==="facet").map(n=>n.workspace)).toEqual([
      "filespace","sources","activity","objects","command"]);
  });
});
