"""Generate exact N-layer static WAD from the verified one-file engine bundle."""
from pathlib import Path
import base64, gzip, hashlib, json, math, re

def h(x): return hashlib.sha256(x).hexdigest()
def b(x): return base64.b64encode(x).decode("ascii")

def build(root: Path, n: int = 15):
    assert 1 <= n <= 128
    file=root/"CGX_FREEDOOM_ONE_CLICK_OFFLINE.html"
    source=file.read_text()
    zipped=re.search(r'(<script type="application/octet-stream" id="cgx-gzip">)([^<]+)(</script>)',source)
    assert zipped
    inner=gzip.decompress(base64.b64decode(zipped.group(2))).decode()
    wadtag=re.search(r'<script id="cgx-wad" type="application/octet-stream">([^<]+)</script>',inner)
    assert wadtag
    wad=base64.b64decode(wadtag.group(1))
    assert h(wad)=="7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d"
    chunk_size=math.ceil(len(wad)/n)
    chunks=[wad[i*chunk_size:min(len(wad),(i+1)*chunk_size)] for i in range(n)]
    assert b"".join(chunks)==wad
    profile=json.loads(re.search(r'<script id="cgx-manifest" type="application/json">([^<]+)</script>',inner).group(1))
    profile["schema"]="cgx-doom-sharded-real-bytes-v1"
    profile["n_layers"]=n
    profile["wad_bytes"]=len(wad)
    profile["fragments"]=[{"id":"wad-%02d"%(i+1),"ordinal":i,"offset":i*chunk_size,
          "size":len(v),"sha256":h(v)} for i,v in enumerate(chunks)]
    profile["model_status"]="EXACT WAD BYTE SHARDS, NOT FREE COMPRESSION"
    inner=re.sub(r'<script id="cgx-manifest" type="application/json">[^<]+</script>',
         lambda m:'<script id="cgx-manifest" type="application/json">'+json.dumps(profile,separators=(",",":"))+'</script>',inner,count=1)
    tags="\n".join('<script id="cgx-shard-%02d" type="application/octet-stream">%s</script>'%(i+1,b(v)) for i,v in enumerate(chunks))
    inner=inner.replace(wadtag.group(0),tags,1)
    original="""  var w=CGXB64(document.getElementById('cgx-wad').textContent);
  var c=CGXB64(document.getElementById('cgx-cfg').textContent);
  window.Module.FS.createDataFile('/', 'freedoom1.wad', w, true, true);"""
    new="""  var graph=JSON.parse(document.getElementById('cgx-manifest').textContent);
  if(graph.fragments.length!==graph.n_layers) throw Error('CGX layer count mismatch');
  var w=new Uint8Array(graph.wad_bytes),cursor=0;
  for(var k=0;k<graph.n_layers;k++){
    var node=graph.fragments[k],e=document.getElementById('cgx-shard-'+String(k+1).padStart(2,'0'));
    if(!e||node.ordinal!==k||node.offset!==cursor)throw Error('CGX missing layer '+k);
    var bytes=CGXB64(e.textContent);
    if(bytes.length!==node.size||cursor+bytes.length>w.length)throw Error('CGX corrupt shard');
    w.set(bytes,cursor);cursor+=bytes.length;
  }
  if(cursor!==w.length)throw Error('CGX incomplete geometry');
  var c=CGXB64(document.getElementById('cgx-cfg').textContent);
  window.Module.FS.createDataFile('/', 'freedoom1.wad', w, true, true);
  info('[cgx] '+graph.n_layers+' independently addressed static layers reconstructed exact IWAD');"""
    assert original in inner
    inner=inner.replace(original,new,1)
    controls="""      boot.classList.add('hidden');
      pad.classList.remove('hidden');"""
    assert controls in inner
    inner=inner.replace(controls,"""      boot.classList.add('hidden');
      if(navigator.maxTouchPoints>0||(matchMedia&&matchMedia('(pointer:coarse)').matches))
        pad.classList.remove('hidden');""",1)
    zipped2=gzip.compress(inner.encode(),compresslevel=5,mtime=0)
    rebuilt=source[:zipped.start(2)]+b(zipped2)+source[zipped.end(2):]
    output=root/"CGX_FREEDOOM_N15_OFFLINE_SHARDED.html"
    output.write_text(rebuilt)
    (root/"CGX_N15_SHARDED_PROFILE.json").write_text(json.dumps(profile,indent=2))
    (root/"CGX_N15_SHARDED_SIZE.json").write_text(json.dumps({"monolithic_bytes":file.stat().st_size,
          "sharded_bytes":output.stat().st_size,"wad_bytes":len(wad),"wad_sha256":h(wad),
          "onefile_sha256":h(rebuilt.encode()),"n_layers":n,
          "initial_download_not_replaced_by_small_key":True},indent=2))
    print("N-LAYER-EXACT-RECONSTRUCTION-PASS",output.stat().st_size)
if __name__=="__main__":
    build(Path("out"))
