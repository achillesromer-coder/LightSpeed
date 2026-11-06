"""Private UOS integration distribution packer, extending the UniSpace shell candidate.
Packages existing tracked native LightSpeed runtime source as a separate component.
Neither this package nor its readiness receipt authorises a public release, mint or deploy.
"""
from __future__ import annotations
import argparse, ast, io, json, re, subprocess, zipfile
from pathlib import Path, PurePosixPath
from package_unispace_premint import (PROJECT,canonical,create as create_shell,
  digest,require,product_artifacts,DANGEROUS)
SCHEMA="UNISPACE-UOS-INTEGRATION-CANDIDATE/0.1"
PREFIX="desktop/LightSpeed_Runtime/"
MODULE_PREFIX=PREFIX+"lightspeed_runtime/"
REQS=(PREFIX+"requirements-core.txt",PREFIX+"requirements-api.txt",
      PREFIX+"requirements-desktop.txt")
REQUIRED=("runtime.py","contracts.py","storage_paths.py","operator_os.py",
          "cgx_capability_registry.py","node_exchange.py","bridge_health.py",
          "desktop_adapters.py","runtime_productization.py")
PRIVATE_ALLOWLIST=(
  "UNVERIFIED_ORIGINAL_SOURCE_RIGHTS",
  "UNVERIFIED_NATIVE_ISSUER_AND_ROOTAUTHORITY",
  "NO_INDEPENDENT_TWO_NODE_DBR_ACCEPTANCE",
  "NO_PROVEN_AUTHENTICATED_FILESPACE_AND_DATASPACE",
  "NO_VALIDATED_DISTRIBUTABLE_OS_INSTALLERS",
  "NO_LIVE_HOUSEHOLD_DEVICE_CONSENT_OR_LEASES",
  "NO_PUBLISHED_SECURITY_OR_SIGNATURE_ATTESTATION",
  "NO_PRODUCTION_HOST_NEGATIVE_TEST_ACCEPTANCE",
)
def index_bytes(repo:Path,rel:str)->bytes:
    require(bool(re.fullmatch(r"[A-Za-z0-9_./-]+",rel)) and
            ".." not in PurePosixPath(rel).parts and not rel.startswith("/"),
            "INVALID_REPO_RELATIVE_PATH")
    mode=subprocess.run(["git","ls-files","--stage","--",rel],cwd=repo,
                        capture_output=True,text=True,timeout=15,check=True).stdout
    require(mode.startswith("100644 ") or mode.startswith("100755 "),"NOT_REGULAR_GIT_INDEX_FILE")
    data=subprocess.run(["git","show",":"+rel],cwd=repo,capture_output=True,
                        timeout=15,check=True).stdout
    require(len(data)<1_000_000,"NATIVE_SOURCE_FILE_TOO_LARGE")
    require(not any(m in data for m in DANGEROUS),"NATIVE_SOURCE_SECRET_MARKER")
    return data
def list_runtime_paths(repo:Path)->list[str]:
    result=subprocess.run(["git","ls-files","--",MODULE_PREFIX],cwd=repo,
                          capture_output=True,text=True,timeout=15,check=True)
    paths=[x.strip().replace("\\","/") for x in result.stdout.splitlines()
           if x.strip().endswith(".py")]
    require(len(paths)>=80,"NATIVE_RUNTIME_SOURCE_UNDERSPECIFIED")
    require(len(paths)==len(set(paths)),"RUNTIME_DUPLICATE_PATH")
    require(all(MODULE_PREFIX+x in paths for x in REQUIRED),"NATIVE_RUNTIME_CRITICAL_MODULE_MISSING")
    return sorted(paths)
def runtime_assets(repo:Path):
    paths=list_runtime_paths(repo)
    out={}
    for rel in [*paths,*REQS]:
        contents=index_bytes(repo,rel)
        if rel.endswith(".py"):
            ast.parse(contents.decode("utf-8-sig"),filename=rel)
        out["native/"+rel[len(PREFIX):]]=contents
    return out,len(paths)
