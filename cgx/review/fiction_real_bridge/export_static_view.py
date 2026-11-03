"""Standalone bounded static mirror packaging for operator-controlled review.
Usage:
  python export_static_view.py --output-dir <new_review_folder>
Does NOT publish online, modify S92, or write an operational database.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from bridge_engine import compile_graph

def main(argv=None):
 parser=argparse.ArgumentParser()
 parser.add_argument("--output-dir",type=Path,required=True)
 args=parser.parse_args(argv)
 repo=Path(__file__).resolve().parent
 graphfile=repo/"MIRROR_GRAPH_REVIEW_V2.json"
 ui=repo/"ui"
 if not ui.is_dir():raise SystemExit("UI source directory missing")
 doc=json.loads(graphfile.read_text(encoding="utf-8-sig"))
 candidate=compile_graph(doc)
 if candidate["graph_sha256"]!=doc["graph_sha256"]:raise SystemExit("metadata graph digest mismatch")
 if candidate["native_admission"] is not False:raise SystemExit("not review-only")
 destination=args.output_dir.resolve()
 forbidden={Path(r"C:\Cognigrex").resolve(),Path(r"D:\LightSpeed\Repositories\LightSpeed_Canonical").resolve()}
 if any(destination==f or f in destination.parents for f in forbidden):
  raise SystemExit("refusing to write into native or canonical directories")
 dest_parent=destination.parent
 if not dest_parent.exists():raise SystemExit("output parent must exist")
 if destination.exists() and any(destination.iterdir()):raise SystemExit("output directory not empty; refuse overwrite")
 destination.mkdir(exist_ok=True)
 film=next(n["id"] for n in candidate["nodes"] if n["identity_key"]=="film:hackers-1995")
 out={"schema":doc["schema"],"graph_sha256":doc["graph_sha256"],
      "parent":doc["parent"],"native_admission":False,"metadata_only":True,
      "sources":doc["sources"],"nodes":doc["nodes"],"mentions":doc["mentions"],"edges":doc["edges"],
      "presentation":{"film_context_id":film,
                      "scene_title":"Hackers (1995) - Cyberdelia scene",
                      "scene_mentions":[m["id"] for m in doc["mentions"] if m["context_node"]==film]}}
 data=(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
 (destination/"graph.json").write_bytes(data)
 for name in ("index.html","mirror.css","mirror.js"):
  (destination/name).write_bytes((ui/name).read_bytes())
 print(json.dumps({"output_dir":str(destination),"graph_sha256":doc["graph_sha256"],
                   "static_graph_sha256":hashlib.sha256(data).hexdigest(),
                   "files":4,"native_mint":False},indent=2))
if __name__=="__main__":main()