"""Prepare source-hash-exact CGX Objects private-file staging, never publish/delete.

DEFAULT: read-only plan. An explicitly authorised operator can supply an
absolute pre-existing PRIVATE destination and --stage --approved-plan-sha256.
No original source is altered; no implicit provider, OwnerSession or DBR grant.
This is a local file migration candidate, NOT a remote access acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SITE=Path("apps/lightspeed-go/public")
EXACT=(
    "data/cgx_object_review_catalogue.json",
    "data/component_geometry_atlas_public_review.json",
)
FOLDERS={"review/renders":".svg","review/mesh":".json"}
MAX_BYTES=4*1024*1024
MAX_FILES=256
SAFE_NAME=re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z",re.ASCII)

class MigrationHold(ValueError):
    pass

def _canonical_hash(items: list[dict]) -> str:
    body=json.dumps(items,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(body).hexdigest()

def _read_exact(path: Path) -> tuple[bytes,os.stat_result]:
    if path.is_symlink():
        raise MigrationHold("SOURCE_SYMLINK_REFUSED")
    try:
        before=path.lstat()
        if not stat.S_ISREG(before.st_mode) or not 0 <= before.st_size <= MAX_BYTES:
            raise MigrationHold("UNSUPPORTED_TYPE_OR_SIZE")
        fd=os.open(path,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0))
        try:
            actual=os.fstat(fd)
            if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(
                actual.st_dev,actual.st_ino,actual.st_size,actual.st_mtime_ns
            ):
                raise MigrationHold("SOURCE_CHANGED")
            with os.fdopen(fd,"rb",closefd=False) as stream:
                raw=stream.read(MAX_BYTES+1)
        finally:
            os.close(fd)
        if len(raw)!=before.st_size:
            raise MigrationHold("SOURCE_CHANGED_OR_TOO_LARGE")
        return raw,before
    except MigrationHold:
        raise
    except OSError as exc:
        raise MigrationHold("SOURCE_READ_FAILED") from exc

def private_review_source_plan(repository_root: Path=ROOT) -> dict:
    site=repository_root/SITE
    if not site.is_dir() or site.is_symlink():
        raise MigrationHold("PUBLIC_SOURCE_TREE_MISSING_OR_SYMLINK")
    entries=[]
    for rel in EXACT:
        if not (site/rel).is_file():
            raise MigrationHold("REQUIRED_PRIVATE_CATALOGUE_MISSING")
        entries.append(rel)
    for folder,suffix in FOLDERS.items():
        source=site/folder
        if not source.is_dir() or source.is_symlink():
            raise MigrationHold("REVIEW_SOURCE_FOLDER_MISSING_OR_SYMLINK")
        for path in sorted(source.iterdir()):
            if path.is_symlink() or not path.is_file():
                raise MigrationHold("REVIEW_SOURCE_NONREGULAR_REFUSED")
            if path.suffix != suffix:
                raise MigrationHold("REVIEW_SOURCE_UNEXPECTED_EXTENSION")
            entries.append(path.relative_to(site).as_posix())
    if len(entries)>MAX_FILES:
        raise MigrationHold("SOURCE_FILE_COUNT_BOUND")
    if len(set(entries))!=len(entries):
        raise MigrationHold("DUPLICATE_SOURCE_ASSET")
    records=[]
    for name in sorted(entries):
        p=site/name
        if not SAFE_NAME.fullmatch(p.name):
            raise MigrationHold("SOURCE_NAME_REJECTED")
        if any(part.is_symlink() for part in [p.parent,p.parent.parent]):
            raise MigrationHold("SOURCE_PARENT_SYMLINK_REFUSED")
        raw,_=_read_exact(p)
        records.append({"source_relative_path":name,
                        "sha256":hashlib.sha256(raw).hexdigest(),
                        "bytes":len(raw)})
    h=_canonical_hash(records)
    return {"schema":"CGX-PRIVATE-REVIEW-ASSET-MIGRATION-PLAN/0.1",
            "status":"READ_ONLY_REVIEW_UNTIL_OWNER_APPROVED_STAGE",
            "source_root":SITE.as_posix(),
            "count":len(records),
            "plan_sha256":h,
            "records":records,
            "source_originals_retained":True,
            "owner_approval_recorded":False,
            "public_release_authorised":False,
            "remote_owner_authenticated":False,
            "cdn_cache_validated":False,
            "actual_two_node_readback":False}

def _check_private_root(repository_root: Path,target_root: Path) -> Path:
    if not target_root.is_absolute() or ".." in target_root.parts:
        raise MigrationHold("TARGET_MUST_BE_ABSOLUTE")
    if not target_root.is_dir() or target_root.is_symlink():
        raise MigrationHold("TARGET_PRIVATE_ROOT_MUST_PREEXIST")
    final=target_root.resolve(strict=True)
    if any(x.lower() in {"public","dist"} for x in final.parts):
        raise MigrationHold("STATIC_TARGET_FORBIDDEN")
    if final == repository_root.resolve() or final.is_relative_to(repository_root.resolve()):
        raise MigrationHold("REPO_TREE_TARGET_FORBIDDEN")
    return final

def stage_approved_private_copy(repository_root:Path,target_root:Path,
                                approved_plan_sha256:str,expected_count:int) -> dict:
    plan=private_review_source_plan(repository_root)
    if expected_count != plan["count"] or plan["count"]<2:
        raise MigrationHold("OWNER_FILE_COUNT_REVIEW_REQUIRED")
    if approved_plan_sha256 != plan["plan_sha256"]:
        raise MigrationHold("SOURCE_PLAN_CHANGED_REAPPROVAL_REQUIRED")
    root=_check_private_root(repository_root,target_root)
    for item in plan["records"]:
        out=root/item["source_relative_path"]
        if out.exists() or out.is_symlink():
            raise MigrationHold("TARGET_EXISTS_NO_OVERWRITE")
        if any(p.is_symlink() for p in [out.parent,out.parent.parent]):
            raise MigrationHold("TARGET_SYMLINK_PARENT_REFUSED")
    copied=[]
    for item in plan["records"]:
        source=repository_root/SITE/item["source_relative_path"]
        raw,_=_read_exact(source)
        if len(raw)!=item["bytes"] or hashlib.sha256(raw).hexdigest()!=item["sha256"]:
            raise MigrationHold("SOURCE_CHANGED_DURING_STAGE")
        output=root/item["source_relative_path"]
        output.parent.mkdir(parents=True,exist_ok=True)
        if not output.parent.resolve().is_relative_to(root):
            raise MigrationHold("TARGET_PARENT_ESCAPE")
        if output.is_symlink() or output.exists():
            raise MigrationHold("TARGET_EXISTS_NO_OVERWRITE")
        fd,temp=tempfile.mkstemp(prefix=".cgx_review_stage_",dir=output.parent)
        try:
            with os.fdopen(fd,"wb") as writer:
                writer.write(raw)
                writer.flush()
                os.fsync(writer.fileno())
            # Hardlink a complete temp file to a new name; this never replaces
            # a preexisting target. Refuse if the filesystem does not support it.
            os.link(temp,output)
            copied_bytes,_=_read_exact(output)
            if hashlib.sha256(copied_bytes).hexdigest()!=item["sha256"]:
                raise MigrationHold("DESTINATION_READBACK_MISMATCH")
            copied.append(item["source_relative_path"])
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
    return {"schema":"CGX-PRIVATE-REVIEW-ASSET-STAGING-RECEIPT/0.1",
            "plan_sha256":plan["plan_sha256"],"copied_count":len(copied),
            "all_source_originals_retained":True,
            "destination_sha256_readback":True,
            "static_source_still_present":True,
            "public_release_authorised":False,
            "owner_session_test":"NOT_PERFORMED",
            "rollback":"Remove newly staged destination files ONLY after separate owner review; originals remain in place"}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--stage",action="store_true")
    p.add_argument("--private-root",type=Path)
    p.add_argument("--approved-plan-sha256")
    p.add_argument("--expected-count",type=int)
    a=p.parse_args()
    if a.stage:
        if not a.private_root or not a.approved_plan_sha256 or a.expected_count is None:
            raise SystemExit("HOLD: --stage requires pre-existing --private-root, --approved-plan-sha256 and --expected-count")
        result=stage_approved_private_copy(a.root,a.private_root,a.approved_plan_sha256,a.expected_count)
    else:
        result=private_review_source_plan(a.root)
    print(json.dumps(result,sort_keys=True,indent=2))
