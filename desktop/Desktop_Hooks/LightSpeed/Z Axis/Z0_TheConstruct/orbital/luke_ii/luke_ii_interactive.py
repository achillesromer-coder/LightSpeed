#!/usr/bin/env python3
"""Build a self-contained-data interactive Luke II v1.3 engineering-review HTML."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path


def build_html(glb_path: Path, manifest_path: Path, parameters_path: Path, verification_path: Path,
               serviceability_path: Path, roundtrip_path: Path) -> str:
    glb_b64 = base64.b64encode(glb_path.read_bytes()).decode("ascii")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    parameters = json.loads(parameters_path.read_text(encoding="utf-8"))
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    serviceability = json.loads(serviceability_path.read_text(encoding="utf-8"))
    roundtrip = json.loads(roundtrip_path.read_text(encoding="utf-8"))
    payload = {
        "manifest": manifest,
        "parameters": parameters,
        "verification": verification,
        "serviceability": serviceability,
        "roundtrip": {k: v for k, v in roundtrip.items() if k != "nodes"},
    }
    data_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Luke II v1.3 — Serviceable Reference Assembly Review</title>
<style>
:root{{--bg:#0b0f14;--panel:#121923;--panel2:#182230;--line:#2c3a4d;--text:#e7eef7;--muted:#95a6b8;--accent:#70c7ff;--warn:#ffc857;--bad:#ff6b6b;--good:#64d98b}}
*{{box-sizing:border-box}} html,body{{margin:0;height:100%;overflow:hidden;background:var(--bg);color:var(--text);font:13px/1.35 Inter,Segoe UI,Arial,sans-serif}}
#app{{display:grid;grid-template-columns:310px 1fr 340px;grid-template-rows:56px 1fr 28px;height:100%}}
header{{grid-column:1/4;display:flex;align-items:center;gap:18px;padding:0 18px;border-bottom:1px solid var(--line);background:#0e151e}}
header h1{{font-size:16px;margin:0;letter-spacing:.03em}} .badge{{padding:4px 8px;border:1px solid #37516a;border-radius:4px;color:var(--accent);font-size:11px}}
#left,#right{{overflow:auto;background:var(--panel);padding:12px}} #left{{border-right:1px solid var(--line)}} #right{{border-left:1px solid var(--line)}}
#viewport{{position:relative;min-width:0;min-height:0}} canvas{{display:block;width:100%;height:100%}}
footer{{grid-column:1/4;display:flex;align-items:center;justify-content:space-between;padding:0 12px;border-top:1px solid var(--line);background:#0e151e;color:var(--muted);font-size:11px}}
section{{border:1px solid var(--line);border-radius:6px;margin-bottom:10px;background:var(--panel2)}} section h2{{font-size:12px;margin:0;padding:8px 10px;border-bottom:1px solid var(--line);letter-spacing:.06em;text-transform:uppercase;color:#c9d8e7}}
.content{{padding:9px}} label{{display:flex;align-items:center;gap:7px;margin:5px 0}} input[type=range]{{width:100%}} input[type=text],select{{width:100%;background:#0d141d;color:var(--text);border:1px solid var(--line);padding:7px;border-radius:4px}}
button{{background:#1b2b3a;color:var(--text);border:1px solid #3a5269;border-radius:4px;padding:6px 8px;cursor:pointer}} button:hover{{border-color:var(--accent)}} .row{{display:flex;gap:6px}} .row>*{{flex:1}}
.metric{{display:grid;grid-template-columns:1fr auto;gap:4px 8px;margin:3px 0}} .metric span:nth-child(odd){{color:var(--muted)}} .good{{color:var(--good)}} .warn{{color:var(--warn)}}
#results{{max-height:260px;overflow:auto;margin-top:7px}} .result{{padding:6px;border-bottom:1px solid #273444;cursor:pointer;word-break:break-word}} .result:hover,.result.active{{background:#22364a}}
pre{{white-space:pre-wrap;word-break:break-word;margin:0;color:#d6e1ec;font:11px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace}}
#loading{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:#0b0f14;z-index:5;font-size:15px}} #selection{{position:absolute;left:12px;bottom:12px;background:rgba(10,15,22,.88);border:1px solid var(--line);padding:7px 9px;border-radius:4px;max-width:48%;color:#dce8f3}}
.layer-count{{margin-left:auto;color:var(--muted);font-size:11px}} .gap{{border-left:3px solid var(--warn);padding:5px 7px;margin:5px 0;background:#171d24}} .small{{font-size:11px;color:var(--muted)}}
@media(max-width:1050px){{#app{{grid-template-columns:250px 1fr}} #right{{display:none}} header,footer{{grid-column:1/3}}}}
</style>
</head>
<body>
<div id="app">
<header><h1>Luke II v1.3 — Serviceable Reference Assembly</h1><span class="badge">REFERENCE CONFIGURATION</span><span class="badge">NOT ENGINEERING RELEASE</span><span class="small">Task: Luke closure before Mark III</span></header>
<aside id="left">
<section><h2>View controls</h2><div class="content">
<div class="row"><button id="home">Home</button><button id="top">Top</button><button id="side">Side</button><button id="iso">Iso</button></div>
<label>Explode <span id="explodeValue" class="layer-count">0%</span></label><input id="explode" type="range" min="0" max="100" value="0" />
<label>Cutaway</label><select id="cutaway"><option value="none">None</option><option value="x">Remove +X half</option><option value="y">Remove +Y half</option><option value="z">Remove upper half</option></select>
<label>Cut position <span id="cutValue" class="layer-count">0.0 m</span></label><input id="cutPosition" type="range" min="-14" max="14" step="0.1" value="0" />
<label><input id="wireframe" type="checkbox"/> Wireframe</label>
<label><input id="envelopeOpacity" type="checkbox" checked/> Transparent service envelopes</label>
</div></section>
<section><h2>System layers</h2><div id="layers" class="content"></div></section>
<section><h2>Component search</h2><div class="content"><input id="search" type="text" placeholder="Name, family, state, gate…"/><div id="results"></div></div></section>
</aside>
<main id="viewport"><div id="loading">Loading embedded 1:1 GLB…</div><div id="selection">Click a component or use search.</div></main>
<aside id="right">
<section><h2>Configuration status</h2><div id="status" class="content"></div></section>
<section><h2>Selected component</h2><div id="detail" class="content"><span class="small">No component selected.</span></div></section>
<section><h2>Habitation allocation</h2><div id="volumes" class="content"></div></section>
<section><h2>Open engineering gaps</h2><div id="gaps" class="content"></div></section>
</aside>
<footer><span>Geometry facts and spatial reservations only. No flight, pressure-vessel, human-rating, electrical, thermal or manufacturing approval.</span><span id="footerCount"></span></footer>
</div>
<script type="application/json" id="reviewData">{data_json}</script>
<script type="module">
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js';
import {{ OrbitControls }} from 'https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/controls/OrbitControls.js';
import {{ GLTFLoader }} from 'https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/loaders/GLTFLoader.js';

const DATA=JSON.parse(document.getElementById('reviewData').textContent);
const components=DATA.manifest.components;
const recordByName=new Map(components.map(r=>[r.node_name,r]));
const broadFamily=(r)=>{{
 const f=r.family;
 if(['solar_hull_panel','pressure_window','window_frame'].includes(f)) return 'Exterior / windows';
 if(f.includes('structure')||f==='primary_structure'||f==='attachment') return 'Structure / attachments';
 if(f.startsWith('habitat')||f==='habitation_equipment'||f==='removable_lining'||f==='egress_path') return 'Habitat / access';
 if(f.includes('harness')||f==='cable_tray'||f==='cable_route_envelope') return 'Harness / cable routes';
 if(f==='service_clearance'||f==='removal_path') return 'Service / removal envelopes';
 if(f.startsWith('mark_iii')||f==='interface') return 'Interfaces / Mark III arm';
 if(f==='payload_path'||f==='field_guide') return 'Illustrative guides';
 return 'Systems / equipment';
}};
const groups=[...new Set(components.map(broadFamily))].sort();
const groupEnabled=new Map(groups.map(g=>[g,true]));
const viewport=document.getElementById('viewport');
const scene=new THREE.Scene(); scene.background=new THREE.Color(0x0b0f14);
const camera=new THREE.PerspectiveCamera(40,1,.01,500); camera.position.set(30,-34,24);
const renderer=new THREE.WebGLRenderer({{antialias:true}}); renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.localClippingEnabled=true; viewport.prepend(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement); controls.enableDamping=true; controls.target.set(0,0,0);
scene.add(new THREE.HemisphereLight(0xddeeff,0x243040,2.0)); const key=new THREE.DirectionalLight(0xffffff,2.2); key.position.set(18,-20,28); scene.add(key); const fill=new THREE.DirectionalLight(0x79bfff,1.0); fill.position.set(-20,14,-8); scene.add(fill);
const grid=new THREE.GridHelper(70,70,0x30465d,0x1b2937); grid.rotation.x=Math.PI/2; grid.position.z=-3; scene.add(grid);
const raycaster=new THREE.Raycaster(), pointer=new THREE.Vector2(); let root=null, selected=null; const clipping=new THREE.Plane(new THREE.Vector3(0,0,0),0);

function resize(){{const w=viewport.clientWidth,h=viewport.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}} addEventListener('resize',resize); resize();
function setCamera(pos){{camera.position.set(...pos);controls.target.set(0,0,0);controls.update();}};
document.getElementById('home').onclick=()=>setCamera([30,-34,24]); document.getElementById('iso').onclick=()=>setCamera([30,-34,24]); document.getElementById('top').onclick=()=>setCamera([0,0,48]); document.getElementById('side').onclick=()=>setCamera([0,-48,0]);

const glbBytes=Uint8Array.from(atob('{glb_b64}'),c=>c.charCodeAt(0)); const glbURL=URL.createObjectURL(new Blob([glbBytes],{{type:'model/gltf-binary'}}));
new GLTFLoader().load(glbURL,gltf=>{{
 root=gltf.scene; scene.add(root); root.traverse(o=>{{if(o.isMesh){{o.userData.basePosition=o.position.clone(); const r=recordByName.get(o.name); o.userData.record=r||null; o.material=o.material.clone();}}}});
 applyVisibility(); applyEnvelopes(); document.getElementById('loading').remove(); URL.revokeObjectURL(glbURL); populateResults('');
}},undefined,e=>{{document.getElementById('loading').textContent='GLB load failed: '+e.message;}});

function applyVisibility(){{if(!root)return; root.traverse(o=>{{if(o.isMesh){{const r=o.userData.record; o.visible=!r||groupEnabled.get(broadFamily(r));}}}});}}
function applyEnvelopes(){{if(!root)return; const transparent=document.getElementById('envelopeOpacity').checked; root.traverse(o=>{{if(o.isMesh&&o.userData.record){{const g=broadFamily(o.userData.record); const env=g==='Service / removal envelopes'||g==='Illustrative guides'; o.material.transparent=env&&transparent; o.material.opacity=env&&transparent?.14:1; o.material.depthWrite=!(env&&transparent);}}}});}}
const layers=document.getElementById('layers'); for(const g of groups){{const n=components.filter(r=>broadFamily(r)===g).length; const l=document.createElement('label'); l.innerHTML=`<input type="checkbox" checked><span>${{g}}</span><span class="layer-count">${{n}}</span>`; l.querySelector('input').onchange=e=>{{groupEnabled.set(g,e.target.checked);applyVisibility();}}; layers.appendChild(l);}}

document.getElementById('explode').oninput=e=>{{const f=+e.target.value/100;document.getElementById('explodeValue').textContent=e.target.value+'%';if(root)root.traverse(o=>{{if(o.isMesh&&o.userData.record){{const c=o.userData.record.centroid_m;const v=new THREE.Vector3(c[0],c[1],c[2]);if(v.length()>0)v.normalize().multiplyScalar(f*5);o.position.copy(o.userData.basePosition).add(v);}}}});}};
function applyClip(){{const mode=document.getElementById('cutaway').value,p=+document.getElementById('cutPosition').value;document.getElementById('cutValue').textContent=p.toFixed(1)+' m';let normal=new THREE.Vector3();if(mode==='x')normal.set(-1,0,0);if(mode==='y')normal.set(0,-1,0);if(mode==='z')normal.set(0,0,-1);clipping.normal.copy(normal);clipping.constant=p;if(root)root.traverse(o=>{{if(o.isMesh)o.material.clippingPlanes=mode==='none'?[]:[clipping];}});}} document.getElementById('cutaway').onchange=applyClip;document.getElementById('cutPosition').oninput=applyClip;
document.getElementById('wireframe').onchange=e=>{{if(root)root.traverse(o=>{{if(o.isMesh)o.material.wireframe=e.target.checked;}});}}; document.getElementById('envelopeOpacity').onchange=applyEnvelopes;

function formatRecord(r){{return `<div class="metric"><span>Name</span><b>${{r.node_name}}</b><span>Family</span><b>${{r.family}}</b><span>Evidence</span><b>${{r.evidence_state}}</b><span>Review gate</span><b>${{r.review_gate}}</b><span>Physical</span><b>${{r.physical}}</b><span>Maintainable</span><b>${{r.maintainable}}</b><span>Attachment</span><b>${{r.attachment_parent||'—'}}</b><span>Cable route</span><b>${{r.cable_route||'—'}}</b><span>Service clearance</span><b>${{r.service_clearance||'—'}}</b><span>Removal path</span><b>${{r.removal_path||'—'}}</b><span>Extents</span><b>${{r.extents_m.map(x=>x.toFixed(3)).join(' × ')}} m</b></div><div class="small">Source basis: ${{r.source_basis}}</div>`;}}
function choose(r){{selected=r;document.getElementById('detail').innerHTML=formatRecord(r);document.getElementById('selection').textContent=r.node_name+' — '+r.evidence_state;document.querySelectorAll('.result').forEach(e=>e.classList.toggle('active',e.dataset.name===r.node_name));}}
renderer.domElement.addEventListener('pointerdown',e=>{{if(!root)return;const rect=renderer.domElement.getBoundingClientRect();pointer.x=((e.clientX-rect.left)/rect.width)*2-1;pointer.y=-((e.clientY-rect.top)/rect.height)*2+1;raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(root.children,true).find(h=>h.object.userData.record);if(hit)choose(hit.object.userData.record);}});
function populateResults(q){{q=q.trim().toLowerCase();const found=components.filter(r=>!q||[r.node_name,r.family,r.evidence_state,r.review_gate,r.source_basis].join(' ').toLowerCase().includes(q)).slice(0,350);const box=document.getElementById('results');box.innerHTML='';for(const r of found){{const d=document.createElement('div');d.className='result';d.dataset.name=r.node_name;d.innerHTML=`<b>${{r.node_name}}</b><div class="small">${{r.family}} · ${{r.evidence_state}}</div>`;d.onclick=()=>choose(r);box.appendChild(d);}}}} document.getElementById('search').oninput=e=>populateResults(e.target.value);

const s=DATA.serviceability,v=DATA.verification,rt=DATA.roundtrip;
document.getElementById('status').innerHTML=`<div class="metric"><span>Geometry</span><b class="good">${{v.status}}</b><span>Serviceability</span><b class="good">${{s.status}}</b><span>GLB round-trip</span><b class="good">${{rt.status}}</b><span>Named nodes</span><b>${{components.length}}</b><span>Physical nodes</span><b>${{s.counts.physical_nodes}}</b><span>Clearance envelopes</span><b>${{s.counts.service_clearances}}</b><span>Removal paths</span><b>${{s.counts.removal_paths}}</b><span>Walkway max gap</span><b>${{s.walkway.maximum_centre_gap_m.toFixed(3)}} m</b></div>`;
const hv=s.habitation_volumes_m3;document.getElementById('volumes').innerHTML=`<div class="metric"><span>Gross planning</span><b>${{hv.gross_planning.toFixed(3)}} m³</b><span>Pressure-liner clear</span><b>${{hv.pressure_liner_clear.toFixed(3)}} m³</b><span>Service allocated</span><b>${{hv.service_allocated_reference.toFixed(3)}} m³</b></div><div class="warn small">Derived spatial allocations only; not certified habitable volume.</div>`;
document.getElementById('gaps').innerHTML=DATA.parameters.open_engineering_gaps.map(g=>`<div class="gap">${{typeof g==='string'?g:(g.id?'<b>'+g.id+'</b> — ':'')+(g.description||g.gap||JSON.stringify(g))}}</div>`).join('');
document.getElementById('footerCount').textContent=`${{components.length.toLocaleString()}} selectable nodes · Issue #31 · PR #30 draft`;
(function animate(){{requestAnimationFrame(animate);controls.update();renderer.render(scene,camera);}})();
</script>
</body></html>'''


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--glb',type=Path,required=True);ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--parameters',type=Path,required=True)
    ap.add_argument('--verification',type=Path,required=True);ap.add_argument('--serviceability',type=Path,required=True);ap.add_argument('--roundtrip',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();a.output.write_text(build_html(a.glb,a.manifest,a.parameters,a.verification,a.serviceability,a.roundtrip),encoding='utf-8')
    print(json.dumps({'status':'PASS_INTERACTIVE_REVIEW_SURFACE','path':a.output.name,'bytes':a.output.stat().st_size,'component_nodes':json.loads(a.manifest.read_text())['node_count']},indent=2));return 0
if __name__=='__main__': raise SystemExit(main())