def uos_artifacts(build:Path,viewer:Path,repo:Path):
    assets,shell=product_artifacts(build,viewer,repo)
    native,count=runtime_assets(repo)
    require(not set(assets)&set(native),"OVERLAPPING_PACKAGE_PATH")
    assets.update(native)
    matrix=[
      {"id":"frontend_ui","state":"SOURCE_COMPILED","proof":"compiled asset hashes"},
      {"id":"public_viewer","state":"SOURCE_VERIFIED","proof":"12-file allowlist hashes"},
      {"id":"first_spaces","state":"SOURCE_MODEL_ONLY","proof":"11-node pinned dependency graph"},
      {"id":"load_batch_preparation","state":"LOCAL_UNSIGNED_METADATA_REVIEW","proof":"local index import, source inspection, deterministic batches and verified draft restore; chain binding unset"},
      {"id":"native_runtime","state":"SOURCE_PACKAGED_NOT_INSTALLED","proof":f"{count} Python syntax-qualified modules"},
      {"id":"desktop_shell","state":"NOT_BUNDLED","proof":"portable signed installers not accepted"},
      {"id":"macos_shell","state":"UNVERIFIED","proof":"OS integration and signing untested"},
      {"id":"linux_shell","state":"UNVERIFIED","proof":"OS integrations untested"},
      {"id":"filespace","state":"EXTERNAL_AUTHENTICATION_HOLD","proof":"source rights/ACL unqualified"},
      {"id":"dataspace","state":"INDEPENDENT_DBR_HOLD","proof":"no signed two-node DBR acceptance"},
      {"id":"ccc_skills_tools","state":"PLANNED_NOT_CONNECTED","proof":"native grants/lease/owner receipts held"},
      {"id":"load_alexandria","state":"EXTERNAL_NOT_BUNDLED","proof":"resolver/admission retained as separate systems"},
      {"id":"socialspace","state":"BILATERAL_OPT_IN_AND_AI_POLICY_HOLD","proof":"existing UniSpace extension; no automatic activation"},
      {"id":"printspace","state":"MEASURED_OUTPUT_ACCEPTANCE_HOLD","proof":"source model is not physical validation"},
      {"id":"native_mint","state":"BLOCKED","proof":"no verified issuer, transactions or RootAuthority"},
      {"id":"device_network","state":"BLOCKED","proof":"no OS consent/attested household endpoints"},
      {"id":"rights_distribution","state":"BLOCKED","proof":"per-component licences not accepted"}
    ]
    assets["metadata/operational-acceptance-matrix.json"]=canonical({
      "schema":"UOS-OPERATIONAL-ACCEPTANCE-MATRIX/0.1",
      "release_ready":False,"end_to_end_verified":False,
      "native_runtime_source_count":count,
      "features":matrix,"blocking_gates":list(PRIVATE_ALLOWLIST)})
    assets["metadata/native-runtime-policy.json"]=canonical({
      "schema":"UOS-PRIVATE-NATIVE-SOURCE-STAGING/0.1",
      "state":"SOURCE_ONLY_PRIVATE_NOT_INSTALLABLE",
      "python_files":count,
      "source":"Git indexed tracked code only, no runtime config or generated user data",
      "dependency_files":[x[len(PREFIX):] for x in REQS],
      "external_runtime_requirements":"Python plus pinned dependencies; exact OS builds and licences unqualified",
      "native_issuer":False,"ccc_activated":False,"source_deletion":False,
      "cross_platform_installers_verified":False,
      "runtime_execute_automatically":False,
      "source_rights_qualified":False})
    manifest={"schema":SCHEMA,"state":"PRIVATE_INTEGRATION_CANDIDATE_NOT_PUBLIC_RELEASE",
      "product":"UniSpace UOS integration (not full end-to-end accepted)",
      "build_profile":"UOS_PRIVATE_ASSEMBLY",
      "native_runtime_python_files":count,
      "shell_manifest_schema":shell["schema"],
      "external_load_alexandria":True,
      "contents":sorted([{"path":name,"bytes":len(data),"sha256":digest(data)}
                         for name,data in assets.items()],key=lambda x:x["path"]),
      "all_gates_accepted":False,"public_release_allowed":False,
      "native_minted":False,"signed":False,"ccc_network_activated":False,
      "physical_devices_paired":False,"source_deleted":False,
      "release_blockers":list(PRIVATE_ALLOWLIST)}
    assets["UOS_INTEGRATION_MANIFEST.json"]=canonical(manifest)
    return assets,manifest
