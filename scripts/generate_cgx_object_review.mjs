import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const repo = path.resolve(import.meta.dirname, "..");
const modelDir = path.join(repo, "assets", "models");
const publicDir = path.join(repo, "apps", "lightspeed-go", "public");
const outDir = path.join(publicDir, "review", "renders");
const meshDir = path.join(publicDir, "review", "mesh");
const statsPath = path.join(publicDir, "data", "cgx_object_mesh_stats.json");
const cataloguePath = path.join(publicDir, "data", "cgx_object_review_catalogue.json");
fs.mkdirSync(outDir, { recursive: true });
fs.mkdirSync(meshDir, { recursive: true });

const metadata = {
  embedded_bio_blocks: ["Embedded bio blocks", "Eco-Grex / multifunctional bio-block reference", "T2"],
  free_flow_batteries: ["Free Flow batteries", "Energy-storage architecture reference", "T2"],
  free_flow_capacitors: ["Free Flow capacitors", "Electrostatic energy architecture reference", "T2"],
  free_flow_solenoid_stack: ["Free Flow solenoid stack", "Inductive / field-stack architecture reference", "T2"],
  intersol: ["InterSol", "Interplanetary relay / repair architecture reference", "T3"],
  luke_family: ["Luke family", "Capture / braking family reference", "T3"],
  m1_elevated_bypass: ["M1 elevated bypass", "Civil corridor reference geometry", "T4"],
  maglev_luke_iv: ["Luke IV maglev catch", "Terrestrial catch / maglev reference", "T3"],
  mark_1p: ["Mark 1P", "Proof-of-concept Mark reference", "T3"],
  mark_i: ["Mark I", "Mark family reference", "T3"],
  mark_iii: ["Mark III", "Modular mission-unit reference", "T3"],
  rfs_emff: ["RFS / EMFF", "Field / propulsion architecture reference", "T2"],
  romer_spaceport: ["Römer Spaceport", "Facility / operations envelope reference", "T4"],
  second_cycle: ["Second Cycle", "Historical corpus reference mesh", "T3"],
  solar_hull: ["Solar Hull / Mark V", "Energy-surface / hull reference", "T3"],
  watchtower: ["WatchTower", "Observation / review tower reference", "T4"],
};

const palette = {
  background: "#071011",
  panel: "#0f1b1c",
  panelAlt: "#142426",
  text: "#f2ede7",
  muted: "#aab9b8",
  line: "#294043",
  teal: "#55d6cf",
  gold: "#c8a458",
  green: "#76d39b",
  red: "#e27e7e",
};

const esc = (s) => String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
const clamp = (v, lo=0, hi=1) => Math.max(lo, Math.min(hi, v));
const mix = (a,b,t) => a.map((v,i)=>Math.round(v+(b[i]-v)*t));
const rgb = (c) => `rgb(${c[0]},${c[1]},${c[2]})`;
const sha256 = (text) => crypto.createHash("sha256").update(text).digest("hex");

const parseObj = (text) => {
  const vertices = [], faces = [];
  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith("v ")) {
      const q=line.trim().split(/\s+/);
      if(q.length>=4) vertices.push([Number(q[1]),Number(q[2]),Number(q[3])]);
    } else if (line.startsWith("f ")) {
      const ids=line.trim().split(/\s+/).slice(1).map((x)=>Number.parseInt(x.split("/")[0],10)-1).filter(Number.isFinite);
      for(let i=1;i<ids.length-1;i++) faces.push([ids[0],ids[i],ids[i+1]]);
    }
  }
  return { vertices, faces };
};

const rotate=(p,elev,azim)=>{
  const e=elev*Math.PI/180,a=azim*Math.PI/180;
  const x=p[0]*Math.cos(a)-p[1]*Math.sin(a), y=p[0]*Math.sin(a)+p[1]*Math.cos(a), z=p[2];
  return [x,y*Math.cos(e)-z*Math.sin(e),y*Math.sin(e)+z*Math.cos(e)];
};
const sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const norm=(a)=>Math.hypot(a[0],a[1],a[2])||1;
const unit=(a)=>{const n=norm(a);return[a[0]/n,a[1]/n,a[2]/n];};
const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];

const boundsFor=(vertices)=>{
  const min=[0,1,2].map((i)=>Math.min(...vertices.map((p)=>p[i])));
  const max=[0,1,2].map((i)=>Math.max(...vertices.map((p)=>p[i])));
  const extents=max.map((v,i)=>v-min[i]);
  return {min,max,extents};
};

