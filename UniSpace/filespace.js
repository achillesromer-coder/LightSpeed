'use strict';
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
  session = undefined; ui('workspace').hidden = true;
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
    filter(); ui('workspace').hidden=false;
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
