#!/usr/bin/env python3
"""No-guess, non-mutating PDS Apophis bundle intake preflight.

Run: python3 apps/public/asteroids/apophis/tools/inspect_pds_bundle.py <downloaded_zip>
This script does NOT infer units/frame/spin and does NOT promote an unqualified mesh.
"""
from __future__ import annotations
import argparse, pathlib, zipfile, hashlib, json, sys
def main():
    p=argparse.ArgumentParser()
    p.add_argument("zip_path",type=pathlib.Path)
    p.add_argument("--max-uncompressed-mb",type=int,default=25)
    args=p.parse_args()
    data=args.zip_path.read_bytes()
    checkhash=hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(args.zip_path) as z:
        files=[i for i in z.infolist() if not i.is_dir()]
        if sum(x.file_size for x in files)>args.max_uncompressed_mb*1024*1024: raise ValueError("Uncompressed archive exceeds bound")
        for i in files:
            path=pathlib.PurePosixPath(i.filename)
            if ".." in path.parts or path.is_absolute():raise ValueError("Unsafe archive member path "+str(path))
        labels=[x.filename for x in files if x.filename.lower().endswith(".xml")]
        candidates=[{"path":x.filename,"bytes":x.file_size,"kind":"candidate only, not validated"} for x in files if x.filename.lower().endswith((".obj",".tab",".ply",".stl",".txt",".mesh",".dat"))]
        report={"status":"UNQUALIFIED_SOURCE_INTAKE_ONLY","download_file":args.zip_path.name,"sha256":checkhash,"archive_bytes":len(data),"files":len(files),"labels":labels,"candidate_geometry_files":candidates,"source_doi":"10.26033/ydyq-5756","must_validate":["label/source ID and DOI","vertex and face indexing","coordinate frame and handedness","length scale and physical units","spin epoch and non-principal-axis dynamics","watertightness, winding and normal orientation","mesh volume and diameter vs source","rights and scholarly attribution","geometry-derived uncertainty and resolution"],"approval_state":"HOLD — no public scientific-mesh promotion"}
        print(json.dumps(report,indent=2))
if __name__=="__main__":
    try:main()
    except Exception as e:print("FAIL:",str(e),file=sys.stderr);sys.exit(1)