const renderView=(vertices,faces,rect,elev,azim,label)=>{
  const [x0,y0,x1,y1]=rect, rv=vertices.map((p)=>rotate(p,elev,azim));
  let minx=Infinity,maxx=-Infinity,miny=Infinity,maxy=-Infinity;
  for(const p of rv){minx=Math.min(minx,p[0]);maxx=Math.max(maxx,p[0]);miny=Math.min(miny,p[1]);maxy=Math.max(maxy,p[1]);}
  const dx=Math.max(maxx-minx,1e-9),dy=Math.max(maxy-miny,1e-9),scale=Math.min((x1-x0-110)/dx,(y1-y0-110)/dy);
  const cx=(x0+x1)/2,cy=(y0+y1)/2,pts=rv.map((p)=>[cx+(p[0]-(minx+maxx)/2)*scale,cy-(p[1]-(miny+maxy)/2)*scale,p[2]]);
  const step=Math.max(1,Math.ceil(faces.length/1200)), ordered=[];
  for(let i=0;i<faces.length;i+=step){const t=faces[i];ordered.push([(pts[t[0]][2]+pts[t[1]][2]+pts[t[2]][2])/3,t]);}
  ordered.sort((a,b)=>a[0]-b[0]);
  let body=`<rect x="${x0}" y="${y0}" width="${x1-x0}" height="${y1-y0}" rx="18" fill="${palette.panel}" stroke="${palette.line}" stroke-width="2"/><text x="${x0+20}" y="${y0+34}" fill="${palette.muted}" font-family="Segoe UI,Arial" font-size="22" font-weight="700">${label.toUpperCase()}</text>`;
  for(const [,t] of ordered){const A=pts[t[0]],B=pts[t[1]],C=pts[t[2]];body+=`<polygon points="${A[0].toFixed(1)},${A[1].toFixed(1)} ${B[0].toFixed(1)},${B[1].toFixed(1)} ${C[0].toFixed(1)},${C[1].toFixed(1)}" fill="${palette.panelAlt}" stroke="${palette.teal}" stroke-width="1.15" stroke-opacity=".72"/>`;}
  return body;
};

const renderEngineeringPlate=(stem,label,role,vertices,faces,sourceHash)=>{
  const {extents}=boundsFor(vertices);
  const rects=[[80,230,1880,1110],[1960,230,3760,1110],[80,1170,1880,2050],[1960,1170,3760,2050]],views=[[24,-42,"perspective"],[90,-90,"top"],[0,-90,"front"],[0,0,"side"]];
  let body=""; for(let i=0;i<4;i++) body+=renderView(vertices,faces,rects[i],views[i][0],views[i][1],views[i][2]);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160" viewBox="0 0 3840 2160"><rect width="3840" height="2160" fill="${palette.background}"/><text x="80" y="100" fill="${palette.text}" font-family="Segoe UI,Arial" font-size="56" font-weight="700">${esc(label)}</text><text x="82" y="152" fill="${palette.muted}" font-family="Segoe UI,Arial" font-size="24">${esc(role)} · source mesh assets/models/${stem}.obj</text><text x="3760" y="102" text-anchor="end" fill="${palette.teal}" font-family="Segoe UI,Arial" font-size="23" font-weight="700">CORPUS SOURCE MESH · REVIEW ONLY</text><line x1="80" y1="185" x2="3760" y2="185" stroke="${palette.line}" stroke-width="2"/>${body}<text x="82" y="2125" fill="${palette.muted}" font-family="Segoe UI,Arial" font-size="20">${vertices.length} vertices · ${faces.length} triangles · extents ${extents.map((v)=>v.toPrecision(5)).join(" × ")} model units · source SHA-256 ${sourceHash.slice(0,16)}… · no material/structural/as-built inference</text></svg>`;
};

const heroFaceData=(vertices,faces)=>{
  const rv=vertices.map((p)=>rotate(p,22,-38));
  const key=unit([-0.45,-0.35,0.82]), fill=unit([0.6,-0.2,0.5]), rim=unit([0.25,0.8,0.5]);
  const rows=[];
  for(const t of faces){
    const A=rv[t[0]],B=rv[t[1]],C=rv[t[2]];
    const n=unit(cross(sub(B,A),sub(C,A)));
    const z=(A[2]+B[2]+C[2])/3;
    let intensity=.16 + .58*Math.abs(dot(n,key)) + .16*Math.max(0,Math.abs(dot(n,fill))) + .1*Math.max(0,Math.abs(dot(n,rim)));
    intensity=clamp(intensity,.12,1);
    rows.push({t,z,intensity});
  }
  rows.sort((a,b)=>a.z-b.z);
  return {rv,rows};
};

