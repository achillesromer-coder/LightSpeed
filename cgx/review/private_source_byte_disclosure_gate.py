"""Bounded evidence-only CGX private-byte disclosure scan for Vite public/dist.

Source: existing 61-item PR193 source plan, or independent owner-approved
private-root bytes plus an external review plan. No public release approval is
ever emitted; this detects some complete/embedded copies, not all transforms.
No source contents, plaintext paths, or credentials are printed in receipts.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
MIGRATION=Path(__file__).with_name("private_object_asset_migration.py")
MAX_MANIFEST=256*1024
MAX_SCAN_FILES=50_000
MAX_SCAN_BYTES=256*1024*1024
MIN_EMBED_BYTES=64
DIGEST_RE=re.compile(r"[0-9a-f]{64}\Z")

class DisclosureHold(ValueError):
    pass

def _migration():
    spec=importlib.util.spec_from_file_location("_cgx_private_migration",MIGRATION)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def _safe_file(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise DisclosureHold("REVIEW_SCAN_NONREGULAR_OR_SYMLINK")
    if path.stat().st_size>limit:
        raise DisclosureHold("REVIEW_SCAN_SIZE_BOUND")
    raw=path.read_bytes()
    if len(raw)>limit:
        raise DisclosureHold("REVIEW_SCAN_SIZE_BOUND")
    return raw

def _checked_plan(plan: dict, migration) -> dict:
    if plan.get("schema")!="CGX-PRIVATE-REVIEW-ASSET-MIGRATION-PLAN/0.1":
        raise DisclosureHold("INVALID_OWNER_SOURCE_PLAN")
    rows=plan.get("records")
    if not isinstance(rows,list) or not 2<=len(rows)<=migration.MAX_FILES:
        raise DisclosureHold("INVALID_OWNER_SOURCE_COUNT")
    if plan.get("count")!=len(rows):
        raise DisclosureHold("SOURCE_PLAN_COUNT_MISMATCH")
    keys=set()
    for row in rows:
        if not isinstance(row,dict): raise DisclosureHold("BAD_SOURCE_RECORD")
        name=row.get("source_relative_path")
        if not isinstance(name,str) or len(name)>250 or name.startswith("/") or "\\" in name or ".." in Path(name).parts:
            raise DisclosureHold("BAD_SOURCE_RELATIVE_PATH")
        allowed=(name in migration.EXACT or
                 any(name.startswith(folder+"/") and name.endswith(extension) and "/" not in name[len(folder)+1:]
                     for folder,extension in migration.FOLDERS.items()))
        if not allowed or name in keys or not migration.SAFE_NAME.fullmatch(Path(name).name):
            raise DisclosureHold("UNREGISTERED_OR_DUPLICATE_SOURCE")
        keys.add(name)
        if not isinstance(row.get("bytes"),int) or not 0<=row["bytes"]<=migration.MAX_BYTES:
            raise DisclosureHold("SOURCE_SIZE_OUT_OF_RANGE")
        if not isinstance(row.get("sha256"),str) or not DIGEST_RE.fullmatch(row["sha256"]):
            raise DisclosureHold("SOURCE_DIGEST_INVALID")
    if rows!=sorted(rows,key=lambda x:x["source_relative_path"]):
        raise DisclosureHold("PLAN_ORDER_INVALID")
    if plan.get("plan_sha256")!=migration._canonical_hash(rows):
        raise DisclosureHold("PLAN_CONTENT_DIGEST_MISMATCH")
    return plan

def source_signatures(repository_root:Path=ROOT, *,
                      private_root:Path|None=None,
                      approved_plan_file:Path|None=None) -> tuple[dict,list[tuple[str,bytes]]]:
    migration=_migration()
    if (private_root is None)!=(approved_plan_file is None):
        raise DisclosureHold("PRIVATE_ROOT_AND_PLAN_MUST_BE_PAIRED")
    if private_root is None:
        plan=_checked_plan(migration.private_review_source_plan(repository_root),migration)
        root=repository_root/migration.SITE
    else:
        path=approved_plan_file
        if path.is_symlink() or not path.is_file() or path.stat().st_size>MAX_MANIFEST:
            raise DisclosureHold("APPROVED_PLAN_FILE_INVALID")
        real=path.resolve(strict=True)
        repo=repository_root.resolve(strict=True)
        if real.is_relative_to(repo) or any(part.lower() in ("public","dist") for part in real.parts):
            raise DisclosureHold("OWNER_PLAN_MUST_BE_PRIVATE_NOT_IN_REPO")
        plan=_checked_plan(json.loads(_safe_file(real,MAX_MANIFEST)),migration)
        root=migration._check_private_root(repository_root,private_root)
    signatures=[]
    for row in plan["records"]:
        candidate=root/row["source_relative_path"]
        if any(p.is_symlink() for p in (candidate,candidate.parent,candidate.parent.parent)):
            raise DisclosureHold("SOURCE_SYMLINK_OR_PARENT")
        payload=_safe_file(candidate,migration.MAX_BYTES)
        if len(payload)!=row["bytes"] or _sha(payload)!=row["sha256"]:
            raise DisclosureHold("SOURCE_PLAN_READBACK_MISMATCH")
        signatures.append((row["source_relative_path"],payload))
    return plan,signatures

def _all_regular_files(scan_root:Path) -> list[Path]:
    if scan_root.is_symlink() or not scan_root.is_dir():
        raise DisclosureHold("PUBLIC_SCAN_ROOT_MISSING_OR_SYMLINK")
    found=[]
    total=0
    for p in sorted(scan_root.rglob("*")):
        if p.is_symlink():
            raise DisclosureHold("PUBLIC_SCAN_SYMLINK")
        if p.is_dir(): continue
        if not p.is_file(): raise DisclosureHold("PUBLIC_SCAN_NONREGULAR")
        found.append(p)
        if len(found)>MAX_SCAN_FILES: raise DisclosureHold("PUBLIC_SCAN_FILE_COUNT_BOUND")
        total+=p.stat().st_size
        if total>MAX_SCAN_BYTES: raise DisclosureHold("PUBLIC_SCAN_TOTAL_SIZE_BOUND")
    return found

def _encoded_signatures(data:bytes) -> tuple[bytes,...]:
    if len(data)<MIN_EMBED_BYTES: return ()
    result=[data,base64.b64encode(data)]
    try:
        text=data.decode("utf-8")
    except UnicodeDecodeError:
        return tuple(result)
    for ascii_flag in (True,False):
        fragment=json.dumps(text,ensure_ascii=ascii_flag)[1:-1].encode("utf-8")
        if fragment not in result: result.append(fragment)
    return tuple(result)

def scan_public_distribution(*,repository_root:Path=ROOT,
                            scan_root:Path,private_root:Path|None=None,
                            approved_plan_file:Path|None=None) -> dict:
    plan,signatures=source_signatures(
        repository_root,private_root=private_root,
        approved_plan_file=approved_plan_file)
    # Never allow a caller to use this as a private-file copy or public-release grant.
    files=_all_regular_files(scan_root)
    leaks=[]
    for candidate in files:
        data=_safe_file(candidate,MAX_SCAN_BYTES)
        digest=_sha(data)
        for name,source_bytes in signatures:
            source_digest=_sha(source_bytes)
            kind=None
            if digest==source_digest and len(data)==len(source_bytes):
                kind="EXACT_RENAMED_OR_ORIGINAL_FILE"
            elif len(source_bytes)>=MIN_EMBED_BYTES:
                variants=_encoded_signatures(source_bytes)
                if source_bytes in data:
                    kind="EMBEDDED_ORIGINAL_BYTES"
                elif any(p in data for p in variants[1:]):
                    kind="ENCODED_COMPLETE_SOURCE"
            if kind:
                # No filenames, asset bytes or source identifiers in public-safe logs.
                leaks.append({"candidate_path_sha256":_sha(candidate.relative_to(scan_root).as_posix().encode()),
                              "source_record_sha256":_sha(name.encode()),"match":kind})
            if len(leaks)>MAX_SCAN_FILES:
                raise DisclosureHold("EXCESSIVE_DISCLOSURE_MATCHES")
    return {
        "schema":"CGX-PUBLIC-DISTRIBUTION-PRIVATE-BYTE-SCAN/0.1",
        "state":"HOLD_PRIVATE_SOURCE_BYTES_PRESENT" if leaks else "NO_MATCHING_COMPLETE_PRIVATE_BYTES_UNVERIFIED",
        "source_plan_sha256":plan["plan_sha256"],
        "source_items_verified":len(signatures),
        "distribution_files_inspected":len(files),
        "private_byte_matches":len(leaks),
        "matches":leaks,
        "public_release_authorised":False,
        "owner_acl_verified":False,
        "live_http_negative_tests":"NOT_PERFORMED",
        "limitations":["Complete files, raw embedded blobs, base64, and JSON-escaped complete text only",
                       "Not an exhaustive detector of partial, transformed, compressed, encrypted or rendered leaks",
                       "No rights, permission, CDN cache or live deployment approval"],
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--scan-root",type=Path,required=True)
    p.add_argument("--private-root",type=Path)
    p.add_argument("--approved-plan-file",type=Path)
    args=p.parse_args()
    try:
        out=scan_public_distribution(repository_root=args.root,scan_root=args.scan_root,
                                     private_root=args.private_root,
                                     approved_plan_file=args.approved_plan_file)
        print(json.dumps(out,sort_keys=True,indent=2))
        if out["private_byte_matches"]>0: sys.exit(2)
    except (DisclosureHold,ValueError,OSError) as exc:
        print(json.dumps({"schema":"CGX-PUBLIC-DISTRIBUTION-PRIVATE-BYTE-SCAN/0.1",
            "state":"HOLD_SCAN_UNAVAILABLE",
            "reason":str(exc).split(":")[0],
            "public_release_authorised":False}))
        sys.exit(2)
