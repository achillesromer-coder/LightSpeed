"""CGX isolated public release bundle — deny-by-default source packaging.

This is a source-only package planner. It copies only reviewed static /cgx
demonstration files into a fresh separate output directory. It NEVER copies the
operator's other Vite public/ assets, grants rights, deploys, signs or authenticates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "apps/lightspeed-go/public/cgx"

# Exact paths, NOT a wildcard under apps/lightspeed-go/public/.
APPROVED = frozenset({
    "index.html","fs/index.html","ds/index.html","ps/index.html",
    "doom/index.html","romer/index.html","eco/index.html",
    "assets/core.js","assets/viewer.js","assets/viewer.css",
    "assets/domain-overviews.js","assets/domain-viewer.js",
})
REQUIRED_CONTEXT = (
    "PUBLIC_SAFE_SYNTHETIC",
    "unispace-cgx-public-demonstration/1",
)
BLOCKED = {
    "operator bridge": re.compile(r"desktopBridge|ownerAuth|lightspeed_runtime|ls_go_job_consumer",re.I),
    "internal review catalogue": re.compile(
        r"cgx_object_review_catalogue|component_geometry_atlas_public_review|cgx_internal_review_projection",re.I),
    "private assets path": re.compile(r"(?<![a-z])/review/(?:mesh|renders)|/data/(?:cgx|component_geometry)",re.I),
    "native owner APIs": re.compile(r"/api/(?:v1|owner)|https?://(?:127\.0\.0\.1|localhost)(?::\d+)?/",re.I),
    "credential syntax": re.compile(r"(?:sk-proj-|ghp_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)",re.I),
    "root escape": re.compile(r"(?:^|[/'\"])\.\.[\\/]",re.M),
}
MAX_FILE_BYTES=250_000
MAX_BYTES=1_000_000

class BundleHold(ValueError):
    pass

def _source_files(root:Path) -> dict[str,Path]:
    if not root.is_dir() or root.is_symlink():
        raise BundleHold("expected ordinary public/cgx source directory")
    found={}
    for p in root.rglob("*"):
        if "deployment" in p.relative_to(root).parts:
            continue   # source-only embed, README and hosted deployment contract
        if p.is_symlink():
            raise BundleHold("symlink source not permitted")
        if p.is_file():
            relative=p.relative_to(root).as_posix()
            if relative in found:raise BundleHold("duplicate path")
            found[relative]=p
    if set(found)!=APPROVED:
        extra=sorted(set(found)-APPROVED)
        missing=sorted(APPROVED-set(found))
        raise BundleHold(f"unexpected public payload: extra={extra}, missing={missing}")
    return found

def inspect_public_bundle(source:Path=SOURCE)->dict[str,Any]:
    found=_source_files(Path(source))
    file_index=[]
    total=0
    all_text=[]
    for relative in sorted(found):
        blob=found[relative].read_bytes()
        if len(blob)>MAX_FILE_BYTES:raise BundleHold(f"source file too large: {relative}")
        total+=len(blob)
        if total>MAX_BYTES:raise BundleHold("public package size beyond bounded review")
        try:text=blob.decode("utf-8")
        except UnicodeError as exc:raise BundleHold("non-UTF8 public payload") from exc
        for label,pattern in BLOCKED.items():
            if pattern.search(text):
                raise BundleHold(f"{label}: {relative}")
        # An HTML page or ESM file may reference only local peer assets or preapproved
        # route names. No network fetch of private data permitted in static examples.
        for uri in re.findall(r"""(?:import\s*(?:[^;]*?\s+from\s*)?|from\s*)['"]([^'"]+)['"]""",text):
            if uri.startswith(("/", "..")) or "://" in uri:
                raise BundleHold(f"external/module boundary: {relative}")
        all_text.append(text)
        file_index.append({
            "path":"cgx/"+relative,
            "sha256":hashlib.sha256(blob).hexdigest(),
            "bytes":len(blob)
        })
    full="\n".join(all_text)
    for required in REQUIRED_CONTEXT:
        if required not in full:raise BundleHold("missing demonstrator authority/evidence marking")
    # No unreviewed provider API, private device bridge or read-write transport.
    return {
        "schema":"CGX-PUBLIC-ALLOWLIST-PACKAGE/0.1",
        "status":"SOURCE_CANDIDATE_NOT_PUBLISHED_NOT_OWNER_SIGNED",
        "root_path":"cgx/",
        "file_count":len(file_index),
        "source_bytes":total,
        "assets":file_index,
        "operator_source_included":False,
        "source_licences_independently_cleared":False,
        "external_host_live_verified":False,
        "native_node_authenticated":False,
        "releases_owner_metadata":False,
        "owner_approval_required":True,
        "issue_158":"OPEN_HOLD_FOR_LS_GO_INTERNAL_STATIC_BOUNDARY",
        "issue_161":"OPEN_HOLD_FOR_REAL_NATIVE_TWO_NODE_ACCEPTANCE",
    }

def make_public_bundle(dest:Path,source:Path=SOURCE)->dict[str,Any]:
    src=Path(source).resolve()
    dst=Path(dest).resolve()
    operator_public=(ROOT/"apps/lightspeed-go/public").resolve()
    if (dst==src or src in dst.parents or dst==ROOT.resolve() or
        dst==operator_public or operator_public in dst.parents):
        raise BundleHold("output cannot overlap source or operator static root")
    if dst.exists():
        raise BundleHold("refuse overwrite of prior release candidate")
    result=inspect_public_bundle(src)
    # Static preview uses a separate fresh root, not the Vite operator build.
    dst.mkdir(parents=True,exist_ok=False)
    try:
        for entry in result["assets"]:
            relative=entry["path"]
            target=dst/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            srcfile=src/relative.removeprefix("cgx/")
            blob=srcfile.read_bytes()
            if hashlib.sha256(blob).hexdigest()!=entry["sha256"] or len(blob)!=entry["bytes"]:
                raise BundleHold("TOCTOU source bytes changed during candidate packaging")
            target.write_bytes(blob)
        config=src/"deployment/vercel.json"
        if not config.is_file() or config.is_symlink():
            raise BundleHold("Vercel policy source missing")
        policy=json.loads(config.read_text(encoding="utf-8"))
        if policy.get("version")!=2 or not any(
            x.get("source")=="/cgx/(.*)" and any(
                v.get("key")=="Content-Security-Policy" and "connect-src 'none'" in v.get("value","")
                for v in x.get("headers",[])) for x in policy.get("headers",[])
        ):
            raise BundleHold("public content security policy has drifted")
        (dst/"vercel.json").write_text(json.dumps(policy,indent=2)+"\n",encoding="utf-8")
        (dst/"cgx-package-review.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        # Post-copy exact byte check, with an explicit tiny allowlist of sidecars.
        actual={p.relative_to(dst).as_posix() for p in dst.rglob("*") if p.is_file()}
        expected={x["path"] for x in result["assets"]}|{"vercel.json","cgx-package-review.json"}
        if actual!=expected:raise BundleHold("unexpected files after public package construction")
    except Exception:
        shutil.rmtree(dst,ignore_errors=True)
        raise
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=SOURCE)
    parser.add_argument("--output",type=Path,help="write new, nonexisting candidate directory; NO upload")
    args=parser.parse_args()
    try:
        report=(make_public_bundle(args.output,args.source) if args.output else inspect_public_bundle(args.source))
        print(json.dumps(report,sort_keys=True,indent=2))
    except BundleHold as exc:
        parser.exit(2,"CGX_PUBLIC_HOLD: "+str(exc)+"\n")
