import fs from "node:fs";
import path from "node:path";

const repo = path.resolve(import.meta.dirname, "..");
const modelDir = path.join(repo, "assets", "models");
const outDir = path.join(repo, "apps", "lightspeed-go", "public", "review", "renders");
const statsPath = path.join(repo, "apps", "lightspeed-go", "public", "data", "cgx_object_mesh_stats.json");
fs.mkdirSync(outDir, { recursive: true });

const metadata = {
  embedded_bio_blocks: ["Embedded bio blocks", "Eco-Grex / multifunctional bio-block reference"],
  free_flow_batteries: ["Free Flow batteries", "Energy-storage architecture reference"],
  free_flow_capacitors: ["Free Flow capacitors", "Electrostatic energy architecture reference"],
  free_flow_solenoid_stack: ["Free Flow solenoid stack", "Inductive / field-stack architecture reference"],
  intersol: ["InterSol", "Interplanetary relay / repair architecture reference"],
  luke_family: ["Luke family", "Capture / braking family reference"],
  m1_elevated_bypass: ["M1 elevated bypass", "Civil corridor reference geometry"],
  maglev_luke_iv: ["Luke IV maglev catch", "Terrestrial catch / maglev reference"],
  mark_1p: ["Mark 1P", "Proof-of-concept Mark reference"],
  mark_i: ["Mark I", "Mark family reference"],
  mark_iii: ["Mark III", "Modular mission-unit reference"],
  rfs_emff: ["RFS / EMFF", "Field / propulsion architecture reference"],
  romer_spaceport: ["Römer Spaceport", "Facility / operations envelope reference"],
  second_cycle: ["Second Cycle", "Historical corpus reference mesh"],
  solar_hull: ["Solar Hull / Mark V", "Energy-surface / hull reference"],
  watchtower: ["WatchTower", "Observation / review tower reference"],
};

const esc = (s) => String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
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
const renderView=(vertices,faces,rect,elev,azim,label)=>{
  const [x0,y0,x1,y1]=rect, rv=vertices.map((p)=>rotate(p,elev,azim));
  let minx=Infinity,maxx=-Infinity,miny=Infinity,maxy=-Infinity;
  for(const p of rv){minx=Math.min(minx,p[0]);maxx=Math.max(maxx,p[0]);miny=Math.min(miny,p[1]);maxy=Math.max(maxy,p[1]);}
  const dx=Math.max(maxx-minx,1e-9),dy=Math.max(maxy-miny,1e-9),scale=Math.min((x1-x0-110)/dx,(y1-y0-110)/dy);
  const cx=(x0+x1)/2,cy=(y0+y1)/2,pts=rv.map((p)=>[cx+(p[0]-(minx+maxx)/2)*scale,cy-(p[1]-(miny+maxy)/2)*scale,p[2]]);
  const step=Math.max(1,Math.ceil(faces.length/1200)), ordered=[];
  for(let i=0;i<faces.length;i+=step){const t=faces[i];ordered.push([(pts[t[0]][2]+pts[t[1]][2]+pts[t[2]][2])/3,t]);}
  ordered.sort((a,b)=>a[0]-b[0]);
  let body=`<rect x="${x0}" y="${y0}" width="${x1-x0}" height="${y1-y0}" rx="18" fill="#0f1b1c" stroke="#294043" stroke-width="2"/><text x="${x0+20}" y="${y0+34}" fill="#aab9b8" font-family="Segoe UI,Arial" font-size="22" font-weight="700">${label.toUpperCase()}</text>`;
  for(const [,t] of ordered){const A=pts[t[0]],B=pts[t[1]],C=pts[t[2]];body+=`<polygon points="${A[0].toFixed(1)},${A[1].toFixed(1)} ${B[0].toFixed(1)},${B[1].toFixed(1)} ${C[0].toFixed(1)},${C[1].toFixed(1)}" fill="#142426" stroke="#55d6cf" stroke-width="1.15" stroke-opacity=".72"/>`;}
  return body;
};
const renderPlate=(stem,label,role,vertices,faces)=>{
  const mins=[0,1,2].map((i)=>Math.min(...vertices.map((p)=>p[i]))),maxs=[0,1,2].map((i)=>Math.max(...vertices.map((p)=>p[i]))),extents=maxs.map((v,i)=>v-mins[i]);
  const rects=[[80,230,1880,1110],[1960,230,3760,1110],[80,1170,1880,2050],[1960,1170,3760,2050]],views=[[24,-42,"perspective"],[90,-90,"top"],[0,-90,"front"],[0,0,"side"]];
  let body=""; for(let i=0;i<4;i++) body+=renderView(vertices,faces,rects[i],views[i][0],views[i][1],views[i][2]);
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160" viewBox="0 0 3840 2160"><rect width="3840" height="2160" fill="#071011"/><text x="80" y="100" fill="#f2ede7" font-family="Segoe UI,Arial" font-size="56" font-weight="700">${esc(label)}</text><text x="82" y="152" fill="#aab9b8" font-family="Segoe UI,Arial" font-size="24">${esc(role)} · source mesh assets/models/${stem}.obj</text><text x="3760" y="102" text-anchor="end" fill="#55d6cf" font-family="Segoe UI,Arial" font-size="23" font-weight="700">CORPUS SOURCE MESH · REVIEW ONLY</text><line x1="80" y1="185" x2="3760" y2="185" stroke="#294043" stroke-width="2"/>${body}<text x="82" y="2125" fill="#aab9b8" font-family="Segoe UI,Arial" font-size="20">${vertices.length} vertices · ${faces.length} triangles · extents ${extents.map((v)=>v.toPrecision(5)).join(" × ")} model units · no material/structural/as-built inference</text></svg>`;
  return { svg, stats:{vertices:vertices.length,faces:faces.length,extents} };
};

const stats={schema:"CGX-OBJECT-MESH-STATS/0.1",generated_by:"scripts/generate_cgx_object_review.mjs",records:[]};
for(const [stem,[label,role]] of Object.entries(metadata)){
  const source=path.join(modelDir,stem+".obj");
  if(!fs.existsSync(source)) continue;
  const {vertices,faces}=parseObj(fs.readFileSync(source,"utf8"));
  const {svg,stats:row}=renderPlate(stem,label,role,vertices,faces);
  fs.writeFileSync(path.join(outDir,stem+"_review.svg"),svg);
  stats.records.push({id:stem,source:path.relative(repo,source).replaceAll("\\","/"),render:path.relative(repo,path.join(outDir,stem+"_review.svg")).replaceAll("\\","/"),...row});
}
fs.writeFileSync(statsPath,JSON.stringify(stats,null,2)+"\n");
console.log(`Rendered ${stats.records.length} source meshes to resolution-independent review SVGs.`);
