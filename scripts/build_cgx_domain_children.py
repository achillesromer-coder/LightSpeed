#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DT = ROOT / "cgx" / "domain_templates"
RUNTIME_DEFAULT = ROOT / "runtime" / "python"

EXPECTED = {
    "state_id": "S91",
    "release": "v1.61",
    "sha256": "1138da5af4e1c66eb60120dd050e2037fc8d7799a9ccebb01ad48089b234785f",
    "content_root": "af640b499078853371196cf7c905979cebf0761c15552b6b8dfbf3ff3d04448d",
    "dbr_root": "18d43abf68b5f7857a21dcb480d9970e95cdacfc869c61b3b1497e900f0dcc64",
    "topology": "150e5267792f43f47807a9f5ca61f12db8077ac98153c2cc6c306a4177de937e",
}

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def load(name: str):
    return json.loads((DT/name).read_text(encoding="utf-8"))

def save_json(root: Path, rel: str, obj):
    p=root/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def read_json(root: Path, rel: str):
    return json.loads((root/rel).read_text(encoding="utf-8"))

def package_source(root: Path, target_rel: str, template_name: str):
    save_json(root,target_rel,load(template_name))

def common_profiles(root: Path):
    mapping={
        "profiles/work_modes.json":"work_modes.json",
        "profiles/depth_profiles.json":"depth_profiles.json",
        "profiles/dimension_registry.json":"dimension_registry.json",
        "profiles/intake_output.json":"intake_output.json",
        "profiles/reasoning_profiles.json":"reasoning_profiles.json",
        "profiles/toolkit_registry.json":"toolkit_registry.json",
        "profiles/workflow_registry.json":"workflow_registry.json",
        "profiles/interaction_preferences.json":"interaction_preferences.json",
        "profiles/provider_templates.json":"provider_templates.json",
        "profiles/surface_registry.json":"surface_registry.json",
        "profiles/migration_policy.json":"migration_policy.json",
        "profiles/queue_registry.json":"queue_registry.json",
        "semantic/universal_object_extension.json":"universal_object_extension_contract.json",
        "semantic/relation_qualifiers.json":"relation_qualifier_contract.json",
        "semantic/cross_domain_bridges.json":"cross_domain_bridge_registry.json",
        "profiles/semantic_view_registry.json":"semantic_view_lens_registry.json",
        "profiles/view_selection_policy.json":"view_selection_policy.json",
    }
    missing=[src for src in mapping.values() if not (DT/src).is_file()]
    if missing:
        raise FileNotFoundError("missing-domain-template:"+",".join(sorted(missing)))
    for dest,src in mapping.items():
        package_source(root,dest,src)

def source_family_subset(domain: str, inclusion: dict) -> list[dict]:
    keep={"ACR3 Next Stage Consolidation Register","Achilles P.A — Canonical Workbook v1.0"}
    if domain=="romer":
        keep|={"Type 1 Romer Cognigrex","Type 1 Systems Cognigrex","Type 1 Operations Cognigrex","Type1_Asteroid_Operating_Workbook","MPL Engine","M1 Elevated Bypass Living Infrastructure","LightSpeed Web Shell Builder","Romer_EMASSC_LinkDrive_DataIndex_Workbook_v0_1"}
    elif domain=="eco":
        keep|={"Type 1 Eco-Grex","Type 1 Operations Cognigrex","LightSpeed Web Shell Builder","Romer_EMASSC_LinkDrive_DataIndex_Workbook_v0_1"}
    else:
        keep|={"Type 1 Systems Cognigrex","Type 1 Romer Cognigrex","Type 1 Operations Cognigrex","N. LightSpeed","LightSpeed Web Shell Builder","Romer_EMASSC_LinkDrive_DataIndex_Workbook_v0_1"}
    return [x for x in inclusion.get("durable_source_families",[]) if x.get("title") in keep]