const renderHero=(stem,label,role,tier,vertices,faces,sourceHash)=>{
  const {rv,rows}=heroFaceData(vertices,faces);
  let minx=Infinity,maxx=-Infinity,miny=Infinity,maxy=-Infinity,minz=Infinity,maxz=-Infinity;
  for(const p of rv){minx=Math.min(minx,p[0]);maxx=Math.max(maxx,p[0]);miny=Math.min(miny,p[1]);maxy=Math.max(maxy,p[1]);minz=Math.min(minz,p[2]);maxz=Math.max(maxz,p[2]);}
  const dx=Math.max(maxx-minx,1e-9),dy=Math.max(maxy-miny,1e-9),dz=Math.max(maxz-minz,1e-9);
  const cx=2160,cy=1120,boxW=2750,boxH=1530,scale=Math.min(boxW/dx,boxH/dy);
  const depth=Math.max(dx,dy,dz),cam=depth*7.5;
  const pts=rv.map((p)=>{
    const zc=p[2]-(minz+maxz)/2;
    const persp=cam/(cam-zc);
    return [cx+(p[0]-(minx+maxx)/2)*scale*persp,cy-(p[1]-(miny+maxy)/2)*scale*persp,p[2]];
  });
  const dark=[17,38,41],light=[92,222,214],gold=[200,164,88];
  const step=Math.max(1,Math.ceil(rows.length/6000));
  let mesh="";
  for(let i=0;i<rows.length;i+=step){
    const {t,intensity}=rows[i],A=pts[t[0]],B=pts[t[1]],C=pts[t[2]];
    const base=mix(dark,light,intensity);
    const accent=intensity>.82?mix(base,gold,.14):base;
    mesh+=`<polygon points="${A[0].toFixed(1)},${A[1].toFixed(1)} ${B[0].toFixed(1)},${B[1].toFixed(1)} ${C[0].toFixed(1)},${C[1].toFixed(1)}" fill="${rgb(accent)}" stroke="#78e3dd" stroke-opacity=".18" stroke-width=".7"/>`;
  }
  const accent=tier==="T4"?palette.gold:tier==="T3"?palette.green:palette.teal;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160" viewBox="0 0 3840 2160">
  <defs>
    <radialGradient id="bg" cx="62%" cy="45%" r="72%"><stop offset="0%" stop-color="#173033"/><stop offset="52%" stop-color="#0c191b"/><stop offset="100%" stop-color="#050a0b"/></radialGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="30"/></filter>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="14" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    <pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse"><path d="M80 0H0V80" fill="none" stroke="#294043" stroke-width="1" opacity=".22"/></pattern>
  </defs>
  <rect width="3840" height="2160" fill="url(#bg)"/><rect width="3840" height="2160" fill="url(#grid)" opacity=".3"/>
  <ellipse cx="2160" cy="1790" rx="1050" ry="150" fill="#000" opacity=".42" filter="url(#shadow)"/>
  <g filter="url(#glow)">${mesh}</g>
  <rect x="96" y="92" width="10" height="170" rx="5" fill="${accent}"/>
  <text x="142" y="142" fill="${palette.muted}" font-family="Segoe UI,Arial" font-size="25" font-weight="700" letter-spacing="4">RÖMER / COGNIGREX · ${tier}</text>
  <text x="142" y="212" fill="${palette.text}" font-family="Segoe UI,Arial" font-size="68" font-weight="700">${esc(label)}</text>
  <text x="145" y="260" fill="${palette.muted}" font-family="Segoe UI,Arial" font-size="26">${esc(role)}</text>
  <g transform="translate(2950 110)"><rect width="790" height="94" rx="47" fill="#0f1b1c" stroke="${accent}" stroke-width="2"/><text x="395" y="59" text-anchor="middle" fill="${accent}" font-family="Segoe UI,Arial" font-size="23" font-weight="700">SOURCE-GEOMETRY HERO · REVIEW ONLY</text></g>
  <text x="142" y="2030" fill="${palette.muted}" font-family="Segoe UI,Arial" font-size="21">assets/models/${stem}.obj · SHA-256 ${sourceHash.slice(0,24)}… · aesthetic lighting is display-only; material finish and performance are not inferred</text>
  <text x="3698" y="2030" text-anchor="end" fill="${palette.muted}" font-family="Segoe UI,Arial" font-size="21">3840 × 2160 · source-faithful silhouette / topology</text>
  </svg>`;
};

const stats={schema:"CGX-OBJECT-MESH-STATS/0.2",generated_by:"scripts/generate_cgx_object_review.mjs",records:[]};
for(const [stem,[label,role,tier]] of Object.entries(metadata)){
  const source=path.join(modelDir,stem+".obj");
  if(!fs.existsSync(source)) continue;
  const sourceText=fs.readFileSync(source,"utf8");
  const sourceHash=sha256(sourceText);
  const {vertices,faces}=parseObj(sourceText);
  const bounds=boundsFor(vertices);
  const plate=renderEngineeringPlate(stem,label,role,vertices,faces,sourceHash);
  const hero=renderHero(stem,label,role,tier,vertices,faces,sourceHash);
  const platePath=path.join(outDir,stem+"_review.svg");
  const heroPath=path.join(outDir,stem+"_hero.svg");
  const meshPath=path.join(meshDir,stem+".json");
  fs.writeFileSync(platePath,plate);
  fs.writeFileSync(heroPath,hero);
  const meshPayload={
    schema:"CGX-MESH-REVIEW-GEOMETRY/0.1",
    id:stem,
    source:path.relative(repo,source).replaceAll("\\","/"),
    source_sha256:sourceHash,
    state:"DERIVED_FROM_SOURCE_MESH / REVIEW_ONLY",
    units:"SOURCE MODEL UNITS / NOT AUTOMATICALLY RELEASED PHYSICAL DIMENSIONS",
    bounds,
    vertices:vertices.map((v)=>v.map((n)=>Number(n.toFixed(7)))),
    faces,
  };
  fs.writeFileSync(meshPath,JSON.stringify(meshPayload));
  stats.records.push({
    id:stem,
    source:path.relative(repo,source).replaceAll("\\","/"),
    source_sha256:sourceHash,
    render:path.relative(repo,platePath).replaceAll("\\","/"),
    hero_render:path.relative(repo,heroPath).replaceAll("\\","/"),
    mesh_data:path.relative(repo,meshPath).replaceAll("\\","/"),
    vertices:vertices.length,
    faces:faces.length,
    extents:bounds.extents,
  });
}
fs.writeFileSync(statsPath,JSON.stringify(stats,null,2)+"\n");

if(fs.existsSync(cataloguePath)){
  const catalogue=JSON.parse(fs.readFileSync(cataloguePath,"utf8"));
  catalogue.schema="CGX-OBJECT-REVIEW-CATALOGUE/0.2";
  catalogue.generated_from_git="0884a000e25a7b002c67d863fa4825a143fb0b3a";
  catalogue.status="INTERNAL_REVIEW / 4K_VECTOR_HERO + ENGINEERING_PLATE + INTERACTIVE_SOURCE_MESH / PHYSICAL_NOT_RUN";
  catalogue.visual_system={
    ...catalogue.visual_system,
    brand_lockup:"RÖMER / COGNIGREX text lockup only; no invented emblem",
    hero_render:"3840×2160 resolution-independent SVG derived from source mesh with display-only three-point technical lighting",
    interactive_mesh:"source-hashed derived geometry payload for local orbit review; no geometry edits",
    material_policy:"display shading only; never infer actual finish/material from visual treatment",
    composition:"single hero focal object, 6–8% safety margin, dark technical field, restrained teal/gold/green accents by tier",
  };
  catalogue.coverage={...catalogue.coverage,source_mesh_interactive_views:stats.records.length,source_mesh_4k_hero_views:stats.records.length};
  const byId=new Map(stats.records.map((r)=>[r.id,r]));
  for(const item of catalogue.macro_review_objects||[]){
    const stem=String(item.source||"").split("/").at(-1)?.replace(/\.obj$/,"");
    const row=byId.get(stem);
    if(!row) continue;
    item.hero_render="/review/renders/"+stem+"_hero.svg";
    item.mesh_data="/review/mesh/"+stem+".json";
    item.source_sha256=row.source_sha256;
    item.render_state="SOURCE_HASHED / 4K HERO + FOUR-VIEW PLATE + INTERACTIVE ORBIT";
  }
  catalogue.pending_owner_layers=[
    "UTP-141 / BUILD-074 — 16 interface operators; provider CI pass, draft engineering lane remains independent",
    "UTP-142 / BUILD-075 — witness/evidence kernel owner contract; physical witnesses NOT_RUN",
    "UTP-143 / BUILD-076 — 17 functional voxel regions; PR #155 draft lane CI pass",
    "UTP-144 / BUILD-077 — SG-0/1/N seed-field stack matrix; PR #155 draft lane CI pass",
    "UTP-145 / BUILD-078 — first P2 R/C/L witness packet; pre-run gates G0/G1/G2 remain evidence-bound"
  ];
  fs.writeFileSync(cataloguePath,JSON.stringify(catalogue,null,2)+"\n");
}
console.log(`Rendered ${stats.records.length} source meshes to 4K hero + engineering SVGs and interactive mesh payloads.`);
