function e(){let e=new DOMParser().parseFromString(`<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>FileSpace tutorial · UniSpace</title><link rel="stylesheet" href="unispace.css"></head>
<body><header><a class="brand" href="index.html">UniSpace</a><nav><a href="#open">Open FileSpace</a></nav></header>
<main><section id="open"><p class="edition">FileSpace / S91</p><h1>Your first carrier</h1>
<ol><li>Keep <b>CGX.cgx</b> with this tutorial. If you downloaded the kit, extract its folder and open <b>FileSpace.html</b> in a browser.</li>
<li>Select the carrier below. The reader checks its identity and opens the contents index locally. No account is required.</li>
<li>Choose a geometric quadrant, then select a file to inspect its cell. Export the original bytes, or export the matching files as a source-linked JSON series.</li></ol>
<label for="carrier">Open CGX.cgx</label> <input id="carrier" type="file" accept=".cgx"><p id="handshake" role="status">Waiting for a carrier.</p></section>
<section id="workspace" hidden><h2>Explore FileSpace</h2><p id="identity"></p>
<section id="geometry" hidden><h3>Raphael geometry</h3><p>Select a role or enter its five-digit ternary review address. Zero opens the empty state.</p>
<label>Role <select id="role"></select></label> <label>Ternary address <input id="trits" size="6" maxlength="5" placeholder="00001"></label>
<button id="resolve-address">Open address</button><p id="geometry-note" role="status"></p>
<canvas id="mesh-view" width="480" height="280" aria-label="Orthographic wireframe of the selected source mesh" style="width:min(100%,480px);height:auto"></canvas>
<button id="show-role">Inspect role record</button> <button id="show-mesh">Inspect mesh record</button></section>
<div id="quadrants" class="sets" aria-label="Geometric quadrants"></div>
<label>Filter paths <input type="search" id="query" placeholder="e.g. spec/CGX"></label>
<p id="matches" aria-live="polite"></p><label for="members">Matching files</label>
<select id="members" size="7" style="display:block;width:100%"></select>
<p id="coordinate"></p>
<button id="preview">Read selected file</button> <button id="export">Export original file</button> <button id="series">Export filtered series</button>
<p id="action" role="status"></p><pre id="excerpt" style="white-space:pre-wrap;overflow-wrap:anywhere;max-height:18rem;overflow:auto"></pre></section>
<footer><p>The reader needs a browser with local file selection, SHA-256 and raw DEFLATE support. Series exports are limited to 64 files and 512 KiB of source bytes. Narrow the filter for larger sets.</p><a href="index.html">Product overview</a></footer>
</main><script src="filespace.js"><\/script></body></html>
`,`text/html`);e.querySelector(`header`)?.remove(),e.querySelector(`footer a`)?.remove(),e.querySelector(`link[rel=stylesheet]`)?.remove();let t=e.createElement(`style`);t.textContent=`:root{color-scheme:light;--ink:#172b2c;--accent:#126b61;--line:#cdd6d1;font:16px/1.5 'Segoe UI',Arial,sans-serif;color:var(--ink);background:#fafaf7}
*{box-sizing:border-box}body{margin:0}main,header{max-width:1440px;margin:auto;padding-inline:clamp(22px,6vw,100px)}a{color:inherit;text-underline-offset:4px}header,nav,figcaption,footer{display:flex;align-items:center;justify-content:space-between;gap:22px}header{min-height:78px;border-bottom:1px solid var(--line)}.brand{font-size:24px;font-weight:650;letter-spacing:-1.5px;text-decoration:none;display:flex;align-items:center;gap:9px}.mark{font-size:40px;color:var(--accent)}nav a{font-size:.9rem;text-decoration:none}nav a:hover,footer a:hover{text-decoration:underline}.hero{display:grid;grid-template-columns:1fr 1fr;align-items:center;gap:3vw;padding-block:clamp(40px,7vw,96px);border-bottom:1px solid var(--line)}.edition,.meta,figcaption,.sets small,.check small,#selection{font:12px/1.5 Consolas,monospace}.edition{color:var(--accent);letter-spacing:.08em}.intro h1{font-size:clamp(66px,8vw,116px);letter-spacing:-.085em;line-height:1;margin:20px 0 12px;font-weight:580}.intro h1 span{color:var(--accent)}.lede{font:italic clamp(26px,2.8vw,43px)/1.2 Georgia,serif;margin:12px 0 22px}.description,.section-lede{max-width:52ch;color:#4c6060}.button{display:inline-flex;align-items:center;gap:1.3em;background:var(--ink);color:white;text-decoration:none;border-radius:4px;padding:14px 20px;margin-top:14px;font-weight:600}.button:hover{background:var(--accent)}.meta{color:#4c6060}figure{min-width:0;margin:0}canvas{display:block;width:100%;aspect-ratio:1.3}figcaption{border-top:1px solid var(--line);padding-top:9px}.sets{display:grid;grid-template-columns:repeat(4,1fr);border-block:1px solid var(--line);margin:30px 0 12px}.sets button{appearance:none;background:transparent;color:inherit;text-align:left;font:inherit;border:0;border-right:1px solid var(--line);padding:24px 18px;cursor:pointer}.sets button:last-child{border:0}.sets button:hover,.sets button[aria-pressed=true]{background:#e8f2ed}.sets strong,.sets span,.sets small,.check code,.check small{display:block}.sets small,.check small{color:var(--accent)}.sets strong{font-size:1.23rem;margin:10px 0}.sets span{font-size:.94rem;color:#405756}h2{font:normal clamp(34px,4vw,60px)/1.1 Georgia,serif;letter-spacing:-.05em;margin:12px 0}#sets,#verify{padding-block:48px}#verify{display:grid;grid-template-columns:1fr 1fr;gap:5vw;border-top:1px solid var(--line)}.check{background:white;padding:24px;border:1px solid var(--line)}.check label{display:block;font-weight:650;margin-bottom:12px}input{max-width:100%}.check code{overflow-wrap:anywhere;font-size:.82rem;margin-top:5px}footer{align-items:start;border-top:1px solid var(--line);padding-block:28px;font-size:.82rem}footer p{max-width:57ch;margin:4px 0}a:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid #03756b;outline-offset:4px}
@media(max-width:820px){.hero,#verify{grid-template-columns:1fr}.sets{grid-template-columns:1fr 1fr}.hero figure{max-width:520px;width:100%;justify-self:center}.sets button{border:1px solid var(--line)}footer{flex-wrap:wrap}}
@media(max-width:480px){.sets{grid-template-columns:1fr}header{min-height:64px}nav{gap:14px}#sets,#verify{padding-block:32px}}
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(260px,100%),1fr));gap:22px;margin:32px 0}.gallery img{width:100%;height:auto;display:block}.gallery small{overflow-wrap:anywhere}#open,#workspace{padding-block:32px}#workspace button{padding:10px;cursor:pointer}#workspace pre{background:#eef2ee;padding:14px}
`,e.head.append(t);let n=e.createElement(`meta`);n.httpEquiv=`Content-Security-Policy`,n.content=`default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'`,e.head.prepend(n),/^[0-9a-f]{64}$/.test(``),e.querySelector(`script[src]`)?.remove();let r=e.createElement(`script`);return r.textContent=`'use strict';
const expected = '1138da5af4e1c66eb60120dd050e2037fc8d7799a9ccebb01ad48089b234785f';
const ui = id => document.getElementById(id);
const text = new TextDecoder();
let session, quadrant = '', visible = [], generation = 0;
async function sha(bytes) {
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('');
}
// S91 is verified before interpreting offsets. Account for its CGX prefix when
// reading a ZIP whose directory addresses may be relative to the ZIP payload.
function directory(bytes) {
  const view = new DataView(bytes), entries = new Map();
  const u16 = p => view.getUint16(p, true), u32 = p => view.getUint32(p, true);
  let e = bytes.byteLength - 22;
  while (e >= Math.max(0, bytes.byteLength - 65557) && u32(e) !== 0x06054b50) e--;
  if (e < 0 || u32(e) !== 0x06054b50) throw Error('Missing carrier directory.');
  let p = e - u32(e + 12);
  const prefix = p - u32(e + 16);
  for (let i = 0; i < u16(e + 10); i++) {
    if (u32(p) !== 0x02014b50) throw Error('Invalid carrier directory.');
    const length = u16(p + 28), local = prefix + u32(p + 42);
    if (u32(local) !== 0x04034b50) throw Error('Invalid member offset.');
    const name = text.decode(new Uint8Array(bytes, p + 46, length));
    const offset = local + 30 + u16(local + 26) + u16(local + 28);
    entries.set(name, {offset, compressed: u32(p + 20), size: u32(p + 24), method: u16(p + 10)});
    p += 46 + length + u16(p + 30) + u16(p + 32);
  }
  return entries;
}
async function readMember(state, path) {
  const m = state.entries.get(path);
  if (!m || m.size > 1024 * 1024) throw Error('Member exceeds the reader limit or is missing.');
  const chunk = state.file.slice(m.offset, m.offset + m.compressed);
  let data;
  if (m.method === 0) data = await chunk.arrayBuffer();
  else if (m.method === 8) data = await new Response(chunk.stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer();
  else throw Error('Unsupported compression method.');
  if (data.byteLength !== m.size) throw Error('Member length mismatch.');
  return data;
}
async function checked(state, row) {
  const bytes = await readMember(state, row.path);
  if (bytes.byteLength !== row.size_bytes || await sha(bytes) !== row.sha256) throw Error('File integrity check failed.');
  return new Uint8Array(bytes);
}
function describe() {
  const row = visible[ui('members').selectedIndex];
  ui('coordinate').textContent = row ? row.semantic_path.join(' / ') + ' · Cell ' + row.cell + ' · ' + row.size_bytes + ' bytes' : '';
  ui('preview').disabled = ui('export').disabled = !row;
  ui('excerpt').textContent = ui('action').textContent = '';
}
let geometryRevision = 0;
async function selectGeometry(state, slot) {
  const revision = ++geometryRevision;
  const row = state.geometry.roles.find(r => r.slot === slot);
  const ctx = ui('mesh-view').getContext('2d');
  ctx.clearRect(0,0,480,280);
  ui('role').value = String(slot);
  ui('trits').value = slot.toString(3).padStart(5,'0');
  ui('show-role').disabled = ui('show-mesh').disabled = true;
  if (!row) {
    ui('geometry-note').textContent = '00000 · Empty · source position 174 · nonmintable';
    return;
  }
  try {
    const record=state.rows.find(r=>r.path===row.mesh);
    const mesh=JSON.parse(text.decode(await checked(state,record)));
    if (revision!==geometryRevision || state!==session) return;
    const points=mesh.v.map(([x,y,z])=>[0.866*x+0.5*z,0.25*x+0.866*y-0.433*z]);
    const extent=points.reduce((v,[x,y])=>Math.max(v,Math.abs(x),Math.abs(y)),0);
    if(!Number.isFinite(extent)||extent<=0)throw Error('Invalid mesh extent.');
    ctx.strokeStyle='#14695d';ctx.lineWidth=1;
    for(const face of mesh.f){
      ctx.beginPath();
      face.forEach((index,i)=>{const [x,y]=points[index];const px=240+x*125/extent,py=140-y*125/extent;
        if(i===0)ctx.moveTo(px,py);else ctx.lineTo(px,py);});
      ctx.closePath();ctx.stroke();
    }
    ui('geometry-note').textContent=row.id+' · '+row.name+' · '+points.length+' vertices · '+mesh.f.length+' faces · private review';
    for(const [button,path] of [['show-role',row.role],['show-mesh',row.mesh]]){
      ui(button).disabled=false;
      ui(button).onclick=()=>{ui('quadrants').firstElementChild.click();ui('query').value=path;filter();ui('members').focus();};
    }
  }catch(error){if(revision===geometryRevision && state===session)ui('geometry-note').textContent=error.message;}
}
async function prepareGeometry(state){
  const index=state.rows.find(r=>r.path==='raphael/index.json');
  if(!index)return;
  const profile=JSON.parse(text.decode(await checked(state,index)));
  if(state!==session)return;
  if(profile.profile!=='unispace-private-ternary-review-v1')throw Error('Unrecognized geometric shorthand.');
  state.geometry=profile;
  ui('role').replaceChildren(new Option('Empty','0'),...profile.roles.map(r=>new Option(r.id+' · '+r.name,String(r.slot))));
  ui('geometry').hidden=false;
  ui('role').onchange=()=>selectGeometry(state,Number(ui('role').value));
  ui('resolve-address').onclick=()=>{
    const value=ui('trits').value,slot=parseInt(value,3);
    if(!/^[012]{5}$/.test(value)||slot>173){
      ++geometryRevision;
      ui('mesh-view').getContext('2d').clearRect(0,0,480,280);ui('role').selectedIndex=-1;
      ui('show-role').disabled=ui('show-mesh').disabled=true;
      ui('geometry-note').textContent='Unassigned address. Choose 00000 through 20102.';
      return;
    }
    selectGeometry(state,slot);
  };
  await selectGeometry(state,0);
}
function filter() {
  const q = ui('query').value.toLowerCase();
  visible = session.rows.filter(r => (!quadrant || r.quadrant === quadrant) && r.path.toLowerCase().includes(q));
  ui('members').replaceChildren(...visible.map(r => new Option(r.path,r.path)));
  if (visible.length) ui('members').selectedIndex = 0;
  const total = visible.reduce((n,r) => n + r.size_bytes, 0);
  ui('series').disabled = !visible.length || visible.length > 64 || total > 524288;
  ui('matches').textContent = visible.length + ' files · ' + total + ' bytes' + (visible.length && ui('series').disabled ? ' · Narrow the filter to export this series.' : '');
  describe();
}
ui('carrier').onchange = async () => {
  const ticket = ++generation, file = ui('carrier').files[0];
  session = undefined; ui('workspace').hidden = true; ui('geometry').hidden=true; ++geometryRevision;
  ui('handshake').textContent = 'Waiting for a carrier.';
  if (!file) return;
  try {
    if (!globalThis.crypto?.subtle || !globalThis.DecompressionStream) throw Error('This browser lacks the required local reader features.');
    const library = document.querySelector('main').dataset;
    const allowed = [{size:3609020, hash:expected, name:'S91 product'}];
    if(library.librarySha)allowed.push({size:Number(library.librarySize),hash:library.librarySha,name:'review library'});
    if (!allowed.some(a=>a.size===file.size)) throw Error('Size differs from the carriers supported by this edition.');
    ui('handshake').textContent = 'Verifying carrier…';
    const raw = await file.arrayBuffer();
    const identity=await sha(raw);
    const match=allowed.find(a=>a.size===file.size && a.hash===identity);
    if (!match) throw Error('Carrier checksum mismatch.');
    const state = {file, entries: directory(raw)};
    const json = async p => JSON.parse(text.decode(await readMember(state,p)));
    const [boot, manifest, topology] = await Promise.all(['cgx/bootstrap.json','cgx/manifest.json','cgx/topology_index.json'].map(json));
    const coords = new Map(topology.nodes.map(n => [n.path,n]));
    state.rows = manifest.files.map(r => {
      const n = coords.get(r.path);
      if (!n || n.sha256 !== r.sha256 || n.bytes !== r.size_bytes) throw Error('Topology and manifest disagree.');
      return {...r, quadrant:n.quadrant, semantic_path:n.semantic_path, cell:n.cell};
    });
    if (ticket !== generation) return;
    session = state; session.boot = boot; session.digest=identity; quadrant = ''; ui('query').value = '';
    ui('identity').textContent = boot.state_id + ' · ' + boot.object_id;
    ui('quadrants').replaceChildren(...['',...new Set(state.rows.map(r=>r.quadrant).sort())].map(k => {
      const b = document.createElement('button'); b.type='button'; b.textContent=k || 'All quadrants';
      b.setAttribute('aria-pressed',String(!k)); b.onclick=()=>{quadrant=k;for(const x of b.parentNode.children)x.setAttribute('aria-pressed',String(x===b));filter();};return b;
    }));
    filter(); await prepareGeometry(state); if(ticket!==generation)return; ui('workspace').hidden=false;
    ui('handshake').textContent='Verified '+match.name+' · '+state.rows.length+' tracked files indexed. Select a file to read its contents.';
  } catch(e) { if(ticket===generation)ui('handshake').textContent=e.message; }
};
ui('query').oninput=filter; ui('members').onchange=describe;
function save(blob,name) {
  const url=URL.createObjectURL(blob), link=document.createElement('a');
  link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
}
for(const op of ['preview','export','series']) ui(op).onclick=async()=>{
  const state=session, rows=op==='series'?[...visible]:[visible[ui('members').selectedIndex]];
  try {
    if(!state || !rows.length || rows.some(r=>!r))return;
    if(op==='series' && (rows.length>64 || rows.reduce((n,r)=>n+r.size_bytes,0)>524288))throw Error('Series exceeds the export limit.');
    const files=[];
    for(const row of rows){
      const data=await checked(state,row);
      if(state!==session)return;
      if(op==='preview')ui('excerpt').textContent=text.decode(data.subarray(0,8192));
      else if(op==='export')save(new Blob([data],{type:'application/octet-stream'}),row.path.split('/').pop());
      else{
        let binary='';for(const byte of data)binary+=String.fromCharCode(byte);
        files.push({...row,bytes_base64:btoa(binary)});
      }
    }
    if(op==='series')save(new Blob([JSON.stringify({format:'unispace-filespace-series-v1',carrier_sha256:state.digest,
      object_id:state.boot.object_id,state_id:state.boot.state_id,content_root:state.boot.content_root,files})],{type:'application/json'}),'UniSpace-series.json');
    ui('action').textContent=op==='preview'?'Verified preview · first 8 KiB maximum.':'Verified export prepared.';
  }catch(e){if(state===session)ui('action').textContent=e.message;}
};
`,e.body.append(r),`<!doctype html>`+e.documentElement.outerHTML}export{e as readerDocument};