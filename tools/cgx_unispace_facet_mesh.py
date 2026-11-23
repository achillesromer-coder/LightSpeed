"""Source-qualified five-space UniSpace facade over ONE existing Cognigrex root.

This module only builds deterministic, read-only dependency projections. It
never mounts a new store, accesses a runtime, hydrates private source bodies,
issues agent/tool commands, or grants object/lease/mint authority. Source
presence means a contract exists, not that its engine is installed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Collection

SCHEMA = "CGX-UNISPACE-SINGLE-ROOT-FACET-MESH/0.1"
PLAN_SCHEMA = "CGX-UNISPACE-FACET-PROJECTION-PLAN/0.1"
ROOT_ID = "cgx:root:cognigrex"
ROOT_CARRIER = "Cognigrex.cgx"
PREFIX = "cgx/domain_templates/"
MAX_SOURCE_BYTES = 2 * 1024 * 1024

# These are five UI/workspace facets, NOT five new root DBs, models, daemons,
# independently admitted engines, physical devices, or signed network peers.
FACETS: dict[str, dict[str, tuple[str, ...]]] = {
    "file_space": {
        "services": ("identity", "ccc"),
        "contracts": ("source_envelope", "file_conversion", "domain_child_identity"),
    },
    "data_space": {
        "services": ("cross_domain_graph",),
        "contracts": ("node_exchange", "execution_lease"),
    },
    "social_space": {
        "services": ("agents", "representations"),
        "contracts": ("provider_notification_evidence", "source_envelope"),
    },
    "print_space": {
        "services": ("representations", "technology_stack"),
        "contracts": ("file_conversion", "file_type_conversion", "source_format_adapters"),
    },
    "intelligence_space": {
        "services": ("agents", "assurance"),
        "contracts": ("agent_runtime", "corpus_test_simulation",
                      "corpus_test_capabilities", "agent_assurance_roles"),
    },
}


class FacetHold(ValueError):
    """Input or source authority condition is not qualified."""


def _tracked_paths(repo: Path) -> set[str]:
    try:
        done = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "-z"],
            check=False, capture_output=True, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FacetHold("tracked-source registry unavailable") from exc
    if done.returncode != 0:
        raise FacetHold("tracked-source registry unavailable")
    return {s.decode("utf-8") for s in done.stdout.split(b"\0") if s}


def _record(repo: Path, rel: str, tracked: set[str]) -> dict[str, Any]:
    if (not rel.startswith(PREFIX) or "\\" in rel or "//" in rel
            or "/../" in rel or "/./" in rel or "\x00" in rel
            or rel not in tracked):
        return {"path": rel, "state": "HOLD_SOURCE_UNTRACKED_OR_UNSAFE",
                "sha256": None}
    path = repo / rel
    if (path.is_symlink() or not path.is_file()
            or not path.resolve().is_relative_to(repo)):
        return {"path": rel, "state": "HOLD_SOURCE_UNAVAILABLE",
                "sha256": None}
    size = path.stat().st_size
    if size <= 0 or size > MAX_SOURCE_BYTES:
        return {"path": rel, "state": "HOLD_SOURCE_EMPTY_OR_UNBOUNDED",
                "sha256": None}
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(262144), b""):
            digest.update(chunk)
    return {"path": rel, "state": "SOURCE_BYTES_OBSERVED",
            "bytes": size, "sha256": digest.hexdigest(),
            "not_native_qualification": True}


def _load(repo: Path, rel: str, tracked: set[str]) -> tuple[dict, dict]:
    record = _record(repo, rel, tracked)
    if record["state"] != "SOURCE_BYTES_OBSERVED":
        raise FacetHold("required parent contract unavailable: " + rel)
    obj = json.loads((repo / rel).read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise FacetHold("invalid source contract root: " + rel)
    return obj, record


def _safe_contract_name(filename: str) -> bool:
    return (isinstance(filename, str) and len(filename) <= 150
            and filename not in {"", ".", ".."}
            and filename.endswith(".json")
            and "/" not in filename and "\\" not in filename
            and all(ch.isalnum() or ch in "-_." for ch in filename))


def build_unispace_facet_mesh(
    repo: Path, tracked: Collection[str] | None = None,
) -> dict[str, Any]:
    """Build one immutable source-evidence view across the five named spaces.

    The tracked argument is an independently obtained Git index; without it
    this function reads the real Git index. No inference from untracked files.
    """
    repo = Path(repo).resolve(strict=True)
    indexed = set(_tracked_paths(repo) if tracked is None else tracked)
    manifest_path = PREFIX + "domains.json"
    parent_path = PREFIX + "cognigrex_parent_topology.json"
    parent_records = [_record(repo, p, indexed) for p in
                      (manifest_path, parent_path)]
    if any(x["state"] != "SOURCE_BYTES_OBSERVED" for x in parent_records):
        return {"schema": SCHEMA, "state": "HOLD_PARENT_UNAVAILABLE",
                "canonical_root_id": ROOT_ID, "canonical_carrier": ROOT_CARRIER,
                "root_sources": parent_records, "facets": [], "unique_contract_count": 0,
                "unique_service_count": 0, "new_root_created": False,
                "new_database_created": False, "model_weights_modified": False,
                "native_execution_authorized": False,
                "mint_or_network_authorized": False}
    domains, _ = _load(repo, manifest_path, indexed)
    topology, _ = _load(repo, parent_path, indexed)
    if (domains.get("schema") != "CGX-DOMAIN-TEMPLATES/0.4"
            or topology.get("schema") != "CGX-COGNIGREX-PARENT-TOPOLOGY/0.2"
            or domains.get("parent_filespace", {}).get("file") != ROOT_CARRIER
            or topology.get("root", {}).get("file") != ROOT_CARRIER):
        raise FacetHold("mismatched canonical parent contract")
    shared = domains.get("shared_contracts")
    services = topology.get("shared_root_services")
    if not isinstance(shared, dict) or not isinstance(services, list):
        raise FacetHold("parent shared contract registry incomplete")
    known_services = {}
    for s in services:
        if not isinstance(s, dict) or not isinstance(s.get("id"), str):
            raise FacetHold("invalid parent service")
        if s["id"] in known_services:
            raise FacetHold("duplicate parent service ID")
        loc = s.get("location")
        if not isinstance(loc, str) or not loc.startswith(ROOT_CARRIER + ":/"):
            raise FacetHold("service escapes canonical parent")
        known_services[s["id"]] = loc

    facets = []
    all_contracts: dict[str, dict] = {}
    all_services: set[str] = set()
    for space_id, spec in FACETS.items():
        requirements = []
        missing = []
        for key in spec["contracts"]:
            name = shared.get(key)
            if not _safe_contract_name(name):
                raise FacetHold("contract path violates parent namespace: " + key)
            rel = PREFIX + name
            record = _record(repo, rel, indexed)
            requirements.append({"contract_id": key, **record})
            if record["state"] != "SOURCE_BYTES_OBSERVED":
                missing.append(rel)
            else:
                old = all_contracts.get(key)
                if old and old["path"] != rel:
                    raise FacetHold("shared contract ID collision")
                all_contracts[key] = {"contract_id": key, **record}
        refs = []
        for service in spec["services"]:
            if service not in known_services:
                raise FacetHold("required parent service missing: " + service)
            refs.append({"service_id": service,
                         "shared_root_ref": known_services[service]})
            all_services.add(service)
        facets.append({
            "id": space_id,
            "state": "SOURCE_CONTRACTS_PRESENT" if not missing else "HOLD_SOURCE_GAPS",
            "canonical_root_ref": ROOT_ID,
            "storage_policy": "REFERENCE_EXISTING_ROOT_ONLY",
            "shared_services": refs,
            "contract_bindings": requirements,
            "missing_contract_paths": missing,
            "model_capabilities_distinct": True,
            "runtime_engine_attached": False,
            "source_hydration_performed": False,
            "owner_or_lease_authority_verified": False,
            "execution_authorized": False,
            "independent_native_admission": False,
            "evidence_boundary": "source file identity only",
        })
    return {
        "schema": SCHEMA, "state": "SOURCE_CONTRACT_MESH_OBSERVED"
        if all(not f["missing_contract_paths"] for f in facets)
        else "HOLD_SOURCE_GAPS",
        "canonical_root_id": ROOT_ID, "canonical_carrier": ROOT_CARRIER,
        "root_sources": parent_records,
        "facets": facets, "facet_count": len(facets),
        "unique_contract_count": len(all_contracts),
        "unique_service_count": len(all_services),
        "unique_contracts": [all_contracts[key] for key in sorted(all_contracts)],
        "shared_service_refs": sorted(all_services),
        "new_root_created": False,
        "new_database_created": False,
        "model_weights_modified": False,
        "native_execution_authorized": False,
        "mint_or_network_authorized": False,
        "semantic_authority_transferred": False,
        "source_hydration_performed": False,
        "generated_ui_committed": False,
    }


def plan_facet_projection(mesh: dict[str, Any], spaces: Collection[str],
                          operation: str = "inspect") -> dict[str, Any]:
    """Project contracts once for any chosen subset; NEVER dispatch actions."""
    if operation not in {"inspect", "propose"}:
        raise FacetHold("operation is not a source-only projection")
    requested = list(spaces)
    if len(requested) > 20 or not requested or any(
            not isinstance(x, str) or x not in FACETS for x in requested):
        raise FacetHold("unknown, missing or unbounded requested space")
    unique = sorted(set(requested))
    if mesh.get("schema") != SCHEMA or mesh.get("canonical_root_id") != ROOT_ID:
        raise FacetHold("invalid parent mesh")
    indexed = {x["id"]: x for x in mesh.get("facets", [])}
    missing = [x for x in unique if x not in indexed]
    if missing:
        raise FacetHold("requested facet unavailable in source mesh")
    contract_map: dict[str, dict] = {}
    service_map: dict[str, set[str]] = {}
    held = []
    for space in unique:
        entry = indexed[space]
        if (entry["state"] != "SOURCE_CONTRACTS_PRESENT"
                or any(c.get("state") != "SOURCE_BYTES_OBSERVED"
                       or not isinstance(c.get("sha256"), str)
                       or len(c["sha256"]) != 64
                       for c in entry["contract_bindings"])):
            held.append(space)
        for contract in entry["contract_bindings"]:
            cid = contract["contract_id"]
            old = contract_map.get(cid)
            if old and (old["path"] != contract["path"] or
                        old["sha256"] != contract["sha256"]):
                raise FacetHold("conflicting shared contract definition")
            contract_map[cid] = contract
        for service in entry["shared_services"]:
            service_map.setdefault(service["service_id"], set()).add(space)
    return {
        "schema": PLAN_SCHEMA,
        "parent_root": ROOT_ID,
        "operation": operation,
        "requested_spaces": unique,
        "state": "SOURCE_PROJECTION_READY_FOR_REVIEW" if not held
        else "HOLD_MISSING_CONTRACTS",
        "contract_refs": [{"contract_id": k, **{kk: vv for kk, vv in v.items()
                         if kk != "contract_id"}}
                          for k, v in sorted(contract_map.items())],
        "service_users": [{"service_id": key,
                           "spaces": sorted(members)}
                          for key, members in sorted(service_map.items())],
        "held_spaces": held,
        "single_runtime_requirement": True,
        "copies_or_hydration_performed": False,
        "owner_action_taken": False,
        "model_inference_executed": False,
        "execution_lease_verified": False,
        "semantic_state_mutated": False,
        "native_approval": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--spaces", nargs="*", choices=tuple(FACETS), default=list(FACETS))
    p.add_argument("--operation", choices=("inspect", "propose"), default="inspect")
    args = p.parse_args()
    mesh = build_unispace_facet_mesh(args.repo)
    output = {"mesh": mesh, "projection": plan_facet_projection(mesh, args.spaces,
                                                                  operation=args.operation)}
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
