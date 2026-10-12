#!/usr/bin/env python3
"""Isolated one-file offline game benchmark; no CGX source mutation."""
import argparse,base64,gzip,hashlib,json,re,struct
from pathlib import Path
SHA="7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d"
LABELS=["identity","map-topology","sector-geometry","actors","BSP","textures","patch-atlas","sprites","flats","palette","effects","music","UI","engine","provenance"]
def H(x):return hashlib.sha256(x).hexdigest()
def B(x):return base64.b64encode(x).decode("ascii")
def build(src:Path,dst:Path,n:int):
 assert 1<=n<=128
 wad=(src/"freedoom1.wad").read_bytes()
 wasm=(src/"websockets-doom.wasm").read_bytes()
 engine=(src/"websockets-doom.js").read_bytes()
 cfg=(src/"default.cfg").read_bytes()
 html=(src/"index.html").read_text()
 assert H(wad)==SHA, "Upstream WAD is not identical to verified Drive original!"
 magic,count,diroff=struct.unpack_from("<4sII",wad)
 assert magic==b"IWAD" and diroff+count*16<=len(wad)
 buckets=[[] for _ in range(n)]
 for i in range(count):
  off,size,name=struct.unpack_from("<II8s",wad,diroff+i*16)
  assert off+size<=len(wad)
  buckets[i%n].append((off,size))
 layers=[{"index":j,"label":LABELS[j] if n==15 else "partition-"+str(j+1),
 "lump_count":len(b),"bytes":sum(size for off,size in b),
 "sha256":H(b"".join(wad[off:off+size] for off,size in b))}
 for j,b in enumerate(buckets)]
 manifest={"schema":"CGX_DOOM_N_LAYER_READONLY_1","n_nodes":n,"n_layers":n,
 "n_geometric_interfaces":n,"key":"CGX-DOOM-15","key_is_secret":False,
 "wad_sha256":H(wad),"engine_wasm_sha256":H(wasm),"engine_js_sha256":H(engine),
 "partition_method":"WAD lump ordinal modulo N; reference geometry only, not extra information",
 "families":layers,"is_authoritative_public_release":False}
 decode="""function CGXB64(s){s=s.replace(/\\s+/g,'');var n=s.length;var out=new Uint8Array(n/4*3-(s.endsWith('==')?2:s.endsWith('=')?1:0));var p=0;for(var i=0;i<n;i+=131072){var a=atob(s.slice(i,i+131072));for(var j=0;j<a.length;j++)out[p++]=a.charCodeAt(j)}return out;}"""
 html=html.replace("'use strict';","'use strict';"+decode,1)
 pre="""preRun: function () {
  try { window.Module.FS.mkdir('/savefiles'); } catch(e) {}
  var w=CGXB64(document.getElementById('cgx-wad').textContent);
  var c=CGXB64(document.getElementById('cgx-cfg').textContent);
  window.Module.FS.createDataFile('/', 'freedoom1.wad', w, true, true);
  window.Module.FS.createDataFile('/', 'default.cfg', c, true, true);
  info('[cgx] local WAD/CFG data preloaded; no network');
 },
    onRuntimeInitialized:"""
 html,k=re.subn(r"preRun: function \(\) \{[\s\S]*?\n    \},\n\n    onRuntimeInitialized:",lambda _:pre,html,count=1)
 assert k==1
 newload="""info('[boot] CGX bundled engine');
  window.Module.wasmBinary=CGXB64(document.getElementById('cgx-wasm').textContent);"""
 html,k=re.subn(r"info\('\[boot\] loading engine…'\);[\s\S]*?document.body.appendChild\(s\);",lambda _:newload,html,count=1)
 assert k==1
 prep='<script id="cgx-wad" type="application/octet-stream">'+B(wad)+'</script>\n'
 prep+='<script id="cgx-wasm" type="application/octet-stream">'+B(wasm)+'</script>\n'
 prep+='<script id="cgx-cfg" type="application/octet-stream">'+B(cfg)+'</script>\n'
 prep+='<script id="cgx-manifest" type="application/json">'+json.dumps(manifest,separators=(',',':'))+'</script>\n'
 html=html.replace('<script>\n(function () {',prep+'<script>\n(function () {',1)
 source=re.sub(r'</script',r'<\\/script',engine.decode(),flags=re.I)
 html=html.replace('</body>','<script>'+source+'</script>\n</body>',1)
 assert 'id="cgx-wad"' in html and 'window.Module.wasmBinary' in html
 whole=html.encode()
 compressed=gzip.compress(whole,compresslevel=9,mtime=0)
 loader="""<!doctype html><html><head><meta charset="utf-8"><title>CGX DOOM OFFLINE ONE FILE</title></head>
<body style="background:#0d131a;color:#eee;font:16px system-ui;text-align:center;padding:12vh 3vw">
<h2>CGX / Freedoom — offline launch</h2><p id="state">Decoding self-contained game…</p>
<script type="application/octet-stream" id="cgx-gzip">__PAYLOAD__</script>
<script>(async()=>{
try{if(!window.DecompressionStream)throw Error('Modern browser required');
var s=document.getElementById('cgx-gzip').textContent.trim(),parts=[];
for(var i=0;i<s.length;i+=131072){var t=atob(s.slice(i,i+131072)),a=new Uint8Array(t.length);for(var j=0;j<t.length;j++)a[j]=t.charCodeAt(j);parts.push(a);}
var t=await new Response(new Blob(parts).stream().pipeThrough(new DecompressionStream('gzip'))).text();
document.open();document.write(t);document.close();
}catch(e){document.getElementById('state').textContent='FAILED: '+e.message;}})();</script></body></html>"""
 single=loader.replace("__PAYLOAD__",B(compressed)).encode()
 dst.mkdir(exist_ok=True,parents=True)
 (dst/"CGX_FREEDOOM_ONE_CLICK_OFFLINE.html").write_bytes(single)
 (dst/"CGX_N_LAYER_PROFILE.json").write_text(json.dumps(manifest,indent=2))
 sizes={"wad_bytes":len(wad),"wasm_bytes":len(wasm),"engine_loader_bytes":len(engine),"embedded_html_uncompressed_bytes":len(whole),
 "embedded_html_gzip_bytes":len(compressed),"one_file_html_bytes":len(single),
 "original_wad_sha256":H(wad),"onefile_sha256":H(single),"n":n,
 "first_install_is_not_delta_only":True,"gameplay_engine_runtime_verified":False}
 (dst/"CGX_SIZE_AND_PROOF.json").write_text(json.dumps(sizes,indent=2))
 (dst/"README_AND_LICENSES.md").write_text(
 "# CGX / Freedoom One-File Offline Benchmark\n\n"
 "Download and double-click CGX_FREEDOOM_ONE_CLICK_OFFLINE.html in a modern browser, then click TAP TO START. "
 "This contains actual open-source Chocolate Doom WebAssembly and the full Freedoom 0.13.0 Phase 1 IWAD.\n\n"
 "Runtime: https://github.com/danborden1/doom-web/tree/e0ba81004e27e7d66141925dfebb091a558e2fe8 ; engine GNU GPL-2.0, corresponding source https://github.com/Saketh-Chandra/doom-wasm-pwa/tree/a77edfd8bbc7 ; Freedoom BSD-3-Clause https://freedoom.github.io/ .\n"
 "Full text licences COPYING and FREEDOOM-COPYING.txt from engine source should accompany further public redistribution.\n\n"
 "The shared N-layer graph references actual IWAD lump slices. It does not make game bytes appear out of a key. "
 "One-file first download and later 119-byte recorded tic-delta are different measurements; the 119-byte record cannot by itself play the game. "
 "Browser gameplay remains to be observed on a real independent device.\n")
 print(json.dumps(sizes,indent=2))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--layers",type=int,default=15)
 a=p.parse_args();build(a.source,a.output,a.layers)
