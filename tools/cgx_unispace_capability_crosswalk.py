#!/usr/bin/env python3
"""Source-qualified LOAD/Alexandria and PrintSpace capability crosswalk.

One existing Cognigrex parent; no model, database, scheduler, native DBR, mount,
machine command, network hydration, publication, release or source deletion.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any
import sys
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.cgx_unispace_crossspace_review import (
    EXPECTED_SHA256 as GATE_SHA256,
    validate_registry,
)

ROOT = Path(__file__).resolve().parents[1]
PARENT = "cgx:root:cognigrex"
SCHEMA = "CGX-UNISPACE-LOAD-PRINTSPACE-CAPABILITY-CROSSWALK/0.1"
MAX_SOURCE = 128000
SOURCE_SPECS = {
    "load_activation": ("cgx/load_minimum/activation_contract.json",
        "c317764d8a21f0c0f29c48933b55cc51f37eca38",
        "465876bcd99a4fa2dc400cead4ad7c5f991410ad",
        "LOAD-ALEXANDRIA-ACTIVATION/0.1"),
    "load_catalogue": ("cgx/load_minimum/filespace_feature_registry.json",
        "31ab6c546f17d086424a42b7821796bc80128b94",
        "465876bcd99a4fa2dc400cead4ad7c5f991410ad",
        "CGX-UNISPACE-FILESPACE-FEATURE-CATALOG/0.1"),
    "load_viewport": ("cgx/load_minimum/semantic_viewport_contract.json",
        "2b1d14cfe951aeb7847eaa12dff18e64e9bc98b7",
        "465876bcd99a4fa2dc400cead4ad7c5f991410ad",
        "LOAD-SEMANTIC-VIEWPORT-CONTRACT/0.1"),
    "print_handoff": ("cgx/manufacturing/printspace_product_handoff_v0_1.json",
        "060ec29e90913dc593f2498c3319d3725ca07792",
        "399b0c8721225bc82c0fa275d46e3b175fd5b9eb",
        "CGX-PRINTSPACE-PRODUCTISATION-HANDOFF/0.1"),
    "print_witness": ("cgx/manufacturing/pc01_interface_witness_plan_v0_1.json",
        "a2236e3873e1053b7d409743fcd1bb43db13de17",
        "399b0c8721225bc82c0fa275d46e3b175fd5b9eb",
        "CGX-PRINTSPACE-INTERFACE-WITNESS-PLAN/0.1"),
}
LOAD_MODES = {"read", "review", "wizard_only"}
EXPECTED_WORKSTREAMS = (
    tuple(f"SW-{n:02d}" for n in range(1,8)) +
    tuple(f"NATIVE-{n:02d}" for n in range(1,5)) +
    tuple(f"PHYS-{n:02d}" for n in range(1,6))
)
VIEW_ALIASES = ("document", "3d", "chat", "graph", "interactive", "matrix")
HEXDIGEST = re.compile("[0-9a-f]{64}\\Z")

class CrosswalkHold(ValueError):
    """Unqualified input: fail closed, never substitute inferred source state."""

def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CrosswalkHold(message)

def _file_bytes(repo: Path, path: str, expected_sha: str, tracked: set[str]) -> bytes:
    _require(path in tracked, "source not in Git tracked set")
    p = repo / path
    _require(not p.is_symlink() and p.is_file()
             and p.resolve().is_relative_to(repo.resolve()), "unsafe source path")
    data = p.read_bytes()
    _require(0 < len(data) <= MAX_SOURCE, "source missing or unbounded")
    git_sha = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
    _require(git_sha == expected_sha, "source blob has moved or been modified: " + path)
    return data

def validate_contracts(data: dict[str, dict[str, Any]], registry: dict[str, Any]) -> dict[str, Any]:
    _require(set(data) == set(SOURCE_SPECS), "source contracts missing or extra")
    for name, (_, _, _, schema) in SOURCE_SPECS.items():
        _require(isinstance(data[name], dict) and data[name].get("schema") == schema,
                 "wrong source schema " + name)
    validate_registry(registry)
    a, c, v, p, w = (data[k] for k in SOURCE_SPECS)
    _require(a.get("status") == "SOURCE_REVIEW_NOT_ADMITTED"
             and a.get("parent_filespace") == "Cognigrex.cgx"
             and a.get("alias") == "LOAD.cgx"
             and a.get("canonical_mutation") is False
             and a.get("accepted_parent_object_id") is None
             and a.get("canonical_object_id") is None
             and a.get("network_fetch") == "DENY_UNTIL_HOST_AUTHORIZED",
             "LOAD activation unexpectedly admitted")
    _require(c.get("status") == "SOURCE_REVIEW_NOT_NATIVE_ADMISSION"
             and c.get("parent") == "Cognigrex.cgx"
             and c.get("alias",{}).get("file") == "LOAD.cgx"
             and c.get("alias",{}).get("one_instance_reference_binding") is True,
             "LOAD family alias or parent mismatched")
    _require(v.get("status") == "SOURCE_REVIEW_NOT_NATIVE_ADMISSION"
             and v.get("authority",{}).get("root") == "Cognigrex.cgx"
             and v.get("authority",{}).get("canonical_mutation") is False
             and v.get("security",{}).get("default") == "deny-all-unless-explicit-authorized-object-IDs"
             and set(v.get("view_aliases",{})) == set(VIEW_ALIASES),
             "unqualified LOAD viewport authority")
    for level in ("h0","h1","h2","h3","h4"):
        _require(level in a.get("hydration",{}), "LOAD hydration level missing")
    for name, val in v.get("default_budget",{}).items():
        if name.startswith("max_"):
            ceiling=v.get("hard_ceiling",{}).get(name)
            _require(type(val) is int and type(ceiling) is int
                     and 0 < val <= ceiling, "invalid viewport bound")
    actions=c.get("actions")
    _require(isinstance(actions,dict) and len(actions)==10, "LOAD action census changed")
    action_cards=[]
    for key, spec in sorted(actions.items()):
        _require(re.fullmatch(r"[a-z]+(?:[._][a-z]+)*",key) is not None
                 and isinstance(spec,dict)
                 and spec.get("mode") in LOAD_MODES
                 and isinstance(spec.get("targets"),list)
                 and bool(spec["targets"])
                 and all(isinstance(t,str) and t in ("filespace","file","object") for t in spec["targets"])
                 and isinstance(spec.get("label"),str),
                 "LOAD action requires independent review")
        action_cards.append({
            "id":key,"label":spec["label"],"targets":spec["targets"],
            "source_mode":spec["mode"],"projection_only":True,
            "source_handler_ref":spec.get("handler_ref"),
            "handler_installed_or_executed":False,
            "execution_authorised":False,
        })
    _require(p.get("canonical_repo")=="achillesromer-coder/LightSpeed"
             and p.get("canonical_pr")==236
             and p.get("proof_ceiling")=="PRIVATE_DIGITAL_SOFTWARE_EVALUATION_ONLY_NO_PHYSICAL_CLAIMS",
             "PrintSpace release ceiling changed")
    mode=p.get("automation_mode",{})
    _require(mode.get("exactly_five_existing_coordinators") is True
             and mode.get("new_scheduler_allowed") is False
             and mode.get("native_mutation_allowed") is False
             and mode.get("archive_move_allowed") is False
             and mode.get("public_launch_allowed") is False
             and mode.get("next_product_auto_activation_allowed") is False,
             "unexpected PrintSpace action authority")
    conclusions=p.get("conclusions",{})
    for key in ("physical_product_qualified","software_final_release_approved",
                "file_space_handoff_authorised","data_space_launch_authorised",
                "unispace_launch_authorised","grex_outreach_authorised"):
        _require(conclusions.get(key) is False, "PrintSpace release or physics falsely qualified")
    streams=p.get("open_workstreams")
    _require(isinstance(streams,list) and len(streams)==16
             and {s.get("id") for s in streams if isinstance(s,dict)}==set(EXPECTED_WORKSTREAMS),
             "PrintSpace workstream census mismatch")
    registry_ids={row["id"] for row in registry["task_groups"]}
    _require(set(EXPECTED_WORKSTREAMS)<=registry_ids, "crossspace gate identity mismatch")
    cards=[]
    for s in streams:
        _require(s.get("independently_verified") is False
                 and s.get("automated_action")=="READ_CHECK_REPORT_ONLY"
                 and s.get("status")=="OPEN_VERIFICATION_OR_APPROVAL"
                 and s.get("hold_code"),
                 "PrintSpace workstream silently promoted")
        cards.append({"gate_id":s["id"],"category":s["category"],
                      "hold_code":s["hold_code"],"source_status":s["status"],
                      "native_admitted":False,"source_pr":236})
    _require(w.get("source_scope")=="OWNER_MATRIX_PLANNING_CLASS_ONLY"
             and w.get("evidence_state")=="UNMEASURED"
             and w.get("manufacturing_ir_configuration_hash") is None
             and w.get("manufacturing_ir_ref")=="cgx://manufacturing/build/pc01-three-layer-coupon",
             "PrintSpace witness observed/measured without device proof")
    regions=w.get("region_selections")
    _require(isinstance(regions,list) and len(regions)==3
             and {r.get("instance_id") for r in regions if isinstance(r,dict)}
                 =={"structure","interface","conductive"}, "witness recipe not qualified")
    for r in regions:
        _require(isinstance(r.get("directional_sha256"),str)
                 and HEXDIGEST.fullmatch(r["directional_sha256"]) is not None,
                 "directional evidence digest invalid")
    return {
        "schema":SCHEMA,"canonical_root":PARENT,
        "status":"SOURCE_ONLY_CAPABILITY_FOLD_NOT_NATIVE_ADMISSION",
        "library":{"alias":"LOAD.cgx","parent":"Cognigrex.cgx","family":"FileSpace",
                   "accepted_object_id":None,"native_mounted":False,
                   "hydration_stages":list(a["hydration"]),
                   "viewport_aliases":sorted(v["view_aliases"]),
                   "actions":action_cards},
        "manufacturing":{"family":"PrintSpace","canonical_pr":236,
                         "ir_ref":w["manufacturing_ir_ref"],"physical_proof":"UNMEASURED",
                         "workstreams":cards,
                         "claimed_software_rc_from_source_only":bool(conclusions.get("private_software_rc_verified")),
                         "independent_software_acceptance":False,
                         "real_print_executed":False},
        "original_gate_count":len(registry["task_groups"]),
        "gate_groups_all_open":True,
        "single_root":True,"no_new_scheduler":True,"source_bytes_hydrated":False,
        "native_dbr_performed":False,"machine_actuated":False,"trained":False,
        "published":False,"archive_deleted":False,
    }

def build(repo: Path = ROOT) -> dict[str, Any]:
    repo=repo.resolve(strict=True)
    done=subprocess.run(["git","-C",str(repo),"ls-files","-z"],
        capture_output=True,check=False,timeout=20)
    _require(done.returncode==0, "unable to resolve tracked sources")
    tracked={v.decode("utf-8") for v in done.stdout.split(b"\0") if v}
    documents={}
    receipts=[]
    for key,(path,sha,source_commit,schema) in SOURCE_SPECS.items():
        raw=_file_bytes(repo,path,sha,tracked)
        documents[key]=json.loads(raw)
        receipts.append({"name":key,"path":path,"original_git_blob":sha,
                         "source_commit":source_commit,"source_schema":schema,
                         "source_sha256":hashlib.sha256(raw).hexdigest(),
                         "original_source_remains_at_review_branch":True})
    gate_path="cgx/review/unispace_crossspace_gate_register_v0_1.json"
    gates_raw=_file_bytes(repo,gate_path,
        "ba58ef20210ac5338fda786f60592ccc7b22b9f7",tracked)
    _require(hashlib.sha256(gates_raw).hexdigest()==GATE_SHA256,
             "original crossspace gate register bytes changed")
    report=validate_contracts(documents,json.loads(gates_raw))
    report["source_contracts"]=receipts
    report["gate_register_sha256"]=GATE_SHA256
    report["original_source_head_verification"]="PINNED_GIT_BLOB_READBACK_NOT_LIVE_BRANCH_ADMISSION"
    digest=json.dumps(report,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")
    report["review_sha256"]=hashlib.sha256(digest).hexdigest()
    return report

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,default=ROOT)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    out=json.dumps(build(args.repo),indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(out,encoding="utf-8")
    else:
        print(out,end="")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
