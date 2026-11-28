"""Read-only model footprint accounting; no inference, blob reads or admission."""
import hashlib,json,re
from pathlib import Path
from lightspeed_runtime.achilles.native_geometry import digest,require

def inventory(root):
    """Measure manifest-declared references and size-matched local blobs.
    Registered digests are not verified content hashes; do not infer model equivalence.
    """
    root=Path(root).resolve()
    manifest_root=(root/"manifests").resolve()
    blobs=(root/"blobs").resolve()
    require(manifest_root.is_relative_to(root) and blobs.is_relative_to(root),"store boundary")
    require(manifest_root.is_dir() and blobs.is_dir(),"model store missing")
    files=sorted(p for p in manifest_root.rglob("*") if p.is_file())
    require(1<=len(files)<=256,"manifest count")
    seen={};rows=[];logical=0;missing=set();mismatch=set();model_weights={}
    for p in files:
        require(p.resolve().is_relative_to(manifest_root),"manifest boundary")
        with p.open("rb") as f: raw=f.read(65537)
        require(0<len(raw)<=65536,"manifest size")
        def unique(pairs):
            out={}
            for k,v in pairs:
                require(k not in out,"duplicate manifest key");out[k]=v
            return out
        m=json.loads(raw,object_pairs_hook=unique)
        require(m.get("schemaVersion")==2 and type(m.get("config")) is dict,"manifest schema")
        layers=m.get("layers")
        require(layers is None or type(layers) is list and len(layers)<=128,"layer bound")
        refs=[m["config"]]+(layers or [])
        local=0;weights=0;count=0
        for ref in refs:
            require(type(ref) is dict,"layer schema")
            h=ref.get("digest");n=ref.get("size");kind=ref.get("mediaType")
            require(type(h) is str and re.fullmatch(r"sha256:[0-9a-f]{64}",h) and type(n) is int and 0<=n<=2**50 and type(kind) is str,"blob reference")
            require(h not in seen or seen[h]==n,"conflicting blob size")
            seen[h]=n
            q=blobs/h.replace(":","-")
            require(q.resolve().is_relative_to(blobs),"blob boundary")
            if not q.is_file():missing.add(h);continue
            if q.stat().st_size!=n:mismatch.add(h);continue
            local+=n;count+=1
            if kind=="application/vnd.ollama.image.model":
                weights+=n;model_weights[h]=n
        logical+=local
        rows.append({"manifest":p.relative_to(manifest_root).as_posix(),"manifest_sha256":hashlib.sha256(raw).hexdigest(),
                     "local_reference_bytes":local,"local_model_weight_reference_bytes":weights,
                     "matching_local_references":count,"cloud_or_no_weight_layers":not any(x.get("mediaType")=="application/vnd.ollama.image.model" for x in layers or [])})
    good={h:n for h,n in seen.items() if h not in missing and h not in mismatch}
    unique_bytes=sum(good.values())
    body={"schema":"CGX-IM-MODEL-FOOTPRINT-REVIEW/0.1","manifests":rows,"manifest_count":len(rows),
          "size_matched_unique_blob_count":len(good),"size_matched_reference_bytes":logical,
          "size_matched_unique_blob_bytes":unique_bytes,"repeated_reference_bytes":logical-unique_bytes,
          "unique_weight_blob_bytes":sum(n for h,n in model_weights.items() if h in good),
          "missing_blob_count":len(missing),"size_mismatch_count":len(mismatch),
          "blob_content_hash_verified":False,"inference_verified":False,"native_admitted":False}
    return {"review":body,"sha256":digest(body)}
