#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DT = ROOT / "cgx" / "domain_templates"

def load(name):
    p = DT / name
    if not p.exists():
        raise AssertionError(f"missing required template: {name}")
    return json.loads(p.read_text(encoding="utf-8"))

def flatten_type_values(obj):
    out=[]
    if isinstance(obj, dict):
        for k,v in obj.items():
            if k in {"schema","status","domain","domains","rule","numeric_model_rule","host_local_default","pilot_additions"}:
                continue
            out.extend(flatten_type_values(v))
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v,str):
                out.append(v)
            elif isinstance(v,(dict,list)):
                out.extend(flatten_type_values(v))
    return out

def relation_ids(obj):
    out=set()
    if isinstance(obj, dict):
        if isinstance(obj.get("id"),str):
            out.add(obj["id"])
        for v in obj.values():
            out |= relation_ids(v)
    elif isinstance(obj,list):
        for v in obj:
            out |= relation_ids(v)
    return out

def main():
    failures=[]; warnings=[]
    try:
        domains=load("domains.json")
        shell=load("corpus_aware_base_shell_contract.json")
        receipt=load("pilot_fixture_validation_receipt_2026-09-23.json")
        views=load("semantic_view_lens_registry.json")
        shared_rel=load("relation_qualifier_contract.json")
        bridge=load("cross_domain_bridge_registry.json")
        ext_registry=load("custodial_extension_registry.json")
        cgp_policy=load("cgp_ies_policy_pack.json")
        cgp_fixtures=load("cgp_ies_fixture_scenarios.json")
        cgp_terminology=load("cgp_ies_terminology_map.json")
        cgp_adapters=load("cgp_ies_domain_adapter_registry.json")
        cgp_decision_receipt=load("cgp_ies_decision_receipt_schema.json")
        cgp_owner_values=load("cgp_ies_owner_confirmation_values.json")
        cgp_parent_hydration=load("cgp_ies_parent_extension_manifest.json")
        cgp_authority_ref=load("cgp_ies_authority_phase_ref.json")
        cgp_visibility=load("cgp_ies_release_visibility_policy.json")
        s92_promotion=load("s92_recovery_promotion_verification_2026-09-30.json")
        assurance_registry=load("assurance_method_registry.json")
        assurance_schema=load("unified_assurance_object_schema.json")
        assurance_matrix=load("assurance_selection_matrix.json")
        assurance_crosswalk=load("assurance_reference_crosswalk.json")
        assurance_fixtures=load("assurance_fixture_scenarios.json")
        technology_stack=load("technology_stack_registry.json")
        agent_runtime=load("agent_runtime_contract.json")
        query_policy=load("query_normalisation_policy.json")
        corpus_test_policy=load("corpus_test_simulation_policy.json")
        corpus_test_caps=load("corpus_test_capability_registry.json")
        domain_identity=load("domain_child_identity_registry.json")
        file_conversion=load("file_conversion_contract.json")
        file_type_conversion=load("file_type_conversion_registry.json")
        first_file_conversion=load("first_file_conversion_registry.json")
        child_successor_receipt=load("s92_domain_children_successor_validation_receipt_2026-10-01.json")
        first_file_migration_receipt=load("s92_first_file_migration_receipt_2026-10-01.json")
        source_envelope=load("source_envelope_contract.json")
        source_adapters=load("source_format_adapter_registry.json")
        provider_notifications=load("provider_notification_evidence_contract.json")
    except Exception as e:
        print(json.dumps({"status":"FAIL","failures":[str(e)]}))
        return 1

    if domains.get("schema")!="CGX-DOMAIN-TEMPLATES/0.4":
        failures.append("domains schema is not 0.4")
    if provider_notifications.get("schema")!="CGX-PROVIDER-NOTIFICATION-EVIDENCE/0.1":
        failures.append("provider notification evidence contract schema mismatch")
    if domains.get("shared_contracts",{}).get("provider_notification_evidence")!="provider_notification_evidence_contract.json":
        failures.append("provider notification evidence contract not registered")
    inv=set(provider_notifications.get("invariants") or [])
    if "email-notification-alone-never-closes-or-promotes-canonical-defect-state" not in inv:
        failures.append("provider notification contract lacks secondary-evidence boundary")
    if shell.get("schema")!="CGX-CORPUS-AWARE-BASE-SHELL/0.6":
        failures.append("base-shell contract is not 0.6")
    if domains.get("parent_filespace",{}).get("file")!="Cognigrex.cgx":
        failures.append("parent filespace is not Cognigrex.cgx")

    gp=domains.get("generation_policy",{})
    if gp.get("source_authority")!="latest-durably-observed-Recovery-authority-only":
        failures.append("generator seed is not Recovery-only")
    if "seed-from-unpromoted-validation-candidate" not in gp.get("forbidden",[]):
        failures.append("unpromoted Validation seed is not fail-closed")
    expected_seed={
        "state":"S92",
        "sha256":"722558c274416c8e3d7e555575fb7fa43e0538aca72d6875ee06bb1486175db5",
        "content_root":"bf851642ac5bef93e8b9663f71ea4aa94ede30bf057528101773dd12de830bc1",
        "dbr_root":"a7da29629904db2ac82218eaf36c916adbc057a7e954104053078afbf288ad66",
        "topology":"13cc735955ff8aaabdaf43aed968b510b5dab85416fbb7adee5807215c781074",
    }
    if gp.get("current_recovery_state")!=expected_seed["state"]:
        failures.append("current Recovery pointer is not S92")
    if gp.get("current_recovery_sha256")!=expected_seed["sha256"]:
        failures.append("current Recovery SHA-256 mismatch")
    if gp.get("current_recovery_content_root")!=expected_seed["content_root"]:
        failures.append("current Recovery content-root mismatch")
    if gp.get("current_recovery_dbr_root")!=expected_seed["dbr_root"]:
        failures.append("current Recovery DBR-root mismatch")
    if gp.get("current_recovery_topology")!=expected_seed["topology"]:
        failures.append("current Recovery topology mismatch")
    if gp.get("accepted_later_candidate") not in (None,"",[]):
        warnings.append("later candidate remains populated after S92 Recovery promotion")
    promo=gp.get("recovery_promotion_evidence") or {}
    if not promo.get("exact_byte_match") or not promo.get("download_readback"):
        failures.append("S92 Recovery promotion lacks exact-byte/readback receipt")
    if s92_promotion.get("status")!="PROMOTED_AND_READBACK_VERIFIED":
        failures.append("S92 promotion verification is not promoted/readback verified")
    sr=s92_promotion.get("recovery",{})
    if sr.get("sha256")!=expected_seed["sha256"] or sr.get("drive_id")!=gp.get("current_recovery_file_id"):
        failures.append("S92 promotion verification does not match current Recovery pointer")

    if query_policy.get("schema")!="CGX-QUERY-NORMALISATION-POLICY/0.1":
        failures.append("query-normalisation policy schema mismatch")
    query_constraints=set(query_policy.get("hard_constraints") or [])
    if "when a native checkbox, dropdown, range, scope or selector can represent a constraint, use that control before adding query prose" not in query_constraints:
        failures.append("query-normalisation native-control precedence missing")
    if query_policy.get("output",{}).get("canonical_mutation") is not False:
        failures.append("query-normalisation must not mutate canon")

    if corpus_test_policy.get("schema")!="CGX-CORPUS-TEST-CASCADE/0.1":
        failures.append("corpus-test policy schema mismatch")
    if corpus_test_policy.get("result_policy",{}).get("known_before_execution") is not False:
        failures.append("corpus-test policy pre-populates results")
    if corpus_test_policy.get("activation",{}).get("automatic_external_or_physical_activation") is not False:
        failures.append("corpus-test policy permits automatic external/physical activation")
    final_gate=corpus_test_policy.get("result_policy",{}).get("required_final_gate") or {}
    for field,expected in (("proof_state","proven"),("readback_state","verified"),("commit_state","committed")):
        if final_gate.get(field)!=expected:
            failures.append(f"corpus-test final gate missing {field}={expected}")

    if corpus_test_caps.get("schema")!="CGX-CORPUS-TEST-CAPABILITY-REGISTRY/0.1":
        failures.append("corpus-test capability registry schema mismatch")
    caps={x.get("capability_id"):x for x in corpus_test_caps.get("capabilities",[]) if isinstance(x,dict)}
    for capability_id in ("rfs-emff-screening","gmat","mpl","python-deterministic"):
        if capability_id not in caps:
            failures.append(f"corpus-test capability missing: {capability_id}")
        elif caps[capability_id].get("corpus_packet_required_for_orchestrated_execution") is not True:
            failures.append(f"corpus packet not required for {capability_id}")

    if domain_identity.get("schema")!="CGX-DOMAIN-CHILD-IDENTITY/0.1":
        failures.append("domain child identity registry schema mismatch")
    expected_child_ids={
        "romer":("cgx:domain:romer","cgx:root:cognigrex"),
        "eco":("cgx:domain:eco","cgx:root:cognigrex"),
        "emassc":("cgx:domain:emassc","cgx:root:cognigrex"),
        "lightspeed":("cgx:domain:lightspeed","cgx:domain:emassc"),
    }
    children=domain_identity.get("children") or {}
    for domain,(semantic_id,parent_id) in expected_child_ids.items():
        child=children.get(domain) or {}
        if child.get("semantic_object_id")!=semantic_id:
            failures.append(f"stable semantic identity mismatch for {domain}")
        if child.get("parent_semantic_object_id")!=parent_id:
            failures.append(f"stable semantic parent mismatch for {domain}")

    if file_conversion.get("schema")!="CGX-FILE-CONVERSION-CONTRACT/0.1":
        failures.append("file conversion contract schema mismatch")
    classes=file_conversion.get("classes") or {}
    for class_id in ("R0_EXACT","R1_SEMANTIC_REVERSIBLE","R2_RECONSTRUCTED","R3_GENERATIVE"):
        if class_id not in classes:
            failures.append(f"file conversion class missing: {class_id}")
    conversion_invariants=set(file_conversion.get("invariants") or [])
    for required in (
        "no bulk file-format conversion automatically transfers semantic authority",
        "unknown or unsupported structure remains Frontier rather than being guessed",
        "R3 views never close R0/R1/R2 evidence gaps",
    ):
        if required not in conversion_invariants:
            failures.append(f"file conversion invariant missing: {required}")

    if file_type_conversion.get("schema")!="CGX-FILE-TYPE-CONVERSION-REGISTRY/0.1":
        failures.append("file type conversion registry schema mismatch")
    type_items=file_type_conversion.get("types") or []
    type_ids={item.get("id") for item in type_items if isinstance(item,dict)}
    for required in (
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/html",
        "application/x-cgx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/xml",
        "application/zip",
        "model/ply",
        "model/3mf",
        "application/toml",
        "application/yaml",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.oasis.opendocument.presentation",
        "application/vnd.sqlite3",
        "image/vnd.dxf",
        "image/vnd.dwg",
        "application/vnd.apache.parquet",
    ):
        if required not in type_ids:
            failures.append(f"file type conversion capability missing: {required}")
    if (file_type_conversion.get("fallback") or {}).get("status")!="R0-reference-only":
        failures.append("unknown file conversion fallback is not R0-reference-only")

    if source_envelope.get("schema")!="CGX-SOURCE-ENVELOPE/0.1":
        failures.append("source envelope contract schema mismatch")
    if source_envelope.get("parent_conversion_contract")!="file_conversion_contract.json":
        failures.append("source envelope is not bound to canonical conversion contract")
    if source_envelope.get("type_authority")!="file_type_conversion_registry.json":
        failures.append("source envelope is not bound to canonical file-type registry")
    if source_envelope.get("canonical_mutation") is not False:
        failures.append("source envelope must remain read-only projection")

    if source_adapters.get("schema")!="CGX-SOURCE-FORMAT-ADAPTER-REGISTRY/0.1":
        failures.append("source adapter registry schema mismatch")
    if source_adapters.get("parent_type_registry")!="file_type_conversion_registry.json":
        failures.append("source adapter registry lacks parent type authority")
    adapter_ids={item.get("adapter_id") for item in source_adapters.get("adapters",[]) if isinstance(item,dict)}
    for required in ("text-stdlib-v0.1","toml-stdlib-v0.1","json-stdlib-v0.1","csv-stdlib-v0.1","docx-ooxml-stdlib-v0.1","xlsx-ooxml-stdlib-v0.1","pptx-ooxml-stdlib-v0.1","xml-stdlib-v0.1","zip-stdlib-v0.1","odf-stdlib-v0.1","sqlite-stdlib-v0.1","dxf-ascii-stdlib-v0.1","dwg-reference-v0.1","parquet-reference-v0.1","html-stdlib-v0.1","svg-xml-stdlib-v0.1","image-metadata-stdlib-v0.1","gltf-stdlib-v0.1","step-part21-stdlib-v0.1","freecad-fcstd-stdlib-v0.1","obj-mesh-stdlib-v0.1","stl-mesh-stdlib-v0.1","ply-mesh-stdlib-v0.1","3mf-stdlib-v0.1"):
        if required not in adapter_ids:
            failures.append(f"source intake adapter missing: {required}")

    type_by_id={item.get("id"):item for item in file_type_conversion.get("types",[]) if isinstance(item,dict)}
    adapter_expectations={
        "text/plain":"text-stdlib-v0.1",
        "text/markdown":"text-stdlib-v0.1",
        "application/json":"json-stdlib-v0.1",
        "text/csv":"csv-stdlib-v0.1",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":"xlsx-ooxml-stdlib-v0.1",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document":"docx-ooxml-stdlib-v0.1",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation":"pptx-ooxml-stdlib-v0.1",
        "application/xml":"xml-stdlib-v0.1",
        "application/zip":"zip-stdlib-v0.1",
        "application/toml":"toml-stdlib-v0.1",
        "application/yaml":"text-stdlib-v0.1",
        "application/vnd.oasis.opendocument.text":"odf-stdlib-v0.1",
        "application/vnd.oasis.opendocument.spreadsheet":"odf-stdlib-v0.1",
        "application/vnd.oasis.opendocument.presentation":"odf-stdlib-v0.1",
        "application/vnd.sqlite3":"sqlite-stdlib-v0.1",
        "image/vnd.dxf":"dxf-ascii-stdlib-v0.1",
        "image/vnd.dwg":"dwg-reference-v0.1",
        "application/vnd.apache.parquet":"parquet-reference-v0.1",
        "text/html":"html-stdlib-v0.1",
        "image/svg+xml":"svg-xml-stdlib-v0.1",
        "image/png":"image-metadata-stdlib-v0.1",
        "image/jpeg":"image-metadata-stdlib-v0.1",
        "image/gif":"image-metadata-stdlib-v0.1",
        "model/gltf+json":"gltf-stdlib-v0.1",
        "model/gltf-binary":"gltf-stdlib-v0.1",
        "model/step":"step-part21-stdlib-v0.1",
        "application/x-freecad":"freecad-fcstd-stdlib-v0.1",
        "model/obj":"obj-mesh-stdlib-v0.1",
        "model/stl":"stl-mesh-stdlib-v0.1",
        "model/ply":"ply-mesh-stdlib-v0.1",
        "model/3mf":"3mf-stdlib-v0.1",
    }
    for media_type,adapter_id in adapter_expectations.items():
        item=type_by_id.get(media_type) or {}
        if item.get("adapter")!=adapter_id:
            failures.append(f"source intake adapter mismatch: {media_type} -> {item.get('adapter')} expected {adapter_id}")
    if (type_by_id.get("application/pdf") or {}).get("status")!="capability-gated":
        failures.append("PDF conversion must remain capability-gated until specialist parser is bound")
    if any((type_by_id.get(media_type) or {}).get("status")!="capability-gated" for media_type in ("image/vnd.dwg","application/vnd.apache.parquet")):
        failures.append("DWG and Parquet must remain capability-gated until specialist parsers are bound")
    if (type_by_id.get("application/yaml") or {}).get("status")!="supported-text-only":
        failures.append("YAML must remain text-only until a semantic YAML adapter is admitted")

    if first_file_conversion.get("schema")!="CGX-FIRST-FILE-CONVERSION-REGISTRY/0.1":
        failures.append("first-file conversion registry schema mismatch")
    mappings=first_file_conversion.get("mappings") or []
    mapping_ids=[item.get("mapping_id") for item in mappings if isinstance(item,dict)]
    if len(mapping_ids)!=len(set(mapping_ids)):
        failures.append("first-file mapping IDs are duplicated")
    expected_first_files={
        "FF-MARK3-XLSX-001":("fab23970e80c016a2140ec0f87c1d0d7e15c365190fdacb5dc2ee2a1c2a81075",13,8,6),
        "FF-ECO-BIOBLOCK-XLSX-001":("f1cf7a5d3a2e463881cd5389d265d0b70f1b56f849d87da70c57697b75b61d0b",14,11,9),
        "FF-RFS-EMFF-XLSX-001":("1cc3f421ed128186b1ab018f7af8eda27bc30572b21bc8b8a1d2bada91c9a58f",12,11,6),
    }
    by_mapping={item.get("mapping_id"):item for item in mappings if isinstance(item,dict)}
    for mapping_id,(source_hash,cells,objects,relations) in expected_first_files.items():
        item=by_mapping.get(mapping_id) or {}
        if item.get("source_sha256")!=source_hash:
            failures.append(f"first-file source hash mismatch: {mapping_id}")
        proof=item.get("s91_proof") or {}
        for key,expected in (("cells",cells),("objects",objects),("relations",relations)):
            if proof.get(key)!=expected:
                failures.append(f"first-file S91 proof mismatch: {mapping_id}:{key}")
    relation_registry_by_domain={
        "romer":load("romer_relation_registry.json"),
        "eco":load("eco_relation_registry.json"),
        "emassc":load("emassc_ls_relation_registry.json"),
    }
    for mapping_id,item in by_mapping.items():
        domain=item.get("domain")
        if domain not in relation_registry_by_domain:
            continue
        admitted=relation_ids(relation_registry_by_domain[domain])
        missing=sorted(set(item.get("required_relation_types") or [])-admitted)
        if missing:
            failures.append(
                f"first-file relation vocabulary missing for {mapping_id}: {', '.join(missing)}"
            )

    ls_bridge=by_mapping.get("FF-RFS-LS-BRIDGE-001") or {}
    if (ls_bridge.get("s91_proof") or {}).get("scientific_state_duplicated") is not False:
        failures.append("LS first-file bridge must not duplicate EMASSC scientific authority")

    if child_successor_receipt.get("schema")!="CGX-S92-DOMAIN-CHILD-SUCCESSOR-VALIDATION/0.1":
        failures.append("S92 child successor receipt schema mismatch")
    if "DURABLE_PERSISTENCE_OPEN" not in child_successor_receipt.get("status",""):
        failures.append("S92 child successor receipt must preserve open persistence gate")
    persistence=child_successor_receipt.get("persistence") or {}
    if persistence.get("write_succeeded") is not False:
        failures.append("S92 child successor receipt falsely claims durable persistence")
    child_outputs=child_successor_receipt.get("outputs") or {}
    expected_semantic_ids={
        "romer":"cgx:domain:romer",
        "eco":"cgx:domain:eco",
        "emassc":"cgx:domain:emassc",
        "lightspeed":"cgx:domain:lightspeed",
    }
    for domain,semantic_id in expected_semantic_ids.items():
        output=child_outputs.get(domain) or {}
        if output.get("semantic_object_id")!=semantic_id:
            failures.append(f"S92 successor semantic identity mismatch: {domain}")
        if output.get("verify")!="PASS" or output.get("packed_reopen_verify")!="PASS":
            failures.append(f"S92 successor verifier receipt not PASS: {domain}")

    if first_file_migration_receipt.get("schema")!="CGX-S92-FIRST-FILE-MIGRATION-RECEIPT/0.1":
        failures.append("S92 first-file migration receipt schema mismatch")
    if "DURABLE_PERSISTENCE_OPEN" not in first_file_migration_receipt.get("status",""):
        failures.append("S92 first-file migration receipt must preserve open persistence gate")
    migration_outputs=first_file_migration_receipt.get("outputs") or {}
    for domain,semantic_id in expected_semantic_ids.items():
        output=migration_outputs.get(domain) or {}
        if output.get("semantic_object_id")!=semantic_id:
            failures.append(f"S92 first-file migration semantic identity mismatch: {domain}")
        if output.get("verify")!="PASS" or output.get("packed_reopen_verify")!="PASS":
            failures.append(f"S92 first-file migration verifier receipt not PASS: {domain}")
    if (migration_outputs.get("lightspeed") or {}).get("scientific_state_duplicated") is not False:
        failures.append("S92 LightSpeed migration must not duplicate EMASSC scientific state")

    shared=domains.get("shared_contracts",{})
    for key,name in shared.items():
        if not (DT/name).exists():
            failures.append(f"shared contract missing: {key} -> {name}")

    view_ids={x.get("id") for x in views.get("shared_view_families",[]) if isinstance(x,dict)}
    for key in ("eco_specialised_views","romer_specialised_views","emassc_ls_specialised_views"):
        view_ids.update(v for v in views.get(key,[]) if isinstance(v,str))

    domain_files={
        "romer":("romer_type_registry.json","romer_relation_registry.json"),
        "eco":("eco_type_registry.json","eco_relation_registry.json"),
        "emassc":("emassc_ls_type_registry.json","emassc_ls_relation_registry.json"),
    }
    shared_rel_ids=relation_ids(shared_rel)
    for domain,cfg in domains.get("domains",{}).items():
        if domain not in domain_files:
            continue
        tname,rname=domain_files[domain]
        typ=load(tname); rel=load(rname)
        vals=flatten_type_values(typ)
        dup=sorted({x for x in vals if vals.count(x)>1})
        if dup:
            warnings.append(f"{domain}: repeated type labels across registry groups: {dup}")
        if not relation_ids(rel):
            failures.append(f"{domain}: no typed relations")
        if not shared_rel_ids:
            failures.append("shared relation registry empty")
        for field in ("semantic_library","type_registry","relation_registry"):
            ref=cfg.get(field)
            if not ref or not (DT/ref).exists():
                failures.append(f"{domain}: unresolved {field}: {ref}")
        for v in cfg.get("default_views",[]):
            if v not in view_ids:
                failures.append(f"{domain}: unknown default view: {v}")

    ls=domains.get("domains",{}).get("emassc",{}).get("children",{}).get("lightspeed")
    if not ls or ls.get("file")!="LS.cgx":
        failures.append("LS.cgx is not bound beneath EMASSC")

    cgp=[x for x in ext_registry.get("extensions",[]) if x.get("id")=="cgp-ies"]
    if len(cgp)!=1:
        failures.append("cgp-ies shared extension missing or duplicated")
    else:
        cgp=cgp[0]
        if cgp.get("binding_mode")!="REFERENCE":
            failures.append("cgp-ies must bind by reference")
        if cgp.get("source_path")!="Cognigrex.cgx:/extensions/cgp-ies":
            failures.append("cgp-ies parent source path mismatch")
    if cgp_policy.get("schema")!="CGX-CGP-IES-POLICY/0.1":
        failures.append("cgp-ies policy schema mismatch")
    if len(cgp_fixtures.get("scenarios",[]))<22:
        failures.append("cgp-ies fixture coverage below twenty-two scenarios")
    if cgp_terminology.get("schema")!="CGX-CGP-IES-TERMINOLOGY/0.1":
        failures.append("cgp-ies terminology schema mismatch")
    if cgp_adapters.get("schema")!="CGX-CGP-IES-DOMAIN-ADAPTERS/0.1":
        failures.append("cgp-ies domain adapter schema mismatch")
    if set(cgp_adapters.get("domains",{})) != {"romer","eco","emassc","lightspeed"}:
        failures.append("cgp-ies domain adapter coverage mismatch")
    if cgp_decision_receipt.get("schema")!="CGX-CGP-IES-DECISION-RECEIPT/0.1":
        failures.append("cgp-ies decision receipt schema mismatch")
    if "ACCEPTED_BASELINES" not in cgp_owner_values.get("status",""):
        failures.append("cgp-ies owner baseline acceptance missing")
    if cgp_authority_ref.get("schema")!="CGX-CGP-IES-AUTHORITY-PHASE-REF/0.1":
        failures.append("cgp-ies authority phase ref schema mismatch")
    if cgp_authority_ref.get("detailed_contract_class")!="Restricted":
        failures.append("cgp-ies detailed authority contract must remain Restricted")
    if cgp_visibility.get("schema")!="CGX-CGP-IES-RELEASE-VISIBILITY/0.1":
        failures.append("cgp-ies release visibility schema mismatch")
    if "detailed root-authority topology" not in cgp_visibility.get("public_projection_deny",[]):
        failures.append("cgp-ies public deny list missing root authority topology")
    if cgp_parent_hydration.get("status")!="PROMOTED_S92 / HISTORICAL_REPRODUCIBLE_BUILD_MANIFEST":
        failures.append("cgp-ies parent hydration manifest promotion state mismatch")
    if cgp_parent_hydration.get("seed",{}).get("sha256")!="1138da5af4e1c66eb60120dd050e2037fc8d7799a9ccebb01ad48089b234785f":
        failures.append("cgp-ies historical parent build seed is not exact S91 predecessor")
    if cgp_parent_hydration.get("promotion",{}).get("recovery_sha256")!=expected_seed["sha256"]:
        failures.append("cgp-ies parent build manifest does not point to promoted S92")
    if "extensions/bindings" not in shell.get("required_sections",[]):
        failures.append("base shell does not require extension binding")

    if assurance_registry.get("location")!="Cognigrex.cgx:/assurance":
        failures.append("assurance parent source path mismatch")
    if assurance_schema.get("schema")!="CGX-UNIFIED-ASSURANCE-OBJECT/0.1":
        failures.append("unified assurance object schema mismatch")
    if assurance_matrix.get("schema")!="CGX-ASSURANCE-SELECTION-MATRIX/0.1":
        failures.append("assurance selection matrix schema mismatch")
    if assurance_crosswalk.get("status")!="applicability map / not certification":
        failures.append("assurance reference crosswalk must remain non-certification")
    if len(assurance_fixtures.get("scenarios",[]))<10:
        failures.append("assurance fixture coverage below ten scenarios")
    if "assurance/bindings" not in shell.get("required_sections",[]):
        failures.append("base shell does not require assurance binding")
    if "assurance" not in domains.get("parent_filespace",{}).get("shared_kernel",[]):
        failures.append("assurance missing from parent shared kernel")

    if technology_stack.get("schema")!="CGX-TECHNOLOGY-STACK/0.1":
        failures.append("technology stack schema mismatch")
    if technology_stack.get("location")!="Cognigrex.cgx:/stack":
        failures.append("technology stack parent path mismatch")
    if agent_runtime.get("schema")!="CGX-AGENT-RUNTIME-CONTRACT/0.1":
        failures.append("agent runtime contract schema mismatch")
    if "model-is-capability-not-agent-identity" not in agent_runtime.get("invariants",[]):
        failures.append("agent/model identity boundary missing")

    proof=receipt.get("proof",{})
    if proof.get("fixtures")!=3 or proof.get("failures")!=0:
        failures.append("pilot fixture proof is not 3 fixtures / 0 failures")
    if proof.get("warnings")!=2:
        warnings.append("pilot warning count changed from expected bounded value 2")
    if receipt.get("generator_gate") is None:
        failures.append("pilot receipt lacks generator gate")
    if bridge.get("location")!="Cognigrex.cgx:/graph/bridges":
        failures.append("cross-domain bridge registry is not parent-bound")

    result={
        "status":"PASS" if not failures else "FAIL",
        "failures":failures,
        "warnings":warnings,
        "recovery_seed":gp.get("current_recovery_state"),
        "later_candidate":gp.get("accepted_later_candidate"),
        "fixture_bundle_sha256":receipt.get("fixture_bundle",{}).get("sha256"),
        "recovery_sha256":gp.get("current_recovery_sha256"),
        "recovery_content_root":gp.get("current_recovery_content_root"),
        "recovery_dbr_root":gp.get("current_recovery_dbr_root"),
        "recovery_topology":gp.get("current_recovery_topology"),
    }
    print(json.dumps(result,sort_keys=True))
    return 1 if failures else 0

if __name__=="__main__":
    sys.exit(main())