def intake_queue(domain: str) -> dict:
    items={
        "romer":[
            {"priority":1,"source":"Mark_III_Digital_Twin_v0_1.xlsx","sha256":"fab23970e80c016a2140ec0f87c1d0d7e15c365190fdacb5dc2ee2a1c2a81075","mode":"TRACK/REFERENCE then semantic assimilation","target":"/romer/mark-iii","status":"review"},
        ],
        "eco":[
            {"priority":1,"source":"Embedded_Bio_Blocks_Digital_Twin_v0_1.xlsx","sha256":"f1cf7a5d3a2e463881cd5389d265d0b70f1b56f849d87da70c57697b75b61d0b","mode":"TRACK/REFERENCE then semantic assimilation","target":"/eco/bio-blocks","status":"review"},
        ],
        "emassc":[
            {"priority":1,"source":"RFS_EMFF_Digital_Twin_Test_Sandbox_v0_1.xlsx","sha256":"1cc3f421ed128186b1ab018f7af8eda27bc30572b21bc8b8a1d2bada91c9a58f","mode":"TRACK/REFERENCE then semantic assimilation","target":"/emassc/rfs-emff","status":"review"},
        ],
        "lightspeed":[
            {"priority":1,"source":"S91 runtime/conformance provider surfaces","mode":"capability/reference binding","target":"/lightspeed/runtime","status":"review"}
        ]
    }
    return {"schema_version":"0.3","domain":domain,"default_action":"review","auto_commit":False,"items":items[domain]}

