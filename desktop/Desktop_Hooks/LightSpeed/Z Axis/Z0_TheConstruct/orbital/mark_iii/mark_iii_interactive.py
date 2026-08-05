#!/usr/bin/env python3
"""Build the Mark III v0.3 original-layout interactive review surface."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path


def build_html(
    glb: Path,
    manifest: Path,
    parameters: Path,
    verification: Path,
    serviceability: Path,
    roundtrip: Path,
    manufacturing: Path | None = None,
) -> str:
    data = {
        "manifest": json.loads(manifest.read_text()),
        "parameters": json.loads(parameters.read_text()),
        "verification": json.loads(verification.read_text()),
        "serviceability": json.loads(serviceability.read_text()),
        "roundtrip": json.loads(roundtrip.read_text()),
        "manufacturing": json.loads(manufacturing.read_text())
        if manufacturing and manufacturing.exists()
        else None,
    }
    glb64 = base64.b64encode(glb.read_bytes()).decode("ascii")
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    template = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mark III v0.3 Original-Layout Review</title>
<style>*{box-sizing:border-box}body{margin:0;background:#090d12;color:#dce5ed;font:13px system-ui,Segoe UI,sans-serif;overflow:hidden}#app{display:grid;grid-template-columns:330px 1fr 350px;grid-template-rows:58px calc(100vh - 88px) 30px;height:100vh}header{grid-column:1/4;display:flex;align-items:center;gap:12px;padding:0 16px;background:#101821;border-bottom:1px solid #293746;white-space:nowrap;overflow:auto}header b{font-size:17px}.tag{padding:5px 9px;border:1px solid #3a536b;border-radius:12px;color:#a8c8df}aside{background:#0f161e;overflow:auto;padding:12px;border-right:1px solid #263544}#right{border-left:1px solid #263544;border-right:0}#viewport{position:relative;min-width:0}canvas{display:block}h3{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:#8eabc0;margin:14px 0 8px}button,select,input{background:#17232e;color:#dce5ed;border:1px solid #364c60;border-radius:5px;padding:7px}button{cursor:pointer}.row{display:flex;gap:6px;flex-wrap:wrap}.layer{display:grid;grid-template-columns:22px 1fr auto;gap:5px;align-items:center;padding:4px 0}.count,.muted{color:#8196a7}#search{width:100%}.result{padding:7px;border-bottom:1px solid #1f2b37;cursor:pointer;overflow-wrap:anywhere}.result:hover,.result.active{background:#1b2a38}.metric{display:grid;grid-template-columns:1fr 1.3fr;gap:6px 8px}.metric b{overflow-wrap:anywhere}.good{color:#7fd1a1}.warn{color:#e5c374}.bad{color:#e48d8d}.gap{padding:7px 0;border-bottom:1px solid #24323f}label.ctrl{display:grid;gap:5px;margin:8px 0}input[type=range]{width:100%;padding:0}footer{grid-column:1/4;padding:6px 12px;color:#8295a6;background:#101821;border-top:1px solid #263544}#loading{position:absolute;inset:0;display:grid;place-items:center;background:#090d12;color:#9fc3dc;z-index:4}#selection{position:absolute;left:12px;bottom:12px;background:#101821e8;border:1px solid #354c60;padding:8px;max-width:72%;border-radius:5px}.small{font-size:11px;color:#92a6b7;line-height:1.4}.gate{border-left:3px solid #e5c374;padding-left:8px}.mode{border-left:3px solid #6fb3d2;padding-left:8px}</style></head>
<body><div id="app"><header><b>Mark III v0.3 — Original Layout / Print &amp; Plating Development</b><span class="tag" id="nodeTag">__NODECOUNT__ named nodes</span><span class="tag">25-socket dual spiral</span><span class="tag">18 body solenoids</span><span class="tag">Manufacturing reference · deployment blocked</span></header>
<aside><h3>View</h3><div class="row"><button id="home">Home</button><button id="front">Front</button><button id="side">Side</button><button id="top">Top</button></div>
<label class="ctrl">Explode <span id="explodeValue">0%</span><input id="explode" type="range" min="0" max="100" value="0"></label>
<label class="ctrl">Cutaway axis<select id="cutaway"><option value="none">None</option><option value="x">X</option><option value="y">Y</option><option value="z">Z</option></select></label>
<label class="ctrl">Cut position <span id="cutValue">0.00 m</span><input id="cutPosition" type="range" min="-1" max="1" step="0.01" value="0"></label>
<label class="ctrl">Array review<select id="arraySelect"><option value="all">All guides</option><option value="none">Hide guides</option><option value="1">1 module</option><option value="2">2 modules</option><option value="4">4 modules</option><option value="8">8 modules</option><option value="18">18 modules</option></select></label>
<label class="ctrl mode">Resonator mode<select id="resMode"><option value="all">Dual interleaved A+B</option><option value="A">Spiral A + centre</option><option value="B">Spiral B + centre</option><option value="roles">Flower-of-Life role bands</option><option value="none">Hide resonators/guides</option></select></label>
<label class="ctrl">Manufacturing view<select id="mfgMode"><option value="all">All manufacturing references</option><option value="substrate">Print substrate</option><option value="plating">Plating allowances/features</option><option value="none">Hide manufacturing references</option></select></label>
<label><input id="wireframe" type="checkbox"> Wireframe</label> <label><input id="envelopes" type="checkbox" checked> Transparent envelopes</label>
<h3>Layers</h3><div id="layers"></div><h3>Search</h3><input id="search" placeholder="component, role, state, print part"><div id="results"></div></aside>
<div id="viewport"><div id="loading">Loading embedded 1:1 GLB…</div><div id="selection">Select a component to inspect.</div></div>
<aside id="right"><h3>Qualification</h3><div id="status"></div><h3>Selected component</h3><div id="detail" class="muted">No selection.</div><h3>Resonator configuration</h3><div id="resInfo"></div><h3>Manufacturing gates</h3><div id="mfgInfo"></div><h3>Source conflicts</h3><div id="conflicts"></div><h3>Known unknowns</h3><div id="gaps"></div></aside>
<footer id="footer"></footer></div><script id="reviewData" type="application/json">__PAYLOAD__</script>
<script type="module">import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js';import{OrbitControls}from'https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/controls/OrbitControls.js';import{GLTFLoader}from'https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/loaders/GLTFLoader.js';
const D=JSON.parse(document.getElementById('reviewData').textContent),C=D.manifest.components,R=new Map(C.map(x=>[x.node_name,x]));nodeTag.textContent=`${C.length} named nodes`;
const group=x=>{if(x.family==='array_guide')return'Array guides';if(['service_clearance','removal_path','connector_access','cable_bend_space'].includes(x.family))return'Service / access envelopes';if(['shell_panel','solar_hull_skin','fastener','plating_allowance','plating_feature'].includes(x.family))return'Exterior / manufacturing';if(['coupler','coupler_latch','coupler_bridge'].includes(x.family))return'Coupling';if(['solenoid','coil_reference','field_guide'].includes(x.family))return'Solenoids / field guides';if(['resonator','resonator_mount','resonator_guide'].includes(x.family))return'Resonator matrix';if(['energy','energy_tray','controller'].includes(x.family))return'Energy / controls';if(['sensor','comms'].includes(x.family))return'Sensors / comms';if(['cable_tray','harness'].includes(x.family))return'Cable / harness';if(x.subsystem==='arm_system')return'Arms / joints';if(x.subsystem==='probe_system')return'Central probe';if(['process_tunnel','sample_cartridge'].includes(x.family))return'Process chamber';if(x.subsystem==='original_layout')return'Original-layout guides';return'Structure / isolation'};
const groups=[...new Set(C.map(group))].sort(),enabled=new Map(groups.map(g=>[g,true]));const viewport=document.getElementById('viewport'),scene=new THREE.Scene();scene.background=new THREE.Color(0x090d12);const cam=new THREE.PerspectiveCamera(42,1,.001,100);cam.position.set(1.45,-1.75,1.15);const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.localClippingEnabled=true;viewport.prepend(renderer.domElement);const controls=new OrbitControls(cam,renderer.domElement);controls.enableDamping=true;controls.target.set(0,0,-.18);scene.add(new THREE.HemisphereLight(0xe7f1ff,0x26313e,2));const key=new THREE.DirectionalLight(0xffffff,2.2);key.position.set(2,-2,3);scene.add(key);const grid=new THREE.GridHelper(5,50,0x294052,0x182633);grid.rotation.x=Math.PI/2;grid.position.z=-.96;scene.add(grid);
function resize(){const w=viewport.clientWidth,h=viewport.clientHeight;renderer.setSize(w,h,false);cam.aspect=w/h;cam.updateProjectionMatrix()}addEventListener('resize',resize);resize();function view(p,t=[0,0,-.18]){cam.position.set(...p);controls.target.set(...t);controls.update()}home.onclick=()=>view([1.45,-1.75,1.15]);front.onclick=()=>view([-1.65,0,-.18]);side.onclick=()=>view([0,-1.75,-.18]);top.onclick=()=>view([0,0,1.65],[0,0,-.18]);
let root=null;const bytes=Uint8Array.from(atob('__GLB64__'),c=>c.charCodeAt(0)),url=URL.createObjectURL(new Blob([bytes],{type:'model/gltf-binary'}));new GLTFLoader().load(url,g=>{root=g.scene;scene.add(root);root.traverse(o=>{if(o.isMesh){o.userData.base=o.position.clone();o.userData.record=R.get(o.name)||null;o.material=o.material.clone()}});apply();loading.remove();URL.revokeObjectURL(url);populate('')},undefined,e=>loading.textContent='GLB load failed: '+e.message);
const layers=document.getElementById('layers');for(const g of groups){const l=document.createElement('label');l.className='layer';l.innerHTML=`<input type=checkbox checked><span>${g}</span><span class=count>${C.filter(x=>group(x)===g).length}</span>`;l.querySelector('input').onchange=e=>{enabled.set(g,e.target.checked);apply()};layers.appendChild(l)}
function resonatorVisible(r){const mode=resMode.value;if(!['resonator','resonator_mount','resonator_guide'].includes(r.family))return true;if(mode==='none')return false;if(mode==='all')return true;if(mode==='roles')return r.family==='resonator'||r.configuration==='FLOWER_OF_LIFE_ROLE_BANDS';if(r.family==='resonator')return r.configuration==='SHARED_CENTRAL'||r.configuration===`DUAL_SPIRAL_${mode}`;if(r.family==='resonator_mount')return r.configuration===`DUAL_SPIRAL_${mode}`;return r.configuration===`SPIRAL_${mode}`}
function manufacturingVisible(r){const mode=mfgMode.value;if(!['shell_panel','plating_allowance','plating_feature','fastener'].includes(r.family))return true;if(mode==='all')return true;if(mode==='none')return !['plating_allowance','plating_feature','fastener'].includes(r.family);if(mode==='substrate')return r.family==='shell_panel'||r.family==='fastener';if(mode==='plating')return r.family==='plating_allowance'||r.family==='plating_feature';return true}
function apply(){if(!root)return;const arr=arraySelect.value;root.traverse(o=>{if(!o.isMesh)return;const r=o.userData.record;if(!r)return;let v=enabled.get(group(r))&&resonatorVisible(r)&&manufacturingVisible(r);if(r.family==='array_guide')v=v&&(arr==='all'||r.array_configuration===arr);o.visible=v;const env=['service_clearance','removal_path','connector_access','cable_bend_space','array_guide','field_guide','resonator_guide','plating_allowance','layout_guide'].includes(r.family);o.material.transparent=env&&envelopes.checked;o.material.opacity=env&&envelopes.checked?.14:1;o.material.depthWrite=!(env&&envelopes.checked)}}arraySelect.onchange=apply;resMode.onchange=apply;mfgMode.onchange=apply;envelopes.onchange=apply;wireframe.onchange=e=>root&&root.traverse(o=>{if(o.isMesh)o.material.wireframe=e.target.checked});
explode.oninput=e=>{explodeValue.textContent=e.target.value+'%';const f=+e.target.value/100;if(root)root.traverse(o=>{if(o.isMesh&&o.userData.record){const c=o.userData.record.centroid_m,v=new THREE.Vector3(...c);if(v.length())v.normalize().multiplyScalar(f*.25);o.position.copy(o.userData.base).add(v)}})};const plane=new THREE.Plane(new THREE.Vector3(),0);function clip(){const mode=cutaway.value,p=+cutPosition.value;cutValue.textContent=p.toFixed(2)+' m';plane.normal.set(mode==='x'?-1:0,mode==='y'?-1:0,mode==='z'?-1:0);plane.constant=p;if(root)root.traverse(o=>{if(o.isMesh)o.material.clippingPlanes=mode==='none'?[]:[plane]})}cutaway.onchange=clip;cutPosition.oninput=clip;
function esc(x){return String(x??'—').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}function details(r){const fields=[['Name',r.node_name],['Family',r.family],['Subsystem',r.subsystem],['Evidence',r.evidence_state],['Role',r.component_role],['Configuration',r.configuration],['Manufacturing',r.manufacturing_state],['Print part',r.print_part],['Physical',r.physical],['Maintainable',r.maintainable],['Attachment',r.attachment_parent],['Cable route',r.cable_route],['Panel access',r.panel_access],['Clearance',r.service_clearance],['Removal path',r.removal_path],['Extents',r.extents_m.map(x=>x.toFixed(4)).join(' × ')+' m'],['Review gate',r.review_gate],['Source basis',r.source_basis]];return `<div class=metric>${fields.map(([a,b])=>`<span>${esc(a)}</span><b>${esc(b)}</b>`).join('')}</div>`}
const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();renderer.domElement.addEventListener('pointerdown',e=>{if(!root)return;const b=renderer.domElement.getBoundingClientRect();mouse.x=(e.clientX-b.left)/b.width*2-1;mouse.y=-(e.clientY-b.top)/b.height*2+1;ray.setFromCamera(mouse,cam);const hit=ray.intersectObjects(root.children,true).find(x=>x.object.userData.record);if(hit)choose(hit.object.userData.record)});function choose(r){detail.innerHTML=details(r);selection.innerHTML=`<b>${esc(r.node_name)}</b><div class=small>${esc(r.component_role||r.family)} · ${esc(r.evidence_state)}</div>`;document.querySelectorAll('.result').forEach(x=>x.classList.toggle('active',x.dataset.n===r.node_name))}function populate(q){results.innerHTML='';const z=q.trim().toLowerCase(),rows=C.filter(r=>!z||JSON.stringify(r).toLowerCase().includes(z)).slice(0,180);for(const r of rows){const d=document.createElement('div');d.className='result';d.dataset.n=r.node_name;d.innerHTML=`<b>${esc(r.node_name)}</b><div class=small>${esc(r.component_role||r.family)} · ${esc(r.evidence_state)}</div>`;d.onclick=()=>choose(r);results.appendChild(d)}}search.oninput=e=>populate(e.target.value);
const s=D.serviceability,v=D.verification,rt=D.roundtrip,m=D.manufacturing;status.innerHTML=`<div class=metric><span>Geometry</span><b class=good>${esc(v.status)}</b><span>Serviceability</span><b class=good>${esc(s.status)}</b><span>GLB round-trip</span><b class=good>${esc(rt.status)}</b><span>Named nodes</span><b>${C.length}</b><span>Physical nodes</span><b>${s.counts.physical_nodes}</b><span>Resonators</span><b>${s.counts.resonators}</b><span>Body solenoids</span><b>${s.counts.solenoid_nodes}</b><span>Print references</span><b>${s.counts.print_reference_count}</b><span>Module envelope</span><b>${s.canonical_module_envelope_m.extents.map(x=>x.toFixed(3)).join(' × ')} m</b></div>`;
const rc=D.parameters.resonator_configuration;resInfo.innerHTML=`<div class=mode><b>${esc(rc.default_mode)}</b><div class=small>${esc(rc.multifunction_strategy)}</div></div>`+Object.entries(rc.roles).map(([k,x])=>`<div class=gap><b>${esc(k)}: ${x.count}</b><div class=small>${esc(x.source_label)} · ${esc(x.state)}</div></div>`).join('');mfgInfo.innerHTML=m?`<div class=gate><b class=${m.status.startsWith('PASS')?'good':'bad'}>${esc(m.status)}</b><div class=small>${esc(m.allowed_interpretation)}</div></div>`+m.stages.map(x=>`<div class=gap><b>${esc(x.stage)} — ${esc(x.name)}</b><div class=small>${esc(x.state)} · ${esc(x.release)}</div></div>`).join(''):`<div class=warn>Manufacturing audit not embedded.</div>`;conflicts.innerHTML=D.parameters.source_conflicts.map(x=>`<div class=gap><b>${esc(x.id)}</b> — ${esc(x.description)}<div class=small>${esc(x.resolution)}</div></div>`).join('');gaps.innerHTML=D.parameters.known_unknowns.map(x=>`<div class=gap><b>${esc(x.id)}</b> — ${esc(x.description)}</div>`).join('');footer.textContent=`${C.length} selectable nodes · v0.3 original-layout authority · PR #33 remains draft · manufacturing and deployment release blocked`;function animate(){requestAnimationFrame(animate);controls.update();renderer.render(scene,cam)}animate();</script></body></html>'''
    return template.replace("__PAYLOAD__", payload).replace("__GLB64__", glb64).replace("__NODECOUNT__", str(data["manifest"]["node_count"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    for key in (
        "glb",
        "manifest",
        "parameters",
        "verification",
        "serviceability",
        "roundtrip",
        "output",
    ):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--manufacturing", type=Path)
    args = parser.parse_args()
    html = build_html(
        args.glb,
        args.manifest,
        args.parameters,
        args.verification,
        args.serviceability,
        args.roundtrip,
        args.manufacturing,
    )
    args.output.write_text(html, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS_ORIGINAL_LAYOUT_INTERACTIVE_REVIEW_SURFACE",
                "path": args.output.name,
                "bytes": args.output.stat().st_size,
                "component_nodes": json.loads(args.manifest.read_text())["node_count"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
