"""Non-authoritative CGX/UniSpace capability and library coverage projection.

Reads existing owner registries by reference. Does not create another library,
download third-party sources, run capability routes or certify any adapter.
Output is a bounded read-only inspection for Creator, Press and owner review.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

REGISTRIES = {
    "file_types": "cgx/domain_templates/file_type_conversion_registry.json",
    "lenses": "cgx/domain_templates/semantic_view_lens_registry.json",
    "bridges": "cgx/domain_templates/cross_domain_bridge_registry.json",
    "toolkits": "cgx/domain_templates/toolkit_registry.json",
    "routes": "cgx/domain_templates/plugin_capability_routes.json",
    "corpus": "cgx/domain_templates/corpus_inclusion_registry.json",
    "alexandria": "cgx/review/alexandria_external_reference_intake_20261020.json",
    "passive_edge": "cgx/domain_templates/passive_edge_profile_registry.json",
    "keyed_publication": "cgx/review/unispace_keyed_publication_candidate_20261020.json",
    "first_file_mappings": "cgx/domain_templates/first_file_conversion_registry.json",
    "volumetric_kernel": "cgx/component_atlas/type1_volumetric_kernel_v0_1.json",
    "physical_instance_contract": "cgx/component_atlas/component_instance_build_packet_contract_v0_1.json"
}

def _load(root: Path, relative: str) -> tuple[dict[str, Any], dict[str, Any]]:
    f = root / relative
    raw = f.read_bytes()
    if len(raw) > 10_000_000:
        raise ValueError("registry source exceeds bounded scan")
    doc = json.loads(raw)
    if not isinstance(doc, dict):
        raise ValueError("registry must be an object")
    return doc, {"source_path": relative, "source_sha256": hashlib.sha256(raw).hexdigest(),
                 "source_bytes": len(raw), "owner": "existing-source-file-not-this-projection"}

def _unique_ids(records: list, key: str = "id") -> None:
    ids = [(x.get(key) if isinstance(x, dict) else x) for x in records]
    if any(not isinstance(i, str) or not i.strip() for i in ids):
        raise ValueError("blank or malformed registry identifier")
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate registry identities must not be silently collapsed")

def build_library_coverage(root: Path = ROOT) -> dict[str, Any]:
    sources = {}
    d = {}
    for k, p in REGISTRIES.items():
        d[k], sources[k] = _load(root, p)
    types = d["file_types"]["types"]
    lenses = d["lenses"]
    shared = lenses["shared_view_families"]
    eco = lenses["eco_specialised_views"]
    romer = lenses["romer_specialised_views"]
    emassc = lenses["emassc_ls_specialised_views"]
    bridges = d["bridges"]["bridge_types"]
    toolkits = d["toolkits"]["toolkits"]
    routes = d["routes"]["routes"]
    semantic = d["corpus"]["first_class_semantic_classes"]
    providers = d["corpus"]["durable_source_families"]
    external = d["alexandria"]["groups"]
    profiles = d["passive_edge"]["profiles"]
    first_file = d["first_file_mappings"]["mappings"]
    volumetric = d["volumetric_kernel"]["records"]
    instance_classes = d["physical_instance_contract"]["instance_types"]

    for seq in (types,shared,eco,romer,emassc,bridges,toolkits,semantic,providers,profiles):
        _unique_ids(seq, key="id")
    if not isinstance(routes, dict) or len(routes) != len(set(routes)):
        raise ValueError("tool routes must be keyed unique dictionary")
    for name, route in routes.items():
        if not isinstance(name,str) or not isinstance(route,dict):
            raise ValueError("invalid capability route declaration")
    if any(not isinstance(g.get("records"),list) for g in external):
        raise ValueError("external catalogue groups missing")
    for group in external:
        if not isinstance(group.get("origin"),dict):
            raise ValueError("external group origin required")
        if any(r.get("state") != "DISCOVERY_REFERENCE_ONLY" or
               r.get("rights") != "UPSTREAM_LICENSE_UNVERIFIED" for r in group["records"]):
            raise ValueError("external references must not be auto-licensed")

    all_lens_names = [x["id"] for x in shared] + eco + romer + emassc
    _unique_ids(all_lens_names)
    _unique_ids(first_file, key="mapping_id")
    _unique_ids(volumetric, key="kernel_id")
    _unique_ids(instance_classes)
    type_statuses = dict(sorted(Counter(t["status"] for t in types).items()))
    route_states = dict(sorted(Counter(r.get("state", "UNCLASSIFIED") for r in routes.values()).items()))
    groups = [{
        "catalogue": g["origin"]["name"], "source_commit": g["origin"]["commit"],
        "entry_count": len(g["records"]),
        "unique_declared_source_links": len(set(
            link for item in g["records"] for link in item.get("sources", []))),
        "payload_downloaded": False,"licences_checked":False
    } for g in external]

    return {
        "schema": "CGX-UNISPACE-LIBRARY-COVERAGE-PROJECTION/0.1",
        "status": "DERIVED_READ_ONLY_NOT_AUTHORITY_NOT_LIVE_CAPABILITY_PROOF",
        "root": "Cognigrex.cgx",
        "source_roots": sources,
        "counts": {
            "declared_file_profiles": len(types),
            "shared_lenses": len(shared),
            "domain_lenses": len(eco)+len(romer)+len(emassc),
            "total_distinct_lenses": len(all_lens_names),
            "bridge_types": len(bridges),
            "toolkits": len(toolkits),
            "registered_capability_routes": len(routes),
            "semantic_classes": len(semantic),
            "durable_source_families": len(providers),
            "external_index_entries": sum(x["entry_count"] for x in groups),
            "passive_edge_profiles": len(profiles),
            "first_file_mappings": len(first_file),
            "volumetric_kernels": len(volumetric),
            "physical_instance_classes": len(instance_classes)
        },
        "file_type_declarations": {
            "status_counts": type_statuses,
            "types": [{
                "media_type": t["id"],
                "adapter_id": t.get("adapter"),
                "declared_status": t["status"],
                "execution_test": "NOT_PERFORMED_BY_COVERAGE_PROJECTION"
            } for t in types]
        },
        "conversion_mapping_catalogue": [{"mapping_id": m["mapping_id"],
                                         "domain": m.get("domain"),
                                         "declared_status": d["first_file_mappings"].get("status"),
                                         "independently_retested": False}
                                        for m in first_file],
        "geometry_kernel_catalogue": [{"kernel_id": k["kernel_id"],
                                       "evidence_ceiling": "SYMBOLIC_TOPOLOGY_NOT_PHYSICAL_QUALIFICATION"}
                                      for k in volumetric],
        "physical_instance_classes": instance_classes,
        "lens_catalogue": all_lens_names,
        "bridge_catalogue": [b["id"] for b in bridges],
        "toolkit_catalogue": [t["id"] for t in toolkits],
        "route_catalogue": [{
            "id": name, "declared_state": r.get("state","UNCLASSIFIED"),
            "live_probed": False
        } for name,r in sorted(routes.items())],
        "route_state_counts": route_states,
        "semantic_classes": semantic,
        "durable_owner_source_refs": [
            {"title": p.get("title"),"id":p["id"],"access_verified":False}
            for p in providers
        ],
        "external_reference_catalogue": groups,
        "pending_frontiers": [
            {"id": x.get("id"),"topic":x.get("topic"),"state":"SOURCE_REGISTERED_NOT_RESOLVED"}
            for x in d["corpus"].get("unresolved_frontiers",[])
        ],
        "activation_gates": list(d["keyed_publication"]["activation_gates"]),
        "admission_notes": [
            "Registered format is not proof of a loaded decoder or faithful round-trip.",
            "Runtime route 'available' is a declaration; this scan does not call tools or verify host process.",
            "A game/engine link is discovery only; no third-party game bytes acquired, used or licensed by this scan.",
            "Actual functionality requires host/device execution, source readback, rights and release scope.",
            "Volumetric kernels are symbolic topology families, not qualified CAD, supplier dimensions or component instances.",
            "First-file source mappings and reported historic fixtures are not newly independently tested by this coverage view.",
            "No duplicate object master, file rewriter, release grant, app, private index or supplier inventory is created."
        ]
    }

if __name__ == "__main__":
    print(json.dumps(build_library_coverage(), indent=2, ensure_ascii=False))
