"""UniSpace owner-reviewed distributable SHELL package, not a release publisher.
Excludes LOAD/Alexandria, private datasets, host bridge, secrets and mint keys.
No network access, no external commands except local Node projection readback.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

SCHEMA="UNISPACE-PRODUCT-PREMINT-PACKAGE/0.1"
DANGEROUS=(b"-----BEGIN PRIVATE KEY-----",b"sk-proj-",b"ghp_",b"-----BEGIN OPENSSH PRIVATE KEY-----")
PROJECT=Path(__file__).resolve().parents[3]
def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def canonical(o):return (json.dumps(o,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
def require(cond:bool,why:str):
    if not cond:raise ValueError(why)
def safe_file(root:Path,path:str)->bytes:
    relative=PurePosixPath(path)
    require(not relative.is_absolute() and len(relative.parts)>0
            and all(p not in (".","..","") for p in relative.parts),"UNSAFE_PACKAGE_PATH")
    cur=root
    for part in relative.parts:
        cur=cur/part
        require(not cur.is_symlink(),"SYMLINK_NOT_ALLOWED")
    require(cur.is_file(),"MISSING_PACKAGE_FILE:"+path)
    data=cur.read_bytes()
    require(len(data)<2_000_000,"OVERSIZE_PUBLIC_ASSET")
    require(not any(marker in data for marker in DANGEROUS),"KEY_OR_SECRET_SIGNATURE")
    return data
class IndexAssets(HTMLParser):
    def __init__(self):super().__init__();self.assets=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="script" and "src" in a:self.assets.append(a["src"])
        if tag=="link" and a.get("rel")=="stylesheet":self.assets.append(a.get("href",""))
def extract_shell(build:Path):
    page=safe_file(build,"index.html")
    parsed=IndexAssets();parsed.feed(page.decode("utf-8"))
    require(len(parsed.assets)>=2 and len(parsed.assets)<=12,"INVALID_SHELL_REFERENCES")
    assets={"shell/index.html":page}
    for uri in parsed.assets:
        require(re.fullmatch(r"/assets/[A-Za-z0-9._-]+\.(?:js|css)",uri) is not None,
                "EXTERNAL_OR_UNSAFE_ASSET_REFERENCE")
        name=uri.lstrip("/")
        assets["shell/"+name]=safe_file(build,name)
    require(any(n.endswith(".js") for n in assets) and
            any(n.endswith(".css") for n in assets),"MISSING_JS_CSS")
    js=b"\n".join(v for k,v in assets.items() if k.endswith(".js"))
    require(b"CGX first-spaces lattice" in js and
            b"Export concept review JSON" in js,"CURRENT_REVIEW_GUI_NOT_IN_BUILD")
    return assets
def extract_viewer(viewer:Path):
    meta=json.loads(safe_file(viewer,"cgx-package-review.json"))
    require(meta.get("schema")=="CGX-PUBLIC-ALLOWLIST-PACKAGE/0.1" and
            meta.get("status")=="SOURCE_CANDIDATE_NOT_PUBLISHED_NOT_OWNER_SIGNED" and
            meta.get("file_count")==12 and len(meta.get("assets",[]))==12,
            "UNQUALIFIED_PUBLIC_VIEWER")
    paths=[]
    assets={}
    for item in meta["assets"]:
        path=item["path"]
        require(isinstance(path,str) and path.startswith("cgx/") and
                path.endswith((".html",".js",".css")) and path not in paths,
                "INVALID_PUBLIC_VIEWER_ALLOWLIST")
        data=safe_file(viewer,path)
        require(digest(data)==item["sha256"] and len(data)==item["bytes"],
                "PUBLIC_VIEWER_SOURCE_DIGEST_DRIFT")
        paths.append(path)
        assets["viewer/"+path]=data
    require(sum(len(x) for x in assets.values())==meta.get("source_bytes"),
            "VIEWER_BYTE_COUNT_DRIFT")
    return assets,digest(safe_file(viewer,"cgx-package-review.json"))
def static_lattice(repo:Path):
    js=("import {planFirstSpacesReview} from './apps/lightspeed-go/src/"
        "cgxFirstSpacesReviewModel.mjs';"
        "let p=planFirstSpacesReview();"
        "console.log(JSON.stringify({schema:p.schema,parent:p.canonical_parent,"
        "nodes:p.nodes.map(x=>({key:x.key,kind:x.kind,label:x.label,"
        "parent:x.parent,requires:x.requires,role:x.role})),"
        "edges:p.edges,sequence:p.mint_sequence,load_alias:p.library,"
        "native_minted:p.native_minted,may_sign:p.may_sign}));")
    cp=subprocess.run(["node","--input-type=module","-e",js],cwd=repo,
                      capture_output=True,text=True,timeout=15,check=True)
    x=json.loads(cp.stdout)
    require(x["parent"]=="cgx:root:cognigrex" and x["load_alias"]=="LOAD.cgx" and
            len(x["nodes"])==11 and len(x["sequence"])==11 and
            not x["native_minted"] and not x["may_sign"],"LATTICE_ADMISSION_MISMATCH")
    return x
def product_artifacts(build:Path,viewer:Path,repo:Path):
    files=extract_shell(build)
    public,public_digest=extract_viewer(viewer)
    files.update(public)
    lattice=static_lattice(repo)
    files["metadata/first-spaces-lattice.json"]=canonical(lattice)
    ccc={"schema":"CCC-NETWORK-PREMINT-PLAN/0.1","state":"PLANNED_NOT_CONNECTED",
         "host_network_active":False,"ccc_registry_minted":False,
         "sequence":["manual Founder review","accepted CGX identity and rights",
                     "qualified LOAD/CCC source and tool library entries",
                     "signed issuer and independent two-node DBR",
                     "scoped CCC capability network admission",
                     "scientific Grex operating acceptance",
                     "later fiction/game/Interdimensional Hang additions"],
         "lan_discovery":False,"device_handshake":False,
         "capability_grants":False,"native_signer":False,
         "nonowned_device_enrolment":False}
    files["metadata/ccc-next-network-plan.json"]=canonical(ccc)
    pkg=json.loads((repo/"apps/lightspeed-go/package.json").read_text(encoding="utf-8"))
    lock=json.loads((repo/"apps/lightspeed-go/package-lock.json").read_text(encoding="utf-8"))
    modules={}
    for name in ("vite","typescript","vitest"):
        resolved=lock.get("packages",{}).get("node_modules/"+name,{})
        modules[name]={"version":resolved.get("version","UNVERIFIED"),
                       "licence":"NOT_VERIFIED_IN_THIS_PACKAGE",
                       "included_runtime":False}
    files["metadata/component-inventory.json"]=canonical({
        "schema":"UNISPACE-PRODUCT-DEPENDENCY-INVENTORY/0.1",
        "app_version":pkg["version"],"build_tools":modules,
        "components":{"shell":"BROWSER_CLIENT_ONLY","viewer":"STATIC_ALLOWLIST_ONLY",
                      "fractal_lattice":"SOURCE_VIEW_GRAPH_NOT_NATIVE_OBJECT",
                      "ccc":"PLANNED_NOT_CONNECTED"},
        "external_not_bundled":["LOAD.cgx","Alexandria","Cognigrex native issuer",
                                "FileSpace private source carrier","DataSpace DBR",
                                "LightSpeed/Neo native execution","CCC network","device adapters"],
        "data_projection_policy":"PUBLIC_SOURCE_FIXTURES_NOT_BUNDLED; DYNAMIC PANELS MAY SHOW UNAVAILABLE"
    })
    readme=("UniSpace v"+pkg["version"]+" — private pre-mint product candidate\n"
      "======================================================\n"
      "shell/index.html : compiled UniSpace UI and first-spaces review control.\n"
      "viewer/cgx/index.html : separately allowlisted public-safe CGX preview.\n"
      "metadata/first-spaces-lattice.json : 11-node source-only topological model.\n"
      "metadata/ccc-next-network-plan.json : NOT an active network.\n"
      "All LOAD/Alexandria/native issuer/DBR/provider data and private review files are EXCLUDED.\n"
      "Some dynamic panels need authenticated external data and may show unavailable states.\n"
      "No license rights, native Object_IDs, mint authority, signing or publication are approved.\n"
      "This archive is a local packaging candidate, not a deployable production approval.\n")
    files["README.txt"]=readme.encode()
    hashes=[{"path":name,"sha256":digest(data),"bytes":len(data)}
            for name,data in sorted(files.items())]
    manifest={"schema":SCHEMA,"state":"CANDIDATE_PACKAGED_NOT_DEPLOYED",
              "product":"UniSpace","application_version":pkg["version"],
              "root_identity":"cgx:root:cognigrex","source_branch":"existing_PR_206",
              "private_host_dependencies_not_bundled":True,
              "native_mints_created":0,"root_issuer_signed":False,
              "dbr_admitted":False,"rights_qualified":False,
              "public_release_approved":False,"full_offline_functionality_claimed":False,
              "user_interface_compiled":True,"fractal_alignment":"STABLE_VIEW_LATTICE_ONLY",
              "viewer_allowlist_receipt_sha256":public_digest,
              "file_count_without_manifest":len(files),
              "asset_hashes":hashes,
              "holds":["source rights","native issuer and RootAuthority",
                       "independent two-node DBR","provider permissions",
                       "authenticated user and source projection",
                       "household pairing acceptance","production release"]}
    files["MANIFEST.json"]=canonical(manifest)
    return files,manifest
def create(build:Path,viewer:Path,out:Path,repo:Path=PROJECT):
    require(not out.exists(),"PACKAGE_ALREADY_EXISTS")
    build,viewer,repo=map(Path,(build,viewer,repo))
    files,manifest=product_artifacts(build,viewer,repo)
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_suffix(out.suffix+".partial")
    require(not tmp.exists(),"PARTIAL_ARCHIVE_EXISTS")
    try:
        with zipfile.ZipFile(tmp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name,data in sorted(files.items()):
                info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o100644<<16
                z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
        with zipfile.ZipFile(tmp) as z:
            require(z.testzip() is None,"ZIP_INTEGRITY_FAILURE")
            require(set(z.namelist())==set(files),"ZIP_ENTRY_MISMATCH")
            for name,data in files.items():
                require(z.read(name)==data,"ZIP_READBACK_DRIFT:"+name)
        tmp.rename(out)
    finally:
        if tmp.exists():tmp.unlink()
    report={"schema":"UNISPACE-PACKAGE-HOST-RECEIPT/0.1",
            "state":"LOCAL_CANDIDATE_VERIFIED_NO_PUBLISH",
            "archive_file":out.name,"archive_bytes":out.stat().st_size,
            "archive_sha256":digest(out.read_bytes()),
            "asset_count":len(files),"shell_assets":sum(x.startswith("shell/") for x in files),
            "public_viewer_assets":sum(x.startswith("viewer/") for x in files),
            "manifest_sha256":digest(files["MANIFEST.json"]),
            "external_load_alexandria_included":False,
            "source_rights_qualified":False,
            "native_minted":False,"signed":False,
            "published":False,"source_deleted":False}
    out.with_suffix(".receipt.json").write_bytes(canonical(report))
    return report
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--build",type=Path,required=True)
    p.add_argument("--viewer",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(create(a.build,a.viewer,a.out),sort_keys=True))
