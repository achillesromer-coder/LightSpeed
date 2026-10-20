"""Alexandria Basic candidate: deterministic offline, reference-only ZIP.

Inputs: existing reviewed Alexandria reference catalogues and lessons.
Payload: self-contained HTML, source-reference metadata, synthetic-only course
prompts, provenance and SHA256 manifest. No private CGX review assets, binaries,
runtime engines, datasets, model weights, cookies or network fetches.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[2]
REVIEW=ROOT/"cgx"/"review"
SOURCE_FILES=(
    "alexandria_external_reference_intake_20261020.json",
    "alexandria_curated_upstream_tools_20261020.json",
    "alexandria_official_reference_roots_20261020.json",
    "alexandria_foundation_learning_modules_v0_1.json"
)
ZIP_ENTRY_NAMES=("README.txt","catalogue.json","index.html","lessons.json","manifest.json")

def _json(data):
    return (json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8")

def _get_sources(root):
    docs={}
    roots={}
    for name in SOURCE_FILES:
        raw=(root/"cgx"/"review"/name).read_bytes()
        docs[name]=json.loads(raw)
        roots[name]={"sha256":hashlib.sha256(raw).hexdigest(),"byte_length":len(raw)}
    return docs,roots

def _render_html(root):
    p=root/"cgx/review/alexandria_offline_reference_preview.py"
    spec=importlib.util.spec_from_file_location("_alexandria_preview_module",p)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # The imported generator is deliberately source-bound to this repository,
    # not arbitrary uploaded documents, and does no network requests.
    return module.build_offline_reference_html().encode("utf-8")

def make_review_package(root: Path=ROOT) -> bytes:
    docs,roots=_get_sources(root)
    curated=docs[SOURCE_FILES[1]]["repositories"]
    old=docs[SOURCE_FILES[0]]["groups"]
    official=docs[SOURCE_FILES[2]]["official_references"]
    lessons=docs[SOURCE_FILES[3]]["modules"]
    if len(curated)!=31 or sum(len(g["records"]) for g in old)!=207 or len(official)!=13 or len(lessons)!=18:
        raise ValueError("expected source catalogue version/counts are not present")
    if any(x.get("redistribution_authorised") is not False for x in curated):
        raise ValueError("non-reference-only package source")
    if any(x.get("public_kit_inclusion")!="REFERENCE_ONLY_HOLD" for x in official):
        raise ValueError("external data inclusion not rights-cleared")
    if any(x.get("third_party_bytes_included") is not False or
           x.get("module_state")!="UNEXECUTED_SOURCE_LINKED_EDUCATION" for x in lessons):
        raise ValueError("unexpected lesson execution or contents")

    refs=[]
    for item in curated:
        refs.append({"kind":"repository","name":item["repository"],"url":item["url"],
                     "domain":item["domain"],"licence_metadata":item["github_licence_metadata"],
                     "rights":"UNVERIFIED_FOR_REDISTRIBUTION"})
    for group in old:
        for item in group["records"]:
            refs.append({"kind":"historical-index","name":item.get("title","Untitled"),
                         "category":item.get("category"),
                         "source_urls":item.get("sources",[]),
                         "index_origin":group["origin"]["name"],
                         "rights":"UPSTREAM_LICENSE_UNVERIFIED"})
    for item in official:
        refs.append({"kind":"official-reference","name":item["name"],"url":item["url"],
                     "domain":item["domain"],"rights":"REFERENCE_ONLY_HOLD"})
    if len(refs)!=251:
        raise ValueError("source identity coverage mismatch")
    selected=[{k:m[k] for k in ("id","track","title","instruction","expected_artifact",
                                "qualification_hold","repository_sources","module_state")} for m in lessons]
    html=_render_html(root)
    if b"<script src=" in html or b"fetch(" in html or b"XMLHttpRequest" in html:
        raise ValueError("unexpected remote code or data loader")
    readme=("Alexandria Basic — OFFLINE REFERENCE REVIEW ONLY\n"
            "251 linked source references and 18 synthetic-first exercises.\n"
            "This is an unapproved offline learning index: not a licence grant, "
            "game archive, executable library, live CGX node or finished public UniSpace release.\n"
            "References remain governed by their upstream owners and individual licences.\n"
            "Open index.html locally to search, filter and read exercises without a network.\n"
            "External source links require network and are never opened automatically.\n"
            "The package contains no third-party program bytes, models, datasets, or CGX review asset corpus.\n"
            "Checksums in manifest.json describe the four payload files, not third-party authenticity.\n").encode("utf-8")
    payload={
      "README.txt":readme,
      "catalogue.json":_json({"schema":"ALEXANDRIA-BASIC-REFERENCE-LIST/0.1",
                            "scope":"REVIEW_ONLY","source_count":len(refs),"references":refs}),
      "index.html":html,
      "lessons.json":_json({"schema":"ALEXANDRIA-BASIC-LESSONS/0.1",
                           "qualification":"SYNTHETIC_LEARNING_NOT_EXECUTED","modules":selected}),
    }
    checks=[{"name":name,"sha256":hashlib.sha256(value).hexdigest(),"bytes":len(value)}
            for name,value in sorted(payload.items())]
    payload["manifest.json"]=_json({
        "schema":"ALEXANDRIA-BASIC-OFFLINE-REVIEW-MANIFEST/0.1",
        "status":"REVIEW_ONLY_NOT_PUBLIC_RELEASE",
        "build_date":"2026-10-20",
        "content":checks,
        "source_roots":roots,
        "rights":"External references and licence metadata are NOT source/asset redistribution grants",
        "signed":False,"verified_on_second_device":False,
        "contains_private_cgx_assets":False,"contains_executables":False,
        "parent_identity":"Cognigrex.cgx",
        "catalogue_canonical":False
    })
    import io
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as zipped:
        for name in sorted(payload):
            info=zipfile.ZipInfo(name,date_time=(2020,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o644 << 16)
            zipped.writestr(info,payload[name],compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    return buf.getvalue()

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    content=make_review_package()
    out.write_bytes(content)
    print(json.dumps({"review_package":str(out),
                      "size_bytes":len(content),
                      "sha256":hashlib.sha256(content).hexdigest(),
                      "state":"REVIEW_ONLY_UNPUBLISHED"}))