def verify_uos_archive(path:Path):
    with zipfile.ZipFile(path) as z:
        infos=z.infolist()
        require(len(infos)<=500 and sum(i.file_size for i in infos)<=30_000_000,
                "ARCHIVE_BUDGET_EXCEEDED")
        require(z.testzip() is None,"ZIP_INTEGRITY_ERROR")
        names=z.namelist()
        require(len(names)==len(set(names)) and
                "UOS_INTEGRATION_MANIFEST.json" in names,"INTEGRATION_MANIFEST_MISSING")
        for name in names:
            require(bool(re.fullmatch(r"[A-Za-z0-9_./-]+",name)) and
                    not name.startswith("/") and
                    all(part not in ("", ".", "..") for part in name.split("/")),
                    "UNSAFE_ARCHIVE_PATH")
        require(all((i.external_attr >> 16) & 0o170000 != 0o120000 for i in infos),
                "SYMLINK_ARCHIVE_MEMBER")
        m=json.loads(z.read("UOS_INTEGRATION_MANIFEST.json"))
        require(m.get("schema")==SCHEMA and
                m.get("state")=="PRIVATE_INTEGRATION_CANDIDATE_NOT_PUBLIC_RELEASE" and
                all(m.get(k) is False for k in ("public_release_allowed","native_minted",
                  "signed","ccc_network_activated","physical_devices_paired","source_deleted",
                  "all_gates_accepted")) and m.get("release_blockers")==list(PRIVATE_ALLOWLIST),
                "UNSAFE_RELEASE_MANIFEST")
        contents=m.get("contents")
        require(isinstance(contents,list) and all(isinstance(a,dict) and
                set(a)=={"path","bytes","sha256"} for a in contents),"INVALID_ASSET_MANIFEST")
        listed=[a["path"] for a in contents]
        require(all(isinstance(n,str) for n in listed) and len(listed)==len(set(listed)) and
                set(listed)==set(names)-{"UOS_INTEGRATION_MANIFEST.json"},
                "ARCHIVE_MEMBERSHIP_MISMATCH")
        for a in contents:
            b=z.read(a["path"])
            require(type(a["bytes"]) is int and digest(b)==a["sha256"] and len(b)==a["bytes"],
                    "ARCHIVE_DIGEST_MISMATCH")
        policy=json.loads(z.read("metadata/native-runtime-policy.json"))
        matrix=json.loads(z.read("metadata/operational-acceptance-matrix.json"))
        require(policy.get("state")=="SOURCE_ONLY_PRIVATE_NOT_INSTALLABLE" and
                all(policy.get(k) is False for k in ("native_issuer","ccc_activated",
                    "source_deletion","cross_platform_installers_verified",
                    "runtime_execute_automatically","source_rights_qualified")) and
                matrix.get("release_ready") is False and matrix.get("end_to_end_verified") is False and
                matrix.get("blocking_gates")==list(PRIVATE_ALLOWLIST),"UNSAFE_RUNTIME_POLICY")
        modules=sum(n.startswith("native/lightspeed_runtime/") and n.endswith(".py") for n in listed)
        require(type(m.get("native_runtime_python_files")) is int and modules>=80 and
                modules==m["native_runtime_python_files"]==policy.get("python_files")==
                matrix.get("native_runtime_source_count"),"RUNTIME_MODULE_COUNT_DRIFT")
        return m

def create(build:Path,viewer:Path,out:Path,repo:Path=PROJECT):
    require(not out.exists(),"PACKAGE_ALREADY_EXISTS")
    assets,manifest=uos_artifacts(Path(build),Path(viewer),Path(repo))
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_suffix(out.suffix+".partial")
    require(not tmp.exists(),"INCOMPLETE_ARCHIVE_PREEXISTS")
    try:
        with zipfile.ZipFile(tmp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for name,data in sorted(assets.items()):
                info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o100644<<16
                z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
        check=verify_uos_archive(tmp)
        require(check["native_runtime_python_files"]>=80,"RUNTIME_MODULE_COUNT_DRIFT")
        tmp.rename(out)
    finally:
        if tmp.exists():tmp.unlink()
    result={"schema":"UOS-PRIVATE-INTEGRATION-HOST-RECEIPT/0.1",
        "state":"PRIVATE_INTEGRATION_PACKAGED_NOT_PUBLIC",
        "archive_name":out.name,"archive_bytes":out.stat().st_size,
        "sha256":digest(out.read_bytes()),"entries":len(assets),
        "native_modules":manifest["native_runtime_python_files"],
        "status":"REQUIRES_RUNTIME_INSTALLATION_AND_NATIVE_PROOF",
        "public_release_allowed":False,"signed":False,"native_minted":False,
        "ccc_activated":False,"devices_paired":False,
        "source_originals_retained":True}
    out.with_suffix(".receipt.json").write_bytes(canonical(result))
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--build",type=Path,required=True)
    p.add_argument("--viewer",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(create(args.build,args.viewer,args.out),sort_keys=True))