def domain_payload(domain: str, domains: dict, inclusion: dict, seed_ref: dict, fixture: dict) -> dict[str,object]:
    if domain=="lightspeed":
        em=domains["domains"]["emassc"]
        cfg=em["children"]["lightspeed"]
        semantic_library="emassc_lightspeed_semantic_library.json"
        type_registry="emassc_ls_type_registry.json"
        relation_registry="emassc_ls_relation_registry.json"
        principal="Achilles"
        display="LightSpeed / EMC²"
        modules=["runtime","host","device","node","provider","connector","capability","workflow","job","sync","transport","security","package","conformance"]
        namespace="cgx://romer.industries/emassc/lightspeed"
        parent="EMASSC.cgx"
    else:
        cfg=domains["domains"][domain]
        semantic_library=cfg["semantic_library"]
        type_registry=cfg["type_registry"]
        relation_registry=cfg["relation_registry"]
        principal=cfg.get("principal_agent")
        display=cfg.get("display")
        modules=cfg.get("modules",[])
        namespace=cfg.get("namespace")
        parent="Cognigrex.cgx"
    return {
      "identity/domain.json":{
        "schema_version":"0.3","domain_id":domain,"display_name":display,
        "filespace_filename":cfg["file"],"preferred_namespace":namespace,
        "namespace_status":domains.get("namespace_status"),"logical_master":"cgx://cgx.cgx",
        "parent_filespace":parent,"source_master_reference":seed_ref,
        "authority_transfer":False
      },
      "identity/agent_bindings.json":{
        "schema_version":"0.3","principal_agent":principal,
        "authority":"policy+capability+scoped-owner bounded",
        "network_or_model_strength_never_grants_authority":True
      },
      "governance/authority_model.json":{
        "schema_version":"0.3","domain":domain,"principal_agent":principal,
        "canonical_rule":"one authority per meaning; many representations/providers permitted",
        "transition_rule":"current scoped Drive/Git/CAD/raw-evidence owners remain controlling until parity and explicit semantic promotion",
        "mutation_rule":"Overlay -> owner/policy review -> atomic Resolve/DBR commit -> verifier/readback",
        "ai_rule":"AI output is proposed/derived until promoted under evidence/authority policy",
        "acr3_end_state":"read-only provenance after GST-029 passes; no permanent handoff lane"
      },
      "corpus/domain_map.json":{
        "schema_version":"0.3","domain":domain,"modules":modules,
        "parent_filespace":parent,"semantic_library":semantic_library,
        "type_registry":type_registry,"relation_registry":relation_registry
      },
      "corpus/source_family_registry.json":{
        "schema_version":"0.3","domain":domain,"sources":source_family_subset(domain,inclusion),
        "rule":"provider/source location does not transfer semantic authority"
      },
      "corpus/common_authority_map.json":{
        "schema_version":"0.3","domain":domain,
        "transition_authority":{"acr3":"transition/provenance until GST-029","current_recovery":"S91/v1.61"},
        "source_families":[{"title":x.get("title"),"id":x.get("id"),"role":x.get("role")} for x in source_family_subset(domain,inclusion)]
      },
      "corpus/current_control_snapshot.json":{
        "schema_version":"0.3","classification":"POINTER_ONLY / REFRESH PROVIDER BEFORE CONSEQUENCE",
        "recovery_seed":seed_ref,"acr3_retirement":"HELD / GST-029"
      },
      "corpus/acr3_domain_migration.json":{
        "schema_version":"0.3","domain":domain,"state":"queue-not-bulk-payload",
        "rule":"assimilate unique semantics exactly once; unresolved placement becomes Frontier"
      },
      "corpus/specialist_owner_links.json":{
        "schema_version":"0.3","domain":domain,"source_families":[{"id":x.get("id"),"role":x.get("role")} for x in source_family_subset(domain,inclusion)]
      },
      "frontier/current_gates.json":{
        "schema_version":"0.3","current_recovery":seed_ref,
        "acr3_retirement":{"status":"HELD","gate":"GST-029"},
        "physical_s91":{"status":"OPEN","execution":"CGX-PHY-20260923-BNE-05"},
        "fixture_proof":{"status":fixture.get("status"),"warnings":fixture.get("proof",{}).get("warnings")},
        "rule":"missing evidence/capability remains Frontier and cannot be manufactured by a view"
      },
      "frontier/unresolved_source_and_role_boundaries.json":{
        "schema_version":"0.3","items":inclusion.get("unresolved_frontiers",[])
      },
      "integrations/provider_root_registry.json":{
        "schema_version":"0.3","roots":[{"title":x.get("title"),"provider":"google-drive","file_id":x.get("id"),"role":x.get("role")} for x in source_family_subset(domain,inclusion)]
      },
      "capabilities/specialist_and_external_tools.json":{
        "schema_version":"0.3","policy":"capability is not authority","provider_classes":inclusion.get("capability_and_provider_classes",[])
      },
      "queue/acr3_assimilation.json":{
        "schema_version":"0.3","domain":domain,"status":"ACTIVE_UNTIL_GST-029","exact_once":True
      },
      "queue/first_file_intake.json":intake_queue(domain),
      "representations/default_recipes.json":{
        "schema_version":"0.2","source":"living semantic state",
        "outputs":["cgx","html","pdf","docx","xlsx","pptx","svg","png","json","csv","step","fcstd","obj","glb"],
        "receipt_required":True,"release_default":"internal",
        "rule":"generated artifact is a representation, not semantic authority"
      },
      "publications/derived_surface_registry.json":{
        "schema_version":"0.2","domain":domain,"default":"internal",
        "rule":"publication is a release-gated derived lens; never technical/source authority"
      },
      "proof/pilot_fixture_conformance.json":fixture,
      "semantic/type_registry.json":load(type_registry),
      "semantic/relation_registry.json":load(relation_registry),
      "semantic/library.json":load(semantic_library),
    }

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--master",required=True,type=Path,help="Exact current Recovery .cgx carrier")
    ap.add_argument("--out-dir",required=True,type=Path)
    ap.add_argument("--runtime-python",type=Path,default=RUNTIME_DEFAULT)
    ap.add_argument("--keep-workdirs",action="store_true")
    args=ap.parse_args()

    sys.path.insert(0,str(args.runtime_python.resolve()))
    import cgx_kernel as kernel
    import cgx_hydration as hydration

    if sha256_file(args.master)!=EXPECTED["sha256"]:
        raise SystemExit("FAIL: Recovery seed SHA-256 is not accepted S91")
    ws=kernel.open_workspace(args.master)
    try:
        check=kernel.verify(ws.root)
        if not check.get("ok"): raise SystemExit("FAIL: Recovery verifier: "+";".join(check.get("errors",[])))
        boot=kernel.load_json(ws.root,"cgx/bootstrap.json",{})
        dbr=kernel.load_json(ws.root,"cgx/dbr.json",{})
        if boot.get("state_id")!=EXPECTED["state_id"] or boot.get("content_root")!=EXPECTED["content_root"] or boot.get("topology_snapshot_hash")!=EXPECTED["topology"] or dbr.get("dbr_root")!=EXPECTED["dbr_root"]:
            raise SystemExit("FAIL: Recovery identity/root mismatch")
    finally:
        ws.close()

    domains=load("domains.json")
    fixture=load("pilot_fixture_validation_receipt_2026-09-23.json")
    inclusion=load("corpus_inclusion_registry.json")
    if fixture.get("proof",{}).get("fixtures")!=3 or fixture.get("proof",{}).get("failures")!=0:
        raise SystemExit("FAIL: fixture gate not closed")
    gp=domains.get("generation_policy",{})
    if gp.get("current_recovery_sha256")!=EXPECTED["sha256"]:
        raise SystemExit("FAIL: domains.json Recovery pointer mismatch")

    args.out_dir.mkdir(parents=True,exist_ok=True)
    work=args.out_dir/"work"
    if work.exists(): shutil.rmtree(work)
    work.mkdir()
    template=work/"S91_seed_template"
    seed_result=hydration.create_seed_template(template,args.master,profile_id="reader")
    if not seed_result.get("verify",{}).get("ok"):
        raise SystemExit("FAIL: S91 seed-template verifier")

    seed_ref={
      "object_id":"cgx:phase-a:42d99b46c0d322f08b59b7b7",
      "state_id":"S91","release":"v1.61",
      "content_root":EXPECTED["content_root"],"dbr_root":EXPECTED["dbr_root"],
      "topology_snapshot":EXPECTED["topology"],"carrier_sha256":EXPECTED["sha256"],
      "recovery_file_id":gp.get("current_recovery_file_id"),"verifier":"PASS"
    }

    build_receipt={"schema":"CGX-DOMAIN-CHILD-BUILD/0.1","seed":seed_ref,"fixture_gate":fixture.get("fixture_bundle",{}),"outputs":{}}
    for domain in ("romer","eco","emassc","lightspeed"):
        cfg=domains["domains"][domain] if domain!="lightspeed" else domains["domains"]["emassc"]["children"]["lightspeed"]
        root=work/domain
        inst=hydration.instantiate_seed(template,root,display_name=cfg.get("display",domain))
        if not inst.get("verify",{}).get("ok"):
            raise SystemExit("FAIL: instantiate "+domain)
        payload=domain_payload(domain,domains,inclusion,seed_ref,fixture)
        def op(payload=payload):
            common_profiles(root)
            for rel,obj in payload.items(): save_json(root,rel,obj)
        state=kernel.mutate(root,"domain_base_install",f"Install reviewed {domain} domain base package",op,
            {"domain":domain,"parent":"EMASSC.cgx" if domain=="lightspeed" else "Cognigrex.cgx",
             "review_source":"LightSpeed PR52","fixture_bundle_sha256":fixture.get("fixture_bundle",{}).get("sha256")})
        check=kernel.verify(root)
        if not check.get("ok"):
            raise SystemExit("FAIL: post-install verifier "+domain+":"+";".join(check.get("errors",[])))
        carrier=args.out_dir/cfg["file"]
        kernel.write_carrier(root,carrier)
        packed_sha=sha256_file(carrier)
        reopened=kernel.open_workspace(carrier)
        try:
            reopen_check=kernel.verify(reopened.root)
            rb=kernel.load_json(reopened.root,"cgx/bootstrap.json",{})
            rd=kernel.load_json(reopened.root,"cgx/dbr.json",{})
        finally: reopened.close()
        if not reopen_check.get("ok"):
            raise SystemExit("FAIL: packed reopen verifier "+domain)
        build_receipt["outputs"][domain]={
            "file":cfg["file"],"object_id":rb.get("object_id"),"state_id":rb.get("state_id"),
            "content_root":rb.get("content_root"),"dbr_root":rd.get("dbr_root"),
            "topology":rb.get("topology_snapshot_hash"),"sha256":packed_sha,
            "tracked_objects":len(kernel.load_json(root,"cgx/manifest.json",{}).get("files",[])),
            "commit_verified":state.get("commit_verified"),"verify":"PASS","packed_reopen_verify":"PASS"
        }

    receipt_path=args.out_dir/"BUILD_RECEIPT_S91_DOMAIN_CHILDREN.json"
    receipt_path.write_text(json.dumps(build_receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    if not args.keep_workdirs: shutil.rmtree(work)
    print(json.dumps(build_receipt,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
