"""Fail-closed static public-asset audit for the current UniSpace/LS GO build.

Known internal CGX engineering review content under Vite public/ requires owner
clearance and authenticated serving, not a static-root filename change.
This scanner cannot prove remote deployment behavior or comprehensive absence
of private material. --strict blocks release while known risks remain.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_PUBLIC = "apps/lightspeed-go/public"
EXACT_HOLDS = {
    "data/cgx_object_review_catalogue.json": "PRIVATE_OBJECT_CATALOGUE_REVIEW",
    "data/component_geometry_atlas_public_review.json": "INTERNAL_COMPONENT_ATLAS_REVIEW",
}
DIR_HOLDS = {
    "review/renders": "INTERNAL_REVIEW_RENDER",
    "review/mesh": "INTERNAL_REVIEW_MESH",
}
MAX_SCAN = 50_000

def audit_public_assets(root: Path=ROOT) -> dict:
    public=root/SITE_PUBLIC
    blocked=[]
    for rel,reason in EXACT_HOLDS.items():
        p=public/rel
        if p.is_file():
            blocked.append({"static_route":"/"+rel,"reason":reason,
                            "root_relative":SITE_PUBLIC+"/"+rel})
    for rel,reason in DIR_HOLDS.items():
        folder=public/rel
        if not folder.is_dir(): continue
        for p in sorted(folder.rglob("*")):
            if not p.is_file() or p.is_symlink(): continue
            relative=p.relative_to(public).as_posix()
            blocked.append({"static_route":"/"+relative,"reason":reason,
                            "root_relative":SITE_PUBLIC+"/"+relative})
            if len(blocked)>MAX_SCAN: raise ValueError("public asset audit size bound")
    blocked=sorted(blocked,key=lambda x:x["static_route"])
    return {
        "schema":"CGX-UNISPACE-PUBLIC-ASSET-BOUNDARY-AUDIT/0.1",
        "site_root":SITE_PUBLIC,
        "state":"HOLD_PUBLIC_RELEASE" if blocked else "NO_KNOWN_PATH_BLOCKERS_UNVERIFIED",
        "known_internal_static_file_count":len(blocked),
        "known_internal_static_files":blocked,
        "release_authorised":False,
        "runtime_authenticated":False,
        "negative_live_http_tests":"NOT_PERFORMED",
        "private_server_acl":"NOT_VERIFIED",
        "owner_asset_rights":"NOT_VERIFIED",
        "static_build_disclosure":"Vite publicDir copies files directly to distributable static paths",
        "requirements":[
            "Remove/rehome internal review catalogues, meshes and renders outside Vite publicDir before public build",
            "Serve needed private reviews only through current authenticated owner resolver with project/role ACL and short-lived grants",
            "Verify the target build output does not contain held source bytes or filenames",
            "Independently test unauthenticated, revoked and cross-tenant HTTP access on actual deployed host",
            "Allowlist only individually rights-cleared public-safe assets with SHA-256/owner evidence",
            "Repeat public/private audit at every build after migration"
        ],
        "limits":"Only named CGX review source patterns are scanned. A clean report is NOT sufficient public-release authorization."
    }

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--strict",action="store_true",help="fail closed if known private assets still live under public/")
    cli.add_argument("--root",default=None,help="repository root; default location derived from this source")
    a=cli.parse_args()
    result=audit_public_assets(Path(a.root) if a.root else ROOT)
    print(json.dumps(result,indent=2))
    if a.strict and result["known_internal_static_file_count"]>0:
        raise SystemExit(2)
