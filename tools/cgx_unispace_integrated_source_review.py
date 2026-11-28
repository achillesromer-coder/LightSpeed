#!/usr/bin/env python3
"""Read-only single-root UniSpace source composition and closure assessment.

Projects existing five-facet mesh, 51 cross-space engineering gates, ten
LOAD/Alexandria source actions, sixteen PrintSpace workstreams, 51 *different*
public route descriptors and historic Git observations into one review receipt.
It does not create runtime storage, authority or public deployment.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.cgx_unispace_capability_crosswalk import build as build_capabilities
from tools.cgx_unispace_capability_crosswalk import _file_bytes
from tools.cgx_unispace_facet_mesh import build_unispace_facet_mesh
from tools.cgx_unispace_crossspace_review import (
    EXPECTED_SHA256, source_review
)
from tools.cgx_unispace_hybrid_source_review import compose

SCHEMA = "CGX-UNISPACE-SINGLE-ROOT-REVIEW-CONVERGENCE/0.1"
ROOT = "cgx:root:cognigrex"
PUBLIC_GATEWAY = "docs/romer-web-hooks/uos_universal_gateway_embed.html"
GATEWAY_BLOB = "06156cfd290a7af3a2b767e3ddcfca16ef93a234"
ROUTES = re.compile(
    r'^\s*\["(/[^"]*)", "([^"]+)", "([^"]+)", "([^"]+)", '
    r'"(observed|historical|candidate|missing-404)"\],?\s*$',
    re.MULTILINE,
)
BANNED = (
    re.compile(r'\b(?:fetch|WebSocket|XMLHttpRequest|eval|Function)\s*\('),
    re.compile(r'\b(?:localStorage|sessionStorage)\b'),
    re.compile(r'<(?:iframe|script\s+src=)', re.IGNORECASE),
)

class ReviewHold(ValueError):
    """Required original source, provenance or no-authority contract absent."""

def inspect_gateway(text: str) -> dict:
    if not isinstance(text, str) or len(text) > 60000:
        raise ReviewHold("unbounded passive public gateway")
    if any(p.search(text) for p in BANNED):
        raise ReviewHold("gateway introduced network/privileged code")
    route_array=re.search(r'var routes = \[\s*\n(.*?)\n\s*\];',text,re.DOTALL)
    if not route_array:
        raise ReviewHold("original source route table missing")
    chunk=route_array.group(1)
    lines=[s.strip() for s in chunk.splitlines() if s.strip() and not s.strip().startswith("//")]
    items=[{"path":m[1],"title":m[2],"type":m[3],"facet":m[4],"evidence":m[5]}
           for m in ROUTES.finditer(chunk)]
    if len(lines)!=len(items) or len(items)!=51:
        raise ReviewHold("public gateway source route census changed")
    ids=[i["path"] for i in items]
    if len(set(ids))!=51 or any(len(x)>160 or x!=x.lower() or ".." in x for x in ids):
        raise ReviewHold("invalid public URL route identity")
    missing={i["path"] for i in items if i["evidence"]=="missing-404"}
    expected={f"/w{i}-data" for i in range(1,7)}
    if missing!=expected:
        raise ReviewHold("unknown or misclassified 404 source labels")
    for entry in items:
        if entry["path"] in missing and entry["facet"]!="dataspace":
            raise ReviewHold("missing public link remapped to privileged space")
    return {
        "route_count":51,"missing_404":sorted(missing),
        "route_status_counts":{s:sum(x["evidence"]==s for x in items)
            for s in ("observed","historical","candidate","missing-404")},
        "route_discovery_only":True,"published_pages_created":False,
        "peer_authenticated":False,"network_fetch_performed":False,
        "execution_authorised":False,
        "source_route_facet_count":len(set(x["facet"] for x in items)),
    }

def read_json(repo: Path, relative: str, maximum: int = 250000) -> dict:
    p=repo/relative
    if p.is_symlink() or not p.is_file() or p.stat().st_size>maximum:
        raise ReviewHold("unavailable source: "+relative)
    out=json.loads(p.read_text("utf-8"))
    if not isinstance(out,dict):
        raise ReviewHold("wrong source JSON root: "+relative)
    return out

def build(repo: Path) -> dict:
    repo=repo.resolve(strict=True)
    done=subprocess.run(["git","-C",str(repo),"ls-files","-z"],
                        capture_output=True,check=False,timeout=20)
    if done.returncode:
        raise ReviewHold("Git source index unavailable")
    tracked={part.decode("utf-8") for part in done.stdout.split(b"\0") if part}
    gateway_raw=_file_bytes(repo,PUBLIC_GATEWAY,GATEWAY_BLOB,tracked)
    gateway=inspect_gateway(gateway_raw.decode("utf-8"))
    capabilities=build_capabilities(repo)
    mesh=build_unispace_facet_mesh(repo,tracked)
    if (mesh.get("canonical_root_id")!=ROOT
            or mesh.get("state")!="SOURCE_CONTRACT_MESH_OBSERVED"
            or mesh.get("facet_count")!=5
            or mesh.get("unique_contract_count")!=12
            or mesh.get("unique_service_count")!=7):
        raise ReviewHold("existing source facet mesh not qualified")
    gate_path="cgx/review/unispace_crossspace_gate_register_v0_1.json"
    gate_raw=(repo/gate_path).read_bytes()
    gate_sha=hashlib.sha256(gate_raw).hexdigest()
    if gate_sha!=EXPECTED_SHA256:
        raise ReviewHold("original 51-gate source changed")
    gates=json.loads(gate_raw)
    engineering=source_review(gates,gate_sha,{"mesh":mesh})
    if engineering["task_count"]!=51 or not engineering["source_mesh_observed"]:
        raise ReviewHold("original five-facet engineering gates incomplete")
    snapshot=read_json(repo,"cgx/review/unispace_git_pr_source_snapshot_20261122.json")
    overlap=read_json(repo,"cgx/review/unispace_source_path_overlap_20261122.json")
    hybrid=compose(snapshot,overlap,gates,source_mesh={"mesh":mesh},
                   source_register_sha256=gate_sha)
    if hybrid["exact_crossspace_mesh_bound"] is not True:
        raise ReviewHold("hybrid source is not bound to original gate bytes")
    if capabilities["original_gate_count"]!=engineering["task_count"]:
        raise ReviewHold("LOAD/PrintSpace gate crosswalk disagrees with original")
    release_holds=[
        "EXACT_PARENT_PR228_230_232_ANCESTRY_AND_RIGHTS_SIGNOFF",
        "PR205_LOAD_NATIVE_IDENTITY_ACL_LEASE_AND_HYDRATION",
        "PR236_PRINTSPACE_INDEPENDENT_TEST_AND_PHYSICAL_EVIDENCE",
        "FILESPACE_DATASPACE_TWO_NODE_SIGNED_DBR_READBACK",
        "HISTORICAL_AUTOMATION_PROVIDER_OUTPUT_COMPLETENESS_AND_RESTORE",
        "UOS_51_ROUTES_6_UNPUBLISHED_LINKS_OWNER_PUBLICATION",
        "OFFLINE_MOBILE_WINDOWS_GUI_ACCESSIBILITY_SECURITY_UAT",
        "OWNER_RELEASE_SIGNATURE_ROLLBACK_AND_SUPPORT",
        "OWNER_EXACT_TARGET_ARCHIVE_DISPOSITION_AFTER_DBR_PROOF",
    ]
    result={
        "schema":SCHEMA,
        "canonical_root":ROOT,
        "state":"INTEGRATED_SOURCE_REVIEW_NOT_DEPLOYED",
        "independent_scope_counts":{
            "root_count":1,
            "workspace_facets":mesh["facet_count"],
            "shared_contracts":mesh["unique_contract_count"],
            "root_shared_services":mesh["unique_service_count"],
            "engineering_gate_groups":engineering["task_count"],
            "engineering_gate_groups_open":engineering["task_count"],
            "public_route_descriptors":gateway["route_count"],
            "public_missing_404_routes":len(gateway["missing_404"]),
            "LOAD_actions":len(capabilities["library"]["actions"]),
            "PrintSpace_workstreams":len(capabilities["manufacturing"]["workstreams"]),
            "source_only_priority_prs":hybrid["open_pr_records"],
        },
        "source_receipts":{
            "facet_mesh_schema":mesh["schema"],
            "original_gate_sha256":gate_sha,
            "capability_review_sha256":capabilities["review_sha256"],
            "hybrid_review_sha256":hybrid["review_sha256"],
            "gateway_original_git_blob":GATEWAY_BLOB,
            "gateway_sha256":hashlib.sha256(gateway_raw).hexdigest(),
            "gateway_source_pr":233,
        },
        "public_gateway":gateway,
        "open_conditions":release_holds,
        "source_head_mismatches":hybrid["source_head_mismatches"],
        "historical_source_prs":hybrid["historic_prs_in_comparison"],
        "native_root_admitted":False,"source_rights_all_accepted":False,
        "archive_deletion_authorised":False,"native_dbr_proved":False,
        "physical_print_qualified":False,"public_published":False,
        "model_training_performed":False,"new_scheduler_created":False,
        "new_database_created":False,"authority_transferred":False,
        "original_sources_retained":True,
    }
    digest=json.dumps(result,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True).encode("ascii")
    result["review_sha256"]=hashlib.sha256(digest).hexdigest()
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    data=json.dumps(build(args.repo),sort_keys=True,indent=2)+"\n"
    if args.output:
        args.output.write_text(data,encoding="utf-8")
    else:
        print(data,end="")

if __name__=="__main__":
    main()
