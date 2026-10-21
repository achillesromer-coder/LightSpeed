"""Bounded original plog MIT source scope at a fixed libdatachannel gitlink.

No build, execution, whole-library licence clearance or native CGX admission.
"""
import hashlib
import json
from cgx.portable_node.project_gitlink_evidence import _git_tree, _git_blob

REV="94899e0b926ac1b0f4750bfbd495167b4a6ae9ef"
TREE="efd55db485576861edede33a8ed2adfc019fe5d7"
PARENT="git:paullouisageneau/libdatachannel@6b1e2e620f1e37f0eafeee702eaea0043cb305fd"
BLOBS={"LICENSE":"8a91a0aeeb54dded3f8ee9f8e105f07100ff67fc",
"CMakeLists.txt":"aac6bf573481f3b56926e711bee741221dd0a1d4",
"library.json":"bdb2ea2a52f38b5f00332721c890a0f85287c9ed",
"include/plog/Log.h":"138d92f5fe47f35d50b296b21e0a093350aa6258",
"include/plog/Logger.h":"0e116e4c6bb847892df91f258c37d3dc01d1a0f0"}

def _entry(tree,name,mode):
    matches=[x for x in tree["entries"] if x.get("path")==name and x.get("mode")==mode]
    if len(matches)!=1:
        raise ValueError("missing or duplicate Git entry: "+name)
    return matches[0]["sha"]

def compile_plog_scope(parent, trees, originals):
    if not isinstance(parent,dict) or parent.get("schema")!="CGX-ALEXANDRIA-LIBDATACHANNEL-SOURCE-SCOPE/0.1" or parent.get("source_root")!=PARENT or parent.get("native_dbr_verified") is not False or parent.get("canonical_object_id") is not None:
        raise ValueError("untrusted parent source authority")
    links=parent.get("nested_gitlinks")
    if not isinstance(links,list):
        raise ValueError("no verified parent gitlinks")
    link=[x for x in links if isinstance(x,dict) and x.get("path")=="deps/plog"]
    if len(link)!=1 or link[0].get("pinned_commit_sha1")!=REV or link[0].get("source_url")!="https://github.com/SergiusTheBest/plog.git" or link[0].get("source_acquired") is not False or link[0].get("licence_verified") is not False:
        raise ValueError("plog pinned gitlink mismatch or rights promotion")
    if not isinstance(trees,dict) or trees.get("schema")!="CGX-PLOG-PINNED-GIT-TREES/0.1" or trees.get("repo")!="SergiusTheBest/plog" or trees.get("commit")!=REV or trees.get("root_tree_sha")!=TREE:
        raise ValueError("untrusted tree identity")
    checked={}
    for part in ("root","include","include_plog"):
        t=trees.get(part)
        if not isinstance(t,dict) or t.get("truncated") is not False or t.get("sha")!=_git_tree(t):
            raise ValueError("Git tree mismatch or truncation")
        checked[part]=t
    if checked["root"]["sha"]!=TREE or _entry(checked["root"],"include","040000")!=checked["include"]["sha"] or _entry(checked["include"],"plog","040000")!=checked["include_plog"]["sha"]:
        raise ValueError("Git tree ancestor mismatch")
    if not isinstance(originals,dict) or set(originals)!=set(BLOBS):
        raise ValueError("exact 5-file source required")
    texts={}
    proofs=[]
    for name in sorted(BLOBS):
        raw=originals[name]
        if type(raw) is not bytes or not raw or len(raw)>65536 or _git_blob(raw)!=BLOBS[name]:
            raise ValueError("original Git blob mismatch")
        bucket=checked["include_plog"] if name.startswith("include/plog/") else checked["root"]
        if _entry(bucket,name.split("/")[-1],"100644")!=BLOBS[name]:
            raise ValueError("file not verified in Git tree")
        texts[name]=raw.decode("utf-8",errors="strict")
        proofs.append({"path":name,"bytes":len(raw),"git_blob_sha1":BLOBS[name],"sha256":hashlib.sha256(raw).hexdigest(),"source_bytes_embedded":False})
    if not (texts["LICENSE"].startswith("MIT License") and "Copyright (c) 2022 Sergey Podobry" in texts["LICENSE"] and "The above copyright notice and this permission notice shall be included" in texts["LICENSE"]):
        raise ValueError("MIT licence text mismatch")
    if "License: MIT" not in texts["include/plog/Log.h"][:500]:
        raise ValueError("header licence mismatch")
    meta=json.loads(texts["library.json"])
    cmake=texts["CMakeLists.txt"]
    if not (meta.get("name")=="plog" and meta.get("license")=="MIT" and meta.get("version")=="1.1.10" and "plog/Log.h" in meta.get("headers",[]) and "project(plog VERSION 1.1.10 LANGUAGES CXX)" in cmake and "INTERFACE)" in cmake and "add_library(" in cmake):
        raise ValueError("packaging metadata mismatch")
    return {
        "schema":"CGX-ALEXANDRIA-PLOG-SOURCE-SCOPE/0.1",
        "status":"PINNED_FIVE_ORIGINAL_FILES_MIT_NOTICE_CANDIDATE",
        "source_root":"git:SergiusTheBest/plog@"+REV,
        "parent_source_root":PARENT,
        "parent_gitlink_path":"deps/plog",
        "pinned_tree_sha1":TREE,
        "original_file_proofs":proofs,
        "original_file_count":5,
        "licensing":{"repository_declared":"MIT","original_text_verified":True,
            "permission_and_copyright_notice_retention_required":True,
            "one_header_notice_verified":True,
            "all_headers_and_third_party_notices_verified":False,
            "distribution_approved":False},
        "packaging":{"cmake_version_claim":"1.1.10","platformio_license_claim":"MIT",
            "header_interface_library_declared":True,"compiled":False,"package_tested":False},
        "capability":{"category":"CXX_LOGGING_HEADER_LIBRARY_CANDIDATE",
            "operationally_verified":False,"canon_admitted":False},
        "whole_repository_acquired":False,"source_bytes_embedded":False,
        "native_dbr_verified":False,"canonical_object_id":None,
        "frontier":["REVIEW_ALL_REMAINING_PLOG_HEADERS","QUALIFY_ALL_THIRD_PARTY_NOTICES",
          "RUN_APPROVED_CXX_BUILD_TEST","VERIFY_NATIVE_SIGNED_CGX_DBR_READBACK"]
    }
